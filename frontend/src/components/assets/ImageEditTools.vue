<script setup>
/**
 * ImageEditTools.vue - KI-Bildbearbeitung: Hintergrund entfernen, Style Transfer, Outpainting
 *
 * Tools:
 * - Hintergrund entfernen (Freisteller)
 * - Style Transfer (Foto in Illustration, Aquarell, Minimalistisch, Comic, Oelgemaelde)
 * - Format anpassen (Outpainting: 1:1 -> 4:5, 9:16, etc.)
 *
 * Shows Before/After comparison slider. Saves as new version (original preserved).
 */
import { ref, computed, watch, nextTick } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  /** The asset object to edit */
  asset: {
    type: Object,
    required: true,
  },
  /** Show/hide the modal */
  show: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'image-edited'])
const toast = useToast()

// State
const selectedTool = ref('remove_background')
const selectedStyle = ref('illustration')
const selectedRatio = ref('4:5')
const processing = ref(false)
const editedImageUrl = ref(null)
const editedAsset = ref(null)
const editSource = ref('')
const sliderPosition = ref(50)
const isDragging = ref(false)

// Tool definitions
const tools = [
  {
    id: 'remove_background',
    label: 'Hintergrund entfernen',
    icon: '✂️',
    description: 'Freisteller erstellen – Hintergrund wird entfernt',
  },
  {
    id: 'style_transfer',
    label: 'Style Transfer',
    icon: '🎨',
    description: 'Foto in einen anderen Stil umwandeln',
  },
  {
    id: 'outpainting',
    label: 'Format anpassen',
    icon: '🖼️',
    description: 'Bild mit KI auf neues Format erweitern',
  },
]

// Style presets for style transfer
const stylePresets = [
  { id: 'illustration', label: 'Illustration', icon: '🎨', desc: 'Digital, bunt, flaches Design' },
  { id: 'watercolor', label: 'Aquarell', icon: '💧', desc: 'Weiche Farben, Pinselstriche' },
  { id: 'minimalist', label: 'Minimalistisch', icon: '◻️', desc: 'Klare Linien, wenig Farben' },
  { id: 'comic', label: 'Comic', icon: '💥', desc: 'Outlines, Halftone, Pop-Art' },
  { id: 'oil_painting', label: 'Oelgemaelde', icon: '🖌️', desc: 'Klassisch, Textur, tiefe Farben' },
]

// Aspect ratio presets for outpainting
const ratioPresets = [
  { id: '1:1', label: '1:1', desc: 'Quadrat (Instagram Feed)' },
  { id: '4:5', label: '4:5', desc: 'Hochformat (Instagram Feed)' },
  { id: '9:16', label: '9:16', desc: 'Story / Reel / TikTok' },
  { id: '16:9', label: '16:9', desc: 'Querformat (YouTube)' },
]

// Original image URL
const originalImageUrl = computed(() => {
  if (!props.asset) return ''
  // Use the file_path or construct from API
  if (props.asset.file_path) {
    return '/api' + props.asset.file_path
  }
  return ''
})

// Reset state when tool changes
watch(selectedTool, () => {
  editedImageUrl.value = null
  editedAsset.value = null
  sliderPosition.value = 50
})

// Reset when modal opens/closes
watch(() => props.show, (val) => {
  if (val) {
    editedImageUrl.value = null
    editedAsset.value = null
    selectedTool.value = 'remove_background'
    sliderPosition.value = 50
  }
})

async function applyEdit() {
  if (processing.value) return
  processing.value = true
  editedImageUrl.value = null
  editedAsset.value = null

  try {
    const payload = {
      asset_id: props.asset.id,
      operation: selectedTool.value,
    }

    if (selectedTool.value === 'style_transfer') {
      payload.style = selectedStyle.value
    } else if (selectedTool.value === 'outpainting') {
      payload.target_aspect_ratio = selectedRatio.value
    }

    const res = await api.post('/api/ai/edit-image', payload)

    if (res.data.status === 'success') {
      editedImageUrl.value = res.data.image_url
      editedAsset.value = res.data.asset
      editSource.value = res.data.source
      toast.success(res.data.message || 'Bild bearbeitet!')
    } else {
      toast.error(res.data.message || 'Bearbeitung fehlgeschlagen.')
    }
  } catch (err) {
    const msg = err.response?.data?.detail || 'Bildbearbeitung fehlgeschlagen.'
    toast.error(msg)
  } finally {
    processing.value = false
  }
}

function useEditedImage() {
  if (editedAsset.value) {
    emit('image-edited', editedAsset.value)
    emit('close')
  }
}

function closeModal() {
  emit('close')
}

// Before/After slider interaction
function onSliderMouseDown(e) {
  isDragging.value = true
  updateSlider(e)
}

function onSliderMouseMove(e) {
  if (!isDragging.value) return
  updateSlider(e)
}

function onSliderMouseUp() {
  isDragging.value = false
}

function updateSlider(e) {
  const container = e.currentTarget.closest('[data-compare-container]')
  if (!container) return
  const rect = container.getBoundingClientRect()
  const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width))
  sliderPosition.value = (x / rect.width) * 100
}

