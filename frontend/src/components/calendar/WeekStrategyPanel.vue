<script setup>
/**
 * WeekStrategyPanel.vue
 *
 * Collapsible sidebar panel for the Calendar view that shows weekly
 * strategy recommendations based on the content strategy config.
 * Analyzes scheduled posts and suggests improvements.
 *
 * @see backend/app/api/routes/calendar.py - strategy-recommendations endpoint
 * @see frontend/src/config/seasonalCalendar.js - Seasonal calendar data
 * @see frontend/src/config/contentPillars.js - Content pillar definitions
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import AppIcon from '@/components/icons/AppIcon.vue'

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: true,
  },
  /** Current week in YYYY-Www format (e.g. "2026-W08") */
  week: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['toggle', 'refresh-calendar'])

const router = useRouter()
const loading = ref(false)
const error = ref(null)
const data = ref(null)

async function fetchRecommendations() {
  if (props.collapsed) return
  loading.value = true
  error.value = null
  try {
    const params = props.week ? { week: props.week } : {}
    const res = await api.get('/api/calendar/strategy-recommendations', { params })
    data.value = res.data
  } catch (err) {
    error.value = 'Strategie-Daten konnten nicht geladen werden'
  } finally {
    loading.value = false
  }
}

onMounted(fetchRecommendations)
watch(() => props.week, fetchRecommendations)
watch(() => props.collapsed, (val) => {
  if (!val && !data.value) fetchRecommendations()
})

// Computed helpers
const summary = computed(() => data.value?.summary || {})
const warnings = computed(() => data.value?.warnings || [])
const recommendations = computed(() => data.value?.recommendations || [])
const quickActions = computed(() => data.value?.quick_actions || [])
const seasonalContext = computed(() => data.value?.seasonal_context || '')
const optimalTimes = computed(() => data.value?.optimal_posting_times || {})

const postProgress = computed(() => {
  const total = summary.value.total_posts || 0
  const goal = summary.value.weekly_goal || 5
  return Math.min(100, Math.round((total / goal) * 100))
})

const reelProgress = computed(() => {
  const count = summary.value.video_count || 0
  const goal = summary.value.reels_goal || 3
  return Math.min(100, Math.round((count / goal) * 100))
})

const progressColor = computed(() => {
  const pct = postProgress.value
  if (pct >= 80) return 'bg-green-500'
  if (pct >= 50) return 'bg-yellow-500'
  return 'bg-red-500'
})

const reelProgressColor = computed(() => {
  const pct = reelProgress.value
  if (pct >= 80) return 'bg-green-500'
  if (pct >= 50) return 'bg-yellow-500'
  return 'bg-red-500'
})

// Country labels
const countryLabels = {
  usa: 'USA', kanada: 'Kanada', australien: 'Australien',
  neuseeland: 'Neuseeland', irland: 'Irland',
}

const countrySummary = computed(() => {
  const counts = summary.value.country_counts || {}
  const entries = Object.entries(counts)
  if (entries.length === 0) return 'Keine Länder'
  return entries.map(([c, n]) => `${countryLabels[c] || c} (${n})`).join(', ')
})

// Quick action handler: navigate to create post with preselection
function handleQuickAction(action) {
  const query = {}
  if (action.platform) query.platform = action.platform
  if (action.category) query.category = action.category
  if (action.country) query.country = action.country
  router.push({ path: '/create/quick', query })
}

// Platform labels for optimal times
const platformLabels = {
  instagram_feed: 'IG Feed',
  instagram_story: 'IG Story',
  instagram_reel: 'IG Reel',
  tiktok: 'TikTok',
}
</script>

