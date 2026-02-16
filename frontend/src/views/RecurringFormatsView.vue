<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import HelpTooltip from '@/components/common/HelpTooltip.vue'
import { tooltipTexts } from '@/utils/tooltipTexts'
import TourSystem from '@/components/common/TourSystem.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const auth = useAuthStore()

// State
const formats = ref([])
const loading = ref(false)
const showCreateForm = ref(false)
const editingId = ref(null)
const filterFrequency = ref('')
const filterActive = ref('')
const aiPreviewFormat = ref(null)
const aiLoading = ref(false)
const aiResult = ref(null)
const aiTopic = ref('')
const aiCountry = ref('')
const tourRef = ref(null)

// Toast
const toastMessage = ref('')
const toastType = ref('success')
function showToast(msg, type = 'success') {
  toastMessage.value = msg
  toastType.value = type
  setTimeout(() => { toastMessage.value = '' }, 3500)
}

// Form data
const form = ref({
  name: '',
  description: '',
  frequency: 'weekly',
  preferred_day: 'Montag',
  preferred_time: '18:00',
  tone: 'jugendlich',
  hashtags: '',
  icon: '🔄',
  category: 'tipps_tricks',
  is_active: true,
})

const DAYS = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
const FREQUENCIES = [
  { value: 'daily', label: 'Taeglich' },
  { value: 'weekly', label: 'Woechentlich' },
  { value: 'biweekly', label: 'Alle 2 Wochen' },
  { value: 'monthly', label: 'Monatlich' },
]
const TONES = [
  { value: 'jugendlich', label: 'Jugendlich' },
  { value: 'witzig', label: 'Witzig' },
  { value: 'emotional', label: 'Emotional' },
  { value: 'motivierend', label: 'Motivierend' },
  { value: 'informativ', label: 'Informativ' },
  { value: 'serioess', label: 'Serioess' },
]
const CATEGORIES = [
  { value: 'tipps_tricks', label: 'Tipps & Tricks' },
  { value: 'erfahrungsberichte', label: 'Erfahrungsberichte' },
  { value: 'laender_spotlight', label: 'Laender-Spotlight' },
  { value: 'faq', label: 'FAQ / Fun Facts' },
  { value: 'fristen_cta', label: 'Fristen & CTA' },
  { value: 'hinter_den_kulissen', label: 'Hinter den Kulissen' },
  { value: 'game_challenges', label: 'Games & Challenges' },
]
const COUNTRIES = [
  { value: '', label: 'Kein Fokus' },
  { value: 'usa', label: 'USA' },
  { value: 'kanada', label: 'Kanada' },
  { value: 'australien', label: 'Australien' },
  { value: 'neuseeland', label: 'Neuseeland' },
  { value: 'irland', label: 'Irland' },
]
const ICONS = ['💪', '😂', '📸', '🤓', '🌅', '🔄', '🎯', '🎉', '🌍', '🏆', '❓', '🎬']

// Computed
const filteredFormats = computed(() => {
  let list = formats.value
  if (filterFrequency.value) {
    list = list.filter(f => f.frequency === filterFrequency.value)
  }
  if (filterActive.value !== '') {
    const active = filterActive.value === 'true'
    list = list.filter(f => f.is_active === active)
  }
  return list
})

const activeCount = computed(() => formats.value.filter(f => f.is_active).length)
const totalCount = computed(() => formats.value.length)

// Fetch
async function fetchFormats() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    const res = await fetch('/api/recurring-formats', {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    formats.value = await res.json()
  } catch (err) {
    console.error('Fetch formats error:', err)
    showToast('Formate konnten nicht geladen werden.', 'error')
  } finally {
    loading.value = false
  }
}

