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
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
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

const { loadTourProgress, markTourSeen, hasSeenTour, loadedFromBackend, tourStartRequest, clearTourStartRequest } = useTour()

const tooltipEl = ref(null)
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

const OFFSET = 12
const TOOLTIP_WIDTH = 340

function isElementInViewport(el) {
  const r = el.getBoundingClientRect()
  return r.top >= 16 && r.bottom <= window.innerHeight - 16
}

function afterPaint(fn) {
  requestAnimationFrame(() => requestAnimationFrame(fn))
}

function resolvePosition(preferred, rect, actualH, actualW, vw, vh) {
  const space = {
    bottom: vh - rect.bottom - OFFSET,
    top: rect.top - OFFSET,
    right: vw - rect.right - OFFSET,
    left: rect.left - OFFSET,
  }
  const order = {
    bottom: ['bottom', 'top', 'right', 'left'],
    top: ['top', 'bottom', 'right', 'left'],
    right: ['right', 'left', 'bottom', 'top'],
    left: ['left', 'right', 'bottom', 'top'],
  }[preferred] || ['bottom', 'top', 'right', 'left']

  for (const dir of order) {
    if ((dir === 'bottom' || dir === 'top') && space[dir] >= actualH) return dir
    if ((dir === 'right' || dir === 'left') && space[dir] >= actualW) return dir
  }
  return 'center'
}

function applyPosition(dir, rect, actualH, actualW, vw, vh) {
  function clampLeft(l) {
    return Math.max(16, Math.min(l, vw - TOOLTIP_WIDTH - 16))
  }
  function clampTop(t) {
    return Math.max(16, Math.min(t, vh - actualH - 16))
  }

  if (dir === 'bottom') {
    tooltipStyle.value = {
      top: (rect.bottom + OFFSET) + 'px',
      left: clampLeft(rect.left) + 'px',
      maxWidth: TOOLTIP_WIDTH + 'px',
      visibility: 'visible',
    }
    arrowStyle.value = {
      top: '-8px',
      left: '24px',
      borderBottom: '8px solid white',
      borderLeft: '8px solid transparent',
      borderRight: '8px solid transparent',
    }
  } else if (dir === 'top') {
    tooltipStyle.value = {
      top: Math.max(16, rect.top - OFFSET - actualH) + 'px',
      left: clampLeft(rect.left) + 'px',
      maxWidth: TOOLTIP_WIDTH + 'px',
      visibility: 'visible',
    }
    arrowStyle.value = {
      bottom: '-8px',
      left: '24px',
      borderTop: '8px solid white',
      borderLeft: '8px solid transparent',
      borderRight: '8px solid transparent',
    }
  } else if (dir === 'right') {
    tooltipStyle.value = {
      top: clampTop(rect.top) + 'px',
      left: clampLeft(rect.right + OFFSET) + 'px',
      maxWidth: TOOLTIP_WIDTH + 'px',
      visibility: 'visible',
    }
    arrowStyle.value = {
      top: '20px',
      left: '-8px',
      borderRight: '8px solid white',
      borderTop: '8px solid transparent',
      borderBottom: '8px solid transparent',
    }
  } else if (dir === 'left') {
    tooltipStyle.value = {
      top: clampTop(rect.top) + 'px',
      left: Math.max(16, rect.left - TOOLTIP_WIDTH - OFFSET) + 'px',
      maxWidth: TOOLTIP_WIDTH + 'px',
      visibility: 'visible',
    }
    arrowStyle.value = {
      top: '20px',
      right: '-8px',
      borderLeft: '8px solid white',
      borderTop: '8px solid transparent',
      borderBottom: '8px solid transparent',
    }
  } else {
    // center fallback
    tooltipStyle.value = {
      top: Math.max(16, (vh - actualH) / 2) + 'px',
      left: Math.max(16, (vw - TOOLTIP_WIDTH) / 2) + 'px',
      maxWidth: TOOLTIP_WIDTH + 'px',
      visibility: 'visible',
    }
    arrowStyle.value = {}
  }
}

function positionTooltip() {
  const step = steps.value[currentStep.value]
  if (!step) return

  const el = document.querySelector(step.target)
  if (!el) {
    if (currentStep.value < steps.value.length - 1) {
      currentStep.value++
      positionTooltip()
    } else {
      completeTour()
    }
    return
  }

  const needsScroll = !isElementInViewport(el)
  if (needsScroll) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
  const scrollDelay = needsScroll ? 450 : 0

  // Pass 1: render tooltip invisibly so the browser can calculate its real height
  tooltipStyle.value = {
    top: '-9999px',
    left: '-9999px',
    maxWidth: TOOLTIP_WIDTH + 'px',
    visibility: 'hidden',
  }
  arrowStyle.value = {}

  setTimeout(() => {
    afterPaint(() => {
      const rect = el.getBoundingClientRect()
      const vw = window.innerWidth
      const vh = window.innerHeight

      // Highlight ring
      const hlTop = Math.max(0, rect.top - 6)
      const hlLeft = Math.max(0, rect.left - 6)
      const hlHeight = Math.min(rect.height + 12, vh - hlTop)
      const hlWidth = Math.min(rect.width + 12, vw - hlLeft)
      highlightStyle.value = {
        top: hlTop + 'px',
        left: hlLeft + 'px',
        width: hlWidth + 'px',
        height: hlHeight + 'px',
      }

      // Pass 2: measure actual tooltip height after browser paint
      const actualH = tooltipEl.value ? tooltipEl.value.getBoundingClientRect().height : 300
      const dir = resolvePosition(step.position || 'bottom', rect, actualH, TOOLTIP_WIDTH, vw, vh)
      applyPosition(dir, rect, actualH, TOOLTIP_WIDTH, vw, vh)
    })
  }, scrollDelay)
}

// ─── Navigation ────────────────────────────────────────────

function nextStep() {
  if (currentStep.value < steps.value.length - 1) {
    currentStep.value++
    positionTooltip()
  } else {
    completeTour()
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
    positionTooltip()
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
  positionTooltip()
}

defineExpose({ startTour })

// ─── Resize handler ────────────────────────────────────────
function handleResize() {
  if (isVisible.value) positionTooltip()
}

// ─── Watch for external tour start requests (from TopBar button) ──
watch(tourStartRequest, (req) => {
  if (req && req.pageKey === props.pageKey) {
    clearTourStartRequest()
    startTour()
  }
})

// ─── Video page keys that have a workflow overview tour ──────
const videoPageKeys = [
  'thumbnail-generator', 'video-overlays', 'video-composer',
  'video-templates', 'video-export', 'audio-mixer',
]

// ─── Auto-start on first visit ─────────────────────────────
onMounted(async () => {
  window.addEventListener('resize', handleResize)

  if (!props.autoStart || !steps.value.length) return

  await loadTourProgress()

  if (!hasSeenTour(props.pageKey)) {
    // If this is a video page and the overview tour hasn't been seen,
    // delay the page tour to avoid overlap with the workflow overview tour
    if (videoPageKeys.includes(props.pageKey) && !hasSeenTour('video-tools-overview')) {
      // Don't auto-start – the user will see the overview first,
      // then can start the page tour via the "? Tour" button or on next visit
      return
    }
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
        ref="tooltipEl"
        class="fixed z-[10000] bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-5 transition-all duration-300 max-h-[calc(100vh-32px)] overflow-y-auto"
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
            Tour überspringen
          </button>
          <div class="flex items-center gap-2">
            <button
              v-if="currentStep > 0"
              @click="prevStep"
              class="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              Zurück
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
