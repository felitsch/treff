<script setup>
/**
 * ReportGenerator.vue — Generate weekly/monthly performance reports as PDF or CSV.
 *
 * Features:
 * - Period selection (week/month)
 * - Format selection (PDF/CSV)
 * - Live preview of report data before generation
 * - Download button with progress indicator
 * - Report history with re-download capability
 * - TREFF branding in PDF output
 *
 * Endpoints used:
 *   GET  /api/reports/preview?period=week|month
 *   POST /api/reports/generate { period, format }
 *   GET  /api/reports/history
 */
import { ref, onMounted, watch } from 'vue'
import api from '@/utils/api'

const period = ref('month')
const format = ref('pdf')
const generating = ref(false)
const previewData = ref(null)
const previewLoading = ref(false)
const history = ref([])
const historyLoading = ref(false)

// Category/platform labels
const categoryLabels = {
  laender_spotlight: 'Länder-Spotlight',
  erfahrungsberichte: 'Erfahrungsberichte',
  infografiken: 'Infografiken',
  fristen_cta: 'Fristen/CTA',
  tipps_tricks: 'Tipps & Tricks',
  faq: 'FAQ',
  foto_posts: 'Foto-Posts',
  reel_tiktok_thumbnails: 'Reels/TikTok',
  story_posts: 'Stories',
  story_teaser: 'Story-Teaser',
}
const platformLabels = {
  instagram_feed: 'Instagram Feed',
  instagram_story: 'Instagram Story',
  tiktok: 'TikTok',
}
const countryLabels = {
  usa: 'USA',
  canada: 'Kanada',
  australia: 'Australien',
  newzealand: 'Neuseeland',
  ireland: 'Irland',
}

// Load preview data
async function loadPreview() {
  previewLoading.value = true
  try {
    const res = await api.get(`/api/reports/preview?period=${period.value}`)
    previewData.value = res.data
  } catch (err) {
    console.error('Failed to load report preview:', err)
    previewData.value = null
  } finally {
    previewLoading.value = false
  }
}

// Load report history
async function loadHistory() {
  historyLoading.value = true
  try {
    const res = await api.get('/api/reports/history')
    history.value = res.data || []
  } catch (err) {
    console.error('Failed to load report history:', err)
    history.value = []
  } finally {
    historyLoading.value = false
  }
}

