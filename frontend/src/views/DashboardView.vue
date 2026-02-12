<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'

const router = useRouter()

const loading = ref(true)
const error = ref(null)

// Dashboard data
const stats = ref({
  posts_this_week: 0,
  scheduled_posts: 0,
  total_assets: 0,
  total_posts: 0,
})
const recentPosts = ref([])
const calendarEntries = ref([])

// Mini calendar: next 7 days
const next7Days = computed(() => {
  const days = []
  const today = new Date()
  for (let i = 0; i < 7; i++) {
    const d = new Date(today)
    d.setDate(today.getDate() + i)
    days.push({
      date: d,
      dateStr: d.toISOString().split('T')[0],
      dayName: d.toLocaleDateString('de-DE', { weekday: 'short' }),
      dayNum: d.getDate(),
      isToday: i === 0,
      month: d.toLocaleDateString('de-DE', { month: 'short' }),
    })
  }
  return days
})

// Check if a day has scheduled entries
function getEntriesForDate(dateStr) {
  return calendarEntries.value.filter((e) => e.scheduled_date === dateStr)
}

// Status badge colors
function statusColor(status) {
  switch (status) {
    case 'draft':
      return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
    case 'scheduled':
      return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
    case 'exported':
      return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
    case 'posted':
      return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300'
    case 'reminded':
      return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
    default:
      return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
  }
}

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

