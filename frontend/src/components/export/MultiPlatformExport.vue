<script setup>
/**
 * MultiPlatformExport.vue — One-Click Multi-Platform Export Modal
 *
 * Generates platform-specific versions of a post:
 * - Instagram Feed (1:1, 1080x1080)
 * - Instagram Story (9:16, 1080x1920)
 * - Instagram Portrait (4:5, 1080x1350)
 * - TikTok (9:16, 1080x1920)
 *
 * Export options: ZIP download, scheduling queue, or individual download.
 * Includes crop/resize preview per format and progress indicator.
 */
import { ref, computed, watch, onMounted } from 'vue'
import JSZip from 'jszip'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import AppIcon from '@/components/icons/AppIcon.vue'

const toast = useToast()

const props = defineProps({
  /** The source post object (must have id, platform, slide_data, etc.) */
  post: { type: Object, required: true },
  /** Parsed slides array */
  slides: { type: Array, default: () => [] },
  /** Whether the modal is visible */
  visible: { type: Boolean, default: false },
  /** Current captions */
  captionInstagram: { type: String, default: '' },
  captionTiktok: { type: String, default: '' },
  hashtagsInstagram: { type: String, default: '' },
  hashtagsTiktok: { type: String, default: '' },
})

const emit = defineEmits(['close', 'export-complete'])

// ── Format definitions ──────────────────────────────────────────
const formats = [
  {
    key: 'instagram_feed',
    label: 'Instagram Feed',
    aspect: '1:1',
    width: 1080,
    height: 1080,
    icon: 'camera',
    color: 'pink',
    previewW: 80,
    previewH: 80,
  },
  {
    key: 'instagram_story',
    label: 'Instagram Story',
    aspect: '9:16',
    width: 1080,
    height: 1920,
    icon: 'device-phone-mobile',
    color: 'purple',
    previewW: 45,
    previewH: 80,
  },
  {
    key: 'instagram_portrait',
    label: 'Instagram Portrait',
    aspect: '4:5',
    width: 1080,
    height: 1350,
    icon: 'photo',
    color: 'indigo',
    previewW: 64,
    previewH: 80,
  },
  {
    key: 'tiktok',
    label: 'TikTok',
    aspect: '9:16',
    width: 1080,
    height: 1920,
    icon: 'musical-note',
    color: 'cyan',
    previewW: 45,
    previewH: 80,
  },
]

// ── State ────────────────────────────────────────────────────────
const selectedFormats = ref(['instagram_feed'])
const adjustCaptionPerPlatform = ref(false)
const adjustHashtagsPerPlatform = ref(false)
const exporting = ref(false)
const exportProgress = ref({})
const exportResults = ref([])
const exportError = ref(null)
const exportMode = ref('zip') // 'zip', 'queue', 'individual'

// ── Computed ─────────────────────────────────────────────────────
const canExport = computed(() => {
  return selectedFormats.value.length > 0 && !exporting.value
})

const sourceFormat = computed(() => {
  const p = props.post?.platform || 'instagram_feed'
  const match = formats.find(f => f.key === p)
  return match || formats[0]
})

const totalFormats = computed(() => selectedFormats.value.length)

// ── Actions ──────────────────────────────────────────────────────
function toggleFormat(key) {
  const idx = selectedFormats.value.indexOf(key)
  if (idx >= 0) {
    selectedFormats.value.splice(idx, 1)
  } else {
    selectedFormats.value.push(key)
  }
}

function selectAllFormats() {
  selectedFormats.value = formats.map(f => f.key)
}

function deselectAllFormats() {
  selectedFormats.value = []
}

