<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/utils/api'

// State
const assets = ref([])
const loading = ref(true)
const error = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadError = ref(null)
const isDragOver = ref(false)
const searchQuery = ref('')
const selectedFilter = ref('all')
const selectedCategory = ref('all')
const selectedCountry = ref('all')
const showDeleteConfirm = ref(null)

// Upload metadata
const uploadCategory = ref('')
const uploadCountry = ref('')
const uploadTags = ref('')

// Category and Country options
const categoryOptions = [
  { value: 'logo', label: 'Logo' },
  { value: 'background', label: 'Hintergrund' },
  { value: 'photo', label: 'Foto' },
  { value: 'icon', label: 'Icon' },
  { value: 'country', label: 'Laenderbild' },
]

const countryOptions = [
  { value: 'usa', label: 'USA' },
  { value: 'kanada', label: 'Kanada' },
  { value: 'australien', label: 'Australien' },
  { value: 'neuseeland', label: 'Neuseeland' },
  { value: 'irland', label: 'Irland' },
]

// Category label helper
function categoryLabel(value) {
  const opt = categoryOptions.find(o => o.value === value)
  return opt ? opt.label : value
}

// Country label helper
function countryLabel(value) {
  const opt = countryOptions.find(o => o.value === value)
  return opt ? opt.label : value
}

// Computed
const filteredAssets = computed(() => {
  let filtered = assets.value
  if (selectedFilter.value !== 'all') {
    filtered = filtered.filter(a => a.file_type === `image/${selectedFilter.value}`)
  }
  if (selectedCategory.value !== 'all') {
    filtered = filtered.filter(a => a.category === selectedCategory.value)
  }
  if (selectedCountry.value !== 'all') {
    filtered = filtered.filter(a => a.country === selectedCountry.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    filtered = filtered.filter(a =>
      (a.original_filename || a.filename || '').toLowerCase().includes(q) ||
      (a.tags || '').toLowerCase().includes(q) ||
      (a.category || '').toLowerCase().includes(q) ||
      (a.country || '').toLowerCase().includes(q)
    )
  }
  return filtered
})

// Check if any filters are active
const hasActiveFilters = computed(() => {
  return selectedFilter.value !== 'all' || selectedCategory.value !== 'all' || selectedCountry.value !== 'all' || searchQuery.value.trim() !== ''
})

// Fetch all assets (filtering is done client-side via filteredAssets computed)
async function fetchAssets() {
  loading.value = true
  error.value = null
  try {
    const response = await api.get('/api/assets')
    assets.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Fehler beim Laden der Assets'
  } finally {
    loading.value = false
  }
}

// Upload file
async function uploadFile(file) {
  // Validate file type
  const allowed = ['image/jpeg', 'image/png', 'image/webp']
  if (!allowed.includes(file.type)) {
    uploadError.value = `Dateityp ${file.type} nicht erlaubt. Erlaubt: JPG, PNG, WebP`
    return
  }

  // Validate file size (max 20MB)
  if (file.size > 20 * 1024 * 1024) {
    uploadError.value = 'Datei ist zu groß (max. 20 MB)'
    return
  }

  uploading.value = true
  uploadProgress.value = 0
  uploadError.value = null

  const formData = new FormData()
  formData.append('file', file)
  if (uploadCategory.value) {
    formData.append('category', uploadCategory.value)
  }
  if (uploadCountry.value) {
    formData.append('country', uploadCountry.value)
  }
  if (uploadTags.value.trim()) {
    formData.append('tags', uploadTags.value.trim())
  }

  try {
    const response = await api.post('/api/assets/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        }
      },
    })

    // Add the new asset to the top of the list
    assets.value.unshift(response.data)
    uploadProgress.value = 100

    // Reset upload metadata after successful upload
    uploadCategory.value = ''
    uploadCountry.value = ''
    uploadTags.value = ''
  } catch (err) {
    uploadError.value = err.response?.data?.detail || 'Upload fehlgeschlagen'
  } finally {
    // Small delay so user sees 100% completion
    setTimeout(() => {
      uploading.value = false
      uploadProgress.value = 0
    }, 800)
  }
}

