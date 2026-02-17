<script setup>
/**
 * StudentsView — Enhanced Students Hub
 *
 * Combines student management with Story Arc progress and Content Pipeline
 * indicators. Student cards use country-themed borders via useCountryTheme.
 * Quick "Create from Student" opens Smart Create with student context.
 *
 * @see Feature #294: C-08: Enhanced Students Hub
 */
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '@/stores/students'
import { useToast } from '@/composables/useToast'
import { getCountryTheme, resolveCountryKey, COUNTRY_THEMES } from '@/composables/useCountryTheme'
import PersonalityEditor from '@/components/students/PersonalityEditor.vue'
import WorkflowHint from '@/components/common/WorkflowHint.vue'
import api from '@/utils/api'
import TourSystem from '@/components/common/TourSystem.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const router = useRouter()
const store = useStudentStore()
const toast = useToast()

const tourRef = ref(null)

// ── Hub Statistics ──
const storyArcs = ref([])
const pipelineCounts = ref({}) // { studentId: count }
const hubStats = computed(() => {
  const total = store.students.length
  const active = store.students.filter(s => s.status === 'active').length
  const withArcs = new Set(storyArcs.value.map(a => a.student_id)).size
  const pendingContent = Object.values(pipelineCounts.value).reduce((s, c) => s + c, 0)
  return { total, active, withArcs, pendingContent }
})

// ── Data Loading ──
async function loadStoryArcs() {
  try {
    const { data } = await api.get('/api/story-arcs')
    storyArcs.value = Array.isArray(data) ? data : []
  } catch { storyArcs.value = [] }
}

async function loadPipelineCounts() {
  try {
    const { data } = await api.get('/api/pipeline/inbox', { params: { limit: 100 } })
    const counts = {}
    if (data && data.items) {
      for (const item of data.items) {
        if (item.student_id) {
          counts[item.student_id] = (counts[item.student_id] || 0) + 1
        }
      }
    }
    pipelineCounts.value = counts
  } catch { pipelineCounts.value = {} }
}

const showStoryArcHint = computed(() => {
  return store.students.length > 0 && storyArcs.value.length === 0
})

// ── Filters ──
const filterCountry = ref('')
const filterStatus = ref('')
const filterContentStatus = ref('') // 'new' = has pending pipeline items
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
  active: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  upcoming: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  completed: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
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

const filteredStudents = computed(() => {
  let result = store.students

  // Content status filter
  if (filterContentStatus.value === 'new') {
    result = result.filter(s => (pipelineCounts.value[s.id] || 0) > 0)
  }

  return result
})

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
    toast.success('Student erfolgreich gelöscht.')
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

// ── Country Theme Helpers ──
function getStudentTheme(student) {
  return getCountryTheme(student.country)
}

function getStudentBorderStyle(student) {
  const theme = getStudentTheme(student)
  return {
    borderColor: theme.primaryColor,
    borderLeftWidth: '4px',
  }
}

function getStudentAvatarStyle(student) {
  const theme = getStudentTheme(student)
  return {
    backgroundColor: theme.primaryColor + '15',
    color: theme.primaryColor,
  }
}

// ── Story Arc Helpers ──
function getStudentArcs(studentId) {
  return storyArcs.value.filter(a => a.student_id === studentId)
}

function getArcProgress(arc) {
  const planned = arc.planned_episodes || 0
  const published = arc.published_episodes || 0
  if (planned === 0) return 0
  return Math.min(100, Math.round((published / planned) * 100))
}

const arcStatusColors = {
  active: '#22C55E',
  paused: '#F59E0B',
  draft: '#6B7280',
  completed: '#3B82F6',
}

// ── Pipeline Helpers ──
function getStudentPipelineCount(studentId) {
  return pipelineCounts.value[studentId] || 0
}

// ── Personality Badge ──
const toneIcons = {
  witzig: 'face-smile',
  emotional: 'heart',
  motivierend: 'thumb-up',
  jugendlich: 'sparkles',
  serioess: 'clipboard-list',
  storytelling: 'book-open',
  'behind-the-scenes': 'film',
  provokant: 'bolt',
  wholesome: 'heart',
  informativ: 'chart-bar',
}

