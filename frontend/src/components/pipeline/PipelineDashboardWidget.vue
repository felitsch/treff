<script setup>
/**
 * PipelineDashboardWidget.vue — Content Pipeline Status Dashboard Widget
 *
 * Visualizes the content pipeline funnel and shows items at different stages:
 *   Received → Analyzed → Drafted → Scheduled
 *
 * Features:
 * - Funnel visualization with animated counts per stage
 * - Click on a stage to filter and show items in that status
 * - Quick-action buttons: "Alle analysieren", "Vorschlaege reviewen"
 * - Compact mobile view (only numbers, no funnel)
 * - Integrates with useContentPipelineStore for data
 *
 * @see Feature #301 — P-01: Pipeline Dashboard Widget
 * @see stores/contentPipeline.js — Pipeline state management
 * @see DashboardView.vue — Parent integration
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useContentPipelineStore } from '@/stores/contentPipeline'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import PipelineItemCard from './PipelineItemCard.vue'

const router = useRouter()
const pipelineStore = useContentPipelineStore()

const props = defineProps({
  /** Whether the widget data is still loading */
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['refresh'])

// ═══════════════════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════════════════

/** Currently selected funnel stage (null = overview, or a status string) */
const activeStage = ref(null)

/** Local loading for pipeline-specific fetches */
const fetchingItems = ref(false)

/** Filtered items for the active stage */
const filteredItems = ref([])

// ═══════════════════════════════════════════════════════════════════════
// PIPELINE FUNNEL STAGES
// ═══════════════════════════════════════════════════════════════════════

const funnelStages = [
  {
    key: 'pending',
    label: 'Empfangen',
    icon: 'inbox-arrow-down',
    color: 'text-amber-600 dark:text-amber-400',
    bgColor: 'bg-amber-50 dark:bg-amber-900/20',
    borderColor: 'border-amber-200 dark:border-amber-800',
    barColor: 'bg-amber-400',
    activeRing: 'ring-amber-300 dark:ring-amber-600',
  },
  {
    key: 'analyzed',
    label: 'Analysiert',
    icon: 'sparkles',
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    borderColor: 'border-blue-200 dark:border-blue-800',
    barColor: 'bg-blue-400',
    activeRing: 'ring-blue-300 dark:ring-blue-600',
  },
  {
    key: 'processed',
    label: 'Entwurf',
    icon: 'document-text',
    color: 'text-cyan-600 dark:text-cyan-400',
    bgColor: 'bg-cyan-50 dark:bg-cyan-900/20',
    borderColor: 'border-cyan-200 dark:border-cyan-800',
    barColor: 'bg-cyan-400',
    activeRing: 'ring-cyan-300 dark:ring-cyan-600',
  },
  {
    key: 'scheduled',
    label: 'Geplant',
    icon: 'calendar',
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-50 dark:bg-green-900/20',
    borderColor: 'border-green-200 dark:border-green-800',
    barColor: 'bg-green-400',
    activeRing: 'ring-green-300 dark:ring-green-600',
  },
]

// ═══════════════════════════════════════════════════════════════════════
// COMPUTED
// ═══════════════════════════════════════════════════════════════════════

/** Count items per stage from store data */
const stageCounts = computed(() => {
  const items = pipelineStore.inboxItems || []
  const counts = {}
  for (const stage of funnelStages) {
    counts[stage.key] = items.filter(item => item.status === stage.key).length
  }
  return counts
})

/** Total items in pipeline */
const totalItems = computed(() => {
  return Object.values(stageCounts.value).reduce((sum, c) => sum + c, 0)
})

/** Max count for funnel bar width scaling */
const maxCount = computed(() => {
  const vals = Object.values(stageCounts.value)
  return Math.max(...vals, 1)
})

/** Whether there's a bottleneck (analyzed items > drafted) */
const hasBottleneck = computed(() => {
  return (stageCounts.value.analyzed || 0) > (stageCounts.value.processed || 0) * 2
})

/** Items needing attention (pending or analyzed, not yet processed) */
const actionableCount = computed(() => {
  return (stageCounts.value.pending || 0) + (stageCounts.value.analyzed || 0)
})

// ═══════════════════════════════════════════════════════════════════════
// METHODS
// ═══════════════════════════════════════════════════════════════════════

