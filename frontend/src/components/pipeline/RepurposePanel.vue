<script setup>
/**
 * RepurposePanel.vue — Content Repurposing Engine
 *
 * Takes an existing post and adapts it for a different platform/format.
 * AI adjusts caption (length, tone, hashtags), format (1:1 -> 9:16), and
 * platform-specific elements.
 *
 * Layout: Original post (left) | Target platform selection + adapted preview (right)
 *
 * @see services/content_multiplier.py — Backend adaptation logic
 * @see stores/contentPipeline.js — Pipeline Pinia store
 */
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const toast = useToast()
const router = useRouter()

const props = defineProps({
  /** Post ID to repurpose. If provided, the post will be fetched automatically. */
  postId: { type: [Number, String], default: null },
  /** Post object passed directly (alternative to postId). */
  post: { type: Object, default: null },
})

const emit = defineEmits(['saved', 'close'])

// ═══════════════════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════════════════

/** Source post data */
const sourcePost = ref(null)

/** Whether the source post is being loaded */
const loadingSource = ref(false)

/** Selected target format */
const targetFormat = ref('instagram_story')

/** Whether AI adaptation is in progress */
const adapting = ref(false)

/** Whether the derivative is being saved */
const saving = ref(false)

/** Adapted version (editable) */
const adaptedCaption = ref('')
const adaptedHashtags = ref('')
const adaptedCta = ref('')
const adaptedTitle = ref('')

/** Error message */
const errorMessage = ref('')

/** Result after saving */
const savedResult = ref(null)

// ═══════════════════════════════════════════════════════════════════════
// PLATFORM DEFINITIONS
// ═══════════════════════════════════════════════════════════════════════

const TARGET_FORMATS = [
  {
    key: 'instagram_feed',
    label: 'Instagram Feed',
    icon: '📸',
    format: '1:1',
    description: 'Quadratischer Feed-Post (1080x1080)',
    captionHint: 'Ausfuehrlich, storytelling-orientiert, 150-500 Zeichen',
    hashtagHint: '10-25 Hashtags',
    maxCaption: 2200,
  },
  {
    key: 'instagram_story',
    label: 'Instagram Story',
    icon: '📖',
    format: '9:16',
    description: 'Vertikale Story (1080x1920)',
    captionHint: 'Kurz & direkt, max. 200 Zeichen, Sticker-Aufforderung',
    hashtagHint: '3-5 Hashtags',
    maxCaption: 200,
  },
  {
    key: 'tiktok',
    label: 'TikTok',
    icon: '🎵',
    format: '9:16',
    description: 'Vertikales TikTok-Video (1080x1920)',
    captionHint: 'Knackig, trend-bewusst, Hook am Anfang, max. 300 Zeichen',
    hashtagHint: '4-8 Hashtags',
    maxCaption: 300,
  },
  {
    key: 'carousel',
    label: 'Carousel',
    icon: '🎠',
    format: '1:1',
    description: 'Swipeable Carousel-Slides (1080x1080)',
    captionHint: 'Slide-by-slide Erklaerung, educational, 200-500 Zeichen',
    hashtagHint: '10-25 Hashtags',
    maxCaption: 2200,
  },
]

// ═══════════════════════════════════════════════════════════════════════
// COMPUTED
// ═══════════════════════════════════════════════════════════════════════

const selectedTarget = computed(() => TARGET_FORMATS.find(f => f.key === targetFormat.value))

const sourceCaption = computed(() => {
  if (!sourcePost.value) return ''
  return sourcePost.value.caption_instagram || sourcePost.value.caption_tiktok || ''
})

const sourceHashtags = computed(() => {
  if (!sourcePost.value) return ''
  return sourcePost.value.hashtags_instagram || sourcePost.value.hashtags_tiktok || ''
})

const sourcePlatformLabel = computed(() => {
  if (!sourcePost.value) return ''
  const labels = {
    instagram_feed: 'Instagram Feed',
    instagram_story: 'Instagram Story',
    tiktok: 'TikTok',
    carousel: 'Carousel',
  }
  return labels[sourcePost.value.platform] || sourcePost.value.platform || 'Unbekannt'
})

