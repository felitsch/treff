<script setup>
/**
 * SmartScheduler.vue — KI-basierte Posting-Zeit-Vorschlaege
 *
 * Shows:
 * - Recommended time slots (heatmap-style, clickable)
 * - "Bester Zeitpunkt" one-click button
 * - Warnings for suboptimal times / over-posting / conflicts
 * - Platform-specific tips
 * - Mini calendar with already scheduled posts
 * - Date picker for target date
 */
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/utils/api'

const props = defineProps({
  platform: { type: String, default: 'instagram_feed' },
  modelValue: { type: Object, default: () => ({ date: '', time: '' }) },
})

const emit = defineEmits(['update:modelValue'])

// ─── State ───────────────────────────────────────────────────────
const loading = ref(false)
const scheduleData = ref(null)
const selectedDate = ref('')
const selectedTime = ref('')
const showHeatmap = ref(false)

// ─── Computed ────────────────────────────────────────────────────
const recommendedSlots = computed(() => scheduleData.value?.recommended_slots || [])
const warnings = computed(() => scheduleData.value?.warnings || [])
const scheduledPosts = computed(() => scheduleData.value?.scheduled_posts || [])
const bestTime = computed(() => scheduleData.value?.best_time || '17:00')
const platformTip = computed(() => scheduleData.value?.platform_tip || '')
const targetDayName = computed(() => scheduleData.value?.target_day_name || '')
const postsOnTarget = computed(() => scheduleData.value?.posts_on_target_date || 0)

// Heatmap for the target day
const heatmapHours = computed(() => {
  if (!scheduleData.value?.heatmap) return []
  const targetWeekday = scheduleData.value.target_weekday
  const dayData = scheduleData.value.heatmap[targetWeekday]
  if (!dayData) return []
  // Only show hours 6-22
  return dayData.hours.filter(h => h.hour >= 6 && h.hour <= 22)
})

// Mini-calendar: upcoming week with scheduled post counts
const miniCalendar = computed(() => {
  if (!scheduleData.value) return []
  const targetDate = new Date(scheduleData.value.target_date)
  const posts = scheduledPosts.value
  const days = []

  for (let i = -1; i < 7; i++) {
    const d = new Date(targetDate)
    d.setDate(d.getDate() + i)
    const dateStr = d.toISOString().split('T')[0]
    const dayPosts = posts.filter(p => p.date === dateStr)
    const dayNames = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa']
    days.push({
      date: dateStr,
      dayName: dayNames[d.getDay()],
      dayNum: d.getDate(),
      postCount: dayPosts.length,
      isTarget: i === 0,
      isToday: dateStr === new Date().toISOString().split('T')[0],
    })
  }
  return days
})

// ─── Methods ─────────────────────────────────────────────────────
async function fetchScheduleData() {
  loading.value = true
  try {
    const params = { platform: props.platform }
    if (selectedDate.value) params.target_date = selectedDate.value
    const res = await api.get('/api/ai/smart-schedule', { params })
    scheduleData.value = res.data
    if (!selectedDate.value) {
      selectedDate.value = res.data.target_date
    }
  } catch (err) {
    // Handled by interceptor
  } finally {
    loading.value = false
  }
}

function selectTimeSlot(time) {
  selectedTime.value = time
  emit('update:modelValue', { date: selectedDate.value, time })
}

function applyBestTime() {
  selectedTime.value = bestTime.value
  emit('update:modelValue', { date: selectedDate.value, time: bestTime.value })
}

function selectCalendarDay(dateStr) {
  selectedDate.value = dateStr
  fetchScheduleData()
}

function getScoreColor(score) {
  if (score >= 70) return 'bg-green-500'
  if (score >= 40) return 'bg-yellow-400'
  if (score >= 10) return 'bg-orange-300'
  return 'bg-gray-200 dark:bg-gray-700'
}

function getScoreTextColor(score) {
  if (score >= 70) return 'text-green-600 dark:text-green-400'
  if (score >= 40) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-gray-500 dark:text-gray-400'
}

