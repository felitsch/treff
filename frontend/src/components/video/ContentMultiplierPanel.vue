<script setup>
/**
 * ContentMultiplierPanel — 1 Video → 5 Formate
 *
 * Takes a source video asset and generates derivative content suggestions:
 * 1. Reel-Cut (15-60s highlight clip for IG Reels)
 * 2. Story-Sequence (3-5 vertical story slides)
 * 3. Feed-Post (best frame with overlay, 1:1 format)
 * 4. TikTok-Version (with different hook)
 * 5. Carousel (keyframes as swipeable slides)
 *
 * "Alle generieren" creates draft posts for each selected derivative.
 */
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const toast = useToast()

const props = defineProps({
  videoAsset: { type: Object, default: null },
})

const emit = defineEmits(['generated'])

// ─── Derivative definitions ─────────────────────────────────
const DERIVATIVES = [
  {
    key: 'reel_cut',
    name: 'Reel-Cut',
    icon: '📱',
    platform: 'Instagram Reels',
    platformIcon: '📸',
    format: '9:16',
    resolution: '1080 x 1920',
    estimatedDuration: '15-60s',
    description: 'Highlight-Clip als vertikales Reel. Die spannendsten Momente des Videos in 15-60 Sekunden.',
    captionStyle: 'Kurz, mit Hook am Anfang und CTA am Ende',
    hashtagCount: '15-25',
    backendFormat: 'instagram_story',
  },
  {
    key: 'story_sequence',
    name: 'Story-Sequence',
    icon: '📖',
    platform: 'Instagram Stories',
    platformIcon: '📸',
    format: '9:16',
    resolution: '1080 x 1920',
    estimatedDuration: '3-5 Slides',
    description: '3-5 vertikale Story-Slides mit Text-Overlays. Ideal fuer Storytelling und Interaktion.',
    captionStyle: 'Sticker-Aufforderung (Umfrage, Frage, Slider)',
    hashtagCount: '3-5',
    backendFormat: 'instagram_story',
  },
  {
    key: 'feed_post',
    name: 'Feed-Post',
    icon: '⬜',
    platform: 'Instagram Feed',
    platformIcon: '📸',
    format: '1:1',
    resolution: '1080 x 1080',
    estimatedDuration: 'Standbild',
    description: 'Bestes Frame mit Text-Overlay als Feed-Post. Quadratisches Format fuer den Instagram-Feed.',
    captionStyle: 'Ausfuehrlich, storytelling-orientiert, mit Absaetzen und Emojis',
    hashtagCount: '15-25',
    backendFormat: 'instagram_feed',
  },
  {
    key: 'tiktok_version',
    name: 'TikTok-Version',
    icon: '🎵',
    platform: 'TikTok',
    platformIcon: '🎵',
    format: '9:16',
    resolution: '1080 x 1920',
    estimatedDuration: '15-180s',
    description: 'TikTok-optimierte Version mit anderem Hook und trendigen Elementen. Gen-Z-kompatibel.',
    captionStyle: 'Knackig, trend-bewusst, mit Hook, Gen-Z-kompatibel',
    hashtagCount: '4-8',
    backendFormat: 'tiktok',
  },
  {
    key: 'carousel',
    name: 'Carousel',
    icon: '🎠',
    platform: 'Instagram Carousel',
    platformIcon: '📸',
    format: '1:1',
    resolution: '1080 x 1080',
    estimatedDuration: '5-10 Slides',
    description: 'Keyframes als swipeable Carousel-Slides. Educational Content im Slide-by-Slide Format.',
    captionStyle: 'Slide-by-slide Erklaerung, nummeriert, educational',
    hashtagCount: '15-25',
    backendFormat: 'carousel',
  },
]

// ─── State ──────────────────────────────────────────────────
const selectedDerivatives = ref(DERIVATIVES.map(d => d.key)) // all selected by default
const generating = ref(false)
const generationProgress = ref({})
const generationResults = ref([])
const generationError = ref(null)

// Per-derivative captions
const captions = ref({})
const hashtags = ref({})

// Initialize captions/hashtags with suggestions
function initializeSuggestions() {
  const videoName = props.videoAsset?.filename || props.videoAsset?.original_filename || 'Video'
  const cleanName = videoName.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ')

  for (const d of DERIVATIVES) {
    if (!captions.value[d.key]) {
      captions.value[d.key] = generateCaptionSuggestion(d, cleanName)
    }
    if (!hashtags.value[d.key]) {
      hashtags.value[d.key] = generateHashtagSuggestion(d)
    }
  }
}

