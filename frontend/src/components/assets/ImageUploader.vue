<script setup>
/**
 * ImageUploader.vue — Drag & Drop Bild-Upload-Bereich
 *
 * Features:
 * - Drag & Drop von Dateien
 * - Klick zum Wählen (File Input Fallback)
 * - Paste aus Clipboard (Strg+V)
 * - URL-Import
 * - Upload-Progress mit animierter Progress-Bar
 * - Thumbnail-Grid nach Upload mit Remove-Button pro Bild
 * - Drag-Reordering für Carousel-Posts (vuedraggable)
 * - Client-seitige Validierung: Max 10 Bilder, Max 10MB pro Bild, nur JPG/PNG/WebP
 * - Bild-Crop/Resize Dialog vor Upload (1:1, 4:5, 9:16)
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import draggable from 'vuedraggable'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  /** Maximum number of images allowed */
  maxImages: { type: Number, default: 10 },
  /** Maximum file size in bytes (default 10MB) */
  maxFileSize: { type: Number, default: 10 * 1024 * 1024 },
  /** Accepted MIME types */
  acceptedTypes: {
    type: Array,
    default: () => ['image/jpeg', 'image/png', 'image/webp'],
  },
  /** Upload category for backend */
  category: { type: String, default: 'background' },
  /** Whether to show the crop dialog before upload */
  enableCrop: { type: Boolean, default: true },
  /** Pre-selected crop aspect ratio */
  cropAspectRatio: { type: String, default: '' },
  /** Whether carousel (multi-image) mode is enabled */
  carousel: { type: Boolean, default: true },
})

const emit = defineEmits([
  'upload',        // emitted when a single image is uploaded: { asset, url }
  'remove',        // emitted when an image is removed: { index, asset }
  'reorder',       // emitted when images are reordered: images[]
  'crop-request',  // emitted when user wants to crop an image: { asset, index }
])

const toast = useToast()

// ── State ──────────────────────────────────────────────────────────
const isDragOver = ref(false)
const uploads = ref([]) // { id, file, progress, status, asset?, preview?, error? }
const images = ref([])  // uploaded images: { id, asset, url, originalFilename }
const showUrlInput = ref(false)
const urlInput = ref('')
const importingUrl = ref(false)
const fileInputRef = ref(null)

// ── Crop state ─────────────────────────────────────────────────────
const showCropModal = ref(false)
const cropFile = ref(null)       // File object to crop before upload
const cropPreviewUrl = ref('')   // Object URL for crop preview
const selectedCropRatio = ref(props.cropAspectRatio || 'free')
const cropArea = ref({ x: 0, y: 0, width: 100, height: 100 })
const cropImageEl = ref(null)
const cropImageLoaded = ref(false)
const cropContainerRef = ref(null)
const cropDisplayScale = ref(1)
const cropDisplayWidth = ref(0)
const cropDisplayHeight = ref(0)
const naturalWidth = ref(0)
const naturalHeight = ref(0)
const isCropDragging = ref(false)
const isCropResizing = ref(false)
const cropDragStart = ref({ x: 0, y: 0, cropX: 0, cropY: 0 })

const cropRatioOptions = [
  { value: 'free', label: 'Frei', ratio: null },
  { value: '4:5', label: '4:5', ratio: 4 / 5 },
  { value: '1:1', label: '1:1', ratio: 1 },
  { value: '9:16', label: '9:16', ratio: 9 / 16 },
  { value: '16:9', label: '16:9', ratio: 16 / 9 },
  { value: '4:3', label: '4:3', ratio: 4 / 3 },
]

const currentCropRatioObj = computed(() =>
  cropRatioOptions.find(r => r.value === selectedCropRatio.value)
)

const cropDisplayArea = computed(() => ({
  x: cropArea.value.x * cropDisplayScale.value,
  y: cropArea.value.y * cropDisplayScale.value,
  width: cropArea.value.width * cropDisplayScale.value,
  height: cropArea.value.height * cropDisplayScale.value,
}))

