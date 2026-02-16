<script setup>
/**
 * TopPostsRanking.vue
 *
 * Sortable ranking of top-performing posts based on engagement rate
 * or specific metrics (likes, comments, shares, saves, reach).
 * Displays in a compact card grid with ranking badges.
 */
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import EmptyState from '@/components/common/EmptyState.vue'

const router = useRouter()

const loading = ref(true)
const posts = ref([])
const totalWithMetrics = ref(0)
const sortBy = ref('engagement_rate')
const period = ref(null) // null = all time

const sortOptions = [
  { value: 'engagement_rate', label: 'Engagement Rate', icon: '📈' },
  { value: 'likes', label: 'Likes', icon: '❤️' },
  { value: 'comments', label: 'Kommentare', icon: '💬' },
  { value: 'shares', label: 'Shares', icon: '🔄' },
  { value: 'saves', label: 'Saves', icon: '🔖' },
  { value: 'reach', label: 'Reichweite', icon: '👁️' },
]

const periodOptions = [
  { value: null, label: 'Gesamt' },
  { value: 'week', label: '7 Tage' },
  { value: 'month', label: '30 Tage' },
  { value: 'quarter', label: 'Quartal' },
  { value: 'year', label: 'Jahr' },
]

// Category labels
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

function platformIcon(platform) {
  switch (platform) {
    case 'instagram_feed': return '📸'
    case 'instagram_story': return '📱'
    case 'tiktok': return '🎵'
    default: return '📝'
  }
}

function rankBadge(index) {
  if (index === 0) return { text: '🥇', bg: 'bg-yellow-100 dark:bg-yellow-900/30' }
  if (index === 1) return { text: '🥈', bg: 'bg-gray-100 dark:bg-gray-700' }
  if (index === 2) return { text: '🥉', bg: 'bg-orange-100 dark:bg-orange-900/30' }
  return { text: `#${index + 1}`, bg: 'bg-gray-50 dark:bg-gray-700/50' }
}

function engagementColor(rate) {
  if (rate >= 5) return 'text-green-600 dark:text-green-400'
  if (rate >= 3) return 'text-blue-600 dark:text-blue-400'
  if (rate >= 1) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-500 dark:text-red-400'
}

async function fetchTopPosts() {
  loading.value = true
  try {
    let url = `/api/analytics/top-posts?sort_by=${sortBy.value}&limit=10`
    if (period.value) {
      url += `&period=${period.value}`
    }
    const res = await api.get(url)
    posts.value = res.data.posts || []
    totalWithMetrics.value = res.data.total_with_metrics || 0
  } catch (err) {
    console.error('Failed to load top posts:', err)
    posts.value = []
  } finally {
    loading.value = false
  }
}

function navigateToPost(postId) {
  router.push(`/create/post/${postId}/edit`)
}

async function exportCSV() {
  try {
    let url = '/api/analytics/performance-export'
    if (period.value) {
      url += `?period=${period.value}`
    }
    const res = await api.get(url, { responseType: 'blob' })
    const blob = new Blob([res.data], { type: 'text/csv' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `treff_performance_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
    URL.revokeObjectURL(link.href)
  } catch (err) {
    console.error('Failed to export CSV:', err)
  }
}

watch([sortBy, period], () => {
  fetchTopPosts()
})

onMounted(() => {
  fetchTopPosts()
})
</script>

<template>
  <div data-testid="top-posts-ranking">
    <!-- Header with filters -->
    <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
      <div class="flex items-center gap-2">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white">
          🏆 Top-Performing Posts
        </h3>
        <span v-if="totalWithMetrics > 0" class="text-xs px-2 py-0.5 bg-[#3B7AB1]/10 text-[#3B7AB1] rounded-full font-medium">
          {{ totalWithMetrics }} Posts
        </span>
      </div>

      <div class="flex items-center gap-2">
        <!-- Period filter -->
        <select
          v-model="period"
          class="text-xs px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 focus:ring-2 focus:ring-[#3B7AB1]/50"
          data-testid="period-filter"
        >
          <option v-for="opt in periodOptions" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>

        <!-- Sort filter -->
        <select
          v-model="sortBy"
          class="text-xs px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 focus:ring-2 focus:ring-[#3B7AB1]/50"
          data-testid="sort-filter"
        >
          <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">
            {{ opt.icon }} {{ opt.label }}
          </option>
        </select>

        <!-- CSV Export button -->
        <button
          @click="exportCSV"
          class="flex items-center gap-1 text-xs px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 transition"
          title="Performance-Daten als CSV exportieren"
          data-testid="export-csv-btn"
        >
          📥 CSV
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="h-16 bg-gray-100 dark:bg-gray-700 rounded-lg animate-pulse"></div>
    </div>

    <!-- Empty state -->
    <EmptyState
      v-else-if="posts.length === 0"
      svgIcon="chart-bar"
      title="Noch keine Performance-Daten"
      description="Trage Metriken (Likes, Kommentare, Reichweite) fuer deine Posts ein, um das Ranking zu sehen."
      actionLabel="Post bearbeiten"
      actionTo="/library/history"
      :compact="true"
    />

    <!-- Post ranking list -->
    <div v-else class="space-y-2">
      <div
        v-for="(post, index) in posts"
        :key="post.id"
        @click="navigateToPost(post.id)"
        class="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-[#3B7AB1]/50 hover:shadow-sm cursor-pointer transition group"
        :data-testid="'top-post-' + index"
      >
        <!-- Rank badge -->
        <div class="flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center text-sm font-bold" :class="rankBadge(index).bg">
          {{ rankBadge(index).text }}
        </div>

        <!-- Post info -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span class="text-sm">{{ platformIcon(post.platform) }}</span>
            <p class="text-sm font-medium text-gray-900 dark:text-white truncate group-hover:text-[#3B7AB1]">
              {{ post.title || 'Ohne Titel' }}
            </p>
          </div>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            {{ categoryLabel(post.category) }}
            <span v-if="post.posted_at"> · {{ new Date(post.posted_at).toLocaleDateString('de-DE') }}</span>
          </p>
        </div>

        <!-- Metrics summary -->
        <div class="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
          <span v-if="post.perf_likes !== null" title="Likes">❤️ {{ post.perf_likes }}</span>
          <span v-if="post.perf_comments !== null" title="Kommentare">💬 {{ post.perf_comments }}</span>
          <span v-if="post.perf_reach !== null" title="Reichweite">👁️ {{ post.perf_reach }}</span>
        </div>

        <!-- Engagement rate -->
        <div class="flex-shrink-0 text-right" data-testid="post-engagement">
          <p class="text-sm font-bold" :class="engagementColor(post.engagement_rate)">
            {{ post.engagement_rate.toFixed(1) }}%
          </p>
          <p class="text-[10px] text-gray-400">Eng. Rate</p>
        </div>
      </div>
    </div>
  </div>
</template>