function getPersonalityBadge(student) {
  if (!student.personality_preset) return null
  try {
    const preset = typeof student.personality_preset === 'string'
      ? JSON.parse(student.personality_preset)
      : student.personality_preset
    if (!preset || !preset.tone) return null
    const iconName = toneIcons[preset.tone] || 'user'
    return { iconName, label: `${preset.tone} (H${preset.humor_level || 3}/5)` }
  } catch {
    return null
  }
}

// ── Quick Actions ──
function createFromStudent(student) {
  router.push({ path: '/create/smart', query: { student_id: student.id } })
}

function viewStudentDetail(student) {
  router.push(`/students/${student.id}`)
}

onMounted(() => {
  loadStudents()
  loadStoryArcs()
  loadPipelineCounts()
})
</script>

<template>
  <div class="min-h-screen" data-testid="students-hub">
    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4" data-tour="students-header">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Students Hub</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Schüler-Profile, Story-Arcs & Content-Pipeline auf einen Blick
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
          class="btn-primary flex items-center gap-2"
          @click="openCreateForm"
          data-tour="students-add-btn"
          data-testid="add-student-btn"
        >
          <span>+</span>
          <span>Student hinzufügen</span>
        </button>
      </div>
    </div>

    <!-- Hub Stats Bar -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6" data-testid="hub-stats">
      <div class="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
        <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ hubStats.total }}</div>
        <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Schüler gesamt</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
        <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ hubStats.active }}</div>
        <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Aktiv</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
        <div class="text-2xl font-bold text-primary-600 dark:text-primary-400">{{ hubStats.withArcs }}</div>
        <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Mit Story-Arcs</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
        <div class="text-2xl font-bold text-secondary-600 dark:text-secondary-400">{{ hubStats.pendingContent }}</div>
        <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Pipeline-Items</div>
      </div>
    </div>

    <!-- Workflow Hint: Story-Arcs -->
    <div data-tour="students-story-arc-hint">
      <WorkflowHint
        hint-id="students-story-arcs"
        message="Tipp: Erstelle einen Story-Arc für deine Schüler, um mehrteilige Serien zu planen."
        link-text="Story-Arcs"
        link-to="/calendar/story-arcs"
        icon="book-open"
        :show="showStoryArcHint"
      />
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 mb-6" data-testid="students-filters">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Suche nach Name, Stadt, Schule..."
        class="input-field w-64"
        @input="loadStudents"
        data-testid="search-input"
      />
      <select
        v-model="filterCountry"
        class="input-field w-auto"
        @change="loadStudents"
        data-testid="filter-country"
      >
        <option value="">Alle Länder</option>
        <option v-for="c in countries" :key="c.value" :value="c.value">
          {{ countryFlags[c.value] }} {{ c.label }}
        </option>
      </select>
      <select
        v-model="filterStatus"
        class="input-field w-auto"
        @change="loadStudents"
        data-testid="filter-status"
      >
        <option value="">Alle Status</option>
        <option v-for="s in statuses" :key="s.value" :value="s.value">
          {{ s.label }}
        </option>
      </select>
      <select
        v-model="filterContentStatus"
        class="input-field w-auto"
        data-testid="filter-content"
      >
        <option value="">Alle Inhalte</option>
        <option value="new">Neue Pipeline-Items</option>
      </select>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="text-center py-12 text-gray-500">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
      <p class="mt-2 text-sm">Lade Studenten...</p>
    </div>

    <!-- Empty state -->
    <EmptyState
      v-else-if="filteredStudents.length === 0"
      svgIcon="academic-cap"
      title="Noch keine Schüler angelegt"
      description="Lege deinen ersten Austausch-Schüler an, um personalisierte Content-Serien und Story-Arcs zu erstellen."
      actionLabel="Schüler anlegen"
      @action="showForm = true"
    />

    <!-- Student Grid with Country-Themed Cards -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" data-tour="students-list" data-testid="students-grid">
      <div
        v-for="(student, idx) in filteredStudents"
        :key="student.id"
        class="bg-white dark:bg-gray-800 rounded-xl shadow-card hover:shadow-card-hover border border-gray-200 dark:border-gray-700 overflow-hidden transition-all duration-200 cursor-pointer group"
        :style="getStudentBorderStyle(student)"
        :data-tour="idx === 0 ? 'students-personality' : undefined"
        :data-testid="'student-card-' + student.id"
        @click="viewStudentDetail(student)"
      >
        <!-- Country Gradient Top Bar -->
        <div class="h-1.5" :style="{ background: getStudentTheme(student).gradient }"></div>

        <div class="p-5">
          <!-- Header: Avatar + Name + Status -->
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-3">
              <div
                class="w-12 h-12 rounded-full flex items-center justify-center text-xl overflow-hidden flex-shrink-0 ring-2 ring-offset-1 dark:ring-offset-gray-800"
                :style="{ ...getStudentAvatarStyle(student), ringColor: getStudentTheme(student).primaryColor }"
              >
                <img
                  v-if="student.profile_image_url"
                  :src="student.profile_image_url"
                  :alt="student.name"
                  class="w-full h-full object-cover"
                />
                <span v-else class="text-lg font-bold" :style="{ color: getStudentTheme(student).primaryColor }">
                  {{ student.name.charAt(0).toUpperCase() }}
                </span>
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-white text-sm leading-tight">{{ student.name }}</h3>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {{ countryFlags[student.country] }} {{ getCountryLabel(student.country) }}
                  <span v-if="student.city"> &middot; {{ student.city }}</span>
                </p>
              </div>
            </div>
            <div class="flex flex-col items-end gap-1">
              <span :class="['text-[10px] font-medium px-2 py-0.5 rounded-full whitespace-nowrap', statusColors[student.status]]">
                {{ getStatusLabel(student.status) }}
              </span>
              <!-- Pipeline Badge -->
              <span
                v-if="getStudentPipelineCount(student.id) > 0"
                class="text-[10px] font-medium px-2 py-0.5 rounded-full bg-secondary-100 text-secondary-800 dark:bg-secondary-900/30 dark:text-secondary-400 whitespace-nowrap"
                data-testid="pipeline-badge"
              >
                {{ getStudentPipelineCount(student.id) }} neue Inhalte
              </span>
            </div>
          </div>

          <!-- Details -->
          <div class="space-y-1 text-xs text-gray-600 dark:text-gray-400 mb-3">
            <p v-if="student.school_name" class="truncate">
              <span class="text-gray-400">Schule:</span> {{ student.school_name }}
            </p>
            <p v-if="student.start_date || student.end_date" class="truncate">
              <span class="text-gray-400">Zeitraum:</span>
              {{ student.start_date || '?' }} bis {{ student.end_date || '?' }}
            </p>
            <p v-if="student.bio" class="line-clamp-1 text-gray-500 dark:text-gray-500">
              {{ student.bio }}
            </p>
          </div>

          <!-- Personality Badge -->
          <div v-if="getPersonalityBadge(student)" class="mb-3">
            <span class="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 rounded-full text-[10px] font-medium">
              <AppIcon :name="getPersonalityBadge(student).iconName" class="w-3 h-3 inline-block" />
              {{ getPersonalityBadge(student).label }}
            </span>
          </div>

          <!-- Story Arc Progress (Mini) -->
          <div v-if="getStudentArcs(student.id).length > 0" class="mb-3" data-testid="story-arc-section">
            <div class="text-[10px] font-medium text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wide">Story-Arcs</div>
            <div class="space-y-1.5">
              <div
                v-for="arc in getStudentArcs(student.id).slice(0, 2)"
                :key="arc.id"
                class="flex items-center gap-2"
              >
                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between mb-0.5">
                    <span class="text-[10px] text-gray-700 dark:text-gray-300 truncate">{{ arc.title }}</span>
                    <span class="text-[10px] text-gray-400 ml-1 flex-shrink-0">{{ getArcProgress(arc) }}%</span>
                  </div>
                  <div class="h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all duration-500"
                      :style="{ width: getArcProgress(arc) + '%', backgroundColor: arcStatusColors[arc.status] || '#6B7280' }"
                    ></div>
                  </div>
                </div>
              </div>
              <p v-if="getStudentArcs(student.id).length > 2" class="text-[10px] text-gray-400">
                +{{ getStudentArcs(student.id).length - 2 }} weitere
              </p>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex gap-1.5 pt-3 border-t border-gray-100 dark:border-gray-700">
            <button
              class="flex-1 text-xs font-medium py-1.5 rounded-lg transition-colors hover:bg-opacity-10"
              :style="{ color: getStudentTheme(student).primaryColor }"
              :class="'hover:bg-gray-100 dark:hover:bg-gray-700'"
              @click.stop="viewStudentDetail(student)"
              data-testid="btn-details"
            >
              Details
            </button>
            <button
              class="flex-1 text-xs font-medium text-primary-600 dark:text-primary-400 py-1.5 rounded-lg hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
              @click.stop="createFromStudent(student)"
              data-testid="btn-create-from-student"
            >
              Smart Create
            </button>
            <button
              class="text-xs font-medium text-gray-500 dark:text-gray-400 px-2 py-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              @click.stop="openEditForm(student)"
              data-testid="btn-edit"
            >
              &#9998;
            </button>
            <button
              class="text-xs font-medium text-red-500 px-2 py-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              @click.stop="confirmDelete(student)"
              data-testid="btn-delete"
            >
              &#128465;
            </button>
          </div>
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
            <label class="input-label">Name *</label>
            <input
              v-model="formData.name"
              type="text"
              required
              placeholder="z.B. Jonathan Müller"
              class="input-field w-full"
              data-testid="form-name"
            />
          </div>

          <!-- Country + Status -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="input-label">Land *</label>
              <select
                v-model="formData.country"
                required
                class="input-field w-full"
                data-testid="form-country"
              >
                <option v-for="c in countries" :key="c.value" :value="c.value">
                  {{ countryFlags[c.value] }} {{ c.label }}
                </option>
              </select>
            </div>
            <div>
              <label class="input-label">Status</label>
              <select
                v-model="formData.status"
                class="input-field w-full"
                data-testid="form-status"
              >
                <option v-for="s in statuses" :key="s.value" :value="s.value">
                  {{ s.label }}
                </option>
              </select>
            </div>
          </div>

          <!-- City -->
          <div>
            <label class="input-label">Stadt</label>
            <input
              v-model="formData.city"
              type="text"
              placeholder="z.B. Vancouver"
              class="input-field w-full"
            />
          </div>

          <!-- School -->
          <div>
            <label class="input-label">Schule</label>
            <input
              v-model="formData.school_name"
              type="text"
              placeholder="z.B. Kitsilano Secondary"
              class="input-field w-full"
            />
          </div>

          <!-- Host Family -->
          <div>
            <label class="input-label">Gastfamilie</label>
            <input
              v-model="formData.host_family_name"
              type="text"
              placeholder="z.B. Smith"
              class="input-field w-full"
            />
          </div>

          <!-- Date range -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="input-label">Startdatum</label>
              <input v-model="formData.start_date" type="date" class="input-field w-full" />
            </div>
            <div>
              <label class="input-label">Enddatum</label>
              <input v-model="formData.end_date" type="date" class="input-field w-full" />
            </div>
          </div>

          <!-- Bio -->
          <div>
            <label class="input-label">Bio</label>
            <textarea
              v-model="formData.bio"
              rows="3"
              placeholder="Kurze Beschreibung des Studenten..."
              class="input-field w-full"
            ></textarea>
          </div>

          <!-- Fun Facts -->
          <div>
            <label class="input-label">Fun Facts</label>
            <textarea
              v-model="formData.fun_facts"
              rows="2"
              placeholder='z.B. ["Spielt Eishockey", "Liebt Poutine"]'
              class="input-field w-full"
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
              class="btn-ghost flex-1"
              @click="cancelForm"
            >
              Abbrechen
            </button>
            <button
              type="submit"
              class="btn-primary flex-1"
              :disabled="store.loading"
              data-testid="form-submit"
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
        <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-2">Student löschen?</h3>
        <p class="text-gray-500 dark:text-gray-400 text-sm mb-4">
          Möchtest du <strong>{{ studentToDelete?.name }}</strong> wirklich löschen?
          Diese Aktion kann nicht rückgängig gemacht werden.
        </p>
        <div class="flex gap-3">
          <button
            class="btn-ghost flex-1"
            @click="cancelDelete"
          >
            Abbrechen
          </button>
          <button
            class="btn-danger flex-1"
            @click="executeDelete"
          >
            Löschen
          </button>
        </div>
      </div>
    </div>

    <!-- Page-specific guided tour -->
    <TourSystem ref="tourRef" page-key="students" />
  </div>
</template>
