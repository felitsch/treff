<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-treff-light dark:bg-treff-dark">
    <div class="text-center">
      <h1 class="text-6xl font-bold text-treff-blue">404</h1>
      <p class="mt-4 text-xl text-gray-600 dark:text-gray-400">Seite nicht gefunden</p>
      <p class="mt-2 text-gray-500 dark:text-gray-500">Die angeforderte Seite existiert nicht.</p>
      <button
        class="mt-6 rounded-lg bg-treff-blue px-6 py-2.5 text-sm font-medium text-white hover:bg-treff-blue/90 focus-ring"
        @click="router.push('/dashboard')"
      >
        Zurueck zum Dashboard
      </button>
    </div>
  </div>
</template>
