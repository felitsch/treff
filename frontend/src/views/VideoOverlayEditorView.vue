<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/utils/api'
import EmptyState from '@/components/common/EmptyState.vue'
import TourSystem from '@/components/common/TourSystem.vue'
import VideoWorkflowTour from '@/components/common/VideoWorkflowTour.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const route = useRoute()
const router = useRouter()

const workflowTourRef = ref(null)

// ---------- State ----------
const loading = ref(true)
const saving = ref(false)
const rendering = ref(false)
const videoAssets = ref([])
const selectedAssetId = ref(null)
const selectedAsset = ref(null)
const overlayName = ref('Unbenanntes Overlay')
const overlayId = ref(null)
const layers = ref([])
const selectedLayerIndex = ref(-1)
const videoEl = ref(null)
const previewContainer = ref(null)
const currentTime = ref(0)
const videoDuration = ref(0)
const isPlaying = ref(false)
const videoReady = ref(false)
const toastMessage = ref('')
const toastType = ref('success')
const showToast = ref(false)
const renderStatus = ref('pending')
const renderedPath = ref(null)

// TREFF brand constants
const TREFF_BLUE = '#3B7AB1'
const TREFF_YELLOW = '#FDD000'
const TREFF_DARK = '#1A1A2E'

// Animation options
const animationOptions = [
  { value: 'none', label: 'Keine', icon: '' },
  { value: 'fade_in', label: 'Einblenden', icon: 'sparkles' },
  { value: 'slide_in_left', label: 'Von Links', icon: 'arrow-path' },
  { value: 'slide_in_bottom', label: 'Von Unten', icon: 'arrow-path' },
  { value: 'pop_in', label: 'Pop-In', icon: 'bolt' },
]

// Font options
const fontOptions = [
  'Inter', 'Arial', 'Helvetica', 'Georgia', 'Verdana', 'Courier New', 'Impact',
]

// Layer type presets
const layerPresets = [
  {
    type: 'text',
    label: 'Text',
    icon: 'pencil-square',
    defaults: { text: 'Neuer Text', x: 10, y: 50, width: 80, height: 8, fontSize: 32, color: '#FFFFFF', bgColor: 'rgba(0,0,0,0.6)', animation: 'none' },
  },
  {
    type: 'logo',
    label: 'TREFF Logo',
    icon: 'tag',
    defaults: { text: 'TREFF Sprachreisen', x: 5, y: 3, width: 40, height: 6, fontSize: 24, color: '#FFFFFF', bgColor: TREFF_BLUE, bold: true, animation: 'fade_in' },
  },
  {
    type: 'subtitle',
    label: 'Untertitel',
    icon: 'chat-bubble',
    defaults: { text: 'Untertitel hier', x: 5, y: 85, width: 90, height: 8, fontSize: 28, color: '#FFFFFF', bgColor: 'rgba(0,0,0,0.7)', textAlign: 'center', animation: 'fade_in' },
  },
  {
    type: 'hashtag',
    label: 'Hashtags',
    icon: 'hashtag',
    defaults: { text: '#treffsprachreisen #highschool #auslandsjahr', x: 5, y: 92, width: 90, height: 5, fontSize: 18, color: TREFF_YELLOW, bgColor: 'rgba(0,0,0,0.5)', animation: 'slide_in_bottom' },
  },
]

// Computed
const selectedLayer = computed(() => {
  if (selectedLayerIndex.value >= 0 && selectedLayerIndex.value < layers.value.length) {
    return layers.value[selectedLayerIndex.value]
  }
  return null
})

const videoSrc = computed(() => {
  if (!selectedAsset.value) return ''
  return selectedAsset.value.file_path
})

const hasChanges = computed(() => {
  return layers.value.length > 0
})

// ---------- Methods ----------

function toast(msg, type = 'success') {
  toastMessage.value = msg
  toastType.value = type
  showToast.value = true
  setTimeout(() => { showToast.value = false }, 3000)
}

async function fetchVideoAssets() {
  try {
    const res = await api.get('/api/assets', { params: { file_type: 'video' } })
    // Filter only actual video assets
    videoAssets.value = (res.data || []).filter(a =>
      a.file_type && a.file_type.startsWith('video/')
    )
  } catch (e) {
    // Error toast shown by API interceptor
  }
}

