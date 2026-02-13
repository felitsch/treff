<template>
  <div class="cliffhanger-panel rounded-xl border border-amber-200 dark:border-amber-800 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 overflow-hidden" data-testid="cliffhanger-panel">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-amber-100 to-orange-100 dark:from-amber-900/40 dark:to-orange-900/40 border-b border-amber-200 dark:border-amber-800">
      <div class="flex items-center gap-2">
        <span class="text-xl">👀</span>
        <h3 class="text-sm font-bold text-amber-900 dark:text-amber-200">Cliffhanger & Teaser</h3>
      </div>
      <div class="flex items-center gap-2">
        <span v-if="isLastEpisode" class="inline-flex items-center gap-1 px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-full text-[10px] font-semibold">
          <span>🏁</span> Letzte Episode
        </span>
        <button
          @click="generateCliffhanger"
          :disabled="generating"
          class="inline-flex items-center gap-1 px-3 py-1.5 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-xs font-semibold transition-colors"
          data-testid="generate-cliffhanger-btn"
        >
          <span v-if="generating" class="animate-spin inline-block h-3 w-3 border-2 border-white border-t-transparent rounded-full"></span>
          <span v-else>✨</span>
          {{ generating ? 'Generiere...' : 'Generieren' }}
        </button>
      </div>
    </div>

    <div class="p-4 space-y-4">
      <!-- Cliffhanger Text -->
      <div>
        <label class="block text-xs font-semibold text-amber-800 dark:text-amber-300 mb-1">
          📖 Cliffhanger-Text
        </label>
        <textarea
          v-model="cliffhangerText"
          rows="2"
          placeholder="Ein packender Cliffhanger fuer das Ende der Episode..."
          class="w-full px-3 py-2 rounded-lg border border-amber-300 dark:border-amber-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-amber-500 focus:border-transparent resize-none"
          data-testid="cliffhanger-text-input"
          @input="emitUpdate"
        ></textarea>
      </div>

      <!-- Teaser Variant Selector -->
      <div>
        <label class="block text-xs font-semibold text-amber-800 dark:text-amber-300 mb-2">
          🎯 Teaser-Variante
        </label>
        <div class="grid grid-cols-3 gap-2">
          <button
            v-for="(variant, key) in teaserVariants"
            :key="key"
            @click="selectVariant(key)"
            :class="[
              'flex flex-col items-center gap-1 p-3 rounded-lg border-2 text-xs transition-all',
              selectedVariant === key
                ? 'border-amber-500 bg-amber-100 dark:bg-amber-900/40 text-amber-900 dark:text-amber-200 shadow-md'
                : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-amber-300 dark:hover:border-amber-600'
            ]"
            :data-testid="'teaser-variant-' + key"
          >
            <span class="text-lg">{{ variant.icon }}</span>
            <span class="font-semibold">{{ variant.label }}</span>
            <span class="text-[10px] opacity-70">{{ variant.description }}</span>
          </button>
        </div>
      </div>

      <!-- Days Until Next (for countdown variant) -->
      <div v-if="selectedVariant === 'countdown'" class="flex items-center gap-3">
        <label class="text-xs font-semibold text-amber-800 dark:text-amber-300 whitespace-nowrap">
          ⏳ Tage bis naechste Episode:
        </label>
        <input
          v-model.number="daysUntilNext"
          type="number"
          min="1"
          max="30"
          class="w-20 px-3 py-1.5 rounded-lg border border-amber-300 dark:border-amber-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-amber-500 focus:border-transparent text-center"
          data-testid="days-until-next-input"
          @input="emitUpdate"
        />
      </div>

      <!-- Teaser Text -->
      <div>
        <label class="block text-xs font-semibold text-amber-800 dark:text-amber-300 mb-1">
          💬 Teaser-Text
        </label>
        <textarea
          v-model="teaserText"
          rows="2"
          :placeholder="teaserPlaceholder"
          class="w-full px-3 py-2 rounded-lg border border-amber-300 dark:border-amber-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-amber-500 focus:border-transparent resize-none"
          data-testid="teaser-text-input"
          @input="emitUpdate"
        ></textarea>
      </div>

      <!-- All Variants Display (when generated) -->
      <div v-if="allVariants && Object.keys(allVariants).length > 0" class="space-y-2">
        <label class="block text-xs font-semibold text-amber-800 dark:text-amber-300">
          🔄 Alle Varianten (zum Wechseln klicken)
        </label>
        <div class="space-y-1.5">
          <button
            v-for="(text, key) in allVariants"
            :key="key"
            @click="applyVariant(key, text)"
            :class="[
              'w-full text-left px-3 py-2 rounded-lg text-xs transition-all flex items-start gap-2',
              selectedVariant === key
                ? 'bg-amber-200 dark:bg-amber-800/40 text-amber-900 dark:text-amber-200 ring-2 ring-amber-400'
                : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-amber-50 dark:hover:bg-amber-900/20 border border-gray-200 dark:border-gray-700'
            ]"
            :data-testid="'variant-option-' + key"
          >
            <span class="mt-0.5 shrink-0">{{ variantIcons[key] }}</span>
            <span>{{ text }}</span>
          </button>
        </div>
      </div>

      <!-- Next Episode Link -->
      <div v-if="nextEpisodeInfo" class="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-sm">🔗</span>
            <div>
              <span class="text-xs font-semibold text-blue-800 dark:text-blue-300">Naechste Episode verknuepft:</span>
              <div class="text-xs text-blue-600 dark:text-blue-400 mt-0.5">
                E{{ nextEpisodeInfo.episode_number }}: {{ nextEpisodeInfo.episode_title }}
                <span v-if="nextEpisodeInfo.post && nextEpisodeInfo.post.scheduled_date" class="text-blue-500 dark:text-blue-500">
                  · {{ formatDate(nextEpisodeInfo.post.scheduled_date) }}
                </span>
              </div>
            </div>
          </div>
          <a
            v-if="nextEpisodeInfo.post"
            :href="'/posts/' + nextEpisodeInfo.post.id + '/edit'"
            class="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200 underline"
            data-testid="next-episode-link"
          >
            Oeffnen →
          </a>
        </div>
      </div>

      <!-- Preview Card -->
      <div v-if="cliffhangerText || teaserText" class="rounded-xl overflow-hidden" data-testid="cliffhanger-preview">
        <div class="bg-[#1A1A2E] p-6 text-center space-y-4">
          <div class="text-5xl animate-pulse">👀</div>
          <p class="text-white/90 text-sm italic leading-relaxed max-w-xs mx-auto">{{ cliffhangerText }}</p>
          <div class="w-12 h-0.5 bg-[#FDD000] mx-auto rounded"></div>
          <h4 class="text-[#FDD000] text-lg font-extrabold">Fortsetzung folgt...</h4>
          <p v-if="teaserText" class="text-white/50 text-xs">{{ teaserText }}</p>
          <div class="flex items-center justify-center gap-1.5 mt-2">
            <div class="h-1 bg-[#FDD000] rounded-full" :style="{ width: progressWidth }"></div>
            <div class="h-1 bg-white/10 rounded-full flex-1"></div>
          </div>
          <p class="text-white/30 text-[10px]">@treff_sprachreisen</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/utils/api'

