/**
 * useCountryTheme — Country-specific theme composable for TREFF Sprachreisen.
 *
 * Provides reactive color tokens, CSS classes, and CSS custom properties
 * for each destination country. Used by TCountryThemeProvider.vue to
 * inject theme context into child components, or standalone for one-off
 * country-themed UI sections.
 *
 * Supported countries: 'usa' | 'canada' | 'australia' | 'newzealand' | 'ireland'
 *
 * Usage:
 *   import { useCountryTheme } from '@/composables/useCountryTheme'
 *   const { theme, cssVars, gradientStyle } = useCountryTheme('usa')
 *
 * @see @/components/common/TCountryThemeProvider.vue
 * @see @/config/designTokens.js
 */
import { computed, ref, unref, watch } from 'vue'

// ═══════════════════════════════════════════════════════════════════
// COUNTRY THEME DEFINITIONS
// ═══════════════════════════════════════════════════════════════════

const COUNTRY_THEMES = {
  usa: {
    key: 'usa',
    label: 'USA',
    emoji: '🇺🇸',
    primaryColor: '#B22234',
    secondaryColor: '#002147',
    accentColor: '#6B9BD2',
    lightBg: '#FFF5F6',
    darkBg: '#1A0A0D',
    // Tailwind class mappings
    gradientClass: 'bg-gradient-usa',
    borderClass: 'border-treff-usa-red',
    bgClass: 'bg-treff-usa-red/10',
    textClass: 'text-treff-usa-red',
    // Full palette
    palette: {
      red: '#B22234',
      navy: '#002147',
      white: '#FFFFFF',
      sky: '#6B9BD2',
      gold: '#FFD700',
    },
    gradient: 'linear-gradient(135deg, #B22234 0%, #002147 50%, #6B9BD2 100%)',
    gradientDark: 'linear-gradient(135deg, #8B1A29 0%, #001733 50%, #4A7AAF 100%)',
    gradientSubtle: 'linear-gradient(135deg, rgba(178,34,52,0.08) 0%, rgba(0,33,71,0.08) 100%)',
    gradientSubtleDark: 'linear-gradient(135deg, rgba(178,34,52,0.15) 0%, rgba(0,33,71,0.15) 100%)',
  },

  canada: {
    key: 'canada',
    label: 'Kanada',
    emoji: '🇨🇦',
    primaryColor: '#FF0000',
    secondaryColor: '#FFFFFF',
    accentColor: '#C41E3A',
    lightBg: '#FFF5F5',
    darkBg: '#1A0808',
    gradientClass: 'bg-gradient-canada',
    borderClass: 'border-treff-canada-red',
    bgClass: 'bg-treff-canada-red/10',
    textClass: 'text-treff-canada-red',
    palette: {
      red: '#FF0000',
      white: '#FFFFFF',
      maple: '#C41E3A',
      cream: '#FFF5E1',
      forest: '#2E5A36',
    },
    gradient: 'linear-gradient(135deg, #FF0000 0%, #C41E3A 50%, #FFF5E1 100%)',
    gradientDark: 'linear-gradient(135deg, #CC0000 0%, #9B1830 50%, #D4C4A8 100%)',
    gradientSubtle: 'linear-gradient(135deg, rgba(255,0,0,0.08) 0%, rgba(196,30,58,0.08) 100%)',
    gradientSubtleDark: 'linear-gradient(135deg, rgba(255,0,0,0.15) 0%, rgba(196,30,58,0.15) 100%)',
  },

  australia: {
    key: 'australia',
    label: 'Australien',
    emoji: '🇦🇺',
    primaryColor: '#CC7722',
    secondaryColor: '#006994',
    accentColor: '#8B4513',
    lightBg: '#FFFBF5',
    darkBg: '#1A1208',
    gradientClass: 'bg-gradient-australia',
    borderClass: 'border-treff-australia-ochre',
    bgClass: 'bg-treff-australia-ochre/10',
    textClass: 'text-treff-australia-ochre',
    palette: {
      earth: '#8B4513',
      ochre: '#CC7722',
      ocean: '#006994',
      sand: '#F4D8A5',
      sky: '#87CEEB',
    },
    gradient: 'linear-gradient(135deg, #8B4513 0%, #CC7722 50%, #006994 100%)',
    gradientDark: 'linear-gradient(135deg, #6B3410 0%, #A66019 50%, #005070 100%)',
    gradientSubtle: 'linear-gradient(135deg, rgba(139,69,19,0.08) 0%, rgba(0,105,148,0.08) 100%)',
    gradientSubtleDark: 'linear-gradient(135deg, rgba(139,69,19,0.15) 0%, rgba(0,105,148,0.15) 100%)',
  },

  newzealand: {
    key: 'newzealand',
    label: 'Neuseeland',
    emoji: '🇳🇿',
    primaryColor: '#1B4D3E',
    secondaryColor: '#4CAF50',
    accentColor: '#5CB8E6',
    lightBg: '#F5FFF8',
    darkBg: '#081A12',
    gradientClass: 'bg-gradient-nz',
    borderClass: 'border-treff-nz-forest',
    bgClass: 'bg-treff-nz-forest/10',
    textClass: 'text-treff-nz-forest',
    palette: {
      forest: '#1B4D3E',
      fern: '#4CAF50',
      sky: '#5CB8E6',
      cream: '#FAF3E0',
      earth: '#8B6F47',
    },
    gradient: 'linear-gradient(135deg, #1B4D3E 0%, #4CAF50 50%, #5CB8E6 100%)',
    gradientDark: 'linear-gradient(135deg, #143D30 0%, #3D8B40 50%, #4A9BC2 100%)',
    gradientSubtle: 'linear-gradient(135deg, rgba(27,77,62,0.08) 0%, rgba(92,184,230,0.08) 100%)',
    gradientSubtleDark: 'linear-gradient(135deg, rgba(27,77,62,0.15) 0%, rgba(92,184,230,0.15) 100%)',
  },

  ireland: {
    key: 'ireland',
    label: 'Irland',
    emoji: '🇮🇪',
    primaryColor: '#169B62',
    secondaryColor: '#FF8C00',
    accentColor: '#A9A9A9',
    lightBg: '#F5FFF5',
    darkBg: '#081A08',
    gradientClass: 'bg-gradient-ireland',
    borderClass: 'border-treff-ireland-green',
    bgClass: 'bg-treff-ireland-green/10',
    textClass: 'text-treff-ireland-green',
    palette: {
      green: '#169B62',
      gold: '#FF8C00',
      stone: '#A9A9A9',
      white: '#FFFFFF',
      moss: '#3D5A3E',
    },
    gradient: 'linear-gradient(135deg, #169B62 0%, #FF8C00 50%, #FFFFFF 100%)',
    gradientDark: 'linear-gradient(135deg, #127A4E 0%, #CC7000 50%, #D4D4D4 100%)',
    gradientSubtle: 'linear-gradient(135deg, rgba(22,155,98,0.08) 0%, rgba(255,140,0,0.08) 100%)',
    gradientSubtleDark: 'linear-gradient(135deg, rgba(22,155,98,0.15) 0%, rgba(255,140,0,0.15) 100%)',
  },
}

