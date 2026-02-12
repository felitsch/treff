<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

// State
const loading = ref(false)
const error = ref(null)

// Unscheduled drafts sidebar
const unscheduledPosts = ref([])
const loadingUnscheduled = ref(false)
const sidebarCollapsed = ref(false)

// Drag-and-drop state
const draggedPost = ref(null)
const dragOverDate = ref(null)
const schedulingPost = ref(null)
const scheduleTime = ref('10:00')
const scheduleTargetDate = ref(null)
const showTimeDialog = ref(false)
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1) // 1-based
const postsByDate = ref({})
const totalPosts = ref(0)

// View mode: 'month', 'week', or 'queue'
const viewMode = ref('month')

// Platform filter: null = all, or 'instagram_feed', 'instagram_story', 'tiktok'
const platformFilter = ref(null)

// Gap detection: days without scheduled posts
const gapDates = ref(new Set())
const showGaps = ref(true)

// Weekly/monthly goal stats
const goalStats = ref({
  posts_this_week: 0,
  weekly_goal: 3,
  posts_this_month: 0,
  monthly_goal: 12,
})

// Platform filter options
const platformOptions = [
  { value: null, label: 'Alle', icon: '📋' },
  { value: 'instagram_feed', label: 'IG Feed', icon: '📷' },
  { value: 'instagram_story', label: 'IG Story', icon: '📱' },
  { value: 'tiktok', label: 'TikTok', icon: '🎵' },
]

// Weekly view state
const weekDate = ref(new Date().toISOString().split('T')[0]) // YYYY-MM-DD for current week
const weekPostsByDate = ref({})
const weekStartDate = ref(null)
const weekEndDate = ref(null)

// Queue view state
const queuePosts = ref([])
const queueCount = ref(0)

// German month names
const monthNames = [
  'Januar', 'Februar', 'Maerz', 'April', 'Mai', 'Juni',
  'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember',
]

// German day abbreviations (Monday first)
const dayNames = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']

// German full day names (Monday first)
const dayNamesFull = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']

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

// Time slots for weekly view (6:00 - 23:00)
const timeSlots = Array.from({ length: 18 }, (_, i) => {
  const hour = i + 6
  return {
    hour,
    label: `${String(hour).padStart(2, '0')}:00`,
  }
})

// Computed: current month label
const currentMonthLabel = computed(() => {
  return `${monthNames[currentMonth.value - 1]} ${currentYear.value}`
})

// Computed: week days array (Mon-Sun) with date strings and posts
const weekDays = computed(() => {
  if (!weekStartDate.value) return []

  const startDate = new Date(weekStartDate.value + 'T00:00:00')
  const today = new Date()
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

  const days = []
  for (let i = 0; i < 7; i++) {
    const d = new Date(startDate)
    d.setDate(d.getDate() + i)
    const dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    days.push({
      dayName: dayNames[i],
      dayNameFull: dayNamesFull[i],
      date: d.getDate(),
      month: d.getMonth() + 1,
      dateStr,
      isToday: dateStr === todayStr,
      posts: weekPostsByDate.value[dateStr] || [],
    })
  }
  return days
})

// Computed: week label (e.g., "10. - 16. Februar 2026")
const weekLabel = computed(() => {
  if (!weekStartDate.value || !weekEndDate.value) return ''
  const start = new Date(weekStartDate.value + 'T00:00:00')
  const end = new Date(weekEndDate.value + 'T00:00:00')
  const startDay = start.getDate()
  const endDay = end.getDate()
  const startMonth = monthNames[start.getMonth()]
  const endMonth = monthNames[end.getMonth()]

  if (start.getMonth() === end.getMonth()) {
    return `${startDay}. - ${endDay}. ${endMonth} ${end.getFullYear()}`
  }
  return `${startDay}. ${startMonth} - ${endDay}. ${endMonth} ${end.getFullYear()}`
})

// Computed: total posts in the current week
const weekTotalPosts = computed(() => {
  let count = 0
  for (const posts of Object.values(weekPostsByDate.value)) {
    count += posts.length
  }
  return count
})

// Get posts at a specific time slot for a specific day in weekly view
function getPostsAtTimeSlot(dayDateStr, hour) {
  const posts = weekPostsByDate.value[dayDateStr] || []
  return posts.filter(post => {
    if (!post.scheduled_time) {
      // Posts without scheduled_time show in the 09:00 slot by default
      return hour === 9
    }
    const postHour = parseInt(post.scheduled_time.split(':')[0], 10)
    return postHour === hour
  })
}

