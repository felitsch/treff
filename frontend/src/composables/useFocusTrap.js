/**
 * useFocusTrap — Composable for trapping keyboard focus within a container.
 *
 * Used for modals, dialogs, and overlay panels to prevent keyboard focus
 * from escaping the active UI surface. Part of WCAG 2.1 AA compliance.
 *
 * Usage:
 *   const { activate, deactivate } = useFocusTrap(containerRef)
 *   // Call activate() when modal opens, deactivate() when it closes
 *
 * @see https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/
 */
import { onUnmounted } from 'vue'

const FOCUSABLE_SELECTORS = [
  'a[href]',
  'area[href]',
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  'button:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
  '[contenteditable]',
].join(', ')

export function useFocusTrap(containerRef) {
  let previouslyFocused = null
  let isActive = false

  function getFocusableElements() {
    if (!containerRef.value) return []
    return Array.from(containerRef.value.querySelectorAll(FOCUSABLE_SELECTORS))
      .filter(el => !el.hasAttribute('disabled') && el.offsetParent !== null)
  }

  function handleKeydown(e) {
    if (!isActive || e.key !== 'Tab') return

    const focusable = getFocusableElements()
    if (focusable.length === 0) {
      e.preventDefault()
      return
    }

    const first = focusable[0]
    const last = focusable[focusable.length - 1]

    if (e.shiftKey) {
      // Shift+Tab: if focus is on first element, wrap to last
      if (document.activeElement === first || !containerRef.value.contains(document.activeElement)) {
        e.preventDefault()
        last.focus()
      }
    } else {
      // Tab: if focus is on last element, wrap to first
      if (document.activeElement === last || !containerRef.value.contains(document.activeElement)) {
        e.preventDefault()
        first.focus()
      }
    }
  }

  function activate() {
    if (isActive) return
    isActive = true
    previouslyFocused = document.activeElement
    document.addEventListener('keydown', handleKeydown, true)

    // Focus the first focusable element inside the container
    requestAnimationFrame(() => {
      const focusable = getFocusableElements()
      if (focusable.length > 0) {
        focusable[0].focus()
      } else if (containerRef.value) {
        // If no focusable children, make the container itself focusable
        containerRef.value.setAttribute('tabindex', '-1')
        containerRef.value.focus()
      }
    })
  }

  function deactivate() {
    if (!isActive) return
    isActive = false
    document.removeEventListener('keydown', handleKeydown, true)

    // Restore focus to the element that was focused before the trap
    if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
      requestAnimationFrame(() => {
        previouslyFocused.focus()
      })
    }
    previouslyFocused = null
  }

  // Auto-cleanup on unmount
  onUnmounted(() => {
    deactivate()
  })

  return { activate, deactivate }
}
