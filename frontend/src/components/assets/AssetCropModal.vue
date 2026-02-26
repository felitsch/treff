<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import { useFocusTrap } from '@/composables/useFocusTrap'

const props = defineProps({
  asset: { type: Object, required: true },
  show: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'cropped'])

const toast = useToast()
const canvasRef = ref(null)
const containerRef = ref(null)
const cropModalRef = ref(null)
const { activate: activateFocusTrap, deactivate: deactivateFocusTrap } = useFocusTrap(cropModalRef)

// Crop state
const cropX = ref(0)
const cropY = ref(0)
const cropWidth = ref(100)
const cropHeight = ref(100)
const selectedRatio = ref('free')
const saveAsNew = ref(true)
const isCropping = ref(false)
const imageLoaded = ref(false)
const imageEl = ref(null)

// Display state (scaled coordinates for the UI)
const displayScale = ref(1)
const displayWidth = ref(0)
const displayHeight = ref(0)

// Drag state
const isDragging = ref(false)
const isResizing = ref(false)
const dragStart = ref({ x: 0, y: 0, cropX: 0, cropY: 0 })
const resizeHandle = ref(null)

// Aspect ratio options
const ratioOptions = [
  { value: 'free', label: 'Frei', ratio: null },
  { value: '4:5', label: '4:5', ratio: 4 / 5 },
  { value: '1:1', label: '1:1', ratio: 1 },
  { value: '4:3', label: '4:3', ratio: 4 / 3 },
  { value: '3:4', label: '3:4', ratio: 3 / 4 },
  { value: '16:9', label: '16:9', ratio: 16 / 9 },
  { value: '9:16', label: '9:16', ratio: 9 / 16 },
]

const currentRatioObj = computed(() => ratioOptions.find(r => r.value === selectedRatio.value))

// Image source URL
const imageSrc = computed(() => {
  if (!props.asset) return ''
  return props.asset.file_path
})

// Computed crop info
const cropInfo = computed(() => ({
  x: Math.round(cropX.value),
  y: Math.round(cropY.value),
  width: Math.round(cropWidth.value),
  height: Math.round(cropHeight.value),
}))

// Display-space crop coordinates (scaled for the preview)
const displayCrop = computed(() => ({
  x: cropX.value * displayScale.value,
  y: cropY.value * displayScale.value,
  width: cropWidth.value * displayScale.value,
  height: cropHeight.value * displayScale.value,
}))

function loadImage() {
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    imageEl.value = img
    imageLoaded.value = true
    nextTick(() => {
      fitImageToContainer()
      initCropArea()
    })
  }
  img.onerror = () => {
    toast.error('Bild konnte nicht geladen werden')
  }
  img.src = imageSrc.value
}

function fitImageToContainer() {
  if (!imageEl.value) return
  // Use parent element width or fallback to a sensible default
  const parentEl = containerRef.value?.parentElement
  const containerWidth = parentEl ? parentEl.clientWidth : 640
  const maxHeight = 500
  const imgW = props.asset.width || imageEl.value.naturalWidth
  const imgH = props.asset.height || imageEl.value.naturalHeight

  const scaleW = containerWidth / imgW
  const scaleH = maxHeight / imgH
  displayScale.value = Math.min(scaleW, scaleH, 1)
  displayWidth.value = imgW * displayScale.value
  displayHeight.value = imgH * displayScale.value
}

function initCropArea() {
  const imgW = props.asset.width || imageEl.value?.naturalWidth || 100
  const imgH = props.asset.height || imageEl.value?.naturalHeight || 100

  const ratio = currentRatioObj.value?.ratio
  if (ratio) {
    // Fit the largest possible crop area with this ratio
    if (imgW / imgH > ratio) {
      // Image is wider - height is the constraint
      cropHeight.value = imgH
      cropWidth.value = imgH * ratio
    } else {
      // Image is taller - width is the constraint
      cropWidth.value = imgW
      cropHeight.value = imgW / ratio
    }
  } else {
    cropWidth.value = imgW
    cropHeight.value = imgH
  }

  // Center the crop area
  cropX.value = (imgW - cropWidth.value) / 2
  cropY.value = (imgH - cropHeight.value) / 2
}

// Watch for ratio changes
watch(selectedRatio, () => {
  if (imageLoaded.value) {
    initCropArea()
  }
})

// Mouse/touch handlers for crop area manipulation
function onCropMouseDown(e) {
  e.preventDefault()
  isDragging.value = true
  const rect = containerRef.value.getBoundingClientRect()
  dragStart.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top,
    cropX: cropX.value,
    cropY: cropY.value,
  }
  document.addEventListener('mousemove', onCropMouseMove)
  document.addEventListener('mouseup', onCropMouseUp)
}

