<script setup>
/**
 * ShotListCard - Displays a single shot list as a checklist with share functionality.
 *
 * Shows shot list title, metadata, progress bar, individual shots as checklist items,
 * and share/delete actions.
 */
import { computed } from 'vue'

const props = defineProps({
  shotList: { type: Object, required: true },
  expanded: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle', 'share', 'delete', 'open'])

const progress = computed(() => {
  if (!props.shotList.shots_total) return 0
  return Math.round((props.shotList.shots_completed / props.shotList.shots_total) * 100)
})

const statusLabel = computed(() => {
  const map = {
    active: 'Aktiv',
    completed: 'Abgeschlossen',
    archived: 'Archiviert',
  }
  return map[props.shotList.status] || props.shotList.status
})

const statusColor = computed(() => {
  const map = {
    active: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    completed: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    archived: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
  }
  return map[props.shotList.status] || 'bg-gray-100 text-gray-600'
})

const countryLabels = {
  usa: 'USA',
  canada: 'Kanada',
  australia: 'Australien',
  newzealand: 'Neuseeland',
  ireland: 'Irland',
}

const countryFlag = computed(() => {
  const flags = { usa: '🇺🇸', canada: '🇨🇦', australia: '🇦🇺', newzealand: '🇳🇿', ireland: '🇮🇪' }
  return flags[props.shotList.country] || '🌍'
})

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-200 dark:border-gray-700 overflow-hidden transition-shadow hover:shadow-md">
    <!-- Card Header -->
    <div class="p-4 cursor-pointer" @click="emit('toggle', shotList.id)">
      <div class="flex items-start justify-between">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-lg">{{ countryFlag }}</span>
            <h3 class="font-semibold text-gray-900 dark:text-white truncate">
              {{ shotList.title }}
            </h3>
          </div>
          <div class="flex items-center gap-2 flex-wrap text-xs text-gray-500 dark:text-gray-400">
            <span :class="[statusColor, 'px-2 py-0.5 rounded-full font-medium']">
              {{ statusLabel }}
            </span>
            <span v-if="shotList.student_name">{{ shotList.student_name }}</span>
            <span v-if="shotList.country">{{ countryLabels[shotList.country] || shotList.country }}</span>
            <span>{{ shotList.shots_total }} Shots</span>
            <span v-if="shotList.created_at">{{ formatDate(shotList.created_at) }}</span>
          </div>
        </div>

        <!-- Expand/Collapse icon -->
        <svg
          :class="['w-5 h-5 text-gray-400 transition-transform', expanded ? 'rotate-180' : '']"
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      <!-- Progress Bar -->
      <div class="mt-3">
        <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
          <span>{{ shotList.shots_completed }}/{{ shotList.shots_total }} Shots</span>
          <span>{{ progress }}%</span>
        </div>
        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            class="h-2 rounded-full transition-all duration-500"
            :class="progress >= 100 ? 'bg-green-500' : 'bg-blue-500'"
            :style="{ width: progress + '%' }"
          />
        </div>
      </div>
    </div>

    <!-- Expanded: Shot Details -->
    <div v-if="expanded" class="border-t border-gray-200 dark:border-gray-700">
      <div class="p-4 space-y-3">
        <div
          v-for="shot in (shotList.shots || [])"
          :key="shot.shot_number"
          :class="[
            'p-3 rounded-lg border transition-colors',
            shot.completed
              ? 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800'
              : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600'
          ]"
        >
          <div class="flex items-start gap-3">
            <!-- Shot Number -->
            <div
              :class="[
                'w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0',
                shot.completed
                  ? 'bg-green-500 text-white'
                  : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
              ]"
            >
              <span v-if="shot.completed">&#10003;</span>
              <span v-else>{{ shot.shot_number }}</span>
            </div>

            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-900 dark:text-white">
                {{ shot.description_for_student }}
              </p>
              <p v-if="shot.example" class="text-xs text-gray-500 dark:text-gray-400 mt-1 italic">
                Beispiel: {{ shot.example }}
              </p>
              <div class="flex items-center gap-3 mt-2 text-xs text-gray-400 dark:text-gray-500">
                <span v-if="shot.duration_hint" class="flex items-center gap-1">
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  {{ shot.duration_hint }}
                </span>
                <span v-if="shot.orientation" class="flex items-center gap-1">
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                  {{ shot.orientation }}
                </span>
                <span v-if="shot.lighting_tip" class="flex items-center gap-1">
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
                  {{ shot.lighting_tip }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="px-4 pb-4 flex items-center gap-2 flex-wrap">
        <button
          @click.stop="emit('open', shotList.id)"
          class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Öffnen
        </button>
        <button
          @click.stop="emit('share', shotList.id)"
          :class="[
            'px-3 py-1.5 text-sm rounded-lg transition-colors flex items-center gap-1',
            shotList.is_shared
              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 hover:bg-green-200'
              : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200'
          ]"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>
          {{ shotList.is_shared ? 'Geteilt' : 'Teilen' }}
        </button>
        <button
          @click.stop="emit('delete', shotList.id)"
          class="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
        >
          Loeschen
        </button>
      </div>
    </div>
  </div>
</template>