function generateCaptionSuggestion(derivative, videoName) {
  switch (derivative.key) {
    case 'reel_cut':
      return `Ein Auslandsjahr veraendert alles. Schau dir an, was ${videoName} erlebt hat! 🌍✈️ #auslandsjahr`
    case 'story_sequence':
      return `Swipe fuer die ganze Geschichte! 👉 ${videoName}`
    case 'feed_post':
      return `Erinnerungen, die ein Leben lang bleiben. 💙 ${videoName} — mit TREFF Sprachreisen.`
    case 'tiktok_version':
      return `POV: Du verbringst ein Jahr im Ausland und es ist besser als jeder Film 🎬🌏 #auslandsjahr #highschool #treff`
    case 'carousel':
      return `5 Dinge, die du ueber ein Auslandsjahr wissen solltest 📚 Swipe durch! #auslandsjahr #treffsprachreisen`
    default:
      return ''
  }
}

function generateHashtagSuggestion(derivative) {
  const baseTags = '#auslandsjahr #treffsprachreisen #highschool #exchange #studyabroad'
  switch (derivative.key) {
    case 'reel_cut':
      return `${baseTags} #reels #travelreels #exchangeyear #abenteuer #fernweh #teenager #schule #usa #kanada`
    case 'story_sequence':
      return '#auslandsjahr #treff #story #erfahrungsbericht'
    case 'feed_post':
      return `${baseTags} #erinnerungen #memories #sprachreise #gastfamilie #highschoolyear`
    case 'tiktok_version':
      return '#auslandsjahr #highschool #exchangestudent #studyabroad #treff #fyp #foryou #viral'
    case 'carousel':
      return `${baseTags} #tipps #ratgeber #carousel #education #eltern`
    default:
      return baseTags
  }
}

watch(() => props.videoAsset, () => {
  if (props.videoAsset) {
    initializeSuggestions()
  }
}, { immediate: true })

// ─── Computed ───────────────────────────────────────────────
const isSelected = (key) => selectedDerivatives.value.includes(key)
const selectedCount = computed(() => selectedDerivatives.value.length)

const canGenerate = computed(() => {
  return props.videoAsset && selectedCount.value > 0 && !generating.value
})

// ─── Methods ────────────────────────────────────────────────
function toggleDerivative(key) {
  const idx = selectedDerivatives.value.indexOf(key)
  if (idx >= 0) {
    selectedDerivatives.value.splice(idx, 1)
  } else {
    selectedDerivatives.value.push(key)
  }
}

function selectAll() {
  selectedDerivatives.value = DERIVATIVES.map(d => d.key)
}

function deselectAll() {
  selectedDerivatives.value = []
}

