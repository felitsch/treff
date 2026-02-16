<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'
import HelpTooltip from '@/components/common/HelpTooltip.vue'
import { tooltipTexts } from '@/utils/tooltipTexts'
import TourSystem from '@/components/common/TourSystem.vue'
import { useTour } from '@/composables/useTour'
import BaseCard from '@/components/common/BaseCard.vue'
import TaskHistoryPanel from '@/components/tasks/TaskHistoryPanel.vue'

const tourRef = ref(null)
const { seenTours, loadTourProgress, resetTour, resetAllTours } = useTour()
const resettingTour = ref(null)

const auth = useAuthStore()

// Loading / error state
const loading = ref(true)
const saving = ref(false)
const error = ref(null)
const saveSuccess = ref(false)

// Account info (from auth store user)
const accountEmail = ref('')
const accountDisplayName = ref('')

// Brand settings
const brandPrimaryColor = ref('#3B7AB1')
const brandSecondaryColor = ref('#FDD000')
const brandAccentColor = ref('#FFFFFF')

// API key configuration
const geminiApiKey = ref('')
const openaiApiKey = ref('')
const unsplashApiKey = ref('')

// Posting goals
const postsPerWeek = ref('3')
const postsPerMonth = ref('12')
const preferredPostingTime = ref('10:00')
const preferredPlatform = ref('instagram_feed')
const minEpisodeGapDays = ref('1')

// ── Target Content-Mix state ──
const targetMixCategories = ref({})
const targetMixPlatforms = ref({
  instagram_feed: 40,
  instagram_story: 30,
  tiktok: 30,
})
const targetMixCountries = ref({
  usa: 30,
  canada: 20,
  australia: 20,
  newzealand: 15,
  ireland: 15,
})

// ── Hashtag Manager state ──
const hashtagSets = ref([])
const hashtagSetsLoading = ref(false)
const hashtagFilterCountry = ref('')
const hashtagFilterCategory = ref('')
const showCreateHashtagForm = ref(false)
const newHashtagSet = ref({ name: '', hashtags: '', category: '', country: '' })
const savingHashtagSet = ref(false)
const editingHashtagSetId = ref(null)
const editingHashtagSet = ref({ name: '', hashtags: '', category: '', country: '' })

const countryOptions = [
  { value: '', label: 'Alle Laender' },
  { value: 'usa', label: 'USA' },
  { value: 'canada', label: 'Kanada' },
  { value: 'australia', label: 'Australien' },
  { value: 'newzealand', label: 'Neuseeland' },
  { value: 'ireland', label: 'Irland' },
]

const categoryOptions = [
  { value: '', label: 'Alle Kategorien' },
  { value: 'allgemein', label: 'Allgemein' },
  { value: 'laender_spotlight', label: 'Laender-Spotlight' },
  { value: 'erfahrungsberichte', label: 'Erfahrungsberichte' },
  { value: 'fristen_cta', label: 'Fristen/CTA' },
  { value: 'tipps_tricks', label: 'Tipps & Tricks' },
  { value: 'faq', label: 'FAQ' },
  { value: 'infografiken', label: 'Infografiken' },
]

const countryName = (code) => {
  const map = { usa: 'USA', canada: 'Kanada', australia: 'Australien', newzealand: 'Neuseeland', ireland: 'Irland' }
  return map[code] || code || 'Allgemein'
}

const filteredHashtagSets = computed(() => {
  return hashtagSets.value.filter(s => {
    if (hashtagFilterCountry.value && s.country !== hashtagFilterCountry.value) return false
    if (hashtagFilterCategory.value && s.category !== hashtagFilterCategory.value) return false
    return true
  })
})

async function fetchHashtagSets() {
  hashtagSetsLoading.value = true
  try {
    const res = await api.get('/api/hashtag-sets')
    hashtagSets.value = res.data.hashtag_sets || []
  } catch (err) {
    console.error('Failed to load hashtag sets:', err)
  } finally {
    hashtagSetsLoading.value = false
  }
}

async function createHashtagSet() {
  if (!newHashtagSet.value.name.trim() || !newHashtagSet.value.hashtags.trim()) return
  savingHashtagSet.value = true
  try {
    const tagsArray = newHashtagSet.value.hashtags
      .split(/[\s,]+/)
      .map(t => t.trim())
      .filter(t => t.length > 0)
      .map(t => t.startsWith('#') ? t : '#' + t)
    const res = await api.post('/api/hashtag-sets', {
      name: newHashtagSet.value.name.trim(),
      hashtags: tagsArray,
      category: newHashtagSet.value.category || null,
      country: newHashtagSet.value.country || null,
      performance_score: 5.0,
    })
    hashtagSets.value.unshift(res.data)
    newHashtagSet.value = { name: '', hashtags: '', category: '', country: '' }
    showCreateHashtagForm.value = false
  } catch (err) {
    console.error('Failed to create hashtag set:', err)
  } finally {
    savingHashtagSet.value = false
  }
}

function startEditHashtagSet(hs) {
  editingHashtagSetId.value = hs.id
  editingHashtagSet.value = {
    name: hs.name,
    hashtags: hs.hashtags.join(' '),
    category: hs.category || '',
    country: hs.country || '',
  }
}

function cancelEditHashtagSet() {
  editingHashtagSetId.value = null
  editingHashtagSet.value = { name: '', hashtags: '', category: '', country: '' }
}

async function saveEditHashtagSet(id) {
  if (!editingHashtagSet.value.name.trim()) return
  savingHashtagSet.value = true
  try {
    const tagsArray = editingHashtagSet.value.hashtags
      .split(/[\s,]+/)
      .map(t => t.trim())
      .filter(t => t.length > 0)
      .map(t => t.startsWith('#') ? t : '#' + t)
    const res = await api.put(`/api/hashtag-sets/${id}`, {
      name: editingHashtagSet.value.name.trim(),
      hashtags: tagsArray,
      category: editingHashtagSet.value.category || null,
      country: editingHashtagSet.value.country || null,
    })
    const idx = hashtagSets.value.findIndex(s => s.id === id)
    if (idx !== -1) hashtagSets.value[idx] = res.data
    editingHashtagSetId.value = null
  } catch (err) {
    console.error('Failed to update hashtag set:', err)
  } finally {
    savingHashtagSet.value = false
  }
}

