<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import api from '@/utils/api'
import ContentMixPanel from '@/components/calendar/ContentMixPanel.vue'
import CalendarExportImport from '@/components/calendar/CalendarExportImport.vue'
import RecurringPostSettings from '@/components/calendar/RecurringPostSettings.vue'
import WorkflowHint from '@/components/common/WorkflowHint.vue'
import HelpTooltip from '@/components/common/HelpTooltip.vue'
import { tooltipTexts } from '@/utils/tooltipTexts'
import TourSystem from '@/components/common/TourSystem.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SkeletonBase from '@/components/common/SkeletonBase.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import { toSeasonalMarkers, getMonthConfig } from '@/config/seasonalCalendar'

const auth = useAuthStore()
const router = useRouter()
const toast = useToast()

// State
const loading = ref(false)
const error = ref(null)

// Unscheduled drafts sidebar
const unscheduledPosts = ref([])
const loadingUnscheduled = ref(false)
const sidebarCollapsed = ref(window.innerWidth < 768)

// Content-Mix right sidebar
const mixPanelCollapsed = ref(window.innerWidth < 1024)

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

// Multi-select state for batch drag-and-drop
const selectedPostIds = ref(new Set())
const isMultiSelectMode = ref(false)
const showMultiMoveDialog = ref(false)
const multiMoveTargetDate = ref(null)
const multiMoveTime = ref('10:00')

// View mode: 'month', 'week', or 'queue'
const viewMode = ref('month')

// Platform filter: null = all, or 'instagram_feed', 'instagram_story', 'tiktok'
const platformFilter = ref(null)

// Gap detection: days without scheduled posts
const gapDates = ref(new Set())
const showGaps = ref(true)

const tourRef = ref(null)

// Weekly/monthly goal stats
const goalStats = ref({
  posts_this_week: 0,
  weekly_goal: 3,
  posts_this_month: 0,
  monthly_goal: 12,
})

// Seasonal markers (Bewerbungsfristen, Abflugzeiten, etc.)
const seasonalMarkers = ref([])
const showSeasonalMarkers = ref(true)

// Recycling suggestions for gap days
const recyclingSuggestions = ref({}) // dateStr -> suggestion
const showRecyclingSuggestions = ref(true)

// Recurring Format Placeholders
const recurringPlaceholders = ref([]) // Array of placeholder objects from API
const showRecurringFormats = ref(true)

// Export/Import Modal
const showExportImport = ref(false)

// Recurring Post Settings Modal
const showRecurringSettings = ref(false)
const recurringTargetPost = ref(null) // { id, title, scheduled_date }

function openRecurringSettings(post) {
  recurringTargetPost.value = post
  showRecurringSettings.value = true
}

// Story Arc Timeline
const showArcTimeline = ref(true)
const arcTimelineData = ref([]) // Array of arc objects from API
const hoveredEpisode = ref(null) // { arc, episode, x, y } for tooltip
const tooltipPosition = ref({ x: 0, y: 0 })

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

// Platform lanes view state
const platformLanes = ref([])
const crossPlatformStats = ref({})
const detailedCrossStats = ref(null)
const lanesLoading = ref(false)

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
  story_teaser: { bg: 'bg-fuchsia-100 dark:bg-fuchsia-900/40', border: 'border-fuchsia-400', text: 'text-fuchsia-700 dark:text-fuchsia-300', dot: 'bg-fuchsia-500' },
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
  story_teaser: { label: 'Teaser', icon: '👉' },
}

