<template>
  <div :class="gridClass">
    <SkeletonCard
      v-for="i in count"
      :key="i"
      :show-image="showImage"
      :image-aspect="imageAspect"
      :show-title="showTitle"
      :title-width="getTitleWidth(i)"
      :text-lines="textLines"
      :text-line-height="textLineHeight"
      :show-actions="showActions"
      :border="border"
      :padding="padding"
    />
  </div>
</template>

<script setup>
import SkeletonCard from './SkeletonCard.vue'

const props = defineProps({
  /** Number of skeleton cards to show */
  count: { type: Number, default: 8 },
  /** Grid columns class (responsive Tailwind grid) */
  gridClass: {
    type: String,
    default: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4',
  },
  /** Show image in cards */
  showImage: { type: Boolean, default: true },
  /** Image aspect ratio */
  imageAspect: { type: String, default: 'square' },
  /** Show title in cards */
  showTitle: { type: Boolean, default: true },
  /** Number of body text lines */
  textLines: { type: Number, default: 2 },
  /** Text line height */
  textLineHeight: { type: String, default: '0.625rem' },
  /** Show action bar in cards */
  showActions: { type: Boolean, default: false },
  /** Show card border */
  border: { type: Boolean, default: false },
  /** Padding for content area */
  padding: { type: String, default: 'p-4' },
})

/** Vary title widths slightly for natural look */
function getTitleWidth(index) {
  const widths = ['75%', '60%', '85%', '70%', '80%', '65%', '90%', '55%']
  return widths[(index - 1) % widths.length]
}
</script>
