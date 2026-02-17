<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import AppIcon from '@/components/icons/AppIcon.vue'

const props = defineProps({
  postId: { type: [Number, String], default: null },
  storyArcId: { type: [Number, String], default: null },
  platform: { type: String, default: '' },
  country: { type: String, default: '' },
  category: { type: String, default: '' },
})

const emit = defineEmits(['update:relatedCount'])

const toast = useToast()
const loading = ref(false)
const loadingSuggestions = ref(false)
const relations = ref([])
const suggestions = ref([])
const showPanel = ref(false)
const showSearchMode = ref(false)
const searchQuery = ref('')
const searchResults = ref([])
const searchLoading = ref(false)

// Relation type labels
const typeLabels = {
  story_teaser: { label: 'Story-Teaser', icon: 'device-mobile', color: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300' },
  cross_reference: { label: 'Verweis', icon: 'link', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' },
  sequel: { label: 'Fortsetzung', icon: 'book-open', color: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300' },
  related: { label: 'Verwandt', icon: 'arrow-path', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' },
}

const platformIcons = {
  instagram_feed: 'camera',
  instagram_story: 'device-mobile',
  tiktok: 'musical-note',
}

const platformLabels = {
  instagram_feed: 'IG Feed',
  instagram_story: 'IG Story',
  tiktok: 'TikTok',
}

async function loadRelations() {
  if (!props.postId) return
  loading.value = true
  try {
    const res = await api.get(`/api/posts/${props.postId}/relations`)
    relations.value = res.data.relations || []
    emit('update:relatedCount', relations.value.length)
  } catch (err) {
    console.error('Failed to load relations:', err)
  } finally {
    loading.value = false
  }
}

async function loadSuggestions() {
  if (!props.postId) return
  loadingSuggestions.value = true
  try {
    const res = await api.post(`/api/posts/${props.postId}/suggest-relations`)
    suggestions.value = (res.data.suggestions || []).filter(s => {
      // Exclude already-linked posts
      const linkedIds = relations.value.map(r => r.related_post?.id).filter(Boolean)
      return !linkedIds.includes(s.post.id)
    })
  } catch (err) {
    console.error('Failed to load suggestions:', err)
  } finally {
    loadingSuggestions.value = false
  }
}

async function addRelation(targetPostId, relationType = 'cross_reference', note = '') {
  if (!props.postId) return
  try {
    await api.post(`/api/posts/${props.postId}/relations`, {
      target_post_id: targetPostId,
      relation_type: relationType,
      note,
    })
    toast.success('Verknuepfung erstellt!', 2000)
    await loadRelations()
    // Remove from suggestions
    suggestions.value = suggestions.value.filter(s => s.post.id !== targetPostId)
    // Remove from search results
    searchResults.value = searchResults.value.filter(p => p.id !== targetPostId)
  } catch (err) {
    if (err.response?.status === 409) {
      toast.error('Verknuepfung existiert bereits', 3000)
    } else {
      toast.error('Fehler: ' + (err.response?.data?.detail || err.message), 3000)
    }
  }
}

async function removeRelation(relationId) {
  if (!props.postId) return
  try {
    await api.delete(`/api/posts/${props.postId}/relations/${relationId}`)
    toast.success('Verknuepfung entfernt', 2000)
    await loadRelations()
  } catch (err) {
    toast.error('Fehler: ' + (err.response?.data?.detail || err.message), 3000)
  }
}

async function searchPosts() {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  searchLoading.value = true
  try {
    const res = await api.get('/api/posts', { params: { search: searchQuery.value, limit: 10, page: 1 } })
    const items = res.data.items || res.data || []
    // Filter out current post and already-linked posts
    const linkedIds = new Set(relations.value.map(r => r.related_post?.id).filter(Boolean))
    linkedIds.add(Number(props.postId))
    searchResults.value = items.filter(p => !linkedIds.has(p.id))
  } catch (err) {
    console.error('Search failed:', err)
  } finally {
    searchLoading.value = false
  }
}

// When panel becomes visible, load data
watch(showPanel, (val) => {
  if (val && props.postId) {
    loadRelations()
    loadSuggestions()
  }
})

onMounted(() => {
  if (props.postId) {
    // Pre-load relation count
    loadRelations()
  }
})

// Selecting relation type for a suggestion
const selectedType = ref('cross_reference')
</script>

<template>
  <div class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden" data-testid="related-posts-panel">
    <!-- Toggle header -->
    <button
      @click="showPanel = !showPanel"
      class="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
      data-testid="related-posts-toggle"
    >
      <div class="flex items-center gap-2">
        <AppIcon name="link" class="w-5 h-5" />
        <span class="text-sm font-bold text-gray-700 dark:text-gray-300">
          Verknuepfte Posts
        </span>
        <span v-if="relations.length > 0" class="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-[#3B7AB1] text-white">
          {{ relations.length }}
        </span>
      </div>
      <span class="text-gray-400 transition-transform" :class="showPanel ? 'rotate-180' : ''">&#9660;</span>
    </button>

    <!-- Panel content -->
    <div v-if="showPanel" class="px-4 pb-4 space-y-4">
      <!-- Loading state -->
      <div v-if="loading" class="flex items-center justify-center py-4">
        <div class="animate-spin h-5 w-5 border-2 border-[#3B7AB1] border-t-transparent rounded-full"></div>
      </div>

      <!-- Existing relations -->
      <div v-if="relations.length > 0" class="space-y-2">
        <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Aktuelle Verknuepfungen:</label>
        <div
          v-for="rel in relations"
          :key="rel.id"
          class="flex items-center gap-2 p-2 rounded-lg bg-gray-50 dark:bg-gray-700/30 group"
          data-testid="relation-item"
        >
          <!-- Type badge -->
          <span
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium"
            :class="typeLabels[rel.relation_type]?.color || 'bg-gray-100 text-gray-600'"
          >
            <AppIcon :name="typeLabels[rel.relation_type]?.icon || 'link'" class="w-3 h-3 inline-block" />
            {{ typeLabels[rel.relation_type]?.label || rel.relation_type }}
          </span>
          <!-- Direction arrow -->
          <span class="text-xs text-gray-400">
            {{ rel.direction === 'outgoing' ? '→' : '←' }}
          </span>
          <!-- Related post info -->
          <div v-if="rel.related_post" class="flex-1 min-w-0">
            <router-link
              :to="`/create/post/${rel.related_post.id}/edit`"
              class="text-xs font-medium text-[#3B7AB1] hover:underline truncate block"
              :title="rel.related_post.title"
            >
              <AppIcon v-if="platformIcons[rel.related_post.platform]" :name="platformIcons[rel.related_post.platform]" class="w-3 h-3 inline-block" />
              {{ rel.related_post.title || 'Ohne Titel' }}
              <span class="text-gray-400">#{{ rel.related_post.id }}</span>
            </router-link>
            <span class="text-[10px] text-gray-400">
              {{ platformLabels[rel.related_post.platform] || rel.related_post.platform }}
              <span v-if="rel.related_post.country">| {{ rel.related_post.country }}</span>
              <span v-if="rel.related_post.episode_number"> | E{{ rel.related_post.episode_number }}</span>
            </span>
          </div>
          <!-- Note -->
          <span v-if="rel.note" class="text-[10px] text-gray-400 italic truncate max-w-[80px]" :title="rel.note">{{ rel.note }}</span>
          <!-- Remove button -->
          <button
            @click="removeRelation(rel.id)"
            class="opacity-0 group-hover:opacity-100 p-1 text-red-400 hover:text-red-600 transition-all"
            title="Verknuepfung entfernen"
            data-testid="remove-relation-btn"
          >
            &times;
          </button>
        </div>
      </div>

      <!-- Suggestions section -->
      <div v-if="suggestions.length > 0">
        <label class="text-xs font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">
          <span>&#10024;</span> Vorgeschlagene Verknuepfungen:
        </label>
        <div class="space-y-1.5 mt-1.5">
          <div
            v-for="(sug, idx) in suggestions.slice(0, 6)"
            :key="'sug-' + idx"
            class="flex items-center gap-2 p-2 rounded-lg border border-dashed border-gray-200 dark:border-gray-600 hover:border-[#3B7AB1] hover:bg-blue-50/50 dark:hover:bg-blue-900/10 transition-colors group"
            data-testid="suggestion-item"
          >
            <!-- Suggested type badge -->
            <span
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium"
              :class="typeLabels[sug.suggested_type]?.color || 'bg-gray-100 text-gray-600'"
            >
              <AppIcon :name="typeLabels[sug.suggested_type]?.icon || 'link'" class="w-3 h-3 inline-block" />
              {{ typeLabels[sug.suggested_type]?.label || sug.suggested_type }}
            </span>
            <!-- Post info -->
            <div class="flex-1 min-w-0">
              <span class="text-xs font-medium text-gray-700 dark:text-gray-300 truncate block">
                <AppIcon v-if="platformIcons[sug.post.platform]" :name="platformIcons[sug.post.platform]" class="w-3 h-3 inline-block" />
                {{ sug.post.title || 'Ohne Titel' }}
                <span class="text-gray-400">#{{ sug.post.id }}</span>
              </span>
              <span class="text-[10px] text-gray-400">{{ sug.reason }}</span>
            </div>
            <!-- Add button -->
            <button
              @click="addRelation(sug.post.id, sug.suggested_type, sug.reason)"
              class="opacity-0 group-hover:opacity-100 px-2 py-1 text-[10px] font-bold text-white bg-[#3B7AB1] rounded hover:bg-[#2E6A9E] transition-all"
              data-testid="add-suggestion-btn"
            >
              + Verknuepfen
            </button>
          </div>
        </div>
      </div>

      <!-- Search for posts to link -->
      <div>
        <button
          @click="showSearchMode = !showSearchMode"
          class="text-xs font-medium text-[#3B7AB1] hover:text-[#2E6A9E] transition-colors flex items-center gap-1"
          data-testid="search-posts-toggle"
        >
          <span>&#128269;</span>
          {{ showSearchMode ? 'Suche schliessen' : 'Post suchen & verknuepfen' }}
        </button>

        <div v-if="showSearchMode" class="mt-2 space-y-2">
          <div class="flex gap-2">
            <input
              v-model="searchQuery"
              @input="searchPosts"
              placeholder="Post-Titel suchen..."
              class="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
              data-testid="search-posts-input"
            />
            <select
              v-model="selectedType"
              class="px-2 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-xs text-gray-700 dark:text-gray-300 focus:ring-2 focus:ring-[#3B7AB1]"
            >
              <option value="cross_reference">Verweis</option>
              <option value="story_teaser">Story-Teaser</option>
              <option value="sequel">Fortsetzung</option>
              <option value="related">Verwandt</option>
            </select>
          </div>

          <div v-if="searchLoading" class="flex items-center justify-center py-2">
            <div class="animate-spin h-4 w-4 border-2 border-[#3B7AB1] border-t-transparent rounded-full"></div>
          </div>

          <div v-else-if="searchResults.length > 0" class="space-y-1">
            <div
              v-for="result in searchResults"
              :key="'search-' + result.id"
              class="flex items-center gap-2 p-2 rounded-lg bg-gray-50 dark:bg-gray-700/30 hover:bg-blue-50 dark:hover:bg-blue-900/10 cursor-pointer transition-colors"
              @click="addRelation(result.id, selectedType)"
              data-testid="search-result-item"
            >
              <AppIcon :name="platformIcons[result.platform] || 'document-text'" class="w-3.5 h-3.5" />
              <div class="flex-1 min-w-0">
                <span class="text-xs font-medium text-gray-700 dark:text-gray-300 truncate block">
                  {{ result.title || 'Ohne Titel' }}
                  <span class="text-gray-400">#{{ result.id }}</span>
                </span>
                <span class="text-[10px] text-gray-400">
                  {{ platformLabels[result.platform] || result.platform }}
                  <span v-if="result.country">| {{ result.country }}</span>
                  | {{ result.status }}
                </span>
              </div>
              <span class="text-[10px] text-[#3B7AB1] font-bold">+ Verknuepfen</span>
            </div>
          </div>

          <p v-else-if="searchQuery.trim() && !searchLoading" class="text-xs text-gray-400 py-2">
            Keine passenden Posts gefunden.
          </p>
        </div>
      </div>

      <!-- Auto-suggest teaser hint (when post belongs to a story arc) -->
      <div
        v-if="storyArcId && relations.filter(r => r.relation_type === 'story_teaser').length === 0"
        class="p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg"
        data-testid="teaser-suggestion-hint"
      >
        <div class="flex items-start gap-2">
          <AppIcon name="light-bulb" class="w-4 h-4 shrink-0" />
          <div>
            <p class="text-xs font-medium text-amber-700 dark:text-amber-300">
              Tipp: Erstelle einen Feed-Teaser-Post!
            </p>
            <p class="text-[10px] text-amber-600 dark:text-amber-400 mt-0.5">
              Dieser Post gehoert zu einer Story-Serie. Ein Feed-Post als Teaser
              ("Kennst du schon die Geschichte? Schau in unsere Stories!") kann die
              Reichweite deutlich erhoehen.
            </p>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <p v-if="!loading && relations.length === 0 && suggestions.length === 0 && !showSearchMode" class="text-xs text-gray-400 text-center py-2">
        Keine Verknuepfungen vorhanden. Suche nach Posts oder nutze die Vorschlaege.
      </p>
    </div>
  </div>
</template>
