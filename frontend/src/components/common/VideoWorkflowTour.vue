<script setup>
/**
 * VideoWorkflowTour – Overview tour for the Video-Tool-Suite.
 *
 * Shows a modal-style guided overview explaining the 6 video pages
 * and their workflow relationship:
 *   Thumbnails → Overlay → Schnitt → Branding → Export → Audio
 *
 * Auto-triggers once on the first visit to ANY video page.
 * Can be restarted from the TopBar tour button.
 */
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import { useTour } from '@/composables/useTour'

const TOUR_KEY = 'video-tools-overview'

const router = useRouter()
const { loadTourProgress, markTourSeen, hasSeenTour, loadedFromBackend, tourStartRequest, clearTourStartRequest } = useTour()

const isVisible = ref(false)
const currentStep = ref(0)

const steps = [
  {
    icon: 'film',
    title: 'Die Video-Tool-Suite im Überblick',
    description:
      'TREFF Sprachreisen bietet dir 6 spezialisierte Video-Tools, die perfekt zusammenarbeiten. Der typische Workflow: Thumbnails erstellen, Overlays hinzufügen, Clips zusammenschneiden, Branding-Templates anwenden, für Plattformen exportieren und Audio-Spuren mixen. Lass uns jeden Schritt kennenlernen!',
    page: null,
  },
  {
    icon: 'film',
    title: '1. Thumbnail-Generator',
    description:
      'Erstelle klickstarke Vorschaubilder für deine Videos und Reels. Wähle einen Hintergrund, schreibe einen Hook-Text (max 5-7 Wörter) und exportiere in verschiedenen Größen (YouTube 1280x720, Instagram 1080x1350 (4:5 Feed), Reels 1080x1920). Gute Thumbnails steigern die Klickrate um bis zu 150%!',
    page: '/video/thumbnails',
    navLabel: 'Thumbnails öffnen',
  },
  {
    icon: 'video-camera',
    title: '2. Video-Overlay-Editor',
    description:
      'Füge Text, Logos, Sticker und Animationen über deine Videos. Ideal für TREFF-Branding, Untertitel und Call-to-Actions. Jeder Overlay-Layer kann einzeln positioniert, skaliert und zeitlich eingestellt werden. Mehrere Layer übereinander sind möglich — so entsteht professionelles Video-Branding.',
    page: '/video/overlays',
    navLabel: 'Overlay-Editor öffnen',
  },
  {
    icon: 'scissors',
    title: '3. Video-Composer (Schnitt)',
    description:
      'Kombiniere mehrere Clips zu einem fertigen Video. Ziehe Clips per Drag & Drop in die Timeline, kürze sie auf die optimale Länge und füge Übergänge (Crossfade, Cut) hinzu. Wähle das Ausgabeformat: 9:16 für Reels/TikTok, 4:5 für Instagram Feed, 16:9 für YouTube. Ideal sind 15-60 Sekunden für Social Media.',
    page: '/video/composer',
    navLabel: 'Composer öffnen',
  },
  {
    icon: 'tag',
    title: '4. Video-Branding-Templates',
    description:
      'Verwalte wiederverwendbare Vorlagen für Intros, Outros, Bauchbinden und Texteinblendungen — alles im TREFF-Design (Blau #4C8BC2, Gelb #FDD000). Einmal erstellt, kannst du Templates immer wieder auf verschiedene Videos anwenden. Konsistentes Branding über alle Videos stärkt die Markenwahrnehmung.',
    page: '/video/templates',
    navLabel: 'Templates öffnen',
  },
  {
    icon: 'export',
    title: '5. Video-Export',
    description:
      'Optimiere deine Videos für verschiedene Plattformen mit dem richtigen Seitenverhältnis, Fokuspunkt und Qualitätseinstellungen. Nutze Batch-Export, um ein Video gleichzeitig in mehreren Formaten zu exportieren — z.B. 9:16 für Reels UND 4:5 für den Feed. Alle Varianten als ZIP herunterladen.',
    page: '/video/export',
    navLabel: 'Export öffnen',
  },
  {
    icon: 'musical-note',
    title: '6. Audio-Mixer',
    description:
      'Füge Hintergrundmusik, Soundeffekte und Voiceover zu deinen Videos hinzu. Regle die Lautstärke jeder Spur einzeln (Musik 20-30%, Voiceover 100%, Original-Audio 50%) und füge Fade-In/Fade-Out hinzu. Professioneller Sound macht den Unterschied zwischen amateurhaft und hochwertig!',
    page: '/video/audio-mixer',
    navLabel: 'Audio-Mixer öffnen',
  },
  {
    icon: 'arrow-path',
    title: 'Der komplette Workflow',
    description:
      'So arbeiten die Tools zusammen: (1) Erstelle ein Thumbnail für dein Video. (2) Füge Overlays wie Logos und Untertitel hinzu. (3) Schneide Clips im Composer zusammen. (4) Wende Branding-Templates an (Intro, Outro). (5) Exportiere für Instagram, TikTok oder YouTube. (6) Mixe Hintergrundmusik dazu. Jede Seite hat auch eine eigene Mini-Tour — klicke den ?-Button oben rechts!',
    page: null,
  },
]

const totalSteps = steps.length
const currentStepData = computed(() => steps[currentStep.value])
const isLastStep = computed(() => currentStep.value === totalSteps - 1)

