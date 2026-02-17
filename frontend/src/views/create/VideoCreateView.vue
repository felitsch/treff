<script setup>
/**
 * VideoCreateView — Unified "Brand This Video" page
 *
 * Replaces the 5 separate video tool pages with a single step-flow on one page:
 * 1. Upload → 2. Branding (Intro/Outro) → 3. Lower Third → 4. Musik → 5. Preview → 6. Export
 *
 * All sections are visible on one scrollable page (no wizard navigation).
 * Sections expand/collapse and visually indicate completion status.
 */
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import VideoUploadPreview from '@/components/video/VideoUploadPreview.vue'
import BrandingSelector from '@/components/video/BrandingSelector.vue'
import LowerThirdEditor from '@/components/video/LowerThirdEditor.vue'
import MusicSelector from '@/components/video/MusicSelector.vue'
import MultiPlatformExport from '@/components/video/MultiPlatformExport.vue'
import ContentMultiplierPanel from '@/components/video/ContentMultiplierPanel.vue'
import ThumbnailAISuggestions from '@/components/video/ThumbnailAISuggestions.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const router = useRouter()
const toast = useToast()

// ─── Core state ─────────────────────────────────────────────
const selectedAsset = ref(null)
const selectedIntro = ref(null)
const selectedOutro = ref(null)

const lowerThird = ref({
  enabled: false,
  name: '',
  title: '',
  fontFamily: 'Inter',
  fontSize: 24,
  textColor: '#FFFFFF',
  bgColor: '#1A1A2E',
  bgOpacity: 0.85,
  position: 'bottom-left',
  animation: 'slide_in_left',
  startTime: 0,
  endTime: 0,
})

const musicConfig = ref({
  enabled: false,
  trackId: null,
  trackName: '',
  volume: 0.3,
  fadeIn: 1.0,
  fadeOut: 2.0,
})

// ─── Section management ─────────────────────────────────────
const sections = [
  { key: 'upload', label: '1. Video waehlen', icon: 'film', description: 'Video hochladen oder aus der Bibliothek waehlen' },
  { key: 'branding', label: '2. Branding', icon: 'tag', description: 'Intro/Outro-Templates fuer Laender-Branding' },
  { key: 'lowerthird', label: '3. Lower Third', icon: 'chat-bubble', description: 'Name & Titel als Texteinblendung' },
  { key: 'music', label: '4. Musik', icon: 'musical-note', description: 'Hintergrundmusik auswaehlen und mischen' },
  { key: 'thumbnail', label: '5. Thumbnail', icon: 'photo', description: 'AI-Thumbnail aus Video-Frames mit Text-Overlay und A/B-Varianten' },
  { key: 'preview', label: '6. Vorschau', icon: 'eye', description: 'Finales Video mit allen Overlays' },
  { key: 'export', label: '7. Export', icon: 'export', description: 'Multi-Format-Export fuer alle Plattformen' },
  { key: 'multiply', label: '8. Multiplizieren', icon: 'rocket', description: '1 Video → 5 Formate als Draft-Posts' },
]

const expandedSections = ref({
  upload: true,
  branding: false,
  lowerthird: false,
  music: false,
  thumbnail: false,
  preview: false,
  export: false,
  multiply: false,
})

// Section completion status
const sectionStatus = computed(() => ({
  upload: selectedAsset.value ? 'complete' : 'pending',
  branding: selectedIntro.value || selectedOutro.value ? 'complete' : 'optional',
  lowerthird: lowerThird.value.enabled && lowerThird.value.name ? 'complete' : 'optional',
  music: musicConfig.value.enabled && musicConfig.value.trackId ? 'complete' : 'optional',
  thumbnail: selectedAsset.value ? 'ready' : 'locked',
  preview: selectedAsset.value ? 'ready' : 'locked',
  export: selectedAsset.value ? 'ready' : 'locked',
  multiply: selectedAsset.value ? 'ready' : 'locked',
}))

function toggleSection(key) {
  expandedSections.value[key] = !expandedSections.value[key]
}

function statusIcon(status) {
  switch (status) {
    case 'complete': return '&#10003;'
    case 'optional': return '○'
    case 'ready': return '→'
    case 'locked': return '&#128274;'
    default: return '○'
  }
}

