<script setup>
/**
 * PipelineStatusBadge.vue — Compact status badge with count + color
 *
 * Shows a pipeline status as a pill badge with status-specific coloring.
 * Used inside PipelineDashboardWidget and PipelineItemCard.
 *
 * @see Feature #301 — P-01: Pipeline Dashboard Widget
 */
import { computed } from 'vue'

const props = defineProps({
  /** Pipeline status: 'pending' | 'analyzed' | 'processing' | 'processed' | 'failed' | 'drafted' | 'scheduled' */
  status: { type: String, required: true },
  /** Optional count to display alongside the label */
  count: { type: Number, default: null },
  /** Size variant: 'xs' | 'sm' | 'md' */
  size: { type: String, default: 'sm', validator: v => ['xs', 'sm', 'md'].includes(v) },
})

const statusConfig = {
  pending:    { label: 'Empfangen',   color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',   dotColor: 'bg-amber-500' },
  received:   { label: 'Empfangen',   color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',   dotColor: 'bg-amber-500' },
  analyzed:   { label: 'Analysiert',  color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',       dotColor: 'bg-blue-500' },
  processing: { label: 'Verarbeitet', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300', dotColor: 'bg-yellow-500' },
  suggested:  { label: 'Vorschlag',   color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300', dotColor: 'bg-purple-500' },
  drafted:    { label: 'Entwurf',     color: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300',       dotColor: 'bg-cyan-500' },
  processed:  { label: 'Entwurf',     color: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300',       dotColor: 'bg-cyan-500' },
  scheduled:  { label: 'Geplant',     color: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',   dotColor: 'bg-green-500' },
  failed:     { label: 'Fehler',      color: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',           dotColor: 'bg-red-500' },
}

const config = computed(() => statusConfig[props.status] || statusConfig.pending)

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'xs': return 'text-[9px] px-1.5 py-0.5'
    case 'md': return 'text-xs px-2.5 py-1'
    default: return 'text-[10px] px-2 py-0.5'
  }
})
</script>

<template>
  <span
    class="inline-flex items-center gap-1 rounded-full font-semibold"
    :class="[config.color, sizeClasses]"
    :data-testid="`pipeline-status-badge-${status}`"
  >
    <span class="w-1.5 h-1.5 rounded-full flex-shrink-0" :class="config.dotColor"></span>
    {{ config.label }}
    <span v-if="count !== null" class="font-bold">{{ count }}</span>
  </span>
</template>
