<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick, inject } from 'vue'
import api from '@/utils/api'
import TourSystem from '@/components/common/TourSystem.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import SkeletonBase from '@/components/common/SkeletonBase.vue'
import SkeletonGrid from '@/components/common/SkeletonGrid.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const tourRef = ref(null)

// Inject library-level search
const librarySearch = inject('librarySearch', ref(''))
const libraryTemplateCount = inject('libraryTemplateCount', ref(null))

const loading = ref(true)
const error = ref(null)
const templates = ref([])
const selectedCategory = ref('')
const selectedPlatform = ref('')
const selectedOwnership = ref('')  // '' = Alle, 'system' = System-Templates, 'custom' = Meine Templates

// Duplicate template state
const duplicating = ref(false)

// Delete template state
const showDeleteModal = ref(false)
const deletingTemplate = ref(null)
const deleting = ref(false)
const deleteError = ref(null)

// Create template modal state
const showCreateModal = ref(false)
const creating = ref(false)
const createError = ref(null)
const createSuccess = ref(false)
const createSubmitted = ref(false)
const createFieldErrors = ref({
  name: '',
  category: '',
  html_content: '',
  css_content: '',
})
const newTemplate = ref({
  name: '',
  category: '',
  platform_format: 'feed_square',
  slide_count: 1,
  html_content: '<div class="template">\n  <h1>{{title}}</h1>\n  <p>{{content}}</p>\n</div>',
  css_content: '.template {\n  padding: 40px;\n  font-family: Inter, sans-serif;\n  color: #FFFFFF;\n  background: linear-gradient(135deg, #1A1A2E 0%, #3B7AB1 100%);\n  min-height: 100%;\n}',
  placeholder_fields: '["title", "content"]',
})

// Placeholder insertion toolbar for template HTML editor
const showPlaceholderDropdown = ref(false)
const htmlTextareaRef = ref(null)

const AVAILABLE_PLACEHOLDERS = [
  { name: 'headline', label: 'Ueberschrift', icon: 'document-text' },
  { name: 'subheadline', label: 'Unterueberschrift', icon: 'clipboard-list' },
  { name: 'body_text', label: 'Fliesstext', icon: 'document-text' },
  { name: 'cta_text', label: 'CTA-Text', icon: 'rocket' },
  { name: 'name', label: 'Name', icon: 'user' },
  { name: 'land', label: 'Land', icon: 'globe' },
  { name: 'stadt', label: 'Stadt', icon: 'building-office' },
  { name: 'datum', label: 'Datum', icon: 'calendar' },
  { name: 'quote', label: 'Zitat', icon: 'chat-bubble' },
  { name: 'quote_text', label: 'Zitat-Text', icon: 'chat-bubble' },
  { name: 'quote_author', label: 'Zitat-Autor', icon: 'pencil' },
  { name: 'zahl', label: 'Zahl / Statistik', icon: 'hashtag' },
  { name: 'image', label: 'Bild-Platzhalter', icon: 'photo' },
]

function insertPlaceholder(placeholderName) {
  const placeholder = `{{${placeholderName}}}`
  const textarea = htmlTextareaRef.value
  if (textarea) {
    const start = textarea.selectionStart || 0
    const end = textarea.selectionEnd || 0
    const content = newTemplate.value.html_content
    newTemplate.value.html_content = content.substring(0, start) + placeholder + content.substring(end)
    // Re-focus and position cursor after the inserted placeholder
    nextTick(() => {
      textarea.focus()
      const newPos = start + placeholder.length
      textarea.setSelectionRange(newPos, newPos)
    })
  } else {
    // Fallback: append at end
    newTemplate.value.html_content += placeholder
  }
  // Auto-update placeholder_fields JSON if this placeholder isn't already listed
  try {
    let fields = JSON.parse(newTemplate.value.placeholder_fields || '[]')
    if (!Array.isArray(fields)) fields = []
    if (!fields.includes(placeholderName)) {
      fields.push(placeholderName)
      newTemplate.value.placeholder_fields = JSON.stringify(fields)
    }
  } catch {
    newTemplate.value.placeholder_fields = JSON.stringify([placeholderName])
  }
  showPlaceholderDropdown.value = false
}

// =============================================
// Template Editor with Live Preview
// =============================================
const showEditorModal = ref(false)
const editorTemplate = ref(null)
const editorPreviewRef = ref(null)
const editorIsEditMode = ref(false)
const editorSaving = ref(false)
const editorSaveError = ref(null)
const editorSaveSuccess = ref(false)
const editorTemplateName = ref('')

