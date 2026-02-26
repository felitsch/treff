/**
 * useTour composable - manages page-level tour state.
 *
 * Tracks which page tours the user has already seen (via backend settings),
 * exposes helpers to start / complete / skip a tour, and auto-triggers tours
 * on first visit.
 *
 * Also provides a shared "tour start request" mechanism:
 *   - requestTourStart(pageKey) – called from TopBar to request a tour restart
 *   - tourStartRequest – reactive ref that TourSystem watches to auto-trigger
 *   - clearTourStartRequest() – called by TourSystem after handling the request
 */
import { ref, readonly } from 'vue'
import api from '@/utils/api'

// LocalStorage key for fast synchronous tour persistence (resilient to API failures)
const TOUR_STORAGE_KEY = 'treff_tour_progress'

// Module-level cache so every component shares the same state
const seenTours = ref(loadFromLocalStorage())       // { dashboard: true, templates: true, ... }
const loadedFromBackend = ref(false)
const loading = ref(false)

/**
 * Load tour progress from localStorage synchronously.
 * This ensures tours are never shown again even if the backend API is slow or fails.
 */
function loadFromLocalStorage() {
  try {
    const stored = localStorage.getItem(TOUR_STORAGE_KEY)
    if (stored) return JSON.parse(stored)
  } catch {
    // Corrupted data – ignore
  }
  return {}
}

/**
 * Persist tour progress to localStorage for instant access on next page load.
 */
function saveToLocalStorage(data) {
  try {
    localStorage.setItem(TOUR_STORAGE_KEY, JSON.stringify(data))
  } catch {
    // Storage full – ignore
  }
}

// Tour start request – a shared reactive ref for cross-component communication
// When TopBar sets this to a pageKey, the matching TourSystem picks it up
const tourStartRequest = ref(null)  // null | { pageKey: string, timestamp: number }

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
        const backendData = JSON.parse(raw)
        // Merge: a tour marked as seen in either source stays seen
        seenTours.value = { ...seenTours.value, ...backendData }
        saveToLocalStorage(seenTours.value)
      } catch {
        // Keep localStorage data if backend data is corrupted
      }
    }
    loadedFromBackend.value = true
  } catch {
    // Silently fail – localStorage data is already loaded as fallback
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
 * Saves to both localStorage (instant) and backend (durable).
 */
async function markTourSeen(pageKey) {
  seenTours.value = { ...seenTours.value, [pageKey]: true }
  saveToLocalStorage(seenTours.value)
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
  saveToLocalStorage(seenTours.value)
  await saveTourProgress()
}

/**
 * Reset all tours.
 */
async function resetAllTours() {
  seenTours.value = {}
  saveToLocalStorage(seenTours.value)
  await saveTourProgress()
}

/**
 * Request a tour start for the given page key.
 * The TopBar calls this; the matching TourSystem component picks it up.
 */
function requestTourStart(pageKey) {
  tourStartRequest.value = { pageKey, timestamp: Date.now() }
}

/**
 * Clear the tour start request (called by TourSystem after handling).
 */
function clearTourStartRequest() {
  tourStartRequest.value = null
}

export function useTour() {
  return {
    seenTours: readonly(seenTours),
    loadedFromBackend: readonly(loadedFromBackend),
    tourStartRequest: readonly(tourStartRequest),
    loadTourProgress,
    markTourSeen,
    hasSeenTour,
    resetTour,
    resetAllTours,
    requestTourStart,
    clearTourStartRequest,
  }
}
