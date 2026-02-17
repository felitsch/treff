<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import HelpTooltip from '@/components/common/HelpTooltip.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { tooltipTexts } from '@/utils/tooltipTexts'
import TourSystem from '@/components/common/TourSystem.vue'
import VideoWorkflowTour from '@/components/common/VideoWorkflowTour.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const router = useRouter()
const toast = useToast()

// ---- State ----
const videoAssets = ref([])
const loadingAssets = ref(true)
const selectedAsset = ref(null)
const analyzing = ref(false)
const analysisData = ref(null)

// Export settings
const selectedAspectRatio = ref('9:16')
const selectedPlatform = ref('instagram_reel')
const quality = ref(75)
const focusX = ref(50)
const focusY = ref(50)

// Export state
const exporting = ref(false)
const exportProgress = ref(0)
const exportResult = ref(null)
const exportError = ref(null)

// Batch export state
const batchMode = ref(false)
const batchFormats = ref([])
const batchExporting = ref(false)
const batchResults = ref(null)

// Export history
const exportHistory = ref([])
const loadingHistory = ref(false)
const tourRef = ref(null)
const workflowTourRef = ref(null)

// Available formats
const aspectRatios = {
  '9:16': { width: 1080, height: 1920, label: 'Reel/TikTok (9:16)', icon: 'device-mobile' },
  '1:1': { width: 1080, height: 1080, label: 'Feed Quadrat (1:1)', icon: 'grid' },
  '4:5': { width: 1080, height: 1350, label: 'Feed Portrait (4:5)', icon: 'photo' },
}

const platformPresets = {
  instagram_reel: { label: 'Instagram Reel', aspect_ratio: '9:16', max_duration: 90, icon: 'camera' },
  instagram_feed: { label: 'Instagram Feed', aspect_ratio: '1:1', max_duration: 60, icon: 'camera' },
  instagram_feed_portrait: { label: 'Instagram Feed (Portrait)', aspect_ratio: '4:5', max_duration: 60, icon: 'camera' },
  tiktok: { label: 'TikTok', aspect_ratio: '9:16', max_duration: 180, icon: 'musical-note' },
}

// ---- Computed ----
const currentPlatform = computed(() => platformPresets[selectedPlatform.value])
const currentRatio = computed(() => aspectRatios[selectedAspectRatio.value])

const cropInfo = computed(() => {
  if (!analysisData.value) return null
  return analysisData.value.aspect_ratios[selectedAspectRatio.value]
})

const platformCompat = computed(() => {
  if (!analysisData.value) return null
  return analysisData.value.platform_compatibility[selectedPlatform.value]
})

const qualityLabel = computed(() => {
  if (quality.value >= 85) return 'Hoch'
  if (quality.value >= 60) return 'Mittel'
  if (quality.value >= 35) return 'Niedrig'
  return 'Minimal'
})

const qualityColor = computed(() => {
  if (quality.value >= 85) return 'text-green-600'
  if (quality.value >= 60) return 'text-blue-600'
  if (quality.value >= 35) return 'text-yellow-600'
  return 'text-red-600'
})

