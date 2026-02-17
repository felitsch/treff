<script setup>
/**
 * PerformancePulseWidget.vue — Mini line chart showing posting frequency
 * vs. goal (Ist vs. Soll) over the last 4 weeks with trend arrow.
 *
 * Uses a lightweight SVG chart (no external chart library dependency).
 *
 * Part of Dashboard 6-Widget-Architektur (Feature #310).
 *
 * Props:
 *   data (Object) — Performance pulse data from dashboard-widgets API
 *     { weeks: [], goal: 3, trend: 'up'|'down'|'stable', current_week_count: 0 }
 *
 * @see DashboardView.vue — Parent integration
 */
import { computed } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({
      weeks: [],
      goal: 3,
      trend: 'stable',
      current_week_count: 0,
    }),
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['refresh'])

// Chart dimensions
const CHART_W = 240
const CHART_H = 80
const PADDING = 8

// Compute SVG path for the line chart
const chartData = computed(() => {
  const weeks = props.data?.weeks || []
  if (weeks.length === 0) return { linePath: '', areaPath: '', goalY: 0, points: [] }

  const counts = weeks.map(w => w.count)
  const maxVal = Math.max(...counts, props.data.goal || 3, 1)

  const usableW = CHART_W - PADDING * 2
  const usableH = CHART_H - PADDING * 2

  const points = counts.map((val, i) => ({
    x: PADDING + (i / Math.max(counts.length - 1, 1)) * usableW,
    y: PADDING + usableH - (val / maxVal) * usableH,
    value: val,
    label: weeks[i]?.label || '',
  }))

  // Build line path
  let linePath = ''
  points.forEach((p, i) => {
    if (i === 0) linePath += `M ${p.x} ${p.y}`
    else linePath += ` L ${p.x} ${p.y}`
  })

  // Build area path (fill below line)
  let areaPath = linePath
  if (points.length > 0) {
    areaPath += ` L ${points[points.length - 1].x} ${PADDING + usableH}`
    areaPath += ` L ${points[0].x} ${PADDING + usableH} Z`
  }

  // Goal line Y position
  const goalY = PADDING + usableH - ((props.data.goal || 3) / maxVal) * usableH

  return { linePath, areaPath, goalY, points }
})

// Trend arrow and color
const trendInfo = computed(() => {
  const trend = props.data?.trend || 'stable'
  switch (trend) {
    case 'up': return { icon: '\u2191', label: 'Aufwaerts', class: 'text-green-600 dark:text-green-400', bg: 'bg-green-50 dark:bg-green-900/30' }
    case 'down': return { icon: '\u2193', label: 'Abwaerts', class: 'text-red-600 dark:text-red-400', bg: 'bg-red-50 dark:bg-red-900/30' }
    default: return { icon: '\u2192', label: 'Stabil', class: 'text-gray-600 dark:text-gray-400', bg: 'bg-gray-50 dark:bg-gray-700/30' }
  }
})

// Goal achievement percentage
const goalPercent = computed(() => {
  const goal = props.data?.goal || 3
  const current = props.data?.current_week_count || 0
  if (goal === 0) return 100
  return Math.min(Math.round((current / goal) * 100), 100)
})
</script>

<template>
  <BaseCard padding="none" data-tour="dashboard-performance-pulse" data-testid="performance-pulse-widget">
    <template #header>
      <h2 class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
        <span>📈</span> Performance Pulse
      </h2>
    </template>
    <template #headerAction>
      <div class="flex items-center gap-2">
        <button
          @click="emit('refresh')"
          class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          title="Aktualisieren"
          :disabled="loading"
        >
          <svg class="w-4 h-4" :class="{ 'animate-spin': loading }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
        <router-link to="/analytics" class="text-xs text-[#4C8BC2] hover:text-blue-600 dark:hover:text-blue-400 font-medium">
          Alle anzeigen &rarr;
        </router-link>
      </div>
    </template>

    <div class="p-4">
      <!-- Loading skeleton -->
      <div v-if="loading" class="space-y-3 animate-pulse">
        <div class="h-20 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
        <div class="flex justify-between">
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
        </div>
      </div>

      <template v-else>
        <!-- Stats row -->
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <span class="text-2xl font-bold text-gray-900 dark:text-white tabular-nums">
              {{ data.current_week_count }}
            </span>
            <span class="text-xs text-gray-500 dark:text-gray-400">/{{ data.goal }} Posts diese Woche</span>
          </div>
          <span
            class="flex items-center gap-0.5 text-xs font-semibold px-2 py-0.5 rounded-full"
            :class="[trendInfo.class, trendInfo.bg]"
          >
            {{ trendInfo.icon }} {{ trendInfo.label }}
          </span>
        </div>

        <!-- SVG Line Chart -->
        <div class="relative rounded-lg bg-gray-50 dark:bg-gray-700/30 p-1">
          <svg
            :viewBox="`0 0 ${CHART_W} ${CHART_H}`"
            class="w-full h-20"
            preserveAspectRatio="xMidYMid meet"
          >
            <!-- Area fill -->
            <path
              v-if="chartData.areaPath"
              :d="chartData.areaPath"
              fill="url(#pulse-gradient)"
              opacity="0.3"
            />

            <!-- Goal line (dashed) -->
            <line
              v-if="chartData.goalY"
              :x1="PADDING"
              :y1="chartData.goalY"
              :x2="CHART_W - PADDING"
              :y2="chartData.goalY"
              stroke="#FDD000"
              stroke-width="1"
              stroke-dasharray="4 3"
              opacity="0.7"
            />

            <!-- Data line -->
            <path
              v-if="chartData.linePath"
              :d="chartData.linePath"
              fill="none"
              stroke="#4C8BC2"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />

            <!-- Data points -->
            <circle
              v-for="(point, i) in chartData.points"
              :key="i"
              :cx="point.x"
              :cy="point.y"
              r="3"
              fill="white"
              stroke="#4C8BC2"
              stroke-width="2"
            />

            <!-- Week labels at bottom -->
            <text
              v-for="(point, i) in chartData.points"
              :key="'label-'+i"
              :x="point.x"
              :y="CHART_H - 1"
              text-anchor="middle"
              class="fill-gray-400 dark:fill-gray-500"
              font-size="8"
            >
              {{ point.label }}
            </text>

            <!-- Value labels above points -->
            <text
              v-for="(point, i) in chartData.points"
              :key="'val-'+i"
              :x="point.x"
              :y="point.y - 7"
              text-anchor="middle"
              class="fill-gray-700 dark:fill-gray-300"
              font-size="9"
              font-weight="600"
            >
              {{ point.value }}
            </text>

            <!-- Gradient definition -->
            <defs>
              <linearGradient id="pulse-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#4C8BC2" stop-opacity="0.4" />
                <stop offset="100%" stop-color="#4C8BC2" stop-opacity="0.05" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        <!-- Legend row -->
        <div class="flex items-center justify-between mt-2 text-[10px] text-gray-400 dark:text-gray-500">
          <div class="flex items-center gap-3">
            <span class="flex items-center gap-1">
              <span class="w-3 h-0.5 bg-[#4C8BC2] rounded-full inline-block"></span>
              Ist
            </span>
            <span class="flex items-center gap-1">
              <span class="w-3 h-0.5 bg-[#FDD000] rounded-full inline-block border-dashed"></span>
              Soll ({{ data.goal }}/Woche)
            </span>
          </div>
          <span>{{ goalPercent }}% Ziel erreicht</span>
        </div>
      </template>
    </div>
  </BaseCard>
</template>
