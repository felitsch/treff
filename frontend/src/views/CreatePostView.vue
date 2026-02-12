<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import draggable from 'vuedraggable'
import JSZip from 'jszip'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import { useCreatePostStore } from '@/stores/createPost'

const router = useRouter()
const toast = useToast()
const store = useCreatePostStore()

// ── Extract reactive refs from store (preserves state across navigation) ──
const {
  currentStep,
  loading,
  error,
  successMsg,
  selectedCategory,
  templates,
  selectedTemplate,
  loadingTemplates,
  selectedPlatform,
  topic,
  keyPoints,
  country,
  tone,
  generatingText,
  generatedContent,
  slides,
  captionInstagram,
  captionTiktok,
  hashtagsInstagram,
  hashtagsTiktok,
  ctaText,
  currentPreviewSlide,
  uploadingImage,
  assets,
  aiImagePrompt,
  generatingImage,
  generatedImageResult,
  aiImageError,
  exporting,
  savedPost,
  exportComplete,
  exportQuality,
  regeneratingField,
  validationMessage,
} = storeToRefs(store)

const totalSteps = 9

// Step 1: Category selection (static data - no need for store)
const categories = [
  { id: 'laender_spotlight', label: 'Laender-Spotlight', icon: '🌍', desc: 'Informative Posts ueber Ziellaender' },
  { id: 'erfahrungsberichte', label: 'Erfahrungsberichte', icon: '💬', desc: 'Alumni-Erfahrungen & Testimonials' },
  { id: 'infografiken', label: 'Infografiken', icon: '📊', desc: 'Vergleiche, Statistiken, Fakten' },
  { id: 'fristen_cta', label: 'Fristen & CTA', icon: '⏰', desc: 'Bewerbungsfristen & Calls-to-Action' },
  { id: 'tipps_tricks', label: 'Tipps & Tricks', icon: '💡', desc: 'Praktische Tipps fuers Auslandsjahr' },
  { id: 'faq', label: 'FAQ', icon: '❓', desc: 'Haeufig gestellte Fragen' },
  { id: 'foto_posts', label: 'Foto-Posts', icon: '📸', desc: 'Fotos mit Branding-Overlay' },
  { id: 'reel_tiktok_thumbnails', label: 'Reel/TikTok', icon: '🎬', desc: 'Thumbnails fuer Videos' },
  { id: 'story_posts', label: 'Story-Posts', icon: '📱', desc: 'Instagram Story Content' },
]

// Step 3: Platform (static data)
const platforms = [
  { id: 'instagram_feed', label: 'Instagram Feed', icon: '📷', format: '1:1 / 4:5' },
  { id: 'instagram_story', label: 'Instagram Story', icon: '📱', format: '9:16' },
  { id: 'tiktok', label: 'TikTok', icon: '🎵', format: '9:16' },
]

// Step 4: Countries (static data)
const countries = [
  { id: 'usa', label: 'USA', flag: '🇺🇸' },
  { id: 'canada', label: 'Kanada', flag: '🇨🇦' },
  { id: 'australia', label: 'Australien', flag: '🇦🇺' },
  { id: 'newzealand', label: 'Neuseeland', flag: '🇳🇿' },
  { id: 'ireland', label: 'Irland', flag: '🇮🇪' },
]

// Step 8: Prompt suggestions (static data)
const promptSuggestions = [
  'American high school hallway with students',
  'Canadian Rocky Mountains landscape at sunset',
  'Sydney Opera House and harbour at golden hour',
  'New Zealand green hills with sheep',
  'Dublin cobblestone streets with colorful doors',
  'German exchange student arriving at American host family',
  'Group of international students in school cafeteria',
  'Teenagers playing sports on American football field',
]

// ── Computed ──────────────────────────────────────────────────────────
const canProceed = computed(() => {
  switch (currentStep.value) {
    case 1: return !!selectedCategory.value
    case 2: return !!selectedTemplate.value
    case 3: return !!selectedPlatform.value
    case 4: return true  // topic/keypoints are optional, country optional
    case 5: return !!generatedContent.value
    case 6: return slides.value.length > 0
    case 7: return slides.value.length > 0
    case 8: return true  // background image is optional
    case 9: return true
    default: return false
  }
})

const stepValidationMessages = {
  1: 'Bitte waehle eine Kategorie aus, bevor du fortfaehrst.',
  2: 'Bitte waehle ein Template aus, bevor du fortfaehrst.',
  3: 'Bitte waehle eine Plattform aus, bevor du fortfaehrst.',
  5: 'Bitte generiere zuerst den Inhalt, bevor du fortfaehrst.',
  6: 'Es sind keine Slides vorhanden. Bitte generiere zuerst Inhalte.',
  7: 'Es sind keine Slides vorhanden. Bitte generiere zuerst Inhalte.',
}

const stepLabels = [
  'Kategorie',
  'Template',
  'Plattform',
  'Thema',
  'Generieren',
  'Vorschau',
  'Bearbeiten',
  'Bild',
  'Export',
]

const selectedCategoryObj = computed(() => categories.find(c => c.id === selectedCategory.value))
const selectedPlatformObj = computed(() => platforms.find(p => p.id === selectedPlatform.value))
const selectedCountryObj = computed(() => countries.find(c => c.id === country.value))

// ── Methods ──────────────────────────────────────────────────────────

function nextStep() {
  if (currentStep.value < totalSteps && canProceed.value) {
    validationMessage.value = ''
    currentStep.value++
    error.value = ''
    successMsg.value = ''
    if (currentStep.value === 2) loadTemplates()
    if (currentStep.value === 8) loadAssets()
  } else if (!canProceed.value) {
    validationMessage.value = stepValidationMessages[currentStep.value] || 'Bitte fuelle alle Pflichtfelder aus.'
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--
    error.value = ''
    successMsg.value = ''
    validationMessage.value = ''
  }
}

function goToStep(step) {
  if (step <= currentStep.value || (step === currentStep.value + 1 && canProceed.value)) {
    currentStep.value = step
    error.value = ''
    successMsg.value = ''
    validationMessage.value = ''
    if (step === 2) loadTemplates()
    if (step === 8) loadAssets()
  }
}

// Clear validation message when user makes a selection
watch([selectedCategory, selectedTemplate, selectedPlatform, generatedContent, slides], () => {
  validationMessage.value = ''
})

async function loadTemplates() {
  loadingTemplates.value = true
  try {
    const params = new URLSearchParams()
    if (selectedCategory.value) params.append('category', selectedCategory.value)
    const response = await api.get(`/api/templates?${params.toString()}`)
    templates.value = response.data
  } catch (e) {
    console.error('Failed to load templates:', e)
    templates.value = []
  } finally {
    loadingTemplates.value = false
  }
}

async function generateText() {
  generatingText.value = true
  error.value = ''

  try {
    const slideCount = selectedTemplate.value?.slide_count || 1
    const response = await api.post('/api/ai/generate-text', {
      category: selectedCategory.value,
      topic: topic.value.trim() || null,
      key_points: keyPoints.value.trim() || null,
      country: country.value || null,
      platform: selectedPlatform.value,
      slide_count: slideCount,
      tone: tone.value,
    })

    generatedContent.value = response.data
    slides.value = response.data.slides || []
    captionInstagram.value = response.data.caption_instagram || ''
    captionTiktok.value = response.data.caption_tiktok || ''
    hashtagsInstagram.value = response.data.hashtags_instagram || ''
    hashtagsTiktok.value = response.data.hashtags_tiktok || ''
    ctaText.value = response.data.cta_text || ''
    currentPreviewSlide.value = 0

    successMsg.value = 'Inhalt erfolgreich generiert!'
    setTimeout(() => { successMsg.value = '' }, 3000)
  } catch (e) {
    console.error('Text generation failed:', e)
    error.value = 'Textgenerierung fehlgeschlagen: ' + (e.response?.data?.detail || e.message)
  } finally {
    generatingText.value = false
  }
}