// Alias mappings for flexible country key inputs
const COUNTRY_ALIASES = {
  usa: 'usa',
  'united states': 'usa',
  us: 'usa',
  america: 'usa',
  canada: 'canada',
  kanada: 'canada',
  ca: 'canada',
  australia: 'australia',
  australien: 'australia',
  au: 'australia',
  newzealand: 'newzealand',
  'new zealand': 'newzealand',
  neuseeland: 'newzealand',
  nz: 'newzealand',
  ireland: 'ireland',
  irland: 'ireland',
  ie: 'ireland',
}

// Default fallback theme (TREFF brand colors)
const DEFAULT_THEME = {
  key: 'default',
  label: 'TREFF',
  emoji: '🌍',
  primaryColor: '#3B7AB1',
  secondaryColor: '#FDD000',
  accentColor: '#5F9FD6',
  lightBg: '#F5F5F5',
  darkBg: '#1A1A2E',
  gradientClass: 'bg-gradient-to-br from-primary-500 to-secondary-500',
  borderClass: 'border-primary-500',
  bgClass: 'bg-primary-500/10',
  textClass: 'text-primary-500',
  palette: {
    primary: '#3B7AB1',
    secondary: '#FDD000',
    accent: '#5F9FD6',
  },
  gradient: 'linear-gradient(135deg, #3B7AB1 0%, #FDD000 100%)',
  gradientDark: 'linear-gradient(135deg, #2F628E 0%, #CAA600 100%)',
  gradientSubtle: 'linear-gradient(135deg, rgba(59,122,177,0.08) 0%, rgba(253,208,0,0.08) 100%)',
  gradientSubtleDark: 'linear-gradient(135deg, rgba(59,122,177,0.15) 0%, rgba(253,208,0,0.15) 100%)',
}

