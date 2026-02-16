<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import TourSystem from '@/components/common/TourSystem.vue'
import WelcomeFlow from '@/components/common/WelcomeFlow.vue'
import RecyclingPanel from '@/components/dashboard/RecyclingPanel.vue'
import SeriesStatusWidget from '@/components/dashboard/SeriesStatusWidget.vue'
import WorkflowHint from '@/components/common/WorkflowHint.vue'
import HelpTooltip from '@/components/common/HelpTooltip.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import SkeletonBase from '@/components/common/SkeletonBase.vue'
import SkeletonImage from '@/components/common/SkeletonImage.vue'
import { tooltipTexts } from '@/utils/tooltipTexts'

const router = useRouter()

const loading = ref(true)
const error = ref(null)
const tourRef = ref(null)
const showWelcomeFlow = ref(false)
const welcomeCheckDone = ref(false)

// Workflow hint: missing API keys
const apiKeysMissing = ref(false)

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
const acceptingId = ref(null)
const dismissingId = ref(null)
const generatingSuggestions = ref(false)

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

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

function formatDateShort(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: 'short',
  })
}

// Suggestion type icons
function suggestionTypeIcon(type) {
  switch (type) {
    case 'seasonal':
      return '🌸'
    case 'country_rotation':
      return '🌍'
    case 'category_balance':
      return '⚖️'
    case 'gap_fill':
      return '📅'
    case 'weekly_plan':
      return '📋'
    case 'story_teaser':
      return '👉'
    default:
      return '💡'
  }
}

// Suggestion type label
function suggestionTypeLabel(type) {
  const labels = {
    seasonal: 'Saisonal',
    country_rotation: 'Laender-Rotation',
    category_balance: 'Kategorie-Balance',
    gap_fill: 'Luecke fuellen',
    weekly_plan: 'Wochenplan',
    story_teaser: 'Story-Teaser',
  }
  return labels[type] || type
}

// Suggestion type badge color
function suggestionTypeBadge(type) {
  switch (type) {
    case 'seasonal':
      return 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300'
    case 'country_rotation':
      return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
    case 'category_balance':
      return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
    case 'gap_fill':
      return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300'
    case 'weekly_plan':
      return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
    case 'story_teaser':
      return 'bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900/30 dark:text-fuchsia-300'
    default:
      return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
  }
}

// Country flag emoji
function countryFlag(country) {
  const flags = {
    usa: '🇺🇸',
    canada: '🇨🇦',
    australia: '🇦🇺',
    newzealand: '🇳🇿',
    ireland: '🇮🇪',
  }
  return flags[country] || ''
}

// Accept suggestion
async function acceptSuggestion(suggestion) {
  acceptingId.value = suggestion.id
  try {
    await api.put('/api/suggestions/' + suggestion.id + '/accept')
    suggestions.value = suggestions.value.filter((s) => s.id !== suggestion.id)
    // Navigate to create post with pre-filled data
    router.push({
      path: '/create/quick',
      query: {
        category: suggestion.suggested_category || '',
        country: suggestion.suggested_country || '',
      },
    })
  } catch (err) {
    console.error('Failed to accept suggestion:', err)
  } finally {
    acceptingId.value = null
  }
}

// Dismiss suggestion
async function dismissSuggestion(suggestion) {
  dismissingId.value = suggestion.id
  try {
    await api.put('/api/suggestions/' + suggestion.id + '/dismiss')
    suggestions.value = suggestions.value.filter((s) => s.id !== suggestion.id)
  } catch (err) {
    console.error('Failed to dismiss suggestion:', err)
  } finally {
    dismissingId.value = null
  }
}

// Generate new AI content suggestions
async function generateSuggestions() {
  generatingSuggestions.value = true
  try {
    const res = await api.post('/api/ai/suggest-content', {})
    if (res.data.suggestions && res.data.suggestions.length > 0) {
      // Prepend new suggestions to existing ones
      suggestions.value = [...res.data.suggestions, ...suggestions.value]
    }
  } catch (err) {
    console.error('Failed to generate suggestions:', err)
  } finally {
    generatingSuggestions.value = false
  }
}

