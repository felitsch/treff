<script setup>
/**
 * ActiveCampaignsWidget.vue — Shows active/draft campaigns with progress bars
 * (e.g., "3/8 Posts fertig") and status badges.
 *
 * Part of Dashboard 6-Widget-Architektur (Feature #310).
 *
 * Props:
 *   campaigns (Array) — Campaign objects from dashboard-widgets API
 *
 * @see DashboardView.vue — Parent integration
 */
import { useRouter } from 'vue-router'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const props = defineProps({
  campaigns: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['refresh'])
const router = useRouter()

// Status badge styling
function statusBadge(status) {
  switch (status) {
    case 'active': return { label: 'Aktiv', class: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' }
    case 'draft': return { label: 'Entwurf', class: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300' }
    case 'completed': return { label: 'Fertig', class: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300' }
    default: return { label: status, class: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300' }
  }
}

// Goal icon
function goalIcon(goal) {
  switch (goal) {
    case 'awareness': return '👀'
    case 'engagement': return '💬'
    case 'conversion': return '🎯'
    case 'traffic': return '🔗'
    default: return '📊'
  }
}

// Progress percentage
function progressPercent(campaign) {
  if (!campaign.total_posts || campaign.total_posts === 0) return 0
  return Math.round((campaign.completed_posts / campaign.total_posts) * 100)
}

// Progress bar color
function progressColor(percent) {
  if (percent >= 80) return 'bg-green-500'
  if (percent >= 50) return 'bg-[#4C8BC2]'
  if (percent >= 25) return 'bg-[#FDD000]'
  return 'bg-gray-300 dark:bg-gray-600'
}

// Format date range
function dateRange(start, end) {
  if (!start && !end) return ''
  const fmt = (d) => {
    if (!d) return '?'
    const date = new Date(d)
    return date.toLocaleDateString('de-DE', { day: '2-digit', month: 'short' })
  }
  return `${fmt(start)} - ${fmt(end)}`
}

function viewCampaign(id) {
  router.push(`/calendar/week-planner?campaign=${id}`)
}
</script>

<template>
  <BaseCard padding="none" data-tour="dashboard-active-campaigns" data-testid="active-campaigns-widget">
    <template #header>
      <h2 class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
        <span>🎯</span> Aktive Kampagnen
      </h2>
    </template>
    <template #headerAction>
      <div class="flex items-center gap-2">
        <button
          @click="emit('refresh')"
          class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          title="Aktualisieren"
          :disabled="loading"
        >
          <svg class="w-4 h-4" :class="{ 'animate-spin': loading }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
        <button
          @click="router.push('/calendar/week-planner')"
          class="text-xs text-[#4C8BC2] hover:text-blue-600 dark:hover:text-blue-400 font-medium"
        >
          Alle anzeigen &rarr;
        </button>
      </div>
    </template>

    <div class="p-4">
      <!-- Loading skeleton -->
      <div v-if="loading" class="space-y-4 animate-pulse">
        <div v-for="i in 2" :key="'sk-'+i" class="space-y-2">
          <div class="flex justify-between">
            <div class="h-3.5 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded-full w-12"></div>
          </div>
          <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full w-full"></div>
          <div class="h-2.5 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
        </div>
      </div>

      <!-- Empty state -->
      <EmptyState
        v-else-if="campaigns.length === 0"
        svgIcon="sparkles"
        title="Keine aktiven Kampagnen"
        description="Erstelle eine Kampagne, um mehrere Posts zu einem Thema zu planen."
        actionLabel="Kampagne erstellen"
        actionTo="/calendar/week-planner"
        :compact="true"
      />

      <!-- Campaign cards -->
      <div v-else class="space-y-3">
        <div
          v-for="campaign in campaigns"
          :key="campaign.id"
          class="p-3 rounded-lg border border-gray-100 dark:border-gray-700 hover:border-[#4C8BC2]/40 dark:hover:border-[#4C8BC2]/40 hover:bg-blue-50/30 dark:hover:bg-blue-900/10 transition-all cursor-pointer"
          @click="viewCampaign(campaign.id)"
        >
          <!-- Title row -->
          <div class="flex items-start justify-between gap-2 mb-2">
            <div class="flex items-center gap-1.5 min-w-0">
              <span class="text-sm flex-shrink-0">{{ goalIcon(campaign.goal) }}</span>
              <h3 class="text-sm font-semibold text-gray-900 dark:text-white truncate">
                {{ campaign.title }}
              </h3>
            </div>
            <span
              class="text-[10px] font-semibold px-1.5 py-0.5 rounded-full flex-shrink-0"
              :class="statusBadge(campaign.status).class"
            >
              {{ statusBadge(campaign.status).label }}
            </span>
          </div>

          <!-- Progress bar -->
          <div class="mb-2">
            <div class="flex items-center justify-between mb-1">
              <span class="text-[10px] font-medium text-gray-500 dark:text-gray-400">
                {{ campaign.completed_posts }}/{{ campaign.total_posts }} Posts fertig
              </span>
              <span class="text-[10px] font-bold text-gray-600 dark:text-gray-300 tabular-nums">
                {{ progressPercent(campaign) }}%
              </span>
            </div>
            <div class="w-full h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="progressColor(progressPercent(campaign))"
                :style="{ width: `${progressPercent(campaign)}%` }"
              ></div>
            </div>
          </div>

          <!-- Meta row -->
          <div class="flex items-center justify-between text-[10px] text-gray-400 dark:text-gray-500">
            <span v-if="campaign.start_date || campaign.end_date">
              {{ dateRange(campaign.start_date, campaign.end_date) }}
            </span>
            <span v-else>Kein Zeitraum</span>
            <div v-if="campaign.platforms && campaign.platforms.length > 0" class="flex items-center gap-1">
              <span
                v-for="platform in campaign.platforms.slice(0, 3)"
                :key="platform"
                class="bg-gray-100 dark:bg-gray-700 px-1 py-0.5 rounded text-[9px]"
              >
                {{ platform === 'instagram_feed' ? 'IG' : platform === 'tiktok' ? 'TT' : platform === 'instagram_story' ? 'Story' : platform }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </BaseCard>
</template>
