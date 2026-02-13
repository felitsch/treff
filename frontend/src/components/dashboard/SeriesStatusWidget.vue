<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/utils/api'

const loading = ref(true)
const seriesData = ref(null)
const error = ref(null)

// Emojis as JS string constants (these render correctly in Vue templates via interpolation)
const booksEmoji = '\uD83D\uDCDA'
const calendarEmoji = '\uD83D\uDCC5'
const stopwatchEmoji = '\u23F1\uFE0F'
const warningEmoji = '\u26A0\uFE0F'
const hourglassEmoji = '\u23F3'

async function fetchSeriesStatus() {
  loading.value = true
  error.value = null
  try {
    const response = await api.get('/api/series-reminders/series-status')
    seriesData.value = response.data
  } catch (err) {
    error.value = 'Serien-Status konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function statusBadgeClass(status) {
  const classes = {
    active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
    paused: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
    draft: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
    completed: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  }
  return classes[status] || 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
}

function statusLabel(status) {
  const labels = {
    active: 'Aktiv',
    paused: 'Pausiert',
    draft: 'Entwurf',
    completed: 'Abgeschlossen',
  }
  return labels[status] || status
}

function countryFlag(country) {
  const flags = {
    usa: '\uD83C\uDDFA\uD83C\uDDF8',
    kanada: '\uD83C\uDDE8\uD83C\uDDE6',
    australien: '\uD83C\uDDE6\uD83C\uDDFA',
    neuseeland: '\uD83C\uDDF3\uD83C\uDDFF',
    irland: '\uD83C\uDDEE\uD83C\uDDEA',
  }
  return flags[country] || ''
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr + 'T00:00:00')
    return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' })
  } catch {
    return dateStr
  }
}

function dueUrgencyClass(daysUntil) {
  if (daysUntil === null || daysUntil === undefined) return 'text-gray-400'
  if (daysUntil <= 0) return 'text-red-500 font-semibold'
  if (daysUntil <= 1) return 'text-orange-500 font-medium'
  return 'text-gray-500'
}

function pauseUrgencyClass(daysSince) {
  if (daysSince === null || daysSince === undefined) return ''
  if (daysSince >= 5) return 'text-red-500'
  if (daysSince >= 3) return 'text-orange-500'
  return ''
}

const hasSeries = computed(() => seriesData.value && seriesData.value.series && seriesData.value.series.length > 0)

onMounted(() => {
  fetchSeriesStatus()
})
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
    <div class="p-5 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
        <span>{{ booksEmoji }}</span> Serien-Status
      </h2>
      <div v-if="seriesData" class="flex items-center gap-2">
        <span
          v-if="seriesData.active_count > 0"
          class="text-xs font-medium px-2.5 py-1 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
        >
          {{ seriesData.active_count }} aktiv
        </span>
        <span
          v-if="seriesData.overdue_count > 0"
          class="text-xs font-medium px-2.5 py-1 rounded-full bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
          data-testid="overdue-badge"
        >
          {{ seriesData.overdue_count }} ueberfaellig
        </span>
      </div>
    </div>

    <div class="p-5">
      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center py-6">
        <span class="animate-spin text-xl">{{ hourglassEmoji }}</span>
        <span class="ml-2 text-sm text-gray-400">Lade Serien-Status...</span>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="text-center py-6">
        <p class="text-sm text-red-500">{{ error }}</p>
        <button
          @click="fetchSeriesStatus"
          class="mt-2 text-xs text-treff-blue hover:text-blue-600"
        >
          Erneut versuchen
        </button>
      </div>

      <!-- Empty state -->
      <div v-else-if="!hasSeries" class="text-center py-6">
        <div class="text-3xl mb-2">{{ booksEmoji }}</div>
        <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Keine Serien vorhanden</p>
        <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
          Erstelle eine Story-Serie, um den Status hier zu verfolgen.
        </p>
      </div>

      <!-- Series list -->
      <div v-else class="space-y-3">
        <div
          v-for="series in seriesData.series"
          :key="series.id"
          class="border border-gray-100 dark:border-gray-700 rounded-lg p-3 hover:border-treff-blue/30 dark:hover:border-treff-blue/40 transition-colors"
          data-testid="series-status-item"
        >
          <!-- Top: Title + Status + Country -->
          <div class="flex items-center gap-2 mb-2">
            <span v-if="series.country" class="text-sm">{{ countryFlag(series.country) }}</span>
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white truncate flex-1">
              {{ series.title }}
            </h3>
            <span
              class="text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase"
              :class="statusBadgeClass(series.status)"
            >
              {{ statusLabel(series.status) }}
            </span>
          </div>

          <!-- Progress bar -->
          <div class="mb-2">
            <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
              <span>Episode {{ series.current_episode }}/{{ series.planned_episodes }}</span>
              <span>{{ series.progress_percent }}%</span>
            </div>
            <div class="w-full h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-300"
                :class="series.status === 'paused' ? 'bg-yellow-400' : 'bg-treff-blue'"
                :style="{ width: series.progress_percent + '%' }"
              ></div>
            </div>
          </div>

          <!-- Bottom info row -->
          <div class="flex items-center gap-3 text-xs">
            <!-- Next due -->
            <span v-if="series.next_due_date" :class="dueUrgencyClass(series.days_until_next)">
              {{ calendarEmoji }} Naechste: {{ formatDate(series.next_due_date) }}
              <span v-if="series.next_due_time"> {{ series.next_due_time }}</span>
              <span v-if="series.days_until_next !== null">
                ({{ series.days_until_next <= 0 ? 'Heute!' : series.days_until_next === 1 ? 'Morgen' : `in ${series.days_until_next} Tagen` }})
              </span>
            </span>

            <!-- Days since last -->
            <span
              v-if="series.days_since_last_episode !== null && series.status === 'active'"
              :class="pauseUrgencyClass(series.days_since_last_episode)"
            >
              {{ stopwatchEmoji }} Letzte vor {{ series.days_since_last_episode }} Tag{{ series.days_since_last_episode !== 1 ? 'en' : '' }}
            </span>

            <!-- No episodes info -->
            <span
              v-if="!series.next_due_date && series.days_since_last_episode === null && series.status === 'active'"
              class="text-orange-500"
            >
              {{ warningEmoji }} Keine Episoden geplant
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
