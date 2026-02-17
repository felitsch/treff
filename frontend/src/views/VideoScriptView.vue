<script setup>
/**
 * VideoScriptView - Video-Script-Generator für Reels und TikTok
 *
 * Step-Flow: Thema -> Plattform/Dauer -> Hook-Formel -> Script generieren -> Bearbeiten -> Speichern
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import AppIcon from '@/components/icons/AppIcon.vue'
import AudioSuggestionPanel from '@/components/video/AudioSuggestionPanel.vue'
import VoiceoverEditor from '@/components/video/VoiceoverEditor.vue'

const router = useRouter()
const toast = useToast()

// Step flow
const currentStep = ref(1)
const totalSteps = 5

// Step 1: Topic & Category
const topic = ref('')
const country = ref('')
const category = ref('')
const buyerJourneyStage = ref('')
const tone = ref('jugendlich')

// Step 2: Platform & Duration
const platform = ref('reels')
const duration = ref(30)
const timingTemplates = ref({})

// Step 3: Hook Formula
const hookFormulas = ref([])
const selectedHookId = ref('')
const hookPerformanceMap = ref({}) // hook_id -> { usage_count, avg_engagement_rate }

// Step 4: Generated script
const generatedScript = ref(null)
const isGenerating = ref(false)

// Step 5: History
const scriptHistory = ref([])
const isLoadingHistory = ref(false)

// Editing
const editingSceneIndex = ref(-1)
const editForm = ref({})

// Audio sidebar
const showAudioSidebar = ref(false)

// Voiceover tab (Step 4)
const scriptTab = ref('scenes')  // 'scenes' | 'voiceover'
const voiceoverEditorRef = ref(null)

/** Generate voiceover for current script context */
async function generateVoiceover() {
  if (!voiceoverEditorRef.value) return
  await voiceoverEditorRef.value.generate({
    topic: topic.value,
    duration_seconds: duration.value,
    platform: platform.value,
    tone: tone.value,
    hook_formula_id: selectedHookId.value,
    country: country.value,
  })
}

/** Computed platform filter for AudioSuggestionPanel */
const audioPlatformFilter = computed(() => {
  const map = { reels: 'instagram', tiktok: 'tiktok', story: 'instagram' }
  return map[platform.value] || null
})

/** Computed content pillar filter for AudioSuggestionPanel */
const audioContentPillarFilter = computed(() => category.value || null)

/** Handle audio suggestion selection - apply to current editing scene or show info */
function onAudioSelect(suggestion) {
  const moodLabel = suggestion.mood
  const musicNote = `${moodLabel}: '${suggestion.title}'${suggestion.artist ? ` (${suggestion.artist})` : ''}`

  if (editingSceneIndex.value >= 0) {
    // Apply to scene being edited
    editForm.value.music_note = musicNote
    toast.success(`Audio '${suggestion.title}' zur Szene hinzugefügt`)
  } else if (generatedScript.value && generatedScript.value.scenes.length > 0) {
    // Apply to all scenes as default
    generatedScript.value.scenes.forEach(scene => {
      if (!scene.music_note || scene.music_note.trim() === '') {
        scene.music_note = musicNote
      }
    })
    toast.success(`Audio '${suggestion.title}' als Musik-Empfehlung gesetzt`)
  } else {
    toast.info(`Audio-Empfehlung: ${suggestion.title} (${suggestion.mood})`)
  }
}

const countries = [
  { value: '', label: 'Automatisch (gewichtet)' },
  { value: 'usa', label: 'USA' },
  { value: 'canada', label: 'Kanada' },
  { value: 'australia', label: 'Australien' },
  { value: 'newzealand', label: 'Neuseeland' },
  { value: 'ireland', label: 'Irland' },
]

const categories = [
  { value: '', label: 'Keine Kategorie' },
  { value: 'laender_spotlight', label: 'Länder-Spotlight' },
  { value: 'erfahrungsberichte', label: 'Erfahrungsberichte' },
  { value: 'tipps_tricks', label: 'Tipps & Tricks' },
  { value: 'fristen_cta', label: 'Fristen & CTA' },
  { value: 'faq', label: 'FAQ' },
]

