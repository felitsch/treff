import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useCreatePostStore = defineStore('createPost', () => {
  // ── Wizard state ──────────────────────────────────────────────────────
  const currentStep = ref(1)
  const loading = ref(false)
  const error = ref('')
  const successMsg = ref('')

  // Step 1: Category selection
  const selectedCategory = ref('')

  // Step 2: Template
  const templates = ref([])
  const selectedTemplate = ref(null)
  const loadingTemplates = ref(false)

  // Step 3: Platform (single selection for preview/primary, multi-select for export)
  const selectedPlatform = ref('instagram_feed')
  const selectedPlatforms = ref(['instagram_feed'])

  // Step 4: Topic & Content Input
  const topic = ref('')
  const keyPoints = ref('')
  const country = ref('')
  const tone = ref('jugendlich')

  // Step 5: AI Generation
  const generatingText = ref(false)
  const generatedContent = ref(null)

  // Step 6: Live Preview + Step 7: Edit
  const slides = ref([])
  const captionInstagram = ref('')
  const captionTiktok = ref('')
  const hashtagsInstagram = ref('')
  const hashtagsTiktok = ref('')
  const ctaText = ref('')
  const currentPreviewSlide = ref(0)

  // Step 6: Platform preview toggle (allows switching preview format independently)
  const previewPlatform = ref('')

  // Step 8: Background Image
  const uploadingImage = ref(false)
  const assets = ref([])

  // Step 8: AI Image Generation
  const aiImagePrompt = ref('')
  const generatingImage = ref(false)
  const generatedImageResult = ref(null)
  const aiImageError = ref('')

  // Step 9: Export
  const exporting = ref(false)
  const savedPost = ref(null)
  const exportComplete = ref(false)
  const exportQuality = ref('1080')

  // Network error retry state
  const networkError = ref(false)
  const lastSaveFunction = ref(null) // 'single' or 'multi' to identify which save to retry

  // Per-field regeneration state (tracks which field is currently being regenerated)
  const regeneratingField = ref('')

  // Validation state
  const validationMessage = ref('')

  function resetWorkflow() {
    currentStep.value = 1
    selectedCategory.value = ''
    selectedTemplate.value = null
    selectedPlatform.value = 'instagram_feed'
    selectedPlatforms.value = ['instagram_feed']
    topic.value = ''
    keyPoints.value = ''
    country.value = ''
    tone.value = 'jugendlich'
    generatedContent.value = null
    slides.value = []
    captionInstagram.value = ''
    captionTiktok.value = ''
    hashtagsInstagram.value = ''
    hashtagsTiktok.value = ''
    ctaText.value = ''
    error.value = ''
    successMsg.value = ''
    validationMessage.value = ''
    savedPost.value = null
    exportComplete.value = false
    currentPreviewSlide.value = 0
    previewPlatform.value = ''
    exportQuality.value = '1080'
    loading.value = false
    generatingText.value = false
    regeneratingField.value = ''
    uploadingImage.value = false
    aiImagePrompt.value = ''
    generatingImage.value = false
    generatedImageResult.value = null
    aiImageError.value = ''
    exporting.value = false
    networkError.value = false
    lastSaveFunction.value = null
    assets.value = []
    templates.value = []
    loadingTemplates.value = false
  }

  /**
   * Check if there is meaningful workflow state worth preserving.
   * Returns true if user has progressed beyond the initial empty state.
   */
  function hasWorkflowState() {
    return currentStep.value > 1 || !!selectedCategory.value
  }

  return {
    // Wizard state
    currentStep,
    loading,
    error,
    successMsg,
    // Step 1
    selectedCategory,
    // Step 2
    templates,
    selectedTemplate,
    loadingTemplates,
    // Step 3
    selectedPlatform,
    selectedPlatforms,
    // Step 4
    topic,
    keyPoints,
    country,
    tone,
    // Step 5
    generatingText,
    generatedContent,
    // Step 6-7
    slides,
    captionInstagram,
    captionTiktok,
    hashtagsInstagram,
    hashtagsTiktok,
    ctaText,
    currentPreviewSlide,
    previewPlatform,
    // Step 8
    uploadingImage,
    assets,
    aiImagePrompt,
    generatingImage,
    generatedImageResult,
    aiImageError,
    // Step 9
    exporting,
    savedPost,
    exportComplete,
    exportQuality,
    networkError,
    lastSaveFunction,
    // Per-field regeneration
    regeneratingField,
    // Validation
    validationMessage,
    // Methods
    resetWorkflow,
    hasWorkflowState,
  }
})
