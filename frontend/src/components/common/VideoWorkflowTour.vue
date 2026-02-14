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
import { useTour } from '@/composables/useTour'

const TOUR_KEY = 'video-tools-overview'

const router = useRouter()
const { loadTourProgress, markTourSeen, hasSeenTour, loadedFromBackend, tourStartRequest, clearTourStartRequest } = useTour()

const isVisible = ref(false)
const currentStep = ref(0)

const steps = [
  {
    icon: '🎬',
    title: 'Die Video-Tool-Suite im Ueberblick',
    description:
      'TREFF Sprachreisen bietet dir 6 spezialisierte Video-Tools, die perfekt zusammenarbeiten. Der typische Workflow: Thumbnails erstellen, Overlays hinzufuegen, Clips zusammenschneiden, Branding-Templates anwenden, fuer Plattformen exportieren und Audio-Spuren mixen. Lass uns jeden Schritt kennenlernen!',
    page: null,
  },
  {
    icon: '🎬',
    title: '1. Thumbnail-Generator',
    description:
      'Erstelle klickstarke Vorschaubilder fuer deine Videos und Reels. Waehle einen Hintergrund, schreibe einen Hook-Text (max 5-7 Woerter) und exportiere in verschiedenen Groessen (YouTube 1280x720, Instagram 1080x1080, Reels 1080x1920). Gute Thumbnails steigern die Klickrate um bis zu 150%!',
    page: '/thumbnail-generator',
    navLabel: 'Thumbnails oeffnen',
  },
  {
    icon: '🎞️',
    title: '2. Video-Overlay-Editor',
    description:
      'Fuege Text, Logos, Sticker und Animationen ueber deine Videos. Ideal fuer TREFF-Branding, Untertitel und Call-to-Actions. Jeder Overlay-Layer kann einzeln positioniert, skaliert und zeitlich eingestellt werden. Mehrere Layer uebereinander sind moeglich — so entsteht professionelles Video-Branding.',
    page: '/video-overlays',
    navLabel: 'Overlay-Editor oeffnen',
  },
  {
    icon: '✂️',
    title: '3. Video-Composer (Schnitt)',
    description:
      'Kombiniere mehrere Clips zu einem fertigen Video. Ziehe Clips per Drag & Drop in die Timeline, kuerze sie auf die optimale Laenge und fuege Uebergaenge (Crossfade, Cut) hinzu. Waehle das Ausgabeformat: 9:16 fuer Reels/TikTok, 1:1 fuer Instagram Feed, 16:9 fuer YouTube. Ideal sind 15-60 Sekunden fuer Social Media.',
    page: '/video-composer',
    navLabel: 'Composer oeffnen',
  },
  {
    icon: '🏷️',
    title: '4. Video-Branding-Templates',
    description:
      'Verwalte wiederverwendbare Vorlagen fuer Intros, Outros, Bauchbinden und Texteinblendungen — alles im TREFF-Design (Blau #4C8BC2, Gelb #FDD000). Einmal erstellt, kannst du Templates immer wieder auf verschiedene Videos anwenden. Konsistentes Branding ueber alle Videos staerkt die Markenwahrnehmung.',
    page: '/video-templates',
    navLabel: 'Templates oeffnen',
  },
  {
    icon: '📤',
    title: '5. Video-Export',
    description:
      'Optimiere deine Videos fuer verschiedene Plattformen mit dem richtigen Seitenverhaeltnis, Fokuspunkt und Qualitaetseinstellungen. Nutze Batch-Export, um ein Video gleichzeitig in mehreren Formaten zu exportieren — z.B. 9:16 fuer Reels UND 1:1 fuer den Feed. Alle Varianten als ZIP herunterladen.',
    page: '/video-export',
    navLabel: 'Export oeffnen',
  },
  {
    icon: '🎵',
    title: '6. Audio-Mixer',
    description:
      'Fuege Hintergrundmusik, Soundeffekte und Voiceover zu deinen Videos hinzu. Regle die Lautstaerke jeder Spur einzeln (Musik 20-30%, Voiceover 100%, Original-Audio 50%) und fuege Fade-In/Fade-Out hinzu. Professioneller Sound macht den Unterschied zwischen amateurhaft und hochwertig!',
    page: '/audio-mixer',
    navLabel: 'Audio-Mixer oeffnen',
  },
  {
    icon: '🔄',
    title: 'Der komplette Workflow',
    description:
      'So arbeiten die Tools zusammen: (1) Erstelle ein Thumbnail fuer dein Video. (2) Fuege Overlays wie Logos und Untertitel hinzu. (3) Schneide Clips im Composer zusammen. (4) Wende Branding-Templates an (Intro, Outro). (5) Exportiere fuer Instagram, TikTok oder YouTube. (6) Mixe Hintergrundmusik dazu. Jede Seite hat auch eine eigene Mini-Tour — klicke den ?-Button oben rechts!',
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
            <span class="text-2xl">{{ currentStepData.icon }}</span>
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
            <span :class="currentStep === 1 ? 'font-bold text-[#4C8BC2]' : 'text-gray-400 dark:text-gray-500'">🎬</span>
            <span class="text-gray-300 dark:text-gray-600">→</span>
            <span :class="currentStep === 2 ? 'font-bold text-[#4C8BC2]' : 'text-gray-400 dark:text-gray-500'">🎞️</span>
            <span class="text-gray-300 dark:text-gray-600">→</span>
            <span :class="currentStep === 3 ? 'font-bold text-[#4C8BC2]' : 'text-gray-400 dark:text-gray-500'">✂️</span>
            <span class="text-gray-300 dark:text-gray-600">→</span>
            <span :class="currentStep === 4 ? 'font-bold text-[#4C8BC2]' : 'text-gray-400 dark:text-gray-500'">🏷️</span>
            <span class="text-gray-300 dark:text-gray-600">→</span>
            <span :class="currentStep === 5 ? 'font-bold text-[#4C8BC2]' : 'text-gray-400 dark:text-gray-500'">📤</span>
            <span class="text-gray-300 dark:text-gray-600">→</span>
            <span :class="currentStep === 6 ? 'font-bold text-[#4C8BC2]' : 'text-gray-400 dark:text-gray-500'">🎵</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex items-center justify-between px-6 py-4 border-t border-gray-100 dark:border-gray-700">
          <button
            @click="skipTour"
            class="text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            Tour ueberspringen
          </button>
          <div class="flex items-center gap-2">
            <button
              v-if="currentStep > 0"
              @click="prevStep"
              class="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              Zurueck
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
