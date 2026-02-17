<script setup>
/**
 * TemplatePreviewModal.vue — Full-size template preview with details.
 *
 * Feature #243: Template-Vorschau Modal mit Details
 * - Large template preview with example data
 * - Meta info: name, category, format, platforms
 * - "Verwenden" button → Post-Creator with template_id
 * - "Anpassen" button → Template-Editor
 * - Tags: countries, seasons, themes
 * - Keyboard: ESC to close, arrow keys to browse
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useFocusTrap } from '@/composables/useFocusTrap'

const props = defineProps({
  template: { type: Object, default: null },
  show: { type: Boolean, default: false },
  isFavorite: { type: Boolean, default: false },
  /** All templates in the filtered list, for arrow-key navigation */
  templateList: { type: Array, default: () => [] },
  categories: { type: Object, default: () => ({}) },
  platformLabels: { type: Object, default: () => ({}) },
  countryFlags: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['close', 'toggle-favorite', 'navigate'])

const router = useRouter()
const modalRef = ref(null)
const { activate: activateFocusTrap, deactivate: deactivateFocusTrap } = useFocusTrap(modalRef)

// ─── Keyboard handling ────────────────────────────────────────────
function handleKeydown(e) {
  if (!props.show) return

  if (e.key === 'Escape') {
    emit('close')
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    e.preventDefault()
    navigatePrev()
  } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
    e.preventDefault()
    navigateNext()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

// ─── Navigation between templates ─────────────────────────────────
const currentIndex = computed(() => {
  if (!props.template || !props.templateList.length) return -1
  return props.templateList.findIndex(t => t.id === props.template.id)
})

const hasPrev = computed(() => currentIndex.value > 0)
const hasNext = computed(() => currentIndex.value >= 0 && currentIndex.value < props.templateList.length - 1)

const positionLabel = computed(() => {
  if (currentIndex.value < 0) return ''
  return `${currentIndex.value + 1} / ${props.templateList.length}`
})

function navigatePrev() {
  if (hasPrev.value) {
    emit('navigate', props.templateList[currentIndex.value - 1])
  }
}

function navigateNext() {
  if (hasNext.value) {
    emit('navigate', props.templateList[currentIndex.value + 1])
  }
}

// ─── Preview HTML generation ──────────────────────────────────────
const previewSrc = computed(() => {
  const t = props.template
  if (!t) return ''

  let html = t.html_content || ''
  let css = t.css_content || ''

  // Parse colors
  let colors = {}
  try { colors = JSON.parse(t.default_colors || '{}') } catch (e) { /* ignore */ }
  const primary = colors.primary || '#3B7AB1'
  const secondary = colors.secondary || '#FDD000'
  const accent = colors.accent || '#FFFFFF'
  const background = colors.background || '#1A1A2E'

  // Parse fonts
  let fonts = {}
  try { fonts = JSON.parse(t.default_fonts || '{}') } catch (e) { /* ignore */ }
  const headingFont = fonts.heading_font || 'Montserrat'
  const bodyFont = fonts.body_font || 'Inter'

  // Replace CSS variables
  css = css
    .replace(/var\(--primary(?:-color)?\)/g, primary)
    .replace(/var\(--secondary(?:-color)?\)/g, secondary)
    .replace(/var\(--accent(?:-color)?\)/g, accent)
    .replace(/var\(--background(?:-color)?\)/g, background)
    .replace(/var\(--heading-font\)/g, headingFont)
    .replace(/var\(--body-font\)/g, bodyFont)

  // Replace placeholders with sample content
  html = html
    .replace(/\{\{headline\}\}/g, 'Dein Highschool-Abenteuer')
    .replace(/\{\{subheadline\}\}/g, 'Mit TREFF Sprachreisen')
    .replace(/\{\{body_text\}\}/g, 'Erlebe das Abenteuer deines Lebens mit einem Highschool-Aufenthalt im Ausland. Neue Freunde, neue Kultur, unvergessliche Erfahrungen.')
    .replace(/\{\{cta_text\}\}/g, 'Jetzt bewerben')
    .replace(/\{\{quote_text\}\}/g, 'Das war die beste Zeit meines Lebens! Ich habe so viel gelernt und tolle Freundschaften geschlossen.')
    .replace(/\{\{quote_author\}\}/g, 'Lisa M., 17')
    .replace(/\{\{student_name\}\}/g, 'Max Müller')
    .replace(/\{\{student_name_initial\}\}/g, 'M')
    .replace(/\{\{arc_title\}\}/g, 'Mein Abenteuer in den USA')
    .replace(/\{\{episode_number\}\}/g, '2')
    .replace(/\{\{episode_title\}\}/g, 'Der erste Schultag')
    .replace(/\{\{total_episodes\}\}/g, '4')
    .replace(/\{\{previously_text\}\}/g, 'In der letzten Episode: Max kam in seiner Gastfamilie an und entdeckte sein neues Zuhause...')
    .replace(/\{\{cliffhanger_text\}\}/g, 'Wie wird Max seinen ersten Schultag überstehen?')
    .replace(/\{\{next_episode_hint\}\}/g, 'Morgen: Der erste Football-Abend!')
    .replace(/\{\{bullet_points\}\}/g, '<li>Kultureller Austausch erleben</li><li>Englisch fließend sprechen</li><li>Freundschaften fürs Leben</li><li>Selbstständigkeit entwickeln</li>')
    .replace(/\{\{title\}\}/g, t.name)
    .replace(/\{\{content\}\}/g, 'Vorschau-Inhalt für das Template')

  // Dimensions
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

// ─── Computed metadata ────────────────────────────────────────────
const catInfo = computed(() => {
  if (!props.template) return { label: '', icon: '', color: '' }
  return props.categories[props.template.category] || {
    label: props.template.category,
    icon: '',
    color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  }
})

const platInfo = computed(() => {
  if (!props.template) return { label: '', icon: '', dim: '' }
  return props.platformLabels[props.template.platform_format] || {
    label: props.template.platform_format,
    icon: '',
    dim: '',
  }
})

const countryFlag = computed(() => {
  if (!props.template?.country) return null
  return props.countryFlags[props.template.country] || null
})

const countryLabel = computed(() => {
  if (!props.template?.country) return null
  const names = {
    usa: 'USA',
    canada: 'Kanada',
    australia: 'Australien',
    newzealand: 'Neuseeland',
    ireland: 'Irland',
  }
  return names[props.template.country] || props.template.country
})

// Placeholder fields
const placeholderFields = computed(() => {
  if (!props.template?.placeholder_fields) return []
  try {
    const fields = JSON.parse(props.template.placeholder_fields)
    return Array.isArray(fields) ? fields : []
  } catch (e) {
    return []
  }
})

// Platform suitability tags
const platformTags = computed(() => {
  if (!props.template) return []
  const fmt = props.template.platform_format
  const tags = []
  if (fmt === 'feed_square') {
    tags.push('Instagram Feed', 'Facebook')
  } else if (fmt === 'feed_portrait') {
    tags.push('Instagram Feed', 'Facebook', 'Pinterest')
  } else if (fmt === 'story') {
    tags.push('Instagram Story', 'Facebook Story', 'WhatsApp Status')
  } else if (fmt === 'tiktok') {
    tags.push('TikTok', 'Instagram Reels', 'YouTube Shorts')
  }
  return tags
})

// Season/theme tags
const themeTags = computed(() => {
  if (!props.template) return []
  const cat = props.template.category
  const tags = []
  // Map categories to suitable themes
  if (cat === 'laender_spotlight') tags.push('Länderinfo', 'Inspiration')
  if (cat === 'erfahrungsberichte') tags.push('Testimonial', 'Social Proof')
  if (cat === 'infografiken') tags.push('Informativ', 'Statistiken')
  if (cat === 'fristen_cta') tags.push('Deadline', 'Bewerbung')
  if (cat === 'tipps_tricks') tags.push('Ratgeber', 'Vorbereitung')
  if (cat === 'faq') tags.push('Häufige Fragen', 'Service')
  if (cat === 'foto_posts') tags.push('Visuell', 'Storytelling')
  if (cat === 'reel_tiktok_thumbnails') tags.push('Video', 'Thumbnail')
  if (cat === 'story_posts') tags.push('Interaktiv', 'Engagement')
  if (cat === 'story_teaser') tags.push('Teaser', 'Serie')
  if (cat === 'story_series') tags.push('Serie', 'Mehrteilig')
  // Add "Ganzjährig" for most templates
  tags.push('Ganzjährig')
  return tags
})

// Preview scale based on format
const previewDims = computed(() => {
  if (!props.template) return { w: 1080, h: 1080 }
  const dims = {
    feed_square: { w: 1080, h: 1080 },
    feed_portrait: { w: 1080, h: 1350 },
    story: { w: 1080, h: 1920 },
    tiktok: { w: 1080, h: 1920 },
  }
  return dims[props.template.platform_format] || dims.feed_square
})

const previewScale = computed(() => {
  const d = previewDims.value
  // Scale to fit within ~450px width and ~550px height
  return Math.min(450 / d.w, 550 / d.h)
})

// ─── Actions ──────────────────────────────────────────────────────
function useTemplate() {
  if (!props.template) return
  router.push({
    path: '/create/quick',
    query: { template_id: props.template.id },
  })
}

function editTemplate() {
  if (!props.template) return
  router.push({
    path: '/library/templates',
    query: { highlight: props.template.id, edit: 'true' },
  })
}

// Prevent body scroll and manage focus trap when modal is open
watch(() => props.show, (isOpen) => {
  if (isOpen) {
    document.body.style.overflow = 'hidden'
    // Activate focus trap after DOM update
    requestAnimationFrame(() => activateFocusTrap())
  } else {
    document.body.style.overflow = ''
    deactivateFocusTrap()
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="show && template"
        ref="modalRef"
        class="fixed inset-0 z-[9998] flex items-center justify-center"
        role="dialog"
        aria-modal="true"
        aria-labelledby="template-preview-title"
        data-testid="template-preview-modal"
      >
        <!-- Backdrop -->
        <div
          class="absolute inset-0 bg-black/60 backdrop-blur-sm"
          @click="emit('close')"
          aria-hidden="true"
        />

        <!-- Modal content -->
        <div class="relative z-10 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-5xl w-[95vw] max-h-[90vh] overflow-hidden flex flex-col lg:flex-row">

          <!-- Left side: Large preview -->
          <div class="lg:w-3/5 bg-gray-100 dark:bg-gray-800 flex items-center justify-center p-6 relative min-h-[300px]">
            <!-- Navigation arrows -->
            <button
              v-if="hasPrev"
              @click="navigatePrev"
              class="absolute left-2 top-1/2 -translate-y-1/2 z-20 w-10 h-10 flex items-center justify-center rounded-full bg-white/90 dark:bg-gray-700/90 shadow-lg hover:bg-white dark:hover:bg-gray-600 transition-colors"
              aria-label="Vorheriges Template"
              data-testid="prev-btn"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-gray-700 dark:text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
            </button>

            <button
              v-if="hasNext"
              @click="navigateNext"
              class="absolute right-2 top-1/2 -translate-y-1/2 z-20 w-10 h-10 flex items-center justify-center rounded-full bg-white/90 dark:bg-gray-700/90 shadow-lg hover:bg-white dark:hover:bg-gray-600 transition-colors"
              aria-label="Nächstes Template"
              data-testid="next-btn"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-gray-700 dark:text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </button>

            <!-- Position indicator -->
            <span v-if="positionLabel" class="absolute bottom-3 left-1/2 -translate-x-1/2 z-20 text-xs font-medium text-gray-500 dark:text-gray-400 bg-white/80 dark:bg-gray-700/80 px-3 py-1 rounded-full">
              {{ positionLabel }}
            </span>

            <!-- Template preview iframe -->
            <div class="relative overflow-hidden rounded-lg shadow-md" :style="{ width: previewDims.w * previewScale + 'px', height: previewDims.h * previewScale + 'px' }">
              <iframe
                :srcdoc="previewSrc"
                class="pointer-events-none border-0 origin-top-left"
                :style="{
                  width: previewDims.w + 'px',
                  height: previewDims.h + 'px',
                  transform: `scale(${previewScale})`,
                }"
                sandbox="allow-same-origin"
                loading="eager"
                tabindex="-1"
                aria-hidden="true"
              />
            </div>
          </div>

          <!-- Right side: Details -->
          <div class="lg:w-2/5 p-6 overflow-y-auto flex flex-col">
            <!-- Close button -->
            <button
              @click="emit('close')"
              class="absolute top-4 right-4 z-20 w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              aria-label="Schließen (ESC)"
              data-testid="close-btn"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <!-- Template name & favorite -->
            <div class="flex items-start gap-3 mb-4">
              <h2 id="template-preview-title" class="text-xl font-bold text-gray-900 dark:text-white flex-1" data-testid="modal-title">
                {{ template.name }}
              </h2>
              <button
                @click="emit('toggle-favorite', template.id)"
                :class="[
                  'w-9 h-9 flex items-center justify-center rounded-full transition-all shrink-0',
                  isFavorite
                    ? 'bg-yellow-100 text-yellow-500 dark:bg-yellow-900/50'
                    : 'bg-gray-100 text-gray-400 hover:text-yellow-500 dark:bg-gray-800 dark:text-gray-500',
                ]"
                :aria-label="isFavorite ? 'Aus Favoriten entfernen' : 'Als Favorit markieren'"
                data-testid="modal-fav-btn"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" :fill="isFavorite ? 'currentColor' : 'none'" :stroke="isFavorite ? 'none' : 'currentColor'" stroke-width="2" class="w-5 h-5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
                </svg>
              </button>
            </div>

            <!-- Category & format badges -->
            <div class="flex flex-wrap items-center gap-2 mb-4">
              <span :class="['inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-medium', catInfo.color]">
                <span>{{ catInfo.icon }}</span>
                <span>{{ catInfo.label }}</span>
              </span>
              <span class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-medium bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                {{ platInfo.icon }} {{ platInfo.label }}
                <span v-if="platInfo.dim" class="text-gray-400">({{ platInfo.dim }})</span>
              </span>
              <span v-if="template.slide_count > 1" class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400">
                {{ template.slide_count }} Slides
              </span>
            </div>

            <!-- Country -->
            <div v-if="countryFlag" class="flex items-center gap-2 mb-4">
              <span class="text-lg">{{ countryFlag }}</span>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ countryLabel }}</span>
            </div>

            <!-- Description -->
            <div class="mb-4">
              <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">
                Beschreibung
              </h3>
              <p class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                <template v-if="template.category === 'laender_spotlight'">
                  Visuelles Länder-Spotlight-Template für die Präsentation von Highschool-Aufenthaltszielen. Ideal für Carousel-Posts mit Highlights, Fakten und Call-to-Action.
                </template>
                <template v-else-if="template.category === 'erfahrungsberichte'">
                  Template für Erfahrungsberichte und Schüler-Testimonials. Authentische Geschichten von Teilnehmern bauen Vertrauen bei Eltern und Schülern auf.
                </template>
                <template v-else-if="template.category === 'infografiken'">
                  Informatives Infografik-Template mit Bullet-Points und Statistiken. Perfekt für Fakten, Vergleiche und Programmdetails.
                </template>
                <template v-else-if="template.category === 'fristen_cta'">
                  Aufmerksamkeitsstarkes Template für Fristen und Call-to-Actions. Ideal für Bewerbungsdeadlines und zeitlich begrenzte Angebote.
                </template>
                <template v-else-if="template.category === 'tipps_tricks'">
                  Carousel-Template für Tipps und Tricks rund um den Highschool-Aufenthalt. Bietet echten Mehrwert und fördert Engagement.
                </template>
                <template v-else-if="template.category === 'faq'">
                  FAQ-Template für häufig gestellte Fragen. Beantwortet Eltern- und Schülerfragen visuell ansprechend.
                </template>
                <template v-else-if="template.category === 'foto_posts'">
                  Foto-Post-Template mit Overlay-Elementen. Perfekt für Bilder aus dem Ausland mit TREFF-Branding.
                </template>
                <template v-else-if="template.category === 'reel_tiktok_thumbnails'">
                  Thumbnail-Template für Reels und TikTok-Videos. Auffällige Vorschaubilder für mehr Klicks.
                </template>
                <template v-else-if="template.category === 'story_posts'">
                  Instagram-Story-Template mit interaktiven Elementen. Perfekt für Umfragen, Countdowns und Q&A.
                </template>
                <template v-else-if="template.category === 'story_teaser'">
                  Teaser-Template für den Feed, das auf Story-Serien verweist. Generiert Traffic von Feed zu Stories.
                </template>
                <template v-else-if="template.category === 'story_series'">
                  Mehrteiliges Story-Serien-Template mit Episoden-Navigation. Perfekt für längere Erfahrungsberichte über mehrere Tage.
                </template>
                <template v-else>
                  Vielseitiges Template für Social-Media-Posts von TREFF Sprachreisen.
                </template>
              </p>
            </div>

            <!-- Platform suitability -->
            <div class="mb-4">
              <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">
                Geeignete Plattformen
              </h3>
              <div class="flex flex-wrap gap-1.5">
                <span
                  v-for="tag in platformTags"
                  :key="tag"
                  class="inline-flex items-center text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 font-medium"
                >
                  {{ tag }}
                </span>
              </div>
            </div>

            <!-- Theme tags -->
            <div class="mb-4">
              <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">
                Tags
              </h3>
              <div class="flex flex-wrap gap-1.5">
                <span
                  v-for="tag in themeTags"
                  :key="tag"
                  class="inline-flex items-center text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 font-medium"
                >
                  {{ tag }}
                </span>
              </div>
            </div>

            <!-- Placeholder fields -->
            <div v-if="placeholderFields.length > 0" class="mb-6">
              <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">
                Platzhalter-Felder
              </h3>
              <div class="flex flex-wrap gap-1.5">
                <code
                  v-for="field in placeholderFields"
                  :key="field"
                  class="inline-flex items-center text-xs px-2 py-0.5 rounded bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300 font-mono"
                >
                  {{ `\{\{${field}\}\}` }}
                </code>
              </div>
            </div>

            <!-- Action buttons (sticky at bottom) -->
            <div class="mt-auto pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
              <button
                @click="useTemplate"
                class="w-full py-2.5 px-4 rounded-lg bg-[#3B7AB1] text-white text-sm font-semibold hover:bg-[#326a9b] transition-colors flex items-center justify-center gap-2"
                data-testid="use-template-btn"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
                </svg>
                Verwenden
              </button>
              <button
                @click="editTemplate"
                class="w-full py-2.5 px-4 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm font-semibold hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-center justify-center gap-2"
                data-testid="edit-template-btn"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Anpassen
              </button>
            </div>

            <!-- Keyboard hint -->
            <p class="mt-3 text-center text-xs text-gray-400 dark:text-gray-500">
              ESC schließen &middot; Pfeiltasten blättern
            </p>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
