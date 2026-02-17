<script setup>
/**
 * LibraryView.vue — Unified Library Hub (Bibliothek)
 *
 * Combines Assets, Templates, and Posts into a single tabbed interface.
 * Features:
 *  - 3 main tabs: Assets, Templates, Posts (History)
 *  - Cross-tab unified search bar
 *  - URL-driven tab state (/library?tab=assets, /library/templates, etc.)
 *  - Responsive horizontal-scroll tabs on mobile
 *  - Sub-navigation for Template Gallery and Editor within Templates tab
 *  - Maintains all existing functionality from individual views
 *
 * @see AssetsView.vue — Assets tab content
 * @see TemplatesView.vue — Templates tab content
 * @see HistoryView.vue — Posts tab content (now using PostPreviewCards)
 */
import { ref, computed, watch, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// ── Unified search (provided to child views) ──────────────────────
const globalSearchQuery = ref('')
let searchDebounce = null

function onSearchInput(value) {
  globalSearchQuery.value = value
  clearTimeout(searchDebounce)
  searchDebounce = setTimeout(function() {
    // The child views will react to this via provide/inject
  }, 300)
}

function clearSearch() {
  globalSearchQuery.value = ''
}

// Provide search query to child components
provide('librarySearch', globalSearchQuery)

// ── Tab definitions ──────────────────────────────────────────────
const mainTabs = [
  {
    key: 'assets',
    label: 'Assets',
    icon: '&#x1F5BC;',
    iconLabel: 'Bild',
    path: '/library/assets',
    description: 'Fotos, Videos & Medien',
    matchPaths: ['assets'],
  },
  {
    key: 'templates',
    label: 'Templates',
    icon: '&#x1F4C4;',
    iconLabel: 'Dokument',
    path: '/library/templates',
    description: 'Vorlagen & Designs',
    matchPaths: ['templates', 'template-gallery', 'template-editor'],
  },
  {
    key: 'history',
    label: 'Posts',
    icon: '&#x1F4CB;',
    iconLabel: 'Liste',
    path: '/library/history',
    description: 'Post-History & Archiv',
    matchPaths: ['history'],
  },
]

// ── Template sub-tabs ──────────────────────────────────────────
const templateSubTabs = [
  { key: 'templates', label: 'Uebersicht', path: '/library/templates' },
  { key: 'template-gallery', label: 'Galerie', path: '/library/template-gallery' },
  { key: 'template-editor', label: 'Editor', path: '/library/template-editor' },
]

// ── Active tab logic ──────────────────────────────────────────
const currentChild = computed(function() {
  var parts = route.path.split('/library/')
  return parts[1] || 'templates'
})

const activeMainTab = computed(function() {
  var child = currentChild.value
  for (var i = 0; i < mainTabs.length; i++) {
    if (mainTabs[i].matchPaths.indexOf(child) !== -1) {
      return mainTabs[i].key
    }
  }
  return 'templates'
})

const isTemplateTab = computed(function() {
  return activeMainTab.value === 'templates'
})

const activeSubTab = computed(function() {
  var child = currentChild.value
  if (child === 'template-gallery') return 'template-gallery'
  if (child === 'template-editor') return 'template-editor'
  return 'templates'
})

// ── Navigation ──────────────────────────────────────────────
function switchMainTab(tab) {
  router.push(tab.path)
}

function switchSubTab(subTab) {
  router.push(subTab.path)
}

// ── Search placeholder changes with active tab ──────────────
const searchPlaceholder = computed(function() {
  switch (activeMainTab.value) {
    case 'assets': return 'Assets durchsuchen (Dateiname, Tags, Typ...)'
    case 'templates': return 'Templates durchsuchen (Name, Kategorie, Land...)'
    case 'history': return 'Posts durchsuchen (Titel, Kategorie, Status...)'
    default: return 'Bibliothek durchsuchen...'
  }
})

// ── Tab item counts (will be updated by child views via provide/inject) ──
const assetCount = ref(null)
const templateCount = ref(null)
const postCount = ref(null)

provide('libraryAssetCount', assetCount)
provide('libraryTemplateCount', templateCount)
provide('libraryPostCount', postCount)

function getTabCount(key) {
  switch (key) {
    case 'assets': return assetCount.value
    case 'templates': return templateCount.value
    case 'history': return postCount.value
    default: return null
  }
}
</script>

<template>
  <div data-tour="library-hub" data-testid="library-view">
    <!-- ═══ Library Header ═══ -->
    <div class="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
      <!-- Title + Search row -->
      <div class="px-4 sm:px-6 pt-4 pb-3">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 class="text-xl font-bold text-gray-900 dark:text-white">Bibliothek</h1>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Assets, Templates & Posts an einem Ort</p>
          </div>

          <!-- Unified search bar -->
          <div class="relative w-full sm:w-80" data-testid="library-search">
            <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
              </svg>
            </div>
            <input
              type="text"
              :value="globalSearchQuery"
              @input="onSearchInput($event.target.value)"
              :placeholder="searchPlaceholder"
              class="w-full pl-9 pr-8 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-[#3B7AB1]/30 focus:border-[#3B7AB1] transition-colors"
              data-testid="library-search-input"
            />
            <button
              v-if="globalSearchQuery"
              @click="clearSearch"
              class="absolute inset-y-0 right-0 flex items-center pr-2.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              aria-label="Suche leeren"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Main tabs (responsive horizontal scroll on mobile) -->
      <div class="px-4 sm:px-6">
        <nav
          class="flex gap-1 -mb-px overflow-x-auto scrollbar-hide"
          aria-label="Bibliothek-Tabs"
          data-testid="library-main-tabs"
        >
          <button
            v-for="tab in mainTabs"
            :key="tab.key"
            @click="switchMainTab(tab)"
            :class="[
              'flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-all whitespace-nowrap flex-shrink-0',
              activeMainTab === tab.key
                ? 'border-[#3B7AB1] text-[#3B7AB1] dark:text-blue-400 dark:border-blue-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300',
            ]"
            :aria-selected="activeMainTab === tab.key"
            role="tab"
            :data-testid="'library-tab-' + tab.key"
          >
            <span class="text-base" v-html="tab.icon"></span>
            <span>{{ tab.label }}</span>
            <span
              v-if="getTabCount(tab.key) !== null"
              class="ml-1 px-1.5 py-0.5 text-[10px] font-semibold rounded-full"
              :class="activeMainTab === tab.key
                ? 'bg-[#3B7AB1]/10 text-[#3B7AB1] dark:bg-blue-400/10 dark:text-blue-400'
                : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'"
            >
              {{ getTabCount(tab.key) }}
            </span>
          </button>
        </nav>
      </div>

      <!-- Template sub-tabs (only visible when Templates main tab is active) -->
      <div
        v-if="isTemplateTab"
        class="px-4 sm:px-6 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-100 dark:border-gray-800"
        data-testid="library-template-subtabs"
      >
        <nav class="flex gap-1 overflow-x-auto scrollbar-hide" aria-label="Template Sub-Tabs">
          <button
            v-for="subTab in templateSubTabs"
            :key="subTab.key"
            @click="switchSubTab(subTab)"
            :class="[
              'px-3 py-1.5 text-xs font-medium rounded-lg transition-colors whitespace-nowrap my-1.5 flex-shrink-0',
              activeSubTab === subTab.key
                ? 'bg-white dark:bg-gray-700 text-[#3B7AB1] dark:text-blue-400 shadow-sm'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-white/60 dark:hover:bg-gray-700/50',
            ]"
            :data-testid="'library-subtab-' + subTab.key"
          >
            {{ subTab.label }}
          </button>
        </nav>
      </div>
    </div>

    <!-- ═══ Child view content ═══ -->
    <router-view v-slot="{ Component, route: childRoute }">
      <Transition name="page-slide" mode="out-in">
        <div :key="childRoute.path">
          <component :is="Component" />
        </div>
      </Transition>
    </router-view>
  </div>
</template>

<style scoped>
/* Hide scrollbar on mobile tab navigation */
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
