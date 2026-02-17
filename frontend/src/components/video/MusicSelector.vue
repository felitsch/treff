<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import AppIcon from '@/components/icons/AppIcon.vue'

const toast = useToast()

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      enabled: false,
      trackId: null,
      trackName: '',
      volume: 0.3,
      fadeIn: 1.0,
      fadeOut: 2.0,
    }),
  },
})

const emit = defineEmits(['update:modelValue'])

// State
const tracks = ref([])
const loading = ref(true)
const categoryFilter = ref('')
const moodFilter = ref('')
const categories = ref([])
const moods = ['happy', 'sad', 'energetic', 'calm', 'epic', 'playful']
const uploadingTrack = ref(false)

// Computed
const filteredTracks = computed(() => {
  let result = tracks.value
  if (categoryFilter.value) {
    result = result.filter(t => t.category === categoryFilter.value)
  }
  if (moodFilter.value) {
    result = result.filter(t => t.mood === moodFilter.value)
  }
  return result
})

const selectedTrack = computed(() => {
  if (!props.modelValue.trackId) return null
  return tracks.value.find(t => t.id === props.modelValue.trackId) || null
})

// Load music library
async function loadTracks() {
  loading.value = true
  try {
    const { data } = await api.get('/api/audio/music')
    tracks.value = data || []
    // Extract unique categories
    const cats = new Set(tracks.value.map(t => t.category).filter(Boolean))
    categories.value = [...cats]
  } catch (err) {
    console.error('Failed to load music:', err)
  } finally {
    loading.value = false
  }
}

function update(key, value) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}

function selectTrack(track) {
  const current = props.modelValue.trackId
  if (current === track.id) {
    // Deselect
    emit('update:modelValue', { ...props.modelValue, trackId: null, trackName: '' })
  } else {
    emit('update:modelValue', { ...props.modelValue, trackId: track.id, trackName: track.name, enabled: true })
  }
}

function formatDuration(seconds) {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

async function uploadCustomTrack(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('audio/')) {
    toast.error('Bitte waehle eine Audiodatei aus (MP3, WAV, OGG).')
    return
  }
  uploadingTrack.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', file.name.replace(/\.[^/.]+$/, ''))
    formData.append('category', 'custom')
    const { data } = await api.post('/api/audio/music/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    toast.success('Musik-Track hochgeladen!')
    await loadTracks()
    if (data?.id) {
      selectTrack(data)
    }
  } catch (err) {
    toast.error('Upload fehlgeschlagen.')
  } finally {
    uploadingTrack.value = false
  }
}

const moodLabels = {
  happy: 'Froehlich',
  sad: 'Melancholisch',
  energetic: 'Energetisch',
  calm: 'Ruhig',
  epic: 'Episch',
  playful: 'Verspielt',
}

onMounted(loadTracks)
</script>

<template>
  <div class="space-y-4">
    <!-- Enable toggle -->
    <div class="flex items-center justify-between">
      <label class="text-sm font-medium text-gray-700 dark:text-gray-300">Hintergrundmusik</label>
      <button
        @click="update('enabled', !props.modelValue.enabled)"
        :class="[
          'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
          props.modelValue.enabled ? 'bg-blue-500' : 'bg-gray-300 dark:bg-gray-600',
        ]"
      >
        <span
          :class="[
            'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
            props.modelValue.enabled ? 'translate-x-6' : 'translate-x-1',
          ]"
        />
      </button>
    </div>

    <div v-if="props.modelValue.enabled" class="space-y-4">
      <!-- Selected track info -->
      <div v-if="selectedTrack" class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 flex items-center gap-3">
        <AppIcon name="musical-note" class="w-7 h-7 text-blue-500" />
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ selectedTrack.name }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            {{ formatDuration(selectedTrack.duration_seconds) }}
            <span v-if="selectedTrack.bpm"> · {{ selectedTrack.bpm }} BPM</span>
            <span v-if="selectedTrack.category"> · {{ selectedTrack.category }}</span>
          </p>
        </div>
        <button
          @click="selectTrack(selectedTrack)"
          class="text-xs text-red-500 hover:text-red-700 px-2 py-1"
        >
          Entfernen
        </button>
      </div>

      <!-- Volume & Fade controls -->
      <div class="grid grid-cols-3 gap-3">
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
            Lautstaerke ({{ Math.round(props.modelValue.volume * 100) }}%)
          </label>
          <input
            :value="props.modelValue.volume"
            @input="update('volume', parseFloat($event.target.value))"
            type="range"
            min="0"
            max="1"
            step="0.05"
            class="w-full accent-blue-500"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
            Fade-In ({{ props.modelValue.fadeIn }}s)
          </label>
          <input
            :value="props.modelValue.fadeIn"
            @input="update('fadeIn', parseFloat($event.target.value))"
            type="range"
            min="0"
            max="5"
            step="0.5"
            class="w-full accent-blue-500"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
            Fade-Out ({{ props.modelValue.fadeOut }}s)
          </label>
          <input
            :value="props.modelValue.fadeOut"
            @input="update('fadeOut', parseFloat($event.target.value))"
            type="range"
            min="0"
            max="5"
            step="0.5"
            class="w-full accent-blue-500"
          />
        </div>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap gap-2">
        <select
          v-model="categoryFilter"
          class="px-3 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
        >
          <option value="">Alle Kategorien</option>
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
        <select
          v-model="moodFilter"
          class="px-3 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
        >
          <option value="">Alle Stimmungen</option>
          <option v-for="m in moods" :key="m" :value="m">{{ moodLabels[m] || m }}</option>
        </select>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-4">
        <div class="animate-spin w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full" />
      </div>

      <!-- Track list -->
      <div v-else class="space-y-1 max-h-[200px] overflow-y-auto">
        <button
          v-for="track in filteredTracks"
          :key="track.id"
          @click="selectTrack(track)"
          :class="[
            'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-all',
            props.modelValue.trackId === track.id
              ? 'bg-blue-100 dark:bg-blue-900/30 ring-1 ring-blue-300'
              : 'hover:bg-gray-50 dark:hover:bg-gray-700/50',
          ]"
          data-testid="music-track-item"
        >
          <AppIcon name="musical-note" class="w-5 h-5 text-gray-400" />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ track.name }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              {{ formatDuration(track.duration_seconds) }}
              <span v-if="track.bpm"> · {{ track.bpm }} BPM</span>
              <span v-if="track.mood"> · {{ moodLabels[track.mood] || track.mood }}</span>
            </p>
          </div>
        </button>

        <div v-if="filteredTracks.length === 0" class="text-center py-4 text-xs text-gray-500 dark:text-gray-400">
          Keine Tracks gefunden.
        </div>
      </div>

      <!-- Upload custom track -->
      <div class="pt-2 border-t border-gray-200 dark:border-gray-700">
        <label class="flex items-center gap-2 cursor-pointer text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800">
          <span>{{ uploadingTrack ? 'Wird hochgeladen...' : '+ Eigene Musik hochladen' }}</span>
          <input
            type="file"
            accept="audio/*"
            class="hidden"
            @change="uploadCustomTrack"
            :disabled="uploadingTrack"
          />
        </label>
      </div>
    </div>
  </div>
</template>
