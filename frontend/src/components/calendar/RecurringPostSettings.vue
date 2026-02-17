<script setup>
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import api from '@/utils/api'

const props = defineProps({
  show: { type: Boolean, default: false },
  postId: { type: Number, default: null },
  postTitle: { type: String, default: '' },
  postScheduledDate: { type: String, default: null },
})

const emit = defineEmits(['close', 'created', 'deleted'])

const auth = useAuthStore()
const toast = useToast()

// Rule config
const frequency = ref('weekly')
const weekday = ref(0) // 0=Mon
const dayOfMonth = ref(1)
const time = ref('10:00')
const endType = ref('occurrences') // 'date' | 'occurrences' | 'none'
const endDate = ref('')
const maxOccurrences = ref(8)

// State
const loading = ref(false)
const existingRule = ref(null)
const loadingRule = ref(false)

const weekdays = [
  { value: 0, label: 'Montag' },
  { value: 1, label: 'Dienstag' },
  { value: 2, label: 'Mittwoch' },
  { value: 3, label: 'Donnerstag' },
  { value: 4, label: 'Freitag' },
  { value: 5, label: 'Samstag' },
  { value: 6, label: 'Sonntag' },
]

const frequencyOptions = [
  { value: 'weekly', label: 'Woechentlich', desc: 'Jede Woche am gleichen Tag' },
  { value: 'biweekly', label: 'Alle 2 Wochen', desc: 'Jeden zweiten Woche' },
  { value: 'monthly', label: 'Monatlich', desc: 'Einmal pro Monat am gleichen Tag' },
]

// Summary text
const summaryText = computed(() => {
  const freq = frequencyOptions.find(f => f.value === frequency.value)
  const dayLabel = frequency.value === 'monthly'
    ? `am ${dayOfMonth.value}. des Monats`
    : `am ${weekdays[weekday.value]?.label || 'Montag'}`

  let end = ''
  if (endType.value === 'occurrences') {
    end = `, ${maxOccurrences.value}x`
  } else if (endType.value === 'date' && endDate.value) {
    const d = new Date(endDate.value)
    end = ` bis ${d.toLocaleDateString('de-DE')}`
  }

  return `${freq?.label || ''} ${dayLabel} um ${time.value}${end}`
})

// Set defaults from post's scheduled date
watch(() => props.show, async (newVal) => {
  if (newVal && props.postId) {
    // Set weekday from scheduled date
    if (props.postScheduledDate) {
      const d = new Date(props.postScheduledDate)
      const jsDay = d.getDay()
      // JS: 0=Sun, 1=Mon... Python: 0=Mon, 6=Sun
      weekday.value = jsDay === 0 ? 6 : jsDay - 1
    }

    // Check if rule already exists
    await loadExistingRule()
  }
})

async function loadExistingRule() {
  loadingRule.value = true
  try {
    const { data: rules } = await api.get('/api/recurring-posts')
    const found = rules.find(r => r.source_post_id === props.postId)
    if (found) {
      existingRule.value = found
      // Populate form from existing rule
      frequency.value = found.frequency
      if (found.weekday !== null) weekday.value = found.weekday
      if (found.day_of_month !== null) dayOfMonth.value = found.day_of_month
      time.value = found.time || '10:00'
      if (found.end_date) {
        endType.value = 'date'
        endDate.value = found.end_date.split('T')[0]
      } else if (found.max_occurrences) {
        endType.value = 'occurrences'
        maxOccurrences.value = found.max_occurrences
      } else {
        endType.value = 'none'
      }
    } else {
      existingRule.value = null
    }
  } catch (err) {
    console.error('Error loading recurring rule:', err)
  } finally {
    loadingRule.value = false
  }
}

async function createRule() {
  loading.value = true
  try {
    const body = {
      source_post_id: props.postId,
      frequency: frequency.value,
      time: time.value,
      generate_ahead_weeks: 4,
    }

    if (frequency.value === 'monthly') {
      body.day_of_month = dayOfMonth.value
    } else {
      body.weekday = weekday.value
    }

    if (endType.value === 'date' && endDate.value) {
      body.end_date = endDate.value
    } else if (endType.value === 'occurrences') {
      body.max_occurrences = maxOccurrences.value
    }

    const { data: result } = await api.post('/api/recurring-posts', body)
    toast.success(`Wiederkehrend: ${result.generated_instances} Posts erstellt`)
    existingRule.value = result
    emit('created', result)
    close()
  } catch (err) {
    // Error toast shown by interceptor
  } finally {
    loading.value = false
  }
}

async function deleteRule() {
  if (!existingRule.value) return
  loading.value = true
  try {
    const { data: result } = await api.delete(`/api/recurring-posts/${existingRule.value.id}?delete_future=true`)
    toast.success(`Wiederkehr-Regel geloescht (${result.deleted_future_instances} zukuenftige Posts entfernt)`)
    existingRule.value = null
    emit('deleted')
    close()
  } catch (err) {
    // Error toast shown by interceptor
  } finally {
    loading.value = false
  }
}