// ── Computed ───────────────────────────────────────────────────────
const canAddMore = computed(() => images.value.length < props.maxImages)
const remainingSlots = computed(() => props.maxImages - images.value.length)
const hasActiveUploads = computed(() => uploads.value.some(u => u.status === 'uploading'))
const acceptString = computed(() => props.acceptedTypes.join(','))

// File size display helper
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// ── Validation ─────────────────────────────────────────────────────
function validateFile(file) {
  const errors = []
  if (!props.acceptedTypes.includes(file.type)) {
    const allowed = props.acceptedTypes.map(t => t.split('/')[1].toUpperCase()).join(', ')
    errors.push(`Nur ${allowed} Dateien erlaubt.`)
  }
  if (file.size > props.maxFileSize) {
    errors.push(`Datei zu groß (${formatFileSize(file.size)}). Max. ${formatFileSize(props.maxFileSize)}.`)
  }
  return errors
}

function validateCount(newCount) {
  if (images.value.length + newCount > props.maxImages) {
    toast.warning(`Maximal ${props.maxImages} Bilder erlaubt. Noch ${remainingSlots.value} Platz verfügbar.`)
    return false
  }
  return true
}

// ── Drag & Drop handlers ───────────────────────────────────────────
function onDragEnter(e) {
  e.preventDefault()
  isDragOver.value = true
}

function onDragOver(e) {
  e.preventDefault()
  isDragOver.value = true
}

function onDragLeave(e) {
  e.preventDefault()
  // Only set to false if we're leaving the drop zone itself
  const rect = e.currentTarget.getBoundingClientRect()
  const x = e.clientX
  const y = e.clientY
  if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
    isDragOver.value = false
  }
}

function onDrop(e) {
  e.preventDefault()
  isDragOver.value = false
  const files = Array.from(e.dataTransfer?.files || [])
  if (files.length > 0) {
    handleFiles(files)
  }
}

// ── Click to select ────────────────────────────────────────────────
function triggerFileInput() {
  fileInputRef.value?.click()
}

function onFileInputChange(event) {
  const files = Array.from(event.target.files || [])
  if (files.length > 0) {
    handleFiles(files)
  }
  // Reset input so same file can be selected again
  if (fileInputRef.value) fileInputRef.value.value = ''
}

// ── Clipboard paste ────────────────────────────────────────────────
function onPaste(e) {
  const items = e.clipboardData?.items
  if (!items) return
  const imageFiles = []
  for (const item of items) {
    if (item.kind === 'file' && props.acceptedTypes.includes(item.type)) {
      const file = item.getAsFile()
      if (file) imageFiles.push(file)
    }
  }
  if (imageFiles.length > 0) {
    e.preventDefault()
    handleFiles(imageFiles)
  }
}

// ── URL Import ─────────────────────────────────────────────────────
async function importFromUrl() {
  const url = urlInput.value.trim()
  if (!url) return

  if (!validateCount(1)) return

  importingUrl.value = true
  try {
    const response = await api.post('/api/assets/stock/import', {
      download_url: url,
      source: 'url_import',
      category: props.category,
    })
    const asset = response.data
    images.value.push({
      id: asset.id,
      asset,
      url: asset.file_path || `/api/uploads/assets/${asset.filename}`,
      originalFilename: asset.original_filename || 'URL Import',
    })
    emit('upload', { asset, url: `/api/uploads/assets/${asset.filename}` })
    toast.success('Bild importiert!')
    urlInput.value = ''
    showUrlInput.value = false
  } catch (err) {
    toast.error(err.response?.data?.detail || 'URL-Import fehlgeschlagen')
  } finally {
    importingUrl.value = false
  }
}

// ── File handling pipeline ─────────────────────────────────────────
function handleFiles(files) {
  const imageFiles = files.filter(f => props.acceptedTypes.includes(f.type))

  if (imageFiles.length === 0) {
    toast.error('Keine gültige Bilddatei gefunden. Erlaubt: JPG, PNG, WebP.')
    return
  }

  if (!validateCount(imageFiles.length)) {
    // Upload only as many as we have slots for
    const allowed = remainingSlots.value
    if (allowed <= 0) return
    imageFiles.splice(allowed)
  }

  // Validate each file
  for (const file of imageFiles) {
    const errors = validateFile(file)
    if (errors.length > 0) {
      toast.error(`${file.name}: ${errors.join(' ')}`)
      continue
    }

    if (props.enableCrop && imageFiles.length === 1) {
      // Show crop dialog for single file
      openCropDialog(file)
    } else {
      // Upload directly (batch mode, no crop)
      uploadFile(file)
    }
  }
}

