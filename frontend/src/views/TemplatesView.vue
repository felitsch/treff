<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import api from '@/utils/api'

const loading = ref(true)
const error = ref(null)
const templates = ref([])
const selectedCategory = ref('')
const selectedPlatform = ref('')

// Create template modal state
const showCreateModal = ref(false)
const creating = ref(false)
const createError = ref(null)
const createSuccess = ref(false)
const newTemplate = ref({
  name: '',
  category: '',
  platform_format: 'feed_square',
  slide_count: 1,
  html_content: '<div class="template">\n  <h1>{{title}}</h1>\n  <p>{{content}}</p>\n</div>',
  css_content: '.template {\n  padding: 40px;\n  font-family: Inter, sans-serif;\n  color: #FFFFFF;\n  background: linear-gradient(135deg, #1A1A2E 0%, #4C8BC2 100%);\n  min-height: 100%;\n}',
  placeholder_fields: '["title", "content"]',
})

// =============================================
// Template Editor with Live Preview
// =============================================
const showEditorModal = ref(false)
const editorTemplate = ref(null)
const editorPreviewRef = ref(null)

// Customization state - these drive the live preview
const editorCustom = ref({
  primaryColor: '#4C8BC2',
  secondaryColor: '#FDD000',
  accentColor: '#FFFFFF',
  backgroundColor: '#1A1A2E',
  headlineText: 'Dein Highschool-Abenteuer',
  subheadlineText: 'Starte jetzt mit TREFF Sprachreisen',
  bodyText: 'Erlebe das Abenteuer deines Lebens mit einem Highschool-Aufenthalt im Ausland.',
  ctaText: 'Jetzt bewerben',
  headingFont: 'Montserrat',
  bodyFont: 'Inter',
})

// Available fonts for selection
const availableFonts = [
  { value: 'Montserrat', label: 'Montserrat' },
  { value: 'Inter', label: 'Inter' },
  { value: 'Poppins', label: 'Poppins' },
  { value: 'Playfair Display', label: 'Playfair Display' },
  { value: 'Roboto', label: 'Roboto' },
  { value: 'Open Sans', label: 'Open Sans' },
  { value: 'Lato', label: 'Lato' },
]

// Computed: rendered preview HTML that updates reactively
const editorPreviewHtml = computed(() => {
  if (!editorTemplate.value) return ''

  const c = editorCustom.value
  let html = editorTemplate.value.html_content || ''
  let css = editorTemplate.value.css_content || ''

  // Replace placeholders in HTML with user-entered text
  html = html.replace(/\{\{title\}\}/g, c.headlineText)
  html = html.replace(/\{\{headline\}\}/g, c.headlineText)
  html = html.replace(/\{\{subheadline\}\}/g, c.subheadlineText)
  html = html.replace(/\{\{content\}\}/g, c.bodyText)
  html = html.replace(/\{\{body_text\}\}/g, c.bodyText)
  html = html.replace(/\{\{cta_text\}\}/g, c.ctaText)
  html = html.replace(/\{\{cta\}\}/g, c.ctaText)
  html = html.replace(/\{\{quote_text\}\}/g, c.bodyText)
  html = html.replace(/\{\{quote_author\}\}/g, 'Max M., Austauschschueler')
  html = html.replace(/\{\{bullet_points\}\}/g, 'Punkt 1, Punkt 2, Punkt 3')
  // Remove any remaining unmatched placeholders
  html = html.replace(/\{\{image\}\}/g, '')
  html = html.replace(/\{\{[^}]+\}\}/g, '')

  // Build CSS with customized colors and fonts
  // The templates use CSS variables like var(--primary-color), var(--secondary-color), var(--bg-color)
  // We set these at the root level so inline style fallbacks get overridden
  const customCss = `
    @import url('https://fonts.googleapis.com/css2?family=${encodeURIComponent(c.headingFont)}:wght@400;600;700;800&family=${encodeURIComponent(c.bodyFont)}:wght@300;400;500;600&display=swap');

    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { margin: 0; overflow: hidden; }

    :root {
      --primary-color: ${c.primaryColor};
      --secondary-color: ${c.secondaryColor};
      --accent-color: ${c.accentColor};
      --bg-color: ${c.backgroundColor};
      --primary: ${c.primaryColor};
      --secondary: ${c.secondaryColor};
      --background: ${c.backgroundColor};
      --heading-font: '${c.headingFont}', sans-serif;
      --body-font: '${c.bodyFont}', sans-serif;
    }

    ${css}

    /* Override font families with user selection */
    .template-wrapper, .template, .slide, [class*="template"] {
      font-family: '${c.bodyFont}', sans-serif !important;
    }
    .template-headline, .template-wrapper h1, .template h1, h1 {
      font-family: '${c.headingFont}', sans-serif !important;
    }
    .template-subheadline, .template-wrapper h2, .template h2, h2 {
      font-family: '${c.headingFont}', sans-serif !important;
    }
    .template-body-text, .template-wrapper p, .template p, p {
      font-family: '${c.bodyFont}', sans-serif !important;
    }

    /* Override colors with user selection via inline style overrides */
    .template-headline {
      color: ${c.primaryColor} !important;
    }
    .template-subheadline {
      color: ${c.secondaryColor} !important;
    }
    .template-bg {
      background: ${c.backgroundColor} !important;
    }
    .template-cta {
      background: ${c.secondaryColor} !important;
      color: ${c.backgroundColor} !important;
    }
    .template-logo {
      background: ${c.primaryColor} !important;
    }
  `

  return '<!DOCTYPE html><html><head><meta charset="utf-8"><style>' + customCss + '</style></head><body>' + html + '</body></html>'
})

