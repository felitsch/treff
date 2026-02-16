<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import JSZip from 'jszip'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import { useStudentStore } from '@/stores/students'
import TourSystem from '@/components/common/TourSystem.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SkeletonBase from '@/components/common/SkeletonBase.vue'
import BaseCard from '@/components/common/BaseCard.vue'

const router = useRouter()
const toast = useToast()
const studentStore = useStudentStore()

const loading = ref(true)
const error = ref(null)
const posts = ref([])
const tourRef = ref(null)

// Pagination
const currentPage = ref(1)
const totalPages = ref(1)
const totalPosts = ref(0)
const postsPerPage = ref(10)

// Filters
const searchQuery = ref('')
const filterCategory = ref('')
const filterPlatform = ref('')
const filterStatus = ref('')
const filterCountry = ref('')
const filterDateFrom = ref('')
const filterDateTo = ref('')

// Debounced search
let searchTimer = null
function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    fetchPosts()
  }, 200)
}

// Sorting
const sortBy = ref('created_at')
const sortDirection = ref('desc')

const sortOptions = [
  { id: 'created_at', label: 'Erstelldatum' },
  { id: 'updated_at', label: 'Aktualisiert' },
  { id: 'title', label: 'Titel' },
  { id: 'scheduled_date', label: 'Geplantes Datum' },
]

function toggleSortDirection() {
  sortDirection.value = sortDirection.value === 'desc' ? 'asc' : 'desc'
  fetchPosts()
}

function changeSortBy(value) {
  sortBy.value = value
  fetchPosts()
}

// Quick date range presets
const dateRangePresets = [
  { label: 'Letzte 7 Tage', days: 7 },
  { label: 'Letzte 30 Tage', days: 30 },
  { label: 'Letzte 90 Tage', days: 90 },
]

function applyDatePreset(days) {
  const now = new Date()
  const from = new Date(now)
  from.setDate(from.getDate() - days)
  filterDateFrom.value = from.toISOString().split('T')[0]
  filterDateTo.value = now.toISOString().split('T')[0]
  fetchPosts()
}

function clearDateFilter() {
  filterDateFrom.value = ''
  filterDateTo.value = ''
  fetchPosts()
}

function isPresetActive(days) {
  if (!filterDateFrom.value || !filterDateTo.value) return false
  const now = new Date()
  const expectedFrom = new Date(now)
  expectedFrom.setDate(expectedFrom.getDate() - days)
  return filterDateFrom.value === expectedFrom.toISOString().split('T')[0] &&
         filterDateTo.value === now.toISOString().split('T')[0]
}

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
  { id: 'story_teaser', label: 'Story-Teaser', icon: '👉' },
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

const countries = [
  { id: 'usa', label: 'USA', flag: '🇺🇸' },
  { id: 'canada', label: 'Kanada', flag: '🇨🇦' },
  { id: 'australia', label: 'Australien', flag: '🇦🇺' },
  { id: 'newzealand', label: 'Neuseeland', flag: '🇳🇿' },
  { id: 'ireland', label: 'Irland', flag: '🇮🇪' },
]

// Country helpers
function countryLabel(countryId) {
  const c = countries.find(co => co.id === countryId)
  return c ? c.label : countryId
}

function countryFlag(countryId) {
  const c = countries.find(co => co.id === countryId)
  return c ? c.flag : '🌍'
}

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

// Student helper
function getStudentName(studentId) {
  if (!studentId) return null
  const student = studentStore.students.find(s => s.id === studentId)
  return student ? student.name : null
}

// With server-side pagination, posts are already filtered - use directly
const filteredPosts = computed(() => posts.value)

// Active filters count
const activeFilters = computed(() => {
  let count = 0
  if (searchQuery.value && searchQuery.value.trim()) count++
  if (filterCategory.value) count++
  if (filterPlatform.value) count++
  if (filterStatus.value) count++
  if (filterCountry.value) count++
  if (filterDateFrom.value || filterDateTo.value) count++
  return count
})

