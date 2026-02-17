<script setup>
/**
 * NotificationHistoryPanel.vue — Notification History Slide-In Panel
 *
 * Displays a history of all past toast notifications (last 50).
 * Features:
 *  - Slide-in from the right side
 *  - Unread/read state with visual indicator
 *  - Mark all as read
 *  - Clear history
 *  - Relative timestamps (Vor X Min., Vor X Std., etc.)
 *  - Type-specific icons and colors
 *  - Dismiss individual notifications
 *
 * Triggered by a bell icon in the TopBar header.
 *
 * @see useToast.js — Provides notificationHistory, unreadCount, etc.
 * @see TopBar.vue — Contains the bell icon trigger
 */
import { computed, onMounted, onUnmounted } from 'vue'
import { useToast } from '@/composables/useToast'

const {
  notificationHistory,
  unreadCount,
  historyPanelOpen,
  markAllRead,
  markRead,
  removeFromHistory,
  clearHistory,
  closeHistoryPanel,
} = useToast()

// ── Click outside to close ──────────────────────────
function handleClickOutside(e) {
  var panel = document.getElementById('notification-history-panel')
  var bellBtn = document.getElementById('notification-history-bell')
  if (panel && !panel.contains(e.target) && bellBtn && !bellBtn.contains(e.target)) {
    closeHistoryPanel()
  }
}

onMounted(function() {
  document.addEventListener('click', handleClickOutside, true)
})

onUnmounted(function() {
  document.removeEventListener('click', handleClickOutside, true)
})

