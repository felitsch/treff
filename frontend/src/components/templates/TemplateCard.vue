<script setup>
/**
 * TemplateCard.vue — Visual thumbnail card for the Template Gallery.
 *
 * Displays a scaled-down live preview of a template's HTML/CSS,
 * the template name, a category badge, platform format tag,
 * country flag (if applicable), and a favorite toggle button.
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  template: { type: Object, required: true },
  isFavorite: { type: Boolean, default: false },
  categories: { type: Object, default: () => ({}) },
  platformLabels: { type: Object, default: () => ({}) },
  countryFlags: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['toggle-favorite', 'select'])

const iframeRef = ref(null)

// Build a full HTML document for the template preview
const previewSrc = computed(() => {
  const t = props.template
  if (!t) return ''

  let html = t.html_content || ''
  let css = t.css_content || ''

  // Parse colors
  let colors = {}
  try {
    colors = JSON.parse(t.default_colors || '{}')
  } catch (e) { /* ignore */ }

  const primary = colors.primary || '#3B7AB1'
  const secondary = colors.secondary || '#FDD000'
  const accent = colors.accent || '#FFFFFF'
  const background = colors.background || '#1A1A2E'

  // Parse fonts
  let fonts = {}
  try {
    fonts = JSON.parse(t.default_fonts || '{}')
  } catch (e) { /* ignore */ }
  const headingFont = fonts.heading_font || 'Montserrat'
  const bodyFont = fonts.body_font || 'Inter'

  // Replace color placeholders in CSS
  css = css
    .replace(/var\(--primary(?:-color)?\)/g, primary)
    .replace(/var\(--secondary(?:-color)?\)/g, secondary)
    .replace(/var\(--accent(?:-color)?\)/g, accent)
    .replace(/var\(--background(?:-color)?\)/g, background)
    .replace(/var\(--heading-font\)/g, headingFont)
    .replace(/var\(--body-font\)/g, bodyFont)

  // Replace placeholders in HTML with sample content
  html = html
    .replace(/\{\{headline\}\}/g, 'Dein Highschool-Abenteuer')
    .replace(/\{\{subheadline\}\}/g, 'Mit TREFF Sprachreisen')
    .replace(/\{\{body_text\}\}/g, 'Erlebe das Abenteuer deines Lebens.')
    .replace(/\{\{cta_text\}\}/g, 'Jetzt bewerben')
    .replace(/\{\{quote_text\}\}/g, 'Das war die beste Zeit meines Lebens!')
    .replace(/\{\{quote_author\}\}/g, 'Lisa, 17')
    .replace(/\{\{student_name\}\}/g, 'Max')
    .replace(/\{\{student_name_initial\}\}/g, 'M')
    .replace(/\{\{arc_title\}\}/g, 'Mein Abenteuer')
    .replace(/\{\{episode_number\}\}/g, '1')
    .replace(/\{\{episode_title\}\}/g, 'Der Anfang')
    .replace(/\{\{total_episodes\}\}/g, '4')
    .replace(/\{\{previously_text\}\}/g, 'Bisher passiert...')
    .replace(/\{\{cliffhanger_text\}\}/g, 'Wie geht es weiter?')
    .replace(/\{\{next_episode_hint\}\}/g, 'Morgen mehr!')
    .replace(/\{\{bullet_points\}\}/g, '<li>Punkt 1</li><li>Punkt 2</li><li>Punkt 3</li>')
    .replace(/\{\{title\}\}/g, t.name)
    .replace(/\{\{content\}\}/g, 'Vorschau-Inhalt')

  // Get dimensions based on platform format
  const dims = {
    feed_square: { w: 1080, h: 1080 },
    feed_portrait: { w: 1080, h: 1350 },
    story: { w: 1080, h: 1920 },
    tiktok: { w: 1080, h: 1920 },
  }
  const d = dims[t.platform_format] || dims.feed_square

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&family=Inter:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { width: ${d.w}px; height: ${d.h}px; overflow: hidden; }
  body { font-family: ${bodyFont}, sans-serif; }
  ${css}
