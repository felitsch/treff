<script setup>
import { ref, onMounted, computed, inject, watch } from 'vue'
import api from '@/utils/api'
import { useApi } from '@/composables/useApi'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import AssetCropModal from '@/components/assets/AssetCropModal.vue'
import VideoTrimmer from '@/components/assets/VideoTrimmer.vue'
import ImageEditTools from '@/components/assets/ImageEditTools.vue'
import TourSystem from '@/components/common/TourSystem.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SkeletonImage from '@/components/common/SkeletonImage.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const tourRef = ref(null)

// Tab state
const activeTab = ref('library') // 'library' or 'stock'

// State
const assets = ref([])
const loading = ref(true)
const error = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadError = ref(null)
const isDragOver = ref(false)
const searchQuery = ref('')
const librarySearch = inject('librarySearch', ref(''))
const libraryAssetCount = inject('libraryAssetCount', ref(null))
const selectedFilter = ref('all')
const selectedCategory = ref('all')
const selectedCountry = ref('all')
const showDeleteConfirm = ref(null)
const showCropModal = ref(false)
const cropAsset = ref(null)

// Video preview state
const videoPreviewAsset = ref(null)

// Video trimmer state
const showTrimmer = ref(false)
const trimAsset = ref(null)

// KI image edit state
const showImageEdit = ref(false)
const imageEditAsset = ref(null)

// Stock photo state
const stockSearchQuery = ref('')
const stockSource = ref('unsplash')
const stockResults = ref([])
const stockLoading = ref(false)
const stockError = ref(null)
const stockImporting = ref({}) // track which photos are being imported by id
const stockImportSuccess = ref({}) // track successfully imported photos by id
const stockSearched = ref(false) // track if a search has been performed

// Open crop tool for an asset
function openCropTool(asset) {
  cropAsset.value = asset
  showCropModal.value = true
}

// Handle crop completion
function onCropped(croppedAsset) {
  // If saved as new, add to list; otherwise update existing
  const existingIdx = assets.value.findIndex(a => a.id === croppedAsset.id)
  if (existingIdx >= 0) {
    assets.value[existingIdx] = croppedAsset
  } else {
    assets.value.unshift(croppedAsset)
  }
  showCropModal.value = false
  cropAsset.value = null
}

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
  { value: 'video', label: 'Video' },
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

// Check if an asset is a video
function isVideoAsset(asset) {
  return asset.file_type && asset.file_type.startsWith('video/')
}

// Check if an asset is audio
function isAudioAsset(asset) {
  return asset.file_type && asset.file_type.startsWith('audio/')
}

