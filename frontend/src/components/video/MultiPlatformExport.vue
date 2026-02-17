<script setup>
import { ref, computed, watch } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const toast = useToast()

const props = defineProps({
  videoAsset: { type: Object, default: null },
  introTemplate: { type: Object, default: null },
  outroTemplate: { type: Object, default: null },
  lowerThird: { type: Object, default: null },
  musicConfig: { type: Object, default: null },
})

const emit = defineEmits(['export-complete'])

// Export formats
const formats = [
  {
    key: '9:16',
    label: 'Reel / TikTok',
    sublabel: '1080 x 1920',
    icon: '📱',
    platforms: ['Instagram Reels', 'TikTok'],
    width: 1080,
    height: 1920,
  },
  {
    key: '1:1',
    label: 'Feed Quadrat',
    sublabel: '1080 x 1080',
    icon: '⬜',
    platforms: ['Instagram Feed'],
    width: 1080,
    height: 1080,
  },
  {
    key: '16:9',
    label: 'Landscape',
    sublabel: '1920 x 1080',
    icon: '🖥️',
    platforms: ['YouTube', 'Twitter'],
    width: 1920,
    height: 1080,
  },
]

// State
const selectedFormats = ref(['9:16'])
const quality = ref(75)
const focusX = ref(50)
const focusY = ref(50)
const exporting = ref(false)
const exportProgress = ref({})
const exportResults = ref([])
const exportError = ref(null)

// Computed
const qualityLabel = computed(() => {
  if (quality.value >= 85) return 'Hoch'
  if (quality.value >= 60) return 'Mittel'
  if (quality.value >= 35) return 'Niedrig'
  return 'Minimal'
})

const canExport = computed(() => {
  return props.videoAsset && selectedFormats.value.length > 0 && !exporting.value
})

function toggleFormat(key) {
  const idx = selectedFormats.value.indexOf(key)
  if (idx >= 0) {
    selectedFormats.value.splice(idx, 1)
  } else {
    selectedFormats.value.push(key)
  }
}

function selectAllFormats() {
  selectedFormats.value = formats.map(f => f.key)
}

// Export
async function startExport() {
  if (!canExport.value) return
  exporting.value = true
  exportError.value = null
  exportResults.value = []

  // Initialize progress for each format
  for (const fmt of selectedFormats.value) {
    exportProgress.value[fmt] = 0
  }

  try {
    // Step 1: Apply branding if intro/outro selected
    let processedAssetId = props.videoAsset.id
    if (props.introTemplate || props.outroTemplate) {
      const brandPayload = {
        video_asset_id: props.videoAsset.id,
        output_format: selectedFormats.value[0],
      }
      if (props.introTemplate) brandPayload.intro_template_id = props.introTemplate.id
      if (props.outroTemplate) brandPayload.outro_template_id = props.outroTemplate.id

      try {
        const { data: brandResult } = await api.post('/api/video-templates/apply', brandPayload)
        if (brandResult?.asset_id) {
          processedAssetId = brandResult.asset_id
        }
      } catch (brandErr) {
        console.warn('Branding apply failed, continuing with original video:', brandErr)
      }
    }

    // Step 2: Export in each selected format
    if (selectedFormats.value.length === 1) {
      // Single export
      const fmt = selectedFormats.value[0]
      exportProgress.value[fmt] = 20
      const { data } = await api.post('/api/video-export', {
        asset_id: processedAssetId,
        aspect_ratio: fmt,
        quality: quality.value,
        focus_x: focusX.value,
        focus_y: focusY.value,
      })
      exportProgress.value[fmt] = 100
      exportResults.value.push({ format: fmt, ...data })
    } else {
      // Batch export
      const batchFormats = selectedFormats.value.map(fmt => ({
        aspect_ratio: fmt,
        quality: quality.value,
        focus_x: focusX.value,
        focus_y: focusY.value,
      }))

      // Set all to 30%
      for (const fmt of selectedFormats.value) {
        exportProgress.value[fmt] = 30
      }

      const { data } = await api.post('/api/video-export/batch', {
        asset_id: processedAssetId,
        formats: batchFormats,
      })

      // Mark all complete
      for (const fmt of selectedFormats.value) {
        exportProgress.value[fmt] = 100
      }

      if (Array.isArray(data)) {
        exportResults.value = data.map((d, i) => ({
          format: selectedFormats.value[i] || 'unknown',
          ...d,
        }))
      } else if (data?.exports) {
        exportResults.value = data.exports
      }
    }

    toast.success(`${exportResults.value.length} Export(s) erfolgreich erstellt!`)
    emit('export-complete', exportResults.value)
  } catch (err) {
    exportError.value = err.response?.data?.detail || err.message || 'Export fehlgeschlagen'
    toast.error('Export fehlgeschlagen. Bitte versuche es erneut.')
  } finally {
    exporting.value = false
  }
}

