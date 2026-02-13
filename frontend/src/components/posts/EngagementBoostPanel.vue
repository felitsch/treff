<script setup>
import { ref, computed, watch } from 'vue'
import api from '@/utils/api'

const props = defineProps({
  postContent: { type: Object, default: () => ({}) },
  platform: { type: String, default: 'instagram_feed' },
  format: { type: String, default: 'instagram_feed' },
  postingTime: { type: String, default: '' },
})

const emit = defineEmits(['apply-suggestion'])

const suggestions = ref([])
const loading = ref(false)
const error = ref('')
const source = ref('')
const isCollapsed = ref(false)

// Priority styling
const priorityConfig = {
  high: {
    label: 'Hoch',
    badge: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
    border: 'border-l-red-500',
    icon: '\u26A0\uFE0F',
  },
  medium: {
    label: 'Mittel',
    badge: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
    border: 'border-l-amber-500',
    icon: '\u{1F4A1}',
  },
  low: {
    label: 'Niedrig',
    badge: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
    border: 'border-l-green-500',
    icon: '\u2139\uFE0F',
  },
}

// Category labels + icons
const categoryConfig = {
  hook: { label: 'Hook', icon: '\u{1F3A3}' },
  cta: { label: 'CTA', icon: '\u{1F4E2}' },
  length: { label: 'Laenge', icon: '\u{1F4CF}' },
  hashtags: { label: 'Hashtags', icon: '#\uFE0F\u20E3' },
  timing: { label: 'Timing', icon: '\u{1F552}' },
  format: { label: 'Format', icon: '\u{1F4F1}' },
  emotion: { label: 'Emotion', icon: '\u2764\uFE0F' },
  interaction: { label: 'Interaktion', icon: '\u{1F4AC}' },
}

// Count suggestions by priority
const highCount = computed(() => suggestions.value.filter(s => s.priority === 'high').length)
const mediumCount = computed(() => suggestions.value.filter(s => s.priority === 'medium').length)
const lowCount = computed(() => suggestions.value.filter(s => s.priority === 'low').length)

// Computed overall score based on suggestions
const engagementScore = computed(() => {
  if (suggestions.value.length === 0) return 100
  let deduction = 0
  for (const s of suggestions.value) {
    if (s.priority === 'high') deduction += 15
    else if (s.priority === 'medium') deduction += 8
    else deduction += 3
  }
  return Math.max(10, 100 - deduction)
})

const scoreColor = computed(() => {
  if (engagementScore.value >= 80) return 'text-green-600 dark:text-green-400'
  if (engagementScore.value >= 50) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-600 dark:text-red-400'
})

const scoreBarColor = computed(() => {
  if (engagementScore.value >= 80) return 'bg-green-500'
  if (engagementScore.value >= 50) return 'bg-amber-500'
  return 'bg-red-500'
})

async function analyzePost() {
  if (loading.value) return

  loading.value = true
  error.value = ''
  suggestions.value = []

  try {
    const res = await api.post('/api/ai/engagement-boost', {
      post_content: props.postContent,
      platform: props.platform,
      format: props.format,
      posting_time: props.postingTime || undefined,
    })

    suggestions.value = res.data.suggestions || []
    source.value = res.data.source || 'rule_based'
  } catch (e) {
    if (e.response?.status === 429) {
      error.value = 'Zu viele Anfragen. Bitte warte einen Moment.'
    } else {
      error.value = 'Analyse fehlgeschlagen. Bitte versuche es erneut.'
    }
    console.warn('Engagement boost analysis failed:', e)
  } finally {
    loading.value = false
  }
}

