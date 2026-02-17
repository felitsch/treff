<script setup>
/**
 * CreateHubView — Mode-Selector for content creation.
 *
 * Provides 4 large visual cards as a 2x2 grid (desktop) / vertical stack (mobile):
 * 1. Quick Create — fast 2-click draft (1-2 min)
 * 2. Smart Create — upload photo, AI does the rest (3-5 min)
 * 3. Video Create — brand videos for all platforms (5 min)
 * 4. Campaign Create — multi-post series planning (10-15 min)
 *
 * Below the cards: "Letzte Entwuerfe" showing the 3 most recent drafts.
 * Country-Accent theming when a default country is set in settings.
 *
 * @see frontend/src/router/index.js — /create route
 */
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import { useCountryTheme } from '@/composables/useCountryTheme'
import AppIcon from '@/components/icons/AppIcon.vue'

const router = useRouter()

// ─── Country accent theming ──────────────────────────────────
const settingsCountry = ref(null)
const countryTheme = useCountryTheme(settingsCountry)

// ─── Recent drafts ───────────────────────────────────────────
const recentDrafts = ref([])
const draftsLoading = ref(true)

// ─── Create mode cards ──────────────────────────────────────
const createOptions = [
  {
    title: 'Quick Create',
    subtitle: '2 Klicks zum Entwurf',
    description: 'Schnell einen einzelnen Post erstellen mit dem Schritt-fuer-Schritt Editor. Ideal fuer schnelle Inhalte zwischendurch.',
    duration: '1-2 Min',
    path: '/create/quick',
    color: 'blue',
    gradient: 'from-blue-500 to-blue-600',
    lightBg: 'bg-blue-50 dark:bg-blue-950/30',
    border: 'border-blue-200 dark:border-blue-800',
    hoverBorder: 'hover:border-blue-400 dark:hover:border-blue-600',
    iconBg: 'bg-blue-100 dark:bg-blue-900/50',
    iconColor: 'text-blue-600 dark:text-blue-400',
    badgeBg: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
    // Heroicon: bolt (lightning)
    iconPath: 'M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z',
  },
  {
    title: 'Smart Create',
    subtitle: 'Foto hochladen, AI macht den Rest',
    description: 'KI-gestuetzter Post-Generator: Lade ein Bild hoch, AI analysiert es und schlaegt Caption, Hashtags und Template vor.',
    duration: '3-5 Min',
    path: '/create/smart',
    color: 'purple',
    gradient: 'from-purple-500 to-purple-600',
    lightBg: 'bg-purple-50 dark:bg-purple-950/30',
    border: 'border-purple-200 dark:border-purple-800',
    hoverBorder: 'hover:border-purple-400 dark:hover:border-purple-600',
    iconBg: 'bg-purple-100 dark:bg-purple-900/50',
    iconColor: 'text-purple-600 dark:text-purple-400',
    badgeBg: 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300',
    // Heroicon: camera
    iconPath: 'M6.827 6.175A2.31 2.31 0 015.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 00-1.134-.175 2.31 2.31 0 01-1.64-1.055l-.822-1.316a2.192 2.192 0 00-1.736-1.039 48.774 48.774 0 00-5.232 0 2.192 2.192 0 00-1.736 1.039l-.821 1.316z M16.5 12.75a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0z',
  },
  {
    title: 'Video Create',
    subtitle: 'Video fuer alle Plattformen branden',
    description: 'Unified Video-Pipeline: Upload, Intro/Outro-Branding, Lower Third, Musik und Multi-Format-Export in einem Schritt.',
    duration: '5 Min',
    path: '/create/video',
    color: 'red',
    gradient: 'from-red-500 to-red-600',
    lightBg: 'bg-red-50 dark:bg-red-950/30',
    border: 'border-red-200 dark:border-red-800',
    hoverBorder: 'hover:border-red-400 dark:hover:border-red-600',
    iconBg: 'bg-red-100 dark:bg-red-900/50',
    iconColor: 'text-red-600 dark:text-red-400',
    badgeBg: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300',
    // Heroicon: film
    iconPath: 'M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h1.5C5.496 19.5 6 18.996 6 18.375m-2.625 0V5.625m0 0A1.125 1.125 0 014.5 4.5h15a1.125 1.125 0 011.125 1.125m-17.25 0v1.5c0 .621.504 1.125 1.125 1.125M19.5 4.5v1.5c0 .621.504 1.125 1.125 1.125m0 0h1.5m-1.5 0v3.375m0 0h1.5m-1.5 0v3.375m0 0h1.5m-1.5 0V18.375m1.5 0h-1.5m1.5 0a1.125 1.125 0 01-1.125 1.125M4.5 7.25h1.5m-1.5 0v3.375m0 0h1.5m-1.5 0v3.375m0 0h1.5m-1.5 0V18.375m1.5 0H4.5',
  },
  {
    title: 'Campaign Create',
    subtitle: 'Multi-Post-Serie planen',
    description: 'Plane eine mehrteilige Content-Kampagne: Definiere Ziel und Zeitraum, AI generiert einen Post-Plan mit Timeline.',
    duration: '10-15 Min',
    path: '/create/campaign',
    color: 'amber',
    gradient: 'from-amber-500 to-amber-600',
    lightBg: 'bg-amber-50 dark:bg-amber-950/30',
    border: 'border-amber-200 dark:border-amber-800',
    hoverBorder: 'hover:border-amber-400 dark:hover:border-amber-600',
    iconBg: 'bg-amber-100 dark:bg-amber-900/50',
    iconColor: 'text-amber-600 dark:text-amber-400',
    badgeBg: 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300',
    // Heroicon: calendar-days
    iconPath: 'M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5m-9-6h.008v.008H12v-.008zM12 15h.008v.008H12V15zm0 2.25h.008v.008H12v-.008zM9.75 15h.008v.008H9.75V15zm0 2.25h.008v.008H9.75v-.008zM7.5 15h.008v.008H7.5V15zm0 2.25h.008v.008H7.5v-.008zm6.75-4.5h.008v.008h-.008v-.008zm0 2.25h.008v.008h-.008V15zm0 2.25h.008v.008h-.008v-.008zm2.25-4.5h.008v.008H16.5v-.008zm0 2.25h.008v.008H16.5V15z',
  },
]

