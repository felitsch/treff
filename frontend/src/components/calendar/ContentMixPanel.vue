<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Doughnut, Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import api from '@/utils/api'

// Register Chart.js components (including BarElement for bar chart)
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
)

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['toggle'])

const loading = ref(false)
const error = ref(null)
const period = ref('week') // 'week' or 'month'

// Data from API
const mixData = ref(null)

// Fetch content mix data
async function fetchContentMix() {
  loading.value = true
  error.value = null
  try {
    const res = await api.get(`/api/analytics/content-mix?period=${period.value}`)
    mixData.value = res.data
  } catch (err) {
    console.error('Failed to load content mix:', err)
    error.value = 'Fehler beim Laden'
  } finally {
    loading.value = false
  }
}

onMounted(fetchContentMix)
watch(period, fetchContentMix)

// Category hex colors for Chart.js
function categoryHexColor(cat) {
  const colors = {
    laender_spotlight: '#3B82F6',
    erfahrungsberichte: '#A855F7',
    infografiken: '#06B6D4',
    fristen_cta: '#DC2626',
    tipps_tricks: '#F59E0B',
    faq: '#14B8A6',
    foto_posts: '#EC4899',
    reel_tiktok_thumbnails: '#8B5CF6',
    story_posts: '#F97316',
    story_teaser: '#D946EF',
  }
  return colors[cat] || '#6B7280'
}

// Category labels
function categoryLabel(cat) {
  const labels = {
    laender_spotlight: 'Laender',
    erfahrungsberichte: 'Erfahrung',
    infografiken: 'Infografik',
    fristen_cta: 'Fristen',
    tipps_tricks: 'Tipps',
    faq: 'FAQ',
    foto_posts: 'Foto',
    reel_tiktok_thumbnails: 'Reel',
    story_posts: 'Story',
    story_teaser: 'Teaser',
  }
  return labels[cat] || cat
}

// Platform hex colors
function platformHexColor(plat) {
  const colors = {
    instagram_feed: '#E1306C',
    instagram_story: '#833AB4',
    tiktok: '#010101',
  }
  return colors[plat] || '#6B7280'
}

function platformLabel(plat) {
  const labels = {
    instagram_feed: 'IG Feed',
    instagram_story: 'IG Story',
    tiktok: 'TikTok',
  }
  return labels[plat] || plat
}

// Country hex colors
function countryHexColor(c) {
  const colors = {
    usa: '#3B82F6',
    canada: '#DC2626',
    australia: '#F59E0B',
    newzealand: '#10B981',
    ireland: '#22C55E',
  }
  return colors[c] || '#6B7280'
}

function countryLabel(c) {
  const labels = {
    usa: 'USA',
    canada: 'Kanada',
    australia: 'Australien',
    newzealand: 'Neuseeland',
    ireland: 'Irland',
  }
  return labels[c] || c
}

// --- Chart Data ---

// Category donut chart
const categoryChartData = computed(() => {
  if (!mixData.value || mixData.value.categories.length === 0) {
    return { labels: [], datasets: [] }
  }
  return {
    labels: mixData.value.categories.map(c => categoryLabel(c.category)),
    datasets: [{
      data: mixData.value.categories.map(c => c.count),
      backgroundColor: mixData.value.categories.map(c => categoryHexColor(c.category)),
      borderColor: '#ffffff',
      borderWidth: 2,
      hoverOffset: 6,
    }],
  }
})

// Platform donut chart
const platformChartData = computed(() => {
  if (!mixData.value || mixData.value.platforms.length === 0) {
    return { labels: [], datasets: [] }
  }
  return {
    labels: mixData.value.platforms.map(p => platformLabel(p.platform)),
    datasets: [{
      data: mixData.value.platforms.map(p => p.count),
      backgroundColor: mixData.value.platforms.map(p => platformHexColor(p.platform)),
      borderColor: '#ffffff',
      borderWidth: 2,
      hoverOffset: 6,
    }],
  }
})

// Country donut chart
const countryChartData = computed(() => {
  if (!mixData.value || mixData.value.countries.length === 0) {
    return { labels: [], datasets: [] }
  }
  return {
    labels: mixData.value.countries.map(c => countryLabel(c.country)),
    datasets: [{
      data: mixData.value.countries.map(c => c.count),
      backgroundColor: mixData.value.countries.map(c => countryHexColor(c.country)),
      borderColor: '#ffffff',
      borderWidth: 2,
      hoverOffset: 6,
    }],
  }
})

// Bar chart: posts per day of week
const daysBarData = computed(() => {
  if (!mixData.value || !mixData.value.days_of_week) {
    return { labels: [], datasets: [] }
  }
  return {
    labels: mixData.value.days_of_week.map(d => d.day),
    datasets: [{
      label: 'Posts',
      data: mixData.value.days_of_week.map(d => d.count),
      backgroundColor: mixData.value.days_of_week.map(d =>
        d.count > 0 ? '#3B82F6' : '#E5E7EB'
      ),
      borderRadius: 4,
      barThickness: 18,
    }],
  }
})

