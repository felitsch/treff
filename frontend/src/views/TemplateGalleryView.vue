<script setup>
/**
 * TemplateGalleryView.vue — Visual template gallery with category/format/country filters.
 *
 * Feature #242: Template-Galerie mit Kategorie-Filter
 * - Grid layout with visual template thumbnails (TemplateCard)
 * - Filter sidebar: Kategorie, Format, Land as checkbox groups
 * - Search field with real-time filtering
 * - Template count per filter category
 * - Favorite toggle with persistent backend storage
 * - Responsive: 4 cols desktop, 3 tablet, 2 mobile
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import TemplateCard from '@/components/templates/TemplateCard.vue'
import TemplatePreviewModal from '@/components/templates/TemplatePreviewModal.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const router = useRouter()
const toast = useToast()

// ─── Preview modal state ──────────────────────────────────────────
const showPreviewModal = ref(false)
const previewTemplate = ref(null)

// ─── State ────────────────────────────────────────────────────────
const loading = ref(true)
const templates = ref([])
const favoriteIds = ref(new Set())
const searchQuery = ref('')
const showMobileSidebar = ref(false)

// Filters (checkbox multi-select)
const selectedCategories = ref([])
const selectedFormats = ref([])
const selectedCountries = ref([])
const showFavoritesOnly = ref(false)

// ─── Category definitions ─────────────────────────────────────────
const categories = {
  laender_spotlight: { label: 'Laender-Spotlight', icon: 'globe', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' },
  erfahrungsberichte: { label: 'Erfahrungsberichte', icon: 'chat-bubble', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300' },
  infografiken: { label: 'Infografiken', icon: 'chart-bar', color: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' },
  fristen_cta: { label: 'Fristen & CTA', icon: 'clock', color: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' },
  tipps_tricks: { label: 'Tipps & Tricks', icon: 'light-bulb', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' },
  faq: { label: 'FAQ', icon: 'question-mark-circle', color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300' },
  foto_posts: { label: 'Foto-Posts', icon: 'camera', color: 'bg-pink-100 text-pink-700 dark:bg-pink-900 dark:text-pink-300' },
  reel_tiktok_thumbnails: { label: 'Reel/TikTok', icon: 'film', color: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300' },
  story_posts: { label: 'Story-Posts', icon: 'device-mobile', color: 'bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300' },
  story_teaser: { label: 'Story-Teaser', icon: 'arrow-right', color: 'bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900 dark:text-fuchsia-300' },
  story_series: { label: 'Story-Serien', icon: 'book-open', color: 'bg-violet-100 text-violet-700 dark:bg-violet-900 dark:text-violet-300' },
}

const platformLabels = {
  feed_square: { label: '1:1 Feed', icon: 'square-2-stack', dim: '1080x1080' },
  feed_portrait: { label: '4:5 Portrait', icon: 'device-mobile', dim: '1080x1350' },
  story: { label: '9:16 Story', icon: 'device-mobile', dim: '1080x1920' },
  tiktok: { label: '9:16 TikTok', icon: 'musical-note', dim: '1080x1920' },
}

const countryOptions = {
  usa: { label: 'USA', flag: '\u{1F1FA}\u{1F1F8}' },
  canada: { label: 'Kanada', flag: '\u{1F1E8}\u{1F1E6}' },
  australia: { label: 'Australien', flag: '\u{1F1E6}\u{1F1FA}' },
  newzealand: { label: 'Neuseeland', flag: '\u{1F1F3}\u{1F1FF}' },
  ireland: { label: 'Irland', flag: '\u{1F1EE}\u{1F1EA}' },
}

const countryFlags = {
  usa: '\u{1F1FA}\u{1F1F8}',
  canada: '\u{1F1E8}\u{1F1E6}',
  australia: '\u{1F1E6}\u{1F1FA}',
  newzealand: '\u{1F1F3}\u{1F1FF}',
  ireland: '\u{1F1EE}\u{1F1EA}',
}

// ─── Computed: Available filter values from data ──────────────────
const availableCategories = computed(() => {
  const cats = [...new Set(templates.value.map(t => t.category))]
  return cats.filter(c => categories[c]).sort()
})

const availableFormats = computed(() => {
  const fmts = [...new Set(templates.value.map(t => t.platform_format))]
  return fmts.filter(f => platformLabels[f]).sort()
})

const availableCountries = computed(() => {
  const ctrs = [...new Set(templates.value.filter(t => t.country).map(t => t.country))]
  return ctrs.filter(c => countryOptions[c]).sort()
})

// ─── Computed: counts per filter category ─────────────────────────
const categoryCounts = computed(() => {
  const counts = {}
  for (const t of templates.value) {
    counts[t.category] = (counts[t.category] || 0) + 1
  }
  return counts
})

const formatCounts = computed(() => {
  const counts = {}
  for (const t of templates.value) {
    counts[t.platform_format] = (counts[t.platform_format] || 0) + 1
  }
  return counts
})

const countryCounts = computed(() => {
  const counts = {}
  for (const t of templates.value) {
    if (t.country) {
      counts[t.country] = (counts[t.country] || 0) + 1
    }
  }
  return counts
})

// ─── Computed: Filtered templates ─────────────────────────────────
const filteredTemplates = computed(() => {
  let result = templates.value

  // Search
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    result = result.filter(t =>
      t.name.toLowerCase().includes(q) ||
      (categories[t.category]?.label || '').toLowerCase().includes(q)
    )
  }

  // Category filter
  if (selectedCategories.value.length > 0) {
    result = result.filter(t => selectedCategories.value.includes(t.category))
  }

  // Format filter
  if (selectedFormats.value.length > 0) {
    result = result.filter(t => selectedFormats.value.includes(t.platform_format))
  }

  // Country filter
  if (selectedCountries.value.length > 0) {
    result = result.filter(t => selectedCountries.value.includes(t.country))
  }

  // Favorites only
  if (showFavoritesOnly.value) {
    result = result.filter(t => favoriteIds.value.has(t.id))
  }

  return result
})

// Total and filtered counts
const totalCount = computed(() => templates.value.length)
const filteredCount = computed(() => filteredTemplates.value.length)
const activeFilterCount = computed(() =>
  selectedCategories.value.length + selectedFormats.value.length + selectedCountries.value.length + (showFavoritesOnly.value ? 1 : 0)
)

// ─── Data fetching ────────────────────────────────────────────────
async function fetchTemplates() {
  loading.value = true
  try {
    const res = await api.get('/api/templates')
    templates.value = res.data
  } catch (err) {
    console.error('Failed to fetch templates:', err)
  } finally {
    loading.value = false
  }
}

async function fetchFavorites() {
  try {
    const res = await api.get('/api/template-favorites')
    favoriteIds.value = new Set(res.data.favorite_template_ids || [])
  } catch (err) {
    console.error('Failed to fetch favorites:', err)
  }
}

async function toggleFavorite(templateId) {
  const wasFav = favoriteIds.value.has(templateId)
  // Optimistic update
  if (wasFav) {
    favoriteIds.value.delete(templateId)
  } else {
    favoriteIds.value.add(templateId)
  }
  // Force reactivity
  favoriteIds.value = new Set(favoriteIds.value)

  try {
    await api.post(`/api/template-favorites/${templateId}`)
    toast.success(wasFav ? 'Favorit entfernt' : 'Als Favorit markiert')
  } catch (err) {
    // Revert on error
    if (wasFav) {
      favoriteIds.value.add(templateId)
    } else {
      favoriteIds.value.delete(templateId)
    }
    favoriteIds.value = new Set(favoriteIds.value)
  }
}

function clearFilters() {
  selectedCategories.value = []
  selectedFormats.value = []
  selectedCountries.value = []
  showFavoritesOnly.value = false
  searchQuery.value = ''
}

function selectTemplate(template) {
  // Open preview modal instead of navigating
  previewTemplate.value = template
  showPreviewModal.value = true
}

function closePreviewModal() {
  showPreviewModal.value = false
  previewTemplate.value = null
}

function navigatePreview(template) {
  previewTemplate.value = template
}

// ─── Toggle checkbox helpers ──────────────────────────────────────
function toggleCategory(cat) {
  const idx = selectedCategories.value.indexOf(cat)
  if (idx >= 0) {
    selectedCategories.value.splice(idx, 1)
  } else {
    selectedCategories.value.push(cat)
  }
}

function toggleFormat(fmt) {
  const idx = selectedFormats.value.indexOf(fmt)
  if (idx >= 0) {
    selectedFormats.value.splice(idx, 1)
  } else {
    selectedFormats.value.push(fmt)
  }
}

function toggleCountry(ctr) {
  const idx = selectedCountries.value.indexOf(ctr)
  if (idx >= 0) {
    selectedCountries.value.splice(idx, 1)
  } else {
    selectedCountries.value.push(ctr)
  }
}

// ─── Lifecycle ────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([fetchTemplates(), fetchFavorites()])
})
</script>

<template>
  <div class="min-h-screen" data-testid="template-gallery">
    <!-- Page header -->
    <div class="mb-6" data-tour="gallery-header">
      <div class="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            Template-Galerie
          </h1>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ filteredCount }} von {{ totalCount }} Templates
            <span v-if="activeFilterCount > 0" class="text-treff-blue">
              ({{ activeFilterCount }} Filter aktiv)
            </span>
          </p>
        </div>

        <!-- Mobile filter toggle -->
        <button
          class="lg:hidden inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          @click="showMobileSidebar = !showMobileSidebar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 010 2H4a1 1 0 01-1-1zm4 4a1 1 0 011-1h8a1 1 0 010 2H8a1 1 0 01-1-1zm2 4a1 1 0 011-1h4a1 1 0 010 2h-4a1 1 0 01-1-1z" />
          </svg>
          Filter
          <span v-if="activeFilterCount > 0" class="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-treff-blue rounded-full">
            {{ activeFilterCount }}
          </span>
        </button>
      </div>

      <!-- Search bar -->
      <div class="mt-4 relative" data-tour="gallery-search">
        <svg xmlns="http://www.w3.org/2000/svg" class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Template suchen..."
          class="w-full pl-10 pr-10 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-treff-blue focus:border-treff-blue transition-colors"
          data-testid="search-input"
        />
        <button
          v-if="searchQuery"
          @click="searchQuery = ''"
          class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          aria-label="Suche leeren"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Main layout: sidebar + grid -->
    <div class="flex gap-6">

      <!-- ═══ Filter Sidebar ═══ -->
      <aside
        :class="[
          'shrink-0 w-64 lg:block',
          showMobileSidebar ? 'block' : 'hidden',
        ]"
        data-tour="gallery-filters"
        data-testid="filter-sidebar"
      >
        <div class="sticky top-4 space-y-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">

          <!-- Clear all filters -->
          <div v-if="activeFilterCount > 0" class="flex justify-between items-center">
            <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Filter</span>
            <button
              @click="clearFilters"
              class="text-xs text-treff-blue hover:underline font-medium"
              data-testid="clear-filters-btn"
            >
              Alle zuruecksetzen
            </button>
          </div>

          <!-- Favorites toggle -->
          <div>
            <label class="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                v-model="showFavoritesOnly"
                class="w-4 h-4 rounded border-gray-300 text-yellow-500 focus:ring-yellow-500"
                data-testid="favorites-filter"
              />
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-yellow-600 dark:group-hover:text-yellow-400 transition-colors">
                Nur Favoriten
              </span>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4 text-yellow-400">
                <path d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
              </svg>
            </label>
          </div>

          <!-- Divider -->
          <hr class="border-gray-200 dark:border-gray-700" />

          <!-- Kategorie -->
          <div>
            <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
              Kategorie
            </h3>
            <div class="space-y-1.5 max-h-72 overflow-y-auto">
              <label
                v-for="cat in availableCategories"
                :key="cat"
                class="flex items-center gap-2 cursor-pointer group"
              >
                <input
                  type="checkbox"
                  :checked="selectedCategories.includes(cat)"
                  @change="toggleCategory(cat)"
                  class="w-4 h-4 rounded border-gray-300 text-treff-blue focus:ring-treff-blue"
                />
                <span class="text-sm text-gray-700 dark:text-gray-300 group-hover:text-treff-blue transition-colors flex-1 truncate inline-flex items-center gap-1">
                  <AppIcon :name="categories[cat]?.icon || 'document-text'" class="w-4 h-4 inline-block" /> {{ categories[cat]?.label || cat }}
                </span>
                <span class="text-xs text-gray-400 dark:text-gray-500 font-medium">
                  {{ categoryCounts[cat] || 0 }}
                </span>
              </label>
            </div>
          </div>

          <!-- Divider -->
          <hr class="border-gray-200 dark:border-gray-700" />

          <!-- Format -->
          <div>
            <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
              Format
            </h3>
            <div class="space-y-1.5">
              <label
                v-for="fmt in availableFormats"
                :key="fmt"
                class="flex items-center gap-2 cursor-pointer group"
              >
                <input
                  type="checkbox"
                  :checked="selectedFormats.includes(fmt)"
                  @change="toggleFormat(fmt)"
                  class="w-4 h-4 rounded border-gray-300 text-treff-blue focus:ring-treff-blue"
                />
                <span class="text-sm text-gray-700 dark:text-gray-300 group-hover:text-treff-blue transition-colors flex-1 inline-flex items-center gap-1">
                  <AppIcon :name="platformLabels[fmt]?.icon || 'document-text'" class="w-4 h-4 inline-block" /> {{ platformLabels[fmt]?.label || fmt }}
                  <span class="text-xs text-gray-400">({{ platformLabels[fmt]?.dim }})</span>
                </span>
                <span class="text-xs text-gray-400 dark:text-gray-500 font-medium">
                  {{ formatCounts[fmt] || 0 }}
                </span>
              </label>
            </div>
          </div>

          <!-- Divider -->
          <hr class="border-gray-200 dark:border-gray-700" />

          <!-- Land -->
          <div>
            <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
              Land
            </h3>
            <div class="space-y-1.5">
              <label
                v-for="ctr in availableCountries"
                :key="ctr"
                class="flex items-center gap-2 cursor-pointer group"
              >
                <input
                  type="checkbox"
                  :checked="selectedCountries.includes(ctr)"
                  @change="toggleCountry(ctr)"
                  class="w-4 h-4 rounded border-gray-300 text-treff-blue focus:ring-treff-blue"
                />
                <span class="text-sm text-gray-700 dark:text-gray-300 group-hover:text-treff-blue transition-colors flex-1">
                  {{ countryOptions[ctr]?.flag }} {{ countryOptions[ctr]?.label || ctr }}
                </span>
                <span class="text-xs text-gray-400 dark:text-gray-500 font-medium">
                  {{ countryCounts[ctr] || 0 }}
                </span>
              </label>
            </div>
          </div>
        </div>
      </aside>

      <!-- ═══ Template Grid ═══ -->
      <main class="flex-1 min-w-0">

        <!-- Loading skeleton -->
        <div v-if="loading" class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
          <div v-for="i in 8" :key="i" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden animate-pulse">
            <div class="aspect-square bg-gray-200 dark:bg-gray-700" />
            <div class="p-3 space-y-2">
              <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
              <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <EmptyState
          v-else-if="filteredTemplates.length === 0 && !loading"
          icon="document-text"
          :title="searchQuery || activeFilterCount > 0 ? 'Keine Templates gefunden' : 'Noch keine Templates'"
          :description="searchQuery || activeFilterCount > 0
            ? 'Versuche andere Suchbegriffe oder entferne Filter.'
            : 'Es wurden noch keine Templates erstellt.'"
          :action-label="activeFilterCount > 0 ? 'Filter zuruecksetzen' : 'Template erstellen'"
          :action-to="activeFilterCount > 0 ? undefined : '/library/templates'"
          @action="activeFilterCount > 0 ? clearFilters() : null"
          data-testid="empty-state"
        />

        <!-- Template grid -->
        <div
          v-else
          class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4"
          data-testid="template-grid"
          data-tour="gallery-grid"
        >
          <TemplateCard
            v-for="t in filteredTemplates"
            :key="t.id"
            :template="t"
            :is-favorite="favoriteIds.has(t.id)"
            :categories="categories"
            :platform-labels="platformLabels"
            :country-flags="countryFlags"
            @toggle-favorite="toggleFavorite"
            @select="selectTemplate"
          />
        </div>
      </main>
    </div>

    <!-- Template Preview Modal (Feature #243) -->
    <TemplatePreviewModal
      :show="showPreviewModal"
      :template="previewTemplate"
      :is-favorite="previewTemplate ? favoriteIds.has(previewTemplate.id) : false"
      :template-list="filteredTemplates"
      :categories="categories"
      :platform-labels="platformLabels"
      :country-flags="countryFlags"
      @close="closePreviewModal"
      @toggle-favorite="toggleFavorite"
      @navigate="navigatePreview"
    />
  </div>
</template>
