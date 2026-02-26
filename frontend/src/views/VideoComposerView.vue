<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import draggable from 'vuedraggable'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import EmptyState from '@/components/common/EmptyState.vue'
import TourSystem from '@/components/common/TourSystem.vue'
import VideoWorkflowTour from '@/components/common/VideoWorkflowTour.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const router = useRouter()
const toast = useToast()
const workflowTourRef = ref(null)

// ---- State ----
const loading = ref(false)
const videoAssets = ref([])
const loadingAssets = ref(true)

// Timeline clips
const clips = ref([])

// Transition options
const transitionTypes = [
  { value: 'cut', label: 'Cut', icon: '|' },
  { value: 'fade', label: 'Fade', icon: '~' },
  { value: 'crossdissolve', label: 'Cross-Dissolve', icon: '><' },
]

// Output format
const outputFormat = ref('9:16')
const outputFormats = {
  '9:16': { width: 1080, height: 1920, label: 'Reel/TikTok (9:16)' },
  '4:5': { width: 1080, height: 1350, label: 'Feed (4:5)' },
  '1:1': { width: 1080, height: 1080, label: 'Quadrat (1:1)' },
  '16:9': { width: 1920, height: 1080, label: 'Landscape (16:9)' },
}

// Preview state
const previewData = ref(null)
const previewLoading = ref(false)

// Compose state
const composing = ref(false)
const composeProgress = ref(0)
const composeResult = ref(null)
const composeError = ref(null)

// Preview video playback
const previewVideoEl = ref(null)
const showPreviewModal = ref(false)

// Save as asset toggle
const saveAsAsset = ref(true)

// ---- Computed ----
const totalDuration = computed(() => {
  let total = 0
  for (const clip of clips.value) {
    const dur = clipDuration(clip)
    total += dur
  }
  // Subtract transition overlaps
  for (let i = 1; i < clips.value.length; i++) {
    const c = clips.value[i]
    if (c.transition !== 'cut') {
      total -= c.transitionDuration
    }
  }
  return Math.max(0, total)
})

const canCompose = computed(() => {
  return clips.value.length >= 1 && !composing.value && totalDuration.value > 0
})

// ---- Methods ----
function clipDuration(clip) {
  const end = clip.trimEnd ?? clip.assetDuration
  return Math.max(0, end - clip.trimStart)
}

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

// Fetch user's video assets
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

// Add a video asset to the timeline
function addClip(asset) {
  clips.value.push({
    id: Date.now() + Math.random(),
    assetId: asset.id,
    filename: asset.original_filename || asset.filename,
    filePath: asset.file_path,
    thumbnailPath: asset.thumbnail_path,
    assetDuration: asset.duration_seconds || 0,
    width: asset.width,
    height: asset.height,
    trimStart: 0,
    trimEnd: asset.duration_seconds || 0,
    transition: 'cut',
    transitionDuration: 0.5,
  })
  toast.success(`Clip "${asset.original_filename || asset.filename}" hinzugefügt`)
}

// Remove a clip from timeline
function removeClip(index) {
  clips.value.splice(index, 1)
}

// Duplicate a clip
function duplicateClip(index) {
  const original = clips.value[index]
  const copy = { ...original, id: Date.now() + Math.random() }
  clips.value.splice(index + 1, 0, copy)
}

// Set transition for a clip
function setTransition(index, type) {
  if (index > 0) {
    clips.value[index].transition = type
  }
}

// Update trim for a clip
function updateTrimStart(index, value) {
  const val = parseFloat(value)
  if (!isNaN(val) && val >= 0 && val < clips.value[index].trimEnd - 0.1) {
    clips.value[index].trimStart = val
  }
}

function updateTrimEnd(index, value) {
  const val = parseFloat(value)
  if (!isNaN(val) && val > clips.value[index].trimStart + 0.1 && val <= clips.value[index].assetDuration) {
    clips.value[index].trimEnd = val
  }
}

