<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import draggable from 'vuedraggable'
import api from '@/utils/api'
import { useUndoRedo } from '@/composables/useUndoRedo'
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'
import { useToast } from '@/composables/useToast'
import CtaPicker from '@/components/posts/CtaPicker.vue'
import EngagementBoostPanel from '@/components/posts/EngagementBoostPanel.vue'
import CliffhangerPanel from '@/components/posts/CliffhangerPanel.vue'
import RelatedPostsPanel from '@/components/posts/RelatedPostsPanel.vue'
import PostPerformanceInput from '@/components/posts/PostPerformanceInput.vue'
import RepurposePanel from '@/components/pipeline/RepurposePanel.vue'
import VideoRepurposeWizard from '@/components/video/VideoRepurposeWizard.vue'
import { useStudentStore } from '@/stores/students'
import AppIcon from '@/components/icons/AppIcon.vue'
import MultiPlatformExport from '@/components/export/MultiPlatformExport.vue'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const studentStore = useStudentStore()

const postId = computed(() => route.params.id)
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const successMsg = ref('')
const post = ref(null)
const notFound = ref(false)
const slides = ref([])
const currentPreviewSlide = ref(0)
const selectedStudentId = ref(null)

// Repurpose panel modal
const showRepurposePanel = ref(false)

function onRepurposeSaved(result) {
  showRepurposePanel.value = false
  toast.success(`Angepasster Post #${result.post_id} als Draft gespeichert!`, 3000)
}

// Video repurpose wizard modal
const showVideoRepurpose = ref(false)

// Multi-platform export modal
const showMultiPlatformExport = ref(false)

function onMultiExportComplete(results) {
  showMultiPlatformExport.value = false
  toast.success(`${results.length} Plattform-Export(s) abgeschlossen!`, 3000)
}

/** Whether source post is a video/reel type */
const isVideoPost = computed(() => {
  const p = post.value?.platform?.toLowerCase() || ''
  return p.includes('reel') || p.includes('tiktok') || p === 'instagram_reels'
})

function onVideoRepurposeGenerated(result) {
  showVideoRepurpose.value = false
  const count = result.derivative_count || result.derivatives?.length || 0
  toast.success(`${count} Video-Derivat(e) erstellt!`, 3000)
}

// Sibling posts (multi-platform linked posts)
const siblingPosts = ref([])
const linkedGroupId = ref(null)
const showSyncDialog = ref(false)
const syncingToSiblings = ref(false)
const syncFields = ref({
  title: true,
  category: true,
  country: true,
  tone: true,
  scheduled_date: true,
  scheduled_time: true,
  cta_text: true,
  slide_data: true,
})
const syncableFieldLabels = {
  title: 'Titel',
  category: 'Kategorie',
  country: 'Land',
  tone: 'Tonalität',
  scheduled_date: 'Datum',
  scheduled_time: 'Uhrzeit',
  cta_text: 'Call-to-Action',
  slide_data: 'Slide-Inhalte',
}

async function syncToSiblings() {
  if (!post.value || siblingPosts.value.length === 0) return
  syncingToSiblings.value = true
  try {
    const fieldsToSync = {}
    for (const [field, selected] of Object.entries(syncFields.value)) {
      if (selected && post.value[field] !== undefined) {
        fieldsToSync[field] = post.value[field]
      }
    }
    if (fieldsToSync.slide_data) {
      fieldsToSync.slide_data = JSON.stringify(slides.value.map(({ dragId, ...rest }) => rest))
    }
    if (fieldsToSync.cta_text !== undefined) fieldsToSync.cta_text = ctaText.value
    if (fieldsToSync.title !== undefined) fieldsToSync.title = slides.value[0]?.headline || post.value.title

    await api.put('/api/posts/sync-siblings', {
      source_post_id: Number(postId.value),
      fields: fieldsToSync,
    })
    toast.success(`Änderungen auf ${siblingPosts.value.length} Schwester-Post(s) übertragen!`, 3000)
    showSyncDialog.value = false
  } catch (e) {
    toast.error('Sync fehlgeschlagen: ' + (e.response?.data?.detail || e.message), 4000)
  } finally {
    syncingToSiblings.value = false
  }
}

// Editable caption/hashtag fields
const captionInstagram = ref('')
const captionTiktok = ref('')
const hashtagsInstagram = ref('')
const hashtagsTiktok = ref('')
const ctaText = ref('')

// ── Story-Arc / Episode integration ─────────────────────────────────────
const episodeData = ref(null) // The loaded StoryEpisode object
const storyArc = ref(null) // The parent StoryArc
const arcEpisodes = ref([]) // All episodes in the arc
const episodePreviouslyText = ref('')
const episodeCliffhangerText = ref('')
const episodeNextHint = ref('')
const suggestingEpisodeField = ref('')
const loadingEpisode = ref(false)

// Computed: whether this post is part of a story arc
const isEpisodePost = computed(() => !!post.value?.story_arc_id)

async function loadEpisodeData() {
  if (!post.value?.story_arc_id) return
  loadingEpisode.value = true
  try {
    // Load the story arc
    const arcRes = await api.get(`/api/story-arcs/${post.value.story_arc_id}`)
    storyArc.value = arcRes.data

    // Load all episodes in this arc
    const epsRes = await api.get(`/api/story-arcs/${post.value.story_arc_id}/episodes`)
    arcEpisodes.value = epsRes.data || []

    // Find the episode linked to this post
    const ep = arcEpisodes.value.find(e => e.post_id === Number(postId.value))
    if (ep) {
      episodeData.value = ep
      episodePreviouslyText.value = ep.previously_text || ''
      episodeCliffhangerText.value = ep.cliffhanger_text || ''
      episodeNextHint.value = ep.next_episode_hint || ''
    }
  } catch (err) {
    console.error('Failed to load episode data:', err)
  } finally {
    loadingEpisode.value = false
  }
}

async function suggestEpisodeText(field) {
  if (suggestingEpisodeField.value) return
  suggestingEpisodeField.value = field
  try {
    const response = await api.post('/api/ai/suggest-episode-text', {
      arc_id: post.value.story_arc_id,
      episode_number: episodeData.value?.episode_number || post.value.episode_number || 1,
      field,
      topic: post.value?.title || '',
      tone: post.value?.tone || 'jugendlich',
    })
    if (response.data?.suggestion) {
      if (field === 'previously_text') episodePreviouslyText.value = response.data.suggestion
      else if (field === 'cliffhanger_text') episodeCliffhangerText.value = response.data.suggestion
      else if (field === 'next_episode_hint') episodeNextHint.value = response.data.suggestion
      toast.success('Vorschlag generiert!', 2000)
    }
  } catch (err) {
    toast.error('Vorschlag fehlgeschlagen: ' + (err.response?.data?.detail || err.message), 4000)
  } finally {
    suggestingEpisodeField.value = ''
  }
}

