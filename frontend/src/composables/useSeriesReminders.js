import { ref } from 'vue'
import api from '@/utils/api'

const POLL_INTERVAL_MS = 60000 // Check every 60 seconds
const reminders = ref([])
const unreadCount = ref(0)
const loading = ref(false)
let pollTimer = null
let isPolling = false

export function useSeriesReminders() {
  /**
   * Fetch all non-dismissed reminders from the server.
   */
  async function fetchReminders() {
    loading.value = true
    try {
      const token = localStorage.getItem('access_token')
      if (!token) return

      const response = await api.get('/api/series-reminders')
      reminders.value = response.data.reminders || []
      unreadCount.value = response.data.unread_count || 0
    } catch (err) {
      // Silently ignore - polling should not interrupt UX
    } finally {
      loading.value = false
    }
  }

  /**
   * Get unread count only (lightweight endpoint for badge).
   */
  async function fetchUnreadCount() {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) return

      const response = await api.get('/api/series-reminders/unread-count')
      unreadCount.value = response.data.unread_count || 0
    } catch (err) {
      // Silently ignore
    }
  }

  /**
   * Run the series check to generate new reminders (calls backend check logic).
   */
  async function checkAndGenerate() {
    if (isPolling) return
    isPolling = true
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        isPolling = false
        return
      }

      await api.post('/api/series-reminders/check')
      // After check, fetch the updated list
      await fetchReminders()
    } catch (err) {
      // Silently ignore
    } finally {
      isPolling = false
    }
  }

  /**
   * Mark a single reminder as read.
   */
  async function markRead(reminderId) {
    try {
      await api.put(`/api/series-reminders/${reminderId}/read`)
      // Update local state
      const r = reminders.value.find(r => r.id === reminderId)
      if (r) r.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch (err) {
      // Error handled by API interceptor
    }
  }

  /**
   * Mark all reminders as read.
   */
  async function markAllRead() {
    try {
      await api.put('/api/series-reminders/read-all')
      reminders.value.forEach(r => { r.is_read = true })
      unreadCount.value = 0
    } catch (err) {
      // Error handled by API interceptor
    }
  }

  /**
   * Dismiss a reminder (remove from list).
   */
  async function dismissReminder(reminderId) {
    try {
      await api.put(`/api/series-reminders/${reminderId}/dismiss`)
      reminders.value = reminders.value.filter(r => r.id !== reminderId)
      // Recount unread
      unreadCount.value = reminders.value.filter(r => !r.is_read).length
    } catch (err) {
      // Error handled by API interceptor
    }
  }

  /**
   * Start polling: run check immediately then at intervals.
   */
  function startPolling() {
    checkAndGenerate()
    if (!pollTimer) {
      pollTimer = setInterval(checkAndGenerate, POLL_INTERVAL_MS)
    }
  }

  /**
   * Stop polling.
   */
  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  return {
    reminders,
    unreadCount,
    loading,
    fetchReminders,
    fetchUnreadCount,
    checkAndGenerate,
    markRead,
    markAllRead,
    dismissReminder,
    startPolling,
    stopPolling,
  }
}
