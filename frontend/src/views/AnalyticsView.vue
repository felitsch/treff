<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { Line, Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import api from '@/utils/api'
import WorkflowHint from '@/components/common/WorkflowHint.vue'
import TourSystem from '@/components/common/TourSystem.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import TopPostsRanking from '@/components/analytics/TopPostsRanking.vue'
import ActivityHeatmap from '@/components/analytics/ActivityHeatmap.vue'
import ReportGenerator from '@/components/analytics/ReportGenerator.vue'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
)

const loading = ref(true)
const error = ref(null)
const tourRef = ref(null)

// Overview stats
const overview = ref({
  total_posts: 0,
  posts_this_week: 0,
  posts_this_month: 0,
})

// Category distribution
const categories = ref([])

// Platform distribution
const platforms = ref([])

// Country distribution
const countries = ref([])

// Goals
const goals = ref({
  weekly_target: 4,
  weekly_actual: 0,
  monthly_target: 16,
  monthly_actual: 0,
})

// Frequency chart data
const frequencyPeriod = ref('week')
const frequencyData = ref([])
const frequencyLoading = ref(false)

// Computed values
const weeklyProgress = computed(() => {
  if (goals.value.weekly_target === 0) return 0
  return Math.min(100, Math.round((goals.value.weekly_actual / goals.value.weekly_target) * 100))
})

const monthlyProgress = computed(() => {
  if (goals.value.monthly_target === 0) return 0
  return Math.min(100, Math.round((goals.value.monthly_actual / goals.value.monthly_target) * 100))
})

// Category display names
function categoryLabel(cat) {
  const labels = {
    laender_spotlight: 'Laender-Spotlight',
    erfahrungsberichte: 'Erfahrungsbericht',
    infografiken: 'Infografik',
    fristen_cta: 'Fristen/CTA',
    tipps_tricks: 'Tipps & Tricks',
    faq: 'FAQ',
    foto_posts: 'Foto-Post',
    reel_tiktok_thumbnails: 'Reel/TikTok',
    story_posts: 'Story',
    story_teaser: 'Story-Teaser',
  }
  return labels[cat] || cat
}

// Platform display names
function platformLabel(platform) {
  const labels = {
    instagram_feed: 'Instagram Feed',
    instagram_story: 'Instagram Story',
    tiktok: 'TikTok',
  }
  return labels[platform] || platform
}

// Platform icons
function platformIcon(platform) {
  switch (platform) {
    case 'instagram_feed': return '📸'
    case 'instagram_story': return '📱'
    case 'tiktok': return '🎵'
    default: return '📝'
  }
}

// Category hex colors for Chart.js doughnut chart
function categoryHexColor(cat) {
  const colors = {
    laender_spotlight: '#3B82F6',
    erfahrungsberichte: '#22C55E',
    infografiken: '#A855F7',
    fristen_cta: '#DC2626',
    tipps_tricks: '#EAB308',
    faq: '#6366F1',
    foto_posts: '#EC4899',
    reel_tiktok_thumbnails: '#F97316',
    story_posts: '#14B8A6',
    story_teaser: '#D946EF',
  }
  return colors[cat] || '#6B7280'
}

// Category colors for distribution bars (kept for backwards compat)
function categoryColor(cat) {
  const colors = {
    laender_spotlight: 'bg-blue-500',
    erfahrungsberichte: 'bg-green-500',
    infografiken: 'bg-purple-500',
    fristen_cta: 'bg-red-500',
    tipps_tricks: 'bg-yellow-500',
    faq: 'bg-indigo-500',
    foto_posts: 'bg-pink-500',
    reel_tiktok_thumbnails: 'bg-orange-500',
    story_posts: 'bg-teal-500',
    story_teaser: 'bg-fuchsia-500',
  }
  return colors[cat] || 'bg-gray-500'
}

// Total posts across categories (for percentage computation)
const totalCategoryPosts = computed(() => {
  return categories.value.reduce((sum, c) => sum + c.count, 0)
})

// Total posts across platforms (for percentage computation)
const totalPlatformPosts = computed(() => {
  return platforms.value.reduce((sum, p) => sum + p.count, 0)
})