// Check if a day has any unscheduled-time posts (for the all-day row)
function getAllDayPosts(dayDateStr) {
  const posts = weekPostsByDate.value[dayDateStr] || []
  return posts.filter(post => !post.scheduled_time)
}

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

// Navigation - Month view
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

// Navigation - Week view
function prevWeekNav() {
  const d = new Date(weekDate.value + 'T00:00:00')
  d.setDate(d.getDate() - 7)
  weekDate.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function nextWeekNav() {
  const d = new Date(weekDate.value + 'T00:00:00')
  d.setDate(d.getDate() + 7)
  weekDate.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function goToToday() {
  const now = new Date()
  currentYear.value = now.getFullYear()
  currentMonth.value = now.getMonth() + 1
  weekDate.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  fetchData()
}

// Switch view mode
function setViewMode(mode) {
  viewMode.value = mode
  fetchData()
}

// Set platform filter
function setPlatformFilter(platform) {
  platformFilter.value = platform
  fetchData()
}

// Fetch calendar data (month)
async function fetchCalendar() {
  loading.value = true
  error.value = null
  try {
    let url = `/api/calendar?month=${currentMonth.value}&year=${currentYear.value}`
    if (platformFilter.value) {
      url += `&platform=${platformFilter.value}`
    }
    const res = await fetch(url, {
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

// Fetch week data
async function fetchWeek() {
  loading.value = true
  error.value = null
  try {
    let url = `/api/calendar/week?date=${weekDate.value}`
    if (platformFilter.value) {
      url += `&platform=${platformFilter.value}`
    }
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    weekPostsByDate.value = data.posts_by_date || {}
    weekStartDate.value = data.start_date || null
    weekEndDate.value = data.end_date || null
  } catch (err) {
    console.error('Week fetch error:', err)
    error.value = 'Wochenansicht konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

// Fetch unscheduled drafts for sidebar
async function fetchUnscheduled() {
  loadingUnscheduled.value = true
  try {
    const res = await fetch('/api/calendar/unscheduled', {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    unscheduledPosts.value = data.posts || []
  } catch (err) {
    console.error('Unscheduled fetch error:', err)
  } finally {
    loadingUnscheduled.value = false
  }
}

// Fetch gap dates for the current month
async function fetchGaps() {
  try {
    const res = await fetch(`/api/calendar/gaps?month=${currentMonth.value}&year=${currentYear.value}`, {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    gapDates.value = new Set(data.gaps || [])
  } catch (err) {
    console.error('Gaps fetch error:', err)
  }
}

// Fetch goal stats
async function fetchStats() {
  try {
    const res = await fetch('/api/calendar/stats', {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    goalStats.value = data
  } catch (err) {
    console.error('Stats fetch error:', err)
  }
}

// Computed: weekly goal progress percentage (capped at 100)
const weeklyGoalPercent = computed(() => {
  if (!goalStats.value.weekly_goal || goalStats.value.weekly_goal <= 0) return 0
  return Math.min(100, Math.round((goalStats.value.posts_this_week / goalStats.value.weekly_goal) * 100))
})

// Computed: whether weekly goal is met
const weeklyGoalMet = computed(() => {
  return goalStats.value.posts_this_week >= goalStats.value.weekly_goal
})

// Fetch queue data (chronological list of upcoming scheduled posts)
async function fetchQueue() {
  loading.value = true
  error.value = null
  try {
    let url = '/api/calendar/queue'
    if (platformFilter.value) {
      url += `?platform=${platformFilter.value}`
    }
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    queuePosts.value = data.posts || []
    queueCount.value = data.count || 0
  } catch (err) {
    console.error('Queue fetch error:', err)
    error.value = 'Warteschlange konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

// Unified fetch based on current view mode
function fetchData() {
  fetchStats()
  if (viewMode.value === 'month') {
    fetchCalendar()
    fetchGaps()
  } else if (viewMode.value === 'week') {
    fetchWeek()
  } else if (viewMode.value === 'queue') {
    fetchQueue()
  }
}

// Check if a date is a gap (no posts scheduled) - only for current month days
function isGapDate(dateStr, isCurrentMonth) {
  if (!showGaps.value || !isCurrentMonth) return false
  return gapDates.value.has(dateStr)
}

// Computed: number of gap days in current month
const gapCount = computed(() => {
  return gapDates.value.size
})

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

// ========== DATE HELPERS ==========

// Get today's date string in YYYY-MM-DD format (local time)
function getTodayStr() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
}

// Check if a date string (YYYY-MM-DD) is in the past (before today)
function isPastDate(dateStr) {
  if (!dateStr) return false
  return dateStr < getTodayStr()
}

// Scheduling error message for past dates
const scheduleError = ref(null)

// ========== DRAG AND DROP ==========

function onDragStart(event, post) {
  draggedPost.value = post
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', JSON.stringify({ postId: post.id }))
  event.target.classList.add('opacity-50')
}

function onDragEnd(event) {
  draggedPost.value = null
  dragOverDate.value = null
  event.target.classList.remove('opacity-50')
}

function onDragOver(event, dateStr) {
  // Prevent dropping on past dates
  if (isPastDate(dateStr)) {
    event.dataTransfer.dropEffect = 'none'
    return
  }
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
  dragOverDate.value = dateStr
}

function onDragLeave(event, dateStr) {
  if (dragOverDate.value === dateStr) {
    const rect = event.currentTarget.getBoundingClientRect()
    const x = event.clientX
    const y = event.clientY
    if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
      dragOverDate.value = null
    }
  }
}

function onDrop(event, dateStr) {
  event.preventDefault()
  dragOverDate.value = null
  if (!draggedPost.value) return

  // Prevent scheduling on past dates
  if (isPastDate(dateStr)) return

  schedulingPost.value = draggedPost.value
  scheduleTargetDate.value = dateStr
  scheduleTime.value = '10:00'
  scheduleError.value = null
  showTimeDialog.value = true
  draggedPost.value = null
}

async function confirmSchedule() {
  if (!schedulingPost.value || !scheduleTargetDate.value) return

  // Prevent scheduling on past dates
  if (isPastDate(scheduleTargetDate.value)) {
    scheduleError.value = 'Vergangene Daten koennen nicht ausgewaehlt werden.'
    return
  }

  scheduleError.value = null

  try {
    const res = await fetch(`/api/posts/${schedulingPost.value.id}/schedule`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${auth.accessToken}`,
      },
      body: JSON.stringify({
        scheduled_date: scheduleTargetDate.value,
        scheduled_time: scheduleTime.value,
      }),
    })

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      throw new Error(errData.detail || `HTTP ${res.status}`)
    }

    // Refresh both calendar and unscheduled list
    await Promise.all([fetchData(), fetchUnscheduled()])
  } catch (err) {
    console.error('Schedule error:', err)
    error.value = `Fehler beim Planen: ${err.message}`
  } finally {
    showTimeDialog.value = false
    schedulingPost.value = null
    scheduleTargetDate.value = null
    scheduleError.value = null
  }
}

function cancelScheduleDialog() {
  showTimeDialog.value = false
  schedulingPost.value = null
  scheduleTargetDate.value = null
}

function formatDateForDisplay(dateStr) {
  if (!dateStr) return ''
  const parts = dateStr.split('-')
  return `${parts[2]}.${parts[1]}.${parts[0]}`
}

// Prev/Next navigation that respects view mode
function prevNav() {
  if (viewMode.value === 'month') {
    prevMonthNav()
  } else {
    prevWeekNav()
  }
}

function nextNav() {
  if (viewMode.value === 'month') {
    nextMonthNav()
  } else {
    nextWeekNav()
  }
}

// Computed: navigation label
const navLabel = computed(() => {
  if (viewMode.value === 'month') {
    return currentMonthLabel.value
  }
  return weekLabel.value
})

// Computed: active platform label for subtitle
const activePlatformLabel = computed(() => {
  if (!platformFilter.value) return ''
  const opt = platformOptions.find(o => o.value === platformFilter.value)
  return opt ? ` (${opt.icon} ${opt.label})` : ''
})

// Computed: subtitle text
const subtitleText = computed(() => {
  if (viewMode.value === 'month') {
    return `${totalPosts.value} ${totalPosts.value === 1 ? 'Post' : 'Posts'} in ${currentMonthLabel.value}${activePlatformLabel.value}`
  }
  if (viewMode.value === 'queue') {
    return `${queueCount.value} ${queueCount.value === 1 ? 'anstehender Post' : 'anstehende Posts'}${activePlatformLabel.value}`
  }
  return `${weekTotalPosts.value} ${weekTotalPosts.value === 1 ? 'Post' : 'Posts'} in dieser Woche${activePlatformLabel.value}`
})

// Watch month/year changes (for month view)
watch([currentMonth, currentYear], () => {
  if (viewMode.value === 'month') {
    fetchCalendar()
    fetchGaps()
  }
})

// Watch weekDate changes (for week view)
watch(weekDate, () => {
  if (viewMode.value === 'week') {
    fetchWeek()
  }
})

onMounted(() => {
  fetchData()
  fetchUnscheduled()
})
</script>

<template>
  <div class="max-w-full">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Content-Kalender</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {{ subtitleText }}
        </p>
      </div>

      <!-- Controls: platform filter + view toggle + navigation -->
      <div class="flex items-center gap-3 flex-wrap">
        <!-- Platform filter -->
        <div class="flex items-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
          <button
            v-for="opt in platformOptions"
            :key="opt.value ?? 'all'"
            @click="setPlatformFilter(opt.value)"
            class="px-3 py-1.5 text-sm font-medium transition-colors whitespace-nowrap"
            :class="platformFilter === opt.value
              ? 'bg-blue-600 text-white'
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'"
            :title="'Filtern nach ' + opt.label"
          >
            {{ opt.icon }} {{ opt.label }}
          </button>
        </div>

        <!-- View mode toggle -->
        <div class="flex items-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
          <button
            @click="setViewMode('month')"
            class="px-3 py-1.5 text-sm font-medium transition-colors"
            :class="viewMode === 'month'
              ? 'bg-blue-600 text-white'
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'"
          >
            Monat
          </button>
          <button
            @click="setViewMode('week')"
            class="px-3 py-1.5 text-sm font-medium transition-colors"
            :class="viewMode === 'week'
              ? 'bg-blue-600 text-white'
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'"
          >
            Woche
          </button>
          <button
            @click="setViewMode('queue')"
            class="px-3 py-1.5 text-sm font-medium transition-colors"
            :class="viewMode === 'queue'
              ? 'bg-blue-600 text-white'
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'"
          >
            Warteschlange
          </button>
        </div>

        <!-- Today button (hide in queue mode) -->
        <button
          v-if="viewMode !== 'queue'"
          @click="goToToday"
          class="px-3 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          Heute
        </button>

        <!-- Gap detection toggle (only in month view) -->
        <button
          v-if="viewMode === 'month'"
          @click="showGaps = !showGaps"
          class="px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors flex items-center gap-1.5"
          :class="showGaps
            ? 'bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300 border-orange-300 dark:border-orange-600'
            : 'text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'"
          title="Posting-Luecken anzeigen/ausblenden"
        >
          <span v-if="showGaps">&#9888;&#65039;</span><span v-else>&#128065;&#65039;</span>
          Luecken
          <span v-if="showGaps && gapCount > 0" class="bg-orange-200 dark:bg-orange-800 text-orange-800 dark:text-orange-200 text-xs font-bold px-1.5 py-0.5 rounded-full">
            {{ gapCount }}
          </span>
        </button>

        <!-- Prev / Label / Next (hide in queue mode) -->
        <div v-if="viewMode !== 'queue'" class="flex items-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg">
          <button
            @click="prevNav"
            class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-l-lg transition-colors"
            :title="viewMode === 'month' ? 'Vorheriger Monat' : 'Vorherige Woche'"
          >
            <svg class="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <span class="px-4 py-2 font-semibold text-gray-900 dark:text-white min-w-[180px] text-center text-sm">
            {{ navLabel }}
          </span>
          <button
            @click="nextNav"
            class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-r-lg transition-colors"
            :title="viewMode === 'month' ? 'Naechster Monat' : 'Naechste Woche'"
          >
            <svg class="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Weekly Goal Progress Indicator -->
    <div class="mb-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 shadow-sm">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-2">
          <span class="text-lg">🎯</span>
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Woechentliches Posting-Ziel</h3>
        </div>
        <div class="flex items-center gap-2">
          <span
            class="text-sm font-bold"
            :class="weeklyGoalMet ? 'text-green-600 dark:text-green-400' : 'text-blue-600 dark:text-blue-400'"
          >
            {{ goalStats.posts_this_week }}/{{ goalStats.weekly_goal }}
          </span>
          <span v-if="weeklyGoalMet" class="text-green-500 text-lg">✅</span>
        </div>
      </div>
      <!-- Progress bar -->
      <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
        <div
          class="h-3 rounded-full transition-all duration-500 ease-out"
          :class="weeklyGoalMet ? 'bg-green-500' : 'bg-blue-500'"
          :style="{ width: weeklyGoalPercent + '%' }"
        ></div>
      </div>
      <div class="flex items-center justify-between mt-1.5">
        <span class="text-xs text-gray-500 dark:text-gray-400">
          {{ weeklyGoalPercent }}% erreicht
        </span>
        <span v-if="!weeklyGoalMet && goalStats.weekly_goal > goalStats.posts_this_week" class="text-xs text-gray-500 dark:text-gray-400">
          Noch {{ goalStats.weekly_goal - goalStats.posts_this_week }} {{ (goalStats.weekly_goal - goalStats.posts_this_week) === 1 ? 'Post' : 'Posts' }} diese Woche
        </span>
        <span v-else-if="weeklyGoalMet" class="text-xs text-green-600 dark:text-green-400 font-medium">
          Ziel erreicht! 🎉
        </span>
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

    <!-- Main layout: sidebar + calendar -->
    <div v-else class="flex gap-4">
      <!-- Unscheduled drafts sidebar -->
      <div
        class="flex-shrink-0 transition-all duration-300"
        :class="sidebarCollapsed ? 'w-10' : 'w-64'"
      >
        <!-- Collapse toggle -->
        <button
          @click="sidebarCollapsed = !sidebarCollapsed"
          class="w-full flex items-center justify-between px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-t-xl text-sm font-semibold text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          :title="sidebarCollapsed ? 'Seitenleiste einblenden' : 'Seitenleiste ausblenden'"
        >
          <span v-if="!sidebarCollapsed" class="flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            Ungeplante Posts
            <span class="bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-bold px-1.5 py-0.5 rounded-full">
              {{ unscheduledPosts.length }}
            </span>
          </span>
          <svg
            class="w-4 h-4 transition-transform"
            :class="sidebarCollapsed ? 'rotate-180' : ''"
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <!-- Sidebar content -->
        <div
          v-if="!sidebarCollapsed"
          class="bg-white dark:bg-gray-800 border border-t-0 border-gray-200 dark:border-gray-700 rounded-b-xl overflow-hidden"
        >
          <!-- Loading -->
          <div v-if="loadingUnscheduled" class="p-4 text-center">
            <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mx-auto"></div>
          </div>

          <!-- Empty state -->
          <div v-else-if="unscheduledPosts.length === 0" class="p-4 text-center">
            <div class="text-3xl mb-2">🎉</div>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Alle Posts sind geplant!
            </p>
          </div>

          <!-- Draggable posts list -->
          <div v-else class="max-h-[600px] overflow-y-auto p-2 space-y-2">
            <p class="text-xs text-gray-500 dark:text-gray-400 px-1 mb-2">
              Ziehe einen Post auf ein Datum im Kalender
            </p>
            <div
              v-for="post in unscheduledPosts"
              :key="'sidebar-' + post.id"
              draggable="true"
              @dragstart="onDragStart($event, post)"
              @dragend="onDragEnd"
              class="rounded-lg px-3 py-2 border cursor-grab active:cursor-grabbing select-none transition-all hover:shadow-md"
              :class="[
                getCategoryStyle(post.category).bg,
                getCategoryStyle(post.category).text,
                'border-l-[3px]',
                getCategoryStyle(post.category).border,
                'border-gray-200 dark:border-gray-600',
              ]"
              :title="`${post.title || 'Unbenannt'} - ${getCategoryLabel(post.category)} - Ziehen zum Planen`"
            >
              <div class="flex items-center gap-1.5">
                <!-- Drag handle icon -->
                <svg class="w-3.5 h-3.5 flex-shrink-0 text-gray-400 dark:text-gray-500" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 6a2 2 0 1 1 0-4 2 2 0 0 1 0 4zm0 8a2 2 0 1 1 0-4 2 2 0 0 1 0 4zm0 8a2 2 0 1 1 0-4 2 2 0 0 1 0 4zm8-16a2 2 0 1 1 0-4 2 2 0 0 1 0 4zm0 8a2 2 0 1 1 0-4 2 2 0 0 1 0 4zm0 8a2 2 0 1 1 0-4 2 2 0 0 1 0 4z"/>
                </svg>
                <span class="flex-shrink-0 text-sm">{{ getCategoryIcon(post.category) }}</span>
                <span class="truncate text-sm font-medium">{{ post.title || 'Unbenannt' }}</span>
              </div>
              <div class="flex items-center gap-1.5 mt-1 text-xs opacity-75">
                <span>{{ getPlatformIcon(post.platform) }}</span>
                <span>{{ getCategoryLabel(post.category) }}</span>
                <span class="ml-auto" :class="getStatusMeta(post.status).color">
                  {{ getStatusMeta(post.status).icon }} {{ getStatusMeta(post.status).label }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Calendar content area -->
      <div class="flex-1 min-w-0">

    <!-- ==================== MONTHLY VIEW ==================== -->
    <div v-if="viewMode === 'month'" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
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
            dragOverDate === dayObj.dateStr && !isPastDate(dayObj.dateStr) ? 'bg-blue-50 dark:bg-blue-900/30 ring-2 ring-inset ring-blue-400' : '',
            isGapDate(dayObj.dateStr, dayObj.isCurrentMonth) ? 'bg-orange-50 dark:bg-orange-900/20' : '',
            isPastDate(dayObj.dateStr) && draggedPost ? 'opacity-50 cursor-not-allowed' : '',
          ]"
          @dragover="onDragOver($event, dayObj.dateStr)"
          @dragleave="onDragLeave($event, dayObj.dateStr)"
          @drop="onDrop($event, dayObj.dateStr)"
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
            <div class="flex items-center gap-1">
              <!-- Gap indicator -->
              <span
                v-if="isGapDate(dayObj.dateStr, dayObj.isCurrentMonth)"
                class="text-xs font-medium px-1.5 py-0.5 rounded-full bg-orange-100 dark:bg-orange-900/40 text-orange-600 dark:text-orange-400"
                title="Keine Posts geplant - Posting-Luecke"
              >
                Luecke
              </span>
              <!-- Post count badge -->
              <span
                v-if="dayObj.posts.length > 0"
                class="text-xs font-medium px-1.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300"
              >
                {{ dayObj.posts.length }}
              </span>
            </div>
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

          <!-- Drop zone indicator when dragging -->
          <div
            v-if="draggedPost && dragOverDate === dayObj.dateStr"
            class="mt-1 rounded-md border-2 border-dashed border-blue-400 bg-blue-50 dark:bg-blue-900/20 px-2 py-1 text-xs text-blue-600 dark:text-blue-400 text-center"
          >
            Hier ablegen
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== WEEKLY VIEW ==================== -->
    <div v-if="viewMode === 'week'" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
      <!-- Day headers for weekly view -->
      <div class="grid grid-cols-[60px_repeat(7,1fr)] border-b border-gray-200 dark:border-gray-700">
        <!-- Empty corner cell for time column header -->
        <div class="py-3 px-2 text-center text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 bg-gray-50 dark:bg-gray-800/50 border-r border-gray-200 dark:border-gray-700">
          Zeit
        </div>
        <!-- Day columns -->
        <div
          v-for="(day, idx) in weekDays"
          :key="day.dateStr"
          class="py-2 px-1 text-center border-r border-gray-200 dark:border-gray-700 last:border-r-0"
          :class="[
            day.isToday ? 'bg-blue-50 dark:bg-blue-900/20' : (idx >= 5 ? 'bg-gray-50 dark:bg-gray-800/50' : 'bg-white dark:bg-gray-800'),
          ]"
        >
          <div class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
            {{ day.dayName }}
          </div>
          <div
            class="mt-1 text-lg font-bold leading-none"
            :class="day.isToday ? 'text-blue-600 dark:text-blue-400' : 'text-gray-900 dark:text-gray-100'"
          >
            <span
              :class="day.isToday ? 'bg-blue-600 text-white rounded-full w-8 h-8 inline-flex items-center justify-center' : ''"
            >
              {{ day.date }}
            </span>
          </div>
          <div class="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">
            {{ day.posts.length }} {{ day.posts.length === 1 ? 'Post' : 'Posts' }}
          </div>
        </div>
      </div>

      <!-- All-day row (posts without a scheduled_time) -->
      <div class="grid grid-cols-[60px_repeat(7,1fr)] border-b-2 border-gray-300 dark:border-gray-600">
        <div class="py-2 px-2 text-[10px] font-medium text-gray-400 dark:text-gray-500 text-right border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 flex items-center justify-end">
          Ganzt.
        </div>
        <div
          v-for="(day, idx) in weekDays"
          :key="'allday-' + day.dateStr"
          class="py-1 px-1 border-r border-gray-200 dark:border-gray-700 last:border-r-0 min-h-[32px]"
          :class="day.isToday ? 'bg-blue-50/50 dark:bg-blue-900/10' : (idx >= 5 ? 'bg-gray-50/30 dark:bg-gray-800/30' : '')"
        >
          <div
            v-for="post in getAllDayPosts(day.dateStr)"
            :key="'allday-post-' + post.id"
            class="rounded-md px-1.5 py-0.5 text-xs truncate mb-0.5 border-l-[3px]"
            :class="[
              getCategoryStyle(post.category).bg,
              getCategoryStyle(post.category).text,
              getCategoryStyle(post.category).border,
            ]"
            :title="`${post.title || 'Unbenannt'} - ${getCategoryLabel(post.category)} - ${getStatusMeta(post.status).label}`"
          >
            <span class="flex-shrink-0">{{ getCategoryIcon(post.category) }}</span>
            <span class="truncate font-medium ml-1">{{ post.title || 'Unbenannt' }}</span>
          </div>
        </div>
      </div>

      <!-- Time slot rows (scrollable) -->
      <div class="max-h-[600px] overflow-y-auto">
        <div
          v-for="slot in timeSlots"
          :key="slot.hour"
          class="grid grid-cols-[60px_repeat(7,1fr)] border-b border-gray-100 dark:border-gray-700/50"
        >
          <!-- Time label -->
          <div class="py-2 px-2 text-[11px] font-medium text-gray-400 dark:text-gray-500 text-right border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 flex items-start justify-end">
            {{ slot.label }}
          </div>

          <!-- Day cells -->
          <div
            v-for="(day, idx) in weekDays"
            :key="slot.hour + '-' + day.dateStr"
            class="min-h-[48px] py-0.5 px-1 border-r border-gray-100 dark:border-gray-700/30 last:border-r-0 transition-colors"
            :class="[
              day.isToday ? 'bg-blue-50/30 dark:bg-blue-900/5' : (idx >= 5 ? 'bg-gray-50/20 dark:bg-gray-800/20' : ''),
            ]"
          >
            <div
              v-for="post in getPostsAtTimeSlot(day.dateStr, slot.hour)"
              :key="'wk-' + post.id"
              class="rounded-md px-1.5 py-1 text-xs cursor-default mb-0.5 border-l-[3px]"
              :class="[
                getCategoryStyle(post.category).bg,
                getCategoryStyle(post.category).text,
                getCategoryStyle(post.category).border,
              ]"
              :title="`${post.title || 'Unbenannt'} - ${getCategoryLabel(post.category)} - ${getStatusMeta(post.status).label} - ${post.scheduled_time || ''}`"
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
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== QUEUE VIEW ==================== -->
    <div v-if="viewMode === 'queue'" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
      <!-- Queue header -->
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
        <div class="flex items-center gap-3">
          <span class="text-xl">📋</span>
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Anstehende Posts</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ queueCount }} {{ queueCount === 1 ? 'Post' : 'Posts' }} chronologisch sortiert
            </p>
          </div>
        </div>
      </div>

      <!-- Queue list -->
      <div v-if="queuePosts.length > 0" class="divide-y divide-gray-100 dark:divide-gray-700/50">
        <div
          v-for="(post, index) in queuePosts"
          :key="'queue-' + post.id"
          class="flex items-center gap-4 px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
        >
          <!-- Position number -->
          <div class="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 flex items-center justify-center text-sm font-bold">
            {{ index + 1 }}
          </div>

          <!-- Date & time column -->
          <div class="flex-shrink-0 w-32 text-center">
            <div class="text-sm font-semibold text-gray-900 dark:text-white">
              {{ formatDateForDisplay(post.scheduled_date) }}
            </div>
            <div v-if="post.scheduled_time" class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {{ post.scheduled_time }} Uhr
            </div>
          </div>

          <!-- Category color dot + post info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full flex-shrink-0" :class="getCategoryStyle(post.category).dot"></span>
              <span class="font-medium text-gray-900 dark:text-white truncate">
                {{ post.title || 'Unbenannt' }}
              </span>
            </div>
            <div class="flex items-center gap-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
              <span>{{ getCategoryIcon(post.category) }} {{ getCategoryLabel(post.category) }}</span>
              <span>{{ getPlatformIcon(post.platform) }} {{ post.platform ? post.platform.replace('_', ' ') : '' }}</span>
              <span v-if="post.country" class="capitalize">{{ post.country }}</span>
            </div>
          </div>

          <!-- Status badge -->
          <div class="flex-shrink-0">
            <span
              class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium"
              :class="{
                'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400': post.status === 'draft',
                'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300': post.status === 'scheduled',
                'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300': post.status === 'reminded',
                'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300': post.status === 'exported',
                'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300': post.status === 'posted',
              }"
            >
              {{ getStatusMeta(post.status).icon }}
              {{ getStatusMeta(post.status).label }}
            </span>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else class="py-12 text-center">
        <div class="text-5xl mb-3">📭</div>
        <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-1">
          Keine anstehenden Posts
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Plane Posts ein, um sie in der Warteschlange zu sehen.
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

    <!-- Legend -->
    <div class="mt-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 shadow-sm">
      <div class="flex flex-wrap items-start gap-6">
        <div>
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
        <div v-if="viewMode === 'month'">
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Posting-Luecken</h3>
          <div class="flex items-center gap-2">
            <span class="inline-block w-5 h-5 rounded bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-700"></span>
            <span class="text-xs text-gray-600 dark:text-gray-400">Tage ohne geplante Posts</span>
            <span v-if="gapCount > 0" class="text-xs font-medium px-1.5 py-0.5 rounded-full bg-orange-100 dark:bg-orange-900/40 text-orange-600 dark:text-orange-400">
              {{ gapCount }} {{ gapCount === 1 ? 'Tag' : 'Tage' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state (not for queue view - it has its own) -->
    <div
      v-if="!loading && !error && viewMode !== 'queue' && (viewMode === 'month' ? totalPosts === 0 : weekTotalPosts === 0)"
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

      </div><!-- end flex-1 calendar content area -->
    </div><!-- end flex gap-4 main layout -->

    <!-- Schedule time picker dialog (modal) -->
    <div
      v-if="showTimeDialog"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="cancelScheduleDialog"
    >
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 w-full max-w-sm mx-4">
        <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-1">
          Post planen
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          {{ schedulingPost?.title || 'Unbenannt' }}
        </p>

        <!-- Date picker (only allows today and future dates) -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" for="schedule-date-input">Datum</label>
          <input
            id="schedule-date-input"
            v-model="scheduleTargetDate"
            type="date"
            :min="getTodayStr()"
            class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            :class="isPastDate(scheduleTargetDate) ? 'border-red-400 dark:border-red-500' : 'border-gray-300 dark:border-gray-600'"
          />
          <p v-if="isPastDate(scheduleTargetDate)" class="mt-1 text-xs text-red-500 dark:text-red-400">
            Vergangene Daten koennen nicht ausgewaehlt werden.
          </p>
        </div>

        <!-- Time picker -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" for="schedule-time-input">Uhrzeit</label>
          <input
            id="schedule-time-input"
            v-model="scheduleTime"
            type="time"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <!-- Error message -->
        <div v-if="scheduleError" class="mb-4 p-2 bg-red-50 dark:bg-red-900/30 rounded-lg">
          <p class="text-sm text-red-600 dark:text-red-400">{{ scheduleError }}</p>
        </div>

        <!-- Actions -->
        <div class="flex gap-3">
          <button
            @click="cancelScheduleDialog"
            class="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            Abbrechen
          </button>
          <button
            @click="confirmSchedule"
            :disabled="isPastDate(scheduleTargetDate)"
            class="flex-1 px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors"
            :class="isPastDate(scheduleTargetDate) ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'"
          >
            Post planen
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
