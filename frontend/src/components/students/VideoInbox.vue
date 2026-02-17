<script setup>
/**
 * VideoInbox — Student Video/Media Inbox component.
 *
 * Shows unprocessed student uploads with AI analysis suggestions.
 * Can be used standalone (full page) or as a compact widget (dashboard).
 *
 * Props:
 *   - compact: boolean — Widget mode (fewer columns, limited items)
 *   - maxItems: number — Max items to show in compact mode
 *   - studentId: number|null — Filter to specific student
 *
 * @see Feature #300: V-05: Student Video Inbox
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { getCountryTheme } from '@/composables/useCountryTheme'
import api from '@/utils/api'
import AppIcon from '@/components/icons/AppIcon.vue'

const props = defineProps({
  compact: {
    type: Boolean,
    default: false,
  },
  maxItems: {
    type: Number,
    default: 5,
  },
  studentId: {
    type: [Number, String],
    default: null,
  },
})

const emit = defineEmits(['item-processed', 'item-deferred', 'count-changed'])

const router = useRouter()
const toast = useToast()

// ── State ──
const items = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const selectedItems = ref(new Set())
const filterStudent = ref(props.studentId || '')
const filterStatus = ref('')
const processingIds = ref(new Set())

// ── Status config ──
const statusConfig = {
  pending: { label: 'Neu', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400', icon: 'sparkles' },
  analyzed: { label: 'Analysiert', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400', icon: 'search' },
  processing: { label: 'Verarbeitung...', color: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400', icon: 'clock' },
  processed: { label: 'Verarbeitet', color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400', icon: 'check-circle' },
  deferred: { label: 'Zurückgestellt', color: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400', icon: 'pause' },
  failed: { label: 'Fehler', color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400', icon: 'x-circle' },
}

const postTypeLabels = {
  instagram_feed: 'Instagram Feed',
  instagram_story: 'Instagram Story',
  instagram_reel: 'Reel',
  tiktok: 'TikTok',
  carousel: 'Karussell',
}

// ── Computed ──
const displayItems = computed(() => {
  if (props.compact) return items.value.slice(0, props.maxItems)
  return items.value
})

const hasMore = computed(() => {
  if (props.compact) return total.value > props.maxItems
  return items.value.length < total.value
})

const newCount = computed(() => {
  return items.value.filter(i => i.status === 'pending' || i.status === 'analyzed').length
})

const allSelected = computed(() => {
  return displayItems.value.length > 0 && displayItems.value.every(i => selectedItems.value.has(i.id))
})

// ── Data Loading ──
async function loadInbox() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      limit: props.compact ? props.maxItems : 20,
    }
    if (filterStudent.value) params.student_id = filterStudent.value
    if (filterStatus.value) params.status = filterStatus.value

    const { data } = await api.get('/api/pipeline/inbox', { params })
    items.value = data.items || []
    total.value = data.total || 0
    emit('count-changed', total.value)
  } catch (err) {
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// ── Actions ──
async function processItem(item) {
  processingIds.value.add(item.id)
  try {
    await api.post('/api/pipeline/process', { inbox_item_id: item.id })
    toast.success(`"${item.asset_filename || 'Video'}" verarbeitet.`)
    emit('item-processed', item)
    await loadInbox()
  } catch (err) {
    toast.error('Verarbeitung fehlgeschlagen.')
  } finally {
    processingIds.value.delete(item.id)
  }
}

function openInCreator(item) {
  const query = {}
  if (item.student_id) query.student_id = item.student_id
  if (item.id) query.pipeline_item_id = item.id
  router.push({ path: '/create/smart', query })
}

function openVideoCreator(item) {
  const query = {}
  if (item.student_id) query.student_id = item.student_id
  if (item.asset_id) query.asset_id = item.asset_id
  if (item.id) query.pipeline_item_id = item.id
  router.push({ path: '/video/create', query })
}

async function deferItem(item) {
  // Mark as deferred by updating status (we simulate via process with override)
  try {
    await api.put(`/api/pipeline/inbox/${item.id}`, { status: 'deferred' })
    toast.info('Video zurückgestellt.')
    emit('item-deferred', item)
    await loadInbox()
  } catch {
    // Fallback: just remove from list visually
    items.value = items.value.filter(i => i.id !== item.id)
    toast.info('Video zurückgestellt.')
  }
}

// ── Batch Actions ──
function toggleSelectAll() {
  if (allSelected.value) {
    selectedItems.value.clear()
  } else {
    displayItems.value.forEach(i => selectedItems.value.add(i.id))
  }
}

function toggleSelect(id) {
  if (selectedItems.value.has(id)) {
    selectedItems.value.delete(id)
  } else {
    selectedItems.value.add(id)
  }
}

async function batchProcess() {
  const ids = [...selectedItems.value]
  if (ids.length === 0) return
  for (const id of ids) {
    processingIds.value.add(id)
  }
  try {
    for (const id of ids) {
      await api.post('/api/pipeline/process', { inbox_item_id: id })
    }
    toast.success(`${ids.length} Items verarbeitet.`)
    selectedItems.value.clear()
    await loadInbox()
  } catch {
    toast.error('Batch-Verarbeitung teilweise fehlgeschlagen.')
  } finally {
    ids.forEach(id => processingIds.value.delete(id))
  }
}

// ── Helpers ──
function getItemTheme(item) {
  return getCountryTheme(item.detected_country || '')
}

function formatDate(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
  } catch { return iso }
}

function getFileIcon(fileType) {
  if (!fileType) return 'link'
  if (fileType.startsWith('video')) return 'film'
  if (fileType.startsWith('image')) return 'photo'
  return 'link'
}

// ── Watchers ──
watch(() => props.studentId, (val) => {
  filterStudent.value = val || ''
  loadInbox()
})

onMounted(loadInbox)
</script>

<template>
  <div
    :class="compact ? '' : 'bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm'"
    data-testid="video-inbox"
  >
    <!-- Header (full mode only) -->
    <div v-if="!compact" class="p-5 pb-0">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">Video & Media Inbox</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            {{ total }} {{ total === 1 ? 'Item' : 'Items' }}
            <span v-if="newCount > 0" class="text-secondary-600 dark:text-secondary-400 font-medium"> &middot; {{ newCount }} neu</span>
          </p>
        </div>
        <!-- Batch actions -->
        <div v-if="selectedItems.size > 0" class="flex items-center gap-2">
          <span class="text-xs text-gray-500">{{ selectedItems.size }} ausgewählt</span>
          <button class="btn-primary btn-sm" @click="batchProcess" data-testid="batch-process">
            Alle verarbeiten
          </button>
        </div>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap gap-2 mb-4">
        <select
          v-model="filterStatus"
          class="input-field w-auto text-sm"
          @change="loadInbox"
          data-testid="inbox-filter-status"
        >
          <option value="">Alle Status</option>
          <option value="pending">Neu</option>
          <option value="analyzed">Analysiert</option>
          <option value="processed">Verarbeitet</option>
        </select>
      </div>
    </div>

    <!-- Compact header -->
    <div v-if="compact" class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <span class="text-sm font-semibold text-gray-900 dark:text-white">Video Inbox</span>
        <span v-if="newCount > 0" class="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-secondary-100 text-secondary-800 dark:bg-secondary-900/30 dark:text-secondary-400">
          {{ newCount }} neu
        </span>
      </div>
      <button
        v-if="total > 0"
        class="text-xs text-primary-600 dark:text-primary-400 hover:underline"
        @click="router.push('/students')"
      >
        Alle anzeigen
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" :class="compact ? 'py-4' : 'p-5'" class="text-center text-gray-500">
      <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500 mx-auto"></div>
      <p class="mt-1.5 text-xs">Lade Inbox...</p>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="displayItems.length === 0"
      :class="compact ? 'py-6 text-center' : 'p-8 text-center'"
      data-testid="inbox-empty"
    >
      <AppIcon name="inbox" class="w-8 h-8 text-gray-400 mx-auto mb-2" />
      <p class="text-sm text-gray-500 dark:text-gray-400">Keine neuen Videos in der Inbox</p>
      <p v-if="!compact" class="text-xs text-gray-400 dark:text-gray-500 mt-1">
        Lade Schüler-Content über die Pipeline hoch, um ihn hier zu verarbeiten.
      </p>
    </div>

    <!-- Items List -->
    <div v-else :class="compact ? '' : 'p-5 pt-0'">
      <!-- Select All (full mode) -->
      <div v-if="!compact && displayItems.length > 1" class="flex items-center gap-2 mb-3">
        <input
          type="checkbox"
          :checked="allSelected"
          @change="toggleSelectAll"
          class="rounded border-gray-300 dark:border-gray-600 text-primary-500 focus:ring-primary-500"
        />
        <span class="text-xs text-gray-500 dark:text-gray-400">Alle auswählen</span>
      </div>

      <div :class="compact ? 'space-y-2' : 'space-y-3'">
        <div
          v-for="item in displayItems"
          :key="item.id"
          class="flex items-start gap-3 p-3 rounded-lg border transition-all duration-200"
          :class="[
            selectedItems.has(item.id) ? 'border-primary-300 bg-primary-50/50 dark:border-primary-600 dark:bg-primary-900/10' : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600',
            processingIds.has(item.id) ? 'opacity-60' : '',
          ]"
          :data-testid="'inbox-item-' + item.id"
        >
          <!-- Checkbox (full mode) -->
          <input
            v-if="!compact"
            type="checkbox"
            :checked="selectedItems.has(item.id)"
            @change="toggleSelect(item.id)"
            class="mt-1 rounded border-gray-300 dark:border-gray-600 text-primary-500 focus:ring-primary-500"
          />

          <!-- Thumbnail / Icon -->
          <div
            class="w-12 h-12 rounded-lg flex items-center justify-center text-lg flex-shrink-0 overflow-hidden"
            :style="{ backgroundColor: getItemTheme(item).primaryColor + '15' }"
          >
            <img
              v-if="item.asset_thumbnail_path"
              :src="'/uploads/' + item.asset_thumbnail_path"
              :alt="item.asset_filename"
              class="w-full h-full object-cover"
            />
            <AppIcon v-else :name="getFileIcon(item.asset_file_type)" class="w-5 h-5" />
          </div>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-0.5">
              <span class="text-sm font-medium text-gray-900 dark:text-white truncate">
                {{ item.asset_filename || 'Unbenanntes Medium' }}
              </span>
              <span
                :class="['text-[10px] font-medium px-1.5 py-0.5 rounded-full flex-shrink-0', statusConfig[item.status]?.color || 'bg-gray-100 text-gray-600']"
              >
                {{ statusConfig[item.status]?.label || item.status }}
              </span>
            </div>

            <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
              <span v-if="item.student_name">{{ item.student_name }}</span>
              <span v-if="item.detected_country" class="flex items-center gap-0.5">
                <span class="w-1.5 h-1.5 rounded-full" :style="{ backgroundColor: getItemTheme(item).primaryColor }"></span>
                {{ getItemTheme(item).label }}
              </span>
              <span v-if="item.created_at">{{ formatDate(item.created_at) }}</span>
            </div>

            <!-- AI Suggestions -->
            <div v-if="item.suggested_post_type || item.analysis_summary" class="mt-1.5">
              <div v-if="item.suggested_post_type" class="flex items-center gap-1.5 text-[10px]">
                <span class="px-1.5 py-0.5 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 rounded font-medium">
                  {{ postTypeLabels[item.suggested_post_type] || item.suggested_post_type }}
                </span>
                <span v-if="item.suggested_platforms && item.suggested_platforms.length > 0" class="text-gray-400">
                  {{ item.suggested_platforms.join(', ') }}
                </span>
              </div>
              <p v-if="item.analysis_summary && !compact" class="text-[10px] text-gray-500 dark:text-gray-500 mt-0.5 line-clamp-1">
                {{ item.analysis_summary }}
              </p>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-1 flex-shrink-0" v-if="!processingIds.has(item.id)">
            <button
              v-if="item.status !== 'processed' && !compact"
              class="text-[10px] font-medium px-2 py-1 rounded-md bg-primary-500 text-white hover:bg-primary-600 transition-colors"
              @click.stop="openVideoCreator(item)"
              data-testid="btn-brand-post"
              title="Brand & Post"
            >
              Brand & Post
            </button>
            <button
              class="text-[10px] font-medium px-2 py-1 rounded-md text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              @click.stop="openInCreator(item)"
              data-testid="btn-to-creator"
              title="Zum Creator"
            >
              Creator
            </button>
            <button
              v-if="item.status !== 'processed' && !compact"
              class="text-[10px] font-medium px-2 py-1 rounded-md text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              @click.stop="deferItem(item)"
              title="Später"
            >
              Später
            </button>
          </div>

          <!-- Processing spinner -->
          <div v-if="processingIds.has(item.id)" class="flex-shrink-0">
            <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-500"></div>
          </div>
        </div>
      </div>

      <!-- Load More / View All -->
      <div v-if="hasMore" class="mt-3 text-center">
        <button
          v-if="compact"
          class="text-xs text-primary-600 dark:text-primary-400 hover:underline"
          @click="router.push('/students')"
        >
          Alle {{ total }} Items anzeigen
        </button>
        <button
          v-else
          class="btn-ghost btn-sm"
          @click="page++; loadInbox()"
        >
          Mehr laden
        </button>
      </div>
    </div>
  </div>
</template>