// ── Crop Dialog ────────────────────────────────────────────────────
function openCropDialog(file) {
  cropFile.value = file
  cropPreviewUrl.value = URL.createObjectURL(file)
  cropImageLoaded.value = false
  selectedCropRatio.value = props.cropAspectRatio || 'free'
  showCropModal.value = true
}

function onCropImageLoad(event) {
  const img = event.target
  cropImageEl.value = img
  naturalWidth.value = img.naturalWidth
  naturalHeight.value = img.naturalHeight
  cropImageLoaded.value = true

  // Fit to container
  const maxW = 600
  const maxH = 450
  const scaleW = maxW / naturalWidth.value
  const scaleH = maxH / naturalHeight.value
  cropDisplayScale.value = Math.min(scaleW, scaleH, 1)
  cropDisplayWidth.value = naturalWidth.value * cropDisplayScale.value
  cropDisplayHeight.value = naturalHeight.value * cropDisplayScale.value

  initCropArea()
}

function initCropArea() {
  const imgW = naturalWidth.value
  const imgH = naturalHeight.value
  const ratio = currentCropRatioObj.value?.ratio

  if (ratio) {
    if (imgW / imgH > ratio) {
      cropArea.value.height = imgH
      cropArea.value.width = imgH * ratio
    } else {
      cropArea.value.width = imgW
      cropArea.value.height = imgW / ratio
    }
  } else {
    cropArea.value.width = imgW
    cropArea.value.height = imgH
  }
  // Center
  cropArea.value.x = (imgW - cropArea.value.width) / 2
  cropArea.value.y = (imgH - cropArea.value.height) / 2
}

function onCropRatioChange(ratio) {
  selectedCropRatio.value = ratio
  if (cropImageLoaded.value) initCropArea()
}

// ── Crop drag/resize handlers ──────────────────────────────────────
function onCropAreaMouseDown(e) {
  e.preventDefault()
  isCropDragging.value = true
  const rect = cropContainerRef.value.getBoundingClientRect()
  cropDragStart.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top,
    cropX: cropArea.value.x,
    cropY: cropArea.value.y,
  }
  document.addEventListener('mousemove', onCropMouseMove)
  document.addEventListener('mouseup', onCropMouseUp)
}

function onCropResizeMouseDown(e) {
  e.preventDefault()
  e.stopPropagation()
  isCropResizing.value = true
  const rect = cropContainerRef.value.getBoundingClientRect()
  cropDragStart.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top,
    cropW: cropArea.value.width,
    cropH: cropArea.value.height,
  }
  document.addEventListener('mousemove', onCropMouseMove)
  document.addEventListener('mouseup', onCropMouseUp)
}

function onCropMouseMove(e) {
  if (!isCropDragging.value && !isCropResizing.value) return
  const rect = cropContainerRef.value.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
  const imgW = naturalWidth.value
  const imgH = naturalHeight.value

  if (isCropDragging.value) {
    const dx = (mouseX - cropDragStart.value.x) / cropDisplayScale.value
    const dy = (mouseY - cropDragStart.value.y) / cropDisplayScale.value
    let newX = cropDragStart.value.cropX + dx
    let newY = cropDragStart.value.cropY + dy
    newX = Math.max(0, Math.min(newX, imgW - cropArea.value.width))
    newY = Math.max(0, Math.min(newY, imgH - cropArea.value.height))
    cropArea.value.x = newX
    cropArea.value.y = newY
  }

  if (isCropResizing.value) {
    const dx = (mouseX - cropDragStart.value.x) / cropDisplayScale.value
    const dy = (mouseY - cropDragStart.value.y) / cropDisplayScale.value
    const ratio = currentCropRatioObj.value?.ratio

    let newW = cropDragStart.value.cropW + dx
    let newH = cropDragStart.value.cropH + dy
    newW = Math.max(50, Math.min(newW, imgW - cropArea.value.x))
    newH = Math.max(50, Math.min(newH, imgH - cropArea.value.y))

    if (ratio) {
      newH = newW / ratio
      if (newH > imgH - cropArea.value.y) {
        newH = imgH - cropArea.value.y
        newW = newH * ratio
      }
      if (newW > imgW - cropArea.value.x) {
        newW = imgW - cropArea.value.x
        newH = newW / ratio
      }
    }

    cropArea.value.width = newW
    cropArea.value.height = newH
  }
}

