<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ref, computed, onMounted, watch } from 'vue'
import { useTour } from '@/composables/useTour'
import { useToast } from '@/composables/useToast'
import NotificationPanel from '@/components/common/NotificationPanel.vue'
import NotificationHistoryPanel from '@/components/common/NotificationHistoryPanel.vue'
import ProgressIndicator from '@/components/common/ProgressIndicator.vue'
import tourConfigs from '@/tours/tourConfigs'
import { Bars3Icon, SunIcon, MoonIcon, ArrowRightOnRectangleIcon } from '@heroicons/vue/24/outline'

defineEmits(['toggle-sidebar'])

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const isDark = ref(document.documentElement.classList.contains('dark'))
const { requestTourStart, hasSeenTour, loadTourProgress, loadedFromBackend } = useTour()
const { unreadCount, toggleHistoryPanel } = useToast()

// ─── Route-to-tourKey mapping ─────────────────────────────
// Maps route paths to tour config keys
const routeToTourKey = {
  // New routes
  '/home': 'dashboard',
  '/create': 'create-post',
  '/create/quick': 'create-post',
  '/create/smart': 'create-post',
  '/library/templates': 'templates',
  '/library/assets': 'assets',
  '/calendar': 'calendar',
  '/library/history': 'history',
  '/analytics': 'analytics',
  '/settings': 'settings',
  '/students': 'students',
  '/calendar/story-arcs': 'story-arcs',
  '/calendar/week-planner': 'week-planner',
  '/calendar/recurring-formats': 'recurring-formats',
  '/video/export': 'video-export',
  '/video/audio-mixer': 'audio-mixer',
  '/video/thumbnails': 'thumbnail-generator',
  '/video/overlays': 'video-overlays',
  '/video/composer': 'video-composer',
  '/video/templates': 'video-templates',
  // Legacy routes (for redirects)
  '/dashboard': 'dashboard',
  '/create-post': 'create-post',
  '/templates': 'templates',
  '/assets': 'assets',
  '/history': 'history',
  '/story-arcs': 'story-arcs',
  '/week-planner': 'week-planner',
  '/recurring-formats': 'recurring-formats',
  '/video-export': 'video-export',
  '/audio-mixer': 'audio-mixer',
  '/thumbnail-generator': 'thumbnail-generator',
  '/video-overlays': 'video-overlays',
  '/video-composer': 'video-composer',
  '/video-templates': 'video-templates',
}

// Current page tour key (reactive to route changes)
const currentTourKey = computed(() => {
  const path = route.path
  // Direct match
  if (routeToTourKey[path]) return routeToTourKey[path]
  // Prefix match for paths like /students/1 or /story-arcs/2
  for (const [routePath, tourKey] of Object.entries(routeToTourKey)) {
    if (path.startsWith(routePath + '/')) return tourKey
  }
  return null
})

// Whether the current page has a tour available
const hasTourForCurrentPage = computed(() => {
  return currentTourKey.value && tourConfigs[currentTourKey.value]
})

// ─── Pulse animation for first visit ─────────────────────
const showPulse = ref(false)

// Check if this is the first visit to the page (tour not yet seen)
watch(
  () => route.path,
  async () => {
    if (!loadedFromBackend.value) {
      await loadTourProgress()
    }
    if (currentTourKey.value && !hasSeenTour(currentTourKey.value)) {
      showPulse.value = true
      // Stop pulsing after 5 seconds
      setTimeout(() => {
        showPulse.value = false
      }, 5000)
    } else {
      showPulse.value = false
    }
  },
  { immediate: true }
)

// ─── Tooltip ──────────────────────────────────────────────
const showTooltip = ref(false)

// ─── Start tour for current page ─────────────────────────
const startPageTour = () => {
  if (currentTourKey.value) {
    showPulse.value = false
    requestTourStart(currentTourKey.value)
  }
}

const toggleDarkMode = () => {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('darkMode', isDark.value ? 'true' : 'false')
}

const handleLogout = () => {
  auth.logout()
  router.push('/login')
}

// Initialize dark mode from localStorage
if (localStorage.getItem('darkMode') === 'true') {
  document.documentElement.classList.add('dark')
  isDark.value = true
}
</script>

