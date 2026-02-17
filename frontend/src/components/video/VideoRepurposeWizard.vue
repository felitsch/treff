<script setup>
/**
 * VideoRepurposeWizard.vue — Video-First Content-Repurposing Pipeline
 *
 * Wizard-style component that takes a source Reel or TikTok post and generates
 * platform-specific derivatives via the /api/ai/repurpose-video endpoint.
 *
 * Layout:
 *  - Left: Source video/post display (thumbnail, caption, platform info)
 *  - Right: Target derivative formats with effort levels, selection toggles,
 *           one-click "Alle generieren" button
 *
 * Repurposing workflows loaded dynamically from social-content.json via API:
 *  1. Reel → TikTok-Version
 *  2. Reel → Story-Sequenz (3-5 Slides)
 *  3. Reel → Feed-Post (best frame thumbnail)
 *  4. Reel → Carousel (5-7 keyframe slides)
 *  5. Feed → Story
 *  6. Feed → TikTok
 *  7. TikTok → Reels
 *
 * Each derivative shows effort level from social-content.json workflows.
 *
 * @see Feature #319 — V-09: Video-First Content-Repurposing Pipeline
 * @see backend/app/api/routes/ai.py — POST /api/ai/repurpose-video
 * @see ContentMultiplierPanel.vue — Similar pattern for asset-based derivatives
 */
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const toast = useToast()
const router = useRouter()

const props = defineProps({
  /** Source post ID (Reel or TikTok) to repurpose */
  postId: { type: [Number, String], default: null },
  /** Source post object (alternative to postId) */
  post: { type: Object, default: null },
})

const emit = defineEmits(['generated', 'close'])

// ═══════════════════════════════════════════════════════════════════════
// DERIVATIVE FORMAT DEFINITIONS
// ═══════════════════════════════════════════════════════════════════════

const DERIVATIVE_FORMATS = [
  {
    key: 'tiktok',
    name: 'TikTok-Version',
    icon: '🎵',
    platform: 'TikTok',
    format: '9:16',
    description: 'Gleicher Clip, TikTok-optimierter Hook, andere Hashtags (3-5), Trending-Audio-Hinweis',
    workflow: 'Reel → TikTok',
    defaultEffort: 'niedrig',
    defaultMinutes: 2,
    color: 'from-pink-500 to-purple-600',
    bgColor: 'bg-pink-50 dark:bg-pink-900/20',
    borderColor: 'border-pink-200 dark:border-pink-800',
    badgeColor: 'bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300',
  },
  {
    key: 'instagram_story',
    name: 'Story-Sequenz',
    icon: '📱',
    platform: 'Instagram Stories',
    format: '9:16',
    description: '3-5 Key-Frames als Story-Slides mit Text-Overlays und Swipe-Up CTA',
    workflow: 'Reel → Story-Sequenz',
    defaultEffort: 'mittel',
    defaultMinutes: 8,
    color: 'from-orange-500 to-amber-600',
    bgColor: 'bg-orange-50 dark:bg-orange-900/20',
    borderColor: 'border-orange-200 dark:border-orange-800',
    badgeColor: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300',
  },
  {
    key: 'instagram_feed',
    name: 'Feed-Post',
    icon: '🖼️',
    platform: 'Instagram Feed',
    format: '1:1',
    description: 'Bestes Frame als Thumbnail, Carousel aus 3 Keyframes mit Feed-optimierter Caption',
    workflow: 'Reel → Feed-Post',
    defaultEffort: 'mittel',
    defaultMinutes: 8,
    color: 'from-blue-500 to-cyan-600',
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    borderColor: 'border-blue-200 dark:border-blue-800',
    badgeColor: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  },
  {
    key: 'carousel',
    name: 'Carousel',
    icon: '📚',
    platform: 'Instagram Carousel',
    format: '1:1',
    description: '5-7 Keyframes mit Text-Overlays als Slide-Carousel (beliebtestes Instagram-Format)',
    workflow: 'Reel → Carousel',
    defaultEffort: 'mittel',
    defaultMinutes: 8,
    color: 'from-emerald-500 to-teal-600',
    bgColor: 'bg-emerald-50 dark:bg-emerald-900/20',
    borderColor: 'border-emerald-200 dark:border-emerald-800',
    badgeColor: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  },
]