function onCropMouseUp() {
  isCropDragging.value = false
  isCropResizing.value = false
  document.removeEventListener('mousemove', onCropMouseMove)
  document.removeEventListener('mouseup', onCropMouseUp)
}

async function applyCropAndUpload() {
  if (!cropFile.value) return
  showCropModal.value = false

  const ratio = currentCropRatioObj.value?.ratio
  const isFullImage = !ratio &&
    Math.round(cropArea.value.x) === 0 &&
    Math.round(cropArea.value.y) === 0 &&
    Math.abs(cropArea.value.width - naturalWidth.value) < 2 &&
    Math.abs(cropArea.value.height - naturalHeight.value) < 2

  if (isFullImage) {
    // No crop needed, upload directly
    uploadFile(cropFile.value)
  } else {
    // Create a cropped version client-side using Canvas
    try {
      const croppedBlob = await cropImageClientSide(
        cropFile.value,
        Math.round(cropArea.value.x),
        Math.round(cropArea.value.y),
        Math.round(cropArea.value.width),
        Math.round(cropArea.value.height)
      )
      const croppedFile = new File([croppedBlob], cropFile.value.name, { type: cropFile.value.type })
      uploadFile(croppedFile)
    } catch (err) {
      // Fallback: upload original
      toast.warning('Zuschnitt fehlgeschlagen, lade Original hoch...')
      uploadFile(cropFile.value)
    }
  }

  // Cleanup
  if (cropPreviewUrl.value) URL.revokeObjectURL(cropPreviewUrl.value)
  cropFile.value = null
  cropPreviewUrl.value = ''
}

function skipCropAndUpload() {
  if (!cropFile.value) return
  showCropModal.value = false
  uploadFile(cropFile.value)
  if (cropPreviewUrl.value) URL.revokeObjectURL(cropPreviewUrl.value)
  cropFile.value = null
  cropPreviewUrl.value = ''
}

function cancelCrop() {
  showCropModal.value = false
  if (cropPreviewUrl.value) URL.revokeObjectURL(cropPreviewUrl.value)
  cropFile.value = null
  cropPreviewUrl.value = ''
}

function cropImageClientSide(file, x, y, w, h) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      canvas.width = w
      canvas.height = h
      const ctx = canvas.getContext('2d')
      ctx.drawImage(img, x, y, w, h, 0, 0, w, h)
      const mimeType = file.type === 'image/png' ? 'image/png' : 'image/jpeg'
      canvas.toBlob((blob) => {
        if (blob) resolve(blob)
        else reject(new Error('Canvas toBlob failed'))
      }, mimeType, 0.92)
    }
    img.onerror = reject
    img.src = URL.createObjectURL(file)
  })
}

