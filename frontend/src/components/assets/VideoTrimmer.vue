<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import api from '@/utils/api'

const props = defineProps({
  show: { type: Boolean, default: false },
  asset: { type: Object, required: true },
})

const emit = defineEmits(['close', 'trimmed'])

// Video element ref
const videoEl = ref(null)
const timelineEl = ref(null)

// Video state
const videoDuration = ref(0)
const currentTime = ref(0)
const isPlaying = ref(false)
const videoReady = ref(false)

// Trim range (in seconds)
const trimStart = ref(0)
const trimEnd = ref(0)

// Dragging state
const isDraggingStart = ref(false)
const isDraggingEnd = ref(false)
const isDraggingPlayhead = ref(false)

// Trim processing state
const trimming = ref(false)
const trimProgress = ref(0)
const trimError = ref(null)
const saveAsNew = ref(true)

// Format time as MM:SS.ms
function formatTime(seconds) {
  if (!seconds && seconds !== 0) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 10)
  return `${mins}:${secs.toString().padStart(2, '0')}.${ms}`
}

// Computed
const trimDuration = computed(() => {
  return Math.max(0, trimEnd.value - trimStart.value)
})

const trimStartPercent = computed(() => {
  if (!videoDuration.value) return 0
  return (trimStart.value / videoDuration.value) * 100
})

const trimEndPercent = computed(() => {
  if (!videoDuration.value) return 100
  return (trimEnd.value / videoDuration.value) * 100
})

const playheadPercent = computed(() => {
  if (!videoDuration.value) return 0
  return (currentTime.value / videoDuration.value) * 100
})

// Initialize from asset duration if available
function initFromAsset() {
  if (props.asset.duration_seconds && !videoReady.value) {
    videoDuration.value = props.asset.duration_seconds
    trimEnd.value = props.asset.duration_seconds
  }
}

// Video event handlers
function onLoadedMetadata() {
  if (videoEl.value) {
    const dur = videoEl.value.duration
    if (dur && isFinite(dur) && dur > 0) {
      videoDuration.value = dur
      trimEnd.value = dur
    }
    videoReady.value = true
  }
}

function onCanPlay() {
  if (videoEl.value) {
    const dur = videoEl.value.duration
    if (dur && isFinite(dur) && dur > 0 && videoDuration.value === 0) {
      videoDuration.value = dur
      trimEnd.value = dur
    }
    videoReady.value = true
  }
}

function onVideoError() {
  // If video element fails to load, fall back to asset metadata
  if (props.asset.duration_seconds) {
    videoDuration.value = props.asset.duration_seconds
    trimEnd.value = props.asset.duration_seconds
  }
}

function onTimeUpdate() {
  if (videoEl.value && !isDraggingPlayhead.value) {
    currentTime.value = videoEl.value.currentTime

    // Loop within trim range during preview
    if (isPlaying.value && videoEl.value.currentTime >= trimEnd.value) {
      videoEl.value.currentTime = trimStart.value
      videoEl.value.pause()
      isPlaying.value = false
    }
  }
}

function onVideoEnded() {
  isPlaying.value = false
}

// Play/Pause the trimmed preview
function togglePlayPreview() {
  if (!videoEl.value) return

  if (isPlaying.value) {
    videoEl.value.pause()
    isPlaying.value = false
  } else {
    // Start playing from trimStart if current time is outside the range
    if (videoEl.value.currentTime < trimStart.value || videoEl.value.currentTime >= trimEnd.value) {
      videoEl.value.currentTime = trimStart.value
    }
    videoEl.value.play()
    isPlaying.value = true
  }
}

// Seek to start of trim
function seekToStart() {
  if (videoEl.value) {
    videoEl.value.currentTime = trimStart.value
    currentTime.value = trimStart.value
    if (isPlaying.value) {
      videoEl.value.pause()
      isPlaying.value = false
    }
  }
}

