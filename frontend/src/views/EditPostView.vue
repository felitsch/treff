<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import draggable from 'vuedraggable'
import api from '@/utils/api'

const route = useRoute()
const router = useRouter()

const postId = computed(() => route.params.id)
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const successMsg = ref('')
const post = ref(null)
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

async function loadPost() {
  loading.value = true
  error.value = ''
  try {
    const response = await api.get(`/api/posts/${postId.value}`)
    post.value = response.data

    // Parse slide_data JSON
    try {
      const parsed = JSON.parse(response.data.slide_data || '[]')
      slides.value = Array.isArray(parsed) ? parsed : []
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
  } catch (e) {
    error.value = 'Fehler beim Laden: ' + (e.response?.data?.detail || e.message)
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

onMounted(() => {
  loadPost()
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
      <div class="flex gap-2">
        <button
          @click="savePost"
          :disabled="saving"
          class="px-5 py-2.5 bg-[#4C8BC2] hover:bg-[#3a7ab3] disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
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
      <div class="animate-spin h-10 w-10 border-4 border-[#4C8BC2] border-t-transparent rounded-full"></div>
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

        <!-- Slide tabs with drag-and-drop reordering -->
        <div v-if="slides.length > 1" class="mb-1">
          <div class="flex items-center gap-2 mb-2">
            <span class="text-xs text-gray-500 dark:text-gray-400">&#8597; Slides per Drag &amp; Drop neu anordnen</span>
          </div>
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
                  ? 'bg-[#4C8BC2] text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200'"
              >
                <span class="opacity-50">&#10495;</span>
                Slide {{ index + 1 }}
                <span v-if="index === 0" class="font-normal">(Cover)</span>
                <span v-if="index === slides.length - 1 && index > 0" class="font-normal">(CTA)</span>
              </button>
            </template>
          </draggable>
        </div>

        <!-- Current slide edit -->
        <div v-if="slides[currentPreviewSlide]" class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 space-y-3">
          <div>
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Headline</label>
            <input
              v-model="slides[currentPreviewSlide].headline"
              class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent"
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
              class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent"
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
              class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent resize-none"
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
              class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent"
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

        <!-- Captions editing -->
        <div class="space-y-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <label class="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">Instagram Caption</label>
            <textarea v-model="captionInstagram" rows="3"
              class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent resize-none"
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
              class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#4C8BC2] focus:border-transparent resize-none"
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
          class="rounded-2xl overflow-hidden shadow-xl border border-gray-200 dark:border-gray-700 relative bg-gradient-to-br from-[#1A1A2E] to-[#2a2a4e]"
          :class="{
            'aspect-square': post.platform === 'instagram_feed',
            'aspect-[9/16]': post.platform === 'instagram_story' || post.platform === 'tiktok',
          }"
          style="max-width: 320px;"
        >
          <div v-if="slides[currentPreviewSlide]" class="absolute inset-0 p-5 flex flex-col justify-between">
            <div class="flex items-center gap-1.5">
              <div class="bg-[#4C8BC2] rounded px-2 py-0.5"><span class="text-white text-[10px] font-bold">TREFF</span></div>
            </div>
            <div class="flex-1 flex flex-col justify-center py-3">
              <h3 class="text-[#4C8BC2] text-base font-extrabold leading-tight mb-1.5">{{ slides[currentPreviewSlide].headline }}</h3>
              <p v-if="slides[currentPreviewSlide].subheadline" class="text-[#FDD000] text-[11px] font-semibold mb-1.5">{{ slides[currentPreviewSlide].subheadline }}</p>
              <p v-if="slides[currentPreviewSlide].body_text" class="text-gray-300 text-[10px] leading-relaxed line-clamp-4">{{ slides[currentPreviewSlide].body_text }}</p>
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
                :class="sIdx === currentPreviewSlide ? 'bg-[#4C8BC2]' : 'bg-gray-600'"
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

    <!-- Empty state / not found -->
    <div v-else-if="!loading" class="text-center py-20">
      <div class="text-6xl mb-4">&#128533;</div>
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-2">Post nicht gefunden</h2>
      <p class="text-gray-500 dark:text-gray-400 mb-4">Der Post mit ID #{{ postId }} existiert nicht oder gehoert dir nicht.</p>
      <button @click="router.push('/history')" class="px-6 py-3 bg-[#4C8BC2] text-white rounded-lg font-medium hover:bg-[#3a7ab3]">
        Zur History
      </button>
    </div>
  </div>
</template>

<style scoped>
.slide-ghost {
  opacity: 0.4;
  background: #4C8BC2 !important;
  border-radius: 0.5rem;
}
</style>
