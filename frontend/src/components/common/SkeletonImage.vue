<template>
  <div
    :class="[
      'skeleton-shimmer overflow-hidden',
      roundedClass,
    ]"
    :style="containerStyle"
    role="status"
    aria-label="Bild wird geladen..."
  >
    <!-- Image icon placeholder centered -->
    <div class="w-full h-full flex items-center justify-center">
      <svg
        class="w-8 h-8 text-gray-300 dark:text-gray-600"
        fill="currentColor"
        viewBox="0 0 24 24"
      >
        <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z" />
      </svg>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** Aspect ratio: 'square' | '16/9' | '4/3' | '3/4' | '9/16' */
  aspect: { type: String, default: 'square' },
  /** Width — CSS value */
  width: { type: String, default: '100%' },
  /** Height — CSS value (overrides aspect ratio if set) */
  height: { type: String, default: '' },
  /** Border radius variant */
  rounded: { type: String, default: 'lg' },
})

const roundedClass = computed(() => {
  const map = {
    none: 'rounded-none',
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    '2xl': 'rounded-2xl',
    full: 'rounded-full',
    't-xl': 'rounded-t-xl',
  }
  return map[props.rounded] || 'rounded-lg'
})

const containerStyle = computed(() => {
  const style = { width: props.width }
  if (props.height) {
    style.height = props.height
  } else {
    const aspectMap = {
      square: '1 / 1',
      '16/9': '16 / 9',
      '4/3': '4 / 3',
      '3/4': '3 / 4',
      '9/16': '9 / 16',
    }
    style.aspectRatio = aspectMap[props.aspect] || '1 / 1'
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
