<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/utils/api'

const loading = ref(true)
const error = ref(null)
const templates = ref([])
const selectedCategory = ref('')
const selectedPlatform = ref('')

// Category definitions with German labels and colors
const categories = {
  laender_spotlight: { label: 'Laender-Spotlight', icon: '🌍', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' },
  erfahrungsberichte: { label: 'Erfahrungsberichte', icon: '💬', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300' },
  infografiken: { label: 'Infografiken', icon: '📊', color: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' },
  fristen_cta: { label: 'Fristen & CTA', icon: '⏰', color: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' },
  tipps_tricks: { label: 'Tipps & Tricks', icon: '💡', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' },
  faq: { label: 'FAQ', icon: '❓', color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300' },
  foto_posts: { label: 'Foto-Posts', icon: '📸', color: 'bg-pink-100 text-pink-700 dark:bg-pink-900 dark:text-pink-300' },
  reel_tiktok_thumbnails: { label: 'Reel/TikTok', icon: '🎬', color: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300' },
  story_posts: { label: 'Story-Posts', icon: '📱', color: 'bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300' },
}

// Platform format labels
const platformLabels = {
  feed_square: { label: '1:1 Feed', icon: '⬜', dim: '1080x1080' },
  feed_portrait: { label: '4:5 Portrait', icon: '📱', dim: '1080x1350' },
  story: { label: '9:16 Story', icon: '📲', dim: '1080x1920' },
  tiktok: { label: '9:16 TikTok', icon: '🎵', dim: '1080x1920' },
}

// Country flags
const countryFlags = {
  usa: '🇺🇸',
  canada: '🇨🇦',
  australia: '🇦🇺',
  newzealand: '🇳🇿',
  ireland: '🇮🇪',
}

// Unique categories from templates
const availableCategories = computed(() => {
  const cats = [...new Set(templates.value.map(t => t.category))]
  return cats.sort()
})

// Unique platforms from templates
const availablePlatforms = computed(() => {
  const plats = [...new Set(templates.value.map(t => t.platform_format))]
  return plats.sort()
})

// Filtered templates
const filteredTemplates = computed(() => {
  let result = templates.value
  if (selectedCategory.value) {
    result = result.filter(t => t.category === selectedCategory.value)
  }
  if (selectedPlatform.value) {
    result = result.filter(t => t.platform_format === selectedPlatform.value)
  }
  return result
})

// Group templates by category for display
const groupedTemplates = computed(() => {
  const groups = {}
  for (const t of filteredTemplates.value) {
    if (!groups[t.category]) {
      groups[t.category] = []
    }
    groups[t.category].push(t)
  }
  return groups
})

// Template count per category (for filter badges)
const categoryCount = computed(() => {
  const counts = {}
  for (const t of templates.value) {
    counts[t.category] = (counts[t.category] || 0) + 1
  }
  return counts
})

function getCategoryInfo(cat) {
  return categories[cat] || { label: cat, icon: '📄', color: 'bg-gray-100 text-gray-700' }
}

function getPlatformInfo(platform) {
  return platformLabels[platform] || { label: platform, icon: '📄', dim: '' }
}

function getCountryFlag(country) {
  return countryFlags[country] || ''
}

// Parse default_colors JSON safely
function parseColors(colorsStr) {
  try {
    return JSON.parse(colorsStr)
  } catch {
    return { primary: '#4C8BC2', secondary: '#FDD000', accent: '#FFFFFF', background: '#1A1A2E' }
  }
}

function clearFilters() {
  selectedCategory.value = ''
  selectedPlatform.value = ''
}

async function fetchTemplates() {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/api/templates')
    templates.value = res.data
  } catch (err) {
    console.error('Failed to load templates:', err)
    error.value = 'Templates konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchTemplates()
})
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <!-- Page Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Templates</h1>
      <p class="text-gray-500 dark:text-gray-400 mt-1">
        Waehle ein Template fuer deinen naechsten Post. Alle Templates sind fuer TREFF Sprachreisen optimiert.
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="space-y-6">
      <!-- Skeleton filter bar -->
      <div class="flex gap-3">
        <div v-for="i in 4" :key="i" class="h-10 w-28 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"></div>
      </div>
      <!-- Skeleton grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div v-for="i in 8" :key="i" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm animate-pulse">
          <div class="aspect-square bg-gray-200 dark:bg-gray-700 rounded-t-xl"></div>
          <div class="p-4 space-y-2">
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
      <p class="text-red-600 dark:text-red-400">{{ error }}</p>
      <button
        @click="fetchTemplates"
        class="mt-3 px-4 py-2 bg-red-100 dark:bg-red-800 text-red-700 dark:text-red-200 rounded-lg hover:bg-red-200 dark:hover:bg-red-700 transition-colors"
      >
        Erneut versuchen
      </button>
    </div>

    <!-- Content -->
    <div v-else class="space-y-6">
      <!-- Filter Bar -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
        <div class="flex flex-wrap items-center gap-3">
          <!-- Category Filter -->
          <div class="flex items-center gap-2">
            <label class="text-sm font-medium text-gray-600 dark:text-gray-400">Kategorie:</label>
            <select
              v-model="selectedCategory"
              class="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent"
            >
              <option value="">Alle Kategorien</option>
              <option v-for="cat in availableCategories" :key="cat" :value="cat">
                {{ getCategoryInfo(cat).icon }} {{ getCategoryInfo(cat).label }} ({{ categoryCount[cat] }})
              </option>
            </select>
          </div>

          <!-- Platform Filter -->
          <div class="flex items-center gap-2">
            <label class="text-sm font-medium text-gray-600 dark:text-gray-400">Format:</label>
            <select
              v-model="selectedPlatform"
              class="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-treff-blue focus:border-transparent"
            >
              <option value="">Alle Formate</option>
              <option v-for="plat in availablePlatforms" :key="plat" :value="plat">
                {{ getPlatformInfo(plat).icon }} {{ getPlatformInfo(plat).label }}
              </option>
            </select>
          </div>

          <!-- Clear filters -->
          <button
            v-if="selectedCategory || selectedPlatform"
            @click="clearFilters"
            class="text-sm text-gray-500 dark:text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors flex items-center gap-1"
          >
            <span>&#10005;</span> Filter zuruecksetzen
          </button>

          <!-- Result count -->
          <div class="ml-auto text-sm text-gray-500 dark:text-gray-400">
            {{ filteredTemplates.length }} von {{ templates.length }} Templates
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="filteredTemplates.length === 0" class="text-center py-16">
        <div class="text-5xl mb-4">📄</div>
        <p class="text-gray-500 dark:text-gray-400 font-medium text-lg">Keine Templates gefunden</p>
        <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">
          Versuche andere Filter oder setze sie zurueck.
        </p>
        <button
          @click="clearFilters"
          class="mt-4 px-4 py-2 bg-treff-blue text-white text-sm font-medium rounded-lg hover:bg-blue-600 transition-colors"
        >
          Filter zuruecksetzen
        </button>
      </div>

      <!-- Template Grid grouped by category -->
      <div v-for="(catTemplates, category) in groupedTemplates" :key="category" class="space-y-3">
        <!-- Category Header -->
        <div class="flex items-center gap-2">
          <span class="text-xl">{{ getCategoryInfo(category).icon }}</span>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ getCategoryInfo(category).label }}
          </h2>
          <span class="text-sm text-gray-400 dark:text-gray-500">({{ catTemplates.length }})</span>
        </div>

        <!-- Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <div
            v-for="template in catTemplates"
            :key="template.id"
            class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md hover:border-treff-blue/50 dark:hover:border-treff-blue/50 transition-all cursor-pointer group overflow-hidden"
          >
            <!-- Visual Thumbnail -->
            <div class="relative">
              <div
                class="w-full h-48 flex flex-col items-center justify-center p-4 relative overflow-hidden"
                :style="{
                  background: `linear-gradient(135deg, ${parseColors(template.default_colors).background || '#1A1A2E'} 0%, ${parseColors(template.default_colors).primary || '#4C8BC2'} 100%)`,
                }"
              >
                <!-- Template preview mockup -->
                <div class="absolute top-3 left-3">
                  <div
                    class="px-2 py-1 rounded text-[10px] font-bold tracking-wide"
                    :style="{ background: parseColors(template.default_colors).primary || '#4C8BC2', color: '#fff' }"
                  >
                    TREFF
                  </div>
                </div>

                <!-- Country flag badge -->
                <div v-if="template.is_country_themed && template.country" class="absolute top-3 right-3 text-2xl">
                  {{ getCountryFlag(template.country) }}
                </div>

                <!-- Slide count indicator -->
                <div v-if="template.slide_count > 1"
                  class="absolute top-3 bg-black/40 text-white text-xs px-2 py-1 rounded-full backdrop-blur-sm"
                  :class="template.is_country_themed && template.country ? 'right-12' : 'right-3'"
                >
                  {{ template.slide_count }} Slides
                </div>

                <!-- Mockup content lines -->
                <div class="flex flex-col items-start gap-2 w-full px-3 mt-8">
                  <div
                    class="h-4 rounded-sm w-3/4"
                    :style="{ background: parseColors(template.default_colors).primary || '#4C8BC2' }"
                  ></div>
                  <div
                    class="h-3 rounded-sm w-1/2 opacity-70"
                    :style="{ background: parseColors(template.default_colors).secondary || '#FDD000' }"
                  ></div>
                  <div class="flex flex-col gap-1.5 w-full mt-1">
                    <div class="h-2 rounded-sm w-full bg-white/20"></div>
                    <div class="h-2 rounded-sm w-5/6 bg-white/15"></div>
                    <div class="h-2 rounded-sm w-4/6 bg-white/10"></div>
                  </div>
                </div>

                <!-- CTA mockup -->
                <div class="mt-auto mb-2 self-start ml-3">
                  <div
                    class="px-3 py-1 rounded text-[10px] font-bold"
                    :style="{
                      background: parseColors(template.default_colors).secondary || '#FDD000',
                      color: parseColors(template.default_colors).background || '#1A1A2E',
                    }"
                  >
                    CTA
                  </div>
                </div>

                <!-- Hover overlay -->
                <div class="absolute inset-0 bg-treff-blue/0 group-hover:bg-treff-blue/10 transition-colors flex items-center justify-center">
                  <div class="opacity-0 group-hover:opacity-100 transition-opacity bg-white dark:bg-gray-900 text-treff-blue font-medium text-sm px-4 py-2 rounded-lg shadow-lg">
                    Vorschau
                  </div>
                </div>
              </div>
            </div>

            <!-- Template Info -->
            <div class="p-4">
              <h3 class="font-semibold text-gray-900 dark:text-white text-sm truncate group-hover:text-treff-blue transition-colors">
                {{ template.name }}
              </h3>
              <div class="flex items-center gap-2 mt-2 flex-wrap">
                <!-- Platform badge -->
                <span class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                  {{ getPlatformInfo(template.platform_format).icon }}
                  {{ getPlatformInfo(template.platform_format).label }}
                </span>
                <!-- Country badge if themed -->
                <span
                  v-if="template.is_country_themed && template.country"
                  class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300"
                >
                  {{ getCountryFlag(template.country) }}
                  {{ template.country.charAt(0).toUpperCase() + template.country.slice(1) }}
                </span>
                <!-- Default badge -->
                <span
                  v-if="template.is_default"
                  class="text-xs px-2 py-0.5 rounded-full bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-300"
                >
                  Standard
                </span>
              </div>
              <!-- Slide count info -->
              <p class="text-xs text-gray-400 dark:text-gray-500 mt-2">
                {{ template.slide_count === 1 ? 'Einzelbild' : `${template.slide_count} Slides (Carousel)` }}
                &middot; {{ getPlatformInfo(template.platform_format).dim }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
