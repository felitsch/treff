<script setup>
/**
 * ThumbnailAISuggestions — AI-powered video thumbnail generator
 *
 * Features:
 * 1. AI Frame Extraction: Send video to backend, get 5-8 best frames
 * 2. Frame Grid: Clickable thumbnail grid sorted by quality score
 * 3. Text Overlay Editor: Headline, subtext, position, font, color
 * 4. A/B Variants: 2-3 different thumbnail designs per frame
 * 5. Filter Controls: Brightness, contrast adjustments
 * 6. Export: PNG in 1080x1080 or 1080x1920
 */
import { ref, computed, watch } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import AppIcon from '@/components/icons/AppIcon.vue'

const toast = useToast()

const props = defineProps({
  videoAsset: { type: Object, default: null },
})

const emit = defineEmits(['thumbnail-selected'])

// ─── State ──────────────────────────────────────────────────
const extracting = ref(false)
const frames = ref([])
const selectedFrame = ref(null)
const totalDuration = ref(0)

// Text overlay config
const overlayConfig = ref({
  headline: '',
  subtext: '',
  position: 'center', // top, center, bottom
  fontFamily: 'Inter',
  fontSize: 48,
  textColor: '#FFFFFF',
  bgColor: '#000000',
  bgOpacity: 0.6,
})

// Filter config
const filterConfig = ref({
  brightness: 1.0,
  contrast: 1.0,
})

// Variants
const generatingVariants = ref(false)
const variants = ref([])
const selectedVariant = ref(null)

// Export
const exportSize = ref('1080x1080')
const exporting = ref(false)

// ─── Frame extraction ───────────────────────────────────────
async function extractFrames() {
  if (!props.videoAsset) return
  extracting.value = true
  frames.value = []
  selectedFrame.value = null
  variants.value = []
  selectedVariant.value = null

  try {
    const { data } = await api.post('/api/video/thumbnails/extract-frames', {
      asset_id: props.videoAsset.id,
      frame_count: 8,
    })
    frames.value = data.frames || []
    totalDuration.value = data.total_duration || 0
    toast.success(`${frames.value.length} Frames extrahiert!`)

    // Auto-select best frame
    if (frames.value.length > 0) {
      selectFrame(frames.value[0])
    }
  } catch (err) {
    toast.error('Frame-Extraktion fehlgeschlagen.')
    console.error('Frame extraction error:', err)
  } finally {
    extracting.value = false
  }
}

function selectFrame(frame) {
  selectedFrame.value = frame
  variants.value = []
  selectedVariant.value = null
}

