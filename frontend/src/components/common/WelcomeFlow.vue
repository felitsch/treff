<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['complete', 'skip'])

const currentStep = ref(0)
const totalSteps = 6

const progress = computed(() => ((currentStep.value + 1) / totalSteps) * 100)

function nextStep() {
  if (currentStep.value < totalSteps - 1) {
    currentStep.value++
  } else {
    emit('complete')
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

function skipAll() {
  emit('skip')
}

// Area data for step 2
const mainAreas = [
  {
    icon: '✏️',
    title: 'Content-Erstellung',
    desc: 'Posts erstellen mit Templates, KI-Texten und CTA-Bibliothek',
    color: 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-700',
    iconBg: 'bg-blue-100 dark:bg-blue-800',
    pages: ['Post erstellen', 'Templates', 'Assets', 'Students'],
  },
  {
    icon: '📅',
    title: 'Planung',
    desc: 'Content-Kalender, Wochenplaner und Story-Arcs organisieren',
    color: 'bg-amber-50 dark:bg-amber-900/30 border-amber-200 dark:border-amber-700',
    iconBg: 'bg-amber-100 dark:bg-amber-800',
    pages: ['Kalender', 'Wochenplaner', 'Story-Arcs', 'Formate'],
  },
  {
    icon: '🎬',
    title: 'Video-Tools',
    desc: 'Video-Branding, Export, Audio-Mixer und Overlays',
    color: 'bg-purple-50 dark:bg-purple-900/30 border-purple-200 dark:border-purple-700',
    iconBg: 'bg-purple-100 dark:bg-purple-800',
    pages: ['Video-Templates', 'Video-Export', 'Audio-Mixer', 'Overlays'],
  },
  {
    icon: '📊',
    title: 'Analyse',
    desc: 'Performance tracken, Ziele setzen und Content optimieren',
    color: 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-700',
    iconBg: 'bg-green-100 dark:bg-green-800',
    pages: ['Analytics', 'History', 'Dashboard'],
  },
]

// Workflow steps for step 3
const workflowSteps = [
  { icon: '💡', label: 'Idee', desc: 'Content-Vorschlaege oder eigene Ideen' },
  { icon: '📋', label: 'Planen', desc: 'Wochenplaner oder Kalender nutzen' },
  { icon: '✏️', label: 'Erstellen', desc: 'Post mit Templates und KI gestalten' },
  { icon: '📅', label: 'Schedulen', desc: 'Datum und Uhrzeit festlegen' },
  { icon: '📊', label: 'Analysieren', desc: 'Performance auswerten' },
]

// Connection data for step 4
const connections = [
  {
    from: 'Students',
    fromIcon: '👤',
    to: 'Story-Arcs',
    toIcon: '📖',
    desc: 'Studenten-Profile fuettern Story-Arcs mit persoenlichen Geschichten',
    color: 'text-blue-500',
  },
  {
    from: 'Story-Arcs',
    fromIcon: '📖',
    to: 'Kalender',
    toIcon: '📅',
    desc: 'Story-Arc Episoden erscheinen als Timeline im Kalender',
    color: 'text-purple-500',
  },
  {
    from: 'Formate',
    fromIcon: '🔄',
    to: 'Wochenplaner',
    toIcon: '📋',
    desc: 'Wiederkehrende Formate werden vom Wochenplaner beruecksichtigt',
    color: 'text-amber-500',
  },
  {
    from: 'Templates',
    fromIcon: '🎨',
    to: 'Post erstellen',
    toIcon: '✏️',
    desc: 'Templates bilden die Grundlage fuer neue Posts',
    color: 'text-green-500',
  },
  {
    from: 'CTA-Bibliothek',
    fromIcon: '📢',
    to: 'Post erstellen',
    toIcon: '✏️',
    desc: 'Vorgefertigte Call-to-Actions fuer schnelle Post-Erstellung',
    color: 'text-red-500',
  },
]
</script>

<template>
  <Teleport to="body">
    <Transition name="welcome-fade">
      <div
        v-if="show"
        class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
      >
        <div class="relative w-full max-w-3xl mx-4 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
          <!-- Progress bar -->
          <div class="h-1.5 bg-gray-100 dark:bg-gray-800">
            <div
              class="h-full bg-gradient-to-r from-[#4C8BC2] to-[#FDD000] transition-all duration-500 ease-out rounded-r-full"
              :style="{ width: progress + '%' }"
            />
          </div>

          <!-- Header with step indicator and skip -->
          <div class="flex items-center justify-between px-6 pt-4 pb-2">
            <span class="text-xs font-medium text-gray-400 dark:text-gray-500">
              Schritt {{ currentStep + 1 }} von {{ totalSteps }}
            </span>
            <button
              @click="skipAll"
              class="text-xs font-medium text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              Ueberspringen
            </button>
          </div>

          <!-- Content area (scrollable) -->
          <div class="flex-1 overflow-y-auto px-6 pb-6">
            <!-- Step 0: Welcome -->
            <Transition name="slide-step" mode="out-in">
              <div v-if="currentStep === 0" key="step0" class="text-center py-8">
                <div class="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-[#4C8BC2] to-[#FDD000] rounded-2xl flex items-center justify-center shadow-lg">
                  <span class="text-4xl">🎓</span>
                </div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                  Willkommen beim TREFF Post-Generator!
                </h2>
                <p class="text-gray-500 dark:text-gray-400 max-w-lg mx-auto leading-relaxed">
                  Dieses Tool hilft dir, professionelle Instagram- und TikTok-Posts
                  fuer TREFF Sprachreisen in Minuten statt Stunden zu erstellen.
                </p>
                <div class="mt-8 flex flex-wrap items-center justify-center gap-3 text-sm text-gray-400 dark:text-gray-500">
                  <span class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 dark:bg-gray-800 rounded-full">
                    🤖 KI-Textgenerierung
                  </span>
                  <span class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 dark:bg-gray-800 rounded-full">
                    🎨 Anpassbare Templates
                  </span>
                  <span class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 dark:bg-gray-800 rounded-full">
                    📅 Content-Kalender
                  </span>
                  <span class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 dark:bg-gray-800 rounded-full">
                    📊 Analytics
                  </span>
                </div>
              </div>

              <!-- Step 1: 4 Main Areas -->
              <div v-else-if="currentStep === 1" key="step1" class="py-6">
                <div class="text-center mb-6">
                  <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
                    Die 4 Hauptbereiche
                  </h2>
                  <p class="text-sm text-gray-500 dark:text-gray-400">
                    Der Post-Generator ist in vier Bereiche gegliedert
                  </p>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div
                    v-for="area in mainAreas"
                    :key="area.title"
                    class="border rounded-xl p-4 transition-all hover:shadow-md"
                    :class="area.color"
                  >
                    <div class="flex items-start gap-3">
                      <div
                        class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                        :class="area.iconBg"
                      >
                        <span class="text-xl">{{ area.icon }}</span>
                      </div>
                      <div class="min-w-0">
                        <h3 class="font-semibold text-gray-900 dark:text-white text-sm">
                          {{ area.title }}
                        </h3>
                        <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 leading-relaxed">
                          {{ area.desc }}
                        </p>
                        <div class="flex flex-wrap gap-1 mt-2">
                          <span
                            v-for="page in area.pages"
                            :key="page"
                            class="text-[10px] font-medium px-1.5 py-0.5 rounded bg-white/70 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300"
                          >
                            {{ page }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Step 2: Workflow Diagram -->
              <div v-else-if="currentStep === 2" key="step2" class="py-6">
                <div class="text-center mb-6">
                  <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
                    Dein typischer Workflow
                  </h2>
                  <p class="text-sm text-gray-500 dark:text-gray-400">
                    Von der Idee bis zur Analyse - so erstellst du Content
                  </p>
                </div>
                <!-- Workflow steps with arrows -->
                <div class="flex flex-col items-center gap-1">
                  <template v-for="(step, i) in workflowSteps" :key="step.label">
                    <div
                      class="flex items-center gap-4 w-full max-w-md bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-5 py-3.5 shadow-sm hover:shadow-md transition-all"
                    >
                      <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-[#4C8BC2]/10 to-[#FDD000]/10 dark:from-[#4C8BC2]/20 dark:to-[#FDD000]/20 flex items-center justify-center flex-shrink-0">
                        <span class="text-2xl">{{ step.icon }}</span>
                      </div>
                      <div>
                        <div class="flex items-center gap-2">
                          <span class="text-xs font-bold text-[#4C8BC2] uppercase tracking-wider">
                            {{ i + 1 }}. {{ step.label }}
                          </span>
                        </div>
                        <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                          {{ step.desc }}
                        </p>
                      </div>
                    </div>
                    <!-- Arrow between steps -->
                    <div
                      v-if="i < workflowSteps.length - 1"
                      class="flex items-center justify-center w-8 h-6"
                    >
                      <svg class="w-4 h-4 text-[#4C8BC2]" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                      </svg>
                    </div>
                  </template>
                </div>
              </div>

              <!-- Step 3: How Pages Connect (Flowchart) -->
              <div v-else-if="currentStep === 3" key="step3" class="py-6">
                <div class="text-center mb-6">
                  <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
                    Wie alles zusammenhaengt
                  </h2>
                  <p class="text-sm text-gray-500 dark:text-gray-400">
                    Die Seiten arbeiten zusammen - hier der Ueberblick
                  </p>
                </div>
                <div class="space-y-3 max-w-lg mx-auto">
                  <div
                    v-for="conn in connections"
                    :key="conn.from + conn.to"
                    class="flex items-center gap-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3 hover:shadow-md transition-all"
                  >
                    <!-- From -->
                    <div class="flex flex-col items-center flex-shrink-0 w-16">
                      <span class="text-xl">{{ conn.fromIcon }}</span>
                      <span class="text-[10px] font-medium text-gray-600 dark:text-gray-300 mt-0.5 text-center leading-tight">
                        {{ conn.from }}
                      </span>
                    </div>
                    <!-- Arrow -->
                    <div class="flex-shrink-0">
                      <svg class="w-6 h-6" :class="conn.color" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
                      </svg>
                    </div>
                    <!-- To -->
                    <div class="flex flex-col items-center flex-shrink-0 w-16">
                      <span class="text-xl">{{ conn.toIcon }}</span>
                      <span class="text-[10px] font-medium text-gray-600 dark:text-gray-300 mt-0.5 text-center leading-tight">
                        {{ conn.to }}
                      </span>
                    </div>
                    <!-- Description -->
                    <p class="text-xs text-gray-500 dark:text-gray-400 leading-relaxed flex-1 ml-1">
                      {{ conn.desc }}
                    </p>
                  </div>
                </div>
              </div>

              <!-- Step 4: Recommended Start -->
              <div v-else-if="currentStep === 4" key="step4" class="py-6">
                <div class="text-center mb-6">
                  <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
                    Empfohlener Einstieg
                  </h2>
                  <p class="text-sm text-gray-500 dark:text-gray-400">
                    So startest du am besten mit dem Post-Generator
                  </p>
                </div>
                <div class="max-w-md mx-auto space-y-4">
                  <!-- Step 1 -->
                  <div class="flex items-start gap-4">
                    <div class="w-8 h-8 rounded-full bg-[#4C8BC2] text-white flex items-center justify-center font-bold text-sm flex-shrink-0">
                      1
                    </div>
                    <div>
                      <h3 class="font-semibold text-gray-900 dark:text-white text-sm">
                        Settings einrichten
                      </h3>
                      <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        Hinterlege deinen API-Key, Branding-Farben und Posting-Ziele.
                      </p>
                    </div>
                  </div>
                  <!-- Connector line -->
                  <div class="ml-4 h-4 border-l-2 border-dashed border-gray-200 dark:border-gray-700"></div>
                  <!-- Step 2 -->
                  <div class="flex items-start gap-4">
                    <div class="w-8 h-8 rounded-full bg-[#4C8BC2] text-white flex items-center justify-center font-bold text-sm flex-shrink-0">
                      2
                    </div>
                    <div>
                      <h3 class="font-semibold text-gray-900 dark:text-white text-sm">
                        Ersten Post erstellen
                      </h3>
                      <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        Waehle ein Template, lass die KI Texte generieren und passe alles an.
                      </p>
                    </div>
                  </div>
                  <!-- Connector line -->
                  <div class="ml-4 h-4 border-l-2 border-dashed border-gray-200 dark:border-gray-700"></div>
                  <!-- Step 3 -->
                  <div class="flex items-start gap-4">
                    <div class="w-8 h-8 rounded-full bg-[#4C8BC2] text-white flex items-center justify-center font-bold text-sm flex-shrink-0">
                      3
                    </div>
                    <div>
                      <h3 class="font-semibold text-gray-900 dark:text-white text-sm">
                        Im Kalender planen
                      </h3>
                      <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        Plane deine Posts per Drag-and-Drop im Content-Kalender.
                      </p>
                    </div>
                  </div>
                  <!-- Connector line -->
                  <div class="ml-4 h-4 border-l-2 border-dashed border-gray-200 dark:border-gray-700"></div>
                  <!-- Step 4 -->
                  <div class="flex items-start gap-4">
                    <div class="w-8 h-8 rounded-full bg-[#FDD000] text-gray-900 flex items-center justify-center font-bold text-sm flex-shrink-0">
                      4
                    </div>
                    <div>
                      <h3 class="font-semibold text-gray-900 dark:text-white text-sm">
                        Wochenplaner ausprobieren
                      </h3>
                      <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        Lass die KI einen ganzen Wochenplan mit abwechslungsreichem Content vorschlagen.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Step 5: Tour Hints -->
              <div v-else-if="currentStep === 5" key="step5" class="text-center py-8">
                <div class="w-16 h-16 mx-auto mb-6 bg-gradient-to-br from-[#4C8BC2]/10 to-[#FDD000]/10 dark:from-[#4C8BC2]/20 dark:to-[#FDD000]/20 rounded-full flex items-center justify-center">
                  <span class="text-3xl">❓</span>
                </div>
                <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-3">
                  Seitenspezifische Hilfe
                </h2>
                <p class="text-gray-500 dark:text-gray-400 max-w-md mx-auto leading-relaxed mb-6">
                  Auf jeder Seite findest du eine interaktive Tour, die dir die
                  wichtigsten Funktionen Schritt fuer Schritt erklaert.
                </p>
                <div class="max-w-sm mx-auto bg-gray-50 dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700">
                  <div class="flex items-center justify-center gap-3 mb-3">
                    <div class="w-10 h-10 bg-[#4C8BC2] rounded-full flex items-center justify-center text-white font-bold text-lg shadow-md">
                      ?
                    </div>
                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Hilfe-Button
                    </span>
                  </div>
                  <p class="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                    Klicke jederzeit auf den Hilfe-Button in der Seitenleiste oder starte die
                    Tour erneut ueber die Einstellungen.
                  </p>
                </div>
                <div class="mt-8">
                  <p class="text-sm font-medium text-[#4C8BC2]">
                    Bereit loszulegen? 🚀
                  </p>
                  <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    Nach dem Schliessen startet die Dashboard-Tour automatisch.
                  </p>
                </div>
              </div>
            </Transition>
          </div>

          <!-- Footer navigation -->
          <div class="flex items-center justify-between px-6 py-4 border-t border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/50">
            <!-- Step dots -->
            <div class="flex items-center gap-1.5">
              <button
                v-for="i in totalSteps"
                :key="i"
                @click="currentStep = i - 1"
                class="w-2 h-2 rounded-full transition-all duration-300"
                :class="[
                  i - 1 === currentStep
                    ? 'w-6 bg-[#4C8BC2]'
                    : i - 1 < currentStep
                      ? 'bg-[#4C8BC2]/40'
                      : 'bg-gray-300 dark:bg-gray-600',
                ]"
              />
            </div>

            <!-- Navigation buttons -->
            <div class="flex items-center gap-2">
              <button
                v-if="currentStep > 0"
                @click="prevStep"
                class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                Zurueck
              </button>
              <button
                @click="nextStep"
                class="px-6 py-2 text-sm font-medium text-white rounded-lg shadow-sm transition-all"
                :class="[
                  currentStep === totalSteps - 1
                    ? 'bg-gradient-to-r from-[#4C8BC2] to-[#4C8BC2]/80 hover:from-[#3a7ab5] hover:to-[#3a7ab5]/80'
                    : 'bg-[#4C8BC2] hover:bg-[#3a7ab5]',
                ]"
              >
                {{ currentStep === totalSteps - 1 ? 'Los geht\'s!' : 'Weiter' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.welcome-fade-enter-active,
.welcome-fade-leave-active {
  transition: opacity 0.3s ease;
}
.welcome-fade-enter-from,
.welcome-fade-leave-to {
  opacity: 0;
}

.slide-step-enter-active,
.slide-step-leave-active {
  transition: all 0.25s ease;
}
.slide-step-enter-from {
  opacity: 0;
  transform: translateX(20px);
}
.slide-step-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
