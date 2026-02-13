<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'

const props = defineProps({
  text: {
    type: String,
    required: true,
  },
  position: {
    type: String,
    default: 'auto', // auto, top, bottom, left, right
    validator: (v) => ['auto', 'top', 'bottom', 'left', 'right'].includes(v),
  },
  icon: {
    type: String,
    default: 'info', // 'info' or 'question'
  },
  size: {
    type: String,
    default: 'sm', // 'sm', 'md', 'lg'
    validator: (v) => ['sm', 'md', 'lg'].includes(v),
  },
  inline: {
    type: Boolean,
    default: true,
  },
  maxWidth: {
    type: String,
    default: '280px',
  },
})

const isVisible = ref(false)
const tooltipRef = ref(null)
const triggerRef = ref(null)
const tooltipEl = ref(null)
const computedPosition = ref(props.position === 'auto' ? 'top' : props.position)

let hideTimeout = null

function show() {
  if (hideTimeout) {
    clearTimeout(hideTimeout)
    hideTimeout = null
  }
  isVisible.value = true
  nextTick(() => {
    if (props.position === 'auto') {
      calculatePosition()
    }
  })
}

function hide() {
  hideTimeout = setTimeout(() => {
    isVisible.value = false
  }, 150)
}

function toggle(e) {
  e.stopPropagation()
  if (isVisible.value) {
    isVisible.value = false
  } else {
    show()
  }
}

function calculatePosition() {
  if (!triggerRef.value || !tooltipEl.value) return

  const trigger = triggerRef.value.getBoundingClientRect()
  const tooltip = tooltipEl.value.getBoundingClientRect()
  const viewportW = window.innerWidth
  const viewportH = window.innerHeight
  const margin = 8

  // Calculate available space in each direction
  const spaceAbove = trigger.top - margin
  const spaceBelow = viewportH - trigger.bottom - margin
  const spaceLeft = trigger.left - margin
  const spaceRight = viewportW - trigger.right - margin

  // Prefer top, fallback to bottom, then right, then left
  if (spaceAbove >= tooltip.height) {
    computedPosition.value = 'top'
  } else if (spaceBelow >= tooltip.height) {
    computedPosition.value = 'bottom'
  } else if (spaceRight >= tooltip.width) {
    computedPosition.value = 'right'
  } else if (spaceLeft >= tooltip.width) {
    computedPosition.value = 'left'
  } else {
    // Default to top if nothing fits well
    computedPosition.value = 'top'
  }
}

function handleClickOutside(e) {
  if (tooltipRef.value && !tooltipRef.value.contains(e.target)) {
    isVisible.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (hideTimeout) clearTimeout(hideTimeout)
})

const iconClass = computed(() => {
  const base = 'inline-flex items-center justify-center rounded-full cursor-help transition-colors duration-150 flex-shrink-0'
  const sizes = {
    sm: 'w-4 h-4 text-[10px]',
    md: 'w-5 h-5 text-xs',
    lg: 'w-6 h-6 text-sm',
  }
  return `${base} ${sizes[props.size]}`
})

const positionClasses = computed(() => {
  const pos = props.position === 'auto' ? computedPosition.value : props.position
  switch (pos) {
    case 'top':
      return 'bottom-full left-1/2 -translate-x-1/2 mb-2'
    case 'bottom':
      return 'top-full left-1/2 -translate-x-1/2 mt-2'
    case 'left':
      return 'right-full top-1/2 -translate-y-1/2 mr-2'
    case 'right':
      return 'left-full top-1/2 -translate-y-1/2 ml-2'
    default:
      return 'bottom-full left-1/2 -translate-x-1/2 mb-2'
  }
})

const arrowClasses = computed(() => {
  const pos = props.position === 'auto' ? computedPosition.value : props.position
  switch (pos) {
    case 'top':
      return 'top-full left-1/2 -translate-x-1/2 border-t-gray-800 dark:border-t-gray-200 border-l-transparent border-r-transparent border-b-transparent border-4'
    case 'bottom':
      return 'bottom-full left-1/2 -translate-x-1/2 border-b-gray-800 dark:border-b-gray-200 border-l-transparent border-r-transparent border-t-transparent border-4'
    case 'left':
      return 'left-full top-1/2 -translate-y-1/2 border-l-gray-800 dark:border-l-gray-200 border-t-transparent border-b-transparent border-r-transparent border-4'
    case 'right':
      return 'right-full top-1/2 -translate-y-1/2 border-r-gray-800 dark:border-r-gray-200 border-t-transparent border-b-transparent border-l-transparent border-4'
    default:
      return 'top-full left-1/2 -translate-x-1/2 border-t-gray-800 dark:border-t-gray-200 border-l-transparent border-r-transparent border-b-transparent border-4'
  }
})
</script>

<template>
  <span
    ref="tooltipRef"
    :class="['relative', inline ? 'inline-flex items-center' : 'block']"
  >
    <button
      ref="triggerRef"
      type="button"
      :class="iconClass"
      class="bg-gray-200 dark:bg-gray-600 text-gray-500 dark:text-gray-300 hover:bg-blue-100 dark:hover:bg-blue-900 hover:text-blue-600 dark:hover:text-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-300 dark:focus:ring-blue-700"
      :aria-label="'Hilfe: ' + text"
      @mouseenter="show"
      @mouseleave="hide"
      @click="toggle"
      @focus="show"
      @blur="hide"
    >
      <template v-if="icon === 'info'">
        <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 16" class="w-[60%] h-[60%]">
          <path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm0 2.5a1 1 0 1 1 0 2 1 1 0 0 1 0-2zM6.5 7h2v4.5h-2V7h1z"/>
          <rect x="7" y="3.5" width="2" height="2" rx="1"/>
          <rect x="7" y="7" width="2" height="4" rx="0.5"/>
        </svg>
      </template>
      <template v-else>
        <span class="font-bold leading-none">?</span>
      </template>
    </button>

    <Transition
      enter-active-class="transition-opacity duration-150 ease-out"
      leave-active-class="transition-opacity duration-100 ease-in"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isVisible"
        ref="tooltipEl"
        role="tooltip"
        :class="['absolute z-50 pointer-events-auto', positionClasses]"
        :style="{ maxWidth: maxWidth }"
        @mouseenter="show"
        @mouseleave="hide"
      >
        <div
          class="bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-900 text-xs leading-relaxed px-3 py-2 rounded-lg shadow-lg"
        >
          {{ text }}
        </div>
        <div :class="['absolute w-0 h-0', arrowClasses]"></div>
      </div>
    </Transition>
  </span>
</template>
