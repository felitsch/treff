<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import TourSystem from '@/components/common/TourSystem.vue'
import VideoWorkflowTour from '@/components/common/VideoWorkflowTour.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const toast = useToast()

// ---- State ----
// Video selection
const videoAssets = ref([])
const loadingAssets = ref(true)
const selectedVideo = ref(null)

// Music library
const musicTracks = ref([])
const loadingTracks = ref(true)
const selectedTrack = ref(null)
const musicCategories = ref([])
const activeCategory = ref('all')
const musicSearch = ref('')

// User audio assets (uploaded audio)
const userAudioAssets = ref([])
const audioSource = ref('library') // 'library' or 'upload'
const selectedUserAudio = ref(null)

// Waveform
const videoWaveform = ref([])
const musicWaveform = ref([])
const loadingVideoWaveform = ref(false)
const loadingMusicWaveform = ref(false)

// Mixer settings
const originalVolume = ref(1.0)
const musicVolume = ref(0.5)
const fadeInSeconds = ref(1.0)
const fadeOutSeconds = ref(2.0)
const saveAsNew = ref(true)

// Mixing state
const mixing = ref(false)
const mixProgress = ref(0)
const mixResult = ref(null)
const mixError = ref(null)
const tourRef = ref(null)
const workflowTourRef = ref(null)

// ---- Computed ----
const filteredTracks = computed(() => {
  let tracks = musicTracks.value
  if (activeCategory.value !== 'all') {
    tracks = tracks.filter(t => t.category === activeCategory.value)
  }
  if (musicSearch.value.trim()) {
    const q = musicSearch.value.toLowerCase()
    tracks = tracks.filter(t =>
      t.name.toLowerCase().includes(q) ||
      (t.description && t.description.toLowerCase().includes(q))
    )
  }
  return tracks
})

const selectedAudio = computed(() => {
  if (audioSource.value === 'library') return selectedTrack.value
  return selectedUserAudio.value
})

const canMix = computed(() => {
  return selectedVideo.value && selectedAudio.value && !mixing.value
})

const originalVolumeLabel = computed(() => {
  if (originalVolume.value === 0) return 'Stumm'
  if (originalVolume.value <= 0.3) return 'Leise'
  if (originalVolume.value <= 0.7) return 'Mittel'
  if (originalVolume.value <= 1.0) return 'Normal'
  return 'Laut'
})

const musicVolumeLabel = computed(() => {
  if (musicVolume.value === 0) return 'Stumm'
  if (musicVolume.value <= 0.3) return 'Leise'
  if (musicVolume.value <= 0.7) return 'Mittel'
  if (musicVolume.value <= 1.0) return 'Normal'
  return 'Laut'
})

const categoryIcons = {
  upbeat: 'trophy',
  emotional: 'heart',
  chill: 'globe',
  dramatic: 'theater',
  inspirational: 'sparkles',
  fun: 'face-smile',
}

const moodLabels = {
  happy: 'Fröhlich',
  sad: 'Melancholisch',
  energetic: 'Energetisch',
  calm: 'Ruhig',
  epic: 'Episch',
  playful: 'Verspielt',
}

// ---- Methods ----
const fetchVideoAssets = async () => {
  loadingAssets.value = true
  try {
    const { data } = await api.get('/api/assets', { params: { type: 'video' } })
    // Filter to only video assets
    videoAssets.value = (Array.isArray(data) ? data : data.items || []).filter(a =>
      a.file_type && a.file_type.startsWith('video/')
    )
  } catch (e) {
    // Error toast shown by API interceptor
  } finally {
    loadingAssets.value = false
  }
}

const fetchMusicTracks = async () => {
  loadingTracks.value = true
  try {
    const [tracksRes, catsRes] = await Promise.all([
      api.get('/api/audio/music'),
      api.get('/api/audio/music/categories'),
    ])
    musicTracks.value = tracksRes.data
    musicCategories.value = catsRes.data
  } catch (e) {
    // Error toast shown by API interceptor
  } finally {
    loadingTracks.value = false
  }
}

