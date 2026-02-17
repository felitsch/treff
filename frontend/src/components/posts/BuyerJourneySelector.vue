<script setup>
/**
 * BuyerJourneySelector.vue — 3-phase Buyer Journey stepper.
 *
 * Shows Awareness / Consideration / Decision as a visual stepper
 * with explanation, matching hooks, and recommended pillars.
 * Responsive: stepper on desktop, compact cards on mobile.
 */
import { ref, computed, onMounted } from 'vue'
import contentStrategy from '@/config/content-strategy.json'
import { CONTENT_PILLARS } from '@/config/contentPillars'
import api from '@/utils/api'
import AppIcon from '@/components/icons/AppIcon.vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  selectedPillar: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'stage-change'])

// Get buyer journey stages from strategy config
const stages = contentStrategy.buyer_journey.stages

// Stage display config
const stageConfig = {
  awareness: { color: '#3B82F6', bgClass: 'bg-blue-50 dark:bg-blue-900/20', borderClass: 'border-blue-300 dark:border-blue-700', textClass: 'text-blue-700 dark:text-blue-300', icon: 'search', ringClass: 'ring-blue-200' },
  consideration: { color: '#8B5CF6', bgClass: 'bg-purple-50 dark:bg-purple-900/20', borderClass: 'border-purple-300 dark:border-purple-700', textClass: 'text-purple-700 dark:text-purple-300', icon: 'question-mark-circle', ringClass: 'ring-purple-200' },
  decision: { color: '#22C55E', bgClass: 'bg-green-50 dark:bg-green-900/20', borderClass: 'border-green-300 dark:border-green-700', textClass: 'text-green-700 dark:text-green-300', icon: 'fire', ringClass: 'ring-green-200' },
}

// Content-mix analysis data for smart hints
const contentMix = ref(null)
const loadingMix = ref(false)

async function loadContentMix() {
  loadingMix.value = true
  try {
    const res = await api.get('/api/analytics/content-mix?period=week')
    contentMix.value = res.data
  } catch {
    contentMix.value = null
  } finally {
    loadingMix.value = false
  }
}

onMounted(loadContentMix)

// Smart hint: which stage is missing this week
const missingStageHint = computed(() => {
  if (!contentMix.value || contentMix.value.total === 0) return null

  // Calculate posts per buyer journey stage based on pillar mapping
  const stageCounts = { awareness: 0, consideration: 0, decision: 0 }
  const cats = contentMix.value.categories || []

  for (const cat of cats) {
    // Map category to pillar, then pillar to buyer journey stages
    const pillar = CONTENT_PILLARS.find(p => p.id === cat.category)
    if (pillar) {
      for (const stage of pillar.buyerJourneyStage) {
        stageCounts[stage] += cat.count
      }
    }
  }

  // Find most underrepresented stage
  const total = contentMix.value.total
  for (const stage of stages) {
    const actual = stageCounts[stage.id] || 0
    const targetPct = stage.target_share / 100
    const actualPct = actual / total
    if (actualPct < targetPct * 0.3 && total >= 2) {
      return stage
    }
  }
  return null
})

// Auto-suggest stage based on selected pillar
const suggestedStage = computed(() => {
  if (!props.selectedPillar) return null
  const pillar = CONTENT_PILLARS.find(p => p.id === props.selectedPillar)
  if (!pillar || !pillar.buyerJourneyStage.length) return null
  // Suggest the first matching stage that's most underrepresented, or default to first
  return pillar.buyerJourneyStage[0]
})

function selectStage(stageId) {
  emit('update:modelValue', stageId)
  emit('stage-change', stageId)
}

// Get matching pillars for a stage
function getPillarsForStage(stageId) {
  return CONTENT_PILLARS.filter(p => p.buyerJourneyStage.includes(stageId))
}

// Show expanded details
const expandedStage = ref('')
function toggleDetails(stageId) {
  expandedStage.value = expandedStage.value === stageId ? '' : stageId
}
</script>

