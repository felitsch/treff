<script setup>
/**
 * Step3Finalize.vue — Schritt 3: Fertigstellen
 *
 * Platform selection, captions, hashtags, scheduling, and export:
 * - Platform toggle (Instagram Feed, Story, TikTok)
 * - Caption editing (Instagram + TikTok)
 * - Hashtag generation
 * - Export quality selection
 * - Save & Export button
 */
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import JSZip from 'jszip'
import { usePostCreator } from '@/composables/usePostCreator'
import api from '@/utils/api'
import SmartScheduler from '@/components/creator/SmartScheduler.vue'

const router = useRouter()

const {
  selectedCategory,
  selectedTemplate,
  selectedPlatform,
  selectedPlatforms,
  slides,
  currentPreviewSlide,
  captionInstagram,
  captionTiktok,
  hashtagsInstagram,
  hashtagsTiktok,
  ctaText,
  exporting,
  savedPost,
  exportComplete,
  exportQuality,
  networkError,
  error,
  successMsg,
  topic,
  country,
  tone,
  toast,
  resetCreator,
} = usePostCreator()

// Smart scheduling state
const scheduleSelection = ref({ date: '', time: '' })

const platforms = [
  { id: 'instagram_feed', label: 'Instagram Feed', icon: '📷', format: '1:1' },
  { id: 'instagram_story', label: 'Instagram Story', icon: '📱', format: '9:16' },
  { id: 'tiktok', label: 'TikTok', icon: '🎵', format: '9:16' },
]

function togglePlatform(platformId) {
  const idx = selectedPlatforms.value.indexOf(platformId)
  if (idx >= 0) {
    if (selectedPlatforms.value.length > 1) {
      selectedPlatforms.value.splice(idx, 1)
    }
  } else {
    selectedPlatforms.value.push(platformId)
  }
  // Update primary platform
  selectedPlatform.value = selectedPlatforms.value[0] || 'instagram_feed'
}

// ── Hashtag suggestions ──────────────────────────────────────────
const suggestingHashtags = ref(false)

async function suggestHashtags() {
  if (suggestingHashtags.value) return
  suggestingHashtags.value = true
  try {
    const res = await api.post('/api/ai/suggest-hashtags', {
      topic: topic.value || '',
      country: country.value || '',
      platform: selectedPlatform.value || 'instagram_feed',
      category: selectedCategory.value || '',
      tone: tone.value || 'jugendlich',
    })
    if (res.data?.hashtag_string) {
      hashtagsInstagram.value = res.data.hashtag_string
      hashtagsTiktok.value = res.data.hashtag_string
    }
    toast.success('Hashtags generiert')
  } catch {
    toast.error('Hashtag-Vorschlag fehlgeschlagen')
  } finally {
    suggestingHashtags.value = false
  }
}

// ── Platform dimensions ──────────────────────────────────────────
function getDimensions(platform) {
  const scale = exportQuality.value === '2160' ? 2 : 1
  switch (platform || selectedPlatform.value) {
    case 'instagram_story':
    case 'tiktok':
      return { w: 1080 * scale, h: 1920 * scale }
    case 'instagram_feed':
    default:
      return { w: 1080 * scale, h: 1080 * scale }
  }
}