async function fetchDashboardData() {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/api/analytics/dashboard')
    stats.value = res.data.stats
    recentPosts.value = res.data.recent_posts
    calendarEntries.value = res.data.calendar_entries
    suggestions.value = res.data.suggestions || []

    // Trigger animated counters after data load
    setTimeout(() => {
      animateCounter(stats.value.posts_this_week, 'posts_this_week')
      animateCounter(stats.value.scheduled_posts, 'scheduled_posts')
      animateCounter(stats.value.draft_posts || 0, 'draft_posts')
    }, 100)
  } catch (err) {
    console.error('Failed to load dashboard data:', err)
    error.value = 'Dashboard-Daten konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function checkWelcomeStatus() {
  try {
    const res = await api.get('/api/settings')
    const settings = res.data
    // Check welcome flow first (shows before page-specific tour)
    if (!settings.welcome_completed || settings.welcome_completed === 'false') {
      // First time user - show welcome flow immediately
      showWelcomeFlow.value = true
    }
    // Check if API keys are configured (for workflow hint)
    if (!settings.gemini_api_key && !settings.openai_api_key) {
      apiKeysMissing.value = true
    }
  } catch (err) {
    console.error('Failed to check welcome status:', err)
  } finally {
    // Mark check as done so TourSystem can conditionally render
    welcomeCheckDone.value = true
  }
}

async function handleWelcomeComplete() {
  showWelcomeFlow.value = false
  try {
    await api.put('/api/settings', { welcome_completed: 'true' })
  } catch (err) {
    console.error('Failed to save welcome status:', err)
  }
  // After welcome flow, start the page-specific tour
  setTimeout(() => {
    tourRef.value?.startTour()
  }, 400)
}