function formatSize(bytes) {
  if (!bytes) return '—'
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDuration(seconds) {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

// ─── Generate derivatives ───────────────────────────────────
async function generateAll() {
  if (!canGenerate.value) return

  generating.value = true
  generationError.value = null
  generationResults.value = []

  // Init progress for each selected
  for (const key of selectedDerivatives.value) {
    generationProgress.value[key] = { status: 'pending', percent: 0 }
  }

  try {
    // Step 1: Create a source draft post from the video asset
    for (const key of selectedDerivatives.value) {
      generationProgress.value[key] = { status: 'creating', percent: 20 }
    }

    let sourcePostId = null
    try {
      const { data: sourcePost } = await api.post('/api/posts', {
        title: `Quell-Video: ${props.videoAsset.filename || props.videoAsset.original_filename || 'Video'}`,
        category: 'schueler_spotlight',
        platform: 'instagram_feed',
        status: 'draft',
        caption_instagram: `Video-Content von ${props.videoAsset.filename || 'Quell-Video'}`,
        hashtags_instagram: '#auslandsjahr #treffsprachreisen #highschool',
        asset_id: props.videoAsset.id,
      })
      sourcePostId = sourcePost.id
    } catch (err) {
      console.error('Failed to create source post:', err)
      generationError.value = 'Quell-Post konnte nicht erstellt werden.'
      generating.value = false
      return
    }

    // Step 2: Call multiply endpoint for each derivative format
    const selectedFormats = selectedDerivatives.value
      .map(key => DERIVATIVES.find(d => d.key === key))
      .filter(Boolean)
      .map(d => d.backendFormat)

    // Deduplicate formats (e.g., reel_cut and story_sequence both use instagram_story)
    const uniqueFormats = [...new Set(selectedFormats)]

    for (const key of selectedDerivatives.value) {
      generationProgress.value[key] = { status: 'multiplying', percent: 50 }
    }

    const { data: result } = await api.post('/api/pipeline/multiply', {
      post_id: sourcePostId,
      formats: uniqueFormats,
    })

    // Step 3: Update captions per derivative (using provided captions)
    const derivatives = result.derivatives || []
    for (let i = 0; i < derivatives.length; i++) {
      const d = derivatives[i]
      const matchingKey = selectedDerivatives.value.find(key => {
        const def = DERIVATIVES.find(dd => dd.key === key)
        return def && def.backendFormat === d.platform
      })

      if (matchingKey && d.post_id) {
        generationProgress.value[matchingKey] = { status: 'finalizing', percent: 80 }

        // Update the derivative post with our custom captions
        try {
          await api.put(`/api/posts/${d.post_id}`, {
            caption_instagram: d.platform !== 'tiktok' ? captions.value[matchingKey] : null,
            caption_tiktok: d.platform === 'tiktok' ? captions.value[matchingKey] : null,
            hashtags_instagram: d.platform !== 'tiktok' ? hashtags.value[matchingKey] : null,
            hashtags_tiktok: d.platform === 'tiktok' ? hashtags.value[matchingKey] : null,
          })
        } catch (updateErr) {
          console.warn('Failed to update derivative captions:', updateErr)
        }
      }

      generationResults.value.push({
        ...d,
        derivativeKey: matchingKey,
        caption: matchingKey ? captions.value[matchingKey] : '',
        hashtags: matchingKey ? hashtags.value[matchingKey] : '',
      })
    }

    // Mark all as complete
    for (const key of selectedDerivatives.value) {
      generationProgress.value[key] = { status: 'done', percent: 100 }
    }

    toast.success(`${generationResults.value.length} Derivat(e) als Draft-Posts erstellt!`)
    emit('generated', generationResults.value)
  } catch (err) {
    generationError.value = err.response?.data?.detail || err.message || 'Generierung fehlgeschlagen'
    toast.error('Content-Multiplikation fehlgeschlagen.')
  } finally {
    generating.value = false
  }
}

function progressLabel(status) {
  switch (status) {
    case 'pending': return 'Wartend...'
    case 'creating': return 'Quell-Post erstellen...'
    case 'multiplying': return 'Derivate generieren...'
    case 'finalizing': return 'Captions anpassen...'
    case 'done': return 'Fertig!'
    default: return ''
  }
}
</script>

<template>
  <div class="space-y-6" data-testid="content-multiplier-panel">
    <!-- Source video info -->
    <div v-if="videoAsset" class="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 flex items-center gap-4" data-testid="source-video-info">
      <div class="w-16 h-16 bg-gray-200 dark:bg-gray-700 rounded-lg flex items-center justify-center text-2xl shrink-0">
        🎬
      </div>
      <div class="flex-1 min-w-0">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white truncate">
          {{ videoAsset.filename || videoAsset.original_filename }}
        </h3>
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
          {{ formatSize(videoAsset.file_size) }}
          <span v-if="videoAsset.duration_seconds"> · {{ formatDuration(videoAsset.duration_seconds) }}</span>
          <span v-if="videoAsset.width"> · {{ videoAsset.width }}x{{ videoAsset.height }}</span>
        </p>
      </div>
      <div class="text-right">
        <p class="text-xs text-gray-500 dark:text-gray-400">Quell-Video</p>
        <p class="text-lg font-bold text-blue-600 dark:text-blue-400">→ {{ selectedCount }} Derivate</p>
      </div>
    </div>

    <!-- No video selected -->
    <div v-else class="text-center py-8 text-sm text-gray-500 dark:text-gray-400">
      Bitte waehle zuerst ein Video aus, um Content zu multiplizieren.
    </div>

    <!-- Derivative cards -->
    <div v-if="videoAsset">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Derivate auswaehlen</h3>
        <div class="flex gap-2">
          <button @click="selectAll" class="text-xs text-blue-600 dark:text-blue-400 hover:underline">Alle</button>
          <span class="text-gray-300">|</span>
          <button @click="deselectAll" class="text-xs text-gray-500 hover:underline">Keine</button>
        </div>
      </div>

      <div class="space-y-3">
        <div
          v-for="d in DERIVATIVES"
          :key="d.key"
          :class="[
            'rounded-xl border-2 transition-all overflow-hidden',
            isSelected(d.key)
              ? 'border-blue-400 dark:border-blue-600 bg-blue-50/50 dark:bg-blue-900/10'
              : 'border-gray-200 dark:border-gray-700 opacity-60',
          ]"
          :data-testid="`derivative-${d.key}`"
        >
          <!-- Card header (click to toggle) -->
          <button
            @click="toggleDerivative(d.key)"
            class="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
          >
            <!-- Checkbox -->
            <div :class="[
              'w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 transition-all',
              isSelected(d.key)
                ? 'bg-blue-500 border-blue-500'
                : 'border-gray-300 dark:border-gray-600',
            ]">
              <span v-if="isSelected(d.key)" class="text-white text-xs">&#10003;</span>
            </div>

            <!-- Icon & Name -->
            <div class="flex items-center gap-2 flex-1 min-w-0">
              <span class="text-xl">{{ d.icon }}</span>
              <div>
                <p class="text-sm font-semibold text-gray-900 dark:text-white">{{ d.name }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {{ d.platformIcon }} {{ d.platform }} · {{ d.format }} · {{ d.estimatedDuration }}
                </p>
              </div>
            </div>

            <!-- Format badge -->
            <span class="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 font-mono shrink-0">
              {{ d.resolution }}
            </span>

            <!-- Progress indicator -->
            <div v-if="generationProgress[d.key]" class="shrink-0">
              <span v-if="generationProgress[d.key].status === 'done'" class="text-green-500 text-lg">&#10003;</span>
              <div v-else-if="generationProgress[d.key].status !== 'pending'" class="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full" />
            </div>
          </button>

          <!-- Expanded details (when selected) -->
          <div v-if="isSelected(d.key)" class="px-4 pb-4 space-y-3">
            <p class="text-xs text-gray-600 dark:text-gray-400">{{ d.description }}</p>

            <!-- Caption -->
            <div>
              <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                Caption-Vorschlag <span class="text-gray-400">({{ d.captionStyle }})</span>
              </label>
              <textarea
                v-model="captions[d.key]"
                rows="2"
                class="w-full px-3 py-2 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 resize-none"
                :placeholder="`Caption fuer ${d.name}...`"
              />
            </div>

            <!-- Hashtags -->
            <div>
              <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                Hashtags <span class="text-gray-400">({{ d.hashtagCount }} empfohlen)</span>
              </label>
              <input
                v-model="hashtags[d.key]"
                type="text"
                class="w-full px-3 py-2 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                :placeholder="`Hashtags fuer ${d.name}...`"
              />
            </div>

            <!-- Progress bar -->
            <div v-if="generationProgress[d.key] && generationProgress[d.key].status !== 'pending'" class="space-y-1">
              <div class="flex items-center justify-between text-xs">
                <span class="text-gray-600 dark:text-gray-400">{{ progressLabel(generationProgress[d.key].status) }}</span>
                <span class="text-blue-600 font-medium">{{ generationProgress[d.key].percent }}%</span>
              </div>
              <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                <div
                  :class="[
                    'h-1.5 rounded-full transition-all duration-500',
                    generationProgress[d.key].status === 'done' ? 'bg-green-500' : 'bg-blue-500',
                  ]"
                  :style="{ width: `${generationProgress[d.key].percent}%` }"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Generate button -->
    <div v-if="videoAsset" class="pt-2">
      <button
        @click="generateAll"
        :disabled="!canGenerate"
        :class="[
          'w-full py-3 rounded-xl text-sm font-bold transition-all flex items-center justify-center gap-2',
          canGenerate
            ? 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl'
            : 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed',
        ]"
        data-testid="generate-all-button"
      >
        <template v-if="generating">
          <div class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
          Wird generiert... (kann einige Minuten dauern)
        </template>
        <template v-else>
          🚀 {{ selectedCount }} Derivat{{ selectedCount !== 1 ? 'e' : '' }} generieren
        </template>
      </button>
    </div>

    <!-- Error -->
    <div v-if="generationError" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
      <p class="text-sm text-red-700 dark:text-red-400">{{ generationError }}</p>
    </div>

    <!-- Results -->
    <div v-if="generationResults.length > 0" class="space-y-3" data-testid="generation-results">
      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">
        &#10003; {{ generationResults.length }} Draft-Posts erstellt
      </h3>
      <div class="space-y-2">
        <div
          v-for="(result, idx) in generationResults"
          :key="idx"
          class="flex items-center gap-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3"
        >
          <span class="text-green-500 text-lg">&#10003;</span>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 dark:text-white">{{ result.title }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              {{ result.platform }} · Draft-Post #{{ result.post_id }}
            </p>
          </div>
          <a
            :href="`/create/post/${result.post_id}/edit`"
            class="px-3 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all"
          >
            Bearbeiten
          </a>
        </div>
      </div>
      <p class="text-xs text-gray-500 dark:text-gray-400">
        Alle Derivate sind als Draft-Posts im Kalender sichtbar und koennen dort bearbeitet werden.
      </p>
    </div>
  </div>
</template>
