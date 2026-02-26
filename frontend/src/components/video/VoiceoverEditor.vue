<script setup>
/**
 * VoiceoverEditor - Generates and edits voiceover/narration texts with timing markers.
 *
 * Features:
 * - Generates 3 voiceover variants via /api/ai/generate-voiceover
 * - Displays each variant with a timing bar showing sections
 * - Shows speaking duration preview per section
 * - Inline editing of section text
 * - Copy full voiceover or individual sections
 * - Word count / timing accuracy indicator
 */
import { ref, computed, watch } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  /** Pre-fill topic from parent (e.g. VideoScriptView) */
  initialTopic: { type: String, default: '' },
  /** Pre-fill platform */
  initialPlatform: { type: String, default: 'reels' },
  /** Pre-fill duration */
  initialDuration: { type: Number, default: 30 },
  /** Pre-fill tone */
  initialTone: { type: String, default: 'jugendlich' },
  /** Pre-fill hook formula ID */
  initialHookFormulaId: { type: String, default: '' },
  /** Pre-fill country */
  initialCountry: { type: String, default: '' },
  /** Whether to show the generate form (standalone mode) or just the editor */
  showForm: { type: Boolean, default: true },
  /** Compact mode for embedding */
  compact: { type: Boolean, default: false },
})

const emit = defineEmits(['generated', 'select-variant'])

const toast = useToast()

// Form state
const topic = ref(props.initialTopic)
const platform = ref(props.initialPlatform)
const duration = ref(props.initialDuration)
const tone = ref(props.initialTone)
const hookFormulaId = ref(props.initialHookFormulaId)
const country = ref(props.initialCountry)

// Generation state
const isGenerating = ref(false)
const result = ref(null)
const selectedVariant = ref(0)
const editingSectionIndex = ref(-1)
const editText = ref('')

// Sync props when parent updates them
watch(() => props.initialTopic, (v) => { topic.value = v })
watch(() => props.initialPlatform, (v) => { platform.value = v })
watch(() => props.initialDuration, (v) => { duration.value = v })
watch(() => props.initialTone, (v) => { tone.value = v })
watch(() => props.initialHookFormulaId, (v) => { hookFormulaId.value = v })
watch(() => props.initialCountry, (v) => { country.value = v })

const tones = [
  { value: 'jugendlich', label: 'Jugendlich' },
  { value: 'emotional', label: 'Emotional' },
  { value: 'witzig', label: 'Witzig' },
  { value: 'motivierend', label: 'Motivierend' },
  { value: 'informativ', label: 'Informativ' },
  { value: 'storytelling', label: 'Storytelling' },
  { value: 'provokant', label: 'Provokant' },
]

const durations = [
  { value: 15, label: '15s' },
  { value: 30, label: '30s' },
  { value: 60, label: '60s' },
  { value: 90, label: '90s' },
]

const countries = [
  { value: '', label: 'Auto' },
  { value: 'usa', label: 'USA' },
  { value: 'canada', label: 'Kanada' },
  { value: 'australia', label: 'Australien' },
  { value: 'newzealand', label: 'Neuseeland' },
  { value: 'ireland', label: 'Irland' },
]

const currentVariant = computed(() => {
  if (!result.value || !result.value.variants.length) return null
  return result.value.variants[selectedVariant.value] || result.value.variants[0]
})

const timingAccuracy = computed(() => {
  if (!currentVariant.value) return 0
  const { total_words, target_words } = currentVariant.value
  if (!target_words) return 100
  return Math.min(100, Math.round((1 - Math.abs(total_words - target_words) / target_words) * 100))
})

const timingColor = computed(() => {
  const acc = timingAccuracy.value
  if (acc >= 85) return 'text-green-600 dark:text-green-400'
  if (acc >= 65) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-600 dark:text-red-400'
})

const canGenerate = computed(() => topic.value.trim().length > 3)

