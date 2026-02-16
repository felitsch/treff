/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // === TREFF Brand Colors ===
        // Primary: TREFF Blue — Trust, Education, Reliability
        primary: {
          50:  '#EBF3FA',
          100: '#D7E7F5',
          200: '#AFCFEB',
          300: '#87B7E0',
          400: '#5F9FD6',
          500: '#3B7AB1', // Main brand blue
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
          500: '#FDD000', // Main brand yellow
          600: '#CAA600',
          700: '#987D00',
          800: '#655300',
          900: '#332A00',
          950: '#1A1500',
          DEFAULT: '#FDD000',
        },
        // === Extended Brand Scale (explicit treff-blue / treff-yellow) ===
        'treff-blue': {
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
        'treff-yellow': {
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

        // === Country Palettes ===
        // USA — Red, White & Blue patriotic theme
        'treff-usa': {
          red:    '#B22234',
          navy:   '#002147',
          white:  '#FFFFFF',
          sky:    '#6B9BD2',
          gold:   '#FFD700',
          DEFAULT: '#B22234',
        },
        // Canada — Red, White, Maple
        'treff-canada': {
          red:    '#FF0000',
          white:  '#FFFFFF',
          maple:  '#C41E3A',
          cream:  '#FFF5E1',
          forest: '#2E5A36',
          DEFAULT: '#FF0000',
        },
        // Australia — Earth, Ochre, Ocean
        'treff-australia': {
          earth:  '#8B4513',
          ochre:  '#CC7722',
          ocean:  '#006994',
          sand:   '#F4D8A5',
          sky:    '#87CEEB',
          DEFAULT: '#CC7722',
        },
        // New Zealand — Forest, Fern, Sky
        'treff-nz': {
          forest: '#1B4D3E',
          fern:   '#4CAF50',
          sky:    '#5CB8E6',
          cream:  '#FAF3E0',
          earth:  '#8B6F47',
          DEFAULT: '#1B4D3E',
        },
        // Ireland — Green, Gold, Stone
        'treff-ireland': {
          green:  '#169B62',
          gold:   '#FF8C00',
          stone:  '#A9A9A9',
          white:  '#FFFFFF',
          moss:   '#3D5A3E',
          DEFAULT: '#169B62',
        },

        // Legacy aliases (backward compat)
        'treff-dark':   '#1A1A2E',
        'treff-light':  '#F5F5F5',
      },

      // === Font Family ===
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },

      // === Typography Scale (with explicit line-heights) ===
      fontSize: {
        'xs':   ['0.75rem',   { lineHeight: '1rem' }],      // 12px / 16px
        'sm':   ['0.875rem',  { lineHeight: '1.25rem' }],    // 14px / 20px
        'base': ['1rem',      { lineHeight: '1.5rem' }],     // 16px / 24px
        'lg':   ['1.125rem',  { lineHeight: '1.75rem' }],    // 18px / 28px
        'xl':   ['1.25rem',   { lineHeight: '1.75rem' }],    // 20px / 28px
        '2xl':  ['1.5rem',    { lineHeight: '2rem' }],       // 24px / 32px
        '3xl':  ['1.875rem',  { lineHeight: '2.25rem' }],    // 30px / 36px
        '4xl':  ['2.25rem',   { lineHeight: '2.5rem' }],     // 36px / 40px
      },

      // === Spacing Scale (augments default Tailwind 4px grid) ===
      spacing: {
        '4.5': '1.125rem',   // 18px
        '13':  '3.25rem',    // 52px
        '15':  '3.75rem',    // 60px
        '18':  '4.5rem',     // 72px
        '22':  '5.5rem',     // 88px
        '26':  '6.5rem',     // 104px
        '30':  '7.5rem',     // 120px
        '34':  '8.5rem',     // 136px
        '128': '32rem',      // 512px
        '144': '36rem',      // 576px
      },

      // === Border Radius — 3-tier system ===
      borderRadius: {
        'sm':  '0.25rem',   //  4px — subtle (tags, badges)
        'md':  '0.5rem',    //  8px — default (inputs, small cards)
        'lg':  '0.75rem',   // 12px — medium (cards, dialogs)
        'xl':  '1rem',      // 16px — large (panels, modals)
        '2xl': '1.25rem',   // 20px — hero cards, featured content
        '3xl': '1.5rem',    // 24px — splash/promo sections
      },

      // === Box Shadow — 4-tier elevation system ===
      boxShadow: {
        'sm':    '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'DEFAULT': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'md':    '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        'lg':    '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        'xl':    '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
        '2xl':   '0 25px 50px -12px rgb(0 0 0 / 0.25)',
        'card':  '0 1px 3px rgb(0 0 0 / 0.08), 0 1px 2px rgb(0 0 0 / 0.06)',
        'card-hover': '0 4px 12px rgb(0 0 0 / 0.1), 0 2px 4px rgb(0 0 0 / 0.06)',
        'dialog': '0 12px 28px rgb(0 0 0 / 0.12), 0 8px 10px rgb(0 0 0 / 0.08)',
        // === 3-Level Shadow System ===
        'modal': '0 12px 28px rgb(0 0 0 / 0.12), 0 8px 10px rgb(0 0 0 / 0.08)',
        'popup': '0 20px 40px rgb(0 0 0 / 0.18), 0 12px 16px rgb(0 0 0 / 0.1)',
        'inner': 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
        'none':  'none',
      },

      // === Transitions ===
      transitionDuration: {
        '150': '150ms',
        '200': '200ms',
        '250': '250ms',
        '300': '300ms',
      },

      // === Z-Index Scale ===
      zIndex: {
        'dropdown': '50',
        'sticky':   '60',
        'overlay':  '70',
        'modal':    '80',
        'toast':    '90',
        'tooltip':  '100',
      },

      // === Max Width for content areas ===
      maxWidth: {
        'content': '72rem',    // 1152px — main content max
        'narrow':  '48rem',    // 768px  — forms, modals
      },

      // === Animation keyframes ===
      keyframes: {
        'fade-in': {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-down': {
          '0%':   { opacity: '0', transform: 'translateY(-8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'scale-in': {
          '0%':   { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'slide-right': {
          '0%':   { opacity: '0', transform: 'translateX(-12px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
      },
      animation: {
        'fade-in':     'fade-in 200ms ease-out',
        'slide-up':    'slide-up 250ms ease-out',
        'slide-down':  'slide-down 250ms ease-out',
        'scale-in':    'scale-in 200ms ease-out',
        'slide-right': 'slide-right 250ms ease-out',
      },
    },
  },
  plugins: [],
}
