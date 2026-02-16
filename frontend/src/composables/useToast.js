import { ref, computed } from 'vue'

const toasts = ref([])
let idCounter = 0
const MAX_VISIBLE = 3

export function useToast() {
  const visibleToasts = computed(() => toasts.value.slice(-MAX_VISIBLE))

  function addToast({ message, type = 'success', duration = 5000 }) {
    const id = ++idCounter
    toasts.value.push({ id, message, type, visible: true })

    // FIFO: remove oldest when exceeding max
    while (toasts.value.length > MAX_VISIBLE) {
      const oldest = toasts.value[0]
      if (oldest) {
        toasts.value.shift()
      }
    }

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, duration)
    }

    return id
  }

  function removeToast(id) {
    const idx = toasts.value.findIndex(t => t.id === id)
    if (idx !== -1) {
      toasts.value[idx].visible = false
      // Remove from array after transition
      setTimeout(() => {
        toasts.value = toasts.value.filter(t => t.id !== id)
      }, 300)
    }
  }

  function clear() {
    toasts.value = []
  }

  function success(message, duration = 5000) {
    return addToast({ message, type: 'success', duration })
  }

  function error(message, duration = 0) {
    return addToast({ message, type: 'error', duration })
  }

  function warning(message, duration = 5000) {
    return addToast({ message, type: 'warning', duration })
  }

  function info(message, duration = 5000) {
    return addToast({ message, type: 'info', duration })
  }

  return {
    toasts,
    visibleToasts,
    addToast,
    removeToast,
    clear,
    success,
    warning,
    info,
    error,
  }
}
