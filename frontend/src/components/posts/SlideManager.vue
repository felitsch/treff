<script setup>
/**
 * SlideManager.vue — Thumbnail-Leiste mit Add/Remove/Reorder/Duplicate
 *
 * Features:
 * - Visual thumbnail strip showing mini previews of each slide
 * - Drag & drop reordering via vuedraggable
 * - Add new slide (max 10)
 * - Duplicate slide
 * - Remove slide (with confirmation)
 * - Per-slide image indicator
 * - Active slide highlighting with dot indicator
 */
import { ref, computed, watch } from 'vue'
import draggable from 'vuedraggable'

const props = defineProps({
  slides: {
    type: Array,
    required: true,
  },
  currentSlide: {
    type: Number,
    default: 0,
  },
  maxSlides: {
    type: Number,
    default: 10,
  },
})

const emit = defineEmits([
  'update:slides',
  'update:currentSlide',
  'add',
  'remove',
  'duplicate',
  'reorder',
  'select',
])

// Local copy for drag-and-drop (two-way bind via events)
const localSlides = computed({
  get: () => props.slides,
  set: (val) => {
    emit('update:slides', val)
    emit('reorder')
  },
})

const canAddSlide = computed(() => props.slides.length < props.maxSlides)

function selectSlide(index) {
  emit('update:currentSlide', index)
  emit('select', index)
}

function addSlide() {
  if (!canAddSlide.value) return
  emit('add')
}

function requestRemoveSlide(index, event) {
  if (event) event.stopPropagation()
  if (props.slides.length <= 1) return
  emit('remove', index)
}

function duplicateSlide(index, event) {
  if (event) event.stopPropagation()
  if (!canAddSlide.value) return
  emit('duplicate', index)
}

function onDragEnd() {
  emit('reorder')
}

/**
 * Generate a mini background style for the thumbnail based on slide data
 */