// ---- Methods ----
function formatTime(seconds) {
  if (!seconds && seconds !== 0) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// Fetch video assets
async function fetchVideoAssets() {
  loadingAssets.value = true
  try {
    const resp = await api.get('/api/assets', { params: { file_type: 'video' } })
    videoAssets.value = resp.data
  } catch (err) {
    // Error toast shown by API interceptor
  } finally {
    loadingAssets.value = false
  }
}

// Select an asset and analyze it
async function selectAsset(asset) {
  selectedAsset.value = asset
  exportResult.value = null
  exportError.value = null
  batchResults.value = null
  analyzing.value = true
  analysisData.value = null

  try {
    const resp = await api.post('/api/video-export/analyze', { asset_id: asset.id })
    analysisData.value = resp.data

    // Auto-select best platform based on source aspect ratio
    const srcRatio = resp.data.source_width / resp.data.source_height
    if (srcRatio > 0.9 && srcRatio < 1.1) {
      selectedAspectRatio.value = '1:1'
      selectedPlatform.value = 'instagram_feed'
    } else if (srcRatio < 0.7) {
      selectedAspectRatio.value = '9:16'
      selectedPlatform.value = 'instagram_reel'
    } else {
      selectedAspectRatio.value = '4:5'
      selectedPlatform.value = 'instagram_feed_portrait'
    }

    // Load export history for this asset
    fetchExportHistory(asset.id)
  } catch (err) {
    // Error toast shown by API interceptor
    toast.error('Video-Analyse fehlgeschlagen')
  } finally {
    analyzing.value = false
  }
}

// Load export history
async function fetchExportHistory(assetId) {
  loadingHistory.value = true
  try {
    const resp = await api.get('/api/video-export', { params: { asset_id: assetId } })
    exportHistory.value = resp.data
  } catch (err) {
    // Error toast shown by API interceptor
  } finally {
    loadingHistory.value = false
  }
}

// Export single format
async function exportVideo() {
  if (!selectedAsset.value || exporting.value) return

  exporting.value = true
  exportProgress.value = 5
  exportError.value = null
  exportResult.value = null

  const progressInterval = setInterval(() => {
    if (exportProgress.value < 80) {
      exportProgress.value += Math.random() * 10
    }
  }, 700)

  try {
    const resp = await api.post('/api/video-export', {
      asset_id: selectedAsset.value.id,
      aspect_ratio: selectedAspectRatio.value,
      platform: selectedPlatform.value,
      quality: quality.value,
      focus_x: focusX.value,
      focus_y: focusY.value,
    })

    clearInterval(progressInterval)
    exportProgress.value = 100

    await new Promise(resolve => setTimeout(resolve, 400))

    exportResult.value = resp.data
    toast.success(`Video exportiert als ${aspectRatios[selectedAspectRatio.value].label}!`)

    // Refresh history
    fetchExportHistory(selectedAsset.value.id)
  } catch (err) {
    clearInterval(progressInterval)
    exportProgress.value = 0
    exportError.value = err.response?.data?.detail || 'Export fehlgeschlagen'
  } finally {
    exporting.value = false
  }
}

// Batch export
function toggleBatchFormat(ratioKey, platformKey) {
  const idx = batchFormats.value.findIndex(
    f => f.aspect_ratio === ratioKey && f.platform === platformKey
  )
  if (idx >= 0) {
    batchFormats.value.splice(idx, 1)
  } else {
    batchFormats.value.push({
      aspect_ratio: ratioKey,
      platform: platformKey,
      quality: quality.value,
      focus_x: focusX.value,
      focus_y: focusY.value,
    })
  }
}

function isBatchFormatSelected(ratioKey, platformKey) {
  return batchFormats.value.some(
    f => f.aspect_ratio === ratioKey && f.platform === platformKey
  )
}

async function runBatchExport() {
  if (!selectedAsset.value || batchFormats.value.length === 0 || batchExporting.value) return

  batchExporting.value = true
  exportError.value = null
  batchResults.value = null

  try {
    const resp = await api.post('/api/video-export/batch', {
      asset_id: selectedAsset.value.id,
      formats: batchFormats.value.map(f => ({
        ...f,
        quality: quality.value,
        focus_x: focusX.value,
        focus_y: focusY.value,
      })),
    })

    batchResults.value = resp.data
    toast.success(`${resp.data.successful} von ${resp.data.total} Formaten erfolgreich exportiert!`)

    // Refresh history
    fetchExportHistory(selectedAsset.value.id)
  } catch (err) {
    exportError.value = err.response?.data?.detail || 'Batch-Export fehlgeschlagen'
  } finally {
    batchExporting.value = false
  }
}

// Download an export
function downloadExport(exp) {
  if (exp.output_path) {
    const link = document.createElement('a')
    link.href = exp.output_path
    link.download = `treff_${exp.aspect_ratio.replace(':', 'x')}_${exp.platform}.mp4`
    link.click()
  }
}

// Delete an export
async function deleteExport(exp) {
  try {
    await api.delete(`/api/video-export/${exp.id}`)
    exportHistory.value = exportHistory.value.filter(e => e.id !== exp.id)
    toast.success('Export geloescht')
  } catch (err) {
    // Error toast shown by API interceptor
  }
}

// Sync platform when aspect ratio changes
watch(selectedAspectRatio, (ratio) => {
  // Auto-select a matching platform
  if (ratio === '9:16' && !['instagram_reel', 'tiktok'].includes(selectedPlatform.value)) {
    selectedPlatform.value = 'instagram_reel'
  } else if (ratio === '1:1' && selectedPlatform.value !== 'instagram_feed') {
    selectedPlatform.value = 'instagram_feed'
  } else if (ratio === '4:5' && selectedPlatform.value !== 'instagram_feed_portrait') {
    selectedPlatform.value = 'instagram_feed_portrait'
  }
})

onMounted(() => {
  fetchVideoAssets()
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-6" data-testid="video-export-page">
    <!-- Page Header -->
    <div data-tour="ve-header" class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <AppIcon name="export" class="w-6 h-6" />
          Video-Export
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Videos fuer Instagram Reels, TikTok und Feed in optimalen Formaten exportieren
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="workflowTourRef?.startTour()"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[#4C8BC2] bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors"
          title="Video-Workflow-Tour starten"
        >
          <AppIcon name="film" class="w-3.5 h-3.5 inline-block" /> Workflow
        </button>
        <button
          @click="tourRef?.startTour()"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          title="Seiten-Tour starten"
        >
          &#10067; Tour
        </button>
        <button
          @click="batchMode = !batchMode"
          :class="[
            'px-3 py-2 text-xs font-medium rounded-lg border transition-colors',
            batchMode
              ? 'bg-purple-600 text-white border-purple-600'
              : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-purple-400'
          ]"
          data-testid="batch-mode-toggle"
        >
          <AppIcon name="archive" class="w-3.5 h-3.5 inline-block" /> {{ batchMode ? 'Batch-Modus AN' : 'Batch-Modus' }}
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- LEFT: Video Library -->
      <div class="lg:col-span-1">
        <div data-tour="ve-library" class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <h2 class="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <AppIcon name="folder" class="w-4 h-4" /> Video auswaehlen
              <span class="ml-auto text-xs font-normal text-gray-500 dark:text-gray-400" data-testid="video-count">
                {{ videoAssets.length }} Videos
              </span>
            </h2>
          </div>
          <div class="p-3 max-h-[65vh] overflow-y-auto space-y-2">
            <div v-if="loadingAssets" class="flex items-center justify-center py-8">
              <svg class="animate-spin h-6 w-6 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <EmptyState
              v-else-if="videoAssets.length === 0"
              svgIcon="film"
              title="Keine Videos vorhanden"
              description="Lade zuerst Videos in der Asset-Bibliothek hoch, um sie hier zu exportieren."
              actionLabel="Zu Assets"
              actionTo="/library/assets"
              :compact="true"
            />
            <div
              v-for="asset in videoAssets"
              :key="asset.id"
              :class="[
                'group flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors border',
                selectedAsset?.id === asset.id
                  ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700'
                  : 'hover:bg-gray-50 dark:hover:bg-gray-800 border-transparent hover:border-gray-200 dark:hover:border-gray-600'
              ]"
              @click="selectAsset(asset)"
              :data-testid="`library-video-${asset.id}`"
            >
              <div class="w-16 h-10 bg-gray-200 dark:bg-gray-700 rounded overflow-hidden flex-shrink-0 relative">
                <img v-if="asset.thumbnail_path" :src="asset.thumbnail_path" class="w-full h-full object-cover" loading="lazy" :alt="asset.original_filename || 'Video-Vorschau'" />
                <div v-else class="w-full h-full flex items-center justify-center text-gray-400 text-xs"><AppIcon name="video-camera" class="w-4 h-4" /></div>
                <span class="absolute bottom-0 right-0 bg-black/70 text-white text-[10px] px-1 rounded-tl">
                  {{ formatTime(asset.duration_seconds) }}
                </span>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">
                  {{ asset.original_filename || asset.filename }}
                </p>
                <p class="text-[10px] text-gray-400 dark:text-gray-500">
                  {{ asset.width }}x{{ asset.height }} &middot; {{ formatFileSize(asset.file_size) }}
                </p>
              </div>
              <div v-if="selectedAsset?.id === asset.id" class="text-blue-500 text-sm shrink-0">✓</div>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT: Export Controls -->
      <div class="lg:col-span-2 space-y-4">
        <!-- No video selected -->
        <div v-if="!selectedAsset && !analyzing" class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-12 text-center">
          <AppIcon name="export" class="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <h3 class="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">
            Waehle ein Video zum Exportieren
          </h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Klicke auf ein Video in der Bibliothek links, um es fuer den Export vorzubereiten.
          </p>
        </div>

        <!-- Analyzing spinner -->
        <div v-if="analyzing" class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-8 text-center">
          <svg class="animate-spin h-8 w-8 text-blue-500 mx-auto mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="text-sm text-gray-600 dark:text-gray-400">Video wird analysiert...</p>
        </div>

        <!-- Analysis & Export Controls -->
        <template v-if="selectedAsset && analysisData && !analyzing">
          <!-- Source Video Info -->
          <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4" data-testid="source-info">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <AppIcon name="video-camera" class="w-4 h-4" /> Quell-Video
            </h3>
            <div class="flex items-start gap-4">
              <div class="w-28 h-16 bg-gray-200 dark:bg-gray-700 rounded overflow-hidden flex-shrink-0 relative">
                <img loading="lazy" v-if="analysisData.thumbnail_path" :src="analysisData.thumbnail_path" class="w-full h-full object-cover" alt="Video-Vorschau" />
                <div v-else class="w-full h-full flex items-center justify-center text-gray-400"><AppIcon name="video-camera" class="w-5 h-5" /></div>
              </div>
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 flex-1 text-xs">
                <div>
                  <span class="text-gray-500 dark:text-gray-400 block">Datei</span>
                  <span class="font-medium text-gray-800 dark:text-gray-200 truncate block" data-testid="source-filename">{{ analysisData.filename }}</span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400 block">Aufloesung</span>
                  <span class="font-medium text-gray-800 dark:text-gray-200" data-testid="source-resolution">{{ analysisData.source_width }}x{{ analysisData.source_height }}</span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400 block">Dauer</span>
                  <span class="font-medium text-gray-800 dark:text-gray-200">{{ formatTime(analysisData.source_duration) }}</span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400 block">Groesse</span>
                  <span class="font-medium text-gray-800 dark:text-gray-200">{{ formatFileSize(analysisData.file_size) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Aspect Ratio Selection -->
          <div data-tour="ve-aspect-ratio" class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4" data-testid="aspect-ratio-section">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <AppIcon name="adjustments" class="w-4 h-4" /> Seitenverhaeltnis <HelpTooltip :text="tooltipTexts.video.aspectRatio" size="sm" />
            </h3>
            <div class="grid grid-cols-3 gap-3 mb-4">
              <button
                v-for="(ratio, key) in aspectRatios"
                :key="key"
                @click="selectedAspectRatio = key"
                :class="[
                  'relative flex flex-col items-center p-3 rounded-xl border-2 transition-all',
                  selectedAspectRatio === key
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-md'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500'
                ]"
                :data-testid="`ratio-btn-${key}`"
              >
                <!-- Aspect ratio visual preview -->
                <div class="mb-2 bg-gray-300 dark:bg-gray-600 rounded-sm flex items-center justify-center"
                  :style="{
                    width: key === '1:1' ? '40px' : key === '4:5' ? '32px' : '27px',
                    height: key === '1:1' ? '40px' : key === '4:5' ? '40px' : '48px',
                  }"
                >
                  <span class="text-xs text-gray-500 dark:text-gray-400">{{ key }}</span>
                </div>
                <span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ ratio.label }}</span>
                <span class="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">{{ ratio.width }}x{{ ratio.height }}</span>

                <!-- Crop indicator -->
                <div v-if="analysisData?.aspect_ratios[key]?.needs_crop" class="mt-1.5">
                  <span class="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">
                    <AppIcon name="scissors" class="w-3 h-3 inline" /> {{ analysisData.aspect_ratios[key].crop_percentage }}% Crop
                  </span>
                </div>
                <div v-else-if="analysisData" class="mt-1.5">
                  <span class="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                    ✓ Kein Crop
                  </span>
                </div>
              </button>
            </div>

            <!-- Crop Info -->
            <div v-if="cropInfo?.needs_crop" class="bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 rounded-lg p-3 text-xs" data-testid="crop-info">
              <div class="flex items-center gap-2 text-amber-700 dark:text-amber-400">
                <AppIcon name="scissors" class="w-4 h-4 inline text-amber-600 dark:text-amber-400" />
                <span>
                  <strong>{{ cropInfo.crop_direction === 'horizontal' ? 'Horizontal' : 'Vertikal' }}es Cropping</strong>:
                  {{ cropInfo.crop_percentage }}% des Bildes werden abgeschnitten.
                  Verschiebe den Fokus-Punkt um den sichtbaren Bereich anzupassen.
                </span>
              </div>
            </div>
          </div>

          <!-- Focus Point (Smart Cropping) -->
          <div v-if="cropInfo?.needs_crop" data-tour="ve-focus" class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4" data-testid="focus-point-section">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <AppIcon name="fire" class="w-4 h-4" /> Fokus-Punkt (Smart Cropping) <HelpTooltip :text="tooltipTexts.video.focusPoint" size="sm" />
            </h3>
            <p class="text-xs text-gray-500 dark:text-gray-400 mb-3">
              Bestimme den Mittelpunkt des Ausschnitts. Der sichtbare Bereich wird um diesen Punkt zentriert.
            </p>
            <div class="flex items-center gap-6">
              <!-- Focus point visual -->
              <div class="relative w-40 h-24 bg-gray-200 dark:bg-gray-700 rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600" data-testid="focus-preview">
                <img loading="lazy" v-if="analysisData.thumbnail_path" :src="analysisData.thumbnail_path" class="w-full h-full object-cover" alt="Video-Vorschau" />
                <!-- Focus indicator dot -->
                <div
                  class="absolute w-4 h-4 rounded-full bg-red-500 border-2 border-white shadow-lg transform -translate-x-1/2 -translate-y-1/2 pointer-events-none"
                  :style="{ left: focusX + '%', top: focusY + '%' }"
                ></div>
                <!-- Crop overlay visualization -->
                <div v-if="cropInfo.crop_direction === 'horizontal'" class="absolute inset-0 pointer-events-none">
                  <div class="absolute inset-y-0 left-0 bg-black/40" :style="{ width: (focusX - (100 - cropInfo.crop_percentage) / 2) + '%' }" v-if="focusX > (100 - cropInfo.crop_percentage) / 2"></div>
                </div>
              </div>
              <!-- Sliders -->
              <div class="flex-1 space-y-3">
                <label class="block">
                  <span class="text-xs text-gray-600 dark:text-gray-400">Horizontal (X): {{ Math.round(focusX) }}%</span>
                  <input
                    type="range" min="0" max="100" step="1"
                    v-model.number="focusX"
                    class="w-full h-2 mt-1 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    data-testid="focus-x-slider"
                  />
                </label>
                <label class="block">
                  <span class="text-xs text-gray-600 dark:text-gray-400">Vertikal (Y): {{ Math.round(focusY) }}%</span>
                  <input
                    type="range" min="0" max="100" step="1"
                    v-model.number="focusY"
                    class="w-full h-2 mt-1 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    data-testid="focus-y-slider"
                  />
                </label>
                <button
                  @click="focusX = 50; focusY = 50"
                  class="text-[10px] text-blue-600 hover:underline"
                >
                  Auf Mitte zuruecksetzen
                </button>
              </div>
            </div>
          </div>

          <!-- Platform Preset -->
          <div data-tour="ve-platform" class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4" data-testid="platform-section">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <AppIcon name="device-mobile" class="w-4 h-4" /> Platform-Preset
            </h3>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                v-for="(preset, key) in platformPresets"
                :key="key"
                @click="selectedPlatform = key; selectedAspectRatio = preset.aspect_ratio"
                :class="[
                  'flex flex-col items-center p-2.5 rounded-lg border transition-all text-center',
                  selectedPlatform === key
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-400'
                ]"
                :data-testid="`platform-btn-${key}`"
              >
                <AppIcon :name="preset.icon" class="w-5 h-5 mb-1" />
                <span class="text-[10px] font-medium text-gray-700 dark:text-gray-300">{{ preset.label }}</span>
                <span class="text-[10px] text-gray-400">max {{ preset.max_duration }}s</span>
              </button>
            </div>

            <!-- Duration warning -->
            <div v-if="platformCompat && !platformCompat.duration_ok" class="mt-3 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded-lg p-2.5 text-xs text-red-700 dark:text-red-400 flex items-center gap-2" data-testid="duration-warning">
              <AppIcon name="exclamation-triangle" class="w-4 h-4 inline text-red-500 shrink-0" />
              <span>
                Video ist {{ platformCompat.duration_over_by }}s zu lang fuer {{ currentPlatform.label }}.
                Es wird auf {{ platformCompat.max_duration }}s gekuerzt.
              </span>
            </div>
          </div>

          <!-- Quality Slider -->
          <div data-tour="ve-quality" class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4" data-testid="quality-section">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <AppIcon name="adjustments-vertical" class="w-4 h-4" /> Kompression: Qualitaet vs. Dateigroesse <HelpTooltip :text="tooltipTexts.video.qualitySlider" size="sm" />
            </h3>
            <div class="flex items-center gap-4">
              <span class="text-xs text-gray-400 shrink-0">Klein</span>
              <input
                type="range" min="1" max="100" step="1"
                v-model.number="quality"
                class="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
                data-testid="quality-slider"
                aria-label="Kompressionsqualitaet"
                :aria-valuenow="quality"
                aria-valuemin="1"
                aria-valuemax="100"
              />
              <span class="text-xs text-gray-400 shrink-0">Hoch</span>
            </div>
            <div class="flex items-center justify-between mt-2">
              <span class="text-xs text-gray-500 dark:text-gray-400">
                Qualitaet: <span :class="qualityColor" class="font-medium">{{ quality }}% ({{ qualityLabel }})</span>
              </span>
              <span class="text-[10px] text-gray-400">
                {{ quality >= 80 ? 'Groessere Datei, beste Qualitaet' : quality >= 50 ? 'Ausgewogen' : 'Kleine Datei, geringere Qualitaet' }}
              </span>
            </div>
          </div>

          <!-- Batch Mode: Format Selection -->
          <div v-if="batchMode" data-tour="ve-batch" class="bg-purple-50 dark:bg-purple-900/10 rounded-xl border border-purple-200 dark:border-purple-800 p-4" data-testid="batch-section">
            <h3 class="text-sm font-semibold text-purple-800 dark:text-purple-300 mb-3 flex items-center gap-2">
              <AppIcon name="archive" class="w-4 h-4" /> Batch-Export: Formate waehlen
            </h3>
            <p class="text-xs text-purple-600 dark:text-purple-400 mb-3">
              Waehle mehrere Formate aus, um das Video in allen gewuenschten Formaten gleichzeitig zu exportieren.
            </p>
            <div class="space-y-2">
              <label
                v-for="(preset, key) in platformPresets"
                :key="key"
                :class="[
                  'flex items-center gap-3 p-2.5 rounded-lg border cursor-pointer transition-colors',
                  isBatchFormatSelected(preset.aspect_ratio, key)
                    ? 'border-purple-400 bg-purple-100 dark:bg-purple-900/30'
                    : 'border-gray-200 dark:border-gray-700 hover:border-purple-300'
                ]"
              >
                <input
                  type="checkbox"
                  :checked="isBatchFormatSelected(preset.aspect_ratio, key)"
                  @change="toggleBatchFormat(preset.aspect_ratio, key)"
                  class="rounded border-purple-400 text-purple-600 focus:ring-purple-500"
                  :data-testid="`batch-checkbox-${key}`"
                />
                <AppIcon :name="preset.icon" class="w-4 h-4" />
                <div class="flex-1">
                  <span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ preset.label }}</span>
                  <span class="text-[10px] text-gray-400 ml-2">({{ preset.aspect_ratio }}, max {{ preset.max_duration }}s)</span>
                </div>
              </label>
            </div>

            <!-- Batch Export Button -->
            <button
              @click="runBatchExport"
              :disabled="batchFormats.length === 0 || batchExporting"
              class="mt-4 w-full px-4 py-2.5 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              data-testid="batch-export-btn"
            >
              <svg v-if="batchExporting" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ batchExporting ? 'Exportiere...' : `${batchFormats.length} Format${batchFormats.length !== 1 ? 'e' : ''} exportieren` }}
            </button>
          </div>

          <!-- Batch Results -->
          <div v-if="batchResults" class="bg-green-50 dark:bg-green-900/10 rounded-xl border border-green-200 dark:border-green-800 p-4" data-testid="batch-results">
            <h3 class="text-sm font-semibold text-green-800 dark:text-green-300 mb-3 flex items-center gap-2">
              <AppIcon name="check-circle" class="w-4 h-4 inline text-green-500" /> Batch-Export abgeschlossen
            </h3>
            <p class="text-xs text-green-600 dark:text-green-400 mb-3">
              {{ batchResults.successful }} von {{ batchResults.total }} Formaten erfolgreich exportiert.
            </p>
            <div class="space-y-2">
              <div
                v-for="exp in batchResults.exports"
                :key="exp.id || exp.aspect_ratio"
                class="flex items-center justify-between p-2 rounded-lg bg-white dark:bg-gray-800 border border-green-100 dark:border-green-900"
              >
                <div class="text-xs">
                  <span class="font-medium text-gray-700 dark:text-gray-300">{{ exp.aspect_ratio }}</span>
                  <span class="text-gray-400 ml-2">{{ exp.platform }}</span>
                  <span v-if="exp.output_file_size" class="text-gray-400 ml-2">{{ formatFileSize(exp.output_file_size) }}</span>
                </div>
                <div class="flex items-center gap-1">
                  <AppIcon v-if="exp.status === 'done'" name="check-circle" class="w-4 h-4 inline text-green-500" />
                  <AppIcon v-else name="x-circle" class="w-4 h-4 inline text-red-500" />
                  <button
                    v-if="exp.status === 'done' && exp.output_path"
                    @click="downloadExport(exp)"
                    class="px-2 py-1 text-[10px] font-medium text-green-700 bg-green-100 rounded hover:bg-green-200 transition-colors"
                  >
                    Download
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Export Error -->
          <div v-if="exportError" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 flex items-start gap-3" role="alert" data-testid="export-error">
            <AppIcon name="exclamation-triangle" class="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
            <div class="flex-1">
              <p class="text-sm text-red-700 dark:text-red-400 font-medium">{{ exportError }}</p>
            </div>
            <button @click="exportError = null" class="text-red-500 hover:text-red-700 text-sm" aria-label="Fehlermeldung schliessen">✕</button>
          </div>

          <!-- Export Progress -->
          <div v-if="exporting" class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-3" data-testid="export-progress">
            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-600 dark:text-gray-400 flex items-center gap-2">
                <svg class="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Video wird exportiert...
              </span>
              <span class="text-blue-600 dark:text-blue-400 font-medium">{{ Math.round(exportProgress) }}%</span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
              <div class="bg-blue-600 h-2.5 rounded-full transition-all duration-300" :style="{ width: exportProgress + '%' }"></div>
            </div>
          </div>

          <!-- Export Result -->
          <div v-if="exportResult" class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4" data-testid="export-result">
            <h3 class="text-sm font-semibold text-green-800 dark:text-green-300 mb-3 flex items-center gap-2">
              <AppIcon name="check-circle" class="w-4 h-4 inline text-green-500" /> Export erfolgreich!
            </h3>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mb-3">
              <div>
                <span class="text-green-600 dark:text-green-400 font-medium">Format:</span>
                <span class="ml-1 text-green-800 dark:text-green-200">{{ exportResult.aspect_ratio }}</span>
              </div>
              <div>
                <span class="text-green-600 dark:text-green-400 font-medium">Dauer:</span>
                <span class="ml-1 text-green-800 dark:text-green-200">{{ formatTime(exportResult.output_duration) }}</span>
              </div>
              <div>
                <span class="text-green-600 dark:text-green-400 font-medium">Aufloesung:</span>
                <span class="ml-1 text-green-800 dark:text-green-200">{{ exportResult.output_width }}x{{ exportResult.output_height }}</span>
              </div>
              <div>
                <span class="text-green-600 dark:text-green-400 font-medium">Groesse:</span>
                <span class="ml-1 text-green-800 dark:text-green-200">{{ formatFileSize(exportResult.output_file_size) }}</span>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button
                @click="downloadExport(exportResult)"
                class="px-3 py-1.5 text-xs font-medium bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-1"
                data-testid="download-export-btn"
              >
                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download MP4
              </button>
              <span class="text-[10px] text-green-600 dark:text-green-400">
                H.264/AAC &middot; {{ exportResult.platform }}
              </span>
            </div>
          </div>

          <!-- Single Export Action Bar -->
          <div v-if="!batchMode" class="flex items-center justify-end bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <button
              @click="exportVideo"
              :disabled="exporting"
              class="px-5 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2 shadow-md"
              data-testid="export-btn"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              {{ exporting ? 'Exportiere...' : `Als ${currentRatio.label} exportieren` }}
            </button>
          </div>

          <!-- Export History -->
          <div v-if="exportHistory.length > 0" data-tour="ve-history" class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden" data-testid="export-history">
            <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <AppIcon name="clipboard" class="w-4 h-4" /> Export-Verlauf
                <span class="ml-auto text-xs font-normal text-gray-400">{{ exportHistory.length }} Exporte</span>
              </h3>
            </div>
            <div class="divide-y divide-gray-100 dark:divide-gray-800 max-h-60 overflow-y-auto">
              <div
                v-for="exp in exportHistory"
                :key="exp.id"
                class="flex items-center justify-between px-4 py-2.5 hover:bg-gray-50 dark:hover:bg-gray-800/50"
              >
                <div class="flex items-center gap-3 text-xs">
                  <AppIcon v-if="exp.status === 'done'" name="check-circle" class="w-4 h-4 inline text-green-500" />
                  <AppIcon v-else name="x-circle" class="w-4 h-4 inline text-red-500" />
                  <div>
                    <span class="font-medium text-gray-700 dark:text-gray-300">{{ exp.aspect_ratio }}</span>
                    <span class="text-gray-400 ml-1.5">{{ exp.platform }}</span>
                    <span v-if="exp.output_file_size" class="text-gray-400 ml-1.5">{{ formatFileSize(exp.output_file_size) }}</span>
                    <span v-if="exp.output_duration" class="text-gray-400 ml-1.5">{{ formatTime(exp.output_duration) }}</span>
                  </div>
                </div>
                <div class="flex items-center gap-1">
                  <button
                    v-if="exp.status === 'done'"
                    @click="downloadExport(exp)"
                    class="p-1 rounded text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                    title="Download"
                  >
                    <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  </button>
                  <button
                    @click="deleteExport(exp)"
                    class="p-1 rounded text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                    title="Loeschen"
                  >
                    <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <VideoWorkflowTour ref="workflowTourRef" />
    <TourSystem ref="tourRef" page-key="video-export" />
  </div>
</template>