function nextStep() {
  if (currentStep.value < totalSteps - 1) {
    currentStep.value++
  } else {
    completeTour()
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

async function completeTour() {
  isVisible.value = false
  await markTourSeen(TOUR_KEY)
}

function skipTour() {
  completeTour()
}

function startTour() {
  currentStep.value = 0
  isVisible.value = true
}

function navigateToPage(path) {
  if (path) {
    completeTour()
    router.push(path)
  }
}

defineExpose({ startTour })

// Watch for external tour start requests (from TopBar)
watch(tourStartRequest, (req) => {
  if (req && req.pageKey === TOUR_KEY) {
    clearTourStartRequest()
    startTour()
  }
})

// Auto-start on first visit to any video page
onMounted(async () => {
  await loadTourProgress()

  if (!hasSeenTour(TOUR_KEY)) {
    setTimeout(() => {
      startTour()
    }, 400)
  }
})
</script>

<template>
  <Teleport to="body">
    <div v-if="isVisible" class="fixed inset-0 z-[10001] flex items-center justify-center" data-testid="video-workflow-tour">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/60" @click.stop></div>

      <!-- Modal Card -->
      <div class="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-lg w-full mx-4 overflow-hidden">
        <!-- Header with gradient -->
        <div class="bg-gradient-to-r from-[#4C8BC2] to-[#3B7AB1] px-6 py-4">
          <div class="flex items-center gap-2">
            <AppIcon :name="currentStepData.icon" class="w-7 h-7 text-white" />
            <div>
              <p class="text-[10px] uppercase tracking-wider font-semibold text-white/70">
                Video-Tool-Suite Tour
              </p>
              <h3 class="text-lg font-bold text-white">
                {{ currentStepData.title }}
              </h3>
            </div>
          </div>
        </div>

        <!-- Step indicator dots -->
        <div class="flex items-center gap-1.5 px-6 pt-4">
          <div
            v-for="(_, idx) in steps"
            :key="idx"
            class="h-1.5 rounded-full transition-all duration-200"
            :class="[
              idx === currentStep
                ? 'w-6 bg-[#4C8BC2]'
                : idx < currentStep
                  ? 'w-3 bg-[#4C8BC2]/40'
                  : 'w-3 bg-gray-200 dark:bg-gray-600',
            ]"
          ></div>
          <span class="text-xs text-gray-400 dark:text-gray-500 ml-auto">
            {{ currentStep + 1 }}/{{ totalSteps }}
          </span>
        </div>

        <!-- Content -->
        <div class="px-6 py-4">
          <p class="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
            {{ currentStepData.description }}
          </p>

          <!-- Navigation link to the page -->
          <button
            v-if="currentStepData.page"
            @click="navigateToPage(currentStepData.page)"
            class="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-[#4C8BC2] hover:text-[#3B7AB1] transition-colors"
          >
            <span>{{ currentStepData.navLabel }}</span>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>

        <!-- Workflow steps visual (compact) -->
        <div class="px-6 pb-2">
          <div class="flex items-center justify-center gap-1 text-xs">
            <AppIcon name="film" class="w-4 h-4" :class="currentStep === 1 ? 'text-[#4C8BC2]' : 'text-gray-400 dark:text-gray-500'" />
            <span class="text-gray-300 dark:text-gray-600">&rarr;</span>
            <AppIcon name="video-camera" class="w-4 h-4" :class="currentStep === 2 ? 'text-[#4C8BC2]' : 'text-gray-400 dark:text-gray-500'" />
            <span class="text-gray-300 dark:text-gray-600">&rarr;</span>
            <AppIcon name="scissors" class="w-4 h-4" :class="currentStep === 3 ? 'text-[#4C8BC2]' : 'text-gray-400 dark:text-gray-500'" />
            <span class="text-gray-300 dark:text-gray-600">&rarr;</span>
            <AppIcon name="tag" class="w-4 h-4" :class="currentStep === 4 ? 'text-[#4C8BC2]' : 'text-gray-400 dark:text-gray-500'" />
            <span class="text-gray-300 dark:text-gray-600">&rarr;</span>
            <AppIcon name="export" class="w-4 h-4" :class="currentStep === 5 ? 'text-[#4C8BC2]' : 'text-gray-400 dark:text-gray-500'" />
            <span class="text-gray-300 dark:text-gray-600">&rarr;</span>
            <AppIcon name="musical-note" class="w-4 h-4" :class="currentStep === 6 ? 'text-[#4C8BC2]' : 'text-gray-400 dark:text-gray-500'" />
          </div>
        </div>

        <!-- Actions -->
        <div class="flex items-center justify-between px-6 py-4 border-t border-gray-100 dark:border-gray-700">
          <button
            @click="skipTour"
            class="text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            Tour überspringen
          </button>
          <div class="flex items-center gap-2">
            <button
              v-if="currentStep > 0"
              @click="prevStep"
              class="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              Zurück
            </button>
            <button
              @click="nextStep"
              class="px-4 py-1.5 text-xs font-medium text-white bg-[#4C8BC2] rounded-lg hover:bg-[#3B7AB1] transition-colors"
            >
              {{ isLastStep ? 'Tour beenden' : 'Weiter' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