/** Click on a funnel stage to filter items */
async function selectStage(stageKey) {
  if (activeStage.value === stageKey) {
    activeStage.value = null
    filteredItems.value = []
    return
  }
  activeStage.value = stageKey
  fetchingItems.value = true
  try {
    await pipelineStore.fetchInbox({ status: stageKey })
    filteredItems.value = pipelineStore.inboxItems.filter(item => item.status === stageKey)
  } catch {
    filteredItems.value = []
  } finally {
    fetchingItems.value = false
  }
}

/** Quick action: Navigate to pipeline review */
function reviewSuggestions() {
  router.push('/students')
}

/** Quick action: Navigate to create from pipeline */
function processItem(item) {
  router.push({
    path: '/create/quick',
    query: {
      country: item.detected_country || item.student_country || '',
      source: 'pipeline',
      pipeline_id: item.id,
    },
  })
}

/** Quick action: Review single item */
function reviewItem(item) {
  router.push({
    path: '/students',
    query: { pipeline_id: item.id },
  })
}

/** Refresh pipeline data */
async function refresh() {
  try {
    await pipelineStore.fetchInbox()
  } catch {
    // Non-critical
  }
  emit('refresh')
}

// ═══════════════════════════════════════════════════════════════════════
// LIFECYCLE
// ═══════════════════════════════════════════════════════════════════════

onMounted(async () => {
  if (!pipelineStore.hasItems) {
    try {
      await pipelineStore.fetchInbox()
    } catch {
      // Non-critical on dashboard
    }
  }
})
</script>

