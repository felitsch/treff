<script setup>
import { ref, onMounted, onUnmounted, markRaw } from 'vue'
import { useSeriesReminders } from '@/composables/useSeriesReminders'
import { BellIcon, CalendarDaysIcon, PauseCircleIcon, FlagIcon, ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/vue/24/outline'
import { BellIcon as BellSolidIcon } from '@heroicons/vue/24/solid'

const { reminders, unreadCount, loading, fetchReminders, markRead, markAllRead, dismissReminder } = useSeriesReminders()

const isOpen = ref(false)

function togglePanel() {
  isOpen.value = !isOpen.value
  if (isOpen.value && reminders.value.length === 0) {
    fetchReminders()
  }
}

function closePanel() {
  isOpen.value = false
}

function handleClickOutside(e) {
  const panel = document.getElementById('notification-panel')
  const btn = document.getElementById('notification-bell-btn')
  if (panel && !panel.contains(e.target) && btn && !btn.contains(e.target)) {
    closePanel()
  }
}

function handleMarkRead(id) {
  markRead(id)
}

function handleDismiss(id) {
  dismissReminder(id)
}

function handleMarkAllRead() {
  markAllRead()
}

// Reminder type styling
function typeIcon(type) {
  const icons = {
    upcoming_episode: markRaw(CalendarDaysIcon),
    series_paused: markRaw(PauseCircleIcon),
    series_ending: markRaw(FlagIcon),
    gap_warning: markRaw(ExclamationTriangleIcon),
  }
  return icons[type] || markRaw(BellIcon)
}

function typeLabel(type) {
  const labels = {
    upcoming_episode: 'Episode fällig',
    series_paused: 'Serie pausiert',
    series_ending: 'Letzte Episode',
    gap_warning: 'Lücke erkannt',
  }
  return labels[type] || type
}

function typeBadgeClass(type) {
  const classes = {
    upcoming_episode: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    series_paused: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
    series_ending: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    gap_warning: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
  }
  return classes[type] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
}

function countryFlag(country) {
  const flags = {
    usa: '\uD83C\uDDFA\uD83C\uDDF8',
    kanada: '\uD83C\uDDE8\uD83C\uDDE6',
    australien: '\uD83C\uDDE6\uD83C\uDDFA',
    neuseeland: '\uD83C\uDDF3\uD83C\uDDFF',
    irland: '\uD83C\uDDEE\uD83C\uDDEA',
  }
  return flags[country] || ''
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    const now = new Date()
    const diffMs = now - d
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Gerade eben'
    if (diffMins < 60) return `Vor ${diffMins} Min.`
    if (diffHours < 24) return `Vor ${diffHours} Std.`
    if (diffDays < 7) return `Vor ${diffDays} Tag${diffDays > 1 ? 'en' : ''}`
    return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' })
  } catch {
    return ''
  }
}