const countryInfo = computed(() => {
  const c = sourcePost.value?.country?.toLowerCase?.() || ''
  const map = {
    usa: { label: 'USA', flag: '\uD83C\uDDFA\uD83C\uDDF8', color: '#B22234' },
    kanada: { label: 'Kanada', flag: '\uD83C\uDDE8\uD83C\uDDE6', color: '#FF0000' },
    australien: { label: 'Australien', flag: '\uD83C\uDDE6\uD83C\uDDFA', color: '#CC7722' },
    neuseeland: { label: 'Neuseeland', flag: '\uD83C\uDDF3\uD83C\uDDFF', color: '#1B4D3E' },
    irland: { label: 'Irland', flag: '\uD83C\uDDEE\uD83C\uDDEA', color: '#169B62' },
  }
  return map[c] || null
})

/** Formats available (excluding the source format) */
const availableTargets = computed(() => {
  if (!sourcePost.value) return TARGET_FORMATS
  return TARGET_FORMATS.filter(f => f.key !== sourcePost.value.platform)
})

const canAdapt = computed(() => sourcePost.value && !adapting.value && !saving.value)

const canSave = computed(() =>
  sourcePost.value && adaptedCaption.value.trim() && !saving.value && !adapting.value
)

const captionLength = computed(() => adaptedCaption.value.length)

const captionOverLimit = computed(() => {
  if (!selectedTarget.value) return false
  return captionLength.value > selectedTarget.value.maxCaption
})

// ═══════════════════════════════════════════════════════════════════════
// LOAD SOURCE POST
// ═══════════════════════════════════════════════════════════════════════

async function loadSourcePost(id) {
  loadingSource.value = true
  errorMessage.value = ''
  try {
    const { data } = await api.get(`/api/posts/${id}`)
    sourcePost.value = data
    // Auto-select a different target format than the source
    autoSelectTarget()
    // Generate initial adaptation
    generateAdaptation()
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || 'Post konnte nicht geladen werden'
    toast.error('Post nicht gefunden')
  } finally {
    loadingSource.value = false
  }
}

function autoSelectTarget() {
  if (!sourcePost.value) return
  const sourcePlatform = sourcePost.value.platform
  // Pick first available format that's different from source
  const firstAvailable = availableTargets.value[0]
  if (firstAvailable) {
    targetFormat.value = firstAvailable.key
  }
}

// ═══════════════════════════════════════════════════════════════════════
// AI ADAPTATION (rule-based fallback since we use the backend's multiply)
// ═══════════════════════════════════════════════════════════════════════

function generateAdaptation() {
  if (!sourcePost.value || !selectedTarget.value) return

  const caption = sourceCaption.value
  const hashtags = sourceHashtags.value
  const target = selectedTarget.value

  // Rule-based adaptation (instant preview)
  adaptedTitle.value = `${sourcePost.value.title || 'Post'} - ${target.label}`
  adaptedCta.value = sourcePost.value.cta_text || 'Mehr erfahren'

  // Adapt caption length for target
  if (caption.length > target.maxCaption) {
    adaptedCaption.value = caption.slice(0, target.maxCaption - 3).trimEnd() + '...'
  } else {
    adaptedCaption.value = caption
  }

  // Adapt hashtags count for target
  const tagList = hashtags.split(/\s+/).filter(t => t.startsWith('#'))
  const maxTags = target.key === 'instagram_story' ? 5
    : target.key === 'tiktok' ? 8
    : 25
  adaptedHashtags.value = tagList.slice(0, maxTags).join(' ')
}

// ═══════════════════════════════════════════════════════════════════════
// ADAPT WITH AI (calls backend multiply endpoint and creates derivative)
// ═══════════════════════════════════════════════════════════════════════

async function adaptWithAI() {
  if (!canAdapt.value) return
  adapting.value = true
  errorMessage.value = ''

  try {
    const { data } = await api.post('/api/pipeline/multiply', {
      post_id: sourcePost.value.id,
      formats: [targetFormat.value],
    })

    if (data.derivatives && data.derivatives.length > 0) {
      const derivative = data.derivatives[0]
      // Fetch the newly created derivative post to get its full data
      const { data: derivativePost } = await api.get(`/api/posts/${derivative.post_id}`)

      // Populate the fields with AI-generated data
      adaptedTitle.value = derivativePost.title || adaptedTitle.value
      adaptedCaption.value = derivativePost.caption_instagram || derivativePost.caption_tiktok || adaptedCaption.value
      adaptedHashtags.value = derivativePost.hashtags_instagram || derivativePost.hashtags_tiktok || adaptedHashtags.value
      adaptedCta.value = derivativePost.cta_text || adaptedCta.value

      // Store the derivative post ID so we can update it rather than create a new one
      savedResult.value = { post_id: derivative.post_id, alreadyCreated: true }

      toast.success('AI-Anpassung generiert! Du kannst die Vorschlaege jetzt bearbeiten.')
    } else {
      toast.warning('Keine Anpassung moeglich (Quellformat identisch oder ungueltig)')
    }
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || 'AI-Anpassung fehlgeschlagen'
    toast.error('AI-Anpassung fehlgeschlagen')
  } finally {
    adapting.value = false
  }
}