function updateTransitionDuration(index, value) {
  const val = parseFloat(value)
  if (!isNaN(val) && val >= 0.1 && val <= 3.0) {
    clips.value[index].transitionDuration = val
  }
}

// Fetch preview metadata
async function fetchPreview() {
  if (clips.value.length === 0) {
    previewData.value = null
    return
  }
  previewLoading.value = true
  try {
    const resp = await api.post('/api/video-composer/preview', {
      clips: clips.value.map(c => ({
        asset_id: c.assetId,
        trim_start: c.trimStart,
        trim_end: c.trimEnd,
        transition: c.transition,
        transition_duration: c.transitionDuration,
      })),
      output_format: outputFormat.value,
    })
    previewData.value = resp.data
  } catch (err) {
    // Error toast shown by API interceptor
    previewData.value = null
  } finally {
    previewLoading.value = false
  }
}

// Compose the video
async function composeVideo() {
  if (!canCompose.value) return

  composing.value = true
  composeProgress.value = 5
  composeError.value = null
  composeResult.value = null

  // Simulate progress
  const progressInterval = setInterval(() => {
    if (composeProgress.value < 85) {
      composeProgress.value += Math.random() * 8
    }
  }, 800)

  try {
    const resp = await api.post('/api/video-composer/compose', {
      clips: clips.value.map(c => ({
        asset_id: c.assetId,
        trim_start: c.trimStart,
        trim_end: c.trimEnd,
        transition: c.transition,
        transition_duration: c.transitionDuration,
      })),
      output_format: outputFormat.value,
      save_as_asset: saveAsAsset.value,
    })

    clearInterval(progressInterval)
    composeProgress.value = 100

    await new Promise(resolve => setTimeout(resolve, 500))

    composeResult.value = resp.data
    toast.success(`Video zusammengeschnitten! (${clips.value.length} Clips)`)
  } catch (err) {
    clearInterval(progressInterval)
    composeProgress.value = 0
    composeError.value = err.response?.data?.detail || 'Video-Zusammenschnitt fehlgeschlagen'
  } finally {
    composing.value = false
  }
}

// Open preview modal for composed result
function openResultPreview() {
  if (composeResult.value?.file_path) {
    showPreviewModal.value = true
  }
}

// Close preview modal
function closePreviewModal() {
  showPreviewModal.value = false
  if (previewVideoEl.value) {
    previewVideoEl.value.pause()
  }
}

// Download composed video
function downloadResult() {
  if (composeResult.value?.file_path) {
    const link = document.createElement('a')
    link.href = composeResult.value.file_path
    link.download = `composed_video_${outputFormat.value}.mp4`
    link.click()
  }
}

// Reset composer
function resetComposer() {
  clips.value = []
  previewData.value = null
  composeResult.value = null
  composeError.value = null
  composeProgress.value = 0
}

// Debounced preview refresh
let previewTimeout = null
watch([clips, outputFormat], () => {
  if (previewTimeout) clearTimeout(previewTimeout)
  previewTimeout = setTimeout(fetchPreview, 600)
}, { deep: true })