// Platform icons
function platformIcon(platform) {
  switch (platform) {
    case 'instagram_feed':
      return '📸'
    case 'instagram_story':
      return '📱'
    case 'tiktok':
      return '🎵'
    default:
      return '📝'
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

async function fetchDashboardData() {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/api/analytics/dashboard')
    stats.value = res.data.stats
    recentPosts.value = res.data.recent_posts
    calendarEntries.value = res.data.calendar_entries
  } catch (err) {
    console.error('Failed to load dashboard data:', err)
    error.value = 'Dashboard-Daten konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
      <p class="text-gray-500 dark:text-gray-400 mt-1">
        Willkommen zurueck! Hier ist dein Content-Ueberblick.
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="space-y-6">
      <!-- Skeleton stat cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="i in 3" :key="i" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 animate-pulse">
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24 mb-3"></div>
          <div class="h-8 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
        </div>
      </div>
      <!-- Skeleton content blocks -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 animate-pulse h-48"></div>
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 animate-pulse h-48"></div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
      <p class="text-red-600 dark:text-red-400">{{ error }}</p>
      <button
        @click="fetchDashboardData"
        class="mt-3 px-4 py-2 bg-red-100 dark:bg-red-800 text-red-700 dark:text-red-200 rounded-lg hover:bg-red-200 dark:hover:bg-red-700 transition-colors"
      >
        Erneut versuchen
      </button>
    </div>

    <!-- Dashboard Content -->
    <div v-else class="space-y-6">
      <!-- Quick Stats Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Posts this week -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Posts diese Woche</p>
              <p class="text-3xl font-bold text-gray-900 dark:text-white mt-1">{{ stats.posts_this_week }}</p>
            </div>
            <div class="w-12 h-12 bg-blue-50 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
              <span class="text-2xl">📝</span>
            </div>
          </div>
        </div>

        <!-- Scheduled Posts -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Geplante Posts</p>
              <p class="text-3xl font-bold text-gray-900 dark:text-white mt-1">{{ stats.scheduled_posts }}</p>
            </div>
            <div class="w-12 h-12 bg-yellow-50 dark:bg-yellow-900/30 rounded-xl flex items-center justify-center">
              <span class="text-2xl">📅</span>
            </div>
          </div>
        </div>

        <!-- Total Assets -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Gesamt Assets</p>
              <p class="text-3xl font-bold text-gray-900 dark:text-white mt-1">{{ stats.total_assets }}</p>
            </div>
            <div class="w-12 h-12 bg-green-50 dark:bg-green-900/30 rounded-xl flex items-center justify-center">
              <span class="text-2xl">🖼️</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Action Buttons -->
      <div class="flex flex-wrap gap-3">
        <button
          @click="router.push('/create-post')"
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-treff-blue text-white font-medium rounded-lg hover:bg-blue-600 transition-colors shadow-sm"
        >
          <span>✏️</span>
          Post erstellen
        </button>
        <button
          @click="router.push('/calendar')"
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 font-medium rounded-lg border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors shadow-sm"
        >
          <span>📅</span>
          Kalender anzeigen
        </button>
      </div>

      <!-- Middle Row: Mini Calendar + Recent Posts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Mini Calendar (Next 7 Days) -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
          <div class="p-5 border-b border-gray-100 dark:border-gray-700">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <span>📅</span> Naechste 7 Tage
            </h2>
          </div>
          <div class="p-5">
            <div class="grid grid-cols-7 gap-2">
              <div
                v-for="day in next7Days"
                :key="day.dateStr"
                class="flex flex-col items-center rounded-lg p-2 text-center transition-colors"
                :class="[
                  day.isToday
                    ? 'bg-treff-blue/10 dark:bg-treff-blue/20 ring-2 ring-treff-blue'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-700/50',
                ]"
              >
                <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  {{ day.dayName }}
                </span>
                <span
                  class="text-lg font-bold mt-0.5"
                  :class="
                    day.isToday
                      ? 'text-treff-blue'
                      : 'text-gray-900 dark:text-white'
                  "
                >
                  {{ day.dayNum }}
                </span>
                <span class="text-xs text-gray-400 dark:text-gray-500">
                  {{ day.month }}
                </span>
                <!-- Indicator dot for scheduled entries -->
                <div class="mt-1 h-1.5">
                  <div
                    v-if="getEntriesForDate(day.dateStr).length > 0"
                    class="w-1.5 h-1.5 rounded-full bg-treff-blue"
                  ></div>
                </div>
              </div>
            </div>
            <!-- No scheduled posts hint -->
            <div v-if="calendarEntries.length === 0" class="mt-4 text-center text-sm text-gray-400 dark:text-gray-500">
              Keine geplanten Posts in den naechsten 7 Tagen
            </div>
          </div>
        </div>

        <!-- Recent Posts -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
          <div class="p-5 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <span>📋</span> Letzte Posts
            </h2>
            <button
              v-if="recentPosts.length > 0"
              @click="router.push('/history')"
              class="text-sm text-treff-blue hover:text-blue-600 dark:hover:text-blue-400 font-medium"
            >
              Alle anzeigen
            </button>
          </div>
          <div class="p-5">
            <!-- Empty state -->
            <div v-if="recentPosts.length === 0" class="text-center py-8">
              <div class="text-4xl mb-3">📝</div>
              <p class="text-gray-500 dark:text-gray-400 font-medium">Noch keine Posts erstellt</p>
              <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">
                Erstelle deinen ersten Post, um loszulegen!
              </p>
              <button
                @click="router.push('/create-post')"
                class="mt-4 px-4 py-2 bg-treff-blue text-white text-sm font-medium rounded-lg hover:bg-blue-600 transition-colors"
              >
                Ersten Post erstellen
              </button>
            </div>

            <!-- Posts list -->
            <div v-else class="space-y-3">
              <div
                v-for="post in recentPosts"
                :key="post.id"
                class="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer group"
                @click="router.push(`/posts/${post.id}/edit`)"
              >
                <!-- Platform icon -->
                <div class="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span class="text-lg">{{ platformIcon(post.platform) }}</span>
                </div>

                <!-- Post info -->
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-900 dark:text-white truncate group-hover:text-treff-blue transition-colors">
                    {{ post.title || 'Ohne Titel' }}
                  </p>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {{ categoryLabel(post.category) }}
                    <span v-if="post.country" class="ml-1">· {{ post.country }}</span>
                    · {{ formatDate(post.created_at) }}
                  </p>
                </div>

                <!-- Status badge -->
                <span
                  class="text-xs font-medium px-2 py-1 rounded-full flex-shrink-0"
                  :class="statusColor(post.status)"
                >
                  {{ post.status }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Suggestions Section (Placeholder for future) -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
        <div class="p-5 border-b border-gray-100 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <span>💡</span> Content-Vorschlaege
          </h2>
        </div>
        <div class="p-5 text-center py-8">
          <div class="text-4xl mb-3">💡</div>
          <p class="text-gray-500 dark:text-gray-400 font-medium">Keine Vorschlaege vorhanden</p>
          <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">
            Content-Vorschlaege werden hier angezeigt, sobald sie generiert werden.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
