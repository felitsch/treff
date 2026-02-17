<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import AppIcon from '@/components/icons/AppIcon.vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  month: { type: Number, required: true },
  year: { type: Number, required: true },
  platformFilter: { type: String, default: null },
})

const emit = defineEmits(['close', 'imported'])

const auth = useAuthStore()
const toast = useToast()

// Tabs
const activeTab = ref('export') // 'export' | 'import'

// Export state
const exportFormat = ref('csv')
const exporting = ref(false)

// Import state
const importFile = ref(null)
const importPreviewing = ref(false)
const importPreviewData = ref(null)
const importing = ref(false)
const importResult = ref(null)
const skipDuplicates = ref(true)

// Month name helper
const monthNames = [
  'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
  'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember',
]
const monthLabel = computed(() => `${monthNames[props.month - 1]} ${props.year}`)

// Export formats
const formats = [
  {
    id: 'csv',
    label: 'CSV',
    description: 'Tabellendaten für Excel, Google Sheets',
    icon: 'chart-bar',
    ext: '.csv',
  },
  {
    id: 'ical',
    label: 'iCal',
    description: 'Kalender-Events für Apple/Google/Outlook',
    icon: 'calendar',
    ext: '.ics',
  },
  {
    id: 'pdf',
    label: 'PDF-Übersicht',
    description: 'Druckbarer visueller Wochenplan (HTML)',
    icon: 'printer',
    ext: '.html',
  },
]

// Download helper
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// Export function
async function doExport() {
  exporting.value = true
  try {
    let url = ''
    let mediaType = ''
    let defaultFilename = ''

    if (exportFormat.value === 'csv') {
      url = `/api/calendar/export-csv?month=${props.month}&year=${props.year}`
      mediaType = 'text/csv'
    } else if (exportFormat.value === 'ical') {
      url = `/api/calendar/export/ical?month=${props.month}&year=${props.year}`
      mediaType = 'text/calendar'
    } else if (exportFormat.value === 'pdf') {
      url = `/api/calendar/export/pdf?month=${props.month}&year=${props.year}`
      mediaType = 'text/html'
    }

    if (props.platformFilter) {
      url += `&platform=${props.platformFilter}`
    }

    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)

    const blob = await res.blob()

    // Extract filename from Content-Disposition or build default
    const disposition = res.headers.get('Content-Disposition')
    let filename = ''
    if (disposition) {
      const match = disposition.match(/filename="?([^"]+)"?/)
      if (match) filename = match[1]
    }
    if (!filename) {
      const fmt = formats.find(f => f.id === exportFormat.value)
      filename = `TREFF_calendar_${props.year}-${String(props.month).padStart(2, '0')}${fmt?.ext || '.csv'}`
    }

    downloadBlob(blob, filename)
    toast.success(`${exportFormat.value.toUpperCase()}-Export heruntergeladen`)

    // For PDF/HTML, also open in new tab for printing
    if (exportFormat.value === 'pdf') {
      const htmlUrl = URL.createObjectURL(blob)
      window.open(htmlUrl, '_blank')
      setTimeout(() => URL.revokeObjectURL(htmlUrl), 5000)
    }
  } catch (err) {
    console.error('Export error:', err)
    toast.error('Export fehlgeschlagen: ' + (err.message || 'Unbekannter Fehler'))
  } finally {
    exporting.value = false
  }
}

// Import: handle file select
function onFileSelect(event) {
  const file = event.target.files?.[0]
  if (file) {
    importFile.value = file
    importPreviewData.value = null
    importResult.value = null
  }
}