const fetchUserAudioAssets = async () => {
  try {
    const { data } = await api.get('/api/assets', { params: { type: 'audio' } })
    userAudioAssets.value = (Array.isArray(data) ? data : data.items || []).filter(a =>
      a.file_type && a.file_type.startsWith('audio/')
    )
  } catch (e) {
    // Error toast shown by API interceptor
  }
}

const selectVideo = async (asset) => {
  selectedVideo.value = asset
  mixResult.value = null
  mixError.value = null
  // Load waveform for video's audio track
  loadingVideoWaveform.value = true
  try {
    const { data } = await api.get(`/api/audio/waveform/asset/${asset.id}`)
    videoWaveform.value = data.waveform || []
  } catch (e) {
    videoWaveform.value = []
  } finally {
    loadingVideoWaveform.value = false
  }
}

const selectMusicTrack = async (track) => {
  selectedTrack.value = track
  audioSource.value = 'library'
  selectedUserAudio.value = null
  mixResult.value = null
  // Load waveform for music track
  loadingMusicWaveform.value = true
  try {
    const { data } = await api.get(`/api/audio/waveform/library/${track.id}`)
    musicWaveform.value = data.waveform || []
  } catch (e) {
    musicWaveform.value = []
  } finally {
    loadingMusicWaveform.value = false
  }
}

const selectUserAudio = async (asset) => {
  selectedUserAudio.value = asset
  audioSource.value = 'upload'
  selectedTrack.value = null
  mixResult.value = null
  // Load waveform for user audio
  loadingMusicWaveform.value = true
  try {
    const { data } = await api.get(`/api/audio/waveform/asset/${asset.id}`)
    musicWaveform.value = data.waveform || []
  } catch (e) {
    musicWaveform.value = []
  } finally {
    loadingMusicWaveform.value = false
  }
}