function onCropMouseMove(e) {
  if (!isDragging.value && !isResizing.value) return
  const rect = containerRef.value.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
  const imgW = props.asset.width || imageEl.value?.naturalWidth || 100
  const imgH = props.asset.height || imageEl.value?.naturalHeight || 100

  if (isDragging.value) {
    const dx = (mouseX - dragStart.value.x) / displayScale.value
    const dy = (mouseY - dragStart.value.y) / displayScale.value
    let newX = dragStart.value.cropX + dx
    let newY = dragStart.value.cropY + dy

    // Clamp to image bounds
    newX = Math.max(0, Math.min(newX, imgW - cropWidth.value))
    newY = Math.max(0, Math.min(newY, imgH - cropHeight.value))
    cropX.value = newX
    cropY.value = newY
  }

  if (isResizing.value) {
    const dx = (mouseX - dragStart.value.x) / displayScale.value
    const dy = (mouseY - dragStart.value.y) / displayScale.value
    const ratio = currentRatioObj.value?.ratio

    let newW = dragStart.value.cropW + dx
    let newH = dragStart.value.cropH + dy

    // Minimum size
    newW = Math.max(50, newW)
    newH = Math.max(50, newH)

    // Clamp to image bounds
    newW = Math.min(newW, imgW - cropX.value)
    newH = Math.min(newH, imgH - cropY.value)

    if (ratio) {
      // Maintain aspect ratio - use width as primary
      newH = newW / ratio
      if (newH > imgH - cropY.value) {
        newH = imgH - cropY.value
        newW = newH * ratio
      }
      if (newW > imgW - cropX.value) {
        newW = imgW - cropX.value
        newH = newW / ratio
      }
    }

    cropWidth.value = newW
    cropHeight.value = newH
  }
}

function onCropMouseUp() {
  isDragging.value = false
  isResizing.value = false
  document.removeEventListener('mousemove', onCropMouseMove)
  document.removeEventListener('mouseup', onCropMouseUp)
}

function onResizeMouseDown(e) {
  e.preventDefault()
  e.stopPropagation()
  isResizing.value = true
  const rect = containerRef.value.getBoundingClientRect()
  dragStart.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top,
    cropW: cropWidth.value,
    cropH: cropHeight.value,
  }
  document.addEventListener('mousemove', onCropMouseMove)
  document.addEventListener('mouseup', onCropMouseUp)
}

// Apply crop
async function applyCrop() {
  isCropping.value = true
  try {
    const response = await api.post('/api/assets/crop', {
      asset_id: props.asset.id,
      x: Math.round(cropX.value),
      y: Math.round(cropY.value),
      width: Math.round(cropWidth.value),
      height: Math.round(cropHeight.value),
      save_as_new: saveAsNew.value,
    })

    toast.success('Bild erfolgreich zugeschnitten!')
    emit('cropped', response.data)
    emit('close')
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Fehler beim Zuschneiden')
  } finally {
    isCropping.value = false
  }
}

watch(() => props.show, (val) => {
  if (val && props.asset) {
    imageLoaded.value = false
    nextTick(() => loadImage())
    // Activate focus trap for accessibility
    requestAnimationFrame(() => activateFocusTrap())
  } else {
    deactivateFocusTrap()
  }
})

onMounted(() => {
  if (props.show && props.asset) {
    loadImage()
  }
})
</script>

