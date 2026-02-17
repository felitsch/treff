/**
 * useToast.js — Enhanced Toast Notification Composable
 *
 * Features:
 *  - Standard toasts (success, error, warning, info)
 *  - Action buttons on toasts (e.g. "Im Kalender ansehen")
 *  - Progress notifications for long operations (AI generation, export)
 *  - Notification history panel (persisted in localStorage, last 50 items)
 *  - Unread badge count
 *
 * @see ToastItem.vue — Renders individual toasts (with action + progress)
 * @see ToastContainer.vue — Fixed-position toast container
 * @see NotificationHistoryPanel.vue — Slide-in history panel
 */
import { ref, computed } from 'vue'

const toasts = ref([])
let idCounter = 0
const MAX_VISIBLE = 3
const MAX_HISTORY = 50
const HISTORY_KEY = 'treff_notification_history'
const UNREAD_KEY = 'treff_notification_unread_count'

// ── Notification history (persisted in localStorage) ──────────────
const notificationHistory = ref([])
const unreadCount = ref(0)
const historyPanelOpen = ref(false)

// Load history from localStorage on init
function loadHistory() {
  try {
    var stored = localStorage.getItem(HISTORY_KEY)
    if (stored) {
      notificationHistory.value = JSON.parse(stored)
    }
    var unread = localStorage.getItem(UNREAD_KEY)
    if (unread) {
      unreadCount.value = parseInt(unread, 10) || 0
    }
  } catch (e) {
    notificationHistory.value = []
    unreadCount.value = 0
  }
}

function saveHistory() {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(notificationHistory.value.slice(0, MAX_HISTORY)))
    localStorage.setItem(UNREAD_KEY, String(unreadCount.value))
  } catch (e) { /* storage full, ignore */ }
}

function addToHistory(toast) {
  // Don't add progress toasts that are still in-progress
  if (toast.type === 'progress' && toast.progress < 100) return

  var entry = {
    id: toast.id,
    message: toast.message,
    type: toast.type === 'progress' ? 'success' : toast.type,
    timestamp: new Date().toISOString(),
    actionLabel: toast.action ? toast.action.label : null,
    read: false,
  }
  notificationHistory.value.unshift(entry)
  // Trim to max history
  if (notificationHistory.value.length > MAX_HISTORY) {
    notificationHistory.value = notificationHistory.value.slice(0, MAX_HISTORY)
  }
  unreadCount.value++
  saveHistory()
}

// Load on module init
loadHistory()