const props = defineProps({
  arcId: { type: Number, required: true },
  episodeNumber: { type: Number, default: 1 },
  plannedEpisodes: { type: Number, default: 8 },
  episodeContent: { type: String, default: '' },
  initialCliffhanger: { type: String, default: '' },
  initialTeaser: { type: String, default: '' },
  initialVariant: { type: String, default: 'question' },
})

const emit = defineEmits(['update:cliffhanger', 'update:teaser', 'update:variant', 'generated'])

// State
const cliffhangerText = ref(props.initialCliffhanger)
const teaserText = ref(props.initialTeaser)
const selectedVariant = ref(props.initialVariant)
const daysUntilNext = ref(1)
const generating = ref(false)
const allVariants = ref({})
const nextEpisodeInfo = ref(null)
const isLastEpisode = ref(false)

const teaserVariants = {
  countdown: { label: 'Countdown', description: 'Noch X Tage...', icon: '⏳' },
  question: { label: 'Frage', description: 'Was passiert...?', icon: '❓' },
  spoiler: { label: 'Spoiler', description: 'Naechstes Mal:', icon: '👀' },
}

const variantIcons = { countdown: '⏳', question: '❓', spoiler: '👀' }

const teaserPlaceholder = computed(() => {
  const placeholders = {
    countdown: 'Noch 2 Tage bis...',
    question: 'Was passiert, wenn...?',
    spoiler: 'Naechstes Mal: Der erste Schnee',
  }
  return placeholders[selectedVariant.value] || 'Teaser fuer die naechste Episode...'
})

const progressWidth = computed(() => {
  if (!props.plannedEpisodes) return '20%'
  const pct = Math.round((props.episodeNumber / props.plannedEpisodes) * 100)
  return `${Math.min(pct, 95)}%`
})

// Watch prop changes
watch(() => props.initialCliffhanger, (val) => { if (val !== cliffhangerText.value) cliffhangerText.value = val })
watch(() => props.initialTeaser, (val) => { if (val !== teaserText.value) teaserText.value = val })
watch(() => props.initialVariant, (val) => { if (val !== selectedVariant.value) selectedVariant.value = val })

function selectVariant(key) {
  selectedVariant.value = key
  // Apply variant text if available
  if (allVariants.value[key]) {
    teaserText.value = allVariants.value[key]
  }
  emitUpdate()
}

function applyVariant(key, text) {
  selectedVariant.value = key
  teaserText.value = text
  emitUpdate()
}

function emitUpdate() {
  emit('update:cliffhanger', cliffhangerText.value)
  emit('update:teaser', teaserText.value)
  emit('update:variant', selectedVariant.value)
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
  } catch { return dateStr }
}

async function generateCliffhanger() {
  generating.value = true
  try {
    const response = await api.post('/api/ai/generate-cliffhanger', {
      arc_id: props.arcId,
      episode_number: props.episodeNumber,
      episode_content: props.episodeContent,
      teaser_variant: selectedVariant.value,
      days_until_next: daysUntilNext.value,
    })
    const data = response.data
    cliffhangerText.value = data.cliffhanger_text || ''
    teaserText.value = data.teaser_text || ''
    selectedVariant.value = data.teaser_variant || 'question'
    allVariants.value = data.all_variants || {}
    nextEpisodeInfo.value = data.next_episode_info || null
    isLastEpisode.value = data.is_last_episode || false
    emitUpdate()
    emit('generated', data)
  } catch (err) {
    console.error('Cliffhanger generation failed:', err)
  } finally {
    generating.value = false
  }
}

onMounted(() => {
  // If we have initial values, don't auto-generate
  if (props.initialCliffhanger || props.initialTeaser) return
})
</script>
