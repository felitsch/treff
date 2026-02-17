<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import TourSystem from '@/components/common/TourSystem.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const router = useRouter()
const auth = useAuthStore()
const toast = useToast()

// State
const loading = ref(false)
const adopting = ref(false)
const weekStart = ref('')
const postsPerWeek = ref(5)
const includeRecurring = ref(true)
const includeSeries = ref(true)
const daySlots = ref([])
const activeArcs = ref([])
const recurringFormats = ref([])
const season = ref('')
const planGenerated = ref(false)
const dragItem = ref(null)
const dragSourceDay = ref(null)
const tourRef = ref(null)

// Platform filter: which platforms to include in generated plan
const selectedPlatforms = ref(['instagram_feed', 'instagram_story', 'tiktok'])

// Theme/topic focus: which categories to emphasize
const selectedThemes = ref([])

// Inline edit state
const editingItem = ref(null) // { dayIndex, suggestionIndex }
const editForm = ref({ topic: '', category: '', platform: '', country: '', time: '' })

// Category display helpers
const categoryColors = {
  laender_spotlight: { bg: 'bg-blue-100 dark:bg-blue-900/40', border: 'border-blue-400', text: 'text-blue-700 dark:text-blue-300' },
  erfahrungsberichte: { bg: 'bg-purple-100 dark:bg-purple-900/40', border: 'border-purple-400', text: 'text-purple-700 dark:text-purple-300' },
  infografiken: { bg: 'bg-cyan-100 dark:bg-cyan-900/40', border: 'border-cyan-400', text: 'text-cyan-700 dark:text-cyan-300' },
  fristen_cta: { bg: 'bg-red-100 dark:bg-red-900/40', border: 'border-red-400', text: 'text-red-700 dark:text-red-300' },
  tipps_tricks: { bg: 'bg-amber-100 dark:bg-amber-900/40', border: 'border-amber-400', text: 'text-amber-700 dark:text-amber-300' },
  faq: { bg: 'bg-teal-100 dark:bg-teal-900/40', border: 'border-teal-400', text: 'text-teal-700 dark:text-teal-300' },
  foto_posts: { bg: 'bg-pink-100 dark:bg-pink-900/40', border: 'border-pink-400', text: 'text-pink-700 dark:text-pink-300' },
}

const categoryLabels = {
  laender_spotlight: 'Laender-Spotlight',
  erfahrungsberichte: 'Erfahrungsberichte',
  infografiken: 'Infografiken',
  fristen_cta: 'Fristen & CTA',
  tipps_tricks: 'Tipps & Tricks',
  faq: 'FAQ',
  foto_posts: 'Foto-Posts',
}

const platformIcons = {
  instagram_feed: 'camera',
  instagram_stories: 'device-phone-mobile',
  instagram_reels: 'film',
  tiktok: 'musical-note',
}

const platformLabels = {
  instagram_feed: 'IG Feed',
  instagram_stories: 'IG Story',
  instagram_reels: 'IG Reel',
  tiktok: 'TikTok',
}

const countryFlags = {
  usa: '🇺🇸',
  canada: '🇨🇦',
  australia: '🇦🇺',
  newzealand: '🇳🇿',
  ireland: '🇮🇪',
}

const countryNames = {
  usa: 'USA',
  canada: 'Kanada',
  australia: 'Australien',
  newzealand: 'Neuseeland',
  ireland: 'Irland',
}

// Available platform options for filter
const platformOptions = [
  { value: 'instagram_feed', label: 'IG Feed', icon: 'camera' },
  { value: 'instagram_story', label: 'IG Story', icon: 'device-phone-mobile' },
  { value: 'tiktok', label: 'TikTok', icon: 'musical-note' },
]

