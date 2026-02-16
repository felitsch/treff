<script setup>
/**
 * StepIndicator.vue — Horizontal step indicator bar with clickable steps.
 *
 * Used in the 3-step Post Creator flow to show progress and allow
 * jumping back to previous (completed) steps.
 */

const props = defineProps({
  steps: {
    type: Array,
    required: true,
    // Each step: { label: string, icon?: string }
  },
  currentStep: {
    type: Number,
    default: 1,
  },
  /** Allow clicking ahead to incomplete steps */
  allowSkipAhead: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:currentStep'])

function isClickable(stepIdx) {
  const stepNum = stepIdx + 1
  if (stepNum === props.currentStep) return false // Already on this step
  if (stepNum < props.currentStep) return true // Can always go back
  if (props.allowSkipAhead) return true
  return false
}

function goToStep(stepIdx) {
  if (isClickable(stepIdx)) {
    emit('update:currentStep', stepIdx + 1)
  }
}
</script>

<template>
  <div class="step-indicator" data-testid="step-indicator">
    <div class="flex items-center w-full">
      <template v-for="(step, idx) in steps" :key="idx">
        <!-- Step circle + label -->
        <button
          @click="goToStep(idx)"
          class="flex items-center gap-2 group relative flex-shrink-0 transition-all"
          :class="isClickable(idx) ? 'cursor-pointer' : idx + 1 === currentStep ? 'cursor-default' : 'cursor-not-allowed'"
          :data-testid="'step-' + (idx + 1)"
          :aria-current="idx + 1 === currentStep ? 'step' : undefined"
        >
          <!-- Circle -->
          <div
            class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-300"
            :class="{
              'bg-[#3B7AB1] text-white ring-4 ring-[#3B7AB1]/20 shadow-lg shadow-[#3B7AB1]/20': idx + 1 === currentStep,
              'bg-green-500 text-white': idx + 1 < currentStep,
              'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500': idx + 1 > currentStep,
            }"
          >
            <span v-if="idx + 1 < currentStep" class="text-base">&#10003;</span>
            <span v-else-if="step.icon" class="text-base">{{ step.icon }}</span>
            <span v-else>{{ idx + 1 }}</span>
          </div>

          <!-- Label -->
          <div class="hidden sm:flex flex-col">
            <span
              class="text-sm font-semibold transition-colors"
              :class="{
                'text-[#3B7AB1] dark:text-blue-400': idx + 1 === currentStep,
                'text-green-600 dark:text-green-400': idx + 1 < currentStep,
                'text-gray-400 dark:text-gray-500': idx + 1 > currentStep,
              }"
            >{{ step.label }}</span>
            <span
              v-if="step.sublabel"
              class="text-[10px] leading-tight"
              :class="{
                'text-gray-500 dark:text-gray-400': idx + 1 === currentStep,
                'text-green-500 dark:text-green-500': idx + 1 < currentStep,
                'text-gray-300 dark:text-gray-600': idx + 1 > currentStep,
              }"
            >{{ step.sublabel }}</span>
          </div>
        </button>

        <!-- Connector line -->
        <div
          v-if="idx < steps.length - 1"
          class="flex-1 h-0.5 mx-3 rounded-full transition-colors duration-300"
          :class="idx + 1 < currentStep ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700'"
        ></div>
      </template>
    </div>
  </div>
</template>
