<script setup>
/**
 * TBadge.vue — TREFF Design System Badge Component.
 *
 * Status badges for post workflow states and general-purpose labeling.
 * Supports semantic variants mapped to the post lifecycle:
 *   draft → gray, scheduled → blue, exported → yellow, posted → green, error → red
 *
 * Props:
 *   variant (String)  — 'draft' | 'scheduled' | 'exported' | 'posted' | 'error' | 'info' | 'warning'
 *   size    (String)  — 'sm' | 'md' (default: 'md')
 *   dot     (Boolean) — Show a colored dot indicator before text
 *   pill    (Boolean) — Use fully rounded pill shape (default: true)
 *   removable (Boolean) — Show X button to remove
 *
 * Slots:
 *   default — Badge text content
 *
 * Events:
 *   remove — Emitted when removable badge X is clicked
 */
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'draft',
    validator: (v) => ['draft', 'scheduled', 'exported', 'posted', 'error', 'info', 'warning'].includes(v),
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md'].includes(v),
  },
  dot: {
    type: Boolean,
    default: false,
  },
  pill: {
    type: Boolean,
    default: true,
  },
  removable: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['remove'])

// Variant color mappings: bg, text, dot, border
const variantConfig = {
  draft: {
    bg: 'bg-gray-100 dark:bg-gray-700',
    text: 'text-gray-600 dark:text-gray-300',
    dot: 'bg-gray-400 dark:bg-gray-500',
    border: 'border-gray-200 dark:border-gray-600',
    hoverRemove: 'hover:bg-gray-200 dark:hover:bg-gray-600',
  },
  scheduled: {
    bg: 'bg-blue-50 dark:bg-blue-900/30',
    text: 'text-blue-700 dark:text-blue-300',
    dot: 'bg-blue-500 dark:bg-blue-400',
    border: 'border-blue-200 dark:border-blue-700',
    hoverRemove: 'hover:bg-blue-100 dark:hover:bg-blue-800/50',
  },
  exported: {
    bg: 'bg-yellow-50 dark:bg-yellow-900/30',
    text: 'text-yellow-700 dark:text-yellow-300',
    dot: 'bg-yellow-500 dark:bg-yellow-400',
    border: 'border-yellow-200 dark:border-yellow-700',
    hoverRemove: 'hover:bg-yellow-100 dark:hover:bg-yellow-800/50',
  },
  posted: {
    bg: 'bg-green-50 dark:bg-green-900/30',
    text: 'text-green-700 dark:text-green-300',
    dot: 'bg-green-500 dark:bg-green-400',
    border: 'border-green-200 dark:border-green-700',
    hoverRemove: 'hover:bg-green-100 dark:hover:bg-green-800/50',
  },
  error: {
    bg: 'bg-red-50 dark:bg-red-900/30',
    text: 'text-red-700 dark:text-red-300',
    dot: 'bg-red-500 dark:bg-red-400',
    border: 'border-red-200 dark:border-red-700',
    hoverRemove: 'hover:bg-red-100 dark:hover:bg-red-800/50',
  },
  info: {
    bg: 'bg-primary-50 dark:bg-primary-900/30',
    text: 'text-primary-700 dark:text-primary-300',
    dot: 'bg-primary-500 dark:bg-primary-400',
    border: 'border-primary-200 dark:border-primary-700',
    hoverRemove: 'hover:bg-primary-100 dark:hover:bg-primary-800/50',
  },
  warning: {
    bg: 'bg-orange-50 dark:bg-orange-900/30',
    text: 'text-orange-700 dark:text-orange-300',
    dot: 'bg-orange-500 dark:bg-orange-400',
    border: 'border-orange-200 dark:border-orange-700',
    hoverRemove: 'hover:bg-orange-100 dark:hover:bg-orange-800/50',
  },
}

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs gap-1',
  md: 'px-2.5 py-1 text-xs gap-1.5',
}

const dotSizeClasses = {
  sm: 'w-1.5 h-1.5',
  md: 'w-2 h-2',
}

const config = computed(() => variantConfig[props.variant])

const badgeClasses = computed(() => [
  'inline-flex items-center font-medium',
  'transition-colors duration-150',
  config.value.bg,
  config.value.text,
  sizeClasses[props.size],
  props.pill ? 'rounded-full' : 'rounded-md',
])
</script>

<template>
  <span
    :class="badgeClasses"
    data-testid="t-badge"
    :data-variant="variant"
  >
    <!-- Dot indicator -->
    <span
      v-if="dot"
      :class="['rounded-full shrink-0', config.dot, dotSizeClasses[size]]"
      aria-hidden="true"
    />

    <!-- Badge text -->
    <slot />

    <!-- Remove button -->
    <button
      v-if="removable"
      type="button"
      :class="[
        'ml-0.5 -mr-1 inline-flex items-center justify-center rounded-full',
        'w-4 h-4 transition-colors duration-150',
        config.hoverRemove,
      ]"
      aria-label="Entfernen"
      @click.stop="emit('remove')"
    >
      <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </span>
</template>
