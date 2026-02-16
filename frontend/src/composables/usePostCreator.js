/**
 * usePostCreator — Shared composable for the 3-step Post Creator flow.
 *
 * Bridges the existing contentDraft Pinia store with the new simplified
 * 3-step UI. Provides step navigation, validation, and convenience methods
 * that each step component can use.
 *
 * Step mapping (old 9 → new 3):
 *   Old 1 (Category) + Old 2 (Template) → New Step 2 (Design)
 *   Old 3 (Platform) → New Step 3 (Finalize)
 *   Old 4 (Topic) + Old 5 (Generate) + Old 8 (Image) → New Step 1 (Content)
 *   Old 6 (Preview) + Old 7 (Edit) → New Step 2 (Design) preview
 *   Old 9 (Export) → New Step 3 (Finalize)
 */
import { ref, computed } from 'vue'
import { useContentDraftStore } from '@/stores/contentDraft'
import { storeToRefs } from 'pinia'
import { useToast } from '@/composables/useToast'

// Singleton state (shared across components in the same page)
const currentStep = ref(1)
const TOTAL_STEPS = 3

const STEP_DEFINITIONS = [
  { label: 'Inhalt', sublabel: 'Text & Bilder', icon: '📝' },
  { label: 'Design', sublabel: 'Template & Vorschau', icon: '🎨' },
  { label: 'Fertigstellen', sublabel: 'Plattform & Export', icon: '🚀' },
]

export function usePostCreator() {
  const store = useContentDraftStore()
  const toast = useToast()

  const {
    selectedCategory,
    selectedTemplate,
    selectedPlatform,
    selectedPlatforms,
    topic,
    keyPoints,
    country,
    tone,
    slides,
    captionInstagram,
    captionTiktok,
    hashtagsInstagram,
    hashtagsTiktok,
    ctaText,
    currentPreviewSlide,
    generatingText,
    generatedContent,
    loading,
    error,
    successMsg,
    exporting,
    savedPost,
    exportComplete,
    exportQuality,
    networkError,
    lastSaveFunction,
    validationMessage,
    templates,
    loadingTemplates,
    uploadingImage,
    assets,
    aiImagePrompt,
    aiImageAspectRatio,
    generatingImage,
    generatedImageResult,
    aiImageError,
    selectedArcId,
    selectedEpisodeNumber,
    episodePreviouslyText,
    episodeCliffhangerText,
    episodeNextHint,
    interactiveElements,
    humorFormats,
    selectedHumorFormat,
    loadingHumorFormats,
    previewPlatform,
    regeneratingField,
  } = storeToRefs(store)

  // ── Step validation ───────────────────────────────────────────────
  const canProceedStep1 = computed(() => {
    // Step 1 (Content): Need either topic text or slides with content
    return !!(topic.value?.trim() || slides.value.length > 0)
  })

  const canProceedStep2 = computed(() => {
    // Step 2 (Design): Need a template selected and slides generated
    return !!selectedTemplate.value && slides.value.length > 0
  })

  const canProceedStep3 = computed(() => {
    // Step 3 (Finalize): Need platform selected
    return selectedPlatforms.value.length > 0
  })

  const canProceedCurrent = computed(() => {
    switch (currentStep.value) {
      case 1: return canProceedStep1.value
      case 2: return canProceedStep2.value
      case 3: return canProceedStep3.value
      default: return false
    }
  })

  // ── Navigation ────────────────────────────────────────────────────
  function nextStep() {
    if (currentStep.value < TOTAL_STEPS && canProceedCurrent.value) {
      currentStep.value++
    } else if (!canProceedCurrent.value) {
      showStepValidationMessage()
    }
  }

  function prevStep() {
    if (currentStep.value > 1) {
      currentStep.value--
    }
  }

  function goToStep(step) {
    if (step >= 1 && step <= TOTAL_STEPS) {
      // Can always go back, can go forward only if current step is valid
      if (step < currentStep.value || canProceedCurrent.value) {
        currentStep.value = step
      }
    }
  }

  function showStepValidationMessage() {
    switch (currentStep.value) {
      case 1:
        validationMessage.value = 'Bitte gib ein Thema ein oder generiere Inhalte mit KI.'
        break
      case 2:
        if (!selectedTemplate.value) validationMessage.value = 'Bitte waehle ein Template aus.'
        else if (slides.value.length === 0) validationMessage.value = 'Bitte generiere zuerst Inhalte in Schritt 1.'
        break
      case 3:
        validationMessage.value = 'Bitte waehle mindestens eine Plattform aus.'
        break
    }
  }

  // ── Reset ─────────────────────────────────────────────────────────
  function resetCreator() {
    currentStep.value = 1
    store.resetWorkflow()
  }

  function hasState() {
    return store.hasWorkflowState() || currentStep.value > 1
  }

  return {
    // Step navigation
    currentStep,
    TOTAL_STEPS,
    STEP_DEFINITIONS,
    nextStep,
    prevStep,
    goToStep,
    canProceedCurrent,
    canProceedStep1,
    canProceedStep2,
    canProceedStep3,

    // Forwarded store state
    selectedCategory,
    selectedTemplate,
    selectedPlatform,
    selectedPlatforms,
    topic,
    keyPoints,
    country,
    tone,
    slides,
    captionInstagram,
    captionTiktok,
    hashtagsInstagram,
    hashtagsTiktok,
    ctaText,
    currentPreviewSlide,
    generatingText,
    generatedContent,
    loading,
    error,
    successMsg,
    exporting,
    savedPost,
    exportComplete,
    exportQuality,
    networkError,
    lastSaveFunction,
    validationMessage,
    templates,
    loadingTemplates,
    uploadingImage,
    assets,
    aiImagePrompt,
    aiImageAspectRatio,
    generatingImage,
    generatedImageResult,
    aiImageError,
    selectedArcId,
    selectedEpisodeNumber,
    episodePreviouslyText,
    episodeCliffhangerText,
    episodeNextHint,
    interactiveElements,
    humorFormats,
    selectedHumorFormat,
    loadingHumorFormats,
    previewPlatform,
    regeneratingField,

    // Convenience
    store,
    toast,
    resetCreator,
    hasState,
  }
}
