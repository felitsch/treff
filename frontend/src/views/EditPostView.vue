<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import draggable from 'vuedraggable'
import api from '@/utils/api'
import { useUndoRedo } from '@/composables/useUndoRedo'
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'

const route = useRoute()
const router = useRouter()

const postId = computed(() => route.params.id)
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const successMsg = ref('')
const post = ref(null)
const notFound = ref(false)
const slides = ref([])
const currentPreviewSlide = ref(0)

// Editable caption/hashtag fields
const captionInstagram = ref('')
const captionTiktok = ref('')
const hashtagsInstagram = ref('')
const hashtagsTiktok = ref('')
const ctaText = ref('')

// Categories for display
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

const categoryObj = computed(() => categories.find(c => c.id === post.value?.category))

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

    // Initialize undo/redo history with loaded state
    initFromState(getEditableState())

    // Capture initial state for unsaved changes detection (without dragId)
    initialStateSnapshot.value = getCleanState()
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
    }

    await api.put(`/api/posts/${postId.value}`, updateData)

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

onMounted(() => {
  loadPost()
  startListening()
  window.addEventListener('keydown', handleCtrlS, true)
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
          @click="router.push('/history')"
          class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          &#8592; Zurueck
        </button>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Post bearbeiten
          <span v-if="post" class="text-base font-normal text-gray-500 dark:text-gray-400">#{{ post.id }}</span>
        </h1>
      </div>
      <div v-if="post" class="flex gap-2">
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
          <span v-if="categoryObj">{{ categoryObj.icon }} {{ categoryObj.label }}</span>
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
              <span v-if="(slides[currentPreviewSlide].headline?.length || 0) > 40" class="text-xs text-red-500 dark:text-red-400">Text kann den Template-Bereich ueberlaufen</span>
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
              <span v-if="(slides[currentPreviewSlide].subheadline?.length || 0) > 60" class="text-xs text-red-500 dark:text-red-400">Text kann den Template-Bereich ueberlaufen</span>
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
              <span v-if="(slides[currentPreviewSlide].body_text?.length || 0) > 200" class="text-xs text-red-500 dark:text-red-400">Text kann den Template-Bereich ueberlaufen</span>
              <span v-else-if="(slides[currentPreviewSlide].body_text?.length || 0) > 150" class="text-xs text-amber-500 dark:text-amber-400">Nahe am Zeichenlimit</span>
              <span v-else class="text-xs text-gray-400"></span>
              <span class="text-xs" :class="(slides[currentPreviewSlide].body_text?.length || 0) > 200 ? 'text-red-500 dark:text-red-400 font-semibold' : (slides[currentPreviewSlide].body_text?.length || 0) > 150 ? 'text-amber-500 dark:text-amber-400' : 'text-gray-400'">{{ slides[currentPreviewSlide].body_text?.length || 0 }}/200</span>
            </div>
          </div>
          <div v-if="slides[currentPreviewSlide].cta_text !== undefined">
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">CTA</label>
            <input
              v-model="slides[currentPreviewSlide].cta_text"
              class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
              :class="(slides[currentPreviewSlide].cta_text?.length || 0) > 25 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white' : (slides[currentPreviewSlide].cta_text?.length || 0) > 20 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-gray-900 dark:text-white' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white'"
            />
            <div class="flex items-center justify-between mt-0.5">
              <span v-if="(slides[currentPreviewSlide].cta_text?.length || 0) > 25" class="text-xs text-red-500 dark:text-red-400">Text kann den Template-Bereich ueberlaufen</span>
              <span v-else-if="(slides[currentPreviewSlide].cta_text?.length || 0) > 20" class="text-xs text-amber-500 dark:text-amber-400">Nahe am Zeichenlimit</span>
              <span v-else class="text-xs text-gray-400"></span>
              <span class="text-xs" :class="(slides[currentPreviewSlide].cta_text?.length || 0) > 25 ? 'text-red-500 dark:text-red-400 font-semibold' : (slides[currentPreviewSlide].cta_text?.length || 0) > 20 ? 'text-amber-500 dark:text-amber-400' : 'text-gray-400'">{{ slides[currentPreviewSlide].cta_text?.length || 0 }}/25</span>
            </div>
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
                title="Eigene Farbe waehlen"
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

        <!-- Captions editing -->
        <div class="space-y-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <label class="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">Instagram Caption</label>
            <textarea v-model="captionInstagram" rows="3"
              class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent resize-none"
              :class="(captionInstagram?.length || 0) > 2200 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white' : (captionInstagram?.length || 0) > 1800 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-gray-900 dark:text-white' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white'"
            ></textarea>
            <div class="flex items-center justify-between mt-0.5">
              <span v-if="(captionInstagram?.length || 0) > 2200" class="text-xs text-red-500 dark:text-red-400">Instagram-Limit ueberschritten (max 2.200)</span>
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
              <span v-if="(hashtagsInstagram?.length || 0) > 2200" class="text-xs text-red-500 dark:text-red-400">Hashtag-Limit ueberschritten</span>
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
              ? `url(${slides[currentPreviewSlide].background_value}) center/cover`
              : slides[currentPreviewSlide]?.background_value || 'linear-gradient(135deg, #1A1A2E, #2a2a4e)',
          }"
          data-testid="live-preview-container"
        >
          <div v-if="slides[currentPreviewSlide]" class="absolute inset-0 p-5 flex flex-col justify-between">
            <div class="flex items-center gap-1.5">
              <div class="bg-[#3B7AB1] rounded px-2 py-0.5"><span class="text-white text-[10px] font-bold">TREFF</span></div>
            </div>
            <div class="flex-1 flex flex-col justify-center py-3">
              <h3 class="text-white text-base font-extrabold leading-tight mb-1.5 drop-shadow-md" data-testid="preview-headline">{{ slides[currentPreviewSlide].headline }}</h3>
              <p v-if="slides[currentPreviewSlide].subheadline" class="text-[#FDD000] text-[11px] font-semibold mb-1.5 drop-shadow">{{ slides[currentPreviewSlide].subheadline }}</p>
              <p v-if="slides[currentPreviewSlide].body_text" class="text-gray-200 text-[10px] leading-relaxed line-clamp-4 drop-shadow" data-testid="preview-body">{{ slides[currentPreviewSlide].body_text }}</p>
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
            Naechste &#8594;
          </button>
        </div>
      </div>
    </div>

    <!-- 404 / Not Found state -->
    <div v-else-if="notFound" class="text-center py-20" data-testid="post-not-found">
      <div class="text-6xl mb-4">&#128533;</div>
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-2">Post nicht gefunden</h2>
      <p class="text-gray-500 dark:text-gray-400 mb-6">Der Post mit ID #{{ postId }} existiert nicht, wurde geloescht oder gehoert dir nicht.</p>
      <div class="flex items-center justify-center gap-3">
        <button @click="router.push('/history')" class="px-6 py-3 bg-[#3B7AB1] text-white rounded-lg font-medium hover:bg-[#2E6A9E] transition-colors" data-testid="back-to-history-btn">
          Zur History
        </button>
        <button @click="router.push('/dashboard')" class="px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" data-testid="back-to-dashboard-btn">
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
        <button @click="router.push('/dashboard')" class="px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
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

    <!-- Unsaved Changes Warning Dialog -->
    <Teleport to="body">
      <div v-if="showLeaveDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" data-testid="unsaved-changes-dialog">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-6 max-w-sm mx-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Ungespeicherte Aenderungen</h3>
          <p class="text-gray-600 dark:text-gray-300 text-sm mb-6">
            Du hast ungespeicherte Aenderungen. Wenn du die Seite verlaesst, gehen diese verloren.
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
