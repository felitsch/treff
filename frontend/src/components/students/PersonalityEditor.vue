<script setup>
import { ref, computed, watch } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => null,
  },
})

const emit = defineEmits(['update:modelValue'])

// Default personality preset structure
const defaultPreset = {
  tone: 'witzig',
  humor_level: 3,
  emoji_usage: 'moderate',
  perspective: 'first_person',
  catchphrases: [],
}

// Parse incoming modelValue (could be a JSON string or object)
function parsePreset(val) {
  if (!val) return { ...defaultPreset }
  if (typeof val === 'string') {
    try {
      return { ...defaultPreset, ...JSON.parse(val) }
    } catch {
      return { ...defaultPreset }
    }
  }
  return { ...defaultPreset, ...val }
}

const preset = ref(parsePreset(props.modelValue))
const newCatchphrase = ref('')

// Watch for external changes
watch(() => props.modelValue, (val) => {
  preset.value = parsePreset(val)
}, { deep: true })

// Emit changes as JSON string
function emitUpdate() {
  emit('update:modelValue', JSON.stringify(preset.value))
}

// Watch preset changes and emit
watch(preset, () => {
  emitUpdate()
}, { deep: true })

// Catchphrase management
function addCatchphrase() {
  const phrase = newCatchphrase.value.trim()
  if (phrase && !preset.value.catchphrases.includes(phrase)) {
    if (preset.value.catchphrases.length < 5) {
      preset.value.catchphrases.push(phrase)
      newCatchphrase.value = ''
    }
  }
}

function removeCatchphrase(index) {
  preset.value.catchphrases.splice(index, 1)
}

const toneOptions = [
  { value: 'witzig', label: 'Witzig', icon: 'face-smile' },
  { value: 'emotional', label: 'Emotional', icon: 'heart' },
  { value: 'motivierend', label: 'Motivierend', icon: 'rocket' },
  { value: 'jugendlich', label: 'Jugendlich', icon: 'sparkles' },
  { value: 'serioess', label: 'Serioees', icon: 'clipboard-list' },
  { value: 'storytelling', label: 'Storytelling', icon: 'book-open' },
  { value: 'behind-the-scenes', label: 'Behind the Scenes', icon: 'film' },
  { value: 'provokant', label: 'Provokant', icon: 'bolt' },
  { value: 'wholesome', label: 'Wholesome', icon: 'heart' },
  { value: 'informativ', label: 'Informativ', icon: 'chart-bar' },
]

const emojiOptions = [
  { value: 'none', label: 'Keine', desc: 'Kein Emoji-Einsatz' },
  { value: 'minimal', label: 'Minimal', desc: '1-2 Emojis' },
  { value: 'moderate', label: 'Moderat', desc: '3-5 Emojis' },
  { value: 'heavy', label: 'Viel', desc: '6-10 Emojis' },
]

const perspectiveOptions = [
  { value: 'first_person', label: 'Ich-Perspektive', desc: '"Ich habe erlebt..."' },
  { value: 'third_person', label: 'Dritte Person', desc: '"Er/Sie hat erlebt..."' },
]

const humorLevelLabels = ['Kaum', 'Leicht', 'Ausgewogen', 'Deutlich', 'Maximal']

const currentHumorLabel = computed(() => humorLevelLabels[preset.value.humor_level - 1] || 'Ausgewogen')
</script>