const formatDuration = (seconds) => {
  if (!seconds) return '--:--'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

const formatFileSize = (bytes) => {
  if (!bytes) return '--'
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const startMix = async () => {
  if (!canMix.value) return

  mixing.value = true
  mixProgress.value = 0
  mixResult.value = null
  mixError.value = null

  // Simulate progress (actual mixing happens server-side)
  const progressInterval = setInterval(() => {
    if (mixProgress.value < 90) {
      mixProgress.value += Math.random() * 15
    }
  }, 500)

  try {
    const payload = {
      video_asset_id: selectedVideo.value.id,
      audio_source: audioSource.value,
      audio_id: audioSource.value === 'library' ? selectedTrack.value.id : selectedUserAudio.value.id,
      original_volume: originalVolume.value,
      music_volume: musicVolume.value,
      fade_in_seconds: fadeInSeconds.value,
      fade_out_seconds: fadeOutSeconds.value,
      save_as_new: saveAsNew.value,
    }

    const { data } = await api.post('/api/audio/mix', payload)
    mixProgress.value = 100
    mixResult.value = data
    toast.success('Audio-Mix erfolgreich erstellt!')

    // Refresh video assets to show the new mixed video
    if (saveAsNew.value) {
      await fetchVideoAssets()
    }
  } catch (e) {
    mixError.value = e.response?.data?.detail || 'Audio-Mixing fehlgeschlagen'
    toast.error('Audio-Mixing fehlgeschlagen')
  } finally {
    clearInterval(progressInterval)
    mixing.value = false
  }
}

const downloadResult = () => {
  if (!mixResult.value?.file_path) return
  const link = document.createElement('a')
  link.href = mixResult.value.file_path
  link.download = mixResult.value.original_filename || 'mixed-video.mp4'
  link.click()
}

const resetMixer = () => {
  selectedVideo.value = null
  selectedTrack.value = null
  selectedUserAudio.value = null
  videoWaveform.value = []
  musicWaveform.value = []
  originalVolume.value = 1.0
  musicVolume.value = 0.5
  fadeInSeconds.value = 1.0
  fadeOutSeconds.value = 2.0
  saveAsNew.value = true
  mixResult.value = null
  mixError.value = null
  mixProgress.value = 0
}

// ---- Lifecycle ----
onMounted(async () => {
  await Promise.all([
    fetchVideoAssets(),
    fetchMusicTracks(),
    fetchUserAudioAssets(),
  ])
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div data-tour="am-header" class="flex items-start justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <AppIcon name="musical-note" class="w-6 h-6" /> Musik- und Audio-Layer
          </h1>
          <p class="text-gray-500 dark:text-gray-400 mt-1">
            Hintergrundmusik und Audio-Effekte zu Videos hinzufügen. Lautstärke-Kontrolle für Original-Audio vs. Musik.
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
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- LEFT COLUMN: Video Selection + Audio Source -->
        <div class="lg:col-span-1 space-y-6">

          <!-- Step 1: Video Selection -->
          <div data-tour="am-video-select" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
            <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
              <span class="bg-treff-blue text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">1</span>
              Video wählen
            </h2>

            <div v-if="loadingAssets" class="text-center py-8 text-gray-400">
              <div class="animate-spin inline-block w-6 h-6 border-2 border-treff-blue border-t-transparent rounded-full mb-2"></div>
              <p class="text-sm">Videos laden...</p>
            </div>

            <EmptyState
              v-else-if="videoAssets.length === 0"
              svgIcon="film"
              title="Keine Videos vorhanden"
              description="Lade zuerst ein Video in der Asset-Bibliothek hoch, um Musik und Audio hinzuzufügen."
              actionLabel="Zu Assets"
              actionTo="/library/assets"
              :compact="true"
            />

            <div v-else class="space-y-2 max-h-64 overflow-y-auto">
              <button
                v-for="asset in videoAssets"
                :key="asset.id"
                @click="selectVideo(asset)"
                :class="[
                  'w-full text-left p-3 rounded-lg border transition-all',
                  selectedVideo?.id === asset.id
                    ? 'border-treff-blue bg-treff-blue/5 ring-1 ring-treff-blue'
                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                ]"
              >
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 rounded bg-gray-100 dark:bg-gray-700 flex items-center justify-center overflow-hidden flex-shrink-0">
                    <img loading="lazy" v-if="asset.thumbnail_path" :src="asset.thumbnail_path" class="w-full h-full object-cover" :alt="asset.original_filename || 'Video-Vorschau'" />
                    <AppIcon v-else name="film" class="w-5 h-5" />
                  </div>
                  <div class="min-w-0 flex-1">
                    <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {{ asset.original_filename || asset.filename }}
                    </p>
                    <div class="flex items-center gap-2 text-xs text-gray-500">
                      <span>{{ formatDuration(asset.duration_seconds) }}</span>
                      <span>{{ formatFileSize(asset.file_size) }}</span>
                      <span v-if="asset.width">{{ asset.width }}x{{ asset.height }}</span>
                    </div>
                  </div>
                  <span v-if="selectedVideo?.id === asset.id" class="text-treff-blue text-lg flex-shrink-0">&#10003;</span>
                </div>
              </button>
            </div>
          </div>

          <!-- Step 2: Audio Source Toggle -->
          <div data-tour="am-audio-source" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
            <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
              <span class="bg-treff-blue text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">2</span>
              Audio-Quelle
            </h2>

            <div class="flex rounded-lg bg-gray-100 dark:bg-gray-700 p-1 mb-4">
              <button
                @click="audioSource = 'library'"
                :class="[
                  'flex-1 py-2 px-3 text-xs font-medium rounded-md transition-all',
                  audioSource === 'library'
                    ? 'bg-white dark:bg-gray-600 text-treff-blue shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
                ]"
              >
                <AppIcon name="library" class="w-3.5 h-3.5 inline-block" /> Musik-Bibliothek
              </button>
              <button
                @click="audioSource = 'upload'"
                :class="[
                  'flex-1 py-2 px-3 text-xs font-medium rounded-md transition-all',
                  audioSource === 'upload'
                    ? 'bg-white dark:bg-gray-600 text-treff-blue shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
                ]"
              >
                <AppIcon name="microphone" class="w-3.5 h-3.5 inline-block" /> Eigene Audios
              </button>
            </div>

            <!-- Music Library -->
            <div v-if="audioSource === 'library'">
              <!-- Search -->
              <input
                v-model="musicSearch"
                type="text"
                placeholder="Musik suchen..."
                class="w-full mb-3 px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-1 focus:ring-treff-blue focus:border-treff-blue"
              />

              <!-- Category pills -->
              <div class="flex flex-wrap gap-1.5 mb-3">
                <button
                  @click="activeCategory = 'all'"
                  :class="[
                    'px-2.5 py-1 text-xs rounded-full transition-all',
                    activeCategory === 'all'
                      ? 'bg-treff-blue text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
                  ]"
                >
                  Alle
                </button>
                <button
                  v-for="cat in musicCategories"
                  :key="cat.category"
                  @click="activeCategory = cat.category"
                  :class="[
                    'px-2.5 py-1 text-xs rounded-full transition-all',
                    activeCategory === cat.category
                      ? 'bg-treff-blue text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
                  ]"
                >
                  <AppIcon :name="categoryIcons[cat.category] || 'musical-note'" class="w-3.5 h-3.5 inline-block" /> {{ cat.category }} ({{ cat.count }})
                </button>
              </div>

              <!-- Track list -->
              <div v-if="loadingTracks" class="text-center py-6 text-gray-400">
                <div class="animate-spin inline-block w-5 h-5 border-2 border-treff-blue border-t-transparent rounded-full"></div>
              </div>

              <EmptyState
                v-else-if="filteredTracks.length === 0"
                svgIcon="musical-note"
                title="Keine Tracks gefunden"
                description="Versuche eine andere Kategorie oder warte, bis Musik-Tracks verfügbar sind."
                :compact="true"
              />

              <div v-else class="space-y-1.5 max-h-72 overflow-y-auto">
                <button
                  v-for="track in filteredTracks"
                  :key="track.id"
                  @click="selectMusicTrack(track)"
                  :class="[
                    'w-full text-left p-2.5 rounded-lg border transition-all',
                    selectedTrack?.id === track.id
                      ? 'border-treff-blue bg-treff-blue/5 ring-1 ring-treff-blue'
                      : 'border-gray-100 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                  ]"
                >
                  <div class="flex items-center gap-2">
                    <AppIcon :name="categoryIcons[track.category] || 'musical-note'" class="w-5 h-5 flex-shrink-0" />
                    <div class="min-w-0 flex-1">
                      <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ track.name }}</p>
                      <div class="flex items-center gap-2 text-xs text-gray-500">
                        <span>{{ formatDuration(track.duration_seconds) }}</span>
                        <span v-if="track.bpm">{{ track.bpm }} BPM</span>
                        <span v-if="track.mood" class="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700">
                          {{ moodLabels[track.mood] || track.mood }}
                        </span>
                      </div>
                    </div>
                    <div class="flex items-center gap-1 flex-shrink-0">
                      <span v-if="track.usage_count > 0" class="text-xs text-gray-400">{{ track.usage_count }}x</span>
                      <span v-if="selectedTrack?.id === track.id" class="text-treff-blue">&#10003;</span>
                    </div>
                  </div>
                  <p v-if="track.description" class="text-xs text-gray-400 mt-1 line-clamp-1">{{ track.description }}</p>
                </button>
              </div>
            </div>

            <!-- User Audio Assets -->
            <div v-else>
              <div v-if="userAudioAssets.length === 0" class="text-center py-6 text-gray-400">
                <AppIcon name="microphone" class="w-8 h-8 mx-auto mb-2" />
                <p class="text-sm">Keine Audio-Dateien hochgeladen.</p>
                <p class="text-xs mt-1">Lade MP3, WAV oder AAC in der Assets-Seite hoch.</p>
              </div>

              <div v-else class="space-y-1.5 max-h-72 overflow-y-auto">
                <button
                  v-for="asset in userAudioAssets"
                  :key="asset.id"
                  @click="selectUserAudio(asset)"
                  :class="[
                    'w-full text-left p-2.5 rounded-lg border transition-all',
                    selectedUserAudio?.id === asset.id
                      ? 'border-treff-blue bg-treff-blue/5 ring-1 ring-treff-blue'
                      : 'border-gray-100 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                  ]"
                >
                  <div class="flex items-center gap-2">
                    <AppIcon name="microphone" class="w-5 h-5 flex-shrink-0" />
                    <div class="min-w-0 flex-1">
                      <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {{ asset.original_filename || asset.filename }}
                      </p>
                      <div class="flex items-center gap-2 text-xs text-gray-500">
                        <span>{{ formatDuration(asset.duration_seconds) }}</span>
                        <span>{{ formatFileSize(asset.file_size) }}</span>
                      </div>
                    </div>
                    <span v-if="selectedUserAudio?.id === asset.id" class="text-treff-blue flex-shrink-0">&#10003;</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- CENTER COLUMN: Waveform + Mixer -->
        <div class="lg:col-span-2 space-y-6">

          <!-- Waveform Visualizations -->
          <div data-tour="am-waveform" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
            <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
              <span class="bg-treff-blue text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">3</span>
              Audio-Waveform Visualisierung
            </h2>

            <!-- Video audio waveform -->
            <div class="mb-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-medium text-gray-600 dark:text-gray-400">
                  <AppIcon name="film" class="w-3.5 h-3.5 inline-block" /> Original-Audio
                  <span v-if="selectedVideo" class="text-gray-400">({{ selectedVideo.original_filename || selectedVideo.filename }})</span>
                </span>
                <span class="text-xs text-gray-400">{{ originalVolumeLabel }} ({{ Math.round(originalVolume * 100) }}%)</span>
              </div>
              <div class="h-16 bg-gray-50 dark:bg-gray-900 rounded-lg overflow-hidden flex items-end px-1 gap-px border border-gray-100 dark:border-gray-700">
                <template v-if="loadingVideoWaveform">
                  <div class="w-full h-full flex items-center justify-center">
                    <div class="animate-spin w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full"></div>
                  </div>
                </template>
                <template v-else-if="videoWaveform.length > 0">
                  <div
                    v-for="(val, idx) in videoWaveform"
                    :key="'v-' + idx"
                    class="flex-1 rounded-t-sm transition-all duration-200"
                    :style="{
                      height: Math.max(2, val * originalVolume * 100) + '%',
                      backgroundColor: originalVolume === 0 ? '#d1d5db' : `rgba(76, 139, 194, ${0.4 + val * 0.6})`,
                    }"
                  ></div>
                </template>
                <template v-else>
                  <div class="w-full h-full flex items-center justify-center text-xs text-gray-400">
                    {{ selectedVideo ? 'Waveform wird geladen...' : 'Wähle ein Video' }}
                  </div>
                </template>
              </div>
            </div>

            <!-- Music/audio waveform -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-medium text-gray-600 dark:text-gray-400">
                  <AppIcon name="musical-note" class="w-3.5 h-3.5 inline-block" /> Hintergrundmusik
                  <span v-if="selectedAudio" class="text-gray-400">({{ selectedAudio.name || selectedAudio.original_filename || selectedAudio.filename }})</span>
                </span>
                <span class="text-xs text-gray-400">{{ musicVolumeLabel }} ({{ Math.round(musicVolume * 100) }}%)</span>
              </div>
              <div class="h-16 bg-gray-50 dark:bg-gray-900 rounded-lg overflow-hidden flex items-end px-1 gap-px border border-gray-100 dark:border-gray-700">
                <template v-if="loadingMusicWaveform">
                  <div class="w-full h-full flex items-center justify-center">
                    <div class="animate-spin w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full"></div>
                  </div>
                </template>
                <template v-else-if="musicWaveform.length > 0">
                  <div
                    v-for="(val, idx) in musicWaveform"
                    :key="'m-' + idx"
                    class="flex-1 rounded-t-sm transition-all duration-200"
                    :style="{
                      height: Math.max(2, val * musicVolume * 100) + '%',
                      backgroundColor: musicVolume === 0 ? '#d1d5db' : `rgba(253, 208, 0, ${0.4 + val * 0.6})`,
                    }"
                  ></div>
                </template>
                <template v-else>
                  <div class="w-full h-full flex items-center justify-center text-xs text-gray-400">
                    {{ selectedAudio ? 'Waveform wird geladen...' : 'Wähle einen Track' }}
                  </div>
                </template>
              </div>
            </div>
          </div>

          <!-- Volume Mixer -->
          <div data-tour="am-mixer" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
            <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
              <span class="bg-treff-blue text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">4</span>
              Lautstärke-Mixer
            </h2>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <!-- Original Volume -->
              <div>
                <div class="flex items-center justify-between mb-2">
                  <label class="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-1">
                    <AppIcon name="film" class="w-4 h-4 inline-block" /> Original-Audio
                  </label>
                  <span class="text-sm font-mono text-treff-blue">{{ Math.round(originalVolume * 100) }}%</span>
                </div>
                <input
                  v-model.number="originalVolume"
                  type="range"
                  min="0"
                  max="2"
                  step="0.05"
                  class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-treff-blue"
                />
                <div class="flex justify-between text-xs text-gray-400 mt-1">
                  <span>Stumm</span>
                  <span>Normal</span>
                  <span>Laut</span>
                </div>
                <!-- Quick presets -->
                <div class="flex gap-1.5 mt-2">
                  <button
                    v-for="preset in [0, 0.3, 0.5, 0.7, 1.0, 1.5]"
                    :key="'ov-' + preset"
                    @click="originalVolume = preset"
                    :class="[
                      'px-2 py-1 text-xs rounded border transition-all',
                      Math.abs(originalVolume - preset) < 0.01
                        ? 'border-treff-blue bg-treff-blue/10 text-treff-blue'
                        : 'border-gray-200 dark:border-gray-600 text-gray-500 hover:border-gray-300'
                    ]"
                  >
                    {{ Math.round(preset * 100) }}%
                  </button>
                </div>
              </div>

              <!-- Music Volume -->
              <div>
                <div class="flex items-center justify-between mb-2">
                  <label class="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-1">
                    <AppIcon name="musical-note" class="w-4 h-4 inline-block" /> Hintergrundmusik
                  </label>
                  <span class="text-sm font-mono text-amber-500">{{ Math.round(musicVolume * 100) }}%</span>
                </div>
                <input
                  v-model.number="musicVolume"
                  type="range"
                  min="0"
                  max="2"
                  step="0.05"
                  class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-amber-500"
                />
                <div class="flex justify-between text-xs text-gray-400 mt-1">
                  <span>Stumm</span>
                  <span>Normal</span>
                  <span>Laut</span>
                </div>
                <!-- Quick presets -->
                <div class="flex gap-1.5 mt-2">
                  <button
                    v-for="preset in [0, 0.2, 0.4, 0.6, 0.8, 1.0]"
                    :key="'mv-' + preset"
                    @click="musicVolume = preset"
                    :class="[
                      'px-2 py-1 text-xs rounded border transition-all',
                      Math.abs(musicVolume - preset) < 0.01
                        ? 'border-amber-500 bg-amber-50 text-amber-600'
                        : 'border-gray-200 dark:border-gray-600 text-gray-500 hover:border-gray-300'
                    ]"
                  >
                    {{ Math.round(preset * 100) }}%
                  </button>
                </div>
              </div>
            </div>

            <!-- Visual balance indicator -->
            <div class="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
              <div class="flex items-center gap-3">
                <span class="text-xs text-gray-500 w-20">Balance:</span>
                <div class="flex-1 h-3 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden flex">
                  <div
                    class="h-full bg-treff-blue/60 transition-all duration-300"
                    :style="{ width: (originalVolume / (originalVolume + musicVolume || 1)) * 100 + '%' }"
                  ></div>
                  <div
                    class="h-full bg-amber-400/60 transition-all duration-300"
                    :style="{ width: (musicVolume / (originalVolume + musicVolume || 1)) * 100 + '%' }"
                  ></div>
                </div>
                <span class="text-xs text-gray-500 w-20 text-right">
                  {{ Math.round((originalVolume / (originalVolume + musicVolume || 1)) * 100) }}% /
                  {{ Math.round((musicVolume / (originalVolume + musicVolume || 1)) * 100) }}%
                </span>
              </div>
            </div>
          </div>

          <!-- Fade Effects -->
          <div data-tour="am-fade" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
            <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
              <span class="bg-treff-blue text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">5</span>
              Fade-Effekte
            </h2>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <!-- Fade In -->
              <div>
                <div class="flex items-center justify-between mb-2">
                  <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Fade-In (Start)
                  </label>
                  <span class="text-sm font-mono text-green-600">{{ fadeInSeconds.toFixed(1) }}s</span>
                </div>
                <input
                  v-model.number="fadeInSeconds"
                  type="range"
                  min="0"
                  max="10"
                  step="0.5"
                  class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-green-500"
                />
                <div class="flex justify-between text-xs text-gray-400 mt-1">
                  <span>Kein Fade</span>
                  <span>5s</span>
                  <span>10s</span>
                </div>
                <!-- Visual fade-in preview -->
                <div class="mt-2 h-4 bg-gray-100 dark:bg-gray-700 rounded overflow-hidden flex items-end">
                  <div
                    class="h-full rounded"
                    :style="{
                      width: '100%',
                      background: `linear-gradient(to right, transparent 0%, rgba(253,208,0,0.5) ${Math.max(5, fadeInSeconds * 10)}%, rgba(253,208,0,0.5) 100%)`,
                    }"
                  ></div>
                </div>
              </div>

              <!-- Fade Out -->
              <div>
                <div class="flex items-center justify-between mb-2">
                  <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Fade-Out (Ende)
                  </label>
                  <span class="text-sm font-mono text-red-500">{{ fadeOutSeconds.toFixed(1) }}s</span>
                </div>
                <input
                  v-model.number="fadeOutSeconds"
                  type="range"
                  min="0"
                  max="10"
                  step="0.5"
                  class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-red-500"
                />
                <div class="flex justify-between text-xs text-gray-400 mt-1">
                  <span>Kein Fade</span>
                  <span>5s</span>
                  <span>10s</span>
                </div>
                <!-- Visual fade-out preview -->
                <div class="mt-2 h-4 bg-gray-100 dark:bg-gray-700 rounded overflow-hidden flex items-end">
                  <div
                    class="h-full rounded"
                    :style="{
                      width: '100%',
                      background: `linear-gradient(to right, rgba(253,208,0,0.5) 0%, rgba(253,208,0,0.5) ${100 - Math.max(5, fadeOutSeconds * 10)}%, transparent 100%)`,
                    }"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Output Options + Mix Button -->
          <div data-tour="am-output" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
            <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
              <span class="bg-treff-blue text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">6</span>
              Ausgabe-Optionen
            </h2>

            <div class="flex items-center gap-6 mb-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  v-model="saveAsNew"
                  type="checkbox"
                  class="w-4 h-4 rounded border-gray-300 text-treff-blue focus:ring-treff-blue"
                  :true-value="true"
                  :false-value="false"
                />
                <span class="text-sm text-gray-700 dark:text-gray-300">Als neues Video speichern</span>
              </label>
              <span v-if="!saveAsNew" class="text-xs text-amber-600 bg-amber-50 dark:bg-amber-900/30 px-2 py-1 rounded">
                Achtung: Original wird überschrieben!
              </span>
            </div>

            <!-- Summary -->
            <div v-if="selectedVideo && selectedAudio" class="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 mb-4">
              <h3 class="text-xs font-medium text-gray-500 mb-2">Zusammenfassung:</h3>
              <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                <span class="text-gray-500">Video:</span>
                <span class="text-gray-900 dark:text-white truncate">{{ selectedVideo.original_filename || selectedVideo.filename }}</span>
                <span class="text-gray-500">Audio:</span>
                <span class="text-gray-900 dark:text-white truncate">{{ selectedAudio.name || selectedAudio.original_filename }}</span>
                <span class="text-gray-500">Original-Audio:</span>
                <span class="text-gray-900 dark:text-white">{{ Math.round(originalVolume * 100) }}%</span>
                <span class="text-gray-500">Musik:</span>
                <span class="text-gray-900 dark:text-white">{{ Math.round(musicVolume * 100) }}%</span>
                <span class="text-gray-500">Fade-In:</span>
                <span class="text-gray-900 dark:text-white">{{ fadeInSeconds.toFixed(1) }}s</span>
                <span class="text-gray-500">Fade-Out:</span>
                <span class="text-gray-900 dark:text-white">{{ fadeOutSeconds.toFixed(1) }}s</span>
              </div>
            </div>

            <!-- Mix button -->
            <div class="flex items-center gap-3">
              <button
                @click="startMix"
                :disabled="!canMix"
                :class="[
                  'flex-1 py-3 px-6 rounded-lg font-medium text-sm transition-all flex items-center justify-center gap-2',
                  canMix
                    ? 'bg-treff-blue text-white hover:bg-treff-blue/90 shadow-sm'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                ]"
              >
                <span v-if="mixing" class="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
                <AppIcon v-else name="slider" class="w-4 h-4" />
                {{ mixing ? 'Mische Audio...' : 'Audio mixen' }}
              </button>

              <button
                @click="resetMixer"
                class="py-3 px-4 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-600 transition-all"
              >
                Zurücksetzen
              </button>
            </div>

            <!-- Progress bar -->
            <div v-if="mixing" class="mt-4">
              <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  class="h-full bg-treff-blue rounded-full transition-all duration-300"
                  :style="{ width: Math.min(mixProgress, 100) + '%' }"
                ></div>
              </div>
              <p class="text-xs text-gray-500 mt-1 text-center">
                {{ Math.round(mixProgress) }}% - Bitte warten, Audio wird gemischt...
              </p>
            </div>

            <!-- Mix Result -->
            <div v-if="mixResult" class="mt-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div class="flex items-center gap-2 mb-2">
                <span class="text-green-600 text-lg">&#10003;</span>
                <h3 class="text-sm font-medium text-green-800 dark:text-green-300">Audio-Mix erfolgreich!</h3>
              </div>
              <div class="text-xs text-green-700 dark:text-green-400 space-y-1">
                <p>Datei: {{ mixResult.original_filename || mixResult.filename }}</p>
                <p>Größe: {{ formatFileSize(mixResult.file_size) }}</p>
                <p v-if="mixResult.duration_seconds">Dauer: {{ formatDuration(mixResult.duration_seconds) }}</p>
              </div>
              <button
                @click="downloadResult"
                class="mt-3 py-2 px-4 text-xs font-medium bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all"
              >
                Herunterladen
              </button>
            </div>

            <!-- Mix Error -->
            <div v-if="mixError" class="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div class="flex items-center gap-2">
                <span class="text-red-500 text-lg">&#10007;</span>
                <p class="text-sm text-red-800 dark:text-red-300">{{ mixError }}</p>
              </div>
            </div>
          </div>

          <!-- Quick Tips -->
          <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
            <h3 class="text-sm font-medium text-blue-800 dark:text-blue-300 mb-2">Tipps für Social-Media Audio</h3>
            <ul class="text-xs text-blue-700 dark:text-blue-400 space-y-1.5">
              <li class="flex items-start gap-1.5">
                <span class="mt-0.5">&#8226;</span>
                <span><strong>Reels/TikTok:</strong> Musik ist Pflicht! Ohne Musik performen Videos deutlich schlechter.</span>
              </li>
              <li class="flex items-start gap-1.5">
                <span class="mt-0.5">&#8226;</span>
                <span><strong>Balance:</strong> Original-Audio 70-80%, Musik 20-40% - so hört man Sprache klar.</span>
              </li>
              <li class="flex items-start gap-1.5">
                <span class="mt-0.5">&#8226;</span>
                <span><strong>Fade-Out:</strong> Immer 2-3s Fade-Out setzen, damit die Musik nicht abrupt endet.</span>
              </li>
              <li class="flex items-start gap-1.5">
                <span class="mt-0.5">&#8226;</span>
                <span><strong>Stimmung:</strong> Upbeat-Musik für Länder-Highlights, Emotional für Abschiedsszenen.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <VideoWorkflowTour ref="workflowTourRef" />
    <TourSystem ref="tourRef" page-key="audio-mixer" />
  </div>
</template>