async function selectAsset(asset) {
  selectedAssetId.value = asset.id
  selectedAsset.value = asset
  videoDuration.value = asset.duration_seconds || 10
  videoReady.value = false
  // Reset layers when switching video
  layers.value = []
  selectedLayerIndex.value = -1
  overlayId.value = null
  renderStatus.value = 'pending'
  renderedPath.value = null

  // Check if there's an existing overlay for this asset
  try {
    const res = await api.get('/api/video-overlays')
    const existing = (res.data || []).find(o => o.asset_id === asset.id)
    if (existing) {
      overlayId.value = existing.id
      overlayName.value = existing.name
      layers.value = existing.layers || []
      renderStatus.value = existing.render_status || 'pending'
      renderedPath.value = existing.rendered_path
      if (layers.value.length > 0) selectedLayerIndex.value = 0
    }
  } catch (e) {
    // No existing overlay, that's fine
  }
}

function addLayer(preset) {
  const newLayer = {
    ...preset.defaults,
    type: preset.type,
    opacity: 1.0,
    startTime: 0,
    endTime: -1,
    bold: preset.defaults.bold || false,
    italic: false,
    textAlign: preset.defaults.textAlign || 'left',
    fontFamily: 'Inter',
  }
  layers.value.push(newLayer)
  selectedLayerIndex.value = layers.value.length - 1
}

function removeLayer(index) {
  layers.value.splice(index, 1)
  if (selectedLayerIndex.value >= layers.value.length) {
    selectedLayerIndex.value = layers.value.length - 1
  }
}

function moveLayerUp(index) {
  if (index <= 0) return
  const temp = layers.value[index]
  layers.value[index] = layers.value[index - 1]
  layers.value[index - 1] = temp
  selectedLayerIndex.value = index - 1
}

function moveLayerDown(index) {
  if (index >= layers.value.length - 1) return
  const temp = layers.value[index]
  layers.value[index] = layers.value[index + 1]
  layers.value[index + 1] = temp
  selectedLayerIndex.value = index + 1
}

function duplicateLayer(index) {
  const clone = JSON.parse(JSON.stringify(layers.value[index]))
  clone.y = Math.min(clone.y + 5, 95)
  layers.value.splice(index + 1, 0, clone)
  selectedLayerIndex.value = index + 1
}

// Video playback controls
function onVideoTimeUpdate() {
  if (videoEl.value) {
    currentTime.value = videoEl.value.currentTime
  }
}

function onVideoLoaded() {
  if (videoEl.value) {
    videoDuration.value = videoEl.value.duration || 10
    videoReady.value = true
  }
}

function togglePlay() {
  if (!videoEl.value) return
  if (isPlaying.value) {
    videoEl.value.pause()
  } else {
    videoEl.value.play()
  }
  isPlaying.value = !isPlaying.value
}

function seekTo(time) {
  if (videoEl.value) {
    videoEl.value.currentTime = time
    currentTime.value = time
  }
}

function onTimelineClick(e) {
  const rect = e.currentTarget.getBoundingClientRect()
  const pct = (e.clientX - rect.left) / rect.width
  const time = pct * videoDuration.value
  seekTo(time)
}

// Check if a layer should be visible at the current time
function isLayerVisible(layer) {
  const start = layer.startTime || 0
  const end = layer.endTime < 0 ? videoDuration.value : layer.endTime
  return currentTime.value >= start && currentTime.value <= end
}

// Get CSS animation class for preview
function getAnimationStyle(layer) {
  if (!isLayerVisible(layer)) return { opacity: 0, transition: 'opacity 0.3s' }

  const start = layer.startTime || 0
  const elapsed = currentTime.value - start
  const animDuration = 0.5

  const base = { opacity: layer.opacity || 1, transition: 'all 0.3s ease' }

  if (layer.animation === 'fade_in' && elapsed < animDuration) {
    return { ...base, opacity: (elapsed / animDuration) * (layer.opacity || 1) }
  }
  if (layer.animation === 'slide_in_left' && elapsed < animDuration) {
    const progress = elapsed / animDuration
    return { ...base, transform: `translateX(${-100 + progress * 100}%)` }
  }
  if (layer.animation === 'slide_in_bottom' && elapsed < animDuration) {
    const progress = elapsed / animDuration
    return { ...base, transform: `translateY(${100 - progress * 100}%)` }
  }
  if (layer.animation === 'pop_in' && elapsed < animDuration) {
    const progress = elapsed / animDuration
    const scale = 0.3 + progress * 0.7
    return { ...base, transform: `scale(${scale})` }
  }

  return base
}

