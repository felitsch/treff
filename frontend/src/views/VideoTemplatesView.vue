<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import EmptyState from '@/components/common/EmptyState.vue'
import TourSystem from '@/components/common/TourSystem.vue'
import VideoWorkflowTour from '@/components/common/VideoWorkflowTour.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const toast = useToast()
const workflowTourRef = ref(null)

// State
const templates = ref([])
const videoAssets = ref([])
const loading = ref(false)
const activeTab = ref('all') // 'all', 'intro', 'outro'
const countryFilter = ref('')
const styleFilter = ref('')
const countries = ref({})
const styles = ref({})

// Template selection for applying
const selectedIntro = ref(null)
const selectedOutro = ref(null)
const selectedVideoAsset = ref(null)
const outputFormat = ref('9:16')
const applying = ref(false)
const applyProgress = ref(0)
const previewData = ref(null)
const resultData = ref(null)
const showResultModal = ref(false)

// Create template form
const showCreateForm = ref(false)
const createForm = ref({
  name: '',
  description: '',
  template_type: 'intro',
  country: '',
  duration_seconds: 3.0,
  style: 'default',
  primary_color: '#4C8BC2',
  secondary_color: '#FDD000',
  social_handle_instagram: '@treff_sprachreisen',
  social_handle_tiktok: '@treff_sprachreisen',
  website_url: 'www.treff-sprachreisen.de',
  cta_text: '',
})

// Computed
const filteredTemplates = computed(() => {
  let result = templates.value
  if (activeTab.value === 'intro') {
    result = result.filter(t => t.template_type === 'intro')
  } else if (activeTab.value === 'outro') {
    result = result.filter(t => t.template_type === 'outro')
  }
  if (countryFilter.value) {
    result = result.filter(t => t.country === countryFilter.value)
  }
  if (styleFilter.value) {
    result = result.filter(t => t.style === styleFilter.value)
  }
  return result
})

const introTemplates = computed(() => templates.value.filter(t => t.template_type === 'intro'))
const outroTemplates = computed(() => templates.value.filter(t => t.template_type === 'outro'))

const canApply = computed(() => {
  return selectedVideoAsset.value && (selectedIntro.value || selectedOutro.value)
})

const estimatedDuration = computed(() => {
  let dur = 0
  if (selectedIntro.value) {
    const intro = templates.value.find(t => t.id === selectedIntro.value)
    if (intro) dur += intro.duration_seconds
  }
  if (selectedVideoAsset.value) {
    const asset = videoAssets.value.find(a => a.id === selectedVideoAsset.value)
    if (asset && asset.duration_seconds) dur += asset.duration_seconds
  }
  if (selectedOutro.value) {
    const outro = templates.value.find(t => t.id === selectedOutro.value)
    if (outro) dur += outro.duration_seconds
  }
  // Subtract crossfade overlaps
  const segments = [selectedIntro.value, selectedVideoAsset.value, selectedOutro.value].filter(Boolean).length
  const overlaps = Math.max(0, segments - 1) * 0.3
  return Math.max(0, dur - overlaps)
})

// Methods
async function fetchTemplates() {
  loading.value = true
  try {
    const res = await api.get('/api/video-templates')
    templates.value = res.data.templates
    countries.value = res.data.countries
    styles.value = res.data.styles
  } catch (err) {
    toast.error('Fehler beim Laden der Templates')
  } finally {
    loading.value = false
  }
}

async function fetchVideoAssets() {
  try {
    const res = await api.get('/api/assets?category=video')
    videoAssets.value = (res.data.assets || res.data || []).filter(
      a => a.file_type && a.file_type.startsWith('video/')
    )
  } catch {
    // Non-critical
  }
}

