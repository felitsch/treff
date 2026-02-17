<script setup>
/**
 * PostPerformanceInput.vue
 *
 * Form component for manually entering social media performance metrics
 * for a post (likes, comments, shares, saves, reach).
 * Calculates and displays engagement rate in real-time.
 *
 * Props:
 *   - postId: number - The ID of the post to track
 *   - initialData: object - Pre-filled performance data (optional)
 *
 * Emits:
 *   - saved: When metrics are successfully saved
 */
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import AppIcon from '@/components/icons/AppIcon.vue'

const props = defineProps({
  postId: { type: Number, required: true },
  initialData: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['saved'])
const toast = useToast()

const saving = ref(false)
const loading = ref(false)

const likes = ref(null)
const comments = ref(null)
const shares = ref(null)
const saves = ref(null)
const reach = ref(null)
const lastUpdated = ref(null)

// Computed engagement rate
const engagementRate = computed(() => {
  const l = parseInt(likes.value) || 0
  const c = parseInt(comments.value) || 0
  const s = parseInt(shares.value) || 0
  const r = parseInt(reach.value) || 0
  if (r <= 0) return null
  return ((l + c + s) / r * 100).toFixed(2)
})

// Engagement rate color coding
const engagementColor = computed(() => {
  const rate = parseFloat(engagementRate.value)
  if (isNaN(rate)) return 'text-gray-400'
  if (rate >= 5) return 'text-green-600 dark:text-green-400'
  if (rate >= 3) return 'text-blue-600 dark:text-blue-400'
  if (rate >= 1) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-500 dark:text-red-400'
})

const engagementLabel = computed(() => {
  const rate = parseFloat(engagementRate.value)
  if (isNaN(rate)) return ''
  if (rate >= 5) return 'Hervorragend'
  if (rate >= 3) return 'Gut'
  if (rate >= 1) return 'Durchschnittlich'
  return 'Niedrig'
})

// Has any metric been set
const hasMetrics = computed(() => {
  return likes.value !== null || comments.value !== null ||
    shares.value !== null || saves.value !== null || reach.value !== null
})

// Initialize from initial data or fetch from API
function loadFromData(data) {
  likes.value = data.perf_likes ?? data.likes ?? null
  comments.value = data.perf_comments ?? data.comments ?? null
  shares.value = data.perf_shares ?? data.shares ?? null
  saves.value = data.perf_saves ?? data.saves ?? null
  reach.value = data.perf_reach ?? data.reach ?? null
  lastUpdated.value = data.perf_updated_at || null
}

async function fetchPerformance() {
  loading.value = true
  try {
    const res = await api.get(`/api/analytics/performance/${props.postId}`)
    loadFromData(res.data)
  } catch (err) {
    // No metrics yet — that's fine
  } finally {
    loading.value = false
  }
}

async function savePerformance() {
  saving.value = true
  try {
    const res = await api.put(`/api/analytics/performance/${props.postId}`, {
      likes: likes.value !== null && likes.value !== '' ? parseInt(likes.value) : null,
      comments: comments.value !== null && comments.value !== '' ? parseInt(comments.value) : null,
      shares: shares.value !== null && shares.value !== '' ? parseInt(shares.value) : null,
      saves: saves.value !== null && saves.value !== '' ? parseInt(saves.value) : null,
      reach: reach.value !== null && reach.value !== '' ? parseInt(reach.value) : null,
    })
    lastUpdated.value = res.data.perf_updated_at
    toast.success('Performance-Metriken gespeichert')
    emit('saved', res.data)
  } catch (err) {
    toast.error('Fehler beim Speichern der Metriken')
  } finally {
    saving.value = false
  }
}

watch(() => props.initialData, (newData) => {
  if (newData && Object.keys(newData).length > 0) {
    loadFromData(newData)
  }
}, { immediate: true })

onMounted(() => {
  if (!props.initialData || Object.keys(props.initialData).length === 0) {
    fetchPerformance()
  }
})
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5" data-testid="performance-input">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
        <AppIcon name="chart-bar" class="w-5 h-5" />
        Performance-Metriken
      </h3>
      <span v-if="lastUpdated" class="text-xs text-gray-400 dark:text-gray-500">
        Aktualisiert: {{ new Date(lastUpdated).toLocaleDateString('de-DE') }}
      </span>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-8">
      <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#3B7AB1]"></div>
    </div>

    <div v-else>
      <!-- Metrics grid -->
      <div class="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-4">
        <!-- Likes -->
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
            <AppIcon name="heart" class="w-3.5 h-3.5 inline-block" /> Likes
          </label>
          <input
            v-model="likes"
            type="number"
            min="0"
            placeholder="0"
            class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#3B7AB1]/50 focus:border-[#3B7AB1] transition"
            data-testid="perf-likes-input"
          />
        </div>

        <!-- Comments -->
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
            <AppIcon name="chat-bubble" class="w-3.5 h-3.5 inline-block" /> Kommentare
          </label>
          <input
            v-model="comments"
            type="number"
            min="0"
            placeholder="0"
            class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#3B7AB1]/50 focus:border-[#3B7AB1] transition"
            data-testid="perf-comments-input"
          />
        </div>

        <!-- Shares -->
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
            <AppIcon name="arrow-path" class="w-3.5 h-3.5 inline-block" /> Shares
          </label>
          <input
            v-model="shares"
            type="number"
            min="0"
            placeholder="0"
            class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#3B7AB1]/50 focus:border-[#3B7AB1] transition"
            data-testid="perf-shares-input"
          />
        </div>

        <!-- Saves -->
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
            <AppIcon name="bookmark" class="w-3.5 h-3.5 inline-block" /> Saves
          </label>
          <input
            v-model="saves"
            type="number"
            min="0"
            placeholder="0"
            class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#3B7AB1]/50 focus:border-[#3B7AB1] transition"
            data-testid="perf-saves-input"
          />
        </div>

        <!-- Reach -->
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
            <AppIcon name="eye" class="w-3.5 h-3.5 inline-block" /> Reichweite
          </label>
          <input
            v-model="reach"
            type="number"
            min="0"
            placeholder="0"
            class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#3B7AB1]/50 focus:border-[#3B7AB1] transition"
            data-testid="perf-reach-input"
          />
        </div>
      </div>

      <!-- Engagement Rate display -->
      <div class="flex items-center justify-between bg-gray-50 dark:bg-gray-700/50 rounded-lg px-4 py-3 mb-4">
        <div class="flex items-center gap-2">
          <span class="text-sm font-medium text-gray-600 dark:text-gray-300">Engagement Rate:</span>
          <span
            class="text-lg font-bold"
            :class="engagementColor"
            data-testid="engagement-rate"
          >
            {{ engagementRate !== null ? engagementRate + '%' : '—' }}
          </span>
          <span v-if="engagementLabel" class="text-xs px-2 py-0.5 rounded-full" :class="{
            'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400': engagementLabel === 'Hervorragend',
            'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400': engagementLabel === 'Gut',
            'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400': engagementLabel === 'Durchschnittlich',
            'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400': engagementLabel === 'Niedrig',
          }">
            {{ engagementLabel }}
          </span>
        </div>
        <span class="text-xs text-gray-400 dark:text-gray-500">
          (Likes + Kommentare + Shares) / Reichweite
        </span>
      </div>

      <!-- Save button -->
      <div class="flex justify-end">
        <button
          @click="savePerformance"
          :disabled="saving"
          class="flex items-center gap-2 px-4 py-2 bg-[#3B7AB1] text-white text-sm font-medium rounded-lg hover:bg-[#2E6A9E] disabled:opacity-50 disabled:cursor-not-allowed transition"
          data-testid="save-performance-btn"
        >
          <span v-if="saving" class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
          <AppIcon v-else name="document" class="w-4 h-4" />
          {{ saving ? 'Speichern...' : 'Metriken speichern' }}
        </button>
      </div>
    </div>
  </div>
</template>