export function useToast() {
  const visibleToasts = computed(() => toasts.value.slice(-MAX_VISIBLE))

  /**
   * Add a toast notification.
   *
   * @param {Object} options
   * @param {string} options.message - Toast message text
   * @param {string} [options.type='success'] - 'success' | 'error' | 'warning' | 'info' | 'progress'
   * @param {number} [options.duration=5000] - Auto-dismiss after ms (0 = manual dismiss only)
   * @param {Object} [options.action] - Optional action button
   * @param {string} options.action.label - Button text (e.g. "Im Kalender ansehen")
   * @param {Function} options.action.onClick - Click handler
   * @param {number} [options.progress=0] - Initial progress (0-100) for type 'progress'
   * @returns {number} Toast ID (use for updateProgress)
   */
  function addToast({ message, type = 'success', duration = 5000, action = null, progress = 0 }) {
    const id = ++idCounter
    const toast = {
      id,
      message,
      type,
      visible: true,
      action: action || null,
      progress: type === 'progress' ? progress : null,
    }
    toasts.value.push(toast)

    // FIFO: remove oldest when exceeding max
    while (toasts.value.length > MAX_VISIBLE) {
      var oldest = toasts.value[0]
      if (oldest) {
        // Add completed non-progress toasts to history before removing
        if (oldest.type !== 'progress') {
          addToHistory(oldest)
        }
        toasts.value.shift()
      }
    }

    // For non-progress toasts, auto-dismiss and add to history
    if (type !== 'progress' && duration > 0) {
      setTimeout(function() {
        addToHistory(toast)
        removeToast(id)
      }, duration)
    }

    // Progress toasts don't auto-dismiss; they complete via updateProgress
    if (type === 'progress') {
      // No auto-dismiss for progress toasts
    }

    return id
  }

  function removeToast(id) {
    var idx = toasts.value.findIndex(function(t) { return t.id === id })
    if (idx !== -1) {
      toasts.value[idx].visible = false
      // Remove from array after transition
      setTimeout(function() {
        toasts.value = toasts.value.filter(function(t) { return t.id !== id })
      }, 300)
    }
  }

  /**
   * Update progress on a progress-type toast.
   * When progress reaches 100, automatically converts to success and auto-dismisses.
   *
   * @param {number} id - Toast ID returned from addToast
   * @param {number} newProgress - Progress value (0-100)
   * @param {string} [newMessage] - Optional updated message
   */
  function updateProgress(id, newProgress, newMessage) {
    var toast = toasts.value.find(function(t) { return t.id === id })
    if (!toast) return

    toast.progress = Math.min(100, Math.max(0, newProgress))

    if (newMessage) {
      toast.message = newMessage
    }

    // Auto-complete at 100%
    if (toast.progress >= 100) {
      toast.type = 'success'
      toast.progress = null
      // Add to history and auto-dismiss after 3 seconds
      setTimeout(function() {
        addToHistory(toast)
        removeToast(id)
      }, 3000)
    }
  }

  function clear() {
    toasts.value = []
  }

  /**
   * Success toast with optional action button.
   * @param {string} message
   * @param {Object} [options] - { duration, action: { label, onClick } }
   */
  function success(message, options) {
    var duration = 5000
    var action = null
    if (typeof options === 'number') {
      duration = options
    } else if (options && typeof options === 'object') {
      duration = options.duration || 5000
      action = options.action || null
    }
    return addToast({ message, type: 'success', duration, action })
  }

  function error(message, options) {
    var duration = 0
    var action = null
    if (typeof options === 'number') {
      duration = options
    } else if (options && typeof options === 'object') {
      duration = options.duration || 0
      action = options.action || null
    }
    return addToast({ message, type: 'error', duration, action })
  }

  function warning(message, options) {
    var duration = 5000
    var action = null
    if (typeof options === 'number') {
      duration = options
    } else if (options && typeof options === 'object') {
      duration = options.duration || 5000
      action = options.action || null
    }
    return addToast({ message, type: 'warning', duration, action })
  }

  function info(message, options) {
    var duration = 5000
    var action = null
    if (typeof options === 'number') {
      duration = options
    } else if (options && typeof options === 'object') {
      duration = options.duration || 5000
      action = options.action || null
    }
    return addToast({ message, type: 'info', duration, action })
  }

  /**
   * Start a progress notification for long-running operations.
   * Returns the toast ID to update progress via updateProgress().
   *
   * @param {string} message - e.g. "KI generiert Texte..."
   * @param {number} [initialProgress=0] - Starting progress (0-100)
   * @returns {number} Toast ID
   */
  function progress(message, initialProgress) {
    return addToast({ message, type: 'progress', duration: 0, progress: initialProgress || 0 })
  }

  // ── Notification History API ──────────────────────────
  function clearHistory() {
    notificationHistory.value = []
    unreadCount.value = 0
    saveHistory()
  }

  function markAllRead() {
    notificationHistory.value.forEach(function(n) { n.read = true })
    unreadCount.value = 0
    saveHistory()
  }

  function markRead(notificationId) {
    var n = notificationHistory.value.find(function(x) { return x.id === notificationId })
    if (n && !n.read) {
      n.read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
      saveHistory()
    }
  }

  function removeFromHistory(notificationId) {
    var idx = notificationHistory.value.findIndex(function(x) { return x.id === notificationId })
    if (idx !== -1) {
      if (!notificationHistory.value[idx].read) {
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
      notificationHistory.value.splice(idx, 1)
      saveHistory()
    }
  }

  function toggleHistoryPanel() {
    historyPanelOpen.value = !historyPanelOpen.value
  }

  function closeHistoryPanel() {
    historyPanelOpen.value = false
  }

  return {
    // Active toasts
    toasts,
    visibleToasts,
    addToast,
    removeToast,
    updateProgress,
    clear,
    // Shorthand methods
    success,
    warning,
    info,
    error,
    progress,
    // Notification history
    notificationHistory,
    unreadCount,
    historyPanelOpen,
    clearHistory,
    markAllRead,
    markRead,
    removeFromHistory,
    toggleHistoryPanel,
    closeHistoryPanel,
  }
}
