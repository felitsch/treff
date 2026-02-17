<script setup>
/**
 * AudioSuggestionPanel - Browseable audio/music suggestion library
 *
 * Displays curated trending audio recommendations for Reels/TikTok
 * with filters for mood, platform and content pillar.
 * Can be embedded as a sidebar in VideoScriptView or VideoCreateView.
 */
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/utils/api'

const props = defineProps({
  /** Pre-filter by platform: 'tiktok', 'instagram', or null for all */
  platformFilter: {
    type: String,
    default: null,
  },
  /** Pre-filter by content pillar */
  contentPillarFilter: {
    type: String,
    default: null,
  },
  /** Whether panel is shown in compact/sidebar mode */
  compact: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['select'])

// Data
const suggestions = ref([])
const isLoading = ref(false)
const error = ref(null)

// Filters
const selectedMood = ref('')
const selectedPlatform = ref(props.platformFilter || '')
const selectedTempo = ref('')
const selectedPillar = ref(props.contentPillarFilter || '')
const showRoyaltyFreeOnly = ref(false)

// Available filter options
const moods = [
  { value: '', label: 'Alle Stimmungen' },
  { value: 'energetic', label: 'Energetisch', icon: '⚡', color: 'text-yellow-600' },
  { value: 'emotional', label: 'Emotional', icon: '💫', color: 'text-purple-600' },
  { value: 'funny', label: 'Witzig', icon: '😄', color: 'text-green-600' },
  { value: 'chill', label: 'Chill', icon: '🌊', color: 'text-blue-600' },
  { value: 'dramatic', label: 'Dramatisch', icon: '🎭', color: 'text-red-600' },
]

const platforms = [
  { value: '', label: 'Alle Plattformen' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'both', label: 'Beide' },
]

const tempos = [
  { value: '', label: 'Alle Tempi' },
  { value: 'slow', label: 'Langsam' },
  { value: 'medium', label: 'Mittel' },
  { value: 'fast', label: 'Schnell' },
]

const pillars = [
  { value: '', label: 'Alle Content-Pillars' },
  { value: 'laender_spotlight', label: 'Laender-Spotlight' },
  { value: 'erfahrungsberichte', label: 'Erfahrungsberichte' },
  { value: 'tipps_tricks', label: 'Tipps & Tricks' },
  { value: 'fristen_cta', label: 'Fristen & CTA' },
  { value: 'faq', label: 'FAQ' },
]

const moodBadgeColors = {
  energetic: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  emotional: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  funny: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  chill: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  dramatic: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
}

const moodIcons = {
  energetic: '⚡',
  emotional: '💫',
  funny: '😄',
  chill: '🌊',
  dramatic: '🎭',
}

const tempoLabels = {
  slow: 'Langsam',
  medium: 'Mittel',
  fast: 'Schnell',
}

const platformIcons = {
  tiktok: 'TikTok',
  instagram: 'Instagram',
  both: 'Beide',
}

const pillarLabels = {
  laender_spotlight: 'Laender',
  erfahrungsberichte: 'Erfahrungen',
  tipps_tricks: 'Tipps',
  fristen_cta: 'Fristen',
  faq: 'FAQ',
}

// Computed
const filteredCount = computed(() => suggestions.value.length)

// Methods
async function loadSuggestions() {
  isLoading.value = true
  error.value = null

  try {
    const params = {}
    if (selectedMood.value) params.mood = selectedMood.value
    if (selectedPlatform.value) params.platform = selectedPlatform.value
    if (selectedTempo.value) params.tempo = selectedTempo.value
    if (selectedPillar.value) params.content_pillar = selectedPillar.value
    if (showRoyaltyFreeOnly.value) params.is_royalty_free = true
    params.sort_by = 'trending_score'
    params.limit = 50

    const { data } = await api.get('/api/audio-suggestions', { params })
    suggestions.value = data.suggestions || []
  } catch (e) {
    console.error('Failed to load audio suggestions:', e)
    error.value = 'Fehler beim Laden der Audio-Empfehlungen'
  } finally {
    isLoading.value = false
  }
}

function selectSuggestion(suggestion) {
  emit('select', suggestion)
}

function getTrendingStars(score) {
  return Math.round(score / 2)  // Convert 1-10 to 1-5 stars
}

function resetFilters() {
  selectedMood.value = ''
  selectedPlatform.value = props.platformFilter || ''
  selectedTempo.value = ''
  selectedPillar.value = props.contentPillarFilter || ''
  showRoyaltyFreeOnly.value = false
}

// Watch filters
watch(
  [selectedMood, selectedPlatform, selectedTempo, selectedPillar, showRoyaltyFreeOnly],
  () => loadSuggestions(),
)

// Watch prop changes
watch(
  () => props.platformFilter,
  (val) => {
    selectedPlatform.value = val || ''
  },
)

watch(
  () => props.contentPillarFilter,
  (val) => {
    selectedPillar.value = val || ''
  },
)

onMounted(() => {
  loadSuggestions()
})
</script>

<template>
  <div :class="compact ? '' : 'bg-white dark:bg-gray-800 rounded-xl shadow'" data-testid="audio-suggestion-panel">
    <!-- Header -->
    <div :class="compact ? 'mb-3' : 'p-4 border-b border-gray-200 dark:border-gray-700'">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
          </svg>
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
            Audio-Empfehlungen
          </h3>
        </div>
        <span class="text-xs text-gray-500 dark:text-gray-400">
          {{ filteredCount }} Tracks
        </span>
      </div>
    </div>

    <!-- Filters -->
    <div :class="compact ? 'mb-3 space-y-2' : 'p-4 border-b border-gray-200 dark:border-gray-700 space-y-2'">
      <!-- Mood filter pills -->
      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">Stimmung</label>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="m in moods"
            :key="m.value"
            @click="selectedMood = m.value"
            :class="[
              'px-2.5 py-1 rounded-full text-xs font-medium transition-colors',
              selectedMood === m.value
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
            ]"
          >
            <span v-if="m.icon" class="mr-0.5">{{ m.icon }}</span>
            {{ m.label }}
          </button>
        </div>
      </div>

      <!-- Platform & Tempo row -->
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Plattform</label>
          <select
            v-model="selectedPlatform"
            class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option v-for="p in platforms" :key="p.value" :value="p.value">{{ p.label }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Tempo</label>
          <select
            v-model="selectedTempo"
            class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option v-for="t in tempos" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </div>
      </div>

      <!-- Content Pillar filter -->
      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Content-Pillar</label>
        <select
          v-model="selectedPillar"
          class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          <option v-for="p in pillars" :key="p.value" :value="p.value">{{ p.label }}</option>
        </select>
      </div>

      <!-- Royalty-free toggle & Reset -->
      <div class="flex items-center justify-between">
        <label class="flex items-center gap-1.5 cursor-pointer">
          <input
            v-model="showRoyaltyFreeOnly"
            type="checkbox"
            class="w-3.5 h-3.5 text-blue-600 rounded border-gray-300 dark:border-gray-600"
          />
          <span class="text-xs text-gray-600 dark:text-gray-400">Nur lizenzfrei</span>
        </label>
        <button
          @click="resetFilters"
          class="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
        >
          Filter zuruecksetzen
        </button>
      </div>
    </div>

    <!-- Suggestions List -->
    <div :class="compact ? '' : 'p-4'" class="space-y-2 max-h-[400px] overflow-y-auto">
      <!-- Loading -->
      <div v-if="isLoading" class="flex items-center justify-center py-8">
        <svg class="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="text-center py-4">
        <p class="text-sm text-red-500">{{ error }}</p>
        <button @click="loadSuggestions" class="text-xs text-blue-600 hover:underline mt-1">
          Erneut versuchen
        </button>
      </div>

      <!-- Empty -->
      <div v-else-if="suggestions.length === 0" class="text-center py-6">
        <svg class="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
        </svg>
        <p class="text-sm text-gray-400 dark:text-gray-500">Keine passenden Tracks gefunden</p>
        <button @click="resetFilters" class="text-xs text-blue-600 hover:underline mt-1">
          Filter zuruecksetzen
        </button>
      </div>

      <!-- Suggestion cards -->
      <div
        v-else
        v-for="suggestion in suggestions"
        :key="suggestion.id"
        @click="selectSuggestion(suggestion)"
        class="group p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-400 dark:hover:border-blue-500 hover:bg-blue-50/50 dark:hover:bg-blue-900/10 cursor-pointer transition-all"
        :data-testid="`audio-suggestion-${suggestion.id}`"
      >
        <!-- Title row -->
        <div class="flex items-start justify-between mb-1.5">
          <div class="flex-1 min-w-0">
            <h4 class="text-sm font-medium text-gray-900 dark:text-white truncate">
              {{ suggestion.title }}
            </h4>
            <p v-if="suggestion.artist" class="text-xs text-gray-500 dark:text-gray-400">
              {{ suggestion.artist }}
            </p>
          </div>
          <!-- Trending score -->
          <div class="flex items-center gap-0.5 ml-2 flex-shrink-0">
            <span
              v-for="i in 5"
              :key="i"
              :class="[
                'text-xs',
                i <= getTrendingStars(suggestion.trending_score)
                  ? 'text-yellow-500'
                  : 'text-gray-300 dark:text-gray-600'
              ]"
            >&#9733;</span>
          </div>
        </div>

        <!-- Badges row -->
        <div class="flex flex-wrap items-center gap-1.5 mb-1.5">
          <!-- Mood badge -->
          <span :class="[moodBadgeColors[suggestion.mood] || 'bg-gray-100 text-gray-800', 'px-1.5 py-0.5 rounded text-[10px] font-medium']">
            {{ moodIcons[suggestion.mood] || '' }} {{ moods.find(m => m.value === suggestion.mood)?.label || suggestion.mood }}
          </span>

          <!-- Tempo badge -->
          <span class="px-1.5 py-0.5 rounded text-[10px] font-medium bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
            {{ tempoLabels[suggestion.tempo] || suggestion.tempo }}
          </span>

          <!-- Platform badge -->
          <span class="px-1.5 py-0.5 rounded text-[10px] font-medium bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
            {{ platformIcons[suggestion.platform] || suggestion.platform }}
          </span>

          <!-- Royalty-free badge -->
          <span v-if="suggestion.is_royalty_free" class="px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300">
            Lizenzfrei
          </span>
        </div>

        <!-- Suitable for -->
        <div v-if="suggestion.suitable_for && suggestion.suitable_for.length > 0" class="mb-1.5">
          <span class="text-[10px] text-gray-400 dark:text-gray-500">Passt zu: </span>
          <span
            v-for="(pillar, idx) in suggestion.suitable_for"
            :key="pillar"
            class="text-[10px] text-gray-500 dark:text-gray-400"
          >
            {{ pillarLabels[pillar] || pillar }}{{ idx < suggestion.suitable_for.length - 1 ? ', ' : '' }}
          </span>
        </div>

        <!-- Description (truncated) -->
        <p v-if="suggestion.description" class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
          {{ suggestion.description }}
        </p>

        <!-- URL hint link -->
        <a
          v-if="suggestion.url_hint"
          :href="suggestion.url_hint"
          target="_blank"
          rel="noopener noreferrer"
          @click.stop
          class="inline-flex items-center gap-1 text-[10px] text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 mt-1"
        >
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
          Zum Original
        </a>
      </div>
    </div>
  </div>
</template>
