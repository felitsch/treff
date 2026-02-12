import { ref, onMounted, onUnmounted, onBeforeUnmount } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

/**
 * Composable for detecting unsaved changes and warning before navigation.
 *
 * Usage:
 *   const { showLeaveDialog, confirmLeave, cancelLeave, markClean } = useUnsavedChanges(isDirtyFn)
 *
 *   - isDirtyFn: () => boolean — returns true when there are unsaved changes
 *   - showLeaveDialog: ref(boolean) — controls the warning dialog visibility
 *   - confirmLeave: () => void — user confirms leaving (discards changes)
 *   - cancelLeave: () => void — user cancels (stays on page)
 *   - markClean: () => void — marks state as clean (call after save/export)
 *
 * Provides:
 *   1. Vue Router onBeforeRouteLeave guard — shows dialog on sidebar/router navigation
 *   2. window.beforeunload handler — shows browser native dialog on tab close/reload
 */
export function useUnsavedChanges(isDirtyFn) {
  const showLeaveDialog = ref(false)
  const forcedClean = ref(false) // when true, bypass dirty check (after export/save)

  // Store the route navigation resolve/reject callbacks
  let pendingNext = null

  /**
   * Mark state as clean — call after successful save or export.
   * This prevents the warning from appearing after save.
   */
  function markClean() {
    forcedClean.value = true
  }

  /**
   * Reset clean state — call when user makes new changes after saving.
   */
  function resetClean() {
    forcedClean.value = false
  }

  /**
   * Check if the form is currently dirty (has unsaved changes).
   */
  function checkDirty() {
    if (forcedClean.value) return false
    return isDirtyFn()
  }

  /**
   * User confirms leaving — proceed with navigation.
   */
  function confirmLeave() {
    showLeaveDialog.value = false
    if (pendingNext) {
      pendingNext()
      pendingNext = null
    }
  }

  /**
   * User cancels — stay on the page.
   */
  function cancelLeave() {
    showLeaveDialog.value = false
    pendingNext = null
  }

  // ── Vue Router guard ────────────────────────────────────────────────
  onBeforeRouteLeave((to, from, next) => {
    if (checkDirty()) {
      showLeaveDialog.value = true
      pendingNext = next
      // Do NOT call next() yet — wait for user decision
    } else {
      next()
    }
  })

  // ── Browser beforeunload handler ────────────────────────────────────
  function handleBeforeUnload(e) {
    if (checkDirty()) {
      e.preventDefault()
      // Modern browsers require returnValue to be set
      e.returnValue = ''
      return ''
    }
  }

  onMounted(() => {
    window.addEventListener('beforeunload', handleBeforeUnload)
  })

  onUnmounted(() => {
    window.removeEventListener('beforeunload', handleBeforeUnload)
  })

  return {
    showLeaveDialog,
    confirmLeave,
    cancelLeave,
    markClean,
    resetClean,
    checkDirty,
  }
}
