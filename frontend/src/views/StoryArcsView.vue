<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import WorkflowHint from '@/components/common/WorkflowHint.vue'
import HelpTooltip from '@/components/common/HelpTooltip.vue'
import { tooltipTexts } from '@/utils/tooltipTexts'
import TourSystem from '@/components/common/TourSystem.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const router = useRouter()
const toast = useToast()

const arcs = ref([])
const loading = ref(true)
const tourRef = ref(null)

// Filters
const filterStatus = ref('')
const filterCountry = ref('')
const filterStudent = ref('')
const students = ref([])

const countries = [
  { value: 'usa', label: 'USA', flag: '\u{1F1FA}\u{1F1F8}' },
  { value: 'kanada', label: 'Kanada', flag: '\u{1F1E8}\u{1F1E6}' },
  { value: 'australien', label: 'Australien', flag: '\u{1F1E6}\u{1F1FA}' },
  { value: 'neuseeland', label: 'Neuseeland', flag: '\u{1F1F3}\u{1F1FF}' },
  { value: 'irland', label: 'Irland', flag: '\u{1F1EE}\u{1F1EA}' },
]

const countryFlags = {
  usa: '\u{1F1FA}\u{1F1F8}',
  kanada: '\u{1F1E8}\u{1F1E6}',
  australien: '\u{1F1E6}\u{1F1FA}',
  neuseeland: '\u{1F1F3}\u{1F1FF}',
  irland: '\u{1F1EE}\u{1F1EA}',
}

