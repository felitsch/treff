<script setup>
/**
 * ActivityHeatmap.vue — GitHub-style contribution/activity heatmap.
 *
 * Shows the last 12 months of posting activity as a grid of colored cells.
 * Each cell represents one day; color intensity reflects the number of posts.
 * Includes tooltip on hover (date + count + titles), click to navigate to
 * calendar day view, and streak counters (current + longest).
 *
 * Data source: GET /api/analytics/heatmap
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'

const router = useRouter()

const loading = ref(true)
const error = ref(null)
const heatmapData = ref({
  days: [],
  streak: { current: 0, longest: 0 },
  total_posts: 0,
  total_days_with_posts: 0,
  grid_start: '',
  grid_end: '',
})

// Tooltip state
const tooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  date: '',
  count: 0,
  titles: [],
  formattedDate: '',
})

// Month labels for the top axis
const monthLabels = computed(() => {
  if (!heatmapData.value.days.length) return []

  const labels = []
  let lastMonth = -1

  // Group days into weeks (columns)
  const weeks = groupedWeeks.value
  for (let weekIdx = 0; weekIdx < weeks.length; weekIdx++) {
    const firstDayOfWeek = weeks[weekIdx][0]
    if (!firstDayOfWeek) continue
    const date = new Date(firstDayOfWeek.date + 'T00:00:00')
    const month = date.getMonth()
    if (month !== lastMonth) {
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
      labels.push({ label: monthNames[month], weekIdx })
      lastMonth = month
    }
  }
  return labels
})

// Day labels for left axis (Mo, Mi, Fr)
const dayLabels = ['Mo', '', 'Mi', '', 'Fr', '', 'So']

// Group days into weeks (columns) for the grid
const groupedWeeks = computed(() => {
  const days = heatmapData.value.days
  if (!days.length) return []

  const weeks = []
  let currentWeek = []

  // First day should be Monday (weekday=0)
  // If not, pad the beginning
  const firstDay = days[0]
  if (firstDay && firstDay.weekday > 0) {
    for (let i = 0; i < firstDay.weekday; i++) {
      currentWeek.push(null)
    }
  }

  for (const day of days) {
    currentWeek.push(day)
    if (currentWeek.length === 7) {
      weeks.push(currentWeek)
      currentWeek = []
    }
  }

  // Pad the last week if incomplete
  if (currentWeek.length > 0) {
    while (currentWeek.length < 7) {
      currentWeek.push(null)
    }
    weeks.push(currentWeek)
  }

  return weeks
})

// Color intensity based on post count
function cellColor(count) {
  if (count === 0) return 'bg-gray-100 dark:bg-gray-700'
  if (count === 1) return 'bg-sky-200 dark:bg-sky-800'
  if (count === 2) return 'bg-sky-400 dark:bg-sky-600'
  if (count >= 3) return 'bg-sky-600 dark:bg-sky-400'
  return 'bg-gray-100 dark:bg-gray-700'
}

function cellBorder(count) {
  if (count === 0) return 'border-gray-200 dark:border-gray-600'
  return 'border-transparent'
}

// Format date for tooltip
function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr + 'T00:00:00')
  const days = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa']
  const months = ['Januar', 'Februar', 'Maerz', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
  return `${days[date.getDay()]}, ${date.getDate()}. ${months[date.getMonth()]} ${date.getFullYear()}`
}

// Show tooltip on hover
function showTooltip(event, day) {
  if (!day) return
  const rect = event.target.getBoundingClientRect()
  const containerRect = event.target.closest('[data-testid="activity-heatmap"]').getBoundingClientRect()
  tooltip.value = {
    visible: true,
    x: rect.left - containerRect.left + rect.width / 2,
    y: rect.top - containerRect.top - 8,
    date: day.date,
    count: day.count,
    titles: day.titles || [],
    formattedDate: formatDate(day.date),
  }
}

function hideTooltip() {
  tooltip.value.visible = false
}

// Click on a day -> navigate to calendar
function navigateToDay(day) {
  if (!day) return
  router.push({ path: '/calendar', query: { date: day.date } })
}

// Fetch data
async function fetchHeatmap() {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/api/analytics/heatmap')
    heatmapData.value = res.data
  } catch (err) {
    console.error('Failed to load heatmap data:', err)
    error.value = 'Heatmap-Daten konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchHeatmap()
})
</script>

<template>
  <div data-testid="activity-heatmap" class="relative">
    <!-- Streak counters -->
    <div class="flex items-center gap-6 mb-4" data-testid="streak-counters">
      <div class="flex items-center gap-2">
        <span class="text-lg">&#128293;</span>
        <div>
          <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ heatmapData.streak.current }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">Aktuelle Serie</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-lg">&#127942;</span>
        <div>
          <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ heatmapData.streak.longest }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">Laengste Serie</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-lg">&#128197;</span>
        <div>
          <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ heatmapData.total_days_with_posts }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">Tage mit Posts</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-lg">&#128200;</span>
        <div>
          <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ heatmapData.total_posts }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">Posts gesamt (12 Mon.)</p>
        </div>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="h-32 flex items-center justify-center">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500"></div>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="text-center py-8">
      <p class="text-red-500 dark:text-red-400 text-sm">{{ error }}</p>
      <button
        @click="fetchHeatmap"
        class="mt-2 px-3 py-1.5 text-xs bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition"
      >
        Erneut versuchen
      </button>
    </div>

    <!-- Heatmap grid -->
    <div v-else class="overflow-x-auto">
      <!-- Month labels -->
      <div class="flex ml-8 mb-1" style="gap: 0;">
        <div
          v-for="(label, idx) in monthLabels"
          :key="idx"
          class="text-xs text-gray-500 dark:text-gray-400 font-medium"
          :style="{
            position: 'absolute',
            left: (label.weekIdx * 14 + 32) + 'px',
          }"
        >
          {{ label.label }}
        </div>
      </div>

      <div class="relative" :style="{ height: (7 * 14 + 20) + 'px', marginTop: '18px' }">
        <!-- Day labels (left axis) -->
        <div class="absolute left-0 top-0" style="width: 28px;">
          <div
            v-for="(label, idx) in dayLabels"
            :key="idx"
            class="text-[10px] text-gray-400 dark:text-gray-500 text-right pr-1 leading-none"
            :style="{ height: '14px', lineHeight: '14px' }"
          >
            {{ label }}
          </div>
        </div>

        <!-- Grid of cells -->
        <div class="flex gap-[2px]" style="margin-left: 32px;">
          <div
            v-for="(week, weekIdx) in groupedWeeks"
            :key="weekIdx"
            class="flex flex-col gap-[2px]"
          >
            <div
              v-for="(day, dayIdx) in week"
              :key="dayIdx"
              :class="[
                'w-[12px] h-[12px] rounded-[2px] border transition-all duration-150',
                day ? cellColor(day.count) : 'bg-transparent border-transparent',
                day ? cellBorder(day.count) : '',
                day ? 'cursor-pointer hover:ring-2 hover:ring-sky-400 hover:ring-offset-1 dark:hover:ring-offset-gray-800' : '',
              ]"
              :data-date="day?.date"
              :data-count="day?.count"
              @mouseenter="day && showTooltip($event, day)"
              @mouseleave="hideTooltip"
              @click="navigateToDay(day)"
            ></div>
          </div>
        </div>
      </div>

      <!-- Legend -->
      <div class="flex items-center gap-2 mt-3 justify-end" data-testid="heatmap-legend">
        <span class="text-xs text-gray-500 dark:text-gray-400">Weniger</span>
        <div class="w-[12px] h-[12px] rounded-[2px] bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600"></div>
        <div class="w-[12px] h-[12px] rounded-[2px] bg-sky-200 dark:bg-sky-800"></div>
        <div class="w-[12px] h-[12px] rounded-[2px] bg-sky-400 dark:bg-sky-600"></div>
        <div class="w-[12px] h-[12px] rounded-[2px] bg-sky-600 dark:bg-sky-400"></div>
        <span class="text-xs text-gray-500 dark:text-gray-400">Mehr</span>
      </div>
    </div>

    <!-- Tooltip -->
    <div
      v-if="tooltip.visible"
      class="absolute z-50 pointer-events-none"
      :style="{
        left: tooltip.x + 'px',
        top: tooltip.y + 'px',
        transform: 'translate(-50%, -100%)',
      }"
    >
      <div class="bg-gray-900 dark:bg-gray-700 text-white text-xs rounded-lg px-3 py-2 shadow-lg whitespace-nowrap">
        <p class="font-medium">{{ tooltip.formattedDate }}</p>
        <p class="text-gray-300 dark:text-gray-400 mt-0.5">
          {{ tooltip.count === 0 ? 'Keine Posts' : tooltip.count === 1 ? '1 Post' : `${tooltip.count} Posts` }}
        </p>
        <p
          v-for="(title, i) in tooltip.titles"
          :key="i"
          class="text-gray-400 dark:text-gray-300 text-[10px] mt-0.5 truncate max-w-[200px]"
        >
          &bull; {{ title }}
        </p>
        <!-- Arrow -->
        <div class="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900 dark:border-t-gray-700"></div>
      </div>
    </div>
  </div>
</template>
