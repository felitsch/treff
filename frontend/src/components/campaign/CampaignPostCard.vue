<script setup>
/**
 * CampaignPostCard — Compact post card with thumbnail, date, pillar badge, status.
 *
 * Used within the CampaignTimeline to represent individual campaign posts.
 *
 * @see views/create/CampaignCreateView.vue — Parent view
 * @see components/campaign/CampaignTimeline.vue — Timeline container
 */
const props = defineProps({
  post: { type: Object, required: true },
})

defineEmits(['edit', 'remove'])

const countryEmojis = { usa: '🇺🇸', kanada: '🇨🇦', australien: '🇦🇺', neuseeland: '🇳🇿', irland: '🇮🇪' }

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', { weekday: 'short', day: '2-digit', month: 'short' })
}
</script>

<template>
  <div
    class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 hover:shadow-md transition-all cursor-pointer"
    @click="$emit('edit', post)"
    data-testid="campaign-post-card"
  >
    <div class="flex items-center justify-between mb-2">
      <span class="text-xs font-medium text-gray-900 dark:text-white">
        #{{ post.order }}
      </span>
      <span class="text-[10px] text-gray-400">{{ formatDate(post.scheduled_date) }}</span>
    </div>

    <div class="flex items-center gap-1.5 flex-wrap">
      <span class="text-[10px] font-medium px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300">
        {{ post.suggested_category_label || post.suggested_category }}
      </span>
      <span class="text-xs">{{ countryEmojis[post.suggested_country] || '🌍' }}</span>
    </div>

    <p class="text-[10px] text-gray-500 dark:text-gray-400 mt-1.5">
      {{ post.suggested_platform }}
    </p>
  </div>
</template>
