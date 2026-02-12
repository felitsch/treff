<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/utils/api'

const loading = ref(true)
const error = ref(null)

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

// Category colors for distribution bars
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

async function fetchAnalytics() {
  loading.value = true
  error.value = null
  try {
    const [overviewRes, categoriesRes, platformsRes, countriesRes, goalsRes] = await Promise.all([
      api.get('/api/analytics/overview'),
      api.get('/api/analytics/categories'),
      api.get('/api/analytics/platforms'),
      api.get('/api/analytics/countries'),
      api.get('/api/analytics/goals'),
    ])

    overview.value = overviewRes.data
    categories.value = categoriesRes.data
    platforms.value = platformsRes.data
    countries.value = countriesRes.data
    goals.value = goalsRes.data
  } catch (err) {
    console.error('Failed to load analytics:', err)
    error.value = 'Fehler beim Laden der Analytics-Daten.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchAnalytics)
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">Analytics</h1>

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
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
      <p class="text-red-600 dark:text-red-400 mb-3">{{ error }}</p>
      <button
        @click="fetchAnalytics"
        class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
      >
        Erneut versuchen
      </button>
    </div>

    <!-- Analytics content -->
    <div v-else class="space-y-6">
      <!-- Overview stats cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4" data-testid="overview-stats">
        <!-- Total posts -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
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
        </div>

        <!-- Posts this week -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Posts diese Woche</p>
              <p class="text-3xl font-bold text-[#4C8BC2] mt-1" data-testid="posts-this-week">
                {{ overview.posts_this_week }}
              </p>
            </div>
            <div class="w-12 h-12 bg-[#4C8BC2]/10 rounded-xl flex items-center justify-center">
              <span class="text-2xl">📅</span>
            </div>
          </div>
        </div>

        <!-- Posts this month -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
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
        </div>
      </div>

      <!-- Goal tracking -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700" data-testid="goal-tracking">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Zielverfolgung</h2>
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
                :class="weeklyProgress >= 100 ? 'bg-green-500' : 'bg-[#4C8BC2]'"
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
      </div>

      <!-- Distribution charts row -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Category distribution -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700" data-testid="category-distribution">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Kategorieverteilung</h2>
          <div v-if="categories.length === 0" class="text-center py-8">
            <p class="text-gray-400 dark:text-gray-500">Noch keine Posts erstellt</p>
          </div>
          <div v-else class="space-y-3">
            <div v-for="cat in categories" :key="cat.category" class="flex items-center gap-3">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300 w-32 truncate" :title="categoryLabel(cat.category)">
                {{ categoryLabel(cat.category) }}
              </span>
              <div class="flex-1 h-6 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full flex items-center justify-end pr-2 transition-all duration-500"
                  :class="categoryColor(cat.category)"
                  :style="{ width: Math.max(10, (cat.count / totalCategoryPosts) * 100) + '%' }"
                >
                  <span class="text-xs font-bold text-white">{{ cat.count }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Platform distribution -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700" data-testid="platform-distribution">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Plattformverteilung</h2>
          <div v-if="platforms.length === 0" class="text-center py-8">
            <p class="text-gray-400 dark:text-gray-500">Noch keine Posts erstellt</p>
          </div>
          <div v-else class="space-y-4">
            <div v-for="p in platforms" :key="p.platform" class="flex items-center gap-3">
              <span class="text-xl">{{ platformIcon(p.platform) }}</span>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300 w-32">
                {{ platformLabel(p.platform) }}
              </span>
              <div class="flex-1 h-6 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  class="h-full bg-[#4C8BC2] rounded-full flex items-center justify-end pr-2 transition-all duration-500"
                  :style="{ width: Math.max(10, (p.count / totalPlatformPosts) * 100) + '%' }"
                >
                  <span class="text-xs font-bold text-white">{{ p.count }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Country distribution -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700" data-testid="country-distribution">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Laenderverteilung</h2>
        <div v-if="countries.length === 0" class="text-center py-8">
          <p class="text-gray-400 dark:text-gray-500">Noch keine Posts mit Laenderzuweisung</p>
        </div>
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
      </div>
    </div>
  </div>
</template>
