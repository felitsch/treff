<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const tabs = [
  { key: 'templates', label: 'Templates', icon: '📄', path: '/library/templates' },
  { key: 'template-gallery', label: 'Galerie', icon: '🎨', path: '/library/template-gallery' },
  { key: 'assets', label: 'Assets', icon: '🖼️', path: '/library/assets' },
  { key: 'history', label: 'History', icon: '📋', path: '/library/history' },
]

const activeTab = computed(() => {
  const child = route.path.split('/library/')[1]
  if (child === 'template-gallery') return 'template-gallery'
  if (child === 'assets') return 'assets'
  if (child === 'history') return 'history'
  return 'templates'
})

const switchTab = (tab) => {
  router.push(tab.path)
}
</script>

<template>
  <div data-tour="library-hub">
    <!-- Tab bar -->
    <div class="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 sm:px-6">
      <nav class="flex gap-1 -mb-px" aria-label="Bibliothek-Tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="switchTab(tab)"
          :class="[
            'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap',
            activeTab === tab.key
              ? 'border-[#3B7AB1] text-[#3B7AB1] dark:text-blue-400 dark:border-blue-400'
              : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300',
          ]"
          :aria-selected="activeTab === tab.key"
          role="tab"
        >
          <span class="text-base">{{ tab.icon }}</span>
          <span>{{ tab.label }}</span>
        </button>
      </nav>
    </div>

    <!-- Child view content -->
    <router-view />
  </div>
</template>