// Donut chart options (shared)
const donutOptions = computed(() => {
  const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
  return {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '60%',
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(26, 26, 46, 0.9)',
        titleFont: { size: 11, weight: 'bold' },
        bodyFont: { size: 11 },
        padding: 8,
        cornerRadius: 6,
        callbacks: {
          label: function (context) {
            const total = context.dataset.data.reduce((a, b) => a + b, 0)
            const value = context.parsed
            const pct = total > 0 ? Math.round((value / total) * 100) : 0
            return `${context.label}: ${value} (${pct}%)`
          },
        },
      },
    },
  }
})

// Bar chart options
const barOptions = computed(() => {
  const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(26, 26, 46, 0.9)',
        titleFont: { size: 11, weight: 'bold' },
        bodyFont: { size: 11 },
        padding: 8,
        cornerRadius: 6,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1,
          font: { size: 10 },
          color: isDark ? '#9CA3AF' : '#6B7280',
        },
        grid: {
          color: isDark ? 'rgba(75, 85, 99, 0.3)' : 'rgba(229, 231, 235, 0.8)',
        },
      },
      x: {
        ticks: {
          font: { size: 10 },
          color: isDark ? '#9CA3AF' : '#6B7280',
        },
        grid: { display: false },
      },
    },
  }
})

// Active chart tab: 'category', 'platform', 'country'
const activeDonut = ref('category')

// Computed current donut data
const currentDonutData = computed(() => {
  switch (activeDonut.value) {
    case 'platform': return platformChartData.value
    case 'country': return countryChartData.value
    default: return categoryChartData.value
  }
})

const hasDonutData = computed(() => {
  return currentDonutData.value.labels && currentDonutData.value.labels.length > 0
})

// Serie vs Einzel stats
const arcStats = computed(() => {
  if (!mixData.value) return null
  return {
    arc: mixData.value.story_arc_posts || 0,
    single: mixData.value.single_posts || 0,
    total: mixData.value.total || 0,
  }
})
</script>