// ── Canvas rendering for export ──────────────────────────────────
function renderSlideToCanvas(slideIndex, width, height) {
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  const slide = props.slides[slideIndex]
  if (!slide) return null

  const scale = width / 1080

  // Background
  if (slide.background_type === 'color' && slide.background_value) {
    ctx.fillStyle = slide.background_value
  } else {
    ctx.fillStyle = '#1A1A2E'
  }
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  // TREFF logo bar
  ctx.fillStyle = '#3B7AB1'
  const logoW = 80 * scale
  const logoH = 28 * scale
  const logoX = 40 * scale
  const logoY = 40 * scale
  ctx.beginPath()
  ctx.roundRect(logoX, logoY, logoW, logoH, 6 * scale)
  ctx.fill()
  ctx.fillStyle = '#FFFFFF'
  ctx.font = `bold ${14 * scale}px sans-serif`
  ctx.textAlign = 'center'
  ctx.fillText('TREFF', logoX + logoW / 2, logoY + 19 * scale)

  // Headline
  if (slide.headline) {
    ctx.fillStyle = '#FFFFFF'
    ctx.font = `bold ${28 * scale}px sans-serif`
    ctx.textAlign = 'left'
    const headlineY = canvas.height * 0.4
    ctx.fillText(slide.headline, 40 * scale, headlineY, canvas.width - 80 * scale)
  }

  // Subheadline
  if (slide.subheadline) {
    ctx.fillStyle = '#FDD000'
    ctx.font = `bold ${16 * scale}px sans-serif`
    ctx.fillText(slide.subheadline, 40 * scale, canvas.height * 0.4 + 36 * scale, canvas.width - 80 * scale)
  }

  // Body text
  if (slide.body_text) {
    ctx.fillStyle = '#d1d5db'
    ctx.font = `${14 * scale}px sans-serif`
    ctx.textAlign = 'left'
    const bodyY = canvas.height * 0.4 + 70 * scale
    const words = slide.body_text.split(' ')
    let line = ''
    let y = bodyY
    const maxWidth = canvas.width - 80 * scale
    for (const word of words) {
      const test = line + word + ' '
      if (ctx.measureText(test).width > maxWidth && line) {
        ctx.fillText(line.trim(), 40 * scale, y)
        line = word + ' '
        y += 20 * scale
        if (y > canvas.height - 100 * scale) break
      } else {
        line = test
      }
    }
    if (line.trim()) ctx.fillText(line.trim(), 40 * scale, y)
  }

  // CTA button
  if (slide.cta_text) {
    const ctaY = canvas.height - 80 * scale
    ctx.fillStyle = '#FDD000'
    ctx.font = `bold ${14 * scale}px sans-serif`
    ctx.textAlign = 'center'
    const ctaW = ctx.measureText(slide.cta_text).width + 40 * scale
    ctx.beginPath()
    ctx.roundRect(40 * scale, ctaY, ctaW, 36 * scale, 18 * scale)
    ctx.fill()
    ctx.fillStyle = '#1A1A2E'
    ctx.fillText(slide.cta_text, 40 * scale + ctaW / 2, ctaY + 24 * scale)
  }

  return canvas
}

// ── Export Logic ──────────────────────────────────────────────────
async function startExport() {
  if (!canExport.value) return
  exporting.value = true
  exportError.value = null
  exportResults.value = []

  // Initialize progress
  for (const key of selectedFormats.value) {
    exportProgress.value[key] = 0
  }

  try {
    // Step 1: Record exports in backend
    const formatPayload = selectedFormats.value.map(key => {
      const fmt = formats.find(f => f.key === key)
      return {
        platform: key,
        width: fmt.width,
        height: fmt.height,
        label: `${fmt.label} (${fmt.aspect})`,
      }
    })

    // Set progress to 20%
    for (const key of selectedFormats.value) {
      exportProgress.value[key] = 20
    }

    const { data } = await api.post('/api/export/multi-platform', {
      post_id: props.post.id,
      formats: formatPayload,
      add_to_queue: exportMode.value === 'queue',
    })

    // Set progress to 50%
    for (const key of selectedFormats.value) {
      exportProgress.value[key] = 50
    }

    // Step 2: Client-side rendering for each format
    if (exportMode.value === 'zip') {
      await exportAsZip(data.exports)
    } else if (exportMode.value === 'individual') {
      await exportIndividually(data.exports)
    }

    // Set progress to 100%
    for (const key of selectedFormats.value) {
      exportProgress.value[key] = 100
    }

    exportResults.value = data.exports || []
    toast.success(`${exportResults.value.length} Plattform-Export(s) erstellt!`)
    emit('export-complete', exportResults.value)
  } catch (err) {
    exportError.value = err.response?.data?.detail || err.message || 'Export fehlgeschlagen'
    toast.error('Multi-Platform-Export fehlgeschlagen')
  } finally {
    exporting.value = false
  }
}