onMounted(() => {
  fetchVideoAssets()
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-6" data-testid="video-composer-page">
    <!-- Page header -->
    <div data-tour="vc-header" class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <AppIcon name="film" class="w-7 h-7" />
          Video-Zusammenschnitt
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Mehrere Clips zu einem Reel oder TikTok zusammenfügen
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="workflowTourRef?.startTour()"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[#4C8BC2] bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors"
          title="Video-Workflow-Tour starten"
        >
          <AppIcon name="film" class="w-4 h-4 inline-block" /> Workflow
        </button>
        <router-link
          to="/video/templates"
          class="px-3 py-2 text-sm font-medium text-treff-blue bg-treff-blue/10 rounded-lg hover:bg-treff-blue/20 transition-colors flex items-center gap-1.5"
          data-testid="branding-templates-link"
          data-tour="vc-branding-link"
        >
          <AppIcon name="tag" class="w-4 h-4" /> Intro/Outro Branding
        </router-link>
        <button
          v-if="clips.length > 0"
          @click="resetComposer"
          class="px-3 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          data-testid="reset-composer-btn"
        >
          Zurücksetzen
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- LEFT: Clip Library -->
      <div class="lg:col-span-1">
        <div data-tour="vc-library" class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <h2 class="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <AppIcon name="archive" class="w-4 h-4" /> Video-Bibliothek
              <span class="ml-auto text-xs font-normal text-gray-500 dark:text-gray-400" data-testid="video-count">
                {{ videoAssets.length }} Videos
              </span>
            </h2>
          </div>

          <div class="p-3 max-h-[60vh] overflow-y-auto space-y-2">
            <!-- Loading -->
            <div v-if="loadingAssets" class="flex items-center justify-center py-8">
              <svg class="animate-spin h-6 w-6 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>

            <!-- No videos -->
            <EmptyState
              v-else-if="videoAssets.length === 0"
              svgIcon="film"
              title="Keine Videos vorhanden"
              description="Lade zuerst Videos in der Asset-Bibliothek hoch, um sie hier zu schneiden."
              actionLabel="Zu Assets"
              actionTo="/library/assets"
              :compact="true"
            />

            <!-- Video list -->
            <div
              v-for="asset in videoAssets"
              :key="asset.id"
              class="group flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors border border-transparent hover:border-gray-200 dark:hover:border-gray-600"
              @click="addClip(asset)"
              :data-testid="`library-video-${asset.id}`"
            >
              <!-- Thumbnail -->
              <div class="w-16 h-10 bg-gray-200 dark:bg-gray-700 rounded overflow-hidden flex-shrink-0 relative">
                <img
                  v-if="asset.thumbnail_path"
                  :src="asset.thumbnail_path"
                  class="w-full h-full object-cover"
                  loading="lazy"
                />
                <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                  <AppIcon name="video-camera" class="w-4 h-4" />
                </div>
                <!-- Duration badge -->
                <span class="absolute bottom-0 right-0 bg-black/70 text-white text-[10px] px-1 rounded-tl">
                  {{ formatTime(asset.duration_seconds) }}
                </span>
              </div>
              <!-- Info -->
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">
                  {{ asset.original_filename || asset.filename }}
                </p>
                <p class="text-[10px] text-gray-400 dark:text-gray-500">
                  {{ asset.width }}x{{ asset.height }} &middot; {{ formatFileSize(asset.file_size) }}
                </p>
              </div>
              <!-- Add button -->
              <button class="p-1 rounded text-blue-500 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-blue-50 dark:hover:bg-blue-900/30">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT: Timeline & Controls -->
      <div class="lg:col-span-2 space-y-4">
        <!-- Output Format Selector -->
        <div data-tour="vc-format" class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <div class="flex items-center gap-4 flex-wrap">
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Ausgabe-Format:</span>
            <div class="flex gap-2">
              <button
                v-for="(fmt, key) in outputFormats"
                :key="key"
                @click="outputFormat = key"
                :class="[
                  'px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors',
                  outputFormat === key
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-blue-400'
                ]"
                :data-testid="`format-btn-${key}`"
              >
                {{ fmt.label }}
              </button>
            </div>

            <!-- Duration summary -->
            <div class="ml-auto flex items-center gap-3 text-sm">
              <span class="text-gray-500 dark:text-gray-400">
                {{ clips.length }} Clip{{ clips.length !== 1 ? 's' : '' }}
              </span>
              <span class="font-medium text-gray-700 dark:text-gray-200" data-testid="total-duration">
                {{ formatTime(totalDuration) }} gesamt
              </span>
            </div>
          </div>
        </div>

        <!-- Timeline -->
        <div data-tour="vc-timeline" class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h2 class="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <AppIcon name="video-camera" class="w-4 h-4" /> Timeline
            </h2>
            <p class="text-xs text-gray-400 dark:text-gray-500">
              Per Drag & Drop neu anordnen
            </p>
          </div>

          <!-- Empty state -->
          <EmptyState
            v-if="clips.length === 0"
            svgIcon="film"
            title="Keine Clips in der Timeline"
            description="Klicke auf Videos in der Bibliothek links, um sie zur Timeline hinzuzufügen und zu einem Video zusammenzuschneiden."
            :compact="true"
          />

          <!-- Draggable clips -->
          <draggable
            v-else
            v-model="clips"
            item-key="id"
            handle=".drag-handle"
            animation="200"
            class="divide-y divide-gray-100 dark:divide-gray-800"
            ghost-class="opacity-40"
            data-testid="timeline-clips"
          >
            <template #item="{ element: clip, index }">
              <div class="p-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors" :data-testid="`timeline-clip-${index}`">
                <!-- Transition indicator (between clips) -->
                <div v-if="index > 0" class="flex items-center gap-2 mb-2 -mt-1">
                  <div class="h-px flex-1 bg-gray-200 dark:bg-gray-700"></div>
                  <div class="flex items-center gap-1">
                    <select
                      :value="clip.transition"
                      @change="setTransition(index, $event.target.value)"
                      class="text-[10px] px-1.5 py-0.5 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 focus:ring-1 focus:ring-blue-500"
                      :data-testid="`transition-select-${index}`"
                    >
                      <option v-for="t in transitionTypes" :key="t.value" :value="t.value">
                        {{ t.icon }} {{ t.label }}
                      </option>
                    </select>
                    <input
                      v-if="clip.transition !== 'cut'"
                      type="number"
                      :value="clip.transitionDuration"
                      @change="updateTransitionDuration(index, $event.target.value)"
                      min="0.1"
                      max="3"
                      step="0.1"
                      class="w-14 text-[10px] px-1.5 py-0.5 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 text-center focus:ring-1 focus:ring-blue-500"
                      title="Übergangs-Dauer (Sekunden)"
                    />
                    <span v-if="clip.transition !== 'cut'" class="text-[10px] text-gray-400">s</span>
                  </div>
                  <div class="h-px flex-1 bg-gray-200 dark:bg-gray-700"></div>
                </div>

                <div class="flex items-start gap-3">
                  <!-- Drag handle -->
                  <div class="drag-handle cursor-grab active:cursor-grabbing mt-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" data-testid="drag-handle">
                    <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M4 8h16M4 16h16" />
                    </svg>
                  </div>

                  <!-- Clip number -->
                  <div class="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-bold flex items-center justify-center shrink-0 mt-1">
                    {{ index + 1 }}
                  </div>

                  <!-- Thumbnail -->
                  <div class="w-20 h-12 bg-gray-200 dark:bg-gray-700 rounded overflow-hidden flex-shrink-0 relative">
                    <img
                      v-if="clip.thumbnailPath"
                      :src="clip.thumbnailPath"
                      class="w-full h-full object-cover"
                      loading="lazy"
                    />
                    <div v-else class="w-full h-full flex items-center justify-center text-gray-400"><AppIcon name="video-camera" class="w-4 h-4" /></div>
                    <span class="absolute bottom-0 right-0 bg-black/70 text-white text-[10px] px-1 rounded-tl">
                      {{ formatTime(clipDuration(clip)) }}
                    </span>
                  </div>

                  <!-- Clip info & trim controls -->
                  <div class="flex-1 min-w-0 space-y-1.5">
                    <p class="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">
                      {{ clip.filename }}
                    </p>
                    <div class="flex items-center gap-2 flex-wrap">
                      <label class="flex items-center gap-1 text-[10px] text-gray-500 dark:text-gray-400">
                        Start:
                        <input
                          type="number"
                          :value="Math.round(clip.trimStart * 10) / 10"
                          @change="updateTrimStart(index, $event.target.value)"
                          min="0"
                          :max="clip.trimEnd - 0.1"
                          step="0.1"
                          class="w-16 px-1.5 py-0.5 text-[10px] border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-center focus:ring-1 focus:ring-blue-500"
                          :data-testid="`clip-trim-start-${index}`"
                        />
                        <span>s</span>
                      </label>
                      <label class="flex items-center gap-1 text-[10px] text-gray-500 dark:text-gray-400">
                        Ende:
                        <input
                          type="number"
                          :value="Math.round(clip.trimEnd * 10) / 10"
                          @change="updateTrimEnd(index, $event.target.value)"
                          :min="clip.trimStart + 0.1"
                          :max="clip.assetDuration"
                          step="0.1"
                          class="w-16 px-1.5 py-0.5 text-[10px] border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-center focus:ring-1 focus:ring-blue-500"
                          :data-testid="`clip-trim-end-${index}`"
                        />
                        <span>s</span>
                      </label>
                      <span class="text-[10px] text-gray-400 dark:text-gray-500">
                        (Original: {{ formatTime(clip.assetDuration) }})
                      </span>
                    </div>

                    <!-- Trim visual bar -->
                    <div class="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden relative w-full">
                      <div
                        class="absolute inset-y-0 bg-blue-400 dark:bg-blue-500 rounded-full"
                        :style="{
                          left: ((clip.trimStart / clip.assetDuration) * 100) + '%',
                          width: (((clip.trimEnd - clip.trimStart) / clip.assetDuration) * 100) + '%'
                        }"
                      ></div>
                    </div>
                  </div>

                  <!-- Actions -->
                  <div class="flex items-center gap-1 shrink-0">
                    <button
                      @click="duplicateClip(index)"
                      class="p-1.5 rounded text-gray-400 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                      title="Clip duplizieren"
                      :data-testid="`duplicate-clip-${index}`"
                    >
                      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
                      </svg>
                    </button>
                    <button
                      @click="removeClip(index)"
                      class="p-1.5 rounded text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                      title="Clip entfernen"
                      :data-testid="`remove-clip-${index}`"
                    >
                      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>

        <!-- Preview Info Panel -->
        <div v-if="previewData && clips.length > 0" class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4" data-testid="preview-info">
          <h3 class="text-sm font-semibold text-blue-800 dark:text-blue-300 mb-2 flex items-center gap-2">
            <span>ℹ️</span> Vorschau-Info
          </h3>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <span class="text-blue-600 dark:text-blue-400 font-medium">Clips:</span>
              <span class="ml-1 text-blue-800 dark:text-blue-200" data-testid="preview-clip-count">{{ previewData.clip_count }}</span>
            </div>
            <div>
              <span class="text-blue-600 dark:text-blue-400 font-medium">Dauer:</span>
              <span class="ml-1 text-blue-800 dark:text-blue-200">{{ formatTime(previewData.effective_duration) }}</span>
            </div>
            <div>
              <span class="text-blue-600 dark:text-blue-400 font-medium">Format:</span>
              <span class="ml-1 text-blue-800 dark:text-blue-200">{{ previewData.output_label }}</span>
            </div>
            <div>
              <span class="text-blue-600 dark:text-blue-400 font-medium">Auflösung:</span>
              <span class="ml-1 text-blue-800 dark:text-blue-200">{{ previewData.output_width }}x{{ previewData.output_height }}</span>
            </div>
          </div>
        </div>

        <!-- Compose Error -->
        <div v-if="composeError" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 flex items-start gap-3" role="alert">
          <svg class="h-5 w-5 text-red-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div class="flex-1">
            <p class="text-sm text-red-700 dark:text-red-400 font-medium" data-testid="compose-error">{{ composeError }}</p>
          </div>
          <button @click="composeError = null" class="text-red-500 hover:text-red-700">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Compose Progress -->
        <div v-if="composing" class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-3" data-testid="compose-progress">
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-600 dark:text-gray-400 flex items-center gap-2">
              <svg class="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Video wird zusammengeschnitten...
            </span>
            <span class="text-blue-600 dark:text-blue-400 font-medium">
              {{ Math.round(composeProgress) }}%
            </span>
          </div>
          <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
            <div
              class="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
              :style="{ width: composeProgress + '%' }"
            ></div>
          </div>
        </div>

        <!-- Compose Result -->
        <div v-if="composeResult" class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4" data-testid="compose-result">
          <h3 class="text-sm font-semibold text-green-800 dark:text-green-300 mb-3 flex items-center gap-2">
            <AppIcon name="check-circle" class="w-4 h-4 inline-block" /> Video erfolgreich zusammengeschnitten!
          </h3>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mb-3">
            <div>
              <span class="text-green-600 dark:text-green-400 font-medium">Clips:</span>
              <span class="ml-1 text-green-800 dark:text-green-200">{{ composeResult.clip_count }}</span>
            </div>
            <div>
              <span class="text-green-600 dark:text-green-400 font-medium">Dauer:</span>
              <span class="ml-1 text-green-800 dark:text-green-200">{{ formatTime(composeResult.duration_seconds) }}</span>
            </div>
            <div>
              <span class="text-green-600 dark:text-green-400 font-medium">Größe:</span>
              <span class="ml-1 text-green-800 dark:text-green-200">{{ formatFileSize(composeResult.file_size) }}</span>
            </div>
            <div>
              <span class="text-green-600 dark:text-green-400 font-medium">Format:</span>
              <span class="ml-1 text-green-800 dark:text-green-200">{{ composeResult.output_format }}</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="openResultPreview"
              class="px-3 py-1.5 text-xs font-medium bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-1"
              data-testid="preview-result-btn"
            >
              <svg class="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
              Vorschau
            </button>
            <button
              @click="downloadResult"
              class="px-3 py-1.5 text-xs font-medium bg-white dark:bg-gray-800 text-green-700 dark:text-green-300 border border-green-300 dark:border-green-700 rounded-lg hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors flex items-center gap-1"
              data-testid="download-result-btn"
            >
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download
            </button>
            <span v-if="composeResult.asset_id" class="text-[10px] text-green-600 dark:text-green-400 ml-2">
              Als Asset #{{ composeResult.asset_id }} gespeichert
            </span>
          </div>
        </div>

        <!-- Action Bar -->
        <div data-tour="vc-compose" class="flex items-center justify-between bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <label class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              v-model="saveAsAsset"
              class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
              data-testid="save-as-asset-checkbox"
            />
            Als Asset speichern
          </label>
          <button
            @click="composeVideo"
            :disabled="!canCompose"
            class="px-5 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2 shadow-md"
            data-testid="compose-btn"
          >
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {{ composing ? 'Wird zusammengeschnitten...' : 'Video zusammenschneiden' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Preview Modal -->
    <teleport to="body">
      <div
        v-if="showPreviewModal && composeResult"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
        @click.self="closePreviewModal"
        data-testid="preview-modal"
      >
        <div class="relative bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-3xl w-full mx-4 overflow-hidden">
          <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
              Vorschau - Zusammengeschnittenes Video
            </h3>
            <button @click="closePreviewModal" class="p-1 rounded text-gray-400 hover:text-gray-600">
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="bg-black flex items-center justify-center" style="max-height: 70vh;">
            <video
              ref="previewVideoEl"
              :src="composeResult.file_path"
              controls
              autoplay
              class="max-h-[70vh] max-w-full"
              data-testid="preview-video"
            >
              Video nicht verfügbar.
            </video>
          </div>
          <div class="px-4 py-2 text-xs text-gray-500 dark:text-gray-400 flex items-center justify-between border-t border-gray-200 dark:border-gray-700">
            <span>{{ composeResult.clip_count }} Clips &middot; {{ formatTime(composeResult.duration_seconds) }} &middot; {{ formatFileSize(composeResult.file_size) }}</span>
            <button
              @click="downloadResult"
              class="text-blue-600 hover:underline flex items-center gap-1"
            >
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download
            </button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- Tour System -->
    <VideoWorkflowTour ref="workflowTourRef" />
    <TourSystem page-key="video-composer" />
  </div>
</template>
