<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import AppIcon from '@/components/icons/AppIcon.vue'

const router = useRouter()
const toast = useToast()

// Wizard state
const currentStep = ref(1)
const totalSteps = 6
const saving = ref(false)

// Step 1: Student selection
const students = ref([])
const selectedStudentId = ref(null)
const loadingStudents = ref(false)
const showNewStudentForm = ref(false)
const newStudentName = ref('')
const newStudentCountry = ref('')
const creatingStudent = ref(false)

// Step 2: Title & Description
const arcTitle = ref('')
const arcSubtitle = ref('')
const arcDescription = ref('')
const titleSuggestions = ref([])
const loadingTitleSuggestions = ref(false)

// Step 3: Chapter Planning
const episodes = ref([])
const loadingEpisodes = ref(false)
const plannedEpisodeCount = ref(8)
const editingEpisodeIndex = ref(null)
const editTitle = ref('')
const editDescription = ref('')

// Step 4: Tone & Style
const selectedTone = ref('jugendlich')
const toneOptions = [
  { value: 'jugendlich', label: 'Jugendlich', icon: 'fire', description: 'Begeisternd, energetisch, motivierend - perfekt für die Zielgruppe' },
  { value: 'serioess', label: 'Seriös', icon: 'clipboard-list', description: 'Professionell, vertrauenswürdig - ideal wenn Eltern mitlesen' },
]

// Step 5: Schedule
const scheduleFrequency = ref('weekly')
const scheduleStartDate = ref('')
const createCalendarPlaceholders = ref(true)
const frequencyOptions = [
  { value: 'daily', label: 'Täglich', icon: 'fire', description: '1 Episode pro Tag - intensiv' },
  { value: 'twice_weekly', label: '2x pro Woche', icon: 'calendar', description: 'Montag & Donnerstag - gut für Engagement' },
  { value: 'weekly', label: 'Wöchentlich', icon: 'clipboard-list', description: '1x pro Woche - nachhaltig und konsistent' },
  { value: 'biweekly', label: 'Alle 2 Wochen', icon: 'clock', description: 'Gemächlich - für langfristige Serien' },
]

// Step 6: Cover Image
const assets = ref([])
const selectedCoverImageId = ref(null)
const loadingAssets = ref(false)
const coverImagePrompt = ref('')
const generatingCoverImage = ref(false)

// Countries list
const countries = [
  { value: 'usa', label: 'USA', flag: '🇺🇸' },
  { value: 'kanada', label: 'Kanada', flag: '🇨🇦' },
  { value: 'australien', label: 'Australien', flag: '🇦🇺' },
  { value: 'neuseeland', label: 'Neuseeland', flag: '🇳🇿' },
  { value: 'irland', label: 'Irland', flag: '🇮🇪' },
]

// Computed
const selectedStudent = computed(() => {
  if (!selectedStudentId.value) return null
  return students.value.find(s => s.id === selectedStudentId.value) || null
})

const selectedCountry = computed(() => {
  if (selectedStudent.value?.country) return selectedStudent.value.country
  return ''
})

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 1: return true // Student is optional
    case 2: return arcTitle.value.trim().length > 0
    case 3: return episodes.value.length >= 2
    case 4: return true // Tone has default
    case 5: return true // Schedule has defaults
    case 6: return true // Cover image is optional
    default: return true
  }
})

const stepLabels = [
  'Student',
  'Titel',
  'Kapitel',
  'Stil',
  'Zeitplan',
  'Cover',
]

// Load students
async function loadStudents() {
  loadingStudents.value = true
  try {
    const response = await api.get('/api/students')
    students.value = response.data
  } catch (err) {
    // Error toast shown by API interceptor
  } finally {
    loadingStudents.value = false
  }
}

// Create new student inline
async function createNewStudent() {
  if (!newStudentName.value.trim() || !newStudentCountry.value) return
  creatingStudent.value = true
  try {
    const response = await api.post('/api/students', {
      name: newStudentName.value.trim(),
      country: newStudentCountry.value,
      status: 'active',
    })
    students.value.unshift(response.data)
    selectedStudentId.value = response.data.id
    showNewStudentForm.value = false
    newStudentName.value = ''
    newStudentCountry.value = ''
    toast.success('Student erstellt!')
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Fehler beim Erstellen')
  } finally {
    creatingStudent.value = false
  }
}