/**
 * Resolve a country input string to a normalized key.
 * @param {string} country
 * @returns {string|null}
 */
export function resolveCountryKey(country) {
  if (!country) return null
  const normalized = String(country).toLowerCase().trim()
  return COUNTRY_ALIASES[normalized] || null
}

/**
 * Get all available country theme keys.
 * @returns {string[]}
 */
export function getCountryKeys() {
  return Object.keys(COUNTRY_THEMES)
}

/**
 * Get the raw theme object for a country (non-reactive).
 * @param {string} country
 * @returns {object}
 */
export function getCountryTheme(country) {
  const key = resolveCountryKey(country)
  return key ? COUNTRY_THEMES[key] : DEFAULT_THEME
}

// ═══════════════════════════════════════════════════════════════════
// COMPOSABLE
// ═══════════════════════════════════════════════════════════════════

/**
 * useCountryTheme — Reactive composable for country-specific theming.
 *
 * @param {import('vue').Ref<string>|string} countryInput — Country name/key (reactive or static)
 * @returns {object} Reactive theme tokens and CSS helpers
 */
export function useCountryTheme(countryInput) {
  // Support both ref and plain string
  const countryRef = typeof countryInput === 'string'
    ? ref(countryInput)
    : countryInput

  /** Resolved country key (e.g. 'usa', 'canada') */
  const countryKey = computed(() => resolveCountryKey(unref(countryRef)))

  /** Full theme object */
  const theme = computed(() => {
    const key = countryKey.value
    return key ? COUNTRY_THEMES[key] : DEFAULT_THEME
  })

  // ── Convenience reactive properties ──

  const primaryColor = computed(() => theme.value.primaryColor)
  const secondaryColor = computed(() => theme.value.secondaryColor)
  const accentColor = computed(() => theme.value.accentColor)

  const gradientClass = computed(() => theme.value.gradientClass)
  const borderClass = computed(() => theme.value.borderClass)
  const bgClass = computed(() => theme.value.bgClass)
  const textClass = computed(() => theme.value.textClass)

  const label = computed(() => theme.value.label)
  const emoji = computed(() => theme.value.emoji)
  const palette = computed(() => theme.value.palette)

  /** Gradient CSS value (for inline styles) */
  const gradientStyle = computed(() => ({
    background: theme.value.gradient,
  }))

  /** Dark-mode gradient CSS value */
  const gradientDarkStyle = computed(() => ({
    background: theme.value.gradientDark,
  }))

  /** Subtle gradient for backgrounds */
  const gradientSubtleStyle = computed(() => ({
    background: theme.value.gradientSubtle,
  }))

  /**
   * CSS custom properties object for use with :style binding.
   * Sets --country-primary, --country-secondary, --country-accent, --country-gradient.
   */
  const cssVars = computed(() => {
    const t = theme.value
    return {
      '--country-primary': t.primaryColor,
      '--country-secondary': t.secondaryColor,
      '--country-accent': t.accentColor,
      '--country-gradient': t.gradient,
      '--country-gradient-dark': t.gradientDark,
      '--country-gradient-subtle': t.gradientSubtle,
      '--country-gradient-subtle-dark': t.gradientSubtleDark,
      '--country-light-bg': t.lightBg,
      '--country-dark-bg': t.darkBg,
    }
  })

  /** Whether a valid country theme is active (not default fallback) */
  const isCountryTheme = computed(() => countryKey.value !== null)

  /**
   * Set a new country dynamically.
   * @param {string} newCountry
   */
  function setCountry(newCountry) {
    countryRef.value = newCountry
  }

  return {
    // Core
    countryKey,
    theme,
    isCountryTheme,
    setCountry,

    // Color tokens
    primaryColor,
    secondaryColor,
    accentColor,
    palette,

    // CSS classes (Tailwind)
    gradientClass,
    borderClass,
    bgClass,
    textClass,

    // Inline style objects
    gradientStyle,
    gradientDarkStyle,
    gradientSubtleStyle,
    cssVars,

    // Display
    label,
    emoji,
  }
}

// Export constants for external use
export { COUNTRY_THEMES, DEFAULT_THEME, COUNTRY_ALIASES }
