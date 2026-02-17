<script setup>
/**
 * Step1Content.vue — Schritt 1: Inhalt
 *
 * Combined content creation step:
 * - Category selection (quick chips)
 * - Topic/key points text input
 * - Country & tone selection
 * - AI text generation
 * - Image upload or AI image generation
 */
import { ref, computed, watch, onMounted } from 'vue'
import { usePostCreator } from '@/composables/usePostCreator'
import HelpTooltip from '@/components/common/HelpTooltip.vue'
import ImageUploader from '@/components/assets/ImageUploader.vue'
import api from '@/utils/api'
import { CATEGORY_TO_PILLAR, getPillarById } from '@/config/contentPillars'

const {
  selectedCategory,
  selectedPillar,
  topic,
  keyPoints,
  country,
  tone,
  selectedTemplate,
  slides,
  captionInstagram,
  captionTiktok,
  hashtagsInstagram,
  hashtagsTiktok,
  ctaText,
  currentPreviewSlide,
  generatingText,
  generatedContent,
  loading,
  error,
  successMsg,
  uploadingImage,
  assets,
  aiImagePrompt,
  aiImageAspectRatio,
  generatingImage,
  generatedImageResult,
  aiImageError,
  selectedPlatform,
  toast,
  store,
} = usePostCreator()

// ── Static data ─────────────────────────────────────────────────────
const categories = [
  { id: 'laender_spotlight', label: 'Laender-Spotlight', icon: '🌍' },
  { id: 'erfahrungsberichte', label: 'Erfahrungsberichte', icon: '💬' },
  { id: 'infografiken', label: 'Infografiken', icon: '📊' },
  { id: 'fristen_cta', label: 'Fristen & CTA', icon: '⏰' },
  { id: 'tipps_tricks', label: 'Tipps & Tricks', icon: '💡' },
  { id: 'faq', label: 'FAQ', icon: '❓' },
  { id: 'foto_posts', label: 'Foto-Posts', icon: '📸' },
  { id: 'reel_tiktok_thumbnails', label: 'Reel/TikTok', icon: '🎬' },
  { id: 'story_posts', label: 'Story-Posts', icon: '📱' },
  { id: 'story_teaser', label: 'Story-Teaser', icon: '👉' },
  { id: 'story_series', label: 'Story-Serien', icon: '📚' },
]

// Auto-assign content pillar from category
const selectedPillarObj = computed(() => selectedPillar.value ? getPillarById(selectedPillar.value) : null)
watch(selectedCategory, (newCat) => {
  if (newCat && CATEGORY_TO_PILLAR[newCat]) {
    selectedPillar.value = CATEGORY_TO_PILLAR[newCat]
  }
})

const countries = [
  { id: 'usa', label: 'USA', flag: '🇺🇸' },
  { id: 'canada', label: 'Kanada', flag: '🇨🇦' },
  { id: 'australia', label: 'Australien', flag: '🇦🇺' },
  { id: 'newzealand', label: 'Neuseeland', flag: '🇳🇿' },
  { id: 'ireland', label: 'Irland', flag: '🇮🇪' },
]

const toneOptions = [
  { id: 'jugendlich', label: 'Jugendlich', icon: '🎯' },
  { id: 'serioess', label: 'Serioes', icon: '🏛️' },
  { id: 'witzig', label: 'Witzig', icon: '😂' },
  { id: 'emotional', label: 'Emotional', icon: '🥺' },
  { id: 'motivierend', label: 'Motivierend', icon: '💪' },
  { id: 'informativ', label: 'Informativ', icon: '📊' },
  { id: 'storytelling', label: 'Storytelling', icon: '📖' },
]

// ── AI Generation ───────────────────────────────────────────────────
let generationRequestCounter = 0

async function generateContent() {
  if (generatingText.value) return
  if (!topic.value?.trim() && !selectedCategory.value) {
    error.value = 'Bitte gib ein Thema ein oder waehle eine Kategorie.'
    return
  }

  generatingText.value = true
  error.value = ''
  const requestId = ++generationRequestCounter

  try {
    const slideCount = selectedTemplate.value?.slide_count || 3
    const response = await api.post('/api/ai/generate-text', {
      category: selectedCategory.value || 'laender_spotlight',
      topic: topic.value?.trim() || null,
      key_points: keyPoints.value?.trim() || null,
      country: country.value || null,
      platform: selectedPlatform.value || 'instagram_feed',
      slide_count: slideCount,
      tone: tone.value || 'jugendlich',
    })

    if (requestId !== generationRequestCounter) return

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
    if (requestId !== generationRequestCounter) return
    const detail = e.response?.data?.detail || e.message
    error.value = 'Textgenerierung fehlgeschlagen: ' + detail
  } finally {
    generatingText.value = false
  }
}