async function exportAsZip(exportRecords) {
  const zip = new JSZip()
  const date = new Date().toISOString().split('T')[0]

  for (const record of exportRecords) {
    const fmt = formats.find(f => f.key === record.platform)
    if (!fmt) continue

    const width = record.width || fmt.width
    const height = record.height || fmt.height

    if (props.slides.length > 1) {
      // Carousel: create subfolder per format
      const folder = zip.folder(`${fmt.label.replace(/\s+/g, '_')}_${fmt.aspect.replace(':', 'x')}`)
      for (let i = 0; i < props.slides.length; i++) {
        const canvas = renderSlideToCanvas(i, width, height)
        if (!canvas) continue
        const dataUrl = canvas.toDataURL('image/png')
        const base64 = dataUrl.split(',')[1]
        folder.file(`TREFF_${date}_slide_${String(i + 1).padStart(2, '0')}.png`, base64, { base64: true })
      }
    } else {
      const canvas = renderSlideToCanvas(0, width, height)
      if (!canvas) continue
      const dataUrl = canvas.toDataURL('image/png')
      const base64 = dataUrl.split(',')[1]
      zip.file(`TREFF_${fmt.label.replace(/\s+/g, '_')}_${fmt.aspect.replace(':', 'x')}_${date}.png`, base64, { base64: true })
    }

    // Update progress per format
    exportProgress.value[record.platform] = 80
  }

  // Generate and download ZIP
  const content = await zip.generateAsync({ type: 'blob' })
  const link = document.createElement('a')
  link.download = `TREFF_MultiPlatform_${date}.zip`
  link.href = URL.createObjectURL(content)
  link.click()
  URL.revokeObjectURL(link.href)
}