// Clear all filters
function clearFilters() {
  searchQuery.value = ''
  filterCategory.value = ''
  filterPlatform.value = ''
  filterStatus.value = ''
  filterCountry.value = ''
  filterDateFrom.value = ''
  filterDateTo.value = ''
}

// Fetch posts from API with pagination
async function fetchPosts(resetPage = true) {
  loading.value = true
  error.value = null
  if (resetPage) {
    currentPage.value = 1
  }
  try {
    const params = {}
    if (filterCategory.value) params.category = filterCategory.value
    if (filterPlatform.value) params.platform = filterPlatform.value
    if (filterStatus.value) params.status = filterStatus.value
    if (filterCountry.value) params.country = filterCountry.value
    if (searchQuery.value && searchQuery.value.trim()) params.search = searchQuery.value.trim()
    if (filterDateFrom.value) params.date_from = filterDateFrom.value
    if (filterDateTo.value) params.date_to = filterDateTo.value
    params.sort_by = sortBy.value
    params.sort_direction = sortDirection.value
    params.page = currentPage.value
    params.limit = postsPerPage.value

    const response = await api.get('/api/posts', { params })
    // Handle paginated response
    if (response.data && response.data.items) {
      posts.value = response.data.items
      totalPosts.value = response.data.total
      totalPages.value = response.data.total_pages
      currentPage.value = response.data.page
    } else {
      // Backward compatible: flat array response
      posts.value = response.data
      totalPosts.value = response.data.length
      totalPages.value = 1
      currentPage.value = 1
    }
  } catch (err) {
    console.error('Failed to fetch posts:', err)
    error.value = 'Fehler beim Laden der Posts. Bitte versuche es erneut.'
  } finally {
    loading.value = false
  }
}

// Pagination navigation
function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchPosts(false)
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    goToPage(currentPage.value + 1)
  }
}

function prevPage() {
  if (currentPage.value > 1) {
    goToPage(currentPage.value - 1)
  }
}

// Generate visible page numbers for pagination
const visiblePages = computed(() => {
  const pages = []
  const total = totalPages.value
  const current = currentPage.value

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    pages.push(1)
    if (current > 3) pages.push('...')
    for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) {
      pages.push(i)
    }
    if (current < total - 2) pages.push('...')
    pages.push(total)
  }
  return pages
})

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

// Execute delete (idempotent - guards against double-click)
async function executeDelete() {
  if (!postToDelete.value || deleting.value) return
  deleting.value = true
  const deleteId = postToDelete.value.id
  try {
    await api.delete(`/api/posts/${deleteId}`)
    showDeleteDialog.value = false
    postToDelete.value = null
    // Re-fetch current page; if the page is now empty, go back one page
    await fetchPosts(false)
    if (posts.value.length === 0 && currentPage.value > 1) {
      currentPage.value = Math.max(1, currentPage.value - 1)
      await fetchPosts(false)
    }
  } catch (err) {
    // If post is already deleted (404), treat as success (idempotent delete)
    if (err.response?.status === 404) {
      showDeleteDialog.value = false
      postToDelete.value = null
      await fetchPosts(false)
      if (posts.value.length === 0 && currentPage.value > 1) {
        currentPage.value = Math.max(1, currentPage.value - 1)
        await fetchPosts(false)
      }
    } else {
      console.error('Failed to delete post:', err)
      // Error toast is shown by global API interceptor
    }
  } finally {
    deleting.value = false
  }
}

// Mark post as posted
async function markAsPosted(post) {
  try {
    const response = await api.put(`/api/posts/${post.id}/status`, {
      status: 'posted',
    })
    // Update the post in the local list with the response data
    const idx = posts.value.findIndex(p => p.id === post.id)
    if (idx !== -1) {
      posts.value[idx] = response.data
    }
  } catch (err) {
    console.error('Failed to mark post as posted:', err)
    // Error toast is shown by global API interceptor
  }
}