// Suggest titles
async function suggestTitles() {
  loadingTitleSuggestions.value = true
  try {
    const response = await api.post('/api/ai/suggest-arc-title', {
      student_id: selectedStudentId.value,
      country: selectedCountry.value,
      tone: selectedTone.value,
    })
    titleSuggestions.value = response.data.suggestions || []
  } catch (err) {
    // Error toast shown by API interceptor
    toast.error('Titelvorschläge konnten nicht geladen werden')
  } finally {
    loadingTitleSuggestions.value = false
  }
}

// Apply title suggestion
function applyTitleSuggestion(suggestion) {
  arcTitle.value = suggestion.title
  arcSubtitle.value = suggestion.subtitle || ''
  arcDescription.value = suggestion.description || ''
}

// Suggest chapters
async function suggestChapters() {
  loadingEpisodes.value = true
  try {
    const response = await api.post('/api/ai/suggest-arc-chapters', {
      student_id: selectedStudentId.value,
      country: selectedCountry.value,
      title: arcTitle.value,
      description: arcDescription.value,
      planned_episodes: plannedEpisodeCount.value,
      tone: selectedTone.value,
    })
    episodes.value = (response.data.episodes || []).map(ep => ({
      number: ep.number,
      title: ep.title,
      description: ep.description,
    }))
  } catch (err) {
    // Error toast shown by API interceptor
    toast.error('Kapitelvorschläge konnten nicht geladen werden')
  } finally {
    loadingEpisodes.value = false
  }
}

// Episode management
function addEpisode() {
  const nextNum = episodes.value.length + 1
  episodes.value.push({
    number: nextNum,
    title: `Episode ${nextNum}`,
    description: '',
  })
}

function removeEpisode(index) {
  episodes.value.splice(index, 1)
  // Re-number
  episodes.value.forEach((ep, i) => { ep.number = i + 1 })
}

function startEditEpisode(index) {
  editingEpisodeIndex.value = index
  editTitle.value = episodes.value[index].title
  editDescription.value = episodes.value[index].description
}

function saveEditEpisode() {
  if (editingEpisodeIndex.value !== null) {
    episodes.value[editingEpisodeIndex.value].title = editTitle.value
    episodes.value[editingEpisodeIndex.value].description = editDescription.value
    editingEpisodeIndex.value = null
  }
}

function cancelEditEpisode() {
  editingEpisodeIndex.value = null
}

function moveEpisode(index, direction) {
  const newIndex = index + direction
  if (newIndex < 0 || newIndex >= episodes.value.length) return
  const temp = episodes.value[index]
  episodes.value[index] = episodes.value[newIndex]
  episodes.value[newIndex] = temp
  // Re-number
  episodes.value.forEach((ep, i) => { ep.number = i + 1 })
}

// Load assets for cover image selection
async function loadAssets() {
  loadingAssets.value = true
  try {
    const response = await api.get('/api/assets')
    assets.value = (response.data || []).filter(a => a.file_type === 'image')
  } catch (err) {
    // Error toast shown by API interceptor
  } finally {
    loadingAssets.value = false
  }
}

// Generate cover image with AI
async function generateCoverImage() {
  if (!coverImagePrompt.value.trim()) {
    toast.error('Bitte gib einen Prompt ein')
    return
  }
  generatingCoverImage.value = true
  try {
    const response = await api.post('/api/ai/generate-image', {
      prompt: coverImagePrompt.value.trim(),
      platform: 'instagram_story',
      category: 'cover_image',
      country: selectedCountry.value,
    })
    if (response.data.asset) {
      assets.value.unshift(response.data.asset)
      selectedCoverImageId.value = response.data.asset.id
      toast.success('Cover-Bild generiert!')
    }
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Bild-Generierung fehlgeschlagen')
  } finally {
    generatingCoverImage.value = false
  }
}