function applySuggestion(suggestion) {
  emit('apply-suggestion', suggestion)
}
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm" data-testid="engagement-boost-panel">
    <!-- Header -->
    <div
      class="flex items-center justify-between px-4 py-3 cursor-pointer select-none"
      @click="isCollapsed = !isCollapsed"
      data-testid="engagement-boost-header"
    >
      <div class="flex items-center gap-2">
        <span class="text-lg">{{'&#x1F680;'}}</span>
        <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-200">Engagement-Boost</h3>
        <span
          v-if="suggestions.length > 0"
          class="px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-[#3B7AB1] text-white"
        >{{ suggestions.length }}</span>
      </div>
      <div class="flex items-center gap-2">
        <!-- Score badge -->
        <span
          v-if="suggestions.length > 0"
          class="text-xs font-bold"
          :class="scoreColor"
        >{{ engagementScore }}/100</span>
        <svg
          class="w-4 h-4 text-gray-500 transition-transform"
          :class="{ 'rotate-180': !isCollapsed }"
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>

    <!-- Content -->
    <div v-if="!isCollapsed" class="px-4 pb-4">
      <!-- Analyze Button -->
      <button
        @click="analyzePost"
        :disabled="loading"
        class="w-full py-2.5 px-4 rounded-lg text-sm font-medium transition-all duration-200"
        :class="loading
          ? 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
          : 'bg-gradient-to-r from-[#3B7AB1] to-[#4C8BC2] text-white hover:from-[#2F6A9F] hover:to-[#3B7AB1] shadow-sm hover:shadow-md active:scale-[0.98]'"
        data-testid="engagement-boost-analyze-btn"
      >
        <span v-if="loading" class="flex items-center justify-center gap-2">
          <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Analysiere...
        </span>
        <span v-else-if="suggestions.length > 0" class="flex items-center justify-center gap-2">
          <span>{{'&#x1F504;'}}</span>
          Erneut analysieren
        </span>
        <span v-else class="flex items-center justify-center gap-2">
          <span>{{'&#x1F50D;'}}</span>
          Post analysieren
        </span>
      </button>

      <!-- Error -->
      <div v-if="error" class="mt-3 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
        <p class="text-xs text-red-600 dark:text-red-400">{{ error }}</p>
      </div>

      <!-- Results -->
      <div v-if="suggestions.length > 0" class="mt-3 space-y-3" data-testid="engagement-boost-results">
        <!-- Score Bar -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between text-xs">
            <span class="text-gray-500 dark:text-gray-400">Engagement-Score</span>
            <span class="font-bold" :class="scoreColor">{{ engagementScore }}%</span>
          </div>
          <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              :class="scoreBarColor"
              :style="{ width: engagementScore + '%' }"
            ></div>
          </div>
          <div class="flex items-center gap-3 text-[10px] text-gray-500 dark:text-gray-400">
            <span v-if="highCount > 0" class="flex items-center gap-0.5">
              <span class="inline-block w-1.5 h-1.5 rounded-full bg-red-500"></span>
              {{ highCount }} wichtig
            </span>
            <span v-if="mediumCount > 0" class="flex items-center gap-0.5">
              <span class="inline-block w-1.5 h-1.5 rounded-full bg-amber-500"></span>
              {{ mediumCount }} mittel
            </span>
            <span v-if="lowCount > 0" class="flex items-center gap-0.5">
              <span class="inline-block w-1.5 h-1.5 rounded-full bg-green-500"></span>
              {{ lowCount }} optional
            </span>
          </div>
        </div>

        <!-- Suggestion Cards -->
        <div class="space-y-2">
          <div
            v-for="(suggestion, index) in suggestions"
            :key="index"
            class="p-3 rounded-lg border-l-4 bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700 transition-all hover:shadow-sm"
            :class="priorityConfig[suggestion.priority]?.border || 'border-l-gray-400'"
            :data-testid="'engagement-suggestion-' + index"
          >
            <!-- Suggestion Header -->
            <div class="flex items-center justify-between mb-1.5">
              <div class="flex items-center gap-1.5">
                <span class="text-sm">{{ categoryConfig[suggestion.category]?.icon || '\u{1F4A1}' }}</span>
                <span class="text-[10px] font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                  {{ categoryConfig[suggestion.category]?.label || suggestion.category }}
                </span>
              </div>
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-bold text-[#3B7AB1]">{{ suggestion.estimated_boost }}</span>
                <span
                  class="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
                  :class="priorityConfig[suggestion.priority]?.badge || 'bg-gray-100 text-gray-600'"
                >{{ priorityConfig[suggestion.priority]?.label || suggestion.priority }}</span>
              </div>
            </div>

            <!-- Suggestion Text -->
            <p class="text-xs text-gray-700 dark:text-gray-300 leading-relaxed mb-2">
              {{ suggestion.suggestion }}
            </p>

            <!-- Apply Button -->
            <button
              @click="applySuggestion(suggestion)"
              class="w-full py-1.5 px-3 rounded-md text-xs font-medium bg-[#3B7AB1]/10 text-[#3B7AB1] hover:bg-[#3B7AB1]/20 dark:bg-[#3B7AB1]/20 dark:hover:bg-[#3B7AB1]/30 transition-colors"
              :data-testid="'apply-suggestion-' + index"
            >
              {{ suggestion.action_text || 'Anwenden' }}
            </button>
          </div>
        </div>

        <!-- Source indicator -->
        <div class="text-[10px] text-gray-400 dark:text-gray-500 text-center pt-1">
          Analysiert mit {{ source === 'gemini' ? 'KI (Gemini)' : 'Smart-Analyse' }}
        </div>
      </div>

      <!-- Empty state (no analysis yet) -->
      <div v-else-if="!loading && !error" class="mt-3 text-center py-3">
        <p class="text-xs text-gray-400 dark:text-gray-500">
          Klicke auf "Post analysieren" um Vorschlaege zur Engagement-Steigerung zu erhalten.
        </p>
      </div>
    </div>
  </div>
</template>