// ═══════════════════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════════════════

/** Source post data */
const sourcePost = ref(null)
/** Loading source post */
const loadingSource = ref(false)
/** Selected derivative keys */
const selectedFormats = ref(DERIVATIVE_FORMATS.map(d => d.key))
/** Whether generation is in progress */
const generating = ref(false)
/** Per-format generation progress */
const generationProgress = ref({})
/** Generation results */
const generationResults = ref(null)
/** Generation error */
const generationError = ref(null)
/** Whether to schedule across the week */
const scheduleAcrossWeek = ref(true)
/** Workflow metadata from social-content.json (loaded from API response) */
const workflowMetadata = ref([])
/** Effort overrides from social-content.json workflows */
const effortMap = ref({})

// ═══════════════════════════════════════════════════════════════════════
// COMPUTED
// ═══════════════════════════════════════════════════════════════════════

const isSelected = (key) => selectedFormats.value.includes(key)

const selectedCount = computed(() => selectedFormats.value.length)

const canGenerate = computed(() => {
  return sourcePost.value && selectedCount.value > 0 && !generating.value
})

const totalEstimatedMinutes = computed(() => {
  return selectedFormats.value.reduce((sum, key) => {
    const fmt = DERIVATIVE_FORMATS.find(d => d.key === key)
    if (!fmt) return sum
    // Use effort from API metadata if available, else default
    const effort = effortMap.value[key]
    return sum + (effort?.minutes ?? fmt.defaultMinutes)
  }, 0)
})

