import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useStudentStore = defineStore('students', () => {
  const students = ref([])
  const currentStudent = ref(null)
  const loading = ref(false)
  const error = ref('')

  // Computed
  const activeStudents = computed(() => students.value.filter(s => s.status === 'active'))
  const completedStudents = computed(() => students.value.filter(s => s.status === 'completed'))
  const upcomingStudents = computed(() => students.value.filter(s => s.status === 'upcoming'))

  // Fetch all students with optional filters
  async function fetchStudents(filters = {}) {
    loading.value = true
    error.value = ''
    try {
      const params = new URLSearchParams()
      if (filters.country) params.append('country', filters.country)
      if (filters.status) params.append('status', filters.status)
      if (filters.start_date_from) params.append('start_date_from', filters.start_date_from)
      if (filters.start_date_to) params.append('start_date_to', filters.start_date_to)
      if (filters.search) params.append('search', filters.search)

      const queryString = params.toString()
      const url = queryString ? `/api/students?${queryString}` : '/api/students'
      const response = await api.get(url)
      students.value = response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Fehler beim Laden der Studenten'
    } finally {
      loading.value = false
    }
  }

  // Fetch a single student by ID
  async function fetchStudent(id) {
    loading.value = true
    error.value = ''
    try {
      const response = await api.get(`/api/students/${id}`)
      currentStudent.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Student nicht gefunden'
      return null
    } finally {
      loading.value = false
    }
  }

  // Create a new student
  async function createStudent(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await api.post('/api/students', data)
      students.value.unshift(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Fehler beim Erstellen des Studenten'
      return null
    } finally {
      loading.value = false
    }
  }

  // Update an existing student
  async function updateStudent(id, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await api.put(`/api/students/${id}`, data)
      // Update in local list
      const index = students.value.findIndex(s => s.id === id)
      if (index !== -1) {
        students.value[index] = response.data
      }
      if (currentStudent.value?.id === id) {
        currentStudent.value = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Fehler beim Aktualisieren des Studenten'
      return null
    } finally {
      loading.value = false
    }
  }

  // Delete a student
  async function deleteStudent(id) {
    loading.value = true
    error.value = ''
    try {
      await api.delete(`/api/students/${id}`)
      students.value = students.value.filter(s => s.id !== id)
      if (currentStudent.value?.id === id) {
        currentStudent.value = null
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Fehler beim Loeschen des Studenten'
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    students,
    currentStudent,
    loading,
    error,
    activeStudents,
    completedStudents,
    upcomingStudents,
    fetchStudents,
    fetchStudent,
    createStudent,
    updateStudent,
    deleteStudent,
  }
})
