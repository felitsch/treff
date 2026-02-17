<script setup>
import { ref, computed } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import AppIcon from '@/components/icons/AppIcon.vue'

const props = defineProps({
  topic: { type: String, default: '' },
  country: { type: String, default: '' },
  tone: { type: String, default: 'jugendlich' },
  platform: { type: String, default: 'instagram_feed' },
})

const emit = defineEmits(['hook-selected'])

const toast = useToast()

const hooks = ref([])
const loading = ref(false)
const selectedHookIndex = ref(-1)
const source = ref('')
const hasGenerated = ref(false)

const hookTypeColors = {
  frage: 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-700 hover:border-blue-400',
  statistik: 'bg-purple-50 dark:bg-purple-900/30 border-purple-200 dark:border-purple-700 hover:border-purple-400',
  emotion: 'bg-pink-50 dark:bg-pink-900/30 border-pink-200 dark:border-pink-700 hover:border-pink-400',
  provokation: 'bg-amber-50 dark:bg-amber-900/30 border-amber-200 dark:border-amber-700 hover:border-amber-400',
  story_opener: 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-700 hover:border-green-400',
}

const hookTypeSelectedColors = {
  frage: 'bg-blue-100 dark:bg-blue-800/50 border-blue-500 dark:border-blue-400 ring-2 ring-blue-300 dark:ring-blue-600',
  statistik: 'bg-purple-100 dark:bg-purple-800/50 border-purple-500 dark:border-purple-400 ring-2 ring-purple-300 dark:ring-purple-600',
  emotion: 'bg-pink-100 dark:bg-pink-800/50 border-pink-500 dark:border-pink-400 ring-2 ring-pink-300 dark:ring-pink-600',
  provokation: 'bg-amber-100 dark:bg-amber-800/50 border-amber-500 dark:border-amber-400 ring-2 ring-amber-300 dark:ring-amber-600',
  story_opener: 'bg-green-100 dark:bg-green-800/50 border-green-500 dark:border-green-400 ring-2 ring-green-300 dark:ring-green-600',
}

const hookTypeIconMap = {
  frage: 'question-mark-circle',
  statistik: 'chart-bar',
  emotion: 'heart',
  provokation: 'bolt',
  story_opener: 'book-open',
}

const selectedHook = computed(() => {
  if (selectedHookIndex.value >= 0 && selectedHookIndex.value < hooks.value.length) {
    return hooks.value[selectedHookIndex.value]
  }
  return null
})

async function generateHooks() {
  loading.value = true
  selectedHookIndex.value = -1
  try {
    const response = await api.post('/api/ai/generate-hooks', {
      topic: props.topic || 'Auslandsjahr',
      country: props.country || null,
      tone: props.tone,
      platform: props.platform,
      count: 5,
    })
    hooks.value = response.data.hooks || []
    source.value = response.data.source || 'rule_based'
    hasGenerated.value = true
    toast.success(`${hooks.value.length} Hook-Varianten generiert!`)
  } catch (e) {
    const detail = e.response?.data?.detail || e.message
    toast.error('Hook-Generierung fehlgeschlagen: ' + detail)
  } finally {
    loading.value = false
  }
}

function selectHook(index) {
  if (selectedHookIndex.value === index) {
    // Deselect
    selectedHookIndex.value = -1
    emit('hook-selected', null)
  } else {
    selectedHookIndex.value = index
    const hook = hooks.value[index]
    emit('hook-selected', hook)

    // Save selection to backend for analytics
    api.post('/api/ai/save-hook-selection', {
      hook_text: hook.hook_text,
      hook_type: hook.hook_type,
      topic: props.topic,
      country: props.country,
    }).catch(() => {
      // Silent fail - analytics save is non-critical
    })
  }
}

function getCardClasses(index, hookType) {
  if (selectedHookIndex.value === index) {
    return hookTypeSelectedColors[hookType] || hookTypeSelectedColors.frage
  }
  return hookTypeColors[hookType] || hookTypeColors.frage
}
</script>

