<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ref } from 'vue'
import NotificationPanel from '@/components/common/NotificationPanel.vue'

defineEmits(['toggle-sidebar'])

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const isDark = ref(document.documentElement.classList.contains('dark'))

const toggleDarkMode = () => {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('darkMode', isDark.value ? 'true' : 'false')
}

const handleLogout = () => {
  auth.logout()
  router.push('/login')
}

// Initialize dark mode from localStorage
if (localStorage.getItem('darkMode') === 'true') {
  document.documentElement.classList.add('dark')
  isDark.value = true
}
</script>

<template>
  <header class="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6 dark:bg-gray-900 dark:border-gray-700">
    <div class="flex items-center gap-4">
      <button
        class="md:hidden text-gray-500 hover:text-gray-700 focus-ring rounded-lg p-1"
        @click="$emit('toggle-sidebar')"
        aria-label="Menu"
      >
        ☰
      </button>
      <h1 class="text-lg font-semibold text-gray-900 dark:text-white">
        {{ route.meta?.title || route.name }}
      </h1>
    </div>

    <div class="flex items-center gap-4">
      <!-- Series Notification Bell -->
      <NotificationPanel />

      <!-- Dark mode toggle -->
      <button
        class="rounded-lg p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 focus-ring"
        @click="toggleDarkMode"
        :aria-label="isDark ? 'Heller Modus' : 'Dunkler Modus'"
      >
        {{ isDark ? '☀️' : '🌙' }}
      </button>

      <!-- User info -->
      <span v-if="auth.user" class="text-sm text-gray-600 dark:text-gray-300">
        {{ auth.user.display_name || auth.user.email }}
      </span>

      <!-- Logout -->
      <button
        class="rounded-lg px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 focus-ring"
        @click="handleLogout"
      >
        Logout
      </button>
    </div>
  </header>
</template>