// Generate and download report
async function generateReport() {
  generating.value = true
  try {
    const res = await api.post('/api/reports/generate', {
      period: period.value,
      format: format.value,
    }, {
      responseType: 'blob',
    })

    // Create download link
    const blob = new Blob([res.data], {
      type: format.value === 'pdf' ? 'application/pdf' : 'text/csv',
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const now = new Date()
    const dateStr = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`
    const periodLabel = period.value === 'week' ? 'Wochenbericht' : 'Monatsbericht'
    link.download = `TREFF_${periodLabel}_${dateStr}.${format.value}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    // Refresh history
    await loadHistory()
  } catch (err) {
    console.error('Failed to generate report:', err)
  } finally {
    generating.value = false
  }
}

// Format date for display
function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Watch period changes for live preview
watch(period, () => {
  loadPreview()
})

onMounted(() => {
  loadPreview()
  loadHistory()
})
</script>

<template>
  <div data-testid="report-generator" class="space-y-6">
    <!-- Options Row -->
    <div class="flex flex-wrap items-center gap-4" data-testid="report-options">
      <!-- Period Selection -->
      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Zeitraum</label>
        <div class="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          <button
            @click="period = 'week'"
            class="px-4 py-2 text-sm font-medium rounded-md transition-all"
            :class="period === 'week'
              ? 'bg-white dark:bg-gray-600 text-[#3B7AB1] shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
            data-testid="period-week"
          >
            Woche
          </button>
          <button
            @click="period = 'month'"
            class="px-4 py-2 text-sm font-medium rounded-md transition-all"
            :class="period === 'month'
              ? 'bg-white dark:bg-gray-600 text-[#3B7AB1] shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
            data-testid="period-month"
          >
            Monat
          </button>
        </div>
      </div>

      <!-- Format Selection -->
      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Format</label>
        <div class="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          <button
            @click="format = 'pdf'"
            class="px-4 py-2 text-sm font-medium rounded-md transition-all flex items-center gap-1.5"
            :class="format === 'pdf'
              ? 'bg-white dark:bg-gray-600 text-red-600 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
            data-testid="format-pdf"
          >
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M4 18h12V6h-4V2H4v16zm5-1H7v-5h2c1.1 0 2 .9 2 2s-.9 2-2 2H8v1zm0-4H8v2h1c.55 0 1-.45 1-1s-.45-1-1-1z"/></svg>
            PDF
          </button>
          <button
            @click="format = 'csv'"
            class="px-4 py-2 text-sm font-medium rounded-md transition-all flex items-center gap-1.5"
            :class="format === 'csv'
              ? 'bg-white dark:bg-gray-600 text-green-600 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
            data-testid="format-csv"
          >
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M4 18h12V6h-4V2H4v16zm6-7h4v1h-4v-1zm0 2h4v1h-4v-1zm0 2h4v1h-4v-1zm-4-4h3v1H6v-1zm0 2h3v1H6v-1zm0 2h3v1H6v-1z"/></svg>
            CSV
          </button>
        </div>
      </div>

      <!-- Generate Button -->
      <div class="ml-auto">
        <label class="block text-xs font-medium text-transparent mb-1">&nbsp;</label>
        <button
          @click="generateReport"
          :disabled="generating"
          class="px-6 py-2 bg-[#3B7AB1] text-white text-sm font-medium rounded-lg hover:bg-[#2d6a9e] transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          data-testid="generate-btn"
        >
          <template v-if="generating">
            <div class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
            Generiere...
          </template>
          <template v-else>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Report generieren
          </template>
        </button>
      </div>
    </div>

    <!-- Preview Section -->
    <div v-if="previewLoading" class="flex items-center justify-center py-8">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#3B7AB1]"></div>
    </div>

    <div v-else-if="previewData" data-testid="report-preview" class="space-y-4">
      <!-- Preview Header -->
      <div class="flex items-center gap-3">
        <span class="text-xl">&#128203;</span>
        <div>
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ previewData.period_label }}</h3>
          <p class="text-xs text-gray-500 dark:text-gray-400">{{ previewData.date_range }}</p>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="preview-stats">
        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-center">
          <p class="text-xl font-bold text-[#3B7AB1]">{{ previewData.total_posts }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">Posts erstellt</p>
        </div>
        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-center">
          <p class="text-xl font-bold text-[#3B7AB1]">{{ previewData.posts_with_metrics }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">Mit Metriken</p>
        </div>
        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-center">
          <p class="text-xl font-bold text-[#3B7AB1]">{{ previewData.metrics.avg_engagement_rate }}%</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">Engagement Rate</p>
        </div>
        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-center">
          <p class="text-xl font-bold text-[#3B7AB1]">{{ previewData.metrics.total_reach.toLocaleString('de-DE') }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">Reichweite</p>
        </div>
      </div>

      <!-- Distribution preview (compact) -->
      <div v-if="Object.keys(previewData.categories).length > 0" class="flex flex-wrap gap-2">
        <span
          v-for="(count, cat) in previewData.categories"
          :key="cat"
          class="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded text-xs"
        >
          {{ categoryLabels[cat] || cat }}: {{ count }}
        </span>
        <span
          v-for="(count, plat) in previewData.platforms"
          :key="plat"
          class="inline-flex items-center gap-1 px-2 py-1 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300 rounded text-xs"
        >
          {{ platformLabels[plat] || plat }}: {{ count }}
        </span>
      </div>

      <!-- Top Posts Preview -->
      <div v-if="previewData.top_posts && previewData.top_posts.length > 0">
        <h4 class="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">Top-Posts</h4>
        <div class="space-y-1">
          <div
            v-for="(post, idx) in previewData.top_posts.slice(0, 5)"
            :key="post.id"
            class="flex items-center gap-2 text-xs"
          >
            <span class="font-bold text-gray-400 w-4">{{ idx + 1 }}.</span>
            <span class="truncate flex-1 text-gray-700 dark:text-gray-300">{{ post.title }}</span>
            <span class="text-green-600 dark:text-green-400 font-medium">{{ post.engagement_rate }}%</span>
            <span class="text-gray-400">{{ post.reach }} Reach</span>
          </div>
        </div>
      </div>

      <!-- Recommendations Preview -->
      <div v-if="previewData.recommendations && previewData.recommendations.length > 0" class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
        <h4 class="text-xs font-semibold text-amber-800 dark:text-amber-300 mb-1">Empfehlungen</h4>
        <ul class="space-y-0.5">
          <li
            v-for="(rec, i) in previewData.recommendations"
            :key="i"
            class="text-xs text-amber-700 dark:text-amber-400"
          >
            &bull; {{ rec }}
          </li>
        </ul>
      </div>
    </div>

    <!-- Report History -->
    <div v-if="history.length > 0" data-testid="report-history">
      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-1.5">
        <span>&#128197;</span>
        Fruehere Reports
      </h3>
      <div class="space-y-1.5">
        <div
          v-for="report in history"
          :key="report.id"
          class="flex items-center gap-3 px-3 py-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-sm"
        >
          <span :class="report.report_type === 'pdf' ? 'text-red-500' : 'text-green-500'" class="font-mono text-xs font-bold uppercase">
            {{ report.report_type }}
          </span>
          <span class="flex-1 text-gray-700 dark:text-gray-300 text-xs truncate">
            {{ report.title }}
          </span>
          <span class="text-xs text-gray-400">
            {{ report.post_count }} Posts
          </span>
          <span class="text-xs text-gray-400">
            {{ formatDate(report.created_at) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