// Import: preview
async function previewImport() {
  if (!importFile.value) return
  importPreviewing.value = true
  importPreviewData.value = null
  importResult.value = null

  try {
    const formData = new FormData()
    formData.append('file', importFile.value)

    const res = await fetch('/api/calendar/import/csv/preview', {
      method: 'POST',
      headers: { Authorization: `Bearer ${auth.accessToken}` },
      body: formData,
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }

    importPreviewData.value = await res.json()
  } catch (err) {
    console.error('Import preview error:', err)
    toast.error('Vorschau fehlgeschlagen: ' + (err.message || 'Unbekannter Fehler'))
  } finally {
    importPreviewing.value = false
  }
}

// Import: commit
async function commitImport() {
  if (!importPreviewData.value) return
  importing.value = true

  try {
    const res = await fetch('/api/calendar/import/csv', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${auth.accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        rows: importPreviewData.value.rows,
        skip_duplicates: skipDuplicates.value,
      }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }

    importResult.value = await res.json()
    toast.success(importResult.value.message || 'Import abgeschlossen')
    emit('imported')
  } catch (err) {
    console.error('Import error:', err)
    toast.error('Import fehlgeschlagen: ' + (err.message || 'Unbekannter Fehler'))
  } finally {
    importing.value = false
  }
}

// Reset import state
function resetImport() {
  importFile.value = null
  importPreviewData.value = null
  importResult.value = null
  skipDuplicates.value = true
}

function close() {
  resetImport()
  emit('close')
}

// Computed: valid rows for import
const validRowCount = computed(() => {
  if (!importPreviewData.value) return 0
  let count = importPreviewData.value.valid_rows
  if (skipDuplicates.value) {
    count -= (importPreviewData.value.duplicate_rows || 0)
  }
  return Math.max(0, count)
})
</script>

<template>
  <!-- Modal Backdrop -->
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      @click.self="close"
    >
      <div
        class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-2xl mx-4 max-h-[85vh] flex flex-col overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-label="Kalender Export & Import"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Kalender Export & Import</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{{ monthLabel }}</p>
          </div>
          <button
            @click="close"
            class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="Schließen"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Tab Bar -->
        <div class="flex border-b border-gray-200 dark:border-gray-700 px-6">
          <button
            @click="activeTab = 'export'"
            :class="[
              'px-4 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'export'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
            ]"
          >
            <span class="flex items-center gap-1.5">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export
            </span>
          </button>
          <button
            @click="activeTab = 'import'"
            :class="[
              'px-4 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'import'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
            ]"
          >
            <span class="flex items-center gap-1.5">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              Import
            </span>
          </button>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto px-6 py-5">

          <!-- ====== EXPORT TAB ====== -->
          <div v-if="activeTab === 'export'">
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Wähle ein Format und exportiere den Content-Kalender für {{ monthLabel }}.
            </p>

            <!-- Format Selection -->
            <div class="space-y-3">
              <label
                v-for="fmt in formats"
                :key="fmt.id"
                :class="[
                  'flex items-center gap-4 p-4 rounded-xl border-2 cursor-pointer transition-all',
                  exportFormat === fmt.id
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                ]"
              >
                <input
                  type="radio"
                  :value="fmt.id"
                  v-model="exportFormat"
                  class="sr-only"
                />
                <AppIcon :name="fmt.icon" class="w-7 h-7" />
                <div class="flex-1">
                  <div class="font-medium text-gray-900 dark:text-white">{{ fmt.label }}</div>
                  <div class="text-sm text-gray-500 dark:text-gray-400">{{ fmt.description }}</div>
                </div>
                <div
                  :class="[
                    'w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors',
                    exportFormat === fmt.id
                      ? 'border-blue-500 bg-blue-500'
                      : 'border-gray-300 dark:border-gray-600'
                  ]"
                >
                  <svg v-if="exportFormat === fmt.id" class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                  </svg>
                </div>
              </label>
            </div>

            <!-- Export Button -->
            <div class="mt-6">
              <button
                @click="doExport"
                :disabled="exporting"
                class="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                <svg v-if="!exporting" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <svg v-else class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ exporting ? 'Exportiere...' : `${exportFormat.toUpperCase()} exportieren` }}
              </button>
            </div>
          </div>

          <!-- ====== IMPORT TAB ====== -->
          <div v-if="activeTab === 'import'">

            <!-- Import Result (show after successful import) -->
            <div v-if="importResult" class="space-y-4">
              <div class="flex items-center gap-3 p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
                <svg class="w-6 h-6 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <div class="font-medium text-green-800 dark:text-green-200">Import abgeschlossen</div>
                  <div class="text-sm text-green-600 dark:text-green-400">
                    {{ importResult.imported }} Posts importiert, {{ importResult.skipped }} übersprungen
                  </div>
                </div>
              </div>

              <div v-if="importResult.errors?.length" class="p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
                <div class="text-sm font-medium text-amber-700 dark:text-amber-300 mb-1">Warnungen:</div>
                <ul class="text-xs text-amber-600 dark:text-amber-400 list-disc pl-4 space-y-0.5">
                  <li v-for="(err, i) in importResult.errors" :key="i">{{ err }}</li>
                </ul>
              </div>

              <button
                @click="resetImport"
                class="w-full py-2 px-4 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              >
                Weiteren Import starten
              </button>
            </div>

            <!-- Import Steps (no result yet) -->
            <div v-else>
              <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Importiere Posting-Plaene aus einer CSV-Datei. Erwartete Spalten:
                <code class="text-xs bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded">date, time, title, category, platform, country, hashtags</code>
              </p>

              <!-- File Upload -->
              <div class="mb-4">
                <label
                  class="flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-xl cursor-pointer transition-colors"
                  :class="importFile ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/10' : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'"
                >
                  <input
                    type="file"
                    accept=".csv"
                    class="sr-only"
                    @change="onFileSelect"
                  />
                  <svg v-if="!importFile" class="w-8 h-8 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <div v-if="importFile" class="flex items-center gap-2 text-blue-600 dark:text-blue-400">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span class="font-medium">{{ importFile.name }}</span>
                  </div>
                  <span v-else class="text-sm text-gray-500 dark:text-gray-400">CSV-Datei wählen oder hierher ziehen</span>
                </label>
              </div>

              <!-- Preview Button -->
              <button
                v-if="importFile && !importPreviewData"
                @click="previewImport"
                :disabled="importPreviewing"
                class="w-full py-2.5 px-4 bg-gray-600 hover:bg-gray-700 disabled:opacity-50 text-white font-medium rounded-xl transition-colors flex items-center justify-center gap-2 mb-4"
              >
                <svg v-if="!importPreviewing" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ importPreviewing ? 'Analysiere...' : 'Vorschau anzeigen' }}
              </button>

              <!-- Preview Results -->
              <div v-if="importPreviewData" class="space-y-4">
                <!-- Summary Bar -->
                <div class="flex gap-3 text-sm">
                  <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-800">
                    <span class="font-medium">{{ importPreviewData.total_rows }}</span>
                    <span class="text-gray-500">Zeilen</span>
                  </div>
                  <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-100 dark:bg-green-900/30">
                    <span class="font-medium text-green-700 dark:text-green-400">{{ importPreviewData.valid_rows }}</span>
                    <span class="text-green-600 dark:text-green-500">gültig</span>
                  </div>
                  <div v-if="importPreviewData.error_rows > 0" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-100 dark:bg-red-900/30">
                    <span class="font-medium text-red-700 dark:text-red-400">{{ importPreviewData.error_rows }}</span>
                    <span class="text-red-600 dark:text-red-500">Fehler</span>
                  </div>
                  <div v-if="importPreviewData.duplicate_rows > 0" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-100 dark:bg-amber-900/30">
                    <span class="font-medium text-amber-700 dark:text-amber-400">{{ importPreviewData.duplicate_rows }}</span>
                    <span class="text-amber-600 dark:text-amber-500">Duplikate</span>
                  </div>
                </div>

                <!-- Detected Columns -->
                <div class="text-xs text-gray-500 dark:text-gray-400">
                  Erkannte Spalten:
                  <span v-for="(col, i) in importPreviewData.columns_detected" :key="col" class="font-medium text-gray-700 dark:text-gray-300">
                    {{ col }}<span v-if="i < importPreviewData.columns_detected.length - 1">, </span>
                  </span>
                </div>

                <!-- Row Preview Table -->
                <div class="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
                  <div class="overflow-x-auto max-h-60">
                    <table class="w-full text-xs">
                      <thead class="bg-gray-50 dark:bg-gray-800 sticky top-0">
                        <tr>
                          <th class="px-3 py-2 text-left font-medium text-gray-500">#</th>
                          <th class="px-3 py-2 text-left font-medium text-gray-500">Status</th>
                          <th class="px-3 py-2 text-left font-medium text-gray-500">Datum</th>
                          <th class="px-3 py-2 text-left font-medium text-gray-500">Zeit</th>
                          <th class="px-3 py-2 text-left font-medium text-gray-500">Titel</th>
                          <th class="px-3 py-2 text-left font-medium text-gray-500">Plattform</th>
                          <th class="px-3 py-2 text-left font-medium text-gray-500">Kategorie</th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
                        <tr
                          v-for="row in importPreviewData.rows"
                          :key="row.row_number"
                          :class="{
                            'bg-red-50 dark:bg-red-900/10': !row.valid,
                            'bg-amber-50 dark:bg-amber-900/10': row.valid && row.duplicate,
                          }"
                        >
                          <td class="px-3 py-1.5 text-gray-400">{{ row.row_number }}</td>
                          <td class="px-3 py-1.5">
                            <span v-if="!row.valid" class="text-red-500" title="Fehler">&#x2716;</span>
                            <span v-else-if="row.duplicate" class="text-amber-500" title="Duplikat">&#x26A0;</span>
                            <span v-else class="text-green-500" title="OK">&#x2714;</span>
                          </td>
                          <td class="px-3 py-1.5 font-mono">{{ row.date }}</td>
                          <td class="px-3 py-1.5 font-mono">{{ row.time }}</td>
                          <td class="px-3 py-1.5 max-w-[150px] truncate">{{ row.title }}</td>
                          <td class="px-3 py-1.5">{{ row.platform }}</td>
                          <td class="px-3 py-1.5">{{ row.category }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <!-- Warnings/Errors for rows -->
                <div v-if="importPreviewData.rows.some(r => r.warnings?.length || r.errors?.length)" class="max-h-32 overflow-y-auto text-xs space-y-1">
                  <template v-for="row in importPreviewData.rows" :key="'warn-' + row.row_number">
                    <div v-for="(err, i) in row.errors" :key="'e-' + row.row_number + '-' + i" class="text-red-600 dark:text-red-400">
                      Zeile {{ row.row_number }}: {{ err }}
                    </div>
                    <div v-for="(warn, i) in row.warnings" :key="'w-' + row.row_number + '-' + i" class="text-amber-600 dark:text-amber-400">
                      Zeile {{ row.row_number }}: {{ warn }}
                    </div>
                  </template>
                </div>

                <!-- Skip duplicates toggle -->
                <label v-if="importPreviewData.duplicate_rows > 0" class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    v-model="skipDuplicates"
                    class="w-4 h-4 text-blue-600 rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700 focus:ring-blue-500"
                  />
                  Duplikate überspringen ({{ importPreviewData.duplicate_rows }} Zeilen)
                </label>

                <!-- Import Button -->
                <div class="flex gap-3">
                  <button
                    @click="resetImport"
                    class="flex-1 py-2.5 px-4 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  >
                    Abbrechen
                  </button>
                  <button
                    @click="commitImport"
                    :disabled="importing || validRowCount === 0"
                    class="flex-1 py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-colors flex items-center justify-center gap-2"
                  >
                    <svg v-if="importing" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    {{ importing ? 'Importiere...' : `${validRowCount} Posts importieren` }}
                  </button>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  </Teleport>
</template>