// Navigation
function nextStep() {
  if (currentStep.value < totalSteps && canProceed.value) {
    currentStep.value++
    // Auto-load data for certain steps
    if (currentStep.value === 3 && episodes.value.length === 0) {
      suggestChapters()
    }
    if (currentStep.value === 6) {
      loadAssets()
    }
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

function goToStep(step) {
  // Only allow going to completed steps or current step
  if (step <= currentStep.value) {
    currentStep.value = step
  }
}

// Set default start date
function setDefaultStartDate() {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  scheduleStartDate.value = tomorrow.toISOString().split('T')[0]
}

// Save wizard
async function saveWizard() {
  if (!arcTitle.value.trim()) {
    toast.error('Bitte gib einen Titel ein')
    return
  }
  saving.value = true
  try {
    const payload = {
      title: arcTitle.value.trim(),
      subtitle: arcSubtitle.value.trim() || null,
      description: arcDescription.value.trim() || null,
      student_id: selectedStudentId.value || null,
      country: selectedCountry.value || null,
      tone: selectedTone.value,
      planned_episodes: episodes.value.length,
      cover_image_id: selectedCoverImageId.value || null,
      status: 'active',
      episodes: episodes.value.map(ep => ({
        title: ep.title,
        description: ep.description,
      })),
      schedule_frequency: scheduleFrequency.value,
      schedule_start_date: scheduleStartDate.value || null,
      create_calendar_placeholders: createCalendarPlaceholders.value,
    }

    const response = await api.post('/api/story-arcs/wizard', payload)
    toast.success(`Story-Arc "${response.data.title}" erstellt mit ${response.data.episodes?.length || 0} Episoden!`)

    // Navigate to calendar or student detail
    if (response.data.calendar_posts_created > 0) {
      router.push('/calendar')
    } else if (selectedStudentId.value) {
      router.push(`/students/${selectedStudentId.value}`)
    } else {
      router.push('/home')
    }
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Fehler beim Erstellen des Story-Arcs')
  } finally {
    saving.value = false
  }
}

// Format schedule date for preview
function formatScheduleDate(index) {
  if (!scheduleStartDate.value) return ''
  const start = new Date(scheduleStartDate.value)
  const gaps = { daily: 1, twice_weekly: 3, weekly: 7, biweekly: 14 }
  const gap = gaps[scheduleFrequency.value] || 7
  const d = new Date(start.getTime() + index * gap * 86400000)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' })
}

// Init
onMounted(() => {
  loadStudents()
  setDefaultStartDate()
})
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        Story-Arc Wizard
      </h1>
      <p class="mt-1 text-gray-500 dark:text-gray-400">
        Erstelle eine neue Story-Serie in wenigen Schritten
      </p>
    </div>

    <!-- Step Indicator -->
    <div class="mb-8">
      <div class="flex items-center justify-between">
        <template v-for="(label, index) in stepLabels" :key="index">
          <button
            class="flex flex-col items-center group"
            @click="goToStep(index + 1)"
            :disabled="index + 1 > currentStep"
          >
            <div
              :class="[
                'w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all',
                index + 1 === currentStep
                  ? 'bg-treff-blue text-white ring-4 ring-treff-blue/20'
                  : index + 1 < currentStep
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400',
              ]"
            >
              <span v-if="index + 1 < currentStep">&#10003;</span>
              <span v-else>{{ index + 1 }}</span>
            </div>
            <span
              :class="[
                'mt-1 text-xs font-medium',
                index + 1 === currentStep
                  ? 'text-treff-blue'
                  : index + 1 < currentStep
                  ? 'text-green-600'
                  : 'text-gray-400',
              ]"
            >{{ label }}</span>
          </button>
          <div
            v-if="index < stepLabels.length - 1"
            :class="[
              'flex-1 h-0.5 mx-2',
              index + 1 < currentStep ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700',
            ]"
          />
        </template>
      </div>
    </div>

    <!-- Step Content -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 min-h-[400px]">

      <!-- ==================== STEP 1: Student Selection ==================== -->
      <div v-if="currentStep === 1">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
          Student auswählen
        </h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
          Wähle einen Studenten für die Serie oder überspringe diesen Schritt.
        </p>

        <!-- Loading -->
        <div v-if="loadingStudents" class="text-center py-8">
          <div class="animate-spin w-8 h-8 border-4 border-treff-blue border-t-transparent rounded-full mx-auto"></div>
          <p class="mt-2 text-sm text-gray-500">Lade Studenten...</p>
        </div>

        <!-- Student Cards -->
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
          <button
            v-for="student in students"
            :key="student.id"
            @click="selectedStudentId = selectedStudentId === student.id ? null : student.id"
            :class="[
              'p-4 rounded-lg border-2 text-left transition-all',
              selectedStudentId === student.id
                ? 'border-treff-blue bg-treff-blue/5'
                : 'border-gray-200 dark:border-gray-600 hover:border-gray-300',
            ]"
          >
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-treff-blue/10 flex items-center justify-center text-lg">
                <template v-if="countries.find(c => c.value === student.country)?.flag">{{ countries.find(c => c.value === student.country).flag }}</template>
                <AppIcon v-else name="academic-cap" class="w-5 h-5" />
              </div>
              <div>
                <div class="font-medium text-gray-900 dark:text-white">{{ student.name }}</div>
                <div class="text-xs text-gray-500">
                  {{ countries.find(c => c.value === student.country)?.label || student.country }}
                  <span v-if="student.city"> &middot; {{ student.city }}</span>
                </div>
              </div>
              <div v-if="selectedStudentId === student.id" class="ml-auto text-treff-blue text-xl">&#10003;</div>
            </div>
          </button>
        </div>

        <!-- No students -->
        <div v-if="!loadingStudents && students.length === 0" class="text-center py-4 text-gray-400">
          Noch keine Studenten angelegt.
        </div>

        <!-- New Student Form Toggle -->
        <div class="mt-4 border-t border-gray-100 dark:border-gray-700 pt-4">
          <button
            v-if="!showNewStudentForm"
            @click="showNewStudentForm = true"
            class="text-sm text-treff-blue hover:underline font-medium"
          >
            + Neuen Studenten anlegen
          </button>
          <div v-else class="space-y-3">
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300">Neuer Student</h3>
            <input
              v-model="newStudentName"
              type="text"
              placeholder="Name"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white"
            />
            <select
              v-model="newStudentCountry"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white"
            >
              <option value="">Land wählen...</option>
              <option v-for="c in countries" :key="c.value" :value="c.value">
                {{ c.flag }} {{ c.label }}
              </option>
            </select>
            <div class="flex gap-2">
              <button
                @click="createNewStudent"
                :disabled="creatingStudent || !newStudentName.trim() || !newStudentCountry"
                class="px-4 py-2 bg-treff-blue text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-treff-blue/90"
              >
                {{ creatingStudent ? 'Erstelle...' : 'Erstellen' }}
              </button>
              <button
                @click="showNewStudentForm = false"
                class="px-4 py-2 text-gray-500 hover:text-gray-700 text-sm"
              >
                Abbrechen
              </button>
            </div>
          </div>
        </div>

        <!-- Skip hint -->
        <p class="mt-4 text-xs text-gray-400">
          Du kannst diesen Schritt überspringen, wenn die Serie nicht an einen bestimmten Studenten gebunden ist.
        </p>
      </div>

      <!-- ==================== STEP 2: Title & Description ==================== -->
      <div v-if="currentStep === 2">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
          Titel & Beschreibung
        </h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
          Gib deiner Story-Serie einen einprägsamen Titel.
        </p>

        <!-- AI Suggestions -->
        <div class="mb-6">
          <button
            @click="suggestTitles"
            :disabled="loadingTitleSuggestions"
            class="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg text-sm font-medium hover:from-purple-600 hover:to-pink-600 disabled:opacity-50"
          >
            <span v-if="loadingTitleSuggestions">...</span>
            <AppIcon v-else name="sparkles" class="w-4 h-4" />
            {{ loadingTitleSuggestions ? 'Generiere Vorschläge...' : 'KI-Titelvorschläge' }}
          </button>

          <div v-if="titleSuggestions.length > 0" class="mt-3 space-y-2">
            <button
              v-for="(sug, i) in titleSuggestions"
              :key="i"
              @click="applyTitleSuggestion(sug)"
              class="w-full p-3 text-left rounded-lg border border-purple-200 dark:border-purple-700 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors"
            >
              <div class="font-medium text-gray-900 dark:text-white text-sm">{{ sug.title }}</div>
              <div v-if="sug.subtitle" class="text-xs text-purple-500 mt-0.5">{{ sug.subtitle }}</div>
              <div v-if="sug.description" class="text-xs text-gray-500 mt-1">{{ sug.description }}</div>
            </button>
          </div>
        </div>

        <!-- Manual Input -->
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Titel <span class="text-red-500">*</span>
            </label>
            <input
              v-model="arcTitle"
              type="text"
              placeholder="z.B. Emmas USA-Abenteuer"
              maxlength="100"
              class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-treff-blue"
            />
            <div class="text-xs text-gray-400 mt-1 text-right">{{ arcTitle.length }}/100</div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Untertitel</label>
            <input
              v-model="arcSubtitle"
              type="text"
              placeholder="z.B. Ein Auslandsjahr voller Überraschungen"
              maxlength="150"
              class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-treff-blue"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Beschreibung</label>
            <textarea
              v-model="arcDescription"
              rows="3"
              placeholder="Worum geht es in dieser Serie?"
              class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-treff-blue resize-none"
            ></textarea>
          </div>
        </div>
      </div>

      <!-- ==================== STEP 3: Chapter Planning ==================== -->
      <div v-if="currentStep === 3">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
          Kapitelplanung
        </h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Plane die Episoden deiner Serie. KI schlägt typische Kapitel vor.
        </p>

        <!-- Controls -->
        <div class="flex items-center gap-3 mb-4">
          <label class="text-sm text-gray-600 dark:text-gray-400">Anzahl Episoden:</label>
          <select
            v-model.number="plannedEpisodeCount"
            class="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white"
          >
            <option v-for="n in [3,4,5,6,7,8,10,12,15,20]" :key="n" :value="n">{{ n }}</option>
          </select>
          <button
            @click="suggestChapters"
            :disabled="loadingEpisodes"
            class="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg text-sm font-medium hover:from-purple-600 hover:to-pink-600 disabled:opacity-50"
          >
            <span v-if="loadingEpisodes">...</span>
            <AppIcon v-else name="sparkles" class="w-4 h-4" />
            {{ loadingEpisodes ? 'Generiere...' : 'KI-Vorschläge' }}
          </button>
          <button
            @click="addEpisode"
            class="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
          >
            + Hinzufügen
          </button>
        </div>

        <!-- Loading -->
        <div v-if="loadingEpisodes" class="text-center py-8">
          <div class="animate-spin w-8 h-8 border-4 border-treff-blue border-t-transparent rounded-full mx-auto"></div>
          <p class="mt-2 text-sm text-gray-500">KI plant Kapitelstruktur...</p>
        </div>

        <!-- Episode List -->
        <div v-else class="space-y-2 max-h-[360px] overflow-y-auto pr-1">
          <div
            v-for="(ep, index) in episodes"
            :key="index"
            class="p-3 rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50"
          >
            <!-- Viewing mode -->
            <div v-if="editingEpisodeIndex !== index" class="flex items-start gap-3">
              <div class="w-8 h-8 rounded-full bg-treff-blue/10 text-treff-blue font-bold text-sm flex items-center justify-center flex-shrink-0 mt-0.5">
                {{ ep.number }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="font-medium text-gray-900 dark:text-white text-sm">{{ ep.title }}</div>
                <div v-if="ep.description" class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ ep.description }}</div>
              </div>
              <div class="flex items-center gap-1 flex-shrink-0">
                <button @click="moveEpisode(index, -1)" :disabled="index === 0" class="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30" title="Nach oben">&#9650;</button>
                <button @click="moveEpisode(index, 1)" :disabled="index === episodes.length - 1" class="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30" title="Nach unten">&#9660;</button>
                <button @click="startEditEpisode(index)" class="p-1 text-gray-400 hover:text-treff-blue" title="Bearbeiten">&#9998;</button>
                <button @click="removeEpisode(index)" class="p-1 text-gray-400 hover:text-red-500" title="Entfernen">&#10005;</button>
              </div>
            </div>

            <!-- Editing mode -->
            <div v-else class="space-y-2">
              <input
                v-model="editTitle"
                type="text"
                class="w-full px-3 py-1.5 border border-treff-blue rounded-lg text-sm dark:bg-gray-700 dark:text-white"
                placeholder="Episodentitel"
              />
              <input
                v-model="editDescription"
                type="text"
                class="w-full px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white"
                placeholder="Kurze Beschreibung"
              />
              <div class="flex gap-2">
                <button @click="saveEditEpisode" class="px-3 py-1 bg-treff-blue text-white rounded text-xs font-medium">Speichern</button>
                <button @click="cancelEditEpisode" class="px-3 py-1 text-gray-500 rounded text-xs">Abbrechen</button>
              </div>
            </div>
          </div>

          <!-- Empty state -->
          <div v-if="episodes.length === 0" class="text-center py-8 text-gray-400">
            <AppIcon name="book-open" class="w-8 h-8 mx-auto mb-2" />
            <p>Klicke auf "KI-Vorschläge" um Kapitel zu generieren</p>
          </div>
        </div>
      </div>

      <!-- ==================== STEP 4: Tone & Style ==================== -->
      <div v-if="currentStep === 4">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
          Ton & Stil
        </h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
          Lege den Erzählstil deiner Serie fest.
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <button
            v-for="option in toneOptions"
            :key="option.value"
            @click="selectedTone = option.value"
            :class="[
              'p-5 rounded-xl border-2 text-left transition-all',
              selectedTone === option.value
                ? 'border-treff-blue bg-treff-blue/5 ring-2 ring-treff-blue/20'
                : 'border-gray-200 dark:border-gray-600 hover:border-gray-300',
            ]"
          >
            <AppIcon :name="option.icon" class="w-8 h-8 mb-2" />
            <div class="font-semibold text-gray-900 dark:text-white">{{ option.label }}</div>
            <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ option.description }}</div>
          </button>
        </div>

        <div class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <p class="text-sm text-blue-700 dark:text-blue-300">
            <strong>Tipp:</strong> Der Ton wird in der KI-Textgenerierung für alle Episoden verwendet.
            "Jugendlich" spricht Schüler direkt an, "Seriös" ist ideal für informative Serien, die auch Eltern lesen.
          </p>
        </div>
      </div>

      <!-- ==================== STEP 5: Schedule ==================== -->
      <div v-if="currentStep === 5">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
          Zeitplanung
        </h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
          Plane, wie oft neue Episoden erscheinen sollen.
        </p>

        <!-- Frequency -->
        <div class="space-y-3 mb-6">
          <button
            v-for="option in frequencyOptions"
            :key="option.value"
            @click="scheduleFrequency = option.value"
            :class="[
              'w-full p-4 rounded-lg border-2 text-left transition-all flex items-center gap-4',
              scheduleFrequency === option.value
                ? 'border-treff-blue bg-treff-blue/5'
                : 'border-gray-200 dark:border-gray-600 hover:border-gray-300',
            ]"
          >
            <AppIcon :name="option.icon" class="w-7 h-7" />
            <div>
              <div class="font-medium text-gray-900 dark:text-white">{{ option.label }}</div>
              <div class="text-xs text-gray-500">{{ option.description }}</div>
            </div>
            <div v-if="scheduleFrequency === option.value" class="ml-auto text-treff-blue text-xl">&#10003;</div>
          </button>
        </div>

        <!-- Start Date -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Startdatum
          </label>
          <input
            v-model="scheduleStartDate"
            type="date"
            class="px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-treff-blue"
          />
        </div>

        <!-- Calendar Placeholders Toggle -->
        <label class="flex items-center gap-3 cursor-pointer">
          <div
            :class="[
              'relative w-11 h-6 rounded-full transition-colors',
              createCalendarPlaceholders ? 'bg-treff-blue' : 'bg-gray-300 dark:bg-gray-600',
            ]"
            @click="createCalendarPlaceholders = !createCalendarPlaceholders"
          >
            <div
              :class="[
                'absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow',
                createCalendarPlaceholders ? 'translate-x-5' : '',
              ]"
            />
          </div>
          <div>
            <div class="font-medium text-sm text-gray-900 dark:text-white">Kalender-Platzhalter erstellen</div>
            <div class="text-xs text-gray-500">Erstellt Draft-Posts im Kalender für jede Episode</div>
          </div>
        </label>

        <!-- Preview -->
        <div v-if="createCalendarPlaceholders && episodes.length > 0 && scheduleStartDate" class="mt-6 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Vorschau Zeitplan:</h3>
          <div class="space-y-1 max-h-[200px] overflow-y-auto">
            <div v-for="(ep, i) in episodes" :key="i" class="flex items-center gap-2 text-sm">
              <span class="w-6 h-6 rounded-full bg-treff-blue/10 text-treff-blue text-xs flex items-center justify-center font-bold">{{ ep.number }}</span>
              <span class="text-gray-500 w-20">{{ formatScheduleDate(i) }}</span>
              <span class="text-gray-900 dark:text-white">{{ ep.title }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ==================== STEP 6: Cover Image ==================== -->
      <div v-if="currentStep === 6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
          Cover-Bild
        </h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
          Wähle ein Cover-Bild aus deiner Bibliothek oder generiere eines mit KI.
        </p>

        <!-- AI Generation -->
        <div class="mb-6 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
          <h3 class="text-sm font-medium text-purple-700 dark:text-purple-300 mb-2">KI Cover-Bild generieren</h3>
          <div class="flex gap-2">
            <input
              v-model="coverImagePrompt"
              type="text"
              :placeholder="`z.B. Highschool-Gebäude in ${countries.find(c => c.value === selectedCountry)?.label || 'USA'} mit Sonnenlicht`"
              class="flex-1 px-3 py-2 border border-purple-300 dark:border-purple-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white"
            />
            <button
              @click="generateCoverImage"
              :disabled="generatingCoverImage"
              class="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg text-sm font-medium hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 whitespace-nowrap"
            >
              <template v-if="generatingCoverImage">Generiere...</template>
              <template v-else><AppIcon name="sparkles" class="w-4 h-4 inline-block" /> Generieren</template>
            </button>
          </div>
        </div>

        <!-- Asset Grid -->
        <div v-if="loadingAssets" class="text-center py-8">
          <div class="animate-spin w-8 h-8 border-4 border-treff-blue border-t-transparent rounded-full mx-auto"></div>
        </div>
        <div v-else-if="assets.length > 0" class="grid grid-cols-3 sm:grid-cols-4 gap-3 max-h-[300px] overflow-y-auto">
          <button
            v-for="asset in assets"
            :key="asset.id"
            @click="selectedCoverImageId = selectedCoverImageId === asset.id ? null : asset.id"
            :class="[
              'relative aspect-square rounded-lg overflow-hidden border-2 transition-all',
              selectedCoverImageId === asset.id
                ? 'border-treff-blue ring-2 ring-treff-blue/30'
                : 'border-transparent hover:border-gray-300',
            ]"
          >
            <img
              :src="`/api/assets/${asset.id}/file`"
              :alt="asset.original_name"
              class="w-full h-full object-cover"
            />
            <div v-if="selectedCoverImageId === asset.id" class="absolute inset-0 bg-treff-blue/30 flex items-center justify-center">
              <span class="text-white text-2xl font-bold">&#10003;</span>
            </div>
          </button>
        </div>
        <div v-else class="text-center py-8 text-gray-400">
          <p>Keine Bilder in der Bibliothek. Generiere ein Cover-Bild oder lade eins in der Asset-Verwaltung hoch.</p>
        </div>

        <p class="mt-4 text-xs text-gray-400">
          Das Cover-Bild ist optional. Du kannst es später noch ändern.
        </p>
      </div>
    </div>

    <!-- Navigation Buttons -->
    <div class="flex items-center justify-between mt-6">
      <button
        v-if="currentStep > 1"
        @click="prevStep"
        class="px-5 py-2.5 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 font-medium text-sm"
      >
        Zurück
      </button>
      <div v-else></div>

      <div class="flex gap-3">
        <button
          v-if="currentStep < totalSteps"
          @click="nextStep"
          :disabled="!canProceed"
          class="px-5 py-2.5 bg-treff-blue text-white rounded-lg hover:bg-treff-blue/90 font-medium text-sm disabled:opacity-50"
        >
          Weiter
        </button>
        <button
          v-if="currentStep === totalSteps"
          @click="saveWizard"
          :disabled="saving || !arcTitle.trim()"
          class="px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium text-sm disabled:opacity-50 flex items-center gap-2"
        >
          <span v-if="saving" class="animate-spin">&#8635;</span>
          {{ saving ? 'Erstelle Serie...' : 'Serie erstellen' }}
        </button>
      </div>
    </div>
  </div>
</template>