// Save overlay config
async function saveOverlay() {
  if (!selectedAssetId.value) return
  saving.value = true

  try {
    const payload = {
      asset_id: selectedAssetId.value,
      name: overlayName.value,
      layers: layers.value,
    }

    let res
    if (overlayId.value) {
      res = await api.put(`/api/video-overlays/${overlayId.value}`, {
        name: overlayName.value,
        layers: layers.value,
      })
    } else {
      res = await api.post('/api/video-overlays', payload)
    }

    overlayId.value = res.data.id
    renderStatus.value = res.data.render_status || 'pending'
    toast('Overlay gespeichert!', 'success')
  } catch (e) {
    toast('Fehler beim Speichern: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    saving.value = false
  }
}

// Render video with overlays via ffmpeg
async function renderVideo() {
  if (!overlayId.value) {
    await saveOverlay()
  }
  if (!overlayId.value) return

  rendering.value = true
  renderStatus.value = 'rendering'

  try {
    const res = await api.post(`/api/video-overlays/${overlayId.value}/render`)
    renderStatus.value = res.data.render_status || 'done'
    renderedPath.value = res.data.rendered_path
    toast('Video erfolgreich gerendert!', 'success')
  } catch (e) {
    renderStatus.value = 'error'
    toast('Rendering fehlgeschlagen: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    rendering.value = false
  }
}

// Delete overlay
async function deleteOverlay() {
  if (!overlayId.value) return
  if (!confirm('Overlay wirklich löschen?')) return

  try {
    await api.delete(`/api/video-overlays/${overlayId.value}`)
    overlayId.value = null
    layers.value = []
    selectedLayerIndex.value = -1
    renderStatus.value = 'pending'
    renderedPath.value = null
    toast('Overlay gelöscht.', 'success')
  } catch (e) {
    toast('Fehler beim Löschen.', 'error')
  }
}

function formatTime(s) {
  if (!s || isNaN(s)) return '0:00'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

// ---------- Draggable Overlay Logic ----------
const isDragging = ref(false)
const dragLayerIndex = ref(-1)
const dragStartX = ref(0)
const dragStartY = ref(0)
const dragStartLayerX = ref(0)
const dragStartLayerY = ref(0)

function onOverlayMouseDown(e, idx) {
  // Select the layer
  selectedLayerIndex.value = idx

  // Begin drag
  isDragging.value = true
  dragLayerIndex.value = idx

  const container = previewContainer.value
  if (!container) return

  const rect = container.getBoundingClientRect()
  dragStartX.value = e.clientX
  dragStartY.value = e.clientY
  dragStartLayerX.value = layers.value[idx].x
  dragStartLayerY.value = layers.value[idx].y

  e.preventDefault()
  e.stopPropagation()

  document.addEventListener('mousemove', onOverlayMouseMove)
  document.addEventListener('mouseup', onOverlayMouseUp)
}

function onOverlayMouseMove(e) {
  if (!isDragging.value || dragLayerIndex.value < 0) return

  const container = previewContainer.value
  if (!container) return

  const rect = container.getBoundingClientRect()
  const deltaXPct = ((e.clientX - dragStartX.value) / rect.width) * 100
  const deltaYPct = ((e.clientY - dragStartY.value) / rect.height) * 100

  const layer = layers.value[dragLayerIndex.value]
  if (!layer) return

  // Clamp to 0-100 range (minus layer width/height to keep within bounds)
  layer.x = Math.max(0, Math.min(100 - layer.width, dragStartLayerX.value + deltaXPct))
  layer.y = Math.max(0, Math.min(100 - layer.height, dragStartLayerY.value + deltaYPct))

  // Round to 1 decimal
  layer.x = Math.round(layer.x * 10) / 10
  layer.y = Math.round(layer.y * 10) / 10
}

function onOverlayMouseUp() {
  isDragging.value = false
  dragLayerIndex.value = -1
  document.removeEventListener('mousemove', onOverlayMouseMove)
  document.removeEventListener('mouseup', onOverlayMouseUp)
}

// Touch support for draggable overlays
function onOverlayTouchStart(e, idx) {
  if (e.touches.length !== 1) return
  const touch = e.touches[0]
  onOverlayMouseDown({ clientX: touch.clientX, clientY: touch.clientY, preventDefault: () => e.preventDefault(), stopPropagation: () => e.stopPropagation() }, idx)
}

function onOverlayTouchMove(e) {
  if (!isDragging.value) return
  if (e.touches.length !== 1) return
  const touch = e.touches[0]
  onOverlayMouseMove({ clientX: touch.clientX, clientY: touch.clientY })
  e.preventDefault()
}

function onOverlayTouchEnd() {
  onOverlayMouseUp()
}

// Animation frame for smooth preview updates
let rafId = null
function animLoop() {
  if (videoEl.value && isPlaying.value) {
    currentTime.value = videoEl.value.currentTime
  }
  rafId = requestAnimationFrame(animLoop)
}

onMounted(async () => {
  await fetchVideoAssets()
  loading.value = false
  rafId = requestAnimationFrame(animLoop)

  // If asset_id in query, auto-select
  if (route.query.asset_id) {
    const assetId = parseInt(route.query.asset_id)
    const asset = videoAssets.value.find(a => a.id === assetId)
    if (asset) {
      await selectAsset(asset)
    }
  }
})

onUnmounted(() => {
  if (rafId) cancelAnimationFrame(rafId)
  // Cleanup drag listeners
  document.removeEventListener('mousemove', onOverlayMouseMove)
  document.removeEventListener('mouseup', onOverlayMouseUp)
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
    <!-- Toast notification -->
    <Teleport to="body">
      <div v-if="showToast" class="fixed top-4 right-4 z-[9999] px-4 py-3 rounded-lg shadow-lg text-white text-sm font-medium transition-all"
           :class="toastType === 'success' ? 'bg-green-500' : 'bg-red-500'">
        {{ toastMessage }}
      </div>
    </Teleport>

    <!-- Header -->
    <div data-tour="vo-header" class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <AppIcon name="film" class="w-6 h-6 inline-block" /> Video-Overlay Editor
        </h1>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          TREFF-Branding, Texte und Untertitel auf Videos legen
        </p>
      </div>
      <button
        @click="workflowTourRef?.startTour()"
        class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[#4C8BC2] bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors"
        title="Video-Workflow-Tour starten"
      >
        <AppIcon name="film" class="w-4 h-4 inline-block" /> Workflow
      </button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
    </div>

    <template v-else>
      <!-- Step 1: Select Video Asset -->
      <div v-if="!selectedAsset" data-tour="vo-video-select" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Video auswählen</h2>

        <EmptyState
          v-if="videoAssets.length === 0"
          svgIcon="film"
          title="Keine Videos vorhanden"
          description="Lade zuerst ein Video in der Asset-Bibliothek hoch, um Overlays und Text-Layer hinzuzufügen."
          actionLabel="Zu Assets"
          actionTo="/library/assets"
        />

        <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <button
            v-for="asset in videoAssets"
            :key="asset.id"
            @click="selectAsset(asset)"
            class="relative group rounded-lg overflow-hidden border-2 border-gray-200 dark:border-gray-700 hover:border-blue-500 transition-all"
          >
            <div class="aspect-video bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
              <img loading="lazy" v-if="asset.thumbnail_path" :src="asset.thumbnail_path" class="w-full h-full object-cover" :alt="asset.original_filename || 'Video-Vorschau'" />
              <AppIcon v-else name="film" class="w-8 h-8" />
            </div>
            <div class="p-2 text-xs text-gray-700 dark:text-gray-300 truncate">
              {{ asset.original_filename || asset.filename }}
            </div>
            <div v-if="asset.duration_seconds" class="absolute top-1 right-1 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
              {{ formatTime(asset.duration_seconds) }}
            </div>
            <!-- Play button overlay -->
            <div class="absolute inset-0 bg-black/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <div class="w-10 h-10 rounded-full bg-white/90 flex items-center justify-center">
                <span class="text-blue-600 text-lg ml-0.5">▶</span>
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- Step 2: Overlay Editor -->
      <div v-else class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <!-- Left: Layer panel -->
        <div class="lg:col-span-3 space-y-4">
          <!-- Back button & overlay name -->
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-4">
            <button @click="selectedAsset = null; selectedAssetId = null" class="text-sm text-blue-600 hover:text-blue-700 mb-3 flex items-center gap-1">
              ← Anderes Video
            </button>
            <label for="overlay-name" class="sr-only">Overlay-Name</label>
            <input
              id="overlay-name"
              v-model="overlayName"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm font-medium"
              placeholder="Overlay-Name"
              aria-label="Overlay-Name"
            />
          </div>

          <!-- Add Layer Buttons -->
          <div data-tour="vo-layer-add" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-4">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Layer hinzufügen</h3>
            <div class="grid grid-cols-2 gap-2">
              <button
                v-for="preset in layerPresets"
                :key="preset.type"
                @click="addLayer(preset)"
                class="flex items-center gap-1.5 px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/30 text-xs font-medium text-gray-700 dark:text-gray-300 transition-colors"
              >
                <AppIcon :name="preset.icon" class="w-4 h-4" />
                <span>{{ preset.label }}</span>
              </button>
            </div>
          </div>

          <!-- Layer List -->
          <div data-tour="vo-layer-list" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-4">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
              Layers ({{ layers.length }})
            </h3>
            <div v-if="layers.length === 0" class="text-center py-4 text-gray-400 text-xs">
              Noch keine Layers. Füge oben welche hinzu.
            </div>
            <div v-else class="space-y-1.5">
              <div
                v-for="(layer, idx) in layers"
                :key="idx"
                @click="selectedLayerIndex = idx"
                :class="[
                  'flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-xs transition-colors',
                  selectedLayerIndex === idx
                    ? 'bg-blue-100 dark:bg-blue-900/40 border border-blue-300 dark:border-blue-700'
                    : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700',
                ]"
              >
                <!-- Visibility indicator -->
                <span :class="isLayerVisible(layer) ? 'text-green-500' : 'text-gray-300'" class="text-xs">●</span>
                <!-- Type icon -->
                <AppIcon :name="layerPresets.find(p => p.type === layer.type)?.icon || 'pencil-square'" class="w-3.5 h-3.5" />
                <!-- Name/text preview -->
                <span class="flex-1 truncate text-gray-700 dark:text-gray-300">
                  {{ layer.text.substring(0, 20) || '(leer)' }}
                </span>
                <!-- Time range badge -->
                <span class="text-[10px] text-gray-400 whitespace-nowrap">
                  {{ formatTime(layer.startTime) }}-{{ layer.endTime < 0 ? 'Ende' : formatTime(layer.endTime) }}
                </span>
                <!-- Actions -->
                <div class="flex gap-0.5">
                  <button @click.stop="moveLayerUp(idx)" :disabled="idx === 0" class="text-gray-400 hover:text-gray-600 disabled:opacity-30" title="Nach oben" aria-label="Ebene nach oben verschieben">↑</button>
                  <button @click.stop="moveLayerDown(idx)" :disabled="idx === layers.length - 1" class="text-gray-400 hover:text-gray-600 disabled:opacity-30" title="Nach unten" aria-label="Ebene nach unten verschieben">↓</button>
                  <button @click.stop="duplicateLayer(idx)" class="text-gray-400 hover:text-blue-500" title="Duplizieren" aria-label="Ebene duplizieren">⧉</button>
                  <button @click.stop="removeLayer(idx)" class="text-gray-400 hover:text-red-500" title="Löschen" aria-label="Ebene löschen">✕</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Center: Video preview with overlay layers -->
        <div class="lg:col-span-6 space-y-4">
          <div data-tour="vo-preview" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden">
            <!-- Video Preview Area -->
            <div ref="previewContainer" class="relative bg-black aspect-video">
              <video
                ref="videoEl"
                :src="videoSrc"
                class="w-full h-full object-contain"
                @timeupdate="onVideoTimeUpdate"
                @loadedmetadata="onVideoLoaded"
                @ended="isPlaying = false"
                @pause="isPlaying = false"
                @play="isPlaying = true"
                preload="metadata"
                playsinline
              />

              <!-- Overlay layers rendered on top of video (draggable) -->
              <div class="absolute inset-0 pointer-events-none"
                   @touchmove="onOverlayTouchMove"
                   @touchend="onOverlayTouchEnd">
                <div
                  v-for="(layer, idx) in layers"
                  :key="'overlay-' + idx"
                  :style="{
                    position: 'absolute',
                    left: layer.x + '%',
                    top: layer.y + '%',
                    width: layer.width + '%',
                    minHeight: layer.height + '%',
                    fontSize: (layer.fontSize * 0.5) + 'px',
                    fontFamily: layer.fontFamily || 'Inter, sans-serif',
                    color: layer.color || '#FFFFFF',
                    backgroundColor: isLayerVisible(layer) ? (layer.bgColor || 'transparent') : 'transparent',
                    fontWeight: layer.bold ? 'bold' : 'normal',
                    fontStyle: layer.italic ? 'italic' : 'normal',
                    textAlign: layer.textAlign || 'left',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    lineHeight: '1.3',
                    overflow: 'hidden',
                    boxSizing: 'border-box',
                    pointerEvents: 'auto',
                    cursor: isDragging && dragLayerIndex === idx ? 'grabbing' : 'grab',
                    userSelect: 'none',
                    ...getAnimationStyle(layer),
                    border: selectedLayerIndex === idx ? '2px dashed #FDD000' : '2px dashed transparent',
                  }"
                  @mousedown="onOverlayMouseDown($event, idx)"
                  @touchstart="onOverlayTouchStart($event, idx)"
                >
                  {{ layer.text }}
                </div>
              </div>
            </div>

            <!-- Playback Controls -->
            <div class="p-3 bg-gray-900">
              <!-- Timeline -->
              <div class="mb-2">
                <div
                  class="relative h-6 bg-gray-700 rounded-full cursor-pointer overflow-hidden"
                  @click="onTimelineClick"
                >
                  <!-- Progress bar -->
                  <div
                    class="absolute top-0 left-0 h-full bg-blue-500/40 rounded-full"
                    :style="{ width: (videoDuration ? (currentTime / videoDuration * 100) : 0) + '%' }"
                  />
                  <!-- Layer time ranges -->
                  <div
                    v-for="(layer, idx) in layers"
                    :key="'tl-' + idx"
                    class="absolute top-0 h-full rounded-sm"
                    :class="selectedLayerIndex === idx ? 'bg-yellow-400/50 z-10' : 'bg-green-400/25'"
                    :style="{
                      left: (videoDuration ? (layer.startTime / videoDuration * 100) : 0) + '%',
                      width: (videoDuration ? (((layer.endTime < 0 ? videoDuration : layer.endTime) - layer.startTime) / videoDuration * 100) : 0) + '%',
                    }"
                  />
                  <!-- Playhead -->
                  <div
                    class="absolute top-0 w-0.5 h-full bg-white z-20"
                    :style="{ left: (videoDuration ? (currentTime / videoDuration * 100) : 0) + '%' }"
                  />
                </div>
              </div>

              <!-- Controls row -->
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <button
                    @click="togglePlay"
                    class="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors"
                  >
                    {{ isPlaying ? '⏸' : '▶' }}
                  </button>
                  <button @click="seekTo(0)" class="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white text-xs">⏮</button>
                  <span class="text-white text-xs font-mono">
                    {{ formatTime(currentTime) }} / {{ formatTime(videoDuration) }}
                  </span>
                </div>

                <!-- Action buttons -->
                <div data-tour="vo-render" class="flex items-center gap-2">
                  <button
                    @click="saveOverlay"
                    :disabled="saving || !hasChanges"
                    class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white text-xs rounded-lg flex items-center gap-1 transition-colors"
                  >
                    <AppIcon v-if="saving" name="clock" class="w-3.5 h-3.5 animate-spin" />
                    <AppIcon v-else name="document" class="w-3.5 h-3.5" />
                    Speichern
                  </button>
                  <button
                    @click="renderVideo"
                    :disabled="rendering || layers.length === 0"
                    class="px-3 py-1.5 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white text-xs rounded-lg flex items-center gap-1 transition-colors"
                  >
                    <AppIcon v-if="rendering" name="clock" class="w-3.5 h-3.5 animate-spin" />
                    <AppIcon v-else name="film" class="w-3.5 h-3.5" />
                    Rendern
                  </button>
                  <button
                    v-if="overlayId"
                    @click="deleteOverlay"
                    class="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs rounded-lg transition-colors"
                  >
                    <AppIcon name="archive" class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <!-- Render status -->
              <div v-if="renderStatus === 'done' && renderedPath" class="mt-2 p-2 bg-green-900/40 rounded-lg flex items-center justify-between">
                <span class="text-green-400 text-xs flex items-center gap-1"><AppIcon name="check-circle" class="w-3.5 h-3.5 inline-block" /> Gerendert!</span>
                <a
                  :href="renderedPath"
                  target="_blank"
                  class="text-xs text-green-300 underline hover:text-green-200"
                >
                  Video herunterladen
                </a>
              </div>
              <div v-else-if="renderStatus === 'rendering'" class="mt-2 p-2 bg-yellow-900/40 rounded-lg">
                <span class="text-yellow-400 text-xs animate-pulse flex items-center gap-1"><AppIcon name="clock" class="w-3.5 h-3.5 inline-block" /> Video wird gerendert...</span>
              </div>
              <div v-else-if="renderStatus === 'error'" class="mt-2 p-2 bg-red-900/40 rounded-lg">
                <span class="text-red-400 text-xs flex items-center gap-1"><AppIcon name="x-circle" class="w-3.5 h-3.5 inline-block" /> Rendering fehlgeschlagen</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Layer properties panel -->
        <div class="lg:col-span-3">
          <div data-tour="vo-properties" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-4 sticky top-6">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
              Layer-Eigenschaften
            </h3>

            <div v-if="!selectedLayer" class="text-center py-8 text-gray-400 text-xs">
              Wähle einen Layer aus der Liste aus.
            </div>

            <div v-else class="space-y-3">
              <!-- Text content -->
              <div>
                <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Text</label>
                <textarea
                  v-model="selectedLayer.text"
                  rows="2"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm resize-none"
                />
              </div>

              <!-- Position -->
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">X Position (%)</label>
                  <input type="number" v-model.number="selectedLayer.x" min="0" max="100" step="1"
                    class="w-full px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Y Position (%)</label>
                  <input type="number" v-model.number="selectedLayer.y" min="0" max="100" step="1"
                    class="w-full px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
                </div>
              </div>

              <!-- Size -->
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Breite (%)</label>
                  <input type="number" v-model.number="selectedLayer.width" min="5" max="100" step="1"
                    class="w-full px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Höhe (%)</label>
                  <input type="number" v-model.number="selectedLayer.height" min="2" max="100" step="1"
                    class="w-full px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
                </div>
              </div>

              <!-- Font -->
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Schriftgröße</label>
                  <input type="number" v-model.number="selectedLayer.fontSize" min="8" max="120" step="1"
                    class="w-full px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Schriftart</label>
                  <select v-model="selectedLayer.fontFamily"
                    class="w-full px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm">
                    <option v-for="f in fontOptions" :key="f" :value="f">{{ f }}</option>
                  </select>
                </div>
              </div>

              <!-- Style buttons -->
              <div class="flex gap-2">
                <button
                  @click="selectedLayer.bold = !selectedLayer.bold"
                  :class="selectedLayer.bold ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'"
                  class="px-3 py-1.5 rounded-lg text-sm font-bold transition-colors"
                >B</button>
                <button
                  @click="selectedLayer.italic = !selectedLayer.italic"
                  :class="selectedLayer.italic ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'"
                  class="px-3 py-1.5 rounded-lg text-sm italic transition-colors"
                >I</button>
                <button
                  v-for="align in ['left', 'center', 'right']"
                  :key="align"
                  @click="selectedLayer.textAlign = align"
                  :class="selectedLayer.textAlign === align ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'"
                  class="px-3 py-1.5 rounded-lg text-xs transition-colors"
                ><template v-if="align === 'left'">&#9665;</template><AppIcon v-else-if="align === 'center'" name="bars-3" class="w-3.5 h-3.5 inline" /><template v-else>&#9655;</template></button>
              </div>

              <!-- Colors -->
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Textfarbe</label>
                  <div class="flex items-center gap-2">
                    <input type="color" v-model="selectedLayer.color" class="w-8 h-8 rounded border cursor-pointer" />
                    <input type="text" v-model="selectedLayer.color"
                      class="flex-1 px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-xs font-mono" />
                  </div>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Hintergrund</label>
                  <div class="flex items-center gap-1">
                    <button
                      v-for="bg in ['rgba(0,0,0,0.6)', 'rgba(0,0,0,0.8)', TREFF_BLUE, TREFF_YELLOW, TREFF_DARK, 'transparent']"
                      :key="bg"
                      @click="selectedLayer.bgColor = bg"
                      class="w-6 h-6 rounded border border-gray-300 cursor-pointer"
                      :class="selectedLayer.bgColor === bg ? 'ring-2 ring-blue-500' : ''"
                      :style="{ backgroundColor: bg === 'transparent' ? '#fff' : bg }"
                      :title="bg"
                    >
                      <span v-if="bg === 'transparent'" class="text-[8px] text-red-400">✕</span>
                    </button>
                  </div>
                </div>
              </div>

              <!-- Opacity slider -->
              <div>
                <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Deckkraft: {{ Math.round((selectedLayer.opacity || 1) * 100) }}%
                </label>
                <input type="range" v-model.number="selectedLayer.opacity" min="0" max="1" step="0.05"
                  class="w-full accent-blue-500" />
              </div>

              <!-- Time controls -->
              <div class="border-t border-gray-200 dark:border-gray-700 pt-3">
                <h4 class="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">Zeitsteuerung</h4>
                <div class="grid grid-cols-2 gap-2">
                  <div>
                    <label class="block text-xs text-gray-500 mb-1">Einblenden bei (s)</label>
                    <input type="number" v-model.number="selectedLayer.startTime" min="0" :max="videoDuration" step="0.1"
                      class="w-full px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
                  </div>
                  <div>
                    <label class="block text-xs text-gray-500 mb-1">Ausblenden bei (s)</label>
                    <input type="number" v-model.number="selectedLayer.endTime" min="-1" :max="videoDuration" step="0.1"
                      class="w-full px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
                    <p class="text-[10px] text-gray-400 mt-0.5">-1 = bis Ende</p>
                  </div>
                </div>
                <!-- Quick time buttons -->
                <div class="flex gap-1 mt-2">
                  <button @click="selectedLayer.startTime = currentTime"
                    class="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-[10px] text-gray-600 dark:text-gray-400 hover:bg-blue-100 dark:hover:bg-blue-900/30">
                    Start = jetzt ({{ formatTime(currentTime) }})
                  </button>
                  <button @click="selectedLayer.endTime = currentTime"
                    class="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-[10px] text-gray-600 dark:text-gray-400 hover:bg-blue-100 dark:hover:bg-blue-900/30">
                    Ende = jetzt ({{ formatTime(currentTime) }})
                  </button>
                </div>
              </div>

              <!-- Animation -->
              <div class="border-t border-gray-200 dark:border-gray-700 pt-3">
                <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">Animation</label>
                <div class="grid grid-cols-2 gap-1.5">
                  <button
                    v-for="anim in animationOptions"
                    :key="anim.value"
                    @click="selectedLayer.animation = anim.value"
                    :class="selectedLayer.animation === anim.value
                      ? 'bg-blue-100 dark:bg-blue-900/40 border-blue-400 text-blue-700 dark:text-blue-300'
                      : 'bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-600'"
                    class="px-2 py-1.5 rounded-lg border text-xs flex items-center gap-1 transition-colors"
                  >
                    <AppIcon v-if="anim.icon" :name="anim.icon" class="w-3.5 h-3.5" />
                    <span v-else>&mdash;</span>
                    <span>{{ anim.label }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Tour System -->
    <VideoWorkflowTour ref="workflowTourRef" />
    <TourSystem page-key="video-overlays" />
  </div>
</template>
