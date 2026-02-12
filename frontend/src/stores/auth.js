import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('access_token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)
  const user = ref(null)

  const isAuthenticated = computed(() => !!accessToken.value)

  async function login(email, password) {
    const response = await api.post('/api/auth/login', { email, password })
    accessToken.value = response.data.access_token
    refreshToken.value = response.data.refresh_token
    localStorage.setItem('access_token', response.data.access_token)
    localStorage.setItem('refresh_token', response.data.refresh_token)
    await fetchUser()
  }

  async function register(email, password, displayName) {
    await api.post('/api/auth/register', {
      email,
      password,
      display_name: displayName,
    })
  }

  async function fetchUser() {
    try {
      const response = await api.get('/api/auth/me')
      user.value = response.data
    } catch (error) {
      logout()
    }
  }

  async function refreshAccessToken() {
    try {
      const response = await api.post('/api/auth/refresh', {
        refresh_token: refreshToken.value,
      })
      accessToken.value = response.data.access_token
      refreshToken.value = response.data.refresh_token
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
    } catch (error) {
      logout()
    }
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return {
    accessToken,
    refreshToken,
    user,
    isAuthenticated,
    login,
    register,
    fetchUser,
    refreshAccessToken,
    logout,
  }
})