async function createTemplate() {
  try {
    const data = { ...createForm.value }
    if (!data.country) delete data.country
    if (!data.cta_text) delete data.cta_text
    const res = await api.post('/api/video-templates', data)
    templates.value.push(res.data)
    toast.success(`Template "${res.data.name}" erstellt`)
    showCreateForm.value = false
    resetCreateForm()
  } catch (err) {
    toast.error('Fehler beim Erstellen: ' + (err.response?.data?.detail || err.message))
  }
}

async function deleteTemplate(id, name) {
  if (!confirm(`Template "${name}" wirklich löschen?`)) return
  try {
    await api.delete(`/api/video-templates/${id}`)
    templates.value = templates.value.filter(t => t.id !== id)
    toast.success(`Template "${name}" gelöscht`)
  } catch (err) {
    toast.error('Löschen fehlgeschlagen: ' + (err.response?.data?.detail || err.message))
  }
}

function resetCreateForm() {
  createForm.value = {
    name: '',
    description: '',
    template_type: 'intro',
    country: '',
    duration_seconds: 3.0,
    style: 'default',
    primary_color: '#4C8BC2',
    secondary_color: '#FDD000',
    social_handle_instagram: '@treff_sprachreisen',
    social_handle_tiktok: '@treff_sprachreisen',
    website_url: 'www.treff-sprachreisen.de',
    cta_text: '',
  }
}

function selectIntro(template) {
  selectedIntro.value = selectedIntro.value === template.id ? null : template.id
}

function selectOutro(template) {
  selectedOutro.value = selectedOutro.value === template.id ? null : template.id
}

async function applyTemplates() {
  if (!canApply.value) return
  applying.value = true
  applyProgress.value = 0
  resultData.value = null

  // Simulate progress
  const progressInterval = setInterval(() => {
    if (applyProgress.value < 90) {
      applyProgress.value += Math.random() * 15
    }
  }, 500)

  try {
    const payload = {
      video_asset_id: selectedVideoAsset.value,
      output_format: outputFormat.value,
      save_as_asset: true,
    }
    if (selectedIntro.value) payload.intro_template_id = selectedIntro.value
    if (selectedOutro.value) payload.outro_template_id = selectedOutro.value

    const res = await api.post('/api/video-templates/apply', payload)
    resultData.value = res.data
    applyProgress.value = 100
    showResultModal.value = true
    toast.success('Video mit Branding erfolgreich erstellt!')
  } catch (err) {
    toast.error('Fehler: ' + (err.response?.data?.detail || err.message))
  } finally {
    clearInterval(progressInterval)
    applying.value = false
  }
}

async function fetchPreview() {
  if (!canApply.value) {
    previewData.value = null
    return
  }
  try {
    const payload = {
      video_asset_id: selectedVideoAsset.value,
      output_format: outputFormat.value,
    }
    if (selectedIntro.value) payload.intro_template_id = selectedIntro.value
    if (selectedOutro.value) payload.outro_template_id = selectedOutro.value

    const res = await api.post('/api/video-templates/preview', payload)
    previewData.value = res.data
  } catch {
    previewData.value = null
  }
}

function getTemplateById(id) {
  return templates.value.find(t => t.id === id)
}