// ── Image upload handler ────────────────────────────────────────────
function onImageUpload({ url }) {
  if (slides.value.length > 0) {
    const slide = slides.value[currentPreviewSlide.value] || slides.value[0]
    slide.background_type = 'image'
    slide.background_value = url
    toast.success('Bild als Hintergrund gesetzt')
  }
}

async function loadAssets() {
  try {
    const res = await api.get('/api/assets')
    assets.value = res.data?.assets || res.data || []
  } catch { /* ignore */ }
}

onMounted(() => {
  loadAssets()
})

// ── AI Image generation ─────────────────────────────────────────────
async function generateAiImage() {
  if (!aiImagePrompt.value?.trim()) {
    aiImageError.value = 'Bitte gib einen Prompt ein.'
    return
  }
  if (generatingImage.value) return
  generatingImage.value = true
  aiImageError.value = ''

  try {
    const response = await api.post('/api/ai/generate-image', {
      prompt: aiImagePrompt.value.trim(),
      platform: selectedPlatform.value || 'instagram_feed',
      category: 'ai_generated',
      country: country.value || null,
    })
    generatedImageResult.value = response.data

    if (response.data.image_url && slides.value.length > 0) {
      const slide = slides.value[currentPreviewSlide.value] || slides.value[0]
      slide.background_type = 'image'
      slide.background_value = response.data.image_url
      toast.success('KI-Bild generiert und als Hintergrund gesetzt')
    }
  } catch (e) {
    aiImageError.value = 'Bildgenerierung fehlgeschlagen: ' + (e.response?.data?.detail || e.message)
  } finally {
    generatingImage.value = false
  }
}
</script>

