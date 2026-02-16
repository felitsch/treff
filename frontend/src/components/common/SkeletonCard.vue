<template>
  <div
    :class="[
      'bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden',
      border ? 'border border-gray-200 dark:border-gray-700' : '',
    ]"
  >
    <!-- Image area (optional) -->
    <SkeletonImage
      v-if="showImage"
      :aspect="imageAspect"
      rounded="none"
      width="100%"
    />

    <!-- Content area -->
    <div :class="['space-y-3', padding]">
      <!-- Title line -->
      <SkeletonBase
        v-if="showTitle"
        :width="titleWidth"
        height="1rem"
        rounded="md"
      />

      <!-- Subtitle / description lines -->
      <SkeletonText
        v-if="textLines > 0"
        :lines="textLines"
        :line-height="textLineHeight"
      />

      <!-- Action bar (badges, buttons) -->
      <div v-if="showActions" class="flex items-center gap-2 pt-1">
        <SkeletonBase width="4rem" height="1.5rem" rounded="full" />
        <SkeletonBase width="3rem" height="1.5rem" rounded="full" />
      </div>
    </div>
  </div>
</template>

<script setup>
import SkeletonBase from './SkeletonBase.vue'
import SkeletonText from './SkeletonText.vue'
import SkeletonImage from './SkeletonImage.vue'

defineProps({
  /** Show image placeholder at top */
  showImage: { type: Boolean, default: true },
  /** Image aspect ratio */
  imageAspect: { type: String, default: 'square' },
  /** Show title line */
  showTitle: { type: Boolean, default: true },
  /** Title width */
  titleWidth: { type: String, default: '75%' },
  /** Number of body text lines (0 to hide) */
  textLines: { type: Number, default: 2 },
  /** Text line height */
  textLineHeight: { type: String, default: '0.625rem' },
  /** Show action bar with badge placeholders */
  showActions: { type: Boolean, default: false },
  /** Show border */
  border: { type: Boolean, default: false },
  /** Padding class for content area */
  padding: { type: String, default: 'p-4' },
})
</script>
