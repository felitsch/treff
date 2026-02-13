/**
 * useTour composable - manages page-level tour state.
 *
 * Tracks which page tours the user has already seen (via backend settings),
 * exposes helpers to start / complete / skip a tour, and auto-triggers tours
 * on first visit.
 */
import { ref, readonly } from 'vue'
import api from '@/utils/api'

// Module-level cache so every component shares the same state
const seenTours = ref({})       // { dashboard: true, templates: true, ... }
const loadedFromBackend = ref(false)
const loading = ref(false)

/**
 * Load the tour_progress setting from the backend once per session.
 * The value is stored as a JSON string under the key "tour_progress".
 */
async function loadTourProgress() {
  if (loadedFromBackend.value) return
  if (loading.value) return
  loading.value = true
  try {
    const res = await api.get('/api/settings')
    const raw = res.data?.tour_progress
    if (raw) {
      try {
        seenTours.value = JSON.parse(raw)
      } catch {
        seenTours.value = {}
      }
    }
    loadedFromBackend.value = true
  } catch {
    // Silently fail – tour will just show again
  } finally {
    loading.value = false
  }
}

/**
 * Persist the current seenTours map to the backend.
 */
async function saveTourProgress() {
  try {
    await api.put('/api/settings', {
      tour_progress: JSON.stringify(seenTours.value),
    })
  } catch {
    // Best-effort
  }
}

/**
 * Mark a page tour as completed/seen.
 */
async function markTourSeen(pageKey) {
  seenTours.value = { ...seenTours.value, [pageKey]: true }
  await saveTourProgress()
}

/**
 * Check whether the user has already seen a page tour.
 */
function hasSeenTour(pageKey) {
  return !!seenTours.value[pageKey]
}

/**
 * Reset a single tour so it will auto-trigger again on next visit.
 */
async function resetTour(pageKey) {
  const copy = { ...seenTours.value }
  delete copy[pageKey]
  seenTours.value = copy
  await saveTourProgress()
}

/**
 * Reset all tours.
 */
async function resetAllTours() {
  seenTours.value = {}
  await saveTourProgress()
}

export function useTour() {
  return {
    seenTours: readonly(seenTours),
    loadedFromBackend: readonly(loadedFromBackend),
    loadTourProgress,
    markTourSeen,
    hasSeenTour,
    resetTour,
    resetAllTours,
  }
}
