<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import SidebarNav from './SidebarNav.vue'
import TopBar from './TopBar.vue'
import BreadcrumbNav from './BreadcrumbNav.vue'
import MobileBottomNav from './MobileBottomNav.vue'
import { useReminders } from '@/composables/useReminders'
import { useSeriesReminders } from '@/composables/useSeriesReminders'

const router = useRouter()
// Restore sidebar state from localStorage (default: expanded on desktop)
const savedSidebarState = localStorage.getItem('treff-sidebar-collapsed')
const sidebarCollapsed = ref(savedSidebarState === 'true')
const isMobileOverlay = ref(false)
const { startPolling, stopPolling } = useReminders()
const { startPolling: startSeriesPolling, stopPolling: stopSeriesPolling } = useSeriesReminders()

// Page transition direction: forward slides left, backward slides right
const transitionName = computed(() => {
  return router.transitionDirection === 'backward' ? 'page-slide-back' : 'page-slide'
})

const TABLET_BREAKPOINT = 1024

const toggleSidebar = () => {
  if (window.innerWidth < 768) {
    // Mobile: toggle overlay sidebar
    isMobileOverlay.value = !isMobileOverlay.value
  } else {
    sidebarCollapsed.value = !sidebarCollapsed.value
    // Persist sidebar state
    localStorage.setItem('treff-sidebar-collapsed', String(sidebarCollapsed.value))
  }
}

const closeMobileOverlay = () => {
  isMobileOverlay.value = false
}

const handleResize = () => {
  const width = window.innerWidth
  if (width < 768) {
    // Mobile: hide sidebar behind hamburger
    sidebarCollapsed.value = false
    isMobileOverlay.value = false
  } else if (width < TABLET_BREAKPOINT) {
    // Tablet: auto-collapse sidebar
    sidebarCollapsed.value = true
    isMobileOverlay.value = false
  } else {
    // Desktop: expand sidebar
    sidebarCollapsed.value = false
    isMobileOverlay.value = false
  }
}

// Start reminder polling when the layout mounts (user is authenticated)
onMounted(() => {
  startPolling()
  startSeriesPolling()
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  stopPolling()
  stopSeriesPolling()
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-treff-light dark:bg-treff-dark">
    <!-- Skip-to-content link for keyboard users (WCAG 2.1 AA) -->
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[9999] focus:rounded-lg focus:bg-treff-blue focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-white"
      data-testid="skip-to-content"
    >
      Zum Hauptinhalt springen
    </a>

    <!-- Mobile overlay backdrop -->
    <div
      v-if="isMobileOverlay"
      class="fixed inset-0 z-30 bg-black/50 md:hidden"
      @click="closeMobileOverlay"
      aria-hidden="true"
    />

    <!-- Sidebar - hidden on mobile unless overlay is active -->
    <div
      :class="[
        'md:relative md:flex md:flex-shrink-0',
        isMobileOverlay ? 'fixed inset-y-0 left-0 z-40 flex' : 'hidden md:flex',
      ]"
    >
      <SidebarNav :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />
    </div>

    <!-- Main content -->
    <div class="flex flex-1 flex-col overflow-hidden min-w-0">
      <TopBar @toggle-sidebar="toggleSidebar" />
      <BreadcrumbNav />

      <main id="main-content" class="flex-1 overflow-y-auto p-6 pb-20 md:pb-6" role="main" aria-label="Hauptinhalt">
        <RouterView v-slot="{ Component, route }">
          <Transition :name="transitionName" mode="out-in">
            <div :key="route.path" class="page-wrapper">
              <component :is="Component" />
            </div>
          </Transition>
        </RouterView>
      </main>
    </div>

    <!-- Mobile Bottom Navigation (visible only on mobile) -->
    <MobileBottomNav />
  </div>
</template>