async function downloadExport(result) {
  try {
    const exportId = result.id || result.export_id
    if (!exportId) return
    const response = await api.get(`/api/video-export/${exportId}/download`, {
      responseType: 'blob',
    })
    const url = URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `treff-video-${result.format || 'export'}.mp4`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    toast.error('Download fehlgeschlagen.')
  }
}
</script>

<template>
  <div class="space-y-4">
    <!-- Format selection -->
    <div>
      <div class="flex items-center justify-between mb-2">
        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">Export-Formate</label>
        <button
          @click="selectAllFormats"
          class="text-xs text-blue-600 dark:text-blue-400 hover:underline"
        >
          Alle auswaehlen
        </button>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <button
          v-for="fmt in formats"
          :key="fmt.key"
          @click="toggleFormat(fmt.key)"
          :class="[
            'relative flex flex-col items-center p-4 rounded-xl border-2 transition-all',
            selectedFormats.includes(fmt.key)
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 ring-1 ring-blue-300'
              : 'border-gray-200 dark:border-gray-700 hover:border-blue-300',
          ]"
          data-testid="export-format-card"
        >
          <!-- Checkbox -->
          <div :class="[
            'absolute top-2 right-2 w-5 h-5 rounded border-2 flex items-center justify-center transition-all',
            selectedFormats.includes(fmt.key)
              ? 'bg-blue-500 border-blue-500'
              : 'border-gray-300 dark:border-gray-600',
          ]">
            <span v-if="selectedFormats.includes(fmt.key)" class="text-white text-xs">&#10003;</span>
          </div>

          <!-- Format preview -->
          <div class="mb-2 text-2xl">{{ fmt.icon }}</div>
          <div
            class="border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-700 mb-2"
            :style="{
              width: fmt.key === '16:9' ? '56px' : fmt.key === '1:1' ? '40px' : '28px',
              height: fmt.key === '16:9' ? '32px' : fmt.key === '1:1' ? '40px' : '50px',
              borderRadius: '4px',
            }"
          />
          <p class="text-sm font-medium text-gray-900 dark:text-white">{{ fmt.label }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">{{ fmt.sublabel }}</p>
          <div class="flex gap-1 mt-1">
            <span
              v-for="p in fmt.platforms"
              :key="p"
              class="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300"
            >
              {{ p }}
            </span>
          </div>
        </button>
      </div>
    </div>

    <!-- Quality slider -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        Qualitaet: {{ qualityLabel }} ({{ quality }}%)
      </label>
      <input
        v-model="quality"
        type="range"
        min="1"
        max="100"
        class="w-full accent-blue-500"
      />
    </div>

    <!-- Focus point -->
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
          Fokus-X ({{ focusX }}%)
        </label>
        <input
          v-model="focusX"
          type="range"
          min="0"
          max="100"
          class="w-full accent-blue-500"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
          Fokus-Y ({{ focusY }}%)
        </label>
        <input
          v-model="focusY"
          type="range"
          min="0"
          max="100"
          class="w-full accent-blue-500"
        />
      </div>
    </div>

    <!-- Export button -->
    <button
      @click="startExport"
      :disabled="!canExport"
      :class="[
        'w-full py-3 rounded-xl text-sm font-bold transition-all flex items-center justify-center gap-2',
        canExport
          ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl'
          : 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed',
      ]"
      data-testid="export-button"
    >
      <template v-if="exporting">
        <div class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
        Wird exportiert...
      </template>
      <template v-else>
        📤 {{ selectedFormats.length }} Format{{ selectedFormats.length !== 1 ? 'e' : '' }} exportieren
      </template>
    </button>

    <!-- Export progress -->
    <div v-if="exporting" class="space-y-2">
      <div v-for="fmt in selectedFormats" :key="fmt" class="flex items-center gap-3">
        <span class="text-xs text-gray-600 dark:text-gray-400 w-16">{{ fmt }}</span>
        <div class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            class="bg-blue-500 h-2 rounded-full transition-all"
            :style="{ width: `${exportProgress[fmt] || 0}%` }"
          />
        </div>
        <span class="text-xs text-gray-500 w-10 text-right">{{ exportProgress[fmt] || 0 }}%</span>
      </div>
    </div>

    <!-- Export error -->
    <div v-if="exportError" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
      <p class="text-sm text-red-700 dark:text-red-400">{{ exportError }}</p>
    </div>

    <!-- Export results -->
    <div v-if="exportResults.length > 0" class="space-y-2" data-testid="export-results">
      <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Fertige Exporte:</h4>
      <div v-for="(result, idx) in exportResults" :key="idx" class="flex items-center gap-3 bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
        <span class="text-green-500 text-lg">&#10003;</span>
        <div class="flex-1">
          <p class="text-sm font-medium text-gray-900 dark:text-white">{{ result.format || result.aspect_ratio }}</p>
          <p v-if="result.output_width" class="text-xs text-gray-500">
            {{ result.output_width }}x{{ result.output_height }}
          </p>
        </div>
        <button
          @click="downloadExport(result)"
          class="px-3 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all"
        >
          Herunterladen
        </button>
      </div>
    </div>
  </div>
</template>
