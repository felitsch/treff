<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

// State
const loading = ref(false)
const error = ref(null)
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1) // 1-based
const postsByDate = ref({})
const totalPosts = ref(0)

// German month names
const monthNames = [
  'Januar', 'Februar', 'Maerz', 'April', 'Mai', 'Juni',
  'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember',
]

// German day abbreviations (Monday first)
const dayNames = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']

// Category colors - solid background colors for calendar cards
const categoryColors = {
  laender_spotlight: { bg: 'bg-blue-100 dark:bg-blue-900/40', border: 'border-blue-400', text: 'text-blue-700 dark:text-blue-300', dot: 'bg-blue-500' },
  erfahrungsberichte: { bg: 'bg-purple-100 dark:bg-purple-900/40', border: 'border-purple-400', text: 'text-purple-700 dark:text-purple-300', dot: 'bg-purple-500' },
  infografiken: { bg: 'bg-cyan-100 dark:bg-cyan-900/40', border: 'border-cyan-400', text: 'text-cyan-700 dark:text-cyan-300', dot: 'bg-cyan-500' },
  fristen_cta: { bg: 'bg-red-100 dark:bg-red-900/40', border: 'border-red-400', text: 'text-red-700 dark:text-red-300', dot: 'bg-red-500' },
  tipps_tricks: { bg: 'bg-amber-100 dark:bg-amber-900/40', border: 'border-amber-400', text: 'text-amber-700 dark:text-amber-300', dot: 'bg-amber-500' },
  faq: { bg: 'bg-teal-100 dark:bg-teal-900/40', border: 'border-teal-400', text: 'text-teal-700 dark:text-teal-300', dot: 'bg-teal-500' },
  foto_posts: { bg: 'bg-pink-100 dark:bg-pink-900/40', border: 'border-pink-400', text: 'text-pink-700 dark:text-pink-300', dot: 'bg-pink-500' },
  reel_tiktok_thumbnails: { bg: 'bg-violet-100 dark:bg-violet-900/40', border: 'border-violet-400', text: 'text-violet-700 dark:text-violet-300', dot: 'bg-violet-500' },
  story_posts: { bg: 'bg-orange-100 dark:bg-orange-900/40', border: 'border-orange-400', text: 'text-orange-700 dark:text-orange-300', dot: 'bg-orange-500' },
}

// Category labels & icons
const categoryMeta = {
  laender_spotlight: { label: 'Laender', icon: '🌍' },
  erfahrungsberichte: { label: 'Erfahrung', icon: '💬' },
  infografiken: { label: 'Infografik', icon: '📊' },
  fristen_cta: { label: 'Fristen', icon: '⏰' },
  tipps_tricks: { label: 'Tipps', icon: '💡' },
  faq: { label: 'FAQ', icon: '❓' },
  foto_posts: { label: 'Foto', icon: '📸' },
  reel_tiktok_thumbnails: { label: 'Reel', icon: '🎬' },
  story_posts: { label: 'Story', icon: '📱' },
}

// Status icons and labels
const statusMeta = {
  draft: { label: 'Entwurf', icon: '📝', color: 'text-gray-500' },
  scheduled: { label: 'Geplant', icon: '📅', color: 'text-blue-500' },
  reminded: { label: 'Erinnert', icon: '🔔', color: 'text-yellow-500' },
  exported: { label: 'Exportiert', icon: '📤', color: 'text-green-500' },
  posted: { label: 'Veroeffentlicht', icon: '✅', color: 'text-emerald-500' },
}

// Platform icons
const platformIcons = {
  instagram_feed: '📷',
  instagram_story: '📱',
  tiktok: '🎵',
}

// Computed: current month label
const currentMonthLabel = computed(() => {
  return `${monthNames[currentMonth.value - 1]} ${currentYear.value}`
})