function getWarningStyle(severity) {
  if (severity === 'warning') return 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700 text-yellow-800 dark:text-yellow-300'
  return 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700 text-blue-800 dark:text-blue-300'
}

// ─── Watchers ────────────────────────────────────────────────────
watch(() => props.platform, () => {
  fetchScheduleData()
})

watch(selectedDate, (newDate) => {
  if (newDate) {
    emit('update:modelValue', { date: newDate, time: selectedTime.value })
  }
})

// ─── Lifecycle ───────────────────────────────────────────────────
onMounted(() => {
  // Initialize with tomorrow
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  selectedDate.value = tomorrow.toISOString().split('T')[0]
  fetchScheduleData()
})
</script>

<template>
  <div class="space-y-4" data-testid="smart-scheduler">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-bold text-gray-700 dark:text-gray-300 flex items-center gap-2">
        <span>🤖</span> Smart-Scheduling
      </h3>
      <span v-if="scheduleData" class="text-xs text-gray-400">
        {{ scheduleData.platform_label }}
      </span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-6">
      <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#3B7AB1]"></div>
    </div>

    <template v-else-if="scheduleData">
      <!-- Date Picker Row -->
      <div class="flex items-center gap-3">
        <label class="text-xs font-medium text-gray-500 dark:text-gray-400 whitespace-nowrap">Datum:</label>
        <input
          v-model="selectedDate"
          type="date"
          @change="fetchScheduleData"
          class="flex-1 px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#3B7AB1]"
          data-testid="schedule-date-input"
        />
        <span class="text-xs text-gray-500 dark:text-gray-400">{{ targetDayName }}</span>
      </div>

      <!-- "Bester Zeitpunkt" Button -->
      <button
        @click="applyBestTime"
        class="w-full px-4 py-3 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 bg-gradient-to-r from-[#3B7AB1] to-[#4C8BC2] text-white hover:from-[#2E6A9E] hover:to-[#3B7AB1] shadow-lg shadow-[#3B7AB1]/20"
        data-testid="best-time-btn"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456Z" />
        </svg>
        Bester Zeitpunkt: {{ bestTime }} Uhr
      </button>

      <!-- Recommended Time Slots -->
      <div>
        <div class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Empfohlene Zeiten fuer {{ targetDayName }}:</div>
        <div class="grid grid-cols-5 gap-2" data-testid="recommended-slots">
          <button
            v-for="slot in recommendedSlots"
            :key="slot.hour"
            @click="selectTimeSlot(slot.time)"
            :class="[
              'relative p-2 rounded-lg border-2 text-center transition-all',
              selectedTime === slot.time
                ? 'border-[#3B7AB1] bg-[#3B7AB1]/10 ring-2 ring-[#3B7AB1]/30'
                : slot.conflict
                  ? 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10 opacity-60'
                  : 'border-gray-200 dark:border-gray-600 hover:border-[#3B7AB1]/50 hover:bg-gray-50 dark:hover:bg-gray-700',
            ]"
            :data-testid="'slot-' + slot.hour"
          >
            <div class="text-sm font-bold text-gray-900 dark:text-white">{{ slot.time }}</div>
            <div :class="['text-[10px] font-medium', getScoreTextColor(slot.score)]">
              {{ slot.label }}
            </div>
            <!-- Score bar -->
            <div class="mt-1 h-1 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div :class="['h-full rounded-full', getScoreColor(slot.score)]" :style="{ width: slot.score + '%' }"></div>
            </div>
            <!-- Conflict indicator -->
            <div v-if="slot.conflict" class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center text-white text-[8px]">!</div>
          </button>
        </div>
      </div>

      <!-- Heatmap Toggle -->
      <button
        @click="showHeatmap = !showHeatmap"
        class="w-full text-xs text-[#3B7AB1] hover:text-[#2E6A9E] font-medium py-1"
        data-testid="toggle-heatmap"
      >
        {{ showHeatmap ? '▲ Heatmap ausblenden' : '▼ Heatmap anzeigen' }}
      </button>

      <!-- Heatmap (expandable) -->
      <div v-if="showHeatmap" class="overflow-x-auto" data-testid="heatmap">
        <div class="flex gap-1 min-w-max">
          <div
            v-for="h in heatmapHours"
            :key="h.hour"
            @click="selectTimeSlot(h.label)"
            :class="[
              'w-10 cursor-pointer rounded text-center py-1 transition-all',
              selectedTime === h.label ? 'ring-2 ring-[#3B7AB1]' : '',
            ]"
            :title="`${h.label} — Score: ${h.score}`"
          >
            <div class="text-[9px] text-gray-400 mb-0.5">{{ h.label.split(':')[0] }}</div>
            <div
              class="h-6 rounded-sm mx-0.5"
              :class="[
                h.score >= 70 ? 'bg-green-500' :
                h.score >= 40 ? 'bg-yellow-400' :
                h.score >= 10 ? 'bg-orange-200 dark:bg-orange-800' :
                'bg-gray-100 dark:bg-gray-800'
              ]"
              :style="{ opacity: Math.max(0.3, h.score / 100) }"
            ></div>
          </div>
        </div>
        <div class="flex items-center gap-3 mt-2 text-[10px] text-gray-400">
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-green-500 inline-block"></span> Optimal</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-yellow-400 inline-block"></span> Gut</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-orange-200 dark:bg-orange-800 inline-block"></span> Moeglich</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-gray-100 dark:bg-gray-800 inline-block"></span> Nicht empfohlen</span>
        </div>
      </div>

      <!-- Warnings -->
      <div v-if="warnings.length > 0" class="space-y-2" data-testid="scheduling-warnings">
        <div
          v-for="(warning, i) in warnings"
          :key="i"
          :class="['px-3 py-2 rounded-lg border text-xs', getWarningStyle(warning.severity)]"
        >
          <span class="mr-1">{{ warning.severity === 'warning' ? '⚠️' : 'ℹ️' }}</span>
          {{ warning.message }}
        </div>
      </div>

      <!-- Mini Calendar -->
      <div>
        <div class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Wochenueberblick:</div>
        <div class="grid grid-cols-8 gap-1" data-testid="mini-calendar">
          <div
            v-for="day in miniCalendar"
            :key="day.date"
            @click="selectCalendarDay(day.date)"
            :class="[
              'relative text-center rounded-lg p-2 cursor-pointer transition-all border',
              day.isTarget
                ? 'border-[#3B7AB1] bg-[#3B7AB1]/10 ring-1 ring-[#3B7AB1]/30'
                : day.isToday
                  ? 'border-[#FDD000] bg-[#FDD000]/10'
                  : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700',
            ]"
          >
            <div class="text-[10px] text-gray-400">{{ day.dayName }}</div>
            <div class="text-sm font-bold text-gray-900 dark:text-white">{{ day.dayNum }}</div>
            <!-- Post count dots -->
            <div v-if="day.postCount > 0" class="flex justify-center gap-0.5 mt-0.5">
              <span
                v-for="n in Math.min(day.postCount, 3)"
                :key="n"
                class="w-1.5 h-1.5 rounded-full bg-[#3B7AB1]"
              ></span>
              <span v-if="day.postCount > 3" class="text-[8px] text-gray-400 ml-0.5">+{{ day.postCount - 3 }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Platform Tip -->
      <div v-if="platformTip" class="px-3 py-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <div class="text-xs text-blue-800 dark:text-blue-300 flex items-start gap-2">
          <span>💡</span>
          <span>{{ platformTip }}</span>
        </div>
      </div>

      <!-- Selected summary -->
      <div v-if="selectedTime" class="px-3 py-2 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg" data-testid="schedule-summary">
        <div class="text-xs text-green-800 dark:text-green-300 flex items-center gap-2">
          <span>✅</span>
          <span>Geplant fuer: <strong>{{ new Date(selectedDate).toLocaleDateString('de-DE', { weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric' }) }}, {{ selectedTime }} Uhr</strong></span>
        </div>
      </div>
    </template>
  </div>
</template>