<template>
  <div class="space-y-5">
    <div class="flex items-center gap-2 mb-1">
      <AppIcon name="user" class="w-5 h-5" />
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Persoenlichkeits-Preset</h3>
    </div>

    <!-- Tone -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Ton / Stil</label>
      <div class="grid grid-cols-2 gap-2">
        <button
          v-for="opt in toneOptions"
          :key="opt.value"
          type="button"
          :class="[
            'flex items-center gap-2 px-3 py-2 rounded-lg border text-sm text-left transition-all',
            preset.tone === opt.value
              ? 'border-treff-blue bg-treff-blue/10 text-treff-blue font-medium'
              : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-400'
          ]"
          @click="preset.tone = opt.value"
        >
          <AppIcon :name="opt.icon" class="w-4 h-4 inline-block" />
          <span>{{ opt.label }}</span>
        </button>
      </div>
    </div>

    <!-- Humor Level -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Humor-Level: <span class="text-treff-blue font-semibold">{{ preset.humor_level }}/5</span>
        <span class="text-gray-400 ml-1">({{ currentHumorLabel }})</span>
      </label>
      <input
        v-model.number="preset.humor_level"
        type="range"
        min="1"
        max="5"
        step="1"
        class="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-lg appearance-none cursor-pointer accent-treff-blue"
      />
      <div class="flex justify-between text-xs text-gray-400 mt-1 px-0.5">
        <span class="flex items-center gap-0.5"><AppIcon name="face-smile" class="w-3 h-3" /> Kaum</span>
        <span class="flex items-center gap-0.5"><AppIcon name="face-smile" class="w-3 h-3" /> Leicht</span>
        <span class="flex items-center gap-0.5"><AppIcon name="face-smile" class="w-3 h-3" /> Mittel</span>
        <span class="flex items-center gap-0.5"><AppIcon name="face-smile" class="w-3 h-3" /> Deutlich</span>
        <span class="flex items-center gap-0.5"><AppIcon name="fire" class="w-3 h-3" /> Maximal</span>
      </div>
    </div>

    <!-- Emoji Usage -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Emoji-Nutzung</label>
      <div class="grid grid-cols-4 gap-2">
        <button
          v-for="opt in emojiOptions"
          :key="opt.value"
          type="button"
          :class="[
            'px-2 py-2 rounded-lg border text-xs text-center transition-all',
            preset.emoji_usage === opt.value
              ? 'border-treff-blue bg-treff-blue/10 text-treff-blue font-medium'
              : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-400'
          ]"
          @click="preset.emoji_usage = opt.value"
        >
          <div class="font-medium">{{ opt.label }}</div>
          <div class="text-gray-400 text-[10px] mt-0.5">{{ opt.desc }}</div>
        </button>
      </div>
    </div>

    <!-- Perspective -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Perspektive</label>
      <div class="grid grid-cols-2 gap-2">
        <button
          v-for="opt in perspectiveOptions"
          :key="opt.value"
          type="button"
          :class="[
            'px-3 py-2.5 rounded-lg border text-sm text-left transition-all',
            preset.perspective === opt.value
              ? 'border-treff-blue bg-treff-blue/10 text-treff-blue font-medium'
              : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-400'
          ]"
          @click="preset.perspective = opt.value"
        >
          <div class="font-medium">{{ opt.label }}</div>
          <div class="text-gray-400 text-xs mt-0.5">{{ opt.desc }}</div>
        </button>
      </div>
    </div>

    <!-- Catchphrases -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Typische Phrasen
        <span class="text-gray-400 font-normal">({{ preset.catchphrases.length }}/5)</span>
      </label>
      <div v-if="preset.catchphrases.length > 0" class="flex flex-wrap gap-2 mb-2">
        <span
          v-for="(phrase, i) in preset.catchphrases"
          :key="i"
          class="inline-flex items-center gap-1 px-2.5 py-1 bg-treff-yellow/20 text-amber-800 dark:text-amber-300 rounded-full text-sm"
        >
          "{{ phrase }}"
          <button
            type="button"
            class="ml-1 text-amber-600 hover:text-red-500 font-bold"
            @click="removeCatchphrase(i)"
          >
            &times;
          </button>
        </span>
      </div>
      <div v-if="preset.catchphrases.length < 5" class="flex gap-2">
        <input
          v-model="newCatchphrase"
          type="text"
          placeholder='z.B. "Alter, krass!"'
          class="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm dark:bg-gray-700 dark:text-white"
          maxlength="50"
          @keydown.enter.prevent="addCatchphrase"
        />
        <button
          type="button"
          class="px-3 py-1.5 bg-treff-blue text-white rounded-lg text-sm hover:bg-blue-600 transition-colors"
          :disabled="!newCatchphrase.trim()"
          @click="addCatchphrase"
        >
          +
        </button>
      </div>
    </div>

    <!-- Preview summary -->
    <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-xs text-gray-500 dark:text-gray-400">
      <div class="font-medium text-gray-700 dark:text-gray-300 mb-1">Vorschau:</div>
      <AppIcon :name="toneOptions.find(t => t.value === preset.tone)?.icon || 'user'" class="w-4 h-4 inline-block" />
      {{ toneOptions.find(t => t.value === preset.tone)?.label || preset.tone }}
      &middot; Humor {{ preset.humor_level }}/5
      &middot; Emoji: {{ emojiOptions.find(e => e.value === preset.emoji_usage)?.label || preset.emoji_usage }}
      &middot; {{ perspectiveOptions.find(p => p.value === preset.perspective)?.label || preset.perspective }}
      <span v-if="preset.catchphrases.length > 0">
        &middot; {{ preset.catchphrases.length }} Phrasen
      </span>
    </div>
  </div>
</template>
