/**
 * useApi — Centralized API composable for consistent error handling.
 *
 * All API calls made through this composable automatically benefit from:
 *   - Loading state management (loading ref per call)
 *   - Centralized error handling via axios interceptors (toast notifications)
 *   - 422 validation errors with field-specific messages (error.validationErrors)
 *   - 429 rate limit with retry timer toast
 *   - Network error detection
 *   - Optional silent mode (suppress toast for expected errors)
 *   - Convenience HTTP method wrappers (get, post, put, patch, del)
 *
 * Usage:
 *   const { execute, get, post, put, del, loading, error, data, validationErrors } = useApi()
 *
 *   // Simple GET via convenience method
 *   await get('/api/posts')
 *
 *   // POST with payload
 *   await post('/api/posts', payload, { onSuccess: (res) => router.push('/posts') })
 *
 *   // Low-level execute (when you need full control)
 *   await execute(() => api.get('/api/posts'))
 *
 *   // Silent mode (suppress global toast)
 *   await get('/api/settings', null, { silent: true })
 *
 * @module composables/useApi
 */
import { ref, readonly } from 'vue'
import api from '@/utils/api'

/**
 * @typedef {Object} ApiOptions
 * @property {boolean} [silent=false] - If true, suppress global toast (errors still returned)
 * @property {Function} [onSuccess] - Callback on success, receives response
 * @property {Function} [onError] - Callback on error, receives error object
 */

/**
 * @typedef {Object} UseApiReturn
 * @property {import('vue').Ref<boolean>} loading - Whether a request is in flight
 * @property {import('vue').Ref<string|null>} error - Last error message (null if none)
 * @property {import('vue').Ref<any>} data - Last successful response data
 * @property {import('vue').Ref<Object>} validationErrors - Field-specific 422 errors { fieldName: message }
 * @property {Function} execute - Execute an API call with automatic state management
 * @property {Function} get - Convenience GET wrapper
 * @property {Function} post - Convenience POST wrapper
 * @property {Function} put - Convenience PUT wrapper
 * @property {Function} patch - Convenience PATCH wrapper
 * @property {Function} del - Convenience DELETE wrapper
 * @property {Function} reset - Clear error, data, and validationErrors
 */

/**
 * Composable for making API calls with centralized error/loading state.
 * @returns {UseApiReturn}
 */
export function useApi() {
  const loading = ref(false)
  const error = ref(null)
  const data = ref(null)
  const validationErrors = ref({})

  /**
   * Execute an API call with automatic loading/error state management.
   *
   * @param {Function} apiFn - A function that returns an axios promise (e.g. () => api.get('/url'))
   * @param {ApiOptions} [options] - Options
   * @returns {Promise<any|null>} The response data on success, or null on error
   */
  async function execute(apiFn, options = {}) {
    const { silent = false, onSuccess, onError } = options

    loading.value = true
    error.value = null
    validationErrors.value = {}

    try {
      // If silent mode, configure the axios request to skip global toasts
      // We wrap the apiFn call — the _silent flag is set on the config in api.js
      if (silent) {
        // Temporarily add _silent to next request via interceptor
        const reqInterceptor = api.interceptors.request.use((config) => {
          config._silent = true
          return config
        })
        try {
          const response = await apiFn()
          data.value = response.data
          if (onSuccess) onSuccess(response)
          return response.data
        } finally {
          api.interceptors.request.eject(reqInterceptor)
        }
      }

      const response = await apiFn()
      data.value = response.data
      if (onSuccess) onSuccess(response)
      return response.data
    } catch (err) {
      // Extract user-friendly error message
      const status = err.response?.status
      const detail = err.response?.data?.detail

      if (status === 422 && err.validationErrors) {
        validationErrors.value = err.validationErrors
        error.value = typeof detail === 'string'
          ? detail
          : 'Validierungsfehler. Bitte pruefe deine Eingaben.'
      } else if (typeof detail === 'string') {
        error.value = detail
      } else if (!err.response) {
        error.value = 'Netzwerkfehler. Bitte pruefe deine Internetverbindung.'
      } else {
        error.value = `Fehler (${status || 'unbekannt'})`
      }

      if (onError) onError(err)
      return null
    } finally {
      loading.value = false
    }
  }

  // ── Convenience HTTP method wrappers ──────────────────────────────

  /**
   * Convenience wrapper for GET requests.
   * @param {string} url - API endpoint path
   * @param {Object} [params] - Query parameters (passed as axios params)
   * @param {ApiOptions} [options] - Options (silent, onSuccess, onError)
   * @returns {Promise<any|null>} The response data on success, or null on error
   */
  function get(url, params = null, options = {}) {
    const config = params ? { params } : undefined
    return execute(() => api.get(url, config), options)
  }

  /**
   * Convenience wrapper for POST requests.
   * @param {string} url - API endpoint path
   * @param {any} [payload] - Request body
   * @param {ApiOptions} [options] - Options
   * @returns {Promise<any|null>}
   */
  function post(url, payload, options = {}) {
    return execute(() => api.post(url, payload), options)
  }

  /**
   * Convenience wrapper for PUT requests.
   * @param {string} url - API endpoint path
   * @param {any} [payload] - Request body
   * @param {ApiOptions} [options] - Options
   * @returns {Promise<any|null>}
   */
  function put(url, payload, options = {}) {
    return execute(() => api.put(url, payload), options)
  }

  /**
   * Convenience wrapper for PATCH requests.
   * @param {string} url - API endpoint path
   * @param {any} [payload] - Request body
   * @param {ApiOptions} [options] - Options
   * @returns {Promise<any|null>}
   */
  function patch(url, payload, options = {}) {
    return execute(() => api.patch(url, payload), options)
  }

  /**
   * Convenience wrapper for DELETE requests.
   * @param {string} url - API endpoint path
   * @param {ApiOptions} [options] - Options
   * @returns {Promise<any|null>}
   */
  function del(url, options = {}) {
    return execute(() => api.delete(url), options)
  }

  /**
   * Clear all state (error, data, validationErrors).
   */
  function reset() {
    error.value = null
    data.value = null
    validationErrors.value = {}
  }

  return {
    loading: readonly(loading),
    error: readonly(error),
    data: readonly(data),
    validationErrors: readonly(validationErrors),
    execute,
    get,
    post,
    put,
    patch,
    del,
    reset,
  }
}
