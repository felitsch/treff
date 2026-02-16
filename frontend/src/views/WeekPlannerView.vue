<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import TourSystem from '@/components/common/TourSystem.vue'
import EmptyState from '@/components/common/EmptyState.vue'

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
  instagram_feed: '📷',
  instagram_stories: '📱',
  instagram_reels: '🎬',
  tiktok: '🎵',
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
    console.error('Weekly planner error:', err)
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
    console.error('Drop error:', err)
  }
  dragItem.value = null
  dragSourceDay.value = null
}

function onDragEnd() {
  dragItem.value = null
  dragSourceDay.value = null
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
    console.error('Adopt plan error:', err)
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
          <span>📅</span> Wochen-Content-Planer
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
    <div data-tour="wp-controls" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-6">
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

        <!-- Generate Button -->
        <button
          data-tour="wp-generate"
          @click="generatePlan"
          :disabled="loading"
          class="px-5 py-2 bg-treff-blue text-white rounded-lg font-medium hover:bg-treff-blue/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
        >
          <span v-if="loading" class="animate-spin">⏳</span>
          <span v-else>✨</span>
          {{ loading ? 'Generiere...' : 'Plan generieren' }}
        </button>
      </div>
    </div>

    <!-- Active Story Arcs Info -->
    <div v-if="activeArcs.length > 0" class="bg-purple-50 dark:bg-purple-900/20 rounded-xl border border-purple-200 dark:border-purple-800 p-4 mb-6">
      <h3 class="text-sm font-semibold text-purple-800 dark:text-purple-300 mb-2 flex items-center gap-2">
        <span>📖</span> Aktive Story-Serien ({{ activeArcs.length }})
      </h3>
      <div class="flex flex-wrap gap-3">
        <div
          v-for="arc in activeArcs"
          :key="arc.id"
          class="flex items-center gap-2 bg-white dark:bg-gray-800 rounded-lg px-3 py-1.5 border border-purple-200 dark:border-purple-700 text-sm"
        >
          <span>{{ countryFlags[arc.country] || '🌍' }}</span>
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
            <span v-if="adopting" class="animate-spin">⏳</span>
            <span v-else>✅</span>
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
              <div class="font-medium text-gray-600 dark:text-gray-400 truncate">📌 {{ post.title || post.category }}</div>
            </div>
          </div>

          <!-- Suggestions (draggable) -->
          <div class="px-2 py-2 space-y-2">
            <div
              v-for="(suggestion, sIdx) in slot.suggestions"
              :key="`${slot.date}-${sIdx}`"
              draggable="true"
              @dragstart="onDragStart($event, dayIndex, sIdx)"
              @dragend="onDragEnd"
              class="p-2.5 rounded-lg border-2 cursor-grab active:cursor-grabbing transition-all hover:shadow-md"
              :class="[
                getCategoryStyle(suggestion.category).bg,
                getCategoryStyle(suggestion.category).border,
                suggestion.is_series ? 'ring-2 ring-purple-400 dark:ring-purple-600' : '',
              ]"
            >
              <!-- Suggestion Header -->
              <div class="flex items-center justify-between mb-1">
                <div class="flex items-center gap-1">
                  <span class="text-sm">{{ suggestion.icon }}</span>
                  <span class="text-[10px] font-bold uppercase tracking-wider" :class="getCategoryStyle(suggestion.category).text">
                    {{ suggestion.is_series ? 'Serie' : suggestion.is_recurring ? 'Format' : 'Mix' }}
                  </span>
                </div>
                <button
                  @click.stop="removeSuggestion(dayIndex, sIdx)"
                  class="text-gray-400 hover:text-red-500 text-xs p-0.5 rounded"
                  title="Entfernen"
                >
                  ✕
                </button>
              </div>

              <!-- Topic -->
              <div class="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5 line-clamp-2">
                {{ suggestion.topic }}
              </div>

              <!-- Meta row -->
              <div class="flex items-center gap-1.5 flex-wrap">
                <span class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-white/60 dark:bg-gray-900/40 text-[10px] font-medium text-gray-700 dark:text-gray-300">
                  {{ platformIcons[suggestion.platform] }} {{ platformLabels[suggestion.platform] }}
                </span>
                <span class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-white/60 dark:bg-gray-900/40 text-[10px] font-medium text-gray-700 dark:text-gray-300">
                  {{ countryFlags[suggestion.country] }} {{ countryNames[suggestion.country] }}
                </span>
                <span class="inline-flex items-center px-1.5 py-0.5 rounded bg-white/60 dark:bg-gray-900/40 text-[10px] font-medium text-gray-700 dark:text-gray-300">
                  🕐 {{ suggestion.time }}
                </span>
              </div>

              <!-- Reason (tooltip-style) -->
              <div class="mt-1.5 text-[10px] text-gray-500 dark:text-gray-400 italic line-clamp-1">
                {{ suggestion.reason }}
              </div>
            </div>

            <!-- Empty state -->
            <div
              v-if="!slot.suggestions.length && !(slot.existing_posts && slot.existing_posts.length)"
              class="py-6 text-center text-gray-400 dark:text-gray-600 text-xs"
            >
              <div class="text-xl mb-1">📭</div>
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
      <div class="text-4xl animate-bounce mb-4">🤖</div>
      <p class="text-gray-600 dark:text-gray-400 font-medium">KI generiert deinen Wochenplan...</p>
      <p class="text-gray-400 dark:text-gray-500 text-sm mt-1">Beruecksichtigt Serien, Formate und Content-Mix</p>
    </div>

    <!-- Legend -->
    <div v-if="planGenerated" data-tour="wp-legend" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 mt-6">
      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Legende & Tipps</h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-gray-600 dark:text-gray-400">
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded bg-purple-400 ring-2 ring-purple-300"></span>
          <span>📖 Story-Serie Episode</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded bg-amber-400"></span>
          <span>🔁 Wiederkehrendes Format</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded bg-blue-400"></span>
          <span>✨ Content-Mix Optimierung</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded bg-gray-300"></span>
          <span>📌 Bestehender Post</span>
        </div>
      </div>
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-3">
        💡 Tipp: Ziehe Karten per Drag & Drop auf andere Tage. Klicke ✕ um einen Vorschlag zu entfernen. "Plan uebernehmen" erstellt alle Vorschlaege als geplante Posts im Kalender.
      </p>
    </div>

    <TourSystem ref="tourRef" page-key="week-planner" />
  </div>
</template>