function statusColor(status) {
  switch (status) {
    case 'complete': return 'text-green-500 bg-green-100 dark:bg-green-900/30'
    case 'optional': return 'text-gray-400 bg-gray-100 dark:bg-gray-700'
    case 'ready': return 'text-blue-500 bg-blue-100 dark:bg-blue-900/30'
    case 'locked': return 'text-gray-300 bg-gray-50 dark:bg-gray-800'
    default: return 'text-gray-400 bg-gray-100 dark:bg-gray-700'
  }
}

// Auto-expand next section when asset is selected
watch(selectedAsset, (asset) => {
  if (asset) {
    expandedSections.value.branding = true
  }
})

// ─── Preview state ──────────────────────────────────────────
const previewLoading = ref(false)
const previewUrl = ref(null)

const assetUrl = computed(() => {
  if (!selectedAsset.value) return ''
  return `/api/assets/${selectedAsset.value.id}/file`
})

// ─── Timeline markers ──────────────────────────────────────
const timelineMarkers = computed(() => {
  if (!selectedAsset.value) return []
  const markers = []
  const videoDuration = selectedAsset.value.duration_seconds || 30

  if (selectedIntro.value) {
    markers.push({
      label: 'Intro',
      color: '#3B82F6',
      start: 0,
      duration: selectedIntro.value.duration_seconds || 3,
    })
  }

  markers.push({
    label: 'Video',
    color: '#10B981',
    start: selectedIntro.value ? (selectedIntro.value.duration_seconds || 3) : 0,
    duration: videoDuration,
  })

  if (lowerThird.value.enabled) {
    markers.push({
      label: 'Lower Third',
      color: '#F59E0B',
      start: selectedIntro.value ? (selectedIntro.value.duration_seconds || 3) : 0,
      duration: lowerThird.value.endTime || videoDuration,
      overlay: true,
    })
  }

  if (selectedOutro.value) {
    const outroStart = (selectedIntro.value ? selectedIntro.value.duration_seconds || 3 : 0) + videoDuration
    markers.push({
      label: 'Outro',
      color: '#8B5CF6',
      start: outroStart,
      duration: selectedOutro.value.duration_seconds || 3,
    })
  }

  if (musicConfig.value.enabled) {
    markers.push({
      label: 'Musik',
      color: '#EC4899',
      start: 0,
      duration: totalDuration.value,
      overlay: true,
    })
  }

  return markers
})

const totalDuration = computed(() => {
  let total = selectedAsset.value?.duration_seconds || 0
  if (selectedIntro.value) total += selectedIntro.value.duration_seconds || 3
  if (selectedOutro.value) total += selectedOutro.value.duration_seconds || 3
  return total
})