<template>
  <aside
    class="transition-all duration-300 flex-shrink-0 overflow-hidden"
    :class="collapsed ? 'w-0' : 'w-72 xl:w-80'"
    aria-label="Wochen-Strategie-Assistent"
  >
    <div
      v-if="!collapsed"
      class="w-72 xl:w-80 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-y-auto max-h-[calc(100vh-8rem)]"
    >
      <!-- Header -->
      <div class="sticky top-0 z-10 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-3">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-bold text-gray-900 dark:text-gray-100 flex items-center gap-1.5">
            <AppIcon name="fire" class="w-5 h-5" />
            Wochen-Strategie
          </h3>
          <div class="flex items-center gap-1">
            <button
              @click="fetchRecommendations"
              class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded transition-colors"
              title="Empfehlungen aktualisieren"
              :disabled="loading"
            >
              <svg class="w-4 h-4" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            <button
              @click="emit('toggle')"
              class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded transition-colors"
              title="Panel schließen"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        <p v-if="data" class="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">
          {{ data.start_date }} - {{ data.end_date }}
        </p>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="p-4 text-center">
        <div class="animate-pulse space-y-3">
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mx-auto"></div>
          <div class="h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mx-auto"></div>
        </div>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="p-4 text-center text-sm text-red-600 dark:text-red-400">
        {{ error }}
        <button @click="fetchRecommendations" class="block mx-auto mt-2 text-blue-600 hover:underline text-xs">
          Erneut versuchen
        </button>
      </div>

      <!-- Content -->
      <div v-else-if="data" class="divide-y divide-gray-100 dark:divide-gray-700">

        <!-- Progress Bars -->
        <div class="p-3 space-y-2.5">
          <!-- Total Posts -->
          <div>
            <div class="flex items-center justify-between text-xs mb-1">
              <span class="font-medium text-gray-700 dark:text-gray-300">Posts geplant</span>
              <span class="font-bold" :class="postProgress >= 80 ? 'text-green-600 dark:text-green-400' : postProgress >= 50 ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'">
                {{ summary.total_posts }} / {{ summary.weekly_goal }}
              </span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all duration-500"
                :class="progressColor"
                :style="{ width: postProgress + '%' }"
              ></div>
            </div>
          </div>

          <!-- Reels/Video -->
          <div>
            <div class="flex items-center justify-between text-xs mb-1">
              <span class="font-medium text-gray-700 dark:text-gray-300">Reels / Video</span>
              <span class="font-bold" :class="reelProgress >= 80 ? 'text-green-600 dark:text-green-400' : reelProgress >= 50 ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'">
                {{ summary.video_count }} / {{ summary.reels_goal }}
              </span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all duration-500"
                :class="reelProgressColor"
                :style="{ width: reelProgress + '%' }"
              ></div>
            </div>
          </div>

          <!-- Countries -->
          <div class="text-xs text-gray-600 dark:text-gray-400">
            <span class="font-medium">Länder:</span> {{ countrySummary }}
          </div>
        </div>

        <!-- Warnings (high severity) -->
        <div v-if="warnings.length > 0" class="p-3 space-y-2">
          <div
            v-for="(w, i) in warnings"
            :key="'warn-' + i"
            class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-2.5 text-xs"
          >
            <div class="flex items-start gap-2">
              <span class="text-base flex-shrink-0">{{ w.icon }}</span>
              <p class="text-red-800 dark:text-red-200 font-medium leading-relaxed">{{ w.message }}</p>
            </div>
          </div>
        </div>

        <!-- Seasonal Context -->
        <div v-if="seasonalContext" class="p-3">
          <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-2.5">
            <div class="flex items-start gap-2">
              <AppIcon name="calendar" class="w-5 h-5 flex-shrink-0 text-blue-600 dark:text-blue-400" />
              <p class="text-xs text-blue-800 dark:text-blue-200 leading-relaxed">{{ seasonalContext }}</p>
            </div>
          </div>
        </div>

        <!-- Recommendations -->
        <div v-if="recommendations.length > 0" class="p-3 space-y-1.5">
          <h4 class="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">Empfehlungen</h4>
          <div
            v-for="(r, i) in recommendations"
            :key="'rec-' + i"
            class="bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/50 rounded-lg p-2 text-xs"
          >
            <div class="flex items-start gap-1.5">
              <span class="flex-shrink-0">{{ r.icon }}</span>
              <p class="text-amber-900 dark:text-amber-200 leading-relaxed">{{ r.message }}</p>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div v-if="quickActions.length > 0" class="p-3">
          <h4 class="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">Schnell-Aktionen</h4>
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="(a, i) in quickActions"
              :key="'action-' + i"
              @click="handleQuickAction(a)"
              class="inline-flex items-center gap-1 px-2.5 py-1.5 text-[11px] font-medium rounded-lg border transition-colors
                bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600
                text-gray-700 dark:text-gray-300
                hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:border-blue-300 dark:hover:border-blue-600 hover:text-blue-700 dark:hover:text-blue-300"
            >
              <span>{{ a.icon }}</span>
              {{ a.label }}
            </button>
          </div>
        </div>

        <!-- Optimal Posting Times -->
        <div v-if="Object.keys(optimalTimes).length > 0" class="p-3">
          <h4 class="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">Optimale Posting-Zeiten</h4>
          <div class="space-y-1.5">
            <div
              v-for="(times, platform) in optimalTimes"
              :key="platform"
              class="text-xs"
            >
              <span class="font-medium text-gray-700 dark:text-gray-300">{{ platformLabels[platform] || platform }}:</span>
              <div class="flex flex-wrap gap-1 mt-0.5">
                <span
                  v-for="t in times.weekday"
                  :key="t"
                  class="inline-block px-1.5 py-0.5 rounded bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-[10px] font-medium"
                  :title="'Wochentag: ' + t"
                >
                  {{ t }}
                </span>
              </div>
            </div>
          </div>
          <p class="text-[10px] text-gray-400 dark:text-gray-500 mt-1.5 flex items-center gap-1">
            <span class="inline-block w-2 h-2 rounded bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-700"></span>
            = Optimale Wochentag-Slots
          </p>
        </div>

        <!-- All good state -->
        <div v-if="warnings.length === 0 && recommendations.length === 0" class="p-4 text-center">
          <AppIcon name="trophy" class="w-7 h-7 text-green-500" />
          <p class="text-sm font-medium text-green-600 dark:text-green-400 mt-1">Perfekt!</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">Alle Strategie-Ziele für diese Woche erreicht.</p>
        </div>
      </div>

      <!-- No data state -->
      <div v-else class="p-4 text-center text-sm text-gray-500 dark:text-gray-400">
        Keine Daten verfügbar
      </div>
    </div>
  </aside>
</template>