async function saveEpisodeData() {
  if (!episodeData.value || !post.value?.story_arc_id) return
  try {
    const updateData = {
      episode_title: episodeData.value.episode_title,
      post_id: Number(postId.value),
      episode_number: episodeData.value.episode_number,
      previously_text: episodePreviouslyText.value || null,
      cliffhanger_text: episodeCliffhangerText.value || null,
      next_episode_hint: episodeNextHint.value || null,
      status: episodeData.value.status,
    }
    await api.put(`/api/story-arcs/${post.value.story_arc_id}/episodes/${episodeData.value.id}`, updateData)
  } catch (err) {
    console.error('Episode save failed:', err)
    toast.error('Episode-Daten konnten nicht gespeichert werden', 4000)
  }
}

// Cliffhanger generation callback
function onCliffhangerGenerated(data) {
  if (data.cliffhanger_text) {
    episodeCliffhangerText.value = data.cliffhanger_text
  }
  if (data.teaser_text) {
    episodeNextHint.value = data.teaser_text
  }
  toast.success('Cliffhanger & Teaser generiert!', 2500)
}

// Categories for display
const categories = [
  { id: 'laender_spotlight', label: 'Länder-Spotlight', icon: 'globe-alt' },
  { id: 'erfahrungsberichte', label: 'Erfahrungsberichte', icon: 'chat-bubble-left-right' },
  { id: 'infografiken', label: 'Infografiken', icon: 'chart-bar' },
  { id: 'fristen_cta', label: 'Fristen & CTA', icon: 'clock' },
  { id: 'tipps_tricks', label: 'Tipps & Tricks', icon: 'light-bulb' },
  { id: 'faq', label: 'FAQ', icon: 'question-mark-circle' },
  { id: 'foto_posts', label: 'Foto-Posts', icon: 'camera' },
  { id: 'reel_tiktok_thumbnails', label: 'Reel/TikTok', icon: 'film' },
  { id: 'story_posts', label: 'Story-Posts', icon: 'device-phone-mobile' },
]

const categoryObj = computed(() => categories.find(c => c.id === post.value?.category))

// ── Engagement Boost Panel ────────────────────────────────────────────
const engagementBoostPostContent = computed(() => ({
  slides: slides.value,
  caption_instagram: captionInstagram.value,
  caption_tiktok: captionTiktok.value,
  hashtags_instagram: hashtagsInstagram.value,
  hashtags_tiktok: hashtagsTiktok.value,
  cta_text: ctaText.value,
  category: post.value?.category || '',
  country: post.value?.country || '',
  tone: post.value?.tone || '',
}))

function onApplyEngagementSuggestion(suggestion) {
  // Show feedback with the suggestion - user can manually apply it
  successMsg.value = `Vorschlag: ${suggestion.action_text} — ${suggestion.suggestion.slice(0, 80)}...`
  setTimeout(() => { successMsg.value = '' }, 5000)
}

// ── Undo / Redo ────────────────────────────────────────────────────────
function getEditableState() {
  return {
    slides: JSON.parse(JSON.stringify(slides.value)),
    captionInstagram: captionInstagram.value,
    captionTiktok: captionTiktok.value,
    hashtagsInstagram: hashtagsInstagram.value,
    hashtagsTiktok: hashtagsTiktok.value,
    ctaText: ctaText.value,
  }
}

function applyEditableState(state) {
  slides.value = state.slides
  captionInstagram.value = state.captionInstagram
  captionTiktok.value = state.captionTiktok
  hashtagsInstagram.value = state.hashtagsInstagram
  hashtagsTiktok.value = state.hashtagsTiktok
  ctaText.value = state.ctaText
  ensureDragIds()
}

const { canUndo, canRedo, undo, redo, snapshot, initFromState, startListening, stopListening, isApplying } = useUndoRedo(applyEditableState)

// Debounced snapshot on content changes
let snapshotTimer = null
function debouncedSnapshot() {
  if (isApplying.value) return
  clearTimeout(snapshotTimer)
  snapshotTimer = setTimeout(() => {
    snapshot(getEditableState())
  }, 500)
}

// Watch all editable fields for changes and record snapshots
watch(
  () => [
    JSON.stringify(slides.value),
    captionInstagram.value,
    captionTiktok.value,
    hashtagsInstagram.value,
    hashtagsTiktok.value,
    ctaText.value,
  ],
  () => {
    debouncedSnapshot()
  },
  { deep: false }
)

// Drag IDs for vuedraggable
let dragIdCounter = 0
function ensureDragIds() {
  for (const slide of slides.value) {
    if (!slide.dragId) {
      slide.dragId = `edit-slide-${++dragIdCounter}`
    }
  }
}

function onSlideReorder() {
  currentPreviewSlide.value = 0
  ensureDragIds()
}

// ── Add / Remove slide ─────────────────────────────────────────────────
const showDeleteSlideConfirm = ref(false)
const slideToDeleteIndex = ref(-1)

function addSlide() {
  const newSlide = {
    headline: 'Neue Slide',
    subheadline: '',
    body_text: '',
    cta_text: '',
    background_type: 'color',
    background_value: '#3B7AB1',
  }
  slides.value.push(newSlide)
  ensureDragIds()
  currentPreviewSlide.value = slides.value.length - 1
}

function requestRemoveSlide(index) {
  if (slides.value.length <= 1) return
  slideToDeleteIndex.value = index
  showDeleteSlideConfirm.value = true
}

function confirmRemoveSlide() {
  if (slideToDeleteIndex.value < 0 || slideToDeleteIndex.value >= slides.value.length) return
  slides.value.splice(slideToDeleteIndex.value, 1)
  if (currentPreviewSlide.value >= slides.value.length) {
    currentPreviewSlide.value = slides.value.length - 1
  }
  ensureDragIds()
  showDeleteSlideConfirm.value = false
  slideToDeleteIndex.value = -1
}

function cancelRemoveSlide() {
  showDeleteSlideConfirm.value = false
  slideToDeleteIndex.value = -1
}