const tones = [
  { value: 'jugendlich', label: 'Jugendlich' },
  { value: 'emotional', label: 'Emotional' },
  { value: 'witzig', label: 'Witzig' },
  { value: 'motivierend', label: 'Motivierend' },
  { value: 'informativ', label: 'Informativ' },
  { value: 'storytelling', label: 'Storytelling' },
  { value: 'provokant', label: 'Provokant' },
]

const buyerStages = [
  { value: '', label: 'Keine Vorgabe' },
  { value: 'awareness', label: 'Awareness (Fernweh wecken)' },
  { value: 'consideration', label: 'Consideration (Vergleichen)' },
  { value: 'decision', label: 'Decision (Bewerben)' },
]

const platforms = [
  { value: 'reels', label: 'Instagram Reels', icon: 'camera' },
  { value: 'tiktok', label: 'TikTok', icon: 'musical-note' },
  { value: 'story', label: 'Instagram Story', icon: 'device-mobile' },
]

const durations = [
  { value: 15, label: '15 Sekunden', desc: 'Schnell & knackig' },
  { value: 30, label: '30 Sekunden', desc: 'Standard Reel' },
  { value: 60, label: '60 Sekunden', desc: 'Ausführlich' },
  { value: 90, label: '90 Sekunden', desc: 'TikTok Storytelling' },
]

const canGenerate = computed(() => topic.value.trim().length > 3)

const sceneTypeLabels = {
  hook: 'Hook',
  problem: 'Problem/Frage',
  intro: 'Intro',
  content: 'Hauptinhalt',
  content_2: 'Hauptinhalt 2',
  content_3: 'Hauptinhalt 3',
  proof: 'Beweis/Beispiel',
  transition: 'Übergang',
  cta: 'Call-to-Action',
}

const sceneTypeColors = {
  hook: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  problem: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
  intro: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  content: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  content_2: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  content_3: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  proof: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  transition: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
  cta: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
}

// Load initial data
onMounted(async () => {
  await loadTimingTemplates()
  await loadHookFormulas()
  await loadHistory()
})

async function loadTimingTemplates() {
  try {
    const { data } = await api.get('/api/video-scripts/timing-templates')
    timingTemplates.value = data.templates || {}
  } catch (e) {
    console.error('Failed to load timing templates:', e)
  }
}

async function loadHookFormulas() {
  try {
    const platMap = { reels: 'instagram_reels', tiktok: 'tiktok', story: 'instagram_stories' }
    const [formulaRes, perfRes] = await Promise.allSettled([
      api.get('/api/video-scripts/hook-formulas', {
        params: { platform: platMap[platform.value] || 'instagram_reels' },
      }),
      api.get('/api/analytics/hook-performance'),
    ])
    if (formulaRes.status === 'fulfilled') {
      hookFormulas.value = formulaRes.value.data.formulas || []
    }
    if (perfRes.status === 'fulfilled') {
      const perfData = perfRes.value.data
      const map = {}
      for (const h of (perfData.hook_stats || [])) {
        map[h.id] = { usage_count: h.usage_count, avg_engagement_rate: h.avg_engagement_rate }
      }
      hookPerformanceMap.value = map
    }
  } catch (e) {
    console.error('Failed to load hook formulas:', e)
  }
}

async function loadHistory() {
  isLoadingHistory.value = true
  try {
    const { data } = await api.get('/api/video-scripts', { params: { limit: 10 } })
    scriptHistory.value = data.scripts || []
  } catch (e) {
    console.error('Failed to load script history:', e)
  } finally {
    isLoadingHistory.value = false
  }
}

