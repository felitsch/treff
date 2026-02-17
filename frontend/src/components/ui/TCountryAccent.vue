<script setup>
/**
 * TCountryAccent.vue — TREFF Design System Country Accent Decorator.
 *
 * Renders a decorative color accent (border, gradient stripe, or subtle bg)
 * based on a destination country. Used to add country-specific visual flair
 * to cards, sections, and list items without wrapping the entire tree in
 * a theme provider.
 *
 * Props:
 *   country  (String)  — Country key: 'usa' | 'canada' | 'australia' | 'newzealand' | 'ireland'
 *   mode     (String)  — Accent style: 'border-left' | 'border-top' | 'gradient-bar' | 'bg' (default: 'border-left')
 *   size     (String)  — Accent thickness: 'sm' | 'md' | 'lg' (default: 'md')
 *   tag      (String)  — Wrapper HTML element (default: 'div')
 *   rounded  (Boolean) — Apply rounded corners to accent (default: false)
 *
 * Slots:
 *   default — Content to be decorated
 *
 * @see useCountryTheme.js — Uses the same country palette system
 */
import { computed } from 'vue'
import { useCountryTheme, getCountryTheme } from '@/composables/useCountryTheme'

const props = defineProps({
  country: {
    type: String,
    default: '',
  },
  mode: {
    type: String,
    default: 'border-left',
    validator: (v) => ['border-left', 'border-top', 'gradient-bar', 'bg'].includes(v),
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v),
  },
  tag: {
    type: String,
    default: 'div',
  },
  rounded: {
    type: Boolean,
    default: false,
  },
})

// Get theme data for the country
const themeData = computed(() => getCountryTheme(props.country))

// Size mapping for border width
const borderSizes = {
  sm: '2px',
  md: '3px',
  lg: '4px',
}

// Size mapping for gradient bar height/width
const barSizes = {
  sm: '3px',
  md: '4px',
  lg: '6px',
}

// Computed inline styles based on mode
const accentStyle = computed(() => {
  const theme = themeData.value
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.secondaryColor || theme.accentColor})`

  switch (props.mode) {
    case 'border-left':
      return {
        borderLeftWidth: borderSizes[props.size],
        borderLeftStyle: 'solid',
        borderLeftColor: theme.primaryColor,
      }

    case 'border-top':
      return {
        borderTopWidth: borderSizes[props.size],
        borderTopStyle: 'solid',
        borderTopColor: theme.primaryColor,
      }

    case 'gradient-bar':
      // Gradient bar is rendered as a pseudo-element via the bar slot
      return {}

    case 'bg':
      return {
        backgroundColor: `${theme.primaryColor}08`,
      }

    default:
      return {}
  }
})

// Gradient bar style (for gradient-bar mode)
const gradientBarStyle = computed(() => {
  const theme = themeData.value
  const size = barSizes[props.size]
  const gradient = `linear-gradient(90deg, ${theme.primaryColor}, ${theme.secondaryColor || theme.accentColor})`

  return {
    height: size,
    background: gradient,
    borderRadius: props.rounded ? '9999px' : '0',
  }
})

// Dark mode background style (for 'bg' mode)
const bgDarkStyle = computed(() => {
  const theme = themeData.value
  return {
    '--accent-bg-light': `${theme.primaryColor}08`,
    '--accent-bg-dark': `${theme.primaryColor}15`,
  }
})

const wrapperClasses = computed(() => [
  'relative',
  props.mode === 'bg' ? 'country-accent-bg' : '',
  props.rounded && (props.mode === 'border-left' || props.mode === 'border-top')
    ? 'rounded-lg overflow-hidden'
    : '',
])
</script>

<template>
  <component
    :is="tag"
    :class="wrapperClasses"
    :style="[accentStyle, mode === 'bg' ? bgDarkStyle : {}]"
    :data-country="country || 'default'"
    data-testid="t-country-accent"
  >
    <!-- Gradient bar (rendered above content for gradient-bar mode) -->
    <div
      v-if="mode === 'gradient-bar'"
      :style="gradientBarStyle"
      class="w-full shrink-0"
      aria-hidden="true"
    />

    <slot
      :primary-color="themeData.primaryColor"
      :secondary-color="themeData.secondaryColor"
      :accent-color="themeData.accentColor"
      :label="themeData.label"
      :emoji="themeData.emoji"
    />
  </component>
</template>

<style scoped>
.country-accent-bg {
  background-color: var(--accent-bg-light);
}

:root.dark .country-accent-bg,
.dark .country-accent-bg {
  background-color: var(--accent-bg-dark);
}
</style>