function formatDuration(seconds) {
  if (!seconds) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

// ─── Export handling ────────────────────────────────────────
function onExportComplete(results) {
  toast.success('Video-Export abgeschlossen!')
}

// ─── Mobile responsive ─────────────────────────────────────
const isMobile = ref(false)

function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-6" data-testid="video-create-view">
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center gap-3 mb-2">
        <button
          @click="router.push('/create')"
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        >
          &larr;
        </button>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Brand This Video</h1>
      </div>
      <p class="text-sm text-gray-600 dark:text-gray-400 ml-8">
        Erstelle gebrandete Social-Media-Videos in einem Schritt: Upload, Intro/Outro, Lower Third, Musik und Multi-Format-Export.
      </p>
    </div>

    <!-- Progress summary bar -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 mb-6 shadow-sm">
      <div class="flex items-center gap-4 overflow-x-auto pb-1">
        <div
          v-for="section in sections"
          :key="section.key"
          class="flex items-center gap-2 shrink-0"
        >
          <div
            :class="[
              'w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-all',
              statusColor(sectionStatus[section.key]),
            ]"
            v-html="statusIcon(sectionStatus[section.key])"
          />
          <span class="text-xs font-medium text-gray-600 dark:text-gray-400 hidden sm:inline">
            {{ section.label.replace(/^\d+\.\s*/, '') }}
          </span>
          <span v-if="section.key !== 'export'" class="text-gray-300 dark:text-gray-600 hidden sm:inline">→</span>
        </div>
      </div>
      <div v-if="selectedAsset" class="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
        <p class="text-xs text-gray-500 dark:text-gray-400">
          Gesamtdauer: <span class="font-semibold text-gray-700 dark:text-gray-300">{{ formatDuration(totalDuration) }}</span>
          <span v-if="selectedIntro"> · Intro: {{ selectedIntro.name }}</span>
          <span v-if="selectedOutro"> · Outro: {{ selectedOutro.name }}</span>
          <span v-if="lowerThird.enabled"> · Lower Third</span>
          <span v-if="musicConfig.enabled"> · Musik</span>
        </p>
      </div>
    </div>

    <!-- Sections -->
    <div class="space-y-4">
      <!-- Each section is an expandable card -->
      <div
        v-for="section in sections"
        :key="section.key"
        :class="[
          'bg-white dark:bg-gray-800 rounded-xl border transition-all overflow-hidden',
          expandedSections[section.key]
            ? 'border-blue-200 dark:border-blue-800 shadow-md'
            : 'border-gray-200 dark:border-gray-700 shadow-sm',
        ]"
        :data-testid="`section-${section.key}`"
      >
        <!-- Section header -->
        <button
          @click="toggleSection(section.key)"
          class="w-full flex items-center gap-3 px-5 py-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
        >
          <div
            :class="[
              'w-8 h-8 rounded-lg flex items-center justify-center text-base shrink-0 transition-all',
              statusColor(sectionStatus[section.key]),
            ]"
            v-html="statusIcon(sectionStatus[section.key])"
          />
          <div class="flex-1 min-w-0">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-1.5">
              <AppIcon :name="section.icon" class="w-4 h-4 inline-block" />
              {{ section.label }}
            </h3>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ section.description }}</p>
          </div>

          <!-- Status badge -->
          <span
            v-if="sectionStatus[section.key] === 'complete'"
            class="text-xs px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 font-medium"
          >
            Fertig
          </span>
          <span
            v-else-if="sectionStatus[section.key] === 'optional'"
            class="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 font-medium"
          >
            Optional
          </span>

          <!-- Expand/collapse chevron -->
          <svg
            :class="['w-5 h-5 text-gray-400 transition-transform', expandedSections[section.key] ? 'rotate-180' : '']"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <!-- Section content -->
        <div v-show="expandedSections[section.key]" class="px-5 pb-5 pt-1">
          <!-- 1. Upload -->
          <VideoUploadPreview
            v-if="section.key === 'upload'"
            :selectedAsset="selectedAsset"
            @select="selectedAsset = $event"
          />

          <!-- 2. Branding -->
          <BrandingSelector
            v-if="section.key === 'branding'"
            :selectedIntro="selectedIntro"
            :selectedOutro="selectedOutro"
            @update:selectedIntro="selectedIntro = $event"
            @update:selectedOutro="selectedOutro = $event"
          />

          <!-- 3. Lower Third -->
          <LowerThirdEditor
            v-if="section.key === 'lowerthird'"
            v-model="lowerThird"
          />

          <!-- 4. Music -->
          <MusicSelector
            v-if="section.key === 'music'"
            v-model="musicConfig"
          />

          <!-- 5. Thumbnail AI -->
          <ThumbnailAISuggestions
            v-if="section.key === 'thumbnail'"
            :videoAsset="selectedAsset"
          />

          <!-- 6. Preview -->
          <div v-if="section.key === 'preview'" class="space-y-4">
            <div v-if="!selectedAsset" class="text-center py-8 text-sm text-gray-500 dark:text-gray-400">
              Bitte waehle zuerst ein Video aus (Schritt 1).
            </div>
            <template v-else>
              <!-- Video preview -->
              <div class="bg-gray-900 rounded-xl overflow-hidden">
                <video
                  :src="assetUrl"
                  controls
                  class="w-full max-h-[400px] object-contain"
                  preload="metadata"
                />
              </div>

              <!-- Timeline visualization -->
              <div v-if="timelineMarkers.length > 0" class="space-y-2" data-testid="video-timeline">
                <h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Timeline</h4>
                <div class="relative bg-gray-100 dark:bg-gray-700 rounded-lg p-3">
                  <!-- Main timeline bar -->
                  <div class="relative h-8 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                    <div
                      v-for="(marker, idx) in timelineMarkers.filter(m => !m.overlay)"
                      :key="idx"
                      class="absolute top-0 h-full flex items-center justify-center text-[10px] font-medium text-white"
                      :style="{
                        left: `${(marker.start / totalDuration) * 100}%`,
                        width: `${(marker.duration / totalDuration) * 100}%`,
                        backgroundColor: marker.color,
                      }"
                    >
                      {{ marker.label }}
                    </div>
                  </div>

                  <!-- Overlay markers -->
                  <div
                    v-for="(marker, idx) in timelineMarkers.filter(m => m.overlay)"
                    :key="'overlay-' + idx"
                    class="mt-1"
                  >
                    <div class="relative h-4 rounded-full overflow-hidden" style="opacity: 0.6">
                      <div
                        class="absolute top-0 h-full rounded-full flex items-center justify-center text-[9px] font-medium text-white"
                        :style="{
                          left: `${(marker.start / totalDuration) * 100}%`,
                          width: `${(marker.duration / totalDuration) * 100}%`,
                          backgroundColor: marker.color,
                        }"
                      >
                        {{ marker.label }}
                      </div>
                    </div>
                  </div>

                  <!-- Duration label -->
                  <div class="flex justify-between mt-2 text-[10px] text-gray-500 dark:text-gray-400">
                    <span>0:00</span>
                    <span>{{ formatDuration(totalDuration) }}</span>
                  </div>
                </div>
              </div>

              <!-- Summary of applied effects -->
              <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 space-y-1">
                <h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Zusammenfassung</h4>
                <p class="text-sm text-gray-700 dark:text-gray-300">
                  <span class="font-medium">Video:</span> {{ selectedAsset.filename || selectedAsset.original_filename }}
                  ({{ formatDuration(selectedAsset.duration_seconds) }})
                </p>
                <p v-if="selectedIntro" class="text-sm text-gray-700 dark:text-gray-300">
                  <span class="font-medium">Intro:</span> {{ selectedIntro.name }} ({{ selectedIntro.duration_seconds }}s)
                </p>
                <p v-if="selectedOutro" class="text-sm text-gray-700 dark:text-gray-300">
                  <span class="font-medium">Outro:</span> {{ selectedOutro.name }} ({{ selectedOutro.duration_seconds }}s)
                </p>
                <p v-if="lowerThird.enabled" class="text-sm text-gray-700 dark:text-gray-300">
                  <span class="font-medium">Lower Third:</span> {{ lowerThird.name }} — {{ lowerThird.title }}
                </p>
                <p v-if="musicConfig.enabled && musicConfig.trackName" class="text-sm text-gray-700 dark:text-gray-300">
                  <span class="font-medium">Musik:</span> {{ musicConfig.trackName }} ({{ Math.round(musicConfig.volume * 100) }}%)
                </p>
                <p class="text-sm font-medium text-gray-900 dark:text-white mt-2">
                  Gesamtdauer: {{ formatDuration(totalDuration) }}
                </p>
              </div>
            </template>
          </div>

          <!-- 6. Export -->
          <div v-if="section.key === 'export'">
            <div v-if="!selectedAsset" class="text-center py-8 text-sm text-gray-500 dark:text-gray-400">
              Bitte waehle zuerst ein Video aus (Schritt 1).
            </div>
            <MultiPlatformExport
              v-else
              :videoAsset="selectedAsset"
              :introTemplate="selectedIntro"
              :outroTemplate="selectedOutro"
              :lowerThird="lowerThird"
              :musicConfig="musicConfig"
              @export-complete="onExportComplete"
            />
          </div>

          <!-- 7. Content Multiplier -->
          <div v-if="section.key === 'multiply'">
            <div v-if="!selectedAsset" class="text-center py-8 text-sm text-gray-500 dark:text-gray-400">
              Bitte waehle zuerst ein Video aus (Schritt 1).
            </div>
            <ContentMultiplierPanel
              v-else
              :videoAsset="selectedAsset"
              @generated="onExportComplete"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile: Floating action button for quick-expand Export -->
    <div
      v-if="isMobile && selectedAsset"
      class="fixed bottom-6 right-6 z-50"
    >
      <button
        @click="expandedSections.export = true; nextTick(() => document.querySelector('[data-testid=section-export]')?.scrollIntoView({ behavior: 'smooth' }))"
        class="w-14 h-14 bg-blue-600 text-white rounded-full shadow-xl flex items-center justify-center text-xl hover:bg-blue-700 transition-all"
      >
        <AppIcon name="export" class="w-6 h-6" />
      </button>
    </div>
  </div>
</template>
