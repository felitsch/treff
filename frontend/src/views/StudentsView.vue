<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '@/stores/students'
import { useToast } from '@/composables/useToast'
import PersonalityEditor from '@/components/students/PersonalityEditor.vue'
import WorkflowHint from '@/components/common/WorkflowHint.vue'
import api from '@/utils/api'
import TourSystem from '@/components/common/TourSystem.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const router = useRouter()
const store = useStudentStore()
const toast = useToast()

const tourRef = ref(null)

// Workflow hint: show Story-Arc hint when students exist but no arcs
const storyArcCount = ref(-1) // -1 = not loaded yet
async function checkStoryArcs() {
  try {
    const { data } = await api.get('/api/story-arcs')
    storyArcCount.value = Array.isArray(data) ? data.length : 0
  } catch { storyArcCount.value = 0 }
}
const showStoryArcHint = computed(() => {
  return store.students.length > 0 && storyArcCount.value === 0
})

// Filters
const filterCountry = ref('')
const filterStatus = ref('')
const searchQuery = ref('')

// Form state
const showForm = ref(false)
const editingStudent = ref(null)
const formData = ref(getEmptyForm())

// Delete confirmation
const showDeleteConfirm = ref(false)
const studentToDelete = ref(null)

const countries = [
  { value: 'usa', label: 'USA' },
  { value: 'kanada', label: 'Kanada' },
  { value: 'australien', label: 'Australien' },
  { value: 'neuseeland', label: 'Neuseeland' },
  { value: 'irland', label: 'Irland' },
]

const statuses = [
  { value: 'active', label: 'Aktiv' },
  { value: 'upcoming', label: 'Bevorstehend' },
  { value: 'completed', label: 'Abgeschlossen' },
]

const countryFlags = {
  usa: '🇺🇸',
  kanada: '🇨🇦',
  australien: '🇦🇺',
  neuseeland: '🇳🇿',
  irland: '🇮🇪',
}

const statusColors = {
  active: 'bg-green-100 text-green-800',
  upcoming: 'bg-blue-100 text-blue-800',
  completed: 'bg-gray-100 text-gray-600',
}

function getEmptyForm() {
  return {
    name: '',
    country: 'usa',
    city: '',
    school_name: '',
    host_family_name: '',
    start_date: '',
    end_date: '',
    bio: '',
    fun_facts: '',
    status: 'active',
    personality_preset: null,
  }
}

const filteredStudents = computed(() => store.students)

async function loadStudents() {
  const filters = {}
  if (filterCountry.value) filters.country = filterCountry.value
  if (filterStatus.value) filters.status = filterStatus.value
  if (searchQuery.value) filters.search = searchQuery.value
  await store.fetchStudents(filters)
}

function openCreateForm() {
  editingStudent.value = null
  formData.value = getEmptyForm()
  showForm.value = true
}

function openEditForm(student) {
  editingStudent.value = student
  formData.value = {
    name: student.name,
    country: student.country,
    city: student.city || '',
    school_name: student.school_name || '',
    host_family_name: student.host_family_name || '',
    start_date: student.start_date || '',
    end_date: student.end_date || '',
    bio: student.bio || '',
    fun_facts: student.fun_facts || '',
    status: student.status,
    personality_preset: student.personality_preset || null,
  }
  showForm.value = true
}

function cancelForm() {
  showForm.value = false
  editingStudent.value = null
  formData.value = getEmptyForm()
}

async function submitForm() {
  if (!formData.value.name.trim()) {
    toast.error('Bitte gib einen Namen ein.')
    return
  }

  const data = { ...formData.value }
  // Clean empty strings to null for optional fields
  if (!data.city) data.city = null
  if (!data.school_name) data.school_name = null
  if (!data.host_family_name) data.host_family_name = null
  if (!data.start_date) data.start_date = null
  if (!data.end_date) data.end_date = null
  if (!data.bio) data.bio = null
  if (!data.fun_facts) data.fun_facts = null
  if (!data.personality_preset) data.personality_preset = null

  if (editingStudent.value) {
    const result = await store.updateStudent(editingStudent.value.id, data)
    if (result) {
      toast.success('Student erfolgreich aktualisiert.')
      cancelForm()
      await loadStudents()
    }
  } else {
    const result = await store.createStudent(data)
    if (result) {
      toast.success('Student erfolgreich erstellt.')
      cancelForm()
      await loadStudents()
    }
  }
}

function confirmDelete(student) {
  studentToDelete.value = student
  showDeleteConfirm.value = true
}

async function executeDelete() {
  if (!studentToDelete.value) return
  const success = await store.deleteStudent(studentToDelete.value.id)
  if (success) {
    toast.success('Student erfolgreich geloescht.')
  }
  showDeleteConfirm.value = false
  studentToDelete.value = null
}

function cancelDelete() {
  showDeleteConfirm.value = false
  studentToDelete.value = null
}

