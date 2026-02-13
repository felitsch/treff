<script setup>
/**
 * TourSystem – reusable page-level guided tour component.
 *
 * Props:
 *   pageKey  – matches a key in tourConfigs (e.g. 'dashboard', 'templates')
 *   autoStart – if true, auto-trigger on first visit (default: true)
 *
 * Emits:
 *   complete – when the user finishes or skips the tour
 *
 * Usage inside any page view:
 *   <TourSystem page-key="templates" />
 *   <!-- plus a manual restart button -->
 *   <button @click="tourRef?.startTour()">Tour starten</button>
 */
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useTour } from '@/composables/useTour'
import tourConfigs from '@/tours/tourConfigs'

const props = defineProps({
  pageKey: {
    type: String,
    required: true,
  },
  autoStart: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['complete'])

const { loadTourProgress, markTourSeen, hasSeenTour, loadedFromBackend } = useTour()

const currentStep = ref(0)
const tooltipStyle = ref({})
const arrowStyle = ref({})
const highlightStyle = ref({})
const isVisible = ref(false)

const config = computed(() => tourConfigs[props.pageKey])
const steps = computed(() => config.value?.steps || [])
const totalSteps = computed(() => steps.value.length)
const currentStepData = computed(() => steps.value[currentStep.value])
const isLastStep = computed(() => currentStep.value === steps.value.length - 1)

// ─── Positioning ───────────────────────────────────────────

function positionTooltip() {
  const step = steps.value[currentStep.value]
  if (!step) return

  const el = document.querySelector(step.target)
  if (!el) {
    // Target not found – skip to next or complete
    if (currentStep.value < steps.value.length - 1) {
      currentStep.value++
      nextTick(() => positionTooltip())
    } else {
      completeTour()
    }
    return
  }

  // Scroll element into view if needed
  el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })

  // Small delay after scroll to get correct rect
  setTimeout(() => {
    const rect = el.getBoundingClientRect()

    // Highlight box
    highlightStyle.value = {
      top: rect.top - 6 + 'px',
      left: rect.left - 6 + 'px',
      width: rect.width + 12 + 'px',
      height: rect.height + 12 + 'px',
    }

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
  }, 100)
}

// ─── Navigation ────────────────────────────────────────────

function nextStep() {
  if (currentStep.value < steps.value.length - 1) {
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

async function completeTour() {
  isVisible.value = false
  await markTourSeen(props.pageKey)
  emit('complete')
}

function skipTour() {
  completeTour()
}

// ─── Public: allow parent to start tour manually ───────────
function startTour() {
  if (!steps.value.length) return
  currentStep.value = 0
  isVisible.value = true
  nextTick(() => {
    setTimeout(() => positionTooltip(), 200)
  })
}

defineExpose({ startTour })

// ─── Resize handler ────────────────────────────────────────
function handleResize() {
  if (isVisible.value) positionTooltip()
}

// ─── Auto-start on first visit ─────────────────────────────
onMounted(async () => {
  window.addEventListener('resize', handleResize)

  if (!props.autoStart || !steps.value.length) return

  await loadTourProgress()

  if (!hasSeenTour(props.pageKey)) {
    // First visit – auto-start after DOM settles
    setTimeout(() => {
      startTour()
    }, 600)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  isVisible.value = false
})
</script>

<template>
  <Teleport to="body">
    <div v-if="isVisible && currentStepData" class="tour-system" data-testid="tour-system">
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

        <!-- Page tour title badge -->
        <div class="flex items-center gap-2 mb-2">
          <span class="text-[10px] uppercase tracking-wider font-semibold text-treff-blue bg-treff-blue/10 px-2 py-0.5 rounded-full">
            {{ config?.title || 'Tour' }}
          </span>
        </div>

        <!-- Step indicator dots -->
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
.tour-system {
  /* Container for z-index stacking context */
}
</style>
