<template>
  <div
    v-if="message"
    class="rounded-lg border px-4 py-3 flex items-start gap-3"
    :class="variantClasses"
    role="alert"
    data-testid="error-banner"
  >
    <!-- Icon -->
    <span class="shrink-0 mt-0.5 text-lg" aria-hidden="true">{{ icon }}</span>

    <!-- Content -->
    <div class="flex-1 min-w-0">
      <p class="text-sm font-medium" :class="textClass">{{ message }}</p>
      <p v-if="detail" class="text-xs mt-1 opacity-75">{{ detail }}</p>
    </div>

    <!-- Retry button -->
    <button
      v-if="retryable"
      @click="$emit('retry')"
      class="shrink-0 text-sm font-medium underline hover:no-underline focus:outline-none focus:ring-2 focus:ring-offset-1 rounded"
      :class="textClass"
    >
      Erneut versuchen
    </button>

    <!-- Dismiss button -->
    <button
      v-if="dismissible"
      @click="$emit('dismiss')"
      class="shrink-0 text-lg leading-none opacity-50 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-offset-1 rounded"
      :class="textClass"
      aria-label="Fehler schliessen"
    >
      &times;
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** Error message to display */
  message: { type: String, default: '' },
  /** Optional detail/description below the message */
  detail: { type: String, default: '' },
  /** Variant: 'error' (red), 'warning' (yellow), 'info' (blue) */
  variant: { type: String, default: 'error', validator: v => ['error', 'warning', 'info'].includes(v) },
  /** Show a "Erneut versuchen" button */
  retryable: { type: Boolean, default: false },
  /** Show a dismiss (x) button */
  dismissible: { type: Boolean, default: false },
})

defineEmits(['retry', 'dismiss'])

const icon = computed(() => {
  switch (props.variant) {
    case 'warning': return '\u26A0\uFE0F'
    case 'info': return '\u2139\uFE0F'
    default: return '\u274C'
  }
})

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'warning':
      return 'bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-700'
    case 'info':
      return 'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-700'
    default:
      return 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-700'
  }
})

const textClass = computed(() => {
  switch (props.variant) {
    case 'warning': return 'text-yellow-800 dark:text-yellow-200'
    case 'info': return 'text-blue-800 dark:text-blue-200'
    default: return 'text-red-800 dark:text-red-200'
  }
})
</script>
