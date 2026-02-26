<script setup>
/**
 * PostCreatorView.vue — 3-Schritt Post-Creator
 *
 * Simplified post creation flow with horizontal step indicator:
 *   Step 1: Inhalt (Content) — Text, AI generation, images
 *   Step 2: Design — Template selection, live preview, slide editing
 *   Step 3: Fertigstellen — Platform, hashtags, export
 *
 * Replaces the old 9-step wizard for a faster, more intuitive workflow.
 * The old CreatePostView.vue remains available as advanced/legacy mode.
 */
import { computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import StepIndicator from '@/components/common/StepIndicator.vue'
import Step1Content from '@/components/creator/Step1Content.vue'
import Step2Design from '@/components/creator/Step2Design.vue'
import Step3Finalize from '@/components/creator/Step3Finalize.vue'
import { usePostCreator } from '@/composables/usePostCreator'
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'

const router = useRouter()

const {
  currentStep,
  TOTAL_STEPS,
  STEP_DEFINITIONS,
  nextStep,
  prevStep,
  goToStep,
  canProceedCurrent,
  slides,
  exportComplete,
  validationMessage,
  hasState,
  resetCreator,
} = usePostCreator()

// ── Step indicator steps ────────────────────────────────────────────
const stepDefs = computed(() => STEP_DEFINITIONS)

function onStepChange(step) {
  goToStep(step)
}

// ── Unsaved changes guard ───────────────────────────────────────────
const { showLeaveDialog, confirmLeave, cancelLeave, markClean } = useUnsavedChanges(
  () => hasState(),
  router
)

// Mark clean on export complete
watch(() => exportComplete.value, (val) => {
  if (val) markClean()
})

// ── Keyboard shortcuts ──────────────────────────────────────────────
function handleKeydown(e) {
  // Ctrl+Enter to advance step
  if (e.ctrlKey && e.key === 'Enter' && canProceedCurrent.value) {
    e.preventDefault()
    nextStep()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-6" data-testid="post-creator-view">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Post erstellen</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">In 3 Schritten zum fertigen Social-Media-Post</p>
      </div>
      <div class="flex items-center gap-2">
        <router-link
          to="/create/advanced"
          class="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 underline"
          title="Zum erweiterten 9-Schritt Wizard"
        >
          Erweiterter Modus
        </router-link>
        <button
          v-if="hasState() && !exportComplete"
          @click="resetCreator"
          class="px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:text-red-500 hover:border-red-300 transition-colors"
          data-testid="reset-btn"
        >
          Zurücksetzen
        </button>
      </div>
    </div>

    <!-- Step Indicator -->
    <div class="mb-8">
      <StepIndicator
        :steps="stepDefs"
        :current-step="currentStep"
        @update:current-step="onStepChange"
      />
    </div>

    <!-- Step Content -->
    <div class="min-h-[400px]">
      <Transition name="step-fade" mode="out-in">
        <Step1Content v-if="currentStep === 1" key="step1" />
        <Step2Design v-else-if="currentStep === 2" key="step2" />
        <Step3Finalize v-else-if="currentStep === 3" key="step3" />
      </Transition>
    </div>

    <!-- Validation Message -->
    <div v-if="validationMessage" class="mt-4 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-300 dark:border-amber-700 rounded-lg text-amber-800 dark:text-amber-300 flex items-center gap-2" role="alert">
      <span>&#9888;&#65039;</span>
      <span>{{ validationMessage }}</span>
      <button @click="validationMessage = ''" class="ml-auto text-amber-600 hover:text-amber-800 font-bold">&times;</button>
    </div>

    <!-- Navigation Buttons -->
    <div v-if="!exportComplete" class="flex items-center justify-between mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
      <button
        v-if="currentStep > 1"
        @click="prevStep"
        class="px-6 py-3 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 font-medium transition-colors"
        data-testid="prev-btn"
      >
        &#8592; Zurück
      </button>
      <div v-else></div>

      <div class="flex items-center gap-2">
        <span class="text-xs text-gray-400">Schritt {{ currentStep }} von {{ TOTAL_STEPS }}</span>
        <span v-if="canProceedCurrent && currentStep < TOTAL_STEPS" class="text-xs text-gray-400">&#183; Ctrl+Enter</span>
      </div>

      <button
        v-if="currentStep < TOTAL_STEPS"
        @click="nextStep"
        class="px-6 py-3 rounded-lg font-medium transition-colors"
        :class="canProceedCurrent
          ? 'bg-[#3B7AB1] hover:bg-[#2E6A9E] text-white'
          : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'"
        data-testid="next-btn"
      >
        Weiter &#8594;
      </button>
      <div v-else></div>
    </div>

    <!-- Unsaved Changes Dialog -->
    <Teleport to="body">
      <div v-if="showLeaveDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-6 max-w-sm w-full mx-4">
          <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-2">Aenderungen verwerfen?</h3>
          <p class="text-sm text-gray-500 mb-4">Du hast ungespeicherte Aenderungen. Moechtest du die Seite wirklich verlassen?</p>
          <div class="flex gap-3">
            <button @click="cancelLeave" class="flex-1 px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium">Bleiben</button>
            <button @click="confirmLeave" class="flex-1 px-4 py-2 rounded-lg bg-red-600 text-white font-medium">Verlassen</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.step-fade-enter-active,
.step-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.step-fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.step-fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
