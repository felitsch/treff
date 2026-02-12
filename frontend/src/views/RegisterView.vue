<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const displayName = ref('')
const error = ref('')
const loading = ref(false)
const submitted = ref(false)

// Per-field validation errors
const fieldErrors = reactive({
  email: '',
  password: '',
})

function validateFields() {
  let valid = true
  fieldErrors.email = ''
  fieldErrors.password = ''

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!email.value || !email.value.trim()) {
    fieldErrors.email = 'E-Mail-Adresse ist erforderlich'
    valid = false
  } else if (!emailRegex.test(email.value.trim())) {
    fieldErrors.email = 'Bitte gib eine gueltige E-Mail-Adresse ein'
    valid = false
  }

  if (!password.value) {
    fieldErrors.password = 'Passwort ist erforderlich'
    valid = false
  } else if (password.value.length < 8) {
    fieldErrors.password = 'Passwort muss mindestens 8 Zeichen lang sein'
    valid = false
  }

  return valid
}

const handleRegister = async () => {
  error.value = ''
  submitted.value = true

  if (!validateFields()) {
    return
  }

  loading.value = true
  try {
    await auth.register(email.value, password.value, displayName.value)
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch (err) {
    const detail = err.response?.data?.detail
    if (Array.isArray(detail)) {
      // Pydantic validation error format: [{msg: "Value error, ...", ...}]
      error.value = detail.map(e => e.msg?.replace('Value error, ', '') || e.msg).join('. ')
    } else if (typeof detail === 'string') {
      error.value = detail
    } else {
      error.value = 'Registrierung fehlgeschlagen'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-treff-light dark:bg-treff-dark px-4">
    <div class="w-full max-w-md rounded-xl bg-white p-8 shadow-lg dark:bg-gray-900">
      <div class="mb-8 text-center">
        <h1 class="text-3xl font-bold text-treff-blue">TREFF</h1>
        <p class="mt-2 text-gray-600 dark:text-gray-400">Konto erstellen</p>
      </div>

      <form @submit.prevent="handleRegister" novalidate class="space-y-4">
        <div>
          <label for="displayName" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Anzeigename
          </label>
          <input
            id="displayName"
            v-model="displayName"
            type="text"
            class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-treff-blue focus:outline-none focus:ring-2 focus:ring-treff-blue/20 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
            placeholder="Dein Name"
            aria-label="Anzeigename"
          />
        </div>

        <div>
          <label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            E-Mail
          </label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            :class="[
              'mt-1 w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 dark:bg-gray-800 dark:text-white',
              submitted && fieldErrors.email
                ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20 dark:border-red-500'
                : 'border-gray-300 focus:border-treff-blue focus:ring-treff-blue/20 dark:border-gray-600'
            ]"
            placeholder="email@treff.de"
            aria-label="E-Mail Adresse"
          />
          <p v-if="submitted && fieldErrors.email" class="mt-1 text-sm text-red-600 dark:text-red-400" role="alert" data-testid="email-error">
            {{ fieldErrors.email }}
          </p>
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Passwort
          </label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            minlength="8"
            :class="[
              'mt-1 w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-2 dark:bg-gray-800 dark:text-white',
              submitted && fieldErrors.password
                ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20 dark:border-red-500'
                : 'border-gray-300 focus:border-treff-blue focus:ring-treff-blue/20 dark:border-gray-600'
            ]"
            placeholder="Mindestens 8 Zeichen"
            aria-label="Passwort"
          />
          <p v-if="submitted && fieldErrors.password" class="mt-1 text-sm text-red-600 dark:text-red-400" role="alert" data-testid="password-error">
            {{ fieldErrors.password }}
          </p>
        </div>

        <div v-if="error" class="rounded-lg bg-red-50 p-3 text-sm text-red-600 dark:bg-red-900/20 dark:text-red-400" role="alert">
          {{ error }}
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full rounded-lg bg-treff-blue px-4 py-2.5 text-sm font-medium text-white hover:bg-treff-blue/90 focus-ring disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? 'Registrieren...' : 'Registrieren' }}
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-gray-600 dark:text-gray-400">
        Bereits ein Konto?
        <router-link to="/login" class="text-treff-blue hover:underline">
          Anmelden
        </router-link>
      </p>
    </div>
  </div>
</template>
