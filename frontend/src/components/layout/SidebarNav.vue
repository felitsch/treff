<script setup>
import { ref, onMounted, onUnmounted, watch, markRaw } from 'vue'
import { useRoute } from 'vue-router'
import {
  ChartBarIcon,
  PencilSquareIcon,
  BoltIcon,
  DocumentIcon,
  CalendarDaysIcon,
  CalendarIcon,
  BookOpenIcon,
  ArrowPathIcon,
  PhotoIcon,
  DocumentTextIcon,
  ClipboardDocumentListIcon,
  AcademicCapIcon,
  FilmIcon,
  VideoCameraIcon,
  ScissorsIcon,
  TagIcon,
  ArrowUpTrayIcon,
  MusicalNoteIcon,
  SparklesIcon,
  PresentationChartLineIcon,
  Cog6ToothIcon,
  PaintBrushIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from '@heroicons/vue/24/outline'

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
      { name: 'Home', path: '/home', icon: markRaw(ChartBarIcon) },
    ],
  },
  {
    label: 'Erstellen',
    key: 'create',
    items: [
      { name: 'Erstellen', path: '/create', icon: markRaw(PencilSquareIcon) },
      { name: 'Quick Post', path: '/create/quick', icon: markRaw(BoltIcon) },
      { name: 'Entwürfe', path: '/create/drafts', icon: markRaw(DocumentIcon) },
      { name: 'Kampagne', path: '/create/campaign', icon: markRaw(CalendarDaysIcon) },
    ],
  },
  {
    label: 'Kalender',
    key: 'calendar',
    items: [
      { name: 'Kalender', path: '/calendar', icon: markRaw(CalendarIcon) },
      { name: 'Wochenplaner', path: '/calendar/week-planner', icon: markRaw(CalendarDaysIcon) },
      { name: 'Story-Arcs', path: '/calendar/story-arcs', icon: markRaw(BookOpenIcon) },
      { name: 'Formate', path: '/calendar/recurring-formats', icon: markRaw(ArrowPathIcon) },
    ],
  },
  {
    label: 'Bibliothek',
    key: 'library',
    items: [
      { name: 'Assets', path: '/library/assets', icon: markRaw(PhotoIcon) },
      { name: 'Templates', path: '/library/templates', icon: markRaw(DocumentTextIcon) },
      { name: 'Posts', path: '/library/history', icon: markRaw(ClipboardDocumentListIcon) },
    ],
  },
  {
    label: 'Schüler',
    key: 'students',
    items: [
      { name: 'Schüler', path: '/students', icon: markRaw(AcademicCapIcon) },
    ],
  },
  {
    label: 'Video-Tools',
    key: 'video',
    items: [
      { name: 'Thumbnails', path: '/video/thumbnails', icon: markRaw(FilmIcon) },
      { name: 'Video-Overlay', path: '/video/overlays', icon: markRaw(VideoCameraIcon) },
      { name: 'Video-Schnitt', path: '/video/composer', icon: markRaw(ScissorsIcon) },
      { name: 'Video-Branding', path: '/video/templates', icon: markRaw(TagIcon) },
      { name: 'Video-Export', path: '/video/export', icon: markRaw(ArrowUpTrayIcon) },
      { name: 'Audio-Mixer', path: '/video/audio-mixer', icon: markRaw(MusicalNoteIcon) },
      { name: 'Script-Generator', path: '/video/script-generator', icon: markRaw(DocumentTextIcon) },
    ],
  },
  {
    label: 'KI-Tools',
    key: 'ai',
    items: [
      { name: 'Prompt-History', path: '/ai/prompt-history', icon: markRaw(SparklesIcon) },
    ],
  },
  {
    label: 'Analyse & Einstellungen',
    key: 'analytics',
    items: [
      { name: 'Analytics', path: '/analytics', icon: markRaw(PresentationChartLineIcon) },
      { name: 'Settings', path: '/settings', icon: markRaw(Cog6ToothIcon) },
      { name: 'Design-System', path: '/design-system', icon: markRaw(PaintBrushIcon) },
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
    aria-label="Seitenleiste"
  >
    <!-- Logo -->
    <div class="flex h-16 items-center justify-center border-b border-gray-200 dark:border-gray-700 px-4">
      <span v-if="!collapsed" class="text-xl font-bold text-treff-blue">TREFF</span>
      <span v-else class="text-xl font-bold text-treff-blue">T</span>
    </div>

    <!-- Prominent Create button -->
    <div class="px-3 py-3 border-b border-gray-200 dark:border-gray-700">
      <router-link
        to="/create"
        :class="[
          'flex items-center justify-center gap-2 rounded-xl font-semibold transition-all',
          'bg-treff-blue text-white hover:bg-treff-blue/90 shadow-sm hover:shadow-md',
          collapsed ? 'w-10 h-10 mx-auto text-lg' : 'w-full py-2.5 px-4 text-sm',
        ]"
        aria-label="Neuen Content erstellen"
        data-testid="sidebar-create-button"
      >
        <svg class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        <span v-if="!collapsed">Erstellen</span>
      </router-link>
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
                <component :is="item.icon" class="w-5 h-5" />
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
                <component :is="item.icon" class="w-5 h-5 mr-3 shrink-0" />
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
      <component :is="collapsed ? ChevronRightIcon : ChevronLeftIcon" class="w-5 h-5" />
    </button>
  </aside>
</template>