<template>
  <div class="hook-selector" data-testid="hook-selector">
    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <AppIcon name="sparkles" class="w-5 h-5" />
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Hook / Attention-Grabber</h3>
      </div>
      <button
        @click="generateHooks"
        :disabled="loading"
        class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors"
        :class="loading
          ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
          : 'bg-[#3B7AB1] hover:bg-[#2E6A9E] text-white'"
        data-testid="generate-hooks-btn"
      >
        <span v-if="loading" class="animate-spin h-3.5 w-3.5 border-2 border-current border-t-transparent rounded-full"></span>
        <AppIcon v-else name="sparkles" class="w-3.5 h-3.5" />
        {{ loading ? 'Generiere...' : (hasGenerated ? 'Neu generieren' : 'Hooks generieren') }}
      </button>
    </div>

    <!-- Description -->
    <p v-if="!hasGenerated" class="text-xs text-gray-500 dark:text-gray-400 mb-3">
      Die ersten 1-3 Sekunden entscheiden, ob jemand weiterliest. Generiere mehrere Hook-Varianten und waehle den besten!
    </p>

    <!-- Hook Cards -->
    <div v-if="hooks.length > 0" class="space-y-2" data-testid="hooks-list">
      <button
        v-for="(hook, index) in hooks"
        :key="index"
        @click="selectHook(index)"
        class="w-full text-left p-3 rounded-xl border-2 transition-all duration-200 cursor-pointer group"
        :class="getCardClasses(index, hook.hook_type)"
        :data-testid="'hook-card-' + index"
      >
        <div class="flex items-start gap-2.5">
          <!-- Type Icon & Badge -->
          <div class="flex-shrink-0 mt-0.5">
            <AppIcon :name="hookTypeIconMap[hook.hook_type] || 'sparkles'" class="w-5 h-5" />
          </div>

          <!-- Hook Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span
                class="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded-full"
                :class="{
                  'bg-blue-200/60 dark:bg-blue-700/40 text-blue-700 dark:text-blue-300': hook.hook_type === 'frage',
                  'bg-purple-200/60 dark:bg-purple-700/40 text-purple-700 dark:text-purple-300': hook.hook_type === 'statistik',
                  'bg-pink-200/60 dark:bg-pink-700/40 text-pink-700 dark:text-pink-300': hook.hook_type === 'emotion',
                  'bg-amber-200/60 dark:bg-amber-700/40 text-amber-700 dark:text-amber-300': hook.hook_type === 'provokation',
                  'bg-green-200/60 dark:bg-green-700/40 text-green-700 dark:text-green-300': hook.hook_type === 'story_opener',
                }"
              >
                {{ hook.hook_type_label }}
              </span>
              <!-- Selected checkmark -->
              <span
                v-if="selectedHookIndex === index"
                class="text-xs font-bold text-green-600 dark:text-green-400 flex items-center gap-0.5"
              >
                ✓ Ausgewaehlt
              </span>
            </div>
            <p class="text-sm text-gray-800 dark:text-gray-200 leading-snug">
              {{ hook.hook_text }}
            </p>
          </div>

          <!-- Selection indicator -->
          <div class="flex-shrink-0 mt-1">
            <div
              class="w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors"
              :class="selectedHookIndex === index
                ? 'border-green-500 bg-green-500'
                : 'border-gray-300 dark:border-gray-600 group-hover:border-gray-400'"
            >
              <span v-if="selectedHookIndex === index" class="text-white text-[10px] font-bold">✓</span>
            </div>
          </div>
        </div>
      </button>
    </div>

    <!-- Selected hook usage hint -->
    <div v-if="selectedHook" class="mt-3 p-2.5 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg" data-testid="hook-usage-hint">
      <p class="text-xs text-green-700 dark:text-green-400">
        <strong>✓ Hook ausgewaehlt:</strong> Wird als erste Zeile deines Posts verwendet.
      </p>
    </div>

    <!-- Source indicator -->
    <div v-if="hasGenerated && hooks.length > 0" class="mt-2 text-right">
      <span class="text-[10px] text-gray-400 dark:text-gray-500">
        Quelle: {{ source === 'gemini' ? 'KI (Gemini)' : 'Vorlage' }}
      </span>
    </div>
  </div>
</template>
