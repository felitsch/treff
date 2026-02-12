<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'

const router = useRouter()

const loading = ref(true)
const error = ref(null)
const posts = ref([])

// Filters
const searchQuery = ref('')
const filterCategory = ref('')
const filterPlatform = ref('')
const filterStatus = ref('')

const categories = [
  { id: 'laender_spotlight', label: 'Laender-Spotlight', icon: '🌍' },
  { id: 'erfahrungsberichte', label: 'Erfahrungsberichte', icon: '💬' },
  { id: 'infografiken', label: 'Infografiken', icon: '📊' },
  { id: 'fristen_cta', label: 'Fristen & CTA', icon: '⏰' },
  { id: 'tipps_tricks', label: 'Tipps & Tricks', icon: '💡' },
  { id: 'faq', label: 'FAQ', icon: '❓' },
  { id: 'foto_posts', label: 'Foto-Posts', icon: '📸' },
  { id: 'reel_tiktok_thumbnails', label: 'Reel/TikTok', icon: '🎬' },
  { id: 'story_posts', label: 'Story-Posts', icon: '📱' },
]

const platforms = [
  { id: 'instagram_feed', label: 'Instagram Feed', icon: '📷' },
  { id: 'instagram_story', label: 'Instagram Story', icon: '📱' },
  { id: 'tiktok', label: 'TikTok', icon: '🎵' },
]

const statuses = [
  { id: 'draft', label: 'Entwurf' },
  { id: 'scheduled', label: 'Geplant' },
  { id: 'reminded', label: 'Erinnert' },
  { id: 'exported', label: 'Exportiert' },
  { id: 'posted', label: 'Veroeffentlicht' },
]

// Category helpers
function categoryLabel(catId) {
  const cat = categories.find(c => c.id === catId)
  return cat ? cat.label : catId
}

function categoryIcon(catId) {
  const cat = categories.find(c => c.id === catId)
  return cat ? cat.icon : '📄'
}

// Platform helpers
function platformLabel(platId) {
  const plat = platforms.find(p => p.id === platId)
  return plat ? plat.label : platId
}

function platformIcon(platId) {
  const plat = platforms.find(p => p.id === platId)
  return plat ? plat.icon : '📱'
}

// Status helpers
function statusLabel(statusId) {
  const s = statuses.find(st => st.id === statusId)
  return s ? s.label : statusId
}

function statusColor(statusId) {
  switch (statusId) {
    case 'draft':
      return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
    case 'scheduled':
      return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
    case 'reminded':
      return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
    case 'exported':
      return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
    case 'posted':
      return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
    default:
      return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
  }
}

// Category color for thumbnail backgrounds
function categoryColor(catId) {
  const colors = {
    laender_spotlight: 'from-blue-400 to-blue-600',
    erfahrungsberichte: 'from-purple-400 to-purple-600',
    infografiken: 'from-cyan-400 to-cyan-600',
    fristen_cta: 'from-red-400 to-red-600',
    tipps_tricks: 'from-amber-400 to-amber-600',
    faq: 'from-teal-400 to-teal-600',
    foto_posts: 'from-pink-400 to-pink-600',
    reel_tiktok_thumbnails: 'from-violet-400 to-violet-600',
    story_posts: 'from-orange-400 to-orange-600',
  }
  return colors[catId] || 'from-gray-400 to-gray-600'
}