function getThumbnailStyle(slide) {
  if (slide.background_type === 'image' && slide.background_value) {
    return {
      backgroundImage: `url(${slide.background_value})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
    }
  }
  if (slide.background_value && slide.background_value.startsWith('#')) {
    return { backgroundColor: slide.background_value }
  }
  if (slide.background_value && slide.background_value.startsWith('linear-gradient')) {
    return { background: slide.background_value }
  }
  return { background: 'linear-gradient(135deg, #1A1A2E, #2a2a4e)' }
}
</script>

<template>
  <div class="slide-manager" data-testid="slide-manager">
    <!-- Header -->
    <div class="flex items-center justify-between mb-2">
      <div class="flex items-center gap-2">
        <span class="text-sm font-semibold text-gray-700 dark:text-gray-300">
          Slides
        </span>
        <span class="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 font-medium">
          {{ slides.length }} / {{ maxSlides }}
        </span>
      </div>
      <div class="flex items-center gap-1">
        <span v-if="slides.length > 1" class="text-[10px] text-gray-400 dark:text-gray-500 mr-1">Drag zum Umordnen</span>
        <button
          v-if="canAddSlide"
          @click="addSlide"
          class="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-[#3B7AB1] hover:text-[#3B7AB1] dark:hover:border-[#3B7AB1] dark:hover:text-[#3B7AB1] transition-colors"
          data-testid="add-slide-btn"
          title="Neue Slide hinzufuegen"
        >
          <span class="text-sm">+</span> Slide
        </button>
        <span
          v-else
          class="text-[10px] text-amber-500 dark:text-amber-400 font-medium"
        >
          Max. {{ maxSlides }} Slides
        </span>
      </div>
    </div>

    <!-- Thumbnail Strip -->
    <div class="flex items-stretch gap-2 overflow-x-auto pb-2 scrollbar-thin" data-testid="slide-thumbnail-strip">
      <draggable
        v-model="localSlides"
        item-key="dragId"
        handle=".slide-drag-handle"
        animation="200"
        ghost-class="slide-ghost"
        class="flex gap-2"
        @end="onDragEnd"
      >
        <template #item="{ element: slide, index }">
          <div
            class="slide-thumbnail group relative flex-shrink-0 cursor-pointer rounded-lg border-2 transition-all duration-200"
            :class="[
              currentSlide === index
                ? 'border-[#3B7AB1] ring-2 ring-[#3B7AB1]/30 shadow-md scale-[1.02]'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500',
            ]"
            :data-testid="'slide-thumb-' + index"
            @click="selectSlide(index)"
          >
            <!-- Thumbnail preview -->
            <div
              class="slide-drag-handle w-20 h-20 rounded-t-md overflow-hidden relative cursor-grab active:cursor-grabbing"
              :style="getThumbnailStyle(slide)"
            >
              <!-- Mini text preview -->
              <div class="absolute inset-0 p-1.5 flex flex-col justify-center">
                <div
                  class="text-[7px] font-bold text-white leading-tight line-clamp-2 drop-shadow"
                  :class="{ 'text-[6px]': (slide.headline || '').length > 20 }"
                >
                  {{ slide.headline || 'Leer' }}
                </div>
                <div
                  v-if="slide.subheadline"
                  class="text-[5px] text-[#FDD000] leading-tight line-clamp-1 mt-0.5 drop-shadow"
                >
                  {{ slide.subheadline }}
                </div>
              </div>

              <!-- Image indicator -->
              <div
                v-if="slide.background_type === 'image'"
                class="absolute top-0.5 right-0.5 w-3.5 h-3.5 bg-green-500/80 rounded-full flex items-center justify-center"
                title="Bild vorhanden"
              >
                <span class="text-[7px] text-white">&#128247;</span>
              </div>
            </div>

            <!-- Slide label + actions -->
            <div class="px-1 py-0.5 bg-white dark:bg-gray-800 rounded-b-md flex items-center justify-between gap-0.5">
              <span class="text-[9px] font-semibold text-gray-600 dark:text-gray-400 truncate">
                <span v-if="index === 0">Cover</span>
                <span v-else-if="index === slides.length - 1 && index > 0">CTA</span>
                <span v-else>{{ index + 1 }}</span>
              </span>

              <!-- Actions (visible on hover) -->
              <div class="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  v-if="canAddSlide"
                  @click="duplicateSlide(index, $event)"
                  class="w-4 h-4 flex items-center justify-center rounded text-[8px] text-gray-400 hover:text-[#3B7AB1] hover:bg-[#3B7AB1]/10 transition-colors"
                  title="Slide duplizieren"
                  :data-testid="'duplicate-slide-' + index"
                >
                  &#x2398;
                </button>
                <button
                  v-if="slides.length > 1"
                  @click="requestRemoveSlide(index, $event)"
                  class="w-4 h-4 flex items-center justify-center rounded text-[8px] text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                  title="Slide entfernen"
                  :data-testid="'remove-slide-' + index"
                >
                  &#x2715;
                </button>
              </div>
            </div>
          </div>
        </template>
      </draggable>

      <!-- Add slide card (visual placeholder) -->
      <div
        v-if="canAddSlide"
        @click="addSlide"
        class="flex-shrink-0 w-20 h-[94px] rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 hover:border-[#3B7AB1] dark:hover:border-[#3B7AB1] flex flex-col items-center justify-center cursor-pointer transition-colors group"
        data-testid="add-slide-card"
      >
        <span class="text-xl text-gray-400 dark:text-gray-500 group-hover:text-[#3B7AB1] transition-colors">+</span>
        <span class="text-[9px] text-gray-400 dark:text-gray-500 group-hover:text-[#3B7AB1] transition-colors">Neue Slide</span>
      </div>
    </div>

    <!-- Dot indicator (for quick navigation) -->
    <div v-if="slides.length > 1" class="flex justify-center gap-1.5 mt-2" data-testid="slide-dots">
      <button
        v-for="(s, sIdx) in slides"
        :key="'dot-' + sIdx"
        @click="selectSlide(sIdx)"
        class="w-2 h-2 rounded-full transition-all duration-200"
        :class="sIdx === currentSlide
          ? 'bg-[#3B7AB1] scale-125'
          : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500'"
        :title="'Slide ' + (sIdx + 1)"
      ></button>
    </div>
  </div>
</template>

<style scoped>
.slide-ghost {
  opacity: 0.4;
  border-color: #3B7AB1 !important;
  background: rgba(59, 122, 177, 0.1);
}

.scrollbar-thin::-webkit-scrollbar {
  height: 4px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 2px;
}

.dark .scrollbar-thin::-webkit-scrollbar-thumb {
  background: #4b5563;
}
</style>
