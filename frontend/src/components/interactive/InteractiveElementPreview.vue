<script setup>
/**
 * InteractiveElementPreview - Visual preview of Instagram Story interactive elements.
 *
 * Renders Poll, Quiz, EmojiSlider, and QuestionBox overlays on story previews.
 * These are visual simulations - not functional. They remind the user to add
 * these native elements when actually posting to Instagram.
 */
import { computed } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const props = defineProps({
  element: {
    type: Object,
    required: true,
    // { element_type, question_text, options, correct_answer, emoji, position_x, position_y }
  },
  interactive: {
    type: Boolean,
    default: false, // If true, show drag handle
  },
})

const emit = defineEmits(['remove', 'edit'])

const elementStyle = computed(() => ({
  position: 'absolute',
  left: `${Math.max(5, Math.min(95, props.element.position_x || 50)) - 40}%`,
  top: `${Math.max(5, Math.min(95, props.element.position_y || 50)) - 10}%`,
  width: '80%',
  zIndex: 10,
}))

const typeIcon = computed(() => {
  const icons = {
    poll: 'chart-bar',
    quiz: 'sparkles',
    slider: 'slider',
    question: 'question-mark-circle',
  }
  return icons[props.element.element_type] || 'chart-bar'
})

const typeLabel = computed(() => {
  const labels = {
    poll: 'Umfrage',
    quiz: 'Quiz',
    slider: 'Emoji-Slider',
    question: 'Fragen-Sticker',
  }
  return labels[props.element.element_type] || 'Element'
})
</script>

<template>
  <div :style="elementStyle" class="pointer-events-auto" :data-testid="'interactive-element-' + element.element_type">
    <div class="bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm rounded-2xl shadow-xl border border-white/30 p-3 relative">
      <!-- Type badge -->
      <div class="absolute -top-2 -right-2 bg-purple-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-md flex items-center gap-1">
        <AppIcon :name="typeIcon" class="w-3 h-3 inline-block" /> {{ typeLabel }}
      </div>

      <!-- Interactive controls (edit/remove) -->
      <div v-if="interactive" class="absolute -top-2 -left-2 flex gap-1">
        <button
          @click.stop="emit('edit', element)"
          class="w-5 h-5 bg-blue-500 text-white rounded-full flex items-center justify-center text-[10px] shadow-md hover:bg-blue-600 transition-colors"
          title="Bearbeiten"
        >
          &#9998;
        </button>
        <button
          @click.stop="emit('remove', element)"
          class="w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center text-[10px] shadow-md hover:bg-red-600 transition-colors"
          title="Entfernen"
          :data-testid="'remove-interactive-' + element.element_type"
        >
          &times;
        </button>
      </div>

      <!-- POLL Preview -->
      <div v-if="element.element_type === 'poll'" class="space-y-2">
        <p class="text-xs font-bold text-gray-900 dark:text-white text-center leading-tight">
          {{ element.question_text }}
        </p>
        <div class="flex gap-1.5">
          <div
            v-for="(opt, idx) in (element.options || [])"
            :key="idx"
            class="flex-1 py-1.5 rounded-lg text-center text-[11px] font-semibold transition-colors"
            :class="idx === 0 ? 'bg-blue-500 text-white' : 'bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-white'"
          >
            {{ opt }}
          </div>
        </div>
      </div>

      <!-- QUIZ Preview -->
      <div v-else-if="element.element_type === 'quiz'" class="space-y-1.5">
        <p class="text-xs font-bold text-gray-900 dark:text-white text-center leading-tight">
          {{ element.question_text }}
        </p>
        <div class="grid grid-cols-2 gap-1">
          <div
            v-for="(opt, idx) in (element.options || [])"
            :key="idx"
            class="py-1 px-2 rounded-lg text-center text-[10px] font-medium transition-colors"
            :class="idx === element.correct_answer
              ? 'bg-green-500 text-white ring-2 ring-green-300'
              : 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200'"
          >
            {{ opt }}
          </div>
        </div>
      </div>

      <!-- SLIDER Preview -->
      <div v-else-if="element.element_type === 'slider'" class="space-y-2">
        <p class="text-xs font-bold text-gray-900 dark:text-white text-center leading-tight">
          {{ element.question_text }}
        </p>
        <div class="relative h-6 bg-gradient-to-r from-gray-200 to-purple-400 dark:from-gray-600 dark:to-purple-500 rounded-full overflow-hidden">
          <div class="absolute left-[65%] top-1/2 -translate-y-1/2 text-lg">
            {{ element.emoji || '🔥' }}
          </div>
        </div>
      </div>

      <!-- QUESTION Preview -->
      <div v-else-if="element.element_type === 'question'" class="space-y-1.5">
        <p class="text-xs font-bold text-gray-900 dark:text-white text-center leading-tight">
          {{ element.question_text }}
        </p>
        <div class="bg-gray-100 dark:bg-gray-700 rounded-lg px-3 py-2 text-center">
          <span class="text-[10px] text-gray-400 dark:text-gray-500 italic">Antwort eingeben...</span>
        </div>
      </div>
    </div>
  </div>
</template>
