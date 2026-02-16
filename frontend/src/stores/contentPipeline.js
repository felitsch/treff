/**
 * useContentPipelineStore — Student Inbox und Content-Verarbeitungs-Queue.
 *
 * Architecture:
 * Manages the Smart Content Pipeline where student-submitted media (photos,
 * videos) flows through an analysis → review → draft-creation workflow.
 * Communicates with /api/pipeline backend endpoints.
 *
 * Pipeline Flow:
 *   1. Student uploads media (image/video)
 *   2. AI analyzes media → suggests post type, captions, platforms, country
 *   3. Social-Media-Mitarbeiterin reviews suggestions in the inbox
 *   4. One-click processing creates a draft post from the analyzed item
 *   5. Content multiplication generates derivative formats
 *
 * This store was extracted from the monolithic useCreatePostStore as part
 * of the Pinia Store Architektur (I-05) decomposition.
 *
 * @see stores/contentDraft.js — Post-creation wizard state
 * @see stores/campaign.js     — Multi-post campaign planning state
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useContentPipelineStore = defineStore('contentPipeline', () => {
  // ═══════════════════════════════════════════════════════════════════
  // INBOX STATE
  // ═══════════════════════════════════════════════════════════════════

  /** List of pipeline inbox items (analyzed student uploads) */
  const inboxItems = ref([])

  /** Total count of inbox items (for pagination) */
  const inboxTotal = ref(0)

  /** Current page for paginated inbox */
  const inboxPage = ref(1)

  /** Items per page */
  const inboxLimit = ref(20)

  /** Loading state for inbox operations */
  const loading = ref(false)

  /** Error message from the last failed operation */
  const error = ref('')

  /** Currently selected inbox item for detail view */
  const activeItem = ref(null)

  /** Whether media analysis (AI) is in progress */
  const analyzing = ref(false)

  /** Whether processing (draft creation) is in progress */
  const processing = ref(false)

  // ═══════════════════════════════════════════════════════════════════
  // FILTER STATE
  // ═══════════════════════════════════════════════════════════════════

  /** Filter by student ID (null = all students) */
  const filterStudentId = ref(null)

  /** Filter by status (null = all statuses) */
  const filterStatus = ref(null)

  // ═══════════════════════════════════════════════════════════════════
  // GETTERS
  // ═══════════════════════════════════════════════════════════════════

  const pendingCount = computed(() =>
    inboxItems.value.filter(item => item.status === 'pending').length
  )

  const analyzedCount = computed(() =>
    inboxItems.value.filter(item => item.status === 'analyzed').length
  )

  const processedCount = computed(() =>
    inboxItems.value.filter(item => item.status === 'processed').length
  )

  const hasItems = computed(() => inboxItems.value.length > 0)

  const totalPages = computed(() =>
    Math.ceil(inboxTotal.value / inboxLimit.value) || 1
  )

  // ═══════════════════════════════════════════════════════════════════
  // ACTIONS — Inbox
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Fetch inbox items with pagination and optional filters.
   * @param {Object} options - { page, studentId, status }
   */
  async function fetchInbox(options = {}) {
    loading.value = true
    error.value = ''
    try {
      const params = new URLSearchParams()
      const page = options.page || inboxPage.value
      params.append('page', page.toString())
      params.append('limit', inboxLimit.value.toString())
      if (options.studentId || filterStudentId.value) {
        params.append('student_id', (options.studentId || filterStudentId.value).toString())
      }
      if (options.status || filterStatus.value) {
        params.append('status', options.status || filterStatus.value)
      }
      const response = await api.get(`/api/pipeline/inbox?${params.toString()}`)
      inboxItems.value = response.data.items || []
      inboxTotal.value = response.data.total || 0
      inboxPage.value = response.data.page || page
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Inbox konnte nicht geladen werden'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ═══════════════════════════════════════════════════════════════════
  // ACTIONS — Media Analysis
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Upload and analyze a media file (image or video).
   * Creates an asset and pipeline item with AI-generated suggestions.
   * @param {File} file - The file to upload and analyze
   * @param {Object} options - { studentId, sourceDescription }
   * @returns {Object} Pipeline item with analysis results
   */
  async function analyzeMedia(file, options = {}) {
    analyzing.value = true
    error.value = ''
    try {
      const formData = new FormData()
      formData.append('file', file)
      if (options.studentId) formData.append('student_id', options.studentId.toString())
      if (options.sourceDescription) formData.append('source_description', options.sourceDescription)

      const response = await api.post('/api/pipeline/analyze-media', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      // Refresh inbox to include the new item
      await fetchInbox()

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Medienanalyse fehlgeschlagen'
      throw err
    } finally {
      analyzing.value = false
    }
  }

  // ═══════════════════════════════════════════════════════════════════
  // ACTIONS — Processing (Draft Creation)
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Process an inbox item into a draft post.
   * @param {number} inboxItemId - The pipeline item ID to process
   * @param {Object} overrides - Optional { postType, platform, tone, country }
   * @returns {Object} Created draft post info
   */
  async function processItem(inboxItemId, overrides = {}) {
    processing.value = true
    error.value = ''
    try {
      const payload = {
        inbox_item_id: inboxItemId,
        ...overrides,
      }
      const response = await api.post('/api/pipeline/process', payload)

      // Update the item status in local state
      const idx = inboxItems.value.findIndex(item => item.id === inboxItemId)
      if (idx !== -1) {
        inboxItems.value[idx] = {
          ...inboxItems.value[idx],
          status: 'processed',
          result_post_id: response.data.post_id,
        }
      }

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Verarbeitung fehlgeschlagen'
      throw err
    } finally {
      processing.value = false
    }
  }

  /**
   * Mark an inbox item as processed (local state update).
   * @param {number} itemId
   */
  function markAsProcessed(itemId) {
    const idx = inboxItems.value.findIndex(item => item.id === itemId)
    if (idx !== -1) {
      inboxItems.value[idx].status = 'processed'
    }
  }

  // ═══════════════════════════════════════════════════════════════════
  // ACTIONS — Content Multiplication
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Generate derivative posts from a source post for different platforms.
   * @param {number} postId - Source post ID
   * @param {string[]} formats - Target formats (e.g., ["instagram_story", "tiktok"])
   * @returns {Object} Multiplication results with derivative info
   */
  async function multiplyContent(postId, formats = ['instagram_story', 'tiktok']) {
    loading.value = true
    error.value = ''
    try {
      const response = await api.post('/api/pipeline/multiply', {
        post_id: postId,
        formats,
      })
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Content-Multiplikation fehlgeschlagen'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ═══════════════════════════════════════════════════════════════════
  // ACTIONS — Reset
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Reset all pipeline state.
   */
  function resetAll() {
    inboxItems.value = []
    inboxTotal.value = 0
    inboxPage.value = 1
    activeItem.value = null
    loading.value = false
    error.value = ''
    analyzing.value = false
    processing.value = false
    filterStudentId.value = null
    filterStatus.value = null
  }

  // ═══════════════════════════════════════════════════════════════════
  // PUBLIC API
  // ═══════════════════════════════════════════════════════════════════

  return {
    // State
    inboxItems,
    inboxTotal,
    inboxPage,
    inboxLimit,
    loading,
    error,
    activeItem,
    analyzing,
    processing,
    filterStudentId,
    filterStatus,

    // Getters
    pendingCount,
    analyzedCount,
    processedCount,
    hasItems,
    totalPages,

    // Actions — Inbox
    fetchInbox,

    // Actions — Analysis
    analyzeMedia,

    // Actions — Processing
    processItem,
    markAsProcessed,

    // Actions — Multiplication
    multiplyContent,

    // Actions — Reset
    resetAll,
  }
})