function formatTimestamp(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

// ─── Variant generation ─────────────────────────────────────
async function generateVariants() {
  if (!selectedFrame.value) return
  generatingVariants.value = true
  variants.value = []
  selectedVariant.value = null

  try {
    const { data } = await api.post('/api/video/thumbnails/generate-variants', {
      asset_id: props.videoAsset.id,
      frame_filename: selectedFrame.value.filename,
      headline: overlayConfig.value.headline,
      subtext: overlayConfig.value.subtext,
      position: overlayConfig.value.position,
      font_family: overlayConfig.value.fontFamily,
      font_size: overlayConfig.value.fontSize,
      text_color: overlayConfig.value.textColor,
      bg_color: overlayConfig.value.bgColor,
      bg_opacity: overlayConfig.value.bgOpacity,
      brightness: filterConfig.value.brightness,
      contrast: filterConfig.value.contrast,
      variant_count: 3,
    })
    variants.value = data.variants || []
    toast.success(`${variants.value.length} Varianten generiert!`)

    if (variants.value.length > 0) {
      selectedVariant.value = variants.value[0]
    }
  } catch (err) {
    toast.error('Varianten-Generierung fehlgeschlagen.')
    console.error('Variant generation error:', err)
  } finally {
    generatingVariants.value = false
  }
}

// ─── Export ──────────────────────────────────────────────────
async function exportThumbnail() {
  const sourceFile = selectedVariant.value?.filename || selectedFrame.value?.filename
  if (!sourceFile) return

  exporting.value = true
  try {
    const response = await api.post('/api/video/thumbnails/export', {
      source_filename: sourceFile,
      size: exportSize.value,
    }, { responseType: 'blob' })

    const url = URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `treff-thumbnail-${exportSize.value}.png`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Thumbnail exportiert!')

    emit('thumbnail-selected', {
      filename: sourceFile,
      size: exportSize.value,
    })
  } catch (err) {
    toast.error('Export fehlgeschlagen.')
  } finally {
    exporting.value = false
  }
}

// Font options
const fontOptions = [
  { value: 'Inter', label: 'Inter' },
  { value: 'Helvetica', label: 'Helvetica' },
  { value: 'Georgia', label: 'Georgia' },
  { value: 'monospace', label: 'Monospace' },
]

const positionOptions = [
  { value: 'top', label: 'Oben', icon: 'arrow-up-tray' },
  { value: 'center', label: 'Mitte', icon: 'adjustments' },
  { value: 'bottom', label: 'Unten', icon: 'arrow-down-tray' },
]

const exportSizes = [
  { value: '1080x1080', label: '1080x1080 (Feed)', icon: 'photo' },
  { value: '1080x1920', label: '1080x1920 (Reel/Story)', icon: 'device-mobile' },
]

// Auto-extract when video changes
watch(() => props.videoAsset, (asset) => {
  if (asset) {
    frames.value = []
    selectedFrame.value = null
    variants.value = []
  }
})
</script>

<template>
  <div class="space-y-5" data-testid="thumbnail-ai-suggestions">
    <!-- No video -->
    <div v-if="!videoAsset" class="text-center py-8 text-sm text-gray-500 dark:text-gray-400">
      Bitte wähle zuerst ein Video aus (Schritt 1).
    </div>

    <template v-else>
      <!-- Extract button -->
      <div v-if="frames.length === 0 && !extracting">
        <button
          @click="extractFrames"
          class="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold transition-all flex items-center justify-center gap-2"
          data-testid="extract-frames-button"
        >
          <AppIcon name="sparkles" class="w-5 h-5" /> Beste Frames extrahieren (AI)
        </button>
        <p class="text-xs text-gray-500 dark:text-gray-400 text-center mt-2">
          Extrahiert 5-8 der besten Frames aus dem Video für Thumbnails.
        </p>
      </div>

      <!-- Extracting progress -->
      <div v-if="extracting" class="text-center py-6">
        <div class="animate-spin w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full mx-auto mb-3" />
        <p class="text-sm text-gray-600 dark:text-gray-400">Frames werden extrahiert...</p>
      </div>

      <!-- Frame grid -->
      <div v-if="frames.length > 0" class="space-y-3">
        <div class="flex items-center justify-between">
          <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300">
            {{ frames.length }} Frames (sortiert nach Qualitaet)
          </h4>
          <button
            @click="extractFrames"
            class="text-xs text-blue-600 dark:text-blue-400 hover:underline"
          >
            Neu extrahieren
          </button>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2" data-testid="frame-grid">
          <button
            v-for="frame in frames"
            :key="frame.frame_index"
            @click="selectFrame(frame)"
            :class="[
              'relative rounded-lg overflow-hidden border-2 transition-all group',
              selectedFrame?.frame_index === frame.frame_index
                ? 'border-blue-500 ring-2 ring-blue-300'
                : 'border-gray-200 dark:border-gray-700 hover:border-blue-300',
            ]"
            data-testid="frame-item"
          >
            <img
              :src="frame.url"
              :alt="`Frame ${frame.frame_index + 1}`"
              class="w-full aspect-video object-cover"
              loading="lazy"
            />
            <!-- Score badge -->
            <div class="absolute top-1 right-1 bg-black/60 text-white text-[10px] px-1.5 py-0.5 rounded-full">
              {{ Math.round(frame.score * 100) }}%
            </div>
            <!-- Timestamp -->
            <div class="absolute bottom-1 left-1 bg-black/60 text-white text-[10px] px-1.5 py-0.5 rounded-full">
              {{ formatTimestamp(frame.timestamp) }}
            </div>
            <!-- Selected indicator -->
            <div
              v-if="selectedFrame?.frame_index === frame.frame_index"
              class="absolute inset-0 bg-blue-500/20 flex items-center justify-center"
            >
              <span class="text-white text-xl font-bold bg-blue-500 rounded-full w-8 h-8 flex items-center justify-center">&#10003;</span>
            </div>
          </button>
        </div>
      </div>

      <!-- Selected frame editor -->
      <div v-if="selectedFrame" class="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 space-y-4" data-testid="frame-editor">
        <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300">
          Text-Overlay Editor — Frame {{ selectedFrame.frame_index + 1 }}
        </h4>

        <!-- Text fields -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Headline</label>
            <input
              v-model="overlayConfig.headline"
              type="text"
              placeholder="z.B. Mein Auslandsjahr"
              class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Subtext</label>
            <input
              v-model="overlayConfig.subtext"
              type="text"
              placeholder="z.B. 12 Monate in den USA"
              class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <!-- Position -->
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Position</label>
          <div class="flex gap-2">
            <button
              v-for="pos in positionOptions"
              :key="pos.value"
              @click="overlayConfig.position = pos.value"
              :class="[
                'flex-1 px-3 py-2 rounded-lg text-xs font-medium text-center transition-all flex items-center justify-center gap-1',
                overlayConfig.position === pos.value
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 ring-1 ring-blue-300'
                  : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200',
              ]"
            >
              <AppIcon :name="pos.icon" class="w-4 h-4" /> {{ pos.label }}
            </button>
          </div>
        </div>

        <!-- Font & Size & Colors -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div>
            <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Schrift</label>
            <select
              v-model="overlayConfig.fontFamily"
              class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option v-for="f in fontOptions" :key="f.value" :value="f.value">{{ f.label }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Groesse ({{ overlayConfig.fontSize }}px)</label>
            <input v-model.number="overlayConfig.fontSize" type="range" min="24" max="72" class="w-full accent-blue-500" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Textfarbe</label>
            <input v-model="overlayConfig.textColor" type="color" class="w-8 h-8 rounded cursor-pointer border-0" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Hintergrund</label>
            <input v-model="overlayConfig.bgColor" type="color" class="w-8 h-8 rounded cursor-pointer border-0" />
          </div>
        </div>

        <!-- Filters -->
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
              Helligkeit ({{ Math.round(filterConfig.brightness * 100) }}%)
            </label>
            <input v-model.number="filterConfig.brightness" type="range" min="0.5" max="1.5" step="0.05" class="w-full accent-blue-500" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
              Kontrast ({{ Math.round(filterConfig.contrast * 100) }}%)
            </label>
            <input v-model.number="filterConfig.contrast" type="range" min="0.5" max="2.0" step="0.05" class="w-full accent-blue-500" />
          </div>
        </div>

        <!-- Generate variants button -->
        <button
          @click="generateVariants"
          :disabled="generatingVariants"
          class="w-full py-2.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-sm font-bold transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          data-testid="generate-variants-button"
        >
          <template v-if="generatingVariants">
            <div class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
            Varianten werden generiert...
          </template>
          <template v-else>
            <AppIcon name="paint-brush" class="w-5 h-5" /> A/B-Varianten generieren ({{ overlayConfig.headline ? 'mit Text' : 'ohne Text' }})
          </template>
        </button>
      </div>

      <!-- Variants grid -->
      <div v-if="variants.length > 0" class="space-y-3" data-testid="variants-section">
        <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300">
          {{ variants.length }} A/B-Varianten
        </h4>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <button
            v-for="variant in variants"
            :key="variant.variant_index"
            @click="selectedVariant = variant"
            :class="[
              'relative rounded-xl overflow-hidden border-2 transition-all',
              selectedVariant?.variant_index === variant.variant_index
                ? 'border-blue-500 ring-2 ring-blue-300'
                : 'border-gray-200 dark:border-gray-700 hover:border-blue-300',
            ]"
            data-testid="variant-card"
          >
            <img
              :src="variant.url"
              :alt="`Variante ${variant.variant_index + 1}: ${variant.style}`"
              class="w-full aspect-square object-cover"
              loading="lazy"
            />
            <div class="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/70 to-transparent p-3">
              <p class="text-white text-sm font-medium">{{ variant.style }}</p>
              <p class="text-white/70 text-xs">Variante {{ variant.variant_index + 1 }}</p>
            </div>
            <!-- Selected indicator -->
            <div
              v-if="selectedVariant?.variant_index === variant.variant_index"
              class="absolute top-2 right-2 bg-blue-500 text-white w-6 h-6 rounded-full flex items-center justify-center text-xs"
            >
              &#10003;
            </div>
          </button>
        </div>
      </div>

      <!-- Export section -->
      <div v-if="selectedFrame || selectedVariant" class="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 space-y-3" data-testid="export-section">
        <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Thumbnail exportieren</h4>

        <!-- Size selection -->
        <div class="flex gap-2">
          <button
            v-for="size in exportSizes"
            :key="size.value"
            @click="exportSize = size.value"
            :class="[
              'flex-1 px-3 py-2 rounded-lg text-xs font-medium text-center transition-all',
              exportSize === size.value
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 ring-1 ring-blue-300'
                : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200',
            ]"
          >
            <AppIcon :name="size.icon" class="w-4 h-4 inline-block" /> {{ size.label }}
          </button>
        </div>

        <!-- Export button -->
        <button
          @click="exportThumbnail"
          :disabled="exporting"
          class="w-full py-2.5 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-bold transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          data-testid="export-thumbnail-button"
        >
          <template v-if="exporting">
            <div class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
            Wird exportiert...
          </template>
          <template v-else>
            <AppIcon name="arrow-down-tray" class="w-5 h-5" /> Als PNG exportieren ({{ exportSize }})
          </template>
        </button>
      </div>
    </template>
  </div>
</template>
