/**
 * TREFF Design Tokens — JavaScript Export
 *
 * All design tokens from tailwind.config.js and main.css exported
 * as JS objects for programmatic access (template rendering,
 * dynamic styles, chart colors, email templates, etc.).
 *
 * Usage:
 *   import { colors, countryPalettes, gradients, shadows, typography, animations } from '@/config/designTokens'
 *   const usaRed = countryPalettes.usa.red  // '#B22234'
 */

// ═══════════════════════════════════════════════════════════════════
// COLORS
// ═══════════════════════════════════════════════════════════════════

export const colors = {
  // Primary: TREFF Blue — Trust, Education, Reliability
  primary: {
    50:  '#EBF3FA',
    100: '#D7E7F5',
    200: '#AFCFEB',
    300: '#87B7E0',
    400: '#5F9FD6',
    500: '#3B7AB1',
    600: '#2F628E',
    700: '#244A6A',
    800: '#193247',
    900: '#0E1A23',
    950: '#070D12',
    DEFAULT: '#3B7AB1',
  },

  // Secondary: TREFF Yellow — Energy, Adventure, Youth
  secondary: {
    50:  '#FFFBE6',
    100: '#FFF7CC',
    200: '#FFEF99',
    300: '#FFE766',
    400: '#FFDF33',
    500: '#FDD000',
    600: '#CAA600',
    700: '#987D00',
    800: '#655300',
    900: '#332A00',
    950: '#1A1500',
    DEFAULT: '#FDD000',
  },

  // Extended brand scale (explicit names)
  treffBlue: {
    50:  '#EBF3FA',
    100: '#D7E7F5',
    200: '#AFCFEB',
    300: '#87B7E0',
    400: '#5F9FD6',
    500: '#3B7AB1',
    600: '#2F628E',
    700: '#244A6A',
    800: '#193247',
    900: '#0E1A23',
    DEFAULT: '#3B7AB1',
  },

  treffYellow: {
    50:  '#FFFBE6',
    100: '#FFF7CC',
    200: '#FFEF99',
    300: '#FFE766',
    400: '#FFDF33',
    500: '#FDD000',
    600: '#CAA600',
    700: '#987D00',
    800: '#655300',
    900: '#332A00',
    DEFAULT: '#FDD000',
  },

  // Neutral
  treffDark:  '#1A1A2E',
  treffLight: '#F5F5F5',
}

// ═══════════════════════════════════════════════════════════════════
// COUNTRY PALETTES
// ═══════════════════════════════════════════════════════════════════

export const countryPalettes = {
  usa: {
    red:    '#B22234',
    navy:   '#002147',
    white:  '#FFFFFF',
    sky:    '#6B9BD2',
    gold:   '#FFD700',
    DEFAULT: '#B22234',
  },
  canada: {
    red:    '#FF0000',
    white:  '#FFFFFF',
    maple:  '#C41E3A',
    cream:  '#FFF5E1',
    forest: '#2E5A36',
    DEFAULT: '#FF0000',
  },
  australia: {
    earth:  '#8B4513',
    ochre:  '#CC7722',
    ocean:  '#006994',
    sand:   '#F4D8A5',
    sky:    '#87CEEB',
    DEFAULT: '#CC7722',
  },
  nz: {
    forest: '#1B4D3E',
    fern:   '#4CAF50',
    sky:    '#5CB8E6',
    cream:  '#FAF3E0',
    earth:  '#8B6F47',
    DEFAULT: '#1B4D3E',
  },
  ireland: {
    green:  '#169B62',
    gold:   '#FF8C00',
    stone:  '#A9A9A9',
    white:  '#FFFFFF',
    moss:   '#3D5A3E',
    DEFAULT: '#169B62',
  },
}

// ═══════════════════════════════════════════════════════════════════
// GRADIENTS
// ═══════════════════════════════════════════════════════════════════

