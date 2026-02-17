<script setup>
/**
 * CaptionOptimizer.vue - KI-Caption-Optimierung mit A/B Varianten
 *
 * Appears after caption text is entered/generated. Offers optimization
 * options (shorten, emojis, tone, CTA) and shows 2-3 variants side-by-side
 * for comparison. User can select a variant or revert to original.
 */
import { ref, computed } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import AppIcon from '@/components/icons/AppIcon.vue'

const props = defineProps({
  /** Current caption text to optimize */
  caption: {
    type: String,
    default: '',
  },
  /** Target platform */
  platform: {
    type: String,
    default: 'instagram_feed',
  },
  /** Country context */
  country: {
    type: String,
    default: '',
  },
  /** Post category context */
  category: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['apply-variant', 'revert'])
const toast = useToast()

// State
const selectedOptions = ref(['shorten'])
const optimizing = ref(false)
const variants = ref([])
const originalText = ref('')
const source = ref('')
const showVariants = ref(false)

// Optimization options
const optimizationOptions = [
  { id: 'shorten', label: 'Kürzen', icon: 'scissors', desc: 'Auf das Wesentliche kürzen' },
  { id: 'add_emojis', label: 'Emojis +', icon: 'face-smile', desc: 'Passende Emojis einfügen' },
  { id: 'remove_emojis', label: 'Emojis -', icon: 'x-circle', desc: 'Alle Emojis entfernen' },
  { id: 'change_tone_casual', label: 'Lockerer', icon: 'face-smile', desc: 'Jugendlicher, lockerer Ton' },
  { id: 'change_tone_serious', label: 'Seriöser', icon: 'academic-cap', desc: 'Professioneller, seriöser Ton' },
  { id: 'add_cta', label: '+ CTA', icon: 'megaphone', desc: 'Call-to-Action hinzufügen' },
  { id: 'add_hook', label: '+ Hook', icon: 'bolt', desc: 'Aufmerksamkeitsstarken Einstieg' },
]

// Platform-specific character limits
const charLimit = computed(() => {
  const limits = {
    instagram_feed: 2200,
    instagram_story: 200,
    instagram_reels: 2200,
    tiktok: 150,
  }
  return limits[props.platform] || 2200
})

// Toggle option selection
function toggleOption(optionId) {
  const idx = selectedOptions.value.indexOf(optionId)
  if (idx >= 0) {
    selectedOptions.value.splice(idx, 1)
  } else {
    // Prevent conflicting options
    if (optionId === 'add_emojis') {
      selectedOptions.value = selectedOptions.value.filter(o => o !== 'remove_emojis')
    } else if (optionId === 'remove_emojis') {
      selectedOptions.value = selectedOptions.value.filter(o => o !== 'add_emojis')
    } else if (optionId === 'change_tone_casual') {
      selectedOptions.value = selectedOptions.value.filter(o => o !== 'change_tone_serious')
    } else if (optionId === 'change_tone_serious') {
      selectedOptions.value = selectedOptions.value.filter(o => o !== 'change_tone_casual')
    }
    selectedOptions.value.push(optionId)
  }
}

// Generate optimized variants
async function optimize() {
  if (!props.caption?.trim()) {
    toast.error('Bitte zuerst einen Caption-Text eingeben.')
    return
  }
  if (selectedOptions.value.length === 0) {
    toast.error('Bitte mindestens eine Optimierungs-Option wählen.')
    return
  }

  optimizing.value = true
  variants.value = []
  originalText.value = props.caption
  showVariants.value = false

  try {
    const res = await api.post('/api/ai/optimize-caption', {
      text: props.caption,
      platform: props.platform,
      options: selectedOptions.value,
      num_variants: 3,
      country: props.country || null,
      category: props.category || null,
    })

    variants.value = res.data.variants || []
    originalText.value = res.data.original?.text || props.caption
    source.value = res.data.source || 'local'
    showVariants.value = true

    if (variants.value.length === 0) {
      toast.error('Keine Varianten generiert.')
    }
  } catch (err) {
    const msg = err.response?.data?.detail || 'Optimierung fehlgeschlagen.'
    toast.error(msg)
  } finally {
    optimizing.value = false
  }
}

// Select a variant
function selectVariant(variant) {
  emit('apply-variant', variant.text)
  toast.success(`Variante "${variant.label}" übernommen!`)
}

// Revert to original
function revertToOriginal() {
  emit('revert', originalText.value)
  toast.success('Originaltext wiederhergestellt.')
}

// Compute simple diff highlighting: find added/removed parts
function getHighlightedDiff(variantText) {
  const original = originalText.value
  if (!original || !variantText) return variantText

  // Simple word-level diff
  const origWords = original.split(/\s+/)
  const varWords = variantText.split(/\s+/)
  const origSet = new Set(origWords.map(w => w.toLowerCase()))

  // Highlight words that are new (not in original)
  return varWords.map(word => {
    const isNew = !origSet.has(word.toLowerCase())
    return { word, isNew }
  })
}
</script>

<template>
  <div
    class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden"
    data-testid="caption-optimizer"
  >
    <!-- Header -->
    <div class="px-4 py-3 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center gap-2">
        <AppIcon name="sparkles" class="w-5 h-5" />
        <h3 class="text-sm font-bold text-gray-800 dark:text-gray-200">KI Caption-Optimierung</h3>
        <span
          v-if="source"
          class="text-[10px] font-medium px-1.5 py-0.5 rounded-full"
          :class="source === 'gemini' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'"
        >
          {{ source === 'gemini' ? 'KI' : 'Lokal' }}
        </span>
      </div>
    </div>

    <div class="p-4 space-y-4">
      <!-- Optimization Options -->
      <div>
        <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">Optimierungen wählen:</label>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="opt in optimizationOptions"
            :key="opt.id"
            @click="toggleOption(opt.id)"
            :class="[
              'inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-lg border transition-all',
              selectedOptions.includes(opt.id)
                ? 'border-[#4C8BC2] bg-blue-50 dark:bg-blue-900/20 text-[#4C8BC2] dark:text-blue-300'
                : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-500',
            ]"
            :title="opt.desc"
            :data-testid="`opt-${opt.id}`"
          >
            <AppIcon :name="opt.icon" class="w-4 h-4 inline-block" />
            <span>{{ opt.label }}</span>
          </button>
        </div>
      </div>

      <!-- Generate Button -->
      <button
        @click="optimize"
        :disabled="optimizing || !caption?.trim() || selectedOptions.length === 0"
        class="w-full py-2.5 px-4 bg-[#4C8BC2] text-white text-sm font-semibold rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        data-testid="optimize-btn"
      >
        <AppIcon v-if="optimizing" name="clock" class="w-4 h-4 animate-spin" />
        <AppIcon v-else name="sparkles" class="w-4 h-4" />
        {{ optimizing ? 'Optimiere...' : 'Varianten generieren' }}
      </button>

      <!-- Variants Display -->
      <div v-if="showVariants && variants.length > 0" class="space-y-3" data-testid="variants-container">
        <!-- Original -->
        <div class="p-3 rounded-lg border-2 border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-900/50">
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Original</span>
            <div class="flex items-center gap-2">
              <span class="text-[10px] text-gray-400">{{ originalText.length }}/{{ charLimit }}</span>
              <button
                @click="revertToOriginal"
                class="text-xs font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 underline transition-colors"
                data-testid="revert-btn"
              >
                Zurück zum Original
              </button>
            </div>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-line leading-relaxed">{{ originalText }}</p>
        </div>

        <!-- Variant Cards -->
        <div class="grid grid-cols-1 gap-3" :class="variants.length <= 2 ? 'sm:grid-cols-2' : 'sm:grid-cols-3'">
          <button
            v-for="(variant, idx) in variants"
            :key="idx"
            @click="selectVariant(variant)"
            class="text-left p-3 rounded-lg border-2 border-gray-200 dark:border-gray-600 hover:border-[#4C8BC2] dark:hover:border-blue-400 bg-white dark:bg-gray-800 transition-all group cursor-pointer"
            :data-testid="`variant-${idx}`"
          >
            <!-- Variant header -->
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold text-[#4C8BC2] dark:text-blue-300 uppercase tracking-wide">{{ variant.label }}</span>
              <span
                class="text-[10px] font-medium px-1.5 py-0.5 rounded"
                :class="variant.char_count > charLimit ? 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'"
              >
                {{ variant.char_count }}/{{ charLimit }}
              </span>
            </div>

            <!-- Variant text with diff highlighting -->
            <p class="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-line leading-relaxed mb-2">
              <template v-for="(part, pIdx) in getHighlightedDiff(variant.text)" :key="pIdx">
                <span
                  :class="part.isNew ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 px-0.5 rounded' : ''"
                >{{ part.word }}</span>{{ ' ' }}
              </template>
            </p>

            <!-- Changes summary -->
            <p class="text-[10px] text-gray-400 dark:text-gray-500 italic">{{ variant.changes_summary }}</p>

            <!-- Select button (hover) -->
            <div class="mt-2 text-center opacity-0 group-hover:opacity-100 transition-opacity">
              <span class="inline-flex items-center gap-1 text-xs font-semibold text-[#4C8BC2] dark:text-blue-300">
                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                Übernehmen
              </span>
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