// ── Canvas rendering ─────────────────────────────────────────────
function renderSlideToCanvas(slideIndex, platform) {
  const dims = getDimensions(platform)
  const scale = exportQuality.value === '2160' ? 2 : 1
  const canvas = document.createElement('canvas')
  canvas.width = dims.w
  canvas.height = dims.h
  const ctx = canvas.getContext('2d')

  const slide = slides.value[slideIndex]
  if (!slide) return null

  // Background
  if (slide.background_type === 'color' && slide.background_value) {
    ctx.fillStyle = slide.background_value
  } else {
    ctx.fillStyle = '#1A1A2E'
  }
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  // TREFF logo bar
  ctx.fillStyle = '#3B7AB1'
  const logoW = 80 * scale
  const logoH = 28 * scale
  const logoX = 40 * scale
  const logoY = 40 * scale
  ctx.beginPath()
  ctx.roundRect(logoX, logoY, logoW, logoH, 6 * scale)
  ctx.fill()
  ctx.fillStyle = '#FFFFFF'
  ctx.font = `bold ${14 * scale}px sans-serif`
  ctx.textAlign = 'center'
  ctx.fillText('TREFF', logoX + logoW / 2, logoY + 19 * scale)

  // Headline
  if (slide.headline) {
    ctx.fillStyle = '#FFFFFF'
    ctx.font = `extrabold ${28 * scale}px sans-serif`
    ctx.textAlign = 'left'
    const headlineY = canvas.height * 0.4
    ctx.fillText(slide.headline, 40 * scale, headlineY, canvas.width - 80 * scale)
  }

  // Subheadline
  if (slide.subheadline) {
    ctx.fillStyle = '#FDD000'
    ctx.font = `bold ${16 * scale}px sans-serif`
    ctx.fillText(slide.subheadline, 40 * scale, canvas.height * 0.4 + 36 * scale, canvas.width - 80 * scale)
  }

  // Body text
  if (slide.body_text) {
    ctx.fillStyle = '#d1d5db'
    ctx.font = `${14 * scale}px sans-serif`
    const bodyY = canvas.height * 0.4 + 70 * scale
    // Simple word wrap
    const words = slide.body_text.split(' ')
    let line = ''
    let y = bodyY
    const maxWidth = canvas.width - 80 * scale
    for (const word of words) {
      const test = line + word + ' '
      if (ctx.measureText(test).width > maxWidth && line) {
        ctx.fillText(line.trim(), 40 * scale, y)
        line = word + ' '
        y += 20 * scale
        if (y > canvas.height - 100 * scale) break
      } else {
        line = test
      }
    }
    if (line.trim()) ctx.fillText(line.trim(), 40 * scale, y)
  }

  // CTA button
  if (slide.cta_text) {
    const ctaY = canvas.height - 80 * scale
    ctx.fillStyle = '#FDD000'
    const ctaW = ctx.measureText(slide.cta_text).width + 40 * scale
    ctx.beginPath()
    ctx.roundRect(40 * scale, ctaY, ctaW, 36 * scale, 18 * scale)
    ctx.fill()
    ctx.fillStyle = '#1A1A2E'
    ctx.font = `bold ${14 * scale}px sans-serif`
    ctx.textAlign = 'center'
    ctx.fillText(slide.cta_text, 40 * scale + ctaW / 2, ctaY + 24 * scale)
  }

  return canvas
}

// ── Save & Export ────────────────────────────────────────────────
async function saveAndExport() {
  if (exporting.value) return
  exporting.value = true
  error.value = ''

  try {
    // Save post to DB
    const cleanSlides = slides.value.map(({ dragId, _templateColors, _templateFonts, _templateId, ...rest }) => rest)
    // Determine status based on scheduling
    const hasSchedule = scheduleSelection.value.date && scheduleSelection.value.time
    const postStatus = hasSchedule ? 'scheduled' : 'draft'

    const postData = {
      category: selectedCategory.value || 'laender_spotlight',
      country: country.value || null,
      platform: selectedPlatform.value || 'instagram_feed',
      title: slides.value[0]?.headline || topic.value || 'Post',
      status: postStatus,
      slide_data: JSON.stringify(cleanSlides),
      caption_instagram: captionInstagram.value,
      caption_tiktok: captionTiktok.value,
      hashtags_instagram: hashtagsInstagram.value,
      hashtags_tiktok: hashtagsTiktok.value,
      cta_text: ctaText.value || slides.value[slides.value.length - 1]?.cta_text || '',
      template_id: selectedTemplate.value?.id || null,
      scheduled_date: hasSchedule ? scheduleSelection.value.date : null,
      scheduled_time: hasSchedule ? scheduleSelection.value.time : null,
    }

    const response = await api.post('/api/posts', postData)
    savedPost.value = response.data

    // Record the export
    const exportEndpoint = slides.value.length > 1 ? '/api/export/render-carousel' : '/api/export/render'
    await api.post(exportEndpoint, {
      post_id: response.data.id,
      platform: selectedPlatform.value,
      resolution: exportQuality.value,
      slide_count: slides.value.length,
    })

    // Download
    if (slides.value.length > 1) {
      await downloadAsZip()
    } else {
      downloadAsImage(0)
    }

    exportComplete.value = true
    toast.success('Post gespeichert und exportiert!')
  } catch (e) {
    error.value = 'Export fehlgeschlagen: ' + (e.response?.data?.detail || e.message)
    networkError.value = true
  } finally {
    exporting.value = false
  }
}

