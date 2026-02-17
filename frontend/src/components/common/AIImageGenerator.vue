<script setup>
/**
 * AIImageGenerator.vue - Reusable AI Image Generation Component
 *
 * Features:
 * - Prompt textarea with character counter
 * - Context-aware prompt suggestions based on country/topic
 * - Style selection (Fotorealistisch, Illustration, Minimalistisch, TREFF-Branded)
 * - Format/aspect ratio selection (1:1, 4:5, 9:16)
 * - Loading state with animated progress indicator
 * - Generated image preview with "Verwenden" and "Nochmal" buttons
 * - Auto-saves generated images to asset library
 *
 * @emits use-image - Emitted when user clicks "Verwenden" with { imageUrl, asset, result }
 * @emits image-generated - Emitted immediately after successful generation with full result
 */
import { ref, computed, watch } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  /** Current prompt text (v-model:prompt) */
  prompt: { type: String, default: '' },
  /** Selected aspect ratio override (v-model:aspectRatio) */
  aspectRatio: { type: String, default: '' },
  /** Selected style (v-model:style) */
  style: { type: String, default: 'photorealistic' },
  /** Whether generation is in progress (v-model:generating) */
  generating: { type: Boolean, default: false },
  /** Last generation result */
  result: { type: Object, default: null },
  /** Error message */
  error: { type: String, default: '' },
  /** Currently selected platform (for auto aspect ratio) */
  platform: { type: String, default: 'instagram_feed' },
  /** Currently selected country (for context-aware suggestions) */
  country: { type: String, default: '' },
  /** Currently selected topic (for context-aware suggestions) */
  topic: { type: String, default: '' },
  /** Currently selected category (for context-aware suggestions) */
  category: { type: String, default: '' },
  /** Whether the component is disabled */
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits([
  'update:prompt',
  'update:aspectRatio',
  'update:style',
  'update:generating',
  'update:result',
  'update:error',
  'use-image',
  'regenerate',
  'image-generated',
])

const toast = useToast()

// ── Local state ─────────────────────────────────────────────────────────
const progressPercent = ref(0)
const progressInterval = ref(null)

// ── Style options ───────────────────────────────────────────────────────
const styleOptions = [
  { value: 'photorealistic', label: 'Fotorealistisch', icon: 'camera', description: 'Hochwertige Fotos' },
  { value: 'illustration', label: 'Illustration', icon: 'paint-brush', description: 'Bunte Illustrationen' },
  { value: 'minimalist', label: 'Minimalistisch', icon: 'squares-2x2', description: 'Klare, einfache Designs' },
  { value: 'branded', label: 'TREFF-Branded', icon: 'tag', description: 'TREFF-Markenfarben' },
]

// ── Aspect ratio options ────────────────────────────────────────────────
const aspectRatioOptions = [
  { value: '1:1', label: '1:1', sublabel: 'Feed', icon: 'photo' },
  { value: '4:5', label: '4:5', sublabel: 'Portrait', icon: 'device-mobile' },
  { value: '9:16', label: '9:16', sublabel: 'Story', icon: 'device-mobile' },
]

// ── Platform to default aspect ratio mapping ────────────────────────────
const platformAspectRatioMap = {
  instagram_feed: '1:1',
  instagram_story: '9:16',
  tiktok: '9:16',
}

const platformDefaultAspectRatio = computed(() =>
  platformAspectRatioMap[props.platform] || '1:1'
)

const effectiveAspectRatio = computed(() =>
  props.aspectRatio || platformDefaultAspectRatio.value
)

// ── Context-aware prompt suggestions ────────────────────────────────────
const COUNTRY_SUGGESTIONS = {
  usa: [
    'American high school hallway with students and lockers',
    'Yellow school bus in suburban neighborhood at sunrise',
    'Homecoming football game with cheering crowd',
    'Teenagers at American diner eating burgers',
    'New York City skyline at sunset, vibrant colors',
  ],
  kanada: [
    'Canadian Rocky Mountains landscape with crystal clear lake',
    'Students playing ice hockey on frozen outdoor rink',
    'Maple trees in autumn colors along Canadian road',
    'Vancouver skyline with mountains and ocean',
    'Cozy log cabin in snowy Canadian forest',
  ],
  australien: [
    'Sydney Opera House and harbour at golden hour',
    'Students surfing at Bondi Beach, blue sky',
    'Australian outback with red sand and kangaroo silhouette',
    'Great Barrier Reef underwater coral scene',
    'Melbourne street art in colorful laneway',
  ],
  neuseeland: [
    'New Zealand green hills with sheep, Lord of the Rings landscape',
    'Milford Sound fiord with dramatic mountains',
    'Maori cultural village with traditional carvings',
    'Students hiking in Tongariro National Park',
    'Auckland harbour bridge at twilight',
  ],
  irland: [
    'Dublin cobblestone streets with colorful Georgian doors',
    'Cliffs of Moher overlooking Atlantic Ocean',
    'Irish countryside with stone walls and green pastures',
    'Students in traditional Irish pub with live music',
    'Trinity College Dublin library with old books',
  ],
}