export const gradients = {
  usa:       'linear-gradient(135deg, #B22234 0%, #002147 50%, #6B9BD2 100%)',
  canada:    'linear-gradient(135deg, #FF0000 0%, #C41E3A 50%, #FFF5E1 100%)',
  australia: 'linear-gradient(135deg, #8B4513 0%, #CC7722 50%, #006994 100%)',
  nz:        'linear-gradient(135deg, #1B4D3E 0%, #4CAF50 50%, #5CB8E6 100%)',
  ireland:   'linear-gradient(135deg, #169B62 0%, #FF8C00 50%, #FFFFFF 100%)',
  adventure: 'linear-gradient(135deg, #3B7AB1 0%, #FDD000 50%, #FF6B35 100%)',
}

export const gradientsDark = {
  usa:       'linear-gradient(135deg, #8B1A29 0%, #001733 50%, #4A7AAF 100%)',
  canada:    'linear-gradient(135deg, #CC0000 0%, #9B1830 50%, #D4C4A8 100%)',
  australia: 'linear-gradient(135deg, #6B3410 0%, #A66019 50%, #005070 100%)',
  nz:        'linear-gradient(135deg, #143D30 0%, #3D8B40 50%, #4A9BC2 100%)',
  ireland:   'linear-gradient(135deg, #127A4E 0%, #CC7000 50%, #D4D4D4 100%)',
  adventure: 'linear-gradient(135deg, #2F628E 0%, #CAA600 50%, #CC5529 100%)',
}

// ═══════════════════════════════════════════════════════════════════
// SHADOWS (3-Level System)
// ═══════════════════════════════════════════════════════════════════

export const shadows = {
  // Level 1 — Low elevation (cards, lists)
  card:      '0 1px 3px rgb(0 0 0 / 0.08), 0 1px 2px rgb(0 0 0 / 0.06)',
  cardHover: '0 4px 12px rgb(0 0 0 / 0.1), 0 2px 4px rgb(0 0 0 / 0.06)',

  // Level 2 — Medium elevation (modals, dialogs)
  modal:     '0 12px 28px rgb(0 0 0 / 0.12), 0 8px 10px rgb(0 0 0 / 0.08)',
  dialog:    '0 12px 28px rgb(0 0 0 / 0.12), 0 8px 10px rgb(0 0 0 / 0.08)',

  // Level 3 — High elevation (popups, tooltips, dropdowns)
  popup:     '0 20px 40px rgb(0 0 0 / 0.18), 0 12px 16px rgb(0 0 0 / 0.1)',
}

// ═══════════════════════════════════════════════════════════════════
// TYPOGRAPHY
// ═══════════════════════════════════════════════════════════════════

export const typography = {
  fontFamily: {
    sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
    mono: ['JetBrains Mono', 'monospace'],
  },

  // Named typography scale
  display: {
    fontSize: '1.5rem',     // 24px (2xl)
    fontWeight: '700',      // bold
    lineHeight: '1.25',     // tight
  },
  heading: {
    fontSize: '1.25rem',    // 20px (xl)
    fontWeight: '600',      // semibold
    lineHeight: '1.375',    // snug
  },
  body: {
    fontSize: '1rem',       // 16px (base)
    fontWeight: '400',      // normal
    lineHeight: '1.625',    // relaxed
  },
  caption: {
    fontSize: '0.875rem',   // 14px (sm)
    fontWeight: '400',      // normal
    lineHeight: '1.5',      // normal
  },

  // Full font-size scale
  scale: {
    xs:   { fontSize: '0.75rem',  lineHeight: '1rem' },
    sm:   { fontSize: '0.875rem', lineHeight: '1.25rem' },
    base: { fontSize: '1rem',     lineHeight: '1.5rem' },
    lg:   { fontSize: '1.125rem', lineHeight: '1.75rem' },
    xl:   { fontSize: '1.25rem',  lineHeight: '1.75rem' },
    '2xl': { fontSize: '1.5rem',  lineHeight: '2rem' },
    '3xl': { fontSize: '1.875rem', lineHeight: '2.25rem' },
    '4xl': { fontSize: '2.25rem', lineHeight: '2.5rem' },
  },
}

