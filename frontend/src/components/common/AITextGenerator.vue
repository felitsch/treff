<script setup>
/**
 * AITextGenerator.vue — Reusable AI Text Generation Component
 *
 * Features:
 * - Prompt input with topic/key points
 * - Tone/language/length option chips
 * - Country selection
 * - API integration with /api/ai/generate-text
 * - Typing animation (word-by-word streaming simulation)
 * - Variant preview: shows 2-3 variants to choose from
 * - "Nochmal generieren" button for new variant
 * - Error handling: API errors, rate limiting, timeout
 * - Generated text is editable in textarea before applying
 *
 * @emits generate - Emitted when user triggers generation with params
 * @emits apply - Emitted when user applies a variant: { variant, index }
 * @emits update:generating - v-model for generating state
 */
import { ref, computed, watch, nextTick } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import { getHooksForPlatform, getHooksSortedByEffectiveness, HOOK_CATEGORIES } from '@/config/hookFormulas'

const props = defineProps({
  /** Category for the post */
  category: { type: String, default: '' },
  /** Pre-filled topic */
  topic: { type: String, default: '' },
  /** Pre-filled key points */
  keyPoints: { type: String, default: '' },
  /** Selected country */
  country: { type: String, default: '' },
  /** Selected platform */
  platform: { type: String, default: 'instagram_feed' },
  /** Selected tone */
  tone: { type: String, default: 'jugendlich' },
  /** Number of slides to generate */
  slideCount: { type: Number, default: 1 },
  /** Student ID for personality presets */
  studentId: { type: Number, default: null },
  /** Whether generation is in progress */
  generating: { type: Boolean, default: false },
  /** Previously generated content (to show summary) */
  generatedContent: { type: Object, default: null },
  /** Humor format if selected */
  humorFormat: { type: Object, default: null },
  /** Whether to show the compact mode (no options, just generate button) */
  compact: { type: Boolean, default: false },
  /** Whether the component is disabled */
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits([
  'generate',
  'generate-humor',
  'apply',
  'apply-variant',
  'update:generating',
])

const toast = useToast()

// ── Variants state ──────────────────────────────────────────────────────
const variants = ref([])           // Array of generated content variants
const selectedVariantIndex = ref(0)
const generatingVariants = ref(false)
const variantError = ref('')

// ── Hook formula state ──────────────────────────────────────────────────
const selectedHookId = ref('')
const showHookPanel = ref(false)

/** Hook formulas filtered for the current platform */
const platformHooks = computed(() => getHooksForPlatform(props.platform))

/** Top 3 hooks sorted by effectiveness for current platform */
const topHooks = computed(() => getHooksSortedByEffectiveness(props.platform).slice(0, 3))

/** The selected hook formula object */
const selectedHook = computed(() =>
  platformHooks.value.find(h => h.id === selectedHookId.value) || null
)

/** Select a hook formula */
function selectHook(hookId) {
  selectedHookId.value = selectedHookId.value === hookId ? '' : hookId
}

// ── Typing animation state ──────────────────────────────────────────────
const typingText = ref('')
const isTyping = ref(false)
const typingTimer = ref(null)

// ── Computed ────────────────────────────────────────────────────────────
const hasContent = computed(() => !!props.generatedContent)
const variantCount = computed(() => variants.value.length)
const currentVariant = computed(() => variants.value[selectedVariantIndex.value] || null)

// ── Methods ─────────────────────────────────────────────────────────────

/** Trigger main generation */
function triggerGenerate() {
  if (props.disabled || props.generating) return
  if (props.humorFormat) {
    emit('generate-humor')
  } else {
    emit('generate')
  }
}

/** Generate 2-3 variants for comparison */
async function generateVariants() {
  if (generatingVariants.value) return
  generatingVariants.value = true
  variantError.value = ''
  variants.value = []
  selectedVariantIndex.value = 0

  try {
    // Generate 3 variants in parallel
    const requests = Array.from({ length: 3 }, () =>
      api.post('/api/ai/generate-text', {
        category: props.category,
        topic: props.topic?.trim() || null,
        key_points: props.keyPoints?.trim() || null,
        country: props.country || null,
        platform: props.platform,
        slide_count: props.slideCount,
        tone: props.tone,
        student_id: props.studentId || null,
      })
    )

    const results = await Promise.allSettled(requests)
    const successfulVariants = results
      .filter(r => r.status === 'fulfilled')
      .map(r => r.value.data)

    if (successfulVariants.length === 0) {
      variantError.value = 'Keine Varianten konnten generiert werden. Bitte versuche es erneut.'
    } else {
      variants.value = successfulVariants
      // Start typing animation for the first variant
      animateTyping(successfulVariants[0])
      toast.success(`${successfulVariants.length} Varianten generiert!`)
    }
  } catch (e) {
    const status = e.response?.status
    const detail = e.response?.data?.detail || ''
    if (status === 429) {
      variantError.value = detail || 'Zu viele Anfragen. Bitte warte einen Moment.'
    } else {
      variantError.value = 'Varianten konnten nicht generiert werden: ' + (detail || e.message)
    }
  } finally {
    generatingVariants.value = false
  }
}

/** Simulate typing animation for generated text */
function animateTyping(variant) {
  if (!variant) return
  const headline = variant.slides?.[0]?.headline || ''
  const words = headline.split(' ')
  typingText.value = ''
  isTyping.value = true
  let wordIndex = 0

  if (typingTimer.value) clearInterval(typingTimer.value)

  typingTimer.value = setInterval(() => {
    if (wordIndex < words.length) {
      typingText.value += (wordIndex > 0 ? ' ' : '') + words[wordIndex]
      wordIndex++
    } else {
      clearInterval(typingTimer.value)
      typingTimer.value = null
      isTyping.value = false
    }
  }, 80) // 80ms per word for smooth streaming feel
}

/** Select a variant and animate it */
function selectVariant(index) {
  selectedVariantIndex.value = index
  if (variants.value[index]) {
    animateTyping(variants.value[index])
  }
}

/** Apply the selected variant */
function applyVariant() {
  const variant = currentVariant.value
  if (variant) {
    emit('apply-variant', { variant, index: selectedVariantIndex.value })
    toast.success('Variante uebernommen!')
  }
}

/** Clean up typing timer on unmount */
function cleanup() {
  if (typingTimer.value) {
    clearInterval(typingTimer.value)
    typingTimer.value = null
  }
}

// Watch for external generation completion to trigger animation
watch(() => props.generatedContent, (newContent) => {
  if (newContent && !isTyping.value) {
    animateTyping(newContent)
  }
})

// Cleanup
import { onUnmounted } from 'vue'
onUnmounted(cleanup)
</script>

<template>
  <div class="ai-text-generator" data-testid="ai-text-generator">
    <!-- Header -->
    <div class="text-center mb-6">
      <div class="flex justify-center mb-4">
        <AppIcon :name="humorFormat ? humorFormat.icon : 'sparkles'" class="w-12 h-12" />
      </div>
      <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
        {{ humorFormat ? 'Humor-Content generieren' : 'KI-Textgenerierung' }}
      </h3>
      <p class="text-gray-500 dark:text-gray-400">
        {{ humorFormat
          ? `"${humorFormat.name}" - Humor-Format mit KI-gestuetzten Textvorschlaegen.`
          : 'Texte, Captions und Hashtags werden basierend auf deiner Auswahl generiert.' }}
      </p>
    </div>

    <!-- Generation options summary (when not compact) -->
    <div v-if="!compact" class="mb-6">
      <slot name="summary">
        <!-- Default summary - can be overridden by parent -->
      </slot>
    </div>

    <!-- Hook Formula Suggestions (from hookFormulas.js config) -->
    <div v-if="!compact && !humorFormat && platformHooks.length > 0" class="mb-6" data-testid="hook-formula-panel">
      <button
        @click="showHookPanel = !showHookPanel"
        class="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-gray-600 dark:text-gray-400 hover:text-[#3B7AB1] transition-colors"
      >
        <span class="flex items-center gap-1.5">
          <AppIcon name="sparkles" class="w-4 h-4" />
          Hook-Formel waehlen
          <span v-if="selectedHook" class="px-1.5 py-0.5 rounded-full bg-[#3B7AB1]/10 text-[#3B7AB1] text-[10px]">{{ selectedHook.name }}</span>
        </span>
        <span>{{ showHookPanel ? '▲' : '▼' }}</span>
      </button>

      <div v-if="showHookPanel" class="mt-2 space-y-2">
        <!-- Top 3 recommended hooks -->
        <div class="grid grid-cols-1 gap-2">
          <button
            v-for="hook in topHooks"
            :key="hook.id"
            @click="selectHook(hook.id)"
            class="text-left p-3 rounded-lg border-2 transition-all"
            :class="selectedHookId === hook.id
              ? 'border-[#3B7AB1] bg-[#3B7AB1]/5'
              : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'"
            :data-testid="'hook-' + hook.id"
          >
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs font-bold text-gray-800 dark:text-gray-200">{{ hook.name }}</span>
              <span class="flex items-center gap-1">
                <span class="text-[10px] px-1.5 py-0.5 rounded-full" :class="'bg-' + (HOOK_CATEGORIES[hook.category]?.color === '#3B82F6' ? 'blue' : HOOK_CATEGORIES[hook.category]?.color === '#EF4444' ? 'red' : HOOK_CATEGORIES[hook.category]?.color === '#F59E0B' ? 'amber' : HOOK_CATEGORIES[hook.category]?.color === '#8B5CF6' ? 'purple' : 'green') + '-100 dark:bg-' + (HOOK_CATEGORIES[hook.category]?.color === '#3B82F6' ? 'blue' : HOOK_CATEGORIES[hook.category]?.color === '#EF4444' ? 'red' : HOOK_CATEGORIES[hook.category]?.color === '#F59E0B' ? 'amber' : HOOK_CATEGORIES[hook.category]?.color === '#8B5CF6' ? 'purple' : 'green') + '-900/20 text-gray-600 dark:text-gray-400'">{{ HOOK_CATEGORIES[hook.category]?.name || hook.category }}</span>
                <span class="text-[10px] font-bold" :class="hook.effectiveness >= 9 ? 'text-green-600 dark:text-green-400' : hook.effectiveness >= 8 ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500'">{{ hook.effectiveness }}/10</span>
              </span>
            </div>
            <p class="text-[11px] text-gray-500 dark:text-gray-400 italic">{{ hook.template }}</p>
            <p v-if="hook.tip" class="text-[10px] text-gray-400 mt-1 flex items-start gap-1"><AppIcon name="light-bulb" class="w-3 h-3 flex-shrink-0 mt-px" /> {{ hook.tip }}</p>
          </button>
        </div>

        <!-- Show remaining hooks link -->
        <button
          v-if="platformHooks.length > 3"
          @click="showHookPanel = 'all'"
          class="text-[11px] text-[#3B7AB1] hover:underline"
        >
          +{{ platformHooks.length - 3 }} weitere Hooks anzeigen
        </button>

        <!-- All hooks (when expanded) -->
        <template v-if="showHookPanel === 'all'">
          <button
            v-for="hook in platformHooks.slice(3)"
            :key="hook.id"
            @click="selectHook(hook.id)"
            class="w-full text-left p-2 rounded-lg border transition-all text-xs"
            :class="selectedHookId === hook.id
              ? 'border-[#3B7AB1] bg-[#3B7AB1]/5'
              : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'"
          >
            <span class="font-semibold text-gray-800 dark:text-gray-200">{{ hook.name }}</span>
            <span class="ml-2 text-gray-400">{{ hook.effectiveness }}/10</span>
            <span class="block text-gray-500 dark:text-gray-400 italic mt-0.5">{{ hook.template }}</span>
          </button>
        </template>
      </div>
    </div>

    <!-- Main Generate Button -->
    <div class="flex flex-col items-center gap-3 mb-6">
      <button
        @click="triggerGenerate"
        :disabled="generating || disabled"
        class="px-8 py-4 text-white font-bold rounded-xl transition-colors flex items-center justify-center gap-2 text-lg"
        :class="humorFormat
          ? 'bg-gradient-to-r from-[#FDD000] to-[#FFB800] hover:from-[#E8C300] hover:to-[#EBA800] text-gray-900 disabled:from-gray-300 disabled:to-gray-300 dark:disabled:from-gray-700 dark:disabled:to-gray-700 disabled:text-gray-500'
          : 'bg-[#3B7AB1] hover:bg-[#2E6A9E] disabled:bg-gray-300 dark:disabled:bg-gray-700'"
        data-testid="generate-content-btn"
      >
        <span v-if="generating" class="animate-spin h-5 w-5 border-2 border-current border-t-transparent rounded-full"></span>
        <AppIcon v-else :name="humorFormat ? humorFormat.icon : 'sparkles'" class="w-5 h-5" />
        {{ generating ? 'Generiere...' : (humorFormat ? 'Humor-Content generieren' : 'Inhalt generieren') }}
      </button>

      <!-- Variants Button (shown after first generation) -->
      <button
        v-if="hasContent && !humorFormat"
        @click="generateVariants"
        :disabled="generatingVariants || generating"
        class="px-6 py-2.5 border-2 border-[#3B7AB1] text-[#3B7AB1] font-semibold rounded-xl transition-colors flex items-center gap-2 text-sm hover:bg-[#3B7AB1]/10 disabled:opacity-40 disabled:cursor-not-allowed"
        data-testid="generate-variants-btn"
      >
        <span v-if="generatingVariants" class="animate-spin h-4 w-4 border-2 border-[#3B7AB1] border-t-transparent rounded-full"></span>
        <AppIcon v-else name="sparkles" class="w-4 h-4" />
        {{ generatingVariants ? 'Generiere Varianten...' : '3 Varianten generieren' }}
      </button>
    </div>

    <!-- Typing Animation Preview (shown during/after generation) -->
    <div
      v-if="isTyping || typingText"
      class="mb-6 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl border border-gray-200 dark:border-gray-600"
      data-testid="typing-preview"
    >
      <div class="flex items-center gap-2 mb-2">
        <span class="text-xs font-bold text-[#3B7AB1] uppercase tracking-wider">KI schreibt</span>
        <span v-if="isTyping" class="flex gap-0.5">
          <span class="w-1.5 h-1.5 bg-[#3B7AB1] rounded-full animate-bounce" style="animation-delay: 0ms"></span>
          <span class="w-1.5 h-1.5 bg-[#3B7AB1] rounded-full animate-bounce" style="animation-delay: 150ms"></span>
          <span class="w-1.5 h-1.5 bg-[#3B7AB1] rounded-full animate-bounce" style="animation-delay: 300ms"></span>
        </span>
        <AppIcon v-else name="check-circle" class="w-4 h-4 text-green-500" />
      </div>
      <p class="text-gray-800 dark:text-gray-200 text-base font-medium leading-relaxed">
        {{ typingText }}<span v-if="isTyping" class="inline-block w-0.5 h-5 bg-[#3B7AB1] ml-0.5 animate-pulse"></span>
      </p>
    </div>

    <!-- Variants Comparison (shown when variants are generated) -->
    <div
      v-if="variants.length > 1"
      class="mb-6 space-y-3"
      data-testid="variants-panel"
    >
      <div class="flex items-center justify-between">
        <h4 class="text-sm font-bold text-gray-700 dark:text-gray-300">Varianten-Vorschau</h4>
        <span class="text-xs text-gray-400">{{ variants.length }} Varianten</span>
      </div>

      <div class="grid grid-cols-1 gap-3">
        <button
          v-for="(variant, idx) in variants"
          :key="idx"
          @click="selectVariant(idx)"
          class="text-left p-4 rounded-xl border-2 transition-all"
          :class="selectedVariantIndex === idx
            ? 'border-[#3B7AB1] bg-[#3B7AB1]/5 shadow-md'
            : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'"
          :data-testid="`variant-${idx}`"
        >
          <div class="flex items-center gap-2 mb-2">
            <span
              class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
              :class="selectedVariantIndex === idx
                ? 'bg-[#3B7AB1] text-white'
                : 'bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300'"
            >{{ idx + 1 }}</span>
            <span v-if="selectedVariantIndex === idx" class="text-xs font-semibold text-[#3B7AB1]">Ausgewaehlt</span>
            <span v-if="variant.source" class="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500">
              {{ variant.source === 'gemini' ? 'KI' : 'Vorlage' }}
            </span>
          </div>
          <p class="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-1 line-clamp-1">
            {{ variant.slides?.[0]?.headline || 'Kein Titel' }}
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
            {{ variant.slides?.[0]?.body_text || variant.caption_instagram || '' }}
          </p>
        </button>
      </div>

      <!-- Apply selected variant button -->
      <button
        @click="applyVariant"
        class="w-full px-4 py-2.5 bg-[#3B7AB1] hover:bg-[#2E6A9E] text-white font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
        data-testid="apply-variant-btn"
      >
        <AppIcon name="check-circle" class="w-4 h-4" /> Variante {{ selectedVariantIndex + 1 }} uebernehmen
      </button>
    </div>

    <!-- Error display -->
    <div
      v-if="variantError"
      class="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-600 dark:text-red-400 flex items-center gap-2"
      data-testid="variant-error"
    >
      <AppIcon name="warning" class="w-4 h-4 flex-shrink-0" />
      {{ variantError }}
    </div>

    <!-- Generated content summary -->
    <div v-if="generatedContent && !variants.length" class="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700 text-left">
      <div class="flex items-center gap-2 text-green-600 dark:text-green-400 mb-3">
        <AppIcon name="check-circle" class="w-5 h-5" />
        <span class="font-bold">{{ generatedContent.humor_format ? 'Humor-Content generiert!' : 'Inhalt generiert!' }}</span>
      </div>
      <ul class="text-sm text-gray-600 dark:text-gray-400 space-y-1 list-disc list-inside" data-testid="generation-summary">
        <li>{{ (generatedContent.slides?.length || 0) }} Slide(s) mit Texten</li>
        <li>Instagram Caption erstellt</li>
        <li>TikTok Caption erstellt</li>
        <li>Hashtags generiert</li>
        <li v-if="generatedContent.humor_format">Humor-Format: {{ generatedContent.humor_format }}</li>
        <li v-if="generatedContent.source">Quelle: {{ generatedContent.source === 'gemini' ? 'KI (Gemini)' : 'Vorlage' }}</li>
      </ul>

      <!-- Nochmal generieren button -->
      <button
        @click="triggerGenerate"
        :disabled="generating || disabled"
        class="mt-4 px-4 py-2 text-sm font-medium rounded-lg border border-[#3B7AB1] text-[#3B7AB1] hover:bg-[#3B7AB1]/10 transition-colors flex items-center gap-1.5 disabled:opacity-40"
        data-testid="regenerate-btn"
      >
        <AppIcon name="arrow-path" class="w-4 h-4" /> Nochmal generieren
      </button>
    </div>

    <!-- Slot for additional content (e.g. HookSelector) -->
    <slot name="after-generation" />
  </div>
</template>
