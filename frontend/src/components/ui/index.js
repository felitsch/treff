/**
 * TREFF Design System — UI Component Library
 *
 * Barrel export for all base UI components.
 * Import with: import { TButton, TBadge, ... } from '@/components/ui'
 *
 * Components:
 *   TButton              — Multi-variant button (primary/secondary/ghost/danger)
 *   TBadge               — Status badges (draft/scheduled/exported/posted/error)
 *   TInput               — Form input with label, error, helper text, v-model
 *   TModal               — Dialog modal with backdrop, sizes, focus trap
 *   TEmptyState          — Placeholder for empty content areas
 *   TCountryAccent       — Decorative country-specific color accents
 *   TCountryThemeProvider — Country theme context provider (provide/inject)
 *
 * @see BaseCard.vue (in components/common/) for card-level component
 */

export { default as TButton } from './TButton.vue'
export { default as TBadge } from './TBadge.vue'
export { default as TInput } from './TInput.vue'
export { default as TModal } from './TModal.vue'
export { default as TEmptyState } from './TEmptyState.vue'
export { default as TCountryAccent } from './TCountryAccent.vue'
export { default as TCountryThemeProvider } from './TCountryThemeProvider.vue'
