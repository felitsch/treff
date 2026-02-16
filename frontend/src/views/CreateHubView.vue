<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const createOptions = [
  {
    title: 'Quick Post',
    description: 'Schnell einen einzelnen Post erstellen mit dem Schritt-fuer-Schritt Editor.',
    icon: '✏️',
    path: '/create/quick',
    color: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
    iconBg: 'bg-blue-100 dark:bg-blue-900/40',
  },
  {
    title: 'Smart Post (KI)',
    description: 'KI-gestuetzter Post-Generator mit automatischen Texten und Bildvorschlaegen.',
    icon: '🤖',
    path: '/create/smart',
    color: 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800',
    iconBg: 'bg-purple-100 dark:bg-purple-900/40',
  },
  {
    title: 'Video erstellen',
    description: 'Video-Content fuer Reels und TikTok mit Thumbnails, Overlays und Export.',
    icon: '🎬',
    path: '/create/video',
    color: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
    iconBg: 'bg-red-100 dark:bg-red-900/40',
  },
  {
    title: 'Kampagne planen',
    description: 'Mehrteilige Content-Serie oder Kampagne mit Story-Arcs und Wochenplaner.',
    icon: '📅',
    path: '/create/campaign',
    color: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800',
    iconBg: 'bg-amber-100 dark:bg-amber-900/40',
  },
]
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-8" data-tour="create-hub">
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Content erstellen</h1>
      <p class="mt-2 text-gray-600 dark:text-gray-400">Waehle eine Erstellungsmethode fuer deinen naechsten Post.</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <button
        v-for="option in createOptions"
        :key="option.path"
        @click="router.push(option.path)"
        :class="[
          'flex items-start gap-4 p-6 rounded-xl border-2 text-left transition-all hover:shadow-lg hover:scale-[1.02] cursor-pointer',
          option.color,
        ]"
      >
        <div :class="['flex items-center justify-center w-14 h-14 rounded-xl text-2xl shrink-0', option.iconBg]">
          {{ option.icon }}
        </div>
        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ option.title }}</h3>
          <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">{{ option.description }}</p>
        </div>
      </button>
    </div>
  </div>
</template>
