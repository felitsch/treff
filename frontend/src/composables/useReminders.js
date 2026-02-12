import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const POLL_INTERVAL_MS = 60000 // Check every 60 seconds
const activeReminders = ref([])
const acknowledgedIds = new Set() // Track already-shown reminders in this session
let pollTimer = null
let isPolling = false

export function useReminders() {
  const toast = useToast()

  async function checkReminders() {
    if (isPolling) return
    isPolling = true

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        isPolling = false
        return
      }

      const response = await api.get('/api/calendar/reminders')
      const reminders = response.data.reminders || []

      // Show notification for each new reminder not yet acknowledged in this session
      for (const reminder of reminders) {
        if (!acknowledgedIds.has(reminder.id)) {
          acknowledgedIds.add(reminder.id)

          // Build notification message referencing the correct post
          const timeStr = reminder.scheduled_time || '00:00'
          const dateStr = formatDate(reminder.scheduled_date)
          const title = reminder.title || 'Unbenannter Post'
          const platform = formatPlatform(reminder.platform)

          const message = `\uD83D\uDD14 Post faellig: "${title}" (${platform}) war fuer ${dateStr} um ${timeStr} Uhr geplant.`

          // Show as info toast with longer duration (15 seconds)
          toast.addToast({
            message,
            type: 'info',
            duration: 15000,
          })
        }
      }

      activeReminders.value = reminders
    } catch (err) {
      // Silently ignore errors during polling (e.g., network issues, 401)
      // The API interceptor already handles token refresh
    } finally {
      isPolling = false
    }
  }

  function formatDate(dateStr) {
    if (!dateStr) return ''
    try {
      const d = new Date(dateStr + 'T00:00:00')
      return d.toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      })
    } catch {
      return dateStr
    }
  }

  function formatPlatform(platform) {
    const map = {
      instagram_feed: 'IG Feed',
      instagram_story: 'IG Story',
      tiktok: 'TikTok',
    }
    return map[platform] || platform || ''
  }

  async function acknowledgeReminder(postId) {
    try {
      await api.put(`/api/calendar/reminders/${postId}/acknowledge`)
      // Remove from active reminders
      activeReminders.value = activeReminders.value.filter(r => r.id !== postId)
    } catch (err) {
      // Error already handled by API interceptor
    }
  }

  function startPolling() {
    // Check immediately
    checkReminders()

    // Then poll periodically
    if (!pollTimer) {
      pollTimer = setInterval(checkReminders, POLL_INTERVAL_MS)
    }
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  return {
    activeReminders,
    checkReminders,
    acknowledgeReminder,
    startPolling,
    stopPolling,
  }
}