function close() {
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      @click.self="close"
    >
      <div
        class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-lg mx-4 max-h-[85vh] flex flex-col overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-label="Wiederkehrende Post Einstellungen"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <span class="text-xl">🔁</span>
              Wiederkehrender Post
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5 truncate max-w-[300px]">{{ postTitle }}</p>
          </div>
          <button
            @click="close"
            class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="Schliessen"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto px-6 py-5 space-y-5">

          <!-- Loading -->
          <div v-if="loadingRule" class="flex items-center justify-center py-8">
            <svg class="w-6 h-6 animate-spin text-blue-500" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>

          <template v-else>
            <!-- Existing Rule Info -->
            <div v-if="existingRule" class="p-4 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
              <div class="flex items-center gap-2 text-blue-700 dark:text-blue-300 font-medium mb-1">
                <span>🔁</span>
                Aktive Wiederkehr-Regel
              </div>
              <div class="text-sm text-blue-600 dark:text-blue-400">
                {{ existingRule.frequency_label }} &mdash;
                {{ existingRule.weekday_label || `Tag ${existingRule.day_of_month}` }}
                um {{ existingRule.time }}
              </div>
              <div class="text-xs text-blue-500 dark:text-blue-500 mt-1">
                {{ existingRule.generated_count }} Instanzen generiert
              </div>
            </div>

            <!-- Frequency -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Frequenz</label>
              <div class="space-y-2">
                <label
                  v-for="opt in frequencyOptions"
                  :key="opt.value"
                  :class="[
                    'flex items-center gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all',
                    frequency === opt.value
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  ]"
                >
                  <input type="radio" :value="opt.value" v-model="frequency" class="sr-only" />
                  <div
                    :class="[
                      'w-4 h-4 rounded-full border-2 flex items-center justify-center',
                      frequency === opt.value ? 'border-blue-500 bg-blue-500' : 'border-gray-300 dark:border-gray-600'
                    ]"
                  >
                    <div v-if="frequency === opt.value" class="w-2 h-2 bg-white rounded-full"></div>
                  </div>
                  <div class="flex-1">
                    <div class="font-medium text-gray-900 dark:text-white text-sm">{{ opt.label }}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">{{ opt.desc }}</div>
                  </div>
                </label>
              </div>
            </div>

            <!-- Weekday (for weekly/biweekly) -->
            <div v-if="frequency !== 'monthly'">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Wochentag</label>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="day in weekdays"
                  :key="day.value"
                  @click="weekday = day.value"
                  :class="[
                    'px-3 py-1.5 text-sm rounded-lg border transition-colors',
                    weekday === day.value
                      ? 'bg-blue-500 text-white border-blue-500'
                      : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700 hover:border-blue-300'
                  ]"
                >
                  {{ day.label.substring(0, 2) }}
                </button>
              </div>
            </div>

            <!-- Day of month (for monthly) -->
            <div v-if="frequency === 'monthly'">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Tag im Monat</label>
              <select
                v-model.number="dayOfMonth"
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
              >
                <option v-for="d in 28" :key="d" :value="d">{{ d }}.</option>
              </select>
            </div>

            <!-- Time -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Uhrzeit</label>
              <input
                v-model="time"
                type="time"
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
              />
            </div>

            <!-- End Condition -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Ende der Wiederholung</label>
              <div class="space-y-2">
                <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input type="radio" value="occurrences" v-model="endType" class="text-blue-600" />
                  Nach Anzahl Wiederholungen
                </label>
                <div v-if="endType === 'occurrences'" class="ml-6">
                  <input
                    v-model.number="maxOccurrences"
                    type="number"
                    min="1"
                    max="52"
                    class="w-24 px-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
                  />
                  <span class="text-xs text-gray-500 ml-2">Wiederholungen</span>
                </div>

                <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input type="radio" value="date" v-model="endType" class="text-blue-600" />
                  Bis Datum
                </label>
                <div v-if="endType === 'date'" class="ml-6">
                  <input
                    v-model="endDate"
                    type="date"
                    class="w-48 px-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
                  />
                </div>

                <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input type="radio" value="none" v-model="endType" class="text-blue-600" />
                  Kein Ende (manuell stoppen)
                </label>
              </div>
            </div>

            <!-- Summary -->
            <div class="p-3 rounded-xl bg-gray-50 dark:bg-gray-800 text-sm text-gray-600 dark:text-gray-400">
              <span class="font-medium text-gray-700 dark:text-gray-300">Zusammenfassung:</span>
              {{ summaryText }}
            </div>
          </template>
        </div>

        <!-- Footer Actions -->
        <div class="flex gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
          <button
            v-if="existingRule"
            @click="deleteRule"
            :disabled="loading"
            class="px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-xl hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
          >
            Regel loeschen
          </button>
          <div class="flex-1"></div>
          <button
            @click="close"
            class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          >
            Abbrechen
          </button>
          <button
            @click="createRule"
            :disabled="loading"
            class="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-xl transition-colors flex items-center gap-2 text-sm"
          >
            <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ existingRule ? 'Regel aktualisieren' : 'Wiederkehrend machen' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