// ─── Country accent styles ───────────────────────────────────
const accentStyle = computed(() => {
  if (!countryTheme.isCountryTheme.value) return {}
  return {
    borderTop: `3px solid ${countryTheme.theme.value.primaryColor}`,
  }
})

const accentBadge = computed(() => {
  if (!countryTheme.isCountryTheme.value) return null
  return {
    emoji: countryTheme.theme.value.emoji,
    label: countryTheme.theme.value.label,
    color: countryTheme.theme.value.primaryColor,
  }
})

// ─── Data fetching ───────────────────────────────────────────
async function fetchSettings() {
  try {
    const res = await api.get('/api/settings')
    const settings = res.data
    // Look for a default_country or country setting
    if (settings?.default_country) {
      settingsCountry.value = settings.default_country
    } else if (settings?.country) {
      settingsCountry.value = settings.country
    }
  } catch {
    // Settings not available, no accent
  }
}

async function fetchRecentDrafts() {
  draftsLoading.value = true
  try {
    const res = await api.get('/api/posts', {
      params: {
        status: 'draft',
        sort_by: 'updated_at',
        sort_direction: 'desc',
        page: 1,
        limit: 3,
      },
    })
    // API returns paginated: { items: [...], total, page, ... } or flat array
    if (Array.isArray(res.data)) {
      recentDrafts.value = res.data.slice(0, 3)
    } else if (res.data?.items) {
      recentDrafts.value = res.data.items.slice(0, 3)
    } else {
      recentDrafts.value = []
    }
  } catch {
    recentDrafts.value = []
  } finally {
    draftsLoading.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function formatTimeAgo(dateStr) {
  if (!dateStr) return ''
  const now = new Date()
  const d = new Date(dateStr)
  const diff = Math.floor((now - d) / 1000)
  if (diff < 60) return 'Gerade eben'
  if (diff < 3600) return `vor ${Math.floor(diff / 60)} Min`
  if (diff < 86400) return `vor ${Math.floor(diff / 3600)} Std`
  if (diff < 604800) return `vor ${Math.floor(diff / 86400)} Tagen`
  return formatDate(dateStr)
}

function platformIcon(platform) {
  if (platform === 'tiktok') return 'musical-note'
  return 'camera' // instagram default
}

function statusBadgeClass(status) {
  switch (status) {
    case 'draft': return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
    case 'scheduled': return 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300'
    case 'published': return 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300'
    default: return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
  }
}

onMounted(() => {
  fetchSettings()
  fetchRecentDrafts()
})
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-8" data-tour="create-hub" data-testid="create-hub-view">
    <!-- Header with optional country accent badge -->
    <div class="mb-8">
      <div class="flex items-center gap-3">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Content erstellen</h1>
        <span
          v-if="accentBadge"
          class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border"
          :style="{ borderColor: accentBadge.color, color: accentBadge.color }"
          data-testid="country-accent-badge"
        >
          {{ accentBadge.emoji }} {{ accentBadge.label }}
        </span>
      </div>
      <p class="mt-2 text-gray-600 dark:text-gray-400">
        Waehle eine Erstellungsmethode fuer deinen naechsten Post.
      </p>
    </div>

    <!-- Mode selector cards: 2x2 desktop, 1x4 mobile -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6" data-testid="create-mode-grid">
      <button
        v-for="option in createOptions"
        :key="option.path"
        @click="router.push(option.path)"
        :class="[
          'group relative flex flex-col p-6 rounded-2xl border-2 text-left transition-all duration-200',
          'hover:shadow-xl hover:scale-[1.02] hover:-translate-y-0.5 cursor-pointer',
          'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
          option.lightBg,
          option.border,
          option.hoverBorder,
        ]"
        :style="countryTheme.isCountryTheme.value ? accentStyle : {}"
        :data-testid="`create-card-${option.color}`"
      >
        <!-- Top row: icon + duration badge -->
        <div class="flex items-start justify-between mb-4">
          <!-- Icon circle with Heroicon SVG -->
          <div :class="['flex items-center justify-center w-14 h-14 rounded-xl shrink-0 transition-transform group-hover:scale-110', option.iconBg]">
            <svg
              :class="['w-7 h-7', option.iconColor]"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path stroke-linecap="round" stroke-linejoin="round" :d="option.iconPath" />
            </svg>
          </div>

          <!-- Duration badge -->
          <span :class="['inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold', option.badgeBg]">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {{ option.duration }}
          </span>
        </div>

        <!-- Title + subtitle -->
        <h3 class="text-lg font-bold text-gray-900 dark:text-white group-hover:text-gray-800 dark:group-hover:text-white">
          {{ option.title }}
        </h3>
        <p class="text-sm font-medium text-gray-500 dark:text-gray-400 mt-0.5 mb-2">
          {{ option.subtitle }}
        </p>

        <!-- Description -->
        <p class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed flex-1">
          {{ option.description }}
        </p>

        <!-- Arrow indicator (hover reveal) -->
        <div class="mt-4 flex items-center text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity"
          :class="option.iconColor"
        >
          <span>Starten</span>
          <svg class="w-4 h-4 ml-1 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
          </svg>
        </div>
      </button>
    </div>

    <!-- ─── Letzte Entwuerfe section ──────────────────────────── -->
    <div class="mt-10" data-testid="recent-drafts-section">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Letzte Entwuerfe</h2>
        <router-link
          to="/create/drafts"
          class="text-sm text-blue-600 dark:text-blue-400 hover:underline font-medium"
        >
          Alle anzeigen
        </router-link>
      </div>

      <!-- Loading state -->
      <div v-if="draftsLoading" class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          v-for="i in 3"
          :key="i"
          class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 animate-pulse"
        >
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-3"></div>
          <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
          <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
        </div>
      </div>

      <!-- Empty state -->
      <div
        v-else-if="recentDrafts.length === 0"
        class="bg-white dark:bg-gray-800 rounded-xl border-2 border-dashed border-gray-200 dark:border-gray-700 p-8 text-center"
        data-testid="no-drafts-empty"
      >
        <div class="flex justify-center mb-3">
          <div class="w-12 h-12 rounded-xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
            <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          </div>
        </div>
        <p class="text-sm font-medium text-gray-900 dark:text-white">Noch keine Entwuerfe</p>
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Erstelle deinen ersten Post mit einer der Methoden oben.</p>
      </div>

      <!-- Draft cards -->
      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          v-for="draft in recentDrafts"
          :key="draft.id"
          @click="router.push(`/create/post/${draft.id}/edit`)"
          class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-left hover:shadow-md hover:border-gray-300 dark:hover:border-gray-600 transition-all group cursor-pointer"
          :data-testid="`draft-card-${draft.id}`"
        >
          <!-- Title -->
          <h4 class="text-sm font-semibold text-gray-900 dark:text-white truncate group-hover:text-blue-600 dark:group-hover:text-blue-400">
            {{ draft.title || 'Unbenannter Entwurf' }}
          </h4>

          <!-- Meta: platform + category -->
          <div class="flex items-center gap-2 mt-2">
            <AppIcon :name="platformIcon(draft.platform)" class="w-4 h-4 inline-block" />
            <span v-if="draft.category" class="text-xs text-gray-500 dark:text-gray-400 truncate">
              {{ draft.category }}
            </span>
            <span v-if="draft.country" class="text-xs text-gray-400 dark:text-gray-500">
              · {{ draft.country }}
            </span>
          </div>

          <!-- Status + timestamp -->
          <div class="flex items-center justify-between mt-3">
            <span :class="['text-[10px] font-medium px-1.5 py-0.5 rounded', statusBadgeClass(draft.status)]">
              {{ draft.status === 'draft' ? 'Entwurf' : draft.status }}
            </span>
            <span class="text-[10px] text-gray-400 dark:text-gray-500">
              {{ formatTimeAgo(draft.updated_at || draft.created_at) }}
            </span>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>
