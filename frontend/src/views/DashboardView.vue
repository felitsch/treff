<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import TourSystem from '@/components/common/TourSystem.vue'
import WelcomeFlow from '@/components/common/WelcomeFlow.vue'
import RecyclingPanel from '@/components/dashboard/RecyclingPanel.vue'
import SeriesStatusWidget from '@/components/dashboard/SeriesStatusWidget.vue'
import WorkflowHint from '@/components/common/WorkflowHint.vue'
import HelpTooltip from '@/components/common/HelpTooltip.vue'
import EmptyState from '@/components/common/EmptyState.vue'
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
  total_assets: 0,
  total_posts: 0,
})
const recentPosts = ref([])
const calendarEntries = ref([])
const suggestions = ref([])
const acceptingId = ref(null)
const dismissingId = ref(null)
const generatingSuggestions = ref(false)

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
      path: '/create-post',
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

onMounted(() => {
  fetchDashboardData()
  checkWelcomeStatus()
})
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <!-- Page Header -->
    <div class="mb-8 flex items-start justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Willkommen zurueck! Hier ist dein Content-Ueberblick.
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
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center" role="alert">
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
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" data-tour="dashboard-stats">
        <!-- Posts this week -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">Posts diese Woche <HelpTooltip :text="tooltipTexts.dashboard.postsThisWeek" size="sm" /></p>
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
              <p class="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">Geplante Posts <HelpTooltip :text="tooltipTexts.dashboard.scheduledPosts" size="sm" /></p>
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
              <p class="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">Gesamt Assets <HelpTooltip :text="tooltipTexts.dashboard.totalAssets" size="sm" /></p>
              <p class="text-3xl font-bold text-gray-900 dark:text-white mt-1">{{ stats.total_assets }}</p>
            </div>
            <div class="w-12 h-12 bg-green-50 dark:bg-green-900/30 rounded-xl flex items-center justify-center">
              <span class="text-2xl">🖼️</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Action Buttons -->
      <div class="flex flex-wrap gap-3" data-tour="quick-actions">
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
              <span>📅</span> Naechste 7 Tage <HelpTooltip :text="tooltipTexts.dashboard.next7Days" size="sm" />
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
              <span>📋</span> Letzte Posts <HelpTooltip :text="tooltipTexts.dashboard.recentPosts" size="sm" />
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
            <EmptyState
              v-if="recentPosts.length === 0"
              icon="📝"
              title="Noch keine Posts erstellt"
              description="Erstelle deinen ersten Social-Media-Post fuer TREFF und starte mit deinem Content-Plan!"
              actionLabel="Ersten Post erstellen"
              actionTo="/create-post"
              secondaryLabel="Einstellungen pruefen"
              secondaryTo="/settings"
              :compact="true"
            />

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

      <!-- Series Status Widget -->
      <SeriesStatusWidget />

      <!-- Content Recycling Panel -->
      <RecyclingPanel />

      <!-- Content Suggestions Section -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
        <div class="p-5 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <span>💡</span> Content-Vorschlaege <HelpTooltip :text="tooltipTexts.dashboard.suggestions" size="sm" />
          </h2>
          <div class="flex items-center gap-2">
            <span
              v-if="suggestions.length > 0"
              class="text-xs font-medium px-2.5 py-1 rounded-full bg-treff-blue/10 text-treff-blue dark:bg-treff-blue/20"
            >
              {{ suggestions.length }} offen
            </span>
            <button
              @click="generateSuggestions"
              :disabled="generatingSuggestions"
              data-testid="generate-suggestions-btn"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-treff-blue rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span v-if="generatingSuggestions" class="animate-spin">⏳</span>
              <span v-else>✨</span>
              {{ generatingSuggestions ? 'Generiere...' : 'Generieren' }}
            </button>
          </div>
        </div>
        <div class="p-5">
          <!-- Empty state -->
          <EmptyState
            v-if="suggestions.length === 0"
            icon="💡"
            title="Keine Vorschlaege vorhanden"
            description="Klicke auf 'Generieren' um KI-gestuetzte Content-Vorschlaege fuer deine naechsten Posts zu erhalten."
            actionLabel="Vorschlaege generieren"
            :compact="true"
            @action="generateSuggestions"
          />

          <!-- Suggestions list -->
          <div v-else class="space-y-4">
            <div
              v-for="suggestion in suggestions"
              :key="suggestion.id"
              class="border border-gray-100 dark:border-gray-700 rounded-lg p-4 hover:border-treff-blue/30 dark:hover:border-treff-blue/40 transition-colors"
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
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-treff-blue rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
      </div>
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