// Seek to end of trim
function seekToEnd() {
  if (videoEl.value) {
    videoEl.value.currentTime = Math.max(0, trimEnd.value - 0.1)
    currentTime.value = Math.max(0, trimEnd.value - 0.1)
    if (isPlaying.value) {
      videoEl.value.pause()
      isPlaying.value = false
    }
  }
}

// Set trim start to current time
function setStartHere() {
  if (currentTime.value < trimEnd.value - 0.1) {
    trimStart.value = Math.round(currentTime.value * 10) / 10
  }
}

// Set trim end to current time
function setEndHere() {
  if (currentTime.value > trimStart.value + 0.1) {
    trimEnd.value = Math.round(currentTime.value * 10) / 10
  }
}

// Timeline mouse/touch interaction
function getTimeFromPosition(e) {
  if (!timelineEl.value || !videoDuration.value) return 0
  const rect = timelineEl.value.getBoundingClientRect()
  const x = (e.clientX || e.touches?.[0]?.clientX || 0) - rect.left
  const fraction = Math.max(0, Math.min(1, x / rect.width))
  return fraction * videoDuration.value
}

function onTimelineMouseDown(e) {
  e.preventDefault()
  const time = getTimeFromPosition(e)

  // Determine what the user is grabbing
  const startDist = Math.abs(time - trimStart.value)
  const endDist = Math.abs(time - trimEnd.value)
  const threshold = videoDuration.value * 0.02 // 2% of total duration

  if (startDist < threshold && startDist <= endDist) {
    isDraggingStart.value = true
  } else if (endDist < threshold) {
    isDraggingEnd.value = true
  } else {
    // Click on timeline - seek to position
    isDraggingPlayhead.value = true
    currentTime.value = time
    if (videoEl.value) {
      videoEl.value.currentTime = time
    }
  }

  document.addEventListener('mousemove', onDocumentMouseMove)
  document.addEventListener('mouseup', onDocumentMouseUp)
  document.addEventListener('touchmove', onDocumentMouseMove)
  document.addEventListener('touchend', onDocumentMouseUp)
}

function onDocumentMouseMove(e) {
  const time = getTimeFromPosition(e)

  if (isDraggingStart.value) {
    trimStart.value = Math.max(0, Math.min(time, trimEnd.value - 0.1))
    // Snap video to start handle
    if (videoEl.value) {
      videoEl.value.currentTime = trimStart.value
      currentTime.value = trimStart.value
    }
  } else if (isDraggingEnd.value) {
    trimEnd.value = Math.max(trimStart.value + 0.1, Math.min(time, videoDuration.value))
    // Snap video to end handle
    if (videoEl.value) {
      videoEl.value.currentTime = trimEnd.value
      currentTime.value = trimEnd.value
    }
  } else if (isDraggingPlayhead.value) {
    currentTime.value = Math.max(0, Math.min(time, videoDuration.value))
    if (videoEl.value) {
      videoEl.value.currentTime = currentTime.value
    }
  }
}

function onDocumentMouseUp() {
  isDraggingStart.value = false
  isDraggingEnd.value = false
  isDraggingPlayhead.value = false
  document.removeEventListener('mousemove', onDocumentMouseMove)
  document.removeEventListener('mouseup', onDocumentMouseUp)
  document.removeEventListener('touchmove', onDocumentMouseMove)
  document.removeEventListener('touchend', onDocumentMouseUp)
}

// Start handle drag
function onStartHandleMouseDown(e) {
  e.preventDefault()
  e.stopPropagation()
  isDraggingStart.value = true
  document.addEventListener('mousemove', onDocumentMouseMove)
  document.addEventListener('mouseup', onDocumentMouseUp)
  document.addEventListener('touchmove', onDocumentMouseMove)
  document.addEventListener('touchend', onDocumentMouseUp)
}

// End handle drag
function onEndHandleMouseDown(e) {
  e.preventDefault()
  e.stopPropagation()
  isDraggingEnd.value = true
  document.addEventListener('mousemove', onDocumentMouseMove)
  document.addEventListener('mouseup', onDocumentMouseUp)
  document.addEventListener('touchmove', onDocumentMouseMove)
  document.addEventListener('touchend', onDocumentMouseUp)
}

