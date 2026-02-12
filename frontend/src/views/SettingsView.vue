<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'

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
const brandPrimaryColor = ref('#4C8BC2')
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
    <div v-else-if="error && !saving" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center mb-6">
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
              class="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 cursor-not-allowed"
              data-testid="account-email"
            />
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">E-Mail kann nicht geaendert werden.</p>
          </div>

          <!-- Display Name (read-only) -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Anzeigename</label>
            <input
              type="text"
              :value="accountDisplayName"
              readonly
              class="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 cursor-not-allowed"
              data-testid="account-display-name"
            />
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
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Primaerfarbe</label>
            <div class="flex items-center gap-3">
              <input
                type="color"
                v-model="brandPrimaryColor"
                class="w-12 h-10 rounded-lg border border-gray-200 dark:border-gray-600 cursor-pointer p-0.5"
                data-testid="brand-primary-color"
              />
              <input
                type="text"
                v-model="brandPrimaryColor"
                class="flex-1 px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white font-mono text-sm"
                placeholder="#4C8BC2"
              />
            </div>
          </div>

          <!-- Secondary Color -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Sekundaerfarbe</label>
            <div class="flex items-center gap-3">
              <input
                type="color"
                v-model="brandSecondaryColor"
                class="w-12 h-10 rounded-lg border border-gray-200 dark:border-gray-600 cursor-pointer p-0.5"
                data-testid="brand-secondary-color"
              />
              <input
                type="text"
                v-model="brandSecondaryColor"
                class="flex-1 px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white font-mono text-sm"
                placeholder="#FDD000"
              />
            </div>
          </div>

          <!-- Accent Color -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Akzentfarbe</label>
            <div class="flex items-center gap-3">
              <input
                type="color"
                v-model="brandAccentColor"
                class="w-12 h-10 rounded-lg border border-gray-200 dark:border-gray-600 cursor-pointer p-0.5"
                data-testid="brand-accent-color"
              />
              <input
                type="text"
                v-model="brandAccentColor"
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
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Google Gemini API-Schluessel</label>
            <input
              type="password"
              v-model="geminiApiKey"
              placeholder="AIza..."
              class="w-full px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-treff-blue focus:border-transparent"
              data-testid="gemini-api-key"
            />
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Fuer KI-Textgenerierung und Bildgenerierung</p>
          </div>

          <!-- OpenAI API Key -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">OpenAI API-Schluessel (Optional)</label>
            <input
              type="password"
              v-model="openaiApiKey"
              placeholder="sk-..."
              class="w-full px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-treff-blue focus:border-transparent"
              data-testid="openai-api-key"
            />
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Fallback fuer Textgenerierung</p>
          </div>

          <!-- Unsplash API Key -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Unsplash API-Schluessel (Optional)</label>
            <input
              type="password"
              v-model="unsplashApiKey"
              placeholder="Client-ID..."
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
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Posts pro Woche</label>
            <select
              v-model="postsPerWeek"
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
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Posts pro Monat</label>
            <select
              v-model="postsPerMonth"
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
              class="w-full px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent"
              data-testid="preferred-posting-time"
            />
          </div>

          <!-- Preferred platform -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Bevorzugte Plattform</label>
            <select
              v-model="preferredPlatform"
              class="w-full px-4 py-2.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent"
              data-testid="preferred-platform"
            >
              <option value="instagram_feed">Instagram Feed</option>
              <option value="instagram_story">Instagram Story</option>
              <option value="tiktok">TikTok</option>
            </select>
          </div>
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