<template>
  <header class="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6 dark:bg-gray-900 dark:border-gray-700" role="banner">
    <div class="flex items-center gap-4">
      <button
        class="md:hidden text-gray-500 hover:text-gray-700 focus-ring rounded-lg p-1"
        @click="$emit('toggle-sidebar')"
        aria-label="Menu"
      >
        <Bars3Icon class="h-6 w-6" />
      </button>
      <h1 class="text-lg font-semibold text-gray-900 dark:text-white">
        {{ route.meta?.title || route.name }}
      </h1>
    </div>

    <div class="flex items-center gap-4">
      <!-- Background Task Progress Indicator -->
      <ProgressIndicator />

      <!-- Series Notification Bell -->
      <NotificationPanel />

      <!-- Notification History Bell -->
      <div class="relative">
        <button
          id="notification-history-bell"
          @click="toggleHistoryPanel"
          class="rounded-lg p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 focus-ring transition-colors relative"
          aria-label="Benachrichtigungs-Verlauf"
          data-testid="notification-history-bell"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"/>
          </svg>
          <!-- Unread badge -->
          <span
            v-if="unreadCount > 0"
            class="absolute -top-0.5 -right-0.5 flex items-center justify-center min-w-[16px] h-4 px-1 text-[9px] font-bold bg-red-500 text-white rounded-full leading-none"
            data-testid="notification-history-badge"
          >
            {{ unreadCount > 9 ? '9+' : unreadCount }}
          </span>
        </button>
      </div>

      <!-- Notification History Panel (slide-in from right) -->
      <NotificationHistoryPanel />

      <!-- Tour Restart Button (visible on ALL authenticated pages) -->
      <div
        class="relative"
        @mouseenter="showTooltip = true"
        @mouseleave="showTooltip = false"
        data-testid="tour-restart-button"
      >
        <button
          @click="startPageTour"
          :disabled="!hasTourForCurrentPage"
          class="relative rounded-lg p-2 transition-colors focus-ring"
          :class="hasTourForCurrentPage
            ? 'text-gray-500 hover:bg-blue-50 hover:text-treff-blue dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-blue-400 cursor-pointer'
            : 'text-gray-300 dark:text-gray-600 cursor-default'"
          :aria-label="hasTourForCurrentPage ? 'Seiten-Tour starten' : 'Keine Tour für diese Seite'"
        >
          <!-- Pulse animation ring on first visit -->
          <span
            v-if="showPulse && hasTourForCurrentPage"
            class="absolute inset-0 rounded-lg animate-ping bg-treff-blue/20"
          ></span>
          <!-- Question mark icon -->
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 relative" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
          </svg>
        </button>

        <!-- Tooltip -->
        <div
          v-if="showTooltip"
          class="absolute right-0 top-full mt-2 z-50 whitespace-nowrap rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white shadow-lg dark:bg-gray-700"
        >
          {{ hasTourForCurrentPage ? 'Seiten-Tour starten' : 'Keine Tour für diese Seite' }}
          <!-- Tooltip arrow -->
          <div class="absolute -top-1 right-3 h-2 w-2 rotate-45 bg-gray-900 dark:bg-gray-700"></div>
        </div>
      </div>

      <!-- Dark mode toggle -->
      <button
        class="rounded-lg p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 focus-ring"
        @click="toggleDarkMode"
        :aria-label="isDark ? 'Heller Modus' : 'Dunkler Modus'"
      >
        <SunIcon v-if="isDark" class="h-5 w-5" />
        <MoonIcon v-else class="h-5 w-5" />
      </button>

      <!-- User info -->
      <span v-if="auth.user" class="text-sm text-gray-600 dark:text-gray-300">
        {{ auth.user.display_name || auth.user.email }}
      </span>

      <!-- Logout -->
      <button
        class="rounded-lg px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 focus-ring inline-flex items-center gap-1.5"
        @click="handleLogout"
      >
        <ArrowRightOnRectangleIcon class="h-4 w-4" />
        Logout
      </button>
    </div>
  </header>
</template>
