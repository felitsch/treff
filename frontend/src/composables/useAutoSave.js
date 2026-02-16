/**
 * useAutoSave - Auto-save composable for Post Creator drafts.
 *
 * Features:
 * - Auto-saves draft every 30 seconds (configurable)
 * - Debounced save on significant changes
 * - Shows "Gespeichert um HH:MM" indicator
 * - Shows unsaved changes dot indicator
 * - Draft restoration on mount
 * - Draft cleanup when post is finalized
 *
 * @param {Object} options
 * @param {Function} options.getState - Returns current wizard state as plain object
 * @param {Function} options.onRestore - Called with draft data to restore wizard state
 * @param {number} options.intervalMs - Auto-save interval (default: 30000 = 30s)
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import api from '@/utils/api'

export function useAutoSave({ getState, onRestore, intervalMs = 30000 } = {}) {
  // ── State ─────────────────────────────────────────────────────────
  const draftId = ref(null)
  const lastSavedAt = ref(null)
  const saving = ref(false)
  const hasUnsavedChanges = ref(false)
  const lastSavedSnapshot = ref(null)
  const restoringDraft = ref(false)
  const restoreAvailable = ref(false)
  const restoreDraft = ref(null)

  let autoSaveTimer = null
  let debounceTimer = null

  // ── Computed ──────────────────────────────────────────────────────
  const lastSavedLabel = computed(() => {
    if (!lastSavedAt.value) return null
    const d = new Date(lastSavedAt.value)
    const hh = String(d.getHours()).padStart(2, '0')
    const mm = String(d.getMinutes()).padStart(2, '0')
    return `${hh}:${mm}`
  })

  const saveStatusText = computed(() => {
    if (saving.value) return 'Speichert...'
    if (lastSavedLabel.value) return `Gespeichert um ${lastSavedLabel.value}`
    return null
  })

  // ── Methods ───────────────────────────────────────────────────────

  /**
   * Create a snapshot of the current state for comparison.
   */
  function createSnapshot() {
    if (!getState) return ''
    try {
      const state = getState()
      return JSON.stringify(state)
    } catch {
      return ''
    }
  }

  /**
   * Check if state has changed since last save.
   */
  function checkForChanges() {
    const current = createSnapshot()
    if (!current) return false
    if (!lastSavedSnapshot.value) return !!current && current !== '{}'
    return current !== lastSavedSnapshot.value
  }

  /**
   * Save the current state as a draft.
   */
  async function saveDraft() {
    if (!getState || saving.value) return
    const state = getState()
    if (!state || !state.selectedCategory) return // Don't save empty states

    saving.value = true
    hasUnsavedChanges.value = false

    try {
      const payload = {
        draft_id: draftId.value || undefined,
        category: state.selectedCategory || 'allgemein',
        platform: state.selectedPlatform || 'instagram_feed',
        country: state.country || null,
        title: state.topic || state.slides?.[0]?.headline || 'Unbenannter Entwurf',
        slide_data: JSON.stringify(state.slides || []),
        caption_instagram: state.captionInstagram || '',
        caption_tiktok: state.captionTiktok || '',
        hashtags_instagram: state.hashtagsInstagram || '',
        hashtags_tiktok: state.hashtagsTiktok || '',
        cta_text: state.ctaText || '',
        tone: state.tone || 'jugendlich',
        wizard_state: state, // Full wizard state for restoration
      }

      const res = await api.post('/api/posts/drafts/save', payload)

      if (res.data && res.data.draft) {
        draftId.value = res.data.draft.id
        lastSavedAt.value = new Date().toISOString()
        lastSavedSnapshot.value = createSnapshot()
      }
    } catch (err) {
      console.error('Auto-save failed:', err)
      hasUnsavedChanges.value = true
    } finally {
      saving.value = false
    }
  }

  /**
   * Debounced save (called on changes).
   */
  function debouncedSave() {
    hasUnsavedChanges.value = true
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      if (checkForChanges()) {
        saveDraft()
      }
    }, 3000) // 3 second debounce
  }

  /**
   * Check for existing draft and offer restoration.
   */
  async function checkForDraft() {
    try {
      const res = await api.get('/api/posts/drafts/latest')
      if (res.data && res.data.draft) {
        restoreDraft.value = res.data.draft
        restoreAvailable.value = true
      }
    } catch {
      // No draft available, that's fine
    }
  }

  /**
   * Restore a draft into the wizard.
   */
  async function restoreFromDraft(draft) {
    if (!draft || !onRestore) return
    restoringDraft.value = true

    try {
      // Try to parse wizard state from custom_fonts
      let wizardState = null
      if (draft.custom_fonts) {
        try {
          const parsed = JSON.parse(draft.custom_fonts)
          wizardState = parsed._wizard_state || parsed
        } catch {
          // Not JSON, skip
        }
      }

      // Restore using wizard state or post fields
      const restoreData = wizardState || {
        selectedCategory: draft.category || '',
        selectedPlatform: draft.platform || 'instagram_feed',
        country: draft.country || '',
        topic: draft.title || '',
        tone: draft.tone || 'jugendlich',
        slides: draft.slide_data ? JSON.parse(draft.slide_data) : [],
        captionInstagram: draft.caption_instagram || '',
        captionTiktok: draft.caption_tiktok || '',
        hashtagsInstagram: draft.hashtags_instagram || '',
        hashtagsTiktok: draft.hashtags_tiktok || '',
        ctaText: draft.cta_text || '',
      }

      onRestore(restoreData)
      draftId.value = draft.id
      lastSavedAt.value = draft.updated_at
      lastSavedSnapshot.value = createSnapshot()
      restoreAvailable.value = false
    } finally {
      restoringDraft.value = false
    }
  }

  /**
   * Dismiss the restore offer.
   */
  function dismissRestore() {
    restoreAvailable.value = false
    restoreDraft.value = null
  }

  /**
   * Delete the current draft (called when post is finalized/exported).
   */
  async function cleanupDraft() {
    if (!draftId.value) return
    try {
      await api.delete(`/api/posts/drafts/${draftId.value}`)
      draftId.value = null
      lastSavedAt.value = null
      lastSavedSnapshot.value = null
      hasUnsavedChanges.value = false
    } catch {
      // Draft may already be deleted or converted
    }
  }

  /**
   * Mark changes detected (call from watchers).
   */
  function markChanged() {
    debouncedSave()
  }

  // ── Lifecycle ─────────────────────────────────────────────────────

  function startAutoSave() {
    if (autoSaveTimer) clearInterval(autoSaveTimer)
    autoSaveTimer = setInterval(() => {
      if (checkForChanges()) {
        saveDraft()
      }
    }, intervalMs)
  }

  function stopAutoSave() {
    if (autoSaveTimer) {
      clearInterval(autoSaveTimer)
      autoSaveTimer = null
    }
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
  }

  onMounted(() => {
    checkForDraft()
    startAutoSave()
  })

  onUnmounted(() => {
    stopAutoSave()
    // Final save on unmount if there are changes
    if (hasUnsavedChanges.value && getState) {
      saveDraft()
    }
  })

  return {
    // State
    draftId,
    lastSavedAt,
    saving,
    hasUnsavedChanges,
    restoringDraft,
    restoreAvailable,
    restoreDraft,

    // Computed
    lastSavedLabel,
    saveStatusText,

    // Methods
    saveDraft,
    markChanged,
    checkForDraft,
    restoreFromDraft,
    dismissRestore,
    cleanupDraft,
    startAutoSave,
    stopAutoSave,
  }
}
