<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const rememberMe = ref(false)
const error = ref('')
const loading = ref(false)
const submitted = ref(false)

// Per-field validation errors
const fieldErrors = ref({ email: '', password: '' })

// ── Country Image Rotation ──────────────────────────
const countries = [
  {
    key: 'usa',
    label: 'USA',
    emoji: '\uD83C\uDDFA\uD83C\uDDF8',
    slogan: 'Dein American Dream beginnt hier',
    gradient: 'linear-gradient(135deg, rgba(178,34,52,0.85) 0%, rgba(0,33,71,0.9) 100%)',
    accentColor: '#B22234',
  },
  {
    key: 'canada',
    label: 'Kanada',
    emoji: '\uD83C\uDDE8\uD83C\uDDE6',
    slogan: 'Erlebe Kanada \u2014 Natur & Kultur pur',
    gradient: 'linear-gradient(135deg, rgba(255,0,0,0.8) 0%, rgba(196,30,58,0.9) 100%)',
    accentColor: '#FF0000',
  },
  {
    key: 'australia',
    label: 'Australien',
    emoji: '\uD83C\uDDE6\uD83C\uDDFA',
    slogan: 'G\'day \u2014 Dein Abenteuer Down Under',
    gradient: 'linear-gradient(135deg, rgba(139,69,19,0.8) 0%, rgba(0,105,148,0.9) 100%)',
    accentColor: '#CC7722',
  },
  {
    key: 'newzealand',
    label: 'Neuseeland',
    emoji: '\uD83C\uDDF3\uD83C\uDDFF',
    slogan: 'Kia Ora \u2014 Entdecke Neuseeland',
    gradient: 'linear-gradient(135deg, rgba(27,77,62,0.85) 0%, rgba(92,184,230,0.9) 100%)',
    accentColor: '#1B4D3E',
  },
  {
    key: 'ireland',
    label: 'Irland',
    emoji: '\uD83C\uDDEE\uD83C\uDDEA',
    slogan: 'Die gruene Insel wartet auf dich',
    gradient: 'linear-gradient(135deg, rgba(22,155,98,0.85) 0%, rgba(255,140,0,0.9) 100%)',
    accentColor: '#169B62',
  },
]

const currentIndex = ref(0)
let rotationInterval = null

const currentCountry = computed(() => countries[currentIndex.value])

function startRotation() {
  rotationInterval = setInterval(() => {
    currentIndex.value = (currentIndex.value + 1) % countries.length
  }, 5000)
}

onMounted(() => {
  startRotation()
})

onUnmounted(() => {
  if (rotationInterval) clearInterval(rotationInterval)
})

// ── Form Validation ──────────────────────────────────
function validateFields() {
  let valid = true
  fieldErrors.value = { email: '', password: '' }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!email.value || !email.value.trim()) {
    fieldErrors.value.email = 'E-Mail-Adresse ist erforderlich'
    valid = false
  } else if (!emailRegex.test(email.value.trim())) {
    fieldErrors.value.email = 'Bitte gib eine gueltige E-Mail-Adresse ein'
    valid = false
  }

  if (!password.value) {
    fieldErrors.value.password = 'Passwort ist erforderlich'
    valid = false
  } else if (password.value.length < 8) {
    fieldErrors.value.password = 'Passwort muss mindestens 8 Zeichen lang sein'
    valid = false
  }

  return valid
}

