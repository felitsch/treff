<script setup>
defineProps({
  toast: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close'])

function getIcon(type) {
  switch (type) {
    case 'success': return '\u2713'
    case 'error': return '\u2716'
    case 'warning': return '\u26A0'
    case 'info': return '\u2139'
    default: return '\u2713'
  }
}
</script>

<template>
  <div
    class="pointer-events-auto rounded-lg shadow-lg border px-4 py-3 flex items-start gap-3 min-w-[300px]"
    :class="{
      'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-800 text-green-800 dark:text-green-200': toast.type === 'success',
      'bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200': toast.type === 'error',
      'bg-yellow-50 dark:bg-yellow-900/30 border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-200': toast.type === 'warning',
      'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-200': toast.type === 'info',
    }"
    :data-toast-id="toast.id"
    data-testid="toast-notification"
    role="alert"
  >
    <!-- Icon -->
    <span
      class="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold"
      :class="{
        'bg-green-200 dark:bg-green-800 text-green-700 dark:text-green-200': toast.type === 'success',
        'bg-red-200 dark:bg-red-800 text-red-700 dark:text-red-200': toast.type === 'error',
        'bg-yellow-200 dark:bg-yellow-800 text-yellow-700 dark:text-yellow-200': toast.type === 'warning',
        'bg-blue-200 dark:bg-blue-800 text-blue-700 dark:text-blue-200': toast.type === 'info',
      }"
    >
      {{ getIcon(toast.type) }}
    </span>

    <!-- Message -->
    <span class="flex-1 text-sm font-medium">{{ toast.message }}</span>

    <!-- Close button -->
    <button
      @click="emit('close', toast.id)"
      class="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity text-lg leading-none"
      :class="{
        'text-green-600 dark:text-green-300': toast.type === 'success',
        'text-red-600 dark:text-red-300': toast.type === 'error',
        'text-yellow-600 dark:text-yellow-300': toast.type === 'warning',
        'text-blue-600 dark:text-blue-300': toast.type === 'info',
      }"
      aria-label="Schliessen"
      data-testid="toast-close-button"
    >
      &times;
    </button>
  </div>
</template>
