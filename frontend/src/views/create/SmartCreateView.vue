<script setup>
/**
 * SmartCreateView — Upload-First AI-Powered Post Creation Flow
 *
 * Flow: Upload media → AI analyzes → Shows suggestions → User reviews/edits → Save as draft
 *
 * Steps:
 * 1. MediaUploadZone: Full-width drag-and-drop area for image/video upload
 * 2. Analysis loading: Shimmer "AI analysiert dein Bild..." state
 * 3. AI Suggestion Review: Editable fields for post-type, caption, hashtags, template, platform
 * 4. Live preview on the right side
 * 5. One-click "Speichern & Planen" to save everything at once
 *
 * @see /api/pipeline/analyze-media — AI analysis endpoint
 * @see /api/pipeline/process — Create draft post from analysis
 */
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const toast = useToast()

// ─── Step management ─────────────────────────────────────────
const currentStep = ref('upload') // 'upload' | 'analyzing' | 'review' | 'saving'

// ─── Upload state ────────────────────────────────────────────
const uploadedFile = ref(null)
const uploadPreviewUrl = ref(null)
const isDragging = ref(false)

// ─── Analysis results ────────────────────────────────────────
const pipelineItemId = ref(null)
const analysisResult = ref(null)

// ─── Editable suggestion fields ──────────────────────────────
const suggestions = ref({
  postType: 'instagram_feed',
  caption: '',
  hashtags: [],
  hashtagInput: '',
  platform: 'instagram',
  country: null,
  tone: 'jugendlich',
  title: '',
  analysisSummary: '',
})

// ─── Save state ──────────────────────────────────────────────
const isSaving = ref(false)
const savedPostId = ref(null)

// ─── Post type options ───────────────────────────────────────
const postTypeOptions = [
  { value: 'instagram_feed', label: 'Feed Post', icon: '📸', description: 'Standard Instagram Post' },
  { value: 'instagram_story', label: 'Story', icon: '📱', description: 'Instagram Story (9:16)' },
  { value: 'tiktok', label: 'Reel/TikTok', icon: '🎵', description: 'Kurzvideo fuer Reels/TikTok' },
  { value: 'carousel', label: 'Carousel', icon: '🎠', description: 'Mehrere Slides als Carousel' },
]

const platformOptions = [
  { value: 'instagram', label: 'Instagram', icon: '📸' },
  { value: 'tiktok', label: 'TikTok', icon: '🎵' },
]

const toneOptions = [
  { value: 'jugendlich', label: 'Jugendlich' },
  { value: 'serioes', label: 'Serioes' },
  { value: 'witzig', label: 'Witzig' },
  { value: 'emotional', label: 'Emotional' },
  { value: 'motivierend', label: 'Motivierend' },
  { value: 'informativ', label: 'Informativ' },
]

const countryOptions = [
  { value: 'usa', label: 'USA', emoji: '🇺🇸' },
  { value: 'kanada', label: 'Kanada', emoji: '🇨🇦' },
  { value: 'australien', label: 'Australien', emoji: '🇦🇺' },
  { value: 'neuseeland', label: 'Neuseeland', emoji: '🇳🇿' },
  { value: 'irland', label: 'Irland', emoji: '🇮🇪' },
]

// ─── File handling ───────────────────────────────────────────
const ALLOWED_TYPES = [
  'image/jpeg', 'image/png', 'image/webp',
  'video/mp4', 'video/quicktime', 'video/webm',
]

function onDragOver(e) {
  e.preventDefault()
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

function onDrop(e) {
  e.preventDefault()
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) handleFile(file)
}

function onFileSelect(e) {
  const file = e.target?.files?.[0]
  if (file) handleFile(file)
}

function handleFile(file) {
  if (!ALLOWED_TYPES.includes(file.type)) {
    toast.error('Ungueltiger Dateityp. Erlaubt: JPEG, PNG, WebP, MP4, MOV, WebM')
    return
  }
  if (file.size > 100 * 1024 * 1024) {
    toast.error('Datei zu gross. Maximal 100 MB.')
    return
  }

  uploadedFile.value = file
  uploadPreviewUrl.value = URL.createObjectURL(file)
  analyzeMedia()
}

const isVideo = computed(() => {
  return uploadedFile.value?.type?.startsWith('video/')
})

