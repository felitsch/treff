import axios from 'axios'
import { useToast } from '@/composables/useToast'

const api = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const response = await axios.post('/api/auth/refresh', {
            refresh_token: refreshToken,
          })
          const { access_token, refresh_token } = response.data
          localStorage.setItem('access_token', access_token)
          localStorage.setItem('refresh_token', refresh_token)
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return api(originalRequest)
        } catch (refreshError) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }
    }

    // Show error toast for non-401 errors (401 is handled by token refresh above)
    if (error.response?.status !== 401) {
      const toast = useToast()
      // Map common English API messages to German
      const messageTranslations = {
        'Post not found': 'Post wurde nicht gefunden.',
        'Template not found': 'Vorlage wurde nicht gefunden.',
        'Asset not found': 'Asset wurde nicht gefunden.',
        'Not authenticated': 'Nicht authentifiziert. Bitte melde dich erneut an.',
        'Invalid credentials': 'Ungueltige Anmeldedaten.',
        'Email already registered': 'Diese E-Mail-Adresse ist bereits registriert.',
        'Not Found': 'Die angeforderte Ressource wurde nicht gefunden.',
      }
      // Extract user-friendly message from API response
      const detail = error.response?.data?.detail
      let message
      if (typeof detail === 'string') {
        message = messageTranslations[detail] || detail
      } else if (error.response?.status === 404) {
        message = 'Die angeforderte Ressource wurde nicht gefunden.'
      } else if (error.response?.status === 500) {
        message = 'Ein Serverfehler ist aufgetreten. Bitte versuche es spaeter erneut.'
      } else if (error.response?.status === 403) {
        message = 'Zugriff verweigert. Du hast keine Berechtigung fuer diese Aktion.'
      } else if (error.response?.status) {
        message = `Fehler bei der Anfrage (${error.response.status}). Bitte versuche es erneut.`
      } else {
        message = 'Netzwerkfehler. Bitte pruefe deine Internetverbindung.'
      }
      toast.error(message)
    }

    return Promise.reject(error)
  }
)

export default api