const GENERAL_SUGGESTIONS = [
  'German exchange student arriving at host family',
  'Group of international students in school cafeteria',
  'Teenagers studying together in modern library',
  'Packed suitcase with passport and airplane ticket',
  'Graduation cap thrown in the air, celebration',
]

const promptSuggestions = computed(() => {
  const suggestions = []

  // Add country-specific suggestions first
  if (props.country && COUNTRY_SUGGESTIONS[props.country]) {
    suggestions.push(...COUNTRY_SUGGESTIONS[props.country])
  }

  // Add general suggestions
  suggestions.push(...GENERAL_SUGGESTIONS)

  // Deduplicate and limit
  return [...new Set(suggestions)].slice(0, 8)
})

// ── Actions ─────────────────────────────────────────────────────────────

function selectSuggestion(suggestion) {
  emit('update:prompt', suggestion)
}

function selectStyle(styleValue) {
  emit('update:style', styleValue)
}

function selectAspectRatio(ratio) {
  // Toggle off if same ratio clicked
  emit('update:aspectRatio', props.aspectRatio === ratio ? '' : ratio)
}

function startProgressAnimation() {
  progressPercent.value = 0
  // Simulate progress: fast at start, slow near end (never reaches 100)
  progressInterval.value = setInterval(() => {
    if (progressPercent.value < 30) {
      progressPercent.value += 3
    } else if (progressPercent.value < 60) {
      progressPercent.value += 2
    } else if (progressPercent.value < 85) {
      progressPercent.value += 0.5
    } else if (progressPercent.value < 95) {
      progressPercent.value += 0.1
    }
  }, 200)
}

function stopProgressAnimation(success) {
  if (progressInterval.value) {
    clearInterval(progressInterval.value)
    progressInterval.value = null
  }
  if (success) {
    progressPercent.value = 100
  }
}

async function generate() {
  const promptText = props.prompt.trim()
  if (!promptText) {
    emit('update:error', 'Bitte gib einen Prompt ein.')
    return
  }
  if (props.generating) return

  emit('update:generating', true)
  emit('update:error', '')
  emit('update:result', null)
  startProgressAnimation()

  try {
    const payload = {
      prompt: promptText,
      platform: props.platform || 'instagram_feed',
      style: props.style || 'photorealistic',
      category: 'ai_generated',
      country: props.country || null,
    }
    if (props.aspectRatio) {
      payload.aspect_ratio = props.aspectRatio
    }

    const response = await api.post('/api/ai/generate-image', payload)

    stopProgressAnimation(true)
    emit('update:result', response.data)
    emit('image-generated', response.data)
    toast.success(response.data.message || 'Bild erfolgreich generiert!')
  } catch (e) {
    stopProgressAnimation(false)
    const status = e.response?.status
    const detail = e.response?.data?.detail || ''
    let friendlyMessage = ''
    if (status === 400) {
      friendlyMessage = detail || 'Ungültige Eingabe. Bitte überprüfe deinen Prompt.'
    } else if (status === 401 || status === 403) {
      friendlyMessage = 'Sitzung abgelaufen. Bitte melde dich erneut an.'
    } else if (status === 429) {
      friendlyMessage = 'Zu viele Anfragen. Bitte warte einen Moment und versuche es erneut.'
    } else if (status === 500) {
      const knownGermanPhrases = ['Bitte', 'Fehler', 'Serverfehler', 'konnte nicht', 'aufgetreten', 'Speichern', 'generiert', 'versuche', 'erneut']
      const looksUserFriendly = knownGermanPhrases.some(phrase => detail.includes(phrase))
      friendlyMessage = (detail && looksUserFriendly) ? detail : 'Ein Serverfehler ist aufgetreten. Bitte versuche es erneut.'
    } else if (e.code === 'ERR_NETWORK' || e.message?.includes('Network Error')) {
      friendlyMessage = 'Netzwerkfehler. Bitte prüfe deine Internetverbindung.'
    } else if (e.code === 'ECONNABORTED' || e.message?.includes('timeout')) {
      friendlyMessage = 'Die Anfrage hat zu lange gedauert. Bitte versuche es erneut.'
    } else {
      friendlyMessage = 'Die Bildgenerierung ist leider fehlgeschlagen. Bitte versuche es erneut.'
    }
    emit('update:error', friendlyMessage)
  } finally {
    emit('update:generating', false)
  }
}

