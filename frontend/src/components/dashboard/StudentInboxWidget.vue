<script setup>
/**
 * StudentInboxWidget.vue — Shows new student content with thumbnails and
 * quick-action buttons ('Post erstellen', 'Spaeter').
 *
 * Part of Dashboard 6-Widget-Architektur (Feature #310).
 *
 * Props:
 *   items (Array) — Student inbox items from dashboard-widgets API
 *   total (Number) — Total pending inbox items count
 *
 * @see DashboardView.vue — Parent integration
 */
import { useRouter } from 'vue-router'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { parseDate } from '@/utils/dateUtils'

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  total: {
    type: Number,
    default: 0,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['refresh'])
const router = useRouter()

// Country emoji flags
function countryFlag(country) {
  const flags = {
    usa: '\u{1F1FA}\u{1F1F8}',
    kanada: '\u{1F1E8}\u{1F1E6}',
    australien: '\u{1F1E6}\u{1F1FA}',
    neuseeland: '\u{1F1F3}\u{1F1FF}',
    irland: '\u{1F1EE}\u{1F1EA}',
  }
  return flags[(country || '').toLowerCase()] || '\u{1F30D}'
}

// Status badges
function statusBadge(status) {
  switch (status) {
    case 'pending': return { label: 'Neu', class: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300' }
    case 'analyzed': return { label: 'Analysiert', class: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' }
    default: return { label: status, class: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300' }
  }
}

// Time ago formatting
function timeAgo(dateStr) {
  if (!dateStr) return ''
  const date = parseDate(dateStr)
  if (!date) return ''
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `vor ${days} Tag${days > 1 ? 'en' : ''}`
  if (hours > 0) return `vor ${hours} Std.`
  if (minutes > 0) return `vor ${minutes} Min.`
  return 'gerade eben'
}

function createPost(item) {
  router.push({
    path: '/create/quick',
    query: {
      country: item.detected_country || item.student_country || '',
      source: 'student-inbox',
      pipeline_id: item.id,
    },
  })
}

function viewInbox() {
  router.push('/students')
}
</script>

<template>
  <BaseCard padding="none" data-tour="dashboard-student-inbox" data-testid="student-inbox-widget">
    <template #header>
      <h2 class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
        <AppIcon name="inbox" class="w-5 h-5" /> Student Inbox
        <span
          v-if="total > 0"
          class="ml-1 text-[10px] font-bold bg-[#FDD000] text-gray-900 px-1.5 py-0.5 rounded-full"
        >
          {{ total }}
        </span>
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
          @click="viewInbox"
          class="text-xs text-[#4C8BC2] hover:text-blue-600 dark:hover:text-blue-400 font-medium"
        >
          Alle anzeigen &rarr;
        </button>
      </div>
    </template>

    <div class="p-4">
      <!-- Loading skeleton -->
      <div v-if="loading" class="space-y-3">
        <div v-for="i in 3" :key="'sk-'+i" class="flex items-start gap-3 animate-pulse">
          <div class="w-9 h-9 bg-gray-200 dark:bg-gray-700 rounded-full flex-shrink-0"></div>
          <div class="flex-1 space-y-1.5">
            <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            <div class="h-2.5 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <EmptyState
        v-else-if="items.length === 0"
        svgIcon="academic-cap"
        title="Keine neuen Inhalte"
        description="Wenn Schüler neue Fotos oder Videos teilen, erscheinen sie hier."
        :compact="true"
      />

      <!-- Inbox items list -->
      <div v-else class="space-y-2">
        <div
          v-for="item in items"
          :key="item.id"
          class="p-2.5 rounded-lg border border-gray-100 dark:border-gray-700 hover:border-[#4C8BC2]/40 dark:hover:border-[#4C8BC2]/40 transition-all"
        >
          <!-- Header row: avatar + name + badge -->
          <div class="flex items-center gap-2 mb-1.5">
            <div class="w-7 h-7 rounded-full bg-gradient-to-br from-[#4C8BC2] to-[#3B7AB1] flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
              {{ (item.student_name || 'U').charAt(0).toUpperCase() }}
            </div>
            <div class="flex-1 min-w-0">
              <span class="text-sm font-medium text-gray-900 dark:text-white truncate">
                {{ item.student_name }}
              </span>
              <span class="text-xs text-gray-400 dark:text-gray-500 ml-1.5">
                {{ countryFlag(item.student_country || item.detected_country) }}
              </span>
            </div>
            <span
              class="text-[10px] font-semibold px-1.5 py-0.5 rounded-full flex-shrink-0"
              :class="statusBadge(item.status).class"
            >
              {{ statusBadge(item.status).label }}
            </span>
          </div>

          <!-- Description / summary -->
          <p class="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 mb-2 pl-9">
            {{ item.analysis_summary || item.source_description || 'Neuer Inhalt empfangen' }}
          </p>

          <!-- Actions row -->
          <div class="flex items-center justify-between pl-9">
            <span class="text-[10px] text-gray-400 dark:text-gray-500">{{ timeAgo(item.created_at) }}</span>
            <div class="flex items-center gap-1.5">
              <button
                @click="createPost(item)"
                class="text-[10px] font-semibold text-white bg-[#4C8BC2] hover:bg-[#3B7AB1] px-2 py-0.5 rounded transition-colors"
              >
                Post erstellen
              </button>
              <button
                class="text-[10px] font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 px-2 py-0.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                Spaeter
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </BaseCard>
</template>