// Create
async function createFormat() {
  try {
    const hashtags = form.value.hashtags
      ? form.value.hashtags.split(',').map(h => h.trim()).filter(Boolean)
      : []
    const body = {
      ...form.value,
      hashtags,
    }
    const res = await fetch('/api/recurring-formats', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${auth.accessToken}`,
      },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    showCreateForm.value = false
    resetForm()
    await fetchFormats()
    showToast('Format erstellt!')
  } catch (err) {
    console.error('Create format error:', err)
    showToast('Format konnte nicht erstellt werden.', 'error')
  }
}

// Update
async function updateFormat(id) {
  const fmt = formats.value.find(f => f.id === id)
  if (!fmt) return
  try {
    const body = { ...fmt }
    delete body.id
    delete body.created_at
    delete body.updated_at
    delete body.user_id
    delete body.is_default
    const res = await fetch(`/api/recurring-formats/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${auth.accessToken}`,
      },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    editingId.value = null
    await fetchFormats()
    showToast('Format aktualisiert!')
  } catch (err) {
    console.error('Update format error:', err)
    showToast('Format konnte nicht aktualisiert werden.', 'error')
  }
}

// Toggle active
async function toggleActive(fmt) {
  try {
    const res = await fetch(`/api/recurring-formats/${fmt.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${auth.accessToken}`,
      },
      body: JSON.stringify({ is_active: !fmt.is_active }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    await fetchFormats()
    showToast(fmt.is_active ? 'Format deaktiviert' : 'Format aktiviert')
  } catch (err) {
    console.error('Toggle active error:', err)
    showToast('Status konnte nicht geaendert werden.', 'error')
  }
}

// Delete
async function deleteFormat(id) {
  if (!confirm('Dieses Format wirklich loeschen?')) return
  try {
    const res = await fetch(`/api/recurring-formats/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    })
    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.detail || `HTTP ${res.status}`)
    }
    await fetchFormats()
    showToast('Format geloescht!')
  } catch (err) {
    console.error('Delete format error:', err)
    showToast(err.message || 'Format konnte nicht geloescht werden.', 'error')
  }
}

// AI Generate preview
async function generateAIPreview(fmt) {
  aiPreviewFormat.value = fmt
  aiResult.value = null
  aiTopic.value = ''
  aiCountry.value = ''
  aiLoading.value = false
}