/** Platform badge for source post */
const sourcePlatformLabel = computed(() => {
  const p = sourcePost.value?.platform?.toLowerCase() || ''
  if (p.includes('reel')) return { label: 'Instagram Reel', icon: '🎬', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300' }
  if (p.includes('tiktok')) return { label: 'TikTok', icon: '🎵', color: 'bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300' }
  if (p.includes('story')) return { label: 'Instagram Story', icon: '📱', color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300' }
  if (p.includes('feed')) return { label: 'Instagram Feed', icon: '🖼️', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300' }
  return { label: p || 'Unbekannt', icon: '📄', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' }
})

/** Country accent for source post */
const sourceCountry = computed(() => {
  const c = sourcePost.value?.country?.toLowerCase() || ''
  const map = {
    usa: { flag: '🇺🇸', label: 'USA', color: 'text-red-600' },
    kanada: { flag: '🇨🇦', label: 'Kanada', color: 'text-red-500' },
    canada: { flag: '🇨🇦', label: 'Kanada', color: 'text-red-500' },
    australien: { flag: '🇦🇺', label: 'Australien', color: 'text-amber-600' },
    australia: { flag: '🇦🇺', label: 'Australien', color: 'text-amber-600' },
    neuseeland: { flag: '🇳🇿', label: 'Neuseeland', color: 'text-emerald-700' },
    nz: { flag: '🇳🇿', label: 'Neuseeland', color: 'text-emerald-700' },
    irland: { flag: '🇮🇪', label: 'Irland', color: 'text-green-600' },
    ireland: { flag: '🇮🇪', label: 'Irland', color: 'text-green-600' },
  }
  return map[c] || null
})

/** Effort badge display for a format */
function getEffortBadge(formatKey) {
  const fmt = DERIVATIVE_FORMATS.find(d => d.key === formatKey)
  const effort = effortMap.value[formatKey]
  const minutes = effort?.minutes ?? fmt?.defaultMinutes ?? 8
  const label = effort?.label ?? fmt?.defaultEffort ?? 'mittel'

  if (label === 'niedrig' || minutes <= 3) {
    return { label: `Niedrig (${minutes}min)`, color: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300', icon: '⚡' }
  }
  if (label === 'hoch' || minutes >= 12) {
    return { label: `Hoch (${minutes}min)`, color: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300', icon: '🔨' }
  }
  return { label: `Mittel (${minutes}min)`, color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300', icon: '⏱️' }
}

// ═══════════════════════════════════════════════════════════════════════
// METHODS
// ═══════════════════════════════════════════════════════════════════════

function toggleFormat(key) {
  const idx = selectedFormats.value.indexOf(key)
  if (idx >= 0) {
    selectedFormats.value.splice(idx, 1)
  } else {
    selectedFormats.value.push(key)
  }
}

function selectAll() {
  selectedFormats.value = DERIVATIVE_FORMATS.map(d => d.key)
}

function deselectAll() {
  selectedFormats.value = []
}

/** Load source post by ID */
async function loadSourcePost(id) {
  if (!id) return
  loadingSource.value = true
  try {
    const { data } = await api.get(`/api/posts/${id}`)
    sourcePost.value = data
  } catch (err) {
    console.error('Failed to load source post:', err)
    toast.error('Quell-Post konnte nicht geladen werden')
  } finally {
    loadingSource.value = false
  }
}

/** Generate all selected derivatives via video repurposing API */
async function generateAll() {
  if (!canGenerate.value) return

  generating.value = true
  generationError.value = null
  generationResults.value = null

  // Initialize per-format progress
  for (const key of selectedFormats.value) {
    generationProgress.value[key] = { status: 'pending', percent: 0 }
  }

  try {
    // Set all to in-progress
    for (const key of selectedFormats.value) {
      generationProgress.value[key] = { status: 'generating', percent: 30 }
    }

    const { data } = await api.post('/api/ai/repurpose-video', {
      source_post_id: sourcePost.value.id,
      target_formats: selectedFormats.value,
      schedule_across_week: scheduleAcrossWeek.value,
    })

    generationResults.value = data

    // Store workflow metadata from response
    if (data.workflow_metadata?.length) {
      workflowMetadata.value = data.workflow_metadata
      // Update effort map from API data
      for (const wf of data.workflow_metadata) {
        const matchingFormat = DERIVATIVE_FORMATS.find(d =>
          d.key === wf.target || wf.target?.includes(d.key)
        )
        if (matchingFormat) {
          effortMap.value[matchingFormat.key] = {
            label: wf.effort_level?.toLowerCase() || 'mittel',
            minutes: wf.effort_minutes || 8,
          }
        }
      }
    }

    // Mark all as completed
    for (const key of selectedFormats.value) {
      generationProgress.value[key] = { status: 'done', percent: 100 }
    }

    const count = data.derivative_count || data.derivatives?.length || 0
    toast.success(`${count} Video-Derivat(e) erfolgreich erstellt!`)
    emit('generated', data)
  } catch (err) {
    console.error('Video repurposing failed:', err)
    generationError.value = err.response?.data?.detail || 'Generierung fehlgeschlagen'
    for (const key of selectedFormats.value) {
      generationProgress.value[key] = { status: 'error', percent: 0 }
    }
    toast.error('Video-Repurposing fehlgeschlagen')
  } finally {
    generating.value = false
  }
}

/** Navigate to a generated derivative post */
function openDerivative(postId) {
  router.push(`/create/post/${postId}/edit`)
}

/** Navigate to calendar to see scheduled derivatives */
function openCalendar() {
  router.push('/calendar')
}

// ═══════════════════════════════════════════════════════════════════════
// LIFECYCLE
// ═══════════════════════════════════════════════════════════════════════

onMounted(async () => {
  if (props.post) {
    sourcePost.value = props.post
  } else if (props.postId) {
    await loadSourcePost(props.postId)
  }
})

watch(() => props.post, (newPost) => {
  if (newPost) sourcePost.value = newPost
})

watch(() => props.postId, (newId) => {
  if (newId && !props.post) loadSourcePost(newId)
})
</script>

<template>
  <div
    class="flex flex-col lg:flex-row gap-6 p-6 max-w-6xl mx-auto"
    data-testid="video-repurpose-wizard"
  >
    <!-- ═══════════════════════════════════════════════════════════ -->
    <!-- LEFT SIDE: Source Video/Post -->
    <!-- ═══════════════════════════════════════════════════════════ -->
    <div class="lg:w-[380px] flex-shrink-0">
      <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
        <span class="text-xl">🎬</span>
        Quell-Video
      </h3>

      <!-- Loading state -->
      <div
        v-if="loadingSource"
        class="rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 p-8 flex items-center justify-center"
      >
        <div class="animate-spin w-8 h-8 border-3 border-[#3B7AB1] border-t-transparent rounded-full"></div>
      </div>

      <!-- Source post card -->
      <div
        v-else-if="sourcePost"
        class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden shadow-sm"
        data-testid="video-repurpose-source-card"
      >
        <!-- Thumbnail / Video preview -->
        <div class="relative aspect-[9/16] max-h-[320px] bg-gradient-to-br from-[#1A1A2E] to-[#2a2a4e] overflow-hidden">
          <img
            v-if="sourcePost.thumbnail || sourcePost.image_url"
            :src="sourcePost.thumbnail || sourcePost.image_url"
            :alt="sourcePost.title || 'Video-Vorschau'"
            class="absolute inset-0 w-full h-full object-cover"
            loading="lazy"
          />
          <div v-else class="absolute inset-0 flex flex-col items-center justify-center text-white/60">
            <span class="text-4xl mb-2">🎬</span>
            <span class="text-sm">Kein Thumbnail</span>
          </div>
          <!-- Play overlay -->
          <div class="absolute inset-0 flex items-center justify-center">
            <div class="w-14 h-14 rounded-full bg-black/40 backdrop-blur-sm flex items-center justify-center border-2 border-white/50">
              <svg class="w-6 h-6 text-white ml-1" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </div>
          </div>
        </div>

        <!-- Post info -->
        <div class="p-4 space-y-2">
          <h4 class="font-semibold text-gray-900 dark:text-white line-clamp-2 text-sm">
            {{ sourcePost.title || 'Kein Titel' }}
          </h4>

          <!-- Platform + Country badges -->
          <div class="flex flex-wrap gap-1.5">
            <span
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
              :class="sourcePlatformLabel.color"
            >
              <span>{{ sourcePlatformLabel.icon }}</span>
              {{ sourcePlatformLabel.label }}
            </span>
            <span
              v-if="sourceCountry"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700"
              :class="sourceCountry.color"
            >
              {{ sourceCountry.flag }} {{ sourceCountry.label }}
            </span>
          </div>

          <!-- Caption preview -->
          <p
            v-if="sourcePost.caption_instagram || sourcePost.caption"
            class="text-xs text-gray-500 dark:text-gray-400 line-clamp-3"
          >
            {{ sourcePost.caption_instagram || sourcePost.caption }}
          </p>

          <!-- Hashtags -->
          <p
            v-if="sourcePost.hashtags_instagram || sourcePost.hashtags"
            class="text-xs text-blue-500 dark:text-blue-400 line-clamp-2"
          >
            {{ sourcePost.hashtags_instagram || sourcePost.hashtags }}
          </p>
        </div>
      </div>

      <!-- Empty state -->
      <div
        v-else
        class="rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600 p-8 text-center"
      >
        <span class="text-3xl mb-2 block">🎬</span>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Kein Quell-Video ausgewaehlt
        </p>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════ -->
    <!-- RIGHT SIDE: Derivative Formats -->
    <!-- ═══════════════════════════════════════════════════════════ -->
    <div class="flex-1 min-w-0">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <span class="text-xl">🔄</span>
          Derivative Formate
        </h3>
        <div class="flex items-center gap-2 text-xs">
          <button
            @click="selectAll"
            class="text-[#3B7AB1] hover:underline font-medium"
            data-testid="video-repurpose-select-all"
          >
            Alle
          </button>
          <span class="text-gray-300 dark:text-gray-600">|</span>
          <button
            @click="deselectAll"
            class="text-gray-500 hover:underline"
          >
            Keine
          </button>
        </div>
      </div>

      <!-- Derivative cards grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5" data-testid="video-repurpose-derivatives">
        <div
          v-for="fmt in DERIVATIVE_FORMATS"
          :key="fmt.key"
          class="relative rounded-xl border-2 transition-all duration-200 cursor-pointer overflow-hidden"
          :class="[
            isSelected(fmt.key)
              ? `${fmt.borderColor} ${fmt.bgColor} shadow-sm`
              : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 opacity-60 hover:opacity-80',
          ]"
          @click="toggleFormat(fmt.key)"
          :data-testid="`video-repurpose-format-${fmt.key}`"
        >
          <!-- Selection checkbox -->
          <div class="absolute top-3 right-3 z-10">
            <div
              class="w-5 h-5 rounded-md border-2 flex items-center justify-center transition-colors"
              :class="isSelected(fmt.key)
                ? 'bg-[#3B7AB1] border-[#3B7AB1] text-white'
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700'"
            >
              <svg v-if="isSelected(fmt.key)" class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
              </svg>
            </div>
          </div>

          <div class="p-4">
            <!-- Header: icon + name + format badge -->
            <div class="flex items-start gap-3 mb-2">
              <div
                class="w-10 h-10 rounded-lg bg-gradient-to-br flex items-center justify-center text-white text-lg flex-shrink-0"
                :class="fmt.color"
              >
                {{ fmt.icon }}
              </div>
              <div class="min-w-0">
                <h4 class="font-semibold text-sm text-gray-900 dark:text-white">{{ fmt.name }}</h4>
                <div class="flex items-center gap-1.5 mt-0.5">
                  <span class="text-[10px] text-gray-500 dark:text-gray-400">{{ fmt.platform }}</span>
                  <span class="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 font-mono">{{ fmt.format }}</span>
                </div>
              </div>
            </div>

            <!-- Description -->
            <p class="text-xs text-gray-600 dark:text-gray-400 mb-2.5 line-clamp-2">{{ fmt.description }}</p>

            <!-- Effort badge -->
            <div class="flex items-center gap-2">
              <span
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold"
                :class="getEffortBadge(fmt.key).color"
                :data-testid="`video-repurpose-effort-${fmt.key}`"
              >
                <span>{{ getEffortBadge(fmt.key).icon }}</span>
                {{ getEffortBadge(fmt.key).label }}
              </span>
              <span class="text-[10px] text-gray-400 dark:text-gray-500 italic">{{ fmt.workflow }}</span>
            </div>

            <!-- Progress indicator during generation -->
            <div
              v-if="generationProgress[fmt.key]"
              class="mt-2"
            >
              <div class="h-1.5 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :class="{
                    'bg-yellow-400 animate-pulse': generationProgress[fmt.key].status === 'generating',
                    'bg-green-500': generationProgress[fmt.key].status === 'done',
                    'bg-red-500': generationProgress[fmt.key].status === 'error',
                    'bg-gray-300': generationProgress[fmt.key].status === 'pending',
                  }"
                  :style="{ width: generationProgress[fmt.key].percent + '%' }"
                ></div>
              </div>
              <span class="text-[9px] mt-0.5 block" :class="{
                'text-yellow-600 dark:text-yellow-400': generationProgress[fmt.key].status === 'generating',
                'text-green-600 dark:text-green-400': generationProgress[fmt.key].status === 'done',
                'text-red-600 dark:text-red-400': generationProgress[fmt.key].status === 'error',
                'text-gray-400': generationProgress[fmt.key].status === 'pending',
              }">
                {{
                  generationProgress[fmt.key].status === 'generating' ? 'Wird generiert...'
                  : generationProgress[fmt.key].status === 'done' ? 'Fertig!'
                  : generationProgress[fmt.key].status === 'error' ? 'Fehler'
                  : 'Warten...'
                }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Schedule option -->
      <label
        class="flex items-center gap-3 mb-4 px-4 py-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 cursor-pointer"
        data-testid="video-repurpose-schedule-toggle"
      >
        <input
          v-model="scheduleAcrossWeek"
          type="checkbox"
          class="w-4 h-4 rounded border-gray-300 text-[#3B7AB1] focus:ring-[#3B7AB1]"
        />
        <div>
          <span class="text-sm font-medium text-gray-900 dark:text-white">Im Kalender verteilen</span>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            Derivative werden automatisch ueber die Woche verteilt (optimale Posting-Zeiten)
          </p>
        </div>
      </label>

      <!-- Summary + Generate button -->
      <div class="flex items-center justify-between bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 shadow-sm">
        <div>
          <p class="text-sm font-semibold text-gray-900 dark:text-white">
            {{ selectedCount }} von {{ DERIVATIVE_FORMATS.length }} Formate ausgewaehlt
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            Geschaetzter Aufwand: ~{{ totalEstimatedMinutes }} Minuten
          </p>
        </div>

        <button
          @click="generateAll"
          :disabled="!canGenerate"
          class="px-6 py-2.5 rounded-lg text-white font-semibold text-sm transition-all shadow-sm flex items-center gap-2"
          :class="canGenerate
            ? 'bg-gradient-to-r from-[#3B7AB1] to-[#2E6A9E] hover:shadow-md active:scale-95'
            : 'bg-gray-300 dark:bg-gray-600 cursor-not-allowed'"
          data-testid="video-repurpose-generate-all"
        >
          <span v-if="generating" class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
          <span v-else>🚀</span>
          {{ generating ? 'Generiere...' : 'Alle generieren' }}
        </button>
      </div>

      <!-- Error message -->
      <div
        v-if="generationError"
        class="mt-3 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300"
        data-testid="video-repurpose-error"
      >
        <strong>Fehler:</strong> {{ generationError }}
      </div>

      <!-- Results section -->
      <div
        v-if="generationResults?.derivatives?.length"
        class="mt-5 space-y-3"
        data-testid="video-repurpose-results"
      >
        <h4 class="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <span>✅</span>
          Generierte Derivative ({{ generationResults.derivatives.length }})
        </h4>

        <div
          v-for="(deriv, idx) in generationResults.derivatives"
          :key="deriv.post_id || idx"
          class="flex items-center justify-between p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800"
        >
          <div>
            <p class="text-sm font-medium text-gray-900 dark:text-white">{{ deriv.title || deriv.platform }}</p>
            <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              <span>{{ deriv.platform }}</span>
              <span v-if="deriv.scheduled_date">• Geplant: {{ deriv.scheduled_date }}</span>
              <span v-if="deriv.scheduled_time">{{ deriv.scheduled_time }}</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="openDerivative(deriv.post_id)"
              class="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#3B7AB1] text-white hover:bg-[#2E6A9E] transition-colors"
            >
              Bearbeiten
            </button>
          </div>
        </div>

        <!-- Calendar link if scheduled -->
        <button
          v-if="generationResults.scheduled"
          @click="openCalendar"
          class="w-full mt-2 px-4 py-2.5 rounded-lg text-sm font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors flex items-center justify-center gap-2"
        >
          <span>📅</span>
          Im Kalender ansehen
        </button>
      </div>
    </div>
  </div>
</template>