// Drag and drop handlers
function onDragEnter(e) {
  e.preventDefault()
  isDragOver.value = true
}

function onDragOver(e) {
  e.preventDefault()
  isDragOver.value = true
}

function onDragLeave(e) {
  e.preventDefault()
  // Only set false if leaving the drop zone itself
  if (e.currentTarget.contains(e.relatedTarget)) return
  isDragOver.value = false
}

function onDrop(e) {
  e.preventDefault()
  isDragOver.value = false

  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    // Upload first valid image file
    for (const file of files) {
      if (file.type.startsWith('image/')) {
        uploadFile(file)
        break
      }
    }
  }
}

// File input handler
function onFileSelect(e) {
  const files = e.target.files
  if (files && files.length > 0) {
    uploadFile(files[0])
  }
  // Reset file input
  e.target.value = ''
}

// Delete asset
async function deleteAsset(assetId) {
  try {
    await api.delete(`/api/assets/${assetId}`)
    assets.value = assets.value.filter(a => a.id !== assetId)
    showDeleteConfirm.value = null
  } catch (err) {
    error.value = err.response?.data?.detail || 'Loeschen fehlgeschlagen'
  }
}

// Clear all filters
function clearFilters() {
  selectedFilter.value = 'all'
  selectedCategory.value = 'all'
  selectedCountry.value = 'all'
  searchQuery.value = ''
}