// ═══════════════════════════════════════════════════════════════════
// ANIMATIONS
// ═══════════════════════════════════════════════════════════════════

export const animations = {
  fadeIn: {
    name: 'fade-in',
    duration: '200ms',
    easing: 'ease-out',
    css: 'fade-in 200ms ease-out',
    keyframes: { from: { opacity: 0 }, to: { opacity: 1 } },
  },
  slideUp: {
    name: 'slide-up',
    duration: '250ms',
    easing: 'ease-out',
    css: 'slide-up 250ms ease-out',
    keyframes: { from: { opacity: 0, transform: 'translateY(8px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
  },
  slideDown: {
    name: 'slide-down',
    duration: '250ms',
    easing: 'ease-out',
    css: 'slide-down 250ms ease-out',
    keyframes: { from: { opacity: 0, transform: 'translateY(-8px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
  },
  slideRight: {
    name: 'slide-right',
    duration: '250ms',
    easing: 'ease-out',
    css: 'slide-right 250ms ease-out',
    keyframes: { from: { opacity: 0, transform: 'translateX(-12px)' }, to: { opacity: 1, transform: 'translateX(0)' } },
  },
  scaleIn: {
    name: 'scale-in',
    duration: '200ms',
    easing: 'ease-out',
    css: 'scale-in 200ms ease-out',
    keyframes: { from: { opacity: 0, transform: 'scale(0.95)' }, to: { opacity: 1, transform: 'scale(1)' } },
  },
}

// ═══════════════════════════════════════════════════════════════════
// SPACING
// ═══════════════════════════════════════════════════════════════════

export const spacing = {
  '0':   '0px',
  '0.5': '0.125rem',
  '1':   '0.25rem',
  '1.5': '0.375rem',
  '2':   '0.5rem',
  '2.5': '0.625rem',
  '3':   '0.75rem',
  '3.5': '0.875rem',
  '4':   '1rem',
  '4.5': '1.125rem',
  '5':   '1.25rem',
  '6':   '1.5rem',
  '7':   '1.75rem',
  '8':   '2rem',
  '9':   '2.25rem',
  '10':  '2.5rem',
  '11':  '2.75rem',
  '12':  '3rem',
  '13':  '3.25rem',
  '14':  '3.5rem',
  '15':  '3.75rem',
  '16':  '4rem',
  '18':  '4.5rem',
  '20':  '5rem',
  '22':  '5.5rem',
  '24':  '6rem',
  '26':  '6.5rem',
  '28':  '7rem',
  '30':  '7.5rem',
  '32':  '8rem',
  '34':  '8.5rem',
}

// ═══════════════════════════════════════════════════════════════════
// BORDER RADIUS
// ═══════════════════════════════════════════════════════════════════

export const borderRadius = {
  sm:   '0.25rem',
  md:   '0.5rem',
  lg:   '0.75rem',
  xl:   '1rem',
  '2xl': '1.25rem',
  '3xl': '1.5rem',
  full: '9999px',
}

// ═══════════════════════════════════════════════════════════════════
// Z-INDEX
// ═══════════════════════════════════════════════════════════════════

export const zIndex = {
  dropdown: 50,
  sticky:   60,
  overlay:  70,
  modal:    80,
  toast:    90,
  tooltip:  100,
}

// ═══════════════════════════════════════════════════════════════════
// DEFAULT EXPORT — all tokens as single object
// ═══════════════════════════════════════════════════════════════════

const designTokens = {
  colors,
  countryPalettes,
  gradients,
  gradientsDark,
  shadows,
  typography,
  animations,
  spacing,
  borderRadius,
  zIndex,
}

export default designTokens