// Icon components for template usage
const BellIconComponent = markRaw(BellSolidIcon)
const CheckCircleComponent = markRaw(CheckCircleIcon)

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="relative">
    <!-- Notification Bell Button -->
    <button
      id="notification-bell-btn"
      @click="togglePanel"
      class="relative rounded-lg p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 focus-ring"
      aria-label="Serien-Benachrichtigungen"
      data-testid="notification-bell"
    >
      <BellSolidIcon class="h-5 w-5 text-yellow-500" />
      <!-- Unread badge -->
      <span
        v-if="unreadCount > 0"
        class="absolute -top-0.5 -right-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white ring-2 ring-white dark:ring-gray-900"
        data-testid="notification-badge"
      >
        {{ unreadCount > 9 ? '9+' : unreadCount }}
      </span>
    </button>

    <!-- Notification Panel Dropdown -->
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-1"
    >
      <div
        v-if="isOpen"
        id="notification-panel"
        class="absolute right-0 top-12 z-50 w-96 max-h-[480px] rounded-xl border border-gray-200 bg-white shadow-xl dark:border-gray-700 dark:bg-gray-800 overflow-hidden"
        data-testid="notification-panel"
      >
        <!-- Header -->
        <div class="flex items-center justify-between border-b border-gray-100 dark:border-gray-700 px-4 py-3">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <BellSolidIcon class="h-4 w-4 text-yellow-500" /> Serien-Erinnerungen
          </h3>
          <div class="flex items-center gap-2">
            <button
              v-if="unreadCount > 0"
              @click="handleMarkAllRead"
              class="text-xs text-treff-blue hover:text-blue-600 dark:hover:text-blue-400 font-medium"
              data-testid="mark-all-read-btn"
            >
              Alle gelesen
            </button>
            <button
              @click="closePanel"
              class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"
              aria-label="Schließen"
            >
              &#x2715;
            </button>
          </div>
        </div>

        <!-- Reminders List -->
        <div class="overflow-y-auto max-h-[400px]">
          <!-- Loading -->
          <div v-if="loading" class="p-6 text-center">
            <svg class="animate-spin inline-block h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>
            <p class="text-sm text-gray-400 mt-2">Lade Erinnerungen...</p>
          </div>

          <!-- Empty state -->
          <div v-else-if="reminders.length === 0" class="p-6 text-center">
            <CheckCircleIcon class="h-8 w-8 text-green-500 mx-auto mb-2" />
            <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Keine Erinnerungen</p>
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
              Alle Serien sind auf dem neuesten Stand!
            </p>
          </div>

          <!-- Reminder items -->
          <div v-else>
            <div
              v-for="reminder in reminders"
              :key="reminder.id"
              class="border-b border-gray-50 dark:border-gray-700/50 last:border-b-0 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
              :class="{ 'bg-blue-50/50 dark:bg-blue-900/10': !reminder.is_read }"
              data-testid="reminder-item"
            >
              <div class="flex items-start gap-3">
                <!-- Type icon -->
                <div class="mt-0.5 flex-shrink-0">
                  <component :is="typeIcon(reminder.reminder_type)" class="h-5 w-5 text-gray-500 dark:text-gray-400" />
                </div>

                <!-- Content -->
                <div class="flex-1 min-w-0">
                  <!-- Type badge + time -->
                  <div class="flex items-center gap-2 mb-1">
                    <span
                      class="inline-flex items-center text-[10px] font-semibold px-1.5 py-0.5 rounded-full uppercase tracking-wide"
                      :class="typeBadgeClass(reminder.reminder_type)"
                    >
                      {{ typeLabel(reminder.reminder_type) }}
                    </span>
                    <span v-if="reminder.arc_country" class="text-xs">
                      {{ countryFlag(reminder.arc_country) }}
                    </span>
                    <span class="text-[10px] text-gray-400 dark:text-gray-500 ml-auto flex-shrink-0">
                      {{ formatRelativeTime(reminder.created_at) }}
                    </span>
                  </div>

                  <!-- Title -->
                  <p
                    class="text-sm font-medium truncate"
                    :class="reminder.is_read ? 'text-gray-600 dark:text-gray-400' : 'text-gray-900 dark:text-white'"
                  >
                    {{ reminder.title }}
                  </p>

                  <!-- Message -->
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">
                    {{ reminder.message }}
                  </p>

                  <!-- Actions -->
                  <div class="flex items-center gap-2 mt-2">
                    <button
                      v-if="!reminder.is_read"
                      @click="handleMarkRead(reminder.id)"
                      class="text-[11px] font-medium text-treff-blue hover:text-blue-600 dark:hover:text-blue-400"
                      data-testid="mark-read-btn"
                    >
                      Als gelesen markieren
                    </button>
                    <button
                      @click="handleDismiss(reminder.id)"
                      class="text-[11px] font-medium text-gray-400 hover:text-red-500 dark:hover:text-red-400"
                      data-testid="dismiss-btn"
                    >
                      Verwerfen
                    </button>
                  </div>
                </div>

                <!-- Unread dot -->
                <div v-if="!reminder.is_read" class="mt-2 flex-shrink-0">
                  <div class="w-2 h-2 rounded-full bg-treff-blue"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>