// Doughnut chart data for category distribution
const categoryChartData = computed(() => {
  if (categories.value.length === 0) {
    return { labels: [], datasets: [] }
  }
  return {
    labels: categories.value.map(c => categoryLabel(c.category)),
    datasets: [
      {
        data: categories.value.map(c => c.count),
        backgroundColor: categories.value.map(c => categoryHexColor(c.category)),
        borderColor: '#ffffff',
        borderWidth: 2,
        hoverBorderColor: '#ffffff',
        hoverBorderWidth: 3,
        hoverOffset: 8,
      },
    ],
  }
})

// Doughnut chart options
const categoryChartOptions = computed(() => {
  const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
  return {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '55%',
    plugins: {
      legend: {
        display: true,
        position: 'bottom',
        labels: {
          padding: 16,
          usePointStyle: true,
          pointStyle: 'circle',
          font: {
            size: 12,
          },
          color: isDark ? '#D1D5DB' : '#374151',
        },
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(26, 26, 46, 0.9)',
        titleFont: { size: 13, weight: 'bold' },
        bodyFont: { size: 12 },
        padding: 12,
        cornerRadius: 8,
        callbacks: {
          label: function (context) {
            const total = context.dataset.data.reduce((a, b) => a + b, 0)
            const value = context.parsed
            const percentage = total > 0 ? Math.round((value / total) * 100) : 0
            return `${context.label}: ${value} (${percentage}%)`
          },
        },
      },
    },
  }
})

// Frequency chart configuration
const frequencyChartData = computed(() => {
  return {
    labels: frequencyData.value.map(d => d.label),
    datasets: [
      {
        label: 'Posts',
        data: frequencyData.value.map(d => d.count),
        borderColor: '#3B7AB1',
        backgroundColor: 'rgba(76, 139, 194, 0.15)',
        pointBackgroundColor: '#3B7AB1',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointHoverBackgroundColor: '#3B7AB1',
        pointHoverBorderColor: '#ffffff',
        pointHoverBorderWidth: 3,
        borderWidth: 3,
        fill: true,
        tension: 0.3,
      },
    ],
  }
})

const frequencyChartOptions = computed(() => {
  const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
  const tickColor = isDark ? '#D1D5DB' : '#9CA3AF'
  const gridColor = isDark ? 'rgba(156, 163, 175, 0.2)' : 'rgba(156, 163, 175, 0.15)'
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: false,
      },
      tooltip: {
        enabled: true,
        backgroundColor: isDark ? 'rgba(31, 41, 55, 0.95)' : 'rgba(26, 26, 46, 0.9)',
        titleFont: { size: 13, weight: 'bold' },
        titleColor: isDark ? '#F3F4F6' : '#FFFFFF',
        bodyFont: { size: 12 },
        bodyColor: isDark ? '#D1D5DB' : '#FFFFFF',
        padding: 12,
        cornerRadius: 8,
        displayColors: false,
        callbacks: {
          title: function (context) {
            const idx = context[0].dataIndex
            const item = frequencyData.value[idx]
            return item ? item.date : context[0].label
          },
          label: function (context) {
            const count = context.parsed.y
            return count === 1 ? '1 Post' : `${count} Posts`
          },
        },
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Datum',
          color: tickColor,
          font: { size: 12, weight: 'bold' },
        },
        grid: {
          display: false,
        },
        ticks: {
          color: tickColor,
          font: { size: 11 },
          maxRotation: 45,
          autoSkip: true,
          maxTicksLimit: 15,
        },
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Anzahl',
          color: tickColor,
          font: { size: 12, weight: 'bold' },
        },
        beginAtZero: true,
        ticks: {
          color: tickColor,
          font: { size: 11 },
          stepSize: 1,
          precision: 0,
        },
        grid: {
          color: gridColor,
        },
      },
    },
  }
})

const periodLabels = {
  week: 'Letzte 7 Tage',
  month: 'Letzte 30 Tage',
  quarter: 'Letztes Quartal',
  year: 'Letztes Jahr',
}

async function fetchFrequency() {
  frequencyLoading.value = true
  try {
    const res = await api.get(`/api/analytics/frequency?period=${frequencyPeriod.value}`)
    frequencyData.value = res.data.data || []
  } catch (err) {
    // Error toast shown by API interceptor
    frequencyData.value = []
  } finally {
    frequencyLoading.value = false
  }
}

