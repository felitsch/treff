<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import SidebarNav from './SidebarNav.vue'
import TopBar from './TopBar.vue'
import { useReminders } from '@/composables/useReminders'

const sidebarCollapsed = ref(false)
const isMobileOverlay = ref(false)
const { startPolling, stopPolling } = useReminders()

const TABLET_BREAKPOINT = 1024

const toggleSidebar = () => {
  if (window.innerWidth < 768) {
    // Mobile: toggle overlay sidebar
    isMobileOverlay.value = !isMobileOverlay.value
  } else {
    sidebarCollapsed.value = !sidebarCollapsed.value
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
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  stopPolling()
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-treff-light dark:bg-treff-dark">
    <!-- Mobile overlay backdrop -->
    <div
      v-if="isMobileOverlay"
      class="fixed inset-0 z-30 bg-black/50 md:hidden"
      @click="closeMobileOverlay"
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

      <main class="flex-1 overflow-y-auto p-6">
        <RouterView />
      </main>
    </div>
  </div>
</template>