// Format video duration
function formatDuration(seconds) {
  if (!seconds && seconds !== 0) return ''
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// Open video preview modal
function openVideoPreview(asset) {
  videoPreviewAsset.value = asset
}

// Close video preview modal
function closeVideoPreview() {
  videoPreviewAsset.value = null
}

// Open video trimmer
function openTrimmer(asset) {
  trimAsset.value = asset
  showTrimmer.value = true
}

// Open KI image edit tool
function openImageEdit(asset) {
  imageEditAsset.value = asset
  showImageEdit.value = true
}

// Handle KI image edit completion
function onImageEdited(editedAsset) {
  // Add the new edited asset to the top of the list
  assets.value.unshift(editedAsset)
  showImageEdit.value = false
  imageEditAsset.value = null
}

// Handle trim completion
function onTrimmed(trimmedAsset) {
  // If saved as new, add to list; otherwise update existing
  const existingIdx = assets.value.findIndex(a => a.id === trimmedAsset.id)
  if (existingIdx >= 0) {
    assets.value[existingIdx] = trimmedAsset
  } else {
    assets.value.unshift(trimmedAsset)
  }
  showTrimmer.value = false
  trimAsset.value = null
}

// Computed
const filteredAssets = computed(() => {
  let filtered = assets.value
  if (selectedFilter.value !== 'all') {
    if (selectedFilter.value === 'video') {
      filtered = filtered.filter(a => a.file_type && a.file_type.startsWith('video/'))
    } else if (selectedFilter.value === 'audio') {
      filtered = filtered.filter(a => a.file_type && a.file_type.startsWith('audio/'))
    } else {
      filtered = filtered.filter(a => a.file_type === `image/${selectedFilter.value}`)
    }
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

const { execute: apiExecute } = useApi()

// Fetch all assets (filtering is done client-side via filteredAssets computed)
async function fetchAssets() {
  loading.value = true
  error.value = null
  const result = await apiExecute(() => api.get('/api/assets'))
  if (result) {
    assets.value = result
    libraryAssetCount.value = result.length
  } else {
    error.value = 'Fehler beim Laden der Assets'
  }
  loading.value = false
}

// Upload file
async function uploadFile(file) {
  // Validate file type
  const allowedImages = ['image/jpeg', 'image/png', 'image/webp']
  const allowedVideos = ['video/mp4', 'video/quicktime', 'video/webm']
  const allowedAudio = ['audio/mpeg', 'audio/wav', 'audio/aac', 'audio/x-wav', 'audio/mp3', 'audio/x-aac']
  const allowed = [...allowedImages, ...allowedVideos, ...allowedAudio]

  if (!allowed.includes(file.type)) {
    uploadError.value = `Dateityp ${file.type || 'unbekannt'} nicht erlaubt. Erlaubt: JPG, PNG, WebP, MP4, MOV, WebM, MP3, WAV, AAC`
    return
  }

  const isVideo = allowedVideos.includes(file.type)
  const isAudio = allowedAudio.includes(file.type)

  // Validate file size (max 20MB for images, 500MB for videos, 50MB for audio)
  const maxSize = isVideo ? 500 * 1024 * 1024 : isAudio ? 50 * 1024 * 1024 : 20 * 1024 * 1024
  const maxLabel = isVideo ? '500 MB' : isAudio ? '50 MB' : '20 MB'
  if (file.size > maxSize) {
    uploadError.value = `Datei ist zu gross (max. ${maxLabel})`
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
    // Error toast shown by API interceptor; set local error for inline display
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
    // Try to upload the first file - uploadFile() handles type validation
    uploadFile(files[0])
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
  const result = await apiExecute(() => api.delete(`/api/assets/${assetId}`))
  if (result !== null) {
    assets.value = assets.value.filter(a => a.id !== assetId)
    showDeleteConfirm.value = null
  }
  // Error toast shown by API interceptor
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
  if (type === 'video/mp4') return 'MP4'
  if (type === 'video/quicktime') return 'MOV'
  if (type === 'video/webm') return 'WebM'
  if (type === 'audio/mpeg' || type === 'audio/mp3') return 'MP3'
  if (type === 'audio/wav' || type === 'audio/x-wav') return 'WAV'
  if (type === 'audio/aac' || type === 'audio/x-aac') return 'AAC'
  return type.replace('image/', '').toUpperCase()
}

// Stock photo search
async function searchStockPhotos() {
  const query = stockSearchQuery.value.trim()
  if (!query) return

  stockLoading.value = true
  stockError.value = null
  stockResults.value = []
  stockSearched.value = true

  try {
    const response = await api.get('/api/assets/stock/search', {
      params: {
        query,
        source: stockSource.value,
        per_page: 12,
      },
    })
    stockResults.value = response.data.results || []
  } catch (err) {
    // Error toast shown by API interceptor; set local error for inline display
    stockError.value = err.response?.data?.detail || 'Fehler bei der Stock-Foto-Suche'
  } finally {
    stockLoading.value = false
  }
}

// Handle Enter key in stock search
function onStockSearchKeydown(e) {
  if (e.key === 'Enter') {
    searchStockPhotos()
  }
}

// Import stock photo to library
async function importStockPhoto(photo) {
  if (stockImporting.value[photo.id]) return // prevent double-click

  stockImporting.value = { ...stockImporting.value, [photo.id]: true }

  try {
    const response = await api.post('/api/assets/stock/import', {
      download_url: photo.download_url,
      description: photo.description,
      photographer: photo.photographer,
      source: photo.source,
      source_url: photo.source_url,
      width: photo.width,
      height: photo.height,
      category: 'photo',
    })

    // Add the imported asset to the library
    assets.value.unshift(response.data)
    stockImportSuccess.value = { ...stockImportSuccess.value, [photo.id]: true }
  } catch (err) {
    // Error toast shown by API interceptor; set local error for inline display
    stockError.value = err.response?.data?.detail || 'Import fehlgeschlagen'
  } finally {
    stockImporting.value = { ...stockImporting.value, [photo.id]: false }
  }
}

// Sync library-level search
watch(librarySearch, (val) => {
  if (val !== searchQuery.value) {
    searchQuery.value = val
  }
})

onMounted(() => {
  if (librarySearch.value) searchQuery.value = librarySearch.value
  fetchAssets()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between" data-tour="assets-header">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Asset-Bibliothek</h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Bilder und Videos hochladen und verwalten
        </p>
      </div>
      <div class="flex items-center gap-3">
        <button
          @click="tourRef?.startTour()"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          title="Seiten-Tour starten"
        >
          &#10067; Tour
        </button>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ assets.length }} Asset{{ assets.length !== 1 ? 's' : '' }}
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="border-b border-gray-200 dark:border-gray-700" data-testid="asset-tabs" data-tour="assets-tabs">
      <nav class="flex gap-4 -mb-px">
        <button
          @click="activeTab = 'library'"
          :class="[
            'px-4 py-2.5 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'library'
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
          ]"
          data-testid="tab-library"
        >
          <span class="flex items-center gap-2">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Meine Assets
          </span>
        </button>
        <button
          @click="activeTab = 'stock'"
          :class="[
            'px-4 py-2.5 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'stock'
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
          ]"
          data-testid="tab-stock"
        >
          <span class="flex items-center gap-2">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Stock Fotos
          </span>
        </button>
      </nav>
    </div>

    <!-- ============== LIBRARY TAB ============== -->
    <template v-if="activeTab === 'library'">
      <!-- Upload Drop Zone -->
      <div
        data-tour="assets-upload"
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
          accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime,video/webm,audio/mpeg,audio/wav,audio/aac,.mp4,.mov,.webm,.mp3,.wav,.aac"
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
              Bild oder Video hierher ziehen oder <span class="text-blue-600 dark:text-blue-400 underline">durchsuchen</span>
            </span>
          </p>
          <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
            JPG, PNG, WebP (max. 20 MB) &middot; MP4, MOV, WebM (max. 500 MB) &middot; MP3, WAV, AAC (max. 50 MB)
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
        <p class="text-sm text-red-700 dark:text-red-400" data-testid="upload-error">{{ uploadError }}</p>
        <button @click="uploadError = null" class="ml-auto text-red-500 hover:text-red-700">&#10005;</button>
      </div>

      <!-- Filters and Search -->
      <div class="flex flex-col sm:flex-row gap-3" data-testid="filter-bar" data-tour="assets-filters">
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
          <option value="video">Video</option>
          <option value="audio">Audio</option>
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
          {{ selectedFilter === 'video' ? 'Video' : selectedFilter === 'audio' ? 'Audio' : selectedFilter.toUpperCase() }}
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
        <SkeletonImage v-for="i in 8" :key="i" aspect="square" rounded="lg" />
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 rounded-lg p-6 text-center" role="alert">
        <p class="text-red-600 dark:text-red-400">{{ error }}</p>
        <button @click="fetchAssets" class="mt-3 px-4 py-2 text-sm bg-red-100 dark:bg-red-800 text-red-700 dark:text-red-300 rounded-lg hover:bg-red-200 dark:hover:bg-red-700">
          Erneut versuchen
        </button>
      </div>

      <!-- Empty state: no assets at all -->
      <EmptyState
        v-else-if="filteredAssets.length === 0 && !loading && assets.length === 0"
        svgIcon="photo"
        title="Noch keine Assets hochgeladen"
        description="Lade deine ersten Bilder und Videos hoch, um sie in Posts zu verwenden. Du kannst JPG, PNG, GIF und MP4 Dateien nutzen."
        actionLabel="Dateien hochladen"
        @action="$refs.fileInput?.click()"
      />

      <!-- Empty state: filters active, no matches -->
      <EmptyState
        v-else-if="filteredAssets.length === 0 && !loading"
        svgIcon="magnifying-glass"
        title="Keine Treffer"
        description="Versuche einen anderen Suchbegriff oder setze die Filter zurueck."
        actionLabel="Filter zuruecksetzen"
        @action="clearFilters"
      />

      <!-- Asset Grid -->
      <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4" data-testid="asset-grid" data-tour="assets-grid">
        <div
          v-for="asset in filteredAssets"
          :key="asset.id"
          class="stagger-item group relative bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-md transition-shadow"
          :data-testid="`asset-${asset.id}`"
        >
          <!-- Image/Video/Audio thumbnail -->
          <div class="aspect-square bg-gray-100 dark:bg-gray-700 overflow-hidden relative" @click.stop="isVideoAsset(asset) ? openVideoPreview(asset) : null" :class="{ 'cursor-pointer': isVideoAsset(asset) }">
            <!-- Audio asset display -->
            <template v-if="isAudioAsset(asset)">
              <div class="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-indigo-100 to-purple-100 dark:from-indigo-900/30 dark:to-purple-900/30">
                <svg class="h-12 w-12 text-indigo-500 dark:text-indigo-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                </svg>
                <!-- Mini waveform visualization -->
                <div class="flex items-end gap-[2px] h-4">
                  <div v-for="i in 12" :key="i" class="w-1 bg-indigo-400 dark:bg-indigo-500 rounded-full" :style="{ height: (4 + Math.sin(i * 0.8) * 8 + Math.cos(i * 1.3) * 4) + 'px' }"></div>
                </div>
              </div>
              <!-- Duration badge -->
              <div v-if="asset.duration_seconds" class="absolute bottom-1 right-1 bg-black/70 text-white text-[10px] font-medium px-1.5 py-0.5 rounded" data-testid="audio-duration">
                {{ formatDuration(asset.duration_seconds) }}
              </div>
            </template>
            <!-- Video thumbnail with play icon overlay -->
            <template v-else-if="isVideoAsset(asset)">
              <img
                v-if="asset.thumbnail_path"
                :src="asset.thumbnail_path"
                :alt="asset.original_filename || asset.filename"
                class="w-full h-full object-cover"
                loading="lazy"
                @error="(e) => e.target.style.display = 'none'"
              />
              <div v-else class="w-full h-full flex items-center justify-center bg-gray-200 dark:bg-gray-600">
                <svg class="h-12 w-12 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
                </svg>
              </div>
              <!-- Play button overlay -->
              <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div class="bg-black/50 rounded-full p-2">
                  <svg class="h-6 w-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </div>
              </div>
              <!-- Duration badge -->
              <div v-if="asset.duration_seconds" class="absolute bottom-1 right-1 bg-black/70 text-white text-[10px] font-medium px-1.5 py-0.5 rounded" data-testid="video-duration">
                {{ formatDuration(asset.duration_seconds) }}
              </div>
            </template>
            <!-- Image thumbnail -->
            <template v-else>
              <img
                :src="asset.file_path"
                :alt="asset.original_filename || asset.filename"
                class="w-full h-full object-cover"
                loading="lazy"
                @error="(e) => e.target.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22 fill=%22%239CA3AF%22%3E%3Cpath d=%22M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z%22/%3E%3C/svg%3E'"
              />
            </template>
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
              <span class="text-xs font-medium px-1.5 py-0.5 rounded" :class="isVideoAsset(asset) ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-300' : isAudioAsset(asset) ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-300' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'">
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
            <p v-if="(asset.width && asset.height) || (isAudioAsset(asset) && asset.duration_seconds)" class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
              <span v-if="asset.width && asset.height">{{ asset.width }}&times;{{ asset.height }}px</span>
              <span v-if="asset.duration_seconds"><span v-if="asset.width && asset.height"> &middot; </span>{{ formatDuration(asset.duration_seconds) }}</span>
            </p>
          </div>

          <!-- Hover overlay with crop and delete buttons -->
          <div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-start justify-end p-2 pointer-events-none">
            <div class="flex gap-1">
              <!-- Crop button (only for images, not video/audio) -->
              <button
                v-if="!isVideoAsset(asset) && !isAudioAsset(asset)"
                @click.stop="openCropTool(asset)"
                class="pointer-events-auto opacity-0 group-hover:opacity-100 transition-opacity p-1.5 bg-white dark:bg-gray-800 rounded-full shadow hover:bg-blue-50 dark:hover:bg-blue-900/30"
                title="Bild zuschneiden"
                aria-label="Bild zuschneiden"
                :data-testid="`crop-btn-${asset.id}`"
              >
                <svg class="h-3.5 w-3.5 text-gray-500 hover:text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                </svg>
              </button>
              <!-- KI Image Edit button (only for images, not video/audio) -->
              <button
                v-if="!isVideoAsset(asset) && !isAudioAsset(asset)"
                @click.stop="openImageEdit(asset)"
                class="pointer-events-auto opacity-0 group-hover:opacity-100 transition-opacity p-1.5 bg-white dark:bg-gray-800 rounded-full shadow hover:bg-purple-50 dark:hover:bg-purple-900/30"
                title="KI-Bildbearbeitung"
                aria-label="KI-Bildbearbeitung"
                :data-testid="`ai-edit-btn-${asset.id}`"
              >
                <svg class="h-3.5 w-3.5 text-gray-500 hover:text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9.53 16.122a3 3 0 00-5.78 1.128 2.25 2.25 0 01-2.4 2.245 4.5 4.5 0 008.4-2.245c0-.399-.078-.78-.22-1.128zm0 0a15.998 15.998 0 003.388-1.62m-5.043-.025a15.994 15.994 0 011.622-3.395m3.42 3.42a15.995 15.995 0 004.764-4.648l3.876-5.814a1.151 1.151 0 00-1.597-1.597L14.146 6.32a15.996 15.996 0 00-4.649 4.763m3.42 3.42a6.776 6.776 0 00-3.42-3.42" />
                </svg>
              </button>
              <!-- Video buttons: Play + Trim + Audio Mix -->
              <template v-if="isVideoAsset(asset)">
                <button
                  @click.stop="openVideoPreview(asset)"
                  class="pointer-events-auto opacity-0 group-hover:opacity-100 transition-opacity p-1.5 bg-white dark:bg-gray-800 rounded-full shadow hover:bg-blue-50 dark:hover:bg-blue-900/30"
                  title="Video abspielen"
                  aria-label="Video abspielen"
                  :data-testid="`play-btn-${asset.id}`"
                >
                  <svg class="h-3.5 w-3.5 text-gray-500 hover:text-blue-500" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </button>
                <button
                  @click.stop="openTrimmer(asset)"
                  class="pointer-events-auto opacity-0 group-hover:opacity-100 transition-opacity p-1.5 bg-white dark:bg-gray-800 rounded-full shadow hover:bg-purple-50 dark:hover:bg-purple-900/30"
                  title="Video trimmen"
                  aria-label="Video trimmen"
                  :data-testid="`trim-btn-${asset.id}`"
                >
                  <svg class="h-3.5 w-3.5 text-gray-500 hover:text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0-5.758a3 3 0 10-4.243-4.243 3 3 0 004.243 4.243z" />
                  </svg>
                </button>
                <button
                  @click.stop="openAudioMixer(asset)"
                  class="pointer-events-auto opacity-0 group-hover:opacity-100 transition-opacity p-1.5 bg-white dark:bg-gray-800 rounded-full shadow hover:bg-indigo-50 dark:hover:bg-indigo-900/30"
                  title="Audio mixen"
                  aria-label="Audio mixen"
                  :data-testid="`audio-mix-btn-${asset.id}`"
                >
                  <svg class="h-3.5 w-3.5 text-gray-500 hover:text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                  </svg>
                </button>
              </template>
              <!-- Delete button -->
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
                aria-label="Asset loeschen"
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

    <!-- ============== STOCK PHOTOS TAB ============== -->
    <template v-if="activeTab === 'stock'">
      <!-- Stock Photo Search -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6" data-testid="stock-search-panel">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">Stock-Foto-Suche</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Durchsuche kostenlose Stock-Fotos von Unsplash und Pexels
        </p>

        <!-- Search input + source selector -->
        <div class="flex flex-col sm:flex-row gap-3">
          <div class="relative flex-1">
            <input
              v-model="stockSearchQuery"
              type="text"
              placeholder="z.B. school building, campus, highschool..."
              class="w-full pl-9 pr-4 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              data-testid="stock-search-input"
              @keydown="onStockSearchKeydown"
            />
            <svg class="absolute left-3 top-3 h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <select
            v-model="stockSource"
            class="px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            data-testid="stock-source-select"
          >
            <option value="unsplash">Unsplash</option>
            <option value="pexels">Pexels</option>
          </select>
          <button
            @click="searchStockPhotos"
            :disabled="!stockSearchQuery.trim() || stockLoading"
            class="px-6 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            data-testid="stock-search-btn"
          >
            <svg v-if="stockLoading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ stockLoading ? 'Suche...' : 'Suchen' }}
          </button>
        </div>
      </div>

      <!-- Stock Error -->
      <div v-if="stockError" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 flex items-center gap-2" role="alert">
        <span class="text-red-500">&#9888;&#65039;</span>
        <p class="text-sm text-red-700 dark:text-red-400">{{ stockError }}</p>
        <button @click="stockError = null" class="ml-auto text-red-500 hover:text-red-700">&#10005;</button>
      </div>

      <!-- Stock Loading -->
      <div v-if="stockLoading" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
        <SkeletonImage v-for="i in 8" :key="i" aspect="3/2" rounded="lg" />
      </div>

      <!-- Stock Results -->
      <div v-else-if="stockResults.length > 0" data-testid="stock-results">
        <div class="flex items-center justify-between mb-3">
          <p class="text-sm text-gray-600 dark:text-gray-400">
            {{ stockResults.length }} Ergebnis{{ stockResults.length !== 1 ? 'se' : '' }} fuer "{{ stockSearchQuery }}"
            <span class="text-gray-400">via {{ stockSource === 'unsplash' ? 'Unsplash' : 'Pexels' }}</span>
          </p>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4" data-testid="stock-results-grid">
          <div
            v-for="photo in stockResults"
            :key="photo.id"
            class="group relative bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-md transition-shadow"
            :data-testid="`stock-photo-${photo.id}`"
          >
            <!-- Preview thumbnail -->
            <div class="aspect-[3/2] bg-gray-100 dark:bg-gray-700 overflow-hidden">
              <img
                :src="photo.thumbnail_url"
                :alt="photo.description"
                class="w-full h-full object-cover"
                loading="lazy"
                @error="(e) => e.target.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22 fill=%22%239CA3AF%22%3E%3Cpath d=%22M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z%22/%3E%3C/svg%3E'"
              />
            </div>

            <!-- Photo info -->
            <div class="p-2">
              <p class="text-xs font-medium text-gray-900 dark:text-white truncate" :title="photo.description">
                {{ photo.description }}
              </p>
              <div class="flex items-center justify-between mt-1">
                <span class="text-xs text-gray-500 dark:text-gray-400">
                  {{ photo.width }}&times;{{ photo.height }}
                </span>
                <span class="text-xs text-gray-400 dark:text-gray-500 truncate ml-1" :title="photo.photographer">
                  {{ photo.photographer }}
                </span>
              </div>
            </div>

            <!-- Import button overlay -->
            <div class="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-all flex items-center justify-center pointer-events-none">
              <button
                v-if="stockImportSuccess[photo.id]"
                class="pointer-events-auto px-4 py-2 text-sm font-medium bg-green-500 text-white rounded-lg shadow-lg flex items-center gap-2"
                disabled
                :data-testid="`stock-imported-${photo.id}`"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                Importiert
              </button>
              <button
                v-else
                @click.stop="importStockPhoto(photo)"
                :disabled="stockImporting[photo.id]"
                class="pointer-events-auto opacity-0 group-hover:opacity-100 transition-opacity px-4 py-2 text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-lg disabled:opacity-50 flex items-center gap-2"
                :data-testid="`stock-import-btn-${photo.id}`"
              >
                <svg v-if="stockImporting[photo.id]" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                {{ stockImporting[photo.id] ? 'Importiere...' : 'Importieren' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state when no search yet -->
      <div v-else-if="!stockLoading && !stockSearched" class="text-center py-12">
        <div class="text-4xl mb-3">&#128270;</div>
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-1">
          Stock-Fotos durchsuchen
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Gib einen Suchbegriff ein, um kostenlose Stock-Fotos zu finden.
        </p>
      </div>

      <!-- No results after search -->
      <div v-else-if="!stockLoading && stockSearched && stockResults.length === 0" class="text-center py-12">
        <div class="text-4xl mb-3">&#128533;</div>
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-1">
          Keine Ergebnisse
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Versuche einen anderen Suchbegriff.
        </p>
      </div>
    </template>

    <!-- Usage hint (visible at bottom of page, serves as tour target) -->
    <div
      data-tour="assets-usage-hint"
      class="flex items-start gap-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4"
    >
      <AppIcon name="light-bulb" class="w-5 h-5 shrink-0" />
      <div>
        <p class="text-sm font-medium text-blue-800 dark:text-blue-300">Assets in Posts verwenden</p>
        <p class="text-xs text-blue-600 dark:text-blue-400 mt-0.5">
          Deine Assets stehen automatisch im Post-Editor (Schritt 5: Bild), im Video-Composer, Video-Export und Thumbnail-Generator zur Verfuegung. Tagge Assets mit Land und Kategorie fuer automatische Filterung.
        </p>
      </div>
    </div>

    <!-- Crop Modal -->
    <AssetCropModal
      v-if="cropAsset"
      :show="showCropModal"
      :asset="cropAsset"
      @close="showCropModal = false; cropAsset = null"
      @cropped="onCropped"
    />

    <!-- Video Trimmer Modal -->
    <VideoTrimmer
      v-if="trimAsset"
      :show="showTrimmer"
      :asset="trimAsset"
      @close="showTrimmer = false; trimAsset = null"
      @trimmed="onTrimmed"
    />

    <!-- KI Image Edit Modal -->
    <ImageEditTools
      v-if="imageEditAsset"
      :show="showImageEdit"
      :asset="imageEditAsset"
      @close="showImageEdit = false; imageEditAsset = null"
      @image-edited="onImageEdited"
    />

    <!-- Video Preview Modal -->
    <teleport to="body">
      <div v-if="videoPreviewAsset" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70" @click.self="closeVideoPreview" data-testid="video-preview-modal">
        <div class="relative bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-3xl w-full mx-4 overflow-hidden">
          <!-- Modal header -->
          <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <div>
              <h3 class="text-sm font-semibold text-gray-900 dark:text-white truncate" data-testid="video-preview-title">
                {{ videoPreviewAsset.original_filename || videoPreviewAsset.filename }}
              </h3>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                {{ fileTypeLabel(videoPreviewAsset.file_type) }} &middot; {{ formatSize(videoPreviewAsset.file_size) }}
                <span v-if="videoPreviewAsset.width && videoPreviewAsset.height"> &middot; {{ videoPreviewAsset.width }}&times;{{ videoPreviewAsset.height }}px</span>
                <span v-if="videoPreviewAsset.duration_seconds"> &middot; {{ formatDuration(videoPreviewAsset.duration_seconds) }}</span>
              </p>
            </div>
            <div class="flex items-center gap-2">
              <button
                @click="closeVideoPreview(); openTrimmer(videoPreviewAsset)"
                class="px-3 py-1.5 text-xs font-medium text-purple-700 dark:text-purple-300 bg-purple-100 dark:bg-purple-900/30 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-800/40 transition-colors flex items-center gap-1.5"
                data-testid="preview-trim-btn"
              >
                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0-5.758a3 3 0 10-4.243-4.243 3 3 0 004.243 4.243z" />
                </svg>
                Trimmen
              </button>
              <button @click="closeVideoPreview" class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors" data-testid="video-preview-close">
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          <!-- Video player -->
          <div class="bg-black">
            <video
              :src="videoPreviewAsset.file_path"
              controls
              autoplay
              class="w-full max-h-[70vh]"
              data-testid="video-player"
            >
              Dein Browser unterstuetzt dieses Videoformat nicht.
            </video>
          </div>
        </div>
      </div>
    </teleport>

    <!-- Page-specific guided tour -->
    <TourSystem ref="tourRef" page-key="assets" />
  </div>
</template>