// Watch for period change
watch(frequencyPeriod, () => {
  fetchFrequency()
})

async function fetchAnalytics() {
  loading.value = true
  error.value = null
  try {
    const [overviewRes, categoriesRes, platformsRes, countriesRes, goalsRes, frequencyRes] = await Promise.all([
      api.get('/api/analytics/overview'),
      api.get('/api/analytics/categories'),
      api.get('/api/analytics/platforms'),
      api.get('/api/analytics/countries'),
      api.get('/api/analytics/goals'),
      api.get(`/api/analytics/frequency?period=${frequencyPeriod.value}`),
    ])

    overview.value = overviewRes.data
    categories.value = categoriesRes.data
    platforms.value = platformsRes.data
    countries.value = countriesRes.data
    goals.value = goalsRes.data
    frequencyData.value = frequencyRes.data.data || []
  } catch (err) {
    // Error toast shown by API interceptor
    error.value = 'Fehler beim Laden der Analytics-Daten.'
  } finally {
    loading.value = false
  }
}

// Performance trend data
const performanceTrendPeriod = ref('month')
const performanceTrendData = ref([])
const performanceTrendLoading = ref(false)

// Performance reminder data
const performanceReminder = ref({ posts: [], count: 0 })

const performanceTrendChartData = computed(() => {
  return {
    labels: performanceTrendData.value.map(d => d.label),
    datasets: [
      {
        label: 'Engagement Rate (%)',
        data: performanceTrendData.value.map(d => d.engagement_rate),
        borderColor: '#22C55E',
        backgroundColor: 'rgba(34, 197, 94, 0.15)',
        pointBackgroundColor: '#22C55E',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 2,
        fill: true,
        tension: 0.3,
        yAxisID: 'y',
      },
      {
        label: 'Likes',
        data: performanceTrendData.value.map(d => d.likes),
        borderColor: '#EF4444',
        backgroundColor: 'transparent',
        pointBackgroundColor: '#EF4444',
        pointRadius: 3,
        borderWidth: 1.5,
        borderDash: [5, 5],
        tension: 0.3,
        yAxisID: 'y1',
      },
      {
        label: 'Reichweite',
        data: performanceTrendData.value.map(d => d.reach),
        borderColor: '#3B82F6',
        backgroundColor: 'transparent',
        pointBackgroundColor: '#3B82F6',
        pointRadius: 3,
        borderWidth: 1.5,
        borderDash: [5, 5],
        tension: 0.3,
        yAxisID: 'y1',
      },
    ],
  }
})

const performanceTrendChartOptions = computed(() => {
  const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
  const tickColor = isDark ? '#D1D5DB' : '#9CA3AF'
  const gridColor = isDark ? 'rgba(156,163,175,0.15)' : 'rgba(156,163,175,0.1)'
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: {
        display: true,
        position: 'bottom',
        labels: { usePointStyle: true, pointStyle: 'circle', padding: 12, font: { size: 11 }, color: tickColor },
      },
      tooltip: {
        enabled: true,
        backgroundColor: isDark ? 'rgba(31, 41, 55, 0.95)' : 'rgba(26, 26, 46, 0.9)',
        titleColor: isDark ? '#F3F4F6' : '#FFFFFF',
        bodyColor: isDark ? '#D1D5DB' : '#FFFFFF',
        padding: 10,
        cornerRadius: 8,
      },
    },
    scales: {
      x: { display: true, grid: { display: false }, ticks: { color: tickColor, font: { size: 10 }, maxRotation: 45, autoSkip: true, maxTicksLimit: 15 } },
      y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'Eng. Rate (%)', color: '#22C55E', font: { size: 10 } }, beginAtZero: true, ticks: { color: '#22C55E', font: { size: 10 } }, grid: { color: gridColor } },
      y1: { type: 'linear', display: true, position: 'right', title: { display: true, text: 'Anzahl', color: tickColor, font: { size: 10 } }, beginAtZero: true, ticks: { color: tickColor, font: { size: 10 } }, grid: { drawOnChartArea: false } },
    },
  }
})

