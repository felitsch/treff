<script setup>
/**
 * Step2Design.vue — Schritt 2: Design
 *
 * Template selection + live preview + slide editing:
 * - Template thumbnail grid (category-filtered)
 * - Live preview panel (right side)
 * - Slide content editing (headline, subheadline, body, CTA)
 * - SlideManager for multi-slide carousel management
 */
import { ref, computed, watch, onMounted } from 'vue'
import { usePostCreator } from '@/composables/usePostCreator'
import SlideManager from '@/components/posts/SlideManager.vue'
import CtaPicker from '@/components/posts/CtaPicker.vue'
import api from '@/utils/api'

const {
  selectedCategory,
  selectedTemplate,
  templates,
  loadingTemplates,
  slides,
  currentPreviewSlide,
  selectedPlatform,
  selectedPlatforms,
  previewPlatform,
  regeneratingField,
  topic,
  country,
  tone,
  toast,
} = usePostCreator()

const MAX_SLIDES = 10

// ── Load templates ─────────────────────────────────────────────────
async function loadTemplates() {
  loadingTemplates.value = true
  try {
    const params = new URLSearchParams()
    if (selectedCategory.value) params.append('category', selectedCategory.value)
    const response = await api.get(`/api/templates?${params.toString()}`)
    templates.value = response.data
  } catch (e) {
    console.error('Failed to load templates:', e)
    templates.value = []
  } finally {
    loadingTemplates.value = false
  }
}

onMounted(() => {
  if (templates.value.length === 0 || selectedCategory.value) {
    loadTemplates()
  }
})

watch(() => selectedCategory.value, () => {
  loadTemplates()
})

// ── Slide management ──────────────────────────────────────────────
let dragIdCounter = 0
function ensureDragIds() {
  for (const slide of slides.value) {
    if (!slide.dragId) {
      slide.dragId = `slide-${++dragIdCounter}`
    }
  }
}

function addSlide() {
  if (slides.value.length >= MAX_SLIDES) {
    toast.warning(`Maximal ${MAX_SLIDES} Slides erlaubt.`)
    return
  }
  slides.value.push({
    headline: 'Neue Slide',
    subheadline: '',
    body_text: '',
    cta_text: '',
    background_type: 'color',
    background_value: '#3B7AB1',
  })
  ensureDragIds()
  currentPreviewSlide.value = slides.value.length - 1
}

function duplicateSlide(index) {
  if (slides.value.length >= MAX_SLIDES) {
    toast.warning(`Maximal ${MAX_SLIDES} Slides erlaubt.`)
    return
  }
  const clone = JSON.parse(JSON.stringify(slides.value[index]))
  delete clone.dragId
  clone.headline = (clone.headline || '') + ' (Kopie)'
  slides.value.splice(index + 1, 0, clone)
  ensureDragIds()
  currentPreviewSlide.value = index + 1
  toast.success('Slide dupliziert')
}

const showDeleteConfirm = ref(false)
const deleteIndex = ref(-1)

function requestRemoveSlide(index) {
  if (slides.value.length <= 1) return
  deleteIndex.value = index
  showDeleteConfirm.value = true
}

function confirmRemoveSlide() {
  if (deleteIndex.value >= 0 && deleteIndex.value < slides.value.length) {
    slides.value.splice(deleteIndex.value, 1)
    if (currentPreviewSlide.value >= slides.value.length) {
      currentPreviewSlide.value = slides.value.length - 1
    }
    ensureDragIds()
  }
  showDeleteConfirm.value = false
  deleteIndex.value = -1
}

function onSlideReorder() {
  currentPreviewSlide.value = 0
  ensureDragIds()
}

// ── Regenerate field ────────────────────────────────────────────────
async function regenerateField(field, slideIndex = 0) {
  if (regeneratingField.value) return
  const key = slideIndex > 0 ? `${field}_${slideIndex}` : field
  regeneratingField.value = key
  try {
    const response = await api.post('/api/ai/regenerate-field', {
      field,
      slide_index: slideIndex,
      category: selectedCategory.value,
      topic: topic.value,
      country: country.value,
      tone: tone.value,
      platform: selectedPlatform.value,
      context: {
        current_slides: slides.value,
        current_captions: {
          instagram: '',
          tiktok: '',
        },
      },
    })
    if (response.data?.value !== undefined) {
      if (field === 'headline' || field === 'subheadline' || field === 'body_text' || field === 'cta_text') {
        if (slides.value[slideIndex]) {
          slides.value[slideIndex][field] = response.data.value
        }
      }
      toast.success(`${field} neu generiert`)
    }
  } catch (e) {
    toast.error('Regenerierung fehlgeschlagen')
  } finally {
    regeneratingField.value = ''
  }
}

// Effective preview platform
const effectivePreviewPlatform = computed(() =>
  previewPlatform.value || selectedPlatform.value || 'instagram_feed'
)

// Initialize drag IDs on mount
onMounted(() => {
  ensureDragIds()
})
</script>

