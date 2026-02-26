<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import { formatDate } from '@/utils/dateUtils'

const router = useRouter()

const loading = ref(true)
const error = ref(null)
const suggestions = ref([])
const stats = ref(null)
const refreshingId = ref(null)
const filterEvergreen = ref(false)

// Country flag emoji
const countryFlags = {
  usa: '\u{1F1FA}\u{1F1F8}',
  canada: '\u{1F1E8}\u{1F1E6}',
  australia: '\u{1F1E6}\u{1F1FA}',
  newzealand: '\u{1F1F3}\u{1F1FF}',
  ireland: '\u{1F1EE}\u{1F1EA}',
}

// Platform icons
function platformIcon(platform) {
  switch (platform) {
    case 'instagram_feed': return '\u{1F4F8}'
    case 'instagram_story': return '\u{1F4F1}'
    case 'tiktok': return '\u{1F3B5}'
    default: return '\u{1F4DD}'
  }
}

// Score color class
function scoreColor(score) {
  if (score >= 80) return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30'
  if (score >= 50) return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/30'
  return 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700'
}

// formatDate imported from @/utils/dateUtils

const filteredSuggestions = computed(() => {
  if (filterEvergreen.value) {
    return suggestions.value.filter(s => s.is_evergreen)
  }
  return suggestions.value
})

async function fetchRecycling() {
  loading.value = true
  error.value = null
  try {
    const [suggestionsRes, statsRes] = await Promise.all([
      api.get('/api/recycling?limit=5'),
      api.get('/api/recycling/stats'),
    ])
    suggestions.value = suggestionsRes.data.suggestions || []
    stats.value = statsRes.data
  } catch (err) {
    console.error('Failed to load recycling data:', err)
    error.value = 'Recycling-Daten konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function refreshPost(suggestion) {
  refreshingId.value = suggestion.id
  try {
    const res = await api.post(`/api/recycling/${suggestion.id}/refresh`, {})
    // Navigate to edit the new draft post
    if (res.data && res.data.id) {
      router.push(`/create/post/${res.data.id}/edit`)
    }
  } catch (err) {
    console.error('Failed to refresh post:', err)
  } finally {
    refreshingId.value = null
  }
}

function viewOriginal(suggestion) {
  router.push(`/create/post/${suggestion.id}/edit`)
}

onMounted(() => {
  fetchRecycling()
})
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700" data-tour="dashboard-recycling">
    <!-- Header -->
    <div class="p-5 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
        <span>&#9851;</span> Content-Recycling
      </h2>
      <div class="flex items-center gap-2">
        <!-- Evergreen filter toggle -->
        <button
          v-if="stats && stats.evergreen_count > 0"
          @click="filterEvergreen = !filterEvergreen"
          :class="[
            'inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full transition-colors',
            filterEvergreen
              ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
              : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600',
          ]"
        >
          &#127793; Evergreen
        </button>
        <!-- Stats badge -->
        <span
          v-if="stats && stats.total_recyclable > 0"
          class="text-xs font-medium px-2.5 py-1 rounded-full bg-teal-50 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300"
        >
          {{ stats.total_recyclable }} verfügbar
        </span>
      </div>
    </div>

    <!-- Content -->
    <div class="p-5">
      <!-- Loading -->
      <div v-if="loading" class="space-y-3">
        <div v-for="i in 2" :key="i" class="animate-pulse flex items-center gap-3">
          <div class="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
          <div class="flex-1">
            <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
            <div class="h-2.5 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
          </div>
        </div>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="text-center py-4">
        <p class="text-sm text-red-500 dark:text-red-400">{{ error }}</p>
        <button
          @click="fetchRecycling"
          class="mt-2 text-xs text-treff-blue hover:underline"
        >
          Erneut versuchen
        </button>
      </div>

      <!-- Empty state -->
      <div v-else-if="filteredSuggestions.length === 0" class="text-center py-6">
        <div class="text-3xl mb-2">&#9851;</div>
        <p class="text-sm text-gray-500 dark:text-gray-400 font-medium">
          {{ filterEvergreen ? 'Keine Evergreen-Posts zum Recyceln' : 'Keine Posts zum Recyceln' }}
        </p>
        <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
          Posts älter als 90 Tage erscheinen hier als Recycling-Vorschläge.
        </p>
      </div>

      <!-- Suggestions list -->
      <div v-else class="space-y-3">
        <div
          v-for="suggestion in filteredSuggestions"
          :key="suggestion.id"
          class="border border-gray-100 dark:border-gray-700 rounded-lg p-3 hover:border-teal-200 dark:hover:border-teal-700 transition-colors"
        >
          <!-- Top row -->
          <div class="flex items-start gap-3">
            <!-- Platform icon -->
            <div class="w-9 h-9 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
              <span class="text-base">{{ platformIcon(suggestion.platform) }}</span>
            </div>

            <!-- Post info -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-1.5 flex-wrap mb-1">
                <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {{ suggestion.title || 'Ohne Titel' }}
                </p>
                <span
                  v-if="suggestion.is_evergreen"
                  class="inline-flex items-center gap-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300"
                >
                  &#127793; Evergreen
                </span>
              </div>

              <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                <span>{{ suggestion.category_label }}</span>
                <span v-if="suggestion.country">{{ countryFlags[suggestion.country] || '' }}</span>
                <span class="text-gray-300 dark:text-gray-600">|</span>
                <span>{{ formatDate(suggestion.created_at) }}</span>
                <span class="text-gray-300 dark:text-gray-600">|</span>
                <span>{{ suggestion.days_old }} Tage alt</span>
              </div>

              <!-- Reason -->
              <p class="text-[11px] text-gray-400 dark:text-gray-500 mt-1 italic line-clamp-1">
                {{ suggestion.reason }}
              </p>
            </div>

            <!-- Score badge -->
            <div
              class="flex-shrink-0 text-xs font-bold px-2 py-1 rounded-lg"
              :class="scoreColor(suggestion.recycle_score)"
            >
              {{ suggestion.recycle_score }}%
            </div>
          </div>

          <!-- Action buttons -->
          <div class="flex items-center gap-2 mt-2.5 ml-12">
            <button
              @click="refreshPost(suggestion)"
              :disabled="refreshingId === suggestion.id"
              class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-white bg-teal-600 rounded-lg hover:bg-teal-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span v-if="refreshingId === suggestion.id" class="animate-spin">&#9203;</span>
              <span v-else>&#9851;</span>
              Recyceln
            </button>
            <button
              @click="viewOriginal(suggestion)"
              class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              &#128065; Ansehen
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