<template>
  <div class="space-y-6" data-testid="step1-content">
    <!-- Category chips -->
    <div>
      <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Kategorie</label>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="cat in categories"
          :key="cat.id"
          @click="selectedCategory = cat.id"
          class="px-3 py-1.5 rounded-full text-sm font-medium transition-all border"
          :class="selectedCategory === cat.id
            ? 'bg-[#3B7AB1] text-white border-[#3B7AB1]'
            : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-[#3B7AB1] hover:text-[#3B7AB1]'"
          :data-testid="'cat-chip-' + cat.id"
        >
          <span class="mr-1">{{ cat.icon }}</span>{{ cat.label }}
        </button>
      </div>
      <!-- Content Pillar badge -->
      <div v-if="selectedPillarObj" class="mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs border" :style="{ borderColor: selectedPillarObj.color + '40', backgroundColor: selectedPillarObj.color + '08' }">
        <span>{{ selectedPillarObj.icon }}</span>
        <span class="text-gray-600 dark:text-gray-400">Content Pillar:</span>
        <span class="font-medium text-white px-1.5 py-0.5 rounded" :style="{ backgroundColor: selectedPillarObj.color }">{{ selectedPillarObj.name }}</span>
        <span class="text-gray-400 dark:text-gray-500">({{ selectedPillarObj.targetPercentage }}%)</span>
      </div>
    </div>

    <!-- Topic & Key Points -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Thema / Ueberschrift</label>
        <textarea
          v-model="topic"
          rows="3"
          class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent resize-none"
          placeholder="z.B. Highschool-Aufenthalt in den USA - Erfahrungen"
          data-testid="topic-input"
        ></textarea>
      </div>
      <div>
        <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Stichpunkte (optional)</label>
        <textarea
          v-model="keyPoints"
          rows="3"
          class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent resize-none"
          placeholder="z.B. Gastfamilie, Sportteam, Schulalltag"
          data-testid="keypoints-input"
        ></textarea>
      </div>
    </div>

    <!-- Country & Tone row -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Land</label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="c in countries"
            :key="c.id"
            @click="country = country === c.id ? '' : c.id"
            class="px-3 py-1.5 rounded-lg text-sm font-medium transition-all border"
            :class="country === c.id
              ? 'bg-[#3B7AB1] text-white border-[#3B7AB1]'
              : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-[#3B7AB1]'"
            :data-testid="'country-' + c.id"
          >
            {{ c.flag }} {{ c.label }}
          </button>
        </div>
      </div>
      <div>
        <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Tonalitaet</label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="t in toneOptions"
            :key="t.id"
            @click="tone = t.id"
            class="px-2.5 py-1 rounded-lg text-xs font-medium transition-all border"
            :class="tone === t.id
              ? 'bg-[#FDD000] text-[#1A1A2E] border-[#FDD000]'
              : 'bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-[#FDD000]'"
          >
            {{ t.icon }} {{ t.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- Generate Button -->
    <div class="flex items-center gap-3">
      <button
        @click="generateContent"
        :disabled="generatingText || (!topic?.trim() && !selectedCategory)"
        class="px-6 py-3 rounded-xl font-bold text-sm transition-all flex items-center gap-2"
        :class="generatingText
          ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-wait'
          : 'bg-[#3B7AB1] hover:bg-[#2E6A9E] text-white shadow-lg shadow-[#3B7AB1]/20'"
        data-testid="generate-btn"
      >
        <span v-if="generatingText" class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
        <span v-else>&#x2728;</span>
        {{ generatingText ? 'Generiere...' : 'Mit KI generieren' }}
      </button>

      <div v-if="slides.length > 0" class="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
        <span>&#10003;</span>
        <span>{{ slides.length }} Slides generiert</span>
      </div>
    </div>

    <!-- Success message -->
    <div v-if="successMsg" class="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-green-700 dark:text-green-300 text-sm flex items-center gap-2">
      <span>&#10003;</span> {{ successMsg }}
    </div>

    <!-- Error message -->
    <div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300 text-sm flex items-center gap-2">
      <span>&#9888;</span>
      <span class="flex-1">{{ error }}</span>
      <button @click="error = ''" class="text-red-500 hover:text-red-700">&times;</button>
    </div>

    <!-- Divider -->
    <div class="relative">
      <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-gray-200 dark:border-gray-700"></div></div>
      <div class="relative flex justify-center"><span class="bg-white dark:bg-gray-900 px-3 text-sm text-gray-400">Bilder (optional)</span></div>
    </div>

    <!-- Image section: Upload or AI Generate -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Upload -->
      <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-6 hover:border-[#3B7AB1] transition-colors">
        <div class="text-3xl mb-2 text-center">&#128247;</div>
        <p class="text-sm text-gray-600 dark:text-gray-400 mb-3 text-center">Bild hochladen</p>
        <ImageUploader
          :max-images="10"
          :max-file-size="10485760"
          :accepted-types="['image/jpeg', 'image/png', 'image/webp']"
          category="background"
          @upload="onImageUpload"
          data-testid="step1-image-upload"
        />
      </div>

      <!-- AI Image -->
      <div class="border-2 border-purple-200 dark:border-purple-700 rounded-xl p-6 bg-purple-50/30 dark:bg-purple-900/10">
        <div class="text-3xl mb-2 text-center">&#129302;</div>
        <p class="text-sm text-purple-700 dark:text-purple-300 mb-3 text-center font-medium">KI-Bild generieren</p>
        <textarea
          v-model="aiImagePrompt"
          rows="2"
          class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-purple-400 resize-none mb-2"
          placeholder="z.B. American high school hallway with students"
          :disabled="generatingImage"
        ></textarea>
        <button
          @click="generateAiImage"
          :disabled="generatingImage || !aiImagePrompt?.trim()"
          class="w-full px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="generatingImage
            ? 'bg-gray-300 text-gray-500 cursor-wait'
            : 'bg-purple-600 hover:bg-purple-700 text-white'"
          data-testid="ai-image-btn"
        >
          <span v-if="generatingImage" class="flex items-center gap-2 justify-center">
            <span class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
            Generiere...
          </span>
          <span v-else>&#129302; Bild generieren</span>
        </button>
        <div v-if="aiImageError" class="mt-2 text-xs text-red-500">{{ aiImageError }}</div>
        <div v-if="generatedImageResult?.image_url" class="mt-2 rounded-lg overflow-hidden border border-purple-200">
          <img :src="generatedImageResult.image_url" class="w-full h-24 object-cover" alt="KI-generiertes Bild" />
        </div>
      </div>
    </div>
  </div>
</template>