// Date formatting
function formatDate(dateStr) {
  if (!dateStr) return '—'
  const date = new Date(dateStr)
  return date.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatDateShort(dateStr) {
  if (!dateStr) return '—'
  const date = new Date(dateStr)
  return date.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

// Filtered posts
const filteredPosts = computed(() => {
  let result = posts.value

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(p =>
      (p.title && p.title.toLowerCase().includes(q)) ||
      (p.category && p.category.toLowerCase().includes(q)) ||
      (p.caption_instagram && p.caption_instagram.toLowerCase().includes(q)) ||
      (p.caption_tiktok && p.caption_tiktok.toLowerCase().includes(q)) ||
      (p.slide_data && p.slide_data.toLowerCase().includes(q)) ||
      (p.cta_text && p.cta_text.toLowerCase().includes(q))
    )
  }

  if (filterCategory.value) {
    result = result.filter(p => p.category === filterCategory.value)
  }

  if (filterPlatform.value) {
    result = result.filter(p => p.platform === filterPlatform.value)
  }

  if (filterStatus.value) {
    result = result.filter(p => p.status === filterStatus.value)
  }

  return result
})

// Active filters count
const activeFilters = computed(() => {
  let count = 0
  if (searchQuery.value) count++
  if (filterCategory.value) count++
  if (filterPlatform.value) count++
  if (filterStatus.value) count++
  return count
})

// Clear all filters
function clearFilters() {
  searchQuery.value = ''
  filterCategory.value = ''
  filterPlatform.value = ''
  filterStatus.value = ''
}

// Fetch posts from API
async function fetchPosts() {
  loading.value = true
  error.value = null
  try {
    const params = {}
    if (filterCategory.value) params.category = filterCategory.value
    if (filterPlatform.value) params.platform = filterPlatform.value
    if (filterStatus.value) params.status = filterStatus.value
    if (searchQuery.value) params.search = searchQuery.value

    const response = await api.get('/api/posts', { params })
    posts.value = response.data
  } catch (err) {
    console.error('Failed to fetch posts:', err)
    error.value = 'Fehler beim Laden der Posts. Bitte versuche es erneut.'
  } finally {
    loading.value = false
  }
}

// Scheduling dialog state
const showScheduleDialog = ref(false)
const postToSchedule = ref(null)
const scheduling = ref(false)
const scheduleDate = ref('')
const scheduleTime = ref('')
const scheduleError = ref(null)

function openScheduleDialog(post) {
  postToSchedule.value = post
  // Pre-fill with existing schedule if any
  if (post.scheduled_date) {
    // Extract date part (YYYY-MM-DD) from ISO string
    scheduleDate.value = post.scheduled_date.substring(0, 10)
  } else {
    scheduleDate.value = ''
  }
  scheduleTime.value = post.scheduled_time || ''
  scheduleError.value = null
  showScheduleDialog.value = true
}

function cancelSchedule() {
  showScheduleDialog.value = false
  postToSchedule.value = null
  scheduleDate.value = ''
  scheduleTime.value = ''
  scheduleError.value = null
}

async function executeSchedule() {
  if (!postToSchedule.value || !scheduleDate.value || !scheduleTime.value) {
    scheduleError.value = 'Bitte Datum und Uhrzeit angeben.'
    return
  }
  scheduling.value = true
  scheduleError.value = null
  try {
    const response = await api.put(`/api/posts/${postToSchedule.value.id}/schedule`, {
      scheduled_date: scheduleDate.value,
      scheduled_time: scheduleTime.value,
    })
    // Update the post in the local list with the response data
    const idx = posts.value.findIndex(p => p.id === postToSchedule.value.id)
    if (idx !== -1) {
      posts.value[idx] = response.data
    }
    showScheduleDialog.value = false
    postToSchedule.value = null
  } catch (err) {
    console.error('Failed to schedule post:', err)
    scheduleError.value = err.response?.data?.detail || 'Fehler beim Planen des Posts.'
  } finally {
    scheduling.value = false
  }
}

// Delete confirmation dialog state
const showDeleteDialog = ref(false)
const postToDelete = ref(null)
const deleting = ref(false)

// Open delete confirmation dialog
function confirmDeletePost(post) {
  postToDelete.value = post
  showDeleteDialog.value = true
}

// Cancel delete
function cancelDelete() {
  showDeleteDialog.value = false
  postToDelete.value = null
}

// Execute delete
async function executeDelete() {
  if (!postToDelete.value) return
  deleting.value = true
  try {
    await api.delete(`/api/posts/${postToDelete.value.id}`)
    posts.value = posts.value.filter(p => p.id !== postToDelete.value.id)
    showDeleteDialog.value = false
    postToDelete.value = null
  } catch (err) {
    console.error('Failed to delete post:', err)
  } finally {
    deleting.value = false
  }
}

// Navigate to edit
function editPost(postId) {
  router.push(`/posts/${postId}/edit`)
}

// Navigate to create
function createPost() {
  router.push('/create-post')
}

onMounted(() => {
  fetchPosts()
})
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Post-Verlauf</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Alle erstellten Posts anzeigen und verwalten
        </p>
      </div>
      <button
        @click="createPost"
        class="inline-flex items-center gap-2 px-4 py-2 bg-[#4C8BC2] text-white rounded-lg hover:bg-[#3a7ab1] transition-colors"
      >
        <span>+</span>
        <span>Neuer Post</span>
      </button>
    </div>

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-6">
      <div class="flex flex-wrap items-center gap-3">
        <!-- Search -->
        <div class="flex-1 min-w-[200px]">
          <div class="relative">
            <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Posts durchsuchen..."
              class="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent"
              @input="fetchPosts"
            />
          </div>
        </div>

        <!-- Category filter -->
        <select
          v-model="filterCategory"
          @change="fetchPosts"
          class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#4C8BC2]"
        >
          <option value="">Alle Kategorien</option>
          <option v-for="cat in categories" :key="cat.id" :value="cat.id">
            {{ cat.icon }} {{ cat.label }}
          </option>
        </select>

        <!-- Platform filter -->
        <select
          v-model="filterPlatform"
          @change="fetchPosts"
          class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#4C8BC2]"
        >
          <option value="">Alle Plattformen</option>
          <option v-for="plat in platforms" :key="plat.id" :value="plat.id">
            {{ plat.icon }} {{ plat.label }}
          </option>
        </select>

        <!-- Status filter -->
        <select
          v-model="filterStatus"
          @change="fetchPosts"
          class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#4C8BC2]"
        >
          <option value="">Alle Status</option>
          <option v-for="s in statuses" :key="s.id" :value="s.id">
            {{ s.label }}
          </option>
        </select>

        <!-- Clear filters -->
        <button
          v-if="activeFilters > 0"
          @click="clearFilters(); fetchPosts()"
          class="text-sm text-[#4C8BC2] hover:text-[#3a7ab1] transition-colors"
        >
          Filter zuruecksetzen ({{ activeFilters }})
        </button>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="space-y-4">
      <div v-for="i in 4" :key="i" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 animate-pulse">
        <div class="flex items-center gap-4">
          <div class="w-16 h-16 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
          <div class="flex-1">
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-2"></div>
            <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
          </div>
          <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
        </div>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
      <p class="text-red-600 dark:text-red-400 mb-3">{{ error }}</p>
      <button
        @click="fetchPosts"
        class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
      >
        Erneut versuchen
      </button>
    </div>

    <!-- Empty state -->
    <div v-else-if="filteredPosts.length === 0 && !searchQuery && !filterCategory && !filterPlatform && !filterStatus" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-12 text-center">
      <div class="text-5xl mb-4">📝</div>
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Noch keine Posts erstellt</h3>
      <p class="text-gray-500 dark:text-gray-400 mb-6">Erstelle deinen ersten Social-Media-Post fuer TREFF!</p>
      <button
        @click="createPost"
        class="inline-flex items-center gap-2 px-6 py-3 bg-[#4C8BC2] text-white rounded-lg hover:bg-[#3a7ab1] transition-colors"
      >
        <span>+</span>
        <span>Ersten Post erstellen</span>
      </button>
    </div>

    <!-- No results for filter -->
    <div v-else-if="filteredPosts.length === 0" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-12 text-center">
      <div class="text-5xl mb-4">🔍</div>
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Keine Posts gefunden</h3>
      <p class="text-gray-500 dark:text-gray-400 mb-4">Keine Posts passen zu deinen Filtern.</p>
      <button
        @click="clearFilters(); fetchPosts()"
        class="text-[#4C8BC2] hover:text-[#3a7ab1] text-sm"
      >
        Filter zuruecksetzen
      </button>
    </div>

    <!-- Posts list -->
    <div v-else class="space-y-3">
      <!-- Results count -->
      <div class="text-sm text-gray-500 dark:text-gray-400 mb-2">
        {{ filteredPosts.length }} {{ filteredPosts.length === 1 ? 'Post' : 'Posts' }} gefunden
      </div>

      <!-- Post cards -->
      <div
        v-for="post in filteredPosts"
        :key="post.id"
        class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow"
      >
        <div class="flex items-center p-4 gap-4">
          <!-- Thumbnail -->
          <div
            class="w-16 h-16 rounded-lg flex-shrink-0 bg-gradient-to-br flex items-center justify-center text-white text-2xl"
            :class="categoryColor(post.category)"
          >
            {{ categoryIcon(post.category) }}
          </div>

          <!-- Post info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <h3 class="text-sm font-semibold text-gray-900 dark:text-white truncate">
                {{ post.title || 'Unbenannter Post' }}
              </h3>
            </div>
            <div class="flex flex-wrap items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
              <!-- Category -->
              <span class="inline-flex items-center gap-1">
                <span>{{ categoryIcon(post.category) }}</span>
                <span>{{ categoryLabel(post.category) }}</span>
              </span>
              <span class="text-gray-300 dark:text-gray-600">|</span>
              <!-- Platform -->
              <span class="inline-flex items-center gap-1">
                <span>{{ platformIcon(post.platform) }}</span>
                <span>{{ platformLabel(post.platform) }}</span>
              </span>
              <span class="text-gray-300 dark:text-gray-600">|</span>
              <!-- Date -->
              <span>{{ formatDateShort(post.created_at) }}</span>
            </div>
          </div>

          <!-- Status badge -->
          <div class="flex-shrink-0">
            <span
              class="inline-block px-2.5 py-1 rounded-full text-xs font-medium"
              :class="statusColor(post.status)"
            >
              {{ statusLabel(post.status) }}
            </span>
          </div>

          <!-- Scheduled info -->
          <div v-if="post.scheduled_date && post.scheduled_time" class="flex-shrink-0 text-xs text-gray-500 dark:text-gray-400 text-right">
            <div class="flex items-center gap-1">
              <span>📅</span>
              <span>{{ formatDateShort(post.scheduled_date) }}</span>
            </div>
            <div class="flex items-center gap-1">
              <span>🕐</span>
              <span>{{ post.scheduled_time }} Uhr</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-1 flex-shrink-0">
            <button
              @click="openScheduleDialog(post)"
              class="p-2 text-gray-400 hover:text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded-lg transition-colors"
              title="Planen"
            >
              📅
            </button>
            <button
              @click="editPost(post.id)"
              class="p-2 text-gray-400 hover:text-[#4C8BC2] hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title="Bearbeiten"
            >
              ✏️
            </button>
            <button
              @click="confirmDeletePost(post)"
              class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
              title="Loeschen"
            >
              🗑️
            </button>
          </div>
        </div>
      </div>
    </div>
    <!-- Delete Confirmation Dialog -->
    <Teleport to="body">
      <div v-if="showDeleteDialog" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="cancelDelete"></div>
        <!-- Dialog -->
        <div class="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full p-6 z-10">
          <div class="text-center">
            <div class="mx-auto flex items-center justify-center w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 mb-4">
              <span class="text-2xl">⚠️</span>
            </div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Post loeschen?</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
              Moechtest du den Post <strong class="text-gray-700 dark:text-gray-300">"{{ postToDelete?.title || 'Unbenannter Post' }}"</strong> wirklich loeschen? Diese Aktion kann nicht rueckgaengig gemacht werden.
            </p>
            <div class="flex gap-3 justify-center">
              <button
                @click="cancelDelete"
                :disabled="deleting"
                class="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
              >
                Abbrechen
              </button>
              <button
                @click="executeDelete"
                :disabled="deleting"
                class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
              >
                {{ deleting ? 'Wird geloescht...' : 'Loeschen' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Schedule Dialog -->
    <Teleport to="body">
      <div v-if="showScheduleDialog" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="cancelSchedule"></div>
        <!-- Dialog -->
        <div class="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full p-6 z-10">
          <div>
            <div class="flex items-center gap-3 mb-4">
              <div class="flex items-center justify-center w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30">
                <span class="text-xl">📅</span>
              </div>
              <div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Post planen</h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  "{{ postToSchedule?.title || 'Unbenannter Post' }}"
                </p>
              </div>
            </div>

            <!-- Error message -->
            <div v-if="scheduleError" class="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-600 dark:text-red-400">
              {{ scheduleError }}
            </div>

            <!-- Date input -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Datum
              </label>
              <input
                v-model="scheduleDate"
                type="date"
                class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent"
              />
            </div>

            <!-- Time input -->
            <div class="mb-6">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Uhrzeit
              </label>
              <input
                v-model="scheduleTime"
                type="time"
                class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent"
              />
            </div>

            <div class="flex gap-3 justify-end">
              <button
                @click="cancelSchedule"
                :disabled="scheduling"
                class="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
              >
                Abbrechen
              </button>
              <button
                @click="executeSchedule"
                :disabled="scheduling || !scheduleDate || !scheduleTime"
                class="px-4 py-2 bg-[#4C8BC2] text-white rounded-lg hover:bg-[#3a7ab1] transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {{ scheduling ? 'Wird geplant...' : 'Post planen' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