function formatDuration(sec) {
  if (!sec) return '0:00'
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  const mb = bytes / (1024 * 1024)
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${(bytes / 1024).toFixed(0)} KB`
}

onMounted(() => {
  fetchTemplates()
  fetchVideoAssets()
})
</script>

<template>
  <div class="p-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div data-tour="vt-header" class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Video-Branding Templates</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Intro- und Outro-Sequenzen mit TREFF-Branding für einheitliche Reels & TikToks
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="workflowTourRef?.startTour()"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[#4C8BC2] bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors"
          title="Video-Workflow-Tour starten"
        >
          <AppIcon name="film" class="w-3.5 h-3.5 inline-block" /> Workflow
        </button>
        <button
          data-tour="vt-create"
          class="px-4 py-2 bg-treff-blue text-white rounded-lg hover:bg-treff-blue/90 transition-colors"
          @click="showCreateForm = !showCreateForm"
        >
          {{ showCreateForm ? 'Abbrechen' : '+ Neues Template' }}
        </button>
      </div>
    </div>

    <!-- Create Form -->
    <div v-if="showCreateForm" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6">
      <h2 class="text-lg font-semibold mb-4">Neues Video-Template erstellen</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium mb-1">Name *</label>
          <input v-model="createForm.name" type="text" class="w-full border rounded-lg px-3 py-2 dark:bg-gray-700 dark:border-gray-600" placeholder="z.B. Mein Custom Intro" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Typ *</label>
          <select v-model="createForm.template_type" class="w-full border rounded-lg px-3 py-2 dark:bg-gray-700 dark:border-gray-600">
            <option value="intro">Intro</option>
            <option value="outro">Outro</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Land (optional)</label>
          <select v-model="createForm.country" class="w-full border rounded-lg px-3 py-2 dark:bg-gray-700 dark:border-gray-600">
            <option value="">Allgemein</option>
            <option v-for="(meta, key) in countries" :key="key" :value="key">
              {{ meta.flag }} {{ meta.label }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Stil</label>
          <select v-model="createForm.style" class="w-full border rounded-lg px-3 py-2 dark:bg-gray-700 dark:border-gray-600">
            <option v-for="(meta, key) in styles" :key="key" :value="key">
              {{ meta.icon }} {{ meta.label }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Dauer (Sekunden)</label>
          <input v-model.number="createForm.duration_seconds" type="number" min="1" max="10" step="0.5" class="w-full border rounded-lg px-3 py-2 dark:bg-gray-700 dark:border-gray-600" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">CTA-Text (nur Outro)</label>
          <input v-model="createForm.cta_text" type="text" class="w-full border rounded-lg px-3 py-2 dark:bg-gray-700 dark:border-gray-600" placeholder="z.B. Jetzt bewerben!" />
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-medium mb-1">Beschreibung</label>
          <textarea v-model="createForm.description" rows="2" class="w-full border rounded-lg px-3 py-2 dark:bg-gray-700 dark:border-gray-600" placeholder="Kurze Beschreibung des Templates..."></textarea>
        </div>
        <div class="flex items-center gap-3">
          <div>
            <label class="block text-sm font-medium mb-1">Primärfarbe</label>
            <input v-model="createForm.primary_color" type="color" class="w-10 h-10 border rounded cursor-pointer" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Sekundärfarbe</label>
            <input v-model="createForm.secondary_color" type="color" class="w-10 h-10 border rounded cursor-pointer" />
          </div>
        </div>
      </div>
      <div class="mt-4 flex justify-end">
        <button
          @click="createTemplate"
          :disabled="!createForm.name"
          class="px-6 py-2 bg-treff-blue text-white rounded-lg hover:bg-treff-blue/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Template erstellen
        </button>
      </div>
    </div>

    <!-- Main Layout: 2 columns -->
    <div data-tour="vt-workflow" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left: Template Library (2/3) -->
      <div class="lg:col-span-2">
        <!-- Tabs & Filters -->
        <div data-tour="vt-filters" class="flex flex-wrap items-center gap-3 mb-4">
          <div class="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            <button
              v-for="tab in [{ key: 'all', label: 'Alle' }, { key: 'intro', label: 'Intros' }, { key: 'outro', label: 'Outros' }]"
              :key="tab.key"
              @click="activeTab = tab.key"
              :class="[
                'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                activeTab === tab.key
                  ? 'bg-white dark:bg-gray-700 shadow-sm text-treff-blue'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
              ]"
            >
              {{ tab.label }}
            </button>
          </div>

          <select v-model="countryFilter" class="border rounded-lg px-2 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700">
            <option value="">Alle Länder</option>
            <option v-for="(meta, key) in countries" :key="key" :value="key">
              {{ meta.flag }} {{ meta.label }}
            </option>
          </select>

          <select v-model="styleFilter" class="border rounded-lg px-2 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700">
            <option value="">Alle Stile</option>
            <option v-for="(meta, key) in styles" :key="key" :value="key">
              {{ meta.icon }} {{ meta.label }}
            </option>
          </select>

          <span class="text-sm text-gray-500">{{ filteredTemplates.length }} Templates</span>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="text-center py-12 text-gray-500">
          Lade Templates...
        </div>

        <!-- Template Grid -->
        <div v-else data-tour="vt-grid" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div
            v-for="tmpl in filteredTemplates"
            :key="tmpl.id"
            :class="[
              'relative rounded-xl border-2 p-4 cursor-pointer transition-all hover:shadow-md',
              (selectedIntro === tmpl.id || selectedOutro === tmpl.id)
                ? 'border-treff-blue bg-treff-blue/5 shadow-md'
                : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800',
            ]"
            @click="tmpl.template_type === 'intro' ? selectIntro(tmpl) : selectOutro(tmpl)"
          >
            <!-- Selected indicator -->
            <div
              v-if="selectedIntro === tmpl.id || selectedOutro === tmpl.id"
              class="absolute top-2 right-2 w-6 h-6 bg-treff-blue text-white rounded-full flex items-center justify-center text-xs font-bold"
            >
              &#10003;
            </div>

            <!-- Header -->
            <div class="flex items-start gap-3 mb-3">
              <!-- Color preview with country-specific gradient -->
              <div
                class="w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold text-lg flex-shrink-0 shadow-inner"
                :style="{ background: tmpl.background_gradient || `linear-gradient(135deg, ${tmpl.primary_color}, ${tmpl.secondary_color})` }"
              >
                {{ tmpl.country_flag || (tmpl.template_type === 'intro' ? 'IN' : 'OUT') }}
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="font-semibold text-gray-900 dark:text-white truncate">{{ tmpl.name }}</h3>
                <div class="flex items-center gap-2 mt-0.5">
                  <span :class="[
                    'text-xs px-2 py-0.5 rounded-full font-medium',
                    tmpl.template_type === 'intro'
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                      : 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
                  ]">
                    {{ tmpl.template_type === 'intro' ? 'Intro' : 'Outro' }}
                  </span>
                  <span class="text-xs text-gray-500">{{ tmpl.style_icon }} {{ tmpl.style_label }}</span>
                  <span v-if="tmpl.country_flag" class="text-xs">{{ tmpl.country_flag }} {{ tmpl.country_label }}</span>
                  <span v-if="tmpl.motif" class="text-xs text-amber-500 font-medium capitalize">{{ tmpl.motif.replace('_', ' ') }}</span>
                  <span class="text-xs text-gray-400">{{ tmpl.duration_seconds }}s</span>
                </div>
              </div>
            </div>

            <!-- Description -->
            <p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-3">
              {{ tmpl.description }}
            </p>

            <!-- CTA text if outro -->
            <div v-if="tmpl.cta_text" class="text-xs text-treff-yellow font-medium bg-gray-900 dark:bg-gray-950 rounded px-2 py-1 mb-2 inline-block">
              {{ tmpl.cta_text }}
            </div>

            <!-- Footer -->
            <div class="flex items-center justify-between text-xs text-gray-400 mt-2">
              <span v-if="tmpl.is_default" class="text-blue-500 font-medium">System</span>
              <span v-else class="text-amber-500 font-medium">Custom</span>
              <button
                v-if="!tmpl.is_default"
                @click.stop="deleteTemplate(tmpl.id, tmpl.name)"
                class="text-red-400 hover:text-red-600 transition-colors"
              >
                Löschen
              </button>
            </div>
          </div>
        </div>

        <EmptyState
          v-if="!loading && filteredTemplates.length === 0"
          svgIcon="magnifying-glass"
          title="Keine Video-Templates gefunden"
          description="Passe die Filter an oder erstelle ein neues Video-Branding-Template."
          actionLabel="Filter zurücksetzen"
          @action="selectedCategory = ''"
          :compact="true"
        />
      </div>

      <!-- Right: Apply Panel (1/3) -->
      <div class="lg:col-span-1">
        <div data-tour="vt-apply" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5 sticky top-6">
          <h2 class="text-lg font-semibold mb-4">Branding anwenden</h2>

          <!-- Video Asset Selector -->
          <div class="mb-4">
            <label class="block text-sm font-medium mb-1">Video auswählen *</label>
            <select
              v-model="selectedVideoAsset"
              class="w-full border rounded-lg px-3 py-2 dark:bg-gray-700 dark:border-gray-600 text-sm"
              @change="fetchPreview"
            >
              <option :value="null">-- Video wählen --</option>
              <option v-for="asset in videoAssets" :key="asset.id" :value="asset.id">
                {{ asset.original_filename || asset.filename }}
                {{ asset.duration_seconds ? `(${formatDuration(asset.duration_seconds)})` : '' }}
              </option>
            </select>
            <p v-if="videoAssets.length === 0" class="text-xs text-amber-500 mt-1">
              Keine Videos vorhanden.
              <router-link to="/library/assets" class="text-blue-500 hover:underline">Jetzt in Assets hochladen</router-link>
            </p>
          </div>

          <!-- Output Format -->
          <div class="mb-4">
            <label class="block text-sm font-medium mb-1">Ausgabeformat</label>
            <div class="flex gap-2">
              <button
                v-for="fmt in ['9:16', '1:1', '16:9']"
                :key="fmt"
                @click="outputFormat = fmt; fetchPreview()"
                :class="[
                  'flex-1 py-2 rounded-lg text-sm font-medium border transition-colors',
                  outputFormat === fmt
                    ? 'border-treff-blue bg-treff-blue/10 text-treff-blue'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                ]"
              >
                {{ fmt === '9:16' ? 'Reel' : fmt === '1:1' ? 'Feed' : 'Quer' }}
              </button>
            </div>
          </div>

          <!-- Selected Templates Summary -->
          <div class="space-y-3 mb-4">
            <!-- Intro -->
            <div class="flex items-center gap-2 p-2 rounded-lg" :class="selectedIntro ? 'bg-green-50 dark:bg-green-900/20' : 'bg-gray-50 dark:bg-gray-700/50'">
              <span class="text-lg">{{ selectedIntro ? '&#9654;' : '&#9654;' }}</span>
              <div class="flex-1 min-w-0">
                <span class="text-xs font-medium text-gray-500 uppercase">Intro</span>
                <p v-if="selectedIntro" class="text-sm font-medium truncate">
                  {{ getTemplateById(selectedIntro)?.name }}
                  <span class="text-xs text-gray-400">({{ getTemplateById(selectedIntro)?.duration_seconds }}s)</span>
                </p>
                <p v-else class="text-xs text-gray-400">Klicke auf ein Intro-Template</p>
              </div>
              <button v-if="selectedIntro" @click="selectedIntro = null" class="text-gray-400 hover:text-red-500 text-sm">&#10005;</button>
            </div>

            <!-- Content -->
            <div class="flex items-center gap-2 p-2 rounded-lg bg-blue-50 dark:bg-blue-900/20">
              <span class="text-lg">&#127909;</span>
              <div class="flex-1 min-w-0">
                <span class="text-xs font-medium text-gray-500 uppercase">Content</span>
                <p v-if="selectedVideoAsset" class="text-sm font-medium truncate">
                  {{ videoAssets.find(a => a.id === selectedVideoAsset)?.original_filename || 'Video' }}
                </p>
                <p v-else class="text-xs text-gray-400">Wähle ein Video oben</p>
              </div>
            </div>

            <!-- Outro -->
            <div class="flex items-center gap-2 p-2 rounded-lg" :class="selectedOutro ? 'bg-purple-50 dark:bg-purple-900/20' : 'bg-gray-50 dark:bg-gray-700/50'">
              <span class="text-lg">&#9632;</span>
              <div class="flex-1 min-w-0">
                <span class="text-xs font-medium text-gray-500 uppercase">Outro</span>
                <p v-if="selectedOutro" class="text-sm font-medium truncate">
                  {{ getTemplateById(selectedOutro)?.name }}
                  <span class="text-xs text-gray-400">({{ getTemplateById(selectedOutro)?.duration_seconds }}s)</span>
                </p>
                <p v-else class="text-xs text-gray-400">Klicke auf ein Outro-Template</p>
              </div>
              <button v-if="selectedOutro" @click="selectedOutro = null" class="text-gray-400 hover:text-red-500 text-sm">&#10005;</button>
            </div>
          </div>

          <!-- Estimated Duration -->
          <div v-if="canApply" class="text-sm text-gray-600 dark:text-gray-400 mb-4 p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div class="flex justify-between">
              <span>Geschätzte Dauer:</span>
              <span class="font-medium">{{ formatDuration(estimatedDuration) }}</span>
            </div>
            <div class="flex justify-between mt-1">
              <span>Format:</span>
              <span class="font-medium">{{ outputFormat }}</span>
            </div>
          </div>

          <!-- Progress Bar -->
          <div v-if="applying" class="mb-4">
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                class="bg-treff-blue h-2 rounded-full transition-all duration-300"
                :style="{ width: Math.min(applyProgress, 100) + '%' }"
              ></div>
            </div>
            <p class="text-xs text-gray-500 mt-1 text-center">
              Video wird generiert... {{ Math.round(applyProgress) }}%
            </p>
          </div>

          <!-- Apply Button -->
          <button
            @click="applyTemplates"
            :disabled="!canApply || applying"
            class="w-full py-3 bg-treff-blue text-white rounded-lg font-medium hover:bg-treff-blue/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {{ applying ? 'Generiere...' : 'Branding anwenden' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Result Modal -->
    <div v-if="showResultModal && resultData" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="showResultModal = false">
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl max-w-lg w-full p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold">Video mit Branding erstellt!</h3>
          <button @click="showResultModal = false" class="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
        </div>

        <!-- Video Preview -->
        <div class="bg-black rounded-lg overflow-hidden mb-4" style="max-height: 400px;">
          <video
            :src="resultData.file_path"
            controls
            class="w-full"
            style="max-height: 400px;"
          ></video>
        </div>

        <!-- Metadata -->
        <div class="grid grid-cols-2 gap-3 text-sm mb-4">
          <div class="flex justify-between">
            <span class="text-gray-500">Dauer:</span>
            <span class="font-medium">{{ formatDuration(resultData.duration_seconds) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">Größe:</span>
            <span class="font-medium">{{ formatFileSize(resultData.file_size) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">Auflösung:</span>
            <span class="font-medium">{{ resultData.width }}x{{ resultData.height }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">Format:</span>
            <span class="font-medium">{{ resultData.output_format }}</span>
          </div>
        </div>

        <!-- Templates used -->
        <div v-if="resultData.intro_template" class="text-xs text-gray-500 mb-1">
          Intro: {{ resultData.intro_template.name }}
        </div>
        <div v-if="resultData.outro_template" class="text-xs text-gray-500 mb-3">
          Outro: {{ resultData.outro_template.name }}
        </div>

        <div class="flex gap-3">
          <a
            :href="resultData.file_path"
            download
            class="flex-1 py-2 text-center bg-treff-blue text-white rounded-lg hover:bg-treff-blue/90 transition-colors"
          >
            Herunterladen
          </a>
          <button
            @click="showResultModal = false"
            class="flex-1 py-2 text-center border border-gray-300 rounded-lg hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700 transition-colors"
          >
            Schließen
          </button>
        </div>
      </div>
    </div>

    <!-- Tour System -->
    <VideoWorkflowTour ref="workflowTourRef" />
    <TourSystem page-key="video-templates" />
  </div>
</template>
