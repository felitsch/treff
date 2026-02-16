<template>
  <div class="space-y-2" :style="{ gap: gap }">
    <SkeletonBase
      v-for="(line, idx) in lineWidths"
      :key="idx"
      :width="line"
      :height="lineHeight"
      :rounded="rounded"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import SkeletonBase from './SkeletonBase.vue'

const props = defineProps({
  /** Number of text lines to show */
  lines: { type: Number, default: 3 },
  /** Height of each line */
  lineHeight: { type: String, default: '0.75rem' },
  /** Gap between lines */
  gap: { type: String, default: '0.5rem' },
  /** Border radius */
  rounded: { type: String, default: 'md' },
  /** Whether last line should be shorter (more natural look) */
  lastLineShort: { type: Boolean, default: true },
})

const lineWidths = computed(() => {
  const widths = []
  for (let i = 0; i < props.lines; i++) {
    if (i === props.lines - 1 && props.lastLineShort && props.lines > 1) {
      // Last line is shorter for natural text appearance
      widths.push('60%')
    } else if (i === 0) {
      widths.push('100%')
    } else {
      // Vary middle lines slightly
      const pct = 80 + Math.floor((i * 17) % 20)
      widths.push(`${pct}%`)
    }
  }
  return widths
})
</script>
