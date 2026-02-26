<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import api from '@/utils/api'
import AppIcon from '@/components/icons/AppIcon.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import TourSystem from '@/components/common/TourSystem.vue'
import WelcomeFlow from '@/components/common/WelcomeFlow.vue'
import RecyclingPanel from '@/components/dashboard/RecyclingPanel.vue'
import SeriesStatusWidget from '@/components/dashboard/SeriesStatusWidget.vue'
import ContentSuggestions from '@/components/dashboard/ContentSuggestions.vue'
import HelpTooltip from '@/components/common/HelpTooltip.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import ActivityHeatmap from '@/components/analytics/ActivityHeatmap.vue'
import ContentQueueWidget from '@/components/dashboard/ContentQueueWidget.vue'
import StudentInboxWidget from '@/components/dashboard/StudentInboxWidget.vue'
import PerformancePulseWidget from '@/components/dashboard/PerformancePulseWidget.vue'
import ActiveCampaignsWidget from '@/components/dashboard/ActiveCampaignsWidget.vue'
import PillarDistributionWidget from '@/components/dashboard/PillarDistributionWidget.vue'
import PipelineDashboardWidget from '@/components/pipeline/PipelineDashboardWidget.vue'
import SkeletonBase from '@/components/common/SkeletonBase.vue'
import SkeletonImage from '@/components/common/SkeletonImage.vue'
import { tooltipTexts } from '@/utils/tooltipTexts'
import { formatDate, formatDateShort } from '@/utils/dateUtils'

const router = useRouter()
const { execute: apiExecute, loading, error } = useApi()
const tourRef = ref(null)
const showWelcomeFlow = ref(false)
const welcomeCheckDone = ref(false)

// Dashboard data
const stats = ref({
  posts_this_week: 0,
  scheduled_posts: 0,
  draft_posts: 0,
  total_assets: 0,
  total_posts: 0,
})
const recentPosts = ref([])
const calendarEntries = ref([])
const suggestions = ref([])
const contentSuggestionsRef = ref(null)
const generatingSuggestions = ref(false)

// Dashboard 6-Widget-Architektur data
const widgetData = ref({
  content_queue: [],
  student_inbox: { items: [], total: 0 },
  performance_pulse: { weeks: [], goal: 3, trend: 'stable', current_week_count: 0 },
  active_campaigns: [],
})
const widgetsLoading = ref(false)

// Animated counters
const animatedStats = ref({
  posts_this_week: 0,
  scheduled_posts: 0,
  draft_posts: 0,
})