async function loadPost() {
  loading.value = true
  error.value = ''

  // Validate that the post ID is a positive integer
  const idNum = Number(postId.value)
  if (!postId.value || !Number.isInteger(idNum) || idNum <= 0) {
    notFound.value = true
    loading.value = false
    return
  }

  try {
    const response = await api.get(`/api/posts/${postId.value}`)
    post.value = response.data

    // Parse slide_data JSON
    try {
      const parsed = JSON.parse(response.data.slide_data || '[]')
      slides.value = Array.isArray(parsed) ? parsed.map(s => ({
        background_type: 'color',
        background_value: '#1A1A2E',
        ...s,
      })) : []
    } catch {
      slides.value = []
    }

    ensureDragIds()

    // Set caption/hashtag fields
    captionInstagram.value = response.data.caption_instagram || ''
    captionTiktok.value = response.data.caption_tiktok || ''
    hashtagsInstagram.value = response.data.hashtags_instagram || ''
    hashtagsTiktok.value = response.data.hashtags_tiktok || ''
    ctaText.value = response.data.cta_text || ''
    selectedStudentId.value = response.data.student_id || null

    // Initialize undo/redo history with loaded state
    initFromState(getEditableState())

    // Capture initial state for unsaved changes detection (without dragId)
    initialStateSnapshot.value = getCleanState()

    // Fetch sibling posts if part of a linked group
    if (response.data.linked_post_group_id) {
      linkedGroupId.value = response.data.linked_post_group_id
      try {
        const sibRes = await api.get(`/api/posts/${postId.value}/siblings`)
        siblingPosts.value = sibRes.data.siblings || []
      } catch {
        siblingPosts.value = []
      }
    }

    // Load episode data if post is part of a story arc
    if (response.data.story_arc_id) {
      await loadEpisodeData()
    }
  } catch (e) {
    if (e.response?.status === 404 || e.response?.status === 422) {
      notFound.value = true
    } else {
      error.value = 'Fehler beim Laden: ' + (e.response?.data?.detail || e.message)
    }
  } finally {
    loading.value = false
  }
}

async function savePost() {
  saving.value = true
  error.value = ''
  try {
    // Clean slides: remove dragId before saving
    const cleanSlides = slides.value.map(({ dragId, ...rest }) => rest)

    const updateData = {
      slide_data: JSON.stringify(cleanSlides),
      caption_instagram: captionInstagram.value,
      caption_tiktok: captionTiktok.value,
      hashtags_instagram: hashtagsInstagram.value,
      hashtags_tiktok: hashtagsTiktok.value,
      cta_text: ctaText.value,
      title: cleanSlides[0]?.headline || post.value?.title || 'Post',
      student_id: selectedStudentId.value || null,
    }

    await api.put(`/api/posts/${postId.value}`, updateData)

    // Save episode data if post is part of a story arc
    if (isEpisodePost.value && episodeData.value) {
      await saveEpisodeData()
    }

    // Update initial state snapshot (form is now clean after save)
    initialStateSnapshot.value = getCleanState()

    successMsg.value = 'Post gespeichert!'
    setTimeout(() => { successMsg.value = '' }, 3000)
  } catch (e) {
    error.value = 'Speichern fehlgeschlagen: ' + (e.response?.data?.detail || e.message)
  } finally {
    saving.value = false
  }
}

function nextPreviewSlide() {
  if (currentPreviewSlide.value < slides.value.length - 1) currentPreviewSlide.value++
}
function prevPreviewSlide() {
  if (currentPreviewSlide.value > 0) currentPreviewSlide.value--
}

// ── Ctrl+S keyboard shortcut to save ─────────────────────────────────
function handleCtrlS(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    e.stopPropagation()
    if (!saving.value && post.value) {
      savePost()
    }
  }
}

onMounted(async () => {
  await loadPost()
  startListening()
  studentStore.fetchStudents()
  window.addEventListener('keydown', handleCtrlS, true)
  // Auto-open repurpose panel if ?repurpose=true query param is present
  if (route.query.repurpose === 'true' && post.value) {
    showRepurposePanel.value = true
  }
})

onUnmounted(() => {
  stopListening()
  clearTimeout(snapshotTimer)
  window.removeEventListener('keydown', handleCtrlS, true)
})

// ── Unsaved changes warning ───────────────────────────────────────────
const initialStateSnapshot = ref(null)

function getCleanState() {
  // Get editable state without dragId (for comparison only)
  const state = getEditableState()
  state.slides = state.slides.map(({ dragId, ...rest }) => rest)
  return JSON.stringify(state)
}