// Input handlers for precise time entry
function onStartTimeInput(e) {
  const val = parseFloat(e.target.value)
  if (!isNaN(val) && val >= 0 && val < trimEnd.value - 0.1) {
    trimStart.value = val
    if (videoEl.value) {
      videoEl.value.currentTime = val
      currentTime.value = val
    }
  }
}

function onEndTimeInput(e) {
  const val = parseFloat(e.target.value)
  if (!isNaN(val) && val > trimStart.value + 0.1 && val <= videoDuration.value) {
    trimEnd.value = val
    if (videoEl.value) {
      videoEl.value.currentTime = val
      currentTime.value = val
    }
  }
}

// Perform the trim
async function performTrim() {
  trimming.value = true
  trimProgress.value = 10
  trimError.value = null

  try {
    // Simulate initial progress (ffmpeg processing is server-side)
    const progressInterval = setInterval(() => {
      if (trimProgress.value < 85) {
        trimProgress.value += Math.random() * 10
      }
    }, 500)

    const response = await api.post('/api/assets/trim', {
      asset_id: props.asset.id,
      start_time: Math.round(trimStart.value * 100) / 100,
      end_time: Math.round(trimEnd.value * 100) / 100,
      save_as_new: saveAsNew.value,
    })

    clearInterval(progressInterval)
    trimProgress.value = 100

    // Short delay to show 100% completion
    await new Promise(resolve => setTimeout(resolve, 500))

    emit('trimmed', response.data)
  } catch (err) {
    trimError.value = err.response?.data?.detail || 'Video-Trimming fehlgeschlagen'
    trimProgress.value = 0
  } finally {
    trimming.value = false
  }
}

// Reset trim range
function resetTrim() {
  trimStart.value = 0
  trimEnd.value = videoDuration.value
  if (videoEl.value) {
    videoEl.value.currentTime = 0
    currentTime.value = 0
  }
  if (isPlaying.value) {
    videoEl.value?.pause()
    isPlaying.value = false
  }
}

// Initialize on mount and when show changes
onMounted(() => {
  initFromAsset()
})

// Re-initialize when modal opens
watch(() => props.show, (newVal) => {
  if (newVal) {
    initFromAsset()
    // Reset state
    trimming.value = false
    trimProgress.value = 0
    trimError.value = null
    isPlaying.value = false
    currentTime.value = 0
    videoReady.value = false
  }
})

// Cleanup on unmount
onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onDocumentMouseMove)
  document.removeEventListener('mouseup', onDocumentMouseUp)
  document.removeEventListener('touchmove', onDocumentMouseMove)
  document.removeEventListener('touchend', onDocumentMouseUp)
})
</script>