// ─── AI Analysis ─────────────────────────────────────────────
async function analyzeMedia() {
  currentStep.value = 'analyzing'

  const formData = new FormData()
  formData.append('file', uploadedFile.value)

  try {
    const res = await api.post('/api/pipeline/analyze-media', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    analysisResult.value = res.data
    pipelineItemId.value = res.data.pipeline_item_id

    // Populate suggestions from AI results
    suggestions.value.postType = res.data.suggested_post_type || 'instagram_feed'
    suggestions.value.caption = Array.isArray(res.data.suggested_caption_seeds)
      ? res.data.suggested_caption_seeds[0] || ''
      : ''
    suggestions.value.country = res.data.detected_country || null
    suggestions.value.analysisSummary = res.data.analysis_summary || ''
    suggestions.value.title = res.data.analysis_summary
      ? res.data.analysis_summary.substring(0, 60)
      : 'Smart Post'

    // Set platform from post type
    if (res.data.suggested_post_type === 'tiktok') {
      suggestions.value.platform = 'tiktok'
    } else {
      suggestions.value.platform = 'instagram'
    }

    // Generate hashtag suggestions from platforms and caption
    const defaultHashtags = ['treffsprachreisen', 'highschool', 'auslandsjahr']
    if (res.data.detected_country) {
      defaultHashtags.push(res.data.detected_country.toLowerCase())
    }
    suggestions.value.hashtags = defaultHashtags

    currentStep.value = 'review'
  } catch (err) {
    toast.error('AI-Analyse fehlgeschlagen. Bitte versuche es erneut.')
    currentStep.value = 'upload'
  }
}

// ─── Re-analyze ──────────────────────────────────────────────
async function reanalyze() {
  if (!uploadedFile.value) return
  analyzeMedia()
}

// ─── Hashtag management ──────────────────────────────────────
function addHashtag() {
  const tag = suggestions.value.hashtagInput.trim().replace(/^#/, '')
  if (tag && !suggestions.value.hashtags.includes(tag)) {
    suggestions.value.hashtags.push(tag)
  }
  suggestions.value.hashtagInput = ''
}

function removeHashtag(index) {
  suggestions.value.hashtags.splice(index, 1)
}

function onHashtagKeydown(e) {
  if (e.key === 'Enter' || e.key === ',') {
    e.preventDefault()
    addHashtag()
  }
}

// ─── Save / Process ──────────────────────────────────────────
async function savePost() {
  if (!pipelineItemId.value) {
    toast.error('Keine Analyse vorhanden. Bitte lade zuerst ein Bild hoch.')
    return
  }

  isSaving.value = true
  currentStep.value = 'saving'

  try {
    const hashtagString = suggestions.value.hashtags.map(t => `#${t}`).join(' ')
    const captionWithHashtags = suggestions.value.caption + (hashtagString ? '\n\n' + hashtagString : '')

    const res = await api.post('/api/pipeline/process', {
      inbox_item_id: pipelineItemId.value,
      post_type: suggestions.value.postType,
      platform: suggestions.value.platform === 'tiktok' ? 'tiktok' : suggestions.value.postType,
      tone: suggestions.value.tone,
      country: suggestions.value.country,
    })

    savedPostId.value = res.data.post_id
    toast.success('Post als Entwurf gespeichert!')
    currentStep.value = 'review'

    // Update the post with the edited caption
    if (res.data.post_id) {
      await api.put(`/api/posts/${res.data.post_id}`, {
        title: suggestions.value.title,
        caption_instagram: suggestions.value.platform === 'instagram' ? captionWithHashtags : null,
        caption_tiktok: suggestions.value.platform === 'tiktok' ? captionWithHashtags : null,
        hashtags_instagram: suggestions.value.platform === 'instagram' ? hashtagString : null,
        hashtags_tiktok: suggestions.value.platform === 'tiktok' ? hashtagString : null,
      })
    }
  } catch (err) {
    toast.error('Speichern fehlgeschlagen. Bitte versuche es erneut.')
    currentStep.value = 'review'
  } finally {
    isSaving.value = false
  }
}

function editSavedPost() {
  if (savedPostId.value) {
    router.push(`/create/post/${savedPostId.value}/edit`)
  }
}

function startOver() {
  uploadedFile.value = null
  uploadPreviewUrl.value = null
  analysisResult.value = null
  pipelineItemId.value = null
  savedPostId.value = null
  suggestions.value = {
    postType: 'instagram_feed',
    caption: '',
    hashtags: [],
    hashtagInput: '',
    platform: 'instagram',
    country: null,
    tone: 'jugendlich',
    title: '',
    analysisSummary: '',
  }
  currentStep.value = 'upload'
}
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-6" data-testid="smart-create-view">
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center gap-3 mb-2">
        <button
          @click="router.push('/create')"
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          aria-label="Zurueck zum Create Hub"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
        </button>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Smart Create</h1>
        <span class="text-xs font-medium px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300">
          KI-gestuetzt
        </span>
      </div>
      <p class="text-sm text-gray-600 dark:text-gray-400 ml-8">
        Lade ein Foto oder Video hoch — die KI analysiert den Inhalt und schlaegt alles Weitere vor.
      </p>
    </div>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- STEP 1: Upload Zone (full width) -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 'upload'" data-testid="upload-step">
      <div
        :class="[
          'relative border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer',
          isDragging
            ? 'border-purple-400 bg-purple-50 dark:bg-purple-900/20 scale-[1.01]'
            : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/50 hover:border-purple-300 dark:hover:border-purple-700 hover:bg-purple-50/50 dark:hover:bg-purple-900/10',
        ]"
        @dragover="onDragOver"
        @dragleave="onDragLeave"
        @drop="onDrop"
        @click="$refs.fileInput.click()"
        data-testid="media-upload-zone"
      >
        <input
          ref="fileInput"
          type="file"
          accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime,video/webm"
          class="hidden"
          @change="onFileSelect"
        />

        <div class="flex flex-col items-center gap-4">
          <!-- Upload icon -->
          <div class="w-20 h-20 rounded-2xl bg-purple-100 dark:bg-purple-900/40 flex items-center justify-center">
            <svg class="w-10 h-10 text-purple-500 dark:text-purple-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
          </div>

          <div>
            <p class="text-lg font-semibold text-gray-900 dark:text-white">
              Foto oder Video hierher ziehen
            </p>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              oder klicke, um eine Datei auszuwaehlen
            </p>
          </div>

          <div class="flex items-center gap-4 text-xs text-gray-400 dark:text-gray-500">
            <span>JPEG, PNG, WebP</span>
            <span class="w-1 h-1 bg-gray-300 dark:bg-gray-600 rounded-full"></span>
            <span>MP4, MOV, WebM</span>
            <span class="w-1 h-1 bg-gray-300 dark:bg-gray-600 rounded-full"></span>
            <span>Max. 100 MB</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- STEP 2: Analyzing (shimmer loading state) -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 'analyzing'" class="space-y-6" data-testid="analyzing-step">
      <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-8">
        <div class="flex flex-col items-center gap-6">
          <!-- Preview of uploaded file -->
          <div class="w-48 h-48 rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-700 shadow-lg">
            <video v-if="isVideo" :src="uploadPreviewUrl" class="w-full h-full object-cover" muted autoplay loop />
            <img v-else :src="uploadPreviewUrl" class="w-full h-full object-cover" alt="Upload preview" />
          </div>

          <!-- Analyzing animation -->
          <div class="flex flex-col items-center gap-3">
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
              <div class="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
              <div class="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
            </div>
            <p class="text-lg font-semibold text-gray-900 dark:text-white">
              AI analysiert dein {{ isVideo ? 'Video' : 'Bild' }}...
            </p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Inhalt wird erkannt, Vorschlaege werden generiert
            </p>
          </div>

          <!-- Shimmer placeholders -->
          <div class="w-full max-w-md space-y-3">
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-3/4"></div>
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- STEP 3: Review AI Suggestions -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 'review'" data-testid="review-step">
      <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">

        <!-- LEFT: Editable suggestions (3/5 width) -->
        <div class="lg:col-span-3 space-y-5">

          <!-- Analysis summary -->
          <div
            v-if="suggestions.analysisSummary"
            class="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-xl p-4"
          >
            <div class="flex items-start gap-3">
              <div class="w-8 h-8 bg-purple-100 dark:bg-purple-900/40 rounded-lg flex items-center justify-center shrink-0">
                <svg class="w-4 h-4 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
                </svg>
              </div>
              <div>
                <h3 class="text-sm font-semibold text-purple-800 dark:text-purple-300">AI-Analyse</h3>
                <p class="text-sm text-purple-700 dark:text-purple-400 mt-1">{{ suggestions.analysisSummary }}</p>
              </div>
            </div>
          </div>

          <!-- Title -->
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">Titel</label>
            <input
              v-model="suggestions.title"
              type="text"
              class="w-full bg-transparent border-0 border-b border-gray-200 dark:border-gray-600 px-0 py-1 text-sm text-gray-900 dark:text-white focus:ring-0 focus:border-purple-500"
              placeholder="Post-Titel..."
              data-testid="suggestion-title"
            />
          </div>

          <!-- Post Type -->
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <div class="flex items-center justify-between mb-3">
              <label class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Post-Typ</label>
              <button
                @click="reanalyze"
                class="text-xs text-purple-600 dark:text-purple-400 hover:underline font-medium"
              >
                Nochmal analysieren
              </button>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                v-for="opt in postTypeOptions"
                :key="opt.value"
                @click="suggestions.postType = opt.value"
                :class="[
                  'flex flex-col items-center gap-1 p-3 rounded-lg border text-center transition-all text-xs',
                  suggestions.postType === opt.value
                    ? 'border-purple-400 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 ring-1 ring-purple-400'
                    : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-300',
                ]"
                :data-testid="`post-type-${opt.value}`"
              >
                <span class="text-lg">{{ opt.icon }}</span>
                <span class="font-medium">{{ opt.label }}</span>
              </button>
            </div>
          </div>

          <!-- Caption -->
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <div class="flex items-center justify-between mb-2">
              <label class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Caption</label>
              <span class="text-[10px] text-gray-400">{{ suggestions.caption.length }} Zeichen</span>
            </div>
            <textarea
              v-model="suggestions.caption"
              rows="4"
              class="w-full bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:ring-1 focus:ring-purple-500 focus:border-purple-500 resize-none"
              placeholder="Caption fuer deinen Post..."
              data-testid="suggestion-caption"
            />
          </div>

          <!-- Hashtags -->
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">Hashtags</label>
            <div class="flex flex-wrap gap-2 mb-3">
              <span
                v-for="(tag, i) in suggestions.hashtags"
                :key="i"
                class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300"
              >
                #{{ tag }}
                <button
                  @click="removeHashtag(i)"
                  class="ml-0.5 text-purple-500 hover:text-purple-700 dark:hover:text-purple-200"
                  aria-label="Hashtag entfernen"
                >
                  &times;
                </button>
              </span>
            </div>
            <div class="flex gap-2">
              <input
                v-model="suggestions.hashtagInput"
                type="text"
                class="flex-1 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:ring-1 focus:ring-purple-500 focus:border-purple-500"
                placeholder="Hashtag hinzufuegen..."
                @keydown="onHashtagKeydown"
                data-testid="hashtag-input"
              />
              <button
                @click="addHashtag"
                class="px-3 py-1.5 bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 rounded-lg text-sm font-medium hover:bg-purple-200 dark:hover:bg-purple-800/40 transition-colors"
              >
                +
              </button>
            </div>
          </div>

          <!-- Platform + Tone + Country row -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <!-- Platform -->
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
              <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">Plattform</label>
              <div class="flex gap-2">
                <button
                  v-for="opt in platformOptions"
                  :key="opt.value"
                  @click="suggestions.platform = opt.value"
                  :class="[
                    'flex-1 flex items-center justify-center gap-1 py-2 rounded-lg border text-xs font-medium transition-all',
                    suggestions.platform === opt.value
                      ? 'border-purple-400 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                      : 'border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-gray-300',
                  ]"
                  :data-testid="`platform-${opt.value}`"
                >
                  <span>{{ opt.icon }}</span>
                  <span>{{ opt.label }}</span>
                </button>
              </div>
            </div>

            <!-- Tone -->
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
              <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">Tonalitaet</label>
              <select
                v-model="suggestions.tone"
                class="w-full bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg px-2 py-2 text-sm text-gray-900 dark:text-white focus:ring-1 focus:ring-purple-500"
                data-testid="tone-select"
              >
                <option v-for="opt in toneOptions" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </div>

            <!-- Country -->
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
              <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">Land</label>
              <select
                v-model="suggestions.country"
                class="w-full bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg px-2 py-2 text-sm text-gray-900 dark:text-white focus:ring-1 focus:ring-purple-500"
                data-testid="country-select"
              >
                <option :value="null">— Kein Land —</option>
                <option v-for="opt in countryOptions" :key="opt.value" :value="opt.value">
                  {{ opt.emoji }} {{ opt.label }}
                </option>
              </select>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="flex items-center gap-3 pt-2">
            <button
              @click="savePost"
              :disabled="isSaving || !!savedPostId"
              :class="[
                'flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all',
                savedPostId
                  ? 'bg-green-500 text-white cursor-default'
                  : isSaving
                    ? 'bg-purple-400 text-white cursor-wait'
                    : 'bg-purple-600 hover:bg-purple-700 text-white shadow-sm hover:shadow-md',
              ]"
              data-testid="save-button"
            >
              <svg v-if="!isSaving && !savedPostId" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              <svg v-if="savedPostId" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              <span v-if="isSaving">Wird gespeichert...</span>
              <span v-else-if="savedPostId">Gespeichert!</span>
              <span v-else>Speichern & Planen</span>
            </button>

            <button
              v-if="savedPostId"
              @click="editSavedPost"
              class="px-4 py-3 rounded-xl text-sm font-medium border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              data-testid="edit-post-button"
            >
              Bearbeiten
            </button>

            <button
              @click="startOver"
              class="px-4 py-3 rounded-xl text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              data-testid="start-over-button"
            >
              Neues Bild
            </button>
          </div>
        </div>

        <!-- RIGHT: Live Preview (2/5 width) -->
        <div class="lg:col-span-2" data-testid="live-preview">
          <div class="sticky top-6 space-y-4">
            <!-- Preview card -->
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
              <!-- Preview image/video -->
              <div class="aspect-square bg-gray-100 dark:bg-gray-700 overflow-hidden">
                <video
                  v-if="isVideo"
                  :src="uploadPreviewUrl"
                  class="w-full h-full object-cover"
                  muted
                  autoplay
                  loop
                  playsinline
                />
                <img
                  v-else
                  :src="uploadPreviewUrl"
                  class="w-full h-full object-cover"
                  alt="Post preview"
                />
              </div>

              <!-- Preview caption area -->
              <div class="p-4">
                <!-- Platform badge -->
                <div class="flex items-center gap-2 mb-2">
                  <span class="text-xs font-medium px-2 py-0.5 rounded-full"
                    :class="suggestions.platform === 'tiktok' ? 'bg-black text-white' : 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'"
                  >
                    {{ suggestions.platform === 'tiktok' ? 'TikTok' : 'Instagram' }}
                  </span>
                  <span class="text-xs text-gray-400">
                    {{ postTypeOptions.find(o => o.value === suggestions.postType)?.label }}
                  </span>
                </div>

                <!-- Caption preview -->
                <p class="text-sm text-gray-900 dark:text-white whitespace-pre-line leading-relaxed">
                  {{ suggestions.caption || 'Deine Caption erscheint hier...' }}
                </p>

                <!-- Hashtags preview -->
                <p v-if="suggestions.hashtags.length > 0" class="text-sm text-blue-600 dark:text-blue-400 mt-2">
                  {{ suggestions.hashtags.map(t => '#' + t).join(' ') }}
                </p>

                <!-- Country badge -->
                <div v-if="suggestions.country" class="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                  <span class="text-xs text-gray-500 dark:text-gray-400">
                    {{ countryOptions.find(c => c.value === suggestions.country)?.emoji }}
                    {{ countryOptions.find(c => c.value === suggestions.country)?.label }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Upload info -->
            <div class="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 text-xs text-gray-500 dark:text-gray-400">
              <p>
                <span class="font-medium">Datei:</span>
                {{ uploadedFile?.name }}
              </p>
              <p>
                <span class="font-medium">Groesse:</span>
                {{ uploadedFile ? (uploadedFile.size / 1024 / 1024).toFixed(1) + ' MB' : '' }}
              </p>
              <p>
                <span class="font-medium">Typ:</span>
                {{ uploadedFile?.type }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- Saving overlay -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <div
      v-if="currentStep === 'saving'"
      class="fixed inset-0 bg-black/30 flex items-center justify-center z-50"
      data-testid="saving-overlay"
    >
      <div class="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-2xl flex flex-col items-center gap-4">
        <div class="w-12 h-12 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin"></div>
        <p class="text-sm font-semibold text-gray-900 dark:text-white">Post wird gespeichert...</p>
      </div>
    </div>
  </div>
</template>