function getCountryLabel(value) {
  const c = countries.find(c => c.value === value)
  return c ? c.label : value
}

function getStatusLabel(value) {
  const s = statuses.find(s => s.value === value)
  return s ? s.label : value
}

const toneIcons = {
  witzig: '😂',
  emotional: '🥺',
  motivierend: '💪',
  jugendlich: '✨',
  serioess: '📋',
  storytelling: '📖',
  'behind-the-scenes': '🎬',
  provokant: '⚡',
  wholesome: '🥰',
  informativ: '📊',
}

function getPersonalityBadge(student) {
  if (!student.personality_preset) return null
  try {
    const preset = typeof student.personality_preset === 'string'
      ? JSON.parse(student.personality_preset)
      : student.personality_preset
    if (!preset || !preset.tone) return null
    const icon = toneIcons[preset.tone] || '🎭'
    return `${icon} ${preset.tone} (H${preset.humor_level || 3}/5)`
  } catch {
    return null
  }
}

onMounted(() => {
  loadStudents()
  checkStoryArcs()
})
</script>

<template>
  <div class="p-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6" data-tour="students-header">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Studenten</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Verwalte Studentenprofile fuer Content-Serien
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
          class="bg-treff-blue text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
          @click="openCreateForm"
          data-tour="students-add-btn"
        >
          <span>+</span>
          <span>Student hinzufuegen</span>
        </button>
      </div>
    </div>

    <!-- Workflow Hint: Story-Arcs -->
    <div data-tour="students-story-arc-hint">
      <WorkflowHint
        hint-id="students-story-arcs"
        message="Tipp: Erstelle einen Story-Arc fuer deine Schueler, um mehrteilige Serien zu planen."
        link-text="Story-Arcs"
        link-to="/calendar/story-arcs"
        icon="📖"
        :show="showStoryArcHint"
      />
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 mb-6">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Suche nach Name, Stadt, Schule..."
        class="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm w-64 dark:bg-gray-800 dark:text-white"
        @input="loadStudents"
      />
      <select
        v-model="filterCountry"
        class="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm dark:bg-gray-800 dark:text-white"
        @change="loadStudents"
      >
        <option value="">Alle Laender</option>
        <option v-for="c in countries" :key="c.value" :value="c.value">
          {{ countryFlags[c.value] }} {{ c.label }}
        </option>
      </select>
      <select
        v-model="filterStatus"
        class="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm dark:bg-gray-800 dark:text-white"
        @change="loadStudents"
      >
        <option value="">Alle Status</option>
        <option v-for="s in statuses" :key="s.value" :value="s.value">
          {{ s.label }}
        </option>
      </select>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="text-center py-12 text-gray-500">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
      <p class="mt-2">Lade Studenten...</p>
    </div>

    <!-- Empty state -->
    <EmptyState
      v-else-if="filteredStudents.length === 0"
      svgIcon="academic-cap"
      title="Noch keine Schueler angelegt"
      description="Lege deinen ersten Austausch-Schueler an, um personalisierte Content-Serien und Story-Arcs zu erstellen."
      actionLabel="Schueler anlegen"
      @action="showForm = true"
    />

    <!-- Student list -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" data-tour="students-list">
      <div
        v-for="(student, idx) in filteredStudents"
        :key="student.id"
        class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:shadow-md transition-shadow cursor-pointer"
        :data-tour="idx === 0 ? 'students-personality' : undefined"
        @click="router.push(`/students/${student.id}`)"
      >
        <!-- Header row with profile image -->
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-3">
            <div class="w-14 h-14 rounded-full bg-treff-blue/10 flex items-center justify-center text-xl overflow-hidden flex-shrink-0">
              <img
                v-if="student.profile_image_url"
                :src="student.profile_image_url"
                :alt="student.name"
                class="w-full h-full object-cover"
              />
              <span v-else class="text-2xl">{{ countryFlags[student.country] || '🌍' }}</span>
            </div>
            <div>
              <h3 class="font-semibold text-gray-900 dark:text-white">{{ student.name }}</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ countryFlags[student.country] }} {{ getCountryLabel(student.country) }}
                <span v-if="student.city"> &middot; {{ student.city }}</span>
              </p>
            </div>
          </div>
          <span :class="['text-xs font-medium px-2 py-1 rounded-full whitespace-nowrap', statusColors[student.status]]">
            {{ getStatusLabel(student.status) }}
          </span>
        </div>

        <!-- Details -->
        <div class="space-y-1.5 text-sm text-gray-600 dark:text-gray-300 mb-4">
          <p v-if="student.school_name">
            <span class="text-gray-400">Schule:</span> {{ student.school_name }}
          </p>
          <p v-if="student.host_family_name">
            <span class="text-gray-400">Gastfamilie:</span> {{ student.host_family_name }}
          </p>
          <p v-if="student.start_date || student.end_date">
            <span class="text-gray-400">Zeitraum:</span>
            {{ student.start_date || '?' }} bis {{ student.end_date || '?' }}
          </p>
          <p v-if="student.bio" class="line-clamp-2">
            {{ student.bio }}
          </p>
          <p v-if="getPersonalityBadge(student)">
            <span class="text-gray-400">Persoenlichkeit:</span>
            <span class="inline-block ml-1 px-2 py-0.5 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 rounded-full text-xs font-medium">
              {{ getPersonalityBadge(student) }}
            </span>
          </p>
        </div>

        <!-- Actions -->
        <div class="flex gap-2 pt-3 border-t border-gray-100 dark:border-gray-700">
          <button
            class="flex-1 text-sm text-treff-blue hover:bg-treff-blue/10 rounded-lg py-1.5 transition-colors"
            @click.stop="router.push(`/students/${student.id}`)"
          >
            Details
          </button>
          <button
            class="flex-1 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg py-1.5 transition-colors"
            @click.stop="openEditForm(student)"
          >
            Bearbeiten
          </button>
          <button
            class="flex-1 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg py-1.5 transition-colors"
            @click.stop="confirmDelete(student)"
          >
            Loeschen
          </button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Form Modal -->
    <div
      v-if="showForm"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click.self="cancelForm"
    >
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">
          {{ editingStudent ? 'Student bearbeiten' : 'Neuer Student' }}
        </h2>

        <form @submit.prevent="submitForm" class="space-y-4">
          <!-- Name -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name *</label>
            <input
              v-model="formData.name"
              type="text"
              required
              placeholder="z.B. Jonathan Mueller"
              class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:text-white"
            />
          </div>

          <!-- Country + Status -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Land *</label>
              <select
                v-model="formData.country"
                required
                class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:text-white"
              >
                <option v-for="c in countries" :key="c.value" :value="c.value">
                  {{ countryFlags[c.value] }} {{ c.label }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
              <select
                v-model="formData.status"
                class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:text-white"
              >
                <option v-for="s in statuses" :key="s.value" :value="s.value">
                  {{ s.label }}
                </option>
              </select>
            </div>
          </div>

          <!-- City -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Stadt</label>
            <input
              v-model="formData.city"
              type="text"
              placeholder="z.B. Vancouver"
              class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:text-white"
            />
          </div>

          <!-- School -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Schule</label>
            <input
              v-model="formData.school_name"
              type="text"
              placeholder="z.B. Kitsilano Secondary"
              class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:text-white"
            />
          </div>

          <!-- Host Family -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Gastfamilie</label>
            <input
              v-model="formData.host_family_name"
              type="text"
              placeholder="z.B. Smith"
              class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:text-white"
            />
          </div>

          <!-- Date range -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Startdatum</label>
              <input
                v-model="formData.start_date"
                type="date"
                class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:text-white"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Enddatum</label>
              <input
                v-model="formData.end_date"
                type="date"
                class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>

          <!-- Bio -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Bio</label>
            <textarea
              v-model="formData.bio"
              rows="3"
              placeholder="Kurze Beschreibung des Studenten..."
              class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:text-white"
            ></textarea>
          </div>

          <!-- Fun Facts -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fun Facts</label>
            <textarea
              v-model="formData.fun_facts"
              rows="2"
              placeholder='z.B. ["Spielt Eishockey", "Liebt Poutine"]'
              class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:text-white"
            ></textarea>
          </div>

          <!-- Personality Preset -->
          <div class="border-t border-gray-200 dark:border-gray-600 pt-4">
            <PersonalityEditor v-model="formData.personality_preset" />
          </div>

          <!-- Buttons -->
          <div class="flex gap-3 pt-2">
            <button
              type="button"
              class="flex-1 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg py-2 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              @click="cancelForm"
            >
              Abbrechen
            </button>
            <button
              type="submit"
              class="flex-1 bg-treff-blue text-white rounded-lg py-2 hover:bg-blue-600 transition-colors"
              :disabled="store.loading"
            >
              {{ editingStudent ? 'Speichern' : 'Erstellen' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteConfirm"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click.self="cancelDelete"
    >
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm p-6">
        <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-2">Student loeschen?</h3>
        <p class="text-gray-500 dark:text-gray-400 text-sm mb-4">
          Moechtest du <strong>{{ studentToDelete?.name }}</strong> wirklich loeschen?
          Diese Aktion kann nicht rueckgaengig gemacht werden.
        </p>
        <div class="flex gap-3">
          <button
            class="flex-1 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg py-2 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="cancelDelete"
          >
            Abbrechen
          </button>
          <button
            class="flex-1 bg-red-500 text-white rounded-lg py-2 hover:bg-red-600 transition-colors"
            @click="executeDelete"
          >
            Loeschen
          </button>
        </div>
      </div>
    </div>

    <!-- Page-specific guided tour -->
    <TourSystem ref="tourRef" page-key="students" />
  </div>
</template>
