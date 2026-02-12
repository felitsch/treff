<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['complete', 'skip'])

const currentStep = ref(0)
const tooltipStyle = ref({})
const arrowStyle = ref({})
const highlightStyle = ref({})
const isVisible = ref(false)

const steps = [
  {
    target: '[data-tour="sidebar"]',
    title: 'Navigation',
    description:
      'Hier findest du alle Bereiche der App: Dashboard, Posts erstellen, Vorlagen, Assets, Kalender und mehr.',
    position: 'right',
  },
  {
    target: '[data-tour="create-post"]',
    title: 'Post erstellen',
    description:
      'Erstelle neue Social-Media-Posts mit KI-gestuetzter Textgenerierung und professionellen Vorlagen.',
    position: 'right',
  },
  {
    target: '[data-tour="templates"]',
    title: 'Vorlagen',
    description:
      'Waehle aus vorgefertigten Templates fuer Instagram und TikTok, die du individuell anpassen kannst.',
    position: 'right',
  },
  {
    target: '[data-tour="dashboard-stats"]',
    title: 'Dein Dashboard',
    description:
      'Behalte den Ueberblick ueber deine Posts, geplante Inhalte und Assets auf einen Blick.',
    position: 'bottom',
  },
  {
    target: '[data-tour="quick-actions"]',
    title: 'Schnellzugriff',
    description:
      'Starte direkt mit dem Erstellen eines Posts oder oeffne den Kalender fuer die Planung.',
    position: 'bottom',
  },
]

const totalSteps = computed(() => steps.length)

const currentStepData = computed(() => steps[currentStep.value])

const isLastStep = computed(() => currentStep.value === steps.length - 1)

function positionTooltip() {
  const step = steps[currentStep.value]
  if (!step) return

  const el = document.querySelector(step.target)
  if (!el) {
    // Target not found - skip to next or complete
    if (currentStep.value < steps.length - 1) {
      currentStep.value++
      nextTick(() => positionTooltip())
    } else {
      completeTour()
    }
    return
  }

  const rect = el.getBoundingClientRect()

  // Highlight box around the target element
  highlightStyle.value = {
    top: rect.top - 6 + 'px',
    left: rect.left - 6 + 'px',
    width: rect.width + 12 + 'px',
    height: rect.height + 12 + 'px',
  }

  // Position tooltip based on step.position
  const tooltipWidth = 340
  const tooltipOffset = 16

  if (step.position === 'right') {
    tooltipStyle.value = {
      top: rect.top + 'px',
      left: rect.right + tooltipOffset + 'px',
      maxWidth: tooltipWidth + 'px',
    }
    arrowStyle.value = {
      top: '20px',
      left: '-8px',
      borderRight: '8px solid white',
      borderTop: '8px solid transparent',
      borderBottom: '8px solid transparent',
    }
  } else if (step.position === 'bottom') {
    tooltipStyle.value = {
      top: rect.bottom + tooltipOffset + 'px',
      left: rect.left + 'px',
      maxWidth: tooltipWidth + 'px',
    }
    arrowStyle.value = {
      top: '-8px',
      left: '24px',
      borderBottom: '8px solid white',
      borderLeft: '8px solid transparent',
      borderRight: '8px solid transparent',
    }
  } else if (step.position === 'left') {
    tooltipStyle.value = {
      top: rect.top + 'px',
      left: rect.left - tooltipWidth - tooltipOffset + 'px',
      maxWidth: tooltipWidth + 'px',
    }
    arrowStyle.value = {
      top: '20px',
      right: '-8px',
      borderLeft: '8px solid white',
      borderTop: '8px solid transparent',
      borderBottom: '8px solid transparent',
    }
  } else if (step.position === 'top') {
    tooltipStyle.value = {
      bottom: window.innerHeight - rect.top + tooltipOffset + 'px',
      left: rect.left + 'px',
      maxWidth: tooltipWidth + 'px',
    }
    arrowStyle.value = {
      bottom: '-8px',
      left: '24px',
      borderTop: '8px solid white',
      borderLeft: '8px solid transparent',
      borderRight: '8px solid transparent',
    }
  }
}

function nextStep() {
  if (currentStep.value < steps.length - 1) {
    currentStep.value++
    nextTick(() => positionTooltip())
  } else {
    completeTour()
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
    nextTick(() => positionTooltip())
  }
}

function completeTour() {
  isVisible.value = false
  emit('complete')
}

function skipTour() {
  isVisible.value = false
  emit('skip')
}

// Handle window resize
function handleResize() {
  positionTooltip()
}

watch(
  () => props.show,
  (newVal) => {
    if (newVal) {
      currentStep.value = 0
      isVisible.value = true
      nextTick(() => {
        // Small delay to ensure DOM is rendered
        setTimeout(() => positionTooltip(), 100)
      })
    } else {
      isVisible.value = false
    }
  },
  { immediate: true }
)

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <Teleport to="body">
    <div v-if="isVisible" class="onboarding-tour" data-testid="onboarding-tour">
      <!-- Overlay backdrop -->
      <div class="fixed inset-0 bg-black/50 z-[9998]" @click.stop></div>

      <!-- Highlight ring around target element -->
      <div
        class="fixed z-[9999] rounded-xl ring-4 ring-treff-blue/70 bg-transparent pointer-events-none transition-all duration-300"
        :style="highlightStyle"
      ></div>

      <!-- Tooltip card -->
      <div
        class="fixed z-[10000] bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-5 transition-all duration-300"
        :style="tooltipStyle"
      >
        <!-- Arrow -->
        <div class="absolute w-0 h-0" :style="arrowStyle"></div>

        <!-- Step indicator -->
        <div class="flex items-center gap-1.5 mb-3">
          <div
            v-for="(_, idx) in steps"
            :key="idx"
            class="h-1.5 rounded-full transition-all duration-200"
            :class="[
              idx === currentStep
                ? 'w-6 bg-treff-blue'
                : idx < currentStep
                  ? 'w-3 bg-treff-blue/40'
                  : 'w-3 bg-gray-200 dark:bg-gray-600',
            ]"
          ></div>
          <span class="text-xs text-gray-400 dark:text-gray-500 ml-auto">
            {{ currentStep + 1 }}/{{ totalSteps }}
          </span>
        </div>

        <!-- Content -->
        <h3 class="text-base font-bold text-gray-900 dark:text-white mb-1.5">
          {{ currentStepData.title }}
        </h3>
        <p class="text-sm text-gray-600 dark:text-gray-300 leading-relaxed mb-4">
          {{ currentStepData.description }}
        </p>

        <!-- Actions -->
        <div class="flex items-center justify-between">
          <button
            @click="skipTour"
            class="text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            Tour ueberspringen
          </button>
          <div class="flex items-center gap-2">
            <button
              v-if="currentStep > 0"
              @click="prevStep"
              class="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              Zurueck
            </button>
            <button
              @click="nextStep"
              class="px-4 py-1.5 text-xs font-medium text-white bg-treff-blue rounded-lg hover:bg-blue-600 transition-colors"
            >
              {{ isLastStep ? 'Tour beenden' : 'Weiter' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.onboarding-tour {
  /* Ensure high z-index for all children */
}
</style>