async function regenerateField(field, slideIndex = 0) {
  const fieldKey = slideIndex > 0 ? `${field}_${slideIndex}` : field
  regeneratingField.value = fieldKey
  error.value = ''

  try {
    const response = await api.post('/api/ai/regenerate-field', {
      field,
      category: selectedCategory.value,
      country: country.value || null,
      topic: topic.value.trim() || null,
      key_points: keyPoints.value.trim() || null,
      tone: tone.value,
      platform: selectedPlatform.value,
      slide_index: slideIndex,
      slide_count: slides.value.length || 1,
      current_headline: slides.value[currentPreviewSlide.value]?.headline || '',
      current_body: slides.value[currentPreviewSlide.value]?.body_text || '',
    })

    const newValue = response.data.value

    // Apply the regenerated value to the correct field
    switch (field) {
      case 'headline':
        if (slides.value[slideIndex]) slides.value[slideIndex].headline = newValue
        break
      case 'subheadline':
        if (slides.value[slideIndex]) slides.value[slideIndex].subheadline = newValue
        break
      case 'body_text':
        if (slides.value[slideIndex]) slides.value[slideIndex].body_text = newValue
        break
      case 'cta_text':
        if (slides.value[slideIndex]) slides.value[slideIndex].cta_text = newValue
        break
      case 'caption_instagram':
        captionInstagram.value = newValue
        break
      case 'caption_tiktok':
        captionTiktok.value = newValue
        break
      case 'hashtags_instagram':
        hashtagsInstagram.value = newValue
        break
      case 'hashtags_tiktok':
        hashtagsTiktok.value = newValue
        break
    }

    successMsg.value = 'Feld neu generiert!'
    setTimeout(() => { successMsg.value = '' }, 2000)
  } catch (e) {
    console.error('Field regeneration failed:', e)
    error.value = 'Regenerierung fehlgeschlagen: ' + (e.response?.data?.detail || e.message)
  } finally {
    regeneratingField.value = ''
  }
}

async function loadAssets() {
  try {
    const response = await api.get('/api/assets')
    assets.value = response.data
  } catch (e) {
    // Silent fail - assets are optional
  }
}

async function uploadBackgroundImage(event) {
  const file = event.target.files?.[0]
  if (!file) return

  uploadingImage.value = true
  error.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('category', 'background')
    const response = await api.post('/api/assets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    // Set as background for current slide
    const slide = slides.value[currentPreviewSlide.value]
    if (slide) {
      slide.background_type = 'image'
      slide.background_value = `/api/uploads/assets/${response.data.filename}`
    }
    successMsg.value = 'Bild hochgeladen!'
    setTimeout(() => { successMsg.value = '' }, 3000)
    await loadAssets()
  } catch (e) {
    error.value = 'Upload fehlgeschlagen: ' + (e.response?.data?.detail || e.message)
  } finally {
    uploadingImage.value = false
  }
}

function selectAssetAsBackground(asset) {
  const slide = slides.value[currentPreviewSlide.value]
  if (slide) {
    slide.background_type = 'image'
    slide.background_value = `/api/uploads/assets/${asset.filename}`
  }
  successMsg.value = 'Hintergrundbild gesetzt!'
  setTimeout(() => { successMsg.value = '' }, 2000)
}

async function generateAiImage() {
  if (!aiImagePrompt.value.trim()) {
    aiImageError.value = 'Bitte gib einen Prompt ein.'
    return
  }

  generatingImage.value = true
  aiImageError.value = ''
  generatedImageResult.value = null

  try {
    const response = await api.post('/api/ai/generate-image', {
      prompt: aiImagePrompt.value.trim(),
      width: 1024,
      height: 1024,
      category: 'ai_generated',
      country: country.value || null,
    })

    generatedImageResult.value = response.data

    // Auto-set as background for current slide
    if (response.data.image_url) {
      const slide = slides.value[currentPreviewSlide.value]
      if (slide) {
        slide.background_type = 'image'
        slide.background_value = response.data.image_url
      }
    }

    successMsg.value = response.data.message || 'Bild erfolgreich generiert!'
    setTimeout(() => { successMsg.value = '' }, 4000)

    // Refresh assets list to include the new AI-generated image
    await loadAssets()
  } catch (e) {
    console.error('AI image generation failed:', e)
    aiImageError.value = 'Bildgenerierung fehlgeschlagen: ' + (e.response?.data?.detail || e.message)
  } finally {
    generatingImage.value = false
  }
}

function selectPromptSuggestion(suggestion) {
  aiImagePrompt.value = suggestion
}

async function saveAndExport() {
  exporting.value = true
  error.value = ''

  try {
    // Save post to database (strip dragId from slides before saving)
    const cleanSlides = slides.value.map(({ dragId, ...rest }) => rest)
    const postData = {
      category: selectedCategory.value,
      country: country.value || null,
      platform: selectedPlatform.value,
      template_id: selectedTemplate.value?.id || null,
      title: cleanSlides[0]?.headline || 'Neuer Post',
      status: 'draft',
      tone: tone.value,
      slide_data: JSON.stringify(cleanSlides),
      caption_instagram: captionInstagram.value,
      caption_tiktok: captionTiktok.value,
      hashtags_instagram: hashtagsInstagram.value,
      hashtags_tiktok: hashtagsTiktok.value,
      cta_text: ctaText.value,
    }

    const response = await api.post('/api/posts', postData)
    savedPost.value = response.data

    // Record the export - use carousel endpoint for multi-slide posts
    const exportEndpoint = slides.value.length > 1 ? '/api/export/render-carousel' : '/api/export/render'
    await api.post(exportEndpoint, {
      post_id: response.data.id,
      platform: selectedPlatform.value,
      resolution: exportQuality.value,
      slide_count: slides.value.length,
    })

    // Auto-download: ZIP for multi-slide carousels, PNG for single slide
    if (slides.value.length > 1) {
      await downloadAsZip()
    } else {
      downloadAsImage(0)
    }

    exportComplete.value = true
    successMsg.value = 'Post gespeichert und exportiert!'
    toast.success('Post erfolgreich erstellt und gespeichert!', 5000)
  } catch (e) {
    error.value = 'Export fehlgeschlagen: ' + (e.response?.data?.detail || e.message)
  } finally {
    exporting.value = false
  }
}