const { showLeaveDialog, confirmLeave, cancelLeave, markClean } = useUnsavedChanges(() => {
  // Not dirty until initial state is loaded
  if (!initialStateSnapshot.value) return false
  // Compare current state to initial (ignoring dragId which is transient)
  return getCleanState() !== initialStateSnapshot.value
})
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <button
          @click="router.push('/library/history')"
          class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          &#8592; Zurück
        </button>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Post bearbeiten
          <span v-if="post" class="text-base font-normal text-gray-500 dark:text-gray-400">#{{ post.id }}</span>
        </h1>
      </div>
      <div v-if="post" class="flex gap-2">
        <!-- Multi-Platform Export button -->
        <button
          @click="showMultiPlatformExport = true"
          class="px-3 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 border border-[#3B7AB1] dark:border-[#3B7AB1]/60 text-[#3B7AB1] dark:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20"
          title="Alle Plattform-Formate exportieren"
          data-testid="multi-platform-export-btn"
        >
          <AppIcon name="export" class="w-4 h-4 inline-block" /> Alle Formate
        </button>
        <!-- Repurpose button -->
        <button
          @click="showRepurposePanel = true"
          class="px-3 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 border border-purple-300 dark:border-purple-600 text-purple-700 dark:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/20"
          title="Für andere Plattform anpassen"
          data-testid="repurpose-btn"
        >
          <AppIcon name="arrow-path" class="w-4 h-4 inline-block" /> Anpassen
        </button>
        <!-- Video Repurpose button (only for Reels/TikTok posts) -->
        <button
          v-if="isVideoPost"
          @click="showVideoRepurpose = true"
          class="px-3 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 border border-pink-300 dark:border-pink-600 text-pink-700 dark:text-pink-300 hover:bg-pink-50 dark:hover:bg-pink-900/20"
          title="Video in alle Formate umwandeln"
          data-testid="video-repurpose-btn"
        >
          <AppIcon name="video-camera" class="w-4 h-4 inline-block" /> Video-Pipeline
        </button>
        <!-- Undo / Redo buttons -->
        <button
          @click="undo"
          :disabled="!canUndo"
          class="px-3 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 border"
          :class="canUndo
            ? 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
            : 'border-gray-200 dark:border-gray-700 text-gray-300 dark:text-gray-600 cursor-not-allowed'"
          title="Rueckgaengig (Ctrl+Z)"
          data-testid="undo-btn"
        >
          &#8630; Undo
        </button>
        <button
          @click="redo"
          :disabled="!canRedo"
          class="px-3 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 border"
          :class="canRedo
            ? 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
            : 'border-gray-200 dark:border-gray-700 text-gray-300 dark:text-gray-600 cursor-not-allowed'"
          title="Wiederherstellen (Ctrl+Y)"
          data-testid="redo-btn"
        >
          Redo &#8631;
        </button>
        <button
          @click="savePost"
          :disabled="saving"
          class="px-5 py-2.5 bg-[#3B7AB1] hover:bg-[#2E6A9E] disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
        >
          <span v-if="saving" class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
          {{ saving ? 'Speichern...' : 'Speichern' }}
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div v-if="error" class="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300 flex items-center gap-2" role="alert">
      <span>&#9888;</span> {{ error }}
      <button @click="error = ''" class="ml-auto text-red-500 hover:text-red-700">&times;</button>
    </div>
    <div v-if="successMsg" class="mb-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-green-700 dark:text-green-300 flex items-center gap-2">
      <span>&#10003;</span> {{ successMsg }}
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="animate-spin h-10 w-10 border-4 border-[#3B7AB1] border-t-transparent rounded-full"></div>
    </div>

    <!-- Post Editor -->
    <div v-else-if="post" class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Left: Edit panel -->
      <div class="space-y-4">
        <!-- Post info bar -->
        <div class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg text-sm text-gray-600 dark:text-gray-400">
          <span v-if="categoryObj" class="flex items-center gap-1"><AppIcon :name="categoryObj.icon" class="w-4 h-4 inline-block" /> {{ categoryObj.label }}</span>
          <span>&middot;</span>
          <span>{{ post.platform }}</span>
          <span v-if="post.country">&middot; {{ post.country }}</span>
          <span>&middot;</span>
          <span class="px-2 py-0.5 rounded text-xs font-medium"
            :class="{
              'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300': post.status === 'draft',
              'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300': post.status === 'scheduled',
              'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300': post.status === 'posted',
            }"
          >{{ post.status }}</span>
        </div>

        <!-- Linked sibling posts (multi-platform) -->
        <div v-if="siblingPosts.length > 0" class="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <AppIcon name="link" class="w-4 h-4 inline-block" />
              <span class="text-sm font-semibold text-blue-700 dark:text-blue-300">Verknuepfte Plattform-Posts</span>
            </div>
            <button
              @click="showSyncDialog = true"
              class="px-3 py-1 text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-1.5"
              data-testid="sync-siblings-btn"
            >
              <AppIcon name="arrow-path" class="w-3 h-3 inline-block" /> Synchronisieren
            </button>
          </div>
          <div class="flex flex-wrap gap-2">
            <router-link
              v-for="sib in siblingPosts"
              :key="sib.id"
              :to="`/create/post/${sib.id}/edit`"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
              :class="{
                'bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300 hover:bg-pink-200 dark:hover:bg-pink-900/50': sib.platform === 'instagram_feed',
                'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 hover:bg-purple-200 dark:hover:bg-purple-900/50': sib.platform === 'instagram_story',
                'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300 hover:bg-cyan-200 dark:hover:bg-cyan-900/50': sib.platform === 'tiktok',
              }"
            >
              <AppIcon v-if="sib.platform === 'instagram_feed'" name="camera" class="w-4 h-4 inline-block" />
              <AppIcon v-else-if="sib.platform === 'instagram_story'" name="device-phone-mobile" class="w-4 h-4 inline-block" />
              <AppIcon v-else-if="sib.platform === 'tiktok'" name="musical-note" class="w-4 h-4 inline-block" />
              {{ sib.platform === 'instagram_feed' ? 'IG Feed' : sib.platform === 'instagram_story' ? 'IG Story' : 'TikTok' }}
              <span class="opacity-60">#{{ sib.id }}</span>
            </router-link>
          </div>
          <p class="mt-1.5 text-[10px] text-blue-500 dark:text-blue-400">
            Änderungen an diesem Post können auf die Schwester-Posts synchronisiert werden.
          </p>
        </div>

        <!-- Sync to Siblings Dialog (Overlay) -->
        <div v-if="showSyncDialog" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showSyncDialog = false">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 max-w-md w-full mx-4 border border-gray-200 dark:border-gray-700">
            <div class="flex items-center gap-3 mb-4">
              <AppIcon name="arrow-path" class="w-6 h-6 inline-block" />
              <h3 class="text-lg font-bold text-gray-900 dark:text-white">Änderungen synchronisieren</h3>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Wähle aus, welche Felder auf die <strong>{{ siblingPosts.length }} Schwester-Post(s)</strong> übertragen werden sollen:
            </p>
            <div class="flex flex-wrap gap-1.5 mb-4">
              <span
                v-for="sib in siblingPosts"
                :key="'sync-target-' + sib.id"
                class="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium"
                :class="{
                  'bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300': sib.platform === 'instagram_feed',
                  'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300': sib.platform === 'instagram_story',
                  'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300': sib.platform === 'tiktok',
                }"
              >
                <AppIcon :name="sib.platform === 'instagram_feed' ? 'camera' : sib.platform === 'instagram_story' ? 'device-phone-mobile' : 'musical-note'" class="w-3 h-3 inline-block" /> {{ sib.platform === 'instagram_feed' ? 'IG Feed' : sib.platform === 'instagram_story' ? 'IG Story' : 'TikTok' }}
                #{{ sib.id }}
              </span>
            </div>
            <div class="space-y-2 mb-5">
              <label
                v-for="(label, field) in syncableFieldLabels"
                :key="'sync-field-' + field"
                class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/30 cursor-pointer transition-colors"
              >
                <input
                  type="checkbox"
                  v-model="syncFields[field]"
                  class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span class="text-sm text-gray-700 dark:text-gray-300">{{ label }}</span>
              </label>
            </div>
            <div class="flex gap-3">
              <button
                @click="showSyncDialog = false"
                class="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Abbrechen
              </button>
              <button
                @click="syncToSiblings"
                :disabled="syncingToSiblings || !Object.values(syncFields).some(v => v)"
                class="flex-1 px-4 py-2.5 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 rounded-lg transition-colors flex items-center justify-center gap-2"
                data-testid="confirm-sync-btn"
              >
                <span v-if="syncingToSiblings" class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                {{ syncingToSiblings ? 'Synchronisiere...' : 'Synchronisieren' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Story-Arc / Episode fields (shown when post is part of a series) -->
        <div v-if="isEpisodePost" class="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl space-y-4" data-testid="episode-fields">
          <h4 class="font-bold text-[#3B7AB1] text-sm flex items-center gap-2">
            &#128214; Episoden-Details
            <span v-if="loadingEpisode" class="animate-spin h-4 w-4 border-2 border-[#3B7AB1] border-t-transparent rounded-full"></span>
            <span v-if="storyArc" class="text-xs font-normal text-gray-500 dark:text-gray-400">
              &mdash; {{ storyArc.title }}
            </span>
          </h4>

          <!-- Episode info -->
          <div v-if="episodeData" class="flex items-center gap-3 text-xs text-gray-600 dark:text-gray-400">
            <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-[#3B7AB1] text-white font-bold text-xs">
              E{{ episodeData.episode_number }}
            </span>
            <span>{{ episodeData.episode_title }}</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-medium"
              :class="{
                'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300': episodeData.status === 'planned',
                'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300': episodeData.status === 'draft',
                'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300': episodeData.status === 'published',
              }"
            >{{ episodeData.status }}</span>
          </div>

          <!-- Previously Text (Rueckblick) -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="block text-xs font-medium text-gray-700 dark:text-gray-300">Rueckblick ("Bisher bei...")</label>
              <button
                @click="suggestEpisodeText('previously_text')"
                :disabled="suggestingEpisodeField === 'previously_text'"
                class="text-xs text-[#3B7AB1] hover:text-[#2E6A9E] font-medium transition-colors disabled:opacity-50"
                data-testid="suggest-previously-btn"
              >
                <span v-if="suggestingEpisodeField === 'previously_text'" class="animate-spin inline-block h-3 w-3 border-2 border-[#3B7AB1] border-t-transparent rounded-full mr-1"></span>
                &#10024; KI-Vorschlag
              </button>
            </div>
            <textarea
              v-model="episodePreviouslyText"
              rows="2"
              placeholder="z.B. Bisher bei Jonathan: Nach der Ankunft in Seattle hat Jonathan seine Gastfamilie kennengelernt..."
              class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
              data-testid="previously-text-input"
            ></textarea>
          </div>

          <!-- Cliffhanger Text -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="block text-xs font-medium text-gray-700 dark:text-gray-300">Cliffhanger (Ende der Episode)</label>
              <button
                @click="suggestEpisodeText('cliffhanger_text')"
                :disabled="suggestingEpisodeField === 'cliffhanger_text'"
                class="text-xs text-[#3B7AB1] hover:text-[#2E6A9E] font-medium transition-colors disabled:opacity-50"
                data-testid="suggest-cliffhanger-btn"
              >
                <span v-if="suggestingEpisodeField === 'cliffhanger_text'" class="animate-spin inline-block h-3 w-3 border-2 border-[#3B7AB1] border-t-transparent rounded-full mr-1"></span>
                &#10024; KI-Vorschlag
              </button>
            </div>
            <textarea
              v-model="episodeCliffhangerText"
              rows="2"
              placeholder="z.B. Aber was Jonathan am nächsten Tag erlebt, hätte niemand erwartet..."
              class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
              data-testid="cliffhanger-text-input"
            ></textarea>
          </div>

          <!-- Next Episode Hint (Teaser) -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="block text-xs font-medium text-gray-700 dark:text-gray-300">Teaser (nächste Episode)</label>
              <button
                @click="suggestEpisodeText('next_episode_hint')"
                :disabled="suggestingEpisodeField === 'next_episode_hint'"
                class="text-xs text-[#3B7AB1] hover:text-[#2E6A9E] font-medium transition-colors disabled:opacity-50"
                data-testid="suggest-nexthint-btn"
              >
                <span v-if="suggestingEpisodeField === 'next_episode_hint'" class="animate-spin inline-block h-3 w-3 border-2 border-[#3B7AB1] border-t-transparent rounded-full mr-1"></span>
                &#10024; KI-Vorschlag
              </button>
            </div>
            <textarea
              v-model="episodeNextHint"
              rows="2"
              placeholder="z.B. Nächste Episode: Jonathan entdeckt eine völlig neue Seite von Amerika!"
              class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
              data-testid="nexthint-text-input"
            ></textarea>
          </div>

          <!-- Other episodes in arc -->
          <div v-if="arcEpisodes.length > 1">
            <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Alle Episoden in "{{ storyArc?.title }}":</label>
            <div class="space-y-1">
              <div v-for="ep in arcEpisodes" :key="ep.id" class="text-xs flex items-center gap-2"
                :class="ep.post_id === Number(postId) ? 'text-[#3B7AB1] font-semibold' : 'text-gray-500 dark:text-gray-400'"
              >
                <span class="inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold"
                  :class="ep.post_id === Number(postId) ? 'bg-[#3B7AB1] text-white' : 'bg-[#3B7AB1]/20 text-[#3B7AB1]'"
                >{{ ep.episode_number }}</span>
                <span>{{ ep.episode_title }}</span>
                <span v-if="ep.post_id === Number(postId)" class="text-[10px]">(dieser Post)</span>
                <router-link v-else-if="ep.post_id" :to="`/create/post/${ep.post_id}/edit`" class="text-[10px] text-[#3B7AB1] hover:underline">bearbeiten</router-link>
              </div>
            </div>
          </div>
        </div>

        <!-- Cliffhanger & Teaser System (when post is part of a Story-Arc) -->
        <CliffhangerPanel
          v-if="isEpisodePost && storyArc"
          :arc-id="post.story_arc_id"
          :episode-number="episodeData?.episode_number || post.episode_number || 1"
          :planned-episodes="storyArc.planned_episodes || 8"
          :episode-content="post.topic || slides[0]?.headline || ''"
          :initial-cliffhanger="episodeCliffhangerText"
          :initial-teaser="episodeNextHint"
          @update:cliffhanger="episodeCliffhangerText = $event"
          @update:teaser="episodeNextHint = $event"
          @generated="onCliffhangerGenerated"
        />

        <!-- Slide tabs with drag-and-drop reordering + Add/Remove -->
        <div v-if="slides.length >= 1" class="mb-1">
          <div class="flex items-center justify-between mb-2">
            <span v-if="slides.length > 1" class="text-xs text-gray-500 dark:text-gray-400">&#8597; Slides per Drag &amp; Drop neu anordnen</span>
            <span v-else class="text-xs text-gray-500 dark:text-gray-400">{{ slides.length }} Slide</span>
            <span class="text-xs text-gray-400 dark:text-gray-500">{{ slides.length }} Slides</span>
          </div>
          <div class="flex items-center gap-2 flex-wrap">
            <draggable
              v-model="slides"
              item-key="dragId"
              handle=".drag-handle"
              animation="200"
              ghost-class="slide-ghost"
              class="flex gap-1 flex-wrap"
              @end="onSlideReorder"
            >
              <template #item="{ element, index }">
                <button
                  @click="currentPreviewSlide = index"
                  class="px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 drag-handle cursor-grab active:cursor-grabbing"
                  :class="currentPreviewSlide === index
                    ? 'bg-[#3B7AB1] text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'"
                >
                  <span class="opacity-50">&#10495;</span>
                  Slide {{ index + 1 }}
                  <span v-if="index === 0" class="font-normal">(Cover)</span>
                  <span v-if="index === slides.length - 1 && index > 0" class="font-normal">(CTA)</span>
                </button>
              </template>
            </draggable>
            <!-- Add Slide button -->
            <button
              @click="addSlide"
              class="px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 border-2 border-dashed border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-[#3B7AB1] hover:text-[#3B7AB1] dark:hover:border-[#3B7AB1] dark:hover:text-[#3B7AB1]"
              title="Neue Slide hinzufuegen"
              data-testid="add-slide-btn"
            >
              <span>+</span> Slide
            </button>
          </div>
        </div>

        <!-- Current slide edit -->
        <div v-if="slides[currentPreviewSlide]" class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 space-y-3">
          <!-- Slide header with delete button -->
          <div class="flex items-center justify-between pb-2 border-b border-gray-100 dark:border-gray-700">
            <span class="text-sm font-semibold text-gray-700 dark:text-gray-300">
              Slide {{ currentPreviewSlide + 1 }}
              <span v-if="currentPreviewSlide === 0" class="text-xs font-normal text-gray-400">(Cover)</span>
              <span v-if="currentPreviewSlide === slides.length - 1 && currentPreviewSlide > 0" class="text-xs font-normal text-gray-400">(CTA)</span>
            </span>
            <button
              v-if="slides.length > 1"
              @click="requestRemoveSlide(currentPreviewSlide)"
              class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              title="Slide entfernen"
              data-testid="remove-slide-btn"
            >
              &#128465; Entfernen
            </button>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Headline</label>
            <input
              v-model="slides[currentPreviewSlide].headline"
              class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
              :class="(slides[currentPreviewSlide].headline?.length || 0) > 40 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white' : (slides[currentPreviewSlide].headline?.length || 0) > 30 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-gray-900 dark:text-white' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white'"
            />
            <div class="flex items-center justify-between mt-0.5">
              <span v-if="(slides[currentPreviewSlide].headline?.length || 0) > 40" class="text-xs text-red-500 dark:text-red-400">Text kann den Template-Bereich überlaufen</span>
              <span v-else-if="(slides[currentPreviewSlide].headline?.length || 0) > 30" class="text-xs text-amber-500 dark:text-amber-400">Nahe am Zeichenlimit</span>
              <span v-else class="text-xs text-gray-400"></span>
              <span class="text-xs" :class="(slides[currentPreviewSlide].headline?.length || 0) > 40 ? 'text-red-500 dark:text-red-400 font-semibold' : (slides[currentPreviewSlide].headline?.length || 0) > 30 ? 'text-amber-500 dark:text-amber-400' : 'text-gray-400'">{{ slides[currentPreviewSlide].headline?.length || 0 }}/40</span>
            </div>
          </div>
          <div v-if="slides[currentPreviewSlide].subheadline !== undefined">
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Subheadline</label>
            <input
              v-model="slides[currentPreviewSlide].subheadline"
              class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
              :class="(slides[currentPreviewSlide].subheadline?.length || 0) > 60 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white' : (slides[currentPreviewSlide].subheadline?.length || 0) > 45 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-gray-900 dark:text-white' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white'"
            />
            <div class="flex items-center justify-between mt-0.5">
              <span v-if="(slides[currentPreviewSlide].subheadline?.length || 0) > 60" class="text-xs text-red-500 dark:text-red-400">Text kann den Template-Bereich überlaufen</span>
              <span v-else-if="(slides[currentPreviewSlide].subheadline?.length || 0) > 45" class="text-xs text-amber-500 dark:text-amber-400">Nahe am Zeichenlimit</span>
              <span v-else class="text-xs text-gray-400"></span>
              <span class="text-xs" :class="(slides[currentPreviewSlide].subheadline?.length || 0) > 60 ? 'text-red-500 dark:text-red-400 font-semibold' : (slides[currentPreviewSlide].subheadline?.length || 0) > 45 ? 'text-amber-500 dark:text-amber-400' : 'text-gray-400'">{{ slides[currentPreviewSlide].subheadline?.length || 0 }}/60</span>
            </div>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Text</label>
            <textarea
              v-model="slides[currentPreviewSlide].body_text"
              rows="3"
              class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent resize-none"
              :class="(slides[currentPreviewSlide].body_text?.length || 0) > 200 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white' : (slides[currentPreviewSlide].body_text?.length || 0) > 150 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-gray-900 dark:text-white' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white'"
            ></textarea>
            <div class="flex items-center justify-between mt-0.5">
              <span v-if="(slides[currentPreviewSlide].body_text?.length || 0) > 200" class="text-xs text-red-500 dark:text-red-400">Text kann den Template-Bereich überlaufen</span>
              <span v-else-if="(slides[currentPreviewSlide].body_text?.length || 0) > 150" class="text-xs text-amber-500 dark:text-amber-400">Nahe am Zeichenlimit</span>
              <span v-else class="text-xs text-gray-400"></span>
              <span class="text-xs" :class="(slides[currentPreviewSlide].body_text?.length || 0) > 200 ? 'text-red-500 dark:text-red-400 font-semibold' : (slides[currentPreviewSlide].body_text?.length || 0) > 150 ? 'text-amber-500 dark:text-amber-400' : 'text-gray-400'">{{ slides[currentPreviewSlide].body_text?.length || 0 }}/200</span>
            </div>
          </div>
          <div v-if="slides[currentPreviewSlide]?.cta_text !== undefined">
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">CTA-Bibliothek</label>
            <CtaPicker
              v-model="slides[currentPreviewSlide].cta_text"
              :category="post?.category || ''"
              :platform="post?.platform || ''"
              :topic="post?.title || ''"
            />
          </div>
        </div>

        <!-- Background Color Picker -->
        <div v-if="slides[currentPreviewSlide]?.background_type !== 'image'" class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Hintergrundfarbe</label>
          <div class="flex items-center gap-3">
            <div class="flex gap-1.5 flex-wrap">
              <button
                v-for="preset in ['#1A1A2E', '#3B7AB1', '#FDD000', '#2D6A4F', '#E63946', '#7B2CBF', '#FF6B35', '#264653']"
                :key="preset"
                @click="slides[currentPreviewSlide].background_value = preset; slides[currentPreviewSlide].background_type = 'color'"
                class="w-7 h-7 rounded-lg border-2 transition-all hover:scale-110"
                :class="slides[currentPreviewSlide].background_value === preset ? 'border-white ring-2 ring-[#3B7AB1] scale-110' : 'border-gray-300 dark:border-gray-600'"
                :style="{ backgroundColor: preset }"
                :title="preset"
                data-testid="color-preset"
              ></button>
            </div>
            <div class="flex items-center gap-2 ml-auto">
              <input
                type="color"
                :value="slides[currentPreviewSlide].background_value || '#1A1A2E'"
                @input="slides[currentPreviewSlide].background_value = $event.target.value; slides[currentPreviewSlide].background_type = 'color'"
                class="w-8 h-8 rounded cursor-pointer border border-gray-300 dark:border-gray-600"
                title="Eigene Farbe wählen"
                data-testid="color-picker-input"
              />
              <span class="text-xs text-gray-400 font-mono">{{ slides[currentPreviewSlide].background_value || '#1A1A2E' }}</span>
            </div>
          </div>
        </div>
        <div v-else class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Hintergrund</label>
          <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <span>&#x1F5BC;</span>
            <span>Bild als Hintergrund gesetzt</span>
            <button
              @click="slides[currentPreviewSlide].background_type = 'color'; slides[currentPreviewSlide].background_value = '#1A1A2E'"
              class="ml-auto text-xs text-[#3B7AB1] hover:underline"
            >Farbe verwenden</button>
          </div>
        </div>

        <!-- Student-Verknüpfung -->
        <div v-if="studentStore.students.length > 0" class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <label class="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-1"><AppIcon name="academic-cap" class="w-5 h-5 inline-block" /> Student verknüpfen</label>
          <select
            v-model="selectedStudentId"
            class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
          >
            <option :value="null">— Kein Student —</option>
            <option v-for="s in studentStore.students" :key="s.id" :value="s.id">
              {{ s.name }} ({{ s.country }})
            </option>
          </select>
        </div>

        <!-- Related Posts (Cross-Post Linking) -->
        <RelatedPostsPanel
          v-if="post"
          :post-id="Number(postId)"
          :story-arc-id="post.story_arc_id"
          :platform="post.platform"
          :country="post.country"
          :category="post.category"
        />

        <!-- Captions editing -->
        <div class="space-y-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <label class="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">Instagram Caption</label>
            <textarea v-model="captionInstagram" rows="3"
              class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent resize-none"
              :class="(captionInstagram?.length || 0) > 2200 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white' : (captionInstagram?.length || 0) > 1800 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-gray-900 dark:text-white' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white'"
            ></textarea>
            <div class="flex items-center justify-between mt-0.5">
              <span v-if="(captionInstagram?.length || 0) > 2200" class="text-xs text-red-500 dark:text-red-400">Instagram-Limit überschritten (max 2.200)</span>
              <span v-else-if="(captionInstagram?.length || 0) > 1800" class="text-xs text-amber-500 dark:text-amber-400">Nahe am Instagram-Limit</span>
              <span v-else class="text-xs text-gray-400"></span>
              <span class="text-xs" :class="(captionInstagram?.length || 0) > 2200 ? 'text-red-500 dark:text-red-400 font-semibold' : (captionInstagram?.length || 0) > 1800 ? 'text-amber-500 dark:text-amber-400' : 'text-gray-400'">{{ captionInstagram?.length || 0 }}/2.200</span>
            </div>
          </div>
          <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <label class="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2"># Hashtags</label>
            <textarea v-model="hashtagsInstagram" rows="2"
              class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent resize-none"
              :class="(hashtagsInstagram?.length || 0) > 2200 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-blue-600 dark:text-blue-400' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-blue-600 dark:text-blue-400'"
            ></textarea>
            <div class="flex items-center justify-between mt-0.5">
              <span v-if="(hashtagsInstagram?.length || 0) > 2200" class="text-xs text-red-500 dark:text-red-400">Hashtag-Limit überschritten</span>
              <span v-else class="text-xs text-gray-400"></span>
              <span class="text-xs" :class="(hashtagsInstagram?.length || 0) > 2200 ? 'text-red-500 dark:text-red-400 font-semibold' : 'text-gray-400'">{{ hashtagsInstagram?.length || 0 }} Zeichen</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Live preview (sticky) -->
      <div class="lg:sticky lg:top-4 self-start">
        <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Live-Vorschau</div>
        <div
          class="rounded-2xl overflow-hidden shadow-xl border border-gray-200 dark:border-gray-700 relative"
          :class="{
            'aspect-square': post.platform === 'instagram_feed',
            'aspect-[9/16]': post.platform === 'instagram_story' || post.platform === 'tiktok',
          }"
          :style="{
            maxWidth: '320px',
            background: slides[currentPreviewSlide]?.background_type === 'image'
              ? `url(${slides[currentPreviewSlide]?.background_value}) center/cover`
              : slides[currentPreviewSlide]?.background_value || 'linear-gradient(135deg, #1A1A2E, #2a2a4e)',
          }"
          data-testid="live-preview-container"
        >
          <div v-if="slides[currentPreviewSlide]" class="absolute inset-0 p-5 flex flex-col justify-between">
            <div class="flex items-center gap-1.5">
              <div class="bg-[#3B7AB1] rounded px-2 py-0.5"><span class="text-white text-[10px] font-bold">TREFF</span></div>
            </div>
            <div class="flex-1 flex flex-col justify-center py-3">
              <!-- Previously text (Rueckblick) - shown on first slide -->
              <div v-if="isEpisodePost && episodePreviouslyText && currentPreviewSlide === 0" class="mb-2 px-2 py-1 bg-white/10 rounded text-gray-300 text-[10px] italic leading-tight line-clamp-2" data-testid="preview-previously">
                {{ episodePreviouslyText }}
              </div>
              <h3 class="text-white text-base font-extrabold leading-tight mb-1.5 drop-shadow-md" data-testid="preview-headline">{{ slides[currentPreviewSlide].headline }}</h3>
              <p v-if="slides[currentPreviewSlide].subheadline" class="text-[#FDD000] text-[11px] font-semibold mb-1.5 drop-shadow">{{ slides[currentPreviewSlide].subheadline }}</p>
              <p v-if="slides[currentPreviewSlide].body_text" class="text-gray-200 text-[10px] leading-relaxed line-clamp-4 drop-shadow" data-testid="preview-body">{{ slides[currentPreviewSlide].body_text }}</p>
            </div>
            <!-- Cliffhanger text - shown on last slide -->
            <div v-if="isEpisodePost && episodeCliffhangerText && currentPreviewSlide === slides.length - 1" class="mb-2 px-2 py-1 bg-white/10 rounded text-[#FDD000] text-[10px] font-semibold italic leading-tight line-clamp-2" data-testid="preview-cliffhanger">
              {{ episodeCliffhangerText }}
            </div>
            <!-- Next episode hint - shown on last slide -->
            <div v-if="isEpisodePost && episodeNextHint && currentPreviewSlide === slides.length - 1" class="mb-2 px-2 py-1 bg-[#3B7AB1]/20 rounded text-blue-300 text-[10px] leading-tight line-clamp-2" data-testid="preview-nexthint">
              {{ episodeNextHint }}
            </div>
            <div v-if="slides[currentPreviewSlide].cta_text">
              <div class="inline-block bg-[#FDD000] text-[#1A1A2E] px-4 py-1.5 rounded-full font-bold text-[11px]">{{ slides[currentPreviewSlide].cta_text }}</div>
            </div>
            <!-- Slide dots -->
            <div v-if="slides.length > 1" class="flex justify-center gap-1.5 mt-2">
              <button
                v-for="(s, sIdx) in slides"
                :key="sIdx"
                @click="currentPreviewSlide = sIdx"
                class="w-2 h-2 rounded-full transition-colors"
                :class="sIdx === currentPreviewSlide ? 'bg-[#3B7AB1]' : 'bg-gray-600'"
              ></button>
            </div>
          </div>
        </div>

        <!-- Slide navigation -->
        <div v-if="slides.length > 1" class="flex items-center justify-between mt-4" style="max-width: 320px;">
          <button @click="prevPreviewSlide" :disabled="currentPreviewSlide === 0"
            class="px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-30 transition-colors">
            &#8592; Vorherige
          </button>
          <span class="text-sm text-gray-500 dark:text-gray-400">Slide {{ currentPreviewSlide + 1 }} von {{ slides.length }}</span>
          <button @click="nextPreviewSlide" :disabled="currentPreviewSlide === slides.length - 1"
            class="px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-30 transition-colors">
            Nächste &#8594;
          </button>
        </div>

        <!-- Engagement Boost Panel -->
        <div class="mt-4">
          <EngagementBoostPanel
            :post-content="engagementBoostPostContent"
            :platform="post?.platform || 'instagram_feed'"
            :format="post?.platform || 'instagram_feed'"
            :posting-time="''"
            @apply-suggestion="onApplyEngagementSuggestion"
          />
        </div>

        <!-- Performance Metrics Input (for posted posts) -->
        <div class="mt-4" v-if="post && (post.status === 'posted' || post.status === 'exported' || post.status === 'archived')">
          <PostPerformanceInput
            :post-id="Number(postId)"
            :initial-data="post"
          />
        </div>
      </div>
    </div>

    <!-- 404 / Not Found state -->
    <div v-else-if="notFound" class="text-center py-20" data-testid="post-not-found">
      <div class="text-6xl mb-4">&#128533;</div>
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-2">Post nicht gefunden</h2>
      <p class="text-gray-500 dark:text-gray-400 mb-6">Der Post mit ID #{{ postId }} existiert nicht, wurde geloescht oder gehoert dir nicht.</p>
      <div class="flex items-center justify-center gap-3">
        <button @click="router.push('/library/history')" class="px-6 py-3 bg-[#3B7AB1] text-white rounded-lg font-medium hover:bg-[#2E6A9E] transition-colors" data-testid="back-to-history-btn">
          Zur History
        </button>
        <button @click="router.push('/home')" class="px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" data-testid="back-to-dashboard-btn">
          Zum Dashboard
        </button>
      </div>
    </div>

    <!-- Generic error state / other load failures -->
    <div v-else-if="!loading && !post" class="text-center py-20" role="alert">
      <div class="text-6xl mb-4">&#9888;</div>
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-2">Fehler beim Laden</h2>
      <p class="text-gray-500 dark:text-gray-400 mb-6">{{ error || 'Ein unbekannter Fehler ist aufgetreten.' }}</p>
      <div class="flex items-center justify-center gap-3">
        <button @click="loadPost()" class="px-6 py-3 bg-[#3B7AB1] text-white rounded-lg font-medium hover:bg-[#2E6A9E] transition-colors">
          Erneut versuchen
        </button>
        <button @click="router.push('/home')" class="px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
          Zum Dashboard
        </button>
      </div>
    </div>

    <!-- Delete Slide Confirmation Modal -->
    <Teleport to="body">
      <div
        v-if="showDeleteSlideConfirm"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        @click.self="cancelRemoveSlide"
      >
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-6 max-w-sm w-full mx-4 transform transition-all" data-testid="delete-slide-modal">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <span class="text-lg">&#9888;</span>
            </div>
            <div>
              <h3 class="text-lg font-bold text-gray-900 dark:text-white">Slide entfernen?</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Slide {{ slideToDeleteIndex + 1 }} wird unwiderruflich entfernt.
              </p>
            </div>
          </div>
          <div class="flex gap-3">
            <button
              @click="cancelRemoveSlide"
              class="flex-1 px-4 py-2.5 rounded-lg text-sm font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              Abbrechen
            </button>
            <button
              @click="confirmRemoveSlide"
              class="flex-1 px-4 py-2.5 rounded-lg text-sm font-medium bg-red-600 text-white hover:bg-red-700 transition-colors"
              data-testid="confirm-delete-slide-btn"
            >
              Entfernen
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Repurpose Panel Modal -->
    <Teleport to="body">
      <div
        v-if="showRepurposePanel"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        @click.self="showRepurposePanel = false"
        data-testid="repurpose-modal"
      >
        <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-y-auto mx-4 p-6">
          <RepurposePanel
            :post="post"
            @saved="onRepurposeSaved"
            @close="showRepurposePanel = false"
          />
        </div>
      </div>
    </Teleport>

    <!-- Video Repurpose Wizard Modal -->
    <Teleport to="body">
      <div
        v-if="showVideoRepurpose"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        @click.self="showVideoRepurpose = false"
        data-testid="video-repurpose-modal"
      >
        <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-y-auto mx-4">
          <div class="flex items-center justify-between px-6 pt-5 pb-2">
            <h2 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <AppIcon name="film" class="w-5 h-5" /> Video-Content-Pipeline
            </h2>
            <button
              @click="showVideoRepurpose = false"
              class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-1"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <VideoRepurposeWizard
            :post="post"
            @generated="onVideoRepurposeGenerated"
            @close="showVideoRepurpose = false"
          />
        </div>
      </div>
    </Teleport>

    <!-- Multi-Platform Export Modal -->
    <MultiPlatformExport
      :visible="showMultiPlatformExport"
      :post="post"
      :slides="slides"
      :caption-instagram="captionInstagram"
      :caption-tiktok="captionTiktok"
      :hashtags-instagram="hashtagsInstagram"
      :hashtags-tiktok="hashtagsTiktok"
      @close="showMultiPlatformExport = false"
      @export-complete="onMultiExportComplete"
    />

    <!-- Unsaved Changes Warning Dialog -->
    <Teleport to="body">
      <div v-if="showLeaveDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" data-testid="unsaved-changes-dialog">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-6 max-w-sm mx-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Ungespeicherte Änderungen</h3>
          <p class="text-gray-600 dark:text-gray-300 text-sm mb-6">
            Du hast ungespeicherte Änderungen. Wenn du die Seite verlässt, gehen diese verloren.
          </p>
          <div class="flex gap-3 justify-end">
            <button
              @click="cancelLeave"
              class="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors font-medium text-sm"
              data-testid="unsaved-stay-btn"
            >
              Auf Seite bleiben
            </button>
            <button
              @click="confirmLeave"
              class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors font-medium text-sm"
              data-testid="unsaved-leave-btn"
            >
              Verwerfen & Verlassen
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.slide-ghost {
  opacity: 0.4;
  background: #3B7AB1 !important;
  border-radius: 0.5rem;
}
</style>
