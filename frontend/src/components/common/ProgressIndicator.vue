<script setup>
/**
 * ProgressIndicator — Background Task Monitor
 *
 * Appears in the TopBar when background tasks are active.
 * Shows a compact progress badge + expandable dropdown with task details.
 * Polls the backend for task status updates.
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useBackgroundTasks } from '@/composables/useBackgroundTasks'

const {
  activeTasks,
  activeTaskCount,
  hasActiveTasks,
  startPolling,
  stopPolling,
  cancelTask,
} = useBackgroundTasks()

const showDropdown = ref(false)
const recentlyCompleted = ref([])

// Track tasks that just finished to show briefly in the indicator
watch(activeTasks, (newTasks, oldTasks) => {
  if (!oldTasks) return
  const newIds = new Set(newTasks.map(t => t.task_id))
  const finished = (oldTasks || []).filter(t => !newIds.has(t.task_id))
  if (finished.length > 0) {
    for (const t of finished) {
      recentlyCompleted.value.push({ ...t, status: 'completed', _fadeAt: Date.now() + 5000 })
    }
    // Auto-remove after 5s
    setTimeout(() => {
      recentlyCompleted.value = recentlyCompleted.value.filter(t => t._fadeAt > Date.now())
    }, 5200)
  }
})

onMounted(() => {
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})

const allDisplayTasks = computed(() => {
  return [...activeTasks.value, ...recentlyCompleted.value]
})

const hasVisibleTasks = computed(() => allDisplayTasks.value.length > 0)

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

function statusColor(status) {
  const colors = {
    pending: 'text-yellow-500',
    processing: 'text-blue-500',
    completed: 'text-green-500',
    failed: 'text-red-500',
    cancelled: 'text-gray-400',
  }
  return colors[status] || 'text-gray-500'
}

function progressPercent(task) {
  return Math.round((task.progress || 0) * 100)
}

async function handleCancel(taskId) {
  try {
    await cancelTask(taskId)
  } catch (err) {
    // Handled by API interceptor
  }
}

function toggleDropdown() {
  showDropdown.value = !showDropdown.value
}

// Close dropdown when clicking outside
function handleClickOutside(e) {
  if (!e.target.closest('[data-progress-indicator]')) {
    showDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div v-if="hasVisibleTasks" class="relative" data-progress-indicator data-testid="progress-indicator">
    <!-- Compact badge button -->
    <button
      @click="toggleDropdown"
      class="relative flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium transition-colors"
      :class="hasActiveTasks
        ? 'bg-blue-50 text-treff-blue hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400 dark:hover:bg-blue-900/50'
        : 'bg-green-50 text-green-600 hover:bg-green-100 dark:bg-green-900/30 dark:text-green-400 dark:hover:bg-green-900/50'"
      :aria-label="`${activeTaskCount} Hintergrund-Aufgaben`"
    >
      <!-- Spinner for active tasks -->
      <svg v-if="hasActiveTasks" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
      <!-- Checkmark for recently completed -->
      <svg v-else class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
      </svg>
      <span>{{ activeTaskCount > 0 ? activeTaskCount : '' }}</span>
    </button>

    <!-- Dropdown panel -->
    <Transition
      enter-active-class="transition ease-out duration-150"
      enter-from-class="opacity-0 scale-95 -translate-y-1"
      enter-to-class="opacity-100 scale-100 translate-y-0"
      leave-active-class="transition ease-in duration-100"
      leave-from-class="opacity-100 scale-100 translate-y-0"
      leave-to-class="opacity-0 scale-95 -translate-y-1"
    >
      <div
        v-if="showDropdown"
        class="absolute right-0 top-full mt-2 z-50 w-80 rounded-xl border border-gray-200 bg-white shadow-lg dark:bg-gray-800 dark:border-gray-700"
        data-testid="progress-dropdown"
      >
        <!-- Header -->
        <div class="flex items-center justify-between border-b border-gray-100 px-4 py-2.5 dark:border-gray-700">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Hintergrund-Aufgaben</h3>
          <span class="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-300">
            {{ allDisplayTasks.length }}
          </span>
        </div>

        <!-- Task list -->
        <div class="max-h-64 overflow-y-auto p-2">
          <div
            v-for="task in allDisplayTasks"
            :key="task.task_id"
            class="mb-1.5 rounded-lg border border-gray-100 bg-gray-50 p-3 last:mb-0 dark:border-gray-700 dark:bg-gray-750"
            :data-testid="`task-item-${task.task_id}`"
          >
            <div class="flex items-start justify-between gap-2">
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {{ task.title }}
                </p>
                <p class="mt-0.5 text-xs" :class="statusColor(task.status)">
                  {{ statusLabel(task.status) }}
                  <span v-if="task.status === 'processing'">
                    — {{ progressPercent(task) }}%
                  </span>
                </p>
              </div>
              <!-- Cancel button for active tasks -->
              <button
                v-if="task.status === 'pending' || task.status === 'processing'"
                @click.stop="handleCancel(task.task_id)"
                class="flex-shrink-0 rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-900/30"
                aria-label="Abbrechen"
                :data-testid="`cancel-task-${task.task_id}`"
              >
                <svg class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
              </button>
              <!-- Status icon for completed -->
              <span v-else-if="task.status === 'completed'" class="flex-shrink-0 text-green-500">
                <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                </svg>
              </span>
              <!-- Error icon for failed -->
              <span v-else-if="task.status === 'failed'" class="flex-shrink-0 text-red-500">
                <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                </svg>
              </span>
            </div>

            <!-- Progress bar for processing tasks -->
            <div v-if="task.status === 'processing'" class="mt-2">
              <div class="h-1.5 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-600">
                <div
                  class="h-full rounded-full bg-treff-blue transition-all duration-300 ease-out"
                  :style="{ width: progressPercent(task) + '%' }"
                />
              </div>
            </div>

            <!-- Error message for failed tasks -->
            <p v-if="task.error" class="mt-1 text-xs text-red-500 truncate" :title="task.error">
              {{ task.error }}
            </p>
          </div>

          <!-- Empty state -->
          <div v-if="allDisplayTasks.length === 0" class="py-4 text-center text-sm text-gray-400">
            Keine aktiven Aufgaben
          </div>
        </div>

        <!-- Footer link to history -->
        <div class="border-t border-gray-100 px-4 py-2 dark:border-gray-700">
          <router-link
            to="/settings?tab=tasks"
            class="text-xs font-medium text-treff-blue hover:underline dark:text-blue-400"
            @click="showDropdown = false"
          >
            Alle Aufgaben anzeigen →
          </router-link>
        </div>
      </div>
    </Transition>
  </div>
</template>