async function generateScript() {
  if (!canGenerate.value) return
  isGenerating.value = true

  try {
    const payload = {
      topic: topic.value,
      platform: platform.value,
      duration: duration.value,
      tone: tone.value,
    }
    if (selectedHookId.value) payload.hook_formula_id = selectedHookId.value
    if (country.value) payload.country = country.value
    if (category.value) payload.category = category.value
    if (buyerJourneyStage.value) payload.buyer_journey_stage = buyerJourneyStage.value

    const { data } = await api.post('/api/video-scripts/generate', payload)
    generatedScript.value = data
    currentStep.value = 4
    toast.success('Video-Script erfolgreich generiert!')
    await loadHistory()
  } catch (e) {
    console.error('Script generation failed:', e)
    toast.error('Script-Generierung fehlgeschlagen. Bitte versuche es erneut.')
  } finally {
    isGenerating.value = false
  }
}

function startEditScene(index) {
  editingSceneIndex.value = index
  editForm.value = { ...generatedScript.value.scenes[index] }
}

function saveSceneEdit() {
  if (editingSceneIndex.value >= 0 && generatedScript.value) {
    generatedScript.value.scenes[editingSceneIndex.value] = { ...editForm.value }
    editingSceneIndex.value = -1
    toast.success('Szene aktualisiert')
  }
}

function cancelSceneEdit() {
  editingSceneIndex.value = -1
}

function removeScene(index) {
  if (generatedScript.value && generatedScript.value.scenes.length > 1) {
    generatedScript.value.scenes.splice(index, 1)
    // Renumber scenes
    generatedScript.value.scenes.forEach((s, i) => {
      s.scene_number = i + 1
    })
    toast.success('Szene entfernt')
  }
}

async function saveScript() {
  if (!generatedScript.value) return
  try {
    await api.put(`/api/video-scripts/${generatedScript.value.id}`, {
      title: generatedScript.value.title,
      scenes: generatedScript.value.scenes,
      voiceover_full: generatedScript.value.scenes.map(s => s.voiceover_text).join(' '),
    })
    toast.success('Script gespeichert!')
    await loadHistory()
  } catch (e) {
    toast.error('Speichern fehlgeschlagen')
  }
}

function copyVoiceover() {
  if (!generatedScript.value) return
  const text = generatedScript.value.scenes.map(s => s.voiceover_text).join('\n\n')
  navigator.clipboard.writeText(text).then(() => {
    toast.success('Voiceover-Text kopiert!')
  }).catch(() => {
    toast.error('Kopieren fehlgeschlagen')
  })
}

async function deleteScript(id) {
  try {
    await api.delete(`/api/video-scripts/${id}`)
    scriptHistory.value = scriptHistory.value.filter(s => s.id !== id)
    if (generatedScript.value && generatedScript.value.id === id) {
      generatedScript.value = null
      currentStep.value = 1
    }
    toast.success('Script gelöscht')
  } catch (e) {
    toast.error('Löschen fehlgeschlagen')
  }
}

function loadScript(script) {
  generatedScript.value = { ...script, scenes: [...script.scenes] }
  currentStep.value = 4
}

function resetWizard() {
  currentStep.value = 1
  generatedScript.value = null
  topic.value = ''
  selectedHookId.value = ''
  scriptTab.value = 'scenes'
}

