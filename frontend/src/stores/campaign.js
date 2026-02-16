/**
 * useCampaignStore — Multi-Post-Kampagnen-State.
 *
 * Architecture:
 * Manages the lifecycle of marketing campaigns that group multiple posts
 * around a specific goal (awareness, engagement, conversion, traffic).
 * Communicates with the /api/campaigns backend endpoints.
 *
 * Responsibilities:
 *   - CRUD for campaigns (title, goal, dateRange, platforms, status)
 *   - Campaign post plan management (ordered posts within a campaign)
 *   - AI-powered post plan generation (calls /api/campaigns/:id/generate)
 *   - Adding/removing individual posts from a campaign
 *
 * This store was extracted from the monolithic useCreatePostStore as part
 * of the Pinia Store Architektur (I-05) decomposition.
 *
 * @see stores/contentDraft.js    — Post-creation wizard state
 * @see stores/contentPipeline.js — Student inbox & content processing queue
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useCampaignStore = defineStore('campaign', () => {
  // ═══════════════════════════════════════════════════════════════════
  // CAMPAIGN STATE
  // ═══════════════════════════════════════════════════════════════════

  /** List of all campaigns for the current user */
  const campaigns = ref([])

  /** Currently selected/active campaign (for detail view or editing) */
  const activeCampaign = ref(null)

  /** Loading state for campaign operations */
  const loading = ref(false)

  /** Error message from the last failed operation */
  const error = ref('')

  // ── Campaign form state (for create/edit dialogs) ──────────────
  const campaignTitle = ref('')
  const campaignDescription = ref('')
  const goal = ref('awareness')  // awareness | engagement | conversion | traffic
  const dateRange = ref({ start: '', end: '' })
  const platforms = ref(['instagram_feed'])
  const status = ref('draft')  // draft | active | completed

  /** Posts associated with the active campaign */
  const posts = ref([])

  /** Whether AI plan generation is in progress */
  const generatingPlan = ref(false)

  // ═══════════════════════════════════════════════════════════════════
  // GETTERS
  // ═══════════════════════════════════════════════════════════════════

  const campaignCount = computed(() => campaigns.value.length)

  const activeCampaignPostCount = computed(() => {
    if (activeCampaign.value && activeCampaign.value.posts) {
      return activeCampaign.value.posts.length
    }
    return posts.value.length
  })

  const hasActiveCampaign = computed(() => !!activeCampaign.value)

  // ═══════════════════════════════════════════════════════════════════
  // ACTIONS — Campaign CRUD
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Fetch all campaigns for the current user.
   * @param {Object} filters - Optional filters { status, goal }
   */
  async function fetchCampaigns(filters = {}) {
    loading.value = true
    error.value = ''
    try {
      const params = new URLSearchParams()
      if (filters.status) params.append('status', filters.status)
      if (filters.goal) params.append('goal', filters.goal)
      const queryString = params.toString()
      const url = queryString ? `/api/campaigns?${queryString}` : '/api/campaigns'
      const response = await api.get(url)
      campaigns.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Kampagnen konnten nicht geladen werden'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch a single campaign with its posts.
   * @param {number} campaignId
   */
  async function fetchCampaign(campaignId) {
    loading.value = true
    error.value = ''
    try {
      const response = await api.get(`/api/campaigns/${campaignId}`)
      activeCampaign.value = response.data
      posts.value = response.data.posts || []
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Kampagne konnte nicht geladen werden'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new campaign.
   */
  async function createCampaign() {
    loading.value = true
    error.value = ''
    try {
      const payload = {
        title: campaignTitle.value,
        description: campaignDescription.value || null,
        goal: goal.value,
        start_date: dateRange.value.start || null,
        end_date: dateRange.value.end || null,
        platforms: platforms.value,
        status: status.value,
      }
      const response = await api.post('/api/campaigns', payload)
      campaigns.value.unshift(response.data)
      activeCampaign.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Kampagne konnte nicht erstellt werden'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Update an existing campaign.
   * @param {number} campaignId
   * @param {Object} data - Fields to update
   */
  async function updateCampaign(campaignId, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await api.put(`/api/campaigns/${campaignId}`, data)
      // Update in campaigns list
      const idx = campaigns.value.findIndex(c => c.id === campaignId)
      if (idx !== -1) campaigns.value[idx] = response.data
      // Update active campaign if it matches
      if (activeCampaign.value?.id === campaignId) {
        activeCampaign.value = { ...activeCampaign.value, ...response.data }
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Kampagne konnte nicht aktualisiert werden'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete a campaign.
   * @param {number} campaignId
   */
  async function deleteCampaign(campaignId) {
    loading.value = true
    error.value = ''
    try {
      await api.delete(`/api/campaigns/${campaignId}`)
      campaigns.value = campaigns.value.filter(c => c.id !== campaignId)
      if (activeCampaign.value?.id === campaignId) {
        activeCampaign.value = null
        posts.value = []
      }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Kampagne konnte nicht geloescht werden'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ═══════════════════════════════════════════════════════════════════
  // ACTIONS — AI Plan Generation
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Generate an AI-powered post plan for the active campaign.
   * Creates CampaignPost entries with suggested categories, platforms, countries.
   * @param {number} campaignId
   */
  async function generatePlan(campaignId) {
    generatingPlan.value = true
    error.value = ''
    try {
      const response = await api.post(`/api/campaigns/${campaignId}/generate`)
      posts.value = response.data.posts || []
      // Refresh the full campaign to get updated data
      await fetchCampaign(campaignId)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Plan konnte nicht generiert werden'
      throw err
    } finally {
      generatingPlan.value = false
    }
  }

  // ═══════════════════════════════════════════════════════════════════
  // ACTIONS — Post Management within Campaign
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Add a post reference to the campaign posts list (local state).
   * @param {Object} post - Post data to add
   */
  function addPost(post) {
    posts.value.push({
      ...post,
      order: posts.value.length + 1,
    })
  }

  /**
   * Remove a post from the campaign posts list (local state).
   * @param {number} postId - Post ID to remove
   */
  function removePost(postId) {
    posts.value = posts.value.filter(p => (p.post_id || p.id) !== postId)
    // Re-number order
    posts.value.forEach((p, idx) => { p.order = idx + 1 })
  }

  /**
   * Reset the campaign form to default values.
   */
  function resetForm() {
    campaignTitle.value = ''
    campaignDescription.value = ''
    goal.value = 'awareness'
    dateRange.value = { start: '', end: '' }
    platforms.value = ['instagram_feed']
    status.value = 'draft'
    error.value = ''
  }

  /**
   * Reset all campaign state.
   */
  function resetAll() {
    campaigns.value = []
    activeCampaign.value = null
    posts.value = []
    loading.value = false
    generatingPlan.value = false
    resetForm()
  }

  // ═══════════════════════════════════════════════════════════════════
  // PUBLIC API
  // ═══════════════════════════════════════════════════════════════════

  return {
    // State
    campaigns,
    activeCampaign,
    loading,
    error,
    campaignTitle,
    campaignDescription,
    goal,
    dateRange,
    platforms,
    status,
    posts,
    generatingPlan,

    // Getters
    campaignCount,
    activeCampaignPostCount,
    hasActiveCampaign,

    // Actions — CRUD
    fetchCampaigns,
    fetchCampaign,
    createCampaign,
    updateCampaign,
    deleteCampaign,

    // Actions — AI
    generatePlan,

    // Actions — Post management
    addPost,
    removePost,

    // Actions — Reset
    resetForm,
    resetAll,
  }
})