// Customization state - these drive the live preview
const editorCustom = ref({
  primaryColor: '#3B7AB1',
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

// Escape text for safe insertion into HTML (prevents XSS via placeholder injection)
function escapeHtml(text) {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
}

// Computed: rendered preview HTML that updates reactively
const editorPreviewHtml = computed(() => {
  if (!editorTemplate.value) return ''

  const c = editorCustom.value
  let html = editorTemplate.value.html_content || ''
  let css = editorTemplate.value.css_content || ''

  // Replace placeholders in HTML with escaped user-entered text (XSS prevention)
  html = html.replace(/\{\{title\}\}/g, escapeHtml(c.headlineText))
  html = html.replace(/\{\{headline\}\}/g, escapeHtml(c.headlineText))
  html = html.replace(/\{\{subheadline\}\}/g, escapeHtml(c.subheadlineText))
  html = html.replace(/\{\{content\}\}/g, escapeHtml(c.bodyText))
  html = html.replace(/\{\{body_text\}\}/g, escapeHtml(c.bodyText))
  html = html.replace(/\{\{cta_text\}\}/g, escapeHtml(c.ctaText))
  html = html.replace(/\{\{cta\}\}/g, escapeHtml(c.ctaText))
  html = html.replace(/\{\{quote_text\}\}/g, escapeHtml(c.bodyText))
  html = html.replace(/\{\{quote_author\}\}/g, escapeHtml('Max M., Austauschschueler'))
  html = html.replace(/\{\{bullet_points\}\}/g, escapeHtml('Punkt 1, Punkt 2, Punkt 3'))
  html = html.replace(/\{\{previously_text\}\}/g, escapeHtml('Bisher bei Jonathan: Nach der Ankunft in Seattle hat er seine Gastfamilie kennengelernt...'))
  html = html.replace(/\{\{cliffhanger_text\}\}/g, escapeHtml('Aber was Jonathan am naechsten Tag erlebt, haette niemand erwartet...'))
  html = html.replace(/\{\{next_episode_hint\}\}/g, escapeHtml('Naechste Episode: Jonathan entdeckt eine neue Seite von Amerika!'))
  html = html.replace(/\{\{episode_number\}\}/g, escapeHtml('3'))
  html = html.replace(/\{\{episode_title\}\}/g, escapeHtml('Der erste Schneetag'))
  html = html.replace(/\{\{total_episodes\}\}/g, escapeHtml('8'))
  html = html.replace(/\{\{student_name\}\}/g, escapeHtml('Jonathan'))
  html = html.replace(/\{\{student_name_initial\}\}/g, escapeHtml('J'))
  html = html.replace(/\{\{arc_title\}\}/g, escapeHtml('Mein Jahr in Seattle'))
  html = html.replace(/\{\{student_photo\}\}/g, escapeHtml('J'))
  html = html.replace(/\{\{episode_preview\}\}/g, escapeHtml('Wie es weitergeht...'))
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

function openEditor(template, editMode = false) {
  editorTemplate.value = { ...template }
  editorIsEditMode.value = editMode && !template.is_default
  editorSaving.value = false
  editorSaveError.value = null
  editorSaveSuccess.value = false
  editorTemplateName.value = template.name

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
    primaryColor: colors.primary || '#3B7AB1',
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

async function saveTemplateEdits() {
  if (!editorTemplate.value || !editorIsEditMode.value) return

  editorSaving.value = true
  editorSaveError.value = null
  editorSaveSuccess.value = false

  try {
    const c = editorCustom.value
    const payload = {
      name: editorTemplateName.value.trim(),
      default_colors: JSON.stringify({
        primary: c.primaryColor,
        secondary: c.secondaryColor,
        accent: c.accentColor,
        background: c.backgroundColor,
      }),
      default_fonts: JSON.stringify({
        heading_font: c.headingFont,
        body_font: c.bodyFont,
      }),
    }

    const res = await api.put(`/api/templates/${editorTemplate.value.id}`, payload)

    // Update the template in the local list
    const idx = templates.value.findIndex(t => t.id === editorTemplate.value.id)
    if (idx !== -1) {
      templates.value[idx] = res.data
    }

    // Update editorTemplate to reflect saved state
    editorTemplate.value = { ...res.data }
    editorSaveSuccess.value = true

    // Clear success message after delay
    setTimeout(() => {
      editorSaveSuccess.value = false
    }, 3000)
  } catch (err) {
    console.error('Failed to save template:', err)
    if (err.response?.data?.detail) {
      editorSaveError.value = typeof err.response.data.detail === 'string'
        ? err.response.data.detail
        : 'Fehler beim Speichern des Templates.'
    } else {
      editorSaveError.value = 'Template konnte nicht gespeichert werden. Bitte versuche es erneut.'
    }
  } finally {
    editorSaving.value = false
  }
}

// Debounce timer for preview updates - declared early so closeEditor() can access it
let previewUpdateTimer = null

function closeEditor() {
  // Clear any pending debounced preview update
  if (previewUpdateTimer) {
    clearTimeout(previewUpdateTimer)
    previewUpdateTimer = null
  }
  // Explicitly clean up iframe document to prevent memory leaks
  // when rapidly switching between templates
  const iframe = editorPreviewRef.value
  if (iframe) {
    const doc = iframe.contentDocument || iframe.contentWindow?.document
    if (doc) {
      doc.open()
      doc.write('')
      doc.close()
    }
  }
  showEditorModal.value = false
  editorTemplate.value = null
}

function resetToDefaults() {
  editorCustom.value = {
    ...editorCustom.value,
    primaryColor: '#3B7AB1',
    secondaryColor: '#FDD000',
    accentColor: '#FFFFFF',
    backgroundColor: '#1A1A2E',
    headingFont: 'Montserrat',
    bodyFont: 'Inter',
  }
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

// Debounced preview update to prevent memory accumulation from rapid doc.write() calls
function debouncedPreviewUpdate() {
  if (previewUpdateTimer) {
    clearTimeout(previewUpdateTimer)
  }
  previewUpdateTimer = setTimeout(() => {
    previewUpdateTimer = null
    nextTick(() => {
      updatePreviewIframe()
    })
  }, 50) // 50ms debounce - responsive but prevents excessive rewrites
}

// Watch for any customization change and update the iframe preview
watch(editorCustom, () => {
  debouncedPreviewUpdate()
}, { deep: true })

// Clean up debounce timer on component unmount to prevent memory leaks
onUnmounted(() => {
  if (previewUpdateTimer) {
    clearTimeout(previewUpdateTimer)
    previewUpdateTimer = null
  }
})

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
  laender_spotlight: { label: 'Laender-Spotlight', icon: 'globe', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' },
  erfahrungsberichte: { label: 'Erfahrungsberichte', icon: 'chat-bubble', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300' },
  infografiken: { label: 'Infografiken', icon: 'chart-bar', color: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' },
  fristen_cta: { label: 'Fristen & CTA', icon: 'clock', color: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' },
  tipps_tricks: { label: 'Tipps & Tricks', icon: 'light-bulb', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' },
  faq: { label: 'FAQ', icon: 'question-mark-circle', color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300' },
  foto_posts: { label: 'Foto-Posts', icon: 'camera', color: 'bg-pink-100 text-pink-700 dark:bg-pink-900 dark:text-pink-300' },
  reel_tiktok_thumbnails: { label: 'Reel/TikTok', icon: 'film', color: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300' },
  story_posts: { label: 'Story-Posts', icon: 'device-mobile', color: 'bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300' },
  story_teaser: { label: 'Story-Teaser', icon: 'arrow-right', color: 'bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900 dark:text-fuchsia-300' },
  story_series: { label: 'Story-Serien', icon: 'book-open', color: 'bg-violet-100 text-violet-700 dark:bg-violet-900 dark:text-violet-300' },
}

// Platform format labels
const platformLabels = {
  feed_square: { label: '1:1 Feed', icon: 'square-2-stack', dim: '1080x1080' },
  feed_portrait: { label: '4:5 Portrait', icon: 'device-mobile', dim: '1080x1350' },
  story: { label: '9:16 Story', icon: 'device-mobile', dim: '1080x1920' },
  tiktok: { label: '9:16 TikTok', icon: 'musical-note', dim: '1080x1920' },
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
  if (selectedOwnership.value === 'system') {
    result = result.filter(t => t.is_default)
  } else if (selectedOwnership.value === 'custom') {
    result = result.filter(t => !t.is_default)
  }
  // Library-level search filter
  const query = librarySearch.value?.toLowerCase?.() || ''
  if (query) {
    result = result.filter(t =>
      (t.name || '').toLowerCase().includes(query) ||
      (t.category || '').toLowerCase().includes(query) ||
      (t.description || '').toLowerCase().includes(query)
    )
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
  return categories[cat] || { label: cat, icon: 'document-text', color: 'bg-gray-100 text-gray-700' }
}

function getPlatformInfo(platform) {
  return platformLabels[platform] || { label: platform, icon: 'document-text', dim: '' }
}

function getCountryFlag(country) {
  return countryFlags[country] || ''
}

// Parse default_colors JSON safely
function parseColors(colorsStr) {
  try {
    return JSON.parse(colorsStr)
  } catch {
    return { primary: '#3B7AB1', secondary: '#FDD000', accent: '#FFFFFF', background: '#1A1A2E' }
  }
}

function clearFilters() {
  selectedCategory.value = ''
  selectedPlatform.value = ''
  selectedOwnership.value = ''
}

// Duplicate a template via API and add the copy to local list
async function duplicateTemplate(template) {
  duplicating.value = true
  try {
    const res = await api.post(`/api/templates/${template.id}/duplicate`)
    templates.value.push(res.data)
    // Sort templates so the copy appears next to the original
    templates.value.sort((a, b) => {
      if (a.category !== b.category) return a.category.localeCompare(b.category)
      return a.name.localeCompare(b.name)
    })
  } catch (err) {
    console.error('Failed to duplicate template:', err)
  } finally {
    duplicating.value = false
  }
}

// Duplicate from editor modal ("Als Kopie speichern")
async function duplicateFromEditor() {
  if (!editorTemplate.value) return
  duplicating.value = true
  try {
    const res = await api.post(`/api/templates/${editorTemplate.value.id}/duplicate`)
    templates.value.push(res.data)
    templates.value.sort((a, b) => {
      if (a.category !== b.category) return a.category.localeCompare(b.category)
      return a.name.localeCompare(b.name)
    })
    // Switch editor to the duplicate (now editable)
    closeEditor()
    openEditor(res.data, true)
  } catch (err) {
    console.error('Failed to duplicate from editor:', err)
    editorSaveError.value = 'Kopie konnte nicht erstellt werden. Bitte versuche es erneut.'
  } finally {
    duplicating.value = false
  }
}

async function fetchTemplates() {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/api/templates')
    templates.value = res.data
    libraryTemplateCount.value = res.data.length
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
    css_content: '.template {\n  padding: 40px;\n  font-family: Inter, sans-serif;\n  color: #FFFFFF;\n  background: linear-gradient(135deg, #1A1A2E 0%, #3B7AB1 100%);\n  min-height: 100%;\n}',
    placeholder_fields: '["title", "content"]',
  }
  createError.value = null
  createSuccess.value = false
  createSubmitted.value = false
  createFieldErrors.value = { name: '', category: '', html_content: '', css_content: '' }
  showCreateModal.value = true
}

function closeCreateModal() {
  showCreateModal.value = false
  createError.value = null
  createSuccess.value = false
}

function validateCreateForm() {
  let valid = true
  createFieldErrors.value = { name: '', category: '', html_content: '', css_content: '' }

  if (!newTemplate.value.name.trim()) {
    createFieldErrors.value.name = 'Template-Name ist erforderlich'
    valid = false
  }
  if (!newTemplate.value.category) {
    createFieldErrors.value.category = 'Kategorie ist erforderlich'
    valid = false
  }
  if (!newTemplate.value.html_content.trim()) {
    createFieldErrors.value.html_content = 'HTML-Inhalt ist erforderlich'
    valid = false
  }
  if (!newTemplate.value.css_content.trim()) {
    createFieldErrors.value.css_content = 'CSS-Styling ist erforderlich'
    valid = false
  }

  return valid
}

async function createTemplate() {
  createSubmitted.value = true

  if (!validateCreateForm()) return

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

// =============================================
// Delete Template
// =============================================
function openDeleteModal(template) {
  deletingTemplate.value = template
  deleteError.value = null
  showDeleteModal.value = true
}

function closeDeleteModal() {
  showDeleteModal.value = false
  deletingTemplate.value = null
  deleteError.value = null
}

async function confirmDeleteTemplate() {
  if (!deletingTemplate.value) return

  deleting.value = true
  deleteError.value = null

  try {
    await api.delete(`/api/templates/${deletingTemplate.value.id}`)

    // Remove the template from the local list
    templates.value = templates.value.filter(t => t.id !== deletingTemplate.value.id)

    closeDeleteModal()
  } catch (err) {
    console.error('Failed to delete template:', err)
    if (err.response?.data?.detail) {
      deleteError.value = typeof err.response.data.detail === 'string'
        ? err.response.data.detail
        : 'Fehler beim Loeschen des Templates.'
    } else {
      deleteError.value = 'Template konnte nicht geloescht werden. Bitte versuche es erneut.'
    }
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  fetchTemplates()
})
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <!-- Page Header -->
    <div class="mb-6 flex items-start justify-between" data-tour="tpl-header">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Templates</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Waehle ein Template fuer deinen naechsten Post. Alle Templates sind fuer TREFF Sprachreisen optimiert.
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="tourRef?.startTour()"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          title="Seiten-Tour starten"
        >
          &#10067; Tour
        </button>
        <button
          @click="openCreateModal"
          class="flex items-center gap-2 px-4 py-2.5 bg-treff-blue text-white text-sm font-medium rounded-lg hover:bg-blue-600 transition-colors shadow-sm whitespace-nowrap"
          data-tour="tpl-create-btn"
        >
          <span class="text-lg leading-none">+</span>
          Neues Template erstellen
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="space-y-6">
      <!-- Skeleton filter bar -->
      <div class="flex gap-3">
        <SkeletonBase v-for="i in 4" :key="i" width="7rem" height="2.5rem" rounded="lg" />
      </div>
      <!-- Skeleton grid -->
      <SkeletonGrid
        :count="8"
        image-aspect="square"
        :text-lines="1"
        :show-actions="true"
      />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center" role="alert">
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
      <BaseCard padding="md" :header-divider="false" data-tour="tpl-filters">
        <div class="flex flex-wrap items-center gap-3">
          <!-- Category Filter -->
          <div class="flex items-center gap-2">
            <label class="text-sm font-medium text-gray-600 dark:text-gray-400">Kategorie:</label>
            <select
              v-model="selectedCategory"
              aria-label="Kategorie filtern"
              class="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent"
            >
              <option value="">Alle Kategorien</option>
              <option v-for="cat in availableCategories" :key="cat" :value="cat">
                {{ getCategoryInfo(cat).label }} ({{ categoryCount[cat] }})
              </option>
            </select>
          </div>

          <!-- Platform Filter -->
          <div class="flex items-center gap-2">
            <label class="text-sm font-medium text-gray-600 dark:text-gray-400">Format:</label>
            <select
              v-model="selectedPlatform"
              aria-label="Format filtern"
              class="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent"
            >
              <option value="">Alle Formate</option>
              <option v-for="plat in availablePlatforms" :key="plat" :value="plat">
                {{ getPlatformInfo(plat).label }}
              </option>
            </select>
          </div>

          <!-- Ownership Filter: Alle / System / Meine -->
          <div class="flex items-center gap-2">
            <label class="text-sm font-medium text-gray-600 dark:text-gray-400">Typ:</label>
            <select
              v-model="selectedOwnership"
              aria-label="Template-Typ filtern"
              data-testid="ownership-filter"
              class="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent"
            >
              <option value="">Alle Templates</option>
              <option value="system">System-Templates</option>
              <option value="custom">Meine Templates</option>
            </select>
          </div>

          <!-- Clear filters -->
          <button
            v-if="selectedCategory || selectedPlatform || selectedOwnership"
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
      </BaseCard>

      <!-- Empty state -->
      <EmptyState
        v-if="filteredTemplates.length === 0 && templates.length === 0"
        svgIcon="squares-2x2"
        title="Keine Templates vorhanden"
        description="Templates sind die Basis fuer deine Posts. Erstelle oder importiere Vorlagen fuer schnellere Post-Erstellung."
        actionLabel="Post erstellen"
        actionTo="/create/quick"
      />
      <EmptyState
        v-else-if="filteredTemplates.length === 0"
        svgIcon="magnifying-glass"
        title="Keine Templates gefunden"
        description="Keine Templates passen zu deinen aktuellen Filtern. Versuche andere Filter oder setze sie zurueck."
        actionLabel="Filter zuruecksetzen"
        @action="clearFilters"
      />

      <!-- Template Grid grouped by category -->
      <div v-for="(catTemplates, category) in groupedTemplates" :key="category" class="space-y-3" data-tour="tpl-grid">
        <!-- Category Header -->
        <div class="flex items-center gap-2">
          <AppIcon :name="getCategoryInfo(category).icon" class="w-6 h-6 inline-block" />
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ getCategoryInfo(category).label }}
          </h2>
          <span class="text-sm text-gray-400 dark:text-gray-500">({{ catTemplates.length }})</span>
        </div>

        <!-- Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <BaseCard
            v-for="template in catTemplates"
            :key="template.id"
            hoverable
            clickable
            padding="none"
            :header-divider="false"
            class="stagger-item group relative"
            @click="openEditor(template)"
            data-testid="template-card"
          >
            <!-- Action buttons - Duplicate for ALL, Edit/Delete for custom only -->
            <div class="absolute top-3 right-3 z-10 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-all">
              <!-- Duplicate button (all templates) -->
              <button
                @click.stop="duplicateTemplate(template)"
                :disabled="duplicating"
                class="p-2 bg-white/90 dark:bg-gray-800/90 rounded-lg shadow-md hover:bg-green-500 hover:text-white text-gray-600 dark:text-gray-300 transition-all disabled:opacity-50"
                title="Als Kopie speichern"
                aria-label="Template duplizieren"
                data-testid="template-duplicate-btn"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
              <!-- Edit button (custom only) -->
              <button
                v-if="!template.is_default"
                @click.stop="openEditor(template, true)"
                class="p-2 bg-white/90 dark:bg-gray-800/90 rounded-lg shadow-md hover:bg-treff-blue hover:text-white text-gray-600 dark:text-gray-300 transition-all"
                title="Template bearbeiten"
                aria-label="Template bearbeiten"
                data-testid="template-edit-btn"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <!-- Delete button (custom only) -->
              <button
                v-if="!template.is_default"
                @click.stop="openDeleteModal(template)"
                class="p-2 bg-white/90 dark:bg-gray-800/90 rounded-lg shadow-md hover:bg-red-500 hover:text-white text-gray-600 dark:text-gray-300 transition-all"
                title="Template loeschen"
                aria-label="Template loeschen"
                data-testid="template-delete-btn"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
            <!-- Visual Thumbnail -->
            <div class="relative">
              <div
                class="w-full h-48 flex flex-col items-center justify-center p-4 relative overflow-hidden"
                :style="{
                  background: `linear-gradient(135deg, ${parseColors(template.default_colors).background || '#1A1A2E'} 0%, ${parseColors(template.default_colors).primary || '#3B7AB1'} 100%)`,
                }"
              >
                <!-- Template preview mockup -->
                <div class="absolute top-3 left-3">
                  <div
                    class="px-2 py-1 rounded text-[10px] font-bold tracking-wide"
                    :style="{ background: parseColors(template.default_colors).primary || '#3B7AB1', color: '#fff' }"
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
                    :style="{ background: parseColors(template.default_colors).primary || '#3B7AB1' }"
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
                  <AppIcon :name="getPlatformInfo(template.platform_format).icon" class="w-3.5 h-3.5 inline-block" />
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
          </BaseCard>
        </div>
      </div>
    </div>

    <!-- Video Templates Hint -->
    <div
      v-if="!loading && !error"
      class="mt-8 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 border border-indigo-200 dark:border-indigo-800 rounded-xl p-5 flex items-start gap-4"
      data-tour="tpl-video-hint"
    >
      <div class="flex-shrink-0"><AppIcon name="film" class="w-8 h-8 inline-block text-indigo-600" /></div>
      <div class="flex-1">
        <h3 class="text-sm font-semibold text-indigo-900 dark:text-indigo-200 mb-1">
          Video-Templates fuer Reels &amp; TikTok
        </h3>
        <p class="text-sm text-indigo-700 dark:text-indigo-300 leading-relaxed">
          Neben den Post-Templates gibt es spezielle Video-Templates fuer Intros, Outros, Lower Thirds und Overlays.
          Diese findest du auf einer separaten Seite.
        </p>
        <router-link
          to="/video/templates"
          class="inline-flex items-center gap-1.5 mt-2 text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-200 transition-colors"
        >
          Zu den Video-Templates
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </router-link>
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
              aria-label="Dialog schliessen"
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
          <div v-if="createError" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3" role="alert">
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
              aria-label="Template-Name"
              :class="[
                'w-full px-4 py-2.5 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 text-sm',
                createSubmitted && createFieldErrors.name
                  ? 'border-red-500 focus:ring-red-500/20 focus:border-red-500 dark:border-red-500'
                  : 'border-gray-300 dark:border-gray-600 focus:ring-treff-blue focus:border-transparent'
              ]"
              data-testid="create-template-name"
            />
            <p v-if="createSubmitted && createFieldErrors.name" class="mt-1 text-sm text-red-600 dark:text-red-400" role="alert" data-testid="create-name-error">
              {{ createFieldErrors.name }}
            </p>
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
                aria-label="Kategorie"
                :class="[
                  'w-full px-4 py-2.5 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 text-sm',
                  createSubmitted && createFieldErrors.category
                    ? 'border-red-500 focus:ring-red-500/20 focus:border-red-500 dark:border-red-500'
                    : 'border-gray-300 dark:border-gray-600 focus:ring-treff-blue focus:border-transparent'
                ]"
                data-testid="create-template-category"
              >
                <option value="" disabled>Kategorie waehlen...</option>
                <option v-for="(info, key) in categories" :key="key" :value="key">
                  {{ info.label }}
                </option>
              </select>
              <p v-if="createSubmitted && createFieldErrors.category" class="mt-1 text-sm text-red-600 dark:text-red-400" role="alert" data-testid="create-category-error">
                {{ createFieldErrors.category }}
              </p>
            </div>

            <!-- Platform Format -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Plattform-Format <span class="text-red-500">*</span>
              </label>
              <select
                v-model="newTemplate.platform_format"
                aria-label="Plattform-Format"
                class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent text-sm"
              >
                <option v-for="(info, key) in platformLabels" :key="key" :value="key">
                  {{ info.label }} ({{ info.dim }})
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
            <!-- Placeholder Insertion Toolbar -->
            <div class="flex items-center gap-2 mb-1.5">
              <div class="relative">
                <button
                  type="button"
                  @click="showPlaceholderDropdown = !showPlaceholderDropdown"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-700 rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition-colors"
                  data-testid="insert-placeholder-btn"
                >
                  <AppIcon name="variable" class="w-3.5 h-3.5 inline-block" />
                  Platzhalter einfuegen
                  <svg class="w-3.5 h-3.5 transition-transform" :class="showPlaceholderDropdown ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
                </button>
                <div
                  v-if="showPlaceholderDropdown"
                  class="absolute top-full left-0 mt-1 w-56 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl shadow-lg z-30 py-1 max-h-64 overflow-auto"
                  data-testid="placeholder-dropdown"
                >
                  <button
                    v-for="ph in AVAILABLE_PLACEHOLDERS"
                    :key="ph.name"
                    type="button"
                    @click="insertPlaceholder(ph.name)"
                    class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-600 flex items-center gap-2 transition-colors"
                  >
                    <AppIcon :name="ph.icon" class="w-4 h-4 inline-block" />
                    <span class="flex-1">{{ ph.label }}</span>
                    <span class="text-[10px] text-gray-400 dark:text-gray-500 font-mono" v-text="'{{' + ph.name + '}}'"></span>
                  </button>
                </div>
              </div>
              <span class="text-[10px] text-gray-400 dark:text-gray-500">Klicke, um <span v-text="'{{variable}}'" class="font-mono"></span> in den HTML-Code einzufuegen</span>
            </div>
            <textarea
              ref="htmlTextareaRef"
              v-model="newTemplate.html_content"
              rows="6"
              placeholder="<div class='template'>...</div>"
              :class="[
                'w-full px-4 py-2.5 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 text-sm font-mono',
                createSubmitted && createFieldErrors.html_content
                  ? 'border-red-500 focus:ring-red-500/20 focus:border-red-500 dark:border-red-500'
                  : 'border-gray-300 dark:border-gray-600 focus:ring-treff-blue focus:border-transparent'
              ]"
              data-testid="create-template-html"
            ></textarea>
            <p v-if="createSubmitted && createFieldErrors.html_content" class="mt-1 text-sm text-red-600 dark:text-red-400" role="alert" data-testid="create-html-error">
              {{ createFieldErrors.html_content }}
            </p>
            <p v-else class="text-xs text-gray-400 dark:text-gray-500 mt-1">Verwende {{feldname}} als Platzhalter fuer dynamische Inhalte.</p>
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
              :class="[
                'w-full px-4 py-2.5 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 text-sm font-mono',
                createSubmitted && createFieldErrors.css_content
                  ? 'border-red-500 focus:ring-red-500/20 focus:border-red-500 dark:border-red-500'
                  : 'border-gray-300 dark:border-gray-600 focus:ring-treff-blue focus:border-transparent'
              ]"
              data-testid="create-template-css"
            ></textarea>
            <p v-if="createSubmitted && createFieldErrors.css_content" class="mt-1 text-sm text-red-600 dark:text-red-400" role="alert" data-testid="create-css-error">
              {{ createFieldErrors.css_content }}
            </p>
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
            <details class="mt-2">
              <summary class="text-xs text-indigo-600 dark:text-indigo-400 cursor-pointer hover:underline">Verfuegbare Standard-Variablen anzeigen</summary>
              <div class="mt-2 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-xs text-gray-600 dark:text-gray-400 grid grid-cols-2 gap-1.5">
                <span><strong>headline</strong> — Ueberschrift</span>
                <span><strong>subheadline</strong> — Unterueberschrift</span>
                <span><strong>body_text</strong> — Fliesstext</span>
                <span><strong>cta_text</strong> — CTA-Button</span>
                <span><strong>name</strong> — Person / Schueler</span>
                <span><strong>land</strong> — Zielland</span>
                <span><strong>stadt</strong> — Stadt / Region</span>
                <span><strong>datum</strong> — Datum / Frist</span>
                <span><strong>quote</strong> — Zitat (kurz)</span>
                <span><strong>quote_text</strong> — Zitat-Text</span>
                <span><strong>quote_author</strong> — Zitat-Autor</span>
                <span><strong>zahl</strong> — Statistik / Zahl</span>
                <span><strong>image</strong> — Bild-Platzhalter</span>
              </div>
            </details>
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
            :disabled="creating"
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
          <div class="flex-1 min-w-0">
            <h2 class="text-xl font-bold text-gray-900 dark:text-white">
              {{ editorIsEditMode ? 'Template bearbeiten' : 'Template-Vorschau' }}
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
              {{ editorTemplate.name }} &middot;
              <AppIcon :name="getCategoryInfo(editorTemplate.category).icon" class="w-4 h-4 inline-block" /> {{ getCategoryInfo(editorTemplate.category).label }} &middot;
              {{ getPlatformInfo(editorTemplate.platform_format).label }}
              <span v-if="editorIsEditMode" class="inline-flex items-center ml-2 px-2 py-0.5 rounded-full text-xs bg-treff-blue/10 text-treff-blue font-medium">Bearbeiten</span>
            </p>
          </div>
          <button
            @click="closeEditor"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            aria-label="Editor schliessen"
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

            <!-- Save success/error messages -->
            <div v-if="editorSaveSuccess" class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3 text-center">
              <p class="text-green-700 dark:text-green-300 text-sm font-medium">Template erfolgreich gespeichert!</p>
            </div>
            <div v-if="editorSaveError" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3" role="alert">
              <p class="text-red-600 dark:text-red-400 text-sm">{{ editorSaveError }}</p>
            </div>

            <!-- Template Name (edit mode only) -->
            <div v-if="editorIsEditMode" class="space-y-2">
              <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider flex items-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Template-Name
              </h3>
              <input
                v-model="editorTemplateName"
                type="text"
                placeholder="Template-Name eingeben..."
                aria-label="Template-Name"
                class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue"
                data-testid="editor-template-name"
              />
              <hr class="border-gray-200 dark:border-gray-700" />
            </div>

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
                  aria-label="Primaerfarbe Farbwahl"
                  class="w-10 h-10 rounded-lg border border-gray-300 dark:border-gray-600 cursor-pointer"
                  data-testid="editor-primary-color"
                />
                <input
                  v-model="editorCustom.primaryColor"
                  type="text"
                  aria-label="Primaerfarbe Hex-Wert"
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
                  aria-label="Sekundaerfarbe Farbwahl"
                  class="w-10 h-10 rounded-lg border border-gray-300 dark:border-gray-600 cursor-pointer"
                  data-testid="editor-secondary-color"
                />
                <input
                  v-model="editorCustom.secondaryColor"
                  type="text"
                  aria-label="Sekundaerfarbe Hex-Wert"
                  class="flex-1 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono"
                />
              </div>

              <!-- Background Color -->
              <div class="flex items-center gap-3">
                <label class="text-sm text-gray-600 dark:text-gray-400 w-28 flex-shrink-0">Hintergrund</label>
                <input
                  v-model="editorCustom.backgroundColor"
                  type="color"
                  aria-label="Hintergrundfarbe Farbwahl"
                  class="w-10 h-10 rounded-lg border border-gray-300 dark:border-gray-600 cursor-pointer"
                  data-testid="editor-bg-color"
                />
                <input
                  v-model="editorCustom.backgroundColor"
                  type="text"
                  aria-label="Hintergrundfarbe Hex-Wert"
                  class="flex-1 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono"
                />
              </div>

              <!-- Reset to Defaults Button -->
              <button
                @click="resetToDefaults"
                class="w-full mt-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors flex items-center justify-center gap-2"
                data-testid="editor-reset-defaults-btn"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Standardfarben wiederherstellen
              </button>
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
                  aria-label="Ueberschrift-Font"
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
                  aria-label="Fliesstext-Font"
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
                  aria-label="Ueberschrift"
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
                  aria-label="Unterueberschrift"
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
                  aria-label="Fliesstext"
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
                  aria-label="Call-to-Action Text"
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
            {{ editorIsEditMode ? 'Aenderungen werden erst nach dem Speichern uebernommen' : 'Vorschau aktualisiert sich automatisch bei jeder Aenderung' }}
          </p>
          <div class="flex items-center gap-3">
            <button
              @click="closeEditor"
              class="px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
            >
              {{ editorIsEditMode ? 'Abbrechen' : 'Schliessen' }}
            </button>
            <!-- "Als Kopie speichern" button — available for system templates (not editable) -->
            <button
              v-if="editorTemplate && editorTemplate.is_default"
              @click="duplicateFromEditor"
              :disabled="duplicating"
              class="px-5 py-2.5 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              data-testid="editor-duplicate-btn"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              {{ duplicating ? 'Wird kopiert...' : 'Als Kopie speichern' }}
            </button>
            <button
              v-if="editorIsEditMode"
              @click="saveTemplateEdits"
              :disabled="editorSaving || !editorTemplateName.trim()"
              class="px-5 py-2.5 text-sm font-medium text-white bg-treff-blue hover:bg-blue-600 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              data-testid="editor-save-btn"
            >
              <svg v-if="editorSaving" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ editorSaving ? 'Wird gespeichert...' : 'Speichern' }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <!-- =============================================
         Delete Confirmation Modal
         ============================================= -->
    <Teleport to="body">
      <div
        v-if="showDeleteModal && deletingTemplate"
        class="fixed inset-0 z-[60] flex items-center justify-center p-4"
        data-testid="delete-template-modal"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeDeleteModal"></div>

        <!-- Modal Content -->
        <div class="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md p-6 text-center">
          <!-- Warning Icon -->
          <div class="mx-auto w-14 h-14 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mb-4">
            <svg class="w-7 h-7 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </div>

          <!-- Title -->
          <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-2">
            Template loeschen?
          </h3>

          <!-- Description -->
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-2">
            Moechtest du das Template wirklich loeschen?
          </p>
          <p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" data-testid="delete-template-name">
            "{{ deletingTemplate.name }}"
          </p>
          <p class="text-xs text-gray-400 dark:text-gray-500 mb-5">
            Diese Aktion kann nicht rueckgaengig gemacht werden.
          </p>

          <!-- Error Message -->
          <div v-if="deleteError" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 mb-4 text-left" role="alert">
            <p class="text-red-600 dark:text-red-400 text-sm">{{ deleteError }}</p>
          </div>

          <!-- Buttons -->
          <div class="flex items-center justify-center gap-3">
            <button
              @click="closeDeleteModal"
              class="px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
              data-testid="delete-cancel-btn"
            >
              Abbrechen
            </button>
            <button
              @click="confirmDeleteTemplate"
              :disabled="deleting"
              class="px-5 py-2.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              data-testid="delete-confirm-btn"
            >
              <svg v-if="deleting" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ deleting ? 'Wird geloescht...' : 'Loeschen' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Page-specific guided tour -->
    <TourSystem ref="tourRef" page-key="templates" />
  </div>
</template>
