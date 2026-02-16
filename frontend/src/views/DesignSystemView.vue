<script setup>
import { ref } from 'vue'

const activeSection = ref('colors')

const sections = [
  { id: 'colors', label: 'Farben', icon: '🎨' },
  { id: 'typography', label: 'Typografie', icon: '📝' },
  { id: 'buttons', label: 'Buttons', icon: '🔘' },
  { id: 'cards', label: 'Cards', icon: '📦' },
  { id: 'inputs', label: 'Inputs', icon: '📋' },
  { id: 'badges', label: 'Badges', icon: '🏷️' },
  { id: 'shadows', label: 'Shadows', icon: '🌑' },
  { id: 'spacing', label: 'Spacing', icon: '📐' },
  { id: 'radius', label: 'Radius', icon: '⬜' },
]

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
        {{ section.icon }} {{ section.label }}
      </button>
    </div>

    <!-- ═══ COLORS ═══ -->
    <section id="section-colors" class="mb-12">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Farben</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        TREFF Brand-Farben mit vollstaendiger Shade-Palette (50–950). Nutzung: <code class="text-xs bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">bg-primary-500</code>, <code class="text-xs bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">text-secondary-600</code>
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

    <!-- ═══ TYPOGRAPHY ═══ -->
    <section id="section-typography" class="mb-12">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Typografie</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        Inter als primaere Schrift. Jede Groesse hat eine definierte Line-Height fuer konsistente vertikale Rhythmik.
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
          <button class="btn-danger">Loeschen</button>
          <code class="text-[10px] font-mono text-gray-400">.btn-danger</code>
        </div>
      </div>

      <!-- Button sizes -->
      <h3 class="text-base font-semibold text-gray-800 dark:text-gray-200 mb-3">Groessen</h3>
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
          <button class="btn-primary btn-lg">Gross</button>
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
        Drei Card-Varianten fuer unterschiedliche Kontexte.
      </p>

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
            <p class="text-sm text-gray-500 dark:text-gray-400">Randlos, fuer verschachtelte Bereiche.</p>
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
          <input type="text" class="input-field input-error" value="ungueltig@" />
          <p class="input-error-text">Bitte eine gueltige E-Mail-Adresse eingeben.</p>
          <div class="mt-2">
            <code class="text-[10px] font-mono text-gray-400">.input-field.input-error + .input-error-text</code>
          </div>
        </div>

        <!-- Select -->
        <div>
          <label class="input-label">Select</label>
          <select class="input-field">
            <option value="">Land auswaehlen...</option>
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
        Sechs Badge-Varianten fuer Status, Kategorien und Labels.
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
        4px-Grundraster. Erweitert mit halben und grossen Werten fuer flexible Layouts.
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
            <li>Primary Blue fuer Aktionen und Links</li>
            <li>Secondary Yellow sparsam fuer Highlights</li>
            <li>Grautone fuer Text und Hintergruende</li>
            <li>Semantische Farben: green=Erfolg, amber=Warnung, red=Fehler</li>
          </ul>
        </div>
        <div>
          <h4 class="font-semibold mb-2">Typografie</h4>
          <ul class="space-y-1 list-disc list-inside">
            <li>Inter fuer UI, JetBrains Mono fuer Code</li>
            <li>Max 3 Groessen pro View verwenden</li>
            <li>font-bold fuer Titel, font-medium fuer Labels</li>
          </ul>
        </div>
        <div>
          <h4 class="font-semibold mb-2">Spacing</h4>
          <ul class="space-y-1 list-disc list-inside">
            <li>4px-Grundraster einhalten</li>
            <li>p-4 fuer Card-Inhalte, gap-6 zwischen Sektionen</li>
            <li>mb-6 zwischen Seitenabschnitten</li>
          </ul>
        </div>
        <div>
          <h4 class="font-semibold mb-2">Komponenten</h4>
          <ul class="space-y-1 list-disc list-inside">
            <li>btn-primary fuer Hauptaktionen, btn-ghost fuer sekundaere</li>
            <li>card fuer Inhaltsbereiche, card-hover fuer klickbare</li>
            <li>Einheitliche rounded-lg fuer Cards, rounded-md fuer Inputs</li>
          </ul>
        </div>
      </div>
    </section>
  </div>
</template>
