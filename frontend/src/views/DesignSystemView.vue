<script setup>
import { ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import PostPreviewCard from '@/components/posts/PostPreviewCard.vue'
import PostPreviewCardTikTok from '@/components/posts/PostPreviewCardTikTok.vue'
import PostPreviewGrid from '@/components/posts/PostPreviewGrid.vue'
import TCountryThemeProvider from '@/components/ui/TCountryThemeProvider.vue'
import { useCountryTheme, getCountryKeys, COUNTRY_THEMES } from '@/composables/useCountryTheme'
import AppIcon from '@/components/icons/AppIcon.vue'

const activeSection = ref('colors')

const sections = [
  { id: 'colors', label: 'Farben', icon: 'paint-brush' },
  { id: 'country-themes', label: 'Country Themes', icon: 'globe-alt' },
  { id: 'typography', label: 'Typografie', icon: 'document-text' },
  { id: 'buttons', label: 'Buttons', icon: 'cursor-arrow-rays' },
  { id: 'cards', label: 'Cards', icon: 'archive-box' },
  { id: 'inputs', label: 'Inputs', icon: 'clipboard-document-list' },
  { id: 'badges', label: 'Badges', icon: 'tag' },
  { id: 'shadows', label: 'Shadows', icon: 'moon' },
  { id: 'spacing', label: 'Spacing', icon: 'arrows-pointing-out' },
  { id: 'radius', label: 'Radius', icon: 'square-2-stack' },
  { id: 'previews', label: 'Post Previews', icon: 'device-phone-mobile' },
]

// Country theme demo state
const selectedCountry = ref('usa')
const countryTheme = useCountryTheme(selectedCountry)
const allCountryKeys = getCountryKeys()

// ── Demo post data for Post Preview Cards ──
const demoPostInstagram = ref({
  id: 1,
  title: 'Dein Highschool-Jahr in den USA',
  caption_instagram: 'Erlebe das Abenteuer deines Lebens! Ein Schuljahr an einer amerikanischen High School mit TREFF Sprachreisen.',
  hashtags_instagram: '#highschool #usa #austausch #treff #sprachreisen',
  platform: 'instagram_feed',
  country: 'usa',
  status: 'scheduled',
  slide_data: JSON.stringify([
    { headline: 'USA Highschool', subheadline: 'Dein Abenteuer wartet', body_text: 'Erlebe den American Dream hautnah' },
    { headline: 'Slide 2', subheadline: 'Neue Freunde', body_text: 'Finde Freunde für ein ganzes Leben' },
  ]),
})

const demoPostTikTok = ref({
  id: 2,
  title: 'Kanada Erfahrung - TREFF',
  caption_tiktok: 'So sieht ein Tag an einer kanadischen High School aus!',
  hashtags_tiktok: '#kanada #highschool #exchange #fyp',
  platform: 'tiktok',
  country: 'kanada',
  status: 'draft',
  slide_data: '[]',
})

const demoPostAustralia = ref({
  id: 3,
  title: 'Down Under erleben',
  caption_instagram: 'Australien: Surfen, Kanguruhs und die beste Zeit deines Lebens.',
  hashtags_instagram: '#australien #downunder #exchange',
  platform: 'instagram_feed',
  country: 'australien',
  status: 'posted',
  slide_data: '[]',
})

const demoPostNZ = ref({
  id: 4,
  title: 'Neuseeland Abenteuer',
  caption_tiktok: 'Neuseeland hat mein Leben verändert!',
  hashtags_tiktok: '#neuseeland #nz #exchange',
  platform: 'tiktok',
  country: 'neuseeland',
  status: 'exported',
  slide_data: '[]',
})

const demoPostIreland = ref({
  id: 5,
  title: 'Irland entdecken',
  caption_instagram: 'Grüne Hügel, warme Menschen und eine unvergessliche Zeit in Irland.',
  hashtags_instagram: '#irland #ireland #exchange #treff',
  platform: 'instagram_feed',
  country: 'irland',
  status: 'reminded',
  slide_data: '[]',
})

const demoPosts = ref([
  demoPostInstagram.value,
  demoPostTikTok.value,
  demoPostAustralia.value,
  demoPostNZ.value,
  demoPostIreland.value,
])

const previewSlideIndex = ref(0)
const previewSize = ref('md')

const primaryShades = [
  { key: '50',  hex: '#EBF3FA', bg: 'bg-primary-50',  text: 'text-gray-900' },
  { key: '100', hex: '#D7E7F5', bg: 'bg-primary-100', text: 'text-gray-900' },
  { key: '200', hex: '#AFCFEB', bg: 'bg-primary-200', text: 'text-gray-900' },
  { key: '300', hex: '#87B7E0', bg: 'bg-primary-300', text: 'text-gray-900' },
  { key: '400', hex: '#5F9FD6', bg: 'bg-primary-400', text: 'text-white' },
  { key: '500', hex: '#3B7AB1', bg: 'bg-primary-500', text: 'text-white' },
  { key: '600', hex: '#2F628E', bg: 'bg-primary-600', text: 'text-white' },
  { key: '700', hex: '#244A6A', bg: 'bg-primary-700', text: 'text-white' },
  { key: '800', hex: '#193247', bg: 'bg-primary-800', text: 'text-white' },
  { key: '900', hex: '#0E1A23', bg: 'bg-primary-900', text: 'text-white' },
  { key: '950', hex: '#070D12', bg: 'bg-primary-950', text: 'text-white' },
]

const secondaryShades = [
  { key: '50',  hex: '#FFFBE6', bg: 'bg-secondary-50',  text: 'text-gray-900' },
  { key: '100', hex: '#FFF7CC', bg: 'bg-secondary-100', text: 'text-gray-900' },
  { key: '200', hex: '#FFEF99', bg: 'bg-secondary-200', text: 'text-gray-900' },
  { key: '300', hex: '#FFE766', bg: 'bg-secondary-300', text: 'text-gray-900' },
  { key: '400', hex: '#FFDF33', bg: 'bg-secondary-400', text: 'text-gray-900' },
  { key: '500', hex: '#FDD000', bg: 'bg-secondary-500', text: 'text-gray-900' },
  { key: '600', hex: '#CAA600', bg: 'bg-secondary-600', text: 'text-gray-900' },
  { key: '700', hex: '#987D00', bg: 'bg-secondary-700', text: 'text-white' },
  { key: '800', hex: '#655300', bg: 'bg-secondary-800', text: 'text-white' },
  { key: '900', hex: '#332A00', bg: 'bg-secondary-900', text: 'text-white' },
  { key: '950', hex: '#1A1500', bg: 'bg-secondary-950', text: 'text-white' },
]

const typographyScale = [
  { name: 'text-xs',   size: '12px / 16px',  class: 'text-xs',   example: 'Hinweistext, Labels' },
  { name: 'text-sm',   size: '14px / 20px',  class: 'text-sm',   example: 'Body klein, Tabellen' },
  { name: 'text-base', size: '16px / 24px',  class: 'text-base', example: 'Standard Body-Text' },
  { name: 'text-lg',   size: '18px / 28px',  class: 'text-lg',   example: 'Hervorgehobener Text' },
  { name: 'text-xl',   size: '20px / 28px',  class: 'text-xl',   example: 'Section-Header' },
  { name: 'text-2xl',  size: '24px / 32px',  class: 'text-2xl',  example: 'Seitentitel' },
  { name: 'text-3xl',  size: '30px / 36px',  class: 'text-3xl',  example: 'Feature-Titel' },
  { name: 'text-4xl',  size: '36px / 40px',  class: 'text-4xl',  example: 'Hero-Headlines' },
]

const spacingScale = [
  { name: '0',    px: '0px',    class: 'w-0' },
  { name: '0.5',  px: '2px',    class: 'w-0.5' },
  { name: '1',    px: '4px',    class: 'w-1' },
  { name: '2',    px: '8px',    class: 'w-2' },
  { name: '3',    px: '12px',   class: 'w-3' },
  { name: '4',    px: '16px',   class: 'w-4' },
  { name: '5',    px: '20px',   class: 'w-5' },
  { name: '6',    px: '24px',   class: 'w-6' },
  { name: '8',    px: '32px',   class: 'w-8' },
  { name: '10',   px: '40px',   class: 'w-10' },
  { name: '12',   px: '48px',   class: 'w-12' },
  { name: '16',   px: '64px',   class: 'w-16' },
  { name: '20',   px: '80px',   class: 'w-20' },
  { name: '24',   px: '96px',   class: 'w-24' },
]

const radiusScale = [
  { name: 'rounded-sm',  px: '4px',  description: 'Tags, Badges' },
  { name: 'rounded-md',  px: '8px',  description: 'Inputs, Small Cards' },
  { name: 'rounded-lg',  px: '12px', description: 'Cards, Dialogs' },
  { name: 'rounded-xl',  px: '16px', description: 'Panels, Modals' },
  { name: 'rounded-2xl', px: '20px', description: 'Hero Cards' },
  { name: 'rounded-3xl', px: '24px', description: 'Promo Sections' },
  { name: 'rounded-full', px: '9999px', description: 'Avatars, Dots' },
]

const shadowScale = [
  { name: 'shadow-sm',        description: 'Subtile Erhebung' },
  { name: 'shadow',           description: 'Standard' },
  { name: 'shadow-md',        description: 'Karten' },
  { name: 'shadow-lg',        description: 'Dropdowns, Popover' },
  { name: 'shadow-xl',        description: 'Dialoge, Modals' },
  { name: 'shadow-card',      description: 'Card Default' },
  { name: 'shadow-card-hover', description: 'Card Hover' },
  { name: 'shadow-dialog',    description: 'Dialog/Modal' },
]

const scrollToSection = (id) => {
  activeSection.value = id
  document.getElementById(`section-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <div class="min-h-screen" data-tour="design-system-header">
    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Design-System</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">TREFF Sprachreisen — Design-Tokens & Komponenten-Referenz</p>
      </div>
    </div>

    <!-- Section Navigation -->
    <div class="flex flex-wrap gap-2 mb-8 pb-4 border-b border-gray-200 dark:border-gray-700" data-tour="design-system-nav">
      <button
        v-for="section in sections"
        :key="section.id"
        @click="scrollToSection(section.id)"
        :class="[
          'px-3 py-1.5 text-sm font-medium rounded-lg transition-colors',
          activeSection === section.id
            ? 'bg-primary-500 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700',
        ]"
      >
        <AppIcon :name="section.icon" class="w-4 h-4 inline-block" /> {{ section.label }}
      </button>
    </div>

    <!-- ═══ COLORS ═══ -->
    <section id="section-colors" class="mb-12">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Farben</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        TREFF Brand-Farben mit vollständiger Shade-Palette (50–950). Nutzung: <code class="text-xs bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">bg-primary-500</code>, <code class="text-xs bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">text-secondary-600</code>
      </p>

      <!-- Primary -->
      <h3 class="text-base font-semibold text-gray-800 dark:text-gray-200 mb-3">Primary — TREFF Blau</h3>
      <div class="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-11 gap-2 mb-8">
        <div v-for="shade in primaryShades" :key="shade.key" class="flex flex-col items-center">
          <div :class="[shade.bg, shade.text, 'w-full h-16 rounded-lg flex items-center justify-center text-xs font-mono shadow-sm']">
            {{ shade.key }}
          </div>
          <span class="text-[10px] text-gray-500 dark:text-gray-400 mt-1 font-mono">{{ shade.hex }}</span>
        </div>
      </div>

      <!-- Secondary -->
      <h3 class="text-base font-semibold text-gray-800 dark:text-gray-200 mb-3">Secondary — TREFF Gelb</h3>
      <div class="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-11 gap-2 mb-8">
        <div v-for="shade in secondaryShades" :key="shade.key" class="flex flex-col items-center">
          <div :class="[shade.bg, shade.text, 'w-full h-16 rounded-lg flex items-center justify-center text-xs font-mono shadow-sm']">
            {{ shade.key }}
          </div>
          <span class="text-[10px] text-gray-500 dark:text-gray-400 mt-1 font-mono">{{ shade.hex }}</span>
        </div>
      </div>

      <!-- Brand Aliases -->
      <h3 class="text-base font-semibold text-gray-800 dark:text-gray-200 mb-3">Brand-Aliase (Legacy)</h3>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div class="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700">
          <div class="w-10 h-10 rounded-lg bg-treff-blue"></div>
          <div>
            <div class="text-xs font-medium text-gray-700 dark:text-gray-300">treff-blue</div>
            <div class="text-[10px] font-mono text-gray-400">#3B7AB1</div>
          </div>
        </div>
        <div class="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700">
          <div class="w-10 h-10 rounded-lg bg-treff-yellow"></div>
          <div>
            <div class="text-xs font-medium text-gray-700 dark:text-gray-300">treff-yellow</div>
            <div class="text-[10px] font-mono text-gray-400">#FDD000</div>
          </div>
        </div>
        <div class="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700">
          <div class="w-10 h-10 rounded-lg bg-treff-dark"></div>
          <div>
            <div class="text-xs font-medium text-gray-700 dark:text-gray-300">treff-dark</div>
            <div class="text-[10px] font-mono text-gray-400">#1A1A2E</div>
          </div>
        </div>
        <div class="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700">
          <div class="w-10 h-10 rounded-lg bg-treff-light border border-gray-200"></div>
          <div>
            <div class="text-xs font-medium text-gray-700 dark:text-gray-300">treff-light</div>
            <div class="text-[10px] font-mono text-gray-400">#F5F5F5</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══ COUNTRY THEMES ═══ -->
    <section id="section-country-themes" class="mb-12" data-testid="country-themes-section">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Country Themes</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        Länderspezifische Farbpaletten mit dynamischem Theme-Switching. Jedes Land hat eigene Primär-, Sekundär- und Akzentfarben,
        Gradient-Utilities und CSS Custom Properties.
      </p>

      <!-- Country Selector -->
      <div class="flex flex-wrap gap-2 mb-6" data-testid="country-theme-selector">
        <button
          v-for="key in allCountryKeys"
          :key="key"
          @click="selectedCountry = key"
          :data-testid="'country-btn-' + key"
          :class="[
            'px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 border-2',
            selectedCountry === key
              ? 'border-current shadow-md scale-105'
              : 'border-transparent bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700',
          ]"
          :style="selectedCountry === key ? { backgroundColor: COUNTRY_THEMES[key].primaryColor, color: '#FFFFFF', borderColor: COUNTRY_THEMES[key].secondaryColor } : {}"
        >
          {{ COUNTRY_THEMES[key].emoji }} {{ COUNTRY_THEMES[key].label }}
        </button>
      </div>

      <!-- Active Theme Display -->
      <TCountryThemeProvider :country="selectedCountry" subtle data-testid="country-theme-provider">
        <template #default="{ theme, primaryColor, secondaryColor, accentColor, gradientClass, borderClass, bgClass, textClass, label, emoji, palette, isCountryTheme, cssVars, gradientStyle }">
          <div class="rounded-xl p-6 border-2 transition-all duration-300" :style="{ borderColor: primaryColor }">

            <!-- Theme Header -->
            <div class="flex items-center gap-3 mb-6">
              <span class="text-3xl">{{ emoji }}</span>
              <div>
                <h3 class="text-lg font-bold" :style="{ color: primaryColor }" data-testid="country-theme-label">{{ label }}</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  Composable: <code class="text-xs bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">useCountryTheme('{{ countryTheme.countryKey.value }}')</code>
                </p>
              </div>
            </div>

            <!-- Color Swatches -->
            <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Farbpalette</h4>
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 mb-6">
              <div
                v-for="(color, name) in palette"
                :key="name"
                class="flex flex-col items-center"
              >
                <div
                  class="w-full h-14 rounded-lg shadow-sm border border-gray-200 dark:border-gray-600"
                  :style="{ backgroundColor: color }"
                ></div>
                <span class="text-xs font-medium text-gray-700 dark:text-gray-300 mt-1.5">{{ name }}</span>
                <span class="text-[10px] font-mono text-gray-400">{{ color }}</span>
              </div>
            </div>

            <!-- Token Values -->
            <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Theme Tokens</h4>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
              <div class="flex items-center gap-2 p-2 rounded-lg bg-white/50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
                <div class="w-6 h-6 rounded-md shadow-sm" :style="{ backgroundColor: primaryColor }"></div>
                <div>
                  <div class="text-xs font-medium text-gray-700 dark:text-gray-300">Primary</div>
                  <div class="text-[10px] font-mono text-gray-400" data-testid="country-primary-color">{{ primaryColor }}</div>
                </div>
              </div>
              <div class="flex items-center gap-2 p-2 rounded-lg bg-white/50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
                <div class="w-6 h-6 rounded-md shadow-sm border border-gray-200" :style="{ backgroundColor: secondaryColor }"></div>
                <div>
                  <div class="text-xs font-medium text-gray-700 dark:text-gray-300">Secondary</div>
                  <div class="text-[10px] font-mono text-gray-400" data-testid="country-secondary-color">{{ secondaryColor }}</div>
                </div>
              </div>
              <div class="flex items-center gap-2 p-2 rounded-lg bg-white/50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
                <div class="w-6 h-6 rounded-md shadow-sm" :style="{ backgroundColor: accentColor }"></div>
                <div>
                  <div class="text-xs font-medium text-gray-700 dark:text-gray-300">Accent</div>
                  <div class="text-[10px] font-mono text-gray-400" data-testid="country-accent-color">{{ accentColor }}</div>
                </div>
              </div>
            </div>

            <!-- Gradient Previews -->
            <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Gradient Utilities</h4>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
              <div>
                <div
                  class="h-16 rounded-lg shadow-sm"
                  :style="gradientStyle"
                  data-testid="country-gradient-preview"
                ></div>
                <code class="text-[10px] font-mono text-gray-400 mt-1 block">{{ gradientClass }} (Light)</code>
              </div>
              <div>
                <div
                  class="h-16 rounded-lg shadow-sm"
                  :style="countryTheme.gradientDarkStyle.value"
                ></div>
                <code class="text-[10px] font-mono text-gray-400 mt-1 block">{{ gradientClass }}-dark (Dark Mode)</code>
              </div>
            </div>

            <!-- CSS Classes Reference -->
            <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">CSS-Klassen</h4>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
              <div class="p-3 rounded-lg bg-white/60 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">gradientClass</div>
                <code class="text-xs font-mono" :style="{ color: primaryColor }">{{ gradientClass }}</code>
              </div>
              <div class="p-3 rounded-lg bg-white/60 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">borderClass</div>
                <code class="text-xs font-mono" :style="{ color: primaryColor }">{{ borderClass }}</code>
              </div>
              <div class="p-3 rounded-lg bg-white/60 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">bgClass</div>
                <code class="text-xs font-mono" :style="{ color: primaryColor }">{{ bgClass }}</code>
              </div>
              <div class="p-3 rounded-lg bg-white/60 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">textClass</div>
                <code class="text-xs font-mono" :style="{ color: primaryColor }">{{ textClass }}</code>
              </div>
            </div>

            <!-- CSS Custom Properties -->
            <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">CSS Custom Properties</h4>
            <div class="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/80 border border-gray-200 dark:border-gray-700 font-mono text-xs space-y-1">
              <div v-for="(value, varName) in cssVars" :key="varName" class="flex items-center gap-2">
                <span class="text-gray-500 dark:text-gray-400">{{ varName }}:</span>
                <span :style="{ color: value.startsWith('#') || value.startsWith('rgb') ? primaryColor : 'inherit' }">{{ value.length > 60 ? value.substring(0, 60) + '...' : value }}</span>
              </div>
            </div>

            <!-- Live Demo: Themed Card -->
            <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mt-6 mb-3">Live Demo: Themed Card</h4>
            <div
              class="p-5 rounded-xl border-2 transition-all duration-300"
              :style="{ borderColor: primaryColor, background: theme.gradientSubtle }"
              data-testid="country-themed-card"
            >
              <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm" :style="{ backgroundColor: primaryColor }">
                  {{ label.charAt(0) }}
                </div>
                <div>
                  <h5 class="font-semibold text-gray-900 dark:text-white">Highschool in {{ label }}</h5>
                  <p class="text-xs text-gray-500 dark:text-gray-400">Erlebe das Abenteuer deines Lebens!</p>
                </div>
              </div>
              <div class="h-2 rounded-full" :style="gradientStyle"></div>
            </div>
          </div>
        </template>
      </TCountryThemeProvider>

      <!-- All Countries Overview (Compact Grid) -->
      <h3 class="text-base font-semibold text-gray-800 dark:text-gray-200 mt-8 mb-4">Alle Länder-Paletten</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4" data-testid="country-palettes-grid">
        <div
          v-for="key in allCountryKeys"
          :key="key"
          class="rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700 shadow-sm"
        >
          <div class="h-12 flex items-center justify-center text-white font-semibold text-sm" :style="{ background: COUNTRY_THEMES[key].gradient }">
            {{ COUNTRY_THEMES[key].emoji }} {{ COUNTRY_THEMES[key].label }}
          </div>
          <div class="p-3 bg-white dark:bg-gray-800">
            <div class="flex gap-1.5">
              <div
                v-for="(color, name) in COUNTRY_THEMES[key].palette"
                :key="name"
                class="flex-1 h-6 rounded"
                :style="{ backgroundColor: color }"
                :title="name + ': ' + color"
              ></div>
            </div>
            <div class="mt-2 text-[10px] font-mono text-gray-400">
              treff-{{ key === 'newzealand' ? 'nz' : key }}
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══ TYPOGRAPHY ═══ -->
    <section id="section-typography" class="mb-12">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Typografie</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        Inter als primäre Schrift. Jede Größe hat eine definierte Line-Height für konsistente vertikale Rhythmik.
      </p>

      <div class="space-y-4">
        <div v-for="item in typographyScale" :key="item.name"
          class="flex items-baseline gap-4 p-4 rounded-lg border border-gray-200 dark:border-gray-700"
        >
          <div class="w-24 shrink-0">
            <span class="text-xs font-mono text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/30 px-1.5 py-0.5 rounded">{{ item.name }}</span>
          </div>
          <div class="w-28 shrink-0 text-xs text-gray-500 dark:text-gray-400 font-mono">{{ item.size }}</div>
          <div :class="[item.class, 'text-gray-900 dark:text-white flex-1']">{{ item.example }}</div>
        </div>
      </div>

      <div class="mt-6 p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
        <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Font-Familien</h4>
        <div class="flex flex-wrap gap-6">
          <div>
            <span class="font-sans text-lg text-gray-900 dark:text-white">Inter</span>
            <span class="text-xs text-gray-500 dark:text-gray-400 ml-2">font-sans</span>
          </div>
          <div>
            <span class="font-mono text-lg text-gray-900 dark:text-white">JetBrains Mono</span>
            <span class="text-xs text-gray-500 dark:text-gray-400 ml-2">font-mono</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══ BUTTONS ═══ -->
    <section id="section-buttons" class="mb-12">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Buttons</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        Vier Button-Varianten mit konsistentem Sizing, Transitions und Focus-Ring. Klassen: <code class="text-xs bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">btn-primary</code>, <code class="text-xs bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">btn-secondary</code>, <code class="text-xs bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">btn-ghost</code>, <code class="text-xs bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">btn-danger</code>
      </p>

      <!-- Button variants -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="p-6 rounded-lg border border-gray-200 dark:border-gray-700 flex flex-col items-center gap-4">
          <h4 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Primary</h4>
          <button class="btn-primary">Speichern</button>
          <code class="text-[10px] font-mono text-gray-400">.btn-primary</code>
        </div>
        <div class="p-6 rounded-lg border border-gray-200 dark:border-gray-700 flex flex-col items-center gap-4">
          <h4 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Secondary</h4>
          <button class="btn-secondary">Abenteuer</button>
          <code class="text-[10px] font-mono text-gray-400">.btn-secondary</code>
        </div>
        <div class="p-6 rounded-lg border border-gray-200 dark:border-gray-700 flex flex-col items-center gap-4">
          <h4 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Ghost</h4>
          <button class="btn-ghost">Abbrechen</button>
          <code class="text-[10px] font-mono text-gray-400">.btn-ghost</code>
        </div>
        <div class="p-6 rounded-lg border border-gray-200 dark:border-gray-700 flex flex-col items-center gap-4">
          <h4 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Danger</h4>
          <button class="btn-danger">Löschen</button>
          <code class="text-[10px] font-mono text-gray-400">.btn-danger</code>
        </div>
      </div>

      <!-- Button sizes -->
      <h3 class="text-base font-semibold text-gray-800 dark:text-gray-200 mb-3">Größen</h3>
      <div class="flex flex-wrap items-center gap-4 mb-6">
        <div class="flex flex-col items-center gap-2">
          <button class="btn-primary btn-sm">Klein</button>
          <code class="text-[10px] font-mono text-gray-400">btn-sm</code>
        </div>
        <div class="flex flex-col items-center gap-2">
          <button class="btn-primary">Standard</button>
          <code class="text-[10px] font-mono text-gray-400">(default)</code>
        </div>
        <div class="flex flex-col items-center gap-2">
          <button class="btn-primary btn-lg">Groß</button>
          <code class="text-[10px] font-mono text-gray-400">btn-lg</code>
        </div>
        <div class="flex flex-col items-center gap-2">
          <button class="btn-primary btn-icon">+</button>
          <code class="text-[10px] font-mono text-gray-400">btn-icon</code>
        </div>
      </div>

      <!-- Disabled state -->
      <h3 class="text-base font-semibold text-gray-800 dark:text-gray-200 mb-3">Deaktiviert</h3>
      <div class="flex flex-wrap items-center gap-4">
        <button class="btn-primary" disabled>Primary</button>
        <button class="btn-secondary" disabled>Secondary</button>
        <button class="btn-ghost" disabled>Ghost</button>
        <button class="btn-danger" disabled>Danger</button>
      </div>
    </section>

    <!-- ═══ CARDS ═══ -->
    <section id="section-cards" class="mb-12">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Cards</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        BaseCard-Komponente mit verschiedenen Props und Slots für konsistente Kartendarstellung.
      </p>

      <!-- BaseCard demos -->
      <h3 class="text-base font-semibold text-gray-800 dark:text-gray-200 mb-3">BaseCard Varianten</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <!-- Standard -->
        <div>
          <BaseCard padding="md" title="Standard Card" subtitle="Mit Titel und Untertitel">
            <p class="text-sm text-gray-500 dark:text-gray-400">Standard-Karte mit shadow-sm, border und rounded-xl.</p>
          </BaseCard>
          <code class="text-[10px] font-mono text-gray-400 mt-2 block">&lt;BaseCard padding="md"&gt;</code>
        </div>

        <!-- Hoverable -->
        <div>
          <BaseCard padding="md" hoverable title="Hover Card">
            <p class="text-sm text-gray-500 dark:text-gray-400">Schwebt beim Hovern hoch (shadow-md + translate).</p>
          </BaseCard>
          <code class="text-[10px] font-mono text-gray-400 mt-2 block">&lt;BaseCard hoverable&gt;</code>
        </div>

        <!-- Flat -->
        <div>
          <BaseCard padding="md" flat title="Flat Card">
            <p class="text-sm text-gray-500 dark:text-gray-400">Flacher Stil, ideal für verschachtelte Bereiche.</p>
          </BaseCard>
          <code class="text-[10px] font-mono text-gray-400 mt-2 block">&lt;BaseCard flat&gt;</code>
        </div>

        <!-- Section Card with header divider -->
        <div>
          <BaseCard padding="none" title="Section Card" subtitle="Mit Header-Divider">
            <template #headerAction>
              <button class="btn-sm btn-ghost">Aktion</button>
            </template>
            <div class="p-5">
              <p class="text-sm text-gray-500 dark:text-gray-400">Header mit border-b Trennlinie und headerAction-Slot.</p>
            </div>
          </BaseCard>
          <code class="text-[10px] font-mono text-gray-400 mt-2 block">&lt;BaseCard padding="none"&gt; + #headerAction</code>
        </div>

        <!-- Clickable with footer -->
        <div>
          <BaseCard padding="md" clickable hoverable title="Klickbare Karte" @click="() => {}">
            <p class="text-sm text-gray-500 dark:text-gray-400">Klickbar mit cursor-pointer und Footer.</p>
            <template #footer>
              <span class="text-xs text-gray-400">Footer-Bereich mit border-t</span>
            </template>
          </BaseCard>
          <code class="text-[10px] font-mono text-gray-400 mt-2 block">&lt;BaseCard clickable hoverable&gt; + #footer</code>
        </div>

        <!-- Large padding -->
        <div>
          <BaseCard padding="lg" :header-divider="false" title="Große Polsterung">
            <p class="text-sm text-gray-500 dark:text-gray-400">padding="lg" ohne Header-Divider.</p>
          </BaseCard>
          <code class="text-[10px] font-mono text-gray-400 mt-2 block">&lt;BaseCard padding="lg" :header-divider="false"&gt;</code>
        </div>
      </div>

      <!-- Legacy CSS classes -->
      <h3 class="text-base font-semibold text-gray-800 dark:text-gray-200 mb-3">Legacy CSS-Klassen</h3>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div>
          <div class="card mb-2">
            <h4 class="font-semibold text-gray-900 dark:text-white mb-1">Standard Card</h4>
            <p class="text-sm text-gray-500 dark:text-gray-400">Weisser Hintergrund, Rahmen, dezenter Schatten.</p>
          </div>
          <code class="text-[10px] font-mono text-gray-400">.card</code>
        </div>
        <div>
          <div class="card-hover mb-2 cursor-pointer">
            <h4 class="font-semibold text-gray-900 dark:text-white mb-1">Hover Card</h4>
            <p class="text-sm text-gray-500 dark:text-gray-400">Interaktive Karte mit Hover-Elevation.</p>
          </div>
          <code class="text-[10px] font-mono text-gray-400">.card-hover</code>
        </div>
        <div>
          <div class="card-flat mb-2">
            <h4 class="font-semibold text-gray-900 dark:text-white mb-1">Flat Card</h4>
            <p class="text-sm text-gray-500 dark:text-gray-400">Randlos, für verschachtelte Bereiche.</p>
          </div>
          <code class="text-[10px] font-mono text-gray-400">.card-flat</code>
        </div>
      </div>
    </section>

    <!-- ═══ INPUTS ═══ -->
    <section id="section-inputs" class="mb-12">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Inputs</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        Konsistente Formularelemente mit Label, Hint-Text und Fehlerzustand.
      </p>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-8">
        <!-- Default input -->
        <div>
          <label class="input-label">Standard-Input</label>
          <input type="text" class="input-field" placeholder="Vorname eingeben..." />
          <p class="input-hint">Hilfetext unter dem Eingabefeld.</p>
          <div class="mt-2">
            <code class="text-[10px] font-mono text-gray-400">.input-label + .input-field + .input-hint</code>
          </div>
        </div>

        <!-- Error state -->
        <div>
          <label class="input-label">Fehler-Zustand</label>
          <input type="text" class="input-field input-error" value="ungültig@" />
          <p class="input-error-text">Bitte eine gültige E-Mail-Adresse eingeben.</p>
          <div class="mt-2">
            <code class="text-[10px] font-mono text-gray-400">.input-field.input-error + .input-error-text</code>
          </div>
        </div>

        <!-- Select -->
        <div>
          <label class="input-label">Select</label>
          <select class="input-field">
            <option value="">Land auswählen...</option>
            <option>USA</option>
            <option>Kanada</option>
            <option>Australien</option>
          </select>
        </div>

        <!-- Textarea -->
        <div>
          <label class="input-label">Textarea</label>
          <textarea class="input-field" rows="3" placeholder="Beschreibung eingeben..."></textarea>
        </div>
      </div>
    </section>

    <!-- ═══ BADGES ═══ -->
    <section id="section-badges" class="mb-12">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Badges</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        Sechs Badge-Varianten für Status, Kategorien und Labels.
      </p>

      <div class="flex flex-wrap gap-3">
        <div class="flex flex-col items-center gap-2">
          <span class="badge-primary">Primary</span>
          <code class="text-[10px] font-mono text-gray-400">.badge-primary</code>
        </div>
        <div class="flex flex-col items-center gap-2">
          <span class="badge-secondary">Secondary</span>
          <code class="text-[10px] font-mono text-gray-400">.badge-secondary</code>
        </div>
        <div class="flex flex-col items-center gap-2">
          <span class="badge-success">Erfolg</span>
          <code class="text-[10px] font-mono text-gray-400">.badge-success</code>
        </div>
        <div class="flex flex-col items-center gap-2">
          <span class="badge-warning">Warnung</span>
          <code class="text-[10px] font-mono text-gray-400">.badge-warning</code>
        </div>
        <div class="flex flex-col items-center gap-2">
          <span class="badge-danger">Fehler</span>
          <code class="text-[10px] font-mono text-gray-400">.badge-danger</code>
        </div>
        <div class="flex flex-col items-center gap-2">
          <span class="badge-neutral">Neutral</span>
          <code class="text-[10px] font-mono text-gray-400">.badge-neutral</code>
        </div>
      </div>
    </section>

    <!-- ═══ SHADOWS ═══ -->
    <section id="section-shadows" class="mb-12">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Schatten</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        4-stufiges Elevationssystem plus spezielle Card- und Dialog-Schatten.
      </p>

      <div class="grid grid-cols-2 sm:grid-cols-4 gap-6">
        <div v-for="shadow in shadowScale" :key="shadow.name" class="flex flex-col items-center gap-3">
          <div :class="[shadow.name, 'w-full h-20 bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700 flex items-center justify-center']">
            <span class="text-xs text-gray-400 font-mono">{{ shadow.name }}</span>
          </div>
          <span class="text-[10px] text-gray-500 dark:text-gray-400">{{ shadow.description }}</span>
        </div>
      </div>
    </section>

    <!-- ═══ SPACING ═══ -->
    <section id="section-spacing" class="mb-12">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Spacing</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        4px-Grundraster. Erweitert mit halben und großen Werten für flexible Layouts.
      </p>

      <div class="space-y-2">
        <div v-for="sp in spacingScale" :key="sp.name"
          class="flex items-center gap-4"
        >
          <span class="w-10 text-right text-xs font-mono text-gray-500 dark:text-gray-400">{{ sp.name }}</span>
          <div :class="[sp.class, 'h-4 bg-primary-400 dark:bg-primary-500 rounded-sm']" :style="{ minWidth: sp.px }"></div>
          <span class="text-xs text-gray-400 font-mono">{{ sp.px }}</span>
        </div>
      </div>
    </section>

    <!-- ═══ BORDER RADIUS ═══ -->
    <section id="section-radius" class="mb-12">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Border Radius</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        Konsistentes 3-Stufen-System plus runde Varianten.
      </p>

      <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-4">
        <div v-for="r in radiusScale" :key="r.name" class="flex flex-col items-center gap-2">
          <div :class="[r.name, 'w-20 h-20 bg-primary-100 dark:bg-primary-900/40 border-2 border-primary-400 dark:border-primary-500']"></div>
          <span class="text-xs font-mono text-primary-600 dark:text-primary-400">{{ r.name }}</span>
          <span class="text-[10px] text-gray-400">{{ r.px }}</span>
          <span class="text-[10px] text-gray-500 dark:text-gray-400 text-center">{{ r.description }}</span>
        </div>
      </div>
    </section>

    <!-- ═══ DESIGN GUIDELINES ═══ -->
    <section class="mb-12 p-6 rounded-xl bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800">
      <h2 class="text-xl font-bold text-primary-800 dark:text-primary-200 mb-4">Design-Richtlinien</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 text-sm text-primary-700 dark:text-primary-300">
        <div>
          <h4 class="font-semibold mb-2">Farben</h4>
          <ul class="space-y-1 list-disc list-inside">
            <li>Primary Blue für Aktionen und Links</li>
            <li>Secondary Yellow sparsam für Highlights</li>
            <li>Grautöne für Text und Hintergründe</li>
            <li>Semantische Farben: green=Erfolg, amber=Warnung, red=Fehler</li>
          </ul>
        </div>
        <div>
          <h4 class="font-semibold mb-2">Typografie</h4>
          <ul class="space-y-1 list-disc list-inside">
            <li>Inter für UI, JetBrains Mono für Code</li>
            <li>Max 3 Größen pro View verwenden</li>
            <li>font-bold für Titel, font-medium für Labels</li>
          </ul>
        </div>
        <div>
          <h4 class="font-semibold mb-2">Spacing</h4>
          <ul class="space-y-1 list-disc list-inside">
            <li>4px-Grundraster einhalten</li>
            <li>p-4 für Card-Inhalte, gap-6 zwischen Sektionen</li>
            <li>mb-6 zwischen Seitenabschnitten</li>
          </ul>
        </div>
        <div>
          <h4 class="font-semibold mb-2">Komponenten</h4>
          <ul class="space-y-1 list-disc list-inside">
            <li>btn-primary für Hauptaktionen, btn-ghost für sekundäre</li>
            <li>card für Inhaltsbereiche, card-hover für klickbare</li>
            <li>Einheitliche rounded-lg für Cards, rounded-md für Inputs</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- ═══ POST PREVIEW CARDS ═══ -->
    <section id="section-previews" class="mb-12" data-testid="design-system-previews">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Post Preview Cards</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        Realistische Instagram- und TikTok-Mockup-Karten. Zeigen, wie Posts auf den jeweiligen Plattformen aussehen werden.
      </p>

      <!-- Size selector -->
      <div class="flex items-center gap-2 mb-6">
        <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Größe:</span>
        <button
          v-for="s in ['sm', 'md', 'lg']"
          :key="s"
          @click="previewSize = s"
          :class="[
            'px-3 py-1 text-xs font-medium rounded-lg transition-colors',
            previewSize === s ? 'bg-primary-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400'
          ]"
          :data-testid="'preview-size-' + s"
        >
          {{ s.toUpperCase() }}
        </button>
      </div>

      <!-- Individual Cards -->
      <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">Instagram Feed Mockup</h3>
      <div class="flex flex-wrap gap-6 mb-8" data-testid="preview-instagram-section">
        <PostPreviewCard
          :post="demoPostInstagram"
          :size="previewSize"
          :show-caption="true"
          :current-slide-index="previewSlideIndex"
          @slide-change="previewSlideIndex = $event"
          @click="function(){}"
        />
        <PostPreviewCard
          :post="demoPostAustralia"
          :size="previewSize"
          :show-caption="true"
          @click="function(){}"
        />
        <PostPreviewCard
          :post="demoPostIreland"
          :size="previewSize"
          :show-caption="true"
          @click="function(){}"
        />
      </div>

      <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">TikTok Mockup</h3>
      <div class="flex flex-wrap gap-6 mb-8" data-testid="preview-tiktok-section">
        <PostPreviewCardTikTok
          :post="demoPostTikTok"
          :size="previewSize"
          :show-caption="true"
          @click="function(){}"
        />
        <PostPreviewCardTikTok
          :post="demoPostNZ"
          :size="previewSize"
          :show-caption="true"
          @click="function(){}"
        />
      </div>

      <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">Preview Grid (gemischt)</h3>
      <PostPreviewGrid
        :posts="demoPosts"
        :size="previewSize"
        :show-caption="true"
        platform-filter="all"
        @post-click="function(){}"
      />
    </section>
  </div>
</template>