<template>
  <teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
      @click.self="$emit('close')"
      data-testid="video-trimmer-modal"
    >
      <div class="relative bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-4xl w-full mx-4 overflow-hidden max-h-[95vh] flex flex-col">
        <!-- Modal header -->
        <div class="flex items-center justify-between px-5 py-3 border-b border-gray-200 dark:border-gray-700 shrink-0">
          <div>
            <h3 class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <svg class="h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Video trimmen
            </h3>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {{ asset.original_filename || asset.filename }}
            </p>
          </div>
          <button
            @click="$emit('close')"
            class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            data-testid="trimmer-close-btn"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Video player area -->
        <div class="bg-black flex items-center justify-center shrink-0" style="max-height: 50vh;">
          <video
            ref="videoEl"
            :src="asset.file_path"
            class="w-full max-h-[50vh]"
            @loadedmetadata="onLoadedMetadata"
            @canplay="onCanPlay"
            @timeupdate="onTimeUpdate"
            @ended="onVideoEnded"
            @error="onVideoError"
            preload="auto"
            data-testid="trimmer-video"
          >
            Dein Browser unterstuetzt dieses Videoformat nicht.
          </video>
        </div>

        <!-- Controls section -->
        <div class="px-5 py-4 space-y-4 overflow-y-auto">
          <!-- Playback controls -->
          <div class="flex items-center justify-center gap-3">
            <button
              @click="seekToStart"
              class="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              title="Zum Anfang springen"
              data-testid="seek-start-btn"
            >
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0019 16V8a1 1 0 00-1.6-.8l-5.333 4zM4.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0011 16V8a1 1 0 00-1.6-.8l-5.334 4z" />
              </svg>
            </button>
            <button
              @click="togglePlayPreview"
              class="p-3 rounded-full bg-blue-600 hover:bg-blue-700 text-white transition-colors shadow-md"
              :title="isPlaying ? 'Pause' : 'Vorschau abspielen'"
              data-testid="play-preview-btn"
            >
              <svg v-if="isPlaying" class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
              </svg>
              <svg v-else class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            </button>
            <button
              @click="seekToEnd"
              class="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              title="Zum Ende springen"
              data-testid="seek-end-btn"
            >
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M11.933 12.8a1 1 0 000-1.6L6.6 7.2A1 1 0 005 8v8a1 1 0 001.6.8l5.333-4zM19.933 12.8a1 1 0 000-1.6l-5.333-4A1 1 0 0013 8v8a1 1 0 001.6.8l5.333-4z" />
              </svg>
            </button>
          </div>

          <!-- Timeline / Range slider -->
          <div class="space-y-1">
            <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
              <span>{{ formatTime(currentTime) }}</span>
              <span>{{ formatTime(videoDuration) }}</span>
            </div>

            <!-- Timeline track -->
            <div
              ref="timelineEl"
              class="relative h-10 bg-gray-200 dark:bg-gray-700 rounded-lg cursor-pointer select-none"
              @mousedown="onTimelineMouseDown"
              @touchstart.prevent="onTimelineMouseDown"
              data-testid="trim-timeline"
            >
              <!-- Inactive region before start -->
              <div
                class="absolute inset-y-0 left-0 bg-gray-300 dark:bg-gray-600 rounded-l-lg opacity-50"
                :style="{ width: trimStartPercent + '%' }"
              ></div>

              <!-- Active trim region -->
              <div
                class="absolute inset-y-0 bg-blue-100 dark:bg-blue-900/40 border-y-2 border-blue-500"
                :style="{
                  left: trimStartPercent + '%',
                  width: (trimEndPercent - trimStartPercent) + '%'
                }"
              ></div>

              <!-- Inactive region after end -->
              <div
                class="absolute inset-y-0 right-0 bg-gray-300 dark:bg-gray-600 rounded-r-lg opacity-50"
                :style="{ width: (100 - trimEndPercent) + '%' }"
              ></div>

              <!-- Start handle -->
              <div
                class="absolute top-0 bottom-0 w-3 bg-blue-600 rounded-l cursor-ew-resize z-10 flex items-center justify-center hover:bg-blue-700 transition-colors"
                :style="{ left: 'calc(' + trimStartPercent + '% - 6px)' }"
                @mousedown="onStartHandleMouseDown"
                @touchstart.prevent="onStartHandleMouseDown"
                data-testid="trim-start-handle"
              >
                <div class="w-0.5 h-4 bg-white rounded-full"></div>
              </div>

              <!-- End handle -->
              <div
                class="absolute top-0 bottom-0 w-3 bg-blue-600 rounded-r cursor-ew-resize z-10 flex items-center justify-center hover:bg-blue-700 transition-colors"
                :style="{ left: 'calc(' + trimEndPercent + '% - 6px)' }"
                @mousedown="onEndHandleMouseDown"
                @touchstart.prevent="onEndHandleMouseDown"
                data-testid="trim-end-handle"
              >
                <div class="w-0.5 h-4 bg-white rounded-full"></div>
              </div>

              <!-- Playhead -->
              <div
                class="absolute top-0 bottom-0 w-0.5 bg-red-500 z-20 pointer-events-none"
                :style="{ left: playheadPercent + '%' }"
              >
                <div class="absolute -top-1 left-1/2 -translate-x-1/2 w-2.5 h-2.5 bg-red-500 rounded-full shadow"></div>
              </div>
            </div>
          </div>

          <!-- Trim range display and quick actions -->
          <div class="flex items-center justify-between flex-wrap gap-2">
            <div class="flex items-center gap-3">
              <!-- Start time -->
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-medium text-gray-500 dark:text-gray-400">Start:</span>
                <input
                  type="number"
                  :value="Math.round(trimStart * 10) / 10"
                  @change="onStartTimeInput"
                  min="0"
                  :max="trimEnd - 0.1"
                  step="0.1"
                  class="w-20 px-2 py-1 text-xs text-center border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-1 focus:ring-blue-500"
                  data-testid="trim-start-input"
                />
                <button
                  @click="setStartHere"
                  class="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                  title="Start auf aktuelle Position setzen"
                  data-testid="set-start-here-btn"
                >
                  Hier
                </button>
              </div>

              <!-- End time -->
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-medium text-gray-500 dark:text-gray-400">Ende:</span>
                <input
                  type="number"
                  :value="Math.round(trimEnd * 10) / 10"
                  @change="onEndTimeInput"
                  :min="trimStart + 0.1"
                  :max="videoDuration"
                  step="0.1"
                  class="w-20 px-2 py-1 text-xs text-center border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-1 focus:ring-blue-500"
                  data-testid="trim-end-input"
                />
                <button
                  @click="setEndHere"
                  class="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                  title="Ende auf aktuelle Position setzen"
                  data-testid="set-end-here-btn"
                >
                  Hier
                </button>
              </div>
            </div>

            <!-- Duration badge -->
            <div class="flex items-center gap-2">
              <span
                class="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full"
                :class="trimDuration > 0 ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'"
                data-testid="trim-duration-badge"
              >
                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {{ formatTime(trimDuration) }} Dauer
              </span>
              <button
                @click="resetTrim"
                class="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 underline"
                data-testid="reset-trim-btn"
              >
                Zurücksetzen
              </button>
            </div>
          </div>

          <!-- Trim error -->
          <div v-if="trimError" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 flex items-center gap-2" role="alert">
            <svg class="h-4 w-4 text-red-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p class="text-sm text-red-700 dark:text-red-400" data-testid="trim-error">{{ trimError }}</p>
            <button @click="trimError = null" class="ml-auto text-red-500 hover:text-red-700 shrink-0">
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Trim progress bar -->
          <div v-if="trimming" class="space-y-2" data-testid="trim-progress-section">
            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-600 dark:text-gray-400 flex items-center gap-2">
                <svg class="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Video wird getrimmt...
              </span>
              <span class="text-blue-600 dark:text-blue-400 font-medium" data-testid="trim-progress-percent">
                {{ Math.round(trimProgress) }}%
              </span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
              <div
                class="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                :style="{ width: trimProgress + '%' }"
                data-testid="trim-progress-bar"
              ></div>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="flex items-center justify-between pt-2 border-t border-gray-200 dark:border-gray-700">
            <div class="flex items-center gap-3">
              <label class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
                <input
                  type="checkbox"
                  v-model="saveAsNew"
                  class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                  data-testid="save-as-new-checkbox"
                />
                Als neues Asset speichern
              </label>
            </div>
            <div class="flex items-center gap-2">
              <button
                @click="$emit('close')"
                class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                :disabled="trimming"
                data-testid="trimmer-cancel-btn"
              >
                Abbrechen
              </button>
              <button
                @click="performTrim"
                :disabled="trimming || trimDuration < 0.1"
                class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                data-testid="trimmer-save-btn"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {{ trimming ? 'Wird getrimmt...' : 'Video trimmen' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>