function openEditor(template) {
  editorTemplate.value = { ...template }

  // Parse existing colors from template
  const colors = parseColors(template.default_colors)
  let fonts = { heading_font: 'Montserrat', body_font: 'Inter' }
  try {
    fonts = JSON.parse(template.default_fonts) || fonts
  } catch { /* use defaults */ }

  // Parse placeholders to generate sample text
  let placeholders = ['title', 'content']
  try {
    placeholders = JSON.parse(template.placeholder_fields) || placeholders
  } catch { /* use defaults */ }

  editorCustom.value = {
    primaryColor: colors.primary || '#4C8BC2',
    secondaryColor: colors.secondary || '#FDD000',
    accentColor: colors.accent || '#FFFFFF',
    backgroundColor: colors.background || '#1A1A2E',
    headlineText: 'Dein Highschool-Abenteuer',
    subheadlineText: 'Starte jetzt mit TREFF Sprachreisen',
    bodyText: 'Erlebe das Abenteuer deines Lebens mit einem Highschool-Aufenthalt im Ausland.',
    ctaText: 'Jetzt bewerben',
    headingFont: fonts.heading_font || 'Montserrat',
    bodyFont: fonts.body_font || 'Inter',
  }

  showEditorModal.value = true

  // Update preview iframe after modal opens
  nextTick(() => {
    updatePreviewIframe()
  })
}

function closeEditor() {
  showEditorModal.value = false
  editorTemplate.value = null
}

function updatePreviewIframe() {
  const iframe = editorPreviewRef.value
  if (!iframe) return
  const doc = iframe.contentDocument || iframe.contentWindow?.document
  if (!doc) return
  doc.open()
  doc.write(editorPreviewHtml.value)
  doc.close()
}

// Watch for any customization change and update the iframe preview
watch(editorCustom, () => {
  nextTick(() => {
    updatePreviewIframe()
  })
}, { deep: true })

// Get platform dimensions for preview
function getPreviewDimensions(platformFormat) {
  const dims = {
    feed_square: { width: 1080, height: 1080 },
    feed_portrait: { width: 1080, height: 1350 },
    story: { width: 1080, height: 1920 },
    tiktok: { width: 1080, height: 1920 },
  }
  return dims[platformFormat] || dims.feed_square
}

function getPreviewScale(platformFormat) {
  const dims = getPreviewDimensions(platformFormat)
  // Scale to fit within ~400px wide preview area
  return Math.min(380 / dims.width, 500 / dims.height)
}

