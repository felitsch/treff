<script setup>
// Edit Post view - to be implemented by coding agents
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">Post bearbeiten #{{ route.params.id }}</h1>
    <p class="text-gray-500 dark:text-gray-400">Post-Editor wird implementiert...</p>
  </div>
</template>
