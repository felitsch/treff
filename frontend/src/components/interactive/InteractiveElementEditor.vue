<script setup>
/**
 * InteractiveElementEditor - Panel for managing interactive Story elements.
 *
 * Features:
 * - Add new interactive elements (Poll, Quiz, Slider, Question)
 * - AI-generate element content via POST /api/ai/generate-interactive
 * - Edit existing elements inline
 * - Remove elements
 * - Shows export reminder about adding these in real Instagram
 */
import { ref, computed } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const toast = useToast()

const props = defineProps({
  interactiveElements: {
    type: Array,
    default: () => [],
  },
  slideIndex: {
    type: Number,
    default: 0,
  },
  topic: {
    type: String,
    default: '',
  },
  country: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['update:interactiveElements', 'add', 'remove', 'edit'])

const generating = ref(false)
const selectedType = ref('poll')
const editingElement = ref(null)

const elementTypes = [
  { id: 'poll', label: 'Umfrage', icon: '📊', desc: 'Ja/Nein oder A/B Abstimmung' },
  { id: 'quiz', label: 'Quiz', icon: '🧠', desc: 'Multiple-Choice mit richtiger Antwort' },
  { id: 'slider', label: 'Emoji-Slider', icon: '🎚️', desc: 'Bewertungs-Slider mit Emoji' },
  { id: 'question', label: 'Fragen-Sticker', icon: '❓', desc: 'Offene Frage an die Community' },
]

const currentSlideElements = computed(() =>
  props.interactiveElements.filter(el => el.slide_index === props.slideIndex)
)

async function generateElement() {
  generating.value = true
  try {
    const { data } = await api.post('/api/ai/generate-interactive', {
      element_type: selectedType.value,
      topic: props.topic || 'Highschool-Aufenthalt im Ausland',
      country: props.country,
    })

    if (data.status === 'success' && data.element) {
      const newElement = {
        ...data.element,
        slide_index: props.slideIndex,
        position_x: 50,
        position_y: 50,
        _tempId: Date.now(), // Temporary ID for local state
      }
      emit('add', newElement)
      toast.success(`${elementTypes.find(t => t.id === selectedType.value)?.icon} ${elementTypes.find(t => t.id === selectedType.value)?.label} generiert!`)
    }
  } catch (err) {
    console.error('Failed to generate interactive element:', err)
    toast.error('Fehler beim Generieren des interaktiven Elements.')
  } finally {
    generating.value = false
  }
}

function addManualElement() {
  const defaults = {
    poll: {
      question_text: 'Wuerdest du ein Auslandsjahr machen?',
      options: ['Ja! 🙌', 'Nein'],
      correct_answer: null,
      emoji: null,
    },
    quiz: {
      question_text: 'Wie viele Schueler gehen auf eine typische US-Highschool?',
      options: ['500', '1.500', '3.000', '5.000'],
      correct_answer: 1,
      emoji: null,
    },
    slider: {
      question_text: 'Wie sehr freust du dich auf dein Auslandsjahr?',
      options: null,
      correct_answer: null,
      emoji: '🔥',
    },
    question: {
      question_text: 'Was ist deine groesste Frage zum Auslandsjahr?',
      options: null,
      correct_answer: null,
      emoji: null,
    },
  }

  const newElement = {
    element_type: selectedType.value,
    slide_index: props.slideIndex,
    position_x: 50,
    position_y: 50,
    _tempId: Date.now(),
    source: 'manual',
    ...defaults[selectedType.value],
  }
  emit('add', newElement)
  toast.success('Element hinzugefuegt! Bearbeite den Text nach Bedarf.')
}

function startEdit(element) {
  editingElement.value = { ...element }
}

function saveEdit() {
  if (editingElement.value) {
    emit('edit', editingElement.value)
    editingElement.value = null
    toast.success('Element aktualisiert!')
  }
}

function cancelEdit() {
  editingElement.value = null
}

function removeElement(element) {
  emit('remove', element)
  toast.info('Element entfernt.')
}

function addOption() {
  if (editingElement.value && editingElement.value.options) {
    editingElement.value.options.push('Neue Option')
  }
}

function removeOption(idx) {
  if (editingElement.value && editingElement.value.options && editingElement.value.options.length > 2) {
    editingElement.value.options.splice(idx, 1)
    if (editingElement.value.correct_answer >= editingElement.value.options.length) {
      editingElement.value.correct_answer = 0
    }
  }
}
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4" data-testid="interactive-editor">
    <div class="flex items-center gap-2 mb-3">
      <span class="text-lg">🎯</span>
      <h4 class="font-semibold text-sm text-gray-900 dark:text-white">Interaktive Story-Elemente</h4>
      <span class="text-xs text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/30 px-2 py-0.5 rounded-full font-medium">Instagram Story</span>
    </div>

    <p class="text-xs text-gray-500 dark:text-gray-400 mb-3">
      Fuege Umfragen, Quizze, Slider oder Fragen-Sticker hinzu. Diese werden in der Vorschau simuliert — beim echten Posten musst du sie in Instagram hinzufuegen.
    </p>

    <!-- Type selector -->
    <div class="grid grid-cols-2 gap-2 mb-3">
      <button
        v-for="t in elementTypes"
        :key="t.id"
        @click="selectedType = t.id"
        class="flex items-center gap-2 px-3 py-2 rounded-lg border-2 text-left transition-all text-xs"
        :class="selectedType === t.id
          ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
          : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-500'"
        :data-testid="'select-type-' + t.id"
      >
        <span class="text-base">{{ t.icon }}</span>
        <div>
          <div class="font-semibold">{{ t.label }}</div>
          <div class="text-[10px] opacity-70 leading-tight">{{ t.desc }}</div>
        </div>
      </button>
    </div>

    <!-- Action buttons -->
    <div class="flex gap-2 mb-4">
      <button
        @click="generateElement"
        :disabled="generating"
        class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white text-xs font-bold rounded-lg transition-colors"
        data-testid="generate-interactive-btn"
      >
        <span v-if="generating" class="animate-spin h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full"></span>
        <span v-else>✨</span>
        {{ generating ? 'Generiere...' : 'KI generieren' }}
      </button>
      <button
        @click="addManualElement"
        class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 border-2 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-xs font-bold rounded-lg hover:border-purple-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors"
        data-testid="add-manual-interactive-btn"
      >
        <span>+</span> Manuell erstellen
      </button>
    </div>

    <!-- Current elements for this slide -->
    <div v-if="currentSlideElements.length > 0" class="space-y-2">
      <div class="text-xs font-medium text-gray-600 dark:text-gray-400 flex items-center gap-1">
        <span>Elemente auf Slide {{ slideIndex + 1 }}:</span>
        <span class="bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 px-1.5 py-0.5 rounded-full text-[10px] font-bold">{{ currentSlideElements.length }}</span>
      </div>

      <div
        v-for="(el, idx) in currentSlideElements"
        :key="el.id || el._tempId || idx"
        class="flex items-center gap-2 p-2 rounded-lg bg-gray-50 dark:bg-gray-700/50 border border-gray-100 dark:border-gray-700"
        :data-testid="'element-item-' + el.element_type"
      >
        <span class="text-base">{{ elementTypes.find(t => t.id === el.element_type)?.icon }}</span>
        <div class="flex-1 min-w-0">
          <div class="text-xs font-semibold text-gray-800 dark:text-gray-200 truncate">{{ el.question_text }}</div>
          <div class="text-[10px] text-gray-500 dark:text-gray-400">
            {{ elementTypes.find(t => t.id === el.element_type)?.label }}
            <span v-if="el.source" class="ml-1 text-purple-500">({{ el.source === 'gemini' ? 'KI' : 'Manuell' }})</span>
          </div>
        </div>
        <button
          @click="startEdit(el)"
          class="p-1 text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
          title="Bearbeiten"
        >
          &#9998;
        </button>
        <button
          @click="removeElement(el)"
          class="p-1 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 transition-colors"
          title="Entfernen"
          :data-testid="'remove-element-' + el.element_type"
        >
          &times;
        </button>
      </div>
    </div>

    <div v-else class="text-xs text-gray-400 dark:text-gray-500 text-center py-3 italic">
      Noch keine interaktiven Elemente auf dieser Slide.
    </div>

    <!-- Edit modal -->
    <div v-if="editingElement" class="mt-3 p-3 rounded-lg border-2 border-purple-300 dark:border-purple-600 bg-purple-50 dark:bg-purple-900/20 space-y-2">
      <div class="flex items-center justify-between">
        <span class="text-xs font-bold text-purple-700 dark:text-purple-300">Element bearbeiten</span>
        <button @click="cancelEdit" class="text-xs text-gray-500 hover:text-gray-700">&times; Abbrechen</button>
      </div>

      <div>
        <label class="text-[10px] font-medium text-gray-600 dark:text-gray-400">Frage</label>
        <input
          v-model="editingElement.question_text"
          class="w-full px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-xs text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          data-testid="edit-question-input"
        />
      </div>

      <!-- Options for poll/quiz -->
      <div v-if="editingElement.element_type === 'poll' || editingElement.element_type === 'quiz'">
        <label class="text-[10px] font-medium text-gray-600 dark:text-gray-400">Optionen</label>
        <div class="space-y-1">
          <div v-for="(opt, idx) in editingElement.options" :key="idx" class="flex items-center gap-1">
            <input
              v-model="editingElement.options[idx]"
              class="flex-1 px-2 py-1 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-xs text-gray-900 dark:text-white"
            />
            <button
              v-if="editingElement.element_type === 'quiz'"
              @click="editingElement.correct_answer = idx"
              class="px-1.5 py-1 rounded text-[10px] font-bold transition-colors"
              :class="editingElement.correct_answer === idx ? 'bg-green-500 text-white' : 'bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300'"
              :title="'Als richtig markieren'"
            >
              &#10004;
            </button>
            <button
              v-if="editingElement.options.length > 2"
              @click="removeOption(idx)"
              class="text-red-500 text-xs hover:text-red-700"
            >&times;</button>
          </div>
        </div>
        <button
          v-if="editingElement.options && editingElement.options.length < 4"
          @click="addOption"
          class="mt-1 text-[10px] text-purple-600 dark:text-purple-400 hover:underline"
        >+ Option hinzufuegen</button>
      </div>

      <!-- Emoji for slider -->
      <div v-if="editingElement.element_type === 'slider'">
        <label class="text-[10px] font-medium text-gray-600 dark:text-gray-400">Emoji</label>
        <input
          v-model="editingElement.emoji"
          class="w-20 px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm text-center"
          maxlength="2"
        />
      </div>

      <button
        @click="saveEdit"
        class="w-full py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-lg transition-colors"
        data-testid="save-edit-btn"
      >
        Speichern
      </button>
    </div>

    <!-- Export reminder -->
    <div class="mt-3 p-2.5 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800" data-testid="interactive-export-reminder">
      <div class="flex items-start gap-2">
        <span class="text-sm">💡</span>
        <p class="text-[11px] text-amber-700 dark:text-amber-300 leading-relaxed">
          <strong>Vergiss nicht:</strong> Interaktive Elemente (Umfragen, Quizze, Slider, Fragen) muessen beim echten Posten in Instagram manuell hinzugefuegt werden! Die Vorschau hier zeigt dir, wo und wie sie aussehen sollen.
        </p>
      </div>
    </div>
  </div>
</template>