<template>
  <BaseCard padding="none" data-tour="dashboard-pipeline" data-testid="pipeline-dashboard-widget">
    <template #header>
      <h2 class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
        <AppIcon name="funnel" class="w-5 h-5" /> Content-Pipeline
        <span
          v-if="totalItems > 0"
          class="ml-1 text-[10px] font-bold bg-[#4C8BC2] text-white px-1.5 py-0.5 rounded-full"
        >
          {{ totalItems }}
        </span>
        <!-- Bottleneck warning -->
        <span
          v-if="hasBottleneck"
          class="text-[9px] font-medium bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300 px-1.5 py-0.5 rounded-full"
          title="Engpass erkannt: Viele analysierte Items warten auf Verarbeitung"
        >
          Engpass
        </span>
      </h2>
    </template>
    <template #headerAction>
      <div class="flex items-center gap-2">
        <button
          @click="refresh"
          class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          title="Aktualisieren"
          :disabled="loading || pipelineStore.loading"
        >
          <svg
            class="w-4 h-4"
            :class="{ 'animate-spin': loading || pipelineStore.loading }"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
        <button
          @click="reviewSuggestions"
          class="text-xs text-[#4C8BC2] hover:text-blue-600 dark:hover:text-blue-400 font-medium"
        >
          Alle anzeigen &rarr;
        </button>
      </div>
    </template>

    <div class="p-4">
      <!-- Loading skeleton -->
      <div v-if="loading" class="space-y-3">
        <div v-for="i in 4" :key="'sk-'+i" class="flex items-center gap-3 animate-pulse">
          <div class="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-lg flex-shrink-0"></div>
          <div class="flex-1">
            <div class="h-2.5 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
          </div>
          <div class="w-6 h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>

      <!-- Empty state -->
      <EmptyState
        v-else-if="totalItems === 0 && !pipelineStore.loading"
        svgIcon="funnel"
        title="Pipeline ist leer"
        description="Wenn Schüler neue Inhalte teilen oder du Medien hochlädst, erscheinen sie hier im Workflow."
        :compact="true"
      />

      <!-- Funnel visualization -->
      <div v-else>
        <!-- Desktop: Full funnel with bars -->
        <div class="hidden sm:block space-y-1.5" data-testid="pipeline-funnel">
          <button
            v-for="(stage, idx) in funnelStages"
            :key="stage.key"
            @click="selectStage(stage.key)"
            class="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg border transition-all text-left"
            :class="[
              activeStage === stage.key
                ? `${stage.bgColor} ${stage.borderColor} ring-2 ${stage.activeRing}`
                : 'border-transparent hover:bg-gray-50 dark:hover:bg-gray-800/50',
            ]"
            :data-testid="`pipeline-stage-${stage.key}`"
          >
            <!-- Stage icon -->
            <div
              class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
              :class="stage.bgColor"
            >
              <AppIcon :name="stage.icon" class="w-4 h-4" :class="stage.color" />
            </div>

            <!-- Label + bar -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between mb-1">
                <span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ stage.label }}</span>
                <span class="text-xs font-bold" :class="stage.color">{{ stageCounts[stage.key] || 0 }}</span>
              </div>
              <!-- Funnel bar -->
              <div class="h-1.5 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :class="stage.barColor"
                  :style="{ width: `${((stageCounts[stage.key] || 0) / maxCount) * 100}%` }"
                ></div>
              </div>
            </div>

            <!-- Arrow between stages -->
            <span
              v-if="idx < funnelStages.length - 1"
              class="text-gray-300 dark:text-gray-600 text-xs flex-shrink-0 hidden lg:block"
            >
              &#8594;
            </span>
          </button>
        </div>

        <!-- Mobile: Compact number-only view -->
        <div class="sm:hidden grid grid-cols-4 gap-2" data-testid="pipeline-funnel-mobile">
          <button
            v-for="stage in funnelStages"
            :key="stage.key"
            @click="selectStage(stage.key)"
            class="flex flex-col items-center gap-1 py-2 rounded-lg transition-all"
            :class="[
              activeStage === stage.key
                ? `${stage.bgColor} ring-2 ${stage.activeRing}`
                : 'hover:bg-gray-50 dark:hover:bg-gray-800/50',
            ]"
          >
            <span class="text-lg font-bold" :class="stage.color">{{ stageCounts[stage.key] || 0 }}</span>
            <span class="text-[9px] text-gray-500 dark:text-gray-400 font-medium">{{ stage.label }}</span>
          </button>
        </div>

        <!-- Quick action buttons -->
        <div class="flex items-center gap-2 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
          <button
            v-if="stageCounts.pending > 0"
            @click="reviewSuggestions"
            class="flex-1 flex items-center justify-center gap-1.5 text-[10px] font-semibold py-1.5 rounded-lg text-[#4C8BC2] border border-[#4C8BC2]/30 hover:bg-[#4C8BC2]/10 transition-colors"
            data-testid="pipeline-action-analyze"
          >
            <AppIcon name="sparkles" class="w-3 h-3" />
            Alle analysieren
          </button>
          <button
            v-if="stageCounts.analyzed > 0"
            @click="reviewSuggestions"
            class="flex-1 flex items-center justify-center gap-1.5 text-[10px] font-semibold py-1.5 rounded-lg text-white bg-[#4C8BC2] hover:bg-[#3B7AB1] transition-colors"
            data-testid="pipeline-action-review"
          >
            <AppIcon name="eye" class="w-3 h-3" />
            Vorschlaege reviewen
          </button>
          <button
            v-if="actionableCount === 0 && totalItems > 0"
            @click="reviewSuggestions"
            class="flex-1 flex items-center justify-center gap-1.5 text-[10px] font-medium py-1.5 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <AppIcon name="check-circle" class="w-3 h-3" />
            Alles erledigt
          </button>
        </div>

        <!-- Filtered items list (when a stage is selected) -->
        <div
          v-if="activeStage && filteredItems.length > 0"
          class="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 space-y-1.5"
          data-testid="pipeline-filtered-items"
        >
          <PipelineItemCard
            v-for="item in filteredItems.slice(0, 5)"
            :key="item.id"
            :item="item"
            compact
            @process="processItem"
            @review="reviewItem"
          />
          <button
            v-if="filteredItems.length > 5"
            @click="reviewSuggestions"
            class="w-full text-center text-[10px] text-[#4C8BC2] font-medium py-1 hover:underline"
          >
            +{{ filteredItems.length - 5 }} weitere anzeigen
          </button>
        </div>

        <!-- Loading filtered items -->
        <div
          v-else-if="activeStage && fetchingItems"
          class="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700"
        >
          <div class="flex items-center justify-center py-4">
            <div class="animate-spin w-5 h-5 border-2 border-[#4C8BC2] border-t-transparent rounded-full"></div>
          </div>
        </div>

        <!-- No items in selected stage -->
        <div
          v-else-if="activeStage && !fetchingItems && filteredItems.length === 0"
          class="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 text-center py-3"
        >
          <p class="text-xs text-gray-400 dark:text-gray-500">Keine Items in diesem Status</p>
        </div>
      </div>
    </div>
  </BaseCard>
</template>