<template>
  <div
    class="flex-shrink-0 transition-all duration-300"
    :class="[
      collapsed ? 'w-10' : 'w-full md:w-72',
      'max-w-full'
    ]"
  >
    <!-- Collapse toggle header -->
    <button
      @click="emit('toggle')"
      class="w-full flex items-center justify-between px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-t-xl text-sm font-semibold text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
      title="Content-Mix anzeigen/ausblenden"
      aria-label="Content-Mix Panel umschalten"
    >
      <span v-if="!collapsed" class="flex items-center gap-2">
        <span class="text-base">📊</span>
        Content-Mix
        <span
          v-if="mixData && mixData.total > 0"
          class="bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-bold px-1.5 py-0.5 rounded-full"
        >
          {{ mixData.total }}
        </span>
      </span>
      <svg
        class="w-4 h-4 transition-transform"
        :class="collapsed ? '' : 'rotate-180'"
        fill="none" stroke="currentColor" viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </button>

    <!-- Panel content -->
    <div
      v-if="!collapsed"
      class="bg-white dark:bg-gray-800 border border-t-0 border-gray-200 dark:border-gray-700 rounded-b-xl overflow-hidden"
    >
      <!-- Period toggle -->
      <div class="px-3 pt-3 pb-2">
        <div class="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-0.5">
          <button
            @click="period = 'week'"
            class="flex-1 px-3 py-1 text-xs font-medium rounded-md transition-colors"
            :class="period === 'week'
              ? 'bg-white dark:bg-gray-600 text-blue-600 dark:text-blue-400 shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'"
          >
            Woche
          </button>
          <button
            @click="period = 'month'"
            class="flex-1 px-3 py-1 text-xs font-medium rounded-md transition-colors"
            :class="period === 'month'
              ? 'bg-white dark:bg-gray-600 text-blue-600 dark:text-blue-400 shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'"
          >
            Monat
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="p-6 text-center">
        <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mx-auto"></div>
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">Laden...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="p-4 text-center">
        <p class="text-xs text-red-500">{{ error }}</p>
        <button @click="fetchContentMix" class="text-xs text-blue-600 hover:underline mt-1">Nochmal versuchen</button>
      </div>

      <!-- Content -->
      <div v-else-if="mixData" class="px-3 pb-3 space-y-4 max-h-[calc(100vh-300px)] overflow-y-auto">

        <!-- Summary stats -->
        <div class="grid grid-cols-3 gap-2">
          <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2 text-center">
            <div class="text-lg font-bold text-gray-900 dark:text-white">{{ mixData.total }}</div>
            <div class="text-[10px] text-gray-500 dark:text-gray-400">Posts</div>
          </div>
          <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2 text-center">
            <div class="text-lg font-bold text-gray-900 dark:text-white">{{ mixData.categories.length }}</div>
            <div class="text-[10px] text-gray-500 dark:text-gray-400">Kategorien</div>
          </div>
          <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2 text-center">
            <div class="text-lg font-bold text-gray-900 dark:text-white">{{ mixData.countries.length }}</div>
            <div class="text-[10px] text-gray-500 dark:text-gray-400">Laender</div>
          </div>
        </div>

        <!-- Serie vs Einzel split -->
        <div v-if="arcStats && arcStats.total > 0" class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2.5">
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-xs font-medium text-gray-700 dark:text-gray-300">Serie vs. Einzel</span>
          </div>
          <div class="flex h-3 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-600">
            <div
              v-if="arcStats.arc > 0"
              class="bg-violet-500 transition-all duration-300"
              :style="{ width: (arcStats.arc / arcStats.total * 100) + '%' }"
              :title="`Serien: ${arcStats.arc} (${Math.round(arcStats.arc / arcStats.total * 100)}%)`"
            ></div>
            <div
              v-if="arcStats.single > 0"
              class="bg-blue-400 transition-all duration-300"
              :style="{ width: (arcStats.single / arcStats.total * 100) + '%' }"
              :title="`Einzel: ${arcStats.single} (${Math.round(arcStats.single / arcStats.total * 100)}%)`"
            ></div>
          </div>
          <div class="flex items-center justify-between mt-1.5 text-[10px] text-gray-500 dark:text-gray-400">
            <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-violet-500 inline-block"></span> Serien: {{ arcStats.arc }}</span>
            <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-blue-400 inline-block"></span> Einzel: {{ arcStats.single }}</span>
          </div>
        </div>

        <!-- Donut chart section -->
        <div>
          <!-- Donut chart type tabs -->
          <div class="flex items-center gap-1 mb-2">
            <button
              @click="activeDonut = 'category'"
              class="px-2 py-0.5 text-[10px] font-medium rounded-full transition-colors"
              :class="activeDonut === 'category'
                ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300'
                : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'"
            >
              Kategorie
            </button>
            <button
              @click="activeDonut = 'platform'"
              class="px-2 py-0.5 text-[10px] font-medium rounded-full transition-colors"
              :class="activeDonut === 'platform'
                ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300'
                : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'"
            >
              Format
            </button>
            <button
              @click="activeDonut = 'country'"
              class="px-2 py-0.5 text-[10px] font-medium rounded-full transition-colors"
              :class="activeDonut === 'country'
                ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300'
                : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'"
            >
              Land
            </button>
          </div>

          <!-- Donut chart -->
          <div v-if="hasDonutData" class="relative" style="height: 160px">
            <Doughnut :data="currentDonutData" :options="donutOptions" />
          </div>
          <div v-else class="text-center py-6">
            <span class="text-2xl">📭</span>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Keine Daten</p>
          </div>

          <!-- Legend below donut -->
          <div v-if="hasDonutData" class="mt-2 space-y-1">
            <div
              v-for="(item, idx) in currentDonutData.labels"
              :key="'legend-' + idx"
              class="flex items-center justify-between text-[11px]"
            >
              <div class="flex items-center gap-1.5 min-w-0">
                <span
                  class="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  :style="{ backgroundColor: currentDonutData.datasets[0].backgroundColor[idx] }"
                ></span>
                <span class="truncate text-gray-700 dark:text-gray-300">{{ item }}</span>
              </div>
              <span class="text-gray-500 dark:text-gray-400 font-medium ml-2 flex-shrink-0">
                {{ currentDonutData.datasets[0].data[idx] }}
              </span>
            </div>
          </div>
        </div>

        <!-- Bar chart: Posts per day of week -->
        <div>
          <h4 class="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
            Posts pro Wochentag
          </h4>
          <div style="height: 120px">
            <Bar :data="daysBarData" :options="barOptions" />
          </div>
        </div>

        <!-- Warnings -->
        <div v-if="mixData.warnings && mixData.warnings.length > 0">
          <h4 class="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-1">
            <span>&#9888;&#65039;</span> Hinweise
          </h4>
          <div class="space-y-1.5">
            <div
              v-for="(w, idx) in mixData.warnings"
              :key="'warn-' + idx"
              class="flex items-start gap-2 rounded-lg px-2.5 py-2 text-[11px]"
              :class="w.severity === 'warning'
                ? 'bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-300'
                : 'bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300'"
            >
              <span class="flex-shrink-0 text-sm">{{ w.icon }}</span>
              <span>{{ w.message }}</span>
            </div>
          </div>
        </div>

        <!-- Recommendations -->
        <div v-if="mixData.recommendations && mixData.recommendations.length > 0">
          <h4 class="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-1">
            <span>&#128161;</span> Empfehlungen
          </h4>
          <div class="space-y-1.5">
            <div
              v-for="(r, idx) in mixData.recommendations"
              :key="'rec-' + idx"
              class="flex items-start gap-2 rounded-lg px-2.5 py-2 bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-300 text-[11px]"
            >
              <span class="flex-shrink-0 text-sm">{{ r.icon }}</span>
              <span>{{ r.message }}</span>
            </div>
          </div>
        </div>

        <!-- No data state -->
        <div v-if="mixData.total === 0 && (!mixData.warnings || mixData.warnings.length === 0)" class="text-center py-4">
          <span class="text-3xl">📋</span>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Noch keine Posts {{ period === 'week' ? 'diese Woche' : 'diesen Monat' }}
          </p>
        </div>

      </div>
    </div>
  </div>
</template>
