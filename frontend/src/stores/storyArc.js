import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useStoryArcStore = defineStore('storyArc', () => {
  // State
  const storyArcs = ref([])
  const currentArc = ref(null)
  const loading = ref(false)
  const error = ref('')

  // Getters
  const draftArcs = computed(() => storyArcs.value.filter(a => a.status === 'draft'))
  const activeArcs = computed(() => storyArcs.value.filter(a => a.status === 'active'))
  const pausedArcs = computed(() => storyArcs.value.filter(a => a.status === 'paused'))
  const completedArcs = computed(() => storyArcs.value.filter(a => a.status === 'completed'))

  // Actions

  /**
   * Fetch all story arcs with optional filters.
   * @param {Object} filters - { student_id, country, status }
   */
  async function fetchStoryArcs(filters = {}) {
    loading.value = true
    error.value = ''
    try {
      const params = new URLSearchParams()
      if (filters.student_id) params.append('student_id', filters.student_id)
      if (filters.country) params.append('country', filters.country)
      if (filters.status) params.append('status', filters.status)

      const query = params.toString()
      const url = query ? `/api/story-arcs?${query}` : '/api/story-arcs'
      const response = await api.get(url)
      storyArcs.value = response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Fehler beim Laden der Story-Arcs'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch a single story arc by ID.
   * @param {number} id
   */
  async function fetchStoryArc(id) {
    loading.value = true
    error.value = ''
    try {
      const response = await api.get(`/api/story-arcs/${id}`)
      currentArc.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Story-Arc nicht gefunden'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new story arc.
   * @param {Object} arcData - { title, subtitle, description, student_id, country, status, planned_episodes, tone, ... }
   */
  async function createStoryArc(arcData) {
    loading.value = true
    error.value = ''
    try {
      const response = await api.post('/api/story-arcs', arcData)
      storyArcs.value.unshift(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Fehler beim Erstellen des Story-Arcs'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Update an existing story arc.
   * @param {number} id
   * @param {Object} arcData
   */
  async function updateStoryArc(id, arcData) {
    loading.value = true
    error.value = ''
    try {
      const response = await api.put(`/api/story-arcs/${id}`, arcData)
      // Update in local list
      const index = storyArcs.value.findIndex(a => a.id === id)
      if (index !== -1) {
        storyArcs.value[index] = response.data
      }
      if (currentArc.value && currentArc.value.id === id) {
        currentArc.value = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Fehler beim Aktualisieren des Story-Arcs'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete a story arc.
   * @param {number} id
   */
  async function deleteStoryArc(id) {
    loading.value = true
    error.value = ''
    try {
      await api.delete(`/api/story-arcs/${id}`)
      storyArcs.value = storyArcs.value.filter(a => a.id !== id)
      if (currentArc.value && currentArc.value.id === id) {
        currentArc.value = null
      }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Fehler beim Loeschen des Story-Arcs'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    storyArcs,
    currentArc,
    loading,
    error,
    // Getters
    draftArcs,
    activeArcs,
    pausedArcs,
    completedArcs,
    // Actions
    fetchStoryArcs,
    fetchStoryArc,
    createStoryArc,
    updateStoryArc,
    deleteStoryArc,
  }
})