// Duplicate a post
const duplicating = ref(null)
async function duplicatePost(post) {
  duplicating.value = post.id
  try {
    await api.post(`/api/posts/${post.id}/duplicate`)
    // Re-fetch page 1 to show the new duplicate at top
    currentPage.value = 1
    await fetchPosts(false)
  } catch (err) {
    console.error('Failed to duplicate post:', err)
  } finally {
    duplicating.value = null
  }
}

// ── Batch Selection & Export ──
const selectionMode = ref(false)
const selectedPostIds = ref(new Set())
const batchExporting = ref(false)

function toggleSelectionMode() {
  selectionMode.value = !selectionMode.value
  if (!selectionMode.value) {
    selectedPostIds.value = new Set()
  }
}

function togglePostSelection(postId) {
  const newSet = new Set(selectedPostIds.value)
  if (newSet.has(postId)) {
    newSet.delete(postId)
  } else {
    newSet.add(postId)
  }
  selectedPostIds.value = newSet
}

function isPostSelected(postId) {
  return selectedPostIds.value.has(postId)
}

const allOnPageSelected = computed(() => {
  if (posts.value.length === 0) return false
  return posts.value.every(p => selectedPostIds.value.has(p.id))
})

function toggleSelectAll() {
  if (allOnPageSelected.value) {
    // Deselect all on current page
    const newSet = new Set(selectedPostIds.value)
    posts.value.forEach(p => newSet.delete(p.id))
    selectedPostIds.value = newSet
  } else {
    // Select all on current page
    const newSet = new Set(selectedPostIds.value)
    posts.value.forEach(p => newSet.add(p.id))
    selectedPostIds.value = newSet
  }
}

const selectedCount = computed(() => selectedPostIds.value.size)

// Platform dimensions for rendering
const platformDimensions = {
  instagram_feed: { w: 1080, h: 1080 },
  instagram_story: { w: 1080, h: 1920 },
  tiktok: { w: 1080, h: 1920 },
}

function canvasToBlob(canvas) {
  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob), 'image/png')
  })
}

function wrapTextOnCanvas(ctx, text, x, y, maxWidth, lineHeight) {
  const words = text.split(' ')
  let line = ''
  let currentY = y
  for (const word of words) {
    const testLine = line + word + ' '
    const metrics = ctx.measureText(testLine)
    if (metrics.width > maxWidth && line !== '') {
      ctx.fillText(line.trim(), x, currentY)
      line = word + ' '
      currentY += lineHeight
    } else {
      line = testLine
    }
  }
  ctx.fillText(line.trim(), x, currentY)
}

function roundRectOnCanvas(ctx, x, y, w, h, r) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.lineTo(x + w - r, y)
  ctx.quadraticCurveTo(x + w, y, x + w, y + r)
  ctx.lineTo(x + w, y + h - r)
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h)
  ctx.lineTo(x + r, y + h)
  ctx.quadraticCurveTo(x, y + h, x, y + h - r)
  ctx.lineTo(x, y + r)
  ctx.quadraticCurveTo(x, y, x + r, y)
  ctx.closePath()
}