const statusConfig = {
  active: { label: 'Aktiv', color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300', dot: 'bg-green-500' },
  paused: { label: 'Pausiert', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300', dot: 'bg-yellow-500' },
  draft: { label: 'Entwurf', color: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300', dot: 'bg-gray-400' },
  completed: { label: 'Abgeschlossen', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300', dot: 'bg-blue-500' },
}

const filteredArcs = computed(() => {
  let result = arcs.value
  if (filterStudent.value) {
    result = result.filter(a => a.student_id === parseInt(filterStudent.value))
  }
  return result
})

// Stats
const stats = computed(() => {
  const all = arcs.value
  return {
    total: all.length,
    active: all.filter(a => a.status === 'active').length,
    paused: all.filter(a => a.status === 'paused').length,
    draft: all.filter(a => a.status === 'draft').length,
    completed: all.filter(a => a.status === 'completed').length,
  }
})

async function fetchArcs() {
  loading.value = true
  try {
    const params = { enriched: true }
    if (filterStatus.value) params.status = filterStatus.value
    if (filterCountry.value) params.country = filterCountry.value
    const { data } = await api.get('/api/story-arcs', { params })
    arcs.value = data
  } catch (err) {
    console.error('Failed to fetch story arcs:', err)
    toast.error('Fehler beim Laden der Story-Arcs.')
  } finally {
    loading.value = false
  }
}

async function fetchStudents() {
  try {
    const { data } = await api.get('/api/students')
    students.value = data
  } catch (err) {
    // Silently ignore - students filter just won't be populated
  }
}

function getProgress(arc) {
  const total = arc.total_episodes || arc.planned_episodes || 1
  const published = arc.published_episodes || 0
  return Math.round((published / total) * 100)
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: 'short', year: 'numeric' })
}

function openArcDetail(arc) {
  router.push(`/calendar/story-arcs/${arc.id}`)
}

function openWizard() {
  router.push('/calendar/story-arc-wizard')
}

// Workflow hint: suggest creating students when none exist
const showStudentsHint = computed(() => {
  return !loading.value && students.value.length === 0
})

onMounted(() => {
  fetchArcs()
  fetchStudents()
})
</script>

<template>
  <div class="p-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6" data-tour="arcs-header">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">Story-Arcs <HelpTooltip :text="tooltipTexts.storyArcs.arcOverview" /></h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Verwalte deine mehrteiligen Story-Serien
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
          @click="openWizard"
          data-tour="arcs-wizard-btn"
        >
          <span>+</span>
          <span>Neue Story-Serie</span>
        </button>
      </div>
    </div>

    <!-- Workflow Hint: No students -->
    <WorkflowHint
      hint-id="story-arcs-no-students"
      message="Lege zuerst Studentenprofile an, um personalisierte Story-Serien zu erstellen."
      link-text="Studenten verwalten"
      link-to="/students"
      icon="🎓"
      :show="showStudentsHint"
    />

    <!-- Stats cards -->
    <div class="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6" data-tour="arcs-stats">
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 text-center">
        <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats.total }}</p>
        <p class="text-xs text-gray-500 dark:text-gray-400">Gesamt</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 text-center">
        <p class="text-2xl font-bold text-green-600">{{ stats.active }}</p>
        <p class="text-xs text-gray-500 dark:text-gray-400">Aktiv</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 text-center">
        <p class="text-2xl font-bold text-yellow-600">{{ stats.paused }}</p>
        <p class="text-xs text-gray-500 dark:text-gray-400">Pausiert</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 text-center">
        <p class="text-2xl font-bold text-gray-500">{{ stats.draft }}</p>
        <p class="text-xs text-gray-500 dark:text-gray-400">Entwurf</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 text-center">
        <p class="text-2xl font-bold text-blue-600">{{ stats.completed }}</p>
        <p class="text-xs text-gray-500 dark:text-gray-400">Abgeschlossen</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 mb-6" data-tour="arcs-filters">
      <select
        v-model="filterStatus"
        class="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm dark:bg-gray-800 dark:text-white"
        @change="fetchArcs"
      >
        <option value="">Alle Status</option>
        <option value="active">Aktiv</option>
        <option value="paused">Pausiert</option>
        <option value="draft">Entwurf</option>
        <option value="completed">Abgeschlossen</option>
      </select>
      <select
        v-model="filterCountry"
        class="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm dark:bg-gray-800 dark:text-white"
        @change="fetchArcs"
      >
        <option value="">Alle Laender</option>
        <option v-for="c in countries" :key="c.value" :value="c.value">
          {{ c.flag }} {{ c.label }}
        </option>
      </select>
      <select
        v-model="filterStudent"
        class="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm dark:bg-gray-800 dark:text-white"
      >
        <option value="">Alle Studenten</option>
        <option v-for="s in students" :key="s.id" :value="s.id">
          {{ s.name }}
        </option>
      </select>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-gray-500">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
      <p class="mt-2">Lade Story-Arcs...</p>
    </div>

    <!-- Empty state -->
    <EmptyState
      v-else-if="filteredArcs.length === 0"
      icon="📖"
      title="Noch keine Story-Arcs erstellt"
      description="Erstelle deine erste Story-Serie mit dem Wizard. Lege vorher Schueler-Profile an, um personalisierte Serien zu erstellen."
      actionLabel="Story-Serie erstellen"
      @action="openWizard"
      secondaryLabel="Schueler anlegen"
      secondaryTo="/students"
    />

    <!-- Arc Cards Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" data-tour="arcs-list">
      <div
        v-for="arc in filteredArcs"
        :key="arc.id"
        class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-all duration-200 cursor-pointer group"
        @click="openArcDetail(arc)"
      >
        <!-- Cover Image or Placeholder -->
        <div class="h-36 bg-gradient-to-br from-treff-blue/20 to-treff-yellow/20 relative overflow-hidden">
          <img
            v-if="arc.cover_image_url"
            :src="arc.cover_image_url"
            :alt="arc.title"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex items-center justify-center">
            <span class="text-5xl opacity-40">📖</span>
          </div>
          <!-- Status Badge -->
          <div class="absolute top-3 right-3">
            <span
              :class="['text-xs font-semibold px-2.5 py-1 rounded-full', statusConfig[arc.status]?.color || 'bg-gray-100 text-gray-600']"
            >
              {{ statusConfig[arc.status]?.label || arc.status }}
            </span>
          </div>
          <!-- Country Flag -->
          <div v-if="arc.country" class="absolute top-3 left-3">
            <span class="text-xl bg-white/80 dark:bg-gray-900/80 rounded-full w-8 h-8 flex items-center justify-center shadow-sm">
              {{ countryFlags[arc.country] || '\u{1F30D}' }}
            </span>
          </div>
        </div>

        <!-- Card Body -->
        <div class="p-4">
          <!-- Title -->
          <h3 class="font-bold text-gray-900 dark:text-white text-lg leading-snug mb-1 group-hover:text-treff-blue transition-colors">
            {{ arc.title }}
          </h3>
          <p v-if="arc.subtitle" class="text-sm text-gray-500 dark:text-gray-400 mb-2 line-clamp-1">
            {{ arc.subtitle }}
          </p>

          <!-- Student Name -->
          <div v-if="arc.student_name" class="flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-300 mb-3">
            <span class="text-base">🎓</span>
            <span>{{ arc.student_name }}</span>
          </div>

          <!-- Progress Bar -->
          <div class="mb-3">
            <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
              <span>Fortschritt</span>
              <span class="font-medium">
                {{ arc.published_episodes || 0 }}/{{ arc.total_episodes || arc.planned_episodes || 0 }} Episoden
              </span>
            </div>
            <div class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="getProgress(arc) === 100 ? 'bg-green-500' : 'bg-treff-blue'"
                :style="{ width: `${getProgress(arc)}%` }"
              ></div>
            </div>
          </div>

          <!-- Meta Row -->
          <div class="flex items-center justify-between text-xs text-gray-400 dark:text-gray-500">
            <span v-if="arc.tone" class="capitalize">{{ arc.tone }}</span>
            <span>{{ formatDate(arc.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Students connection hint -->
    <div class="mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 flex items-start gap-3" data-tour="arcs-students-hint">
      <span class="text-2xl mt-0.5">🎓</span>
      <div>
        <p class="text-sm font-medium text-blue-800 dark:text-blue-200">Schueler-Profile als Protagonisten</p>
        <p class="text-xs text-blue-600 dark:text-blue-300 mt-1">
          Jede Story-Serie wird mit einem Schueler-Profil verknuepft. Die KI nutzt Name, Land, Schule und Persoenlichkeit fuer authentische Texte.
          <router-link to="/students" class="underline font-medium hover:text-blue-800 dark:hover:text-blue-100">Schueler verwalten &rarr;</router-link>
        </p>
      </div>
    </div>

    <!-- Page-specific guided tour -->
    <TourSystem ref="tourRef" page-key="story-arcs" />
  </div>
</template>