function downloadAsImage(slideIndex) {
  const canvas = renderSlideToCanvas(slideIndex)
  if (!canvas) return
  const link = document.createElement('a')
  const date = new Date().toISOString().split('T')[0]
  link.download = `TREFF_${selectedCategory.value}_${selectedPlatform.value}_${date}.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
}

async function downloadAsZip() {
  const zip = new JSZip()
  const date = new Date().toISOString().split('T')[0]
  for (let i = 0; i < slides.value.length; i++) {
    const canvas = renderSlideToCanvas(i)
    if (!canvas) continue
    const dataUrl = canvas.toDataURL('image/png')
    const base64 = dataUrl.split(',')[1]
    zip.file(`TREFF_${selectedCategory.value}_${selectedPlatform.value}_${date}_${String(i + 1).padStart(2, '0')}.png`, base64, { base64: true })
  }
  const content = await zip.generateAsync({ type: 'blob' })
  const link = document.createElement('a')
  link.download = `TREFF_${selectedCategory.value}_${selectedPlatform.value}_${date}_carousel.zip`
  link.href = URL.createObjectURL(content)
  link.click()
  URL.revokeObjectURL(link.href)
}

function startNewPost() {
  resetCreator()
}
</script>

<template>
  <div class="space-y-6" data-testid="step3-finalize">
    <!-- Export complete state -->
    <div v-if="exportComplete" class="max-w-lg mx-auto bg-white dark:bg-gray-800 rounded-2xl border border-green-200 dark:border-green-800 p-8 text-center">
      <div class="text-6xl mb-4">&#127881;</div>
      <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">Post erfolgreich erstellt!</h3>
      <p class="text-gray-500 dark:text-gray-400 mb-4">
        Dein Post wurde in der Datenbank gespeichert und als exportiert markiert.
      </p>
      <div v-if="savedPost" class="text-sm text-gray-600 dark:text-gray-400 mb-6 space-y-1">
        <div>Post ID: <strong>#{{ savedPost.id }}</strong></div>
        <div>Status: <strong>{{ savedPost.status }}</strong></div>
      </div>
      <div class="flex flex-col sm:flex-row gap-3 justify-center">
        <button
          v-if="slides.length > 1"
          @click="downloadAsZip"
          class="px-6 py-3 bg-[#FDD000] hover:bg-[#e5c000] text-[#1A1A2E] font-bold rounded-lg"
        >&#128230; ZIP erneut herunterladen</button>
        <button v-else @click="downloadAsImage(0)" class="px-6 py-3 bg-[#FDD000] hover:bg-[#e5c000] text-[#1A1A2E] font-bold rounded-lg">
          &#11015; PNG herunterladen
        </button>
        <button @click="router.push('/home')" class="px-6 py-3 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white font-bold rounded-lg">Startseite</button>
        <button @click="startNewPost" class="px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg">Neuen Post</button>
      </div>
    </div>

    <!-- Normal finalize flow -->
    <template v-else>
      <!-- Platform Selection -->
      <div>
        <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Plattformen</label>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <button
            v-for="p in platforms"
            :key="p.id"
            @click="togglePlatform(p.id)"
            class="relative flex items-center gap-3 p-4 rounded-xl border-2 transition-all"
            :class="selectedPlatforms.includes(p.id)
              ? 'border-[#3B7AB1] bg-[#3B7AB1]/5 dark:bg-[#3B7AB1]/10'
              : 'border-gray-200 dark:border-gray-700 hover:border-gray-400'"
            :data-testid="'platform-' + p.id"
          >
            <span class="text-2xl">{{ p.icon }}</span>
            <div>
              <div class="font-semibold text-sm text-gray-900 dark:text-white">{{ p.label }}</div>
              <div class="text-xs text-gray-400">{{ p.format }}</div>
            </div>
            <span
              v-if="selectedPlatforms.includes(p.id)"
              class="absolute top-2 right-2 w-5 h-5 bg-[#3B7AB1] rounded-full flex items-center justify-center text-white text-xs"
            >&#10003;</span>
          </button>
        </div>
      </div>

      <!-- Captions & Hashtags -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Instagram -->
        <div class="space-y-3">
          <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <label class="text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 block">&#128247; Instagram Caption</label>
            <textarea v-model="captionInstagram" rows="3"
              class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1] resize-none"
              data-testid="caption-instagram"
            ></textarea>
            <div class="text-xs text-gray-400 text-right mt-0.5">{{ captionInstagram?.length || 0 }} / 2200</div>
          </div>
          <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-bold text-gray-700 dark:text-gray-300">#️⃣ Instagram Hashtags</label>
              <button @click="suggestHashtags" :disabled="suggestingHashtags"
                class="text-xs text-[#3B7AB1] hover:text-[#2E6A9E] font-medium disabled:opacity-50"
                data-testid="suggest-hashtags-btn"
              >
                {{ suggestingHashtags ? 'Lade...' : '&#x2728; Auto-Suggest' }}
              </button>
            </div>
            <textarea v-model="hashtagsInstagram" rows="2"
              class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-blue-600 dark:text-blue-400 text-sm focus:ring-2 focus:ring-[#3B7AB1] resize-none"
            ></textarea>
          </div>
        </div>

        <!-- TikTok -->
        <div class="space-y-3">
          <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <label class="text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 block">&#127925; TikTok Caption</label>
            <textarea v-model="captionTiktok" rows="3"
              class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1] resize-none"
              data-testid="caption-tiktok"
            ></textarea>
            <div class="text-xs text-gray-400 text-right mt-0.5">{{ captionTiktok?.length || 0 }} / 2200</div>
          </div>
          <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <label class="text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 block">&#127925; TikTok Hashtags</label>
            <textarea v-model="hashtagsTiktok" rows="2"
              class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-blue-600 dark:text-blue-400 text-sm focus:ring-2 focus:ring-[#3B7AB1] resize-none"
            ></textarea>
          </div>
        </div>
      </div>

      <!-- Smart Scheduling -->
      <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800" data-testid="smart-scheduling-section">
        <SmartScheduler
          :platform="selectedPlatform"
          v-model="scheduleSelection"
        />
      </div>

      <!-- Export Quality -->
      <div>
        <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Export-Qualitaet</label>
        <div class="flex gap-3">
          <button
            @click="exportQuality = '1080'"
            class="px-4 py-2 rounded-lg border-2 text-sm font-medium transition-all"
            :class="exportQuality === '1080' ? 'border-[#3B7AB1] bg-[#3B7AB1]/5 text-[#3B7AB1]' : 'border-gray-200 dark:border-gray-700 text-gray-500'"
          >1080p (Standard)</button>
          <button
            @click="exportQuality = '2160'"
            class="px-4 py-2 rounded-lg border-2 text-sm font-medium transition-all"
            :class="exportQuality === '2160' ? 'border-[#3B7AB1] bg-[#3B7AB1]/5 text-[#3B7AB1]' : 'border-gray-200 dark:border-gray-700 text-gray-500'"
          >2160p (4K)</button>
        </div>
      </div>

      <!-- Error -->
      <div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300 text-sm">
        {{ error }}
      </div>

      <!-- Export button -->
      <div class="flex gap-3">
        <button
          @click="saveAndExport"
          :disabled="exporting || selectedPlatforms.length === 0"
          class="flex-1 px-6 py-3 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2"
          :class="exporting
            ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-wait'
            : 'bg-[#3B7AB1] hover:bg-[#2E6A9E] text-white shadow-lg shadow-[#3B7AB1]/20'"
          data-testid="export-btn"
        >
          <span v-if="exporting" class="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></span>
          {{ exporting ? 'Exportiere...' : 'Post speichern & exportieren' }}
        </button>
        <button
          v-if="slides.length > 1 && !exporting"
          @click="downloadAsZip"
          class="px-6 py-3 bg-[#FDD000] hover:bg-[#e5c000] text-[#1A1A2E] font-bold rounded-xl"
        >
          &#128230; ZIP ({{ slides.length }} Slides)
        </button>
      </div>
    </template>
  </div>
</template>
