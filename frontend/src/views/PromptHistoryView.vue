<script setup>
/**
 * PromptHistoryView.vue — KI-Prompt-History & Favoriten
 *
 * Shows all AI prompt calls with their results, supports:
 * - Filter by type (Text, Bild, Hashtags, Optimierung, Video-Script)
 * - Filter favorites only
 * - Search in prompt text
 * - Toggle favorite (star icon)
 * - "Nochmal verwenden" button to reuse prompt
 * - Delete individual entries
 * - Token/cost summary stats
 * - Pagination
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import api from '@/utils/api'
import EmptyState from '@/components/common/EmptyState.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const router = useRouter()
const toast = useToast()

// ─── State ───────────────────────────────────────────────────────
const items = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const totalPages = ref(1)

// Filters
const activeType = ref('')
const favoritesOnly = ref(false)
const searchQuery = ref('')

// Stats
const stats = ref({ total: 0, favorites: 0, by_type: {}, total_tokens: 0, total_estimated_cost: 0 })

// Delete confirmation
const deleteConfirmId = ref(null)

// Type definitions for UI
const PROMPT_TYPES = [
  { key: '', label: 'Alle', icon: 'clipboard-list' },
  { key: 'text', label: 'Text', icon: 'pencil-square' },
  { key: 'image', label: 'Bild', icon: 'photo' },
  { key: 'hashtags', label: 'Hashtags', icon: 'hashtag' },
  { key: 'optimization', label: 'Optimierung', icon: 'wrench' },
  { key: 'video_script', label: 'Video-Script', icon: 'film' },
]

// ─── Computed ────────────────────────────────────────────────────
const typeLabel = computed(() => {
  return (type) => {
    const found = PROMPT_TYPES.find(t => t.key === type)
    return found ? found.label : type
  }
})

const typeIcon = computed(() => {
  return (type) => {
    const found = PROMPT_TYPES.find(t => t.key === type)
    return found ? found.icon : 'clipboard-list'
  }
})

// ─── API calls ───────────────────────────────────────────────────
async function fetchHistory() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (activeType.value) params.prompt_type = activeType.value
    if (favoritesOnly.value) params.favorites_only = true
    if (searchQuery.value.trim()) params.search = searchQuery.value.trim()

    const res = await api.get('/api/ai/history', { params })
    items.value = res.data.items
    total.value = res.data.total
    totalPages.value = res.data.total_pages
  } catch (err) {
    // Error toast handled by interceptor
  } finally {
    loading.value = false
  }
}

async function fetchStats() {
  try {
    const res = await api.get('/api/ai/history/stats')
    stats.value = res.data
  } catch (err) {
    // Silently handle
  }
}

async function toggleFavorite(item) {
  try {
    const res = await api.patch(`/api/ai/history/${item.id}/favorite`)
    item.is_favorite = res.data.is_favorite
    toast.success(res.data.is_favorite ? 'Als Favorit markiert' : 'Favorit entfernt')
    fetchStats()
  } catch (err) {
    // Error toast handled by interceptor
  }
}

async function deleteEntry(id) {
  try {
    await api.delete(`/api/ai/history/${id}`)
    toast.success('Eintrag geloescht')
    deleteConfirmId.value = null
    fetchHistory()
    fetchStats()
  } catch (err) {
    // Error toast handled by interceptor
  }
}

function reusePrompt(item) {
  // Navigate to the appropriate creator with the prompt pre-filled
  const routeMap = {
    text: '/create/quick',
    image: '/create/quick',
    hashtags: '/create/quick',
    optimization: '/create/quick',
    video_script: '/video/script-generator',
  }
  const target = routeMap[item.prompt_type] || '/create/quick'

  // Store reuse data in sessionStorage so the target page can pick it up
  sessionStorage.setItem('reuse_prompt', JSON.stringify({
    prompt_type: item.prompt_type,
    prompt_text: item.prompt_text,
    options: item.options,
  }))

  toast.success('Prompt wird in den Generator uebernommen')
  router.push(target)
}

function formatDate(isoString) {
  if (!isoString) return ''
  const d = new Date(isoString)
  return d.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatCost(cents) {
  if (!cents) return '-'
  return `${cents.toFixed(2)} ct`
}

function truncateText(text, maxLen = 200) {
  if (!text) return ''
  return text.length > maxLen ? text.substring(0, maxLen) + '...' : text
}

// ─── Watchers ────────────────────────────────────────────────────
watch([activeType, favoritesOnly], () => {
  page.value = 1
  fetchHistory()
})

// Debounced search
let searchTimeout = null
watch(searchQuery, () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    page.value = 1
    fetchHistory()
  }, 400)
})

// ─── Lifecycle ───────────────────────────────────────────────────
onMounted(() => {
  fetchHistory()
  fetchStats()
})
</script>

<template>
  <div class="max-w-7xl mx-auto" data-testid="prompt-history-view">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
        <AppIcon name="sparkles" class="w-6 h-6 inline-block" /> KI-Prompt-History
      </h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
        Alle KI-Aufrufe mit Ergebnissen, Favoriten und Wiederverwendung
      </p>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6" data-testid="prompt-history-stats">
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats.total }}</div>
        <div class="text-xs text-gray-500 dark:text-gray-400">Gesamt-Aufrufe</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <div class="text-2xl font-bold text-yellow-500">{{ stats.favorites }}</div>
        <div class="text-xs text-gray-500 dark:text-gray-400">Favoriten</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ (stats.total_tokens || 0).toLocaleString('de-DE') }}</div>
        <div class="text-xs text-gray-500 dark:text-gray-400">Tokens verbraucht</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ formatCost(stats.total_estimated_cost) }}</div>
        <div class="text-xs text-gray-500 dark:text-gray-400">Geschaetzte Kosten</div>
      </div>
    </div>

    <!-- Filters Row -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 mb-6" data-testid="prompt-history-filters">
      <div class="flex flex-col sm:flex-row gap-4">
        <!-- Type filter chips -->
        <div class="flex flex-wrap gap-2">
          <button
            v-for="typeObj in PROMPT_TYPES"
            :key="typeObj.key"
            @click="activeType = typeObj.key"
            :class="[
              'px-3 py-1.5 rounded-full text-xs font-medium transition-colors border',
              activeType === typeObj.key
                ? 'bg-[#3B7AB1] text-white border-[#3B7AB1]'
                : 'bg-gray-50 dark:bg-gray-700 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600'
            ]"
            :data-testid="`filter-type-${typeObj.key || 'all'}`"
          >
            <AppIcon :name="typeObj.icon" class="w-3.5 h-3.5 inline-block" /> {{ typeObj.label }}
            <span v-if="typeObj.key && stats.by_type[typeObj.key]" class="ml-1 opacity-70">
              ({{ stats.by_type[typeObj.key] }})
            </span>
          </button>
        </div>

        <!-- Favorites toggle -->
        <button
          @click="favoritesOnly = !favoritesOnly"
          :class="[
            'px-3 py-1.5 rounded-full text-xs font-medium transition-colors border whitespace-nowrap',
            favoritesOnly
              ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 border-yellow-300 dark:border-yellow-600'
              : 'bg-gray-50 dark:bg-gray-700 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600'
          ]"
          data-testid="filter-favorites"
        >
          <AppIcon name="star" class="w-3.5 h-3.5 inline-block" /> Nur Favoriten
        </button>

        <!-- Search -->
        <div class="flex-1 min-w-[200px]">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Prompt durchsuchen..."
            class="w-full px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
            data-testid="search-input"
          />
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#3B7AB1]"></div>
    </div>

    <!-- Empty State -->
    <EmptyState
      v-else-if="items.length === 0 && !loading"
      svgIcon="sparkles"
      title="Keine KI-Aufrufe gefunden"
      :description="activeType || favoritesOnly || searchQuery
        ? 'Versuche andere Filter oder loesche die Suche.'
        : 'Sobald du KI-Funktionen nutzt (Text, Bild, Hashtags), erscheinen deine Aufrufe hier.'"
      :actionLabel="activeType || favoritesOnly || searchQuery ? 'Filter zuruecksetzen' : 'Post erstellen'"
      :actionTo="activeType || favoritesOnly || searchQuery ? '' : '/create/quick'"
      @action="activeType = ''; favoritesOnly = false; searchQuery = ''"
    />

    <!-- History List -->
    <div v-else class="space-y-3" data-testid="prompt-history-list">
      <div
        v-for="item in items"
        :key="item.id"
        class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow"
        :data-testid="`history-item-${item.id}`"
      >
        <!-- Top row: Type badge + timestamp + actions -->
        <div class="flex items-start justify-between gap-3 mb-3">
          <div class="flex items-center gap-2 flex-wrap">
            <!-- Type badge -->
            <span
              :class="[
                'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium',
                item.prompt_type === 'text' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' :
                item.prompt_type === 'image' ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300' :
                item.prompt_type === 'hashtags' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' :
                item.prompt_type === 'optimization' ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300' :
                item.prompt_type === 'video_script' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' :
                'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              ]"
            >
              <AppIcon :name="typeIcon(item.prompt_type)" class="w-3.5 h-3.5 inline-block" /> {{ typeLabel(item.prompt_type) }}
            </span>

            <!-- Timestamp -->
            <span class="text-xs text-gray-400">{{ formatDate(item.created_at) }}</span>

            <!-- Model -->
            <span v-if="item.model" class="text-xs text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">
              {{ item.model }}
            </span>
          </div>

          <!-- Action buttons -->
          <div class="flex items-center gap-1 shrink-0">
            <!-- Favorite toggle -->
            <button
              @click="toggleFavorite(item)"
              :class="[
                'p-1.5 rounded-lg transition-colors',
                item.is_favorite
                  ? 'text-yellow-500 hover:bg-yellow-50 dark:hover:bg-yellow-900/20'
                  : 'text-gray-400 hover:text-yellow-500 hover:bg-gray-100 dark:hover:bg-gray-700'
              ]"
              :title="item.is_favorite ? 'Favorit entfernen' : 'Als Favorit markieren'"
              :data-testid="`favorite-btn-${item.id}`"
            >
              <svg xmlns="http://www.w3.org/2000/svg" :fill="item.is_favorite ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M11.48 3.499a.562.562 0 0 1 1.04 0l2.125 5.111a.563.563 0 0 0 .475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 0 0-.182.557l1.285 5.385a.562.562 0 0 1-.84.61l-4.725-2.885a.562.562 0 0 0-.586 0L6.982 20.54a.562.562 0 0 1-.84-.61l1.285-5.386a.562.562 0 0 0-.182-.557l-4.204-3.602a.562.562 0 0 1 .321-.988l5.518-.442a.563.563 0 0 0 .475-.345L11.48 3.5Z" />
              </svg>
            </button>

            <!-- Reuse button -->
            <button
              @click="reusePrompt(item)"
              class="p-1.5 rounded-lg text-gray-400 hover:text-[#3B7AB1] hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
              title="Nochmal verwenden"
              :data-testid="`reuse-btn-${item.id}`"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
              </svg>
            </button>

            <!-- Delete button -->
            <button
              v-if="deleteConfirmId !== item.id"
              @click="deleteConfirmId = item.id"
              class="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              title="Loeschen"
              :data-testid="`delete-btn-${item.id}`"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
              </svg>
            </button>

            <!-- Delete confirm -->
            <div v-else class="flex items-center gap-1">
              <button
                @click="deleteEntry(item.id)"
                class="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                :data-testid="`confirm-delete-${item.id}`"
              >
                Loeschen
              </button>
              <button
                @click="deleteConfirmId = null"
                class="px-2 py-1 text-xs bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors"
              >
                Abbrechen
              </button>
            </div>
          </div>
        </div>

        <!-- Prompt text -->
        <div class="mb-2">
          <div class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Prompt:</div>
          <p class="text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700/50 rounded-lg px-3 py-2">
            {{ truncateText(item.prompt_text, 300) }}
          </p>
        </div>

        <!-- Result text -->
        <div v-if="item.result_text" class="mb-2">
          <div class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Ergebnis:</div>
          <p class="text-sm text-gray-700 dark:text-gray-300 bg-green-50 dark:bg-green-900/10 rounded-lg px-3 py-2 border border-green-200 dark:border-green-800/30">
            {{ truncateText(item.result_text, 400) }}
          </p>
        </div>

        <!-- Bottom row: tokens + cost -->
        <div class="flex items-center gap-4 text-xs text-gray-400 mt-2">
          <span v-if="item.tokens_used" class="flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3.5 h-3.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
            </svg>
            {{ item.tokens_used.toLocaleString('de-DE') }} Tokens
          </span>
          <span v-if="item.estimated_cost" class="flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3.5 h-3.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18V10.5Zm-12 0h.008v.008H6V10.5Z" />
            </svg>
            {{ formatCost(item.estimated_cost) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 mt-6" data-testid="pagination">
      <button
        @click="page = Math.max(1, page - 1); fetchHistory()"
        :disabled="page <= 1"
        class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        Zurueck
      </button>
      <span class="text-sm text-gray-500 dark:text-gray-400">
        Seite {{ page }} von {{ totalPages }} ({{ total }} Eintraege)
      </span>
      <button
        @click="page = Math.min(totalPages, page + 1); fetchHistory()"
        :disabled="page >= totalPages"
        class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        Weiter
      </button>
    </div>
  </div>
</template>