async function exportIndividually(exportRecords) {
  const date = new Date().toISOString().split('T')[0]

  for (const record of exportRecords) {
    const fmt = formats.find(f => f.key === record.platform)
    if (!fmt) continue

    const width = record.width || fmt.width
    const height = record.height || fmt.height
    const canvas = renderSlideToCanvas(0, width, height)
    if (!canvas) continue

    const link = document.createElement('a')
    link.download = `TREFF_${fmt.label.replace(/\s+/g, '_')}_${fmt.aspect.replace(':', 'x')}_${date}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()

    exportProgress.value[record.platform] = 80
    // Small delay between downloads
    await new Promise(resolve => setTimeout(resolve, 300))
  }
}

function downloadSingleFormat(record) {
  const fmt = formats.find(f => f.key === record.platform)
  if (!fmt) return

  const date = new Date().toISOString().split('T')[0]
  const width = record.width || fmt.width
  const height = record.height || fmt.height
  const canvas = renderSlideToCanvas(0, width, height)
  if (!canvas) return

  const link = document.createElement('a')
  link.download = `TREFF_${fmt.label.replace(/\s+/g, '_')}_${fmt.aspect.replace(':', 'x')}_${date}.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
  toast.success(`${fmt.label} heruntergeladen`)
}

function resetExport() {
  exportResults.value = []
  exportError.value = null
  exportProgress.value = {}
}

// Color mapping for format badges
function getFormatColorClass(color, isSelected) {
  const colors = {
    pink: isSelected ? 'border-pink-500 bg-pink-50 dark:bg-pink-900/20 ring-1 ring-pink-300' : 'border-gray-200 dark:border-gray-700 hover:border-pink-300',
    purple: isSelected ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20 ring-1 ring-purple-300' : 'border-gray-200 dark:border-gray-700 hover:border-purple-300',
    indigo: isSelected ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20 ring-1 ring-indigo-300' : 'border-gray-200 dark:border-gray-700 hover:border-indigo-300',
    cyan: isSelected ? 'border-cyan-500 bg-cyan-50 dark:bg-cyan-900/20 ring-1 ring-cyan-300' : 'border-gray-200 dark:border-gray-700 hover:border-cyan-300',
  }
  return colors[color] || colors.pink
}

function getCheckboxColorClass(color) {
  const colors = {
    pink: 'bg-pink-500 border-pink-500',
    purple: 'bg-purple-500 border-purple-500',
    indigo: 'bg-indigo-500 border-indigo-500',
    cyan: 'bg-cyan-500 border-cyan-500',
  }
  return colors[color] || 'bg-blue-500 border-blue-500'
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      @click.self="$emit('close')"
      data-testid="multi-platform-export-modal"
    >
      <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto mx-4">
        <!-- Header -->
        <div class="flex items-center justify-between px-6 pt-5 pb-3 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <AppIcon name="export" class="w-5 h-5" />
              Multi-Platform Export
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
              Ein Post, alle Plattform-Formate — mit einem Klick
            </p>
          </div>
          <button
            @click="$emit('close')"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
            data-testid="close-export-modal"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div class="p-6 space-y-6">
          <!-- Source post info -->
          <div class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
            <div class="w-10 h-10 rounded-lg bg-[#3B7AB1]/10 flex items-center justify-center">
              <AppIcon name="document-text" class="w-5 h-5 text-[#3B7AB1]" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                {{ post.title || slides[0]?.headline || 'Post' }}
                <span class="text-gray-400 font-normal">#{{ post.id }}</span>
              </p>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                Aktuelles Format: <strong>{{ sourceFormat.label }} ({{ sourceFormat.aspect }})</strong>
                &middot; {{ slides.length }} Slide{{ slides.length !== 1 ? 's' : '' }}
              </p>
            </div>
          </div>

          <!-- Export results (shown after export) -->
          <div v-if="exportResults.length > 0" class="space-y-3" data-testid="export-results">
            <div class="flex items-center gap-2 text-green-600 dark:text-green-400">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <h3 class="text-sm font-bold">{{ exportResults.length }} Exporte erfolgreich erstellt!</h3>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div
                v-for="(result, idx) in exportResults"
                :key="idx"
                class="flex items-center gap-3 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg"
              >
                <span class="text-green-500 text-lg">&#10003;</span>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ result.label || result.platform }}</p>
                  <p class="text-xs text-gray-500">{{ result.resolution }}</p>
                </div>
                <button
                  @click="downloadSingleFormat(result)"
                  class="px-2.5 py-1.5 text-xs font-medium bg-[#3B7AB1] text-white rounded-lg hover:bg-[#2E6A9E] transition-all whitespace-nowrap"
                  data-testid="download-single-btn"
                >
                  <AppIcon name="download" class="w-3 h-3 inline-block" />
                </button>
              </div>
            </div>

            <div class="flex gap-3 pt-2">
              <button
                @click="resetExport"
                class="flex-1 px-4 py-2.5 text-sm font-medium border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                Weitere Exporte
              </button>
              <button
                @click="$emit('close')"
                class="flex-1 px-4 py-2.5 text-sm font-bold bg-[#3B7AB1] text-white rounded-lg hover:bg-[#2E6A9E] transition-colors"
              >
                Fertig
              </button>
            </div>
          </div>

          <!-- Format selection (before export) -->
          <template v-else>
            <!-- Target formats -->
            <div>
              <div class="flex items-center justify-between mb-3">
                <label class="text-sm font-semibold text-gray-700 dark:text-gray-300">Ziel-Formate</label>
                <div class="flex gap-2">
                  <button
                    @click="selectAllFormats"
                    class="text-xs text-[#3B7AB1] hover:text-[#2E6A9E] font-medium"
                    data-testid="select-all-formats"
                  >
                    Alle auswählen
                  </button>
                  <span class="text-gray-300 dark:text-gray-600">|</span>
                  <button
                    @click="deselectAllFormats"
                    class="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 font-medium"
                  >
                    Keine
                  </button>
                </div>
              </div>

              <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <button
                  v-for="fmt in formats"
                  :key="fmt.key"
                  @click="toggleFormat(fmt.key)"
                  :class="[
                    'relative flex flex-col items-center p-4 rounded-xl border-2 transition-all cursor-pointer',
                    getFormatColorClass(fmt.color, selectedFormats.includes(fmt.key)),
                  ]"
                  :data-testid="'format-' + fmt.key"
                >
                  <!-- Checkbox -->
                  <div :class="[
                    'absolute top-2 right-2 w-5 h-5 rounded border-2 flex items-center justify-center transition-all',
                    selectedFormats.includes(fmt.key)
                      ? getCheckboxColorClass(fmt.color)
                      : 'border-gray-300 dark:border-gray-600',
                  ]">
                    <span v-if="selectedFormats.includes(fmt.key)" class="text-white text-xs font-bold">&#10003;</span>
                  </div>

                  <!-- Aspect ratio preview box -->
                  <div
                    class="border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-700 rounded mb-2 flex items-center justify-center text-[8px] text-gray-400"
                    :style="{ width: fmt.previewW + 'px', height: fmt.previewH + 'px' }"
                  >
                    {{ fmt.aspect }}
                  </div>

                  <AppIcon :name="fmt.icon" class="w-5 h-5 mb-1 text-gray-600 dark:text-gray-400" />
                  <p class="text-xs font-semibold text-gray-900 dark:text-white text-center">{{ fmt.label }}</p>
                  <p class="text-[10px] text-gray-500 dark:text-gray-400">{{ fmt.width }}x{{ fmt.height }}</p>
                </button>
              </div>
            </div>

            <!-- Options -->
            <div class="space-y-3 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl">
              <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Optionen</h4>

              <label class="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  v-model="adjustCaptionPerPlatform"
                  class="h-4 w-4 rounded border-gray-300 text-[#3B7AB1] focus:ring-[#3B7AB1]"
                />
                <span class="text-sm text-gray-700 dark:text-gray-300">Caption pro Plattform anpassen</span>
              </label>

              <label class="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  v-model="adjustHashtagsPerPlatform"
                  class="h-4 w-4 rounded border-gray-300 text-[#3B7AB1] focus:ring-[#3B7AB1]"
                />
                <span class="text-sm text-gray-700 dark:text-gray-300">Hashtags pro Plattform anpassen</span>
              </label>
            </div>

            <!-- Export mode -->
            <div>
              <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Export-Art</label>
              <div class="grid grid-cols-3 gap-2">
                <button
                  @click="exportMode = 'zip'"
                  :class="[
                    'flex flex-col items-center p-3 rounded-lg border-2 text-xs transition-all',
                    exportMode === 'zip'
                      ? 'border-[#3B7AB1] bg-[#3B7AB1]/5 text-[#3B7AB1] font-bold'
                      : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-gray-400',
                  ]"
                  data-testid="export-mode-zip"
                >
                  <AppIcon name="archive" class="w-5 h-5 mb-1" />
                  ZIP-Download
                </button>
                <button
                  @click="exportMode = 'queue'"
                  :class="[
                    'flex flex-col items-center p-3 rounded-lg border-2 text-xs transition-all',
                    exportMode === 'queue'
                      ? 'border-[#3B7AB1] bg-[#3B7AB1]/5 text-[#3B7AB1] font-bold'
                      : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-gray-400',
                  ]"
                  data-testid="export-mode-queue"
                >
                  <AppIcon name="calendar" class="w-5 h-5 mb-1" />
                  In Queue legen
                </button>
                <button
                  @click="exportMode = 'individual'"
                  :class="[
                    'flex flex-col items-center p-3 rounded-lg border-2 text-xs transition-all',
                    exportMode === 'individual'
                      ? 'border-[#3B7AB1] bg-[#3B7AB1]/5 text-[#3B7AB1] font-bold'
                      : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-gray-400',
                  ]"
                  data-testid="export-mode-individual"
                >
                  <AppIcon name="download" class="w-5 h-5 mb-1" />
                  Einzeln laden
                </button>
              </div>
            </div>

            <!-- Progress indicator -->
            <div v-if="exporting" class="space-y-2" data-testid="export-progress">
              <div v-for="key in selectedFormats" :key="key" class="flex items-center gap-3">
                <span class="text-xs text-gray-600 dark:text-gray-400 w-28 truncate">
                  {{ formats.find(f => f.key === key)?.label || key }}
                </span>
                <div class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    class="bg-[#3B7AB1] h-2 rounded-full transition-all duration-300"
                    :style="{ width: `${exportProgress[key] || 0}%` }"
                  />
                </div>
                <span class="text-xs text-gray-500 w-10 text-right">{{ exportProgress[key] || 0 }}%</span>
              </div>
            </div>

            <!-- Error -->
            <div v-if="exportError" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p class="text-sm text-red-700 dark:text-red-400">{{ exportError }}</p>
            </div>

            <!-- Export button -->
            <button
              @click="startExport"
              :disabled="!canExport"
              :class="[
                'w-full py-3.5 rounded-xl text-sm font-bold transition-all flex items-center justify-center gap-2',
                canExport
                  ? 'bg-[#3B7AB1] hover:bg-[#2E6A9E] text-white shadow-lg shadow-[#3B7AB1]/20 hover:shadow-xl'
                  : 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed',
              ]"
              data-testid="export-all-btn"
            >
              <template v-if="exporting">
                <div class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                Wird exportiert...
              </template>
              <template v-else>
                <AppIcon name="export" class="w-5 h-5" />
                Alle exportieren ({{ totalFormats }} Format{{ totalFormats !== 1 ? 'e' : '' }})
              </template>
            </button>
          </template>
        </div>
      </div>
    </div>
  </Teleport>
</template>
