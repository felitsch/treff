<script setup>
/**
 * ToastItem.vue — Individual Toast Notification
 *
 * Enhanced with:
 *  - Action buttons (e.g. "Im Kalender ansehen" link)
 *  - Progress bar for long-running operations
 *  - Progress type with animated bar
 *
 * @see useToast.js — Toast composable with action/progress support
 * @see ToastContainer.vue — Container that renders these
 */
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
    case 'progress': return '\u231B'
    default: return '\u2713'
  }
}

function handleAction(toast) {
  if (toast.action && typeof toast.action.onClick === 'function') {
    toast.action.onClick()
  }
}
</script>

<template>
  <div
    class="pointer-events-auto rounded-lg shadow-lg border min-w-[300px] overflow-hidden"
    :class="{
      'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-800 text-green-800 dark:text-green-200': toast.type === 'success',
      'bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200': toast.type === 'error',
      'bg-yellow-50 dark:bg-yellow-900/30 border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-200': toast.type === 'warning',
      'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-200': toast.type === 'info',
      'bg-indigo-50 dark:bg-indigo-900/30 border-indigo-200 dark:border-indigo-800 text-indigo-800 dark:text-indigo-200': toast.type === 'progress',
    }"
    :data-toast-id="toast.id"
    data-testid="toast-notification"
    role="alert"
  >
    <!-- Main content row -->
    <div class="px-4 py-3 flex items-start gap-3">
      <!-- Icon -->
      <span
        class="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold"
        :class="{
          'bg-green-200 dark:bg-green-800 text-green-700 dark:text-green-200': toast.type === 'success',
          'bg-red-200 dark:bg-red-800 text-red-700 dark:text-red-200': toast.type === 'error',
          'bg-yellow-200 dark:bg-yellow-800 text-yellow-700 dark:text-yellow-200': toast.type === 'warning',
          'bg-blue-200 dark:bg-blue-800 text-blue-700 dark:text-blue-200': toast.type === 'info',
          'bg-indigo-200 dark:bg-indigo-800 text-indigo-700 dark:text-indigo-200': toast.type === 'progress',
        }"
      >
        <!-- Spinning animation for progress -->
        <span v-if="toast.type === 'progress'" class="animate-spin-slow">{{ getIcon(toast.type) }}</span>
        <span v-else>{{ getIcon(toast.type) }}</span>
      </span>

      <!-- Message + Action -->
      <div class="flex-1 min-w-0">
        <span class="text-sm font-medium">{{ toast.message }}</span>

        <!-- Action button -->
        <button
          v-if="toast.action && toast.action.label"
          @click.stop="handleAction(toast)"
          class="ml-2 text-xs font-semibold underline underline-offset-2 opacity-80 hover:opacity-100 transition-opacity"
          :class="{
            'text-green-700 dark:text-green-300': toast.type === 'success',
            'text-red-700 dark:text-red-300': toast.type === 'error',
            'text-yellow-700 dark:text-yellow-300': toast.type === 'warning',
            'text-blue-700 dark:text-blue-300': toast.type === 'info',
            'text-indigo-700 dark:text-indigo-300': toast.type === 'progress',
          }"
          data-testid="toast-action-button"
        >
          {{ toast.action.label }} &#8594;
        </button>
      </div>

      <!-- Close button -->
      <button
        @click="emit('close', toast.id)"
        class="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity text-lg leading-none"
        :class="{
          'text-green-600 dark:text-green-300': toast.type === 'success',
          'text-red-600 dark:text-red-300': toast.type === 'error',
          'text-yellow-600 dark:text-yellow-300': toast.type === 'warning',
          'text-blue-600 dark:text-blue-300': toast.type === 'info',
          'text-indigo-600 dark:text-indigo-300': toast.type === 'progress',
        }"
        aria-label="Schließen"
        data-testid="toast-close-button"
      >
        &times;
      </button>
    </div>

    <!-- Progress bar (only for progress-type toasts) -->
    <div
      v-if="toast.type === 'progress' && toast.progress !== null"
      class="px-4 pb-3"
      data-testid="toast-progress-container"
    >
      <div class="flex items-center gap-2">
        <div class="flex-1 h-1.5 bg-indigo-200 dark:bg-indigo-800 rounded-full overflow-hidden">
          <div
            class="h-full bg-indigo-500 dark:bg-indigo-400 rounded-full transition-all duration-300 ease-out"
            :style="{ width: toast.progress + '%' }"
            data-testid="toast-progress-bar"
          ></div>
        </div>
        <span class="text-[10px] font-semibold tabular-nums text-indigo-600 dark:text-indigo-300 min-w-[32px] text-right">
          {{ Math.round(toast.progress) }}%
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin-slow {
  display: inline-block;
  animation: spin-slow 2s linear infinite;
}
</style>