function onSliderTouch(e) {
  const touch = e.touches[0]
  const container = e.currentTarget.closest('[data-compare-container]')
  if (!container) return
  const rect = container.getBoundingClientRect()
  const x = Math.max(0, Math.min(touch.clientX - rect.left, rect.width))
  sliderPosition.value = (x / rect.width) * 100
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="show"
        class="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-sm"
        @click.self="closeModal"
        data-testid="image-edit-modal"
      >
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col mx-4">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
              🎨 KI-Bildbearbeitung
            </h2>
            <button
              @click="closeModal"
              class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              aria-label="Schliessen"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="flex-1 overflow-y-auto p-6 space-y-5">
            <!-- Tool Selection -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Werkzeug waehlen</label>
              <div class="grid grid-cols-3 gap-2">
                <button
                  v-for="tool in tools"
                  :key="tool.id"
                  @click="selectedTool = tool.id"
                  :class="[
                    'flex flex-col items-center gap-1 p-3 rounded-xl border-2 transition-all text-center',
                    selectedTool === tool.id
                      ? 'border-[#4C8BC2] bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600',
                  ]"
                  data-testid="tool-select"
                >
                  <span class="text-2xl">{{ tool.icon }}</span>
                  <span class="text-xs font-semibold text-gray-800 dark:text-gray-200">{{ tool.label }}</span>
                  <span class="text-[10px] text-gray-500 dark:text-gray-400 leading-tight">{{ tool.description }}</span>
                </button>
              </div>
            </div>

            <!-- Style Transfer Options -->
            <div v-if="selectedTool === 'style_transfer'">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Stil waehlen</label>
              <div class="grid grid-cols-5 gap-2">
                <button
                  v-for="sp in stylePresets"
                  :key="sp.id"
                  @click="selectedStyle = sp.id"
                  :class="[
                    'flex flex-col items-center gap-1 p-2.5 rounded-lg border-2 transition-all text-center',
                    selectedStyle === sp.id
                      ? 'border-[#4C8BC2] bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300',
                  ]"
                  data-testid="style-select"
                >
                  <span class="text-xl">{{ sp.icon }}</span>
                  <span class="text-[10px] font-semibold text-gray-800 dark:text-gray-200">{{ sp.label }}</span>
                </button>
              </div>
            </div>

            <!-- Outpainting Options -->
            <div v-if="selectedTool === 'outpainting'">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Zielformat waehlen</label>
              <div class="grid grid-cols-4 gap-2">
                <button
                  v-for="rp in ratioPresets"
                  :key="rp.id"
                  @click="selectedRatio = rp.id"
                  :class="[
                    'flex flex-col items-center gap-1 p-2.5 rounded-lg border-2 transition-all text-center',
                    selectedRatio === rp.id
                      ? 'border-[#4C8BC2] bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300',
                  ]"
                  data-testid="ratio-select"
                >
                  <span class="text-sm font-bold text-gray-800 dark:text-gray-200">{{ rp.label }}</span>
                  <span class="text-[10px] text-gray-500 dark:text-gray-400">{{ rp.desc }}</span>
                </button>
              </div>
            </div>

            <!-- Apply Button -->
            <button
              @click="applyEdit"
              :disabled="processing"
              data-testid="apply-edit-btn"
              class="w-full py-3 px-4 bg-[#4C8BC2] text-white font-semibold rounded-xl hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <span v-if="processing" class="animate-spin">⏳</span>
              <span v-else>✨</span>
              {{ processing ? 'Bearbeite...' : 'Bearbeitung starten' }}
            </button>

            <!-- Before/After Comparison -->
            <div v-if="editedImageUrl" class="space-y-3">
              <div class="flex items-center justify-between">
                <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-200">Vorher / Nachher Vergleich</h3>
                <span
                  class="text-xs font-medium px-2 py-0.5 rounded-full"
                  :class="editSource === 'gemini' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'"
                >
                  {{ editSource === 'gemini' ? 'KI-bearbeitet' : 'Vorschau (lokal)' }}
                </span>
              </div>

              <!-- Comparison slider -->
              <div
                data-compare-container
                class="relative w-full rounded-lg overflow-hidden select-none cursor-col-resize border border-gray-200 dark:border-gray-700"
                style="aspect-ratio: auto;"
                @mousedown="onSliderMouseDown"
                @mousemove="onSliderMouseMove"
                @mouseup="onSliderMouseUp"
                @mouseleave="onSliderMouseUp"
                @touchmove.prevent="onSliderTouch"
                data-testid="compare-slider"
              >
                <!-- After (edited) – full width background -->
                <img
                  :src="editedImageUrl"
                  alt="Nachher"
                  class="w-full h-auto block"
                  draggable="false"
                />
                <!-- Before (original) – clipped by slider -->
                <div
                  class="absolute top-0 left-0 h-full overflow-hidden"
                  :style="{ width: sliderPosition + '%' }"
                >
                  <img
                    :src="originalImageUrl"
                    alt="Vorher"
                    class="h-full object-cover"
                    :style="{ width: '100%', maxWidth: 'none', minWidth: '100%' }"
                    draggable="false"
                  />
                </div>
                <!-- Slider line -->
                <div
                  class="absolute top-0 h-full w-0.5 bg-white shadow-lg pointer-events-none"
                  :style="{ left: sliderPosition + '%' }"
                >
                  <div class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 bg-white rounded-full shadow-lg flex items-center justify-center pointer-events-auto cursor-col-resize">
                    <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
                    </svg>
                  </div>
                </div>
                <!-- Labels -->
                <span class="absolute top-2 left-2 text-xs font-bold text-white bg-black/50 px-2 py-0.5 rounded">Vorher</span>
                <span class="absolute top-2 right-2 text-xs font-bold text-white bg-black/50 px-2 py-0.5 rounded">Nachher</span>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
            <button
              @click="closeModal"
              class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white transition-colors"
            >
              Abbrechen
            </button>
            <button
              v-if="editedImageUrl"
              @click="useEditedImage"
              data-testid="use-edited-btn"
              class="px-5 py-2 text-sm font-semibold text-white bg-[#4C8BC2] rounded-lg hover:bg-blue-600 transition-colors"
            >
              ✅ Bearbeitetes Bild verwenden
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