async function handleWelcomeSkip() {
  showWelcomeFlow.value = false
  try {
    await api.put('/api/settings', { welcome_completed: 'true' })
  } catch (err) {
    console.error('Failed to save welcome status:', err)
  }
  // After skipping welcome, start the page-specific tour
  setTimeout(() => {
    tourRef.value?.startTour()
  }, 400)
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
          {{ todayFormatted }} &mdash; Hier ist dein Content-Ueberblick.
        </p>
      </div>
      <button
        @click="tourRef?.startTour()"
        class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        title="Seiten-Tour starten"
      >
        &#10067; Tour starten
      </button>
    </div>

    <!-- Workflow Hint: Missing API Keys -->
    <WorkflowHint
      hint-id="dashboard-api-keys"
      message="Keine API-Keys konfiguriert. Hinterlege deinen Gemini- oder OpenAI-Key, um KI-Funktionen zu nutzen."
      link-text="Einstellungen"
      link-to="/settings"
      icon="🔑"
      :show="apiKeysMissing"
    />

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
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center" role="alert">
      <p class="text-red-600 dark:text-red-400">{{ error }}</p>
      <button
        @click="fetchDashboardData"
        class="mt-3 px-4 py-2 bg-red-100 dark:bg-red-800 text-red-700 dark:text-red-200 rounded-lg hover:bg-red-200 dark:hover:bg-red-700 transition-colors"
      >
        Erneut versuchen
      </button>
    </div>

    <!-- ═══ DASHBOARD CONTENT ═══ -->
    <div v-else class="space-y-6">

      <!-- ─── Quick Actions Bar ─── -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3" data-tour="quick-actions">
        <button
          @click="router.push('/create/quick')"
          class="flex items-center gap-3 px-5 py-4 bg-gradient-to-r from-[#4C8BC2] to-[#3B7AB1] text-white font-semibold rounded-xl hover:from-[#3B7AB1] hover:to-[#2D6A9F] transition-all shadow-sm hover:shadow-md group"
        >
          <span class="text-2xl group-hover:scale-110 transition-transform">✏️</span>
          <div class="text-left">
            <span class="block text-sm font-bold">Neuer Post</span>
            <span class="block text-xs opacity-80">Quick Post erstellen</span>
          </div>
        </button>
        <button
          @click="router.push('/library/templates')"
          class="flex items-center gap-3 px-5 py-4 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 font-semibold rounded-xl border border-gray-200 dark:border-gray-700 hover:border-[#4C8BC2] dark:hover:border-[#4C8BC2] hover:bg-blue-50/50 dark:hover:bg-blue-900/10 transition-all shadow-sm hover:shadow-md group"
        >
          <span class="text-2xl group-hover:scale-110 transition-transform">📄</span>
          <div class="text-left">
            <span class="block text-sm font-bold">Aus Template</span>
            <span class="block text-xs text-gray-500 dark:text-gray-400">Vorlage waehlen</span>
          </div>
        </button>
        <button
          @click="generateSuggestions"
          :disabled="generatingSuggestions"
          class="flex items-center gap-3 px-5 py-4 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 font-semibold rounded-xl border border-gray-200 dark:border-gray-700 hover:border-[#FDD000] dark:hover:border-[#FDD000] hover:bg-yellow-50/50 dark:hover:bg-yellow-900/10 transition-all shadow-sm hover:shadow-md group disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span class="text-2xl group-hover:scale-110 transition-transform" :class="{ 'animate-spin': generatingSuggestions }">{{ generatingSuggestions ? '⏳' : '✨' }}</span>
          <div class="text-left">
            <span class="block text-sm font-bold">KI-Vorschlag</span>
            <span class="block text-xs text-gray-500 dark:text-gray-400">{{ generatingSuggestions ? 'Generiere...' : 'Content-Idee generieren' }}</span>
          </div>
        </button>
      </div>

      <!-- ─── Stat Cards with Animated Counters ─── -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" data-tour="dashboard-stats">
        <!-- Posts this week -->
        <BaseCard hoverable clickable padding="md" @click="router.push('/library/history')">
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
              <span class="text-2xl">📝</span>
            </div>
          </div>
          <div class="mt-3 flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500">
            <span>{{ stats.total_posts }} Posts gesamt</span>
          </div>
        </BaseCard>

        <!-- Scheduled Posts -->
        <BaseCard hoverable clickable padding="md" @click="router.push('/calendar')">
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
              <span class="text-2xl">📅</span>
            </div>
          </div>
          <div class="mt-3 flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500">
            <span>Im Kalender eingeplant</span>
          </div>
        </BaseCard>

        <!-- Drafts -->
        <BaseCard hoverable clickable padding="md" @click="router.push('/library/history?status=draft')">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">
                Entwuerfe
                <HelpTooltip :text="tooltipTexts.dashboard.draftPosts || 'Posts im Entwurf-Status, die noch bearbeitet oder geplant werden koennen.'" size="sm" />
              </p>
              <p class="text-3xl font-bold text-gray-900 dark:text-white mt-1 tabular-nums">
                {{ animatedStats.draft_posts }}
              </p>
            </div>
            <div class="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-xl flex items-center justify-center">
              <span class="text-2xl">📋</span>
            </div>
          </div>
          <div class="mt-3 flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500">
            <span>Bereit zur Bearbeitung</span>
          </div>
        </BaseCard>
      </div>

      <!-- ─── Main Content Grid: 3 cols desktop, 2 tablet, 1 mobile ─── -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

        <!-- Recent Posts Thumbnail Grid (spans 2 columns on lg) -->
        <BaseCard padding="none" class="md:col-span-2" data-tour="dashboard-recent-posts">
          <template #header>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <span>📋</span> Letzte Posts
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
              description="Erstelle deinen ersten Social-Media-Post fuer TREFF und starte mit deinem Content-Plan!"
              actionLabel="Ersten Post erstellen"
              actionTo="/create/quick"
              secondaryLabel="Einstellungen pruefen"
              secondaryTo="/settings"
              :compact="true"
            />

            <!-- Thumbnail Grid -->
            <div v-else class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              <div
                v-for="post in recentPosts"
                :key="post.id"
                class="group relative rounded-lg overflow-hidden cursor-pointer border border-gray-100 dark:border-gray-700 hover:border-[#4C8BC2]/50 dark:hover:border-[#4C8BC2]/50 transition-all hover:shadow-md hover:-translate-y-0.5"
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
                    <span class="text-3xl opacity-90">{{ platformIcon(post.platform) }}</span>
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
                  <span class="absolute top-1.5 left-1.5 text-sm bg-white/80 dark:bg-gray-900/80 rounded-full w-6 h-6 flex items-center justify-center shadow-sm">
                    {{ platformIcon(post.platform) }}
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

        <!-- Mini Calendar Widget (right column on lg) -->
        <BaseCard padding="none" data-tour="dashboard-calendar">
          <template #header>
            <h2 class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <span>📅</span> Naechste 7 Tage
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
                <!-- Day name + number -->
                <div class="w-10 text-center flex-shrink-0">
                  <span class="block text-[10px] font-medium text-gray-400 dark:text-gray-500 uppercase leading-none">
                    {{ day.dayName }}
                  </span>
                  <span
                    class="block text-lg font-bold leading-tight mt-0.5"
                    :class="
                      day.isToday
                        ? 'text-[#4C8BC2]'
                        : 'text-gray-900 dark:text-white'
                    "
                  >
                    {{ day.dayNum }}
                  </span>
                </div>

                <!-- Entries or empty -->
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
                  <span v-else class="text-xs text-gray-300 dark:text-gray-600">
                    &mdash;
                  </span>
                </div>

                <!-- Today badge -->
                <span
                  v-if="day.isToday"
                  class="text-[10px] font-bold text-[#4C8BC2] uppercase flex-shrink-0"
                >
                  Heute
                </span>
              </div>
            </div>

            <!-- No scheduled posts hint -->
            <div v-if="calendarEntries.length === 0" class="mt-3 text-center text-xs text-gray-400 dark:text-gray-500 bg-gray-50 dark:bg-gray-700/30 rounded-lg py-2.5 px-3">
              Keine geplanten Posts in den naechsten 7 Tagen.
              <button
                @click="router.push('/calendar/week-planner')"
                class="text-[#4C8BC2] hover:underline font-medium ml-1"
              >
                Wochenplaner
              </button>
            </div>
          </div>
        </BaseCard>
      </div>

      <!-- ─── Series Status Widget ─── -->
      <div data-tour="dashboard-series-status">
        <SeriesStatusWidget />
      </div>

      <!-- ─── Content Recycling Panel ─── -->
      <div data-tour="dashboard-recycling">
        <RecyclingPanel />
      </div>

      <!-- ─── Content Suggestions Section ─── -->
      <BaseCard padding="none" data-tour="dashboard-suggestions">
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <span>💡</span> Content-Vorschlaege <HelpTooltip :text="tooltipTexts.dashboard.suggestions" size="sm" />
          </h2>
        </template>
        <template #headerAction>
          <div class="flex items-center gap-2">
            <span
              v-if="suggestions.length > 0"
              class="text-xs font-medium px-2.5 py-1 rounded-full bg-[#4C8BC2]/10 text-[#4C8BC2] dark:bg-[#4C8BC2]/20"
            >
              {{ suggestions.length }} offen
            </span>
            <button
              @click="generateSuggestions"
              :disabled="generatingSuggestions"
              data-testid="generate-suggestions-btn"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-[#4C8BC2] rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span v-if="generatingSuggestions" class="animate-spin">⏳</span>
              <span v-else>✨</span>
              {{ generatingSuggestions ? 'Generiere...' : 'Generieren' }}
            </button>
          </div>
        </template>
        <div class="p-5">
          <!-- Empty state -->
          <EmptyState
            v-if="suggestions.length === 0"
            svgIcon="sparkles"
            title="Keine Vorschlaege vorhanden"
            description="Klicke auf 'Generieren' um KI-gestuetzte Content-Vorschlaege fuer deine naechsten Posts zu erhalten."
            actionLabel="Vorschlaege generieren"
            :compact="true"
            @action="generateSuggestions"
          />

          <!-- Suggestions grid -->
          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div
              v-for="suggestion in suggestions"
              :key="suggestion.id"
              class="border border-gray-100 dark:border-gray-700 rounded-lg p-4 hover:border-[#4C8BC2]/30 dark:hover:border-[#4C8BC2]/40 transition-colors"
            >
              <!-- Top row: type badge + category + country -->
              <div class="flex items-center gap-2 flex-wrap mb-2">
                <span
                  class="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full"
                  :class="suggestionTypeBadge(suggestion.suggestion_type)"
                >
                  {{ suggestionTypeIcon(suggestion.suggestion_type) }}
                  {{ suggestionTypeLabel(suggestion.suggestion_type) }}
                </span>
                <span
                  v-if="suggestion.suggested_category"
                  class="text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300"
                >
                  {{ categoryLabel(suggestion.suggested_category) }}
                </span>
                <span
                  v-if="suggestion.suggested_country"
                  class="text-xs"
                >
                  {{ countryFlag(suggestion.suggested_country) }}
                </span>
                <span
                  v-if="suggestion.suggested_date"
                  class="text-xs text-gray-400 dark:text-gray-500 ml-auto"
                >
                  {{ formatDate(suggestion.suggested_date) }}
                </span>
              </div>

              <!-- Title -->
              <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                {{ suggestion.title }}
              </h3>

              <!-- Description (if available) -->
              <p
                v-if="suggestion.description"
                class="text-xs text-gray-500 dark:text-gray-400 mb-2 line-clamp-2"
              >
                {{ suggestion.description }}
              </p>

              <!-- Reason -->
              <div
                v-if="suggestion.reason"
                class="flex items-start gap-1.5 mb-3"
              >
                <span class="text-xs text-gray-400 mt-0.5">💬</span>
                <p class="text-xs text-gray-400 dark:text-gray-500 italic">
                  {{ suggestion.reason }}
                </p>
              </div>

              <!-- Action buttons -->
              <div class="flex items-center gap-2">
                <button
                  @click="acceptSuggestion(suggestion)"
                  :disabled="acceptingId === suggestion.id"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-[#4C8BC2] rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span v-if="acceptingId === suggestion.id" class="animate-spin">⏳</span>
                  <span v-else>✅</span>
                  Annehmen
                </button>
                <button
                  @click="dismissSuggestion(suggestion)"
                  :disabled="dismissingId === suggestion.id"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span v-if="dismissingId === suggestion.id" class="animate-spin">⏳</span>
                  <span v-else>❌</span>
                  Ablehnen
                </button>
              </div>
            </div>
          </div>
        </div>
      </BaseCard>
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
