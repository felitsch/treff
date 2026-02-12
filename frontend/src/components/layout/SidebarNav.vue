<script setup>
import { useRoute, useRouter } from 'vue-router'

defineProps({
  collapsed: Boolean,
})

defineEmits(['toggle'])

const route = useRoute()
const router = useRouter()

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: '📊' },
  { name: 'Create Post', path: '/create-post', icon: '✏️' },
  { name: 'Templates', path: '/templates', icon: '📄' },
  { name: 'Assets', path: '/assets', icon: '🖼️' },
  { name: 'Calendar', path: '/calendar', icon: '📅' },
  { name: 'History', path: '/history', icon: '📋' },
  { name: 'Thumbnails', path: '/thumbnail-generator', icon: '🎬' },
  { name: 'Analytics', path: '/analytics', icon: '📈' },
  { name: 'Settings', path: '/settings', icon: '⚙️' },
]

const isActive = (path) => route.path.startsWith(path)
</script>

<template>
  <aside
    :class="[
      'flex flex-col border-r border-gray-200 bg-white dark:bg-gray-900 dark:border-gray-700 transition-all duration-300',
      collapsed ? 'w-16' : 'w-64',
    ]"
  >
    <!-- Logo -->
    <div class="flex h-16 items-center justify-center border-b border-gray-200 dark:border-gray-700 px-4">
      <span v-if="!collapsed" class="text-xl font-bold text-treff-blue">TREFF</span>
      <span v-else class="text-xl font-bold text-treff-blue">T</span>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto py-4" role="navigation" aria-label="Hauptnavigation" data-tour="sidebar">
      <ul class="space-y-1 px-2">
        <li v-for="item in navItems" :key="item.path">
          <router-link
            :to="item.path"
            :class="[
              'flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-base focus-ring',
              isActive(item.path)
                ? 'bg-treff-blue/10 text-treff-blue dark:bg-treff-blue/20'
                : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800',
            ]"
            :aria-label="item.name"
            :data-tour="item.path === '/create-post' ? 'create-post' : item.path === '/templates' ? 'templates' : undefined"
          >
            <span class="text-lg" :class="collapsed ? '' : 'mr-3'">{{ item.icon }}</span>
            <span v-if="!collapsed">{{ item.name }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <!-- Collapse toggle -->
    <button
      class="flex h-12 items-center justify-center border-t border-gray-200 dark:border-gray-700 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 focus-ring"
      @click="$emit('toggle')"
      aria-label="Sidebar ein-/ausklappen"
    >
      {{ collapsed ? '→' : '←' }}
    </button>
  </aside>
</template>
