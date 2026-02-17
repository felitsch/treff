<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflowHints } from '@/composables/useWorkflowHints'
import AppIcon from '@/components/icons/AppIcon.vue'

const props = defineProps({
  /** Unique hint ID for localStorage tracking */
  hintId: { type: String, required: true },
  /** The hint message to display */
  message: { type: String, required: true },
  /** Link text for the action button */
  linkText: { type: String, default: '' },
  /** Vue Router path to navigate to */
  linkTo: { type: String, default: '' },
  /** Icon name for AppIcon component (default: light-bulb) */
  icon: { type: String, default: 'light-bulb' },
  /** Whether the condition to show this hint is met */
  show: { type: Boolean, default: true },
})

const emit = defineEmits(['dismiss'])
const router = useRouter()
const { shouldShowHint, dismissHint } = useWorkflowHints()

const visible = computed(() => props.show && shouldShowHint(props.hintId))

function handleDismiss() {
  dismissHint(props.hintId)
  emit('dismiss', props.hintId)
}

function handleNavigate() {
  if (props.linkTo) {
    router.push(props.linkTo)
  }
}
</script>

<template>
  <transition
    enter-active-class="transition-all duration-300 ease-out"
    enter-from-class="opacity-0 -translate-y-2"
    enter-to-class="opacity-100 translate-y-0"
    leave-active-class="transition-all duration-200 ease-in"
    leave-from-class="opacity-100 translate-y-0"
    leave-to-class="opacity-0 -translate-y-2"
  >
    <div
      v-if="visible"
      class="mb-4 rounded-lg border border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20 px-4 py-3 flex items-start gap-3"
      role="status"
      data-testid="workflow-hint"
    >
      <!-- Icon -->
      <AppIcon :name="icon" class="w-5 h-5 flex-shrink-0 mt-0.5 text-blue-500 dark:text-blue-400" />

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <p class="text-sm text-blue-800 dark:text-blue-200">
          {{ message }}
          <button
            v-if="linkText && linkTo"
            @click="handleNavigate"
            class="inline-flex items-center gap-1 ml-1 font-semibold text-blue-700 dark:text-blue-300 hover:text-blue-900 dark:hover:text-blue-100 underline underline-offset-2 transition-colors"
          >
            {{ linkText }} &rarr;
          </button>
        </p>
      </div>

      <!-- Dismiss button -->
      <button
        @click="handleDismiss"
        class="flex-shrink-0 text-blue-400 hover:text-blue-600 dark:text-blue-500 dark:hover:text-blue-300 transition-colors p-1 rounded hover:bg-blue-100 dark:hover:bg-blue-800/50"
        title="Hinweis schliessen"
        aria-label="Hinweis schliessen"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  </transition>
</template>
