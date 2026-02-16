<template>
  <div
    :class="[
      'skeleton-shimmer rounded',
      roundedClass,
      darkMode ? 'bg-gray-700' : 'bg-gray-200',
      customClass,
    ]"
    :style="computedStyle"
    role="status"
    aria-label="Laden..."
  />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** Width — CSS value (e.g. '100%', '120px', '3/4') */
  width: { type: String, default: '100%' },
  /** Height — CSS value (e.g. '16px', '1rem') */
  height: { type: String, default: '1rem' },
  /** Border radius variant: 'sm' | 'md' | 'lg' | 'xl' | 'full' | 'none' */
  rounded: { type: String, default: 'md' },
  /** If true, renders as a circle (equal width & height) */
  circle: { type: Boolean, default: false },
  /** Additional CSS classes */
  customClass: { type: String, default: '' },
})

const darkMode = computed(() => {
  // We rely on Tailwind dark: classes instead
  return false
})

const roundedClass = computed(() => {
  if (props.circle) return 'rounded-full'
  const map = {
    none: 'rounded-none',
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    '2xl': 'rounded-2xl',
    full: 'rounded-full',
  }
  return map[props.rounded] || 'rounded-md'
})

const computedStyle = computed(() => {
  const style = {}
  if (props.circle) {
    style.width = props.height
    style.height = props.height
  } else {
    style.width = props.width
    style.height = props.height
  }
  return style
})
</script>

<style scoped>
.skeleton-shimmer {
  background: linear-gradient(
    90deg,
    rgb(229 231 235) 0%,
    rgb(243 244 246) 40%,
    rgb(243 244 246) 60%,
    rgb(229 231 235) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

:root.dark .skeleton-shimmer,
.dark .skeleton-shimmer {
  background: linear-gradient(
    90deg,
    rgb(55 65 81) 0%,
    rgb(75 85 99) 40%,
    rgb(75 85 99) 60%,
    rgb(55 65 81) 100%
  );
  background-size: 200% 100%;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