// ── Upload file to backend ─────────────────────────────────────────
async function uploadFile(file) {
  const uploadId = Date.now() + '-' + Math.random().toString(36).slice(2, 8)
  const preview = URL.createObjectURL(file)
  const uploadEntry = {
    id: uploadId,
    file,
    progress: 0,
    status: 'uploading',
    preview,
    error: null,
  }
  uploads.value.push(uploadEntry)

  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('category', props.category)

    const response = await api.post('/api/assets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        const entry = uploads.value.find(u => u.id === uploadId)
        if (entry && progressEvent.total) {
          entry.progress = Math.round((progressEvent.loaded / progressEvent.total) * 100)
        }
      },
    })

    // Upload complete
    const entry = uploads.value.find(u => u.id === uploadId)
    if (entry) {
      entry.status = 'done'
      entry.progress = 100
      entry.asset = response.data
    }

    const asset = response.data
    const imageEntry = {
      id: asset.id,
      asset,
      url: `/api/uploads/assets/${asset.filename}`,
      originalFilename: asset.original_filename || file.name,
    }
    images.value.push(imageEntry)
    emit('upload', { asset, url: imageEntry.url })

    // Remove from uploads list after short delay (for visual feedback)
    setTimeout(() => {
      const idx = uploads.value.findIndex(u => u.id === uploadId)
      if (idx !== -1) uploads.value.splice(idx, 1)
      URL.revokeObjectURL(preview)
    }, 1500)

  } catch (err) {
    const entry = uploads.value.find(u => u.id === uploadId)
    if (entry) {
      entry.status = 'error'
      entry.error = err.response?.data?.detail || err.message || 'Upload fehlgeschlagen'
    }
    toast.error(`Upload fehlgeschlagen: ${file.name}`)
  }
}

// ── Remove image ───────────────────────────────────────────────────
function removeImage(index) {
  const removed = images.value.splice(index, 1)[0]
  emit('remove', { index, asset: removed?.asset })
}

// Remove a failed upload from the list
function dismissUpload(index) {
  const removed = uploads.value.splice(index, 1)[0]
  if (removed?.preview) URL.revokeObjectURL(removed.preview)
}

// ── Drag reorder ───────────────────────────────────────────────────
function onReorder() {
  emit('reorder', [...images.value])
}

// ── Crop existing image ────────────────────────────────────────────
function requestCrop(index) {
  emit('crop-request', { asset: images.value[index]?.asset, index })
}

// ── Lifecycle: clipboard listener ──────────────────────────────────
onMounted(() => {
  document.addEventListener('paste', onPaste)
})
onUnmounted(() => {
  document.removeEventListener('paste', onPaste)
  // Cleanup object URLs
  uploads.value.forEach(u => { if (u.preview) URL.revokeObjectURL(u.preview) })
})

// Expose for parent
defineExpose({ images, canAddMore })
</script>

