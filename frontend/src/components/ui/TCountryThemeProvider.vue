<script setup>
/**
 * TCountryThemeProvider — Provides country-specific theme context to children.
 *
 * Uses Vue's provide/inject pattern to propagate country theme tokens
 * down the component tree. Children can inject the theme with:
 *
 *   import { inject } from 'vue'
 *   const countryTheme = inject('countryTheme')
 *
 * Also sets CSS custom properties on the wrapper element so any
 * descendant can use var(--country-primary), var(--country-secondary), etc.
 *
 * Props:
 *   - country: string — Country key ('usa', 'canada', 'australia', 'newzealand', 'ireland')
 *   - tag: string — HTML wrapper element tag (default: 'div')
 *   - subtle: boolean — Use subtle gradient background (default: false)
 *
 * @see @/composables/useCountryTheme.js
 */
import { provide, toRef, computed, useSlots } from 'vue'
import { useCountryTheme } from '@/composables/useCountryTheme'

const props = defineProps({
  country: {
    type: String,
    default: '',
  },
  tag: {
    type: String,
    default: 'div',
  },
  subtle: {
    type: Boolean,
    default: false,
  },
})

const countryRef = toRef(props, 'country')
const themeData = useCountryTheme(countryRef)

// Provide theme to all descendants
provide('countryTheme', themeData)

// Computed style that includes CSS custom properties + optional subtle bg
const wrapperStyle = computed(() => {
  const vars = { ...themeData.cssVars.value }

  if (props.subtle && themeData.isCountryTheme.value) {
    vars.background = themeData.theme.value.gradientSubtle
  }

  return vars
})

// Computed class for the wrapper
const wrapperClass = computed(() => {
  if (!themeData.isCountryTheme.value) return ''
  return `country-theme country-theme--${themeData.countryKey.value}`
})
</script>

<template>
  <component
    :is="tag"
    :style="wrapperStyle"
    :class="wrapperClass"
    :data-country="themeData.countryKey.value || 'default'"
  >
    <slot
      :theme="themeData.theme.value"
      :country-key="themeData.countryKey.value"
      :primary-color="themeData.primaryColor.value"
      :secondary-color="themeData.secondaryColor.value"
      :accent-color="themeData.accentColor.value"
      :gradient-class="themeData.gradientClass.value"
      :border-class="themeData.borderClass.value"
      :bg-class="themeData.bgClass.value"
      :text-class="themeData.textClass.value"
      :label="themeData.label.value"
      :emoji="themeData.emoji.value"
      :palette="themeData.palette.value"
      :is-country-theme="themeData.isCountryTheme.value"
      :css-vars="themeData.cssVars.value"
      :gradient-style="themeData.gradientStyle.value"
    />
  </component>
</template>

<style scoped>
/* Transition for smooth theme switches */
.country-theme {
  transition: background 300ms ease, border-color 300ms ease, color 300ms ease;
}
</style>
