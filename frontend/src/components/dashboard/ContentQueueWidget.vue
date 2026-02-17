<script setup>
/**
 * ContentQueueWidget.vue — Shows the next 5 scheduled posts as mini preview cards
 * with countdown timers and quick-edit buttons.
 *
 * Part of Dashboard 6-Widget-Architektur (Feature #310).
 *
 * Props:
 *   posts (Array) — Scheduled post objects from dashboard-widgets API
 *
 * @see DashboardView.vue — Parent integration
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const props = defineProps({
  posts: {
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

// Platform icons
function platformIcon(platform) {
  switch (platform) {
    case 'instagram_feed': return '📸'
    case 'instagram_story': return '📱'
    case 'tiktok': return '🎵'
    default: return '📝'
  }
}

// Category color classes
function categoryColor(cat) {
  const colors = {
    laender_spotlight: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
    erfahrungsberichte: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
    infografiken: 'bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300',
    fristen_cta: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
    tipps_tricks: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
    faq: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300',
    foto_posts: 'bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300',
    reel_tiktok_thumbnails: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300',
    story_posts: 'bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300',
  }
  return colors[cat] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
}

// Countdown text (relative to now)
function countdown(scheduledDate, scheduledTime) {
  if (!scheduledDate) return ''

  const now = new Date()
  let target
  if (scheduledTime) {
    target = new Date(`${scheduledDate}T${scheduledTime}:00`)
  } else {
    target = new Date(`${scheduledDate}T09:00:00`)
  }

  const diff = target.getTime() - now.getTime()
  if (diff <= 0) return 'Jetzt faellig'

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 1) return `in ${days} Tagen`
  if (days === 1) return 'morgen'
  if (hours >= 1) return `in ${hours} Std.`
  return `in ${minutes} Min.`
}

// Format scheduled date/time nicely
function formatSchedule(scheduledDate, scheduledTime) {
  if (!scheduledDate) return ''
  const d = new Date(scheduledDate)
  const dateStr = d.toLocaleDateString('de-DE', { weekday: 'short', day: '2-digit', month: 'short' })
  if (scheduledTime) {
    return `${dateStr}, ${scheduledTime} Uhr`
  }
  return dateStr
}

function editPost(postId) {
  router.push(`/create/post/${postId}/edit`)
}
</script>

<template>
  <BaseCard padding="none" data-tour="dashboard-content-queue" data-testid="content-queue-widget">
    <template #header>
      <h2 class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
        <span>📋</span> Content Queue
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
          @click="router.push('/calendar')"
          class="text-xs text-[#4C8BC2] hover:text-blue-600 dark:hover:text-blue-400 font-medium"
        >
          Alle anzeigen &rarr;
        </button>
      </div>
    </template>

    <div class="p-4">
      <!-- Loading skeleton -->
      <div v-if="loading" class="space-y-3">
        <div v-for="i in 3" :key="'sk-'+i" class="flex items-center gap-3 animate-pulse">
          <div class="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-lg flex-shrink-0"></div>
          <div class="flex-1 space-y-1.5">
            <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            <div class="h-2.5 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
          </div>
          <div class="h-6 w-16 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
        </div>
      </div>

      <!-- Empty state -->
      <EmptyState
        v-else-if="posts.length === 0"
        svgIcon="calendar-days"
        title="Keine geplanten Posts"
        description="Plane deinen naechsten Post im Kalender oder erstelle einen neuen."
        actionLabel="Post erstellen"
        actionTo="/create/quick"
        :compact="true"
      />

      <!-- Content queue list -->
      <div v-else class="space-y-2">
        <div
          v-for="post in posts"
          :key="post.id"
          class="flex items-center gap-3 p-2.5 rounded-lg border border-gray-100 dark:border-gray-700 hover:border-[#4C8BC2]/40 dark:hover:border-[#4C8BC2]/40 hover:bg-blue-50/30 dark:hover:bg-blue-900/10 transition-all cursor-pointer group"
          @click="editPost(post.id)"
        >
          <!-- Thumbnail or platform icon -->
          <div class="w-10 h-10 rounded-lg overflow-hidden flex-shrink-0 bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
            <img
              v-if="post.thumbnail_url"
              :src="post.thumbnail_url"
              :alt="post.title"
              class="w-full h-full object-cover"
            />
            <span v-else class="text-lg">{{ platformIcon(post.platform) }}</span>
          </div>

          <!-- Post info -->
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 dark:text-white truncate leading-tight">
              {{ post.title }}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 flex items-center gap-1.5">
              <span>{{ formatSchedule(post.scheduled_date, post.scheduled_time) }}</span>
            </p>
          </div>

          <!-- Countdown badge -->
          <div class="flex items-center gap-1.5 flex-shrink-0">
            <span
              class="text-[10px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap"
              :class="categoryColor(post.category)"
            >
              {{ countdown(post.scheduled_date, post.scheduled_time) }}
            </span>
            <!-- Quick edit button -->
            <button
              @click.stop="editPost(post.id)"
              class="p-1 rounded text-gray-400 hover:text-[#4C8BC2] opacity-0 group-hover:opacity-100 transition-all"
              title="Bearbeiten"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </BaseCard>
</template>