async function runAIGeneration() {
  if (!aiPreviewFormat.value) return
  aiLoading.value = true
  aiResult.value = null
  try {
    const body = {
      format_id: aiPreviewFormat.value.id,
      topic: aiTopic.value || undefined,
      country: aiCountry.value || undefined,
    }
    const res = await fetch('/api/ai/generate-recurring-format-text', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${auth.accessToken}`,
      },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    aiResult.value = await res.json()
  } catch (err) {
    console.error('AI generation error:', err)
    showToast('KI-Generierung fehlgeschlagen.', 'error')
  } finally {
    aiLoading.value = false
  }
}

function closeAIPreview() {
  aiPreviewFormat.value = null
  aiResult.value = null
}

function resetForm() {
  form.value = {
    name: '',
    description: '',
    frequency: 'weekly',
    preferred_day: 'Montag',
    preferred_time: '18:00',
    tone: 'jugendlich',
    hashtags: '',
    icon: '🔄',
    category: 'tipps_tricks',
    is_active: true,
  }
}

function getFrequencyLabel(value) {
  const f = FREQUENCIES.find(f => f.value === value)
  return f ? f.label : value
}

function getToneLabel(value) {
  const t = TONES.find(t => t.value === value)
  return t ? t.label : value
}

function getCategoryLabel(value) {
  const c = CATEGORIES.find(c => c.value === value)
  return c ? c.label : value
}

onMounted(fetchFormats)
</script>

<template>
  <div class="max-w-6xl mx-auto p-6">
    <!-- Toast -->
    <div
      v-if="toastMessage"
      :class="[
        'fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-white text-sm font-medium transition-all',
        toastType === 'error' ? 'bg-red-500' : 'bg-green-500',
      ]"
    >
      {{ toastMessage }}
    </div>

    <!-- Header -->
    <div data-tour="formats-header" class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">Wiederkehrende Formate <HelpTooltip :text="tooltipTexts.storyArcs.recurringFormats" /></h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Running Gags und regelmaessige Content-Formate verwalten.
          <span class="font-medium">{{ activeCount }}/{{ totalCount }} aktiv</span>
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="tourRef?.startTour()"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          title="Seiten-Tour starten"
        >
          &#10067; Tour
        </button>
        <button
          data-tour="formats-create"
          @click="showCreateForm = !showCreateForm"
          class="bg-treff-blue text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <span>{{ showCreateForm ? '✕ Abbrechen' : '+ Neues Format' }}</span>
        </button>
      </div>
    </div>

    <!-- Create Form -->
    <div v-if="showCreateForm" class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 mb-6 shadow-sm">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Neues wiederkehrendes Format</h2>
      <form @submit.prevent="createFormat" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Name -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name *</label>
          <input v-model="form.name" type="text" required placeholder="z.B. Freitags-Fail"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
        </div>

        <!-- Icon -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Icon</label>
          <div class="flex gap-1.5 flex-wrap">
            <button
              v-for="ic in ICONS" :key="ic" type="button"
              @click="form.icon = ic"
              :class="[
                'w-9 h-9 rounded-lg text-lg flex items-center justify-center border transition-colors',
                form.icon === ic
                  ? 'border-treff-blue bg-treff-blue/10'
                  : 'border-gray-200 dark:border-gray-600 hover:border-treff-blue/50',
              ]"
            >{{ ic }}</button>
          </div>
        </div>

        <!-- Description -->
        <div class="md:col-span-2">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Beschreibung *</label>
          <textarea v-model="form.description" required rows="2" placeholder="Worum geht es bei diesem Format?"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"></textarea>
        </div>

        <!-- Frequency -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Haeufigkeit</label>
          <select v-model="form.frequency"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
            <option v-for="f in FREQUENCIES" :key="f.value" :value="f.value">{{ f.label }}</option>
          </select>
        </div>

        <!-- Preferred Day -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Bevorzugter Tag</label>
          <select v-model="form.preferred_day"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
            <option v-for="d in DAYS" :key="d" :value="d">{{ d }}</option>
          </select>
        </div>

        <!-- Time -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Bevorzugte Uhrzeit</label>
          <input v-model="form.preferred_time" type="time"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
        </div>

        <!-- Tone -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tonalitaet</label>
          <select v-model="form.tone"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
            <option v-for="t in TONES" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </div>

        <!-- Category -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Kategorie</label>
          <select v-model="form.category"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
            <option v-for="c in CATEGORIES" :key="c.value" :value="c.value">{{ c.label }}</option>
          </select>
        </div>

        <!-- Hashtags -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Hashtags (kommagetrennt)</label>
          <input v-model="form.hashtags" type="text" placeholder="#MotivationMonday, #TREFF"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
        </div>

        <!-- Submit -->
        <div class="md:col-span-2 flex justify-end">
          <button type="submit" class="bg-treff-blue text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
            Format erstellen
          </button>
        </div>
      </form>
    </div>

    <!-- Filters -->
    <div class="flex gap-3 mb-4 flex-wrap">
      <select v-model="filterFrequency"
        class="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300">
        <option value="">Alle Haeufigkeiten</option>
        <option v-for="f in FREQUENCIES" :key="f.value" :value="f.value">{{ f.label }}</option>
      </select>
      <select v-model="filterActive"
        class="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300">
        <option value="">Alle Status</option>
        <option value="true">Aktiv</option>
        <option value="false">Inaktiv</option>
      </select>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-treff-blue border-t-transparent rounded-full mx-auto mb-3"></div>
      <p class="text-gray-500 dark:text-gray-400">Lade Formate...</p>
    </div>

    <!-- Formats List -->
    <div data-tour="formats-list" v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="fmt in filteredFormats"
        :key="fmt.id"
        :class="[
          'bg-white dark:bg-gray-800 border rounded-xl p-5 shadow-sm transition-all',
          fmt.is_active
            ? 'border-gray-200 dark:border-gray-700'
            : 'border-gray-200 dark:border-gray-700 opacity-60',
        ]"
      >
        <!-- Header -->
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-2">
            <span class="text-2xl">{{ fmt.icon || '🔄' }}</span>
            <div>
              <h3 class="font-semibold text-gray-900 dark:text-white text-sm">{{ fmt.name }}</h3>
              <div class="flex items-center gap-1.5 mt-0.5">
                <span class="text-xs px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">
                  {{ getFrequencyLabel(fmt.frequency) }}
                </span>
                <span v-if="fmt.preferred_day" class="text-xs text-gray-500 dark:text-gray-400">
                  {{ fmt.preferred_day }}
                </span>
                <span v-if="fmt.preferred_time" class="text-xs text-gray-500 dark:text-gray-400">
                  {{ fmt.preferred_time }}
                </span>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-1">
            <span
              v-if="fmt.is_default"
              class="text-xs px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300"
            >Standard</span>
            <span
              :class="[
                'text-xs px-1.5 py-0.5 rounded',
                fmt.is_active
                  ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400',
              ]"
            >{{ fmt.is_active ? 'Aktiv' : 'Inaktiv' }}</span>
          </div>
        </div>

        <!-- Description -->
        <p class="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">{{ fmt.description }}</p>

        <!-- Meta -->
        <div class="flex flex-wrap gap-1.5 mb-3">
          <span v-if="fmt.tone" class="text-xs px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300">
            {{ getToneLabel(fmt.tone) }}
          </span>
          <span v-if="fmt.category" class="text-xs px-2 py-0.5 rounded-full bg-teal-100 dark:bg-teal-900 text-teal-700 dark:text-teal-300">
            {{ getCategoryLabel(fmt.category) }}
          </span>
        </div>

        <!-- Hashtags -->
        <div v-if="fmt.hashtags && fmt.hashtags.length > 0" class="flex flex-wrap gap-1 mb-3">
          <span v-for="tag in fmt.hashtags.slice(0, 4)" :key="tag"
            class="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
            {{ tag }}
          </span>
          <span v-if="fmt.hashtags.length > 4" class="text-xs text-gray-400">+{{ fmt.hashtags.length - 4 }}</span>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-2 pt-2 border-t border-gray-100 dark:border-gray-700">
          <button
            @click="toggleActive(fmt)"
            :class="[
              'text-xs px-2.5 py-1 rounded transition-colors',
              fmt.is_active
                ? 'bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300 hover:bg-orange-200'
                : 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 hover:bg-green-200',
            ]"
          >{{ fmt.is_active ? 'Deaktivieren' : 'Aktivieren' }}</button>

          <button
            @click="generateAIPreview(fmt)"
            data-tour="formats-ai-preview"
            class="text-xs px-2.5 py-1 rounded bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-200 transition-colors"
          >KI-Text</button>

          <button
            v-if="!fmt.is_default"
            @click="deleteFormat(fmt.id)"
            class="text-xs px-2.5 py-1 rounded bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 hover:bg-red-200 transition-colors ml-auto"
          >Loeschen</button>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <EmptyState
      v-if="!loading && filteredFormats.length === 0"
      svgIcon="arrow-path"
      title="Keine wiederkehrenden Formate"
      description="Erstelle dein erstes wiederkehrendes Format wie 'Motivation Monday' oder 'Freitags-Fail'. Formate sorgen fuer konsistenten Content und hoeheres Engagement."
      actionLabel="Format erstellen"
      @action="showCreateForm = true"
    />

    <!-- AI Preview Modal -->
    <div v-if="aiPreviewFormat" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="closeAIPreview">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-lg w-full mx-4 p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ aiPreviewFormat.icon }} KI-Textvorschlag: {{ aiPreviewFormat.name }}
          </h3>
          <button @click="closeAIPreview" class="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
        </div>

        <div class="space-y-3 mb-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Thema (optional)</label>
            <input v-model="aiTopic" type="text" placeholder="z.B. Trinkgeld-Kultur in den USA"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Land (optional)</label>
            <select v-model="aiCountry"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm">
              <option v-for="c in COUNTRIES" :key="c.value" :value="c.value">{{ c.label }}</option>
            </select>
          </div>
          <button
            @click="runAIGeneration"
            :disabled="aiLoading"
            class="w-full bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <span v-if="aiLoading" class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
            <span>{{ aiLoading ? 'Generiere...' : 'Text generieren' }}</span>
          </button>
        </div>

        <!-- AI Result -->
        <div v-if="aiResult" class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-gray-50 dark:bg-gray-900">
          <div class="mb-2">
            <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Titel</span>
            <p class="font-semibold text-gray-900 dark:text-white">{{ aiResult.title }}</p>
          </div>
          <div class="mb-2">
            <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Caption</span>
            <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line">{{ aiResult.caption }}</p>
          </div>
          <div class="mb-2">
            <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Hashtags</span>
            <div class="flex flex-wrap gap-1 mt-1">
              <span v-for="tag in aiResult.hashtags" :key="tag"
                class="text-xs px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300">
                {{ tag }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2 mt-2">
            <span :class="[
              'text-xs px-2 py-0.5 rounded',
              aiResult.source === 'gemini'
                ? 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400',
            ]">
              {{ aiResult.source === 'gemini' ? 'Gemini AI' : 'Regelbasiert' }}
            </span>
            <span class="text-xs text-gray-400">Thema: {{ aiResult.topic_used }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Info Section -->
    <div data-tour="formats-info" class="mt-8 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-5">
      <h3 class="font-semibold text-blue-900 dark:text-blue-200 mb-2">Wie funktionieren wiederkehrende Formate?</h3>
      <ul class="text-sm text-blue-800 dark:text-blue-300 space-y-1.5">
        <li>Aktive Formate erscheinen als Platzhalter im <strong>Kalender</strong> am bevorzugten Wochentag.</li>
        <li>Der <strong>Wochenplaner</strong> schlaegt automatisch Inhalte fuer aktive Formate vor.</li>
        <li>Nutze <strong>KI-Text</strong> um Textvorschlaege fuer jedes Format zu generieren.</li>
        <li>Standard-Formate koennen nicht geloescht, aber deaktiviert werden.</li>
        <li>Erstelle eigene Formate fuer deine individuelle Content-Strategie!</li>
      </ul>
    </div>

    <TourSystem ref="tourRef" page-key="recurring-formats" />
  </div>
</template>
