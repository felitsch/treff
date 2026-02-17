<script setup>
/**
 * CampaignTimeline — Horizontal/vertical timeline with date markers.
 *
 * Displays campaign posts along a timeline with visual date markers,
 * drag-and-drop reordering, and click-to-edit functionality.
 *
 * @see views/create/CampaignCreateView.vue — Parent view
 */
defineProps({
  posts: { type: Array, default: () => [] },
  startDate: { type: String, default: '' },
  endDate: { type: String, default: '' },
})

defineEmits(['edit', 'remove', 'reorder'])

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' })
}
</script>

<template>
  <div class="campaign-timeline" data-testid="campaign-timeline-component">
    <div class="flex items-center gap-2 mb-3 text-xs text-gray-400 dark:text-gray-500">
      <span>{{ formatDate(startDate) }}</span>
      <div class="flex-1 h-px bg-gray-200 dark:bg-gray-700"></div>
      <span>{{ formatDate(endDate) }}</span>
    </div>
    <div class="flex gap-2 overflow-x-auto pb-2">
      <div
        v-for="post in posts"
        :key="post.order"
        class="shrink-0 w-32 bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2 border border-gray-200 dark:border-gray-600 cursor-pointer hover:border-amber-300 transition-colors"
        @click="$emit('edit', post)"
      >
        <p class="text-[10px] font-medium text-gray-900 dark:text-white truncate">
          {{ post.suggested_category_label || 'Post' }}
        </p>
        <p class="text-[9px] text-gray-400">{{ formatDate(post.scheduled_date) }}</p>
      </div>
    </div>
  </div>
</template>
