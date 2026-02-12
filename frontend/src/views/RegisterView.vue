<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const displayName = ref('')
const error = ref('')
const loading = ref(false)

const handleRegister = async () => {
  error.value = ''

  // Client-side email validation
  // Must have content before @, content after @, and a dot in the domain
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!email.value || !emailRegex.test(email.value.trim())) {
    error.value = 'Bitte gib eine gueltige E-Mail-Adresse ein'
    return
  }
  if (!password.value || password.value.length < 8) {
    error.value = 'Passwort muss mindestens 8 Zeichen lang sein'
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
            class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-treff-blue focus:outline-none focus:ring-2 focus:ring-treff-blue/20 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
            placeholder="email@treff.de"
            aria-label="E-Mail Adresse"
          />
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
            class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-treff-blue focus:outline-none focus:ring-2 focus:ring-treff-blue/20 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
            placeholder="Mindestens 8 Zeichen"
            aria-label="Passwort"
          />
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