<template>
  <div data-testid="buyer-journey-selector">
    <!-- Smart hint: missing stage this week -->
    <div
      v-if="missingStageHint && !modelValue"
      class="mb-3 p-2.5 rounded-lg flex items-center gap-2 text-xs border"
      :class="[stageConfig[missingStageHint.id]?.bgClass, stageConfig[missingStageHint.id]?.borderClass]"
      data-testid="journey-recommendation"
    >
      <AppIcon :name="stageConfig[missingStageHint.id]?.icon" class="w-5 h-5" :class="stageConfig[missingStageHint.id]?.textClass" />
      <span :class="stageConfig[missingStageHint.id]?.textClass">
        Du hast diese Woche noch keinen <strong>{{ missingStageHint.name.split(' — ')[0] }}</strong>-Post gemacht
        — die Strategie empfiehlt {{ missingStageHint.target_share }}%.
      </span>
      <button
        @click="selectStage(missingStageHint.id)"
        class="ml-auto px-2 py-0.5 text-white rounded text-xs font-medium hover:opacity-90 transition whitespace-nowrap"
        :style="{ backgroundColor: stageConfig[missingStageHint.id]?.color }"
      >
        Waehlen
      </button>
    </div>

    <!-- Auto-suggestion when pillar is selected -->
    <div
      v-if="suggestedStage && !modelValue && selectedPillar"
      class="mb-3 p-2 bg-gray-50 dark:bg-gray-800 rounded-lg text-xs text-gray-600 dark:text-gray-400 flex items-center gap-2"
    >
      <AppIcon name="light-bulb" class="w-4 h-4 text-yellow-500" />
      <span>
        Fuer diesen Pillar passt
        <button @click="selectStage(suggestedStage)" class="font-semibold underline hover:no-underline" :class="stageConfig[suggestedStage]?.textClass">
          {{ stages.find(s => s.id === suggestedStage)?.name.split(' — ')[0] }}
        </button>
        am besten.
      </span>
    </div>

    <!-- Stepper: 3 phases as cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
      <button
        v-for="(stage, index) in stages"
        :key="stage.id"
        @click="selectStage(stage.id)"
        class="relative p-3 rounded-xl border-2 transition-all text-left group"
        :class="modelValue === stage.id
          ? [stageConfig[stage.id]?.bgClass, 'shadow-md ring-2', stageConfig[stage.id]?.ringClass]
          : 'border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 hover:shadow-sm'"
        :style="modelValue === stage.id ? { borderColor: stageConfig[stage.id]?.color } : {}"
        :data-testid="'journey-card-' + stage.id"
      >
        <!-- Step number & icon -->
        <div class="flex items-center gap-2 mb-2">
          <span
            class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white"
            :style="{ backgroundColor: stageConfig[stage.id]?.color }"
          >
            {{ index + 1 }}
          </span>
          <AppIcon :name="stageConfig[stage.id]?.icon" class="w-5 h-5" :class="stageConfig[stage.id]?.textClass" />
          <span class="text-xs font-mono text-gray-400 ml-auto">{{ stage.target_share }}%</span>
        </div>

        <!-- Stage name -->
        <h4 class="text-sm font-bold text-gray-900 dark:text-white">
          {{ stage.name.split(' — ')[0] }}
        </h4>
        <p class="text-[10px] font-medium mt-0.5" :class="stageConfig[stage.id]?.textClass">
          {{ stage.name.split(' — ')[1] }}
        </p>

        <!-- Short description -->
        <p class="text-[10px] text-gray-500 dark:text-gray-400 mt-1.5 line-clamp-2">{{ stage.description }}</p>

        <!-- Matching content types -->
        <div class="flex flex-wrap gap-1 mt-2">
          <span
            v-for="ct in stage.content_types.slice(0, 3)"
            :key="ct"
            class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-[9px] text-gray-600 dark:text-gray-400"
          >
            {{ ct }}
          </span>
        </div>

        <!-- Selected indicator -->
        <div v-if="modelValue === stage.id" class="absolute top-2 right-2">
          <span class="inline-flex items-center justify-center w-5 h-5 rounded-full text-white text-xs" :style="{ backgroundColor: stageConfig[stage.id]?.color }">&#10003;</span>
        </div>
      </button>
    </div>

    <!-- Example hooks when a stage is selected -->
    <div
      v-if="modelValue"
      class="mt-3 p-3 rounded-lg border"
      :class="[stageConfig[modelValue]?.bgClass, stageConfig[modelValue]?.borderClass]"
      data-testid="journey-hooks"
    >
      <div class="flex items-center gap-2 mb-2">
        <AppIcon :name="stageConfig[modelValue]?.icon" class="w-4 h-4" :class="stageConfig[modelValue]?.textClass" />
        <h5 class="text-xs font-bold" :class="stageConfig[modelValue]?.textClass">
          Passende Hook-Formeln fuer {{ stages.find(s => s.id === modelValue)?.name.split(' — ')[0] }}
        </h5>
      </div>
      <div class="space-y-1">
        <div
          v-for="hook in (stages.find(s => s.id === modelValue)?.example_hooks || [])"
          :key="hook"
          class="text-xs text-gray-700 dark:text-gray-300 flex items-start gap-1.5"
        >
          <span class="text-gray-400 mt-0.5">&#8250;</span>
          <span class="italic">&laquo;{{ hook }}&raquo;</span>
        </div>
      </div>
      <!-- Matching KPIs -->
      <div class="mt-2 flex flex-wrap gap-1">
        <span class="text-[9px] text-gray-400 mr-1">KPIs:</span>
        <span
          v-for="metric in (stages.find(s => s.id === modelValue)?.metrics || []).slice(0, 4)"
          :key="metric"
          class="px-1.5 py-0.5 rounded text-[9px] font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400"
        >
          {{ metric }}
        </span>
      </div>
    </div>
  </div>
</template>
