import { ref, onMounted } from 'vue'

const STORAGE_KEY = 'treff_dismissed_hints'

/**
 * Composable for managing contextual workflow hints.
 * Each hint has an ID, and dismissed state is persisted in localStorage.
 */
export function useWorkflowHints() {
  const dismissedHints = ref(new Set())

  // Load dismissed hints from localStorage on first use
  function loadDismissed() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const arr = JSON.parse(stored)
        if (Array.isArray(arr)) {
          dismissedHints.value = new Set(arr)
        }
      }
    } catch (e) {
      // Ignore parse errors
    }
  }

  // Save dismissed hints to localStorage
  function saveDismissed() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify([...dismissedHints.value]))
    } catch (e) {
      // Ignore storage errors
    }
  }

  // Check if a specific hint is dismissed
  function isHintDismissed(hintId) {
    return dismissedHints.value.has(hintId)
  }

  // Dismiss a specific hint
  function dismissHint(hintId) {
    dismissedHints.value.add(hintId)
    saveDismissed()
  }

  // Check if hint should show (not dismissed)
  function shouldShowHint(hintId) {
    return !isHintDismissed(hintId)
  }

  // Reset all dismissed hints (useful for testing)
  function resetAllHints() {
    dismissedHints.value.clear()
    saveDismissed()
  }

  // Initialize on first use
  loadDismissed()

  return {
    isHintDismissed,
    dismissHint,
    shouldShowHint,
    resetAllHints,
  }
}