// Available theme/category options for focus
const themeOptions = [
  { value: 'laender_spotlight', label: 'Laender-Spotlight', icon: 'globe-alt' },
  { value: 'erfahrungsberichte', label: 'Erfahrungsberichte', icon: 'chat-bubble-left-right' },
  { value: 'infografiken', label: 'Infografiken', icon: 'chart-bar' },
  { value: 'fristen_cta', label: 'Fristen & CTA', icon: 'clock' },
  { value: 'tipps_tricks', label: 'Tipps & Tricks', icon: 'light-bulb' },
  { value: 'faq', label: 'FAQ', icon: 'question-mark-circle' },
  { value: 'foto_posts', label: 'Foto-Posts', icon: 'camera' },
]

// Compute default week start (next Monday)
function getNextMonday() {
  const today = new Date()
  const dayOfWeek = today.getDay()
  const daysUntilMonday = dayOfWeek === 0 ? 1 : (8 - dayOfWeek)
  const nextMon = new Date(today)
  nextMon.setDate(today.getDate() + daysUntilMonday)
  return nextMon.toISOString().split('T')[0]
}

// Total suggestion count
const totalSuggestions = computed(() => {
  return daySlots.value.reduce((sum, slot) => sum + slot.suggestions.length, 0)
})

// Formatted week range
const weekLabel = computed(() => {
  if (!daySlots.value.length) return ''
  const start = daySlots.value[0].date
  const end = daySlots.value[6].date
  const opts = { day: 'numeric', month: 'short' }
  const s = new Date(start + 'T00:00:00').toLocaleDateString('de-DE', opts)
  const e = new Date(end + 'T00:00:00').toLocaleDateString('de-DE', opts)
  return `${s} - ${e}`
})