// ═══════════════════════════════════════════════════════════════════════
// SAVE AS NEW POST
// ═══════════════════════════════════════════════════════════════════════

async function saveAsNewPost() {
  if (!canSave.value) return
  saving.value = true
  errorMessage.value = ''

  try {
    // If we already created a derivative via AI adaptation, update it
    if (savedResult.value?.alreadyCreated && savedResult.value?.post_id) {
      const updateData = {
        title: adaptedTitle.value,
        cta_text: adaptedCta.value,
      }
      if (targetFormat.value === 'tiktok') {
        updateData.caption_tiktok = adaptedCaption.value
        updateData.hashtags_tiktok = adaptedHashtags.value
        updateData.caption_instagram = null
        updateData.hashtags_instagram = null
      } else {
        updateData.caption_instagram = adaptedCaption.value
        updateData.hashtags_instagram = adaptedHashtags.value
        updateData.caption_tiktok = null
        updateData.hashtags_tiktok = null
      }

      await api.put(`/api/posts/${savedResult.value.post_id}`, updateData)
      savedResult.value = {
        post_id: savedResult.value.post_id,
        saved: true,
      }
    } else {
      // Create a new post using the multiply endpoint
      const { data } = await api.post('/api/pipeline/multiply', {
        post_id: sourcePost.value.id,
        formats: [targetFormat.value],
      })

      if (data.derivatives && data.derivatives.length > 0) {
        const derivative = data.derivatives[0]

        // Update the derivative with our edited captions
        const updateData = {
          title: adaptedTitle.value,
          cta_text: adaptedCta.value,
        }
        if (targetFormat.value === 'tiktok') {
          updateData.caption_tiktok = adaptedCaption.value
          updateData.hashtags_tiktok = adaptedHashtags.value
        } else {
          updateData.caption_instagram = adaptedCaption.value
          updateData.hashtags_instagram = adaptedHashtags.value
        }

        await api.put(`/api/posts/${derivative.post_id}`, updateData)

        savedResult.value = {
          post_id: derivative.post_id,
          saved: true,
        }
      } else {
        throw new Error('Keine Derivate erstellt')
      }
    }

    toast.success('Angepasster Post als Draft gespeichert!')
    emit('saved', savedResult.value)
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || 'Speichern fehlgeschlagen'
    toast.error('Post konnte nicht gespeichert werden')
  } finally {
    saving.value = false
  }
}

function navigateToPost(postId) {
  router.push(`/create/post/${postId}/edit`)
}

// ═══════════════════════════════════════════════════════════════════════
// WATCHERS & LIFECYCLE
// ═══════════════════════════════════════════════════════════════════════

// When target format changes, regenerate adaptation
watch(targetFormat, () => {
  savedResult.value = null
  generateAdaptation()
})

// Watch props
watch(() => props.post, (newPost) => {
  if (newPost) {
    sourcePost.value = newPost
    autoSelectTarget()
    generateAdaptation()
  }
}, { immediate: true })

watch(() => props.postId, (newId) => {
  if (newId) {
    loadSourcePost(newId)
  }
}, { immediate: true })
</script>