const handleLogin = async () => {
  error.value = ''
  submitted.value = true

  if (!validateFields()) return

  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/home')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ungueltige Anmeldedaten'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <!-- Desktop: side-by-side layout, Mobile: stacked -->
  <div class="min-h-screen flex flex-col lg:flex-row bg-treff-light dark:bg-treff-dark">

    <!-- ═══ Left Side: Image/Gradient Panel ═══ -->
    <!-- Mobile: compact banner, Desktop: full 50% panel -->
    <div class="relative overflow-hidden h-[30vh] lg:h-auto lg:w-1/2 lg:min-h-screen flex-shrink-0">
      <!-- Background gradient layers for crossfade -->
      <div
        v-for="(country, idx) in countries"
        :key="'bg-' + country.key"
        class="absolute inset-0 transition-opacity ease-in-out"
        :class="idx === currentIndex ? 'opacity-100 z-10' : 'opacity-0 z-0'"
        :style="{ background: country.gradient, transitionDuration: '1200ms' }"
      />

      <!-- Decorative pattern overlay (desktop only) -->
      <div class="absolute inset-0 z-[15] opacity-[0.04] hidden lg:block" style="background-image: url('data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%23ffffff\' fill-opacity=\'1\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E');" />

      <!-- ── Mobile content overlay ── -->
      <div class="lg:hidden relative z-20 flex flex-col items-center justify-center h-full px-6 text-white">
        <div class="mb-3">
          <div class="text-3xl font-bold tracking-tight">
            <span class="text-white">TREFF</span>
            <span class="text-treff-yellow ml-1 text-lg font-normal">Sprachreisen</span>
          </div>
        </div>
        <div class="text-center">
          <div class="text-2xl mb-1 transition-all duration-700">{{ currentCountry.emoji }}</div>
          <p class="text-sm font-medium text-white/90 transition-all duration-700">
            {{ currentCountry.slogan }}
          </p>
        </div>
      </div>

      <!-- ── Desktop content overlay ── -->
      <div class="hidden lg:flex relative z-20 flex-col justify-between h-full w-full p-10">
        <!-- Top: TREFF Logo -->
        <div>
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
              <span class="text-xl font-bold text-white">T</span>
            </div>
            <div>
              <div class="text-2xl font-bold text-white tracking-tight">TREFF</div>
              <div class="text-sm text-white/70 font-medium -mt-0.5">Sprachreisen</div>
            </div>
          </div>
        </div>

        <!-- Center: Country info with animated transitions -->
        <div class="flex-1 flex flex-col justify-center items-start max-w-md">
          <div class="relative w-full">
            <div
              v-for="(country, idx) in countries"
              :key="'info-' + country.key"
              class="transition-all duration-700 ease-in-out"
              :class="idx === currentIndex
                ? 'opacity-100 translate-y-0'
                : 'opacity-0 translate-y-4 absolute inset-0 pointer-events-none'"
            >
              <div class="text-5xl mb-4">{{ country.emoji }}</div>
              <h2 class="text-3xl font-bold text-white mb-2">{{ country.label }}</h2>
              <p class="text-lg text-white/85 leading-relaxed">{{ country.slogan }}</p>
            </div>
          </div>
        </div>

        <!-- Bottom: Country dots indicator -->
        <div class="flex items-center gap-2">
          <button
            v-for="(country, idx) in countries"
            :key="'dot-' + country.key"
            @click="currentIndex = idx"
            class="group relative h-2 rounded-full transition-all duration-300 cursor-pointer"
            :class="idx === currentIndex ? 'w-8 bg-white' : 'w-2 bg-white/40 hover:bg-white/60'"
            :aria-label="'Zeige ' + country.label"
          >
          </button>
          <span class="ml-3 text-xs text-white/50 font-medium">
            {{ currentIndex + 1 }} / {{ countries.length }}
          </span>
        </div>
      </div>
    </div>

    <!-- ═══ Right Side: Login Form ═══ -->
    <div class="flex-1 flex items-center justify-center px-6 py-8 lg:py-0 bg-white dark:bg-gray-900">
      <div class="w-full max-w-md">
        <!-- TREFF Logo badge (desktop only, small) -->
        <div class="hidden lg:flex items-center gap-3 mb-8">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center"
            :style="{ background: currentCountry.accentColor + '15' }">
            <span class="text-lg font-bold" :style="{ color: currentCountry.accentColor }">T</span>
          </div>
          <span class="text-sm font-medium text-gray-400 dark:text-gray-500">Post-Generator</span>
        </div>

        <!-- Heading -->
        <div class="mb-8">
          <h1 class="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">
            Willkommen zurueck
          </h1>
          <p class="mt-2 text-gray-500 dark:text-gray-400">
            Melde dich an, um Content fuer TREFF zu erstellen
          </p>
        </div>

        <!-- Login Form -->
        <form @submit.prevent="handleLogin" novalidate class="space-y-5">
          <!-- Email Field -->
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              E-Mail
            </label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <input
                id="email"
                v-model="email"
                type="email"
                required
                :class="[
                  'w-full pl-10 pr-4 py-3 rounded-xl border text-sm transition-all duration-200',
                  'focus:outline-none focus:ring-2 focus:ring-offset-1',
                  'dark:bg-gray-800 dark:text-white',
                  submitted && fieldErrors.email
                    ? 'border-red-400 focus:border-red-500 focus:ring-red-500/30 dark:border-red-500'
                    : 'border-gray-200 focus:border-primary-500 focus:ring-primary-500/30 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                ]"
                placeholder="email@treff.de"
                aria-label="E-Mail Adresse"
                data-testid="login-email"
              />
            </div>
            <p v-if="submitted && fieldErrors.email" class="mt-1.5 text-sm text-red-600 dark:text-red-400" role="alert" data-testid="email-error">
              {{ fieldErrors.email }}
            </p>
          </div>

          <!-- Password Field -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Passwort
            </label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <input
                id="password"
                v-model="password"
                type="password"
                required
                :class="[
                  'w-full pl-10 pr-4 py-3 rounded-xl border text-sm transition-all duration-200',
                  'focus:outline-none focus:ring-2 focus:ring-offset-1',
                  'dark:bg-gray-800 dark:text-white',
                  submitted && fieldErrors.password
                    ? 'border-red-400 focus:border-red-500 focus:ring-red-500/30 dark:border-red-500'
                    : 'border-gray-200 focus:border-primary-500 focus:ring-primary-500/30 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                ]"
                placeholder="Mindestens 8 Zeichen"
                aria-label="Passwort"
                data-testid="login-password"
              />
            </div>
            <p v-if="submitted && fieldErrors.password" class="mt-1.5 text-sm text-red-600 dark:text-red-400" role="alert" data-testid="password-error">
              {{ fieldErrors.password }}
            </p>
          </div>

          <!-- Remember Me & Forgot Password Row -->
          <div class="flex items-center justify-between">
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                v-model="rememberMe"
                type="checkbox"
                class="w-4 h-4 rounded border-gray-300 text-primary-500 focus:ring-primary-500/50 dark:border-gray-600 dark:bg-gray-800"
                data-testid="remember-me"
              />
              <span class="text-sm text-gray-600 dark:text-gray-400">Angemeldet bleiben</span>
            </label>
            <a href="#" class="text-sm text-primary-500 hover:text-primary-600 dark:text-primary-400 dark:hover:text-primary-300 transition-colors" data-testid="forgot-password">
              Passwort vergessen?
            </a>
          </div>

          <!-- Error Message -->
          <div
            v-if="error"
            class="flex items-center gap-2 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-3.5"
            role="alert"
          >
            <svg class="w-5 h-5 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <span class="text-sm text-red-700 dark:text-red-400">{{ error }}</span>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full rounded-xl bg-primary-500 px-4 py-3 text-sm font-semibold text-white shadow-md
              hover:bg-primary-600 hover:shadow-lg
              active:bg-primary-700
              focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:ring-offset-2
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-all duration-200
              flex items-center justify-center gap-2"
            data-testid="login-submit"
          >
            <svg v-if="loading" class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ loading ? 'Anmelden...' : 'Anmelden' }}
          </button>
        </form>

        <!-- Register Link -->
        <p class="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
          Noch kein Konto?
          <router-link
            to="/register"
            class="font-semibold text-primary-500 hover:text-primary-600 dark:text-primary-400 dark:hover:text-primary-300 transition-colors"
          >
            Jetzt registrieren
          </router-link>
        </p>

        <!-- Footer -->
        <div class="mt-10 pt-6 border-t border-gray-100 dark:border-gray-800">
          <p class="text-xs text-center text-gray-400 dark:text-gray-500">
            TREFF Sprachreisen &mdash; seit 1984
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