// ── Type config ──────────────────────────
function getTypeConfig(type) {
  switch (type) {
    case 'success': return { icon: '\u2713', label: 'Erfolg', bg: 'bg-green-100 dark:bg-green-900/40', text: 'text-green-700 dark:text-green-300', dot: 'bg-green-500' }
    case 'error': return { icon: '\u2716', label: 'Fehler', bg: 'bg-red-100 dark:bg-red-900/40', text: 'text-red-700 dark:text-red-300', dot: 'bg-red-500' }
    case 'warning': return { icon: '\u26A0', label: 'Warnung', bg: 'bg-yellow-100 dark:bg-yellow-900/40', text: 'text-yellow-700 dark:text-yellow-300', dot: 'bg-yellow-500' }
    case 'info': return { icon: '\u2139', label: 'Info', bg: 'bg-blue-100 dark:bg-blue-900/40', text: 'text-blue-700 dark:text-blue-300', dot: 'bg-blue-500' }
    default: return { icon: '\u2139', label: 'Info', bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-700 dark:text-gray-300', dot: 'bg-gray-500' }
  }
}

// ── Relative time formatting ──────────────────────────
function formatRelativeTime(isoString) {
  var now = new Date()
  var then = new Date(isoString)
  var diff = Math.floor((now - then) / 1000)

  if (diff < 60) return 'Gerade eben'
  if (diff < 3600) return 'Vor ' + Math.floor(diff / 60) + ' Min.'
  if (diff < 86400) return 'Vor ' + Math.floor(diff / 3600) + ' Std.'
  if (diff < 604800) return 'Vor ' + Math.floor(diff / 86400) + ' Tag' + (Math.floor(diff / 86400) > 1 ? 'en' : '')
  return then.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const isEmpty = computed(function() {
  return notificationHistory.value.length === 0
})
</script>

<template>
  <Transition
    enter-active-class="transition-all duration-300 ease-out"
    enter-from-class="translate-x-full opacity-0"
    enter-to-class="translate-x-0 opacity-100"
    leave-active-class="transition-all duration-200 ease-in"
    leave-from-class="translate-x-0 opacity-100"
    leave-to-class="translate-x-full opacity-0"
  >
    <div
      v-if="historyPanelOpen"
      id="notification-history-panel"
      class="fixed top-0 right-0 bottom-0 w-96 max-w-[90vw] bg-white dark:bg-gray-900 shadow-2xl border-l border-gray-200 dark:border-gray-700 z-[9998] flex flex-col"
      data-testid="notification-history-panel"
      role="dialog"
      aria-label="Benachrichtigungs-Verlauf"
    >
      <!-- Header -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 flex-shrink-0">
        <div class="flex items-center gap-2">
          <span class="text-lg">&#x1F514;</span>
          <h2 class="text-sm font-bold text-gray-900 dark:text-white">Benachrichtigungen</h2>
          <span
            v-if="unreadCount > 0"
            class="px-1.5 py-0.5 text-[10px] font-bold bg-red-500 text-white rounded-full"
          >
            {{ unreadCount > 9 ? '9+' : unreadCount }}
          </span>
        </div>

        <div class="flex items-center gap-1">
          <!-- Mark all read -->
          <button
            v-if="unreadCount > 0"
            @click="markAllRead"
            class="px-2 py-1 text-[11px] font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded transition-colors"
            data-testid="notification-mark-all-read"
          >
            Alle gelesen
          </button>

          <!-- Clear history -->
          <button
            v-if="!isEmpty"
            @click="clearHistory"
            class="px-2 py-1 text-[11px] font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
            data-testid="notification-clear-history"
          >
            Leeren
          </button>

          <!-- Close button -->
          <button
            @click="closeHistoryPanel"
            class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded transition-colors"
            aria-label="Panel schließen"
            data-testid="notification-history-close"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Notification list -->
      <div class="flex-1 overflow-y-auto">
        <!-- Empty state -->
        <div
          v-if="isEmpty"
          class="flex flex-col items-center justify-center h-full text-center p-6"
        >
          <span class="text-4xl mb-3 opacity-30">&#x1F514;</span>
          <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Keine Benachrichtigungen</p>
          <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Neue Benachrichtigungen erscheinen hier</p>
        </div>

        <!-- Notification items -->
        <div v-else>
          <div
            v-for="notification in notificationHistory"
            :key="notification.id"
            class="relative px-4 py-3 border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors group"
            :class="{ 'bg-blue-50/40 dark:bg-blue-900/10': !notification.read }"
            @click="markRead(notification.id)"
            data-testid="notification-history-item"
          >
            <!-- Unread dot indicator -->
            <div
              v-if="!notification.read"
              class="absolute left-1.5 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-blue-500"
              data-testid="notification-unread-dot"
            ></div>

            <div class="flex items-start gap-3">
              <!-- Type icon -->
              <span
                class="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
                :class="[getTypeConfig(notification.type).bg, getTypeConfig(notification.type).text]"
              >
                {{ getTypeConfig(notification.type).icon }}
              </span>

              <!-- Content -->
              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between gap-2">
                  <p class="text-sm text-gray-900 dark:text-white" :class="{ 'font-semibold': !notification.read }">
                    {{ notification.message }}
                  </p>
                  <!-- Dismiss button (visible on hover) -->
                  <button
                    @click.stop="removeFromHistory(notification.id)"
                    class="flex-shrink-0 opacity-0 group-hover:opacity-60 hover:!opacity-100 transition-opacity text-gray-400 dark:text-gray-500 text-sm"
                    aria-label="Entfernen"
                  >
                    &times;
                  </button>
                </div>

                <div class="flex items-center gap-2 mt-1">
                  <!-- Type badge -->
                  <span
                    class="text-[10px] font-medium px-1.5 py-0.5 rounded-full"
                    :class="[getTypeConfig(notification.type).bg, getTypeConfig(notification.type).text]"
                  >
                    {{ getTypeConfig(notification.type).label }}
                  </span>
                  <!-- Action label if present -->
                  <span
                    v-if="notification.actionLabel"
                    class="text-[10px] text-gray-400 dark:text-gray-500"
                  >
                    &#8594; {{ notification.actionLabel }}
                  </span>
                  <!-- Timestamp -->
                  <span class="text-[10px] text-gray-400 dark:text-gray-500 ml-auto">
                    {{ formatRelativeTime(notification.timestamp) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex-shrink-0 px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
        <p class="text-[10px] text-gray-400 dark:text-gray-500 text-center">
          Letzte {{ notificationHistory.length }} Benachrichtigungen (max. 50)
        </p>
      </div>
    </div>
  </Transition>
</template>