function useImage() {
  if (props.result && props.result.status === 'success') {
    emit('use-image', {
      imageUrl: props.result.image_url,
      asset: props.result.asset,
      result: props.result,
    })
    toast.success('Bild als Hintergrund übernommen!')
  }
}

function regenerate() {
  emit('update:result', null)
  generate()
}

// Cleanup on unmount
import { onUnmounted } from 'vue'
onUnmounted(() => {
  if (progressInterval.value) {
    clearInterval(progressInterval.value)
  }
})
</script>

<template>
  <div class="border-2 border-purple-300 dark:border-purple-600 rounded-xl p-6 bg-purple-50/50 dark:bg-purple-900/10" data-testid="ai-image-generator">
    <!-- Header -->
    <div class="flex items-center gap-2 mb-4">
      <AppIcon name="sparkles" class="w-7 h-7" />
      <h3 class="text-sm font-semibold text-purple-800 dark:text-purple-300">KI-Bild generieren</h3>
    </div>

    <!-- ═══════ Style Selection ═══════ -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Stil</label>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <button
          v-for="opt in styleOptions"
          :key="opt.value"
          @click="selectStyle(opt.value)"
          :class="[
            'flex flex-col items-center gap-1 px-3 py-2.5 rounded-lg text-xs border-2 transition-all duration-200',
            style === opt.value
              ? 'bg-purple-600 text-white border-purple-600 shadow-md scale-[1.02]'
              : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:border-purple-400 hover:shadow-sm'
          ]"
          :disabled="generating || disabled"
          :data-testid="'style-' + opt.value"
        >
          <AppIcon :name="opt.icon" class="w-5 h-5" />
          <span class="font-medium">{{ opt.label }}</span>
          <span :class="['text-[10px]', style === opt.value ? 'text-purple-200' : 'text-gray-400']">{{ opt.description }}</span>
        </button>
      </div>
    </div>

    <!-- ═══════ Prompt Input ═══════ -->
    <div class="mb-3">
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Bildbeschreibung (Prompt)</label>
      <textarea
        :value="prompt"
        @input="$emit('update:prompt', $event.target.value)"
        rows="3"
        maxlength="500"
        class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-purple-400 focus:border-purple-400 resize-none"
        placeholder="z.B. Teenager mit Rucksack vor einer amerikanischen High School"
        :disabled="generating || disabled"
        data-testid="ai-image-prompt"
      ></textarea>
      <div class="flex justify-between items-center mt-1">
        <span class="text-xs text-gray-400">{{ prompt.length }}/500</span>
      </div>
    </div>

    <!-- ═══════ Prompt Suggestions ═══════ -->
    <div class="mb-4">
      <p class="text-xs text-gray-500 dark:text-gray-400 mb-2">
        Vorschläge{{ country ? ` (${country.charAt(0).toUpperCase() + country.slice(1)})` : '' }}:
      </p>
      <div class="flex flex-wrap gap-1.5">
        <button
          v-for="suggestion in promptSuggestions"
          :key="suggestion"
          @click="selectSuggestion(suggestion)"
          class="text-xs px-2.5 py-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-full hover:border-purple-400 hover:text-purple-700 dark:hover:text-purple-300 transition-colors truncate max-w-[220px]"
          :disabled="generating || disabled"
          :title="suggestion"
        >
          {{ suggestion.length > 40 ? suggestion.slice(0, 37) + '...' : suggestion }}
        </button>
      </div>
    </div>

    <!-- ═══════ Format / Aspect Ratio Selection ═══════ -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Format</label>
      <div class="flex items-center gap-3">
        <button
          v-for="ar in aspectRatioOptions"
          :key="ar.value"
          @click="selectAspectRatio(ar.value)"
          :class="[
            'flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border-2 transition-all duration-200',
            (aspectRatio === ar.value || (!aspectRatio && ar.value === platformDefaultAspectRatio))
              ? 'bg-purple-600 text-white border-purple-600 shadow-md'
              : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:border-purple-400'
          ]"
          :disabled="generating || disabled"
          :data-testid="'format-' + ar.value.replace(':', 'x')"
        >
          <AppIcon :name="ar.icon" class="w-4 h-4" />
          <span>{{ ar.label }}</span>
          <span :class="['text-[10px]', (aspectRatio === ar.value || (!aspectRatio && ar.value === platformDefaultAspectRatio)) ? 'text-purple-200' : 'text-gray-400']">
            {{ ar.sublabel }}
          </span>
          <span
            v-if="ar.value === platformDefaultAspectRatio && !aspectRatio"
            :class="['text-[10px] ml-0.5', (ar.value === platformDefaultAspectRatio && !aspectRatio) ? 'text-purple-200' : 'text-gray-400']"
          >(Auto)</span>
        </button>
      </div>
      <p v-if="aspectRatio && aspectRatio !== platformDefaultAspectRatio" class="text-xs text-amber-600 dark:text-amber-400 mt-1.5">
        Manuell überschrieben (Plattform-Standard: {{ platformDefaultAspectRatio }})
      </p>
    </div>

    <!-- ═══════ Generate Button ═══════ -->
    <button
      @click="generate"
      :disabled="generating || !prompt.trim() || disabled"
      class="w-full px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center gap-2 text-sm"
      data-testid="generate-image-btn"
    >
      <span v-if="generating" class="flex items-center gap-2">
        <span class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
        Bild wird generiert...
      </span>
      <span v-else class="inline-flex items-center gap-1"><AppIcon name="paint-brush" class="w-4 h-4" /> Bild generieren ({{ effectiveAspectRatio }})</span>
    </button>

    <!-- ═══════ Progress Indicator ═══════ -->
    <div v-if="generating" class="mt-3" data-testid="generation-progress">
      <div class="flex items-center justify-between mb-1">
        <span class="text-xs text-purple-600 dark:text-purple-400 font-medium">Generierung läuft...</span>
        <span class="text-xs text-gray-500">{{ Math.round(progressPercent) }}%</span>
      </div>
      <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
        <div
          class="bg-gradient-to-r from-purple-500 to-purple-600 h-2 rounded-full transition-all duration-300 ease-out"
          :style="{ width: progressPercent + '%' }"
        ></div>
      </div>
      <p class="text-xs text-gray-400 mt-1.5 text-center">
        KI erstellt dein Bild im Stil "{{ styleOptions.find(s => s.value === style)?.label || 'Fotorealistisch' }}"...
      </p>
    </div>

    <!-- ═══════ Error Display ═══════ -->
    <div v-if="error" class="mt-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-sm text-red-700 dark:text-red-300" role="alert" data-testid="ai-image-error">
      {{ error }}
    </div>

    <!-- ═══════ Generated Image Result ═══════ -->
    <div v-if="result && result.status === 'success'" class="mt-4" data-testid="generated-image-result">
      <!-- Image Preview -->
      <div class="relative rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 mb-3">
        <img
          :src="result.image_url"
          :alt="prompt"
          class="w-full max-h-[400px] object-contain bg-gray-100 dark:bg-gray-800"
          data-testid="generated-image-preview"
        />
        <div class="absolute top-2 right-2 flex gap-1">
          <span class="px-2 py-0.5 bg-black/60 text-white text-[10px] rounded-full">
            {{ result.source === 'gemini' ? 'Gemini AI' : 'Lokal' }}
          </span>
          <span v-if="result.style" class="px-2 py-0.5 bg-purple-600/80 text-white text-[10px] rounded-full">
            {{ styleOptions.find(s => s.value === result.style)?.label || result.style }}
          </span>
        </div>
      </div>

      <!-- Image Info -->
      <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 flex-wrap mb-3">
        <span class="flex items-center gap-1">
          <span class="text-green-500">✓</span>
          In Asset-Bibliothek gespeichert
        </span>
        <span v-if="result.asset">| {{ result.asset.width }}x{{ result.asset.height }}px</span>
        <span v-if="result.aspect_ratio">| {{ result.aspect_ratio }}</span>
      </div>

      <!-- Action Buttons: Use / Regenerate -->
      <div class="flex gap-2">
        <button
          @click="useImage"
          class="flex-1 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center justify-center gap-2 text-sm"
          data-testid="use-image-btn"
        >
          <span>✓</span> Verwenden
        </button>
        <button
          @click="regenerate"
          class="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium flex items-center justify-center gap-2 text-sm"
          :disabled="generating"
          data-testid="regenerate-btn"
        >
          <AppIcon name="arrow-path" class="w-4 h-4" /> Nochmal
        </button>
      </div>
    </div>
  </div>
</template>
