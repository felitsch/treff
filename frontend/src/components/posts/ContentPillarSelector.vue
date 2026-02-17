<script setup>
/**
 * ContentPillarSelector.vue — Visual Content Pillar selector with distribution tracking.
 *
 * Shows all 7 content pillars as cards with:
 * - Icon, name, color badge
 * - Current vs. target percentage (IST vs. SOLL)
 * - Smart hints when a pillar is underrepresented
 * - Responsive: cards on desktop, compact dropdown on mobile
 */
import { ref, computed, onMounted, watch } from 'vue'
import { CONTENT_PILLARS, getPillarById } from '@/config/contentPillars'
import api from '@/utils/api'

const props = defineProps({
  modelValue: { type: String, default: '' },
  compact: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'pillar-change'])

// Distribution data from API
const distribution = ref(null)
const loadingDistribution = ref(false)

async function loadDistribution() {
  loadingDistribution.value = true
  try {
    const res = await api.get('/api/content-pillars/distribution/check')
    distribution.value = res.data
  } catch {
    // Graceful fallback — show pillars without distribution
    distribution.value = null
  } finally {
    loadingDistribution.value = false
  }
}

onMounted(loadDistribution)

// Get actual percentage for a pillar from the distribution data
function getActualPercent(pillarId) {
  if (!distribution.value?.pillars) return null
  const p = distribution.value.pillars.find(x => x.pillar_id === pillarId)
  return p ? Math.round(p.actual_percentage || 0) : 0
}

// Check if pillar is underrepresented (below 50% of target)
function isUnderrepresented(pillar) {
  const actual = getActualPercent(pillar.id)
  if (actual === null) return false
  return actual < (pillar.targetPercentage * 0.5)
}

// Smart recommendation: the most underrepresented pillar
const recommendedPillar = computed(() => {
  if (!distribution.value?.pillars) return null
  let bestGap = 0
  let bestPillar = null
  for (const p of CONTENT_PILLARS) {
    const actual = getActualPercent(p.id)
    if (actual === null) continue
    const gap = p.targetPercentage - actual
    if (gap > bestGap) {
      bestGap = gap
      bestPillar = p
    }
  }
  return bestGap > 5 ? bestPillar : null
})

function selectPillar(pillarId) {
  emit('update:modelValue', pillarId)
  emit('pillar-change', pillarId)
}

// Mobile dropdown mode
const showDropdown = ref(false)
</script>