<template>
  <div class="space-y-4" data-testid="step2-design">
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
      <!-- LEFT: Template selection + Slide editing (3/5) -->
      <div class="lg:col-span-3 space-y-4">
        <!-- Template Grid -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-sm font-semibold text-gray-700 dark:text-gray-300">Template waehlen</label>
            <span v-if="loadingTemplates" class="text-xs text-gray-400">Lade...</span>
            <span v-else class="text-xs text-gray-400">{{ templates.length }} Templates</span>
          </div>

          <div v-if="loadingTemplates" class="flex items-center justify-center h-24">
            <div class="animate-spin h-6 w-6 border-2 border-[#3B7AB1] border-t-transparent rounded-full"></div>
          </div>

          <div v-else class="grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-[240px] overflow-y-auto pr-1">
            <button
              v-for="tmpl in templates"
              :key="tmpl.id"
              @click="selectedTemplate = tmpl"
              class="rounded-xl border-2 overflow-hidden transition-all hover:shadow-md group"
              :class="selectedTemplate?.id === tmpl.id
                ? 'border-[#3B7AB1] ring-2 ring-[#3B7AB1]/30 shadow-md'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-400'"
              :data-testid="'template-card-' + tmpl.id"
            >
              <div class="h-20 bg-gradient-to-br from-[#1A1A2E] to-[#2a2a4e] flex items-center justify-center relative">
                <div class="text-white text-[10px] font-bold px-2 text-center leading-tight">{{ tmpl.name }}</div>
                <span v-if="selectedTemplate?.id === tmpl.id" class="absolute top-1 right-1 w-5 h-5 bg-[#3B7AB1] rounded-full flex items-center justify-center text-white text-[10px]">&#10003;</span>
              </div>
              <div class="px-2 py-1.5 bg-white dark:bg-gray-800">
                <div class="text-[10px] font-medium text-gray-600 dark:text-gray-400 truncate">{{ tmpl.name }}</div>
                <div class="text-[8px] text-gray-400">{{ tmpl.slide_count }} Slides &middot; {{ tmpl.platform_format }}</div>
              </div>
            </button>
          </div>
        </div>

        <!-- SlideManager + Editor (only if slides exist) -->
        <div v-if="slides.length > 0">
          <SlideManager
            :slides="slides"
            :current-slide="currentPreviewSlide"
            :max-slides="MAX_SLIDES"
            @update:slides="val => { slides = val; ensureDragIds() }"
            @update:current-slide="val => currentPreviewSlide = val"
            @add="addSlide"
            @remove="requestRemoveSlide"
            @duplicate="duplicateSlide"
            @reorder="onSlideReorder"
            @select="val => currentPreviewSlide = val"
          />

          <!-- Current slide edit -->
          <div v-if="slides[currentPreviewSlide]" class="mt-3 p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 space-y-3">
            <div class="flex items-center justify-between pb-2 border-b border-gray-100 dark:border-gray-700">
              <span class="text-sm font-semibold text-gray-700 dark:text-gray-300">
                Slide {{ currentPreviewSlide + 1 }}
                <span v-if="currentPreviewSlide === 0" class="text-xs font-normal text-gray-400">(Cover)</span>
              </span>
              <div class="flex items-center gap-1">
                <button
                  v-if="slides.length < MAX_SLIDES"
                  @click="duplicateSlide(currentPreviewSlide)"
                  class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md text-[#3B7AB1] hover:bg-[#3B7AB1]/10"
                  data-testid="duplicate-slide-btn"
                >&#x2398; Duplizieren</button>
                <button
                  v-if="slides.length > 1"
                  @click="requestRemoveSlide(currentPreviewSlide)"
                  class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                >&#128465; Entfernen</button>
              </div>
            </div>

            <!-- Headline -->
            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Headline</label>
                <button @click="regenerateField('headline', currentPreviewSlide)" :disabled="!!regeneratingField"
                  class="text-[10px] text-[#3B7AB1] hover:text-[#2E6A9E] font-medium disabled:opacity-40">&#x1F504; Neu</button>
              </div>
              <input v-model="slides[currentPreviewSlide].headline"
                class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1]" />
            </div>

            <!-- Subheadline -->
            <div v-if="slides[currentPreviewSlide].subheadline !== undefined">
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Subheadline</label>
                <button @click="regenerateField('subheadline', currentPreviewSlide)" :disabled="!!regeneratingField"
                  class="text-[10px] text-[#3B7AB1] hover:text-[#2E6A9E] font-medium disabled:opacity-40">&#x1F504; Neu</button>
              </div>
              <input v-model="slides[currentPreviewSlide].subheadline"
                class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1]" />
            </div>

            <!-- Body text -->
            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Text</label>
                <button @click="regenerateField('body_text', currentPreviewSlide)" :disabled="!!regeneratingField"
                  class="text-[10px] text-[#3B7AB1] hover:text-[#2E6A9E] font-medium disabled:opacity-40">&#x1F504; Neu</button>
              </div>
              <textarea v-model="slides[currentPreviewSlide].body_text" rows="3"
                class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1] resize-none"></textarea>
            </div>

            <!-- CTA -->
            <div v-if="slides[currentPreviewSlide].cta_text !== undefined">
              <label class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1 block">CTA</label>
              <CtaPicker v-model="slides[currentPreviewSlide].cta_text" :category="selectedCategory" :platform="selectedPlatform" :topic="topic" />
            </div>

            <!-- Background color -->
            <div v-if="slides[currentPreviewSlide]?.background_type !== 'image'">
              <label class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1 block">Hintergrundfarbe</label>
              <div class="flex gap-1.5 flex-wrap">
                <button
                  v-for="preset in ['#1A1A2E', '#3B7AB1', '#FDD000', '#2D6A4F', '#E63946', '#7B2CBF', '#FF6B35', '#264653']"
                  :key="preset"
                  @click="slides[currentPreviewSlide].background_value = preset; slides[currentPreviewSlide].background_type = 'color'"
                  class="w-6 h-6 rounded-md border-2 transition-all hover:scale-110"
                  :class="slides[currentPreviewSlide].background_value === preset ? 'border-white ring-2 ring-[#3B7AB1]' : 'border-gray-300 dark:border-gray-600'"
                  :style="{ backgroundColor: preset }"
                ></button>
              </div>
            </div>
          </div>
        </div>

        <!-- No slides yet hint -->
        <div v-else class="p-6 rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600 text-center">
          <p class="text-gray-500 dark:text-gray-400 text-sm">Generiere zuerst Inhalte in Schritt 1, um Slides zu bearbeiten.</p>
        </div>
      </div>

      <!-- RIGHT: Live Preview (2/5) -->
      <div class="lg:col-span-2 lg:sticky lg:top-4 self-start">
        <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Live-Vorschau</div>
        <div
          class="rounded-2xl overflow-hidden shadow-xl border border-gray-200 dark:border-gray-700 relative"
          :class="{
            'aspect-square': effectivePreviewPlatform === 'instagram_feed',
            'aspect-[9/16]': effectivePreviewPlatform === 'instagram_story' || effectivePreviewPlatform === 'tiktok',
          }"
          :style="{
            maxWidth: '320px',
            background: slides[currentPreviewSlide]?.background_type === 'image'
              ? `url(${slides[currentPreviewSlide].background_value}) center/cover`
              : slides[currentPreviewSlide]?.background_value || 'linear-gradient(135deg, #1A1A2E, #2a2a4e)',
          }"
          data-testid="preview-container"
        >
          <div v-if="slides[currentPreviewSlide]" class="absolute inset-0 p-5 flex flex-col justify-between">
            <div class="flex items-center gap-1.5">
              <div class="bg-[#3B7AB1] rounded px-2 py-0.5"><span class="text-white text-[10px] font-bold">TREFF</span></div>
            </div>
            <div class="flex-1 flex flex-col justify-center py-3">
              <h3 class="text-white text-base font-extrabold leading-tight mb-1.5 drop-shadow-md">{{ slides[currentPreviewSlide].headline }}</h3>
              <p v-if="slides[currentPreviewSlide].subheadline" class="text-[#FDD000] text-[11px] font-semibold mb-1.5">{{ slides[currentPreviewSlide].subheadline }}</p>
              <p v-if="slides[currentPreviewSlide].body_text" class="text-gray-200 text-[10px] leading-relaxed line-clamp-4">{{ slides[currentPreviewSlide].body_text }}</p>
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
          <!-- Empty preview -->
          <div v-else class="absolute inset-0 flex items-center justify-center">
            <p class="text-gray-400 text-sm">Keine Slides</p>
          </div>
        </div>

        <!-- Slide navigation -->
        <div v-if="slides.length > 1" class="flex items-center justify-between mt-3">
          <button @click="currentPreviewSlide = Math.max(0, currentPreviewSlide - 1)" :disabled="currentPreviewSlide === 0"
            class="px-2 py-1 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 disabled:opacity-30">&#8592;</button>
          <span class="text-xs text-gray-500">{{ currentPreviewSlide + 1 }} / {{ slides.length }}</span>
          <button @click="currentPreviewSlide = Math.min(slides.length - 1, currentPreviewSlide + 1)" :disabled="currentPreviewSlide === slides.length - 1"
            class="px-2 py-1 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 disabled:opacity-30">&#8594;</button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <Teleport to="body">
      <div v-if="showDeleteConfirm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showDeleteConfirm = false">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-6 max-w-sm w-full mx-4">
          <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-2">Slide entfernen?</h3>
          <p class="text-sm text-gray-500 mb-4">Slide {{ deleteIndex + 1 }} wird unwiderruflich entfernt.</p>
          <div class="flex gap-3">
            <button @click="showDeleteConfirm = false" class="flex-1 px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium">Abbrechen</button>
            <button @click="confirmRemoveSlide" class="flex-1 px-4 py-2 rounded-lg bg-red-600 text-white font-medium">Entfernen</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