async function fetchPerformanceTrend() {
  performanceTrendLoading.value = true
  try {
    const res = await api.get(`/api/analytics/performance-trend?period=${performanceTrendPeriod.value}`)
    performanceTrendData.value = res.data.data || []
  } catch (err) {
    // Error toast shown by API interceptor
    performanceTrendData.value = []
  } finally {
    performanceTrendLoading.value = false
  }
}

async function fetchPerformanceReminder() {
  try {
    const res = await api.get('/api/analytics/performance-reminder')
    performanceReminder.value = res.data
  } catch { /* ignore */ }
}

watch(performanceTrendPeriod, () => {
  fetchPerformanceTrend()
})

// Workflow hint: check if posting goals are configured in settings
const goalsNotConfigured = ref(false)
async function checkGoalsConfig() {
  try {
    const res = await api.get('/api/settings')
    const s = res.data
    if (!s.posts_per_week && !s.posts_per_month) {
      goalsNotConfigured.value = true
    }
  } catch { /* ignore */ }
}

onMounted(() => {
  fetchAnalytics()
  checkGoalsConfig()
  fetchPerformanceTrend()
  fetchPerformanceReminder()
})
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <div class="flex items-center gap-3 mb-6">
      <h1 data-tour="analytics-header" class="text-2xl font-bold text-gray-900 dark:text-white">Analytics</h1>
      <button
        @click="tourRef?.startTour()"
        class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        title="Seiten-Tour starten"
      >
        &#10067; Tour
      </button>
    </div>

    <!-- Workflow Hint: Posting goals not configured -->
    <WorkflowHint
      hint-id="analytics-posting-goals"
      message="Noch keine Posting-Ziele festgelegt? Konfiguriere woechentliche und monatliche Ziele in den Einstellungen."
      link-text="Einstellungen"
      link-to="/settings"
      icon="🎯"
      :show="goalsNotConfigured"
    />

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
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center" role="alert">
      <p class="text-red-600 dark:text-red-400 mb-3">{{ error }}</p>
      <button
        @click="fetchAnalytics"
        class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
      >
        Erneut versuchen
      </button>
    </div>

    <!-- Analytics content -->
    <div v-else data-tour="analytics-charts" class="space-y-6">
      <!-- Overview stats cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4" data-testid="overview-stats">
        <!-- Total posts -->
        <BaseCard padding="lg" :header-divider="false">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Posts gesamt</p>
              <p class="text-3xl font-bold text-gray-900 dark:text-white mt-1" data-testid="total-posts">
                {{ overview.total_posts }}
              </p>
            </div>
            <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
              <span class="text-2xl">📊</span>
            </div>
          </div>
        </BaseCard>

        <!-- Posts this week -->
        <BaseCard padding="lg" :header-divider="false">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Posts diese Woche</p>
              <p class="text-3xl font-bold text-[#3B7AB1] mt-1" data-testid="posts-this-week">
                {{ overview.posts_this_week }}
              </p>
            </div>
            <div class="w-12 h-12 bg-[#3B7AB1]/10 rounded-xl flex items-center justify-center">
              <span class="text-2xl">📅</span>
            </div>
          </div>
        </BaseCard>

        <!-- Posts this month -->
        <BaseCard padding="lg" :header-divider="false">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Posts diesen Monat</p>
              <p class="text-3xl font-bold text-[#FDD000] mt-1" data-testid="posts-this-month">
                {{ overview.posts_this_month }}
              </p>
            </div>
            <div class="w-12 h-12 bg-[#FDD000]/10 rounded-xl flex items-center justify-center">
              <span class="text-2xl">📆</span>
            </div>
          </div>
        </BaseCard>
      </div>

      <!-- Goal tracking -->
      <BaseCard padding="lg" title="Zielverfolgung" :header-divider="false" data-testid="goal-tracking" data-tour="analytics-goals">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Weekly goal -->
          <div>
            <div class="flex justify-between items-center mb-2">
              <span class="text-sm font-medium text-gray-600 dark:text-gray-400">Wochenziel</span>
              <span class="text-sm font-bold text-gray-900 dark:text-white">
                {{ goals.weekly_actual }} / {{ goals.weekly_target }} Posts
              </span>
            </div>
            <div class="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="weeklyProgress >= 100 ? 'bg-green-500' : 'bg-[#3B7AB1]'"
                :style="{ width: weeklyProgress + '%' }"
              ></div>
            </div>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ weeklyProgress }}% erreicht</p>
          </div>

          <!-- Monthly goal -->
          <div>
            <div class="flex justify-between items-center mb-2">
              <span class="text-sm font-medium text-gray-600 dark:text-gray-400">Monatsziel</span>
              <span class="text-sm font-bold text-gray-900 dark:text-white">
                {{ goals.monthly_actual }} / {{ goals.monthly_target }} Posts
              </span>
            </div>
            <div class="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="monthlyProgress >= 100 ? 'bg-green-500' : 'bg-[#FDD000]'"
                :style="{ width: monthlyProgress + '%' }"
              ></div>
            </div>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ monthlyProgress }}% erreicht</p>
          </div>
        </div>
      </BaseCard>

      <!-- Posting frequency line chart -->
      <BaseCard padding="lg" :header-divider="false" data-testid="frequency-chart" data-tour="analytics-frequency">
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Posting-Frequenz</h2>
        </template>
        <template #headerAction>
          <div class="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
            <button
              v-for="(label, key) in periodLabels"
              :key="key"
              @click="frequencyPeriod = key"
              class="px-3 py-1.5 text-xs font-medium rounded-md transition-all"
              :class="frequencyPeriod === key
                ? 'bg-white dark:bg-gray-600 text-[#3B7AB1] shadow-sm'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
              :data-testid="'period-' + key"
            >
              {{ label }}
            </button>
          </div>
        </template>

        <!-- Chart loading -->
        <div v-if="frequencyLoading" class="h-72 flex items-center justify-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#3B7AB1]"></div>
        </div>

        <!-- Chart content -->
        <div v-else class="h-72" data-testid="frequency-line-chart">
          <Line
            :data="frequencyChartData"
            :options="frequencyChartOptions"
          />
        </div>
      </BaseCard>

      <!-- Activity Heatmap (GitHub-style contribution graph) -->
      <BaseCard padding="lg" :header-divider="false" data-testid="activity-heatmap-section" data-tour="analytics-heatmap">
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Aktivitaets-Heatmap</h2>
        </template>
        <template #headerAction>
          <span class="text-xs text-gray-500 dark:text-gray-400">Letzte 12 Monate</span>
        </template>
        <ActivityHeatmap />
      </BaseCard>

      <!-- Distribution charts row -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Category distribution - Doughnut Chart -->
        <BaseCard padding="lg" title="Kategorieverteilung" :header-divider="false" data-testid="category-distribution" data-tour="analytics-categories">
          <EmptyState
            v-if="categories.length === 0"
            svgIcon="chart-bar"
            title="Noch keine Daten"
            description="Erstelle Posts, um die Kategorieverteilung hier zu sehen."
            actionLabel="Post erstellen"
            actionTo="/create/quick"
            :compact="true"
          />
          <div v-else>
            <div class="relative" style="height: 320px;" data-testid="category-pie-chart">
              <Doughnut
                :data="categoryChartData"
                :options="categoryChartOptions"
              />
            </div>
            <p class="text-center text-sm text-gray-500 dark:text-gray-400 mt-2">
              {{ totalCategoryPosts }} Posts insgesamt
            </p>
          </div>
        </BaseCard>

        <!-- Platform distribution -->
        <BaseCard padding="lg" title="Plattformverteilung" :header-divider="false" data-testid="platform-distribution" data-tour="analytics-platforms">
          <EmptyState
            v-if="platforms.length === 0"
            svgIcon="device-phone-mobile"
            title="Noch keine Daten"
            description="Erstelle Posts fuer Instagram oder TikTok, um die Plattformverteilung zu sehen."
            actionLabel="Post erstellen"
            actionTo="/create/quick"
            :compact="true"
          />
          <div v-else class="space-y-4">
            <div v-for="p in platforms" :key="p.platform" class="flex items-center gap-3">
              <span class="text-xl">{{ platformIcon(p.platform) }}</span>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300 w-32">
                {{ platformLabel(p.platform) }}
              </span>
              <div class="flex-1 h-6 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  class="h-full bg-[#3B7AB1] rounded-full flex items-center justify-end pr-2 transition-all duration-500"
                  :style="{ width: Math.max(10, (p.count / totalPlatformPosts) * 100) + '%' }"
                >
                  <span class="text-xs font-bold text-white">{{ p.count }}</span>
                </div>
              </div>
            </div>
          </div>
        </BaseCard>
      </div>

      <!-- Country distribution -->
      <BaseCard padding="lg" title="Laenderverteilung" :header-divider="false" data-testid="country-distribution">
        <EmptyState
          v-if="countries.length === 0"
          svgIcon="globe-alt"
          title="Noch keine Laenderdaten"
          description="Weise Posts Laender zu (USA, Kanada, Australien, Neuseeland, Irland), um die Verteilung hier zu sehen."
          actionLabel="Post erstellen"
          actionTo="/create/quick"
          :compact="true"
        />
        <div v-else class="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div
            v-for="c in countries"
            :key="c.country"
            class="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 text-center"
          >
            <p class="text-2xl mb-1">
              {{ c.country === 'usa' ? '🇺🇸' : c.country === 'canada' ? '🇨🇦' : c.country === 'australia' ? '🇦🇺' : c.country === 'newzealand' ? '🇳🇿' : c.country === 'ireland' ? '🇮🇪' : '🌍' }}
            </p>
            <p class="text-lg font-bold text-gray-900 dark:text-white">{{ c.count }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400 capitalize">{{ c.country }}</p>
          </div>
        </div>
      </BaseCard>

      <!-- Performance Reminder Banner -->
      <div v-if="performanceReminder.count > 0" class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4 flex items-center gap-3" data-testid="performance-reminder">
        <span class="text-2xl">📝</span>
        <div class="flex-1">
          <p class="text-sm font-medium text-amber-800 dark:text-amber-300">
            {{ performanceReminder.count }} Post{{ performanceReminder.count > 1 ? 's' : '' }} warten auf Metriken-Eingabe
          </p>
          <p class="text-xs text-amber-600 dark:text-amber-400">
            Trage Likes, Kommentare und Reichweite fuer Posts der letzten Woche ein.
          </p>
        </div>
        <div class="flex gap-2">
          <router-link
            v-for="rp in performanceReminder.posts.slice(0, 3)"
            :key="rp.id"
            :to="`/create/post/${rp.id}/edit`"
            class="px-3 py-1.5 text-xs font-medium bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition"
          >
            #{{ rp.id }}
          </router-link>
        </div>
      </div>

      <!-- Performance Trend Chart -->
      <BaseCard padding="lg" :header-divider="false" data-testid="performance-trend-chart">
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">📈 Performance-Trend</h2>
        </template>
        <template #headerAction>
          <div class="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
            <button
              v-for="(label, key) in { week: '7 Tage', month: '30 Tage', quarter: 'Quartal', year: 'Jahr' }"
              :key="key"
              @click="performanceTrendPeriod = key"
              class="px-3 py-1.5 text-xs font-medium rounded-md transition-all"
              :class="performanceTrendPeriod === key
                ? 'bg-white dark:bg-gray-600 text-green-600 shadow-sm'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
              :data-testid="'perf-trend-period-' + key"
            >
              {{ label }}
            </button>
          </div>
        </template>

        <div v-if="performanceTrendLoading" class="h-64 flex items-center justify-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
        </div>
        <div v-else class="h-64" data-testid="performance-trend-line-chart">
          <Line
            :data="performanceTrendChartData"
            :options="performanceTrendChartOptions"
          />
        </div>
      </BaseCard>

      <!-- Top Posts Ranking -->
      <BaseCard padding="lg" :header-divider="false" data-testid="top-posts-section">
        <TopPostsRanking />
      </BaseCard>

      <!-- Report Generator -->
      <BaseCard padding="lg" :header-divider="false" data-testid="report-generator-section" data-tour="analytics-reports">
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Report-Generierung</h2>
        </template>
        <template #headerAction>
          <span class="text-xs text-gray-500 dark:text-gray-400">PDF / CSV</span>
        </template>
        <ReportGenerator />
      </BaseCard>
    </div>

    <!-- Page-specific guided tour -->
    <TourSystem ref="tourRef" page-key="analytics" />
  </div>
</template>
