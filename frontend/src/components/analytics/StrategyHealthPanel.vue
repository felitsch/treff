<script setup>
/**
 * StrategyHealthPanel — IST-vs-SOLL Strategy Dashboard
 *
 * Shows at a glance whether the user is on track with their content strategy:
 * - Overall health score (radial progress)
 * - Content Pillar distribution (7 pillars)
 * - Buyer Journey distribution (3 phases)
 * - Country rotation
 * - Platform mix
 * - Video/Reels ratio (target: 40%)
 * - Posting frequency this week
 * - Hook formula usage
 * - Top-3 action recommendations
 *
 * @see Feature #314 (SI-04: Strategie-IST-vs-SOLL Dashboard)
 */
import { ref, onMounted, computed } from 'vue'
import api from '@/utils/api'
import BaseCard from '@/components/common/BaseCard.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const loading = ref(true)
const error = ref(null)
const data = ref(null)

async function fetchStrategyHealth() {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/api/analytics/strategy-health')
    data.value = res.data
  } catch (err) {
    error.value = 'Strategie-Daten konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

// Overall score color
const scoreColor = computed(() => {
  if (!data.value) return '#6B7280'
  const s = data.value.overall_score
  if (s >= 80) return '#22C55E'
  if (s >= 50) return '#F59E0B'
  return '#EF4444'
})

// SVG radial progress for overall score
const scoreCircumference = 2 * Math.PI * 45
const scoreDashOffset = computed(() => {
  if (!data.value) return scoreCircumference
  return scoreCircumference - (data.value.overall_score / 100) * scoreCircumference
})

// Status color helper
function statusColor(status) {
  switch (status) {
    case 'green': return 'text-green-500'
    case 'yellow': return 'text-amber-500'
    case 'red': return 'text-red-500'
    default: return 'text-gray-400'
  }
}

function statusBg(status) {
  switch (status) {
    case 'green': return 'bg-green-500'
    case 'yellow': return 'bg-amber-500'
    case 'red': return 'bg-red-500'
    default: return 'bg-gray-400'
  }
}

function statusBgLight(status) {
  switch (status) {
    case 'green': return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
    case 'yellow': return 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800'
    case 'red': return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
    default: return 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
  }
}

function statusBarColor(status) {
  switch (status) {
    case 'green': return 'bg-green-500'
    case 'yellow': return 'bg-amber-500'
    case 'red': return 'bg-red-500'
    default: return 'bg-gray-400'
  }
}

function trendIcon(trend) {
  switch (trend) {
    case 'on_track': return 'arrow-trending-up'
    case 'behind': return 'minus'
    case 'at_risk': return 'arrow-trending-down'
    default: return 'minus'
  }
}

function trendColor(trend) {
  switch (trend) {
    case 'on_track': return 'text-green-500'
    case 'behind': return 'text-amber-500'
    case 'at_risk': return 'text-red-500'
    default: return 'text-gray-400'
  }
}

function recIcon(type) {
  switch (type) {
    case 'video': return 'film'
    case 'country': return 'globe-europe-africa'
    case 'journey': return 'arrow-trending-up'
    case 'pillar': return 'squares-2x2'
    case 'frequency': return 'calendar'
    default: return 'light-bulb'
  }
}

onMounted(() => {
  fetchStrategyHealth()
})

defineExpose({ refresh: fetchStrategyHealth })
</script>

<template>
  <div data-testid="strategy-health-panel">
    <!-- Loading state -->
    <div v-if="loading" class="space-y-4">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div v-for="i in 3" :key="i" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 animate-pulse">
          <div class="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded mb-3"></div>
          <div class="h-8 w-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 text-center">
      <p class="text-red-600 dark:text-red-400 text-sm">{{ error }}</p>
      <button @click="fetchStrategyHealth" class="mt-2 px-3 py-1.5 text-xs bg-red-600 text-white rounded-lg hover:bg-red-700 transition">
        Erneut versuchen
      </button>
    </div>

    <!-- Strategy Health Content -->
    <div v-else-if="data" class="space-y-5">

      <!-- ═══ ROW 1: Overall Score + Video Ratio + Posting Frequency ═══ -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">

        <!-- Overall Health Score (radial) -->
        <BaseCard padding="lg" :header-divider="false" data-testid="overall-score">
          <div class="flex items-center gap-4">
            <div class="relative flex-shrink-0">
              <svg width="100" height="100" viewBox="0 0 100 100" class="transform -rotate-90">
                <circle cx="50" cy="50" r="45" fill="none" stroke-width="8"
                  class="stroke-gray-200 dark:stroke-gray-700" />
                <circle cx="50" cy="50" r="45" fill="none" stroke-width="8"
                  :stroke="scoreColor"
                  stroke-linecap="round"
                  :stroke-dasharray="scoreCircumference"
                  :stroke-dashoffset="scoreDashOffset"
                  class="transition-all duration-700" />
              </svg>
              <div class="absolute inset-0 flex items-center justify-center">
                <span class="text-2xl font-bold" :style="{ color: scoreColor }">
                  {{ data.overall_score }}
                </span>
              </div>
            </div>
            <div>
              <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Strategie-Score</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Letzte 30 Tage
              </p>
              <p class="text-xs mt-1" :class="statusColor(data.overall_status)">
                {{ data.total_posts_30d }} Posts analysiert
              </p>
            </div>
          </div>
        </BaseCard>

        <!-- Video / Reels Ratio -->
        <BaseCard padding="lg" :header-divider="false" data-testid="video-ratio">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 rounded-lg flex items-center justify-center"
                :class="data.video_ratio.status === 'green' ? 'bg-green-100 dark:bg-green-900/30' : data.video_ratio.status === 'yellow' ? 'bg-amber-100 dark:bg-amber-900/30' : 'bg-red-100 dark:bg-red-900/30'">
                <AppIcon name="film" class="w-5 h-5" />
              </div>
              <div>
                <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Reels-Anteil</h3>
              </div>
            </div>
            <span class="text-lg font-bold" :class="statusColor(data.video_ratio.status)">
              {{ data.video_ratio.actual_pct }}%
            </span>
          </div>
          <div class="w-full h-2.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mb-1.5">
            <div class="h-full rounded-full transition-all duration-500"
              :class="statusBarColor(data.video_ratio.status)"
              :style="{ width: Math.min(100, data.video_ratio.actual_pct / data.video_ratio.target_pct * 100) + '%' }">
            </div>
          </div>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            Ziel: {{ data.video_ratio.target_pct }}% &middot;
            {{ data.video_ratio.actual_count }} von {{ data.video_ratio.total_posts }} Posts
          </p>
        </BaseCard>

        <!-- Posting Frequency This Week -->
        <BaseCard padding="lg" :header-divider="false" data-testid="posting-frequency">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 rounded-lg flex items-center justify-center"
                :class="data.posting_frequency.status === 'green' ? 'bg-green-100 dark:bg-green-900/30' : data.posting_frequency.status === 'yellow' ? 'bg-amber-100 dark:bg-amber-900/30' : 'bg-red-100 dark:bg-red-900/30'">
                <AppIcon name="calendar" class="w-5 h-5" />
              </div>
              <div>
                <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Posting-Frequenz</h3>
              </div>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="text-lg font-bold" :class="statusColor(data.posting_frequency.status)">
                {{ data.posting_frequency.actual }}
              </span>
              <span class="text-sm text-gray-400">/{{ data.posting_frequency.target_optimal }}</span>
              <AppIcon
                :name="trendIcon(data.posting_frequency.trend)"
                class="w-4 h-4"
                :class="trendColor(data.posting_frequency.trend)"
              />
            </div>
          </div>
          <div class="w-full h-2.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mb-1.5">
            <div class="h-full rounded-full transition-all duration-500"
              :class="statusBarColor(data.posting_frequency.status)"
              :style="{ width: Math.min(100, data.posting_frequency.score) + '%' }">
            </div>
          </div>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            Diese Woche &middot; Tag {{ data.posting_frequency.days_elapsed }}/7 &middot;
            Ziel: {{ data.posting_frequency.target_min }}-{{ data.posting_frequency.target_max }} Posts
          </p>
        </BaseCard>
      </div>

      <!-- ═══ ROW 2: Pillar Health + Recommendations ═══ -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">

        <!-- Content Pillar Health (takes 2 cols on desktop) -->
        <BaseCard padding="lg" :header-divider="false" class="lg:col-span-2" data-testid="pillar-health">
          <template #header>
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Content-Pillar Verteilung</h3>
          </template>
          <template #headerAction>
            <span class="text-xs text-gray-400">IST vs. SOLL (30 Tage)</span>
          </template>
          <div class="space-y-2.5">
            <div v-for="pillar in data.pillar_health" :key="pillar.id" class="group">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-sm flex-shrink-0 w-5 text-center">{{ pillar.emoji }}</span>
                <span class="text-xs font-medium text-gray-700 dark:text-gray-300 truncate flex-1">
                  {{ pillar.name }}
                </span>
                <span class="text-xs tabular-nums"
                  :class="statusColor(pillar.status)">
                  {{ pillar.actual_pct }}%
                </span>
                <span class="text-xs text-gray-400 tabular-nums">/ {{ pillar.target_pct }}%</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div class="h-full rounded-full transition-all duration-500"
                    :class="statusBarColor(pillar.status)"
                    :style="{ width: Math.min(100, pillar.target_pct > 0 ? (pillar.actual_pct / pillar.target_pct * 100) : 0) + '%' }">
                  </div>
                </div>
                <span class="text-[10px] w-8 text-right tabular-nums"
                  :class="statusColor(pillar.status)">
                  {{ pillar.actual_count }}
                </span>
              </div>
            </div>
          </div>
        </BaseCard>

        <!-- Top-3 Recommendations -->
        <BaseCard padding="lg" :header-divider="false" data-testid="recommendations">
          <template #header>
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Handlungsempfehlungen</h3>
          </template>
          <div v-if="data.recommendations.length === 0" class="text-center py-6">
            <div class="w-12 h-12 mx-auto bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-2">
              <AppIcon name="check-circle" class="w-7 h-7 text-green-500" />
            </div>
            <p class="text-sm font-medium text-green-600 dark:text-green-400">Alles auf Kurs!</p>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Keine Anpassungen noetig.</p>
          </div>
          <div v-else class="space-y-3">
            <div v-for="(rec, idx) in data.recommendations" :key="idx"
              class="flex items-start gap-3 p-2.5 rounded-lg border transition-colors"
              :class="statusBgLight(idx === 0 ? 'red' : idx === 1 ? 'yellow' : 'green')">
              <div class="flex-shrink-0 w-6 h-6 rounded-full bg-white dark:bg-gray-700 shadow-sm flex items-center justify-center">
                <span class="text-xs font-bold text-gray-700 dark:text-gray-300">{{ idx + 1 }}</span>
              </div>
              <p class="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">
                {{ rec.message }}
              </p>
            </div>
          </div>
        </BaseCard>
      </div>

      <!-- ═══ ROW 3: Journey + Country + Platform ═══ -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">

        <!-- Buyer Journey Health -->
        <BaseCard padding="lg" :header-divider="false" data-testid="journey-health">
          <template #header>
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Buyer Journey</h3>
          </template>
          <div class="space-y-3 mt-1">
            <div v-for="stage in data.journey_health" :key="stage.id">
              <div class="flex justify-between items-center mb-1">
                <span class="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">
                  {{ stage.id === 'awareness' ? 'Awareness' : stage.id === 'consideration' ? 'Consideration' : 'Decision' }}
                </span>
                <span class="text-xs tabular-nums" :class="statusColor(stage.status)">
                  {{ stage.actual_pct }}% <span class="text-gray-400">/ {{ stage.target_pct }}%</span>
                </span>
              </div>
              <div class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-500"
                  :class="statusBarColor(stage.status)"
                  :style="{ width: Math.min(100, stage.target_pct > 0 ? (stage.actual_pct / stage.target_pct * 100) : 0) + '%' }">
                </div>
              </div>
            </div>
          </div>
        </BaseCard>

        <!-- Country Rotation -->
        <BaseCard padding="lg" :header-divider="false" data-testid="country-health">
          <template #header>
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Länder-Rotation</h3>
          </template>
          <div class="space-y-2.5 mt-1">
            <div v-for="country in data.country_health" :key="country.id" class="flex items-center gap-2">
              <span class="text-xs font-medium text-gray-700 dark:text-gray-300 w-20 truncate">
                {{ country.name }}
              </span>
              <div class="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-500"
                  :class="statusBarColor(country.status)"
                  :style="{ width: Math.min(100, country.target_pct > 0 ? (country.actual_pct / country.target_pct * 100) : 0) + '%' }">
                </div>
              </div>
              <span class="text-[10px] tabular-nums w-10 text-right" :class="statusColor(country.status)">
                {{ country.actual_count }}
              </span>
            </div>
          </div>
        </BaseCard>

        <!-- Platform Mix -->
        <BaseCard padding="lg" :header-divider="false" data-testid="platform-health">
          <template #header>
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Plattform-Mix</h3>
          </template>
          <div class="space-y-3 mt-1">
            <div v-for="plat in data.platform_health" :key="plat.id">
              <div class="flex justify-between items-center mb-1">
                <span class="text-xs font-medium text-gray-700 dark:text-gray-300">
                  {{ plat.name }}
                </span>
                <span class="text-xs tabular-nums" :class="statusColor(plat.status)">
                  {{ plat.actual_pct }}% <span class="text-gray-400">/ {{ plat.target_pct }}%</span>
                </span>
              </div>
              <div class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-500"
                  :class="statusBarColor(plat.status)"
                  :style="{ width: Math.min(100, plat.target_pct > 0 ? (plat.actual_pct / plat.target_pct * 100) : 0) + '%' }">
                </div>
              </div>
            </div>
          </div>
        </BaseCard>
      </div>

      <!-- ═══ ROW 4: Hook Formula Usage ═══ -->
      <BaseCard padding="lg" :header-divider="false" data-testid="hook-usage">
        <template #header>
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Hook-Formel Nutzung</h3>
        </template>
        <template #headerAction>
          <span class="text-xs text-gray-400">
            {{ data.hook_usage.used_count }}/{{ data.hook_usage.total_count }} diese Woche
          </span>
        </template>
        <div class="flex flex-wrap gap-2 mt-1">
          <div v-for="hook in data.hook_usage.hooks" :key="hook.id"
            class="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs border transition-colors"
            :class="hook.used
              ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-700 text-green-700 dark:text-green-400'
              : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400'"
          >
            <span v-if="hook.used" class="text-green-500">&#10003;</span>
            <span v-else class="text-gray-300 dark:text-gray-600">&#9711;</span>
            <span class="font-medium">{{ hook.name }}</span>
            <span class="text-[10px] opacity-60">({{ hook.effectiveness }}/10)</span>
          </div>
        </div>
      </BaseCard>

    </div>
  </div>
</template>