// Status icons and labels
const statusMeta = {
  draft: { label: 'Entwurf', icon: '📝', color: 'text-gray-500', bg: 'bg-gray-100 dark:bg-gray-700', badge: 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300' },
  scheduled: { label: 'Geplant', icon: '📅', color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-900/20', badge: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300' },
  in_review: { label: 'In Review', icon: '👁', color: 'text-orange-500', bg: 'bg-orange-50 dark:bg-orange-900/20', badge: 'bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300' },
  reminded: { label: 'Erinnert', icon: '🔔', color: 'text-yellow-500', bg: 'bg-yellow-50 dark:bg-yellow-900/20', badge: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300' },
  exported: { label: 'Exportiert', icon: '📤', color: 'text-green-500', bg: 'bg-green-50 dark:bg-green-900/20', badge: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300' },
  posted: { label: 'Veroeffentlicht', icon: '✅', color: 'text-emerald-500', bg: 'bg-emerald-50 dark:bg-emerald-900/20', badge: 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300' },
  archived: { label: 'Archiviert', icon: '📦', color: 'text-slate-400', bg: 'bg-slate-50 dark:bg-slate-900/20', badge: 'bg-slate-100 dark:bg-slate-900/40 text-slate-600 dark:text-slate-400' },
}

// Status transition rules (which statuses a post can move to)
const statusTransitions = {
  draft: ['scheduled', 'in_review', 'archived'],
  scheduled: ['draft', 'in_review', 'exported', 'archived'],
  in_review: ['draft', 'scheduled', 'exported', 'archived'],
  reminded: ['scheduled', 'in_review', 'exported', 'posted', 'archived'],
  exported: ['scheduled', 'in_review', 'posted', 'archived'],
  posted: ['archived'],
  archived: ['draft'],
}

// Status filter: which statuses to show in calendar
const statusFilter = ref(new Set(['draft', 'scheduled', 'in_review', 'reminded', 'exported', 'posted']))

// Status change dropdown state
const statusDropdownPost = ref(null) // post ID that has dropdown open
const showBatchStatusMenu = ref(false)

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
// Helper to filter posts by status filter
function filterPostsByStatus(posts) {
  if (!posts || posts.length === 0) return []
  return posts.filter(p => statusFilter.value.has(p.status || 'draft'))
}

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
      posts: filterPostsByStatus(postsByDate.value[dateStr] || []),
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
      posts: filterPostsByStatus(postsByDate.value[dateStr] || []),
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
      posts: filterPostsByStatus(postsByDate.value[dateStr] || []),
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
    const { data } = await api.get(url)
    postsByDate.value = data.posts_by_date || {}
    totalPosts.value = data.total_posts || 0
  } catch (err) {
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
    const { data } = await api.get(url)
    weekPostsByDate.value = data.posts_by_date || {}
    weekStartDate.value = data.start_date || null
    weekEndDate.value = data.end_date || null
  } catch (err) {
    error.value = 'Wochenansicht konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

// Fetch unscheduled drafts for sidebar
async function fetchUnscheduled() {
  loadingUnscheduled.value = true
  try {
    const { data } = await api.get('/api/calendar/unscheduled')
    unscheduledPosts.value = data.posts || []
  } catch (err) {
    // Error toast shown by interceptor
  } finally {
    loadingUnscheduled.value = false
  }
}

// Fetch gap dates for the current month
async function fetchGaps() {
  try {
    const { data } = await api.get(`/api/calendar/gaps?month=${currentMonth.value}&year=${currentYear.value}`)
    gapDates.value = new Set(data.gaps || [])
  } catch (err) {
    // Error toast shown by interceptor
  }
}

// Fetch recycling suggestions for gap days in current month
async function fetchRecyclingSuggestions() {
  try {
    const { data } = await api.get(`/api/recycling/calendar-suggestions?month=${currentMonth.value}&year=${currentYear.value}`)
    const map = {}
    for (const s of (data.suggestions || [])) {
      if (s.suggested_post) {
        map[s.gap_date] = s.suggested_post
      }
    }
    recyclingSuggestions.value = map
  } catch (err) {
    recyclingSuggestions.value = {}
  }
}

// Fetch arc timeline data for the current month
async function fetchArcTimeline() {
  if (!showArcTimeline.value) return
  try {
    const { data } = await api.get(`/api/calendar/arc-timeline?month=${currentMonth.value}&year=${currentYear.value}`)
    arcTimelineData.value = data.arcs || []
  } catch (err) {
    arcTimelineData.value = []
  }
}

// Compute arc timeline rows for the month grid
// Each arc becomes a horizontal bar spanning from its first to last episode date
// Multiple arcs can overlap so we assign rows to avoid visual collision
const arcTimelineRows = computed(() => {
  if (!showArcTimeline.value || arcTimelineData.value.length === 0) return []

  const days = calendarDays.value
  if (!days || days.length === 0) return []

  const firstDateStr = days[0].dateStr
  const lastDateStr = days[days.length - 1].dateStr

  const rows = []

  for (const arc of arcTimelineData.value) {
    // Clamp arc start/end to visible range
    const arcStart = arc.start_date < firstDateStr ? firstDateStr : arc.start_date
    const arcEnd = arc.end_date > lastDateStr ? lastDateStr : arc.end_date

    // Find column indices in the 42-cell grid
    const startIdx = days.findIndex(d => d.dateStr >= arcStart)
    const endIdx = days.findIndex(d => d.dateStr > arcEnd)
    const actualEndIdx = endIdx === -1 ? days.length - 1 : endIdx - 1

    if (startIdx === -1 || startIdx > actualEndIdx) continue

    // Find episode positions within the grid
    const episodePositions = []
    for (const ep of arc.episodes) {
      const epIdx = days.findIndex(d => d.dateStr === ep.scheduled_date)
      if (epIdx >= 0) {
        episodePositions.push({
          ...ep,
          colIndex: epIdx,
        })
      }
    }

    rows.push({
      arc,
      startCol: startIdx,
      endCol: actualEndIdx,
      spanCols: actualEndIdx - startIdx + 1,
      episodes: episodePositions,
    })
  }

  return rows
})

// Status color map for episode dots
const episodeStatusColors = {
  draft: '#9CA3AF',      // gray
  scheduled: '#3B82F6',  // blue
  reminded: '#F59E0B',   // amber
  exported: '#10B981',   // green
  posted: '#059669',     // emerald
}

function getEpisodeStatusColor(status) {
  return episodeStatusColors[status] || '#9CA3AF'
}

// Status labels for episodes
const episodeStatusLabels = {
  draft: 'Entwurf',
  scheduled: 'Geplant',
  reminded: 'Erinnert',
  exported: 'Exportiert',
  posted: 'Veroeffentlicht',
}

function showEpisodeTooltip(event, arc, episode) {
  const rect = event.target.getBoundingClientRect()
  tooltipPosition.value = {
    x: rect.left + rect.width / 2,
    y: rect.top - 8,
  }
  hoveredEpisode.value = { arc, episode }
}

function hideEpisodeTooltip() {
  hoveredEpisode.value = null
}

function onEpisodeClick(episode) {
  hideEpisodeTooltip()
  if (episode.id) {
    router.push(`/create/post/${episode.id}/edit`)
  }
}

// Get recycling suggestion for a specific date
function getRecyclingSuggestion(dateStr) {
  if (!showRecyclingSuggestions.value) return null
  return recyclingSuggestions.value[dateStr] || null
}

// Fetch seasonal markers (Bewerbungsfristen, Abflugzeiten, Schuljahresbeginn, etc.)
// Merges backend API markers with frontend seasonalCalendar.js config for richer data.
async function fetchSeasonalMarkers() {
  // Get markers from the frontend seasonal calendar config
  const configMarkers = toSeasonalMarkers(currentMonth.value, currentYear.value)

  try {
    const { data } = await api.get(`/api/calendar/seasonal-markers?month=${currentMonth.value}&year=${currentYear.value}`)
    const apiMarkers = data.markers || []

    // Merge: use API markers as base, add config markers that don't overlap (by date+label)
    const existingKeys = new Set(apiMarkers.map(m => `${m.date}|${m.label}`))
    const uniqueConfigMarkers = configMarkers.filter(m => !existingKeys.has(`${m.date}|${m.label}`))
    seasonalMarkers.value = [...apiMarkers, ...uniqueConfigMarkers]
  } catch (err) {
    // Fallback to config-only markers if API fails
    seasonalMarkers.value = configMarkers
  }
}

// Get seasonal markers for a specific date
function getMarkersForDate(dateStr) {
  if (!showSeasonalMarkers.value) return []
  return seasonalMarkers.value.filter(m => m.date === dateStr)
}

// Fetch recurring format placeholders
async function fetchRecurringPlaceholders() {
  try {
    const { data } = await api.get(`/api/calendar/recurring-placeholders?month=${currentMonth.value}&year=${currentYear.value}`)
    recurringPlaceholders.value = data.placeholders || []
  } catch (err) {
    recurringPlaceholders.value = []
  }
}

// Get recurring format placeholders for a specific date
function getRecurringForDate(dateStr) {
  if (!showRecurringFormats.value) return []
  return recurringPlaceholders.value.filter(p => p.date === dateStr && !p.has_existing_post)
}

// Seasonal marker color mapping
const markerColorClasses = {
  red: { bg: 'bg-red-100 dark:bg-red-900/40', text: 'text-red-700 dark:text-red-300', border: 'border-red-400', dot: 'bg-red-500', badge: 'bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200' },
  blue: { bg: 'bg-blue-100 dark:bg-blue-900/40', text: 'text-blue-700 dark:text-blue-300', border: 'border-blue-400', dot: 'bg-blue-500', badge: 'bg-blue-200 dark:bg-blue-800 text-blue-800 dark:text-blue-200' },
  green: { bg: 'bg-green-100 dark:bg-green-900/40', text: 'text-green-700 dark:text-green-300', border: 'border-green-400', dot: 'bg-green-500', badge: 'bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200' },
  purple: { bg: 'bg-purple-100 dark:bg-purple-900/40', text: 'text-purple-700 dark:text-purple-300', border: 'border-purple-400', dot: 'bg-purple-500', badge: 'bg-purple-200 dark:bg-purple-800 text-purple-800 dark:text-purple-200' },
  amber: { bg: 'bg-amber-100 dark:bg-amber-900/40', text: 'text-amber-700 dark:text-amber-300', border: 'border-amber-400', dot: 'bg-amber-500', badge: 'bg-amber-200 dark:bg-amber-800 text-amber-800 dark:text-amber-200' },
  teal: { bg: 'bg-teal-100 dark:bg-teal-900/40', text: 'text-teal-700 dark:text-teal-300', border: 'border-teal-400', dot: 'bg-teal-500', badge: 'bg-teal-200 dark:bg-teal-800 text-teal-800 dark:text-teal-200' },
}

function getMarkerColorClasses(color) {
  return markerColorClasses[color] || markerColorClasses.red
}

// Fetch goal stats
async function fetchStats() {
  try {
    const { data } = await api.get('/api/calendar/stats')
    goalStats.value = data
  } catch (err) {
    // Error toast shown by interceptor
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
    const { data } = await api.get(url)
    queuePosts.value = data.posts || []
    queueCount.value = data.count || 0
  } catch (err) {
    error.value = 'Warteschlange konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

// Fetch platform lanes data
async function fetchPlatformLanes() {
  lanesLoading.value = true
  try {
    const { data } = await api.get(`/api/calendar/platform-lanes?month=${currentMonth.value}&year=${currentYear.value}`)
    platformLanes.value = data.lanes || []
    crossPlatformStats.value = data.cross_platform_stats || {}
  } catch (err) {
    platformLanes.value = []
  } finally {
    lanesLoading.value = false
  }
}

// Fetch cross-platform stats
async function fetchCrossPlatformStats() {
  try {
    const { data } = await api.get(`/api/calendar/cross-platform-stats?month=${currentMonth.value}&year=${currentYear.value}`)
    detailedCrossStats.value = data
  } catch (err) {
    // Error toast shown by interceptor
  }
}

// Computed: platform lanes calendar days (same as month grid but per platform)
const lanesCalendarDays = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value
  const firstDayOfMonth = new Date(year, month - 1, 1)
  let startDow = firstDayOfMonth.getDay()
  startDow = startDow === 0 ? 6 : startDow - 1
  const daysInMonth = new Date(year, month, 0).getDate()
  const prevMonth = month === 1 ? 12 : month - 1
  const prevYear = month === 1 ? year - 1 : year
  const daysInPrevMonth = new Date(prevYear, prevMonth, 0).getDate()
  const today = new Date()
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  const days = []

  // Previous month's trailing days
  for (let i = startDow - 1; i >= 0; i--) {
    const day = daysInPrevMonth - i
    const dateStr = `${prevYear}-${String(prevMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    days.push({ day, dateStr, isCurrentMonth: false, isToday: dateStr === todayStr })
  }
  // Current month days
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    days.push({ day: d, dateStr, isCurrentMonth: true, isToday: dateStr === todayStr })
  }
  // Fill remaining cells to complete full weeks
  const nextMonth = month === 12 ? 1 : month + 1
  const nextYear = month === 12 ? year + 1 : year
  let nextDay = 1
  while (days.length % 7 !== 0 || days.length < 35) {
    const dateStr = `${nextYear}-${String(nextMonth).padStart(2, '0')}-${String(nextDay).padStart(2, '0')}`
    days.push({ day: nextDay, dateStr, isCurrentMonth: false, isToday: dateStr === todayStr })
    nextDay++
    if (days.length >= 42) break
  }

  return days
})

// Get posts for a specific platform and date in lanes view
function getLanePostsForDate(lane, dateStr) {
  if (!lane || !lane.posts_by_date) return []
  return lane.posts_by_date[dateStr] || []
}

// Unified fetch based on current view mode
function fetchData() {
  fetchStats()
  if (viewMode.value === 'month') {
    fetchCalendar()
    fetchGaps()
    fetchSeasonalMarkers()
    fetchRecyclingSuggestions()
    fetchArcTimeline()
    fetchRecurringPlaceholders()
  } else if (viewMode.value === 'week') {
    fetchWeek()
  } else if (viewMode.value === 'lanes') {
    fetchPlatformLanes()
    fetchCrossPlatformStats()
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

// Episode order validation state
const episodeConflicts = ref([])
const episodeWarnings = ref([])
const episodeInfo = ref(null)
const shiftFollowing = ref(false)
const validatingOrder = ref(false)

// ========== MULTI-SELECT FUNCTIONS ==========

function togglePostSelection(post, event) {
  if (event) event.stopPropagation()
  const id = post.id
  const newSet = new Set(selectedPostIds.value)
  if (newSet.has(id)) {
    newSet.delete(id)
  } else {
    newSet.add(id)
  }
  selectedPostIds.value = newSet
  // Auto-enable multi-select mode when 2+ selected
  if (newSet.size >= 2) {
    isMultiSelectMode.value = true
  } else if (newSet.size === 0) {
    isMultiSelectMode.value = false
  }
}

function isPostSelected(postId) {
  return selectedPostIds.value.has(postId)
}

function clearSelection() {
  selectedPostIds.value = new Set()
  isMultiSelectMode.value = false
}

function selectAllPostsOnDate(dateStr) {
  const posts = postsByDate.value[dateStr] || []
  const newSet = new Set(selectedPostIds.value)
  posts.forEach(p => newSet.add(p.id))
  selectedPostIds.value = newSet
  if (newSet.size >= 2) isMultiSelectMode.value = true
}

// Get all selected posts as objects
const selectedPosts = computed(() => {
  if (selectedPostIds.value.size === 0) return []
  const allPosts = []
  Object.values(postsByDate.value).forEach(datePosts => {
    datePosts.forEach(p => {
      if (selectedPostIds.value.has(p.id)) allPosts.push(p)
    })
  })
  // Also check unscheduled posts
  unscheduledPosts.value.forEach(p => {
    if (selectedPostIds.value.has(p.id)) allPosts.push(p)
  })
  return allPosts
})

function openMultiMoveDialog() {
  if (selectedPostIds.value.size === 0) return
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  multiMoveTargetDate.value = tomorrow.toISOString().split('T')[0]
  multiMoveTime.value = '10:00'
  showMultiMoveDialog.value = true
}

async function confirmMultiMove() {
  if (!multiMoveTargetDate.value || selectedPostIds.value.size === 0) return
  if (isPastDate(multiMoveTargetDate.value)) return

  const postsToMove = [...selectedPosts.value]
  const targetDate = multiMoveTargetDate.value
  const targetTime = multiMoveTime.value

  // Optimistic update: store originals and immediately move posts in UI
  const originals = postsToMove.map(p => ({
    id: p.id,
    scheduled_date: p.scheduled_date,
    scheduled_time: p.scheduled_time,
    status: p.status,
  }))

  // Apply optimistic update
  postsToMove.forEach(p => {
    optimisticMovePost(p, targetDate, targetTime)
  })

  showMultiMoveDialog.value = false
  const movedCount = postsToMove.length
  toast.info(`${movedCount} Posts werden verschoben...`)

  // Send API requests
  let failedCount = 0
  const results = await Promise.allSettled(
    postsToMove.map(p =>
      api.put(`/api/posts/${p.id}/schedule`, {
        scheduled_date: targetDate,
        scheduled_time: targetTime,
      })
    )
  )

  results.forEach((result, idx) => {
    if (result.status === 'rejected') {
      failedCount++
      // Rollback this post
      rollbackPost(originals[idx])
    }
  })

  // Refresh data to ensure consistency
  await Promise.all([fetchData(), fetchUnscheduled()])

  if (failedCount === 0) {
    toast.success(`${movedCount} Posts erfolgreich verschoben`)
  } else {
    toast.error(`${failedCount} von ${movedCount} Posts konnten nicht verschoben werden`)
  }

  clearSelection()
}

function cancelMultiMoveDialog() {
  showMultiMoveDialog.value = false
}

// ========== STATUS MANAGEMENT ==========

function toggleStatusFilter(status) {
  const newSet = new Set(statusFilter.value)
  if (newSet.has(status)) {
    // Don't allow hiding all statuses
    if (newSet.size > 1) newSet.delete(status)
  } else {
    newSet.add(status)
  }
  statusFilter.value = newSet
}

function isStatusVisible(status) {
  return statusFilter.value.has(status)
}

function getAvailableTransitions(currentStatus) {
  return statusTransitions[currentStatus] || []
}

function toggleStatusDropdown(postId) {
  statusDropdownPost.value = statusDropdownPost.value === postId ? null : postId
}

async function changePostStatus(post, newStatus) {
  statusDropdownPost.value = null
  try {
    await api.put(`/api/posts/${post.id}/status`, { status: newStatus })
    // Update locally
    post.status = newStatus
    toast.success(`Status geaendert: ${getStatusMeta(newStatus).label}`)
    // Refresh to keep everything in sync
    await fetchData()
  } catch (err) {
    // Error toast shown by interceptor
  }
}

async function batchChangeStatus(newStatus) {
  if (selectedPostIds.value.size === 0) return
  const postIds = [...selectedPostIds.value]
  try {
    const { data: result } = await api.put('/api/posts/batch-status', { post_ids: postIds, status: newStatus })
    if (result.updated_count > 0) {
      toast.success(`${result.updated_count} Posts auf "${getStatusMeta(newStatus).label}" geaendert`)
    }
    if (result.skipped_count > 0) {
      toast.warning(`${result.skipped_count} Posts uebersprungen (Statuswechsel nicht erlaubt)`)
    }
    clearSelection()
    await fetchData()
  } catch (err) {
    // Error toast shown by interceptor
  }
}

// Compute status overview counts from current calendar data
const statusOverview = computed(() => {
  const counts = {}
  Object.values(postsByDate.value).forEach(posts => {
    posts.forEach(p => {
      const s = p.status || 'draft'
      counts[s] = (counts[s] || 0) + 1
    })
  })
  return counts
})

// ========== OPTIMISTIC UPDATE HELPERS ==========

function optimisticMovePost(post, newDate, newTime) {
  // Remove from old date in postsByDate
  const oldDateStr = post.scheduled_date
  if (oldDateStr && postsByDate.value[oldDateStr]) {
    postsByDate.value[oldDateStr] = postsByDate.value[oldDateStr].filter(p => p.id !== post.id)
  }
  // Remove from unscheduled
  unscheduledPosts.value = unscheduledPosts.value.filter(p => p.id !== post.id)

  // Add to new date
  if (!postsByDate.value[newDate]) {
    postsByDate.value[newDate] = []
  }
  const movedPost = { ...post, scheduled_date: newDate, scheduled_time: newTime, status: 'scheduled' }
  postsByDate.value[newDate].push(movedPost)
}

function rollbackPost(original) {
  // Remove from all dates (it might be in the wrong place)
  Object.keys(postsByDate.value).forEach(dateStr => {
    postsByDate.value[dateStr] = postsByDate.value[dateStr].filter(p => p.id !== original.id)
  })
  // Re-add to original date or unscheduled
  if (original.scheduled_date) {
    if (!postsByDate.value[original.scheduled_date]) {
      postsByDate.value[original.scheduled_date] = []
    }
    postsByDate.value[original.scheduled_date].push({
      id: original.id,
      scheduled_date: original.scheduled_date,
      scheduled_time: original.scheduled_time,
      status: original.status,
    })
  }
}

// ========== DRAG AND DROP ==========

function onDragStart(event, post) {
  // If multi-select mode and this post is selected, drag all selected
  if (isMultiSelectMode.value && isPostSelected(post.id) && selectedPostIds.value.size > 1) {
    draggedPost.value = { ...post, _isMultiDrag: true, _selectedIds: [...selectedPostIds.value] }
    event.dataTransfer.setData('text/plain', JSON.stringify({ postIds: [...selectedPostIds.value] }))
  } else {
    draggedPost.value = post
    event.dataTransfer.setData('text/plain', JSON.stringify({ postId: post.id }))
  }
  event.dataTransfer.effectAllowed = 'move'
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

async function onDrop(event, dateStr) {
  event.preventDefault()
  dragOverDate.value = null
  if (!draggedPost.value) return

  // Prevent scheduling on past dates
  if (isPastDate(dateStr)) return

  // Multi-drag: if multiple posts selected, open multi-move dialog
  if (draggedPost.value._isMultiDrag && draggedPost.value._selectedIds?.length > 1) {
    multiMoveTargetDate.value = dateStr
    multiMoveTime.value = '10:00'
    showMultiMoveDialog.value = true
    draggedPost.value = null
    return
  }

  schedulingPost.value = draggedPost.value
  scheduleTargetDate.value = dateStr
  // Keep existing time if post already has one, else default to 10:00
  scheduleTime.value = draggedPost.value.scheduled_time || '10:00'
  scheduleError.value = null
  episodeConflicts.value = []
  episodeWarnings.value = []
  episodeInfo.value = null
  shiftFollowing.value = false
  showTimeDialog.value = true

  // If post is part of a story arc, validate episode order
  if (draggedPost.value.story_arc_id) {
    await validateEpisodeOrder(draggedPost.value.id, dateStr)
  }

  draggedPost.value = null
}

// Validate episode order when scheduling arc episodes
async function validateEpisodeOrder(postId, targetDate) {
  validatingOrder.value = true
  try {
    const { data } = await api.post('/api/calendar/validate-episode-order', {
      post_id: postId,
      target_date: targetDate,
    })
    episodeConflicts.value = data.conflicts || []
    episodeWarnings.value = data.warnings || []
    episodeInfo.value = data.episode_info || null
  } catch (err) {
    // Error toast shown by interceptor
  } finally {
    validatingOrder.value = false
  }
}

async function confirmSchedule() {
  if (!schedulingPost.value || !scheduleTargetDate.value) return

  // Prevent scheduling on past dates
  if (isPastDate(scheduleTargetDate.value)) {
    scheduleError.value = 'Vergangene Daten koennen nicht ausgewaehlt werden.'
    return
  }

  scheduleError.value = null

  // Store original state for rollback
  const post = schedulingPost.value
  const originalState = {
    id: post.id,
    scheduled_date: post.scheduled_date,
    scheduled_time: post.scheduled_time,
    status: post.status,
  }
  const newDate = scheduleTargetDate.value
  const newTime = scheduleTime.value

  // Optimistic update: immediately move post in UI
  optimisticMovePost(post, newDate, newTime)

  // Close dialog immediately for snappy UX
  showTimeDialog.value = false
  const postTitle = post.title || 'Unbenannt'

  try {
    // Use episode-aware scheduling for arc posts, regular for others
    const isArcPost = post.story_arc_id

    if (isArcPost) {
      // Re-open dialog for arc posts to handle conflicts
      // (optimistic update already applied, will rollback on failure)
      const { data } = await api.post('/api/calendar/schedule-episode', {
        post_id: post.id,
        scheduled_date: newDate,
        scheduled_time: newTime,
        force: episodeConflicts.value.length > 0,
        shift_following: shiftFollowing.value,
      })

      if (!data.success) {
        // Order conflict - rollback optimistic update and re-show dialog
        rollbackPost(originalState)
        scheduleError.value = data.message || 'Reihenfolge-Konflikt'
        episodeConflicts.value = data.conflicts || []
        episodeWarnings.value = data.warnings || []
        schedulingPost.value = post
        scheduleTargetDate.value = newDate
        scheduleTime.value = newTime
        showTimeDialog.value = true
        return
      }
    } else {
      // Regular scheduling for non-arc posts
      await api.put(`/api/posts/${post.id}/schedule`, {
        scheduled_date: newDate,
        scheduled_time: newTime,
      })
    }

    // Success! Show toast and refresh to ensure consistency
    toast.success(`"${postTitle}" auf ${formatDateForDisplay(newDate)} verschoben`)
    await Promise.all([fetchData(), fetchUnscheduled()])
  } catch (err) {
    // Rollback optimistic update on failure
    rollbackPost(originalState)
    // Refresh to ensure UI matches server state
    await Promise.all([fetchData(), fetchUnscheduled()])
  } finally {
    schedulingPost.value = null
    scheduleTargetDate.value = null
    scheduleError.value = null
    episodeConflicts.value = []
    episodeWarnings.value = []
    episodeInfo.value = null
    shiftFollowing.value = false
  }
}

function cancelScheduleDialog() {
  showTimeDialog.value = false
  schedulingPost.value = null
  scheduleTargetDate.value = null
  episodeConflicts.value = []
  episodeWarnings.value = []
  episodeInfo.value = null
  shiftFollowing.value = false
}

function formatDateForDisplay(dateStr) {
  if (!dateStr) return ''
  const parts = dateStr.split('-')
  return `${parts[2]}.${parts[1]}.${parts[0]}`
}

// Export calendar as CSV
async function exportCalendarCSV() {
  try {
    let url = `/api/calendar/export-csv?month=${currentMonth.value}&year=${currentYear.value}`
    if (platformFilter.value) {
      url += `&platform=${platformFilter.value}`
    }
    const res = await api.get(url, { responseType: 'blob' })

    // Extract filename from Content-Disposition header or use default
    const disposition = res.headers?.['content-disposition']
    let filename = `TREFF_calendar_${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}.csv`
    if (disposition) {
      const match = disposition.match(/filename="?([^"]+)"?/)
      if (match) filename = match[1]
    }

    // Trigger download
    const downloadUrl = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(downloadUrl)
  } catch (err) {
    error.value = 'CSV-Export fehlgeschlagen.'
  }
}

// Prev/Next navigation that respects view mode
function prevNav() {
  if (viewMode.value === 'month' || viewMode.value === 'lanes') {
    prevMonthNav()
  } else {
    prevWeekNav()
  }
}

function nextNav() {
  if (viewMode.value === 'month' || viewMode.value === 'lanes') {
    nextMonthNav()
  } else {
    nextWeekNav()
  }
}

// Computed: navigation label
const navLabel = computed(() => {
  if (viewMode.value === 'month' || viewMode.value === 'lanes') {
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
    fetchSeasonalMarkers()
    fetchRecyclingSuggestions()
    fetchArcTimeline()
  } else if (viewMode.value === 'lanes') {
    fetchPlatformLanes()
  }
})

// Watch weekDate changes (for week view)
watch(weekDate, () => {
  if (viewMode.value === 'week') {
    fetchWeek()
  }
})

// Re-validate episode order when date changes in scheduling dialog
watch(scheduleTargetDate, async (newDate) => {
  if (showTimeDialog.value && schedulingPost.value?.story_arc_id && newDate && !isPastDate(newDate)) {
    await validateEpisodeOrder(schedulingPost.value.id, newDate)
  }
})

// Workflow hints
const recurringFormatsCount = ref(-1)
async function checkRecurringFormats() {
  try {
    const { data } = await api.get('/api/recurring-formats')
    recurringFormatsCount.value = Array.isArray(data) ? data.length : 0
  } catch { recurringFormatsCount.value = 0 }
}
const showRecurringFormatsHint = computed(() => {
  return !loading.value && recurringFormatsCount.value === 0
})
const showWeekPlannerHint = computed(() => {
  return !loading.value && totalPosts.value === 0
})

// Close status dropdowns when clicking outside
function handleGlobalClick() {
  statusDropdownPost.value = null
  showBatchStatusMenu.value = false
}

onMounted(() => {
  fetchData()
  fetchUnscheduled()
  checkRecurringFormats()
  document.addEventListener('click', handleGlobalClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleGlobalClick)
})
</script>

<template>
  <div class="max-w-full overflow-hidden">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div class="flex items-center gap-3">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Content-Kalender</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {{ subtitleText }}
          </p>
        </div>
        <button
          @click="tourRef?.startTour()"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          title="Seiten-Tour starten"
        >
          &#10067; Tour
        </button>
      </div>

      <!-- Controls: platform filter + view toggle + navigation -->
      <div data-tour="cal-toolbar" class="flex items-center gap-3 flex-wrap max-w-full">
        <!-- Platform filter -->
        <div class="flex items-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg overflow-x-auto max-w-full">
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

        <!-- Status filter -->
        <div class="flex items-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg overflow-x-auto max-w-full">
          <button
            v-for="(meta, key) in statusMeta"
            :key="'sf-' + key"
            @click="toggleStatusFilter(key)"
            class="px-2 py-1.5 text-xs font-medium transition-colors whitespace-nowrap flex items-center gap-1"
            :class="isStatusVisible(key)
              ? meta.badge
              : 'text-gray-400 dark:text-gray-600 hover:text-gray-600 dark:hover:text-gray-400 line-through opacity-50'"
            :title="(isStatusVisible(key) ? 'Verbergen: ' : 'Anzeigen: ') + meta.label"
          >
            <span>{{ meta.icon }}</span>
            <span class="hidden sm:inline">{{ meta.label }}</span>
            <span v-if="statusOverview[key]" class="ml-0.5 text-[10px] font-bold">{{ statusOverview[key] }}</span>
          </button>
        </div>

        <!-- View mode toggle -->
        <div data-tour="cal-views" class="flex items-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
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
            @click="setViewMode('lanes')"
            class="px-3 py-1.5 text-sm font-medium transition-colors"
            :class="viewMode === 'lanes'
              ? 'bg-blue-600 text-white'
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'"
          >
            Lanes
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
          data-tour="cal-gaps"
          v-if="viewMode === 'month'"
          @click="showGaps = !showGaps"
          class="px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors flex items-center gap-1.5"
          :class="showGaps
            ? 'bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300 border-orange-300 dark:border-orange-600'
            : 'text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'"
          title="Posting-Luecken anzeigen/ausblenden"
          aria-label="Posting-Luecken anzeigen/ausblenden"
        >
          <span v-if="showGaps">&#9888;&#65039;</span><span v-else>&#128065;&#65039;</span>
          Luecken
          <HelpTooltip :text="tooltipTexts.calendar.gapDetection" size="sm" />
          <span v-if="showGaps && gapCount > 0" class="bg-orange-200 dark:bg-orange-800 text-orange-800 dark:text-orange-200 text-xs font-bold px-1.5 py-0.5 rounded-full">
            {{ gapCount }}
          </span>
        </button>

        <!-- Seasonal markers toggle (only in month view) -->
        <button
          data-tour="cal-seasonal"
          v-if="viewMode === 'month'"
          @click="showSeasonalMarkers = !showSeasonalMarkers"
          class="px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors flex items-center gap-1.5"
          :class="showSeasonalMarkers
            ? 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 border-red-300 dark:border-red-600'
            : 'text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'"
          title="Saisonale Markierungen anzeigen/ausblenden (Bewerbungsfristen, Abflugzeiten, etc.)"
          aria-label="Saisonale Markierungen anzeigen/ausblenden"
        >
          <span v-if="showSeasonalMarkers">📋</span><span v-else>📅</span>
          Fristen
          <HelpTooltip :text="tooltipTexts.calendar.seasonalMarkers" size="sm" />
          <span v-if="showSeasonalMarkers && seasonalMarkers.length > 0" class="bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200 text-xs font-bold px-1.5 py-0.5 rounded-full">
            {{ seasonalMarkers.length }}
          </span>
        </button>

        <!-- Story Arc Timeline toggle (only in month view) -->
        <button
          data-tour="cal-arcs"
          v-if="viewMode === 'month'"
          @click="showArcTimeline = !showArcTimeline; if (showArcTimeline) fetchArcTimeline()"
          class="px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors flex items-center gap-1.5"
          :class="showArcTimeline
            ? 'bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300 border-violet-300 dark:border-violet-600'
            : 'text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'"
          title="Story-Arc-Timeline anzeigen/ausblenden"
          aria-label="Story-Arc-Timeline anzeigen/ausblenden"
        >
          <span v-if="showArcTimeline">📖</span><span v-else>📕</span>
          Arcs
          <HelpTooltip :text="tooltipTexts.calendar.storyArcTimeline" size="sm" />
          <span v-if="showArcTimeline && arcTimelineData.length > 0" class="bg-violet-200 dark:bg-violet-800 text-violet-800 dark:text-violet-200 text-xs font-bold px-1.5 py-0.5 rounded-full">
            {{ arcTimelineData.length }}
          </span>
        </button>

        <!-- Recurring Formats toggle (only in month view) -->
        <button
          v-if="viewMode === 'month'"
          @click="showRecurringFormats = !showRecurringFormats; if (showRecurringFormats) fetchRecurringPlaceholders()"
          class="px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors flex items-center gap-1.5"
          :class="showRecurringFormats
            ? 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 border-indigo-300 dark:border-indigo-600'
            : 'text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'"
          title="Wiederkehrende Formate anzeigen/ausblenden"
          aria-label="Wiederkehrende Formate anzeigen/ausblenden"
        >
          <span>🔄</span>
          Formate
          <span v-if="showRecurringFormats && recurringPlaceholders.length > 0" class="bg-indigo-200 dark:bg-indigo-800 text-indigo-800 dark:text-indigo-200 text-xs font-bold px-1.5 py-0.5 rounded-full">
            {{ recurringPlaceholders.length }}
          </span>
        </button>

        <!-- Content-Mix toggle -->
        <button
          data-tour="cal-mix"
          @click="mixPanelCollapsed = !mixPanelCollapsed"
          class="px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors flex items-center gap-1.5"
          :class="!mixPanelCollapsed
            ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-600'
            : 'text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'"
          title="Content-Mix Analyse anzeigen/ausblenden"
          aria-label="Content-Mix Analyse anzeigen/ausblenden"
        >
          <span>📊</span>
          Mix
          <HelpTooltip :text="tooltipTexts.calendar.contentMix" size="sm" />
        </button>

        <!-- Export & Import Calendar button -->
        <button
          @click="showExportImport = true"
          class="px-3 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center gap-1.5"
          title="Kalender exportieren oder importieren"
          aria-label="Kalender exportieren oder importieren"
          data-tour="calendar-export-import"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Export / Import
        </button>

        <!-- Prev / Label / Next (hide in queue mode) -->
        <div v-if="viewMode !== 'queue'" class="flex items-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg">
          <button
            @click="prevNav"
            class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-l-lg transition-colors"
            :title="viewMode === 'month' ? 'Vorheriger Monat' : 'Vorherige Woche'"
            :aria-label="viewMode === 'month' ? 'Vorheriger Monat' : 'Vorherige Woche'"
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
            :aria-label="viewMode === 'month' ? 'Naechster Monat' : 'Naechste Woche'"
          >
            <svg class="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Weekly Goal Progress Indicator -->
    <BaseCard padding="md" :header-divider="false" class="mb-4">
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
    </BaseCard>

    <!-- Error state -->
    <div v-if="error" class="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400" role="alert">
      {{ error }}
    </div>

    <!-- Workflow Hints -->
    <WorkflowHint
      hint-id="calendar-recurring-formats"
      message="Keine wiederkehrenden Formate eingerichtet? Richte Formate ein, um deinen Kalender automatisch zu fuellen."
      link-text="Formate einrichten"
      link-to="/calendar/recurring-formats"
      icon="🔄"
      :show="showRecurringFormatsHint"
    />
    <WorkflowHint
      hint-id="calendar-week-planner"
      message="Dein Kalender ist noch leer. Nutze den KI-Wochenplaner, um schnell eine ganze Woche zu planen."
      link-text="Wochenplaner"
      link-to="/calendar/week-planner"
      icon="🗓️"
      :show="showWeekPlannerHint"
    />

    <!-- Loading state -->
    <div v-if="loading" class="flex flex-col md:flex-row gap-4">
      <!-- Skeleton: Sidebar -->
      <div class="flex-shrink-0 w-full md:w-64">
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-4 space-y-3">
          <SkeletonBase width="60%" height="1rem" />
          <SkeletonBase v-for="i in 3" :key="'side-sk-'+i" width="100%" height="3rem" rounded="lg" />
        </div>
      </div>
      <!-- Skeleton: Calendar Grid -->
      <div class="flex-1 bg-white dark:bg-gray-800 rounded-xl shadow-sm p-4">
        <!-- Month header -->
        <div class="flex items-center justify-between mb-4">
          <SkeletonBase width="8rem" height="1.5rem" />
          <div class="flex gap-2">
            <SkeletonBase width="2rem" height="2rem" rounded="lg" />
            <SkeletonBase width="2rem" height="2rem" rounded="lg" />
          </div>
        </div>
        <!-- Day headers -->
        <div class="grid grid-cols-7 gap-2 mb-2">
          <SkeletonBase v-for="i in 7" :key="'dh-sk-'+i" width="100%" height="1.5rem" />
        </div>
        <!-- Calendar cells (5 rows x 7 cols) -->
        <div class="grid grid-cols-7 gap-2">
          <SkeletonBase v-for="i in 35" :key="'cell-sk-'+i" width="100%" height="4rem" rounded="lg" />
        </div>
      </div>
    </div>

    <!-- Main layout: sidebar + calendar -->
    <div v-else class="flex flex-col md:flex-row gap-4">
      <!-- Unscheduled drafts sidebar -->
      <div
        data-tour="cal-sidebar"
        class="flex-shrink-0 transition-all duration-300"
        :class="[
          sidebarCollapsed ? 'w-10' : 'w-full md:w-64',
          'max-w-full'
        ]"
      >
        <!-- Collapse toggle -->
        <button
          @click="sidebarCollapsed = !sidebarCollapsed"
          class="w-full flex items-center justify-between px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-t-xl text-sm font-semibold text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          :title="sidebarCollapsed ? 'Seitenleiste einblenden' : 'Seitenleiste ausblenden'"
          :aria-label="sidebarCollapsed ? 'Seitenleiste einblenden' : 'Seitenleiste ausblenden'"
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
      <div data-tour="cal-grid" class="flex-1 min-w-0">

    <!-- ==================== MONTHLY VIEW ==================== -->
    <BaseCard v-if="viewMode === 'month'" padding="none" :header-divider="false">
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

      <!-- Story Arc Timeline Layer -->
      <div v-if="showArcTimeline && arcTimelineRows.length > 0" class="border-b border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/20 py-1.5">
        <div
          v-for="(row, rowIdx) in arcTimelineRows"
          :key="'arc-' + row.arc.id"
          class="grid grid-cols-7 mb-1 last:mb-0"
          :style="{ height: '26px' }"
        >
          <!-- Arc bar using CSS grid-column start/end for precise alignment -->
          <div
            class="relative rounded-full flex items-center overflow-visible mx-0.5"
            :style="{
              gridColumnStart: row.startCol + 1,
              gridColumnEnd: row.endCol + 2,
              height: '24px',
              backgroundColor: row.arc.color.light,
              border: '2px solid ' + row.arc.color.bg,
            }"
            :title="row.arc.title + ' (' + row.arc.total_episodes + ' Episoden, ' + row.arc.start_date + ' bis ' + row.arc.end_date + ')'"
          >
            <!-- Arc title (inside the bar) -->
            <span
              class="text-[11px] font-semibold truncate px-2 leading-none whitespace-nowrap pointer-events-none"
              :style="{ color: row.arc.color.text }"
            >
              {{ row.arc.title }}
              <span class="font-normal opacity-75">({{ row.arc.total_episodes }}/{{ row.arc.planned_episodes }})</span>
            </span>

            <!-- Episode dots on the bar -->
            <div
              v-for="ep in row.episodes"
              :key="'ep-' + ep.id"
              class="absolute cursor-pointer z-10 group"
              :style="{
                left: 'calc(' + ((ep.colIndex - row.startCol + 0.5) / row.spanCols * 100) + '% - 9px)',
                top: '1px',
                width: '18px',
                height: '18px',
              }"
              @mouseenter="showEpisodeTooltip($event, row.arc, ep)"
              @mouseleave="hideEpisodeTooltip"
              @click.stop="onEpisodeClick(ep)"
            >
              <div
                class="w-full h-full rounded-full border-2 border-white dark:border-gray-800 shadow-sm transition-transform group-hover:scale-125"
                :style="{ backgroundColor: getEpisodeStatusColor(ep.status) }"
              ></div>
            </div>
          </div>
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
              <!-- Recycling suggestion for gap days -->
              <span
                v-if="isGapDate(dayObj.dateStr, dayObj.isCurrentMonth) && getRecyclingSuggestion(dayObj.dateStr)"
                class="text-xs font-medium px-1.5 py-0.5 rounded-full bg-teal-100 dark:bg-teal-900/40 text-teal-600 dark:text-teal-400 cursor-pointer"
                :title="'Recycling-Vorschlag: ' + (getRecyclingSuggestion(dayObj.dateStr)?.title || '')"
              >
                &#9851;&#65039;
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

          <!-- Seasonal markers -->
          <div v-if="getMarkersForDate(dayObj.dateStr).length > 0" class="space-y-0.5 mb-1">
            <div
              v-for="(marker, mIdx) in getMarkersForDate(dayObj.dateStr)"
              :key="'marker-' + mIdx + '-' + dayObj.dateStr"
              class="rounded-md px-1.5 py-0.5 text-[10px] font-semibold border-l-[3px] flex items-center gap-1 seasonal-marker"
              :class="[
                getMarkerColorClasses(marker.color).bg,
                getMarkerColorClasses(marker.color).text,
                getMarkerColorClasses(marker.color).border,
              ]"
              :title="marker.description"
            >
              <span class="flex-shrink-0">{{ marker.icon }}</span>
              <span class="truncate">{{ marker.label }}</span>
            </div>
          </div>

          <!-- Recurring format placeholders -->
          <div v-if="getRecurringForDate(dayObj.dateStr).length > 0" class="space-y-0.5 mb-1">
            <div
              v-for="(rp, rpIdx) in getRecurringForDate(dayObj.dateStr)"
              :key="'rp-' + rpIdx + '-' + dayObj.dateStr"
              class="rounded-md px-1.5 py-0.5 text-[10px] font-medium border-l-[3px] flex items-center gap-1 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 border-indigo-400 cursor-pointer hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition-colors"
              :title="rp.format_name + (rp.preferred_time ? ' um ' + rp.preferred_time : '')"
              @click="$router.push('/create/quick')"
            >
              <span class="flex-shrink-0">{{ rp.format_icon || '🔄' }}</span>
              <span class="truncate">{{ rp.format_name }}</span>
            </div>
          </div>

          <!-- Post cards -->
          <div class="space-y-1">
            <div
              v-for="post in dayObj.posts.slice(0, 3)"
              :key="post.id"
              draggable="true"
              @dragstart="onDragStart($event, post)"
              @dragend="onDragEnd"
              @click.ctrl="togglePostSelection(post, $event)"
              @click.meta="togglePostSelection(post, $event)"
              class="rounded-md px-1.5 py-1 border-l-3 text-xs cursor-grab active:cursor-grabbing truncate"
              :class="[
                getCategoryStyle(post.category).bg,
                getCategoryStyle(post.category).text,
                'border-l-[3px]',
                getCategoryStyle(post.category).border,
                isPostSelected(post.id) ? 'ring-2 ring-blue-500 ring-offset-1' : '',
              ]"
              :title="`${post.title || 'Unbenannt'} - ${getCategoryLabel(post.category)} - ${getStatusMeta(post.status).label}${post.scheduled_time ? ' um ' + post.scheduled_time : ''}${post.episode_number ? ' (Episode ' + post.episode_number + ')' : ''} – ${isMultiSelectMode ? 'Cmd+Klick zum Aus-/Abwaehlen' : 'Cmd+Klick fuer Mehrfachauswahl'}`"
            >
              <div class="flex items-center gap-1">
                <!-- Selection checkbox in multi-select mode -->
                <input
                  v-if="isMultiSelectMode"
                  type="checkbox"
                  :checked="isPostSelected(post.id)"
                  @click.stop="togglePostSelection(post, $event)"
                  class="w-3 h-3 rounded border-gray-400 text-blue-600 focus:ring-blue-500 flex-shrink-0 cursor-pointer"
                />
                <span class="flex-shrink-0">{{ getCategoryIcon(post.category) }}</span>
                <span class="truncate font-medium">{{ post.title || 'Unbenannt' }}</span>
                <span
                  v-if="post.is_recurring_instance || post.recurring_rule_id"
                  class="flex-shrink-0 text-[10px] cursor-pointer hover:scale-125 transition-transform"
                  title="Wiederkehrender Post – Klicken fuer Einstellungen"
                  @click.stop="openRecurringSettings(post)"
                >🔁</span>
                <span
                  v-if="post.episode_number"
                  class="flex-shrink-0 ml-auto text-[9px] font-bold px-1 py-0 rounded bg-violet-200 dark:bg-violet-800 text-violet-700 dark:text-violet-300"
                  :title="'Episode ' + post.episode_number"
                >E{{ post.episode_number }}</span>
              </div>
              <div class="flex items-center gap-1 mt-0.5 opacity-75">
                <span class="flex-shrink-0 text-[10px]">{{ getPlatformIcon(post.platform) }}</span>
                <span v-if="post.scheduled_time" class="text-[10px]">{{ post.scheduled_time }}</span>
                <!-- Status badge with click-to-change dropdown -->
                <span class="ml-auto relative">
                  <button
                    @click.stop="toggleStatusDropdown(post.id)"
                    class="text-[10px] cursor-pointer hover:opacity-100 transition-opacity"
                    :class="getStatusMeta(post.status).color"
                    :title="'Status: ' + getStatusMeta(post.status).label + ' – Klicken zum Aendern'"
                  >
                    {{ getStatusMeta(post.status).icon }}
                  </button>
                  <!-- Status dropdown -->
                  <div
                    v-if="statusDropdownPost === post.id"
                    class="absolute right-0 bottom-full mb-1 z-30 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl py-1 min-w-[140px]"
                    @click.stop
                  >
                    <div class="px-2 py-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">Status aendern</div>
                    <button
                      v-for="nextStatus in getAvailableTransitions(post.status)"
                      :key="nextStatus"
                      @click.stop="changePostStatus(post, nextStatus)"
                      class="w-full px-3 py-1.5 text-left text-xs flex items-center gap-2 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                      :class="getStatusMeta(nextStatus).color"
                    >
                      <span>{{ getStatusMeta(nextStatus).icon }}</span>
                      <span>{{ getStatusMeta(nextStatus).label }}</span>
                    </button>
                    <div class="border-t border-gray-100 dark:border-gray-700 my-1"></div>
                    <button
                      @click.stop="statusDropdownPost = null; openRecurringSettings(post)"
                      class="w-full px-3 py-1.5 text-left text-xs flex items-center gap-2 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-blue-600 dark:text-blue-400"
                    >
                      <span>🔁</span>
                      <span>{{ post.recurring_rule_id ? 'Wiederkehr bearbeiten' : 'Wiederkehrend machen' }}</span>
                    </button>
                  </div>
                </span>
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
    </BaseCard>

    <!-- ==================== WEEKLY VIEW ==================== -->
    <BaseCard v-if="viewMode === 'week'" padding="none" :header-divider="false">
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
          class="py-1 px-1 border-r border-gray-200 dark:border-gray-700 last:border-r-0 min-h-[32px] transition-colors"
          :class="[
            day.isToday ? 'bg-blue-50/50 dark:bg-blue-900/10' : (idx >= 5 ? 'bg-gray-50/30 dark:bg-gray-800/30' : ''),
            dragOverDate === day.dateStr && !isPastDate(day.dateStr) ? 'bg-blue-50 dark:bg-blue-900/30 ring-2 ring-inset ring-blue-400' : '',
            isPastDate(day.dateStr) && draggedPost ? 'opacity-50 cursor-not-allowed' : '',
          ]"
          @dragover="onDragOver($event, day.dateStr)"
          @dragleave="onDragLeave($event, day.dateStr)"
          @drop="onDrop($event, day.dateStr)"
        >
          <div
            v-for="post in getAllDayPosts(day.dateStr)"
            :key="'allday-post-' + post.id"
            draggable="true"
            @dragstart="onDragStart($event, post)"
            @dragend="onDragEnd"
            class="rounded-md px-1.5 py-0.5 text-xs truncate mb-0.5 border-l-[3px] cursor-grab active:cursor-grabbing"
            :class="[
              getCategoryStyle(post.category).bg,
              getCategoryStyle(post.category).text,
              getCategoryStyle(post.category).border,
              isPostSelected(post.id) ? 'ring-2 ring-blue-500 ring-offset-1' : '',
            ]"
            :title="`${post.title || 'Unbenannt'} - ${getCategoryLabel(post.category)} - ${getStatusMeta(post.status).label}`"
            @click.ctrl="togglePostSelection(post, $event)"
            @click.meta="togglePostSelection(post, $event)"
          >
            <span class="flex-shrink-0">{{ getCategoryIcon(post.category) }}</span>
            <span class="truncate font-medium ml-1">{{ post.title || 'Unbenannt' }}</span>
          </div>
          <!-- Drop zone indicator for weekly all-day row -->
          <div
            v-if="draggedPost && dragOverDate === day.dateStr && !isPastDate(day.dateStr)"
            class="rounded-md border-2 border-dashed border-blue-400 bg-blue-50 dark:bg-blue-900/20 px-1 py-0.5 text-[10px] text-blue-600 dark:text-blue-400 text-center"
          >
            Ablegen
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
              dragOverDate === day.dateStr && !isPastDate(day.dateStr) ? 'bg-blue-50 dark:bg-blue-900/30 ring-2 ring-inset ring-blue-400' : '',
              isPastDate(day.dateStr) && draggedPost ? 'opacity-50 cursor-not-allowed' : '',
            ]"
            @dragover="onDragOver($event, day.dateStr)"
            @dragleave="onDragLeave($event, day.dateStr)"
            @drop="onDrop($event, day.dateStr)"
          >
            <div
              v-for="post in getPostsAtTimeSlot(day.dateStr, slot.hour)"
              :key="'wk-' + post.id"
              draggable="true"
              @dragstart="onDragStart($event, post)"
              @dragend="onDragEnd"
              class="rounded-md px-1.5 py-1 text-xs cursor-grab active:cursor-grabbing mb-0.5 border-l-[3px]"
              :class="[
                getCategoryStyle(post.category).bg,
                getCategoryStyle(post.category).text,
                getCategoryStyle(post.category).border,
                isPostSelected(post.id) ? 'ring-2 ring-blue-500 ring-offset-1' : '',
              ]"
              :title="`${post.title || 'Unbenannt'} - ${getCategoryLabel(post.category)} - ${getStatusMeta(post.status).label} - ${post.scheduled_time || ''}`"
              @click.ctrl="togglePostSelection(post, $event)"
              @click.meta="togglePostSelection(post, $event)"
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
    </BaseCard>

    <!-- ==================== PLATFORM LANES VIEW ==================== -->
    <div v-if="viewMode === 'lanes'" class="space-y-0">
      <!-- Cross-Platform Stats Summary -->
      <BaseCard v-if="crossPlatformStats && crossPlatformStats.total !== undefined" padding="md" :header-divider="false" class="mb-4">
        <div class="flex items-center gap-3 mb-3">
          <span class="text-lg">📊</span>
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Cross-Platform Statistik</h3>
          <span class="text-xs text-gray-500 dark:text-gray-400">{{ currentMonthLabel }}</span>
        </div>
        <!-- Platform count cards -->
        <div class="grid grid-cols-4 gap-3">
          <div class="text-center p-3 rounded-lg bg-gray-50 dark:bg-gray-700/30">
            <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ crossPlatformStats.total || 0 }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Gesamt</div>
          </div>
          <div class="text-center p-3 rounded-lg bg-pink-50 dark:bg-pink-900/20">
            <div class="text-2xl font-bold text-pink-600 dark:text-pink-400">{{ crossPlatformStats.instagram_feed || 0 }}</div>
            <div class="text-xs text-pink-600 dark:text-pink-400 mt-0.5">📷 IG Feed</div>
          </div>
          <div class="text-center p-3 rounded-lg bg-purple-50 dark:bg-purple-900/20">
            <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">{{ crossPlatformStats.instagram_story || 0 }}</div>
            <div class="text-xs text-purple-600 dark:text-purple-400 mt-0.5">📱 IG Story</div>
          </div>
          <div class="text-center p-3 rounded-lg bg-cyan-50 dark:bg-cyan-900/20">
            <div class="text-2xl font-bold text-cyan-600 dark:text-cyan-400">{{ crossPlatformStats.tiktok || 0 }}</div>
            <div class="text-xs text-cyan-600 dark:text-cyan-400 mt-0.5">🎵 TikTok</div>
          </div>
        </div>
        <!-- Platform distribution bars -->
        <div v-if="crossPlatformStats.total > 0" class="mt-3">
          <div class="flex h-3 rounded-full overflow-hidden bg-gray-100 dark:bg-gray-700">
            <div
              v-if="crossPlatformStats.instagram_feed"
              class="bg-pink-500"
              :style="{ width: Math.round((crossPlatformStats.instagram_feed / crossPlatformStats.total) * 100) + '%' }"
              :title="`IG Feed: ${Math.round((crossPlatformStats.instagram_feed / crossPlatformStats.total) * 100)}%`"
            ></div>
            <div
              v-if="crossPlatformStats.instagram_story"
              class="bg-purple-500"
              :style="{ width: Math.round((crossPlatformStats.instagram_story / crossPlatformStats.total) * 100) + '%' }"
              :title="`IG Story: ${Math.round((crossPlatformStats.instagram_story / crossPlatformStats.total) * 100)}%`"
            ></div>
            <div
              v-if="crossPlatformStats.tiktok"
              class="bg-cyan-500"
              :style="{ width: Math.round((crossPlatformStats.tiktok / crossPlatformStats.total) * 100) + '%' }"
              :title="`TikTok: ${Math.round((crossPlatformStats.tiktok / crossPlatformStats.total) * 100)}%`"
            ></div>
          </div>
          <div class="flex justify-between mt-1 text-[10px] text-gray-500 dark:text-gray-400">
            <span v-if="crossPlatformStats.instagram_feed">📷 {{ Math.round((crossPlatformStats.instagram_feed / crossPlatformStats.total) * 100) }}%</span>
            <span v-if="crossPlatformStats.instagram_story">📱 {{ Math.round((crossPlatformStats.instagram_story / crossPlatformStats.total) * 100) }}%</span>
            <span v-if="crossPlatformStats.tiktok">🎵 {{ Math.round((crossPlatformStats.tiktok / crossPlatformStats.total) * 100) }}%</span>
          </div>
        </div>
        <!-- Linked groups info -->
        <div v-if="crossPlatformStats.linked_groups > 0" class="mt-3 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
          <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 font-medium">
            🔗 {{ crossPlatformStats.linked_groups }} verknuepfte Gruppen
          </span>
          <span>Posts werden parallel auf mehreren Plattformen geplant</span>
        </div>
        <!-- Recommendations -->
        <div v-if="detailedCrossStats && detailedCrossStats.recommendations && detailedCrossStats.recommendations.length > 0" class="mt-3 space-y-1">
          <div
            v-for="(rec, rIdx) in detailedCrossStats.recommendations"
            :key="'rec-' + rIdx"
            class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300 text-xs"
          >
            <span>⚠️</span>
            <span>{{ rec.message }}</span>
          </div>
        </div>
        <!-- Multi-platform coverage -->
        <div v-if="detailedCrossStats && detailedCrossStats.multi_platform" class="mt-3 grid grid-cols-3 gap-2 text-center">
          <div class="p-2 rounded-lg bg-blue-50 dark:bg-blue-900/20">
            <div class="text-lg font-bold text-blue-600 dark:text-blue-400">{{ detailedCrossStats.multi_platform.linked_groups || 0 }}</div>
            <div class="text-[10px] text-blue-500 dark:text-blue-400">Verknuepfte Gruppen</div>
          </div>
          <div class="p-2 rounded-lg bg-green-50 dark:bg-green-900/20">
            <div class="text-lg font-bold text-green-600 dark:text-green-400">{{ detailedCrossStats.multi_platform.multi_platform_groups || 0 }}</div>
            <div class="text-[10px] text-green-500 dark:text-green-400">Multi-Plattform</div>
          </div>
          <div class="p-2 rounded-lg bg-violet-50 dark:bg-violet-900/20">
            <div class="text-lg font-bold text-violet-600 dark:text-violet-400">{{ detailedCrossStats.multi_platform.all_three_platforms || 0 }}</div>
            <div class="text-[10px] text-violet-500 dark:text-violet-400">Alle 3 Plattformen</div>
          </div>
        </div>
      </BaseCard>

      <!-- Platform Lanes Grid -->
      <BaseCard padding="none" :header-divider="false">
        <!-- Day headers (same as month view) -->
        <div class="grid grid-cols-[100px_repeat(7,1fr)] border-b border-gray-200 dark:border-gray-700">
          <div class="py-2 px-2 text-center text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 bg-gray-50 dark:bg-gray-800/50 border-r border-gray-200 dark:border-gray-700">
            Plattform
          </div>
          <div
            v-for="(dayName, idx) in dayNames"
            :key="'lane-header-' + idx"
            class="py-2 px-1 text-center text-xs font-semibold uppercase tracking-wider border-r border-gray-200 dark:border-gray-700 last:border-r-0"
            :class="idx >= 5 ? 'text-gray-400 dark:text-gray-500 bg-gray-50 dark:bg-gray-800/50' : 'text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800'"
          >
            {{ dayName }}
          </div>
        </div>

        <!-- One week at a time, with 3 platform rows per week -->
        <div
          v-for="weekIdx in Math.ceil(lanesCalendarDays.length / 7)"
          :key="'lane-week-' + weekIdx"
          class="border-b-2 border-gray-200 dark:border-gray-600 last:border-b-0"
        >
          <!-- Date number row -->
          <div class="grid grid-cols-[100px_repeat(7,1fr)] border-b border-gray-100 dark:border-gray-700/50">
            <div class="py-1 px-2 text-[10px] text-gray-400 dark:text-gray-500 bg-gray-50 dark:bg-gray-800/50 border-r border-gray-200 dark:border-gray-700 flex items-center justify-center font-medium">
              KW
            </div>
            <div
              v-for="(dayObj, dayIdx) in lanesCalendarDays.slice((weekIdx - 1) * 7, weekIdx * 7)"
              :key="'lane-date-' + dayObj.dateStr"
              class="py-1 px-1 text-center border-r border-gray-100 dark:border-gray-700/50 last:border-r-0"
              :class="[
                dayObj.isCurrentMonth ? 'bg-white dark:bg-gray-800' : 'bg-gray-50/50 dark:bg-gray-900/30',
                dayObj.isToday ? 'bg-blue-50 dark:bg-blue-900/20' : '',
              ]"
            >
              <span
                class="text-xs font-medium"
                :class="[
                  dayObj.isToday ? 'bg-blue-600 text-white rounded-full w-6 h-6 inline-flex items-center justify-center' : '',
                  dayObj.isCurrentMonth ? 'text-gray-700 dark:text-gray-300' : 'text-gray-400 dark:text-gray-600',
                ]"
              >{{ dayObj.day }}</span>
            </div>
          </div>

          <!-- Platform rows (3 rows: IG Feed, IG Story, TikTok) -->
          <div
            v-for="(lane, laneIdx) in platformLanes"
            :key="'lane-' + weekIdx + '-' + lane.platform"
            class="grid grid-cols-[100px_repeat(7,1fr)] border-b border-gray-100 dark:border-gray-700/30 last:border-b-0"
          >
            <!-- Platform label -->
            <div
              class="py-1.5 px-2 text-xs font-medium border-r border-gray-200 dark:border-gray-700 flex items-center gap-1.5"
              :class="[
                laneIdx === 0 ? 'bg-pink-50 dark:bg-pink-900/10 text-pink-700 dark:text-pink-300' : '',
                laneIdx === 1 ? 'bg-purple-50 dark:bg-purple-900/10 text-purple-700 dark:text-purple-300' : '',
                laneIdx === 2 ? 'bg-cyan-50 dark:bg-cyan-900/10 text-cyan-700 dark:text-cyan-300' : '',
              ]"
            >
              <span>{{ lane.icon }}</span>
              <span class="truncate">{{ lane.label }}</span>
              <span
                v-if="lane.total > 0"
                class="ml-auto text-[10px] font-bold px-1 py-0 rounded-full"
                :class="[
                  laneIdx === 0 ? 'bg-pink-200 dark:bg-pink-800 text-pink-700 dark:text-pink-300' : '',
                  laneIdx === 1 ? 'bg-purple-200 dark:bg-purple-800 text-purple-700 dark:text-purple-300' : '',
                  laneIdx === 2 ? 'bg-cyan-200 dark:bg-cyan-800 text-cyan-700 dark:text-cyan-300' : '',
                ]"
              >{{ lane.total }}</span>
            </div>

            <!-- Day cells for this platform -->
            <div
              v-for="(dayObj, dayIdx) in lanesCalendarDays.slice((weekIdx - 1) * 7, weekIdx * 7)"
              :key="'lane-cell-' + lane.platform + '-' + dayObj.dateStr"
              class="min-h-[40px] py-0.5 px-0.5 border-r border-gray-100 dark:border-gray-700/30 last:border-r-0"
              :class="[
                dayObj.isCurrentMonth ? 'bg-white dark:bg-gray-800' : 'bg-gray-50/30 dark:bg-gray-900/20',
                dayObj.isToday ? 'bg-blue-50/50 dark:bg-blue-900/10' : '',
                (dayIdx >= 5) ? 'bg-gray-50/20 dark:bg-gray-800/20' : '',
              ]"
            >
              <div
                v-for="post in getLanePostsForDate(lane, dayObj.dateStr)"
                :key="'lane-post-' + post.id"
                class="rounded px-1 py-0.5 text-[10px] cursor-pointer mb-0.5 border-l-2 truncate"
                :class="[
                  getCategoryStyle(post.category).bg,
                  getCategoryStyle(post.category).text,
                  getCategoryStyle(post.category).border,
                ]"
                :title="`${post.title || 'Unbenannt'} - ${getCategoryLabel(post.category)} - ${getStatusMeta(post.status).label}${post.scheduled_time ? ' um ' + post.scheduled_time : ''}${post.linked_post_group_id ? ' 🔗 Verknuepft' : ''}`"
                @click="router.push(`/create/post/${post.id}/edit`)"
              >
                <div class="flex items-center gap-0.5">
                  <span class="flex-shrink-0">{{ getCategoryIcon(post.category) }}</span>
                  <span class="truncate font-medium">{{ post.title || 'Unbenannt' }}</span>
                  <span
                    v-if="post.linked_post_group_id"
                    class="flex-shrink-0 ml-auto text-[9px]"
                    title="Verknuepfter Multi-Plattform Post"
                  >🔗</span>
                </div>
                <div v-if="post.scheduled_time" class="opacity-70 text-[9px]">
                  {{ post.scheduled_time }} {{ getStatusMeta(post.status).icon }}
                </div>
              </div>
              <!-- Empty state dot for days without posts -->
              <div
                v-if="getLanePostsForDate(lane, dayObj.dateStr).length === 0 && dayObj.isCurrentMonth"
                class="h-full flex items-center justify-center"
              >
                <span class="w-1.5 h-1.5 rounded-full bg-gray-200 dark:bg-gray-700"></span>
              </div>
            </div>
          </div>
        </div>
      </BaseCard>
    </div>

    <!-- ==================== QUEUE VIEW ==================== -->
    <BaseCard v-if="viewMode === 'queue'" padding="none" :header-divider="false">
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
          to="/create/quick"
          class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Post erstellen
        </router-link>
      </div>
    </BaseCard>

    <!-- Legend -->
    <BaseCard padding="md" :header-divider="false" class="mt-4">
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
        <div v-if="viewMode === 'month' && showSeasonalMarkers">
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Saisonale Markierungen</h3>
          <div class="flex flex-wrap gap-3">
            <div class="flex items-center gap-1.5">
              <span class="w-3 h-3 rounded-full bg-red-500"></span>
              <span class="text-xs text-gray-600 dark:text-gray-400">📋 Bewerbungsfristen</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-3 h-3 rounded-full bg-blue-500"></span>
              <span class="text-xs text-gray-600 dark:text-gray-400">✈️ Abflugzeiten</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-3 h-3 rounded-full bg-green-500"></span>
              <span class="text-xs text-gray-600 dark:text-gray-400">🏫 Schuljahresbeginn</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-3 h-3 rounded-full bg-purple-500"></span>
              <span class="text-xs text-gray-600 dark:text-gray-400">🏠 Rueckkehr</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-3 h-3 rounded-full bg-amber-500"></span>
              <span class="text-xs text-gray-600 dark:text-gray-400">🎓 Stipendien</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-3 h-3 rounded-full bg-teal-500"></span>
              <span class="text-xs text-gray-600 dark:text-gray-400">🎪 Messen</span>
            </div>
          </div>
        </div>
        <div v-if="viewMode === 'month' && showArcTimeline && arcTimelineData.length > 0">
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Story-Arcs</h3>
          <div class="flex flex-wrap gap-3">
            <div
              v-for="arc in arcTimelineData"
              :key="'legend-arc-' + arc.id"
              class="flex items-center gap-1.5"
            >
              <span
                class="w-3 h-3 rounded-full"
                :style="{ backgroundColor: arc.color.bg }"
              ></span>
              <span class="text-xs text-gray-600 dark:text-gray-400">{{ arc.title }} ({{ arc.total_episodes }}/{{ arc.planned_episodes }})</span>
            </div>
          </div>
          <div class="flex flex-wrap gap-3 mt-2">
            <div class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-full bg-gray-400"></span>
              <span class="text-[10px] text-gray-500 dark:text-gray-400">Entwurf</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
              <span class="text-[10px] text-gray-500 dark:text-gray-400">Geplant</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
              <span class="text-[10px] text-gray-500 dark:text-gray-400">Erinnert</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
              <span class="text-[10px] text-gray-500 dark:text-gray-400">Veroeffentlicht</span>
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
    </BaseCard>

    <!-- Empty state (not for queue view - it has its own) -->
    <EmptyState
      v-if="!loading && !error && viewMode !== 'queue' && viewMode !== 'lanes' && (viewMode === 'month' ? totalPosts === 0 : weekTotalPosts === 0)"
      class="mt-6"
      svgIcon="calendar-days"
      title="Dein Kalender ist noch leer"
      description="Nutze den KI-Wochenplaner, um automatisch Content fuer eine ganze Woche zu planen. Oder erstelle einzelne Posts und plane sie manuell ein."
      actionLabel="Zum Wochenplaner"
      actionTo="/calendar/week-planner"
      secondaryLabel="Post erstellen"
      secondaryTo="/create/quick"
    />

      </div><!-- end flex-1 calendar content area -->

      <!-- Content-Mix right sidebar -->
      <ContentMixPanel
        :collapsed="mixPanelCollapsed"
        @toggle="mixPanelCollapsed = !mixPanelCollapsed"
      />
    </div><!-- end flex gap-4 main layout -->

    <!-- Schedule time picker dialog (modal) -->
    <div
      v-if="showTimeDialog"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="cancelScheduleDialog"
    >
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 w-full max-w-md mx-4">
        <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-1">
          {{ schedulingPost?.story_arc_id ? 'Episode planen' : 'Post planen' }}
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
          {{ schedulingPost?.title || 'Unbenannt' }}
        </p>
        <!-- Episode badge if arc post -->
        <div v-if="schedulingPost?.story_arc_id && episodeInfo" class="mb-4">
          <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300">
            Episode {{ episodeInfo.episode_number || '?' }} von {{ episodeInfo.total_episodes }}
          </span>
        </div>
        <div v-else class="mb-4"></div>

        <!-- Date picker (only allows today and future dates) -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" for="schedule-date-input">Datum</label>
          <input
            id="schedule-date-input"
            v-model="scheduleTargetDate"
            type="date"
            :min="getTodayStr()"
            class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            :class="[
              isPastDate(scheduleTargetDate) ? 'border-red-400 dark:border-red-500' : '',
              episodeConflicts.length > 0 ? 'border-red-400 dark:border-red-500 ring-2 ring-red-200 dark:ring-red-800' : '',
              episodeWarnings.length > 0 && episodeConflicts.length === 0 ? 'border-amber-400 dark:border-amber-500' : '',
              !isPastDate(scheduleTargetDate) && episodeConflicts.length === 0 && episodeWarnings.length === 0 ? 'border-gray-300 dark:border-gray-600' : '',
            ]"
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

        <!-- Validation loading -->
        <div v-if="validatingOrder" class="mb-4 flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
          <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-violet-500"></div>
          Reihenfolge wird geprueft...
        </div>

        <!-- Episode order conflicts (hard errors) -->
        <div v-if="episodeConflicts.length > 0" class="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg" role="alert">
          <div class="flex items-center gap-2 mb-2">
            <svg class="w-5 h-5 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <span class="font-semibold text-sm text-red-700 dark:text-red-300">Reihenfolge-Konflikt</span>
          </div>
          <ul class="space-y-1.5">
            <li
              v-for="(conflict, cIdx) in episodeConflicts"
              :key="'conflict-' + cIdx"
              class="text-xs text-red-600 dark:text-red-400 flex items-start gap-1.5"
            >
              <span class="flex-shrink-0 mt-0.5">&#x274C;</span>
              <span>{{ conflict.message }}</span>
            </li>
          </ul>
        </div>

        <!-- Episode order warnings (soft - gap too small) -->
        <div v-if="episodeWarnings.length > 0 && episodeConflicts.length === 0" class="mb-4 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
          <div class="flex items-center gap-2 mb-2">
            <svg class="w-5 h-5 text-amber-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <span class="font-semibold text-sm text-amber-700 dark:text-amber-300">Abstandswarnung</span>
          </div>
          <ul class="space-y-1.5">
            <li
              v-for="(warning, wIdx) in episodeWarnings"
              :key="'warning-' + wIdx"
              class="text-xs text-amber-600 dark:text-amber-400 flex items-start gap-1.5"
            >
              <span class="flex-shrink-0 mt-0.5">&#x26A0;&#xFE0F;</span>
              <span>{{ warning.message }}</span>
            </li>
          </ul>
        </div>

        <!-- Shift following episodes option (only for arc posts that already have a scheduled date) -->
        <div v-if="schedulingPost?.story_arc_id && episodeInfo?.episode_number" class="mb-4">
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              v-model="shiftFollowing"
              class="w-4 h-4 rounded border-gray-300 dark:border-gray-600 text-violet-600 focus:ring-violet-500"
            />
            <span class="text-sm text-gray-700 dark:text-gray-300">
              Alle folgenden Episoden mit verschieben
            </span>
          </label>
          <p class="mt-1 ml-6 text-xs text-gray-500 dark:text-gray-400">
            Verschiebt Episode {{ (episodeInfo?.episode_number || 0) + 1 }}+ um den gleichen Zeitabstand.
          </p>
        </div>

        <!-- Error message -->
        <div v-if="scheduleError" class="mb-4 p-2 bg-red-50 dark:bg-red-900/30 rounded-lg" role="alert">
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
            :class="[
              isPastDate(scheduleTargetDate) ? 'bg-gray-400 cursor-not-allowed' : '',
              episodeConflicts.length > 0 && !isPastDate(scheduleTargetDate) ? 'bg-red-600 hover:bg-red-700' : '',
              episodeConflicts.length === 0 && !isPastDate(scheduleTargetDate) ? 'bg-blue-600 hover:bg-blue-700' : '',
            ]"
          >
            {{ episodeConflicts.length > 0 ? 'Trotzdem planen' : (schedulingPost?.story_arc_id ? 'Episode planen' : 'Post planen') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Multi-select floating toolbar -->
    <Teleport to="body">
      <Transition name="slide-up">
        <div
          v-if="selectedPostIds.size > 0"
          class="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 px-5 py-3 flex items-center gap-4"
          data-testid="multi-select-toolbar"
        >
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center">
              <span class="text-sm font-bold text-blue-700 dark:text-blue-300">{{ selectedPostIds.size }}</span>
            </div>
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
              {{ selectedPostIds.size === 1 ? 'Post' : 'Posts' }} ausgewaehlt
            </span>
          </div>
          <div class="h-6 w-px bg-gray-200 dark:bg-gray-700"></div>
          <button
            @click="openMultiMoveDialog"
            class="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
            Verschieben
          </button>
          <!-- Batch status change dropdown -->
          <div class="relative">
            <button
              @click="showBatchStatusMenu = !showBatchStatusMenu"
              class="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Status
              <svg class="w-3 h-3 ml-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
            <div
              v-if="showBatchStatusMenu"
              class="absolute bottom-full mb-2 left-0 z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl py-1 min-w-[160px]"
            >
              <div class="px-3 py-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">Alle auf Status setzen</div>
              <button
                v-for="(meta, key) in statusMeta"
                :key="'batch-' + key"
                @click="batchChangeStatus(key); showBatchStatusMenu = false"
                class="w-full px-3 py-1.5 text-left text-xs flex items-center gap-2 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                :class="meta.color"
              >
                <span>{{ meta.icon }}</span>
                <span>{{ meta.label }}</span>
              </button>
            </div>
          </div>
          <button
            @click="clearSelection"
            class="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            Abbrechen
          </button>
        </div>
      </Transition>
    </Teleport>

    <!-- Multi-move dialog (modal) -->
    <div
      v-if="showMultiMoveDialog"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="cancelMultiMoveDialog"
    >
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 w-full max-w-md mx-4">
        <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-1">
          {{ selectedPostIds.size }} Posts verschieben
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Alle ausgewaehlten Posts auf ein neues Datum verschieben.
        </p>

        <!-- Selected posts preview -->
        <div class="mb-4 max-h-[120px] overflow-y-auto space-y-1">
          <div
            v-for="post in selectedPosts"
            :key="'multi-' + post.id"
            class="flex items-center gap-2 px-2 py-1 rounded-md text-xs"
            :class="[getCategoryStyle(post.category).bg, getCategoryStyle(post.category).text]"
          >
            <span>{{ getCategoryIcon(post.category) }}</span>
            <span class="truncate font-medium">{{ post.title || 'Unbenannt' }}</span>
            <span class="ml-auto text-[10px] opacity-70">{{ post.scheduled_date || 'ungeplant' }}</span>
          </div>
        </div>

        <!-- Target date -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" for="multi-move-date">Neues Datum</label>
          <input
            id="multi-move-date"
            v-model="multiMoveTargetDate"
            type="date"
            :min="getTodayStr()"
            class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            :class="isPastDate(multiMoveTargetDate) ? 'border-red-400' : 'border-gray-300 dark:border-gray-600'"
          />
          <p v-if="isPastDate(multiMoveTargetDate)" class="mt-1 text-xs text-red-500 dark:text-red-400">
            Vergangene Daten koennen nicht ausgewaehlt werden.
          </p>
        </div>

        <!-- Target time -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" for="multi-move-time">Uhrzeit</label>
          <input
            id="multi-move-time"
            v-model="multiMoveTime"
            type="time"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <!-- Actions -->
        <div class="flex gap-3">
          <button
            @click="cancelMultiMoveDialog"
            class="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            Abbrechen
          </button>
          <button
            @click="confirmMultiMove"
            :disabled="isPastDate(multiMoveTargetDate)"
            class="flex-1 px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors"
            :class="isPastDate(multiMoveTargetDate) ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'"
          >
            {{ selectedPostIds.size }} Posts verschieben
          </button>
        </div>
      </div>
    </div>

    <!-- Episode Tooltip (floating, follows mouse) -->
    <Teleport to="body">
      <div
        v-if="hoveredEpisode"
        class="fixed z-[100] pointer-events-none"
        :style="{
          left: tooltipPosition.x + 'px',
          top: tooltipPosition.y + 'px',
          transform: 'translate(-50%, -100%)',
        }"
      >
        <div class="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-lg shadow-xl px-3 py-2 text-xs max-w-[260px]">
          <!-- Arc name -->
          <div class="font-bold text-[11px] mb-1 opacity-70">
            {{ hoveredEpisode.arc.title }}
          </div>
          <!-- Episode title -->
          <div class="font-semibold mb-1">
            {{ hoveredEpisode.episode.title }}
          </div>
          <!-- Episode details -->
          <div class="flex flex-col gap-0.5">
            <span>Episode {{ hoveredEpisode.episode.episode_number }} von {{ hoveredEpisode.arc.planned_episodes }}</span>
            <span>Datum: {{ hoveredEpisode.episode.scheduled_date }}{{ hoveredEpisode.episode.scheduled_time ? ' um ' + hoveredEpisode.episode.scheduled_time : '' }}</span>
            <span>Status: {{ episodeStatusLabels[hoveredEpisode.episode.status] || hoveredEpisode.episode.status }}</span>
          </div>
          <!-- Arrow -->
          <div class="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-l-transparent border-r-transparent border-t-gray-900 dark:border-t-gray-100"></div>
        </div>
      </div>
    </Teleport>
    <TourSystem ref="tourRef" page-key="calendar" />

    <!-- Export/Import Modal -->
    <CalendarExportImport
      :show="showExportImport"
      :month="currentMonth"
      :year="currentYear"
      :platform-filter="platformFilter"
      @close="showExportImport = false"
      @imported="fetchCalendarData(); showExportImport = false"
    />

    <!-- Recurring Post Settings Modal -->
    <RecurringPostSettings
      :show="showRecurringSettings"
      :post-id="recurringTargetPost?.id"
      :post-title="recurringTargetPost?.title || 'Unbenannt'"
      :post-scheduled-date="recurringTargetPost?.scheduled_date"
      @close="showRecurringSettings = false"
      @created="fetchCalendarData(); showRecurringSettings = false"
      @deleted="fetchCalendarData(); showRecurringSettings = false"
    />
  </div>
</template>

<style scoped>
/* Multi-select toolbar slide-up animation */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.25s ease-out;
}
.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
.slide-up-enter-to,
.slide-up-leave-from {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
</style>
