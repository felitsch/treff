<script setup>
/**
 * PostPreviewGrid.vue — Grid Layout for Post Preview Cards
 *
 * Displays multiple PostPreviewCard (Instagram) and PostPreviewCardTikTok
 * components in a responsive grid layout. Supports filtering by platform
 * and sorting options.
 *
 * @see PostPreviewCard.vue — Instagram mockup card
 * @see PostPreviewCardTikTok.vue — TikTok mockup card
 */
import { computed, ref } from 'vue'
import PostPreviewCard from './PostPreviewCard.vue'
import PostPreviewCardTikTok from './PostPreviewCardTikTok.vue'

const props = defineProps({
  /** Array of post objects to display */
  posts: { type: Array, default: () => [] },
  /** Card size: 'sm' | 'md' | 'lg' */
  size: { type: String, default: 'md', validator: v => ['sm', 'md', 'lg'].includes(v) },
  /** Whether to show captions on cards */
  showCaption: { type: Boolean, default: true },
  /** Filter by platform: 'all' | 'instagram' | 'tiktok' */
  platformFilter: { type: String, default: 'all' },
  /** Maximum number of posts to display (0 = unlimited) */
  maxItems: { type: Number, default: 0 },
  /** Grid columns override (default auto-fit based on size) */
  columns: { type: Number, default: 0 },
  /** Empty state message */
  emptyMessage: { type: String, default: 'Keine Posts vorhanden' },
})

const emit = defineEmits(['post-click', 'slide-change'])

// Track slide indices per post
const slideIndices = ref({})

function getSlideIndex(postId) {
  return slideIndices.value[postId] || 0
}

function handleSlideChange(postId, idx) {
  slideIndices.value[postId] = idx
  emit('slide-change', { postId, slideIndex: idx })
}

// ── Filtered posts ──
const filteredPosts = computed(() => {
  let result = props.posts

  if (props.platformFilter !== 'all') {
    result = result.filter(p => {
      const platform = (p.platform || '').toLowerCase()
      if (props.platformFilter === 'instagram') {
        return platform.includes('instagram') || platform === 'instagram_feed' || platform === 'instagram_story'
      }
      if (props.platformFilter === 'tiktok') {
        return platform === 'tiktok'
      }
      return true
    })
  }

  if (props.maxItems > 0) {
    result = result.slice(0, props.maxItems)
  }

  return result
})

// ── Platform detection ──
function isTikTok(post) {
  return (post.platform || '').toLowerCase() === 'tiktok'
}

// ── Grid columns class ──
const gridClass = computed(() => {
  if (props.columns > 0) {
    const colMap = {
      1: 'grid-cols-1',
      2: 'grid-cols-1 sm:grid-cols-2',
      3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
      4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
      5: 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5',
    }
    return colMap[props.columns] || 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
  }

  // Auto based on size
  switch (props.size) {
    case 'sm': return 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6'
    case 'lg': return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
    default:   return 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4'
  }
})
</script>

<template>
  <div data-testid="post-preview-grid">
    <!-- Grid of cards -->
    <div
      v-if="filteredPosts.length > 0"
      class="grid gap-4 justify-items-center"
      :class="gridClass"
    >
      <template v-for="post in filteredPosts" :key="post.id || post.title">
        <!-- TikTok card -->
        <PostPreviewCardTikTok
          v-if="isTikTok(post)"
          :post="post"
          :size="size"
          :show-caption="showCaption"
          @click="emit('post-click', post)"
        />
        <!-- Instagram card (default) -->
        <PostPreviewCard
          v-else
          :post="post"
          :size="size"
          :show-caption="showCaption"
          :current-slide-index="getSlideIndex(post.id)"
          @click="emit('post-click', post)"
          @slide-change="(idx) => handleSlideChange(post.id, idx)"
        />
      </template>
    </div>

    <!-- Empty state -->
    <div
      v-else
      class="flex flex-col items-center justify-center py-12 text-center"
      data-testid="post-preview-grid-empty"
    >
      <div class="text-4xl mb-3 opacity-40">&#x1F4F7;</div>
      <p class="text-gray-500 dark:text-gray-400 text-sm">{{ emptyMessage }}</p>
    </div>
  </div>
</template>