</style>
</head>
<body>${html}</body>
</html>`
})

// Category info
const catInfo = computed(() => {
  return props.categories[props.template.category] || {
    label: props.template.category,
    icon: '',
    color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  }
})

// Platform info
const platInfo = computed(() => {
  return props.platformLabels[props.template.platform_format] || {
    label: props.template.platform_format,
    icon: '',
    dim: '',
  }
})

// Country flag
const flag = computed(() => {
  if (!props.template.country) return null
  return props.countryFlags[props.template.country] || null
})

// Slide count label
const slideLabel = computed(() => {
  const count = props.template.slide_count || 1
  return count > 1 ? `${count} Slides` : null
})

// Aspect ratio class for the preview container
const aspectClass = computed(() => {
  const fmt = props.template.platform_format
  if (fmt === 'story' || fmt === 'tiktok') return 'aspect-[9/16]'
  if (fmt === 'feed_portrait') return 'aspect-[4/5]'
  return 'aspect-square'
})
</script>

<template>
  <div
    class="group relative bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer overflow-hidden"
    @click="emit('select', template)"
    data-testid="template-card"
  >
    <!-- Thumbnail preview area -->
    <div
      :class="['relative w-full overflow-hidden bg-gray-100 dark:bg-gray-900 flex items-center justify-center', aspectClass]"
      style="max-height: 280px;"
    >
      <iframe
        ref="iframeRef"
        :srcdoc="previewSrc"
        class="pointer-events-none border-0"
        :style="{
          width: (template.platform_format === 'story' || template.platform_format === 'tiktok') ? '1080px' : (template.platform_format === 'feed_portrait' ? '1080px' : '1080px'),
          height: (template.platform_format === 'story' || template.platform_format === 'tiktok') ? '1920px' : (template.platform_format === 'feed_portrait' ? '1350px' : '1080px'),
          transform: `scale(${(template.platform_format === 'story' || template.platform_format === 'tiktok') ? 0.13 : (template.platform_format === 'feed_portrait' ? 0.175 : 0.2)})`,
          transformOrigin: 'top left',
        }"
        sandbox="allow-same-origin"
        loading="lazy"
        tabindex="-1"
        aria-hidden="true"
      />

      <!-- Overlay gradient on hover -->
      <div class="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />

      <!-- Favorite button -->
      <button
        class="absolute top-2 right-2 z-10 w-8 h-8 flex items-center justify-center rounded-full transition-all duration-200"
        :class="isFavorite
          ? 'bg-yellow-400 text-white shadow-md'
          : 'bg-white/80 dark:bg-gray-700/80 text-gray-400 hover:text-yellow-500 opacity-0 group-hover:opacity-100'"
        @click.stop="emit('toggle-favorite', template.id)"
        :aria-label="isFavorite ? 'Aus Favoriten entfernen' : 'Als Favorit markieren'"
        :title="isFavorite ? 'Aus Favoriten entfernen' : 'Als Favorit markieren'"
        data-testid="favorite-btn"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" :fill="isFavorite ? 'currentColor' : 'none'" :stroke="isFavorite ? 'none' : 'currentColor'" stroke-width="2" class="w-4 h-4">
          <path stroke-linecap="round" stroke-linejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
        </svg>
      </button>

      <!-- Platform format badge -->
      <span class="absolute bottom-2 left-2 z-10 text-xs px-2 py-0.5 rounded-full bg-black/60 text-white font-medium">
        {{ platInfo.icon }} {{ platInfo.label }}
      </span>

      <!-- Country flag badge -->
      <span v-if="flag" class="absolute bottom-2 right-2 z-10 text-lg" :title="template.country">
        {{ flag }}
      </span>
    </div>

    <!-- Card info -->
    <div class="p-3">
      <!-- Template name -->
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white truncate" :title="template.name">
        {{ template.name }}
      </h3>

      <!-- Category badge + slide count -->
      <div class="flex items-center gap-2 mt-1.5">
        <span
          :class="['inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium', catInfo.color]"
        >
          <span>{{ catInfo.icon }}</span>
          <span>{{ catInfo.label }}</span>
        </span>
        <span v-if="slideLabel" class="text-xs text-gray-400 dark:text-gray-500">
          {{ slideLabel }}
        </span>
      </div>
    </div>
  </div>
</template>
