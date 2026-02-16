/**
 * useBackgroundTasks composable
 *
 * Provides reactive state for background task management:
 * - Polls /api/tasks/active every 3s while tasks are running
 * - Exposes activeTasks, taskHistory, and helper methods
 * - Used by ProgressIndicator (TopBar) and TaskHistory view
 */

import { ref, computed, onUnmounted } from 'vue'
import api from '@/utils/api'

const activeTasks = ref([])
const taskHistory = ref([])
const taskHistoryTotal = ref(0)
const isPolling = ref(false)

let pollInterval = null
let currentSpeed = 'slow'
const POLL_INTERVAL_MS = 3000
const SLOW_POLL_INTERVAL_MS = 30000

/**
 * Start polling for active tasks.
 * Polls quickly (3s) when tasks are active, slowly (30s) otherwise.
 */
function startPolling(speed = 'slow') {
  if (pollInterval && currentSpeed === speed) return
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
  isPolling.value = true
  currentSpeed = speed
  fetchActiveTasks()
  const interval = speed === 'fast' ? POLL_INTERVAL_MS : SLOW_POLL_INTERVAL_MS
  pollInterval = setInterval(() => {
    fetchActiveTasks()
  }, interval)
}

function stopPolling() {
  isPolling.value = false
  currentSpeed = 'slow'
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

async function fetchActiveTasks() {
  try {
    const { data } = await api.get('/api/tasks/active')
    const hadTasks = activeTasks.value.length > 0
    activeTasks.value = data.tasks || []
    const hasTasks = activeTasks.value.length > 0
    // Dynamically switch polling speed
    if (hasTasks && currentSpeed !== 'fast') {
      startPolling('fast')
    } else if (!hasTasks && currentSpeed !== 'slow') {
      startPolling('slow')
    }
  } catch (err) {
    // Silently fail — don't interrupt user
  }
}

async function fetchTaskHistory(status = null, limit = 20, offset = 0) {
  try {
    const params = { limit, offset }
    if (status) params.status = status
    const { data } = await api.get('/api/tasks/history', { params })
    taskHistory.value = data.items || []
    taskHistoryTotal.value = data.total || 0
    return data
  } catch (err) {
    return { items: [], total: 0 }
  }
}

async function submitDemoTask(title = 'Demo-Task', durationSeconds = 10, shouldFail = false) {
  try {
    const { data } = await api.post('/api/tasks/submit-demo', {
      title,
      duration_seconds: durationSeconds,
      should_fail: shouldFail,
    })
    // Immediately switch to fast polling
    startPolling('fast')
    return data
  } catch (err) {
    throw err
  }
}

async function cancelTask(taskId) {
  try {
    const { data } = await api.post(`/api/tasks/cancel/${taskId}`)
    await fetchActiveTasks()
    return data
  } catch (err) {
    throw err
  }
}

async function getTaskStatus(taskId) {
  try {
    const { data } = await api.get(`/api/tasks/status/${taskId}`)
    return data
  } catch (err) {
    return null
  }
}

const activeTaskCount = computed(() => activeTasks.value.length)
const hasActiveTasks = computed(() => activeTasks.value.length > 0)

export function useBackgroundTasks() {
  return {
    activeTasks,
    activeTaskCount,
    hasActiveTasks,
    taskHistory,
    taskHistoryTotal,
    isPolling,
    startPolling,
    stopPolling,
    fetchActiveTasks,
    fetchTaskHistory,
    submitDemoTask,
    cancelTask,
    getTaskStatus,
  }
}
