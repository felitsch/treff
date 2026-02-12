<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const handleLogin = async () => {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Invalid credentials'
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
        <p class="mt-2 text-gray-600 dark:text-gray-400">Post-Generator Login</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-4">
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
          class="w-full rounded-lg bg-treff-blue px-4 py-2.5 text-sm font-medium text-white hover:bg-treff-blue/90 focus-ring disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          data-testid="login-submit"
        >
          <svg v-if="loading" class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ loading ? 'Anmelden...' : 'Anmelden' }}
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-gray-600 dark:text-gray-400">
        Noch kein Konto?
        <router-link to="/register" class="text-treff-blue hover:underline">
          Registrieren
        </router-link>
      </p>
    </div>
  </div>
</template>
