<script setup>
/**
 * CampaignCreateView — Multi-Post-Kampagnen-Planungs-View
 *
 * 3-step flow:
 * 1. Setup: Title, description, goal, date range, platforms, country focus
 * 2. AI Generation: Generate post plan via /api/campaigns/:id/generate
 * 3. Timeline: Visualize and edit the generated post plan
 *
 * @see /api/campaigns — Campaign CRUD endpoints
 * @see /api/campaigns/:id/generate — AI plan generation
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import CampaignTimeline from '@/components/campaign/CampaignTimeline.vue'
import CampaignPostCard from '@/components/campaign/CampaignPostCard.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const router = useRouter()
const toast = useToast()

// ─── Step management ─────────────────────────────────────────
const currentStep = ref(1) // 1=setup, 2=generating, 3=timeline

// ─── Step 1: Campaign Setup ─────────────────────────────────
const form = ref({
  title: '',
  description: '',
  goal: 'awareness',
  startDate: new Date().toISOString().split('T')[0],
  endDate: new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0],
  platforms: ['instagram_feed'],
  countries: [],
})

const goalOptions = [
  { value: 'awareness', label: 'Awareness', icon: 'eye', description: 'Reichweite aufbauen, Marke bekannt machen' },
  { value: 'engagement', label: 'Engagement', icon: 'chat-bubble', description: 'Interaktionen foerdern, Community aufbauen' },
  { value: 'conversion', label: 'Conversion', icon: 'fire', description: 'Bewerbungen und Anmeldungen generieren' },
  { value: 'traffic', label: 'Traffic', icon: 'link', description: 'Website-Besuche steigern' },
]

const platformOptions = [
  { value: 'instagram_feed', label: 'Instagram Feed', icon: 'camera' },
  { value: 'instagram_story', label: 'Instagram Story', icon: 'device-mobile' },
  { value: 'tiktok', label: 'TikTok', icon: 'musical-note' },
]

const countryOptions = [
  { value: 'usa', label: 'USA', emoji: '🇺🇸' },
  { value: 'kanada', label: 'Kanada', emoji: '🇨🇦' },
  { value: 'australien', label: 'Australien', emoji: '🇦🇺' },
  { value: 'neuseeland', label: 'Neuseeland', emoji: '🇳🇿' },
  { value: 'irland', label: 'Irland', emoji: '🇮🇪' },
]

// ─── Step 2 & 3: Generated Plan ─────────────────────────────
const campaignId = ref(null)
const generatedPlan = ref(null)
const generatedPosts = ref([])
const isGenerating = ref(false)
const isSaving = ref(false)
const editingPost = ref(null)

// ─── Validation ──────────────────────────────────────────────
const isFormValid = computed(() => {
  return form.value.title.trim().length > 0 &&
    form.value.startDate &&
    form.value.endDate &&
    form.value.platforms.length > 0
})

// ─── Pillar distribution ────────────────────────────────────
const pillarDistribution = computed(() => {
  const dist = {}
  generatedPosts.value.forEach(p => {
    const cat = p.suggested_category_label || p.suggested_category || 'Sonstige'
    dist[cat] = (dist[cat] || 0) + 1
  })
  return Object.entries(dist).map(([label, count]) => ({ label, count }))
})

const totalDays = computed(() => {
  if (!form.value.startDate || !form.value.endDate) return 0
  const start = new Date(form.value.startDate)
  const end = new Date(form.value.endDate)
  return Math.max(1, Math.ceil((end - start) / 86400000))
})

// ─── Platform toggle ─────────────────────────────────────────
function togglePlatform(value) {
  const idx = form.value.platforms.indexOf(value)
  if (idx >= 0) {
    if (form.value.platforms.length > 1) {
      form.value.platforms.splice(idx, 1)
    }
  } else {
    form.value.platforms.push(value)
  }
}

function toggleCountry(value) {
  const idx = form.value.countries.indexOf(value)
  if (idx >= 0) {
    form.value.countries.splice(idx, 1)
  } else {
    form.value.countries.push(value)
  }
}

// ─── Step 1 → Step 2: Create campaign and generate plan ─────
async function generatePlan() {
  if (!isFormValid.value) return

  isGenerating.value = true
  currentStep.value = 2

  try {
    // Create campaign first
    const createRes = await api.post('/api/campaigns', {
      title: form.value.title,
      description: form.value.description,
      goal: form.value.goal,
      start_date: form.value.startDate,
      end_date: form.value.endDate,
      platforms: form.value.platforms,
      status: 'draft',
    })
    campaignId.value = createRes.data.id

    // Generate post plan
    const genRes = await api.post(`/api/campaigns/${campaignId.value}/generate`)
    generatedPlan.value = genRes.data
    generatedPosts.value = genRes.data.posts || []

    toast.success(`Plan mit ${generatedPosts.value.length} Posts generiert!`)
    currentStep.value = 3
  } catch (err) {
    toast.error('Kampagnen-Erstellung fehlgeschlagen. Bitte versuche es erneut.')
    currentStep.value = 1
  } finally {
    isGenerating.value = false
  }
}

// ─── Regenerate plan ─────────────────────────────────────────
async function regeneratePlan() {
  if (!campaignId.value) return
  isGenerating.value = true

  try {
    // Update campaign dates/goal if changed
    await api.put(`/api/campaigns/${campaignId.value}`, {
      title: form.value.title,
      description: form.value.description,
      goal: form.value.goal,
      start_date: form.value.startDate,
      end_date: form.value.endDate,
      platforms: form.value.platforms,
    })

    const genRes = await api.post(`/api/campaigns/${campaignId.value}/generate`)
    generatedPlan.value = genRes.data
    generatedPosts.value = genRes.data.posts || []
    toast.success(`Neuer Plan mit ${generatedPosts.value.length} Posts generiert!`)
  } catch (err) {
    toast.error('Regenerierung fehlgeschlagen.')
  } finally {
    isGenerating.value = false
  }
}

// ─── Save campaign (create actual draft posts) ───────────────
async function saveCampaign() {
  if (!campaignId.value) return
  isSaving.value = true

  try {
    // Activate the campaign
    await api.put(`/api/campaigns/${campaignId.value}`, {
      status: 'active',
    })

    toast.success('Kampagne aktiviert! Posts wurden als Entwürfe gespeichert.')
    router.push('/calendar')
  } catch (err) {
    toast.error('Speichern fehlgeschlagen.')
  } finally {
    isSaving.value = false
  }
}

// ─── Post editing ────────────────────────────────────────────
function openPostEdit(post) {
  editingPost.value = { ...post }
}

function closePostEdit() {
  editingPost.value = null
}

function savePostEdit() {
  if (!editingPost.value) return
  const idx = generatedPosts.value.findIndex(p => p.order === editingPost.value.order)
  if (idx >= 0) {
    generatedPosts.value[idx] = { ...editingPost.value }
  }
  editingPost.value = null
}

function removePost(order) {
  generatedPosts.value = generatedPosts.value.filter(p => p.order !== order)
}

// ─── Drag and drop reorder ──────────────────────────────────
let draggedIndex = null

function onDragStart(index) {
  draggedIndex = index
}

function onDragOver(e, index) {
  e.preventDefault()
}

function onDrop(e, index) {
  e.preventDefault()
  if (draggedIndex === null || draggedIndex === index) return
  const items = [...generatedPosts.value]
  const [removed] = items.splice(draggedIndex, 1)
  items.splice(index, 0, removed)
  // Update order numbers
  items.forEach((item, i) => { item.order = i + 1 })
  generatedPosts.value = items
  draggedIndex = null
}

// ─── Category pillar colors ─────────────────────────────────
function pillarColor(category) {
  const colors = {
    laender_spotlight: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
    erfahrungsbericht: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
    behind_the_scenes: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
    infografik: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300',
    quiz_umfrage: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300',
    meme_humor: 'bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300',
    this_or_that: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
    fristen_cta: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
    preis_vergleich: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
    eltern_info: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300',
    faq: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
    blog_teaser: 'bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300',
    webinar_event: 'bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300',
    story_teaser: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  }
  return colors[category] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
}

function countryEmoji(country) {
  const map = { usa: '🇺🇸', kanada: '🇨🇦', australien: '🇦🇺', neuseeland: '🇳🇿', irland: '🇮🇪' }
  return map[country] || '🌍'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' })
}

function formatDateLong(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', { weekday: 'short', day: '2-digit', month: 'short' })
}
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-6" data-testid="campaign-create-view">
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center gap-3 mb-2">
        <button
          @click="router.push('/create')"
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
        </button>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Kampagne erstellen</h1>
        <span class="text-xs font-medium px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300">
          Multi-Post
        </span>
      </div>
      <p class="text-sm text-gray-600 dark:text-gray-400 ml-8">
        Plane eine mehrteilige Content-Kampagne — AI generiert einen Post-Plan entlang der Buyer Journey.
      </p>
    </div>

    <!-- Step indicator -->
    <div class="flex items-center gap-4 mb-8">
      <div
        v-for="step in [
          { num: 1, label: 'Setup' },
          { num: 2, label: 'AI-Generierung' },
          { num: 3, label: 'Timeline & Plan' },
        ]"
        :key="step.num"
        class="flex items-center gap-2"
      >
        <div
          :class="[
            'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all',
            currentStep >= step.num
              ? 'bg-amber-500 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400',
          ]"
        >
          <svg v-if="currentStep > step.num" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
          <span v-else>{{ step.num }}</span>
        </div>
        <span
          :class="[
            'text-sm font-medium',
            currentStep >= step.num ? 'text-gray-900 dark:text-white' : 'text-gray-400 dark:text-gray-500'
          ]"
        >
          {{ step.label }}
        </span>
        <div v-if="step.num < 3" class="w-8 h-px bg-gray-300 dark:bg-gray-600"></div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- STEP 1: Campaign Setup Form -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 1" class="space-y-6" data-testid="setup-step">
      <!-- Title & Description -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 space-y-4">
        <div>
          <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-1.5">Kampagnen-Titel *</label>
          <input
            v-model="form.title"
            type="text"
            class="w-full bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2.5 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
            placeholder="z.B. Bewerbungsphase Herbst 2026"
            data-testid="campaign-title"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-1.5">Beschreibung (optional)</label>
          <textarea
            v-model="form.description"
            rows="2"
            class="w-full bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:ring-1 focus:ring-amber-500 focus:border-amber-500 resize-none"
            placeholder="Kurze Beschreibung der Kampagnenziele..."
            data-testid="campaign-description"
          />
        </div>
      </div>

      <!-- Goal selection -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-3">Kampagnen-Ziel *</label>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <button
            v-for="opt in goalOptions"
            :key="opt.value"
            @click="form.goal = opt.value"
            :class="[
              'flex flex-col items-center gap-2 p-4 rounded-xl border-2 text-center transition-all',
              form.goal === opt.value
                ? 'border-amber-400 bg-amber-50 dark:bg-amber-900/20 shadow-sm'
                : 'border-gray-200 dark:border-gray-600 hover:border-gray-300',
            ]"
            :data-testid="`goal-${opt.value}`"
          >
            <AppIcon :name="opt.icon" class="w-7 h-7 text-gray-600 dark:text-gray-300" />
            <span class="text-sm font-semibold text-gray-900 dark:text-white">{{ opt.label }}</span>
            <span class="text-[10px] text-gray-500 dark:text-gray-400 leading-tight">{{ opt.description }}</span>
          </button>
        </div>
      </div>

      <!-- Date range -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-3">Zeitraum *</label>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Start</label>
            <input
              v-model="form.startDate"
              type="date"
              class="w-full bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:ring-1 focus:ring-amber-500"
              data-testid="start-date"
            />
          </div>
          <div>
            <label class="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Ende</label>
            <input
              v-model="form.endDate"
              type="date"
              class="w-full bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:ring-1 focus:ring-amber-500"
              data-testid="end-date"
            />
          </div>
        </div>
        <p class="text-xs text-gray-400 mt-2">{{ totalDays }} Tage &middot; ca. {{ Math.max(3, Math.min(20, Math.floor(totalDays / 2))) }} Posts</p>
      </div>

      <!-- Platforms -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-3">Plattformen *</label>
        <div class="flex flex-wrap gap-3">
          <button
            v-for="opt in platformOptions"
            :key="opt.value"
            @click="togglePlatform(opt.value)"
            :class="[
              'flex items-center gap-2 px-4 py-2.5 rounded-lg border-2 text-sm font-medium transition-all',
              form.platforms.includes(opt.value)
                ? 'border-amber-400 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300'
                : 'border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-gray-300',
            ]"
            :data-testid="`platform-${opt.value}`"
          >
            <AppIcon :name="opt.icon" class="w-5 h-5" />
            <span>{{ opt.label }}</span>
          </button>
        </div>
      </div>

      <!-- Country focus -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-3">Länder-Fokus (optional)</label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="opt in countryOptions"
            :key="opt.value"
            @click="toggleCountry(opt.value)"
            :class="[
              'flex items-center gap-1.5 px-3 py-2 rounded-lg border text-sm transition-all',
              form.countries.includes(opt.value)
                ? 'border-amber-400 bg-amber-50 dark:bg-amber-900/20 font-medium'
                : 'border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-gray-300',
            ]"
          >
            <span>{{ opt.emoji }}</span>
            <span>{{ opt.label }}</span>
          </button>
        </div>
      </div>

      <!-- Generate button -->
      <button
        @click="generatePlan"
        :disabled="!isFormValid"
        :class="[
          'w-full flex items-center justify-center gap-2 py-3.5 rounded-xl text-sm font-semibold transition-all',
          isFormValid
            ? 'bg-amber-500 hover:bg-amber-600 text-white shadow-sm hover:shadow-md'
            : 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed',
        ]"
        data-testid="generate-button"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
        </svg>
        AI-Plan generieren
      </button>
    </div>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- STEP 2: Generating (loading state) -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 2" class="py-16" data-testid="generating-step">
      <div class="flex flex-col items-center gap-6">
        <div class="w-16 h-16 border-4 border-amber-200 border-t-amber-500 rounded-full animate-spin"></div>
        <div class="text-center">
          <p class="text-lg font-semibold text-gray-900 dark:text-white">AI generiert deinen Kampagnen-Plan...</p>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {{ form.title }} &middot; {{ goalOptions.find(g => g.value === form.goal)?.label }} &middot; {{ totalDays }} Tage
          </p>
        </div>
        <div class="w-full max-w-sm space-y-2">
          <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
          <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-4/5"></div>
          <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-3/5"></div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- STEP 3: Timeline & Plan -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 3" class="space-y-6" data-testid="timeline-step">

      <!-- Plan summary header -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <div class="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h2 class="text-lg font-bold text-gray-900 dark:text-white">{{ form.title }}</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5 flex items-center gap-1">
              <AppIcon :name="goalOptions.find(g => g.value === form.goal)?.icon || 'eye'" class="w-4 h-4 inline-block" />
              {{ goalOptions.find(g => g.value === form.goal)?.label }}
              &middot; {{ formatDate(form.startDate) }} – {{ formatDate(form.endDate) }}
              &middot; {{ generatedPosts.length }} Posts
            </p>
          </div>
          <div class="flex gap-2">
            <button
              @click="regeneratePlan"
              :disabled="isGenerating"
              class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-600 text-xs font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              data-testid="regenerate-button"
            >
              {{ isGenerating ? 'Generiert...' : 'Neu generieren' }}
            </button>
            <button
              @click="currentStep = 1"
              class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-600 text-xs font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Setup bearbeiten
            </button>
          </div>
        </div>
      </div>

      <!-- Pillar distribution mini-chart -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5" data-testid="pillar-distribution">
        <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-3">Content-Pillar-Verteilung</h3>
        <div class="flex flex-wrap gap-2">
          <div
            v-for="pillar in pillarDistribution"
            :key="pillar.label"
            class="flex items-center gap-2"
          >
            <div class="h-6 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center gap-1.5 px-2.5">
              <span class="text-xs font-medium text-amber-700 dark:text-amber-300">{{ pillar.label }}</span>
              <span class="text-[10px] font-bold text-amber-600 dark:text-amber-400 bg-amber-200 dark:bg-amber-800/50 rounded-full w-4 h-4 flex items-center justify-center">{{ pillar.count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Timeline visualization -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5" data-testid="campaign-timeline">
        <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-4">Timeline</h3>

        <!-- Timeline posts list -->
        <div class="space-y-3">
          <div
            v-for="(post, index) in generatedPosts"
            :key="post.order"
            class="flex items-start gap-3 group"
            draggable="true"
            @dragstart="onDragStart(index)"
            @dragover="(e) => onDragOver(e, index)"
            @drop="(e) => onDrop(e, index)"
            :data-testid="`timeline-post-${post.order}`"
          >
            <!-- Date marker -->
            <div class="w-20 shrink-0 text-right pt-2">
              <p class="text-xs font-semibold text-gray-900 dark:text-white">{{ formatDateLong(post.scheduled_date) }}</p>
            </div>

            <!-- Timeline line -->
            <div class="flex flex-col items-center shrink-0">
              <div class="w-3 h-3 rounded-full bg-amber-400 border-2 border-white dark:border-gray-800 shadow-sm mt-2.5"></div>
              <div v-if="index < generatedPosts.length - 1" class="w-0.5 flex-1 bg-amber-200 dark:bg-amber-800 min-h-[2rem]"></div>
            </div>

            <!-- Post card -->
            <div
              :class="[
                'flex-1 bg-gray-50 dark:bg-gray-700/50 rounded-xl p-3 border border-gray-200 dark:border-gray-600',
                'cursor-grab active:cursor-grabbing hover:shadow-md hover:border-amber-300 dark:hover:border-amber-700 transition-all',
              ]"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span :class="['text-[10px] font-medium px-1.5 py-0.5 rounded', pillarColor(post.suggested_category)]">
                      {{ post.suggested_category_label || post.suggested_category }}
                    </span>
                    <span class="text-[10px] text-gray-400">{{ post.suggested_platform }}</span>
                    <span class="text-sm">{{ countryEmoji(post.suggested_country) }}</span>
                  </div>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Post #{{ post.order }} &middot; {{ post.suggested_country }}
                  </p>
                </div>
                <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    @click="openPostEdit(post)"
                    class="p-1 rounded text-gray-400 hover:text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/20 transition-colors"
                    title="Bearbeiten"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125" />
                    </svg>
                  </button>
                  <button
                    @click="removePost(post.order)"
                    class="p-1 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                    title="Entfernen"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Save campaign -->
      <div class="flex items-center gap-3">
        <button
          @click="saveCampaign"
          :disabled="isSaving || generatedPosts.length === 0"
          :class="[
            'flex-1 flex items-center justify-center gap-2 py-3.5 rounded-xl text-sm font-semibold transition-all',
            generatedPosts.length > 0
              ? 'bg-amber-500 hover:bg-amber-600 text-white shadow-sm hover:shadow-md'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed',
          ]"
          data-testid="save-campaign-button"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
          {{ isSaving ? 'Wird gespeichert...' : 'Kampagne speichern & aktivieren' }}
        </button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- Post Edit Modal -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <div
      v-if="editingPost"
      class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
      @click.self="closePostEdit"
      data-testid="post-edit-modal"
    >
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
        <h3 class="text-lg font-bold text-gray-900 dark:text-white">Post #{{ editingPost.order }} bearbeiten</h3>

        <div>
          <label class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-1 block">Datum</label>
          <input
            v-model="editingPost.scheduled_date"
            type="date"
            class="w-full bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-1 block">Kategorie</label>
          <input
            v-model="editingPost.suggested_category_label"
            type="text"
            class="w-full bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-1 block">Plattform</label>
          <select
            v-model="editingPost.suggested_platform"
            class="w-full bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm"
          >
            <option value="instagram_feed">Instagram Feed</option>
            <option value="instagram_story">Instagram Story</option>
            <option value="tiktok">TikTok</option>
          </select>
        </div>

        <div>
          <label class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-1 block">Land</label>
          <select
            v-model="editingPost.suggested_country"
            class="w-full bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm"
          >
            <option v-for="c in countryOptions" :key="c.value" :value="c.value">{{ c.emoji }} {{ c.label }}</option>
          </select>
        </div>

        <div class="flex gap-3 pt-2">
          <button
            @click="savePostEdit"
            class="flex-1 py-2.5 bg-amber-500 text-white rounded-xl text-sm font-semibold hover:bg-amber-600 transition-colors"
          >
            Speichern
          </button>
          <button
            @click="closePostEdit"
            class="px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            Abbrechen
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
