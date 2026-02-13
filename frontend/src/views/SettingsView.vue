<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'
import HelpTooltip from '@/components/common/HelpTooltip.vue'
import { tooltipTexts } from '@/utils/tooltipTexts'

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

onMounted(() => {
  fetchSettings()
})
</script>

<template>
  <div class="max-w-4xl mx-auto">
    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Einstellungen</h1>
      <p class="text-gray-500 dark:text-gray-400 mt-1">
        Verwalte dein Konto, Branding und Integrationen.
      </p>
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
    <div v-else class="space-y-6">
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
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700" data-testid="account-section">
        <div class="p-5 border-b border-gray-100 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <span>&#128100;</span> Konto
          </h2>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Deine Account-Informationen</p>
        </div>
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
      </div>

      <!-- ======================== -->
      <!-- SECTION 2: Brand Settings -->
      <!-- ======================== -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700" data-testid="brand-section">
        <div class="p-5 border-b border-gray-100 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <span>&#127912;</span> Marken-Einstellungen
          </h2>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Passe die Farben fuer dein Branding an</p>
        </div>
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
      </div>

      <!-- ======================== -->
      <!-- SECTION 3: API Key Configuration -->
      <!-- ======================== -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700" data-testid="api-keys-section">
        <div class="p-5 border-b border-gray-100 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <span>&#128273;</span> API-Schluessel
          </h2>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Konfiguriere externe Dienste fuer KI-Generierung und Bilder</p>
        </div>
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
      </div>

      <!-- ======================== -->
      <!-- SECTION 4: Posting Goals -->
      <!-- ======================== -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700" data-testid="posting-goals-section">
        <div class="p-5 border-b border-gray-100 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <span>&#127919;</span> Posting-Ziele
          </h2>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Setze deine Content-Ziele und bevorzugte Zeiten</p>
        </div>
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
      </div>

      <!-- ======================== -->
      <!-- SECTION 4b: Target Content-Mix -->
      <!-- ======================== -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700" data-testid="target-mix-section">
        <div class="p-5 border-b border-gray-100 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <span>📊</span> Ziel Content-Mix
          </h2>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Definiere die ideale Verteilung deiner Posts (in Prozent)</p>
        </div>
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
      </div>

      <!-- ======================== -->
      <!-- SECTION 5: Hashtag Manager -->
      <!-- ======================== -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700" data-testid="hashtag-manager-section">
        <div class="p-5 border-b border-gray-100 dark:border-gray-700">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <span>#</span> Hashtag-Manager
              </h2>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Verwalte deine Hashtag-Sets fuer verschiedene Laender und Kategorien</p>
            </div>
            <button
              @click="showCreateHashtagForm = !showCreateHashtagForm"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-treff-blue bg-blue-50 dark:bg-blue-900/30 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors"
              data-testid="create-hashtag-set-btn"
            >
              <span v-if="!showCreateHashtagForm">+ Neues Set</span>
              <span v-else>Abbrechen</span>
            </button>
          </div>
        </div>

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
      </div>

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
  </div>
</template>
