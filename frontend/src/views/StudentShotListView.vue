<script setup>
/**
 * StudentShotListView - Shot-List-Generator & Filming Guide fuer Studenten
 *
 * Main view for creating, managing, and sharing shot lists for students abroad.
 * Supports:
 * - Generating shot lists by content type, country, season
 * - Viewing all active shot lists with filters
 * - Sharing shot lists via public link (Mobile-First for students)
 * - Connection to Video-Script-Generator (V-06)
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import ShotListCard from '@/components/video/ShotListCard.vue'

const router = useRouter()
const toast = useToast()

// ── State ──────────────────────────────────
const activeTab = ref('overview') // overview | generate
const isLoading = ref(false)
const isGenerating = ref(false)

// Overview state
const shotLists = ref([])
const expandedId = ref(null)
const filterStatus = ref('')
const filterCountry = ref('')

// Generate form
const contentTypes = ref([])
const seasonalSuggestions = ref([])
const selectedContentType = ref('')
const selectedCountry = ref('')
const studentName = ref('')
const videoScripts = ref([])
const selectedScriptId = ref(null)

// Share modal
const shareModalOpen = ref(false)
const shareUrl = ref('')

// ── Constants ──────────────────────────────
const countries = [
  { value: '', label: 'Alle Länder' },
  { value: 'usa', label: '🇺🇸 USA' },
  { value: 'canada', label: '🇨🇦 Kanada' },
  { value: 'australia', label: '🇦🇺 Australien' },
  { value: 'newzealand', label: '🇳🇿 Neuseeland' },
  { value: 'ireland', label: '🇮🇪 Irland' },
]

const statusFilters = [
  { value: '', label: 'Alle Status' },
  { value: 'active', label: 'Aktiv' },
  { value: 'completed', label: 'Abgeschlossen' },
  { value: 'archived', label: 'Archiviert' },
]

const contentTypeIcons = {
  arrival_story: '✈️',
  first_day_school: '🏫',
  school_day: '📚',
  host_family: '👨‍👩‍👧‍👦',
  cultural_moment: '🌎',
  holiday: '🎄',
  school_event: '🎉',
  farewell: '😢',
  alumni: '🎓',
  general: '📹',
}

// ── Computed ───────────────────────────────
const filteredLists = computed(() => {
  let items = [...shotLists.value]
  if (filterStatus.value) {
    items = items.filter(i => i.status === filterStatus.value)
  }
  if (filterCountry.value) {
    items = items.filter(i => i.country === filterCountry.value)
  }
  return items
})

const totalActive = computed(() => shotLists.value.filter(s => s.status === 'active').length)
const totalCompleted = computed(() => shotLists.value.filter(s => s.status === 'completed').length)

// ── Data Loading ──────────────────────────
onMounted(async () => {
  await Promise.all([
    loadShotLists(),
    loadContentTypes(),
    loadVideoScripts(),
  ])
})

async function loadShotLists() {
  isLoading.value = true
  try {
    const { data } = await api.get('/api/shot-lists', { params: { limit: 50 } })
    shotLists.value = data.items || []
  } catch (e) {
    console.error('Failed to load shot lists:', e)
  } finally {
    isLoading.value = false
  }
}

async function loadContentTypes() {
  try {
    const { data } = await api.get('/api/shot-lists/content-types')
    contentTypes.value = data.content_types || []
    seasonalSuggestions.value = data.seasonal_suggestions || []
  } catch (e) {
    console.error('Failed to load content types:', e)
  }
}

async function loadVideoScripts() {
  try {
    const { data } = await api.get('/api/video-scripts', { params: { limit: 10 } })
    videoScripts.value = data.scripts || []
  } catch (e) {
    console.error('Failed to load video scripts:', e)
  }
}

// ── Actions ────────────────────────────────
async function generateShotList() {
  if (!selectedContentType.value) {
    toast.error('Bitte wähle einen Content-Typ')
    return
  }
  isGenerating.value = true
  try {
    const payload = {
      content_type: selectedContentType.value,
    }
    if (selectedCountry.value) payload.country = selectedCountry.value
    if (studentName.value) payload.student_name = studentName.value
    if (selectedScriptId.value) payload.video_script_id = selectedScriptId.value

    const { data } = await api.post('/api/shot-lists/generate', payload)
    toast.success(`Shot-List "${data.title}" erstellt!`)
    shotLists.value.unshift(data)
    expandedId.value = data.id
    activeTab.value = 'overview'
    // Reset form
    selectedContentType.value = ''
    studentName.value = ''
    selectedScriptId.value = null
  } catch (e) {
    console.error('Failed to generate shot list:', e)
    toast.error('Shot-List konnte nicht generiert werden')
  } finally {
    isGenerating.value = false
  }
}

async function generateFromScript(scriptId) {
  isGenerating.value = true
  try {
    const { data } = await api.post(`/api/shot-lists/from-script/${scriptId}`)
    toast.success(`Shot-List aus Script erstellt!`)
    shotLists.value.unshift(data)
    expandedId.value = data.id
    activeTab.value = 'overview'
  } catch (e) {
    toast.error('Shot-List aus Script konnte nicht generiert werden')
  } finally {
    isGenerating.value = false
  }
}

function toggleExpand(id) {
  expandedId.value = expandedId.value === id ? null : id
}

async function toggleShare(id) {
  try {
    const { data } = await api.post(`/api/shot-lists/${id}/share`)
    const idx = shotLists.value.findIndex(s => s.id === id)
    if (idx >= 0) shotLists.value[idx] = data

    if (data.is_shared && data.share_token) {
      shareUrl.value = `${window.location.origin}/api/shot-lists/shared/${data.share_token}`
      shareModalOpen.value = true
      toast.success('Shot-List wird jetzt geteilt!')
    } else {
      toast.info('Teilen deaktiviert')
    }
  } catch (e) {
    toast.error('Teilen fehlgeschlagen')
  }
}

async function deleteShotList(id) {
  try {
    await api.delete(`/api/shot-lists/${id}`)
    shotLists.value = shotLists.value.filter(s => s.id !== id)
    toast.success('Shot-List geloescht')
  } catch (e) {
    toast.error('Loeschen fehlgeschlagen')
  }
}

function openShotList(id) {
  expandedId.value = id
}

function copyShareLink() {
  navigator.clipboard.writeText(shareUrl.value).then(() => {
    toast.success('Link kopiert!')
  }).catch(() => {
    toast.error('Kopieren fehlgeschlagen')
  })
}
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        Shot-List & Filming-Guide
      </h1>
      <p class="text-gray-600 dark:text-gray-400 mt-1">
        Erstelle konkrete Filmaufträge für Austauschschüler — mit Beispielen, Tipps und Checklisten
      </p>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-3 gap-4 mb-6">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow p-4 text-center">
        <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ shotLists.length }}</div>
        <div class="text-xs text-gray-500 dark:text-gray-400">Gesamt</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow p-4 text-center">
        <div class="text-2xl font-bold text-green-600">{{ totalActive }}</div>
        <div class="text-xs text-gray-500 dark:text-gray-400">Aktiv</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow p-4 text-center">
        <div class="text-2xl font-bold text-blue-600">{{ totalCompleted }}</div>
        <div class="text-xs text-gray-500 dark:text-gray-400">Abgeschlossen</div>
      </div>
    </div>

    <!-- Tab Switcher -->
    <div class="flex gap-2 mb-6">
      <button
        @click="activeTab = 'overview'"
        :class="[
          'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
          activeTab === 'overview'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
        ]"
      >
        Übersicht
      </button>
      <button
        @click="activeTab = 'generate'"
        :class="[
          'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
          activeTab === 'generate'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
        ]"
      >
        + Neue Shot-List
      </button>
    </div>

    <!-- ═══════════════════════════════════════════ -->
    <!-- TAB: Overview -->
    <!-- ═══════════════════════════════════════════ -->
    <div v-if="activeTab === 'overview'">
      <!-- Filters -->
      <div class="flex gap-3 mb-4 flex-wrap">
        <select
          v-model="filterStatus"
          class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
        >
          <option v-for="s in statusFilters" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
        <select
          v-model="filterCountry"
          class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
        >
          <option v-for="c in countries" :key="c.value" :value="c.value">{{ c.label }}</option>
        </select>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent" />
        <p class="mt-2 text-gray-500 dark:text-gray-400">Lade Shot-Lists...</p>
      </div>

      <!-- Empty state -->
      <div v-else-if="filteredLists.length === 0" class="text-center py-16 bg-white dark:bg-gray-800 rounded-xl shadow">
        <div class="text-4xl mb-3">📹</div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Noch keine Shot-Lists
        </h3>
        <p class="text-gray-500 dark:text-gray-400 mb-4">
          Erstelle deine erste Shot-List für einen Austauschschüler.
        </p>
        <button
          @click="activeTab = 'generate'"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Erste Shot-List erstellen
        </button>
      </div>

      <!-- Shot List Cards -->
      <div v-else class="space-y-4">
        <ShotListCard
          v-for="sl in filteredLists"
          :key="sl.id"
          :shot-list="sl"
          :expanded="expandedId === sl.id"
          @toggle="toggleExpand"
          @share="toggleShare"
          @delete="deleteShotList"
          @open="openShotList"
        />
      </div>
    </div>

    <!-- ═══════════════════════════════════════════ -->
    <!-- TAB: Generate -->
    <!-- ═══════════════════════════════════════════ -->
    <div v-if="activeTab === 'generate'" class="space-y-6">
      <!-- Content Type Selection -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          1. Content-Typ wählen
        </h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Wähle welche Art von Content der Schüler filmen soll. Saisonale Empfehlungen sind hervorgehoben.
        </p>

        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          <button
            v-for="ct in contentTypes"
            :key="ct.id"
            @click="selectedContentType = ct.id"
            :class="[
              'p-3 rounded-lg border-2 text-center transition-all',
              selectedContentType === ct.id
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 ring-2 ring-blue-200'
                : ct.is_seasonal
                  ? 'border-yellow-300 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/10 hover:border-yellow-400'
                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
            ]"
          >
            <div class="text-2xl mb-1">{{ contentTypeIcons[ct.id] || '📹' }}</div>
            <div class="text-xs font-medium text-gray-900 dark:text-white">{{ ct.label }}</div>
            <div v-if="ct.is_seasonal" class="text-[10px] text-yellow-600 dark:text-yellow-400 mt-0.5 font-medium">
              Saisonal empfohlen
            </div>
          </button>
        </div>
      </div>

      <!-- Details -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          2. Details festlegen
        </h2>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Land
            </label>
            <select
              v-model="selectedCountry"
              class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">Kein Land (allgemein)</option>
              <option value="usa">🇺🇸 USA</option>
              <option value="canada">🇨🇦 Kanada</option>
              <option value="australia">🇦🇺 Australien</option>
              <option value="newzealand">🇳🇿 Neuseeland</option>
              <option value="ireland">🇮🇪 Irland</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Schüler-Name (optional)
            </label>
            <input
              v-model="studentName"
              type="text"
              placeholder="z.B. Lisa Müller"
              class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
        </div>
      </div>

      <!-- From Video Script (V-06 Connection) -->
      <div v-if="videoScripts.length > 0" class="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Oder: Aus Video-Script erstellen
        </h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Generiere eine Shot-List basierend auf einem bestehenden Video-Script (V-06).
        </p>

        <div class="space-y-2">
          <div
            v-for="script in videoScripts.slice(0, 5)"
            :key="script.id"
            class="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
          >
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-white">{{ script.title }}</p>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                {{ script.platform }} | {{ script.duration_seconds }}s | {{ script.scenes?.length || 0 }} Szenen
              </p>
            </div>
            <button
              @click="generateFromScript(script.id)"
              :disabled="isGenerating"
              class="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
            >
              Shot-List ableiten
            </button>
          </div>
        </div>
      </div>

      <!-- Generate Button -->
      <div class="flex justify-end">
        <button
          @click="generateShotList"
          :disabled="!selectedContentType || isGenerating"
          class="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2 text-sm font-medium"
        >
          <svg v-if="isGenerating" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          {{ isGenerating ? 'Generiere...' : 'Shot-List generieren' }}
        </button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════ -->
    <!-- Share Modal -->
    <!-- ═══════════════════════════════════════════ -->
    <div
      v-if="shareModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="shareModalOpen = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Shot-List teilen
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Sende diesen Link an den Schüler. Die Shot-List wird als mobile-freundliche Checkliste angezeigt.
        </p>
        <div class="flex items-center gap-2 mb-4">
          <input
            :value="shareUrl"
            readonly
            class="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
          />
          <button
            @click="copyShareLink"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm transition-colors"
          >
            Kopieren
          </button>
        </div>
        <div class="flex justify-end">
          <button
            @click="shareModalOpen = false"
            class="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
          >
            Schließen
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
