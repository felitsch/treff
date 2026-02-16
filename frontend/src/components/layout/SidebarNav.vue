<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  collapsed: Boolean,
})

defineEmits(['toggle'])

const route = useRoute()

const navGroups = [
  {
    label: 'Home',
    key: 'home',
    items: [
      { name: 'Home', path: '/home', icon: '📊' },
    ],
  },
  {
    label: 'Erstellen',
    key: 'create',
    items: [
      { name: 'Erstellen', path: '/create', icon: '✏️' },
      { name: 'Quick Post', path: '/create/quick', icon: '⚡' },
      { name: 'Entwuerfe', path: '/create/drafts', icon: '💾' },
      { name: 'Kampagne', path: '/create/campaign', icon: '📅' },
    ],
  },
  {
    label: 'Kalender',
    key: 'calendar',
    items: [
      { name: 'Kalender', path: '/calendar', icon: '📅' },
      { name: 'Wochenplaner', path: '/calendar/week-planner', icon: '🗓️' },
      { name: 'Story-Arcs', path: '/calendar/story-arcs', icon: '📖' },
      { name: 'Formate', path: '/calendar/recurring-formats', icon: '🔄' },
    ],
  },
  {
    label: 'Bibliothek',
    key: 'library',
    items: [
      { name: 'Templates', path: '/library/templates', icon: '📄' },
      { name: 'Galerie', path: '/library/template-gallery', icon: '🎨' },
      { name: 'Editor', path: '/library/template-editor', icon: '✏️' },
      { name: 'Assets', path: '/library/assets', icon: '🖼️' },
      { name: 'History', path: '/library/history', icon: '📋' },
    ],
  },
  {
    label: 'Schueler',
    key: 'students',
    items: [
      { name: 'Schueler', path: '/students', icon: '🎓' },
    ],
  },
  {
    label: 'Video-Tools',
    key: 'video',
    items: [
      { name: 'Thumbnails', path: '/video/thumbnails', icon: '🎬' },
      { name: 'Video-Overlay', path: '/video/overlays', icon: '🎞️' },
      { name: 'Video-Schnitt', path: '/video/composer', icon: '✂️' },
      { name: 'Video-Branding', path: '/video/templates', icon: '🏷️' },
      { name: 'Video-Export', path: '/video/export', icon: '📤' },
      { name: 'Audio-Mixer', path: '/video/audio-mixer', icon: '🎵' },
      { name: 'Script-Generator', path: '/video/script-generator', icon: '📝' },
    ],
  },
  {
    label: 'KI-Tools',
    key: 'ai',
    items: [
      { name: 'Prompt-History', path: '/ai/prompt-history', icon: '🧠' },
    ],
  },
  {
    label: 'Analyse & Einstellungen',
    key: 'analytics',
    items: [
      { name: 'Analytics', path: '/analytics', icon: '📈' },
      { name: 'Settings', path: '/settings', icon: '⚙️' },
      { name: 'Design-System', path: '/design-system', icon: '🎨' },
    ],
  },
]

// Track expanded state of each group
const expandedGroups = ref({})

// Initialize all groups as expanded (desktop default)
const initGroups = (allExpanded) => {
  const state = {}
  navGroups.forEach((group) => {
    state[group.key] = allExpanded
  })
  return state
}

// Detect mobile breakpoint
const isMobile = ref(false)

const checkMobile = () => {
  const wasMobile = isMobile.value
  isMobile.value = window.innerWidth < 768
  // When crossing the mobile/desktop boundary, reset group states
  if (wasMobile !== isMobile.value) {
    expandedGroups.value = initGroups(!isMobile.value)
    expandActiveGroup()
  }
}

// Auto-expand group containing active route
const expandActiveGroup = () => {
  navGroups.forEach((group) => {
    if (group.items.some((item) => route.path.startsWith(item.path))) {
      expandedGroups.value[group.key] = true
    }
  })
}

onMounted(() => {
  isMobile.value = window.innerWidth < 768
  // On mobile: groups collapsed by default; on desktop: all expanded
  expandedGroups.value = initGroups(!isMobile.value)
  // Always expand the group containing the active route
  expandActiveGroup()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

// When route changes, ensure the active group is expanded
watch(() => route.path, () => {
  expandActiveGroup()
})

const toggleGroup = (key) => {
  expandedGroups.value[key] = !expandedGroups.value[key]
}

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
    <nav class="flex-1 overflow-y-auto py-2" role="navigation" aria-label="Hauptnavigation" data-tour="sidebar">
      <!-- Collapsed mode: flat icon list -->
      <template v-if="collapsed">
        <ul class="space-y-1 px-2">
          <template v-for="group in navGroups" :key="group.key">
            <li v-for="item in group.items" :key="item.path">
              <router-link
                :to="item.path"
                :class="[
                  'flex items-center justify-center rounded-lg px-3 py-2.5 text-sm font-medium transition-base focus-ring',
                  isActive(item.path)
                    ? 'bg-treff-blue/10 text-treff-blue dark:bg-treff-blue/20'
                    : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800',
                ]"
                :aria-label="item.name"
                :title="item.name"
                :data-tour="item.path === '/create' || item.path === '/create/quick' ? 'create-post' : item.path === '/library/templates' ? 'templates' : undefined"
              >
                <span class="text-lg">{{ item.icon }}</span>
              </router-link>
            </li>
          </template>
        </ul>
      </template>

      <!-- Expanded mode: grouped navigation -->
      <template v-else>
        <div v-for="(group, groupIndex) in navGroups" :key="group.key" :class="groupIndex > 0 ? 'mt-1' : ''">
          <!-- Group header / divider -->
          <button
            @click="toggleGroup(group.key)"
            class="flex items-center justify-between w-full px-4 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors cursor-pointer select-none"
            :aria-expanded="expandedGroups[group.key]"
            :aria-controls="'nav-group-' + group.key"
          >
            <span>{{ group.label }}</span>
            <svg
              :class="[
                'w-3 h-3 transition-transform duration-200',
                expandedGroups[group.key] ? 'rotate-0' : '-rotate-90',
              ]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Group items (collapsible) -->
          <ul
            :id="'nav-group-' + group.key"
            :class="[
              'overflow-hidden transition-all duration-200 px-2',
              expandedGroups[group.key] ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0 pointer-events-none',
            ]"
          >
            <li v-for="item in group.items" :key="item.path">
              <router-link
                :to="item.path"
                :class="[
                  'flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-base focus-ring',
                  isActive(item.path)
                    ? 'bg-treff-blue/10 text-treff-blue dark:bg-treff-blue/20'
                    : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800',
                ]"
                :aria-label="item.name"
                :data-tour="item.path === '/create' || item.path === '/create/quick' ? 'create-post' : item.path === '/library/templates' ? 'templates' : undefined"
              >
                <span class="text-lg mr-3">{{ item.icon }}</span>
                <span>{{ item.name }}</span>
              </router-link>
            </li>
          </ul>

          <!-- Divider between groups (not after last) -->
          <div
            v-if="groupIndex < navGroups.length - 1 && !expandedGroups[group.key]"
            class="mx-4 mt-1 border-b border-gray-100 dark:border-gray-800"
          />
        </div>
      </template>
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
