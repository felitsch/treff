<script setup>
import { ref } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import SidebarNav from './SidebarNav.vue'
import TopBar from './TopBar.vue'

const sidebarCollapsed = ref(false)

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-treff-light dark:bg-treff-dark">
    <!-- Sidebar -->
    <SidebarNav :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />

    <!-- Main content -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <TopBar @toggle-sidebar="toggleSidebar" />

      <main class="flex-1 overflow-y-auto p-6">
        <RouterView />
      </main>
    </div>
  </div>
</template>
