<script setup>
/**
 * PipelineItemCard.vue — Card for a single pipeline inbox item
 *
 * Shows thumbnail, status badge, student name, detected country,
 * suggested action, and quick-action buttons.
 *
 * @see Feature #301 — P-01: Pipeline Dashboard Widget
 * @see stores/contentPipeline.js — Pipeline Pinia store
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import PipelineStatusBadge from './PipelineStatusBadge.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const props = defineProps({
  /** Pipeline inbox item object */
  item: { type: Object, required: true },
  /** Compact mode for dashboard widget (smaller layout) */
  compact: { type: Boolean, default: false },
})

const emit = defineEmits(['process', 'review', 'dismiss'])
const router = useRouter()

const countryFlags = {
  usa: '\u{1F1FA}\u{1F1F8}',
  kanada: '\u{1F1E8}\u{1F1E6}',
  canada: '\u{1F1E8}\u{1F1E6}',
  australien: '\u{1F1E6}\u{1F1FA}',
  australia: '\u{1F1E6}\u{1F1FA}',
  neuseeland: '\u{1F1F3}\u{1F1FF}',
  nz: '\u{1F1F3}\u{1F1FF}',
  irland: '\u{1F1EE}\u{1F1EA}',
  ireland: '\u{1F1EE}\u{1F1EA}',
}

const country = computed(() => {
  const c = (props.item.detected_country || props.item.student_country || '').toLowerCase()
  return {
    flag: countryFlags[c] || '\u{1F30D}',
    name: props.item.detected_country || props.item.student_country || '',
  }
})

const thumbnail = computed(() => {
  return props.item.asset_thumbnail_path || props.item.thumbnail || ''
})

const fileType = computed(() => {
  const ft = (props.item.asset_file_type || '').toLowerCase()
  if (ft.includes('video') || ft.includes('mp4') || ft.includes('mov')) return 'video'
  return 'image'
})

const suggestedAction = computed(() => {
  const s = props.item.status
  if (s === 'pending') return { label: 'Analysieren', icon: 'sparkles', action: 'review' }
  if (s === 'analyzed') return { label: 'Post erstellen', icon: 'plus', action: 'process' }
  if (s === 'processed') return { label: 'Bearbeiten', icon: 'pencil', action: 'edit' }
  return null
})

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const now = new Date()
  const date = new Date(dateStr)
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  if (days > 0) return `vor ${days}d`
  if (hours > 0) return `vor ${hours}h`
  if (minutes > 0) return `vor ${minutes}m`
  return 'gerade'
}

function handleAction() {
  const action = suggestedAction.value?.action
  if (action === 'process') {
    emit('process', props.item)
  } else if (action === 'review') {
    emit('review', props.item)
  } else if (action === 'edit' && props.item.result_post_id) {
    router.push(`/create/post/${props.item.result_post_id}/edit`)
  }
}
</script>

<template>
  <div
    class="flex items-start gap-2.5 p-2.5 rounded-lg border border-gray-100 dark:border-gray-700 hover:border-[#4C8BC2]/40 dark:hover:border-[#4C8BC2]/40 transition-all group"
    :class="compact ? '' : 'p-3'"
    :data-testid="`pipeline-item-card-${item.id}`"
  >
    <!-- Thumbnail -->
    <div
      class="relative flex-shrink-0 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700"
      :class="compact ? 'w-10 h-10' : 'w-14 h-14'"
    >
      <img
        v-if="thumbnail"
        :src="thumbnail"
        :alt="item.student_name || 'Pipeline item'"
        class="w-full h-full object-cover"
        loading="lazy"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-gray-400 dark:text-gray-500">
        <AppIcon :name="fileType === 'video' ? 'video-camera' : 'photo'" class="w-5 h-5" />
      </div>
      <!-- Video indicator -->
      <div
        v-if="fileType === 'video'"
        class="absolute bottom-0.5 right-0.5 w-3.5 h-3.5 rounded-full bg-black/60 flex items-center justify-center"
      >
        <svg class="w-2 h-2 text-white ml-px" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 min-w-0">
      <!-- Top row: student name + status badge -->
      <div class="flex items-center gap-1.5 mb-0.5">
        <span class="text-xs font-medium text-gray-900 dark:text-white truncate">
          {{ item.student_name || 'Unbekannt' }}
        </span>
        <span class="text-xs flex-shrink-0">{{ country.flag }}</span>
        <PipelineStatusBadge :status="item.status" size="xs" class="ml-auto flex-shrink-0" />
      </div>

      <!-- Summary / suggestion -->
      <p
        class="text-[10px] text-gray-500 dark:text-gray-400 line-clamp-1 mb-1"
      >
        {{ item.analysis_summary || item.suggested_post_type || item.asset_filename || 'Neuer Inhalt' }}
      </p>

      <!-- Bottom row: time + action button -->
      <div class="flex items-center justify-between">
        <span class="text-[9px] text-gray-400 dark:text-gray-500">{{ timeAgo(item.created_at) }}</span>
        <button
          v-if="suggestedAction"
          @click.stop="handleAction"
          class="text-[10px] font-semibold px-2 py-0.5 rounded transition-colors"
          :class="suggestedAction.action === 'process'
            ? 'text-white bg-[#4C8BC2] hover:bg-[#3B7AB1]'
            : 'text-[#4C8BC2] hover:bg-[#4C8BC2]/10'"
        >
          {{ suggestedAction.label }}
        </button>
      </div>
    </div>
  </div>
</template>