/**
 * Generate voiceover variants.
 * Can be called externally via template ref.
 */
async function generate(overrides = {}) {
  if (!topic.value.trim() && !overrides.topic) {
    toast.error('Bitte gib ein Thema ein')
    return
  }

  isGenerating.value = true
  try {
    const payload = {
      topic: overrides.topic || topic.value,
      duration_seconds: overrides.duration_seconds || duration.value,
      platform: overrides.platform || platform.value,
      tone: overrides.tone || tone.value,
    }
    if (overrides.hook_formula_id || hookFormulaId.value) {
      payload.hook_formula_id = overrides.hook_formula_id || hookFormulaId.value
    }
    if (overrides.country || country.value) {
      payload.country = overrides.country || country.value
    }

    const { data } = await api.post('/api/ai/generate-voiceover', payload)
    result.value = data
    selectedVariant.value = 0
    editingSectionIndex.value = -1
    toast.success(`${data.variant_count} Voiceover-Varianten generiert!`)
    emit('generated', data)
  } catch (e) {
    console.error('Voiceover generation failed:', e)
    toast.error('Voiceover-Generierung fehlgeschlagen')
  } finally {
    isGenerating.value = false
  }
}

function selectVariant(index) {
  selectedVariant.value = index
  editingSectionIndex.value = -1
  emit('select-variant', result.value.variants[index])
}

function startEditSection(index) {
  editingSectionIndex.value = index
  editText.value = currentVariant.value.sections[index].text
}

function saveEditSection() {
  if (editingSectionIndex.value >= 0 && currentVariant.value) {
    const section = currentVariant.value.sections[editingSectionIndex.value]
    section.text = editText.value
    section.actual_words = editText.value.split(/\s+/).filter(Boolean).length

    // Recalculate totals
    const totalWords = currentVariant.value.sections.reduce((sum, s) => sum + s.actual_words, 0)
    currentVariant.value.total_words = totalWords
    currentVariant.value.estimated_duration_seconds = Math.round(totalWords / 150 * 60 * 10) / 10

    // Rebuild full_text
    currentVariant.value.full_text = currentVariant.value.sections
      .map(s => `[${s.time_marker}] ${s.text}`)
      .join('\n\n')

    editingSectionIndex.value = -1
    toast.success('Abschnitt aktualisiert')
  }
}

function cancelEdit() {
  editingSectionIndex.value = -1
}

function copyFullText() {
  if (!currentVariant.value) return
  navigator.clipboard.writeText(currentVariant.value.full_text).then(() => {
    toast.success('Voiceover-Text kopiert!')
  }).catch(() => {
    toast.error('Kopieren fehlgeschlagen')
  })
}

function copySectionText(section) {
  navigator.clipboard.writeText(section.text).then(() => {
    toast.success('Abschnitt kopiert!')
  }).catch(() => {
    toast.error('Kopieren fehlgeschlagen')
  })
}