// Format file size
function formatSize(bytes) {
  if (!bytes) return '\u2014'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// Format date
function formatDate(dateStr) {
  if (!dateStr) return '\u2014'
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

// Get file type label
function fileTypeLabel(type) {
  if (!type) return '\u2014'
  return type.replace('image/', '').toUpperCase()
}

onMounted(fetchAssets)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Asset-Bibliothek</h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Bilder hochladen und verwalten
        </p>
      </div>
      <div class="text-sm text-gray-500 dark:text-gray-400">
        {{ assets.length }} Asset{{ assets.length !== 1 ? 's' : '' }}
      </div>
    </div>

    <!-- Upload Drop Zone -->
    <div
      class="relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 cursor-pointer"
      :class="[
        isDragOver
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
          : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500 bg-white dark:bg-gray-800',
        uploading ? 'pointer-events-none opacity-75' : ''
      ]"
      @dragenter="onDragEnter"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
      @click="$refs.fileInput.click()"
      data-testid="drop-zone"
    >
      <input
        ref="fileInput"
        type="file"
        accept="image/jpeg,image/png,image/webp"
        class="hidden"
        @change="onFileSelect"
      />

      <!-- Upload progress -->
      <div v-if="uploading" class="space-y-3">
        <div class="flex items-center justify-center">
          <svg class="animate-spin h-8 w-8 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
        <p class="text-sm font-medium text-blue-600 dark:text-blue-400" data-testid="upload-progress-text">
          Wird hochgeladen... {{ uploadProgress }}%
        </p>
        <div class="w-full max-w-xs mx-auto bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            class="bg-blue-500 h-2 rounded-full transition-all duration-300"
            :style="{ width: uploadProgress + '%' }"
            data-testid="upload-progress-bar"
          ></div>
        </div>
      </div>

      <!-- Default drop zone content -->
      <div v-else>
        <div class="flex justify-center mb-3">
          <svg class="h-12 w-12 text-gray-400" :class="{ 'text-blue-500': isDragOver }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
        </div>
        <p class="text-sm font-medium text-gray-700 dark:text-gray-300">
          <span v-if="isDragOver" class="text-blue-600 dark:text-blue-400">Datei hier ablegen</span>
          <span v-else>
            Bild hierher ziehen oder <span class="text-blue-600 dark:text-blue-400 underline">durchsuchen</span>
          </span>
        </p>
        <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
          JPG, PNG oder WebP &middot; max. 20 MB
        </p>
      </div>
    </div>

    <!-- Upload Metadata (Category & Country selection for uploads) -->
    <div class="flex flex-col sm:flex-row gap-3 bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg p-3" data-testid="upload-metadata">
      <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 shrink-0">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
        </svg>
        <span class="font-medium">Upload-Tags:</span>
      </div>
      <select
        v-model="uploadCategory"
        class="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
        data-testid="upload-category-select"
        @click.stop
      >
        <option value="">Kategorie (optional)</option>
        <option v-for="opt in categoryOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <select
        v-model="uploadCountry"
        class="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
        data-testid="upload-country-select"
        @click.stop
      >
        <option value="">Land (optional)</option>
        <option v-for="opt in countryOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <input
        v-model="uploadTags"
        type="text"
        placeholder="Tags (z.B. kanada, landschaft)"
        class="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 flex-1 min-w-[180px]"
        data-testid="upload-tags-input"
        @click.stop
      />
    </div>

    <!-- Upload error -->
    <div v-if="uploadError" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 flex items-center gap-2" role="alert">
      <span class="text-red-500">&#9888;&#65039;</span>
      <p class="text-sm text-red-700 dark:text-red-400">{{ uploadError }}</p>
      <button @click="uploadError = null" class="ml-auto text-red-500 hover:text-red-700">&#10005;</button>
    </div>

    <!-- Filters and Search -->
    <div class="flex flex-col sm:flex-row gap-3" data-testid="filter-bar">
      <div class="relative flex-1">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Assets durchsuchen..."
          class="w-full pl-9 pr-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <svg class="absolute left-3 top-2.5 h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
      <select
        v-model="selectedCategory"
        class="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
        data-testid="filter-category"
      >
        <option value="all">Alle Kategorien</option>
        <option v-for="opt in categoryOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <select
        v-model="selectedCountry"
        class="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
        data-testid="filter-country"
      >
        <option value="all">Alle Laender</option>
        <option v-for="opt in countryOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <select
        v-model="selectedFilter"
        class="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
        data-testid="filter-type"
      >
        <option value="all">Alle Typen</option>
        <option value="jpeg">JPG</option>
        <option value="png">PNG</option>
        <option value="webp">WebP</option>
      </select>
      <button
        v-if="hasActiveFilters"
        @click="clearFilters"
        class="px-3 py-2 text-sm text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        data-testid="clear-filters-btn"
      >
        Filter zuruecksetzen
      </button>
    </div>

    <!-- Active filters indicator -->
    <div v-if="hasActiveFilters" class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400" data-testid="active-filters-indicator">
      <span>Aktive Filter:</span>
      <span v-if="selectedCategory !== 'all'" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-medium">
        {{ categoryLabel(selectedCategory) }}
        <button @click="selectedCategory = 'all'" class="hover:text-blue-900 dark:hover:text-blue-100">&times;</button>
      </span>
      <span v-if="selectedCountry !== 'all'" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs font-medium">
        {{ countryLabel(selectedCountry) }}
        <button @click="selectedCountry = 'all'" class="hover:text-green-900 dark:hover:text-green-100">&times;</button>
      </span>
      <span v-if="selectedFilter !== 'all'" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-xs font-medium">
        {{ selectedFilter.toUpperCase() }}
        <button @click="selectedFilter = 'all'" class="hover:text-purple-900 dark:hover:text-purple-100">&times;</button>
      </span>
      <span v-if="searchQuery.trim()" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 text-xs font-medium">
        "{{ searchQuery }}"
        <button @click="searchQuery = ''" class="hover:text-yellow-900 dark:hover:text-yellow-100">&times;</button>
      </span>
      <span class="text-gray-400 dark:text-gray-500">&middot; {{ filteredAssets.length }} Ergebnis{{ filteredAssets.length !== 1 ? 'se' : '' }}</span>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      <div v-for="i in 8" :key="i" class="aspect-square bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"></div>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 rounded-lg p-6 text-center">
      <p class="text-red-600 dark:text-red-400">{{ error }}</p>
      <button @click="fetchAssets" class="mt-3 px-4 py-2 text-sm bg-red-100 dark:bg-red-800 text-red-700 dark:text-red-300 rounded-lg hover:bg-red-200 dark:hover:bg-red-700">
        Erneut versuchen
      </button>
    </div>

    <!-- Empty state -->
    <div v-else-if="filteredAssets.length === 0 && !loading" class="text-center py-12">
      <div class="text-4xl mb-3">&#128444;&#65039;</div>
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-1">
        {{ assets.length === 0 ? 'Noch keine Assets' : 'Keine Treffer' }}
      </h3>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        {{ assets.length === 0 ? 'Lade dein erstes Bild hoch, um loszulegen.' : 'Versuche einen anderen Suchbegriff oder Filter.' }}
      </p>
      <button
        v-if="hasActiveFilters"
        @click="clearFilters"
        class="mt-3 px-4 py-2 text-sm bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-700"
        data-testid="empty-clear-filters-btn"
      >
        Filter zuruecksetzen
      </button>
    </div>

    <!-- Asset Grid -->
    <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4" data-testid="asset-grid">
      <div
        v-for="asset in filteredAssets"
        :key="asset.id"
        class="group relative bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-md transition-shadow"
        :data-testid="`asset-${asset.id}`"
      >
        <!-- Image thumbnail -->
        <div class="aspect-square bg-gray-100 dark:bg-gray-700 overflow-hidden">
          <img
            :src="asset.file_path"
            :alt="asset.original_filename || asset.filename"
            class="w-full h-full object-cover"
            loading="lazy"
            @error="(e) => e.target.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22 fill=%22%239CA3AF%22%3E%3Cpath d=%22M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z%22/%3E%3C/svg%3E'"
          />
        </div>

        <!-- Asset info -->
        <div class="p-2">
          <p class="text-xs font-medium text-gray-900 dark:text-white truncate" :title="asset.original_filename || asset.filename">
            {{ asset.original_filename || asset.filename }}
          </p>
          <div class="flex items-center justify-between mt-1">
            <span class="text-xs text-gray-500 dark:text-gray-400">
              {{ formatSize(asset.file_size) }}
            </span>
            <span class="text-xs font-medium px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
              {{ fileTypeLabel(asset.file_type) }}
            </span>
          </div>
          <!-- Category, Country, and Tags badges -->
          <div v-if="asset.category || asset.country || asset.tags" class="flex flex-wrap gap-1 mt-1.5">
            <span
              v-if="asset.category"
              class="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
              :data-testid="`asset-${asset.id}-category`"
            >
              {{ categoryLabel(asset.category) }}
            </span>
            <span
              v-if="asset.country"
              class="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300"
              :data-testid="`asset-${asset.id}-country`"
            >
              {{ countryLabel(asset.country) }}
            </span>
            <span
              v-for="tag in (asset.tags || '').split(',').map(t => t.trim()).filter(t => t)"
              :key="tag"
              class="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300"
              :data-testid="`asset-${asset.id}-tag-${tag}`"
            >
              {{ tag }}
            </span>
          </div>
          <p v-if="asset.width && asset.height" class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
            {{ asset.width }}&times;{{ asset.height }}px
          </p>
        </div>

        <!-- Hover overlay with delete button -->
        <div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-start justify-end p-2 pointer-events-none">
          <button
            v-if="showDeleteConfirm === asset.id"
            @click.stop="deleteAsset(asset.id)"
            class="pointer-events-auto px-2 py-1 text-xs bg-red-500 text-white rounded shadow hover:bg-red-600 transition-colors"
          >
            Loeschen?
          </button>
          <button
            v-else
            @click.stop="showDeleteConfirm = asset.id"
            class="pointer-events-auto opacity-0 group-hover:opacity-100 transition-opacity p-1.5 bg-white dark:bg-gray-800 rounded-full shadow hover:bg-red-50 dark:hover:bg-red-900/30"
            title="Asset loeschen"
          >
            <svg class="h-3.5 w-3.5 text-gray-500 hover:text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