<template>
  <!-- Modal Overlay -->
  <Teleport to="body">
    <div
      v-if="show"
      ref="cropModalRef"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="crop-modal-title"
      data-testid="crop-modal"
    >
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/60" @click="emit('close')" aria-hidden="true"></div>

      <!-- Modal Content -->
      <div class="relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 id="crop-modal-title" class="text-lg font-bold text-gray-900 dark:text-white">Bild zuschneiden</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ asset.original_filename || asset.filename }}
              <span v-if="asset.width && asset.height" class="ml-1">({{ asset.width }}&times;{{ asset.height }}px)</span>
            </p>
          </div>
          <button
            @click="emit('close')"
            class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
            aria-label="Dialog schließen"
            data-testid="crop-modal-close"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-auto p-6 space-y-4">
          <!-- Aspect Ratio Selection -->
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Seitenverhältnis:</span>
            <div class="flex gap-1" data-testid="ratio-buttons">
              <button
                v-for="opt in ratioOptions"
                :key="opt.value"
                @click="selectedRatio = opt.value"
                class="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors"
                :class="selectedRatio === opt.value
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'"
                :data-testid="`ratio-${opt.value}`"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>

          <!-- Image + Crop Area -->
          <div
            ref="containerRef"
            class="relative mx-auto bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden select-none"
            :style="{ width: displayWidth + 'px', height: displayHeight + 'px' }"
            data-testid="crop-container"
          >
            <!-- Source image -->
            <img
              v-if="imageLoaded"
              :src="imageSrc"
              :style="{ width: displayWidth + 'px', height: displayHeight + 'px' }"
              class="block"
              draggable="false"
            />

            <!-- Dark overlay outside crop area -->
            <div
              v-if="imageLoaded"
              class="absolute inset-0 pointer-events-none"
              :style="{
                background: `linear-gradient(to right, rgba(0,0,0,0.5) ${displayCrop.x}px, transparent ${displayCrop.x}px, transparent ${displayCrop.x + displayCrop.width}px, rgba(0,0,0,0.5) ${displayCrop.x + displayCrop.width}px)`
              }"
            ></div>

            <!-- Top overlay -->
            <div
              v-if="imageLoaded"
              class="absolute pointer-events-none bg-black/50"
              :style="{
                left: displayCrop.x + 'px',
                top: '0px',
                width: displayCrop.width + 'px',
                height: displayCrop.y + 'px',
              }"
            ></div>

            <!-- Bottom overlay -->
            <div
              v-if="imageLoaded"
              class="absolute pointer-events-none bg-black/50"
              :style="{
                left: displayCrop.x + 'px',
                top: (displayCrop.y + displayCrop.height) + 'px',
                width: displayCrop.width + 'px',
                height: (displayHeight - displayCrop.y - displayCrop.height) + 'px',
              }"
            ></div>

            <!-- Left overlay -->
            <div
              v-if="imageLoaded"
              class="absolute pointer-events-none bg-black/50"
              :style="{
                left: '0px',
                top: '0px',
                width: displayCrop.x + 'px',
                height: displayHeight + 'px',
              }"
            ></div>

            <!-- Right overlay -->
            <div
              v-if="imageLoaded"
              class="absolute pointer-events-none bg-black/50"
              :style="{
                left: (displayCrop.x + displayCrop.width) + 'px',
                top: '0px',
                width: (displayWidth - displayCrop.x - displayCrop.width) + 'px',
                height: displayHeight + 'px',
              }"
            ></div>

            <!-- Crop selection box (draggable) -->
            <div
              v-if="imageLoaded"
              class="absolute cursor-move"
              :style="{
                left: displayCrop.x + 'px',
                top: displayCrop.y + 'px',
                width: displayCrop.width + 'px',
                height: displayCrop.height + 'px',
                border: '2px dashed white',
                boxShadow: '0 0 0 1px rgba(0,0,0,0.3)',
              }"
              data-testid="crop-selection"
              @mousedown="onCropMouseDown"
            >
              <!-- Grid lines (rule of thirds) -->
              <div class="absolute inset-0 pointer-events-none">
                <div class="absolute left-1/3 top-0 bottom-0 w-px bg-white/30"></div>
                <div class="absolute left-2/3 top-0 bottom-0 w-px bg-white/30"></div>
                <div class="absolute top-1/3 left-0 right-0 h-px bg-white/30"></div>
                <div class="absolute top-2/3 left-0 right-0 h-px bg-white/30"></div>
              </div>

              <!-- Resize handle (bottom-right corner) -->
              <div
                class="absolute -bottom-2 -right-2 w-5 h-5 bg-white border-2 border-blue-500 rounded-sm cursor-se-resize shadow"
                data-testid="crop-resize-handle"
                @mousedown="onResizeMouseDown"
              ></div>

              <!-- Corner indicators -->
              <div class="absolute -top-1 -left-1 w-3 h-3 border-t-2 border-l-2 border-white pointer-events-none"></div>
              <div class="absolute -top-1 -right-1 w-3 h-3 border-t-2 border-r-2 border-white pointer-events-none"></div>
              <div class="absolute -bottom-1 -left-1 w-3 h-3 border-b-2 border-l-2 border-white pointer-events-none"></div>
            </div>

            <!-- Loading spinner -->
            <div v-if="!imageLoaded" class="absolute inset-0 flex items-center justify-center">
              <svg class="animate-spin h-8 w-8 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
          </div>

          <!-- Crop Info -->
          <div class="flex items-center justify-between bg-gray-50 dark:bg-gray-800 rounded-lg p-3" data-testid="crop-info">
            <div class="flex gap-4 text-sm text-gray-600 dark:text-gray-400">
              <span>X: <strong class="text-gray-900 dark:text-white">{{ cropInfo.x }}</strong></span>
              <span>Y: <strong class="text-gray-900 dark:text-white">{{ cropInfo.y }}</strong></span>
              <span>B: <strong class="text-gray-900 dark:text-white">{{ cropInfo.width }}px</strong></span>
              <span>H: <strong class="text-gray-900 dark:text-white">{{ cropInfo.height }}px</strong></span>
            </div>
            <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
              <input
                type="checkbox"
                v-model="saveAsNew"
                class="rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700 text-blue-500 focus:ring-blue-500"
                data-testid="save-as-new-checkbox"
              />
              Als neues Asset speichern
            </label>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <button
            @click="emit('close')"
            class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            Abbrechen
          </button>
          <button
            @click="applyCrop"
            :disabled="isCropping"
            class="px-5 py-2 text-sm font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            data-testid="apply-crop-btn"
          >
            <svg v-if="isCropping" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            {{ isCropping ? 'Wird zugeschnitten...' : 'Zuschneiden' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
