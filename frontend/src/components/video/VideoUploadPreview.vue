<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const toast = useToast()
const emit = defineEmits(['select', 'upload-complete'])

const props = defineProps({
  selectedAsset: { type: Object, default: null },
})

// State
const videoAssets = ref([])
const loadingAssets = ref(true)
const uploading = ref(false)
const uploadProgress = ref(0)
const dragOver = ref(false)

// Video preview
const videoEl = ref(null)

const assetUrl = (asset) => {
  if (!asset) return ''
  if (asset.file_path) return `/api/assets/${asset.id}/file`
  return ''
}

// Load video assets
async function loadAssets() {
  loadingAssets.value = true
  try {
    const { data } = await api.get('/api/assets', { params: { type: 'video' } })
    videoAssets.value = (data.assets || data || []).filter(
      a => a.file_type === 'video' || (a.filename && /\.(mp4|mov|webm|avi)$/i.test(a.filename))
    )
  } catch (err) {
    console.error('Failed to load video assets:', err)
  } finally {
    loadingAssets.value = false
  }
}

// Upload file
async function handleUpload(files) {
  if (!files || files.length === 0) return
  const file = files[0]
  if (!file.type.startsWith('video/')) {
    toast.error('Bitte waehle eine Videodatei aus (MP4, MOV, WebM).')
    return
  }
  uploading.value = true
  uploadProgress.value = 0
  try {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post('/api/assets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        uploadProgress.value = Math.round((e.loaded * 100) / e.total)
      },
    })
    toast.success('Video erfolgreich hochgeladen!')
    await loadAssets()
    // Auto-select the uploaded asset
    const uploaded = videoAssets.value.find(a => a.id === data.id)
    if (uploaded) {
      emit('select', uploaded)
    }
    emit('upload-complete', data)
  } catch (err) {
    toast.error('Upload fehlgeschlagen. Bitte versuche es erneut.')
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

function onDrop(e) {
  e.preventDefault()
  dragOver.value = false
  handleUpload(e.dataTransfer.files)
}

function onDragOver(e) {
  e.preventDefault()
  dragOver.value = true
}

function onDragLeave() {
  dragOver.value = false
}

function onFileInput(e) {
  handleUpload(e.target.files)
}

function selectAsset(asset) {
  emit('select', asset)
}

function formatSize(bytes) {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDuration(seconds) {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

onMounted(loadAssets)
</script>

<template>
  <div class="space-y-4">
    <!-- Upload zone -->
    <div
      @drop="onDrop"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      :class="[
        'relative border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer',
        dragOver
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
          : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500',
      ]"
      @click="$refs.fileInput.click()"
      data-testid="video-upload-zone"
    >
      <input
        ref="fileInput"
        type="file"
        accept="video/*"
        class="hidden"
        @change="onFileInput"
      />
      <div v-if="uploading" class="space-y-3">
        <div class="text-3xl">⬆️</div>
        <p class="text-sm text-gray-600 dark:text-gray-400">Wird hochgeladen... {{ uploadProgress }}%</p>
        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            class="bg-blue-500 h-2 rounded-full transition-all"
            :style="{ width: `${uploadProgress}%` }"
          />
        </div>
      </div>
      <div v-else class="space-y-2">
        <div class="text-3xl">🎬</div>
        <p class="text-sm font-medium text-gray-700 dark:text-gray-300">
          Video hierher ziehen oder klicken
        </p>
        <p class="text-xs text-gray-500 dark:text-gray-400">MP4, MOV, WebM</p>
      </div>
    </div>

    <!-- Selected video preview -->
    <div
      v-if="selectedAsset"
      class="bg-gray-900 rounded-xl overflow-hidden"
      data-testid="video-preview"
    >
      <video
        ref="videoEl"
        :src="assetUrl(selectedAsset)"
        controls
        class="w-full max-h-[300px] object-contain"
        preload="metadata"
      />
      <div class="px-4 py-3 bg-gray-800 flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-white truncate">{{ selectedAsset.filename || selectedAsset.original_filename }}</p>
          <p class="text-xs text-gray-400 mt-0.5">
            {{ formatSize(selectedAsset.file_size) }}
            <span v-if="selectedAsset.duration_seconds"> · {{ formatDuration(selectedAsset.duration_seconds) }}</span>
            <span v-if="selectedAsset.width"> · {{ selectedAsset.width }}x{{ selectedAsset.height }}</span>
          </p>
        </div>
        <button
          @click.stop="emit('select', null)"
          class="text-xs text-gray-400 hover:text-red-400 px-2 py-1 rounded"
        >
          Entfernen
        </button>
      </div>
    </div>

    <!-- Video library -->
    <div v-if="!selectedAsset">
      <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Oder waehle ein vorhandenes Video:
      </h4>
      <div v-if="loadingAssets" class="text-center py-4">
        <div class="animate-spin inline-block w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full" />
      </div>
      <div v-else-if="videoAssets.length === 0" class="text-center py-4 text-sm text-gray-500 dark:text-gray-400">
        Keine Videos in der Bibliothek. Lade ein Video hoch!
      </div>
      <div v-else class="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-[200px] overflow-y-auto">
        <button
          v-for="asset in videoAssets"
          :key="asset.id"
          @click="selectAsset(asset)"
          class="relative group rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 hover:ring-2 hover:ring-blue-500 transition-all text-left"
        >
          <div class="aspect-video bg-gray-800 flex items-center justify-center">
            <span class="text-2xl">🎬</span>
          </div>
          <div class="p-1.5">
            <p class="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">
              {{ asset.filename || asset.original_filename }}
            </p>
            <p class="text-xs text-gray-500">{{ formatSize(asset.file_size) }}</p>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>
