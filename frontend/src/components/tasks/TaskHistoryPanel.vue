<script setup>
/**
 * TaskHistoryPanel — Shows recent background task history
 *
 * Displays last N background tasks with status, progress, timestamps, and error info.
 * Can be embedded in Settings or shown standalone.
 */
import { ref, computed, onMounted } from 'vue'
import { useBackgroundTasks } from '@/composables/useBackgroundTasks'
import { useToast } from '@/composables/useToast'
import BaseCard from '@/components/common/BaseCard.vue'

const {
  taskHistory,
  taskHistoryTotal,
  fetchTaskHistory,
  submitDemoTask,
} = useBackgroundTasks()

const toast = useToast()
const loading = ref(false)
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = 10
const submittingDemo = ref(false)

const totalPages = computed(() => Math.max(1, Math.ceil(taskHistoryTotal.value / pageSize)))

async function loadHistory() {
  loading.value = true
  try {
    await fetchTaskHistory(
      statusFilter.value || null,
      pageSize,
      (currentPage.value - 1) * pageSize
    )
  } finally {
    loading.value = false
  }
}

async function handleDemoTask(shouldFail = false) {
  submittingDemo.value = true
  try {
    const result = await submitDemoTask(
      shouldFail ? 'Fehlschlag-Demo' : 'Hintergrund-Demo',
      shouldFail ? 8 : 6,
      shouldFail
    )
    toast.success(`Task "${result.title}" gestartet (ID: ${result.task_id})`)
    setTimeout(() => loadHistory(), 2000)
  } catch (err) {
    toast.error('Fehler beim Starten des Demo-Tasks')
  } finally {
    submittingDemo.value = false
  }
}

function changeFilter(filter) {
  statusFilter.value = filter
  currentPage.value = 1
  loadHistory()
}

function changePage(page) {
  currentPage.value = page
  loadHistory()
}

function statusLabel(status) {
  const labels = {
    pending: 'Wartend',
    processing: 'Verarbeitung',
    completed: 'Abgeschlossen',
    failed: 'Fehlgeschlagen',
    cancelled: 'Abgebrochen',
  }
  return labels[status] || status
}

function statusBadgeClass(status) {
  const classes = {
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    processing: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    cancelled: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
  }
  return classes[status] || 'bg-gray-100 text-gray-600'
}

function typeIcon(taskType) {
  const icons = {
    ai_image: '🎨',
    bulk_export: '📦',
    report_pdf: '📄',
    template_render: '🖼️',
    demo: '🧪',
  }
  return icons[taskType] || '⚙️'
}

function formatDate(isoString) {
  if (!isoString) return '—'
  const d = new Date(isoString)
  return d.toLocaleString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatDuration(task) {
  if (!task.started_at || !task.completed_at) return '—'
  const start = new Date(task.started_at)
  const end = new Date(task.completed_at)
  const seconds = Math.round((end - start) / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds}s`
}

onMounted(() => {
  loadHistory()
})
</script>

<template>
  <BaseCard padding="none" data-testid="task-history-panel">
    <div class="border-b border-gray-100 px-6 py-4 dark:border-gray-700">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <span>⚡</span> Hintergrund-Aufgaben
          </h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            Verlauf der letzten Hintergrund-Operationen (KI-Bilder, Export, Reports)
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="handleDemoTask(false)"
            :disabled="submittingDemo"
            class="rounded-lg bg-treff-blue px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
            data-testid="submit-demo-task"
          >
            {{ submittingDemo ? 'Startet...' : 'Demo-Task starten' }}
          </button>
          <button
            @click="loadHistory"
            :disabled="loading"
            class="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
          >
            ↻ Aktualisieren
          </button>
        </div>
      </div>
    </div>

    <!-- Status filter -->
    <div class="flex items-center gap-2 px-6 py-3 border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50">
      <span class="text-xs font-medium text-gray-500 dark:text-gray-400">Filter:</span>
      <button
        v-for="filter in [
          { value: '', label: 'Alle' },
          { value: 'completed', label: 'Abgeschlossen' },
          { value: 'failed', label: 'Fehlgeschlagen' },
          { value: 'processing', label: 'Aktiv' },
          { value: 'cancelled', label: 'Abgebrochen' },
        ]"
        :key="filter.value"
        @click="changeFilter(filter.value)"
        class="rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors"
        :class="statusFilter === filter.value
          ? 'bg-treff-blue text-white'
          : 'bg-gray-200 text-gray-600 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'"
      >
        {{ filter.label }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="py-8 text-center text-gray-400">
      <svg class="mx-auto h-6 w-6 animate-spin" viewBox="0 0 24 24" fill="none">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <p class="mt-2 text-sm">Lade Aufgaben...</p>
    </div>

    <!-- Task list -->
    <div v-else-if="taskHistory.length > 0" class="divide-y divide-gray-100 dark:divide-gray-700">
      <div
        v-for="task in taskHistory"
        :key="task.task_id"
        class="flex items-start gap-3 px-6 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
        :data-testid="`history-task-${task.task_id}`"
      >
        <!-- Type icon -->
        <span class="mt-0.5 text-lg">{{ typeIcon(task.task_type) }}</span>

        <!-- Details -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
              {{ task.title }}
            </p>
            <span
              class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
              :class="statusBadgeClass(task.status)"
            >
              {{ statusLabel(task.status) }}
            </span>
          </div>
          <div class="mt-0.5 flex flex-wrap items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
            <span>ID: {{ task.task_id }}</span>
            <span>Erstellt: {{ formatDate(task.created_at) }}</span>
            <span v-if="task.completed_at">Dauer: {{ formatDuration(task) }}</span>
          </div>
          <!-- Error display -->
          <p v-if="task.error" class="mt-1 rounded bg-red-50 px-2 py-1 text-xs text-red-600 dark:bg-red-900/20 dark:text-red-400">
            {{ task.error }}
          </p>
          <!-- Result summary -->
          <p v-if="task.result && task.status === 'completed' && typeof task.result === 'object' && task.result.message" class="mt-1 text-xs text-green-600 dark:text-green-400">
            {{ task.result.message }}
          </p>
        </div>

        <!-- Progress -->
        <div class="flex-shrink-0 text-right">
          <span class="text-xs font-medium" :class="task.status === 'completed' ? 'text-green-600' : task.status === 'failed' ? 'text-red-500' : 'text-gray-500'">
            {{ Math.round((task.progress || 0) * 100) }}%
          </span>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="py-8 text-center">
      <p class="text-sm text-gray-400 dark:text-gray-500">Keine Aufgaben gefunden</p>
      <p class="mt-1 text-xs text-gray-400">Starte einen Demo-Task, um die Funktion zu testen.</p>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-between border-t border-gray-100 px-6 py-3 dark:border-gray-700">
      <p class="text-xs text-gray-500">
        {{ taskHistoryTotal }} Aufgaben insgesamt
      </p>
      <div class="flex items-center gap-1">
        <button
          :disabled="currentPage <= 1"
          @click="changePage(currentPage - 1)"
          class="rounded px-2 py-1 text-xs font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-40 dark:text-gray-400 dark:hover:bg-gray-700"
        >
          ←
        </button>
        <span class="px-2 text-xs text-gray-500">{{ currentPage }} / {{ totalPages }}</span>
        <button
          :disabled="currentPage >= totalPages"
          @click="changePage(currentPage + 1)"
          class="rounded px-2 py-1 text-xs font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-40 dark:text-gray-400 dark:hover:bg-gray-700"
        >
          →
        </button>
      </div>
    </div>
  </BaseCard>
</template>