<template>
  <div class="space-y-6" data-testid="repurpose-panel">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <span class="text-xl">🔄</span>
          Content Repurposing
        </h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
          Passe einen bestehenden Post fuer eine andere Plattform an
        </p>
      </div>
      <button
        v-if="emit"
        @click="emit('close')"
        class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        aria-label="Schliessen"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Loading state -->
    <div v-if="loadingSource" class="flex items-center justify-center py-12 text-gray-500 dark:text-gray-400">
      <div class="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mr-3" />
      Post wird geladen...
    </div>

    <!-- Error -->
    <div v-if="errorMessage && !loadingSource" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
      <p class="text-sm text-red-700 dark:text-red-400">{{ errorMessage }}</p>
    </div>

    <!-- Main content: Side-by-side layout -->
    <div v-if="sourcePost && !loadingSource" class="grid grid-cols-1 lg:grid-cols-2 gap-6">

      <!-- ═══════════════════════════════════════════════════════════ -->
      <!-- LEFT: Original Post -->
      <!-- ═══════════════════════════════════════════════════════════ -->
      <div class="space-y-4">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
          <span class="w-6 h-6 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-xs font-bold">1</span>
          Original-Post
        </h3>

        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden" data-testid="source-post-display">
          <!-- Post header -->
          <div class="px-4 py-3 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-lg">{{ sourcePlatformLabel.includes('TikTok') ? '🎵' : '📸' }}</span>
                <div>
                  <p class="text-sm font-semibold text-gray-900 dark:text-white">{{ sourcePost.title || 'Ohne Titel' }}</p>
                  <p class="text-xs text-gray-500 dark:text-gray-400">{{ sourcePlatformLabel }}</p>
                </div>
              </div>
              <div v-if="countryInfo" class="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full" :style="{ backgroundColor: countryInfo.color + '1A', color: countryInfo.color }">
                <span>{{ countryInfo.flag }}</span>
                <span>{{ countryInfo.label }}</span>
              </div>
            </div>
          </div>

          <!-- Post details -->
          <div class="p-4 space-y-3">
            <!-- Category & Status -->
            <div class="flex flex-wrap gap-2">
              <span class="text-xs px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
                {{ sourcePost.category || 'Ohne Kategorie' }}
              </span>
              <span class="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                {{ sourcePost.status || 'draft' }}
              </span>
              <span v-if="sourcePost.tone" class="text-xs px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400">
                {{ sourcePost.tone }}
              </span>
            </div>

            <!-- Caption -->
            <div v-if="sourceCaption">
              <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Caption</label>
              <p class="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap bg-gray-50 dark:bg-gray-900 rounded-lg p-3 max-h-32 overflow-y-auto">{{ sourceCaption }}</p>
            </div>

            <!-- Hashtags -->
            <div v-if="sourceHashtags">
              <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Hashtags</label>
              <p class="text-xs text-blue-600 dark:text-blue-400 bg-gray-50 dark:bg-gray-900 rounded-lg p-3 max-h-20 overflow-y-auto">{{ sourceHashtags }}</p>
            </div>

            <!-- CTA -->
            <div v-if="sourcePost.cta_text">
              <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">CTA</label>
              <p class="text-sm text-gray-800 dark:text-gray-200">{{ sourcePost.cta_text }}</p>
            </div>

            <!-- Caption length info -->
            <p class="text-xs text-gray-400">
              Caption: {{ sourceCaption.length }} Zeichen · {{ sourceHashtags.split(/\s+/).filter(t => t.startsWith('#')).length }} Hashtags
            </p>
          </div>
        </div>
      </div>

      <!-- ═══════════════════════════════════════════════════════════ -->
      <!-- RIGHT: Target Platform Selection + Adapted Preview -->
      <!-- ═══════════════════════════════════════════════════════════ -->
      <div class="space-y-4">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
          <span class="w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-xs font-bold">2</span>
          Ziel-Plattform &amp; Anpassung
        </h3>

        <!-- Target format selector -->
        <div class="grid grid-cols-2 gap-2" data-testid="target-format-selector">
          <button
            v-for="fmt in availableTargets"
            :key="fmt.key"
            @click="targetFormat = fmt.key"
            :class="[
              'flex items-center gap-2 px-3 py-2.5 rounded-xl border-2 text-left transition-all text-sm',
              targetFormat === fmt.key
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 shadow-sm'
                : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600',
            ]"
            :data-testid="`target-${fmt.key}`"
          >
            <span class="text-lg">{{ fmt.icon }}</span>
            <div class="flex-1 min-w-0">
              <p class="font-semibold truncate">{{ fmt.label }}</p>
              <p class="text-[10px] opacity-70">{{ fmt.format }}</p>
            </div>
          </button>
        </div>

        <!-- AI Adapt button -->
        <button
          @click="adaptWithAI"
          :disabled="!canAdapt"
          class="w-full py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center justify-center gap-2"
          :class="canAdapt
            ? 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white shadow-md hover:shadow-lg'
            : 'bg-gray-200 dark:bg-gray-700 text-gray-500 cursor-not-allowed'"
          data-testid="ai-adapt-button"
        >
          <template v-if="adapting">
            <div class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
            AI passt an...
          </template>
          <template v-else>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            AI-Anpassung generieren
          </template>
        </button>

        <!-- Adapted content (live-preview, editable) -->
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden" data-testid="adapted-preview">
          <!-- Platform mockup header -->
          <div class="px-4 py-3 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center gap-2">
              <span class="text-lg">{{ selectedTarget?.icon }}</span>
              <div class="flex-1">
                <p class="text-sm font-semibold text-gray-900 dark:text-white">{{ selectedTarget?.label }} Preview</p>
                <p class="text-[10px] text-gray-500 dark:text-gray-400">{{ selectedTarget?.description }}</p>
              </div>
              <span class="text-xs font-mono px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                {{ selectedTarget?.format }}
              </span>
            </div>
          </div>

          <div class="p-4 space-y-3">
            <!-- Title -->
            <div>
              <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Titel</label>
              <input
                v-model="adaptedTitle"
                type="text"
                class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Angepasster Titel..."
                data-testid="adapted-title-input"
              />
            </div>

            <!-- Caption -->
            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Caption</label>
                <span
                  :class="captionOverLimit ? 'text-red-500' : 'text-gray-400'"
                  class="text-[10px]"
                >
                  {{ captionLength }}/{{ selectedTarget?.maxCaption }}
                </span>
              </div>
              <textarea
                v-model="adaptedCaption"
                rows="4"
                class="w-full px-3 py-2 text-sm border rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 resize-none"
                :class="captionOverLimit ? 'border-red-400 dark:border-red-600' : 'border-gray-300 dark:border-gray-600'"
                :placeholder="`Caption fuer ${selectedTarget?.label}...`"
                data-testid="adapted-caption-input"
              />
              <p class="text-[10px] text-gray-400 mt-0.5">{{ selectedTarget?.captionHint }}</p>
            </div>

            <!-- Hashtags -->
            <div>
              <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Hashtags</label>
              <input
                v-model="adaptedHashtags"
                type="text"
                class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                :placeholder="`Hashtags fuer ${selectedTarget?.label}...`"
                data-testid="adapted-hashtags-input"
              />
              <p class="text-[10px] text-gray-400 mt-0.5">{{ selectedTarget?.hashtagHint }}</p>
            </div>

            <!-- CTA -->
            <div>
              <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">CTA</label>
              <input
                v-model="adaptedCta"
                type="text"
                maxlength="25"
                class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                placeholder="Call-to-Action..."
                data-testid="adapted-cta-input"
              />
            </div>
          </div>
        </div>

        <!-- Save button -->
        <button
          @click="saveAsNewPost"
          :disabled="!canSave"
          class="w-full py-3 rounded-xl text-sm font-bold transition-all flex items-center justify-center gap-2"
          :class="canSave
            ? 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white shadow-lg hover:shadow-xl'
            : 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed'"
          data-testid="save-repurposed-button"
        >
          <template v-if="saving">
            <div class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
            Wird gespeichert...
          </template>
          <template v-else>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" /></svg>
            Als neuen Post speichern
          </template>
        </button>

        <!-- Success result -->
        <div v-if="savedResult?.saved" class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4" data-testid="save-success">
          <div class="flex items-center gap-3">
            <span class="text-green-500 text-2xl">&#10003;</span>
            <div class="flex-1">
              <p class="text-sm font-semibold text-green-800 dark:text-green-300">
                Draft-Post erfolgreich erstellt!
              </p>
              <p class="text-xs text-green-600 dark:text-green-400 mt-0.5">
                Post #{{ savedResult.post_id }} · {{ selectedTarget?.label }}
              </p>
            </div>
            <button
              @click="navigateToPost(savedResult.post_id)"
              class="px-3 py-1.5 text-xs font-medium bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all"
            >
              Bearbeiten
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state (no post loaded) -->
    <div
      v-if="!sourcePost && !loadingSource && !errorMessage"
      class="text-center py-12 text-gray-500 dark:text-gray-400"
    >
      <span class="text-4xl block mb-3">🔄</span>
      <p class="text-sm">Waehle einen Post aus, um ihn fuer eine andere Plattform anzupassen.</p>
    </div>
  </div>
</template>
