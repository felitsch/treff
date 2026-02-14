<script setup>
import { ref, computed, watch } from 'vue'
import api from '@/utils/api'
import TourSystem from '@/components/common/TourSystem.vue'
import VideoWorkflowTour from '@/components/common/VideoWorkflowTour.vue'

// ── State ──────────────────────────────────────────────────────────
const hookText = ref('')
const backgroundType = ref('color') // 'color' | 'image'
const backgroundColor = ref('#1A1A2E')
const backgroundImageUrl = ref('')
const selectedAsset = ref(null)
const assets = ref([])
const loadingAssets = ref(false)
const exporting = ref(false)
const exportComplete = ref(false)
const savedPost = ref(null)
const error = ref('')
const successMsg = ref('')
const tourRef = ref(null)
const workflowTourRef = ref(null)

// Export format: '9:16' for Reels/TikTok, '1:1' for Feed preview
const exportFormat = ref('9:16')

// Predefined TREFF brand color schemes
const colorPresets = [
  { name: 'Dunkel', bg: '#1A1A2E', text: '#FFFFFF' },
  { name: 'TREFF Blau', bg: '#3B7AB1', text: '#FFFFFF' },
  { name: 'Gelb Akzent', bg: '#FDD000', text: '#1A1A2E' },
  { name: 'Gradient Blau', bg: 'linear-gradient(135deg, #3B7AB1, #1A1A2E)', text: '#FFFFFF' },
  { name: 'Gradient Gold', bg: 'linear-gradient(135deg, #FDD000, #FF8C00)', text: '#1A1A2E' },
  { name: 'Rot Energie', bg: '#E63946', text: '#FFFFFF' },
  { name: 'Gruen Natur', bg: '#2D6A4F', text: '#FFFFFF' },
  { name: 'Lila Kreativ', bg: '#7B2D8E', text: '#FFFFFF' },
]

const selectedPreset = ref(colorPresets[0])

// Font size control
const fontSize = ref('large') // 'medium' | 'large' | 'xlarge'
const fontSizeOptions = [
  { id: 'medium', label: 'M', px: 48 },
  { id: 'large', label: 'L', px: 64 },
  { id: 'xlarge', label: 'XL', px: 80 },
]

// Export format options
const formatOptions = [
  { id: '9:16', label: '9:16', desc: 'Reels & TikTok', width: 1080, height: 1920, previewW: 270, previewH: 480 },
  { id: '1:1', label: '1:1', desc: 'Feed Vorschau', width: 1080, height: 1080, previewW: 340, previewH: 340 },
]

// Dynamic dimensions based on selected format
const currentFormat = computed(() => formatOptions.find(f => f.id === exportFormat.value) || formatOptions[0])
const previewWidth = computed(() => currentFormat.value.previewW)
const previewHeight = computed(() => currentFormat.value.previewH)
const exportWidth = computed(() => currentFormat.value.width)
const exportHeight = computed(() => currentFormat.value.height)