// Generate plan
async function generatePlan() {
  loading.value = true
  planGenerated.value = false
  try {
    const body = {
      week_start: weekStart.value || undefined,
      posts_per_week: postsPerWeek.value,
      include_recurring: includeRecurring.value,
      include_series: includeSeries.value,
      platforms: selectedPlatforms.value.length > 0 ? selectedPlatforms.value : undefined,
      theme_focus: selectedThemes.value.length > 0 ? selectedThemes.value : undefined,
    }
    const res = await fetch('/api/ai/weekly-planner', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${auth.accessToken}`,
      },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    daySlots.value = data.day_slots || []
    activeArcs.value = data.active_arcs || []
    recurringFormats.value = data.recurring_formats || []
    season.value = data.season || ''
    weekStart.value = data.week_start
    planGenerated.value = true
    toast.success(`Wochenplan mit ${data.total_suggestions} Vorschlaegen generiert!`)
  } catch (err) {
    // Error toast shown by API interceptor
    toast.error('Wochenplan konnte nicht generiert werden.')
  } finally {
    loading.value = false
  }
}

// Remove a suggestion from a day
function removeSuggestion(dayIndex, suggestionIndex) {
  daySlots.value[dayIndex].suggestions.splice(suggestionIndex, 1)
}

// Drag and drop
function onDragStart(event, dayIndex, suggestionIndex) {
  dragItem.value = daySlots.value[dayIndex].suggestions[suggestionIndex]
  dragSourceDay.value = dayIndex
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', JSON.stringify({ dayIndex, suggestionIndex }))
}

function onDragOver(event) {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
}

function onDrop(event, targetDayIndex) {
  event.preventDefault()
  try {
    const data = JSON.parse(event.dataTransfer.getData('text/plain'))
    const { dayIndex: sourceDayIndex, suggestionIndex } = data

    if (sourceDayIndex === targetDayIndex) return

    // Remove from source
    const [item] = daySlots.value[sourceDayIndex].suggestions.splice(suggestionIndex, 1)

    // Update the item's date to match target day
    item.date = daySlots.value[targetDayIndex].date

    // Add to target
    daySlots.value[targetDayIndex].suggestions.push(item)

    toast.info(`Verschoben nach ${daySlots.value[targetDayIndex].day}`)
  } catch (err) {
    // Error toast shown by API interceptor
  }
  dragItem.value = null
  dragSourceDay.value = null
}

function onDragEnd() {
  dragItem.value = null
  dragSourceDay.value = null
}

// Inline editing functions
function startEdit(dayIndex, suggestionIndex) {
  const suggestion = daySlots.value[dayIndex].suggestions[suggestionIndex]
  editingItem.value = { dayIndex, suggestionIndex }
  editForm.value = {
    topic: suggestion.topic || '',
    category: suggestion.category || 'laender_spotlight',
    platform: suggestion.platform || 'instagram_feed',
    country: suggestion.country || 'usa',
    time: suggestion.time || '17:00',
  }
}

function saveEdit() {
  if (!editingItem.value) return
  const { dayIndex, suggestionIndex } = editingItem.value
  const suggestion = daySlots.value[dayIndex].suggestions[suggestionIndex]
  suggestion.topic = editForm.value.topic
  suggestion.category = editForm.value.category
  suggestion.platform = editForm.value.platform
  suggestion.country = editForm.value.country
  suggestion.time = editForm.value.time
  editingItem.value = null
  toast.success('Vorschlag aktualisiert')
}

function cancelEdit() {
  editingItem.value = null
}

function isEditing(dayIndex, suggestionIndex) {
  return editingItem.value?.dayIndex === dayIndex && editingItem.value?.suggestionIndex === suggestionIndex
}

// Toggle platform selection
function togglePlatform(platform) {
  const idx = selectedPlatforms.value.indexOf(platform)
  if (idx >= 0) {
    // Don't allow deselecting all
    if (selectedPlatforms.value.length > 1) {
      selectedPlatforms.value.splice(idx, 1)
    }
  } else {
    selectedPlatforms.value.push(platform)
  }
}

// Toggle theme selection
function toggleTheme(theme) {
  const idx = selectedThemes.value.indexOf(theme)
  if (idx >= 0) {
    selectedThemes.value.splice(idx, 1)
  } else {
    selectedThemes.value.push(theme)
  }
}

// One-click adopt plan
async function adoptPlan() {
  const items = []
  for (const slot of daySlots.value) {
    for (const s of slot.suggestions) {
      items.push({
        date: slot.date,
        time: s.time,
        category: s.category,
        country: s.country,
        platform: s.platform,
        topic: s.topic,
        story_arc_id: s.story_arc_id || null,
        episode_number: s.episode_number || null,
      })
    }
  }

  if (items.length === 0) {
    toast.error('Keine Vorschlaege zum Uebernehmen vorhanden.')
    return
  }

  adopting.value = true
  try {
    const res = await fetch('/api/ai/weekly-planner/adopt', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${auth.accessToken}`,
      },
      body: JSON.stringify({ items }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    toast.success(data.message || `${data.count} Posts in den Kalender uebernommen!`)

    // Navigate to calendar after adoption
    setTimeout(() => {
      router.push('/calendar')
    }, 1500)
  } catch (err) {
    // Error toast shown by API interceptor
    toast.error('Plan konnte nicht uebernommen werden.')
  } finally {
    adopting.value = false
  }
}

// Navigate week
function prevWeek() {
  const d = new Date(weekStart.value + 'T00:00:00')
  d.setDate(d.getDate() - 7)
  weekStart.value = d.toISOString().split('T')[0]
  generatePlan()
}

function nextWeek() {
  const d = new Date(weekStart.value + 'T00:00:00')
  d.setDate(d.getDate() + 7)
  weekStart.value = d.toISOString().split('T')[0]
  generatePlan()
}

// Helper
function getCategoryStyle(category) {
  return categoryColors[category] || { bg: 'bg-gray-100', border: 'border-gray-400', text: 'text-gray-700' }
}

onMounted(() => {
  weekStart.value = getNextMonday()
})
</script>

<template>
  <div class="p-4 md:p-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div data-tour="wp-header" class="flex items-start justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <AppIcon name="calendar" class="w-6 h-6 inline-block" /> Wochen-Content-Planer
        </h1>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          KI-gestuetzter Wochenplaner mit Serien-Awareness, wiederkehrenden Formaten und ausgewogenem Content-Mix
        </p>
      </div>
      <button
        @click="tourRef?.startTour()"
        class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        title="Seiten-Tour starten"
      >
        &#10067; Tour
      </button>
    </div>

    <!-- Controls -->
    <BaseCard padding="md" :header-divider="false" data-tour="wp-controls" class="mb-6">
      <div class="flex flex-wrap items-end gap-4">
        <!-- Week Picker -->
        <div class="flex-1 min-w-[180px]">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Woche ab</label>
          <div class="flex items-center gap-2">
            <button
              @click="prevWeek"
              class="p-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
              :disabled="loading"
              title="Vorherige Woche"
            >
              ←
            </button>
            <input
              v-model="weekStart"
              type="date"
              class="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            />
            <button
              @click="nextWeek"
              class="p-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
              :disabled="loading"
              title="Naechste Woche"
            >
              →
            </button>
          </div>
        </div>

        <!-- Posts per Week + Toggles (Filter section) -->
        <div data-tour="wp-filters" class="flex flex-wrap items-end gap-4">
          <div class="min-w-[120px]">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Posts/Woche</label>
            <select
              v-model.number="postsPerWeek"
              class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            >
              <option :value="2">2 Posts</option>
              <option :value="3">3 Posts</option>
              <option :value="4">4 Posts</option>
              <option :value="5">5 Posts</option>
              <option :value="6">6 Posts</option>
              <option :value="7">7 Posts</option>
            </select>
          </div>

          <!-- Toggles -->
          <div class="flex items-center gap-4">
            <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
              <input v-model="includeRecurring" type="checkbox" class="rounded border-gray-300 text-treff-blue focus:ring-treff-blue" />
              Wiederkehrende Formate
            </label>
            <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
              <input v-model="includeSeries" type="checkbox" class="rounded border-gray-300 text-treff-blue focus:ring-treff-blue" />
              Story-Serien
            </label>
          </div>
        </div>

        <!-- Platform Filter -->
        <div class="w-full">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Plattformen</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="p in platformOptions"
              :key="p.value"
              @click="togglePlatform(p.value)"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border-2 transition-all"
              :class="selectedPlatforms.includes(p.value)
                ? 'bg-treff-blue/10 border-treff-blue text-treff-blue dark:bg-treff-blue/20 dark:text-blue-300'
                : 'bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-500'"
            >
              <AppIcon :name="p.icon" class="w-4 h-4 inline-block" />
              <span>{{ p.label }}</span>
              <svg v-if="selectedPlatforms.includes(p.value)" class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Theme Focus (optional) -->
        <div class="w-full">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Themen-Schwerpunkte
            <span class="text-xs font-normal text-gray-400 dark:text-gray-500 ml-1">(optional – leer = ausgewogener Mix)</span>
          </label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="t in themeOptions"
              :key="t.value"
              @click="toggleTheme(t.value)"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border-2 transition-all"
              :class="selectedThemes.includes(t.value)
                ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-400 text-amber-700 dark:text-amber-300'
                : 'bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-500'"
            >
              <AppIcon :name="t.icon" class="w-4 h-4 inline-block" />
              <span>{{ t.label }}</span>
              <svg v-if="selectedThemes.includes(t.value)" class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Generate Button -->
        <button
          data-tour="wp-generate"
          @click="generatePlan"
          :disabled="loading"
          class="px-5 py-2 bg-treff-blue text-white rounded-lg font-medium hover:bg-treff-blue/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
        >
          <AppIcon v-if="loading" name="clock" class="w-5 h-5 inline-block animate-spin" />
          <AppIcon v-else name="sparkles" class="w-5 h-5 inline-block" />
          {{ loading ? 'Generiere...' : 'Plan generieren' }}
        </button>
      </div>
    </BaseCard>

    <!-- Active Story Arcs Info -->
    <div v-if="activeArcs.length > 0" class="bg-purple-50 dark:bg-purple-900/20 rounded-xl border border-purple-200 dark:border-purple-800 p-4 mb-6">
      <h3 class="text-sm font-semibold text-purple-800 dark:text-purple-300 mb-2 flex items-center gap-2">
        <AppIcon name="book-open" class="w-4 h-4 inline-block" /> Aktive Story-Serien ({{ activeArcs.length }})
      </h3>
      <div class="flex flex-wrap gap-3">
        <div
          v-for="arc in activeArcs"
          :key="arc.id"
          class="flex items-center gap-2 bg-white dark:bg-gray-800 rounded-lg px-3 py-1.5 border border-purple-200 dark:border-purple-700 text-sm"
        >
          <span v-if="countryFlags[arc.country]">{{ countryFlags[arc.country] }}</span><AppIcon v-else name="globe-alt" class="w-4 h-4 inline-block" />
          <span class="font-medium text-gray-800 dark:text-gray-200">{{ arc.title }}</span>
          <span class="text-purple-600 dark:text-purple-400 text-xs">Ep. {{ arc.next_episode }}/{{ arc.planned_episodes || '?' }}</span>
        </div>
      </div>
    </div>

    <!-- Weekly Plan Grid -->
    <div v-if="planGenerated" data-tour="wp-grid" class="mb-6">
      <!-- Week Header -->
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          Wochenplan: {{ weekLabel }}
          <span v-if="season" class="text-sm font-normal text-gray-500 dark:text-gray-400">({{ season }})</span>
        </h2>
        <div class="flex items-center gap-3">
          <span class="text-sm text-gray-500 dark:text-gray-400">{{ totalSuggestions }} Vorschlaege</span>
          <button
            data-tour="wp-adopt"
            @click="adoptPlan"
            :disabled="adopting || totalSuggestions === 0"
            class="px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
          >
            <AppIcon v-if="adopting" name="clock" class="w-5 h-5 inline-block animate-spin" />
            <AppIcon v-else name="check-circle" class="w-5 h-5 inline-block" />
            {{ adopting ? 'Uebernehme...' : 'Plan uebernehmen' }}
          </button>
        </div>
      </div>

      <!-- Day Columns -->
      <div class="grid grid-cols-7 gap-3">
        <div
          v-for="(slot, dayIndex) in daySlots"
          :key="slot.date"
          class="rounded-xl border-2 transition-colors min-h-[200px]"
          :class="[
            dragSourceDay !== null && dragSourceDay !== dayIndex
              ? 'border-treff-blue/50 bg-treff-blue/5'
              : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800',
            slot.is_weekend ? 'bg-gray-50 dark:bg-gray-800/80' : '',
          ]"
          @dragover="onDragOver"
          @drop="onDrop($event, dayIndex)"
        >
          <!-- Day Header -->
          <div class="px-3 py-2 border-b border-gray-200 dark:border-gray-700" :class="slot.is_weekend ? 'bg-gray-100 dark:bg-gray-700/50' : ''">
            <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ slot.day }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              {{ new Date(slot.date + 'T00:00:00').toLocaleDateString('de-DE', { day: 'numeric', month: 'short' }) }}
            </div>
          </div>

          <!-- Existing Posts -->
          <div v-if="slot.existing_posts && slot.existing_posts.length > 0" class="px-2 pt-2">
            <div
              v-for="post in slot.existing_posts"
              :key="post.id"
              class="mb-2 p-2 rounded-lg bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-xs opacity-70"
            >
              <div class="font-medium text-gray-600 dark:text-gray-400 truncate flex items-center gap-1"><AppIcon name="map-pin" class="w-3 h-3 inline-block flex-shrink-0" /> {{ post.title || post.category }}</div>
            </div>
          </div>

          <!-- Suggestions (draggable) -->
          <div class="px-2 py-2 space-y-2">
            <div
              v-for="(suggestion, sIdx) in slot.suggestions"
              :key="`${slot.date}-${sIdx}`"
              :draggable="!isEditing(dayIndex, sIdx)"
              @dragstart="!isEditing(dayIndex, sIdx) && onDragStart($event, dayIndex, sIdx)"
              @dragend="onDragEnd"
              class="p-2.5 rounded-lg border-2 transition-all hover:shadow-md"
              :class="[
                isEditing(dayIndex, sIdx) ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20 ring-2 ring-blue-300' : getCategoryStyle(suggestion.category).bg + ' ' + getCategoryStyle(suggestion.category).border + ' cursor-grab active:cursor-grabbing',
                suggestion.is_series && !isEditing(dayIndex, sIdx) ? 'ring-2 ring-purple-400 dark:ring-purple-600' : '',
              ]"
            >
              <!-- EDIT MODE -->
              <div v-if="isEditing(dayIndex, sIdx)" class="space-y-2">
                <div>
                  <label class="text-[10px] font-semibold text-gray-500 uppercase">Thema</label>
                  <input
                    v-model="editForm.topic"
                    type="text"
                    class="w-full mt-0.5 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="Thema eingeben..."
                  />
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <div>
                    <label class="text-[10px] font-semibold text-gray-500 uppercase">Kategorie</label>
                    <select v-model="editForm.category" class="w-full mt-0.5 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                      <option v-for="t in themeOptions" :key="t.value" :value="t.value">{{ t.label }}</option>
                    </select>
                  </div>
                  <div>
                    <label class="text-[10px] font-semibold text-gray-500 uppercase">Plattform</label>
                    <select v-model="editForm.platform" class="w-full mt-0.5 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                      <option v-for="p in platformOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
                    </select>
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <div>
                    <label class="text-[10px] font-semibold text-gray-500 uppercase">Land</label>
                    <select v-model="editForm.country" class="w-full mt-0.5 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                      <option v-for="(name, code) in countryNames" :key="code" :value="code">{{ countryFlags[code] }} {{ name }}</option>
                    </select>
                  </div>
                  <div>
                    <label class="text-[10px] font-semibold text-gray-500 uppercase">Uhrzeit</label>
                    <input v-model="editForm.time" type="time" class="w-full mt-0.5 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
                  </div>
                </div>
                <div class="flex gap-2">
                  <button @click="saveEdit" class="flex-1 px-2 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors">
                    Speichern
                  </button>
                  <button @click="cancelEdit" class="flex-1 px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors">
                    Abbrechen
                  </button>
                </div>
              </div>

              <!-- VIEW MODE -->
              <template v-else>
                <!-- Suggestion Header -->
                <div class="flex items-center justify-between mb-1">
                  <div class="flex items-center gap-1">
                    <span class="text-sm">{{ suggestion.icon }}</span>
                    <span class="text-[10px] font-bold uppercase tracking-wider" :class="getCategoryStyle(suggestion.category).text">
                      {{ suggestion.is_series ? 'Serie' : suggestion.is_recurring ? 'Format' : 'Mix' }}
                    </span>
                  </div>
                  <div class="flex items-center gap-1">
                    <button
                      @click.stop="startEdit(dayIndex, sIdx)"
                      class="text-gray-400 hover:text-blue-500 text-xs p-0.5 rounded"
                      title="Bearbeiten"
                    >
                      <AppIcon name="pencil-square" class="w-3 h-3 inline-block" />
                    </button>
                    <button
                      @click.stop="removeSuggestion(dayIndex, sIdx)"
                      class="text-gray-400 hover:text-red-500 text-xs p-0.5 rounded"
                      title="Entfernen"
                    >
                      ✕
                    </button>
                  </div>
                </div>

                <!-- Topic -->
                <div class="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 line-clamp-2">
                  {{ suggestion.topic }}
                </div>

                <!-- Meta row -->
                <div class="flex items-center gap-1.5 flex-wrap">
                  <span class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-white/60 dark:bg-gray-900/40 text-[10px] font-medium text-gray-700 dark:text-gray-300">
                    <AppIcon :name="platformIcons[suggestion.platform] || 'document-text'" class="w-3 h-3 inline-block" /> {{ platformLabels[suggestion.platform] }}
                  </span>
                  <span class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-white/60 dark:bg-gray-900/40 text-[10px] font-medium text-gray-700 dark:text-gray-300">
                    {{ countryFlags[suggestion.country] }} {{ countryNames[suggestion.country] }}
                  </span>
                  <span class="inline-flex items-center px-1.5 py-0.5 rounded bg-white/60 dark:bg-gray-900/40 text-[10px] font-medium text-gray-700 dark:text-gray-300">
                    <AppIcon name="clock" class="w-3 h-3 inline-block" /> {{ suggestion.time }}
                  </span>
                </div>

                <!-- Reason (tooltip-style) -->
                <div class="mt-1.5 text-[10px] text-gray-500 dark:text-gray-400 italic line-clamp-1">
                  {{ suggestion.reason }}
                </div>
              </template>
            </div>

            <!-- Empty state -->
            <div
              v-if="!slot.suggestions.length && !(slot.existing_posts && slot.existing_posts.length)"
              class="py-6 text-center text-gray-400 dark:text-gray-600 text-xs"
            >
              <div class="mb-1"><AppIcon name="inbox" class="w-6 h-6 inline-block" /></div>
              Kein Post geplant
              <div class="text-[10px] mt-1">Ziehe einen Vorschlag hierher</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State (before plan generation) -->
    <EmptyState
      v-if="!planGenerated && !loading"
      svgIcon="clipboard-document-list"
      title="Wochenplan erstellen"
      description="Waehle oben eine Woche und die Anzahl der Posts aus. Die KI generiert einen ausgewogenen Content-Plan mit wiederkehrenden Formaten, Story-Serien und optimalen Posting-Zeiten."
      actionLabel="Jetzt Plan generieren"
      @action="generatePlan"
    />

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-16">
      <div class="animate-bounce mb-4"><AppIcon name="cpu-chip" class="w-10 h-10 inline-block text-treff-blue" /></div>
      <p class="text-gray-600 dark:text-gray-400 font-medium">KI generiert deinen Wochenplan...</p>
      <p class="text-gray-400 dark:text-gray-500 text-sm mt-1">Beruecksichtigt Serien, Formate und Content-Mix</p>
    </div>

    <!-- Legend -->
    <BaseCard v-if="planGenerated" padding="md" title="Legende & Tipps" :header-divider="false" data-tour="wp-legend" class="mt-6">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-gray-600 dark:text-gray-400">
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded bg-purple-400 ring-2 ring-purple-300"></span>
          <span class="flex items-center gap-1"><AppIcon name="book-open" class="w-3 h-3 inline-block" /> Story-Serie Episode</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded bg-amber-400"></span>
          <span class="flex items-center gap-1"><AppIcon name="arrow-path" class="w-3 h-3 inline-block" /> Wiederkehrendes Format</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded bg-blue-400"></span>
          <span class="flex items-center gap-1"><AppIcon name="sparkles" class="w-3 h-3 inline-block" /> Content-Mix Optimierung</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded bg-gray-300"></span>
          <span class="flex items-center gap-1"><AppIcon name="map-pin" class="w-3 h-3 inline-block" /> Bestehender Post</span>
        </div>
      </div>
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-3">
        <AppIcon name="light-bulb" class="w-4 h-4 inline-block" /> Tipp: Ziehe Karten per Drag & Drop auf andere Tage. Klicke ✕ um einen Vorschlag zu entfernen. "Plan uebernehmen" erstellt alle Vorschlaege als geplante Posts im Kalender.
      </p>
    </BaseCard>

    <TourSystem ref="tourRef" page-key="week-planner" />
  </div>
</template>
