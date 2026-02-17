<script setup>
/**
 * HookPerformanceChart — Hook Formula Performance Tracking
 *
 * Visualizes hook formula usage frequency, engagement data, and effectiveness.
 * Shows which of the 10 strategy hook formulas are used most, which are unused,
 * and correlates with real engagement data when available.
 *
 * @see Feature #321 (SI-06: Hook-Performance-Tracking & Optimierung)
 */
import { ref, onMounted, computed } from 'vue'
import api from '@/utils/api'
import BaseCard from '@/components/common/BaseCard.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const loading = ref(true)
const error = ref(null)
const data = ref(null)

async function fetchHookPerformance() {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/api/analytics/hook-performance')
    data.value = res.data
  } catch (err) {
    error.value = 'Hook-Performance-Daten konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

// Max usage count for scaling bars
const maxUsage = computed(() => {
  if (!data.value?.hook_stats) return 1
  const max = Math.max(...data.value.hook_stats.map(h => h.usage_count), 1)
  return max
})

// Category colors
const categoryColors = {
  curiosity: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-600 dark:text-blue-400', bar: 'bg-blue-500', icon: 'magnifying-glass' },
  emotion: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-600 dark:text-red-400', bar: 'bg-red-500', icon: 'heart' },
  urgency: { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-600 dark:text-amber-400', bar: 'bg-amber-500', icon: 'clock' },
  comparison: { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-600 dark:text-purple-400', bar: 'bg-purple-500', icon: 'arrows-right-left' },
  list: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-600 dark:text-green-400', bar: 'bg-green-500', icon: 'list-bullet' },
}

function getCategoryStyle(category) {
  return categoryColors[category] || categoryColors.curiosity
}

// Effectiveness stars
function effectivenessStars(value) {
  return Math.round(value / 2) // Convert 1-10 to 1-5 stars
}

onMounted(() => {
  fetchHookPerformance()
})

defineExpose({ refresh: fetchHookPerformance })
</script>

<template>
  <div data-testid="hook-performance-chart">
    <!-- Loading state -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 4" :key="i" class="bg-white dark:bg-gray-800 rounded-lg p-4 animate-pulse">
        <div class="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
        <div class="h-3 w-full bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 text-center">
      <p class="text-red-600 dark:text-red-400 text-sm">{{ error }}</p>
      <button @click="fetchHookPerformance" class="mt-2 px-3 py-1.5 text-xs bg-red-600 text-white rounded-lg hover:bg-red-700 transition">
        Erneut versuchen
      </button>
    </div>

    <!-- Hook Performance Content -->
    <div v-else-if="data" class="space-y-5">

      <!-- ═══ ROW 1: Summary Stats ═══ -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="bg-gray-50 dark:bg-gray-800 rounded-xl p-3.5 text-center">
          <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ data.total_posts_with_hook }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Posts mit Hook</p>
        </div>
        <div class="bg-gray-50 dark:bg-gray-800 rounded-xl p-3.5 text-center">
          <p class="text-2xl font-bold" :class="data.hook_coverage_pct >= 50 ? 'text-green-600' : 'text-amber-600'">
            {{ data.hook_coverage_pct }}%
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Hook-Abdeckung</p>
        </div>
        <div class="bg-gray-50 dark:bg-gray-800 rounded-xl p-3.5 text-center">
          <p class="text-2xl font-bold text-[#4C8BC2]">
            {{ data.hook_stats.filter(h => h.usage_count > 0).length }}
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Formeln genutzt</p>
        </div>
        <div class="bg-gray-50 dark:bg-gray-800 rounded-xl p-3.5 text-center">
          <p class="text-2xl font-bold text-red-500">{{ data.unused_hooks.length }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Ungenutzte Formeln</p>
        </div>
      </div>

      <!-- ═══ ROW 2: Hook Formula Bar Chart ═══ -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">

        <!-- Bar Chart (takes 2 cols) -->
        <div class="lg:col-span-2 space-y-2" data-testid="hook-usage-bars">
          <div class="flex items-center justify-between mb-2">
            <h4 class="text-sm font-semibold text-gray-900 dark:text-white">Nutzungshaeufigkeit & Effektivitaet</h4>
            <div class="flex items-center gap-3 text-[10px] text-gray-400">
              <span class="flex items-center gap-1">
                <span class="inline-block w-3 h-2 bg-[#4C8BC2] rounded-sm"></span> Nutzung
              </span>
              <span class="flex items-center gap-1">
                <span class="inline-block w-3 h-2 bg-[#FDD000] rounded-sm"></span> Effektivitaet
              </span>
            </div>
          </div>

          <div v-for="hook in data.hook_stats" :key="hook.id" class="group">
            <div class="flex items-center gap-2 mb-1">
              <span class="w-5 h-5 rounded flex items-center justify-center text-xs flex-shrink-0"
                :class="getCategoryStyle(hook.category).bg">
                <AppIcon :name="getCategoryStyle(hook.category).icon" class="w-3 h-3" />
              </span>
              <span class="text-xs font-medium text-gray-700 dark:text-gray-300 truncate flex-1">
                {{ hook.name }}
              </span>
              <span class="text-xs tabular-nums text-gray-500 dark:text-gray-400">
                {{ hook.usage_count }}x
              </span>
              <span v-if="hook.avg_engagement_rate !== null" class="text-[10px] tabular-nums text-green-500">
                {{ hook.avg_engagement_rate }}% Eng.
              </span>
            </div>
            <div class="flex items-center gap-1.5">
              <!-- Usage bar -->
              <div class="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div class="h-full rounded-full bg-[#4C8BC2] transition-all duration-500"
                  :style="{ width: (hook.usage_count / maxUsage * 100) + '%' }">
                </div>
              </div>
              <!-- Effectiveness bar (out of 10) -->
              <div class="w-16 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden flex-shrink-0">
                <div class="h-full rounded-full bg-[#FDD000] transition-all duration-500"
                  :style="{ width: (hook.strategy_effectiveness / 10 * 100) + '%' }">
                </div>
              </div>
              <span class="text-[10px] w-5 text-right tabular-nums text-gray-400">
                {{ hook.strategy_effectiveness }}/10
              </span>
            </div>
          </div>
        </div>

        <!-- Top Hooks This Week + Unused Hooks -->
        <div class="space-y-4">
          <!-- Top 3 This Week -->
          <div data-testid="top-hooks-week">
            <h4 class="text-sm font-semibold text-gray-900 dark:text-white mb-2.5">Top 3 diese Woche</h4>
            <div v-if="data.top_hooks_this_week.length === 0" class="text-center py-4">
              <p class="text-xs text-gray-400">Noch keine Hook-Nutzung diese Woche</p>
            </div>
            <div v-else class="space-y-2">
              <div v-for="(hook, idx) in data.top_hooks_this_week" :key="hook.id"
                class="flex items-center gap-2.5 p-2 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700">
                <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                  :class="idx === 0 ? 'bg-[#FDD000] text-gray-900' : idx === 1 ? 'bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200' : 'bg-amber-600/30 text-amber-700 dark:text-amber-400'">
                  {{ idx + 1 }}
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">{{ hook.name }}</p>
                </div>
                <span class="text-xs font-bold text-[#4C8BC2]">{{ hook.count }}x</span>
              </div>
            </div>
          </div>

          <!-- Unused Hooks -->
          <div data-testid="unused-hooks">
            <h4 class="text-sm font-semibold text-gray-900 dark:text-white mb-2.5">
              Noch ungenutzt
              <span class="text-xs font-normal text-gray-400 ml-1">({{ data.unused_hooks.length }})</span>
            </h4>
            <div v-if="data.unused_hooks.length === 0" class="text-center py-3">
              <div class="w-10 h-10 mx-auto bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-1.5">
                <AppIcon name="check-circle" class="w-6 h-6 text-green-500" />
              </div>
              <p class="text-xs font-medium text-green-600 dark:text-green-400">Alle Formeln genutzt!</p>
            </div>
            <div v-else class="space-y-1.5">
              <div v-for="hook in data.unused_hooks.slice(0, 5)" :key="hook.id"
                class="flex items-center gap-2 p-2 rounded-lg border border-dashed border-gray-200 dark:border-gray-700 hover:border-[#4C8BC2]/50 hover:bg-[#4C8BC2]/5 transition-colors cursor-default">
                <span class="w-4 h-4 rounded flex items-center justify-center flex-shrink-0"
                  :class="getCategoryStyle(hook.category).bg">
                  <AppIcon :name="getCategoryStyle(hook.category).icon" class="w-2.5 h-2.5" />
                </span>
                <span class="text-xs text-gray-600 dark:text-gray-400 truncate flex-1">{{ hook.name }}</span>
                <span class="text-[10px] text-gray-400">{{ hook.effectiveness }}/10</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