// ── Computed ──────────────────────────────────────────────────────
const previewStyle = computed(() => {
  const base = {
    width: previewWidth.value + 'px',
    height: previewHeight.value + 'px',
  }
  if (backgroundType.value === 'image' && backgroundImageUrl.value) {
    return {
      ...base,
      backgroundImage: `url(${backgroundImageUrl.value})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
    }
  }
  const bg = selectedPreset.value.bg
  if (bg.startsWith('linear-gradient')) {
    return { ...base, background: bg }
  }
  return { ...base, backgroundColor: bg }
})

const textColor = computed(() => {
  if (backgroundType.value === 'image') return '#FFFFFF'
  return selectedPreset.value.text
})

const hookFontSize = computed(() => {
  const opt = fontSizeOptions.find(f => f.id === fontSize.value)
  // Scale down for preview (preview is fraction of export)
  const scale = previewWidth.value / exportWidth.value
  return Math.round((opt?.px || 64) * scale) + 'px'
})

const canExport = computed(() => hookText.value.trim().length > 0)

// ── Methods ──────────────────────────────────────────────────────

async function loadAssets() {
  loadingAssets.value = true
  try {
    const response = await api.get('/api/assets')
    assets.value = response.data
  } catch (e) {
    // Silent - assets are optional
  } finally {
    loadingAssets.value = false
  }
}

function selectPreset(preset) {
  selectedPreset.value = preset
  backgroundType.value = 'color'
  backgroundImageUrl.value = ''
  selectedAsset.value = null
}

function selectAssetBackground(asset) {
  selectedAsset.value = asset
  backgroundType.value = 'image'
  backgroundImageUrl.value = `/api/uploads/assets/${asset.filename}`
}

function clearBackground() {
  backgroundType.value = 'color'
  backgroundImageUrl.value = ''
  selectedAsset.value = null
}

async function uploadImage(event) {
  const file = event.target.files?.[0]
  if (!file) return

  error.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('category', 'thumbnail_background')
    const response = await api.post('/api/assets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    backgroundType.value = 'image'
    backgroundImageUrl.value = `/api/uploads/assets/${response.data.filename}`
    selectedAsset.value = response.data
    successMsg.value = 'Hintergrundbild hochgeladen!'
    setTimeout(() => { successMsg.value = '' }, 2000)
    await loadAssets()
  } catch (e) {
    error.value = 'Upload fehlgeschlagen: ' + (e.response?.data?.detail || e.message)
  }
}

function downloadAsPng() {
  const w = exportWidth.value
  const h = exportHeight.value
  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d')

  // Helper functions
  function wrapText(ctx, text, x, y, maxWidth, lineHeight) {
    const words = text.split(' ')
    let line = ''
    const lines = []
    for (const word of words) {
      const testLine = line + word + ' '
      const metrics = ctx.measureText(testLine)
      if (metrics.width > maxWidth && line !== '') {
        lines.push(line.trim())
        line = word + ' '
      } else {
        line = testLine
      }
    }
    lines.push(line.trim())

    // Center vertically: calculate total text height
    const totalHeight = lines.length * lineHeight
    const startY = y - totalHeight / 2 + lineHeight / 2

    for (let i = 0; i < lines.length; i++) {
      ctx.fillText(lines[i], x, startY + i * lineHeight)
    }
    return lines.length
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

  // Draw background
  const bg = selectedPreset.value.bg
  if (backgroundType.value === 'image' && backgroundImageUrl.value) {
    ctx.fillStyle = '#1A1A2E'
    ctx.fillRect(0, 0, w, h)
  } else if (bg.startsWith('linear-gradient')) {
    const gradient = ctx.createLinearGradient(0, 0, w, h)
    const colorMatch = bg.match(/#[A-Fa-f0-9]{6}/g)
    if (colorMatch && colorMatch.length >= 2) {
      gradient.addColorStop(0, colorMatch[0])
      gradient.addColorStop(1, colorMatch[1])
    }
    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, w, h)
  } else {
    ctx.fillStyle = bg
    ctx.fillRect(0, 0, w, h)
  }

  // Dark overlay for readability
  if (backgroundType.value === 'image') {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.4)'
    ctx.fillRect(0, 0, w, h)
  }

  // Determine text color
  const txtColor = backgroundType.value === 'image' ? '#FFFFFF' : selectedPreset.value.text

  // TREFF logo top-left
  ctx.fillStyle = '#3B7AB1'
  roundRect(ctx, 60, 60, 120, 48, 12)
  ctx.fill()
  ctx.fillStyle = '#FFFFFF'
  ctx.font = 'bold 28px Inter, Arial, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('TREFF', 120, 92)

  ctx.fillStyle = '#9CA3AF'
  ctx.font = '20px Inter, Arial, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('Sprachreisen', 200, 92)

  // Hook text - centered, large, bold
  const opt = fontSizeOptions.find(f => f.id === fontSize.value)
  const hookPx = opt?.px || 64
  ctx.fillStyle = txtColor
  ctx.font = `900 ${hookPx}px Inter, Arial, sans-serif`
  ctx.textAlign = 'center'
  ctx.shadowColor = 'rgba(0, 0, 0, 0.5)'
  ctx.shadowBlur = 20
  ctx.shadowOffsetX = 0
  ctx.shadowOffsetY = 4
  wrapText(ctx, hookText.value.trim(), w / 2, h / 2, w - 160, hookPx * 1.2)
  ctx.shadowColor = 'transparent'
  ctx.shadowBlur = 0

  // CTA at bottom
  const ctaY = h - 150
  ctx.fillStyle = '#FDD000'
  roundRect(ctx, w / 2 - 180, ctaY, 360, 72, 36)
  ctx.fill()
  ctx.fillStyle = '#1A1A2E'
  ctx.font = 'bold 28px Inter, Arial, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('Jetzt ansehen', w / 2, ctaY + 46)

  // TREFF bottom branding
  ctx.fillStyle = txtColor === '#FFFFFF' ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.4)'
  ctx.font = '22px Inter, Arial, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('TREFF Sprachreisen | treff-sprachreisen.de', w / 2, h - 40)

  // Download
  const link = document.createElement('a')
  const date = new Date().toISOString().split('T')[0]
  const safeHook = hookText.value.trim().substring(0, 30).replace(/[^a-zA-Z0-9]/g, '_')
  const formatTag = exportFormat.value === '1:1' ? '1x1' : '9x16'
  link.download = `TREFF_thumbnail_${formatTag}_${date}_${safeHook}.png`
  link.href = canvas.toDataURL('image/png')
  link.click()

  return canvas
}

// For image backgrounds, we need to load the image into canvas
function downloadAsPngWithImage() {
  if (backgroundType.value === 'image' && backgroundImageUrl.value) {
    const w = exportWidth.value
    const h = exportHeight.value
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      const canvas = document.createElement('canvas')
      canvas.width = w
      canvas.height = h
      const ctx = canvas.getContext('2d')

      // Draw background image covering the canvas ratio
      const imgRatio = img.width / img.height
      const canvasRatio = w / h
      let sx = 0, sy = 0, sw = img.width, sh = img.height
      if (imgRatio > canvasRatio) {
        sw = img.height * canvasRatio
        sx = (img.width - sw) / 2
      } else {
        sh = img.width / canvasRatio
        sy = (img.height - sh) / 2
      }
      ctx.drawImage(img, sx, sy, sw, sh, 0, 0, w, h)

      // Dark overlay
      ctx.fillStyle = 'rgba(0, 0, 0, 0.4)'
      ctx.fillRect(0, 0, w, h)

      // Draw text elements same as color version
      drawTextElements(ctx)

      // Download
      const link = document.createElement('a')
      const date = new Date().toISOString().split('T')[0]
      const safeHook = hookText.value.trim().substring(0, 30).replace(/[^a-zA-Z0-9]/g, '_')
      const formatTag = exportFormat.value === '1:1' ? '1x1' : '9x16'
      link.download = `TREFF_thumbnail_${formatTag}_${date}_${safeHook}.png`
      link.href = canvas.toDataURL('image/png')
      link.click()
    }
    img.onerror = () => {
      // Fallback to solid background
      downloadAsPng()
    }
    img.src = backgroundImageUrl.value
  } else {
    downloadAsPng()
  }
}

function drawTextElements(ctx) {
  const w = exportWidth.value
  const h = exportHeight.value

  function wrapText(ctx, text, x, y, maxWidth, lineHeight) {
    const words = text.split(' ')
    let line = ''
    const lines = []
    for (const word of words) {
      const testLine = line + word + ' '
      const metrics = ctx.measureText(testLine)
      if (metrics.width > maxWidth && line !== '') {
        lines.push(line.trim())
        line = word + ' '
      } else {
        line = testLine
      }
    }
    lines.push(line.trim())
    const totalHeight = lines.length * lineHeight
    const startY = y - totalHeight / 2 + lineHeight / 2
    for (let i = 0; i < lines.length; i++) {
      ctx.fillText(lines[i], x, startY + i * lineHeight)
    }
  }

  function roundRect(ctx, x, y, rw, rh, r) {
    ctx.beginPath()
    ctx.moveTo(x + r, y)
    ctx.lineTo(x + rw - r, y)
    ctx.quadraticCurveTo(x + rw, y, x + rw, y + r)
    ctx.lineTo(x + rw, y + rh - r)
    ctx.quadraticCurveTo(x + rw, y + rh, x + rw - r, y + rh)
    ctx.lineTo(x + r, y + rh)
    ctx.quadraticCurveTo(x, y + rh, x, y + rh - r)
    ctx.lineTo(x, y + r)
    ctx.quadraticCurveTo(x, y, x + r, y)
    ctx.closePath()
  }

  const txtColor = backgroundType.value === 'image' ? '#FFFFFF' : selectedPreset.value.text

  // TREFF logo
  ctx.fillStyle = '#3B7AB1'
  roundRect(ctx, 60, 60, 120, 48, 12)
  ctx.fill()
  ctx.fillStyle = '#FFFFFF'
  ctx.font = 'bold 28px Inter, Arial, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('TREFF', 120, 92)

  ctx.fillStyle = '#9CA3AF'
  ctx.font = '20px Inter, Arial, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('Sprachreisen', 200, 92)

  // Hook text
  const opt = fontSizeOptions.find(f => f.id === fontSize.value)
  const hookPx = opt?.px || 64
  ctx.fillStyle = txtColor
  ctx.font = `900 ${hookPx}px Inter, Arial, sans-serif`
  ctx.textAlign = 'center'
  ctx.shadowColor = 'rgba(0, 0, 0, 0.5)'
  ctx.shadowBlur = 20
  ctx.shadowOffsetX = 0
  ctx.shadowOffsetY = 4
  wrapText(ctx, hookText.value.trim(), w / 2, h / 2, w - 160, hookPx * 1.2)
  ctx.shadowColor = 'transparent'
  ctx.shadowBlur = 0

  // CTA
  const ctaY = h - 150
  ctx.fillStyle = '#FDD000'
  roundRect(ctx, w / 2 - 180, ctaY, 360, 72, 36)
  ctx.fill()
  ctx.fillStyle = '#1A1A2E'
  ctx.font = 'bold 28px Inter, Arial, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('Jetzt ansehen', w / 2, ctaY + 46)

  // Bottom branding
  ctx.fillStyle = 'rgba(255,255,255,0.6)'
  ctx.font = '22px Inter, Arial, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('TREFF Sprachreisen | treff-sprachreisen.de', w / 2, h - 40)
}

async function saveAndExport() {
  exporting.value = true
  error.value = ''

  try {
    // Create post in database
    const slideData = [{
      headline: hookText.value.trim(),
      subheadline: '',
      body_text: '',
      cta_text: 'Jetzt ansehen',
      background_type: backgroundType.value,
      background_value: backgroundType.value === 'image' ? backgroundImageUrl.value : selectedPreset.value.bg,
    }]

    const postData = {
      category: 'reel_tiktok_thumbnails',
      country: null,
      platform: exportFormat.value === '1:1' ? 'instagram_feed' : 'tiktok',
      template_id: null,
      title: hookText.value.trim().substring(0, 100),
      status: 'draft',
      tone: 'jugendlich',
      slide_data: JSON.stringify(slideData),
      caption_instagram: '',
      caption_tiktok: '',
      hashtags_instagram: '',
      hashtags_tiktok: '',
      cta_text: 'Jetzt ansehen',
    }

    const response = await api.post('/api/posts', postData)
    savedPost.value = response.data

    // Record export
    await api.post('/api/export/render', {
      post_id: response.data.id,
      platform: exportFormat.value === '1:1' ? 'instagram_feed' : 'tiktok',
      resolution: '1080',
      slide_count: 1,
    })

    // Download PNG
    downloadAsPngWithImage()

    exportComplete.value = true
    successMsg.value = 'Thumbnail gespeichert und exportiert!'
  } catch (e) {
    error.value = 'Export fehlgeschlagen: ' + (e.response?.data?.detail || e.message)
  } finally {
    exporting.value = false
  }
}

function reset() {
  hookText.value = ''
  backgroundType.value = 'color'
  backgroundColor.value = '#1A1A2E'
  backgroundImageUrl.value = ''
  selectedAsset.value = null
  selectedPreset.value = colorPresets[0]
  fontSize.value = 'large'
  exportFormat.value = '9:16'
  exporting.value = false
  exportComplete.value = false
  savedPost.value = null
  error.value = ''
  successMsg.value = ''
}

// Load assets on mount
loadAssets()
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div data-tour="tg-header" class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Thumbnail Generator</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Erstelle Video-Thumbnails im 9:16 oder 1:1 Format</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="workflowTourRef?.startTour()"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[#4C8BC2] bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors"
          title="Video-Workflow-Tour starten"
        >
          🎬 Workflow
        </button>
        <button
          @click="tourRef?.startTour()"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          title="Seiten-Tour starten"
        >
          &#10067; Tour
        </button>
        <button
          @click="reset"
          class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          Zuruecksetzen
        </button>
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

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Left Column: Controls -->
      <div class="lg:col-span-2 space-y-6">

        <!-- Hook Text Input -->
        <div data-tour="tg-hook-text" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">Hook Text</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">Der Text, der auf dem Thumbnail erscheint und Aufmerksamkeit erregt.</p>
          <textarea
            id="hook-text-input"
            v-model="hookText"
            rows="3"
            maxlength="120"
            placeholder="z.B. Das hat NIEMAND erwartet"
            class="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent text-lg"
          ></textarea>
          <div class="flex items-center justify-between mt-2">
            <span class="text-xs text-gray-400">{{ hookText.length }} / 120 Zeichen</span>
            <!-- Font size selector -->
            <div class="flex items-center gap-2">
              <span class="text-xs text-gray-500 dark:text-gray-400">Schriftgroesse:</span>
              <div class="flex gap-1">
                <button
                  v-for="opt in fontSizeOptions"
                  :key="opt.id"
                  @click="fontSize = opt.id"
                  class="w-8 h-8 rounded-lg text-xs font-bold transition-all flex items-center justify-center"
                  :class="fontSize === opt.id
                    ? 'bg-[#3B7AB1] text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'"
                >
                  {{ opt.label }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Background Selection -->
        <div data-tour="tg-background" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">Hintergrund</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">Waehle eine Farbe oder lade ein Bild hoch.</p>

          <!-- Color presets -->
          <div class="mb-4">
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Farbvorlagen</h3>
            <div class="grid grid-cols-4 sm:grid-cols-8 gap-2">
              <button
                v-for="preset in colorPresets"
                :key="preset.name"
                @click="selectPreset(preset)"
                :title="preset.name"
                class="w-full aspect-square rounded-lg border-2 transition-all hover:scale-105"
                :class="selectedPreset.name === preset.name && backgroundType === 'color'
                  ? 'border-[#3B7AB1] ring-2 ring-[#3B7AB1]/30 scale-105'
                  : 'border-gray-200 dark:border-gray-600'"
                :style="{
                  background: preset.bg.startsWith('linear-gradient') ? preset.bg : preset.bg,
                  backgroundColor: preset.bg.startsWith('linear-gradient') ? undefined : preset.bg,
                }"
              >
                <span v-if="selectedPreset.name === preset.name && backgroundType === 'color'" class="text-white text-xs font-bold drop-shadow">&#10003;</span>
              </button>
            </div>
          </div>

          <!-- Custom color picker -->
          <div class="mb-4">
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Eigene Farbe</h3>
            <div class="flex items-center gap-3">
              <input
                type="color"
                v-model="backgroundColor"
                @input="selectPreset({ name: 'Custom', bg: backgroundColor, text: '#FFFFFF' })"
                class="w-10 h-10 rounded-lg border border-gray-300 dark:border-gray-600 cursor-pointer"
              />
              <span class="text-sm text-gray-500 dark:text-gray-400">{{ backgroundColor }}</span>
            </div>
          </div>

          <!-- Divider -->
          <div class="border-t border-gray-200 dark:border-gray-700 my-4"></div>

          <!-- Image upload -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300">Bild als Hintergrund</h3>
              <button
                v-if="backgroundType === 'image'"
                @click="clearBackground"
                class="text-xs text-red-500 hover:text-red-700 font-medium"
              >
                Bild entfernen
              </button>
            </div>
            <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-4 text-center hover:border-[#3B7AB1] transition-colors">
              <label class="inline-block px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium">
                Bild hochladen
                <input type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="uploadImage" />
              </label>
              <p class="text-xs text-gray-400 mt-2">JPG, PNG oder WebP</p>
            </div>

            <!-- Existing assets -->
            <div v-if="assets.length > 0" class="mt-3">
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-2">Aus Asset-Bibliothek:</p>
              <div class="grid grid-cols-6 gap-2 max-h-24 overflow-y-auto">
                <button
                  v-for="asset in assets"
                  :key="asset.id"
                  @click="selectAssetBackground(asset)"
                  class="aspect-square rounded-lg overflow-hidden border-2 transition-all"
                  :class="selectedAsset?.id === asset.id
                    ? 'border-[#3B7AB1] ring-2 ring-[#3B7AB1]/30'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'"
                >
                  <img :src="`/api/uploads/assets/${asset.filename}`" :alt="asset.original_filename" class="w-full h-full object-cover" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Export Section -->
        <div data-tour="tg-export" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Export</h2>

          <!-- Export Format Selector -->
          <div class="mb-4">
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Exportformat</h3>
            <div class="grid grid-cols-2 gap-3">
              <button
                v-for="fmt in formatOptions"
                :key="fmt.id"
                @click="exportFormat = fmt.id"
                class="relative p-3 rounded-lg border-2 transition-all text-left"
                :class="exportFormat === fmt.id
                  ? 'border-[#3B7AB1] bg-[#3B7AB1]/5 dark:bg-[#3B7AB1]/10'
                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'"
              >
                <div class="flex items-center gap-3">
                  <div
                    class="flex-shrink-0 rounded border border-gray-300 dark:border-gray-500 bg-gray-200 dark:bg-gray-600"
                    :style="{
                      width: fmt.id === '9:16' ? '20px' : '28px',
                      height: fmt.id === '9:16' ? '36px' : '28px',
                    }"
                  ></div>
                  <div>
                    <span class="font-bold text-gray-900 dark:text-white text-sm">{{ fmt.label }}</span>
                    <span class="text-xs text-gray-500 dark:text-gray-400 ml-1">({{ fmt.width }}&times;{{ fmt.height }})</span>
                    <p class="text-xs text-gray-500 dark:text-gray-400">{{ fmt.desc }}</p>
                  </div>
                </div>
                <span
                  v-if="exportFormat === fmt.id"
                  class="absolute top-2 right-2 text-[#3B7AB1] text-sm font-bold"
                >&#10003;</span>
              </button>
            </div>
          </div>

          <div class="flex items-center gap-3 mb-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-sm text-gray-600 dark:text-gray-400">
            <span class="text-lg">&#9432;</span>
            <div>
              <strong>Format:</strong> PNG &middot; <strong>Aufloesung:</strong> {{ exportWidth }} &times; {{ exportHeight }} px &middot; <strong>Seitenverhaeltnis:</strong> {{ exportFormat }}
            </div>
          </div>

          <div v-if="!exportComplete" class="flex flex-col sm:flex-row gap-3">
            <button
              @click="saveAndExport"
              :disabled="!canExport || exporting"
              class="flex-1 px-6 py-3 bg-[#3B7AB1] hover:bg-[#2E6A9E] disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white font-bold rounded-lg transition-colors flex items-center justify-center gap-2 disabled:cursor-not-allowed"
            >
              <span v-if="exporting" class="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></span>
              {{ exporting ? 'Exportiere...' : 'Speichern & als PNG exportieren' }}
            </button>
            <button
              @click="downloadAsPngWithImage"
              :disabled="!canExport"
              class="flex-1 px-6 py-3 bg-[#FDD000] hover:bg-[#e5c000] disabled:bg-gray-300 text-[#1A1A2E] font-bold rounded-lg transition-colors flex items-center justify-center gap-2 disabled:cursor-not-allowed"
            >
              &#11015; Nur PNG herunterladen
            </button>
          </div>

          <!-- Export complete -->
          <div v-if="exportComplete" class="text-center py-4">
            <div class="text-4xl mb-2">&#127881;</div>
            <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-1">Thumbnail erstellt!</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">Post #{{ savedPost?.id }} in Datenbank gespeichert. PNG heruntergeladen.</p>
            <div class="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                @click="downloadAsPngWithImage"
                class="px-5 py-2 bg-[#FDD000] hover:bg-[#e5c000] text-[#1A1A2E] font-bold rounded-lg transition-colors text-sm"
              >
                &#11015; Nochmal herunterladen
              </button>
              <button
                @click="reset"
                class="px-5 py-2 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium rounded-lg transition-colors text-sm"
              >
                Neues Thumbnail
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Live Preview -->
      <div data-tour="tg-preview" class="lg:sticky lg:top-4 self-start">
        <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Live-Vorschau ({{ exportFormat }})</h2>

        <div
          id="thumbnail-preview"
          class="rounded-2xl overflow-hidden shadow-xl border border-gray-200 dark:border-gray-700 relative mx-auto"
          :style="previewStyle"
        >
          <!-- Overlay for image backgrounds -->
          <div
            v-if="backgroundType === 'image'"
            class="absolute inset-0 bg-black/40"
          ></div>

          <!-- Content -->
          <div class="absolute inset-0 p-5 flex flex-col justify-between" style="z-index: 1;">
            <!-- TREFF logo -->
            <div class="flex items-center gap-1.5">
              <div class="bg-[#3B7AB1] rounded px-2 py-0.5">
                <span class="text-white text-[10px] font-bold">TREFF</span>
              </div>
              <span class="text-gray-400 text-[9px]">Sprachreisen</span>
            </div>

            <!-- Hook text centered -->
            <div class="flex-1 flex items-center justify-center px-2">
              <p
                v-if="hookText.trim()"
                class="font-black text-center leading-tight break-words"
                :style="{
                  color: textColor,
                  fontSize: hookFontSize,
                  textShadow: backgroundType === 'image' ? '0 2px 8px rgba(0,0,0,0.5)' : 'none',
                }"
              >
                {{ hookText.trim() }}
              </p>
              <p v-else class="text-gray-500 text-sm text-center italic">
                Hook-Text eingeben...
              </p>
            </div>

            <!-- CTA button -->
            <div class="flex flex-col items-center gap-2">
              <div class="inline-block bg-[#FDD000] text-[#1A1A2E] px-4 py-1.5 rounded-full font-bold text-[10px]">
                Jetzt ansehen
              </div>
              <span
                class="text-[8px]"
                :style="{ color: textColor === '#FFFFFF' ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.3)' }"
              >
                TREFF Sprachreisen
              </span>
            </div>
          </div>
        </div>

        <!-- Dimensions info -->
        <div class="mt-3 text-center">
          <span class="inline-flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 px-3 py-1.5 rounded-full">
            <span>&#128247;</span> {{ exportWidth }} &times; {{ exportHeight }} px &middot; {{ exportFormat }}
          </span>
        </div>
      </div>
    </div>

    <VideoWorkflowTour ref="workflowTourRef" />
    <TourSystem ref="tourRef" page-key="thumbnail-generator" />
  </div>
</template>