function nextStep() {
  if (currentStep.value < totalSteps) {
    if (currentStep.value === 3) {
      generateScript()
    } else {
      currentStep.value++
    }
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return mins > 0 ? `${mins}:${String(secs).padStart(2, '0')}` : `0:${String(secs).padStart(2, '0')}`
}
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        Video-Script-Generator
      </h1>
      <p class="text-gray-600 dark:text-gray-400 mt-1">
        Erstelle Szene-für-Szene Skripte für Instagram Reels und TikTok
      </p>
    </div>

    <!-- Step Indicator -->
    <div class="mb-8">
      <div class="flex items-center justify-between">
        <div v-for="step in totalSteps" :key="step" class="flex items-center flex-1">
          <div
            :class="[
              'w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors',
              step === currentStep ? 'bg-blue-600 text-white' :
              step < currentStep ? 'bg-green-500 text-white' :
              'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
            ]"
          >
            <span v-if="step < currentStep">&#10003;</span>
            <span v-else>{{ step }}</span>
          </div>
          <div v-if="step < totalSteps" :class="['flex-1 h-0.5 mx-2', step < currentStep ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700']" />
        </div>
      </div>
      <div class="flex justify-between mt-2 text-xs text-gray-500 dark:text-gray-400">
        <span>Thema</span>
        <span>Plattform</span>
        <span>Hook</span>
        <span>Script</span>
        <span>Verlauf</span>
      </div>
    </div>

    <!-- Step 1: Topic -->
    <div v-if="currentStep === 1" class="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Schritt 1: Thema & Kontext
      </h2>

      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Video-Thema *
          </label>
          <input
            v-model="topic"
            type="text"
            class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="z.B. Mein erster Schultag in den USA"
          />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Land</label>
            <select v-model="country" class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option v-for="c in countries" :key="c.value" :value="c.value">{{ c.label }}</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Kategorie</label>
            <select v-model="category" class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option v-for="c in categories" :key="c.value" :value="c.value">{{ c.label }}</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tonalität</label>
            <select v-model="tone" class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option v-for="t in tones" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Buyer Journey</label>
            <select v-model="buyerJourneyStage" class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option v-for="s in buyerStages" :key="s.value" :value="s.value">{{ s.label }}</option>
            </select>
          </div>
        </div>
      </div>

      <div class="mt-6 flex justify-end">
        <button
          @click="nextStep"
          :disabled="!canGenerate"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Weiter
        </button>
      </div>
    </div>

    <!-- Step 2: Platform & Duration -->
    <div v-if="currentStep === 2" class="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Schritt 2: Plattform & Dauer
      </h2>

      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Plattform</label>
        <div class="grid grid-cols-3 gap-3">
          <button
            v-for="p in platforms"
            :key="p.value"
            @click="platform = p.value; loadHookFormulas()"
            :class="[
              'p-4 rounded-lg border-2 text-center transition-colors',
              platform === p.value
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
            ]"
          >
            <AppIcon :name="p.icon" class="w-6 h-6 mx-auto mb-1" />
            <span class="text-sm font-medium text-gray-900 dark:text-white">{{ p.label }}</span>
          </button>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Video-Dauer</label>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button
            v-for="d in durations"
            :key="d.value"
            @click="duration = d.value"
            :class="[
              'p-4 rounded-lg border-2 text-center transition-colors',
              duration === d.value
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
            ]"
          >
            <span class="text-lg font-bold text-gray-900 dark:text-white block">{{ d.label }}</span>
            <span class="text-xs text-gray-500 dark:text-gray-400">{{ d.desc }}</span>
            <span v-if="timingTemplates[String(d.value)]" class="text-xs text-blue-600 dark:text-blue-400 block mt-1">
              {{ timingTemplates[String(d.value)].scene_count }} Szenen
            </span>
          </button>
        </div>
      </div>

      <div class="mt-6 flex justify-between">
        <button @click="prevStep" class="px-6 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
          Zurück
        </button>
        <button @click="nextStep" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          Weiter
        </button>
      </div>
    </div>

    <!-- Step 3: Hook Formula -->
    <div v-if="currentStep === 3" class="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Schritt 3: Hook-Formel wählen
      </h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
        Die Hook bestimmt die ersten Sekunden deines Videos. Höhere Effektivität = bessere Performance.
      </p>

      <div class="space-y-3 mb-4">
        <!-- Auto option -->
        <button
          @click="selectedHookId = ''"
          :class="[
            'w-full p-4 rounded-lg border-2 text-left transition-colors',
            !selectedHookId
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
              : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
          ]"
        >
          <div class="flex items-center justify-between">
            <div>
              <span class="font-medium text-gray-900 dark:text-white">Automatisch (gewichtet)</span>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">KI wählt die beste Hook basierend auf Effektivität</p>
            </div>
            <span class="text-sm text-blue-600 dark:text-blue-400 font-bold">AUTO</span>
          </div>
        </button>

        <!-- Hook formulas -->
        <button
          v-for="hook in hookFormulas"
          :key="hook.id"
          @click="selectedHookId = hook.id"
          :class="[
            'w-full p-4 rounded-lg border-2 text-left transition-colors',
            selectedHookId === hook.id
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
              : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
          ]"
        >
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <span class="font-medium text-gray-900 dark:text-white">{{ hook.name }}</span>
              <p class="text-sm text-gray-600 dark:text-gray-400 mt-0.5">{{ hook.template }}</p>
              <p v-if="hook.examples && hook.examples.length" class="text-xs text-gray-400 dark:text-gray-500 mt-0.5 italic">
                z.B. "{{ hook.examples[0] }}"
              </p>
              <!-- Hook performance stats badge -->
              <p v-if="hookPerformanceMap[hook.id]" class="text-xs mt-1 flex items-center gap-2" data-testid="hook-stats-badge">
                <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400">
                  {{ hookPerformanceMap[hook.id].usage_count }}x genutzt
                </span>
                <span v-if="hookPerformanceMap[hook.id].avg_engagement_rate" class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400">
                  {{ hookPerformanceMap[hook.id].avg_engagement_rate }}% Engagement
                </span>
              </p>
            </div>
            <div class="ml-4 flex flex-col items-center">
              <div class="flex items-center gap-0.5">
                <span v-for="i in 10" :key="i" :class="['w-1.5 h-3 rounded-sm', i <= hook.effectiveness ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-600']" />
              </div>
              <span class="text-xs text-gray-500 mt-1">{{ hook.effectiveness }}/10</span>
            </div>
          </div>
        </button>
      </div>

      <div class="mt-6 flex justify-between">
        <button @click="prevStep" class="px-6 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
          Zurück
        </button>
        <button
          @click="generateScript"
          :disabled="isGenerating"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-2"
        >
          <svg v-if="isGenerating" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          {{ isGenerating ? 'Generiere...' : 'Script generieren' }}
        </button>
      </div>
    </div>

    <!-- Step 4: Generated Script with Audio Sidebar -->
    <div v-if="currentStep === 4 && generatedScript" class="flex flex-wrap lg:flex-nowrap gap-6">
      <!-- Main script content -->
      <div class="flex-1 min-w-0 space-y-6">
      <!-- Script Header -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ generatedScript.title }}
            </h2>
            <div class="flex items-center gap-3 mt-1 text-sm text-gray-500 dark:text-gray-400">
              <span>{{ generatedScript.platform === 'reels' ? 'Instagram Reels' : generatedScript.platform === 'tiktok' ? 'TikTok' : 'Story' }}</span>
              <span>{{ generatedScript.duration_seconds }}s</span>
              <span v-if="generatedScript.country" class="capitalize">{{ generatedScript.country }}</span>
              <span :class="generatedScript.source === 'gemini' ? 'text-green-600' : 'text-gray-400'">
                {{ generatedScript.source === 'gemini' ? 'KI-generiert' : 'Vorlage' }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="showAudioSidebar = !showAudioSidebar"
              :class="[
                'px-3 py-1.5 text-sm border rounded-lg transition-colors flex items-center gap-1.5',
                showAudioSidebar
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400'
                  : 'border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
              ]"
              title="Audio-Empfehlungen anzeigen"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
              </svg>
              Audio
            </button>
            <button @click="copyVoiceover" class="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors">
              Voiceover kopieren
            </button>
            <button @click="saveScript" class="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
              Speichern
            </button>
            <button @click="resetWizard" class="px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors">
              Neues Script
            </button>
          </div>
        </div>

        <!-- Timeline visualization -->
        <div v-if="scriptTab === 'scenes'" class="relative">
          <div class="flex h-8 rounded-lg overflow-hidden">
            <div
              v-for="(scene, i) in generatedScript.scenes"
              :key="i"
              :style="{ width: `${(scene.end_time - scene.start_time) / generatedScript.duration_seconds * 100}%` }"
              :class="[sceneTypeColors[scene.scene_type] || 'bg-gray-100 text-gray-800', 'flex items-center justify-center text-xs font-medium border-r border-white dark:border-gray-800 cursor-pointer hover:opacity-80 transition-opacity']"
              :title="`${sceneTypeLabels[scene.scene_type] || scene.scene_type}: ${scene.start_time}s - ${scene.end_time}s`"
              @click="startEditScene(i)"
            >
              <span v-if="(scene.end_time - scene.start_time) >= 5">
                {{ sceneTypeLabels[scene.scene_type] || scene.scene_type }}
              </span>
            </div>
          </div>
          <!-- Time markers -->
          <div class="flex justify-between mt-1 text-xs text-gray-400">
            <span>0:00</span>
            <span>{{ formatDuration(Math.floor(generatedScript.duration_seconds / 2)) }}</span>
            <span>{{ formatDuration(generatedScript.duration_seconds) }}</span>
          </div>
        </div>

        <!-- Tab Switcher: Szenen / Voiceover -->
        <div class="flex items-center gap-1 border-t border-gray-100 dark:border-gray-700 pt-3 mt-3">
          <button
            @click="scriptTab = 'scenes'"
            :class="[
              'px-4 py-1.5 text-sm rounded-lg transition-colors flex items-center gap-1.5',
              scriptTab === 'scenes'
                ? 'bg-blue-600 text-white font-medium'
                : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            ]"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
            </svg>
            Szenen
          </button>
          <button
            @click="scriptTab = 'voiceover'"
            :class="[
              'px-4 py-1.5 text-sm rounded-lg transition-colors flex items-center gap-1.5',
              scriptTab === 'voiceover'
                ? 'bg-blue-600 text-white font-medium'
                : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            ]"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
            Voiceover
          </button>
        </div>
      </div>

      <!-- Voiceover Tab Content -->
      <div v-if="scriptTab === 'voiceover'">
        <VoiceoverEditor
          ref="voiceoverEditorRef"
          :initialTopic="topic"
          :initialPlatform="platform"
          :initialDuration="duration"
          :initialTone="tone"
          :initialHookFormulaId="selectedHookId"
          :initialCountry="country"
          :showForm="true"
          :compact="false"
        />
      </div>

      <!-- Scene Cards (only in Szenen tab) -->
      <div v-if="scriptTab === 'scenes'" class="space-y-4">
        <div
          v-for="(scene, i) in generatedScript.scenes"
          :key="i"
          class="bg-white dark:bg-gray-800 rounded-xl shadow p-5"
        >
          <!-- Scene editing mode -->
          <div v-if="editingSceneIndex === i" class="space-y-3">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-semibold text-gray-900 dark:text-white">
                Szene {{ scene.scene_number }} bearbeiten
              </h3>
              <div class="flex gap-2">
                <button @click="saveSceneEdit" class="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700">Speichern</button>
                <button @click="cancelSceneEdit" class="px-3 py-1 text-sm text-gray-500 hover:text-gray-700">Abbrechen</button>
              </div>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">Voiceover-Text</label>
              <textarea v-model="editForm.voiceover_text" rows="2" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">Visuelle Beschreibung</label>
              <textarea v-model="editForm.visual_description" rows="2" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">Text-Overlay</label>
                <input v-model="editForm.text_overlay" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">Musik-Notiz</label>
                <input v-model="editForm.music_note" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
              </div>
            </div>
          </div>

          <!-- Scene display mode -->
          <div v-else>
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-3">
                <span :class="[sceneTypeColors[scene.scene_type] || 'bg-gray-100 text-gray-800', 'px-2 py-0.5 rounded text-xs font-medium']">
                  {{ sceneTypeLabels[scene.scene_type] || scene.scene_type }}
                </span>
                <span class="text-sm font-medium text-gray-900 dark:text-white">
                  Szene {{ scene.scene_number }}
                </span>
                <span class="text-xs text-gray-400">
                  {{ formatDuration(scene.start_time) }} - {{ formatDuration(scene.end_time) }}
                  ({{ scene.end_time - scene.start_time }}s)
                </span>
              </div>
              <div class="flex items-center gap-1">
                <button @click="startEditScene(i)" class="p-1 text-gray-400 hover:text-blue-600 transition-colors" title="Bearbeiten">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                </button>
                <button @click="removeScene(i)" class="p-1 text-gray-400 hover:text-red-600 transition-colors" title="Entfernen">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                </button>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Voiceover</p>
                <p class="text-sm text-gray-900 dark:text-white">{{ scene.voiceover_text }}</p>
              </div>
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Visuell</p>
                <p class="text-sm text-gray-700 dark:text-gray-300">{{ scene.visual_description }}</p>
              </div>
            </div>

            <div class="grid grid-cols-3 gap-4 mt-3">
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Text-Overlay</p>
                <p class="text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 px-2 py-1 rounded">{{ scene.text_overlay }}</p>
              </div>
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                  <svg class="w-3 h-3 inline-block mr-0.5 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" /></svg>
                  Musik
                </p>
                <p class="text-xs text-gray-600 dark:text-gray-400">{{ scene.music_note }}</p>
              </div>
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">B-Roll</p>
                <p class="text-xs text-gray-600 dark:text-gray-400">{{ scene.b_roll_suggestion }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Visual Notes (scenes tab only) -->
      <div v-if="scriptTab === 'scenes' && generatedScript.visual_notes" class="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4">
        <h3 class="text-sm font-semibold text-blue-800 dark:text-blue-300 mb-1">Visuelle Hinweise</h3>
        <p class="text-sm text-blue-700 dark:text-blue-400">{{ generatedScript.visual_notes }}</p>
      </div>

      <div class="flex justify-between">
        <button @click="currentStep = 5" class="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
          Script-Verlauf anzeigen
        </button>
      </div>
      </div><!-- end main script content -->

      <!-- Audio Suggestions Sidebar -->
      <div
        v-if="showAudioSidebar"
        class="w-80 shrink-0 hidden lg:block"
        data-testid="audio-sidebar"
      >
        <div class="sticky top-4">
          <AudioSuggestionPanel
            :platformFilter="audioPlatformFilter"
            :contentPillarFilter="audioContentPillarFilter"
            @select="onAudioSelect"
          />
        </div>
      </div>

      <!-- Mobile Audio Panel (shown below content on small screens) -->
      <div
        v-if="showAudioSidebar"
        class="lg:hidden w-full"
        data-testid="audio-sidebar-mobile"
      >
        <AudioSuggestionPanel
          :platformFilter="audioPlatformFilter"
          :contentPillarFilter="audioContentPillarFilter"
          @select="onAudioSelect"
        />
      </div>
    </div>

    <!-- Step 5: History -->
    <div v-if="currentStep === 5" class="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
          Script-Verlauf
        </h2>
        <button @click="resetWizard" class="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          Neues Script erstellen
        </button>
      </div>

      <div v-if="scriptHistory.length === 0" class="text-center py-12 text-gray-400 dark:text-gray-500">
        <p class="text-lg mb-2">Noch keine Scripts erstellt</p>
        <p class="text-sm">Erstelle dein erstes Video-Script mit dem Wizard oben.</p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="script in scriptHistory"
          :key="script.id"
          class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
        >
          <div class="flex items-center justify-between">
            <div class="flex-1 cursor-pointer" @click="loadScript(script)">
              <h3 class="font-medium text-gray-900 dark:text-white">{{ script.title }}</h3>
              <div class="flex items-center gap-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
                <span>{{ script.platform === 'reels' ? 'Reels' : script.platform === 'tiktok' ? 'TikTok' : 'Story' }}</span>
                <span>{{ script.duration_seconds }}s</span>
                <span>{{ script.scenes?.length || 0 }} Szenen</span>
                <span :class="script.source === 'gemini' ? 'text-green-600' : ''">{{ script.source === 'gemini' ? 'KI' : 'Vorlage' }}</span>
                <span v-if="script.created_at">{{ new Date(script.created_at).toLocaleDateString('de-DE') }}</span>
              </div>
            </div>
            <div class="flex items-center gap-2 ml-4">
              <button @click="loadScript(script)" class="px-3 py-1 text-xs bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 rounded hover:bg-blue-200 transition-colors">
                Öffnen
              </button>
              <button @click="deleteScript(script.id)" class="px-3 py-1 text-xs text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors">
                Löschen
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-4">
        <button @click="prevStep" class="px-6 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
          Zurück
        </button>
      </div>
    </div>
  </div>
</template>