// Computed: calendar grid days (6 rows x 7 cols = 42 cells)
const calendarDays = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value

  // First day of month (0=Sun...6=Sat) => convert to Mon-based (0=Mon...6=Sun)
  const firstDayOfMonth = new Date(year, month - 1, 1)
  let startDow = firstDayOfMonth.getDay() // 0=Sun, 1=Mon, ..., 6=Sat
  // Convert to Monday-based: Mon=0, Tue=1, ..., Sun=6
  startDow = startDow === 0 ? 6 : startDow - 1

  // Days in current month
  const daysInMonth = new Date(year, month, 0).getDate()

  // Days in previous month
  const prevMonth = month === 1 ? 12 : month - 1
  const prevYear = month === 1 ? year - 1 : year
  const daysInPrevMonth = new Date(prevYear, prevMonth, 0).getDate()

  const days = []

  // Previous month's trailing days
  for (let i = startDow - 1; i >= 0; i--) {
    const day = daysInPrevMonth - i
    const dateStr = `${prevYear}-${String(prevMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    days.push({
      day,
      dateStr,
      isCurrentMonth: false,
      isToday: false,
      posts: postsByDate.value[dateStr] || [],
    })
  }

  // Current month days
  const today = new Date()
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    days.push({
      day: d,
      dateStr,
      isCurrentMonth: true,
      isToday: dateStr === todayStr,
      posts: postsByDate.value[dateStr] || [],
    })
  }

  // Fill remaining cells to complete 6 rows (42 cells)
  const nextMonth = month === 12 ? 1 : month + 1
  const nextYear = month === 12 ? year + 1 : year
  let nextDay = 1
  while (days.length < 42) {
    const dateStr = `${nextYear}-${String(nextMonth).padStart(2, '0')}-${String(nextDay).padStart(2, '0')}`
    days.push({
      day: nextDay,
      dateStr,
      isCurrentMonth: false,
      isToday: false,
      posts: postsByDate.value[dateStr] || [],
    })
    nextDay++
  }

  return days
})

// Navigation
function prevMonthNav() {
  if (currentMonth.value === 1) {
    currentMonth.value = 12
    currentYear.value--
  } else {
    currentMonth.value--
  }
}

function nextMonthNav() {
  if (currentMonth.value === 12) {
    currentMonth.value = 1
    currentYear.value++
  } else {
    currentMonth.value++
  }
}

function goToToday() {
  const now = new Date()
  currentYear.value = now.getFullYear()
  currentMonth.value = now.getMonth() + 1
}

// Fetch calendar data
async function fetchCalendar() {
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`/api/calendar?month=${currentMonth.value}&year=${currentYear.value}`, {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    postsByDate.value = data.posts_by_date || {}
    totalPosts.value = data.total_posts || 0
  } catch (err) {
    console.error('Calendar fetch error:', err)
    error.value = 'Kalender konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

// Get color classes for a category
function getCategoryStyle(category) {
  return categoryColors[category] || {
    bg: 'bg-gray-100 dark:bg-gray-800',
    border: 'border-gray-400',
    text: 'text-gray-700 dark:text-gray-300',
    dot: 'bg-gray-500',
  }
}

function getCategoryLabel(category) {
  return categoryMeta[category]?.label || category
}

function getCategoryIcon(category) {
  return categoryMeta[category]?.icon || '📄'
}

function getPlatformIcon(platform) {
  return platformIcons[platform] || '📄'
}

function getStatusMeta(status) {
  return statusMeta[status] || { label: status, icon: '📄', color: 'text-gray-500' }
}

// Watch month/year changes
watch([currentMonth, currentYear], () => {
  fetchCalendar()
})

onMounted(() => {
  fetchCalendar()
})
</script>

<template>
  <div class="max-w-full">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Content-Kalender</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {{ totalPosts }} {{ totalPosts === 1 ? 'Post' : 'Posts' }} in {{ currentMonthLabel }}
        </p>
      </div>

      <!-- Month navigation -->
      <div class="flex items-center gap-2">
        <button
          @click="goToToday"
          class="px-3 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          Heute
        </button>
        <div class="flex items-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg">
          <button
            @click="prevMonthNav"
            class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-l-lg transition-colors"
            title="Vorheriger Monat"
          >
            <svg class="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <span class="px-4 py-2 font-semibold text-gray-900 dark:text-white min-w-[180px] text-center">
            {{ currentMonthLabel }}
          </span>
          <button
            @click="nextMonthNav"
            class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-r-lg transition-colors"
            title="Naechster Monat"
          >
            <svg class="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Error state -->
    <div v-if="error" class="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400">
      {{ error }}
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <span class="ml-3 text-gray-500 dark:text-gray-400">Kalender wird geladen...</span>
    </div>

    <!-- Calendar Grid -->
    <div v-else class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
      <!-- Day headers -->
      <div class="grid grid-cols-7 border-b border-gray-200 dark:border-gray-700">
        <div
          v-for="dayName in dayNames"
          :key="dayName"
          class="py-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400"
          :class="dayName === 'Sa' || dayName === 'So' ? 'bg-gray-50 dark:bg-gray-800/50' : 'bg-white dark:bg-gray-800'"
        >
          {{ dayName }}
        </div>
      </div>

      <!-- Calendar cells - 6 rows -->
      <div class="grid grid-cols-7">
        <div
          v-for="(dayObj, idx) in calendarDays"
          :key="dayObj.dateStr"
          class="min-h-[120px] border-b border-r border-gray-100 dark:border-gray-700/50 p-1.5 transition-colors"
          :class="[
            dayObj.isCurrentMonth ? 'bg-white dark:bg-gray-800' : 'bg-gray-50/50 dark:bg-gray-900/30',
            dayObj.isToday ? 'ring-2 ring-inset ring-blue-500' : '',
            (idx % 7 === 5 || idx % 7 === 6) ? 'bg-gray-50/30 dark:bg-gray-800/50' : '',
          ]"
        >
          <!-- Day number -->
          <div class="flex items-center justify-between mb-1">
            <span
              class="text-sm font-medium leading-none"
              :class="[
                dayObj.isToday ? 'bg-blue-600 text-white rounded-full w-7 h-7 flex items-center justify-center' : '',
                dayObj.isCurrentMonth ? 'text-gray-900 dark:text-gray-100' : 'text-gray-400 dark:text-gray-600',
              ]"
            >
              {{ dayObj.day }}
            </span>
            <!-- Post count badge -->
            <span
              v-if="dayObj.posts.length > 0"
              class="text-xs font-medium px-1.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300"
            >
              {{ dayObj.posts.length }}
            </span>
          </div>

          <!-- Post cards -->
          <div class="space-y-1">
            <div
              v-for="post in dayObj.posts.slice(0, 3)"
              :key="post.id"
              class="rounded-md px-1.5 py-1 border-l-3 text-xs cursor-default truncate"
              :class="[
                getCategoryStyle(post.category).bg,
                getCategoryStyle(post.category).text,
                'border-l-[3px]',
                getCategoryStyle(post.category).border,
              ]"
              :title="`${post.title || 'Unbenannt'} - ${getCategoryLabel(post.category)} - ${getStatusMeta(post.status).label}${post.scheduled_time ? ' um ' + post.scheduled_time : ''}`"
            >
              <div class="flex items-center gap-1">
                <span class="flex-shrink-0">{{ getCategoryIcon(post.category) }}</span>
                <span class="truncate font-medium">{{ post.title || 'Unbenannt' }}</span>
              </div>
              <div class="flex items-center gap-1 mt-0.5 opacity-75">
                <span class="flex-shrink-0 text-[10px]">{{ getPlatformIcon(post.platform) }}</span>
                <span v-if="post.scheduled_time" class="text-[10px]">{{ post.scheduled_time }}</span>
                <span class="ml-auto text-[10px]" :class="getStatusMeta(post.status).color">{{ getStatusMeta(post.status).icon }}</span>
              </div>
            </div>

            <!-- More posts indicator -->
            <div
              v-if="dayObj.posts.length > 3"
              class="text-[10px] text-gray-500 dark:text-gray-400 text-center font-medium"
            >
              +{{ dayObj.posts.length - 3 }} weitere
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="mt-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 shadow-sm">
      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Kategorien</h3>
      <div class="flex flex-wrap gap-3">
        <div
          v-for="(meta, catId) in categoryMeta"
          :key="catId"
          class="flex items-center gap-1.5"
        >
          <span class="w-3 h-3 rounded-full" :class="getCategoryStyle(catId).dot"></span>
          <span class="text-xs text-gray-600 dark:text-gray-400">{{ meta.icon }} {{ meta.label }}</span>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-if="!loading && !error && totalPosts === 0"
      class="mt-6 text-center py-8"
    >
      <div class="text-5xl mb-3">📅</div>
      <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-1">
        Keine geplanten Posts
      </h3>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
        Erstelle Posts und plane sie ein, um sie im Kalender zu sehen.
      </p>
      <router-link
        to="/create-post"
        class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
      >
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Post erstellen
      </router-link>
    </div>
  </div>
</template>
