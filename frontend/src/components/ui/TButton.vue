<script setup>
/**
 * TButton.vue — TREFF Design System Button Component.
 *
 * A versatile button component supporting multiple variants, sizes,
 * loading states, and icon slots. Uses TREFF brand colors and follows
 * the design system's spacing and typography tokens.
 *
 * Props:
 *   variant  (String)  — 'primary' | 'secondary' | 'ghost' | 'danger' (default: 'primary')
 *   size     (String)  — 'sm' | 'md' | 'lg' (default: 'md')
 *   loading  (Boolean) — Shows spinner and disables interaction
 *   disabled (Boolean) — Disables the button
 *   type     (String)  — HTML button type: 'button' | 'submit' | 'reset'
 *   tag      (String)  — Render as different element (e.g. 'a', 'router-link')
 *   to       (String|Object) — Vue Router destination (renders as router-link)
 *   href     (String)  — External link (renders as <a>)
 *   block    (Boolean) — Full width button
 *
 * Slots:
 *   icon-left  — Icon before text
 *   default    — Button label
 *   icon-right — Icon after text
 *
 * @see BaseCard.vue for card-level component
 */
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'ghost', 'danger'].includes(v),
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v),
  },
  loading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  type: {
    type: String,
    default: 'button',
  },
  tag: {
    type: String,
    default: 'button',
  },
  to: {
    type: [String, Object],
    default: null,
  },
  href: {
    type: String,
    default: null,
  },
  block: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['click'])

// Determine which element/component to render
const componentTag = computed(() => {
  if (props.to) return 'router-link'
  if (props.href) return 'a'
  return props.tag
})

// Extra attributes for links
const linkAttrs = computed(() => {
  if (props.to) return { to: props.to }
  if (props.href) return { href: props.href, target: '_blank', rel: 'noopener noreferrer' }
  return { type: props.type }
})

const isDisabled = computed(() => props.disabled || props.loading)

// Variant classes
const variantClasses = {
  primary: [
    'bg-primary-500 text-white',
    'hover:bg-primary-600 active:bg-primary-700',
    'focus-visible:ring-2 focus-visible:ring-primary-300 focus-visible:ring-offset-2',
    'dark:bg-primary-400 dark:text-primary-950 dark:hover:bg-primary-300',
    'dark:focus-visible:ring-primary-500 dark:focus-visible:ring-offset-gray-900',
  ].join(' '),
  secondary: [
    'bg-white text-gray-700 border border-gray-300',
    'hover:bg-gray-50 active:bg-gray-100',
    'focus-visible:ring-2 focus-visible:ring-primary-300 focus-visible:ring-offset-2',
    'dark:bg-gray-800 dark:text-gray-200 dark:border-gray-600',
    'dark:hover:bg-gray-700 dark:active:bg-gray-600',
    'dark:focus-visible:ring-primary-500 dark:focus-visible:ring-offset-gray-900',
  ].join(' '),
  ghost: [
    'bg-transparent text-gray-600',
    'hover:bg-gray-100 active:bg-gray-200',
    'focus-visible:ring-2 focus-visible:ring-gray-300 focus-visible:ring-offset-2',
    'dark:text-gray-300 dark:hover:bg-gray-800 dark:active:bg-gray-700',
    'dark:focus-visible:ring-gray-500 dark:focus-visible:ring-offset-gray-900',
  ].join(' '),
  danger: [
    'bg-red-500 text-white',
    'hover:bg-red-600 active:bg-red-700',
    'focus-visible:ring-2 focus-visible:ring-red-300 focus-visible:ring-offset-2',
    'dark:bg-red-600 dark:hover:bg-red-500',
    'dark:focus-visible:ring-red-400 dark:focus-visible:ring-offset-gray-900',
  ].join(' '),
}

// Size classes
const sizeClasses = {
  sm: 'px-3 py-1.5 text-sm gap-1.5 rounded-md',
  md: 'px-4 py-2 text-sm gap-2 rounded-lg',
  lg: 'px-6 py-3 text-base gap-2.5 rounded-lg',
}

// Icon size classes
const iconSizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-4.5 h-4.5',
  lg: 'w-5 h-5',
}

const buttonClasses = computed(() => [
  // Base
  'inline-flex items-center justify-center font-medium',
  'transition-all duration-200 ease-out',
  'select-none outline-none',
  // Variant
  variantClasses[props.variant],
  // Size
  sizeClasses[props.size],
  // Block
  props.block ? 'w-full' : '',
  // Disabled/loading
  isDisabled.value
    ? 'opacity-50 cursor-not-allowed pointer-events-none'
    : 'cursor-pointer',
])

function handleClick(e) {
  if (isDisabled.value) {
    e.preventDefault()
    return
  }
  emit('click', e)
}
</script>

<template>
  <component
    :is="componentTag"
    v-bind="linkAttrs"
    :class="buttonClasses"
    :disabled="isDisabled && componentTag === 'button'"
    :aria-disabled="isDisabled"
    :aria-busy="loading"
    @click="handleClick"
    data-testid="t-button"
  >
    <!-- Loading spinner -->
    <svg
      v-if="loading"
      :class="['animate-spin shrink-0', iconSizeClasses[size]]"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        class="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="4"
      />
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>

    <!-- Icon left slot -->
    <span
      v-if="$slots['icon-left'] && !loading"
      :class="['shrink-0', iconSizeClasses[size]]"
    >
      <slot name="icon-left" />
    </span>

    <!-- Default slot (label) -->
    <span v-if="$slots.default" :class="{ 'opacity-0': loading && !$slots['icon-left'] && !$slots['icon-right'] }">
      <slot />
    </span>

    <!-- Icon right slot -->
    <span
      v-if="$slots['icon-right']"
      :class="['shrink-0', iconSizeClasses[size]]"
    >
      <slot name="icon-right" />
    </span>
  </component>
</template>