async function deleteHashtagSet(id) {
  try {
    await api.delete(`/api/hashtag-sets/${id}`)
    hashtagSets.value = hashtagSets.value.filter(s => s.id !== id)
  } catch (err) {
    console.error('Failed to delete hashtag set:', err)
  }
}

async function fetchSettings() {
  loading.value = true
  error.value = null
  try {
    // Fetch user profile
    if (!auth.user) {
      await auth.fetchUser()
    }
    accountEmail.value = auth.user?.email || ''
    accountDisplayName.value = auth.user?.display_name || ''

    // Fetch settings from API
    const res = await api.get('/api/settings')
    const settings = res.data

    // Apply stored settings
    if (settings.brand_primary_color) brandPrimaryColor.value = settings.brand_primary_color
    if (settings.brand_secondary_color) brandSecondaryColor.value = settings.brand_secondary_color
    if (settings.brand_accent_color) brandAccentColor.value = settings.brand_accent_color
    if (settings.gemini_api_key) geminiApiKey.value = settings.gemini_api_key
    if (settings.openai_api_key) openaiApiKey.value = settings.openai_api_key
    if (settings.unsplash_api_key) unsplashApiKey.value = settings.unsplash_api_key
    if (settings.posts_per_week) postsPerWeek.value = settings.posts_per_week
    if (settings.posts_per_month) postsPerMonth.value = settings.posts_per_month
    if (settings.preferred_posting_time) preferredPostingTime.value = settings.preferred_posting_time
    if (settings.preferred_platform) preferredPlatform.value = settings.preferred_platform
    if (settings.min_episode_gap_days !== undefined) minEpisodeGapDays.value = settings.min_episode_gap_days

    // Load target-mix settings (JSON stored as strings)
    if (settings.target_mix_platforms) {
      try { targetMixPlatforms.value = JSON.parse(settings.target_mix_platforms) } catch (e) { /* ignore */ }
    }
    if (settings.target_mix_countries) {
      try { targetMixCountries.value = JSON.parse(settings.target_mix_countries) } catch (e) { /* ignore */ }
    }
    if (settings.target_mix_categories) {
      try { targetMixCategories.value = JSON.parse(settings.target_mix_categories) } catch (e) { /* ignore */ }
    }

    // Fetch hashtag sets
    await fetchHashtagSets()
  } catch (err) {
    console.error('Failed to load settings:', err)
    error.value = 'Einstellungen konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  saveSuccess.value = false
  error.value = null
  try {
    // Save display name via profile endpoint
    if (accountDisplayName.value !== (auth.user?.display_name || '')) {
      const profileRes = await api.put('/api/auth/profile', {
        display_name: accountDisplayName.value,
      })
      // Update auth store with new user data
      auth.user = { ...auth.user, display_name: profileRes.data.display_name }
    }

    // Save other settings
    await api.put('/api/settings', {
      brand_primary_color: brandPrimaryColor.value,
      brand_secondary_color: brandSecondaryColor.value,
      brand_accent_color: brandAccentColor.value,
      gemini_api_key: geminiApiKey.value,
      openai_api_key: openaiApiKey.value,
      unsplash_api_key: unsplashApiKey.value,
      posts_per_week: postsPerWeek.value,
      posts_per_month: postsPerMonth.value,
      preferred_posting_time: preferredPostingTime.value,
      preferred_platform: preferredPlatform.value,
      min_episode_gap_days: minEpisodeGapDays.value,
      target_mix_platforms: JSON.stringify(targetMixPlatforms.value),
      target_mix_countries: JSON.stringify(targetMixCountries.value),
      target_mix_categories: JSON.stringify(targetMixCategories.value),
    })
    saveSuccess.value = true
    setTimeout(() => { saveSuccess.value = false }, 3000)
  } catch (err) {
    console.error('Failed to save settings:', err)
    error.value = 'Einstellungen konnten nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

// ── Social Content Strategy state ──
const socialStrategy = ref(null)
const socialStrategyLoading = ref(false)
const socialStrategyError = ref(null)
const socialStrategyExpanded = ref({
  platforms: false,
  hooks: false,
  repurposing: false,
  engagement: false,
  viral: false,
  hashtags: false,
  calendar: false,
})

async function fetchSocialStrategy() {
  socialStrategyLoading.value = true
  socialStrategyError.value = null
  try {
    const res = await api.get('/api/content-strategy/social-strategy')
    socialStrategy.value = res.data
  } catch (err) {
    console.error('Failed to load social strategy:', err)
    socialStrategyError.value = 'Social-Content-Strategie konnte nicht geladen werden.'
  } finally {
    socialStrategyLoading.value = false
  }
}

function toggleStrategySection(key) {
  socialStrategyExpanded.value[key] = !socialStrategyExpanded.value[key]
}

onMounted(() => {
  fetchSettings()
  loadTourProgress()
  fetchSocialStrategy()
})
</script>

<template>
  <div class="max-w-4xl mx-auto">
    <!-- Page Header -->
    <div class="mb-8 flex items-start justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Einstellungen</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Verwalte dein Konto, Branding und Integrationen.
        </p>
      </div>
      <button
        @click="tourRef?.startTour()"
        class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        title="Seiten-Tour starten"
      >
        &#10067; Tour starten
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="space-y-6">
      <div v-for="i in 4" :key="i" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 animate-pulse">
        <div class="h-5 bg-gray-200 dark:bg-gray-700 rounded w-40 mb-4"></div>
        <div class="space-y-3">
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error && !saving" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center mb-6" role="alert">
      <p class="text-red-600 dark:text-red-400">{{ error }}</p>
      <button
        @click="fetchSettings"
        class="mt-3 px-4 py-2 bg-red-100 dark:bg-red-800 text-red-700 dark:text-red-200 rounded-lg hover:bg-red-200 dark:hover:bg-red-700 transition-colors"
      >
        Erneut versuchen
      </button>
    </div>

    <!-- Settings Content -->
    <div v-else class="space-y-6" data-tour="settings-sections">
      <!-- Success Message -->
      <div
        v-if="saveSuccess"
        class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4 flex items-center gap-3"
      >
        <span class="text-green-600 dark:text-green-400 text-lg">&#10003;</span>
        <p class="text-green-700 dark:text-green-300 font-medium">Einstellungen erfolgreich gespeichert!</p>
      </div>

      <!-- Save Error Message -->
      <div
        v-if="error && saving === false && !loading"
        class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 flex items-center gap-3"
        role="alert"
      >
        <span class="text-red-600 dark:text-red-400 text-lg">&#10007;</span>
        <p class="text-red-700 dark:text-red-300 font-medium">{{ error }}</p>
      </div>

      <!-- ======================== -->
      <!-- SECTION 1: Account Settings -->
      <!-- ======================== -->
      <BaseCard padding="none" data-testid="account-section" data-tour="settings-account">
        <template #header>
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <span>&#128100;</span> Konto
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Deine Account-Informationen</p>
          </div>
        </template>
        <div class="p-5 space-y-4">
          <!-- Email (read-only) -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">E-Mail</label>
            <input
              type="email"
              :value="accountEmail"
              readonly
              aria-label="E-Mail Adresse"
              class="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 cursor-not-allowed"
              data-testid="account-email"
            />
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">E-Mail kann nicht geaendert werden.</p>
          </div>

          <!-- Display Name (editable) -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Anzeigename</label>
            <input
              type="text"
              v-model="accountDisplayName"
              placeholder="Dein Anzeigename"
              aria-label="Anzeigename"
              class="w-full px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-treff-blue focus:border-transparent"
              data-testid="account-display-name"
            />
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Wird in der App als dein Name angezeigt.</p>
          </div>
        </div>
      </BaseCard>

      <!-- ======================== -->
      <!-- SECTION 2: Brand Settings -->
      <!-- ======================== -->
      <BaseCard padding="none" data-testid="brand-section" data-tour="settings-brand">
        <template #header>
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <span>&#127912;</span> Marken-Einstellungen
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Passe die Farben fuer dein Branding an</p>
          </div>
        </template>
        <div class="p-5 space-y-4">
          <!-- Primary Color -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-1">Primaerfarbe <HelpTooltip :text="tooltipTexts.settings.primaryColor" size="sm" /></label>
            <div class="flex items-center gap-3">
              <input
                type="color"
                v-model="brandPrimaryColor"
                aria-label="Primaerfarbe Farbwahl"
                class="w-12 h-10 rounded-lg border border-gray-200 dark:border-gray-600 cursor-pointer p-0.5"
                data-testid="brand-primary-color"
              />
              <input
                type="text"
                v-model="brandPrimaryColor"
                aria-label="Primaerfarbe Hex-Wert"
                class="flex-1 px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white font-mono text-sm"
                placeholder="#3B7AB1"
              />
            </div>
          </div>

          <!-- Secondary Color -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-1">Sekundaerfarbe <HelpTooltip :text="tooltipTexts.settings.secondaryColor" size="sm" /></label>
            <div class="flex items-center gap-3">
              <input
                type="color"
                v-model="brandSecondaryColor"
                aria-label="Sekundaerfarbe Farbwahl"
                class="w-12 h-10 rounded-lg border border-gray-200 dark:border-gray-600 cursor-pointer p-0.5"
                data-testid="brand-secondary-color"
              />
              <input
                type="text"
                v-model="brandSecondaryColor"
                aria-label="Sekundaerfarbe Hex-Wert"
                class="flex-1 px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white font-mono text-sm"
                placeholder="#FDD000"
              />
            </div>
          </div>

          <!-- Accent Color -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-1">Akzentfarbe <HelpTooltip :text="tooltipTexts.settings.accentColor" size="sm" /></label>
            <div class="flex items-center gap-3">
              <input
                type="color"
                v-model="brandAccentColor"
                aria-label="Akzentfarbe Farbwahl"
                class="w-12 h-10 rounded-lg border border-gray-200 dark:border-gray-600 cursor-pointer p-0.5"
                data-testid="brand-accent-color"
              />
              <input
                type="text"
                v-model="brandAccentColor"
                aria-label="Akzentfarbe Hex-Wert"
                class="flex-1 px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white font-mono text-sm"
                placeholder="#FFFFFF"
              />
            </div>
          </div>

          <!-- Color Preview -->
          <div class="mt-2">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Vorschau</label>
            <div class="flex items-center gap-2">
              <div
                class="w-16 h-10 rounded-lg border border-gray-200 dark:border-gray-600"
                :style="{ backgroundColor: brandPrimaryColor }"
                title="Primaerfarbe"
              ></div>
              <div
                class="w-16 h-10 rounded-lg border border-gray-200 dark:border-gray-600"
                :style="{ backgroundColor: brandSecondaryColor }"
                title="Sekundaerfarbe"
              ></div>
              <div
                class="w-16 h-10 rounded-lg border border-gray-200 dark:border-gray-600"
                :style="{ backgroundColor: brandAccentColor }"
                title="Akzentfarbe"
              ></div>
            </div>
          </div>
        </div>
      </BaseCard>

      <!-- ======================== -->
      <!-- SECTION 3: API Key Configuration -->
      <!-- ======================== -->
      <BaseCard padding="none" data-testid="api-keys-section" data-tour="settings-api-keys">
        <template #header>
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <span>&#128273;</span> API-Schluessel
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Konfiguriere externe Dienste fuer KI-Generierung und Bilder</p>
          </div>
        </template>
        <div class="p-5 space-y-4">
          <!-- Gemini API Key -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-1">Google Gemini API-Schluessel <HelpTooltip :text="tooltipTexts.settings.geminiApiKey" size="sm" /></label>
            <input
              type="password"
              v-model="geminiApiKey"
              placeholder="AIza..."
              aria-label="Google Gemini API-Schluessel"
              class="w-full px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-treff-blue focus:border-transparent"
              data-testid="gemini-api-key"
            />
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Fuer KI-Textgenerierung und Bildgenerierung</p>
          </div>

          <!-- OpenAI API Key -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-1">OpenAI API-Schluessel (Optional) <HelpTooltip :text="tooltipTexts.settings.openaiApiKey" size="sm" /></label>
            <input
              type="password"
              v-model="openaiApiKey"
              placeholder="sk-..."
              aria-label="OpenAI API-Schluessel"
              class="w-full px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-treff-blue focus:border-transparent"
              data-testid="openai-api-key"
            />
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Fallback fuer Textgenerierung</p>
          </div>

          <!-- Unsplash API Key -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-1">Unsplash API-Schluessel (Optional) <HelpTooltip :text="tooltipTexts.settings.unsplashApiKey" size="sm" /></label>
            <input
              type="password"
              v-model="unsplashApiKey"
              placeholder="Client-ID..."
              aria-label="Unsplash API-Schluessel"
              class="w-full px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-treff-blue focus:border-transparent"
              data-testid="unsplash-api-key"
            />
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Fuer Stock-Fotos in Posts</p>
          </div>
        </div>
      </BaseCard>

      <!-- ======================== -->
      <!-- SECTION 4: Posting Goals -->
      <!-- ======================== -->
      <BaseCard padding="none" data-testid="posting-goals-section" data-tour="settings-posting-goals">
        <template #header>
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <span>&#127919;</span> Posting-Ziele
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Setze deine Content-Ziele und bevorzugte Zeiten</p>
          </div>
        </template>
        <div class="p-5 space-y-4">
          <!-- Posts per week -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-1">Posts pro Woche <HelpTooltip :text="tooltipTexts.settings.postsPerWeek" size="sm" /></label>
            <select
              v-model="postsPerWeek"
              aria-label="Posts pro Woche"
              class="w-full px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent"
              data-testid="posts-per-week"
            >
              <option value="1">1 Post</option>
              <option value="2">2 Posts</option>
              <option value="3">3 Posts</option>
              <option value="4">4 Posts</option>
              <option value="5">5 Posts</option>
              <option value="7">7 Posts (taeglich)</option>
            </select>
          </div>

          <!-- Posts per month -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-1">Posts pro Monat <HelpTooltip :text="tooltipTexts.settings.postsPerMonth" size="sm" /></label>
            <select
              v-model="postsPerMonth"
              aria-label="Posts pro Monat"
              class="w-full px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent"
              data-testid="posts-per-month"
            >
              <option value="4">4 Posts</option>
              <option value="8">8 Posts</option>
              <option value="12">12 Posts</option>
              <option value="20">20 Posts</option>
              <option value="30">30 Posts</option>
            </select>
          </div>

          <!-- Preferred posting time -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Bevorzugte Posting-Zeit</label>
            <input
              type="time"
              v-model="preferredPostingTime"
              aria-label="Bevorzugte Posting-Zeit"
              class="w-full px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent"
              data-testid="preferred-posting-time"
            />
          </div>

          <!-- Preferred platform -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Bevorzugte Plattform</label>
            <select
              v-model="preferredPlatform"
              aria-label="Bevorzugte Plattform"
              class="w-full px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent"
              data-testid="preferred-platform"
            >
              <option value="instagram_feed">Instagram Feed</option>
              <option value="instagram_story">Instagram Story</option>
              <option value="tiktok">TikTok</option>
            </select>
          </div>

          <!-- Min episode gap (Series/Story-Arc) -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Mindestabstand zwischen Episoden</label>
            <select
              v-model="minEpisodeGapDays"
              aria-label="Mindestabstand zwischen Episoden"
              class="w-full px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent"
              data-testid="min-episode-gap"
            >
              <option value="0">Kein Mindestabstand</option>
              <option value="1">1 Tag</option>
              <option value="2">2 Tage</option>
              <option value="3">3 Tage</option>
              <option value="5">5 Tage</option>
              <option value="7">7 Tage (1 Woche)</option>
            </select>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Warnhinweis bei zu kleinem Abstand zwischen Story-Arc-Episoden im Kalender.</p>
          </div>
        </div>
      </BaseCard>

      <!-- ======================== -->
      <!-- SECTION 4b: Target Content-Mix -->
      <!-- ======================== -->
      <BaseCard padding="none" data-testid="target-mix-section" data-tour="settings-content-mix">
        <template #header>
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <span>📊</span> Ziel Content-Mix
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Definiere die ideale Verteilung deiner Posts (in Prozent)</p>
          </div>
        </template>
        <div class="p-5 space-y-5">
          <!-- Platform mix -->
          <div>
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Plattform-Verteilung</h3>
            <div class="space-y-3">
              <div v-for="(label, key) in { instagram_feed: 'Instagram Feed', instagram_story: 'Instagram Story', tiktok: 'TikTok' }" :key="'tmix-plat-' + key" class="flex items-center gap-3">
                <span class="text-sm text-gray-600 dark:text-gray-400 w-28 flex-shrink-0">{{ label }}</span>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  v-model.number="targetMixPlatforms[key]"
                  class="flex-1 h-2 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  :aria-label="'Ziel ' + label + ' Anteil'"
                />
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300 w-10 text-right">{{ targetMixPlatforms[key] || 0 }}%</span>
              </div>
            </div>
          </div>

          <!-- Country mix -->
          <div>
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Laender-Verteilung</h3>
            <div class="space-y-3">
              <div v-for="(label, key) in { usa: 'USA', canada: 'Kanada', australia: 'Australien', newzealand: 'Neuseeland', ireland: 'Irland' }" :key="'tmix-cntry-' + key" class="flex items-center gap-3">
                <span class="text-sm text-gray-600 dark:text-gray-400 w-28 flex-shrink-0">{{ label }}</span>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  v-model.number="targetMixCountries[key]"
                  class="flex-1 h-2 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  :aria-label="'Ziel ' + label + ' Anteil'"
                />
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300 w-10 text-right">{{ targetMixCountries[key] || 0 }}%</span>
              </div>
            </div>
          </div>
        </div>
      </BaseCard>

      <!-- ======================== -->
      <!-- SECTION 5: Hashtag Manager -->
      <!-- ======================== -->
      <BaseCard padding="none" data-testid="hashtag-manager-section" data-tour="settings-hashtags">
        <template #header>
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <span>#</span> Hashtag-Manager
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Verwalte deine Hashtag-Sets fuer verschiedene Laender und Kategorien</p>
          </div>
        </template>
        <template #headerAction>
          <button
            @click="showCreateHashtagForm = !showCreateHashtagForm"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-treff-blue bg-blue-50 dark:bg-blue-900/30 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors"
            data-testid="create-hashtag-set-btn"
          >
            <span v-if="!showCreateHashtagForm">+ Neues Set</span>
            <span v-else>Abbrechen</span>
          </button>
        </template>

        <div class="p-5 space-y-4">
          <!-- Create New Set Form -->
          <div v-if="showCreateHashtagForm" class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 space-y-3" data-testid="create-hashtag-form">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Set-Name</label>
              <input
                v-model="newHashtagSet.name"
                type="text"
                placeholder="z.B. Meine USA Hashtags"
                class="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm text-gray-900 dark:text-white"
                data-testid="new-hashtag-name"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Hashtags (durch Leerzeichen oder Komma getrennt)</label>
              <textarea
                v-model="newHashtagSet.hashtags"
                rows="2"
                placeholder="#TREFFSprachreisen #HighSchoolUSA #Auslandsjahr"
                class="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm text-gray-900 dark:text-white"
                data-testid="new-hashtag-tags"
              ></textarea>
            </div>
            <div class="flex gap-3">
              <div class="flex-1">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Land</label>
                <select v-model="newHashtagSet.country" class="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm text-gray-900 dark:text-white" data-testid="new-hashtag-country">
                  <option value="">Kein Land</option>
                  <option value="usa">USA</option>
                  <option value="canada">Kanada</option>
                  <option value="australia">Australien</option>
                  <option value="newzealand">Neuseeland</option>
                  <option value="ireland">Irland</option>
                </select>
              </div>
              <div class="flex-1">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Kategorie</label>
                <select v-model="newHashtagSet.category" class="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm text-gray-900 dark:text-white" data-testid="new-hashtag-category">
                  <option value="">Keine Kategorie</option>
                  <option value="allgemein">Allgemein</option>
                  <option value="laender_spotlight">Laender-Spotlight</option>
                  <option value="erfahrungsberichte">Erfahrungsberichte</option>
                  <option value="fristen_cta">Fristen/CTA</option>
                  <option value="tipps_tricks">Tipps & Tricks</option>
                  <option value="faq">FAQ</option>
                  <option value="infografiken">Infografiken</option>
                </select>
              </div>
            </div>
            <div class="flex justify-end">
              <button
                @click="createHashtagSet"
                :disabled="savingHashtagSet || !newHashtagSet.name.trim() || !newHashtagSet.hashtags.trim()"
                class="px-4 py-2 text-sm font-medium text-white bg-treff-blue rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                data-testid="save-new-hashtag-btn"
              >
                <span v-if="savingHashtagSet">Speichern...</span>
                <span v-else>Set erstellen</span>
              </button>
            </div>
          </div>

          <!-- Filters -->
          <div class="flex gap-3">
            <select
              v-model="hashtagFilterCountry"
              class="flex-1 px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm text-gray-900 dark:text-white"
              data-testid="hashtag-filter-country"
            >
              <option v-for="opt in countryOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
            <select
              v-model="hashtagFilterCategory"
              class="flex-1 px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm text-gray-900 dark:text-white"
              data-testid="hashtag-filter-category"
            >
              <option v-for="opt in categoryOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>

          <!-- Hashtag Sets List -->
          <div v-if="hashtagSetsLoading" class="text-center py-4">
            <span class="text-gray-400 text-sm">Hashtag-Sets werden geladen...</span>
          </div>

          <div v-else-if="filteredHashtagSets.length === 0" class="text-center py-4">
            <span class="text-gray-400 text-sm">Keine Hashtag-Sets gefunden.</span>
          </div>

          <div v-else class="space-y-3 max-h-96 overflow-y-auto" data-testid="hashtag-sets-list">
            <div
              v-for="hs in filteredHashtagSets"
              :key="hs.id"
              class="border border-gray-200 dark:border-gray-600 rounded-lg p-3"
              :class="hs.is_default ? 'bg-gray-50 dark:bg-gray-700/30' : 'bg-white dark:bg-gray-700'"
              :data-testid="'hashtag-set-' + hs.id"
            >
              <!-- View mode -->
              <div v-if="editingHashtagSetId !== hs.id">
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-sm text-gray-900 dark:text-white">{{ hs.name }}</span>
                    <span v-if="hs.is_default" class="text-xs px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 rounded">Standard</span>
                    <span v-if="hs.country" class="text-xs px-1.5 py-0.5 bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 rounded">{{ countryName(hs.country) }}</span>
                  </div>
                  <div class="flex items-center gap-1" v-if="!hs.is_default">
                    <button
                      @click="startEditHashtagSet(hs)"
                      class="p-1 text-gray-400 hover:text-treff-blue transition-colors"
                      title="Bearbeiten"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                    </button>
                    <button
                      @click="deleteHashtagSet(hs.id)"
                      class="p-1 text-gray-400 hover:text-red-500 transition-colors"
                      title="Loeschen"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                    </button>
                  </div>
                </div>
                <div class="flex flex-wrap gap-1.5">
                  <span
                    v-for="(tag, tidx) in hs.hashtags"
                    :key="tidx"
                    class="text-xs px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-full"
                  >{{ tag }}</span>
                </div>
                <div class="mt-1.5 flex items-center gap-3 text-xs text-gray-400">
                  <span v-if="hs.category">{{ hs.category }}</span>
                  <span>Score: {{ hs.performance_score }}</span>
                </div>
              </div>

              <!-- Edit mode -->
              <div v-else class="space-y-2">
                <input
                  v-model="editingHashtagSet.name"
                  type="text"
                  class="w-full px-3 py-1.5 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded text-sm text-gray-900 dark:text-white"
                />
                <textarea
                  v-model="editingHashtagSet.hashtags"
                  rows="2"
                  class="w-full px-3 py-1.5 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded text-sm text-gray-900 dark:text-white"
                ></textarea>
                <div class="flex gap-2">
                  <select v-model="editingHashtagSet.country" class="flex-1 px-2 py-1.5 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded text-sm text-gray-900 dark:text-white">
                    <option value="">Kein Land</option>
                    <option value="usa">USA</option>
                    <option value="canada">Kanada</option>
                    <option value="australia">Australien</option>
                    <option value="newzealand">Neuseeland</option>
                    <option value="ireland">Irland</option>
                  </select>
                  <select v-model="editingHashtagSet.category" class="flex-1 px-2 py-1.5 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded text-sm text-gray-900 dark:text-white">
                    <option value="">Keine Kategorie</option>
                    <option value="allgemein">Allgemein</option>
                    <option value="laender_spotlight">Laender-Spotlight</option>
                    <option value="erfahrungsberichte">Erfahrungsberichte</option>
                  </select>
                </div>
                <div class="flex justify-end gap-2">
                  <button @click="cancelEditHashtagSet" class="px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">Abbrechen</button>
                  <button
                    @click="saveEditHashtagSet(hs.id)"
                    :disabled="savingHashtagSet"
                    class="px-3 py-1 text-sm font-medium text-white bg-treff-blue rounded hover:bg-blue-600 disabled:opacity-50"
                  >Speichern</button>
                </div>
              </div>
            </div>
          </div>

          <p class="text-xs text-gray-400 dark:text-gray-500">
            {{ filteredHashtagSets.length }} von {{ hashtagSets.length }} Sets angezeigt.
            Standard-Sets koennen nicht bearbeitet oder geloescht werden.
          </p>
        </div>
      </BaseCard>

      <!-- Tour-Einstellungen Section -->
      <BaseCard padding="lg" title="Tour-Einstellungen" subtitle="Jede Seite hat eine eigene gefuehrte Tour, die beim ersten Besuch automatisch startet. Hier kannst du einzelne Tours zuruecksetzen oder alle erneut aktivieren." :header-divider="false">
        <div class="space-y-3">
          <!-- Tour reset buttons per page -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div
              v-for="tourKey in ['dashboard', 'create-post', 'templates', 'assets', 'calendar', 'history', 'week-planner', 'analytics', 'students', 'story-arcs', 'recurring-formats', 'settings', 'video-export', 'audio-mixer', 'thumbnail-generator']"
              :key="tourKey"
              class="flex items-center justify-between px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700"
            >
              <span class="text-sm text-gray-700 dark:text-gray-300 capitalize">{{ tourKey.replace(/-/g, ' ') }}</span>
              <div class="flex items-center gap-2">
                <span
                  v-if="seenTours[tourKey]"
                  class="text-xs text-green-600 dark:text-green-400"
                >&#10003; Gesehen</span>
                <span v-else class="text-xs text-gray-400">Noch nicht gesehen</span>
                <button
                  v-if="seenTours[tourKey]"
                  @click="async () => { resettingTour = tourKey; await resetTour(tourKey); resettingTour = null; }"
                  class="text-xs text-treff-blue hover:text-blue-700 font-medium"
                  :disabled="resettingTour === tourKey"
                >
                  {{ resettingTour === tourKey ? '...' : 'Zuruecksetzen' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Reset all tours button -->
          <div class="pt-2 border-t border-gray-200 dark:border-gray-700">
            <button
              @click="resetAllTours()"
              class="text-sm text-red-500 hover:text-red-700 font-medium transition-colors"
            >
              Alle Tours zuruecksetzen
            </button>
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
              Beim naechsten Besuch jeder Seite wird die Tour erneut automatisch gestartet.
            </p>
          </div>
        </div>
      </BaseCard>

      <!-- ======================== -->
      <!-- SECTION 7: Social Content Strategy -->
      <!-- ======================== -->
      <BaseCard padding="none" data-testid="social-strategy-section" data-tour="settings-social-strategy">
        <template #header>
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <span>&#128640;</span> Social-Content-Strategie
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Plattform-spezifische Best Practices, Hook-Formeln, Engagement-Strategien und Content-Kalender-Regeln.
              Diese Strategie fliesst automatisch in den KI-Text-Generator und den Wochenplaner ein.
            </p>
          </div>
        </template>

        <!-- Loading -->
        <div v-if="socialStrategyLoading" class="p-5">
          <div class="animate-pulse space-y-3">
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
          </div>
        </div>

        <!-- Error -->
        <div v-else-if="socialStrategyError" class="p-5">
          <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-sm text-red-600 dark:text-red-400">
            {{ socialStrategyError }}
          </div>
        </div>

        <!-- Strategy Content -->
        <div v-else-if="socialStrategy" class="p-5 space-y-3">
          <!-- Strategy version info -->
          <div class="flex items-center gap-3 text-xs text-gray-400 dark:text-gray-500 mb-2">
            <span>Version {{ socialStrategy.version || '1.0.0' }}</span>
            <span class="w-1 h-1 rounded-full bg-gray-300 dark:bg-gray-600"></span>
            <span>Aktualisiert: {{ socialStrategy.last_updated || '-' }}</span>
          </div>

          <!-- Collapsible: Plattform-Strategien -->
          <div class="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
            <button
              @click="toggleStrategySection('platforms')"
              class="w-full flex items-center justify-between px-4 py-3 text-left bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              data-testid="social-strategy-platforms-toggle"
            >
              <span class="font-medium text-gray-800 dark:text-gray-200 text-sm flex items-center gap-2">
                <span>&#128241;</span> Plattform-Strategien
                <span class="text-xs text-gray-400 dark:text-gray-500 font-normal">(Posting-Frequenz, Zeiten, Best Practices)</span>
              </span>
              <span class="text-gray-400 transform transition-transform" :class="{ 'rotate-180': socialStrategyExpanded.platforms }">&#9660;</span>
            </button>
            <div v-if="socialStrategyExpanded.platforms" class="p-4 space-y-4">
              <div v-for="(plat, key) in socialStrategy.platforms" :key="key" class="border-b border-gray-100 dark:border-gray-700 pb-3 last:border-0 last:pb-0">
                <h4 class="font-medium text-gray-800 dark:text-gray-200 text-sm mb-2">{{ plat.name || key }}</h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div>
                    <span class="text-gray-500 dark:text-gray-400 block mb-1">Frequenz:</span>
                    <span class="text-gray-700 dark:text-gray-300">{{ plat.posting_frequency?.description || '-' }}</span>
                  </div>
                  <div>
                    <span class="text-gray-500 dark:text-gray-400 block mb-1">Optimale Zeiten:</span>
                    <span class="text-gray-700 dark:text-gray-300">{{ plat.optimal_posting_times?.description || '-' }}</span>
                  </div>
                </div>
                <div v-if="plat.best_practices?.length" class="mt-2">
                  <span class="text-gray-500 dark:text-gray-400 text-xs block mb-1">Best Practices:</span>
                  <ul class="list-disc list-inside text-xs text-gray-600 dark:text-gray-400 space-y-0.5">
                    <li v-for="(bp, idx) in plat.best_practices.slice(0, 3)" :key="idx">{{ bp }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <!-- Collapsible: Hook-Formeln -->
          <div class="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
            <button
              @click="toggleStrategySection('hooks')"
              class="w-full flex items-center justify-between px-4 py-3 text-left bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              data-testid="social-strategy-hooks-toggle"
            >
              <span class="font-medium text-gray-800 dark:text-gray-200 text-sm flex items-center gap-2">
                <span>&#127907;</span> Hook-Formeln
                <span class="text-xs text-gray-400 dark:text-gray-500 font-normal">({{ socialStrategy.hook_formulas?.formulas?.length || 0 }} Formeln)</span>
              </span>
              <span class="text-gray-400 transform transition-transform" :class="{ 'rotate-180': socialStrategyExpanded.hooks }">&#9660;</span>
            </button>
            <div v-if="socialStrategyExpanded.hooks" class="p-4">
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-3">{{ socialStrategy.hook_formulas?.description || '' }}</p>
              <div class="space-y-2">
                <div v-for="hook in (socialStrategy.hook_formulas?.formulas || [])" :key="hook.id" class="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-3">
                  <div class="flex items-center justify-between mb-1">
                    <span class="font-medium text-gray-800 dark:text-gray-200 text-sm">{{ hook.name }}</span>
                    <span class="text-xs px-2 py-0.5 rounded-full"
                      :class="hook.effectiveness >= 9 ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : hook.effectiveness >= 8 ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-600 dark:text-gray-300'"
                    >{{ hook.effectiveness }}/10</span>
                  </div>
                  <p class="text-xs text-gray-600 dark:text-gray-400 italic">"{{ hook.template }}"</p>
                  <div class="flex gap-1.5 mt-1.5">
                    <span v-for="plat in (hook.platforms || [])" :key="plat"
                      class="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400">
                      {{ plat.replace('instagram_', 'IG ') }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Collapsible: Content-Repurposing -->
          <div class="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
            <button
              @click="toggleStrategySection('repurposing')"
              class="w-full flex items-center justify-between px-4 py-3 text-left bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              data-testid="social-strategy-repurposing-toggle"
            >
              <span class="font-medium text-gray-800 dark:text-gray-200 text-sm flex items-center gap-2">
                <span>&#128260;</span> Content-Repurposing
                <span class="text-xs text-gray-400 dark:text-gray-500 font-normal">({{ socialStrategy.content_repurposing?.workflows?.length || 0 }} Workflows)</span>
              </span>
              <span class="text-gray-400 transform transition-transform" :class="{ 'rotate-180': socialStrategyExpanded.repurposing }">&#9660;</span>
            </button>
            <div v-if="socialStrategyExpanded.repurposing" class="p-4">
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-3">{{ socialStrategy.content_repurposing?.description || '' }}</p>
              <div class="space-y-2">
                <div v-for="(wf, idx) in (socialStrategy.content_repurposing?.workflows || [])" :key="idx" class="flex items-center gap-2 text-xs bg-gray-50 dark:bg-gray-700/30 rounded-lg p-2.5">
                  <span class="px-2 py-0.5 rounded bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 font-medium whitespace-nowrap">{{ wf.source.replace('instagram_', 'IG ').replace('erfahrungsbericht_text', 'Erfahrungsbericht') }}</span>
                  <span class="text-gray-400">&#8594;</span>
                  <span class="px-2 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 font-medium whitespace-nowrap">{{ wf.target.replace('instagram_', 'IG ') }}</span>
                  <span class="text-gray-500 dark:text-gray-400 flex-1 truncate">{{ wf.transformation }}</span>
                  <span class="px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap"
                    :class="wf.effort === 'niedrig' ? 'bg-green-50 text-green-600 dark:bg-green-900/20 dark:text-green-400' : wf.effort === 'mittel' ? 'bg-yellow-50 text-yellow-600 dark:bg-yellow-900/20 dark:text-yellow-400' : 'bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-400'"
                  >{{ wf.effort }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Collapsible: Engagement-Strategien -->
          <div class="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
            <button
              @click="toggleStrategySection('engagement')"
              class="w-full flex items-center justify-between px-4 py-3 text-left bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              data-testid="social-strategy-engagement-toggle"
            >
              <span class="font-medium text-gray-800 dark:text-gray-200 text-sm flex items-center gap-2">
                <span>&#128170;</span> Engagement-Strategien
                <span class="text-xs text-gray-400 dark:text-gray-500 font-normal">(CTAs, UGC, Community Building)</span>
              </span>
              <span class="text-gray-400 transform transition-transform" :class="{ 'rotate-180': socialStrategyExpanded.engagement }">&#9660;</span>
            </button>
            <div v-if="socialStrategyExpanded.engagement" class="p-4 space-y-3">
              <div v-for="cta in (socialStrategy.engagement_strategies?.cta_strategies || [])" :key="cta.type" class="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-2.5 text-xs">
                <div class="flex items-center gap-2 mb-1">
                  <span class="font-medium text-gray-800 dark:text-gray-200 capitalize">{{ cta.type.replace('_', ' ') }}</span>
                  <span class="text-gray-400">-</span>
                  <span class="text-gray-600 dark:text-gray-400">{{ cta.description }}</span>
                </div>
                <div class="flex gap-1.5 mt-1">
                  <span v-for="plat in (cta.best_for || [])" :key="plat"
                    class="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400">
                    {{ plat.replace('instagram_', 'IG ') }}
                  </span>
                </div>
              </div>
              <div v-if="socialStrategy.engagement_strategies?.community_building?.length" class="border-t border-gray-200 dark:border-gray-600 pt-3 mt-3">
                <span class="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2 block">Community Building:</span>
                <ul class="list-disc list-inside text-xs text-gray-600 dark:text-gray-400 space-y-1">
                  <li v-for="(tip, idx) in socialStrategy.engagement_strategies.community_building" :key="idx">{{ tip }}</li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Collapsible: Virale Content-Patterns -->
          <div class="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
            <button
              @click="toggleStrategySection('viral')"
              class="w-full flex items-center justify-between px-4 py-3 text-left bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              data-testid="social-strategy-viral-toggle"
            >
              <span class="font-medium text-gray-800 dark:text-gray-200 text-sm flex items-center gap-2">
                <span>&#128293;</span> Virale Content-Patterns
                <span class="text-xs text-gray-400 dark:text-gray-500 font-normal">({{ socialStrategy.viral_patterns?.patterns?.length || 0 }} Patterns)</span>
              </span>
              <span class="text-gray-400 transform transition-transform" :class="{ 'rotate-180': socialStrategyExpanded.viral }">&#9660;</span>
            </button>
            <div v-if="socialStrategyExpanded.viral" class="p-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                <div v-for="pattern in (socialStrategy.viral_patterns?.patterns || [])" :key="pattern.name" class="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-3 text-xs">
                  <span class="font-medium text-gray-800 dark:text-gray-200 block mb-1">{{ pattern.name }}</span>
                  <span class="text-gray-600 dark:text-gray-400">{{ pattern.treff_adaptation }}</span>
                  <div class="flex gap-1 mt-1.5">
                    <span v-for="plat in (pattern.platforms || [])" :key="plat"
                      class="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400">
                      {{ plat.replace('instagram_', 'IG ') }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Collapsible: Hashtag-Strategie -->
          <div class="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
            <button
              @click="toggleStrategySection('hashtags')"
              class="w-full flex items-center justify-between px-4 py-3 text-left bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              data-testid="social-strategy-hashtags-toggle"
            >
              <span class="font-medium text-gray-800 dark:text-gray-200 text-sm flex items-center gap-2">
                <span>#</span> Hashtag-Strategie
                <span class="text-xs text-gray-400 dark:text-gray-500 font-normal">(Brand, Nische, Laender)</span>
              </span>
              <span class="text-gray-400 transform transition-transform" :class="{ 'rotate-180': socialStrategyExpanded.hashtags }">&#9660;</span>
            </button>
            <div v-if="socialStrategyExpanded.hashtags" class="p-4 space-y-3 text-xs">
              <div v-if="socialStrategy.hashtag_strategy?.brand_hashtags">
                <span class="font-medium text-gray-700 dark:text-gray-300 block mb-1">Brand-Hashtags:</span>
                <div class="flex flex-wrap gap-1.5">
                  <span v-for="tag in (socialStrategy.hashtag_strategy.brand_hashtags.primary || [])" :key="tag"
                    class="px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 font-medium">{{ tag }}</span>
                  <span v-for="tag in (socialStrategy.hashtag_strategy.brand_hashtags.secondary || [])" :key="tag"
                    class="px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400">{{ tag }}</span>
                </div>
              </div>
              <div v-if="socialStrategy.hashtag_strategy?.rules?.length">
                <span class="font-medium text-gray-700 dark:text-gray-300 block mb-1">Regeln:</span>
                <ul class="list-disc list-inside text-gray-600 dark:text-gray-400 space-y-0.5">
                  <li v-for="(rule, idx) in socialStrategy.hashtag_strategy.rules" :key="idx">{{ rule }}</li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Collapsible: Content-Kalender-Regeln -->
          <div class="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
            <button
              @click="toggleStrategySection('calendar')"
              class="w-full flex items-center justify-between px-4 py-3 text-left bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              data-testid="social-strategy-calendar-toggle"
            >
              <span class="font-medium text-gray-800 dark:text-gray-200 text-sm flex items-center gap-2">
                <span>&#128197;</span> Content-Kalender-Regeln
                <span class="text-xs text-gray-400 dark:text-gray-500 font-normal">(Woechentliche Slots, Saisonale Prioritaeten)</span>
              </span>
              <span class="text-gray-400 transform transition-transform" :class="{ 'rotate-180': socialStrategyExpanded.calendar }">&#9660;</span>
            </button>
            <div v-if="socialStrategyExpanded.calendar" class="p-4 space-y-3 text-xs">
              <!-- Recurring content slots -->
              <div v-if="socialStrategy.content_calendar_rules?.recurring_content_slots?.length">
                <span class="font-medium text-gray-700 dark:text-gray-300 block mb-2">Woechentliche Content-Slots:</span>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                  <div v-for="slot in socialStrategy.content_calendar_rules.recurring_content_slots" :key="slot.name" class="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-2.5 flex items-start gap-2">
                    <span class="font-medium text-gray-800 dark:text-gray-200 whitespace-nowrap">{{ slot.day }}:</span>
                    <div>
                      <span class="text-blue-600 dark:text-blue-400 font-medium">{{ slot.name }}</span>
                      <span class="text-gray-500 dark:text-gray-400 block">{{ slot.type }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <!-- Seasonal priorities -->
              <div v-if="socialStrategy.content_calendar_rules?.seasonal_priorities">
                <span class="font-medium text-gray-700 dark:text-gray-300 block mb-2">Saisonale Prioritaeten:</span>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                  <div v-for="(season, key) in socialStrategy.content_calendar_rules.seasonal_priorities" :key="key" class="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-2.5">
                    <div class="flex items-center justify-between mb-1">
                      <span class="font-medium text-gray-800 dark:text-gray-200 capitalize">{{ key.replace('_', '-') }}</span>
                      <span class="px-1.5 py-0.5 rounded text-[10px] font-medium"
                        :class="season.urgency === 'sehr_hoch' ? 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400' : season.urgency === 'hoch' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400' : season.urgency === 'mittel' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400' : 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400'"
                      >{{ season.urgency?.replace('_', ' ') }}</span>
                    </div>
                    <span class="text-gray-600 dark:text-gray-400">{{ season.focus }}</span>
                  </div>
                </div>
              </div>
              <!-- Weekly mix rules -->
              <div v-if="socialStrategy.content_calendar_rules?.weekly_mix">
                <span class="font-medium text-gray-700 dark:text-gray-300 block mb-1">Mix-Regeln:</span>
                <ul class="list-disc list-inside text-gray-600 dark:text-gray-400 space-y-0.5">
                  <li>Mind. {{ socialStrategy.content_calendar_rules.weekly_mix.minimum_categories }} verschiedene Kategorien/Woche</li>
                  <li>Mind. {{ socialStrategy.content_calendar_rules.weekly_mix.minimum_countries }} verschiedene Laender/Woche</li>
                  <li>Mind. {{ socialStrategy.content_calendar_rules.weekly_mix.minimum_platforms }} verschiedene Plattformen/Woche</li>
                  <li v-if="socialStrategy.content_calendar_rules.weekly_mix.no_same_country_consecutive_days">Nicht dasselbe Land an aufeinanderfolgenden Tagen</li>
                  <li v-if="socialStrategy.content_calendar_rules.weekly_mix.no_same_category_consecutive_days">Nicht dieselbe Kategorie an aufeinanderfolgenden Tagen</li>
                  <li v-if="socialStrategy.content_calendar_rules.weekly_mix.include_deadline_post_if_within_14_days">Fristen-Post wenn Deadline innerhalb 14 Tagen</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </BaseCard>

      <!-- ======================== -->
      <!-- SECTION 8: Background Tasks History -->
      <!-- ======================== -->
      <TaskHistoryPanel />

      <!-- Save Button -->
      <div class="flex justify-end">
        <button
          @click="saveSettings"
          :disabled="saving"
          class="inline-flex items-center gap-2 px-6 py-3 bg-treff-blue text-white font-medium rounded-lg hover:bg-blue-600 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg v-if="saving" class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span v-if="saving">Speichern...</span>
          <span v-else>Einstellungen speichern</span>
        </button>
      </div>
    </div>

    <!-- Page-specific guided tour -->
    <TourSystem ref="tourRef" page-key="settings" />
  </div>
</template>
