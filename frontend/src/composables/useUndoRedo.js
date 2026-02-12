import { ref, computed, onMounted, onUnmounted } from 'vue'

/**
 * Composable for undo/redo functionality on content edits.
 *
 * Tracks snapshots of the entire editable state (slides + captions/hashtags).
 * Provides undo(), redo(), and keyboard shortcut handling (Ctrl+Z / Ctrl+Y).
 *
 * Usage:
 *   const { canUndo, canRedo, undo, redo, snapshot, initFromState } = useUndoRedo(applyState)
 *   // Call snapshot() whenever state changes (debounced, on blur, etc.)
 *   // applyState(state) will be called when undo/redo restores a state
 */
export function useUndoRedo(applyStateFn) {
  const history = ref([])     // Array of JSON-stringified state snapshots
  const currentIndex = ref(-1) // Pointer into history
  const maxHistory = 50        // Maximum number of snapshots to keep
  const isApplying = ref(false) // Guard: prevents snapshot during apply

  const canUndo = computed(() => currentIndex.value > 0)
  const canRedo = computed(() => currentIndex.value < history.value.length - 1)

  /**
   * Take a snapshot of the current state.
   * Call this when content changes (e.g., on input, after AI generation, on blur).
   */
  function snapshot(state) {
    if (isApplying.value) return // Don't record snapshots triggered by undo/redo

    const serialized = JSON.stringify(state)

    // Don't push duplicate consecutive states
    if (currentIndex.value >= 0 && history.value[currentIndex.value] === serialized) {
      return
    }

    // If we undid some actions and then make a new change, discard the "future"
    if (currentIndex.value < history.value.length - 1) {
      history.value = history.value.slice(0, currentIndex.value + 1)
    }

    history.value.push(serialized)

    // Trim to max history
    if (history.value.length > maxHistory) {
      history.value = history.value.slice(history.value.length - maxHistory)
    }

    currentIndex.value = history.value.length - 1
  }

  /**
   * Initialize the history with an initial state (call once after loading content).
   */
  function initFromState(state) {
    const serialized = JSON.stringify(state)
    history.value = [serialized]
    currentIndex.value = 0
  }

  /**
   * Undo: go back one step in history.
   */
  function undo() {
    if (!canUndo.value) return
    currentIndex.value--
    const state = JSON.parse(history.value[currentIndex.value])
    isApplying.value = true
    applyStateFn(state)
    // Use nextTick-style delay to allow reactive updates to settle
    setTimeout(() => { isApplying.value = false }, 50)
  }

  /**
   * Redo: go forward one step in history.
   */
  function redo() {
    if (!canRedo.value) return
    currentIndex.value++
    const state = JSON.parse(history.value[currentIndex.value])
    isApplying.value = true
    applyStateFn(state)
    setTimeout(() => { isApplying.value = false }, 50)
  }

  /**
   * Keyboard handler for Ctrl+Z (undo) and Ctrl+Y / Ctrl+Shift+Z (redo).
   * Only intercepts when focus is NOT inside a native input/textarea
   * that has its own undo (we intercept always since our state is managed in Vue).
   */
  function handleKeydown(e) {
    // Check for Ctrl+Z (or Cmd+Z on Mac)
    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
      e.preventDefault()
      e.stopPropagation()
      undo()
      return
    }
    // Check for Ctrl+Y or Ctrl+Shift+Z (or Cmd variants)
    if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey) || (e.key === 'Z' && e.shiftKey))) {
      e.preventDefault()
      e.stopPropagation()
      redo()
      return
    }
  }

  /**
   * Start listening for keyboard shortcuts. Call in onMounted.
   */
  function startListening() {
    window.addEventListener('keydown', handleKeydown, true) // capture phase
  }

  /**
   * Stop listening for keyboard shortcuts. Call in onUnmounted.
   */
  function stopListening() {
    window.removeEventListener('keydown', handleKeydown, true)
  }

  /**
   * Clear all history (e.g., when resetting the form).
   */
  function clearHistory() {
    history.value = []
    currentIndex.value = -1
  }

  return {
    canUndo,
    canRedo,
    undo,
    redo,
    snapshot,
    initFromState,
    startListening,
    stopListening,
    clearHistory,
    isApplying,
  }
}