<template>
  <div class="image-uploader" data-testid="image-uploader">
    <!-- ═══ Uploaded Images Grid (Draggable) ═══ -->
    <div v-if="images.length > 0" class="mb-4">
      <div class="flex items-center justify-between mb-2">
        <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300">
          Bilder ({{ images.length }}/{{ maxImages }})
        </h4>
        <span v-if="carousel && images.length > 1" class="text-xs text-gray-400 dark:text-gray-500">
          Drag zum Sortieren
        </span>
      </div>

      <draggable
        v-model="images"
        item-key="id"
        handle=".drag-handle"
        ghost-class="opacity-40"
        animation="200"
        class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-3"
        data-testid="image-grid"
        @end="onReorder"
      >
        <template #item="{ element, index }">
          <div
            class="relative group aspect-square rounded-xl overflow-hidden border-2 border-gray-200 dark:border-gray-700 hover:border-[#3B7AB1] dark:hover:border-[#3B7AB1] transition-all bg-gray-50 dark:bg-gray-800"
            :data-testid="`image-item-${index}`"
          >
            <!-- Drag handle overlay -->
            <div
              v-if="carousel && images.length > 1"
              class="drag-handle absolute inset-0 z-10 cursor-grab active:cursor-grabbing"
            >
              <!-- Drag icon (top-left) -->
              <div class="absolute top-1.5 left-1.5 bg-black/50 text-white rounded p-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 8h16M4 16h16" />
                </svg>
              </div>
            </div>

            <!-- Image thumbnail -->
            <img
              :src="element.url"
              :alt="element.originalFilename"
              class="w-full h-full object-cover"
              loading="lazy"
            />

            <!-- Carousel badge -->
            <div
              v-if="carousel && images.length > 1"
              class="absolute bottom-1.5 left-1.5 bg-black/60 text-white text-[10px] font-bold px-1.5 py-0.5 rounded"
            >
              {{ index + 1 }}
            </div>

            <!-- Actions overlay -->
            <div class="absolute top-1.5 right-1.5 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-20">
              <!-- Crop button -->
              <button
                v-if="enableCrop"
                @click.stop="requestCrop(index)"
                class="bg-black/50 hover:bg-black/70 text-white rounded p-1 transition-colors"
                title="Zuschneiden"
                :data-testid="`crop-btn-${index}`"
              >
                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </button>

              <!-- Remove button -->
              <button
                @click.stop="removeImage(index)"
                class="bg-red-500/80 hover:bg-red-600 text-white rounded p-1 transition-colors"
                title="Entfernen"
                :data-testid="`remove-btn-${index}`"
              >
                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Filename tooltip on hover -->
            <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-1.5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              <span class="text-[10px] text-white truncate block">{{ element.originalFilename }}</span>
            </div>
          </div>
        </template>
      </draggable>
    </div>

    <!-- ═══ Upload Progress Indicators ═══ -->
    <div v-if="uploads.length > 0" class="space-y-2 mb-4">
      <div
        v-for="(upload, idx) in uploads"
        :key="upload.id"
        class="flex items-center gap-3 bg-gray-50 dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700"
        :data-testid="`upload-progress-${idx}`"
      >
        <!-- Thumbnail preview -->
        <div class="w-10 h-10 rounded-lg overflow-hidden bg-gray-200 dark:bg-gray-700 flex-shrink-0">
          <img v-if="upload.preview" :src="upload.preview" class="w-full h-full object-cover" :alt="upload.file?.name || 'Upload-Vorschau'" />
        </div>

        <!-- File info and progress -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs text-gray-700 dark:text-gray-300 truncate">{{ upload.file.name }}</span>
            <span class="text-xs text-gray-400 dark:text-gray-500 flex-shrink-0 ml-2">
              {{ formatFileSize(upload.file.size) }}
            </span>
          </div>

          <!-- Progress bar -->
          <div v-if="upload.status === 'uploading'" class="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
            <div
              class="bg-[#3B7AB1] h-1.5 rounded-full transition-all duration-300 ease-out"
              :style="{ width: upload.progress + '%' }"
              data-testid="upload-progress-bar"
            ></div>
          </div>

          <!-- Success indicator -->
          <div v-else-if="upload.status === 'done'" class="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            Hochgeladen
          </div>

          <!-- Error indicator -->
          <div v-else-if="upload.status === 'error'" class="flex items-center gap-1 text-xs text-red-600 dark:text-red-400">
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.962-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            {{ upload.error }}
            <button @click="dismissUpload(idx)" class="ml-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
              <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Progress percentage -->
        <span v-if="upload.status === 'uploading'" class="text-xs font-medium text-[#3B7AB1] flex-shrink-0">
          {{ upload.progress }}%
        </span>
      </div>
    </div>

    <!-- ═══ Drop Zone ═══ -->
    <div
      v-if="canAddMore"
      class="relative rounded-xl border-2 border-dashed transition-all duration-200 cursor-pointer"
      :class="isDragOver
        ? 'border-[#3B7AB1] bg-blue-50/50 dark:bg-blue-900/10 scale-[1.01]'
        : 'border-gray-300 dark:border-gray-600 hover:border-[#3B7AB1] hover:bg-gray-50 dark:hover:bg-gray-800/50'"
      data-testid="drop-zone"
      @dragenter="onDragEnter"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
      @click="triggerFileInput"
    >
      <div class="flex flex-col items-center justify-center py-8 px-4 pointer-events-none">
        <!-- Icon -->
        <div class="mb-3" :class="isDragOver ? 'scale-110' : ''">
          <svg class="h-10 w-10" :class="isDragOver ? 'text-[#3B7AB1]' : 'text-gray-400 dark:text-gray-500'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
        </div>

        <!-- Text -->
        <p class="text-sm font-medium" :class="isDragOver ? 'text-[#3B7AB1]' : 'text-gray-600 dark:text-gray-400'">
          <span v-if="isDragOver">Hier ablegen!</span>
          <span v-else>
            Bilder hierher ziehen oder
            <span class="text-[#3B7AB1] font-semibold underline underline-offset-2">klicken</span>
          </span>
        </p>

        <p class="text-xs text-gray-400 dark:text-gray-500 mt-1.5">
          JPG, PNG oder WebP &middot; max. {{ formatFileSize(maxFileSize) }} pro Bild
          <span v-if="carousel"> &middot; bis zu {{ maxImages }} Bilder</span>
        </p>

        <!-- Paste hint -->
        <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
          Tipp: Strg+V zum Einfügen aus der Zwischenablage
        </p>
      </div>

      <!-- Hidden file input -->
      <input
        ref="fileInputRef"
        type="file"
        :accept="acceptString"
        :multiple="carousel"
        class="hidden"
        @change="onFileInputChange"
        data-testid="file-input"
      />
    </div>

    <!-- ═══ URL Import Toggle ═══ -->
    <div v-if="canAddMore" class="mt-3">
      <button
        @click="showUrlInput = !showUrlInput"
        class="text-xs text-[#3B7AB1] hover:text-[#2E6A9E] font-medium flex items-center gap-1 transition-colors"
        data-testid="url-import-toggle"
      >
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
        {{ showUrlInput ? 'URL-Import ausblenden' : 'Bild von URL importieren' }}
      </button>

      <div v-if="showUrlInput" class="mt-2 flex gap-2" data-testid="url-import-form">
        <input
          v-model="urlInput"
          type="url"
          placeholder="https://example.com/bild.jpg"
          class="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-[#3B7AB1] focus:border-[#3B7AB1]"
          @keydown.enter="importFromUrl"
          :disabled="importingUrl"
        />
        <button
          @click="importFromUrl"
          :disabled="importingUrl || !urlInput.trim()"
          class="px-4 py-2 bg-[#3B7AB1] text-white rounded-lg hover:bg-[#2E6A9E] disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium flex items-center gap-1.5"
          data-testid="url-import-btn"
        >
          <span v-if="importingUrl" class="animate-spin h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full"></span>
          <span v-else>Importieren</span>
        </button>
      </div>
    </div>

    <!-- ═══ Max images reached notice ═══ -->
    <div v-if="!canAddMore" class="mt-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg p-3 text-sm text-amber-700 dark:text-amber-300 flex items-center gap-2">
      <svg class="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.962-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
      Maximum von {{ maxImages }} Bildern erreicht. Entferne ein Bild, um weitere hinzuzufügen.
    </div>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- CROP DIALOG (Teleported Modal) -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <Teleport to="body">
      <div
        v-if="showCropModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        data-testid="crop-dialog"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/60" @click="cancelCrop"></div>

        <!-- Modal -->
        <div class="relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div>
              <h2 class="text-lg font-bold text-gray-900 dark:text-white">Bild zuschneiden</h2>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ cropFile?.name }}
                <span v-if="naturalWidth && naturalHeight" class="ml-1">({{ naturalWidth }}&times;{{ naturalHeight }}px)</span>
              </p>
            </div>
            <button
              @click="cancelCrop"
              class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
              aria-label="Dialog schließen"
            >
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="flex-1 overflow-auto p-6 space-y-4">
            <!-- Aspect ratio buttons -->
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Format:</span>
              <div class="flex gap-1">
                <button
                  v-for="opt in cropRatioOptions"
                  :key="opt.value"
                  @click="onCropRatioChange(opt.value)"
                  class="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors"
                  :class="selectedCropRatio === opt.value
                    ? 'bg-[#3B7AB1] text-white'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'"
                  :data-testid="`crop-ratio-${opt.value}`"
                >
                  {{ opt.label }}
                </button>
              </div>
            </div>

            <!-- Image + Crop Area -->
            <div
              ref="cropContainerRef"
              class="relative mx-auto bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden select-none"
              :style="{ width: cropDisplayWidth + 'px', height: cropDisplayHeight + 'px' }"
            >
              <img
                v-if="cropPreviewUrl"
                :src="cropPreviewUrl"
                :style="{ width: cropDisplayWidth + 'px', height: cropDisplayHeight + 'px' }"
                class="block"
                draggable="false"
                @load="onCropImageLoad"
              />

              <!-- Overlays (outside crop area) -->
              <template v-if="cropImageLoaded">
                <div class="absolute pointer-events-none bg-black/50" :style="{
                  left: '0px', top: '0px',
                  width: cropDisplayArea.x + 'px', height: cropDisplayHeight + 'px'
                }"></div>
                <div class="absolute pointer-events-none bg-black/50" :style="{
                  left: (cropDisplayArea.x + cropDisplayArea.width) + 'px', top: '0px',
                  width: (cropDisplayWidth - cropDisplayArea.x - cropDisplayArea.width) + 'px', height: cropDisplayHeight + 'px'
                }"></div>
                <div class="absolute pointer-events-none bg-black/50" :style="{
                  left: cropDisplayArea.x + 'px', top: '0px',
                  width: cropDisplayArea.width + 'px', height: cropDisplayArea.y + 'px'
                }"></div>
                <div class="absolute pointer-events-none bg-black/50" :style="{
                  left: cropDisplayArea.x + 'px', top: (cropDisplayArea.y + cropDisplayArea.height) + 'px',
                  width: cropDisplayArea.width + 'px',
                  height: (cropDisplayHeight - cropDisplayArea.y - cropDisplayArea.height) + 'px'
                }"></div>

                <!-- Crop selection box -->
                <div
                  class="absolute cursor-move"
                  :style="{
                    left: cropDisplayArea.x + 'px',
                    top: cropDisplayArea.y + 'px',
                    width: cropDisplayArea.width + 'px',
                    height: cropDisplayArea.height + 'px',
                    border: '2px dashed white',
                    boxShadow: '0 0 0 1px rgba(0,0,0,0.3)',
                  }"
                  @mousedown="onCropAreaMouseDown"
                >
                  <!-- Grid lines (rule of thirds) -->
                  <div class="absolute inset-0 pointer-events-none">
                    <div class="absolute left-1/3 top-0 bottom-0 w-px bg-white/30"></div>
                    <div class="absolute left-2/3 top-0 bottom-0 w-px bg-white/30"></div>
                    <div class="absolute top-1/3 left-0 right-0 h-px bg-white/30"></div>
                    <div class="absolute top-2/3 left-0 right-0 h-px bg-white/30"></div>
                  </div>

                  <!-- Resize handle -->
                  <div
                    class="absolute -bottom-2 -right-2 w-5 h-5 bg-white border-2 border-[#3B7AB1] rounded-sm cursor-se-resize shadow"
                    @mousedown="onCropResizeMouseDown"
                  ></div>

                  <!-- Corner indicators -->
                  <div class="absolute -top-1 -left-1 w-3 h-3 border-t-2 border-l-2 border-white pointer-events-none"></div>
                  <div class="absolute -top-1 -right-1 w-3 h-3 border-t-2 border-r-2 border-white pointer-events-none"></div>
                  <div class="absolute -bottom-1 -left-1 w-3 h-3 border-b-2 border-l-2 border-white pointer-events-none"></div>
                </div>
              </template>

              <!-- Loading spinner -->
              <div v-if="cropPreviewUrl && !cropImageLoaded" class="absolute inset-0 flex items-center justify-center">
                <span class="animate-spin h-8 w-8 border-3 border-[#3B7AB1] border-t-transparent rounded-full"></span>
              </div>
            </div>

            <!-- Crop info -->
            <div class="flex items-center justify-between bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-sm text-gray-600 dark:text-gray-400">
              <div class="flex gap-4">
                <span>B: <strong class="text-gray-900 dark:text-white">{{ Math.round(cropArea.width) }}px</strong></span>
                <span>H: <strong class="text-gray-900 dark:text-white">{{ Math.round(cropArea.height) }}px</strong></span>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-between gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
            <button
              @click="skipCropAndUpload"
              class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
              data-testid="skip-crop-btn"
            >
              Ohne Zuschnitt hochladen
            </button>
            <div class="flex gap-2">
              <button
                @click="cancelCrop"
                class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Abbrechen
              </button>
              <button
                @click="applyCropAndUpload"
                class="px-5 py-2 text-sm font-medium text-white bg-[#3B7AB1] rounded-lg hover:bg-[#2E6A9E] transition-colors flex items-center gap-2"
                data-testid="apply-crop-upload-btn"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                Zuschneiden & Hochladen
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