<template>
  <div data-testid="content-pillar-selector">
    <!-- Smart hint: underrepresented pillar -->
    <div
      v-if="recommendedPillar && !modelValue"
      class="mb-3 p-2.5 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg flex items-center gap-2 text-xs"
      data-testid="pillar-recommendation"
    >
      <span class="text-lg">{{ recommendedPillar.icon }}</span>
      <span class="text-amber-800 dark:text-amber-300">
        <strong>{{ recommendedPillar.name }}</strong> ist unterrepräsentiert
        ({{ getActualPercent(recommendedPillar.id) }}% statt {{ recommendedPillar.targetPercentage }}% Ziel).
      </span>
      <button
        @click="selectPillar(recommendedPillar.id)"
        class="ml-auto px-2 py-0.5 bg-amber-600 text-white rounded text-xs font-medium hover:bg-amber-700 transition whitespace-nowrap"
      >
        Wählen
      </button>
    </div>

    <!-- Desktop: Visual cards grid (hidden on small screens if compact) -->
    <div :class="compact ? 'hidden md:grid' : 'hidden md:grid'" class="grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2">
      <button
        v-for="pillar in CONTENT_PILLARS"
        :key="pillar.id"
        @click="selectPillar(pillar.id)"
        class="relative p-3 rounded-xl border-2 transition-all text-left group hover:shadow-md"
        :class="modelValue === pillar.id
          ? 'border-current shadow-md ring-1 ring-current/20'
          : 'border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500'"
        :style="modelValue === pillar.id ? { borderColor: pillar.color, '--tw-ring-color': pillar.color + '33' } : {}"
        :data-testid="'pillar-card-' + pillar.id"
      >
        <!-- Underrepresented indicator -->
        <div v-if="isUnderrepresented(pillar)" class="absolute -top-1.5 -right-1.5 w-4 h-4 bg-amber-400 rounded-full flex items-center justify-center text-[8px] font-bold text-white" title="Unterrepräsentiert">!</div>

        <div class="flex items-start gap-2">
          <span class="text-xl flex-shrink-0">{{ pillar.icon }}</span>
          <div class="min-w-0 flex-1">
            <div class="text-sm font-semibold text-gray-900 dark:text-white truncate">{{ pillar.name }}</div>
            <div class="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">{{ pillar.description }}</div>

            <!-- Distribution bar -->
            <div class="mt-2 flex items-center gap-1.5">
              <div class="flex-1 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :style="{
                    width: Math.min(100, getActualPercent(pillar.id) ?? 0) + '%',
                    backgroundColor: pillar.color
                  }"
                ></div>
              </div>
              <span class="text-[10px] font-mono text-gray-400 dark:text-gray-500 whitespace-nowrap">
                {{ getActualPercent(pillar.id) ?? '—' }}%/{{ pillar.targetPercentage }}%
              </span>
            </div>

            <!-- Buyer Journey stages -->
            <div class="flex gap-1 mt-1.5 flex-wrap">
              <span
                v-for="stage in pillar.buyerJourneyStage"
                :key="stage"
                class="px-1 py-0.5 rounded text-[9px] font-medium"
                :class="{
                  'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300': stage === 'awareness',
                  'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300': stage === 'consideration',
                  'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300': stage === 'decision',
                }"
              >
                {{ stage === 'awareness' ? 'Awareness' : stage === 'consideration' ? 'Consideration' : 'Decision' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Selected checkmark -->
        <div v-if="modelValue === pillar.id" class="absolute top-2 right-2">
          <span class="inline-flex items-center justify-center w-5 h-5 rounded-full text-white text-xs" :style="{ backgroundColor: pillar.color }">&#10003;</span>
        </div>
      </button>
    </div>

    <!-- Mobile: Compact dropdown (visible only on small screens) -->
    <div class="md:hidden">
      <button
        @click="showDropdown = !showDropdown"
        class="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-left flex items-center gap-2"
        data-testid="pillar-dropdown-toggle"
      >
        <template v-if="modelValue">
          <span class="text-lg">{{ getPillarById(modelValue)?.icon }}</span>
          <span class="flex-1 text-sm font-medium text-gray-900 dark:text-white truncate">{{ getPillarById(modelValue)?.name }}</span>
          <span class="text-xs text-gray-400">{{ getActualPercent(modelValue) ?? '—' }}%/{{ getPillarById(modelValue)?.targetPercentage }}%</span>
        </template>
        <template v-else>
          <span class="text-gray-400 text-sm flex-1">Content Pillar wählen...</span>
        </template>
        <svg class="w-4 h-4 text-gray-400 transition-transform" :class="showDropdown ? 'rotate-180' : ''" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" /></svg>
      </button>

      <!-- Dropdown list -->
      <div v-if="showDropdown" class="mt-1 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 shadow-lg max-h-64 overflow-y-auto">
        <button
          v-for="pillar in CONTENT_PILLARS"
          :key="pillar.id"
          @click="selectPillar(pillar.id); showDropdown = false"
          class="w-full px-3 py-2 flex items-center gap-2 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors text-left border-b border-gray-100 dark:border-gray-700 last:border-b-0"
          :class="modelValue === pillar.id ? 'bg-gray-50 dark:bg-gray-700/50' : ''"
        >
          <span class="text-lg flex-shrink-0">{{ pillar.icon }}</span>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ pillar.name }}</div>
            <div class="text-[10px] text-gray-400">{{ getActualPercent(pillar.id) ?? '—' }}%/{{ pillar.targetPercentage }}% Ziel</div>
          </div>
          <span v-if="modelValue === pillar.id" class="text-green-500 text-sm">&#10003;</span>
          <span v-if="isUnderrepresented(pillar)" class="text-amber-400 text-xs" title="Unterrepräsentiert">&#9888;</span>
        </button>
      </div>
    </div>
  </div>
</template>