function animateCounter(target, key, duration = 800) {
  const start = animatedStats.value[key]
  const end = target
  if (start === end) return
  const startTime = Date.now()
  const tick = () => {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    // easeOutQuart for smooth deceleration
    const eased = 1 - Math.pow(1 - progress, 4)
    animatedStats.value[key] = Math.round(start + (end - start) * eased)
    if (progress < 1) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
}

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

// Status label in German
function statusLabel(status) {
  const labels = {
    draft: 'Entwurf',
    scheduled: 'Geplant',
    exported: 'Exportiert',
    posted: 'Gepostet',
    reminded: 'Erinnert',
  }
  return labels[status] || status
}

// Category display names
function categoryLabel(cat) {
  const labels = {
    laender_spotlight: 'Länder-Spotlight',
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

// Category colors for thumbnail grid
function categoryColor(cat) {
  const colors = {
    laender_spotlight: 'bg-blue-500',
    erfahrungsberichte: 'bg-purple-500',
    infografiken: 'bg-teal-500',
    fristen_cta: 'bg-red-500',
    tipps_tricks: 'bg-amber-500',
    faq: 'bg-indigo-500',
    foto_posts: 'bg-pink-500',
    reel_tiktok_thumbnails: 'bg-rose-500',
    story_posts: 'bg-violet-500',
  }
  return colors[cat] || 'bg-gray-500'
}

// Platform icon names (for AppIcon component)
function platformIcon(platform) {
  switch (platform) {
    case 'instagram_feed':
      return 'camera'
    case 'instagram_story':
      return 'device-mobile'
    case 'tiktok':
      return 'musical-note'
    default:
      return 'document-text'
  }
}

// Platform label
function platformLabel(platform) {
  switch (platform) {
    case 'instagram_feed':
      return 'Instagram Feed'
    case 'instagram_story':
      return 'Instagram Story'
    case 'tiktok':
      return 'TikTok'
    default:
      return 'Post'
  }
}

// formatDate and formatDateShort imported from @/utils/dateUtils

// Generate new AI content suggestions (delegates to ContentSuggestions component)
async function generateSuggestions() {
  if (contentSuggestionsRef.value && contentSuggestionsRef.value.generateSuggestions) {
    generatingSuggestions.value = true
    try {
      await contentSuggestionsRef.value.generateSuggestions()
    } finally {
      generatingSuggestions.value = false
    }
  }
}

async function fetchWidgetData() {
  widgetsLoading.value = true
  try {
    const res = await api.get('/api/analytics/dashboard-widgets')
    if (res.data) {
      widgetData.value = res.data
    }
  } catch {
    // Widget data is non-critical; fail silently
  } finally {
    widgetsLoading.value = false
  }
}

async function fetchDashboardData() {
  const result = await apiExecute(() => api.get('/api/analytics/dashboard'))
  if (result) {
    stats.value = result.stats
    recentPosts.value = result.recent_posts
    calendarEntries.value = result.calendar_entries
    suggestions.value = result.suggestions || []

    // Trigger animated counters after data load
    setTimeout(() => {
      animateCounter(stats.value.posts_this_week, 'posts_this_week')
      animateCounter(stats.value.scheduled_posts, 'scheduled_posts')
      animateCounter(stats.value.draft_posts || 0, 'draft_posts')
    }, 100)
  }
}

async function checkWelcomeStatus() {
  try {
    const res = await api.get('/api/settings')
    const settings = res.data
    // Check welcome flow first (shows before page-specific tour)
    if (!settings.welcome_completed || settings.welcome_completed === 'false') {
      showWelcomeFlow.value = true
    }
  } catch {
    // Non-critical: silently ignore (toast from interceptor if needed)
  } finally {
    welcomeCheckDone.value = true
  }
}

async function handleWelcomeComplete() {
  showWelcomeFlow.value = false
  // Fire-and-forget: errors handled by interceptor
  api.put('/api/settings', { welcome_completed: 'true' }).catch(() => {})
  setTimeout(() => { tourRef.value?.startTour() }, 400)
}

async function handleWelcomeSkip() {
  showWelcomeFlow.value = false
  api.put('/api/settings', { welcome_completed: 'true' }).catch(() => {})
  setTimeout(() => { tourRef.value?.startTour() }, 400)
}

// Current greeting based on time of day
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Guten Morgen'
  if (hour < 18) return 'Guten Tag'
  return 'Guten Abend'
})

// Current date display
const todayFormatted = computed(() => {
  return new Date().toLocaleDateString('de-DE', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
})

onMounted(() => {
  fetchDashboardData()
  fetchWidgetData()
  checkWelcomeStatus()
})
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <!-- Page Header -->
    <div class="mb-6 flex items-start justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ greeting }}!</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          {{ todayFormatted }} &mdash; Hier ist dein Content-Überblick.
        </p>
      </div>
      <button
        @click="tourRef?.startTour()"
        class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        title="Seiten-Tour starten"
      >
        <AppIcon name="help" class="w-4 h-4 inline" /> Tour starten
      </button>
    </div>

    <!-- ═══ SKELETON LOADING STATE ═══ -->
    <div v-if="loading" class="space-y-6">
      <!-- Skeleton: Quick Actions -->
      <div class="flex flex-wrap gap-3">
        <SkeletonBase v-for="i in 3" :key="'qa-sk-'+i" width="11rem" height="3.5rem" rounded="xl" />
      </div>

      <!-- Skeleton: Stat Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="i in 3" :key="'stat-sk-'+i" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div class="space-y-3">
              <SkeletonBase width="6rem" height="1rem" />
              <SkeletonBase width="4rem" height="2rem" />
            </div>
            <SkeletonBase width="3rem" height="3rem" rounded="xl" />
          </div>
        </div>
      </div>

      <!-- Skeleton: 6-Widget Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="i in 6" :key="'wid-sk-'+i" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-5">
          <SkeletonBase width="8rem" height="1rem" class="mb-4" />
          <div class="space-y-2">
            <SkeletonBase v-for="j in 3" :key="'wid-inner-'+i+'-'+j" width="100%" height="2.5rem" rounded="lg" />
          </div>
        </div>
      </div>

      <!-- Skeleton: Main Grid (3 columns) -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- Skeleton: Recent Posts Grid -->
        <div class="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
          <SkeletonBase width="8rem" height="1.25rem" class="mb-4" />
          <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            <SkeletonImage v-for="i in 8" :key="'post-sk-'+i" aspect="square" rounded="lg" />
          </div>
        </div>

        <!-- Skeleton: Mini Calendar -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
          <SkeletonBase width="9rem" height="1.25rem" class="mb-4" />
          <div class="space-y-3">
            <SkeletonBase v-for="i in 7" :key="'cal-sk-'+i" width="100%" height="2.5rem" />
          </div>
        </div>
      </div>

      <!-- Skeleton: Suggestions -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
        <SkeletonBase width="10rem" height="1.25rem" class="mb-4" />
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SkeletonBase v-for="i in 4" :key="'sug-sk-'+i" width="100%" height="7rem" rounded="lg" />
        </div>
      </div>
    </div>

    <!-- ═══ ERROR STATE ═══ -->
    <ErrorBanner
      v-else-if="error"
      :message="error"
      :retryable="true"
      @retry="fetchDashboardData"
    />

    <!-- ═══ DASHBOARD CONTENT ═══ -->
    <div v-else class="space-y-6">

      <!-- ─── Quick Actions Bar ─── -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3" data-tour="quick-actions">
        <button
          @click="router.push('/create/quick')"
          class="flex items-center gap-3 px-5 py-4 bg-gradient-to-r from-[#4C8BC2] to-[#3B7AB1] text-white font-semibold rounded-xl hover:from-[#3B7AB1] hover:to-[#2D6A9F] transition-all shadow-sm hover:shadow-md group"
        >
          <AppIcon name="pencil-square" class="w-7 h-7 group-hover:scale-110 transition-transform" />
          <div class="text-left">
            <span class="block text-sm font-bold">Neuer Post</span>
            <span class="block text-xs opacity-80">Quick Post erstellen</span>
          </div>
        </button>
        <button
          @click="router.push('/library/templates')"
          class="flex items-center gap-3 px-5 py-4 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 font-semibold rounded-xl border border-gray-200 dark:border-gray-700 hover:border-[#4C8BC2] dark:hover:border-[#4C8BC2] hover:bg-blue-50/50 dark:hover:bg-blue-900/10 transition-all shadow-sm hover:shadow-md group"
        >
          <AppIcon name="document-text" class="w-7 h-7 group-hover:scale-110 transition-transform" />
          <div class="text-left">
            <span class="block text-sm font-bold">Aus Template</span>
            <span class="block text-xs text-gray-500 dark:text-gray-400">Vorlage wählen</span>
          </div>
        </button>
        <button
          @click="generateSuggestions"
          :disabled="generatingSuggestions"
          class="flex items-center gap-3 px-5 py-4 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 font-semibold rounded-xl border border-gray-200 dark:border-gray-700 hover:border-[#FDD000] dark:hover:border-[#FDD000] hover:bg-yellow-50/50 dark:hover:bg-yellow-900/10 transition-all shadow-sm hover:shadow-md group disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <AppIcon :name="generatingSuggestions ? 'clock' : 'sparkles'" class="w-7 h-7 group-hover:scale-110 transition-transform" :class="{ 'animate-spin': generatingSuggestions }" />
          <div class="text-left">
            <span class="block text-sm font-bold">KI-Vorschlag</span>
            <span class="block text-xs text-gray-500 dark:text-gray-400">{{ generatingSuggestions ? 'Generiere...' : 'Content-Idee generieren' }}</span>
          </div>
        </button>
      </div>

      <!-- ─── Stat Cards with Animated Counters ─── -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" data-tour="dashboard-stats">
        <!-- Posts this week -->
        <BaseCard hoverable clickable padding="md" class="stagger-item" @click="router.push('/library/history')">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">
                Posts diese Woche
                <HelpTooltip :text="tooltipTexts.dashboard.postsThisWeek" size="sm" />
              </p>
              <p class="text-3xl font-bold text-gray-900 dark:text-white mt-1 tabular-nums">
                {{ animatedStats.posts_this_week }}
              </p>
            </div>
            <div class="w-12 h-12 bg-blue-50 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
              <AppIcon name="document-text" class="w-7 h-7 text-blue-500" />
            </div>
          </div>
          <div class="mt-3 flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500">
            <span>{{ stats.total_posts }} Posts gesamt</span>
          </div>
        </BaseCard>

        <!-- Scheduled Posts -->
        <BaseCard hoverable clickable padding="md" class="stagger-item" @click="router.push('/calendar')">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">
                Geplante Posts
                <HelpTooltip :text="tooltipTexts.dashboard.scheduledPosts" size="sm" />
              </p>
              <p class="text-3xl font-bold text-gray-900 dark:text-white mt-1 tabular-nums">
                {{ animatedStats.scheduled_posts }}
              </p>
            </div>
            <div class="w-12 h-12 bg-yellow-50 dark:bg-yellow-900/30 rounded-xl flex items-center justify-center">
              <AppIcon name="calendar" class="w-7 h-7 text-yellow-500" />
            </div>
          </div>
          <div class="mt-3 flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500">
            <span>Im Kalender eingeplant</span>
          </div>
        </BaseCard>

        <!-- Drafts -->
        <BaseCard hoverable clickable padding="md" class="stagger-item" @click="router.push('/library/history?status=draft')">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">
                Entwürfe
                <HelpTooltip :text="tooltipTexts.dashboard.draftPosts || 'Posts im Entwurf-Status, die noch bearbeitet oder geplant werden können.'" size="sm" />
              </p>
              <p class="text-3xl font-bold text-gray-900 dark:text-white mt-1 tabular-nums">
                {{ animatedStats.draft_posts }}
              </p>
            </div>
            <div class="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-xl flex items-center justify-center">
              <AppIcon name="clipboard-list" class="w-7 h-7 text-gray-500" />
            </div>
          </div>
          <div class="mt-3 flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500">
            <span>Bereit zur Bearbeitung</span>
          </div>
        </BaseCard>
      </div>

      <!-- ─── 6-Widget-Architektur: 3x2 Grid (Desktop), 2x3 (Tablet), 1x6 (Mobile) ─── -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Widget 1: Content Queue -->
        <ContentQueueWidget
          :posts="widgetData.content_queue"
          :loading="widgetsLoading"
          @refresh="fetchWidgetData"
        />

        <!-- Widget 2: Student Inbox -->
        <StudentInboxWidget
          :items="widgetData.student_inbox.items"
          :total="widgetData.student_inbox.total"
          :loading="widgetsLoading"
          @refresh="fetchWidgetData"
        />

        <!-- Widget 3: Performance Pulse -->
        <PerformancePulseWidget
          :data="widgetData.performance_pulse"
          :loading="widgetsLoading"
          @refresh="fetchWidgetData"
        />

        <!-- Widget 4: Active Campaigns -->
        <ActiveCampaignsWidget
          :campaigns="widgetData.active_campaigns"
          :loading="widgetsLoading"
          @refresh="fetchWidgetData"
        />

        <!-- Widget 4b: Content Pillar Distribution -->
        <PillarDistributionWidget />

        <!-- Widget 4c: Pipeline Status -->
        <PipelineDashboardWidget
          :loading="widgetsLoading"
          @refresh="fetchWidgetData"
        />

        <!-- Widget 5: Mini Calendar (existing, moved into grid) -->
        <BaseCard padding="none" data-tour="dashboard-calendar">
          <template #header>
            <h2 class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <AppIcon name="calendar" class="w-5 h-5" /> Nächste 7 Tage
              <HelpTooltip :text="tooltipTexts.dashboard.next7Days" size="sm" />
            </h2>
          </template>
          <template #headerAction>
            <button
              @click="router.push('/calendar')"
              class="text-xs text-[#4C8BC2] hover:text-blue-600 dark:hover:text-blue-400 font-medium"
            >
              Kalender &rarr;
            </button>
          </template>
          <div class="p-4">
            <div class="space-y-1">
              <div
                v-for="day in next7Days"
                :key="day.dateStr"
                class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors"
                :class="[
                  day.isToday
                    ? 'bg-[#4C8BC2]/10 dark:bg-[#4C8BC2]/20 ring-1 ring-[#4C8BC2]/30'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-700/50',
                ]"
              >
                <div class="w-10 text-center flex-shrink-0">
                  <span class="block text-[10px] font-medium text-gray-400 dark:text-gray-500 uppercase leading-none">
                    {{ day.dayName }}
                  </span>
                  <span
                    class="block text-lg font-bold leading-tight mt-0.5"
                    :class="day.isToday ? 'text-[#4C8BC2]' : 'text-gray-900 dark:text-white'"
                  >
                    {{ day.dayNum }}
                  </span>
                </div>
                <div class="flex-1 min-w-0">
                  <div
                    v-if="getEntriesForDate(day.dateStr).length > 0"
                    class="flex items-center gap-1.5 flex-wrap"
                  >
                    <span
                      v-for="(entry, idx) in getEntriesForDate(day.dateStr).slice(0, 3)"
                      :key="entry.id"
                      class="w-2 h-2 rounded-full bg-[#4C8BC2] flex-shrink-0"
                    ></span>
                    <span class="text-xs text-gray-600 dark:text-gray-400 font-medium">
                      {{ getEntriesForDate(day.dateStr).length }} Post{{ getEntriesForDate(day.dateStr).length !== 1 ? 's' : '' }}
                    </span>
                  </div>
                  <span v-else class="text-xs text-gray-300 dark:text-gray-600">&mdash;</span>
                </div>
                <span
                  v-if="day.isToday"
                  class="text-[10px] font-bold text-[#4C8BC2] uppercase flex-shrink-0"
                >
                  Heute
                </span>
              </div>
            </div>
            <div v-if="calendarEntries.length === 0" class="mt-3 text-center text-xs text-gray-400 dark:text-gray-500 bg-gray-50 dark:bg-gray-700/30 rounded-lg py-2.5 px-3">
              Keine geplanten Posts in den nächsten 7 Tagen.
              <button
                @click="router.push('/calendar/week-planner')"
                class="text-[#4C8BC2] hover:underline font-medium ml-1"
              >
                Wochenplaner
              </button>
            </div>
          </div>
        </BaseCard>

        <!-- Widget 6: AI Suggestions (compact version) -->
        <BaseCard padding="none" data-tour="dashboard-suggestions-widget">
          <template #header>
            <h2 class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <AppIcon name="sparkles" class="w-5 h-5" /> KI-Vorschläge
            </h2>
          </template>
          <template #headerAction>
            <button
              @click="generateSuggestions"
              :disabled="generatingSuggestions"
              class="text-xs text-[#4C8BC2] hover:text-blue-600 dark:hover:text-blue-400 font-medium disabled:opacity-50"
            >
              {{ generatingSuggestions ? 'Generiere...' : 'Neue Ideen' }} &rarr;
            </button>
          </template>
          <div class="p-4">
            <EmptyState
              v-if="suggestions.length === 0"
              svgIcon="sparkles"
              title="Keine Vorschläge"
              description="Generiere KI-Ideen für deinen nächsten Post."
              actionLabel="Vorschläge generieren"
              @action="generateSuggestions"
              :compact="true"
            />
            <div v-else class="space-y-2">
              <div
                v-for="sug in suggestions.slice(0, 3)"
                :key="sug.id"
                class="p-2 rounded-lg border border-gray-100 dark:border-gray-700 hover:border-[#FDD000]/50 dark:hover:border-[#FDD000]/50 transition-all cursor-pointer"
                @click="router.push({ path: '/create/quick', query: { category: sug.suggested_category, country: sug.suggested_country } })"
              >
                <p class="text-xs font-semibold text-gray-900 dark:text-white truncate">{{ sug.title }}</p>
                <p class="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-1">{{ sug.description }}</p>
              </div>
            </div>
          </div>
        </BaseCard>
      </div>

      <!-- ─── Main Content Grid: 3 cols desktop, 2 tablet, 1 mobile ─── -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

        <!-- Recent Posts Thumbnail Grid (spans 2 columns on lg) -->
        <BaseCard padding="none" class="md:col-span-2" data-tour="dashboard-recent-posts">
          <template #header>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <AppIcon name="clipboard-list" class="w-5 h-5" /> Letzte Posts
              <HelpTooltip :text="tooltipTexts.dashboard.recentPosts" size="sm" />
            </h2>
          </template>
          <template #headerAction>
            <button
              v-if="recentPosts.length > 0"
              @click="router.push('/library/history')"
              class="text-sm text-[#4C8BC2] hover:text-blue-600 dark:hover:text-blue-400 font-medium"
            >
              Alle anzeigen &rarr;
            </button>
          </template>
          <div class="p-5">
            <!-- Empty state -->
            <EmptyState
              v-if="recentPosts.length === 0"
              svgIcon="document-text"
              title="Noch keine Posts erstellt"
              description="Erstelle deinen ersten Social-Media-Post für TREFF und starte mit deinem Content-Plan!"
              actionLabel="Ersten Post erstellen"
              actionTo="/create/quick"
              secondaryLabel="Einstellungen prüfen"
              secondaryTo="/settings"
              :compact="true"
            />

            <!-- Thumbnail Grid -->
            <div v-else class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              <div
                v-for="post in recentPosts"
                :key="post.id"
                class="stagger-item group relative rounded-lg overflow-hidden cursor-pointer border border-gray-100 dark:border-gray-700 hover:border-[#4C8BC2]/50 dark:hover:border-[#4C8BC2]/50 transition-all hover:shadow-md hover:-translate-y-0.5"
                @click="router.push(`/create/post/${post.id}/edit`)"
              >
                <!-- Thumbnail or Category Placeholder -->
                <div class="aspect-square relative">
                  <img
                    v-if="post.thumbnail_url"
                    :src="post.thumbnail_url"
                    :alt="post.title || 'Post Thumbnail'"
                    class="w-full h-full object-cover"
                    loading="lazy"
                  />
                  <div
                    v-else
                    class="w-full h-full flex flex-col items-center justify-center gap-1.5"
                    :class="categoryColor(post.category)"
                  >
                    <AppIcon :name="platformIcon(post.platform)" class="w-8 h-8 text-white opacity-90" />
                    <span class="text-xs text-white/80 font-medium px-2 text-center leading-tight">{{ categoryLabel(post.category) }}</span>
                  </div>

                  <!-- Hover Overlay -->
                  <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center p-2">
                    <p class="text-white text-xs font-semibold text-center line-clamp-2 mb-1">{{ post.title || 'Ohne Titel' }}</p>
                    <p class="text-white/70 text-[10px] text-center">{{ formatDateShort(post.created_at) }}</p>
                  </div>

                  <!-- Status badge (top right) -->
                  <span
                    class="absolute top-1.5 right-1.5 text-[10px] font-bold px-1.5 py-0.5 rounded-full shadow-sm"
                    :class="statusColor(post.status)"
                  >
                    {{ statusLabel(post.status) }}
                  </span>

                  <!-- Platform icon (top left) -->
                  <span class="absolute top-1.5 left-1.5 bg-white/80 dark:bg-gray-900/80 rounded-full w-6 h-6 flex items-center justify-center shadow-sm">
                    <AppIcon :name="platformIcon(post.platform)" class="w-3.5 h-3.5 text-gray-700 dark:text-gray-300" />
                  </span>

                  <!-- Slide count badge (bottom right) -->
                  <span
                    v-if="post.slide_count > 1"
                    class="absolute bottom-1.5 right-1.5 text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-black/60 text-white shadow-sm"
                  >
                    {{ post.slide_count }} Slides
                  </span>
                </div>
              </div>
            </div>
          </div>
        </BaseCard>

      </div>

      <!-- ─── Activity Heatmap (mini, optional on Dashboard) ─── -->
      <BaseCard padding="lg" :header-divider="false" data-testid="dashboard-heatmap">
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Aktivitäts-Heatmap</h2>
        </template>
        <template #headerAction>
          <router-link to="/analytics" class="text-xs text-[#3B7AB1] hover:text-[#2d6a9e] dark:text-sky-400 font-medium">
            Mehr Analytics &rarr;
          </router-link>
        </template>
        <ActivityHeatmap />
      </BaseCard>

      <!-- ─── Series Status Widget ─── -->
      <div data-tour="dashboard-series-status">
        <SeriesStatusWidget />
      </div>

      <!-- ─── Content Recycling Panel ─── -->
      <div data-tour="dashboard-recycling">
        <RecyclingPanel />
      </div>

      <!-- ─── Content Suggestions Section (full detail view, below widgets) ─── -->
      <ContentSuggestions
        ref="contentSuggestionsRef"
        :initial-suggestions="suggestions"
      />
    </div>

    <!-- Welcome Flow for first-time users (before page tours) -->
    <WelcomeFlow
      :show="showWelcomeFlow"
      @complete="handleWelcomeComplete"
      @skip="handleWelcomeSkip"
    />

    <!-- Page-specific guided tour: only mounts after welcome check, suppresses auto-start if welcome was shown -->
    <TourSystem v-if="welcomeCheckDone" ref="tourRef" page-key="dashboard" :auto-start="!showWelcomeFlow" />
  </div>
</template>
