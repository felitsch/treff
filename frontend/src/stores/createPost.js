/**
 * useCreatePostStore — DEPRECATED: Backward-compatibility wrapper.
 *
 * This function is DEPRECATED and will be removed in a future release.
 * It returns the useContentDraftStore instance for full backward compatibility.
 *
 * Migration guide:
 *   // Before (deprecated):
 *   import { useCreatePostStore } from '@/stores/createPost'
 *   const store = useCreatePostStore()
 *
 *   // After (recommended):
 *   import { useContentDraftStore } from '@/stores/contentDraft'
 *   const store = useContentDraftStore()
 *
 * For content pipeline / student inbox, use:
 *   import { useContentPipelineStore } from '@/stores/contentPipeline'
 *
 * @deprecated Use useContentDraftStore instead
 * @see stores/contentDraft.js    — Vereinfachter Draft-State (Quick/Smart Create)
 * @see stores/contentPipeline.js — Student Inbox & Content-Verarbeitungs-Queue
 */
import { useContentDraftStore } from './contentDraft'

let _deprecationWarned = false

/**
 * @deprecated Use useContentDraftStore from '@/stores/contentDraft' instead.
 * This wrapper exists only for backward compatibility and will be removed.
 */
export function useCreatePostStore() {
  // Emit deprecation warning once per session
  if (!_deprecationWarned) {
    console.warn(
      '[DEPRECATED] useCreatePostStore is deprecated. ' +
      'Migrate to useContentDraftStore or useContentPipelineStore. ' +
      'See stores/contentDraft.js for migration guide.'
    )
    _deprecationWarned = true
  }

  // Return the contentDraft store directly — same refs, same reactivity
  return useContentDraftStore()
}