// Category definitions with German labels and colors
const categories = {
  laender_spotlight: { label: 'Laender-Spotlight', icon: '\u{1F30D}', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' },
  erfahrungsberichte: { label: 'Erfahrungsberichte', icon: '\u{1F4AC}', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300' },
  infografiken: { label: 'Infografiken', icon: '\u{1F4CA}', color: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' },
  fristen_cta: { label: 'Fristen & CTA', icon: '\u{23F0}', color: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' },
  tipps_tricks: { label: 'Tipps & Tricks', icon: '\u{1F4A1}', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' },
  faq: { label: 'FAQ', icon: '\u{2753}', color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300' },
  foto_posts: { label: 'Foto-Posts', icon: '\u{1F4F8}', color: 'bg-pink-100 text-pink-700 dark:bg-pink-900 dark:text-pink-300' },
  reel_tiktok_thumbnails: { label: 'Reel/TikTok', icon: '\u{1F3AC}', color: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300' },
  story_posts: { label: 'Story-Posts', icon: '\u{1F4F1}', color: 'bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300' },
}

// Platform format labels
const platformLabels = {
  feed_square: { label: '1:1 Feed', icon: '\u{2B1C}', dim: '1080x1080' },
  feed_portrait: { label: '4:5 Portrait', icon: '\u{1F4F1}', dim: '1080x1350' },
  story: { label: '9:16 Story', icon: '\u{1F4F2}', dim: '1080x1920' },
  tiktok: { label: '9:16 TikTok', icon: '\u{1F3B5}', dim: '1080x1920' },
}

// Country flags
const countryFlags = {
  usa: '\u{1F1FA}\u{1F1F8}',
  canada: '\u{1F1E8}\u{1F1E6}',
  australia: '\u{1F1E6}\u{1F1FA}',
  newzealand: '\u{1F1F3}\u{1F1FF}',
  ireland: '\u{1F1EE}\u{1F1EA}',
}

// Unique categories from templates
const availableCategories = computed(() => {
  const cats = [...new Set(templates.value.map(t => t.category))]
  return cats.sort()
})

// Unique platforms from templates
const availablePlatforms = computed(() => {
  const plats = [...new Set(templates.value.map(t => t.platform_format))]
  return plats.sort()
})

// Filtered templates
const filteredTemplates = computed(() => {
  let result = templates.value
  if (selectedCategory.value) {
    result = result.filter(t => t.category === selectedCategory.value)
  }
  if (selectedPlatform.value) {
    result = result.filter(t => t.platform_format === selectedPlatform.value)
  }
  return result
})

// Group templates by category for display
const groupedTemplates = computed(() => {
  const groups = {}
  for (const t of filteredTemplates.value) {
    if (!groups[t.category]) {
      groups[t.category] = []
    }
    groups[t.category].push(t)
  }
  return groups
})

// Template count per category (for filter badges)
const categoryCount = computed(() => {
  const counts = {}
  for (const t of templates.value) {
    counts[t.category] = (counts[t.category] || 0) + 1
  }
  return counts
})

// Validate create form
const canCreate = computed(() => {
  return newTemplate.value.name.trim().length > 0 &&
    newTemplate.value.category.length > 0 &&
    newTemplate.value.platform_format.length > 0 &&
    newTemplate.value.html_content.trim().length > 0 &&
    newTemplate.value.css_content.trim().length > 0
})

function getCategoryInfo(cat) {
  return categories[cat] || { label: cat, icon: '\u{1F4C4}', color: 'bg-gray-100 text-gray-700' }
}

function getPlatformInfo(platform) {
  return platformLabels[platform] || { label: platform, icon: '\u{1F4C4}', dim: '' }
}

function getCountryFlag(country) {
  return countryFlags[country] || ''
}

// Parse default_colors JSON safely
function parseColors(colorsStr) {
  try {
    return JSON.parse(colorsStr)
  } catch {
    return { primary: '#4C8BC2', secondary: '#FDD000', accent: '#FFFFFF', background: '#1A1A2E' }
  }
}

function clearFilters() {
  selectedCategory.value = ''
  selectedPlatform.value = ''
}

async function fetchTemplates() {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/api/templates')
    templates.value = res.data
  } catch (err) {
    console.error('Failed to load templates:', err)
    error.value = 'Templates konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function openCreateModal() {
  newTemplate.value = {
    name: '',
    category: '',
    platform_format: 'feed_square',
    slide_count: 1,
    html_content: '<div class="template">\n  <h1>{{title}}</h1>\n  <p>{{content}}</p>\n</div>',
    css_content: '.template {\n  padding: 40px;\n  font-family: Inter, sans-serif;\n  color: #FFFFFF;\n  background: linear-gradient(135deg, #1A1A2E 0%, #4C8BC2 100%);\n  min-height: 100%;\n}',
    placeholder_fields: '["title", "content"]',
  }
  createError.value = null
  createSuccess.value = false
  showCreateModal.value = true
}

function closeCreateModal() {
  showCreateModal.value = false
  createError.value = null
  createSuccess.value = false
}

async function createTemplate() {
  if (!canCreate.value) return

  creating.value = true
  createError.value = null
  createSuccess.value = false

  try {
    const payload = {
      name: newTemplate.value.name.trim(),
      category: newTemplate.value.category,
      platform_format: newTemplate.value.platform_format,
      slide_count: parseInt(newTemplate.value.slide_count) || 1,
      html_content: newTemplate.value.html_content.trim(),
      css_content: newTemplate.value.css_content.trim(),
      placeholder_fields: newTemplate.value.placeholder_fields.trim() || '["title", "content"]',
    }

    const res = await api.post('/api/templates', payload)

    // Add the new template to the list
    templates.value.push(res.data)
    createSuccess.value = true

    // Close modal after short delay so user sees success
    setTimeout(() => {
      closeCreateModal()
    }, 1200)
  } catch (err) {
    console.error('Failed to create template:', err)
    if (err.response?.data?.detail) {
      if (Array.isArray(err.response.data.detail)) {
        createError.value = err.response.data.detail.map(e => e.msg).join(', ')
      } else {
        createError.value = err.response.data.detail
      }
    } else {
      createError.value = 'Template konnte nicht erstellt werden. Bitte versuche es erneut.'
    }
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  fetchTemplates()
})
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <!-- Page Header -->
    <div class="mb-6 flex items-start justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Templates</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Waehle ein Template fuer deinen naechsten Post. Alle Templates sind fuer TREFF Sprachreisen optimiert.
        </p>
      </div>
      <button
        @click="openCreateModal"
        class="flex items-center gap-2 px-4 py-2.5 bg-treff-blue text-white text-sm font-medium rounded-lg hover:bg-blue-600 transition-colors shadow-sm whitespace-nowrap"
      >
        <span class="text-lg leading-none">+</span>
        Neues Template erstellen
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="space-y-6">
      <!-- Skeleton filter bar -->
      <div class="flex gap-3">
        <div v-for="i in 4" :key="i" class="h-10 w-28 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"></div>
      </div>
      <!-- Skeleton grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div v-for="i in 8" :key="i" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm animate-pulse">
          <div class="aspect-square bg-gray-200 dark:bg-gray-700 rounded-t-xl"></div>
          <div class="p-4 space-y-2">
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
      <p class="text-red-600 dark:text-red-400">{{ error }}</p>
      <button
        @click="fetchTemplates"
        class="mt-3 px-4 py-2 bg-red-100 dark:bg-red-800 text-red-700 dark:text-red-200 rounded-lg hover:bg-red-200 dark:hover:bg-red-700 transition-colors"
      >
        Erneut versuchen
      </button>
    </div>

    <!-- Content -->
    <div v-else class="space-y-6">
      <!-- Filter Bar -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
        <div class="flex flex-wrap items-center gap-3">
          <!-- Category Filter -->
          <div class="flex items-center gap-2">
            <label class="text-sm font-medium text-gray-600 dark:text-gray-400">Kategorie:</label>
            <select
              v-model="selectedCategory"
              class="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent"
            >
              <option value="">Alle Kategorien</option>
              <option v-for="cat in availableCategories" :key="cat" :value="cat">
                {{ getCategoryInfo(cat).icon }} {{ getCategoryInfo(cat).label }} ({{ categoryCount[cat] }})
              </option>
            </select>
          </div>

          <!-- Platform Filter -->
          <div class="flex items-center gap-2">
            <label class="text-sm font-medium text-gray-600 dark:text-gray-400">Format:</label>
            <select
              v-model="selectedPlatform"
              class="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent"
            >
              <option value="">Alle Formate</option>
              <option v-for="plat in availablePlatforms" :key="plat" :value="plat">
                {{ getPlatformInfo(plat).icon }} {{ getPlatformInfo(plat).label }}
              </option>
            </select>
          </div>

          <!-- Clear filters -->
          <button
            v-if="selectedCategory || selectedPlatform"
            @click="clearFilters"
            class="text-sm text-gray-500 dark:text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors flex items-center gap-1"
          >
            <span>&#10005;</span> Filter zuruecksetzen
          </button>

          <!-- Result count -->
          <div class="ml-auto text-sm text-gray-500 dark:text-gray-400">
            {{ filteredTemplates.length }} von {{ templates.length }} Templates
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="filteredTemplates.length === 0" class="text-center py-16">
        <div class="text-5xl mb-4">\u{1F4C4}</div>
        <p class="text-gray-500 dark:text-gray-400 font-medium text-lg">Keine Templates gefunden</p>
        <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">
          Versuche andere Filter oder setze sie zurueck.
        </p>
        <button
          @click="clearFilters"
          class="mt-4 px-4 py-2 bg-treff-blue text-white text-sm font-medium rounded-lg hover:bg-blue-600 transition-colors"
        >
          Filter zuruecksetzen
        </button>
      </div>

      <!-- Template Grid grouped by category -->
      <div v-for="(catTemplates, category) in groupedTemplates" :key="category" class="space-y-3">
        <!-- Category Header -->
        <div class="flex items-center gap-2">
          <span class="text-xl">{{ getCategoryInfo(category).icon }}</span>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ getCategoryInfo(category).label }}
          </h2>
          <span class="text-sm text-gray-400 dark:text-gray-500">({{ catTemplates.length }})</span>
        </div>

        <!-- Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <div
            v-for="template in catTemplates"
            :key="template.id"
            class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md hover:border-treff-blue/50 dark:hover:border-treff-blue/50 transition-all cursor-pointer group overflow-hidden"
            @click="openEditor(template)"
            data-testid="template-card"
          >
            <!-- Visual Thumbnail -->
            <div class="relative">
              <div
                class="w-full h-48 flex flex-col items-center justify-center p-4 relative overflow-hidden"
                :style="{
                  background: `linear-gradient(135deg, ${parseColors(template.default_colors).background || '#1A1A2E'} 0%, ${parseColors(template.default_colors).primary || '#4C8BC2'} 100%)`,
                }"
              >
                <!-- Template preview mockup -->
                <div class="absolute top-3 left-3">
                  <div
                    class="px-2 py-1 rounded text-[10px] font-bold tracking-wide"
                    :style="{ background: parseColors(template.default_colors).primary || '#4C8BC2', color: '#fff' }"
                  >
                    TREFF
                  </div>
                </div>

                <!-- Country flag badge -->
                <div v-if="template.is_country_themed && template.country" class="absolute top-3 right-3 text-2xl">
                  {{ getCountryFlag(template.country) }}
                </div>

                <!-- Slide count indicator -->
                <div v-if="template.slide_count > 1"
                  class="absolute top-3 bg-black/40 text-white text-xs px-2 py-1 rounded-full backdrop-blur-sm"
                  :class="template.is_country_themed && template.country ? 'right-12' : 'right-3'"
                >
                  {{ template.slide_count }} Slides
                </div>

                <!-- Custom badge for non-default templates -->
                <div v-if="!template.is_default" class="absolute bottom-3 right-3">
                  <span class="text-xs px-2 py-0.5 rounded-full bg-treff-blue/80 text-white backdrop-blur-sm">
                    Eigenes
                  </span>
                </div>

                <!-- Mockup content lines -->
                <div class="flex flex-col items-start gap-2 w-full px-3 mt-8">
                  <div
                    class="h-4 rounded-sm w-3/4"
                    :style="{ background: parseColors(template.default_colors).primary || '#4C8BC2' }"
                  ></div>
                  <div
                    class="h-3 rounded-sm w-1/2 opacity-70"
                    :style="{ background: parseColors(template.default_colors).secondary || '#FDD000' }"
                  ></div>
                  <div class="flex flex-col gap-1.5 w-full mt-1">
                    <div class="h-2 rounded-sm w-full bg-white/20"></div>
                    <div class="h-2 rounded-sm w-5/6 bg-white/15"></div>
                    <div class="h-2 rounded-sm w-4/6 bg-white/10"></div>
                  </div>
                </div>

                <!-- CTA mockup -->
                <div class="mt-auto mb-2 self-start ml-3">
                  <div
                    class="px-3 py-1 rounded text-[10px] font-bold"
                    :style="{
                      background: parseColors(template.default_colors).secondary || '#FDD000',
                      color: parseColors(template.default_colors).background || '#1A1A2E',
                    }"
                  >
                    CTA
                  </div>
                </div>

                <!-- Hover overlay -->
                <div class="absolute inset-0 bg-treff-blue/0 group-hover:bg-treff-blue/10 transition-colors flex items-center justify-center">
                  <div class="opacity-0 group-hover:opacity-100 transition-opacity bg-white dark:bg-gray-900 text-treff-blue font-medium text-sm px-4 py-2 rounded-lg shadow-lg">
                    Vorschau
                  </div>
                </div>
              </div>
            </div>

            <!-- Template Info -->
            <div class="p-4">
              <h3 class="font-semibold text-gray-900 dark:text-white text-sm truncate group-hover:text-treff-blue transition-colors">
                {{ template.name }}
              </h3>
              <div class="flex items-center gap-2 mt-2 flex-wrap">
                <!-- Platform badge -->
                <span class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                  {{ getPlatformInfo(template.platform_format).icon }}
                  {{ getPlatformInfo(template.platform_format).label }}
                </span>
                <!-- Country badge if themed -->
                <span
                  v-if="template.is_country_themed && template.country"
                  class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300"
                >
                  {{ getCountryFlag(template.country) }}
                  {{ template.country.charAt(0).toUpperCase() + template.country.slice(1) }}
                </span>
                <!-- Default badge -->
                <span
                  v-if="template.is_default"
                  class="text-xs px-2 py-0.5 rounded-full bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-300"
                >
                  Standard
                </span>
                <!-- Custom badge -->
                <span
                  v-if="!template.is_default"
                  class="text-xs px-2 py-0.5 rounded-full bg-treff-blue/10 text-treff-blue dark:bg-treff-blue/20"
                >
                  Eigenes
                </span>
              </div>
              <!-- Slide count info -->
              <p class="text-xs text-gray-400 dark:text-gray-500 mt-2">
                {{ template.slide_count === 1 ? 'Einzelbild' : `${template.slide_count} Slides (Carousel)` }}
                &middot; {{ getPlatformInfo(template.platform_format).dim }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Template Modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      @click.self="closeCreateModal"
    >
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeCreateModal"></div>

      <!-- Modal Content -->
      <div class="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <!-- Modal Header -->
        <div class="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 rounded-t-2xl z-10">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-bold text-gray-900 dark:text-white">Neues Template erstellen</h2>
            <button
              @click="closeCreateModal"
              class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-1"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Modal Body -->
        <div class="px-6 py-5 space-y-5">
          <!-- Success Message -->
          <div v-if="createSuccess" class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 text-center">
            <p class="text-green-700 dark:text-green-300 font-medium">Template erfolgreich erstellt!</p>
          </div>

          <!-- Error Message -->
          <div v-if="createError" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
            <p class="text-red-600 dark:text-red-400 text-sm">{{ createError }}</p>
          </div>

          <!-- Template Name -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Template-Name <span class="text-red-500">*</span>
            </label>
            <input
              v-model="newTemplate.name"
              type="text"
              placeholder="z.B. Mein Custom Template"
              class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-treff-blue focus:border-transparent text-sm"
            />
          </div>

          <!-- Category + Platform Row -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <!-- Category -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Kategorie <span class="text-red-500">*</span>
              </label>
              <select
                v-model="newTemplate.category"
                class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent text-sm"
              >
                <option value="" disabled>Kategorie waehlen...</option>
                <option v-for="(info, key) in categories" :key="key" :value="key">
                  {{ info.icon }} {{ info.label }}
                </option>
              </select>
            </div>

            <!-- Platform Format -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Plattform-Format <span class="text-red-500">*</span>
              </label>
              <select
                v-model="newTemplate.platform_format"
                class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent text-sm"
              >
                <option v-for="(info, key) in platformLabels" :key="key" :value="key">
                  {{ info.icon }} {{ info.label }} ({{ info.dim }})
                </option>
              </select>
            </div>
          </div>

          <!-- Slide Count -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Anzahl Slides
            </label>
            <input
              v-model.number="newTemplate.slide_count"
              type="number"
              min="1"
              max="10"
              class="w-32 px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent text-sm"
            />
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">1 = Einzelbild, 2+ = Carousel</p>
          </div>

          <!-- HTML Content -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              HTML-Inhalt <span class="text-red-500">*</span>
            </label>
            <textarea
              v-model="newTemplate.html_content"
              rows="6"
              placeholder="<div class='template'>...</div>"
              class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-treff-blue focus:border-transparent text-sm font-mono"
            ></textarea>
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Verwende {{feldname}} als Platzhalter fuer dynamische Inhalte.</p>
          </div>

          <!-- CSS Content -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              CSS-Styling <span class="text-red-500">*</span>
            </label>
            <textarea
              v-model="newTemplate.css_content"
              rows="6"
              placeholder=".template { padding: 40px; }"
              class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-treff-blue focus:border-transparent text-sm font-mono"
            ></textarea>
          </div>

          <!-- Placeholder Fields -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Platzhalter-Felder (JSON)
            </label>
            <input
              v-model="newTemplate.placeholder_fields"
              type="text"
              placeholder='["title", "content", "cta_text"]'
              class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-treff-blue focus:border-transparent text-sm font-mono"
            />
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">JSON-Array der Platzhalter-Namen, die im HTML verwendet werden.</p>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-4 rounded-b-2xl flex items-center justify-end gap-3">
          <button
            @click="closeCreateModal"
            class="px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
          >
            Abbrechen
          </button>
          <button
            @click="createTemplate"
            :disabled="!canCreate || creating"
            class="px-6 py-2.5 text-sm font-medium text-white bg-treff-blue hover:bg-blue-600 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <svg v-if="creating" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ creating ? 'Wird erstellt...' : 'Template erstellen' }}
          </button>
        </div>
      </div>
    </div>

    <!-- =============================================
         Template Editor Modal with Live Preview
         ============================================= -->
    <div
      v-if="showEditorModal && editorTemplate"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      data-testid="template-editor-modal"
    >
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="closeEditor"></div>

      <!-- Modal Content - Full Width -->
      <div class="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-6xl max-h-[92vh] overflow-hidden flex flex-col">
        <!-- Modal Header -->
        <div class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between flex-shrink-0">
          <div>
            <h2 class="text-xl font-bold text-gray-900 dark:text-white">Template bearbeiten</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
              {{ editorTemplate.name }} &middot;
              {{ getCategoryInfo(editorTemplate.category).icon }} {{ getCategoryInfo(editorTemplate.category).label }} &middot;
              {{ getPlatformInfo(editorTemplate.platform_format).label }}
            </p>
          </div>
          <button
            @click="closeEditor"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Two-Column Layout: Controls + Preview -->
        <div class="flex flex-1 overflow-hidden">
          <!-- Left Panel: Customization Controls -->
          <div class="w-[420px] flex-shrink-0 border-r border-gray-200 dark:border-gray-700 overflow-y-auto p-5 space-y-5" data-testid="editor-controls">

            <!-- Section: Colors -->
            <div class="space-y-3">
              <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider flex items-center gap-2">
                <span class="w-5 h-5 rounded bg-gradient-to-br from-blue-500 to-yellow-400"></span>
                Farben
              </h3>

              <!-- Primary Color -->
              <div class="flex items-center gap-3">
                <label class="text-sm text-gray-600 dark:text-gray-400 w-28 flex-shrink-0">Primaerfarbe</label>
                <input
                  v-model="editorCustom.primaryColor"
                  type="color"
                  class="w-10 h-10 rounded-lg border border-gray-300 dark:border-gray-600 cursor-pointer"
                  data-testid="editor-primary-color"
                />
                <input
                  v-model="editorCustom.primaryColor"
                  type="text"
                  class="flex-1 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono"
                  data-testid="editor-primary-color-text"
                />
              </div>

              <!-- Secondary Color -->
              <div class="flex items-center gap-3">
                <label class="text-sm text-gray-600 dark:text-gray-400 w-28 flex-shrink-0">Sekundaerfarbe</label>
                <input
                  v-model="editorCustom.secondaryColor"
                  type="color"
                  class="w-10 h-10 rounded-lg border border-gray-300 dark:border-gray-600 cursor-pointer"
                  data-testid="editor-secondary-color"
                />
                <input
                  v-model="editorCustom.secondaryColor"
                  type="text"
                  class="flex-1 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono"
                />
              </div>

              <!-- Background Color -->
              <div class="flex items-center gap-3">
                <label class="text-sm text-gray-600 dark:text-gray-400 w-28 flex-shrink-0">Hintergrund</label>
                <input
                  v-model="editorCustom.backgroundColor"
                  type="color"
                  class="w-10 h-10 rounded-lg border border-gray-300 dark:border-gray-600 cursor-pointer"
                  data-testid="editor-bg-color"
                />
                <input
                  v-model="editorCustom.backgroundColor"
                  type="text"
                  class="flex-1 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono"
                />
              </div>
            </div>

            <hr class="border-gray-200 dark:border-gray-700" />

            <!-- Section: Typography -->
            <div class="space-y-3">
              <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider flex items-center gap-2">
                <span class="text-base">Aa</span>
                Schriftarten
              </h3>

              <!-- Heading Font -->
              <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1">Ueberschrift-Font</label>
                <select
                  v-model="editorCustom.headingFont"
                  class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue"
                  data-testid="editor-heading-font"
                  :style="{ fontFamily: editorCustom.headingFont }"
                >
                  <option v-for="font in availableFonts" :key="font.value" :value="font.value" :style="{ fontFamily: font.value }">
                    {{ font.label }}
                  </option>
                </select>
              </div>

              <!-- Body Font -->
              <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1">Fliesstext-Font</label>
                <select
                  v-model="editorCustom.bodyFont"
                  class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue"
                  data-testid="editor-body-font"
                  :style="{ fontFamily: editorCustom.bodyFont }"
                >
                  <option v-for="font in availableFonts" :key="font.value" :value="font.value" :style="{ fontFamily: font.value }">
                    {{ font.label }}
                  </option>
                </select>
              </div>
            </div>

            <hr class="border-gray-200 dark:border-gray-700" />

            <!-- Section: Content / Text -->
            <div class="space-y-3">
              <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider flex items-center gap-2">
                <span class="text-base">T</span>
                Textinhalte
              </h3>

              <!-- Headline -->
              <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1">Ueberschrift</label>
                <input
                  v-model="editorCustom.headlineText"
                  type="text"
                  class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue"
                  data-testid="editor-headline-text"
                  placeholder="Ueberschrift eingeben..."
                />
              </div>

              <!-- Subheadline -->
              <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1">Unterueberschrift</label>
                <input
                  v-model="editorCustom.subheadlineText"
                  type="text"
                  class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue"
                  data-testid="editor-subheadline-text"
                  placeholder="Unterueberschrift eingeben..."
                />
              </div>

              <!-- Body Text -->
              <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1">Fliesstext</label>
                <textarea
                  v-model="editorCustom.bodyText"
                  rows="3"
                  class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue"
                  data-testid="editor-body-text"
                  placeholder="Text eingeben..."
                ></textarea>
              </div>

              <!-- CTA Text -->
              <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1">Call-to-Action</label>
                <input
                  v-model="editorCustom.ctaText"
                  type="text"
                  class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue"
                  data-testid="editor-cta-text"
                  placeholder="CTA-Text eingeben..."
                />
              </div>
            </div>

            <!-- Info hint -->
            <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
              <p class="text-xs text-blue-700 dark:text-blue-300">
                Alle Aenderungen werden sofort in der Live-Vorschau angezeigt.
                Die Vorschau aktualisiert sich in Echtzeit.
              </p>
            </div>
          </div>

          <!-- Right Panel: Live Preview -->
          <div class="flex-1 bg-gray-100 dark:bg-gray-900 overflow-auto flex flex-col items-center justify-start p-6" data-testid="editor-preview-panel">
            <div class="mb-3 text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2">
              <span class="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              Live-Vorschau &middot; {{ getPlatformInfo(editorTemplate.platform_format).label }} ({{ getPlatformInfo(editorTemplate.platform_format).dim }})
            </div>

            <!-- Preview Container with correct aspect ratio -->
            <div
              class="bg-white shadow-xl rounded-lg overflow-hidden"
              :style="{
                width: getPreviewDimensions(editorTemplate.platform_format).width * getPreviewScale(editorTemplate.platform_format) + 'px',
                height: getPreviewDimensions(editorTemplate.platform_format).height * getPreviewScale(editorTemplate.platform_format) + 'px',
              }"
              data-testid="editor-preview-container"
            >
              <iframe
                ref="editorPreviewRef"
                :style="{
                  width: getPreviewDimensions(editorTemplate.platform_format).width + 'px',
                  height: getPreviewDimensions(editorTemplate.platform_format).height + 'px',
                  transform: `scale(${getPreviewScale(editorTemplate.platform_format)})`,
                  transformOrigin: 'top left',
                  border: 'none',
                }"
                sandbox="allow-same-origin"
                data-testid="editor-preview-iframe"
              ></iframe>
            </div>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-3 flex items-center justify-between flex-shrink-0">
          <p class="text-xs text-gray-400 dark:text-gray-500">
            Vorschau aktualisiert sich automatisch bei jeder Aenderung
          </p>
          <button
            @click="closeEditor"
            class="px-5 py-2.5 text-sm font-medium text-white bg-treff-blue hover:bg-blue-600 rounded-lg transition-colors"
          >
            Schliessen
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
