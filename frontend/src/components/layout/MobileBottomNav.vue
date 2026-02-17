<script setup>
/**
 * MobileBottomNav.vue — Mobile bottom navigation bar (< 768px)
 *
 * Shows the 5 most important navigation items as a fixed bottom bar.
 * Only visible on mobile devices. Replaces the sidebar on small screens.
 */
import { useRoute } from 'vue-router'
import {
  ChartBarIcon,
  PencilSquareIcon,
  CalendarIcon,
  PhotoIcon,
  Cog6ToothIcon,
} from '@heroicons/vue/24/outline'
import {
  ChartBarIcon as ChartBarSolid,
  PencilSquareIcon as PencilSquareSolid,
  CalendarIcon as CalendarSolid,
  PhotoIcon as PhotoSolid,
  Cog6ToothIcon as Cog6ToothSolid,
} from '@heroicons/vue/24/solid'
import { markRaw } from 'vue'

const route = useRoute()

const navItems = [
  { name: 'Home', path: '/home', icon: markRaw(ChartBarIcon), iconActive: markRaw(ChartBarSolid) },
  { name: 'Erstellen', path: '/create', icon: markRaw(PencilSquareIcon), iconActive: markRaw(PencilSquareSolid) },
  { name: 'Kalender', path: '/calendar', icon: markRaw(CalendarIcon), iconActive: markRaw(CalendarSolid) },
  { name: 'Bibliothek', path: '/library', icon: markRaw(PhotoIcon), iconActive: markRaw(PhotoSolid) },
  { name: 'Mehr', path: '/settings', icon: markRaw(Cog6ToothIcon), iconActive: markRaw(Cog6ToothSolid) },
]

const isActive = (path) => route.path.startsWith(path)
</script>

<template>
  <nav
    class="fixed bottom-0 left-0 right-0 z-50 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 md:hidden safe-area-bottom"
    role="navigation"
    aria-label="Mobile Navigation"
    data-testid="mobile-bottom-nav"
  >
    <div class="flex items-center justify-around h-16 px-1">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        :class="[
          'flex flex-col items-center justify-center flex-1 h-full transition-colors',
          isActive(item.path)
            ? 'text-treff-blue'
            : 'text-gray-500 dark:text-gray-400',
        ]"
        :aria-label="item.name"
        :aria-current="isActive(item.path) ? 'page' : undefined"
      >
        <component
          :is="isActive(item.path) ? item.iconActive : item.icon"
          class="w-6 h-6 mb-0.5"
        />
        <span class="text-[10px] font-medium leading-none">{{ item.name }}</span>
      </router-link>
    </div>
  </nav>
</template>

<style scoped>
/* Safe area padding for iOS devices with home indicator */
.safe-area-bottom {
  padding-bottom: env(safe-area-inset-bottom, 0px);
}
</style>