function formatSeconds(sec) {
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

function sectionDuration(section) {
  return Math.round(section.actual_words / 150 * 60 * 10) / 10
}

// Label colors for timing bar segments
const labelColors = {
  'Hook': 'bg-red-400 dark:bg-red-600',
  'Ueberleitung': 'bg-amber-400 dark:bg-amber-600',
  'Hauptteil': 'bg-green-400 dark:bg-green-600',
  'Hauptteil 1': 'bg-green-400 dark:bg-green-600',
  'Hauptteil 2': 'bg-green-500 dark:bg-green-700',
  'Beweis/Beispiel': 'bg-purple-400 dark:bg-purple-600',
  'CTA': 'bg-blue-400 dark:bg-blue-600',
}

function getLabelColor(label) {
  return labelColors[label] || 'bg-gray-400 dark:bg-gray-600'
}

// Expose generate for parent access
defineExpose({ generate })
</script>

<template>
  <div :class="compact ? '' : 'space-y-4'">
    <!-- Generate Form (standalone mode) -->
    <div v-if="showForm" class="bg-white dark:bg-gray-800 rounded-xl shadow p-4">
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
        <svg class="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        </svg>
        Voiceover generieren
      </h3>

      <div class="space-y-3">
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Thema *</label>
          <input
            v-model="topic"
            type="text"
            class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="z.B. Mein erster Schultag in den USA"
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Dauer</label>
            <div class="flex gap-1">
              <button
                v-for="d in durations"
                :key="d.value"
                @click="duration = d.value"
                :class="[
                  'flex-1 px-2 py-1.5 text-xs rounded-md border transition-colors',
                  duration === d.value
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 font-medium'
                    : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-300'
                ]"
              >
                {{ d.label }}
              </button>
            </div>
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Tonalitaet</label>
            <select
              v-model="tone"
              class="w-full px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option v-for="t in tones" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
          </div>
        </div>

        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Land</label>
          <div class="flex gap-1 flex-wrap">
            <button
              v-for="c in countries"
              :key="c.value"
              @click="country = c.value"
              :class="[
                'px-2 py-1 text-xs rounded-md border transition-colors',
                country === c.value
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 font-medium'
                  : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-300'
              ]"
            >
              {{ c.label }}
            </button>
          </div>
        </div>

        <button
          @click="generate()"
          :disabled="isGenerating || !canGenerate"
          class="w-full px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          <svg v-if="isGenerating" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          {{ isGenerating ? 'Generiere...' : 'Voiceover generieren' }}
        </button>
      </div>
    </div>

    <!-- Loading state (when called without form) -->
    <div v-if="!showForm && isGenerating" class="flex items-center justify-center py-8">
      <svg class="animate-spin h-6 w-6 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
      <span class="text-sm text-gray-500 dark:text-gray-400">Voiceover wird generiert...</span>
    </div>

    <!-- Results -->
    <div v-if="result && result.variants.length" class="space-y-3">
      <!-- Variant Tabs -->
      <div class="flex items-center gap-2">
        <button
          v-for="(v, i) in result.variants"
          :key="i"
          @click="selectVariant(i)"
          :class="[
            'px-3 py-1.5 text-xs rounded-lg border transition-colors',
            selectedVariant === i
              ? 'border-blue-500 bg-blue-600 text-white font-medium'
              : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
          ]"
        >
          Variante {{ v.variant_number }}
        </button>

        <div class="flex-1" />

        <!-- Source badge -->
        <span :class="[
          'px-2 py-0.5 text-xs rounded-full font-medium',
          result.source === 'gemini'
            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
        ]">
          {{ result.source === 'gemini' ? 'KI' : 'Vorlage' }}
        </span>

        <!-- Copy button -->
        <button
          @click="copyFullText"
          class="px-3 py-1.5 text-xs border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors flex items-center gap-1"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
          </svg>
          Kopieren
        </button>
      </div>

      <!-- Current Variant Display -->
      <div v-if="currentVariant" class="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden">
        <!-- Meta info -->
        <div class="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
          <div class="flex items-center justify-between text-xs">
            <div class="flex items-center gap-3 text-gray-500 dark:text-gray-400">
              <span class="flex items-center gap-1">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {{ currentVariant.estimated_duration_seconds }}s / {{ currentVariant.target_duration_seconds }}s
              </span>
              <span>{{ currentVariant.total_words }} / {{ currentVariant.target_words }} Woerter</span>
              <span class="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700">{{ currentVariant.hook_formula }}</span>
            </div>
            <span :class="[timingColor, 'font-semibold']">
              {{ timingAccuracy }}% Timing
            </span>
          </div>
        </div>

        <!-- Timing Bar -->
        <div class="px-4 pt-3">
          <div class="flex h-6 rounded-lg overflow-hidden">
            <div
              v-for="(section, i) in currentVariant.sections"
              :key="i"
              :class="[
                getLabelColor(section.label),
                'flex items-center justify-center text-white text-[10px] font-medium cursor-pointer hover:opacity-80 transition-opacity border-r border-white/30 last:border-r-0'
              ]"
              :style="{ width: `${Math.max(8, (section.actual_words / currentVariant.total_words) * 100)}%` }"
              :title="`${section.label}: ${sectionDuration(section)}s (~${section.actual_words} Woerter)`"
              @click="startEditSection(i)"
            >
              <span v-if="section.actual_words / currentVariant.total_words > 0.12">
                {{ section.label }}
              </span>
            </div>
          </div>
          <!-- Time markers under the bar -->
          <div class="flex justify-between mt-0.5 text-[10px] text-gray-400 dark:text-gray-500">
            <span>0:00</span>
            <span>{{ formatSeconds(currentVariant.target_duration_seconds / 2) }}</span>
            <span>{{ formatSeconds(currentVariant.target_duration_seconds) }}</span>
          </div>
        </div>

        <!-- Sections -->
        <div class="p-4 space-y-2">
          <div
            v-for="(section, i) in currentVariant.sections"
            :key="i"
            :class="[
              'rounded-lg border p-3 transition-colors',
              editingSectionIndex === i
                ? 'border-blue-300 dark:border-blue-600 bg-blue-50/50 dark:bg-blue-900/10'
                : 'border-gray-100 dark:border-gray-700 hover:border-gray-200 dark:hover:border-gray-600'
            ]"
          >
            <!-- Section header -->
            <div class="flex items-center justify-between mb-1">
              <div class="flex items-center gap-2">
                <span class="text-xs font-mono text-gray-400 dark:text-gray-500">[{{ section.time_marker }}]</span>
                <span :class="[getLabelColor(section.label), 'px-1.5 py-0.5 rounded text-[10px] text-white font-medium']">
                  {{ section.label }}
                </span>
              </div>
              <div class="flex items-center gap-2 text-[10px] text-gray-400 dark:text-gray-500">
                <span>~{{ sectionDuration(section) }}s</span>
                <span>{{ section.actual_words }} Woerter</span>
                <button
                  @click="copySectionText(section)"
                  class="p-0.5 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                  title="Abschnitt kopieren"
                >
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </button>
                <button
                  v-if="editingSectionIndex !== i"
                  @click="startEditSection(i)"
                  class="p-0.5 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                  title="Bearbeiten"
                >
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Editing mode -->
            <div v-if="editingSectionIndex === i" class="space-y-2">
              <textarea
                v-model="editText"
                rows="3"
                class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              />
              <div class="flex items-center gap-2">
                <button
                  @click="saveEditSection"
                  class="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                >
                  Speichern
                </button>
                <button
                  @click="cancelEdit"
                  class="px-3 py-1 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                >
                  Abbrechen
                </button>
                <span class="text-[10px] text-gray-400 ml-auto">
                  {{ editText.split(/\s+/).filter(Boolean).length }} Woerter
                  (~{{ Math.round(editText.split(/\s+/).filter(Boolean).length / 150 * 60 * 10) / 10 }}s)
                </span>
              </div>
            </div>

            <!-- Display mode -->
            <p v-else class="text-sm text-gray-900 dark:text-white leading-relaxed cursor-pointer" @click="startEditSection(i)">
              {{ section.text }}
            </p>
          </div>
        </div>
      </div>

      <!-- Empty state when no variant selected -->
      <div v-else class="text-center py-8 text-gray-400 dark:text-gray-500 text-sm">
        Wähle eine Variante aus
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-if="!result && !isGenerating && !showForm"
      class="text-center py-8 text-gray-400 dark:text-gray-500"
    >
      <svg class="w-8 h-8 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
      </svg>
      <p class="text-sm">Noch kein Voiceover generiert</p>
      <p class="text-xs mt-1">Klicke auf "Voiceover generieren" um loszulegen</p>
    </div>
  </div>
</template>