function renderSlideForPost(slide, platform) {
  const dims = platformDimensions[platform] || platformDimensions.instagram_feed
  const canvas = document.createElement('canvas')
  canvas.width = dims.w
  canvas.height = dims.h
  const ctx = canvas.getContext('2d')

  // Background
  ctx.fillStyle = slide.background_value || '#1A1A2E'
  ctx.fillRect(0, 0, dims.w, dims.h)

  // Gradient overlay
  const gradient = ctx.createLinearGradient(0, 0, 0, dims.h)
  gradient.addColorStop(0, 'rgba(76, 139, 194, 0.3)')
  gradient.addColorStop(1, 'rgba(26, 26, 46, 0.8)')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, dims.w, dims.h)

  // TREFF logo
  ctx.fillStyle = '#3B7AB1'
  ctx.font = 'bold 28px Inter, Arial, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('TREFF', 60, 80)
  ctx.fillStyle = '#9CA3AF'
  ctx.font = '18px Inter, Arial, sans-serif'
  ctx.fillText('Sprachreisen', 158, 80)

  // Headline
  ctx.fillStyle = '#3B7AB1'
  ctx.font = 'bold 52px Inter, Arial, sans-serif'
  ctx.textAlign = 'center'
  wrapTextOnCanvas(ctx, slide.headline || '', dims.w / 2, 260, dims.w - 160, 62)

  // Subheadline
  if (slide.subheadline) {
    ctx.fillStyle = '#FDD000'
    ctx.font = 'bold 32px Inter, Arial, sans-serif'
    wrapTextOnCanvas(ctx, slide.subheadline, dims.w / 2, 400, dims.w - 160, 40)
  }

  // Body text
  if (slide.body_text) {
    ctx.fillStyle = '#D1D5DB'
    ctx.font = '24px Inter, Arial, sans-serif'
    wrapTextOnCanvas(ctx, slide.body_text, dims.w / 2, 520, dims.w - 160, 32)
  }

  // CTA
  if (slide.cta_text) {
    const ctaY = dims.h - 180
    ctx.fillStyle = '#FDD000'
    roundRectOnCanvas(ctx, dims.w / 2 - 150, ctaY, 300, 56, 28)
    ctx.fill()
    ctx.fillStyle = '#1A1A2E'
    ctx.font = 'bold 24px Inter, Arial, sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(slide.cta_text, dims.w / 2, ctaY + 37)
  }

  // TREFF bottom branding
  ctx.fillStyle = '#3B7AB1'
  ctx.font = 'bold 18px Inter, Arial, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('TREFF Sprachreisen', 60, dims.h - 50)

  return canvas
}

async function executeBatchExport() {
  if (selectedPostIds.value.size === 0) return
  batchExporting.value = true

  try {
    const postIds = Array.from(selectedPostIds.value)

    // Fetch full post data for all selected posts
    const postDetails = []
    for (const pid of postIds) {
      const resp = await api.get(`/api/posts/${pid}`)
      postDetails.push(resp.data)
    }

    // Record batch export in backend
    await api.post('/api/export/batch', {
      post_ids: postIds,
      platform: 'instagram_feed',
      resolution: '1080',
    })

    // Generate ZIP with all posts
    const zip = new JSZip()
    const date = new Date().toISOString().split('T')[0]

    for (const post of postDetails) {
      let slides = []
      try {
        slides = JSON.parse(post.slide_data || '[]')
      } catch {
        slides = [{ headline: post.title || 'Untitled' }]
      }
      if (!Array.isArray(slides) || slides.length === 0) {
        slides = [{ headline: post.title || 'Untitled' }]
      }

      const platform = post.platform || 'instagram_feed'
      const postFolder = zip.folder(`post_${post.id}_${(post.title || 'untitled').replace(/[^a-zA-Z0-9_-]/g, '_').substring(0, 40)}`)

      for (let i = 0; i < slides.length; i++) {
        const canvas = renderSlideForPost(slides[i], platform)
        const blob = await canvasToBlob(canvas)
        const slideNum = String(i + 1).padStart(2, '0')
        postFolder.file(`TREFF_${post.category || 'post'}_${platform}_${date}_slide_${slideNum}.png`, blob)
      }
    }

    const zipBlob = await zip.generateAsync({ type: 'blob' })
    const link = document.createElement('a')
    link.download = `TREFF_batch_export_${postDetails.length}_posts_${date}.zip`
    link.href = URL.createObjectURL(zipBlob)
    link.click()
    URL.revokeObjectURL(link.href)

    toast.success(`${postDetails.length} Posts erfolgreich exportiert!`, 5000)

    // Refresh posts list to show updated status
    await fetchPosts(false)

    // Clear selection
    selectedPostIds.value = new Set()
    selectionMode.value = false
  } catch (err) {
    console.error('Batch export failed:', err)
    toast.error('Batch-Export fehlgeschlagen: ' + (err.response?.data?.detail || err.message), 5000)
  } finally {
    batchExporting.value = false
  }
}

