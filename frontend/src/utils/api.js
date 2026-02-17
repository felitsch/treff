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

// ─── Centralized Error Handling ─────────────────────────────────────
// All API errors flow through this interceptor. It handles:
// - 401: Token refresh + login redirect
// - 403: Permission denied toast
// - 404: Not found toast
// - 422: Validation error with field-specific messages
// - 429: Rate limit with retry timer
// - 500: Generic server error toast
// - Network errors: Connectivity toast

/**
 * Extract a user-friendly error message from a 422 validation response.
 * FastAPI returns { detail: [{ loc: [..., "field"], msg: "...", type: "..." }] }
 * @param {Object} data - The response data
 * @returns {string} Formatted validation error message
 */
function extractValidationErrors(data) {
  const detail = data?.detail
  if (Array.isArray(detail)) {
    const fieldErrors = detail.map((err) => {
      const field = Array.isArray(err.loc) ? err.loc[err.loc.length - 1] : 'Feld'
      const msg = err.msg || 'Ungueltiger Wert'
      return `${field}: ${msg}`
    })
    if (fieldErrors.length <= 3) {
      return fieldErrors.join('\n')
    }
    return `${fieldErrors.slice(0, 3).join('\n')}\n(+${fieldErrors.length - 3} weitere Fehler)`
  }
  if (typeof detail === 'string') return detail
  return 'Validierungsfehler. Bitte pruefe deine Eingaben.'
}

/**
 * Show a rate-limit toast with a countdown retry timer.
 * Looks for Retry-After header; defaults to 30 s.
 * @param {Object} error - Axios error object
 * @param {Object} toast - Toast composable instance
 */
function showRateLimitToast(error, toast) {
  const retryAfter = parseInt(error.response?.headers?.['retry-after'], 10)
  const seconds = retryAfter && retryAfter > 0 ? retryAfter : 30
  const detail = error.response?.data?.detail
  const baseMsg = typeof detail === 'string' && detail
    ? detail
    : 'Zu viele Anfragen.'
  toast.warning(`${baseMsg} Bitte warte ${seconds} Sekunden.`, seconds * 1000)
}

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

// Response interceptor for centralized error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // ── 401 Unauthorized: Token refresh + redirect ──
    // Skip auto-redirect for auth endpoints — let the login/register forms handle their own errors
    const isAuthEndpoint = originalRequest?.url?.includes('/api/auth/login') ||
                           originalRequest?.url?.includes('/api/auth/register')

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
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
      // No refresh token available - redirect to login
      localStorage.removeItem('access_token')
      window.location.href = '/login'
      return Promise.reject(error)
    }

    // ── Toast for non-401 errors ──
    // Skip toast if the request explicitly opts out (e.g. config._silent = true)
    if (error.response?.status !== 401 && !originalRequest?._silent) {
      const toast = useToast()
      const status = error.response?.status
      const detail = error.response?.data?.detail

      let message

      // ── 422 Validation Error: Field-specific messages ──
      if (status === 422) {
        message = extractValidationErrors(error.response?.data)
        toast.warning(message, 8000)
        // Attach parsed field errors to the error object for components
        error.validationErrors = Array.isArray(detail)
          ? detail.reduce((acc, err) => {
              const field = Array.isArray(err.loc) ? err.loc[err.loc.length - 1] : '_general'
              acc[field] = err.msg || 'Ungueltiger Wert'
              return acc
            }, {})
          : {}
        return Promise.reject(error)
      }

      // ── 429 Rate Limited: Toast with retry timer ──
      if (status === 429) {
        showRateLimitToast(error, toast)
        return Promise.reject(error)
      }

      // ── Other status codes ──
      if (typeof detail === 'string' && messageTranslations[detail]) {
        message = messageTranslations[detail]
      } else if (typeof detail === 'string' && status !== 500) {
        message = detail
      } else if (status === 404) {
        message = 'Die angeforderte Ressource wurde nicht gefunden.'
      } else if (status === 500) {
        message = 'Ein Serverfehler ist aufgetreten. Bitte versuche es spaeter erneut.'
      } else if (status === 403) {
        message = 'Zugriff verweigert. Du hast keine Berechtigung fuer diese Aktion.'
      } else if (status) {
        message = `Fehler bei der Anfrage (${status}). Bitte versuche es erneut.`
      } else {
        // Network error (no response at all)
        message = 'Netzwerkfehler. Bitte pruefe deine Internetverbindung.'
      }
      toast.error(message)
    }

    return Promise.reject(error)
  }
)

export default api
