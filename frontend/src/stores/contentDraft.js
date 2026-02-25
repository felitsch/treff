/**
 * useContentDraftStore — Vereinfachter Draft-State fuer Quick/Smart Create.
 *
 * Architecture:
 * This store replaces the content-authoring portion of the old monolithic
 * `useCreatePostStore` (which had 47+ reactive refs). It focuses exclusively
 * on the post-creation wizard workflow:
 *
 *   - Step 1: Category selection
 *   - Step 2: Template selection
 *   - Step 3: Platform selection
 *   - Step 4: Topic, country, tone input
 *   - Step 5: AI text generation
 *   - Step 6-7: Preview & edit (slides, captions, hashtags, CTA)
 *   - Step 8: Background image / AI image
 *   - Step 9: Export
 *
 * Kept to max ~20 core reactive refs by grouping related state into objects
 * (e.g., aiImage.prompt, aiImage.generating) and by moving campaign/pipeline
 * concerns to their own dedicated stores.
 *
 * The old `useCreatePostStore` is kept temporarily for backward-compat and
 * delegates to this store internally.
 *
 * @see stores/contentPipeline.js — Student inbox & content processing queue
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useContentDraftStore = defineStore('contentDraft', () => {
  // ═══════════════════════════════════════════════════════════════════
  // WIZARD NAVIGATION (3 refs)
  // ═══════════════════════════════════════════════════════════════════
  const currentStep = ref(1)
  const loading = ref(false)
  const error = ref('')
  const successMsg = ref('')

  // ═══════════════════════════════════════════════════════════════════
  // CONTENT SELECTION (5 refs)
  // Step 1: Category  |  Step 2: Template  |  Step 3: Platform
  // ═══════════════════════════════════════════════════════════════════
  const selectedCategory = ref('')
  const selectedPillar = ref('')  // Content pillar ID (auto-set from category, or manually overridden)
  const selectedBuyerJourneyStage = ref('')  // awareness, consideration, decision
  const templates = ref([])
  const selectedTemplate = ref(null)
  const loadingTemplates = ref(false)
  const selectedPlatform = ref('instagram_feed')
  const selectedPlatforms = ref(['instagram_feed'])

  // ═══════════════════════════════════════════════════════════════════
  // TEMPLATE PLACEHOLDER VALUES (1 ref)
  // Stores user-entered values for template {{placeholders}}
  // Key = placeholder name, Value = user-entered string
  // ═══════════════════════════════════════════════════════════════════
  const templatePlaceholderValues = ref({})

  // ═══════════════════════════════════════════════════════════════════
  // TOPIC & GENERATION (7 refs)
  // Step 4: Topic input  |  Step 5: AI text generation
  // ═══════════════════════════════════════════════════════════════════
  const topic = ref('')
  const keyPoints = ref('')
  const country = ref('')
  const tone = ref('jugendlich')
  const humorFormats = ref([])
  const selectedHumorFormat = ref(null)
  const loadingHumorFormats = ref(false)
  const generatingText = ref(false)
  const generatedContent = ref(null)

  // ═══════════════════════════════════════════════════════════════════
  // PREVIEW & EDIT (8 refs)
  // Step 6-7: Live preview, captions, hashtags, CTA
  // ═══════════════════════════════════════════════════════════════════
  const slides = ref([])
  const captionInstagram = ref('')
  const captionTiktok = ref('')
  const hashtagsInstagram = ref('')
  const hashtagsTiktok = ref('')
  const ctaText = ref('')
  const currentPreviewSlide = ref(0)
  const previewPlatform = ref('')
  const customColors = ref({ headline: '#3B7AB1', subheadline: '#FDD000', body: '#D1D5DB' })

  // ═══════════════════════════════════════════════════════════════════
  // MEDIA & AI IMAGE (6 refs)
  // Step 8: Background image, AI image generation
  // ═══════════════════════════════════════════════════════════════════
  const uploadingImage = ref(false)
  const assets = ref([])
  const aiImagePrompt = ref('')
  const aiImageAspectRatio = ref('')
  const aiImageStyle = ref('photorealistic')
  const generatingImage = ref(false)
  const generatedImageResult = ref(null)
  const aiImageError = ref('')

  // ═══════════════════════════════════════════════════════════════════
  // INTERACTIVE & STORY-ARC (6 refs)
  // ═══════════════════════════════════════════════════════════════════
  const interactiveElements = ref([])
  const selectedArcId = ref(null)
  const selectedEpisodeNumber = ref(1)
  const episodePreviouslyText = ref('')
  const episodeCliffhangerText = ref('')
  const episodeNextHint = ref('')

  // ═══════════════════════════════════════════════════════════════════
  // EXPORT & SAVE (6 refs)
  // Step 9: Export, network retry, validation
  // ═══════════════════════════════════════════════════════════════════
  const exporting = ref(false)
  const savedPost = ref(null)
  const exportComplete = ref(false)
  const exportQuality = ref('1080')
  const networkError = ref(false)
  const lastSaveFunction = ref(null)
  const regeneratingField = ref('')
  const validationMessage = ref('')

  // ═══════════════════════════════════════════════════════════════════
  // ACTIONS
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Reset the entire workflow to its initial state.
   * Called when starting a new post or navigating away.
   */
  function resetWorkflow() {
    currentStep.value = 1
    selectedCategory.value = ''
    selectedPillar.value = ''
    selectedBuyerJourneyStage.value = ''
    selectedTemplate.value = null
    templatePlaceholderValues.value = {}
    selectedPlatform.value = 'instagram_feed'
    selectedPlatforms.value = ['instagram_feed']
    topic.value = ''
    keyPoints.value = ''
    country.value = ''
    tone.value = 'jugendlich'
    selectedHumorFormat.value = null
    humorFormats.value = []
    loadingHumorFormats.value = false
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
    aiImageAspectRatio.value = ''
    aiImageStyle.value = 'photorealistic'
    generatingImage.value = false
    generatedImageResult.value = null
    aiImageError.value = ''
    exporting.value = false
    networkError.value = false
    lastSaveFunction.value = null
    interactiveElements.value = []
    selectedArcId.value = null
    selectedEpisodeNumber.value = 1
    episodePreviouslyText.value = ''
    episodeCliffhangerText.value = ''
    episodeNextHint.value = ''
    customColors.value = { headline: '#3B7AB1', subheadline: '#FDD000', body: '#D1D5DB' }
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

  // ═══════════════════════════════════════════════════════════════════
  // PUBLIC API
  // ═══════════════════════════════════════════════════════════════════

  return {
    // Wizard state
    currentStep,
    loading,
    error,
    successMsg,
    // Step 1
    selectedCategory,
    selectedPillar,
    selectedBuyerJourneyStage,
    // Step 2
    templates,
    selectedTemplate,
    loadingTemplates,
    templatePlaceholderValues,
    // Step 3
    selectedPlatform,
    selectedPlatforms,
    // Step 4
    topic,
    keyPoints,
    country,
    tone,
    humorFormats,
    selectedHumorFormat,
    loadingHumorFormats,
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
    customColors,
    // Interactive Story Elements
    interactiveElements,
    // Story-Arc / Episode
    selectedArcId,
    selectedEpisodeNumber,
    episodePreviouslyText,
    episodeCliffhangerText,
    episodeNextHint,
    // Step 8
    uploadingImage,
    assets,
    aiImagePrompt,
    aiImageAspectRatio,
    aiImageStyle,
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