// Navigate to edit
function editPost(postId) {
  router.push(`/create/post/${postId}/edit`)
}

// Navigate to create
function createPost() {
  router.push('/create/quick')
}

onMounted(() => {
  fetchPosts()
  studentStore.fetchStudents()
})

onUnmounted(() => {
  clearTimeout(searchTimer)
})
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div data-tour="history-header" class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Post-Verlauf</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Alle erstellten Posts anzeigen und verwalten
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="tourRef?.startTour()"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          title="Seiten-Tour starten"
        >
          &#10067; Tour
        </button>
        <button
          data-tour="history-batch"
          @click="toggleSelectionMode"
          class="inline-flex items-center gap-2 px-4 py-2 rounded-lg transition-colors text-sm"
          :class="selectionMode
            ? 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-500'
            : 'border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'"
        >
          <span>☑️</span>
          <span>{{ selectionMode ? 'Abbrechen' : 'Auswaehlen' }}</span>
        </button>
        <button
          @click="createPost"
          class="inline-flex items-center gap-2 px-4 py-2 bg-[#3B7AB1] text-white rounded-lg hover:bg-[#2E6A9E] transition-colors"
        >
          <span>+</span>
          <span>Neuer Post</span>
        </button>
      </div>
    </div>

    <!-- Batch Actions Bar -->
    <div
      v-if="selectionMode"
      class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4 mb-4 flex items-center justify-between"
    >
      <div class="flex items-center gap-4">
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            :checked="allOnPageSelected"
            @change="toggleSelectAll"
            class="w-4 h-4 rounded border-gray-300 text-[#3B7AB1] focus:ring-[#3B7AB1]"
            aria-label="Alle auf dieser Seite auswaehlen"
          />
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Alle auswaehlen</span>
        </label>
        <span class="text-sm text-gray-500 dark:text-gray-400">
          {{ selectedCount }} {{ selectedCount === 1 ? 'Post' : 'Posts' }} ausgewaehlt
        </span>
      </div>
      <button
        @click="executeBatchExport"
        :disabled="selectedCount === 0 || batchExporting"
        class="inline-flex items-center gap-2 px-4 py-2 bg-[#3B7AB1] text-white rounded-lg hover:bg-[#2E6A9E] transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span>{{ batchExporting ? '⏳' : '📦' }}</span>
        <span>{{ batchExporting ? 'Exportiere...' : `Batch-Export (${selectedCount})` }}</span>
      </button>
    </div>

    <!-- Filters -->
    <BaseCard padding="md" :header-divider="false" data-tour="history-filters" class="mb-6">
      <div class="flex flex-wrap items-center gap-3">
        <!-- Search -->
        <div class="flex-1 min-w-[200px]">
          <div class="relative">
            <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Posts durchsuchen..."
              aria-label="Posts durchsuchen"
              class="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
              @input="debouncedSearch"
            />
          </div>
        </div>

        <!-- Category filter -->
        <select
          v-model="filterCategory"
          @change="fetchPosts"
          aria-label="Kategorie filtern"
          class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1]"
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
          aria-label="Plattform filtern"
          class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1]"
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
          aria-label="Status filtern"
          class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1]"
        >
          <option value="">Alle Status</option>
          <option v-for="s in statuses" :key="s.id" :value="s.id">
            {{ s.label }}
          </option>
        </select>

        <!-- Country filter -->
        <select
          v-model="filterCountry"
          @change="fetchPosts"
          aria-label="Land filtern"
          class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1]"
        >
          <option value="">Alle Laender</option>
          <option v-for="c in countries" :key="c.id" :value="c.id">
            {{ c.flag }} {{ c.label }}
          </option>
        </select>

        <!-- Sort controls -->
        <div class="flex items-center gap-1.5">
          <select
            v-model="sortBy"
            @change="changeSortBy($event.target.value)"
            aria-label="Sortierung"
            class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1]"
          >
            <option v-for="opt in sortOptions" :key="opt.id" :value="opt.id">
              {{ opt.label }}
            </option>
          </select>
          <button
            @click="toggleSortDirection"
            class="p-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:border-[#3B7AB1] hover:text-[#3B7AB1] transition-colors text-sm"
            :title="sortDirection === 'desc' ? 'Absteigend (neueste zuerst)' : 'Aufsteigend (aelteste zuerst)'"
            :aria-label="sortDirection === 'desc' ? 'Absteigend sortieren' : 'Aufsteigend sortieren'"
          >
            {{ sortDirection === 'desc' ? '↓' : '↑' }}
          </button>
        </div>

        <!-- Clear filters -->
        <button
          v-if="activeFilters > 0"
          @click="clearFilters(); fetchPosts()"
          class="text-sm text-[#3B7AB1] hover:text-[#2E6A9E] transition-colors"
        >
          Filter zuruecksetzen ({{ activeFilters }})
        </button>
      </div>

      <!-- Date range filter row -->
      <div class="flex flex-wrap items-center gap-3 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
        <span class="text-sm font-medium text-gray-600 dark:text-gray-400">📅 Zeitraum:</span>

        <!-- Quick presets -->
        <div class="flex gap-1.5">
          <button
            v-for="preset in dateRangePresets"
            :key="preset.days"
            @click="applyDatePreset(preset.days)"
            class="px-2.5 py-1 text-xs rounded-md border transition-colors"
            :class="isPresetActive(preset.days)
              ? 'bg-[#3B7AB1] text-white border-[#3B7AB1]'
              : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-[#3B7AB1] hover:text-[#3B7AB1]'"
          >
            {{ preset.label }}
          </button>
        </div>

        <span class="text-gray-300 dark:text-gray-600">|</span>

        <!-- Custom date inputs -->
        <div class="flex items-center gap-2">
          <label class="text-xs text-gray-500 dark:text-gray-400">Von:</label>
          <input
            v-model="filterDateFrom"
            type="date"
            @change="fetchPosts"
            class="px-2 py-1 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
          />
        </div>
        <div class="flex items-center gap-2">
          <label class="text-xs text-gray-500 dark:text-gray-400">Bis:</label>
          <input
            v-model="filterDateTo"
            type="date"
            @change="fetchPosts"
            class="px-2 py-1 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
          />
        </div>

        <!-- Clear date filter -->
        <button
          v-if="filterDateFrom || filterDateTo"
          @click="clearDateFilter"
          class="text-xs text-gray-400 hover:text-red-500 transition-colors"
          title="Zeitraum-Filter entfernen"
          aria-label="Zeitraum-Filter entfernen"
        >
          ✕
        </button>
      </div>
    </BaseCard>

    <!-- Loading state -->
    <div v-if="loading" class="space-y-4">
      <BaseCard v-for="i in 4" :key="i" padding="md" :header-divider="false">
        <div class="flex items-center gap-4">
          <SkeletonBase width="4rem" height="4rem" rounded="lg" />
          <div class="flex-1 space-y-2">
            <SkeletonBase width="33%" height="1rem" />
            <SkeletonBase width="25%" height="0.75rem" />
          </div>
          <SkeletonBase width="4rem" height="1.5rem" rounded="full" />
        </div>
      </BaseCard>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center" role="alert">
      <p class="text-red-600 dark:text-red-400 mb-3">{{ error }}</p>
      <button
        @click="fetchPosts"
        class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
      >
        Erneut versuchen
      </button>
    </div>

    <!-- Empty state - no posts at all -->
    <EmptyState
      v-else-if="totalPosts === 0 && (!searchQuery || !searchQuery.trim()) && !filterCategory && !filterPlatform && !filterStatus && !filterCountry"
      svgIcon="document-text"
      title="Noch keine Posts erstellt"
      description="Erstelle deinen ersten Social-Media-Post fuer TREFF! Waehle ein Template, schreibe Texte mit KI-Unterstuetzung und plane den Post im Kalender."
      actionLabel="Ersten Post erstellen"
      actionTo="/create/quick"
      secondaryLabel="Zum Wochenplaner"
      secondaryTo="/calendar/week-planner"
    />

    <!-- No results for filter -->
    <EmptyState
      v-else-if="totalPosts === 0"
      svgIcon="magnifying-glass"
      title="Keine Posts gefunden"
      description="Keine Posts passen zu deinen aktuellen Filtern. Setze die Filter zurueck, um alle Posts anzuzeigen."
      actionLabel="Filter zuruecksetzen"
      @action="clearFilters(); fetchPosts()"
    />

    <!-- Posts list -->
    <div v-else data-tour="history-list" class="space-y-3">
      <!-- Results count -->
      <div class="flex items-center justify-between mb-2">
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ totalPosts }} {{ totalPosts === 1 ? 'Post' : 'Posts' }} gefunden
          <span v-if="totalPages > 1" class="ml-1">(Seite {{ currentPage }} von {{ totalPages }})</span>
        </div>
      </div>

      <!-- Post cards -->
      <div
        v-for="post in filteredPosts"
        :key="post.id"
        class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border transition-shadow"
        :class="[
          selectionMode && isPostSelected(post.id)
            ? 'border-[#3B7AB1] bg-blue-50/50 dark:bg-blue-900/10 shadow-md'
            : 'border-gray-200 dark:border-gray-700 hover:shadow-md',
          selectionMode ? 'cursor-pointer' : ''
        ]"
        @click="selectionMode ? togglePostSelection(post.id) : null"
      >
        <div class="flex items-center p-4 gap-4">
          <!-- Selection checkbox -->
          <div v-if="selectionMode" class="flex-shrink-0">
            <input
              type="checkbox"
              :checked="isPostSelected(post.id)"
              @change="togglePostSelection(post.id)"
              class="w-5 h-5 rounded border-gray-300 text-[#3B7AB1] focus:ring-[#3B7AB1] cursor-pointer"
              :aria-label="'Post auswaehlen: ' + (post.title || 'Unbenannter Post')"
            />
          </div>

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
              <!-- Country -->
              <template v-if="post.country">
                <span class="text-gray-300 dark:text-gray-600">|</span>
                <span class="inline-flex items-center gap-1">
                  <span>{{ countryFlag(post.country) }}</span>
                  <span>{{ countryLabel(post.country) }}</span>
                </span>
              </template>
              <!-- Student -->
              <template v-if="post.student_id && getStudentName(post.student_id)">
                <span class="text-gray-300 dark:text-gray-600">|</span>
                <span class="inline-flex items-center gap-1">
                  <span>🎓</span>
                  <span>{{ getStudentName(post.student_id) }}</span>
                </span>
              </template>
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
          <div :data-tour="post === filteredPosts[0] ? 'history-actions' : undefined" class="flex items-center gap-1 flex-shrink-0">
            <button
              v-if="post.status !== 'posted'"
              @click="openScheduleDialog(post)"
              class="p-2 text-gray-400 hover:text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded-lg transition-colors"
              :title="post.status === 'scheduled' || post.status === 'reminded' ? 'Umplanen' : 'Planen'"
              :aria-label="post.status === 'scheduled' || post.status === 'reminded' ? 'Umplanen' : 'Planen'"
            >
              {{ post.status === 'scheduled' || post.status === 'reminded' ? '🔄' : '📅' }}
            </button>
            <button
              v-if="post.status === 'scheduled' || post.status === 'reminded' || post.status === 'exported'"
              @click="markAsPosted(post)"
              class="p-2 text-gray-400 hover:text-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 rounded-lg transition-colors"
              title="Als veroeffentlicht markieren"
              aria-label="Als veroeffentlicht markieren"
            >
              ✅
            </button>
            <button
              @click="duplicatePost(post)"
              :disabled="duplicating === post.id"
              class="p-2 text-gray-400 hover:text-[#3B7AB1] hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Duplizieren"
              aria-label="Duplizieren"
            >
              {{ duplicating === post.id ? '⏳' : '📋' }}
            </button>
            <button
              @click="editPost(post.id)"
              class="p-2 text-gray-400 hover:text-[#3B7AB1] hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title="Bearbeiten"
              aria-label="Bearbeiten"
            >
              ✏️
            </button>
            <button
              @click="confirmDeletePost(post)"
              class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
              title="Loeschen"
              aria-label="Loeschen"
            >
              🗑️
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Content Recycling Hint -->
    <div
      v-if="totalPosts > 0 && !loading && !error"
      data-tour="history-recycling"
      class="bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/30 rounded-xl p-3 mt-4 flex items-center gap-3"
    >
      <span class="text-xl flex-shrink-0">♻️</span>
      <p class="text-xs text-amber-700 dark:text-amber-400">
        <strong>Content-Recycling Tipp:</strong> Dupliziere erfolgreiche Posts und passe sie leicht an — so sparst du Zeit und nutzt bewaehrte Inhalte erneut!
      </p>
    </div>

    <!-- Pagination Controls -->
    <div v-if="totalPages > 1 && !loading && !error" class="flex items-center justify-center gap-2 mt-6">
      <button
        @click="prevPage"
        :disabled="currentPage <= 1"
        class="px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        aria-label="Vorherige Seite"
      >
        &larr; Zurueck
      </button>

      <div class="flex items-center gap-1">
        <template v-for="(pg, idx) in visiblePages" :key="idx">
          <span v-if="pg === '...'" class="px-2 py-1 text-sm text-gray-400 dark:text-gray-500">...</span>
          <button
            v-else
            @click="goToPage(pg)"
            class="w-9 h-9 text-sm rounded-lg border transition-colors"
            :class="pg === currentPage
              ? 'bg-[#3B7AB1] text-white border-[#3B7AB1]'
              : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'"
            :aria-label="'Seite ' + pg"
            :aria-current="pg === currentPage ? 'page' : undefined"
          >
            {{ pg }}
          </button>
        </template>
      </div>

      <button
        @click="nextPage"
        :disabled="currentPage >= totalPages"
        class="px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        aria-label="Naechste Seite"
      >
        Weiter &rarr;
      </button>
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
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-6 break-words">
              Moechtest du den Post <strong class="text-gray-700 dark:text-gray-300 break-all">"{{ postToDelete?.title || 'Unbenannter Post' }}"</strong> wirklich loeschen? Diese Aktion kann nicht rueckgaengig gemacht werden.
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
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ postToSchedule?.status === 'scheduled' || postToSchedule?.status === 'reminded' ? 'Post umplanen' : 'Post planen' }}</h3>
                <p class="text-xs text-gray-500 dark:text-gray-400 break-words">
                  <span class="break-all">"{{ postToSchedule?.title || 'Unbenannter Post' }}"</span>
                </p>
              </div>
            </div>

            <!-- Error message -->
            <div v-if="scheduleError" class="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-600 dark:text-red-400" role="alert">
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
                class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
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
                class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
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
                class="px-4 py-2 bg-[#3B7AB1] text-white rounded-lg hover:bg-[#2E6A9E] transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {{ scheduling ? 'Wird geplant...' : (postToSchedule?.status === 'scheduled' || postToSchedule?.status === 'reminded' ? 'Umplanen' : 'Post planen') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
    <TourSystem ref="tourRef" page-key="history" />
  </div>
</template>