function downloadAsImage(slideIndex = null) {
  // Guard against click event being passed as argument
  if (slideIndex !== null && typeof slideIndex !== 'number') {
    slideIndex = null
  }
  const targetSlide = slideIndex !== null ? slideIndex : currentPreviewSlide.value
  const canvas = renderSlideToCanvas(targetSlide)
  if (!canvas) return

  // Download with proper naming convention: TREFF_[category]_[platform]_[date]_[slide].png
  const link = document.createElement('a')
  const date = new Date().toISOString().split('T')[0]
  const slideNum = String(targetSlide + 1).padStart(2, '0')
  link.download = `TREFF_${selectedCategory.value}_${selectedPlatform.value}_${date}_${slideNum}.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
}

function renderSlideToCanvas(slideIndex) {
  // Render a single slide to a canvas and return it
  const dims = getDimensions()
  const scale = exportQuality.value === '2160' ? 2 : 1
  const canvas = document.createElement('canvas')
  canvas.width = dims.w * scale
  canvas.height = dims.h * scale
  const ctx = canvas.getContext('2d')
  ctx.scale(scale, scale)

  const slide = slides.value[slideIndex]
  if (!slide) return null

  // Background
  ctx.fillStyle = slide.background_value || '#1A1A2E'
  ctx.fillRect(0, 0, dims.w, dims.h)

  // Gradient overlay
  const gradient = ctx.createLinearGradient(0, 0, 0, dims.h)
  gradient.addColorStop(0, 'rgba(76, 139, 194, 0.3)')
  gradient.addColorStop(1, 'rgba(26, 26, 46, 0.8)')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, dims.w, dims.h)

  // TREFF logo
  ctx.fillStyle = '#4C8BC2'
  ctx.font = 'bold 28px Inter, Arial, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('TREFF', 60, 80)
  ctx.fillStyle = '#9CA3AF'
  ctx.font = '18px Inter, Arial, sans-serif'
  ctx.fillText('Sprachreisen', 158, 80)

  // Headline
  ctx.fillStyle = '#4C8BC2'
  ctx.font = 'bold 52px Inter, Arial, sans-serif'
  ctx.textAlign = 'center'
  wrapText(ctx, slide.headline || '', dims.w / 2, 260, dims.w - 160, 62)

  // Subheadline
  if (slide.subheadline) {
    ctx.fillStyle = '#FDD000'
    ctx.font = 'bold 32px Inter, Arial, sans-serif'
    wrapText(ctx, slide.subheadline, dims.w / 2, 400, dims.w - 160, 40)
  }

  // Body text
  if (slide.body_text) {
    ctx.fillStyle = '#D1D5DB'
    ctx.font = '24px Inter, Arial, sans-serif'
    wrapText(ctx, slide.body_text, dims.w / 2, 520, dims.w - 160, 32)
  }

  // CTA
  if (slide.cta_text) {
    const ctaY = dims.h - 180
    ctx.fillStyle = '#FDD000'
    roundRect(ctx, dims.w / 2 - 150, ctaY, 300, 56, 28)
    ctx.fill()
    ctx.fillStyle = '#1A1A2E'
    ctx.font = 'bold 24px Inter, Arial, sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(slide.cta_text, dims.w / 2, ctaY + 37)
  }

  // TREFF bottom branding
  ctx.fillStyle = '#4C8BC2'
  ctx.font = 'bold 18px Inter, Arial, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('TREFF Sprachreisen', 60, dims.h - 50)

  return canvas
}

function canvasToBlob(canvas) {
  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob), 'image/png')
  })
}

async function downloadAsZip() {
  // Generate ZIP containing all slide PNGs
  const zip = new JSZip()
  const date = new Date().toISOString().split('T')[0]

  for (let i = 0; i < slides.value.length; i++) {
    const canvas = renderSlideToCanvas(i)
    if (!canvas) continue
    const blob = await canvasToBlob(canvas)
    const slideNum = String(i + 1).padStart(2, '0')
    const filename = `TREFF_${selectedCategory.value}_${selectedPlatform.value}_${date}_slide_${slideNum}.png`
    zip.file(filename, blob)
  }

  const zipBlob = await zip.generateAsync({ type: 'blob' })
  const link = document.createElement('a')
  link.download = `TREFF_${selectedCategory.value}_${selectedPlatform.value}_${date}_carousel.zip`
  link.href = URL.createObjectURL(zipBlob)
  link.click()
  URL.revokeObjectURL(link.href)
}

function wrapText(ctx, text, x, y, maxWidth, lineHeight) {
  const words = text.split(' ')
  let line = ''
  let currentY = y
  for (const word of words) {
    const testLine = line + word + ' '
    const metrics = ctx.measureText(testLine)
    if (metrics.width > maxWidth && line !== '') {
      ctx.fillText(line.trim(), x, currentY)
      line = word + ' '
      currentY += lineHeight
    } else {
      line = testLine
    }
  }
  ctx.fillText(line.trim(), x, currentY)
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.lineTo(x + w - r, y)
  ctx.quadraticCurveTo(x + w, y, x + w, y + r)
  ctx.lineTo(x + w, y + h - r)
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h)
  ctx.lineTo(x + r, y + h)
  ctx.quadraticCurveTo(x, y + h, x, y + h - r)
  ctx.lineTo(x, y + r)
  ctx.quadraticCurveTo(x, y, x + r, y)
  ctx.closePath()
}

function getDimensions() {
  const dims = {
    instagram_feed: { w: 1080, h: 1080 },
    instagram_story: { w: 1080, h: 1920 },
    tiktok: { w: 1080, h: 1920 },
  }
  return dims[selectedPlatform.value] || dims.instagram_feed
}

function resetWorkflow() {
  store.resetWorkflow()
}

function nextPreviewSlide() {
  if (currentPreviewSlide.value < slides.value.length - 1) currentPreviewSlide.value++
}
function prevPreviewSlide() {
  if (currentPreviewSlide.value > 0) currentPreviewSlide.value--
}

function getTemplateGradient(template) {
  try {
    const colors = JSON.parse(template.default_colors || '{}')
    const primary = colors.primary || '#4C8BC2'
    const secondary = colors.secondary || '#FDD000'
    return `linear-gradient(135deg, ${primary} 0%, ${secondary} 100%)`
  } catch {
    return 'linear-gradient(135deg, #4C8BC2 0%, #FDD000 100%)'
  }
}

// Ensure each slide has a unique dragId for vuedraggable item-key
let dragIdCounter = 0
function ensureDragIds() {
  for (const slide of slides.value) {
    if (!slide.dragId) {
      slide.dragId = `slide-${++dragIdCounter}`
    }
  }
}

function onSlideReorder() {
  // After drag-and-drop reorder, reset preview to first slide
  currentPreviewSlide.value = 0
  ensureDragIds()
}

// Watch for slide changes
watch(slides, () => {
  currentPreviewSlide.value = 0
  ensureDragIds()
})

// On mount: reload data if returning to an in-progress workflow
onMounted(() => {
  if (store.hasWorkflowState()) {
    // Reload templates if we're on or past the template step
    if (currentStep.value >= 2 && selectedCategory.value) {
      loadTemplates()
    }
    // Reload assets if we're on the background image step
    if (currentStep.value >= 8) {
      loadAssets()
    }
    // Re-assign drag IDs to slides if they exist
    ensureDragIds()
  }
})
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Neuen Post erstellen</h1>
      <div class="flex items-center gap-4">
        <span class="text-sm text-gray-500 dark:text-gray-400">Schritt {{ currentStep }} von {{ totalSteps }}</span>
        <button
          @click="resetWorkflow"
          class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          Zuruecksetzen
        </button>
      </div>
    </div>

    <!-- Breadcrumb Navigation -->
    <nav aria-label="Breadcrumb" class="mb-4">
      <ol class="flex items-center flex-wrap gap-1 text-sm">
        <li class="flex items-center">
          <button
            @click="goToStep(1)"
            class="text-gray-500 dark:text-gray-400 hover:text-[#4C8BC2] dark:hover:text-blue-400 transition-colors"
            :class="currentStep === 1 ? 'cursor-default' : 'cursor-pointer'"
          >Post erstellen</button>
        </li>
        <template v-for="(label, idx) in stepLabels.slice(0, currentStep)" :key="'bc-' + idx">
          <li class="flex items-center">
            <span class="mx-1.5 text-gray-400 dark:text-gray-500" aria-hidden="true">/</span>
            <button
              v-if="idx + 1 < currentStep"
              @click="goToStep(idx + 1)"
              class="text-[#4C8BC2] dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:underline transition-colors cursor-pointer"
            >{{ label }}</button>
            <span
              v-else
              class="font-semibold text-gray-900 dark:text-white"
              aria-current="step"
            >{{ label }}</span>
          </li>
        </template>
      </ol>
    </nav>

    <!-- Step Indicator -->
    <div class="mb-8">
      <div class="flex items-center justify-between">
        <template v-for="(label, idx) in stepLabels" :key="idx">
          <button
            @click="goToStep(idx + 1)"
            class="flex flex-col items-center"
            :class="idx + 1 <= currentStep ? 'cursor-pointer' : 'cursor-not-allowed'"
          >
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors"
              :class="{
                'bg-[#4C8BC2] text-white ring-4 ring-blue-200 dark:ring-blue-900': idx + 1 === currentStep,
                'bg-green-500 text-white': idx + 1 < currentStep,
                'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400': idx + 1 > currentStep,
              }"
            >
              <span v-if="idx + 1 < currentStep">&#10003;</span>
              <span v-else>{{ idx + 1 }}</span>
            </div>
            <span
              class="text-[10px] mt-1 hidden sm:block"
              :class="{
                'text-[#4C8BC2] font-semibold dark:text-blue-400': idx + 1 === currentStep,
                'text-green-600 dark:text-green-400': idx + 1 < currentStep,
                'text-gray-400 dark:text-gray-500': idx + 1 > currentStep,
              }"
            >{{ label }}</span>
          </button>
          <div
            v-if="idx < stepLabels.length - 1"
            class="flex-1 h-0.5 mx-1"
            :class="idx + 1 < currentStep ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700'"
          ></div>
        </template>
      </div>
    </div>

    <!-- Messages -->
    <div v-if="error" class="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300 flex items-center gap-2" role="alert">
      <span>&#9888;</span> {{ error }}
      <button @click="error = ''" class="ml-auto text-red-500 hover:text-red-700">&times;</button>
    </div>
    <div v-if="successMsg" class="mb-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-green-700 dark:text-green-300 flex items-center gap-2">
      <span>&#10003;</span> {{ successMsg }}
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 1: Category Selection -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 1">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">Schritt 1: Waehle eine Post-Kategorie</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <button
          v-for="cat in categories"
          :key="cat.id"
          @click="selectedCategory = cat.id"
          class="p-4 rounded-xl border-2 transition-all text-left hover:shadow-md"
          :class="selectedCategory === cat.id
            ? 'border-[#4C8BC2] bg-blue-50 dark:bg-blue-900/20 shadow-md'
            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'"
        >
          <div class="text-2xl mb-2">{{ cat.icon }}</div>
          <div class="font-semibold text-gray-900 dark:text-white">{{ cat.label }}</div>
          <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ cat.desc }}</div>
        </button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 2: Template Selection -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 2">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">Schritt 2: Waehle ein Template</h2>
      <div v-if="loadingTemplates" class="flex items-center justify-center py-12">
        <div class="animate-spin h-8 w-8 border-4 border-[#4C8BC2] border-t-transparent rounded-full"></div>
      </div>
      <div v-else-if="templates.length === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
        Keine Templates fuer diese Kategorie verfuegbar.
      </div>
      <div v-else class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        <button
          v-for="tmpl in templates"
          :key="tmpl.id"
          @click="selectedTemplate = tmpl"
          class="rounded-xl border-2 overflow-hidden transition-all hover:shadow-md"
          :class="selectedTemplate?.id === tmpl.id
            ? 'border-[#4C8BC2] shadow-md ring-2 ring-[#4C8BC2]/30'
            : 'border-gray-200 dark:border-gray-700'"
        >
          <div class="h-28 flex items-center justify-center" :style="{ background: getTemplateGradient(tmpl) }">
            <div class="bg-white/20 backdrop-blur-sm rounded-lg px-3 py-1">
              <span class="text-white text-xs font-bold">TREFF</span>
            </div>
          </div>
          <div class="p-2 bg-white dark:bg-gray-800">
            <div class="text-xs font-medium text-gray-900 dark:text-white truncate">{{ tmpl.name }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">{{ tmpl.platform_format }} &middot; {{ tmpl.slide_count }} Slide{{ tmpl.slide_count > 1 ? 's' : '' }}</div>
          </div>
        </button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 3: Platform Selection -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 3">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">Schritt 3: Waehle die Zielplattform</h2>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl">
        <button
          v-for="p in platforms"
          :key="p.id"
          @click="selectedPlatform = p.id"
          class="p-6 rounded-xl border-2 transition-all text-center hover:shadow-md"
          :class="selectedPlatform === p.id
            ? 'border-[#4C8BC2] bg-blue-50 dark:bg-blue-900/20 shadow-md'
            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'"
        >
          <div class="text-3xl mb-2">{{ p.icon }}</div>
          <div class="font-semibold text-gray-900 dark:text-white">{{ p.label }}</div>
          <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ p.format }}</div>
        </button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 4: Topic & Key Points -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 4">
      <div class="max-w-2xl">
        <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">Schritt 4: Thema & Stichpunkte</h2>

        <!-- Country -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Land (optional)</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="c in countries"
              :key="c.id"
              @click="country = country === c.id ? '' : c.id"
              class="px-4 py-2 rounded-lg border-2 transition-all text-sm"
              :class="country === c.id
                ? 'border-[#4C8BC2] bg-blue-50 dark:bg-blue-900/20 text-[#4C8BC2]'
                : 'border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-gray-300'"
            >
              {{ c.flag }} {{ c.label }}
            </button>
          </div>
        </div>

        <!-- Topic -->
        <div class="mb-6">
          <label for="topic" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Thema / Titel</label>
          <input
            id="topic"
            v-model="topic"
            type="text"
            placeholder="z.B. Highschool-Jahr in Kanada"
            class="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent"
          />
        </div>

        <!-- Key Points -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Stichpunkte (optional)</label>
          <textarea
            v-model="keyPoints"
            rows="3"
            placeholder="z.B. Gastfamilien, Schulsystem, Freizeitaktivitaeten..."
            class="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent"
          ></textarea>
        </div>

        <!-- Tone -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Tonalitaet</label>
          <div class="flex gap-3">
            <button
              @click="tone = 'jugendlich'"
              class="flex-1 px-4 py-3 rounded-lg border-2 transition-all text-sm"
              :class="tone === 'jugendlich'
                ? 'border-[#4C8BC2] bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'"
            >
              <div class="font-semibold text-gray-900 dark:text-white">🎯 Jugendlich</div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">Locker, Gen-Z-freundlich</div>
            </button>
            <button
              @click="tone = 'serioess'"
              class="flex-1 px-4 py-3 rounded-lg border-2 transition-all text-sm"
              :class="tone === 'serioess'
                ? 'border-[#4C8BC2] bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'"
            >
              <div class="font-semibold text-gray-900 dark:text-white">🏛️ Serioes</div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">Fuer Eltern & Entscheider</div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 5: AI Text Generation -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 5">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">Schritt 5: Inhalt generieren</h2>

      <div class="max-w-2xl mx-auto bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8 text-center">
        <div class="text-5xl mb-4">&#x2728;</div>
        <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">KI-Textgenerierung</h3>
        <p class="text-gray-500 dark:text-gray-400 mb-6">
          Texte, Captions und Hashtags werden basierend auf deiner Auswahl generiert.
        </p>

        <!-- Summary of selections -->
        <div class="mb-6 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 text-left space-y-1">
          <div><strong>Kategorie:</strong> {{ selectedCategoryObj?.icon }} {{ selectedCategoryObj?.label }}</div>
          <div><strong>Template:</strong> {{ selectedTemplate?.name }} ({{ selectedTemplate?.slide_count }} Slide{{ selectedTemplate?.slide_count > 1 ? 's' : '' }})</div>
          <div><strong>Plattform:</strong> {{ selectedPlatformObj?.icon }} {{ selectedPlatformObj?.label }}</div>
          <div v-if="selectedCountryObj"><strong>Land:</strong> {{ selectedCountryObj.flag }} {{ selectedCountryObj.label }}</div>
          <div v-if="topic"><strong>Thema:</strong> {{ topic }}</div>
          <div v-if="keyPoints"><strong>Stichpunkte:</strong> {{ keyPoints }}</div>
          <div><strong>Tonalitaet:</strong> {{ tone === 'jugendlich' ? '🎯 Jugendlich' : '🏛️ Serioes' }}</div>
        </div>

        <button
          @click="generateText"
          :disabled="generatingText"
          class="px-8 py-4 bg-[#4C8BC2] hover:bg-[#3a7ab3] disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white font-bold rounded-xl transition-colors flex items-center justify-center gap-2 text-lg mx-auto"
        >
          <span v-if="generatingText" class="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></span>
          <span v-else>&#x2728;</span>
          {{ generatingText ? 'Generiere...' : 'Inhalt generieren' }}
        </button>

        <!-- Generated content summary -->
        <div v-if="generatedContent" class="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700 text-left">
          <div class="flex items-center gap-2 text-green-600 dark:text-green-400 mb-3">
            <span class="text-lg">&#10003;</span>
            <span class="font-bold">Inhalt generiert!</span>
          </div>
          <ul class="text-sm text-gray-600 dark:text-gray-400 space-y-1 list-disc list-inside">
            <li>{{ slides.length }} Slide(s) mit Texten</li>
            <li>Instagram Caption erstellt</li>
            <li>TikTok Caption erstellt</li>
            <li>Hashtags generiert</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 6: Live Preview -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 6">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">Schritt 6: Live-Vorschau</h2>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Preview -->
        <div class="flex flex-col items-center">
          <div
            id="post-preview-container"
            class="rounded-2xl overflow-hidden shadow-xl border border-gray-200 dark:border-gray-700 relative bg-gradient-to-br from-[#1A1A2E] to-[#2a2a4e]"
            :class="{
              'aspect-square w-full max-w-[400px]': selectedPlatform === 'instagram_feed',
              'aspect-[9/16] w-full max-w-[320px]': selectedPlatform === 'instagram_story' || selectedPlatform === 'tiktok',
            }"
          >
            <div v-if="slides[currentPreviewSlide]" class="absolute inset-0 p-6 flex flex-col justify-between">
              <!-- TREFF logo -->
              <div class="flex items-center gap-2">
                <div class="bg-[#4C8BC2] rounded-lg px-3 py-1"><span class="text-white text-sm font-bold">TREFF</span></div>
                <span class="text-gray-400 text-xs">Sprachreisen</span>
              </div>

              <!-- Content -->
              <div class="flex-1 flex flex-col justify-center py-4">
                <h3 class="text-[#4C8BC2] text-xl font-extrabold leading-tight mb-2">
                  {{ slides[currentPreviewSlide]?.headline || '' }}
                </h3>
                <p v-if="slides[currentPreviewSlide]?.subheadline" class="text-[#FDD000] text-sm font-semibold mb-2">
                  {{ slides[currentPreviewSlide].subheadline }}
                </p>
                <p v-if="slides[currentPreviewSlide]?.body_text" class="text-gray-300 text-xs leading-relaxed line-clamp-5">
                  {{ slides[currentPreviewSlide].body_text }}
                </p>

                <!-- Bullet points -->
                <ul v-if="slides[currentPreviewSlide]?.bullet_points?.length" class="mt-2 space-y-1">
                  <li
                    v-for="(bp, bpIdx) in (Array.isArray(slides[currentPreviewSlide].bullet_points) ? slides[currentPreviewSlide].bullet_points : [])"
                    :key="bpIdx"
                    class="text-gray-300 text-xs flex items-start gap-1.5"
                  >
                    <span class="text-[#FDD000] mt-0.5">&#9679;</span>
                    <span>{{ bp }}</span>
                  </li>
                </ul>
              </div>

              <!-- CTA -->
              <div v-if="slides[currentPreviewSlide]?.cta_text">
                <div class="inline-block bg-[#FDD000] text-[#1A1A2E] px-5 py-2 rounded-full font-bold text-sm">
                  {{ slides[currentPreviewSlide].cta_text }}
                </div>
              </div>

              <!-- Slide dots -->
              <div v-if="slides.length > 1" class="flex justify-center gap-1.5 mt-3">
                <button
                  v-for="(s, sIdx) in slides"
                  :key="sIdx"
                  @click="currentPreviewSlide = sIdx"
                  class="w-2 h-2 rounded-full transition-colors"
                  :class="sIdx === currentPreviewSlide ? 'bg-[#4C8BC2]' : 'bg-gray-600'"
                ></button>
              </div>
            </div>
          </div>

          <!-- Slide navigation -->
          <div v-if="slides.length > 1" class="flex items-center justify-between w-full max-w-[400px] mt-4">
            <button @click="prevPreviewSlide" :disabled="currentPreviewSlide === 0"
              class="px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-30 transition-colors">
              &#8592; Vorherige
            </button>
            <span class="text-sm text-gray-500 dark:text-gray-400">Slide {{ currentPreviewSlide + 1 }} von {{ slides.length }}</span>
            <button @click="nextPreviewSlide" :disabled="currentPreviewSlide === slides.length - 1"
              class="px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-30 transition-colors">
              Naechste &#8594;
            </button>
          </div>
        </div>

        <!-- Captions & hashtags sidebar -->
        <div class="space-y-4">
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <h4 class="font-semibold text-sm text-gray-900 dark:text-white mb-2">📷 Instagram Caption</h4>
            <p class="text-xs text-gray-600 dark:text-gray-400 whitespace-pre-line max-h-32 overflow-auto">{{ captionInstagram }}</p>
          </div>
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <h4 class="font-semibold text-sm text-gray-900 dark:text-white mb-2"># Instagram Hashtags</h4>
            <p class="text-xs text-blue-600 dark:text-blue-400 break-words">{{ hashtagsInstagram }}</p>
          </div>
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <h4 class="font-semibold text-sm text-gray-900 dark:text-white mb-2">🎵 TikTok Caption</h4>
            <p class="text-xs text-gray-600 dark:text-gray-400">{{ captionTiktok }}</p>
          </div>
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <h4 class="font-semibold text-sm text-gray-900 dark:text-white mb-2">🎵 TikTok Hashtags</h4>
            <p class="text-xs text-blue-600 dark:text-blue-400 break-words">{{ hashtagsTiktok }}</p>
          </div>
          <div v-if="ctaText" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <h4 class="font-semibold text-sm text-gray-900 dark:text-white mb-2">📢 Call-to-Action</h4>
            <p class="text-xs text-gray-600 dark:text-gray-400">{{ ctaText }}</p>
          </div>
          <div class="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 text-center text-xs text-gray-500 dark:text-gray-400">
            {{ selectedPlatformObj?.icon }} {{ selectedPlatformObj?.label }}
            &middot; {{ selectedCategoryObj?.label }}
            <span v-if="selectedCountryObj"> &middot; {{ selectedCountryObj.flag }} {{ selectedCountryObj.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 7: Edit Generated Content (Headline etc.) -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 7">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">Schritt 7: Inhalt bearbeiten</h2>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Edit panel -->
        <div class="space-y-4">
          <!-- Slide tabs with drag-and-drop reordering -->
          <div v-if="slides.length > 1" class="mb-3">
            <div class="flex items-center gap-2 mb-2">
              <span class="text-xs text-gray-500 dark:text-gray-400">↕ Slides per Drag & Drop neu anordnen</span>
            </div>
            <draggable
              v-model="slides"
              item-key="dragId"
              handle=".drag-handle"
              animation="200"
              ghost-class="slide-ghost"
              class="flex gap-1 flex-wrap"
              @end="onSlideReorder"
            >
              <template #item="{ element, index }">
                <button
                  @click="currentPreviewSlide = index"
                  class="px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 drag-handle cursor-grab active:cursor-grabbing"
                  :class="currentPreviewSlide === index
                    ? 'bg-[#4C8BC2] text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200'"
                >
                  <span class="opacity-50">⠿</span>
                  Slide {{ index + 1 }}
                  <span v-if="index === 0" class="font-normal">(Cover)</span>
                  <span v-if="index === slides.length - 1 && index > 0" class="font-normal">(CTA)</span>
                </button>
              </template>
            </draggable>
          </div>

          <!-- Current slide edit -->
          <div v-if="slides[currentPreviewSlide]" class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 space-y-3">
            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Headline</label>
                <button
                  @click="regenerateField('headline', currentPreviewSlide)"
                  :disabled="!!regeneratingField"
                  class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-md bg-[#4C8BC2]/10 text-[#4C8BC2] hover:bg-[#4C8BC2]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  :title="'Headline neu generieren'"
                >
                  <span :class="{ 'animate-spin': regeneratingField === (currentPreviewSlide > 0 ? 'headline_' + currentPreviewSlide : 'headline') }" class="text-sm">&#x1F504;</span>
                  <span>Neu</span>
                </button>
              </div>
              <input
                v-model="slides[currentPreviewSlide].headline"
                class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent"
                :class="(slides[currentPreviewSlide].headline?.length || 0) > 40 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white' : (slides[currentPreviewSlide].headline?.length || 0) > 30 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-gray-900 dark:text-white' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white'"
              />
              <div class="flex items-center justify-between mt-0.5">
                <span v-if="(slides[currentPreviewSlide].headline?.length || 0) > 40" class="text-xs text-red-500 dark:text-red-400">Text kann den Template-Bereich ueberlaufen</span>
                <span v-else-if="(slides[currentPreviewSlide].headline?.length || 0) > 30" class="text-xs text-amber-500 dark:text-amber-400">Nahe am Zeichenlimit</span>
                <span v-else class="text-xs text-gray-400"></span>
                <span class="text-xs" :class="(slides[currentPreviewSlide].headline?.length || 0) > 40 ? 'text-red-500 dark:text-red-400 font-semibold' : (slides[currentPreviewSlide].headline?.length || 0) > 30 ? 'text-amber-500 dark:text-amber-400' : 'text-gray-400'">{{ slides[currentPreviewSlide].headline?.length || 0 }}/40</span>
              </div>
            </div>
            <div v-if="slides[currentPreviewSlide].subheadline !== undefined">
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Subheadline</label>
                <button
                  @click="regenerateField('subheadline', currentPreviewSlide)"
                  :disabled="!!regeneratingField"
                  class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-md bg-[#4C8BC2]/10 text-[#4C8BC2] hover:bg-[#4C8BC2]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  :title="'Subheadline neu generieren'"
                >
                  <span :class="{ 'animate-spin': regeneratingField === (currentPreviewSlide > 0 ? 'subheadline_' + currentPreviewSlide : 'subheadline') }" class="text-sm">&#x1F504;</span>
                  <span>Neu</span>
                </button>
              </div>
              <input
                v-model="slides[currentPreviewSlide].subheadline"
                class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent"
                :class="(slides[currentPreviewSlide].subheadline?.length || 0) > 60 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white' : (slides[currentPreviewSlide].subheadline?.length || 0) > 45 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-gray-900 dark:text-white' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white'"
              />
              <div class="flex items-center justify-between mt-0.5">
                <span v-if="(slides[currentPreviewSlide].subheadline?.length || 0) > 60" class="text-xs text-red-500 dark:text-red-400">Text kann den Template-Bereich ueberlaufen</span>
                <span v-else-if="(slides[currentPreviewSlide].subheadline?.length || 0) > 45" class="text-xs text-amber-500 dark:text-amber-400">Nahe am Zeichenlimit</span>
                <span v-else class="text-xs text-gray-400"></span>
                <span class="text-xs" :class="(slides[currentPreviewSlide].subheadline?.length || 0) > 60 ? 'text-red-500 dark:text-red-400 font-semibold' : (slides[currentPreviewSlide].subheadline?.length || 0) > 45 ? 'text-amber-500 dark:text-amber-400' : 'text-gray-400'">{{ slides[currentPreviewSlide].subheadline?.length || 0 }}/60</span>
              </div>
            </div>
            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Text</label>
                <button
                  @click="regenerateField('body_text', currentPreviewSlide)"
                  :disabled="!!regeneratingField"
                  class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-md bg-[#4C8BC2]/10 text-[#4C8BC2] hover:bg-[#4C8BC2]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  :title="'Text neu generieren'"
                >
                  <span :class="{ 'animate-spin': regeneratingField === (currentPreviewSlide > 0 ? 'body_text_' + currentPreviewSlide : 'body_text') }" class="text-sm">&#x1F504;</span>
                  <span>Neu</span>
                </button>
              </div>
              <textarea
                v-model="slides[currentPreviewSlide].body_text"
                rows="3"
                class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent resize-none"
                :class="(slides[currentPreviewSlide].body_text?.length || 0) > 200 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white' : (slides[currentPreviewSlide].body_text?.length || 0) > 150 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-gray-900 dark:text-white' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white'"
              ></textarea>
              <div class="flex items-center justify-between mt-0.5">
                <span v-if="(slides[currentPreviewSlide].body_text?.length || 0) > 200" class="text-xs text-red-500 dark:text-red-400">Text kann den Template-Bereich ueberlaufen</span>
                <span v-else-if="(slides[currentPreviewSlide].body_text?.length || 0) > 150" class="text-xs text-amber-500 dark:text-amber-400">Nahe am Zeichenlimit</span>
                <span v-else class="text-xs text-gray-400"></span>
                <span class="text-xs" :class="(slides[currentPreviewSlide].body_text?.length || 0) > 200 ? 'text-red-500 dark:text-red-400 font-semibold' : (slides[currentPreviewSlide].body_text?.length || 0) > 150 ? 'text-amber-500 dark:text-amber-400' : 'text-gray-400'">{{ slides[currentPreviewSlide].body_text?.length || 0 }}/200</span>
              </div>
            </div>
            <div v-if="slides[currentPreviewSlide].cta_text">
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-gray-500 dark:text-gray-400">CTA</label>
                <button
                  @click="regenerateField('cta_text', currentPreviewSlide)"
                  :disabled="!!regeneratingField"
                  class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-md bg-[#4C8BC2]/10 text-[#4C8BC2] hover:bg-[#4C8BC2]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  :title="'CTA neu generieren'"
                >
                  <span :class="{ 'animate-spin': regeneratingField === (currentPreviewSlide > 0 ? 'cta_text_' + currentPreviewSlide : 'cta_text') }" class="text-sm">&#x1F504;</span>
                  <span>Neu</span>
                </button>
              </div>
              <input
                v-model="slides[currentPreviewSlide].cta_text"
                class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent"
                :class="(slides[currentPreviewSlide].cta_text?.length || 0) > 25 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white' : (slides[currentPreviewSlide].cta_text?.length || 0) > 20 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-gray-900 dark:text-white' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white'"
              />
              <div class="flex items-center justify-between mt-0.5">
                <span v-if="(slides[currentPreviewSlide].cta_text?.length || 0) > 25" class="text-xs text-red-500 dark:text-red-400">Text kann den Template-Bereich ueberlaufen</span>
                <span v-else-if="(slides[currentPreviewSlide].cta_text?.length || 0) > 20" class="text-xs text-amber-500 dark:text-amber-400">Nahe am Zeichenlimit</span>
                <span v-else class="text-xs text-gray-400"></span>
                <span class="text-xs" :class="(slides[currentPreviewSlide].cta_text?.length || 0) > 25 ? 'text-red-500 dark:text-red-400 font-semibold' : (slides[currentPreviewSlide].cta_text?.length || 0) > 20 ? 'text-amber-500 dark:text-amber-400' : 'text-gray-400'">{{ slides[currentPreviewSlide].cta_text?.length || 0 }}/25</span>
              </div>
            </div>
          </div>

          <!-- Captions editing -->
          <div class="space-y-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <div class="flex items-center justify-between mb-2">
                <label class="text-sm font-bold text-gray-700 dark:text-gray-300">&#x1F4F7; Instagram Caption</label>
                <button
                  @click="regenerateField('caption_instagram')"
                  :disabled="!!regeneratingField"
                  class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-md bg-[#4C8BC2]/10 text-[#4C8BC2] hover:bg-[#4C8BC2]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  :title="'Instagram Caption neu generieren'"
                >
                  <span :class="{ 'animate-spin': regeneratingField === 'caption_instagram' }" class="text-sm">&#x1F504;</span>
                  <span>Neu</span>
                </button>
              </div>
              <textarea v-model="captionInstagram" rows="3"
                class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent resize-none"
                :class="(captionInstagram?.length || 0) > 2200 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white' : (captionInstagram?.length || 0) > 1800 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-gray-900 dark:text-white' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white'"
              ></textarea>
              <div class="flex items-center justify-between mt-0.5">
                <span v-if="(captionInstagram?.length || 0) > 2200" class="text-xs text-red-500 dark:text-red-400">Instagram-Limit ueberschritten (max 2.200)</span>
                <span v-else-if="(captionInstagram?.length || 0) > 1800" class="text-xs text-amber-500 dark:text-amber-400">Nahe am Instagram-Limit</span>
                <span v-else class="text-xs text-gray-400"></span>
                <span class="text-xs" :class="(captionInstagram?.length || 0) > 2200 ? 'text-red-500 dark:text-red-400 font-semibold' : (captionInstagram?.length || 0) > 1800 ? 'text-amber-500 dark:text-amber-400' : 'text-gray-400'">{{ captionInstagram?.length || 0 }}/2.200</span>
              </div>
            </div>
            <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <div class="flex items-center justify-between mb-2">
                <label class="text-sm font-bold text-gray-700 dark:text-gray-300"># Instagram Hashtags</label>
                <button
                  @click="regenerateField('hashtags_instagram')"
                  :disabled="!!regeneratingField"
                  class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-md bg-[#4C8BC2]/10 text-[#4C8BC2] hover:bg-[#4C8BC2]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  :title="'Instagram Hashtags neu generieren'"
                >
                  <span :class="{ 'animate-spin': regeneratingField === 'hashtags_instagram' }" class="text-sm">&#x1F504;</span>
                  <span>Neu</span>
                </button>
              </div>
              <textarea v-model="hashtagsInstagram" rows="2"
                class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent resize-none"
                :class="(hashtagsInstagram?.length || 0) > 2200 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-blue-600 dark:text-blue-400' : (hashtagsInstagram?.length || 0) > 1800 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-blue-600 dark:text-blue-400' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-blue-600 dark:text-blue-400'"
              ></textarea>
              <div class="flex items-center justify-between mt-0.5">
                <span v-if="(hashtagsInstagram?.length || 0) > 2200" class="text-xs text-red-500 dark:text-red-400">Hashtag-Limit ueberschritten</span>
                <span v-else class="text-xs text-gray-400"></span>
                <span class="text-xs" :class="(hashtagsInstagram?.length || 0) > 2200 ? 'text-red-500 dark:text-red-400 font-semibold' : 'text-gray-400'">{{ hashtagsInstagram?.length || 0 }} Zeichen</span>
              </div>
            </div>
            <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <div class="flex items-center justify-between mb-2">
                <label class="text-sm font-bold text-gray-700 dark:text-gray-300">&#x1F3B5; TikTok Hashtags</label>
                <button
                  @click="regenerateField('hashtags_tiktok')"
                  :disabled="!!regeneratingField"
                  class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-md bg-[#4C8BC2]/10 text-[#4C8BC2] hover:bg-[#4C8BC2]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  :title="'TikTok Hashtags neu generieren'"
                >
                  <span :class="{ 'animate-spin': regeneratingField === 'hashtags_tiktok' }" class="text-sm">&#x1F504;</span>
                  <span>Neu</span>
                </button>
              </div>
              <textarea v-model="hashtagsTiktok" rows="2"
                class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent resize-none"
                :class="(hashtagsTiktok?.length || 0) > 2200 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-blue-600 dark:text-blue-400' : (hashtagsTiktok?.length || 0) > 1800 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-blue-600 dark:text-blue-400' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-blue-600 dark:text-blue-400'"
              ></textarea>
              <div class="flex items-center justify-between mt-0.5">
                <span v-if="(hashtagsTiktok?.length || 0) > 2200" class="text-xs text-red-500 dark:text-red-400">Hashtag-Limit ueberschritten</span>
                <span v-else class="text-xs text-gray-400"></span>
                <span class="text-xs" :class="(hashtagsTiktok?.length || 0) > 2200 ? 'text-red-500 dark:text-red-400 font-semibold' : 'text-gray-400'">{{ hashtagsTiktok?.length || 0 }} Zeichen</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Mini live preview (sticky) -->
        <div class="lg:sticky lg:top-4 self-start">
          <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Live-Vorschau</div>
          <div
            class="rounded-2xl overflow-hidden shadow-xl border border-gray-200 dark:border-gray-700 relative bg-gradient-to-br from-[#1A1A2E] to-[#2a2a4e]"
            :class="{
              'aspect-square': selectedPlatform === 'instagram_feed',
              'aspect-[9/16]': selectedPlatform === 'instagram_story' || selectedPlatform === 'tiktok',
            }"
            style="max-width: 320px;"
          >
            <div v-if="slides[currentPreviewSlide]" class="absolute inset-0 p-5 flex flex-col justify-between">
              <div class="flex items-center gap-1.5">
                <div class="bg-[#4C8BC2] rounded px-2 py-0.5"><span class="text-white text-[10px] font-bold">TREFF</span></div>
              </div>
              <div class="flex-1 flex flex-col justify-center py-3">
                <h3 class="text-[#4C8BC2] text-base font-extrabold leading-tight mb-1.5">{{ slides[currentPreviewSlide].headline }}</h3>
                <p v-if="slides[currentPreviewSlide].subheadline" class="text-[#FDD000] text-[11px] font-semibold mb-1.5">{{ slides[currentPreviewSlide].subheadline }}</p>
                <p v-if="slides[currentPreviewSlide].body_text" class="text-gray-300 text-[10px] leading-relaxed line-clamp-4">{{ slides[currentPreviewSlide].body_text }}</p>
              </div>
              <div v-if="slides[currentPreviewSlide].cta_text">
                <div class="inline-block bg-[#FDD000] text-[#1A1A2E] px-4 py-1.5 rounded-full font-bold text-[11px]">{{ slides[currentPreviewSlide].cta_text }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 8: Background Image Upload / AI Generation (Optional) -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 8">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">Schritt 8: Hintergrundbild (optional)</h2>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div class="space-y-6">

          <!-- AI Image Generation -->
          <div class="border-2 border-purple-300 dark:border-purple-600 rounded-xl p-6 bg-purple-50/50 dark:bg-purple-900/10">
            <div class="flex items-center gap-2 mb-3">
              <span class="text-2xl">🤖</span>
              <h3 class="text-sm font-semibold text-purple-800 dark:text-purple-300">KI-Bild generieren</h3>
            </div>

            <!-- Prompt Input -->
            <div class="mb-3">
              <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1">Bildbeschreibung (Prompt)</label>
              <textarea
                v-model="aiImagePrompt"
                rows="3"
                maxlength="500"
                class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-purple-400 focus:border-purple-400 resize-none"
                placeholder="z.B. American high school hallway with students"
                :disabled="generatingImage"
              ></textarea>
              <div class="flex justify-between items-center mt-1">
                <span class="text-xs text-gray-400">{{ aiImagePrompt.length }}/500</span>
              </div>
            </div>

            <!-- Prompt Suggestions -->
            <div class="mb-4">
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-2">Vorschlaege:</p>
              <div class="flex flex-wrap gap-1.5">
                <button
                  v-for="suggestion in promptSuggestions"
                  :key="suggestion"
                  @click="selectPromptSuggestion(suggestion)"
                  class="text-xs px-2.5 py-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-full hover:border-purple-400 hover:text-purple-700 dark:hover:text-purple-300 transition-colors truncate max-w-[200px]"
                  :disabled="generatingImage"
                >
                  {{ suggestion }}
                </button>
              </div>
            </div>

            <!-- Generate Button -->
            <button
              @click="generateAiImage"
              :disabled="generatingImage || !aiImagePrompt.trim()"
              class="w-full px-4 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center gap-2"
            >
              <span v-if="generatingImage" class="flex items-center gap-2">
                <span class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                Bild wird generiert...
              </span>
              <span v-else>🎨 Bild generieren</span>
            </button>

            <!-- AI Error -->
            <div v-if="aiImageError" class="mt-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-sm text-red-700 dark:text-red-300">
              {{ aiImageError }}
            </div>

            <!-- Generated Image Result -->
            <div v-if="generatedImageResult && generatedImageResult.status === 'success'" class="mt-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
              <div class="flex items-center gap-2 mb-2">
                <span class="text-green-600">✓</span>
                <span class="text-sm font-medium text-green-700 dark:text-green-300">{{ generatedImageResult.message }}</span>
              </div>
              <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                <span>Quelle: {{ generatedImageResult.source === 'gemini' ? 'Gemini AI' : 'Lokale Generierung' }}</span>
                <span v-if="generatedImageResult.asset">| {{ generatedImageResult.asset.width }}x{{ generatedImageResult.asset.height }}px</span>
              </div>
            </div>
          </div>

          <!-- Divider -->
          <div class="relative">
            <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-gray-200 dark:border-gray-700"></div></div>
            <div class="relative flex justify-center"><span class="bg-white dark:bg-gray-900 px-3 text-sm text-gray-400">oder</span></div>
          </div>

          <!-- Upload -->
          <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-8 text-center hover:border-[#4C8BC2] transition-colors">
            <div class="text-4xl mb-3">📷</div>
            <p class="text-gray-600 dark:text-gray-400 mb-3">Hintergrundbild hochladen</p>
            <label class="inline-block px-6 py-2.5 bg-[#4C8BC2] text-white rounded-lg cursor-pointer hover:bg-[#3a7ab3] transition-colors font-medium">
              <span v-if="uploadingImage" class="flex items-center gap-2">
                <span class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                Hochladen...
              </span>
              <span v-else>Datei waehlen</span>
              <input type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="uploadBackgroundImage" :disabled="uploadingImage" />
            </label>
            <p class="text-xs text-gray-400 mt-2">JPG, PNG oder WebP (max. 20 MB)</p>
          </div>

          <!-- Existing assets -->
          <div v-if="assets.length > 0">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Vorhandene Bilder:</h3>
            <div class="grid grid-cols-3 sm:grid-cols-4 gap-3">
              <button
                v-for="asset in assets"
                :key="asset.id"
                @click="selectAssetAsBackground(asset)"
                class="aspect-square rounded-lg overflow-hidden border-2 border-gray-200 dark:border-gray-700 hover:border-[#4C8BC2] transition-all relative group"
              >
                <img :src="`/api/uploads/assets/${asset.filename}`" :alt="asset.original_filename" class="w-full h-full object-cover" />
                <div v-if="asset.source === 'ai_generated'" class="absolute top-1 right-1 bg-purple-600 text-white text-[8px] px-1.5 py-0.5 rounded font-bold">KI</div>
              </button>
            </div>
          </div>

          <div class="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 text-sm text-gray-500 dark:text-gray-400">
            💡 Dieser Schritt ist optional. Ohne Bild wird der Standard-Farbverlauf verwendet.
          </div>
        </div>

        <!-- Preview -->
        <div class="self-start">
          <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Vorschau</div>
          <div
            class="rounded-2xl overflow-hidden shadow-xl border border-gray-200 dark:border-gray-700 relative"
            :class="{
              'aspect-square': selectedPlatform === 'instagram_feed',
              'aspect-[9/16]': selectedPlatform === 'instagram_story' || selectedPlatform === 'tiktok',
            }"
            :style="{
              maxWidth: '320px',
              background: slides[currentPreviewSlide]?.background_type === 'image'
                ? `url(${slides[currentPreviewSlide].background_value}) center/cover`
                : 'linear-gradient(135deg, #1A1A2E, #2a2a4e)',
            }"
          >
            <div v-if="slides[currentPreviewSlide]" class="absolute inset-0 p-5 flex flex-col justify-between bg-black/20">
              <div class="flex items-center gap-1.5">
                <div class="bg-[#4C8BC2] rounded px-2 py-0.5"><span class="text-white text-[10px] font-bold">TREFF</span></div>
              </div>
              <div class="flex-1 flex flex-col justify-center py-3">
                <h3 class="text-white text-base font-extrabold leading-tight mb-1.5 drop-shadow">{{ slides[currentPreviewSlide].headline }}</h3>
                <p v-if="slides[currentPreviewSlide].subheadline" class="text-[#FDD000] text-[11px] font-semibold drop-shadow">{{ slides[currentPreviewSlide].subheadline }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 9: Export / Save -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 9">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">Schritt 9: Exportieren & Speichern</h2>

      <!-- Pre-export summary -->
      <div v-if="!exportComplete" class="max-w-2xl mx-auto bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4">Zusammenfassung</h3>
        <div class="grid grid-cols-2 gap-3 text-sm mb-6">
          <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div class="text-gray-500 dark:text-gray-400 text-xs">Kategorie</div>
            <div class="font-medium text-gray-900 dark:text-white">{{ selectedCategoryObj?.icon }} {{ selectedCategoryObj?.label }}</div>
          </div>
          <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div class="text-gray-500 dark:text-gray-400 text-xs">Plattform</div>
            <div class="font-medium text-gray-900 dark:text-white">{{ selectedPlatformObj?.icon }} {{ selectedPlatformObj?.label }}</div>
          </div>
          <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div class="text-gray-500 dark:text-gray-400 text-xs">Template</div>
            <div class="font-medium text-gray-900 dark:text-white">{{ selectedTemplate?.name }}</div>
          </div>
          <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div class="text-gray-500 dark:text-gray-400 text-xs">Slides</div>
            <div class="font-medium text-gray-900 dark:text-white">{{ slides.length }}</div>
          </div>
          <div v-if="selectedCountryObj" class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div class="text-gray-500 dark:text-gray-400 text-xs">Land</div>
            <div class="font-medium text-gray-900 dark:text-white">{{ selectedCountryObj.flag }} {{ selectedCountryObj.label }}</div>
          </div>
          <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div class="text-gray-500 dark:text-gray-400 text-xs">Headline</div>
            <div class="font-medium text-gray-900 dark:text-white truncate">{{ slides[0]?.headline }}</div>
          </div>
        </div>

        <!-- Export Quality Selector -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Export-Qualitaet</label>
          <div class="flex gap-3">
            <button
              @click="exportQuality = '1080'"
              data-testid="quality-1080"
              :class="[
                'flex-1 px-4 py-3 rounded-lg border-2 transition-all text-sm font-medium',
                exportQuality === '1080'
                  ? 'border-[#4C8BC2] bg-[#4C8BC2]/10 text-[#4C8BC2]'
                  : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-300'
              ]"
            >
              <div class="font-bold">Standard (1080px)</div>
              <div class="text-xs mt-0.5 opacity-70">Empfohlen fuer Social Media</div>
            </button>
            <button
              @click="exportQuality = '2160'"
              data-testid="quality-2160"
              :class="[
                'flex-1 px-4 py-3 rounded-lg border-2 transition-all text-sm font-medium',
                exportQuality === '2160'
                  ? 'border-[#4C8BC2] bg-[#4C8BC2]/10 text-[#4C8BC2]'
                  : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-300'
              ]"
            >
              <div class="font-bold">Hohe Qualitaet (2160px)</div>
              <div class="text-xs mt-0.5 opacity-70">Fuer Druck und hohe Aufloesung</div>
            </button>
          </div>
        </div>

        <div class="flex flex-col sm:flex-row gap-3">
          <button
            @click="saveAndExport"
            :disabled="exporting"
            class="flex-1 px-6 py-3 bg-[#4C8BC2] hover:bg-[#3a7ab3] disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <span v-if="exporting" class="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></span>
            {{ exporting ? 'Speichern...' : 'Post speichern & exportieren' }}
          </button>
          <button
            v-if="slides.length > 1"
            @click="downloadAsZip"
            :disabled="slides.length === 0"
            class="flex-1 px-6 py-3 bg-[#FDD000] hover:bg-[#e5c000] disabled:bg-gray-300 text-[#1A1A2E] font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            📦 Als ZIP herunterladen ({{ slides.length }} Slides)
          </button>
          <button
            v-else
            @click="downloadAsImage"
            :disabled="slides.length === 0"
            class="flex-1 px-6 py-3 bg-[#FDD000] hover:bg-[#e5c000] disabled:bg-gray-300 text-[#1A1A2E] font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            ⬇ Als PNG herunterladen
          </button>
        </div>
      </div>

      <!-- Export complete -->
      <div v-if="exportComplete" class="max-w-2xl mx-auto bg-white dark:bg-gray-800 rounded-xl border border-green-200 dark:border-green-800 p-8 text-center">
        <div class="text-6xl mb-4">🎉</div>
        <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">Post erfolgreich erstellt!</h3>
        <p class="text-gray-500 dark:text-gray-400 mb-4">
          Dein Post wurde in der Datenbank gespeichert und als exportiert markiert.
        </p>
        <div v-if="savedPost" class="text-sm text-gray-600 dark:text-gray-400 mb-6 space-y-1">
          <div>Post ID: <strong>#{{ savedPost.id }}</strong></div>
          <div>Status: <strong>{{ savedPost.status }}</strong></div>
          <div>Kategorie: <strong>{{ selectedCategoryObj?.label }}</strong></div>
        </div>
        <div class="flex flex-col sm:flex-row gap-3 justify-center">
          <button v-if="slides.length > 1" @click="downloadAsZip" class="px-6 py-3 bg-[#FDD000] hover:bg-[#e5c000] text-[#1A1A2E] font-bold rounded-lg transition-colors">
            📦 ZIP herunterladen ({{ slides.length }} Slides)
          </button>
          <button v-else @click="downloadAsImage" class="px-6 py-3 bg-[#FDD000] hover:bg-[#e5c000] text-[#1A1A2E] font-bold rounded-lg transition-colors">
            ⬇ PNG herunterladen
          </button>
          <button @click="router.push('/dashboard')" class="px-6 py-3 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-900 dark:text-white font-bold rounded-lg transition-colors">
            Zum Dashboard
          </button>
          <button @click="resetWorkflow" class="px-6 py-3 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium rounded-lg transition-colors">
            Neuen Post erstellen
          </button>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- Validation Message -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="validationMessage" class="mt-4 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-300 dark:border-amber-700 rounded-lg text-amber-800 dark:text-amber-300 flex items-center gap-2" role="alert" data-testid="validation-message">
      <span class="text-lg">&#9888;&#65039;</span>
      <span>{{ validationMessage }}</span>
      <button @click="validationMessage = ''" class="ml-auto text-amber-600 hover:text-amber-800 dark:text-amber-400 dark:hover:text-amber-200 font-bold">&times;</button>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- Navigation Buttons -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div class="flex items-center justify-between mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
      <button
        v-if="currentStep > 1 && !exportComplete"
        @click="prevStep"
        class="px-6 py-3 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 font-medium transition-colors"
      >
        &#8592; Zurueck
      </button>
      <div v-else></div>

      <button
        v-if="currentStep < totalSteps && !exportComplete"
        @click="nextStep"
        class="px-6 py-3 rounded-lg font-medium transition-colors"
        :class="canProceed
          ? 'bg-[#4C8BC2] hover:bg-[#3a7ab3] text-white'
          : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'"
      >
        Weiter &#8594;
      </button>
    </div>
  </div>
</template>

<style scoped>
.slide-ghost {
  opacity: 0.4;
  background: #4C8BC2 !important;
  border-radius: 0.5rem;
}
</style>
