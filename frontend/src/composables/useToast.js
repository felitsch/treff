import { ref } from 'vue'

const toasts = ref([])
let idCounter = 0

export function useToast() {
  function addToast({ message, type = 'success', duration = 5000 }) {
    const id = ++idCounter
    toasts.value.push({ id, message, type, visible: true })

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

  function success(message, duration = 5000) {
    return addToast({ message, type: 'success', duration })
  }

  function error(message, duration = 0) {
    return addToast({ message, type: 'error', duration })
  }

  function info(message, duration = 5000) {
    return addToast({ message, type: 'info', duration })
  }

  return {
    toasts,
    addToast,
    removeToast,
    success,
    info,
    error,
  }
}
