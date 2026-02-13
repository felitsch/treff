<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import draggable from 'vuedraggable'
import JSZip from 'jszip'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import { useCreatePostStore } from '@/stores/createPost'
import { useUndoRedo } from '@/composables/useUndoRedo'
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'
import CtaPicker from '@/components/posts/CtaPicker.vue'
import HookSelector from '@/components/posts/HookSelector.vue'
import InteractiveElementPreview from '@/components/interactive/InteractiveElementPreview.vue'
import InteractiveElementEditor from '@/components/interactive/InteractiveElementEditor.vue'
import EngagementBoostPanel from '@/components/posts/EngagementBoostPanel.vue'
import CliffhangerPanel from '@/components/posts/CliffhangerPanel.vue'
import HelpTooltip from '@/components/common/HelpTooltip.vue'
import WorkflowHint from '@/components/common/WorkflowHint.vue'
import { tooltipTexts } from '@/utils/tooltipTexts'
import { useStudentStore } from '@/stores/students'
import { useStoryArcStore } from '@/stores/storyArc'
import TourSystem from '@/components/common/TourSystem.vue'

const router = useRouter()
const route = useRoute()
const toast = useToast()
const store = useCreatePostStore()

// ── Extract reactive refs from store (preserves state across navigation) ──
const {
  currentStep,
  loading,
  error,
  successMsg,
  selectedCategory,
  templates,
  selectedTemplate,
  loadingTemplates,
  selectedPlatform,
  selectedPlatforms,
  topic,
  keyPoints,
  country,
  tone,
  generatingText,
  generatedContent,
  slides,
  captionInstagram,
  captionTiktok,
  hashtagsInstagram,
  hashtagsTiktok,
  ctaText,
  currentPreviewSlide,
  previewPlatform,
  uploadingImage,
  assets,
  aiImagePrompt,
  aiImageAspectRatio,
  generatingImage,
  generatedImageResult,
  aiImageError,
  exporting,
  savedPost,
  exportComplete,
  exportQuality,
  networkError,
  lastSaveFunction,
  regeneratingField,
  validationMessage,
  humorFormats,
  selectedHumorFormat,
  loadingHumorFormats,
  interactiveElements,
  selectedArcId,
  selectedEpisodeNumber,
  episodePreviouslyText,
  episodeCliffhangerText,
  episodeNextHint,
} = storeToRefs(store)

const totalSteps = 9
const tourRef = ref(null)

// ── Workflow Hints ───────────────────────────────────────────────────────
const showAssetsHint = computed(() => currentStep.value === 8 && assets.value.length === 0 && !uploadingImage.value)
const showTemplatesHint = computed(() => currentStep.value === 2 && templates.value.length === 0 && !loadingTemplates.value)

// ── Multi-Platform Auto-Adapt state ─────────────────────────────────────
const adaptContent = ref(true) // Auto-adapt content for each platform

// ── Hook / Attention-Grabber state ──────────────────────────────────────
const selectedHook = ref(null)

function onHookSelected(hook) {
  selectedHook.value = hook
  if (hook && slides.value.length > 0) {
    // Apply the hook as the subheadline of the first slide (attention-grabbing opener)
    const firstSlide = slides.value[0]
    if (firstSlide) {
      firstSlide.subheadline = hook.hook_text
    }
  }
}

// ── Engagement Boost Panel ────────────────────────────────────────────
const engagementBoostPostContent = computed(() => ({
  slides: slides.value,
  caption_instagram: captionInstagram.value,
  caption_tiktok: captionTiktok.value,
  hashtags_instagram: hashtagsInstagram.value,
  hashtags_tiktok: hashtagsTiktok.value,
  cta_text: ctaText.value,
  category: selectedCategory.value,
  country: country.value,
  tone: tone.value,
}))

function onApplyEngagementSuggestion(suggestion) {
  toast.info(`Vorschlag: ${suggestion.action_text} — ${suggestion.suggestion.slice(0, 80)}...`)
}

// ── Hashtag Auto-Suggest state ──────────────────────────────────────────
const suggestingHashtags = ref(false)
const suggestedEmojis = ref([])

async function suggestHashtags() {
  if (suggestingHashtags.value) return
  suggestingHashtags.value = true
  try {
    const res = await api.post('/api/ai/suggest-hashtags', {
      topic: topic.value || '',
      country: country.value || '',
      platform: selectedPlatform.value || 'instagram_feed',
      category: selectedCategory.value || '',
      tone: tone.value || 'jugendlich',
    })
    if (res.data && res.data.hashtag_string) {
      hashtagsInstagram.value = res.data.hashtag_string
      hashtagsTiktok.value = res.data.hashtag_string
    }
    if (res.data && res.data.emoji_suggestions) {
      suggestedEmojis.value = res.data.emoji_suggestions.recommended_emojis || []
    }
  } catch (err) {
    console.error('Hashtag suggestion failed:', err)
  } finally {
    suggestingHashtags.value = false
  }
}

// ── Race condition protection for AI generation ──────────────────────────
// Track generation requests so late responses don't overwrite manual edits
let generationRequestCounter = 0
let pendingGenerationData = ref(null)  // Holds AI response when user edited during generation
const showOverwriteDialog = ref(false) // Controls the overwrite confirmation dialog

// Step 1: Category selection (static data - no need for store)
const categories = [
  { id: 'laender_spotlight', label: 'Laender-Spotlight', icon: '🌍', desc: 'Informative Posts ueber Ziellaender' },
  { id: 'erfahrungsberichte', label: 'Erfahrungsberichte', icon: '💬', desc: 'Alumni-Erfahrungen & Testimonials' },
  { id: 'infografiken', label: 'Infografiken', icon: '📊', desc: 'Vergleiche, Statistiken, Fakten' },
  { id: 'fristen_cta', label: 'Fristen & CTA', icon: '⏰', desc: 'Bewerbungsfristen & Calls-to-Action' },
  { id: 'tipps_tricks', label: 'Tipps & Tricks', icon: '💡', desc: 'Praktische Tipps fuers Auslandsjahr' },
  { id: 'faq', label: 'FAQ', icon: '❓', desc: 'Haeufig gestellte Fragen' },
  { id: 'foto_posts', label: 'Foto-Posts', icon: '📸', desc: 'Fotos mit Branding-Overlay' },
  { id: 'reel_tiktok_thumbnails', label: 'Reel/TikTok', icon: '🎬', desc: 'Thumbnails fuer Videos' },
  { id: 'story_posts', label: 'Story-Posts', icon: '📱', desc: 'Instagram Story Content' },
  { id: 'story_teaser', label: 'Story-Teaser', icon: '👉', desc: 'Feed-Post als Wegweiser zu Story-Serien' },
  { id: 'story_series', label: 'Story-Serien', icon: '📚', desc: 'Mehrteilige Story-Serien mit Episoden' },
]

// Step 3: Platform (static data)
const platforms = [
  { id: 'instagram_feed', label: 'Instagram Feed', icon: '📷', format: '1:1 / 4:5' },
  { id: 'instagram_story', label: 'Instagram Story', icon: '📱', format: '9:16' },
  { id: 'tiktok', label: 'TikTok', icon: '🎵', format: '9:16' },
]

// Step 4: Countries (static data)
const countries = [
  { id: 'usa', label: 'USA', flag: '🇺🇸' },
  { id: 'canada', label: 'Kanada', flag: '🇨🇦' },
  { id: 'australia', label: 'Australien', flag: '🇦🇺' },
  { id: 'newzealand', label: 'Neuseeland', flag: '🇳🇿' },
  { id: 'ireland', label: 'Irland', flag: '🇮🇪' },
]

// Step 4: Tone options (static data)
const toneOptions = [
  { id: 'jugendlich', label: 'Jugendlich', icon: '🎯', desc: 'Locker, Gen-Z-freundlich', example: '"Hey, dein Abenteuer wartet!"' },
  { id: 'serioess', label: 'Serioes', icon: '🏛️', desc: 'Fuer Eltern & Entscheider', example: '"Vertrauen Sie auf 40 Jahre Erfahrung."' },
  { id: 'witzig', label: 'Witzig', icon: '😂', desc: 'Humor & Wortspiele', example: '"Dein Koffer ist schwerer als deine Mathe-Note?"' },
  { id: 'emotional', label: 'Emotional', icon: '🥺', desc: 'Beruehrend & persoenlich', example: '"Der Moment, wenn du ankommst und weisst: Hier gehoere ich hin."' },
  { id: 'motivierend', label: 'Motivierend', icon: '💪', desc: 'Empowernd & aktivierend', example: '"Trau dich! Dein Auslandsjahr wartet auf DICH!"' },
  { id: 'informativ', label: 'Informativ', icon: '📊', desc: 'Fakten & Details', example: '"Highschool USA vs. Kanada: Kosten im Vergleich."' },
  { id: 'behind-the-scenes', label: 'Behind the Scenes', icon: '👀', desc: 'Authentisch & transparent', example: '"Was passiert bei TREFF, bevor ihr in den Flieger steigt?"' },
  { id: 'storytelling', label: 'Storytelling', icon: '📖', desc: 'Erzaehlerisch & narrativ', example: '"Es war 6 Uhr morgens am Frankfurter Flughafen..."' },
  { id: 'provokant', label: 'Provokant', icon: '⚡', desc: 'Mutig & scroll-stoppend', example: '"Unpopular Opinion: Ein Auslandsjahr bringt dir mehr als jedes Abi."' },
  { id: 'wholesome', label: 'Wholesome', icon: '🥰', desc: 'Herzlich & warmherzig', example: '"Wenn deine Gastmutter dir deinen Lieblingskuchen backt..."' },
]

const selectedToneObj = computed(() => toneOptions.find(t => t.id === tone.value))

// Story-Arc / Episode integration
const storyArcStore = useStoryArcStore()
const arcEpisodes = ref([])
const loadingArcEpisodes = ref(false)
const suggestingEpisodeField = ref('')

async function loadStoryArcs() {
  try {
    await storyArcStore.fetchStoryArcs()
  } catch { /* ignore */ }
}

async function loadArcEpisodes(arcId) {
  if (!arcId) { arcEpisodes.value = []; return }
  loadingArcEpisodes.value = true
  try {
    const response = await api.get(`/api/story-arcs/${arcId}/episodes`)
    arcEpisodes.value = response.data || []
    // Auto-set episode number to next available
    const maxEp = arcEpisodes.value.reduce((max, ep) => Math.max(max, ep.episode_number || 0), 0)
    selectedEpisodeNumber.value = maxEp + 1
  } catch {
    arcEpisodes.value = []
  } finally {
    loadingArcEpisodes.value = false
  }
}

function selectArc(arcId) {
  if (selectedArcId.value === arcId) {
    selectedArcId.value = null
    arcEpisodes.value = []
    episodePreviouslyText.value = ''
    episodeCliffhangerText.value = ''
    episodeNextHint.value = ''
    selectedEpisodeNumber.value = 1
    return
  }
  selectedArcId.value = arcId
  loadArcEpisodes(arcId)
  // Set country from arc if not already set
  const arc = storyArcStore.storyArcs.find(a => a.id === arcId)
  if (arc) {
    if (arc.country && !country.value) country.value = arc.country
    if (arc.tone) tone.value = arc.tone
  }
}

async function suggestEpisodeText(field) {
  if (suggestingEpisodeField.value) return
  suggestingEpisodeField.value = field
  try {
    const response = await api.post('/api/ai/suggest-episode-text', {
      arc_id: selectedArcId.value,
      episode_number: selectedEpisodeNumber.value,
      field,
      topic: topic.value || '',
      tone: tone.value || 'jugendlich',
    })
    if (response.data?.suggestion) {
      if (field === 'previously_text') episodePreviouslyText.value = response.data.suggestion
      else if (field === 'cliffhanger_text') episodeCliffhangerText.value = response.data.suggestion
      else if (field === 'next_episode_hint') episodeNextHint.value = response.data.suggestion
      toast.success('Vorschlag generiert!', 2000)
    }
  } catch (err) {
    toast.error('Vorschlag fehlgeschlagen: ' + (err.response?.data?.detail || err.message), 4000)
  } finally {
    suggestingEpisodeField.value = ''
  }
}

// Cliffhanger generation callback - update episode texts when AI generates them
function onCliffhangerGenerated(data) {
  if (data.cliffhanger_text) {
    episodeCliffhangerText.value = data.cliffhanger_text
  }
  if (data.teaser_text) {
    episodeNextHint.value = data.teaser_text
  }
  toast.success('Cliffhanger & Teaser generiert!', 2500)
}

// Episode save helper: create or update episode when saving a post linked to an arc
const savedEpisodeId = ref(null)
async function _saveOrUpdateEpisode(postId) {
  if (!selectedArcId.value || !postId) return
  try {
    const episodeData = {
      episode_title: topic.value || slides.value[0]?.headline || `Episode ${selectedEpisodeNumber.value}`,
      post_id: postId,
      episode_number: selectedEpisodeNumber.value,
      previously_text: episodePreviouslyText.value || null,
      cliffhanger_text: episodeCliffhangerText.value || null,
      next_episode_hint: episodeNextHint.value || null,
      status: 'draft',
    }
    if (savedEpisodeId.value) {
      // Update existing episode
      await api.put(`/api/story-arcs/${selectedArcId.value}/episodes/${savedEpisodeId.value}`, episodeData)
    } else {
      // Check if an episode for this post already exists
      const existing = arcEpisodes.value.find(ep => ep.post_id === postId)
      if (existing) {
        savedEpisodeId.value = existing.id
        await api.put(`/api/story-arcs/${selectedArcId.value}/episodes/${existing.id}`, episodeData)
      } else {
        // Create new episode
        const response = await api.post(`/api/story-arcs/${selectedArcId.value}/episodes`, episodeData)
        savedEpisodeId.value = response.data.id
        // Refresh episodes list
        await loadArcEpisodes(selectedArcId.value)
      }
    }
  } catch (err) {
    console.error('Episode save failed:', err)
    toast.error('Episode-Daten konnten nicht gespeichert werden: ' + (err.response?.data?.detail || err.message), 4000)
  }
}

// Student/Personality integration
const studentStore = useStudentStore()
const selectedStudentId = ref(null)
const selectedStudentPreset = computed(() => {
  if (!selectedStudentId.value) return null
  const student = studentStore.students.find(s => s.id === selectedStudentId.value)
  if (!student || !student.personality_preset) return null
  try {
    return typeof student.personality_preset === 'string'
      ? JSON.parse(student.personality_preset)
      : student.personality_preset
  } catch { return null }
})

const toneIcons = {
  witzig: '😂', emotional: '🥺', motivierend: '💪', jugendlich: '✨',
  serioess: '📋', storytelling: '📖', 'behind-the-scenes': '🎬',
  provokant: '⚡', wholesome: '🥰', informativ: '📊',
}

function selectStudent(studentId) {
  if (selectedStudentId.value === studentId) {
    selectedStudentId.value = null
    return
  }
  selectedStudentId.value = studentId
  const student = studentStore.students.find(s => s.id === studentId)
  if (student && student.personality_preset) {
    try {
      const preset = typeof student.personality_preset === 'string'
        ? JSON.parse(student.personality_preset)
        : student.personality_preset
      if (preset && preset.tone) {
        tone.value = preset.tone
        toast.info(`Persoenlichkeits-Preset von ${student.name} uebernommen: ${toneIcons[preset.tone] || ''} ${preset.tone}`)
      }
    } catch { /* ignore parse errors */ }
  }
}

// Step 8: Prompt suggestions (static data)
const promptSuggestions = [
  'American high school hallway with students',
  'Canadian Rocky Mountains landscape at sunset',
  'Sydney Opera House and harbour at golden hour',
  'New Zealand green hills with sheep',
  'Dublin cobblestone streets with colorful doors',
  'German exchange student arriving at American host family',
  'Group of international students in school cafeteria',
  'Teenagers playing sports on American football field',
]

// ── Computed ──────────────────────────────────────────────────────────
const canProceed = computed(() => {
  switch (currentStep.value) {
    case 1: return !!selectedCategory.value
    case 2: return !!selectedTemplate.value
    case 3: return selectedPlatforms.value.length > 0
    case 4: return true  // topic/keypoints are optional, country optional
    case 5: return !!generatedContent.value
    case 6: return slides.value.length > 0
    case 7: return slides.value.length > 0
    case 8: return true  // background image is optional
    case 9: return true
    default: return false
  }
})

const stepValidationMessages = {
  1: 'Bitte waehle eine Kategorie aus, bevor du fortfaehrst.',
  2: 'Bitte waehle ein Template aus, bevor du fortfaehrst.',
  3: 'Bitte waehle eine Plattform aus, bevor du fortfaehrst.',
  5: 'Bitte generiere zuerst den Inhalt, bevor du fortfaehrst.',
  6: 'Es sind keine Slides vorhanden. Bitte generiere zuerst Inhalte.',
  7: 'Es sind keine Slides vorhanden. Bitte generiere zuerst Inhalte.',
}

const stepLabels = [
  'Kategorie',
  'Template',
  'Plattform',
  'Thema',
  'Generieren',
  'Vorschau',
  'Bearbeiten',
  'Bild',
  'Export',
]

const selectedCategoryObj = computed(() => categories.find(c => c.id === selectedCategory.value))
const selectedPlatformObj = computed(() => platforms.find(p => p.id === selectedPlatform.value))
const selectedCountryObj = computed(() => countries.find(c => c.id === country.value))

// Effective preview platform: uses the toggle value if set, otherwise falls back to selectedPlatform
const effectivePreviewPlatform = computed(() => previewPlatform.value || selectedPlatform.value)
const effectivePreviewPlatformObj = computed(() => platforms.find(p => p.id === effectivePreviewPlatform.value))

// Initialize previewPlatform when platform changes
watch(selectedPlatform, (val) => {
  if (!previewPlatform.value) previewPlatform.value = val
})

// ── Platform-specific aspect ratio for image generation ──────────────
const platformAspectRatioMap = {
  instagram_feed: '1:1',
  instagram_story: '9:16',
  tiktok: '9:16',
}

const aspectRatioOptions = [
  { value: '1:1', label: '1:1 (Quadrat)' },
  { value: '9:16', label: '9:16 (Hochformat)' },
  { value: '16:9', label: '16:9 (Querformat)' },
  { value: '4:5', label: '4:5 (Instagram)' },
]

const platformDefaultAspectRatio = computed(() =>
  platformAspectRatioMap[selectedPlatform.value] || '1:1'
)

const platformAspectRatioLabel = computed(() => {
  const ratio = platformAspectRatioMap[selectedPlatform.value]
  if (!ratio) return '1:1'
  const option = aspectRatioOptions.find(o => o.value === ratio)
  return option ? option.label : ratio
})

const effectiveAspectRatio = computed(() =>
  aiImageAspectRatio.value || platformDefaultAspectRatio.value
)

// ── Methods ──────────────────────────────────────────────────────────

function togglePlatform(platformId) {
  const idx = selectedPlatforms.value.indexOf(platformId)
  if (idx >= 0) {
    // Don't allow deselecting the last platform
    if (selectedPlatforms.value.length <= 1) return
    selectedPlatforms.value.splice(idx, 1)
    // If we deselected the primary/preview platform, switch to the first remaining one
    if (selectedPlatform.value === platformId) {
      selectedPlatform.value = selectedPlatforms.value[0]
    }
  } else {
    selectedPlatforms.value.push(platformId)
  }
  // Keep primary platform in sync: primary is always the first selected platform
  if (!selectedPlatforms.value.includes(selectedPlatform.value)) {
    selectedPlatform.value = selectedPlatforms.value[0]
  }
}

function nextStep() {
  if (currentStep.value < totalSteps && canProceed.value) {
    validationMessage.value = ''
    currentStep.value++
    error.value = ''
    successMsg.value = ''
    if (currentStep.value === 2) loadTemplates()
    if (currentStep.value === 6 && !previewPlatform.value) previewPlatform.value = selectedPlatform.value
    if (currentStep.value === 8) loadAssets()
  } else if (!canProceed.value) {
    validationMessage.value = stepValidationMessages[currentStep.value] || 'Bitte fuelle alle Pflichtfelder aus.'
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--
    error.value = ''
    successMsg.value = ''
    validationMessage.value = ''
  }
}

function goToStep(step) {
  if (step <= currentStep.value || (step === currentStep.value + 1 && canProceed.value)) {
    currentStep.value = step
    error.value = ''
    successMsg.value = ''
    validationMessage.value = ''
    if (step === 2) loadTemplates()
    if (step === 6 && !previewPlatform.value) previewPlatform.value = selectedPlatform.value
    if (step === 8) loadAssets()
  }
}

// Clear validation message when user makes a selection
watch([selectedCategory, selectedTemplate, selectedPlatform, selectedPlatforms, generatedContent, slides], () => {
  validationMessage.value = ''
})

async function loadTemplates() {
  loadingTemplates.value = true
  try {
    const params = new URLSearchParams()
    if (selectedCategory.value) params.append('category', selectedCategory.value)
    const response = await api.get(`/api/templates?${params.toString()}`)
    templates.value = response.data
  } catch (e) {
    console.error('Failed to load templates:', e)
    templates.value = []
  } finally {
    loadingTemplates.value = false
  }
}

async function loadHumorFormats() {
  if (humorFormats.value.length > 0) return // Already loaded
  loadingHumorFormats.value = true
  try {
    const response = await api.get('/api/ai/humor-formats')
    humorFormats.value = response.data.humor_formats || []
  } catch (e) {
    console.error('Failed to load humor formats:', e)
    humorFormats.value = []
  } finally {
    loadingHumorFormats.value = false
  }
}

function selectHumorFormat(format) {
  if (selectedHumorFormat.value?.id === format.id) {
    selectedHumorFormat.value = null // Toggle off
  } else {
    selectedHumorFormat.value = format
    // Pre-fill topic from format example if topic is empty
    if (!topic.value && format.example_text?.topic) {
      topic.value = format.example_text.topic
    }
  }
}

async function generateHumorContent() {
  if (generatingText.value) return
  generatingText.value = true
  error.value = ''

  const requestId = ++generationRequestCounter
  const stateBeforeGeneration = slides.value.length > 0 ? JSON.stringify(slides.value) : null

  try {
    const response = await api.post('/api/ai/generate-humor', {
      format_id: selectedHumorFormat.value.id,
      topic: topic.value.trim() || 'Auslandsjahr',
      country: country.value || null,
      tone: tone.value,
    })

    if (requestId !== generationRequestCounter) return

    const currentState = slides.value.length > 0 ? JSON.stringify(slides.value) : null
    const userEditedDuringGeneration = stateBeforeGeneration !== null && currentState !== stateBeforeGeneration

    // Transform humor response to match the standard content format
    const humorData = response.data
    const transformedData = {
      slides: humorData.slides || [],
      caption_instagram: humorData.caption || '',
      caption_tiktok: humorData.caption || '',
      hashtags_instagram: Array.isArray(humorData.hashtags) ? humorData.hashtags.join(' ') : (humorData.hashtags || ''),
      hashtags_tiktok: Array.isArray(humorData.hashtags) ? humorData.hashtags.join(' ') : (humorData.hashtags || ''),
      cta_text: humorData.slides?.[0]?.cta_text || '',
      source: humorData.source || 'rule_based',
      humor_format: humorData.format_name,
    }

    if (userEditedDuringGeneration) {
      pendingGenerationData.value = transformedData
      showOverwriteDialog.value = true
      toast.info('Humor-Generierung abgeschlossen. Deine manuellen Aenderungen werden beibehalten.')
    } else {
      applyGeneratedContent(transformedData)
    }
  } catch (e) {
    console.error('Humor generation failed:', e)
    const status = e.response?.status
    const detail = e.response?.data?.detail || ''
    if (status === 429) {
      error.value = detail || 'Zu viele Anfragen. Bitte warte einen Moment.'
    } else {
      error.value = 'Humor-Generierung fehlgeschlagen: ' + (detail || e.message)
    }
  } finally {
    generatingText.value = false
  }
}

async function generateText() {
  // Prevent duplicate requests from rapid clicks
  if (generatingText.value) return
  generatingText.value = true
  error.value = ''

  // Capture state before generation to detect manual edits during the request
  const requestId = ++generationRequestCounter
  const stateBeforeGeneration = slides.value.length > 0 ? JSON.stringify(slides.value) : null

  try {
    const slideCount = selectedTemplate.value?.slide_count || 1
    const response = await api.post('/api/ai/generate-text', {
      category: selectedCategory.value,
      topic: topic.value.trim() || null,
      key_points: keyPoints.value.trim() || null,
      country: country.value || null,
      platform: selectedPlatform.value,
      slide_count: slideCount,
      tone: tone.value,
      student_id: selectedStudentId.value || null,
    })

    // Check if this is still the latest request (another generation may have started)
    if (requestId !== generationRequestCounter) {
      // A newer generation request was initiated - discard this late response
      return
    }

    // Check if user manually edited content while generation was in progress
    const currentState = slides.value.length > 0 ? JSON.stringify(slides.value) : null
    const userEditedDuringGeneration = stateBeforeGeneration !== null && currentState !== stateBeforeGeneration

    if (userEditedDuringGeneration) {
      // User edited content while AI was generating - don't overwrite silently
      // Store the pending data and show confirmation dialog
      pendingGenerationData.value = response.data
      showOverwriteDialog.value = true
      toast.info('KI-Generierung abgeschlossen. Deine manuellen Aenderungen werden beibehalten, bis du die neuen Inhalte uebernimmst.')
    } else {
      // No manual edits during generation - apply normally
      applyGeneratedContent(response.data)
    }
  } catch (e) {
    console.error('Text generation failed:', e)
    const status = e.response?.status
    const detail = e.response?.data?.detail || ''
    if (status === 429) {
      error.value = detail || 'Zu viele Anfragen. Bitte warte einen Moment und versuche es erneut.'
    } else {
      error.value = 'Textgenerierung fehlgeschlagen: ' + (detail || e.message)
    }
  } finally {
    generatingText.value = false
  }
}

// Apply AI-generated content to all fields
function applyGeneratedContent(data) {
  generatedContent.value = data
  slides.value = data.slides || []
  captionInstagram.value = data.caption_instagram || ''
  captionTiktok.value = data.caption_tiktok || ''
  hashtagsInstagram.value = data.hashtags_instagram || ''
  hashtagsTiktok.value = data.hashtags_tiktok || ''
  ctaText.value = data.cta_text || ''
  currentPreviewSlide.value = 0

  successMsg.value = 'Inhalt erfolgreich generiert!'
  setTimeout(() => { successMsg.value = '' }, 3000)

  // Initialize undo/redo history with newly generated content
  ensureDragIds()
  initFromState(getEditableState())
}

// Accept pending AI-generated content (user confirmed overwrite)
function acceptPendingGeneration() {
  if (pendingGenerationData.value) {
    applyGeneratedContent(pendingGenerationData.value)
    pendingGenerationData.value = null
    showOverwriteDialog.value = false
    toast.success('KI-generierte Inhalte uebernommen.')
  }
}

// Dismiss pending AI-generated content (keep manual edits)
function dismissPendingGeneration() {
  pendingGenerationData.value = null
  showOverwriteDialog.value = false
  toast.info('Manuelle Aenderungen beibehalten.')
}

async function regenerateField(field, slideIndex = 0) {
  const fieldKey = slideIndex > 0 ? `${field}_${slideIndex}` : field
  // Prevent duplicate requests from rapid clicks
  if (regeneratingField.value) return
  regeneratingField.value = fieldKey
  error.value = ''

  // Capture the field's current value before the async request
  // to detect if user manually edited it during regeneration
  let valueBeforeRegeneration = null
  switch (field) {
    case 'headline':
      valueBeforeRegeneration = slides.value[slideIndex]?.headline || ''
      break
    case 'subheadline':
      valueBeforeRegeneration = slides.value[slideIndex]?.subheadline || ''
      break
    case 'body_text':
      valueBeforeRegeneration = slides.value[slideIndex]?.body_text || ''
      break
    case 'cta_text':
      valueBeforeRegeneration = slides.value[slideIndex]?.cta_text || ''
      break
    case 'caption_instagram':
      valueBeforeRegeneration = captionInstagram.value
      break
    case 'caption_tiktok':
      valueBeforeRegeneration = captionTiktok.value
      break
    case 'hashtags_instagram':
      valueBeforeRegeneration = hashtagsInstagram.value
      break
    case 'hashtags_tiktok':
      valueBeforeRegeneration = hashtagsTiktok.value
      break
  }

  try {
    const response = await api.post('/api/ai/regenerate-field', {
      field,
      category: selectedCategory.value,
      country: country.value || null,
      topic: topic.value.trim() || null,
      key_points: keyPoints.value.trim() || null,
      tone: tone.value,
      platform: selectedPlatform.value,
      slide_index: slideIndex,
      slide_count: slides.value.length || 1,
      current_headline: slides.value[currentPreviewSlide.value]?.headline || '',
      current_body: slides.value[currentPreviewSlide.value]?.body_text || '',
    })

    const newValue = response.data.value

    // Check if user manually edited this field while regeneration was in progress
    let currentFieldValue = null
    switch (field) {
      case 'headline':
        currentFieldValue = slides.value[slideIndex]?.headline || ''
        break
      case 'subheadline':
        currentFieldValue = slides.value[slideIndex]?.subheadline || ''
        break
      case 'body_text':
        currentFieldValue = slides.value[slideIndex]?.body_text || ''
        break
      case 'cta_text':
        currentFieldValue = slides.value[slideIndex]?.cta_text || ''
        break
      case 'caption_instagram':
        currentFieldValue = captionInstagram.value
        break
      case 'caption_tiktok':
        currentFieldValue = captionTiktok.value
        break
      case 'hashtags_instagram':
        currentFieldValue = hashtagsInstagram.value
        break
      case 'hashtags_tiktok':
        currentFieldValue = hashtagsTiktok.value
        break
    }

    if (currentFieldValue !== valueBeforeRegeneration) {
      // User edited this field during regeneration - don't overwrite
      toast.info('Feld wurde waehrend der Regenerierung bearbeitet. Manuelle Aenderungen beibehalten.')
      return
    }

    // Apply the regenerated value to the correct field
    switch (field) {
      case 'headline':
        if (slides.value[slideIndex]) slides.value[slideIndex].headline = newValue
        break
      case 'subheadline':
        if (slides.value[slideIndex]) slides.value[slideIndex].subheadline = newValue
        break
      case 'body_text':
        if (slides.value[slideIndex]) slides.value[slideIndex].body_text = newValue
        break
      case 'cta_text':
        if (slides.value[slideIndex]) slides.value[slideIndex].cta_text = newValue
        break
      case 'caption_instagram':
        captionInstagram.value = newValue
        break
      case 'caption_tiktok':
        captionTiktok.value = newValue
        break
      case 'hashtags_instagram':
        hashtagsInstagram.value = newValue
        break
      case 'hashtags_tiktok':
        hashtagsTiktok.value = newValue
        break
    }

    successMsg.value = 'Feld neu generiert!'
    setTimeout(() => { successMsg.value = '' }, 2000)
  } catch (e) {
    console.error('Field regeneration failed:', e)
    const status = e.response?.status
    const detail = e.response?.data?.detail || ''
    if (status === 429) {
      error.value = detail || 'Zu viele Anfragen. Bitte warte einen Moment und versuche es erneut.'
    } else {
      error.value = 'Regenerierung fehlgeschlagen: ' + (detail || e.message)
    }
  } finally {
    regeneratingField.value = ''
  }
}

async function loadAssets() {
  try {
    const response = await api.get('/api/assets')
    assets.value = response.data
  } catch (e) {
    // Silent fail - assets are optional
  }
}

async function uploadBackgroundImage(event) {
  const file = event.target.files?.[0]
  if (!file) return

  uploadingImage.value = true
  error.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('category', 'background')
    const response = await api.post('/api/assets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    // Set as background for current slide
    const slide = slides.value[currentPreviewSlide.value]
    if (slide) {
      slide.background_type = 'image'
      slide.background_value = `/api/uploads/assets/${response.data.filename}`
    }
    successMsg.value = 'Bild hochgeladen!'
    setTimeout(() => { successMsg.value = '' }, 3000)
    await loadAssets()
  } catch (e) {
    error.value = 'Upload fehlgeschlagen: ' + (e.response?.data?.detail || e.message)
  } finally {
    uploadingImage.value = false
  }
}

function selectAssetAsBackground(asset) {
  const slide = slides.value[currentPreviewSlide.value]
  if (slide) {
    slide.background_type = 'image'
    slide.background_value = `/api/uploads/assets/${asset.filename}`
  }
  successMsg.value = 'Hintergrundbild gesetzt!'
  setTimeout(() => { successMsg.value = '' }, 2000)
}

async function generateAiImage() {
  if (!aiImagePrompt.value.trim()) {
    aiImageError.value = 'Bitte gib einen Prompt ein.'
    return
  }
  // Prevent duplicate requests from rapid clicks
  if (generatingImage.value) return
  generatingImage.value = true
  aiImageError.value = ''
  generatedImageResult.value = null

  try {
    // Build request with platform-specific aspect ratio
    const imagePayload = {
      prompt: aiImagePrompt.value.trim(),
      platform: selectedPlatform.value || 'instagram_feed',
      category: 'ai_generated',
      country: country.value || null,
    }
    // If user manually selected an aspect ratio override, include it (takes precedence over platform)
    if (aiImageAspectRatio.value) {
      imagePayload.aspect_ratio = aiImageAspectRatio.value
    }
    const response = await api.post('/api/ai/generate-image', imagePayload)

    generatedImageResult.value = response.data

    // Auto-set as background for current slide
    if (response.data.image_url) {
      const slide = slides.value[currentPreviewSlide.value]
      if (slide) {
        slide.background_type = 'image'
        slide.background_value = response.data.image_url
      }
    }

    successMsg.value = response.data.message || 'Bild erfolgreich generiert!'
    setTimeout(() => { successMsg.value = '' }, 4000)

    // Refresh assets list to include the new AI-generated image
    await loadAssets()
  } catch (e) {
    console.error('AI image generation failed:', e)
    // Map API errors to user-friendly German messages
    const status = e.response?.status
    const detail = e.response?.data?.detail || ''
    let friendlyMessage = ''
    if (status === 400) {
      // Validation errors from backend are already user-friendly (German)
      friendlyMessage = detail || 'Ungueltige Eingabe. Bitte ueberprüfe deinen Prompt.'
    } else if (status === 401 || status === 403) {
      friendlyMessage = 'Sitzung abgelaufen. Bitte melde dich erneut an.'
    } else if (status === 429) {
      friendlyMessage = 'Zu viele Anfragen. Bitte warte einen Moment und versuche es erneut.'
    } else if (status === 500) {
      // Backend 500 errors: use detail only if it looks like a user-friendly German message.
      // Check for known German user-friendly phrases; otherwise show generic German fallback.
      const knownGermanPhrases = [
        'Bitte', 'Fehler', 'Serverfehler', 'konnte nicht', 'aufgetreten',
        'Speichern', 'generiert', 'versuche', 'erneut',
      ]
      const looksUserFriendly = knownGermanPhrases.some(phrase => detail.includes(phrase))
      friendlyMessage = (detail && looksUserFriendly)
        ? detail
        : 'Ein Serverfehler ist aufgetreten. Bitte versuche es erneut.'
    } else if (e.code === 'ERR_NETWORK' || e.message?.includes('Network Error')) {
      friendlyMessage = 'Netzwerkfehler. Bitte pruefe deine Internetverbindung und versuche es erneut.'
    } else if (e.code === 'ECONNABORTED' || e.message?.includes('timeout')) {
      friendlyMessage = 'Die Anfrage hat zu lange gedauert. Bitte versuche es erneut.'
    } else {
      friendlyMessage = 'Die Bildgenerierung ist leider fehlgeschlagen. Bitte versuche es erneut.'
    }
    aiImageError.value = friendlyMessage
  } finally {
    generatingImage.value = false
  }
}

function selectPromptSuggestion(suggestion) {
  aiImagePrompt.value = suggestion
}

function isNetworkError(e) {
  // Direct network errors (no response received)
  if (
    e.code === 'ERR_NETWORK' ||
    e.code === 'ECONNABORTED' ||
    e.message?.includes('Network Error') ||
    e.message?.includes('timeout') ||
    (!e.response && e.request)
  ) return true
  // Proxy/gateway errors indicate the backend is unreachable
  const status = e.response?.status
  if (status === 502 || status === 503 || status === 504) return true
  // Vite dev proxy returns 500 when backend is down (ECONNREFUSED)
  if (status === 500) {
    const detail = e.response?.data?.detail || e.response?.data || ''
    const detailStr = typeof detail === 'string' ? detail : JSON.stringify(detail)
    if (
      detailStr.includes('ECONNREFUSED') ||
      detailStr.includes('connect ECONNREFUSED') ||
      detailStr.includes('proxy') ||
      detailStr === '' ||
      !e.response?.data
    ) return true
  }
  return false
}

async function saveAndExport() {
  exporting.value = true
  error.value = ''
  networkError.value = false
  lastSaveFunction.value = null

  try {
    // Save post to database (strip dragId from slides before saving)
    const cleanSlides = slides.value.map(({ dragId, ...rest }) => rest)
    const postData = {
      category: selectedCategory.value,
      country: country.value || null,
      platform: selectedPlatform.value,
      template_id: selectedTemplate.value?.id || null,
      title: cleanSlides[0]?.headline || 'Neuer Post',
      status: 'draft',
      tone: tone.value,
      slide_data: JSON.stringify(cleanSlides),
      caption_instagram: captionInstagram.value,
      caption_tiktok: captionTiktok.value,
      hashtags_instagram: hashtagsInstagram.value,
      hashtags_tiktok: hashtagsTiktok.value,
      cta_text: ctaText.value,
      story_arc_id: selectedArcId.value || null,
      episode_number: selectedArcId.value ? selectedEpisodeNumber.value : null,
    }

    const response = await api.post('/api/posts', postData)
    savedPost.value = response.data

    // Save/update episode if arc is selected
    if (selectedArcId.value) {
      await _saveOrUpdateEpisode(savedPost.value.id)
    }

    // Save interactive elements if any exist
    if (interactiveElements.value.length > 0) {
      try {
        const elementsData = interactiveElements.value.map(el => ({
          slide_index: el.slide_index,
          element_type: el.element_type,
          question_text: el.question_text,
          options: el.options,
          correct_answer: el.correct_answer,
          emoji: el.emoji,
          position_x: el.position_x || 50,
          position_y: el.position_y || 50,
        }))
        await api.put(`/api/posts/${response.data.id}/interactive-elements`, elementsData)
      } catch (ieErr) {
        console.warn('Failed to save interactive elements:', ieErr)
      }
    }

    // Record the export - use carousel endpoint for multi-slide posts
    const exportEndpoint = slides.value.length > 1 ? '/api/export/render-carousel' : '/api/export/render'
    await api.post(exportEndpoint, {
      post_id: response.data.id,
      platform: selectedPlatform.value,
      resolution: exportQuality.value,
      slide_count: slides.value.length,
    })

    // Auto-download: ZIP for multi-slide carousels, PNG for single slide
    if (slides.value.length > 1) {
      await downloadAsZip()
    } else {
      downloadAsImage(0)
    }

    exportComplete.value = true
    networkError.value = false
    lastSaveFunction.value = null
    successMsg.value = 'Post gespeichert und exportiert!'
    toast.success('Post erfolgreich erstellt und gespeichert!', 5000)
  } catch (e) {
    if (isNetworkError(e)) {
      error.value = 'Netzwerkfehler beim Speichern. Bitte pruefe deine Internetverbindung.'
      networkError.value = true
      lastSaveFunction.value = 'single'
    } else {
      error.value = 'Export fehlgeschlagen: ' + (e.response?.data?.detail || e.message)
      networkError.value = false
    }
  } finally {
    exporting.value = false
  }
}

async function retrySave() {
  if (lastSaveFunction.value === 'multi') {
    await exportAllPlatforms()
  } else {
    await saveAndExport()
  }
}

// ── Ctrl+S: Quick save as draft (no export/download) ────────────────
const savingDraft = ref(false)

async function saveDraft() {
  if (savingDraft.value || exporting.value) return
  // Only allow save if we have enough data (category + platform + slides)
  if (!selectedCategory.value || !selectedPlatform.value || slides.value.length === 0) {
    toast.info('Bitte erstelle zuerst Inhalte, bevor du speicherst.', 3000)
    return
  }

  savingDraft.value = true
  try {
    const cleanSlides = slides.value.map(({ dragId, ...rest }) => rest)
    const postData = {
      category: selectedCategory.value,
      country: country.value || null,
      platform: selectedPlatform.value,
      template_id: selectedTemplate.value?.id || null,
      title: cleanSlides[0]?.headline || 'Neuer Post',
      status: 'draft',
      tone: tone.value,
      slide_data: JSON.stringify(cleanSlides),
      caption_instagram: captionInstagram.value,
      caption_tiktok: captionTiktok.value,
      hashtags_instagram: hashtagsInstagram.value,
      hashtags_tiktok: hashtagsTiktok.value,
      cta_text: ctaText.value,
      story_arc_id: selectedArcId.value || null,
      episode_number: selectedArcId.value ? selectedEpisodeNumber.value : null,
      student_id: selectedStudentId.value || null,
    }

    if (savedPost.value?.id) {
      // Update existing saved post
      await api.put(`/api/posts/${savedPost.value.id}`, postData)
      // Update/create episode if arc is selected
      if (selectedArcId.value) {
        await _saveOrUpdateEpisode(savedPost.value.id)
      }
      toast.success('Entwurf gespeichert!', 3000)
    } else if (selectedPlatforms.value.length > 1) {
      // Create linked sibling posts for multiple platforms
      const response = await api.post('/api/posts/multi-platform', {
        post_data: {
          ...postData,
          platform: undefined, // removed, set per-platform by backend
        },
        platforms: selectedPlatforms.value,
        adapt_content: adaptContent.value,
        source_platform: selectedPlatform.value,
      })
      // Save the first post as the "main" savedPost for further edits
      savedPost.value = response.data.posts[0]
      if (selectedArcId.value) await _saveOrUpdateEpisode(savedPost.value.id)
      const count = response.data.count
      const adaptedNote = response.data.adapted ? ' (KI-adaptiert)' : ''
      toast.success(`Entwurf fuer ${count} Plattformen gespeichert!${adaptedNote}`, 4000)
    } else {
      // Create new draft (single platform)
      const response = await api.post('/api/posts', postData)
      savedPost.value = response.data
      if (selectedArcId.value) await _saveOrUpdateEpisode(savedPost.value.id)
      toast.success('Entwurf gespeichert!', 3000)
    }
  } catch (e) {
    toast.error('Speichern fehlgeschlagen: ' + (e.response?.data?.detail || e.message), 5000)
  } finally {
    savingDraft.value = false
  }
}

function handleCtrlS(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    e.stopPropagation()
    // On step 9, use the full save+export. Otherwise save as draft.
    if (currentStep.value === 9 && !exportComplete.value) {
      if (selectedPlatforms.value.length > 1) {
        exportAllPlatforms()
      } else {
        saveAndExport()
      }
    } else {
      saveDraft()
    }
  }
}

function downloadAsImage(slideIndex = null) {
  // Guard against click event being passed as argument
  if (slideIndex !== null && typeof slideIndex !== 'number') {
    slideIndex = null
  }
  const targetSlide = slideIndex !== null ? slideIndex : currentPreviewSlide.value
  const canvas = renderSlideToCanvas(targetSlide)
  if (!canvas) return

  // Download with proper naming convention: TREFF_[category]_[platform]_[date]_[slide].png
  const link = document.createElement('a')
  const date = new Date().toISOString().split('T')[0]
  const slideNum = String(targetSlide + 1).padStart(2, '0')
  link.download = `TREFF_${selectedCategory.value}_${selectedPlatform.value}_${date}_${slideNum}.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
}

function renderSlideToCanvas(slideIndex) {
  // Render a single slide to a canvas and return it
  const dims = getDimensions()
  const scale = exportQuality.value === '2160' ? 2 : 1
  const canvas = document.createElement('canvas')
  canvas.width = dims.w * scale
  canvas.height = dims.h * scale
  const ctx = canvas.getContext('2d')
  ctx.scale(scale, scale)

  const slide = slides.value[slideIndex]
  if (!slide) return null

  // Background
  ctx.fillStyle = slide.background_value || '#1A1A2E'
  ctx.fillRect(0, 0, dims.w, dims.h)

  // Gradient overlay
  const gradient = ctx.createLinearGradient(0, 0, 0, dims.h)
  gradient.addColorStop(0, 'rgba(76, 139, 194, 0.3)')
  gradient.addColorStop(1, 'rgba(26, 26, 46, 0.8)')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, dims.w, dims.h)

  // TREFF logo
  ctx.fillStyle = '#3B7AB1'
  ctx.font = 'bold 28px Inter, Arial, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('TREFF', 60, 80)
  ctx.fillStyle = '#9CA3AF'
  ctx.font = '18px Inter, Arial, sans-serif'
  ctx.fillText('Sprachreisen', 158, 80)

  // Headline
  ctx.fillStyle = '#3B7AB1'
  ctx.font = 'bold 52px Inter, Arial, sans-serif'
  ctx.textAlign = 'center'
  wrapText(ctx, slide.headline || '', dims.w / 2, 260, dims.w - 160, 62)

  // Subheadline
  if (slide.subheadline) {
    ctx.fillStyle = '#FDD000'
    ctx.font = 'bold 32px Inter, Arial, sans-serif'
    wrapText(ctx, slide.subheadline, dims.w / 2, 400, dims.w - 160, 40)
  }

  // Body text
  if (slide.body_text) {
    ctx.fillStyle = '#D1D5DB'
    ctx.font = '24px Inter, Arial, sans-serif'
    wrapText(ctx, slide.body_text, dims.w / 2, 520, dims.w - 160, 32)
  }

  // Episode: Previously text on first slide
  if (selectedArcId.value && episodePreviouslyText.value && slideIndex === 0) {
    ctx.fillStyle = 'rgba(255,255,255,0.08)'
    roundRect(ctx, 60, 600, dims.w - 120, 60, 8)
    ctx.fill()
    ctx.fillStyle = '#D1D5DB'
    ctx.font = 'italic 18px Inter, Arial, sans-serif'
    ctx.textAlign = 'center'
    wrapText(ctx, episodePreviouslyText.value, dims.w / 2, 632, dims.w - 180, 22)
  }

  // Episode: Cliffhanger on last slide
  if (selectedArcId.value && episodeCliffhangerText.value && slideIndex === slides.value.length - 1) {
    const chY = dims.h - 300
    ctx.fillStyle = 'rgba(255,255,255,0.08)'
    roundRect(ctx, 60, chY, dims.w - 120, 52, 8)
    ctx.fill()
    ctx.fillStyle = '#FDD000'
    ctx.font = 'bold italic 18px Inter, Arial, sans-serif'
    ctx.textAlign = 'center'
    wrapText(ctx, episodeCliffhangerText.value, dims.w / 2, chY + 30, dims.w - 180, 22)
  }

  // Episode: Next episode hint on last slide
  if (selectedArcId.value && episodeNextHint.value && slideIndex === slides.value.length - 1) {
    const nhY = dims.h - 240
    ctx.fillStyle = 'rgba(59,122,177,0.2)'
    roundRect(ctx, 60, nhY, dims.w - 120, 46, 8)
    ctx.fill()
    ctx.fillStyle = '#93C5FD'
    ctx.font = '16px Inter, Arial, sans-serif'
    ctx.textAlign = 'center'
    wrapText(ctx, episodeNextHint.value, dims.w / 2, nhY + 28, dims.w - 180, 20)
  }

  // CTA
  if (slide.cta_text) {
    const ctaY = dims.h - 180
    ctx.fillStyle = '#FDD000'
    roundRect(ctx, dims.w / 2 - 150, ctaY, 300, 56, 28)
    ctx.fill()
    ctx.fillStyle = '#1A1A2E'
    ctx.font = 'bold 24px Inter, Arial, sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(slide.cta_text, dims.w / 2, ctaY + 37)
  }

  // TREFF bottom branding
  ctx.fillStyle = '#3B7AB1'
  ctx.font = 'bold 18px Inter, Arial, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('TREFF Sprachreisen', 60, dims.h - 50)

  return canvas
}

function renderSlideToCanvasForPlatform(slideIndex, platform) {
  // Render a single slide to a canvas for a specific platform's dimensions
  const dims = getDimensionsForPlatform(platform)
  const scale = exportQuality.value === '2160' ? 2 : 1
  const canvas = document.createElement('canvas')
  canvas.width = dims.w * scale
  canvas.height = dims.h * scale
  const ctx = canvas.getContext('2d')
  ctx.scale(scale, scale)

  const slide = slides.value[slideIndex]
  if (!slide) return null

  // Background
  ctx.fillStyle = slide.background_value || '#1A1A2E'
  ctx.fillRect(0, 0, dims.w, dims.h)

  // Gradient overlay
  const gradient = ctx.createLinearGradient(0, 0, 0, dims.h)
  gradient.addColorStop(0, 'rgba(76, 139, 194, 0.3)')
  gradient.addColorStop(1, 'rgba(26, 26, 46, 0.8)')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, dims.w, dims.h)

  // TREFF logo
  ctx.fillStyle = '#3B7AB1'
  ctx.font = 'bold 28px Inter, Arial, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('TREFF', 60, 80)
  ctx.fillStyle = '#9CA3AF'
  ctx.font = '18px Inter, Arial, sans-serif'
  ctx.fillText('Sprachreisen', 158, 80)

  // Headline
  ctx.fillStyle = '#3B7AB1'
  ctx.font = 'bold 52px Inter, Arial, sans-serif'
  ctx.textAlign = 'center'
  wrapText(ctx, slide.headline || '', dims.w / 2, 260, dims.w - 160, 62)

  // Subheadline
  if (slide.subheadline) {
    ctx.fillStyle = '#FDD000'
    ctx.font = 'bold 32px Inter, Arial, sans-serif'
    wrapText(ctx, slide.subheadline, dims.w / 2, 400, dims.w - 160, 40)
  }

  // Body text
  if (slide.body_text) {
    ctx.fillStyle = '#D1D5DB'
    ctx.font = '24px Inter, Arial, sans-serif'
    wrapText(ctx, slide.body_text, dims.w / 2, 520, dims.w - 160, 32)
  }

  // Episode: Previously text on first slide
  if (selectedArcId.value && episodePreviouslyText.value && slideIndex === 0) {
    ctx.fillStyle = 'rgba(255,255,255,0.08)'
    roundRect(ctx, 60, 600, dims.w - 120, 60, 8)
    ctx.fill()
    ctx.fillStyle = '#D1D5DB'
    ctx.font = 'italic 18px Inter, Arial, sans-serif'
    ctx.textAlign = 'center'
    wrapText(ctx, episodePreviouslyText.value, dims.w / 2, 632, dims.w - 180, 22)
  }

  // Episode: Cliffhanger on last slide
  if (selectedArcId.value && episodeCliffhangerText.value && slideIndex === slides.value.length - 1) {
    const chY = dims.h - 300
    ctx.fillStyle = 'rgba(255,255,255,0.08)'
    roundRect(ctx, 60, chY, dims.w - 120, 52, 8)
    ctx.fill()
    ctx.fillStyle = '#FDD000'
    ctx.font = 'bold italic 18px Inter, Arial, sans-serif'
    ctx.textAlign = 'center'
    wrapText(ctx, episodeCliffhangerText.value, dims.w / 2, chY + 30, dims.w - 180, 22)
  }

  // Episode: Next episode hint on last slide
  if (selectedArcId.value && episodeNextHint.value && slideIndex === slides.value.length - 1) {
    const nhY = dims.h - 240
    ctx.fillStyle = 'rgba(59,122,177,0.2)'
    roundRect(ctx, 60, nhY, dims.w - 120, 46, 8)
    ctx.fill()
    ctx.fillStyle = '#93C5FD'
    ctx.font = '16px Inter, Arial, sans-serif'
    ctx.textAlign = 'center'
    wrapText(ctx, episodeNextHint.value, dims.w / 2, nhY + 28, dims.w - 180, 20)
  }

  // CTA
  if (slide.cta_text) {
    const ctaY = dims.h - 180
    ctx.fillStyle = '#FDD000'
    roundRect(ctx, dims.w / 2 - 150, ctaY, 300, 56, 28)
    ctx.fill()
    ctx.fillStyle = '#1A1A2E'
    ctx.font = 'bold 24px Inter, Arial, sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(slide.cta_text, dims.w / 2, ctaY + 37)
  }

  // TREFF bottom branding
  ctx.fillStyle = '#3B7AB1'
  ctx.font = 'bold 18px Inter, Arial, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('TREFF Sprachreisen', 60, dims.h - 50)

  return canvas
}

function canvasToBlob(canvas) {
  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob), 'image/png')
  })
}

async function downloadAsZip() {
  // Generate ZIP containing all slide PNGs
  const zip = new JSZip()
  const date = new Date().toISOString().split('T')[0]

  for (let i = 0; i < slides.value.length; i++) {
    const canvas = renderSlideToCanvas(i)
    if (!canvas) continue
    const blob = await canvasToBlob(canvas)
    const slideNum = String(i + 1).padStart(2, '0')
    const filename = `TREFF_${selectedCategory.value}_${selectedPlatform.value}_${date}_slide_${slideNum}.png`
    zip.file(filename, blob)
  }

  const zipBlob = await zip.generateAsync({ type: 'blob' })
  const link = document.createElement('a')
  link.download = `TREFF_${selectedCategory.value}_${selectedPlatform.value}_${date}_carousel.zip`
  link.href = URL.createObjectURL(zipBlob)
  link.click()
  URL.revokeObjectURL(link.href)
}

async function exportAllPlatforms() {
  // Export for all selected platforms — creates a ZIP with per-platform folders
  exporting.value = true
  error.value = ''
  networkError.value = false
  lastSaveFunction.value = null

  try {
    // Step 1: Save linked posts for all selected platforms
    const cleanSlides = slides.value.map(({ dragId, ...rest }) => rest)
    const basePostData = {
      category: selectedCategory.value,
      country: country.value || null,
      template_id: selectedTemplate.value?.id || null,
      title: cleanSlides[0]?.headline || 'Neuer Post',
      status: 'draft',
      tone: tone.value,
      slide_data: JSON.stringify(cleanSlides),
      caption_instagram: captionInstagram.value,
      caption_tiktok: captionTiktok.value,
      hashtags_instagram: hashtagsInstagram.value,
      hashtags_tiktok: hashtagsTiktok.value,
      cta_text: ctaText.value,
      story_arc_id: selectedArcId.value || null,
      episode_number: selectedArcId.value ? selectedEpisodeNumber.value : null,
    }

    // Use multi-platform endpoint to create linked sibling posts
    const mpResponse = await api.post('/api/posts/multi-platform', {
      post_data: basePostData,
      platforms: selectedPlatforms.value,
      adapt_content: adaptContent.value,
      source_platform: selectedPlatform.value,
    })
    savedPost.value = mpResponse.data.posts[0]
    const createdPosts = mpResponse.data.posts

    // Save/update episode if arc is selected
    if (selectedArcId.value) {
      await _saveOrUpdateEpisode(savedPost.value.id)
    }

    // Step 2: Record export for each platform (use first matching post)
    for (const platform of selectedPlatforms.value) {
      const matchingPost = createdPosts.find(p => p.platform === platform) || savedPost.value
      const exportEndpoint = slides.value.length > 1 ? '/api/export/render-carousel' : '/api/export/render'
      await api.post(exportEndpoint, {
        post_id: matchingPost.id,
        platform: platform,
        resolution: exportQuality.value,
        slide_count: slides.value.length,
      })
    }

    // Step 3: Generate and download ZIP with all platforms
    const zip = new JSZip()
    const date = new Date().toISOString().split('T')[0]

    for (const platform of selectedPlatforms.value) {
      const platformFolder = zip.folder(platform)
      for (let i = 0; i < slides.value.length; i++) {
        const canvas = renderSlideToCanvasForPlatform(i, platform)
        if (!canvas) continue
        const blob = await canvasToBlob(canvas)
        const slideNum = String(i + 1).padStart(2, '0')
        const filename = `TREFF_${selectedCategory.value}_${platform}_${date}_slide_${slideNum}.png`
        platformFolder.file(filename, blob)
      }
    }

    const zipBlob = await zip.generateAsync({ type: 'blob' })
    const link = document.createElement('a')
    link.download = `TREFF_${selectedCategory.value}_all_platforms_${date}.zip`
    link.href = URL.createObjectURL(zipBlob)
    link.click()
    URL.revokeObjectURL(link.href)

    exportComplete.value = true
    networkError.value = false
    lastSaveFunction.value = null
    successMsg.value = `${selectedPlatforms.value.length} verknuepfte Posts fuer alle Plattformen gespeichert und exportiert!`
    toast.success(`${selectedPlatforms.value.length} verknuepfte Posts erfolgreich erstellt! (Multi-Plattform)`, 5000)
  } catch (e) {
    if (isNetworkError(e)) {
      error.value = 'Netzwerkfehler beim Speichern. Bitte pruefe deine Internetverbindung.'
      networkError.value = true
      lastSaveFunction.value = 'multi'
    } else {
      error.value = 'Export fehlgeschlagen: ' + (e.response?.data?.detail || e.message)
      networkError.value = false
    }
  } finally {
    exporting.value = false
  }
}

function wrapText(ctx, text, x, y, maxWidth, lineHeight) {
  const words = text.split(' ')
  let line = ''
  let currentY = y
  for (const word of words) {
    const testLine = line + word + ' '
    const metrics = ctx.measureText(testLine)
    if (metrics.width > maxWidth && line !== '') {
      ctx.fillText(line.trim(), x, currentY)
      line = word + ' '
      currentY += lineHeight
    } else {
      line = testLine
    }
  }
  ctx.fillText(line.trim(), x, currentY)
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.lineTo(x + w - r, y)
  ctx.quadraticCurveTo(x + w, y, x + w, y + r)
  ctx.lineTo(x + w, y + h - r)
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h)
  ctx.lineTo(x + r, y + h)
  ctx.quadraticCurveTo(x, y + h, x, y + h - r)
  ctx.lineTo(x, y + r)
  ctx.quadraticCurveTo(x, y, x + r, y)
  ctx.closePath()
}

function getDimensionsForPlatform(platform) {
  const dims = {
    instagram_feed: { w: 1080, h: 1080 },
    instagram_story: { w: 1080, h: 1920 },
    tiktok: { w: 1080, h: 1920 },
  }
  return dims[platform] || dims.instagram_feed
}

function getDimensions() {
  return getDimensionsForPlatform(selectedPlatform.value)
}

function resetWorkflow() {
  store.resetWorkflow()
  clearHistory()
}

function nextPreviewSlide() {
  if (currentPreviewSlide.value < slides.value.length - 1) currentPreviewSlide.value++
}
function prevPreviewSlide() {
  if (currentPreviewSlide.value > 0) currentPreviewSlide.value--
}

function getTemplateGradient(template) {
  try {
    const colors = JSON.parse(template.default_colors || '{}')
    const primary = colors.primary || '#3B7AB1'
    const secondary = colors.secondary || '#FDD000'
    return `linear-gradient(135deg, ${primary} 0%, ${secondary} 100%)`
  } catch {
    return 'linear-gradient(135deg, #3B7AB1 0%, #FDD000 100%)'
  }
}

// Ensure each slide has a unique dragId for vuedraggable item-key
let dragIdCounter = 0
function ensureDragIds() {
  for (const slide of slides.value) {
    if (!slide.dragId) {
      slide.dragId = `slide-${++dragIdCounter}`
    }
  }
}

function onSlideReorder() {
  // After drag-and-drop reorder, reset preview to first slide
  currentPreviewSlide.value = 0
  ensureDragIds()
}

// ── Add / Remove slide ─────────────────────────────────────────────────
const showDeleteSlideConfirm = ref(false)
const slideToDeleteIndex = ref(-1)

function addSlide() {
  const newSlide = {
    headline: 'Neue Slide',
    subheadline: '',
    body_text: '',
    cta_text: '',
    background_type: 'color',
    background_value: '#3B7AB1',
  }
  slides.value.push(newSlide)
  ensureDragIds()
  // Switch to the newly added slide
  currentPreviewSlide.value = slides.value.length - 1
}

function requestRemoveSlide(index) {
  if (slides.value.length <= 1) return // Prevent removing the last slide
  slideToDeleteIndex.value = index
  showDeleteSlideConfirm.value = true
}

function confirmRemoveSlide() {
  if (slideToDeleteIndex.value < 0 || slideToDeleteIndex.value >= slides.value.length) return
  slides.value.splice(slideToDeleteIndex.value, 1)
  // Adjust current preview if needed
  if (currentPreviewSlide.value >= slides.value.length) {
    currentPreviewSlide.value = slides.value.length - 1
  }
  ensureDragIds()
  showDeleteSlideConfirm.value = false
  slideToDeleteIndex.value = -1
}

function cancelRemoveSlide() {
  showDeleteSlideConfirm.value = false
  slideToDeleteIndex.value = -1
}

// ── Interactive Story Element handlers ────────────────────────────────
function addInteractiveElement(element) {
  interactiveElements.value = [...interactiveElements.value, element]
}

function removeInteractiveElement(element) {
  interactiveElements.value = interactiveElements.value.filter(
    el => (el.id || el._tempId) !== (element.id || element._tempId)
  )
}

function editInteractiveElement(updatedElement) {
  interactiveElements.value = interactiveElements.value.map(el =>
    (el.id || el._tempId) === (updatedElement.id || updatedElement._tempId)
      ? updatedElement
      : el
  )
}

// Computed: elements for the currently previewed slide
const currentSlideInteractiveElements = computed(() =>
  interactiveElements.value.filter(el => el.slide_index === currentPreviewSlide.value)
)

// Check if we should show interactive elements (story platform selected)
const showInteractiveElements = computed(() =>
  selectedPlatforms.value.includes('instagram_story')
)

// Watch for slide changes
watch(slides, () => {
  currentPreviewSlide.value = 0
  ensureDragIds()
})

// ── Undo / Redo ────────────────────────────────────────────────────────
function getEditableState() {
  return {
    slides: JSON.parse(JSON.stringify(slides.value)),
    captionInstagram: captionInstagram.value,
    captionTiktok: captionTiktok.value,
    hashtagsInstagram: hashtagsInstagram.value,
    hashtagsTiktok: hashtagsTiktok.value,
    ctaText: ctaText.value,
  }
}

function applyEditableState(state) {
  slides.value = state.slides
  captionInstagram.value = state.captionInstagram
  captionTiktok.value = state.captionTiktok
  hashtagsInstagram.value = state.hashtagsInstagram
  hashtagsTiktok.value = state.hashtagsTiktok
  ctaText.value = state.ctaText
  ensureDragIds()
}

const { canUndo, canRedo, undo, redo, snapshot, initFromState, startListening, stopListening, isApplying, clearHistory } = useUndoRedo(applyEditableState)

// Debounced snapshot on content changes
let undoSnapshotTimer = null
function debouncedSnapshot() {
  if (isApplying.value) return
  clearTimeout(undoSnapshotTimer)
  undoSnapshotTimer = setTimeout(() => {
    snapshot(getEditableState())
  }, 500)
}

// Watch all editable fields for changes and record snapshots (only when on step 7 - edit mode)
watch(
  () => [
    JSON.stringify(slides.value),
    captionInstagram.value,
    captionTiktok.value,
    hashtagsInstagram.value,
    hashtagsTiktok.value,
    ctaText.value,
  ],
  () => {
    if (currentStep.value >= 6) {
      debouncedSnapshot()
    }
  },
  { deep: false }
)

// Initialize undo history when content is first generated (entering step 6+)
watch(currentStep, (newStep, oldStep) => {
  if (newStep >= 6 && oldStep < 6 && slides.value.length > 0) {
    initFromState(getEditableState())
  }
  // Auto-load humor formats when reaching Step 4
  if (newStep === 4 && humorFormats.value.length === 0) {
    loadHumorFormats()
  }
})

// On mount: reload data if returning to an in-progress workflow,
// or pre-fill from accepted suggestion query params
onMounted(() => {
  // Load students for personality preset selection in step 4
  studentStore.fetchStudents()
  // Load story arcs for episode integration in step 4
  loadStoryArcs()

  // Check if navigated from an accepted suggestion (query params from dashboard)
  const suggestionCategory = route.query.category
  const suggestionCountry = route.query.country
  if (suggestionCategory) {
    // Reset any existing workflow state and pre-fill from suggestion
    store.resetWorkflow()
    selectedCategory.value = suggestionCategory
    if (suggestionCountry) {
      country.value = suggestionCountry
    }
    // Auto-advance: load templates for the selected category
    loadTemplates()
    // Clear query params from URL to avoid re-applying on refresh
    router.replace({ path: '/create-post' })
  } else if (store.hasWorkflowState()) {
    // Reload templates if we're on or past the template step
    if (currentStep.value >= 2 && selectedCategory.value) {
      loadTemplates()
    }
    // Reload assets if we're on the background image step
    if (currentStep.value >= 8) {
      loadAssets()
    }
    // Re-assign drag IDs to slides if they exist
    ensureDragIds()
    // If returning to edit steps with existing slides, init undo history
    if (currentStep.value >= 6 && slides.value.length > 0) {
      initFromState(getEditableState())
    }
  }
  startListening()
  window.addEventListener('keydown', handleCtrlS, true)
})

onUnmounted(() => {
  stopListening()
  clearTimeout(undoSnapshotTimer)
  window.removeEventListener('keydown', handleCtrlS, true)
})

// ── Unsaved changes warning ───────────────────────────────────────────
const { showLeaveDialog, confirmLeave, cancelLeave, markClean } = useUnsavedChanges(() => {
  // Dirty if user has started the workflow (selected a category or beyond step 1)
  // AND the post hasn't been exported yet
  return store.hasWorkflowState() && !exportComplete.value
})
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Neuen Post erstellen</h1>
      <div class="flex items-center gap-4">
        <span class="text-sm text-gray-500 dark:text-gray-400">Schritt {{ currentStep }} von {{ totalSteps }}</span>
        <button
          @click="resetWorkflow"
          class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          Zuruecksetzen
        </button>
      </div>
    </div>

    <!-- Workflow Hints -->
    <WorkflowHint
      hint-id="create-post-no-assets"
      message="Kein passendes Bild? Lade Bilder in die Asset-Bibliothek hoch, um sie hier zu verwenden."
      link-text="Asset-Bibliothek"
      link-to="/assets"
      icon="🖼️"
      :show="showAssetsHint"
    />
    <WorkflowHint
      hint-id="create-post-no-templates"
      message="Keine Templates gefunden? Erstelle oder importiere Vorlagen fuer schnellere Post-Erstellung."
      link-text="Templates verwalten"
      link-to="/templates"
      icon="📄"
      :show="showTemplatesHint"
    />

    <!-- Breadcrumb Navigation -->
    <nav aria-label="Breadcrumb" class="mb-4">
      <ol class="flex items-center flex-wrap gap-1 text-sm">
        <li class="flex items-center">
          <button
            @click="goToStep(1)"
            class="text-gray-500 dark:text-gray-400 hover:text-[#3B7AB1] dark:hover:text-blue-400 transition-colors"
            :class="currentStep === 1 ? 'cursor-default' : 'cursor-pointer'"
          >Post erstellen</button>
        </li>
        <template v-for="(label, idx) in stepLabels.slice(0, currentStep)" :key="'bc-' + idx">
          <li class="flex items-center">
            <span class="mx-1.5 text-gray-400 dark:text-gray-500" aria-hidden="true">/</span>
            <button
              v-if="idx + 1 < currentStep"
              @click="goToStep(idx + 1)"
              class="text-[#3B7AB1] dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:underline transition-colors cursor-pointer"
            >{{ label }}</button>
            <span
              v-else
              class="font-semibold text-gray-900 dark:text-white"
              aria-current="step"
            >{{ label }}</span>
          </li>
        </template>
      </ol>
    </nav>

    <!-- Step Indicator -->
    <div class="mb-8">
      <div class="flex items-center justify-between">
        <template v-for="(label, idx) in stepLabels" :key="idx">
          <button
            @click="goToStep(idx + 1)"
            class="flex flex-col items-center"
            :class="idx + 1 <= currentStep ? 'cursor-pointer' : 'cursor-not-allowed'"
          >
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors"
              :class="{
                'bg-[#3B7AB1] text-white ring-4 ring-blue-200 dark:ring-blue-900': idx + 1 === currentStep,
                'bg-green-500 text-white': idx + 1 < currentStep,
                'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400': idx + 1 > currentStep,
              }"
            >
              <span v-if="idx + 1 < currentStep">&#10003;</span>
              <span v-else>{{ idx + 1 }}</span>
            </div>
            <span
              class="text-[10px] mt-1 hidden sm:block"
              :class="{
                'text-[#3B7AB1] font-semibold dark:text-blue-400': idx + 1 === currentStep,
                'text-green-600 dark:text-green-400': idx + 1 < currentStep,
                'text-gray-400 dark:text-gray-500': idx + 1 > currentStep,
              }"
            >{{ label }}</span>
          </button>
          <div
            v-if="idx < stepLabels.length - 1"
            class="flex-1 h-0.5 mx-1"
            :class="idx + 1 < currentStep ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700'"
          ></div>
        </template>
      </div>
    </div>

    <!-- Messages -->
    <div v-if="error" class="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300" role="alert" data-testid="error-message">
      <div class="flex items-center gap-2">
        <span>&#9888;</span>
        <span class="flex-1">{{ error }}</span>
        <button @click="error = ''; networkError = false" class="text-red-500 hover:text-red-700">&times;</button>
      </div>
      <div v-if="networkError" class="mt-3 flex items-center gap-3">
        <button
          @click="retrySave"
          :disabled="exporting"
          data-testid="retry-save-btn"
          class="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
        >
          <span v-if="exporting" class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
          <span v-else>&#8635;</span>
          {{ exporting ? 'Wird erneut versucht...' : 'Erneut versuchen' }}
        </button>
        <span class="text-sm text-red-500 dark:text-red-400">Pruefe deine Internetverbindung und versuche es erneut.</span>
      </div>
    </div>
    <div v-if="successMsg" class="mb-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-green-700 dark:text-green-300 flex items-center gap-2">
      <span>&#10003;</span> {{ successMsg }}
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 1: Category Selection -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 1">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">Schritt 1: Waehle eine Post-Kategorie <HelpTooltip :text="tooltipTexts.createPost.stepCategory" /></h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <button
          v-for="cat in categories"
          :key="cat.id"
          @click="selectedCategory = cat.id"
          class="p-4 rounded-xl border-2 transition-all text-left hover:shadow-md"
          :class="selectedCategory === cat.id
            ? 'border-[#3B7AB1] bg-blue-50 dark:bg-blue-900/20 shadow-md'
            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'"
        >
          <div class="text-2xl mb-2">{{ cat.icon }}</div>
          <div class="font-semibold text-gray-900 dark:text-white">{{ cat.label }}</div>
          <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ cat.desc }}</div>
        </button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 2: Template Selection -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 2">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">Schritt 2: Waehle ein Template <HelpTooltip :text="tooltipTexts.createPost.stepTemplate" /></h2>
      <div v-if="loadingTemplates" class="flex items-center justify-center py-12">
        <div class="animate-spin h-8 w-8 border-4 border-[#3B7AB1] border-t-transparent rounded-full"></div>
      </div>
      <div v-else-if="templates.length === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
        Keine Templates fuer diese Kategorie verfuegbar.
      </div>
      <div v-else class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        <button
          v-for="tmpl in templates"
          :key="tmpl.id"
          @click="selectedTemplate = tmpl"
          class="rounded-xl border-2 overflow-hidden transition-all hover:shadow-md"
          :class="selectedTemplate?.id === tmpl.id
            ? 'border-[#3B7AB1] shadow-md ring-2 ring-[#3B7AB1]/30'
            : 'border-gray-200 dark:border-gray-700'"
        >
          <div class="h-28 flex items-center justify-center" :style="{ background: getTemplateGradient(tmpl) }">
            <div class="bg-white/20 backdrop-blur-sm rounded-lg px-3 py-1">
              <span class="text-white text-xs font-bold">TREFF</span>
            </div>
          </div>
          <div class="p-2 bg-white dark:bg-gray-800">
            <div class="text-xs font-medium text-gray-900 dark:text-white truncate">{{ tmpl.name }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">{{ tmpl.platform_format }} &middot; {{ tmpl.slide_count }} Slide{{ tmpl.slide_count > 1 ? 's' : '' }}</div>
          </div>
        </button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 3: Platform Selection (Multi-Select) -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 3">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">Schritt 3: Waehle die Zielplattform(en) <HelpTooltip :text="tooltipTexts.createPost.stepPlatform" /></h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">Du kannst mehrere Plattformen waehlen — beim Export werden separate Dateien fuer jede Plattform erstellt.</p>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl">
        <button
          v-for="p in platforms"
          :key="p.id"
          @click="togglePlatform(p.id)"
          class="p-6 rounded-xl border-2 transition-all text-center hover:shadow-md relative"
          :class="selectedPlatforms.includes(p.id)
            ? 'border-[#3B7AB1] bg-blue-50 dark:bg-blue-900/20 shadow-md'
            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'"
        >
          <div v-if="selectedPlatforms.includes(p.id)" class="absolute top-2 right-2 w-6 h-6 bg-[#3B7AB1] rounded-full flex items-center justify-center">
            <span class="text-white text-xs font-bold">&#10003;</span>
          </div>
          <div class="text-3xl mb-2">{{ p.icon }}</div>
          <div class="font-semibold text-gray-900 dark:text-white">{{ p.label }}</div>
          <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ p.format }}</div>
        </button>
      </div>
      <div v-if="selectedPlatforms.length > 1" class="mt-4 space-y-3">
        <div class="text-sm text-[#3B7AB1] font-medium">
          {{ selectedPlatforms.length }} Plattformen ausgewaehlt — Vorschau zeigt: {{ selectedPlatformObj?.label }}
        </div>
        <!-- Auto-Adapt Toggle -->
        <div class="p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border border-blue-200 dark:border-blue-700 rounded-xl">
          <label class="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              v-model="adaptContent"
              class="mt-1 h-5 w-5 rounded border-gray-300 text-[#3B7AB1] focus:ring-[#3B7AB1] cursor-pointer"
            />
            <div>
              <div class="font-semibold text-gray-900 dark:text-white text-sm flex items-center gap-2">
                <span>&#x2728;</span> KI-Autoadaption aktivieren <HelpTooltip :text="tooltipTexts.createPost.multiPlatform" size="sm" />
              </div>
              <p class="text-xs text-gray-600 dark:text-gray-400 mt-1">
                Texte werden automatisch an jede Plattform angepasst:
                <strong>Story</strong> = kurz + CTA,
                <strong>Feed</strong> = laenger + Hashtags,
                <strong>TikTok</strong> = Hook-fokussiert.
              </p>
            </div>
          </label>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 4: Topic & Key Points -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 4">
      <div class="max-w-2xl">
        <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">Schritt 4: Thema & Stichpunkte <HelpTooltip :text="tooltipTexts.createPost.stepTopic" /></h2>

        <!-- Country -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-1">Land (optional) <HelpTooltip :text="tooltipTexts.createPost.stepCountry" size="sm" /></label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="c in countries"
              :key="c.id"
              @click="country = country === c.id ? '' : c.id"
              class="px-4 py-2 rounded-lg border-2 transition-all text-sm"
              :class="country === c.id
                ? 'border-[#3B7AB1] bg-blue-50 dark:bg-blue-900/20 text-[#3B7AB1]'
                : 'border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-gray-300'"
            >
              {{ c.flag }} {{ c.label }}
            </button>
          </div>
        </div>

        <!-- Topic -->
        <div class="mb-6">
          <label for="topic" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-1">Thema / Titel <HelpTooltip :text="tooltipTexts.createPost.stepTopic" size="sm" /></label>
          <input
            id="topic"
            v-model="topic"
            type="text"
            placeholder="z.B. Highschool-Jahr in Kanada"
            class="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
          />
        </div>

        <!-- Key Points -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-1">Stichpunkte (optional) <HelpTooltip :text="tooltipTexts.createPost.stepKeyPoints" size="sm" /></label>
          <textarea
            v-model="keyPoints"
            rows="3"
            placeholder="z.B. Gastfamilien, Schulsystem, Freizeitaktivitaeten..."
            class="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
          ></textarea>
        </div>

        <!-- Student / Personality Preset (optional) -->
        <div v-if="studentStore.students.length > 0" class="mb-6">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-1">🎭 Studenten-Persoenlichkeit (optional) <HelpTooltip :text="tooltipTexts.createPost.studentSelector" size="sm" /></label>
          <p class="text-xs text-gray-400 dark:text-gray-500 mb-2">Waehle einen Studenten, um dessen Persoenlichkeits-Preset fuer die KI-Textgenerierung zu verwenden.</p>
          <div class="flex flex-wrap gap-2">
            <button v-for="student in studentStore.students" :key="student.id" type="button" @click="selectStudent(student.id)" class="px-3 py-2 rounded-lg border-2 transition-all text-sm text-left" :class="selectedStudentId === student.id ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20 ring-1 ring-purple-500/30' : 'border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-gray-300'">
              <div class="font-semibold text-gray-900 dark:text-white text-sm">{{ student.name }}</div>
              <div v-if="student.personality_preset" class="text-xs text-purple-600 dark:text-purple-400 mt-0.5">🎭 Preset aktiv</div>
              <div v-else class="text-xs text-gray-400 mt-0.5">Kein Preset</div>
            </button>
          </div>
          <div v-if="selectedStudentPreset" class="mt-2 px-3 py-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg text-xs text-purple-700 dark:text-purple-300"><span class="font-medium">Aktives Preset:</span> {{ toneIcons[selectedStudentPreset.tone] || '🎭' }} {{ selectedStudentPreset.tone }} · Humor {{ selectedStudentPreset.humor_level || 3 }}/5 · Emoji: {{ selectedStudentPreset.emoji_usage || 'moderate' }} · {{ selectedStudentPreset.perspective === 'first_person' ? 'Ich-Perspektive' : 'Dritte Person' }}</div>
        </div>

        <!-- Story-Arc / Episode (optional) -->
        <div v-if="storyArcStore.storyArcs.length > 0" class="mb-6" data-testid="story-arc-section">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-1">📖 Story-Arc (optional) <HelpTooltip :text="tooltipTexts.createPost.storyArcSelector" size="sm" /></label>
          <p class="text-xs text-gray-400 dark:text-gray-500 mb-2">Ist dieser Post Teil einer Story-Serie? Waehle einen Arc, um Episoden-Felder anzuzeigen.</p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="arc in storyArcStore.storyArcs"
              :key="arc.id"
              @click="selectArc(arc.id)"
              class="px-3 py-2 rounded-lg border-2 transition-all text-sm text-left"
              :class="selectedArcId === arc.id
                ? 'border-[#3B7AB1] bg-blue-50 dark:bg-blue-900/20 ring-1 ring-[#3B7AB1]/30'
                : 'border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-gray-300'"
              :data-testid="'arc-btn-' + arc.id"
            >
              <div class="font-semibold text-gray-900 dark:text-white text-sm">{{ arc.title }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                {{ arc.status }} · {{ arc.current_episode }}/{{ arc.planned_episodes }} Episoden
              </div>
            </button>
          </div>

          <!-- Episode fields (shown when an arc is selected) -->
          <div v-if="selectedArcId" class="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl space-y-4" data-testid="episode-fields">
            <h4 class="font-bold text-[#3B7AB1] text-sm flex items-center gap-2">
              📖 Episoden-Details
              <span v-if="loadingArcEpisodes" class="animate-spin h-4 w-4 border-2 border-[#3B7AB1] border-t-transparent rounded-full"></span>
            </h4>

            <!-- Episode Number -->
            <div>
              <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Episode-Nummer</label>
              <input
                v-model.number="selectedEpisodeNumber"
                type="number"
                min="1"
                class="w-24 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
                data-testid="episode-number-input"
              />
              <span class="ml-2 text-xs text-gray-500">
                ({{ arcEpisodes.length }} bestehende Episoden)
              </span>
            </div>

            <!-- Previously Text (Rueckblick) -->
            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="block text-xs font-medium text-gray-700 dark:text-gray-300">Rueckblick ("Bisher bei...")</label>
                <button
                  @click="suggestEpisodeText('previously_text')"
                  :disabled="suggestingEpisodeField === 'previously_text'"
                  class="text-xs text-[#3B7AB1] hover:text-[#2E6A9E] font-medium transition-colors disabled:opacity-50"
                  data-testid="suggest-previously-btn"
                >
                  <span v-if="suggestingEpisodeField === 'previously_text'" class="animate-spin inline-block h-3 w-3 border-2 border-[#3B7AB1] border-t-transparent rounded-full mr-1"></span>
                  ✨ KI-Vorschlag
                </button>
              </div>
              <textarea
                v-model="episodePreviouslyText"
                rows="2"
                placeholder="z.B. Bisher bei Jonathan: Nach der Ankunft in Seattle hat Jonathan seine Gastfamilie kennengelernt..."
                class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
                data-testid="previously-text-input"
              ></textarea>
            </div>

            <!-- Cliffhanger Text -->
            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="block text-xs font-medium text-gray-700 dark:text-gray-300">Cliffhanger (Ende der Episode)</label>
                <button
                  @click="suggestEpisodeText('cliffhanger_text')"
                  :disabled="suggestingEpisodeField === 'cliffhanger_text'"
                  class="text-xs text-[#3B7AB1] hover:text-[#2E6A9E] font-medium transition-colors disabled:opacity-50"
                  data-testid="suggest-cliffhanger-btn"
                >
                  <span v-if="suggestingEpisodeField === 'cliffhanger_text'" class="animate-spin inline-block h-3 w-3 border-2 border-[#3B7AB1] border-t-transparent rounded-full mr-1"></span>
                  ✨ KI-Vorschlag
                </button>
              </div>
              <textarea
                v-model="episodeCliffhangerText"
                rows="2"
                placeholder="z.B. Aber was Jonathan am naechsten Tag erlebt, haette niemand erwartet..."
                class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
                data-testid="cliffhanger-text-input"
              ></textarea>
            </div>

            <!-- Next Episode Hint (Teaser) -->
            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="block text-xs font-medium text-gray-700 dark:text-gray-300">Teaser (naechste Episode)</label>
                <button
                  @click="suggestEpisodeText('next_episode_hint')"
                  :disabled="suggestingEpisodeField === 'next_episode_hint'"
                  class="text-xs text-[#3B7AB1] hover:text-[#2E6A9E] font-medium transition-colors disabled:opacity-50"
                  data-testid="suggest-nexthint-btn"
                >
                  <span v-if="suggestingEpisodeField === 'next_episode_hint'" class="animate-spin inline-block h-3 w-3 border-2 border-[#3B7AB1] border-t-transparent rounded-full mr-1"></span>
                  ✨ KI-Vorschlag
                </button>
              </div>
              <textarea
                v-model="episodeNextHint"
                rows="2"
                placeholder="z.B. Naechste Episode: Jonathan entdeckt eine voellig neue Seite von Amerika!"
                class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
                data-testid="nexthint-text-input"
              ></textarea>
            </div>

            <!-- Existing episodes list -->
            <div v-if="arcEpisodes.length > 0">
              <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Bestehende Episoden:</label>
              <div class="space-y-1">
                <div v-for="ep in arcEpisodes" :key="ep.id" class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2">
                  <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-[#3B7AB1]/20 text-[#3B7AB1] font-bold text-[10px]">{{ ep.episode_number }}</span>
                  <span>{{ ep.episode_title }}</span>
                  <span class="text-gray-400">({{ ep.status }})</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tone -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-1">Tonalitaet <HelpTooltip :text="tooltipTexts.createPost.stepTone" size="sm" /></label>
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
            <button
              v-for="t in toneOptions"
              :key="t.id"
              @click="tone = t.id"
              class="px-3 py-3 rounded-lg border-2 transition-all text-sm text-left"
              :class="tone === t.id
                ? 'border-[#3B7AB1] bg-blue-50 dark:bg-blue-900/20 ring-1 ring-[#3B7AB1]/30'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-500'"
            >
              <div class="font-semibold text-gray-900 dark:text-white text-sm">{{ t.icon }} {{ t.label }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 leading-tight">{{ t.desc }}</div>
            </button>
          </div>
          <!-- Example sentence for selected tone -->
          <div v-if="selectedToneObj" class="mt-2 px-3 py-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-xs text-gray-500 dark:text-gray-400 italic">
            Beispiel: {{ selectedToneObj.example }}
          </div>
        </div>

        <!-- Humor Format Gallery (Optional) -->
        <div class="mb-6" data-testid="humor-format-section">
          <div class="flex items-center justify-between mb-2">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Humor-Format (optional)
            </label>
            <button
              v-if="humorFormats.length === 0 && !loadingHumorFormats"
              @click="loadHumorFormats"
              class="text-xs text-[#3B7AB1] hover:text-[#2E6A9E] font-medium transition-colors"
              data-testid="load-humor-formats-btn"
            >
              Humor-Formate laden
            </button>
            <button
              v-if="selectedHumorFormat"
              @click="selectedHumorFormat = null"
              class="text-xs text-red-500 hover:text-red-600 font-medium transition-colors"
              data-testid="clear-humor-format-btn"
            >
              Format abwaehlen
            </button>
          </div>
          <p class="text-xs text-gray-500 dark:text-gray-400 mb-3">
            Waehle ein Humor-Format fuer virale Meme-Inhalte auf Instagram und TikTok.
          </p>

          <!-- Loading spinner -->
          <div v-if="loadingHumorFormats" class="flex items-center justify-center py-6">
            <div class="animate-spin h-6 w-6 border-3 border-[#3B7AB1] border-t-transparent rounded-full"></div>
          </div>

          <!-- Humor Format Grid -->
          <div v-else-if="humorFormats.length > 0" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2" data-testid="humor-format-gallery">
            <button
              v-for="fmt in humorFormats"
              :key="fmt.id"
              @click="selectHumorFormat(fmt)"
              class="p-3 rounded-xl border-2 transition-all text-left hover:shadow-md"
              :class="selectedHumorFormat?.id === fmt.id
                ? 'border-[#FDD000] bg-yellow-50 dark:bg-yellow-900/20 shadow-md ring-1 ring-[#FDD000]/30'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'"
              :data-testid="'humor-format-' + fmt.id"
            >
              <div class="text-xl mb-1">{{ fmt.icon }}</div>
              <div class="font-semibold text-gray-900 dark:text-white text-xs leading-tight">{{ fmt.name }}</div>
              <div class="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5 leading-tight">
                {{ fmt.platform_fit === 'both' ? 'IG + TT' : fmt.platform_fit === 'instagram' ? 'Instagram' : 'TikTok' }}
              </div>
            </button>
          </div>

          <!-- Selected humor format detail -->
          <div v-if="selectedHumorFormat" class="mt-3 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-[#FDD000]/40 rounded-xl" data-testid="humor-format-detail">
            <div class="flex items-start gap-3">
              <span class="text-2xl">{{ selectedHumorFormat.icon }}</span>
              <div class="flex-1 min-w-0">
                <h4 class="font-bold text-gray-900 dark:text-white text-sm">{{ selectedHumorFormat.name }}</h4>
                <p class="text-xs text-gray-600 dark:text-gray-400 mt-1">{{ selectedHumorFormat.description }}</p>
                <div class="mt-2 flex flex-wrap gap-1">
                  <span class="px-2 py-0.5 bg-[#3B7AB1]/10 text-[#3B7AB1] text-[10px] font-medium rounded-full">
                    {{ selectedHumorFormat.platform_fit === 'both' ? 'Instagram & TikTok' : selectedHumorFormat.platform_fit === 'instagram' ? 'Instagram' : 'TikTok' }}
                  </span>
                  <span class="px-2 py-0.5 bg-[#FDD000]/20 text-yellow-700 dark:text-yellow-300 text-[10px] font-medium rounded-full">
                    Humor-Template
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 5: AI Text Generation -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 5">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">Schritt 5: Inhalt generieren <HelpTooltip :text="tooltipTexts.createPost.stepGenerate" /></h2>

      <div class="max-w-2xl mx-auto bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8 text-center">
        <div class="text-5xl mb-4">{{ selectedHumorFormat ? selectedHumorFormat.icon : '&#x2728;' }}</div>
        <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
          {{ selectedHumorFormat ? 'Humor-Content generieren' : 'KI-Textgenerierung' }}
        </h3>
        <p class="text-gray-500 dark:text-gray-400 mb-6">
          {{ selectedHumorFormat
            ? `"${selectedHumorFormat.name}" - Humor-Format mit KI-gestuetzten Textvorschlaegen.`
            : 'Texte, Captions und Hashtags werden basierend auf deiner Auswahl generiert.' }}
        </p>

        <!-- Summary of selections -->
        <div class="mb-6 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 text-left space-y-1">
          <div><strong>Kategorie:</strong> {{ selectedCategoryObj?.icon }} {{ selectedCategoryObj?.label }}</div>
          <div><strong>Template:</strong> {{ selectedTemplate?.name }} ({{ selectedTemplate?.slide_count }} Slide{{ selectedTemplate?.slide_count > 1 ? 's' : '' }})</div>
          <div><strong>Plattform:</strong> {{ selectedPlatformObj?.icon }} {{ selectedPlatformObj?.label }}</div>
          <div v-if="selectedCountryObj"><strong>Land:</strong> {{ selectedCountryObj.flag }} {{ selectedCountryObj.label }}</div>
          <div v-if="topic"><strong>Thema:</strong> {{ topic }}</div>
          <div v-if="keyPoints"><strong>Stichpunkte:</strong> {{ keyPoints }}</div>
          <div><strong>Tonalitaet:</strong> {{ selectedToneObj?.icon }} {{ selectedToneObj?.label || tone }}</div>
          <div v-if="selectedStudentId && studentStore.students.find(s => s.id === selectedStudentId)"><strong>🎭 Student:</strong> {{ studentStore.students.find(s => s.id === selectedStudentId)?.name }} <span v-if="selectedStudentPreset" class="text-purple-600 dark:text-purple-400">(Preset: {{ selectedStudentPreset.tone }}, H{{ selectedStudentPreset.humor_level }}/5)</span></div>
          <div v-if="selectedHumorFormat" class="pt-1 border-t border-gray-200 dark:border-gray-600 mt-1">
            <strong>Humor-Format:</strong> {{ selectedHumorFormat.icon }} {{ selectedHumorFormat.name }}
            <span class="text-[10px] ml-1 px-1.5 py-0.5 bg-[#FDD000]/20 text-yellow-700 dark:text-yellow-300 rounded-full">Meme</span>
          </div>
          <div v-if="selectedArcId" class="pt-1 border-t border-gray-200 dark:border-gray-600 mt-1">
            <strong>📖 Story-Arc:</strong> {{ storyArcStore.storyArcs.find(a => a.id === selectedArcId)?.title || 'Arc #' + selectedArcId }}
            <span class="ml-1 text-xs text-[#3B7AB1]">Episode {{ selectedEpisodeNumber }}</span>
          </div>
        </div>

        <button
          @click="selectedHumorFormat ? generateHumorContent() : generateText()"
          :disabled="generatingText"
          class="px-8 py-4 text-white font-bold rounded-xl transition-colors flex items-center justify-center gap-2 text-lg mx-auto"
          :class="selectedHumorFormat
            ? 'bg-gradient-to-r from-[#FDD000] to-[#FFB800] hover:from-[#E8C300] hover:to-[#EBA800] text-gray-900 disabled:from-gray-300 disabled:to-gray-300 dark:disabled:from-gray-700 dark:disabled:to-gray-700 disabled:text-gray-500'
            : 'bg-[#3B7AB1] hover:bg-[#2E6A9E] disabled:bg-gray-300 dark:disabled:bg-gray-700'"
          data-testid="generate-content-btn"
        >
          <span v-if="generatingText" class="animate-spin h-5 w-5 border-2 border-current border-t-transparent rounded-full"></span>
          <span v-else>{{ selectedHumorFormat ? selectedHumorFormat.icon : '&#x2728;' }}</span>
          {{ generatingText ? 'Generiere...' : (selectedHumorFormat ? 'Humor-Content generieren' : 'Inhalt generieren') }}
        </button>

        <!-- Generated content summary -->
        <div v-if="generatedContent" class="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700 text-left">
          <div class="flex items-center gap-2 text-green-600 dark:text-green-400 mb-3">
            <span class="text-lg">&#10003;</span>
            <span class="font-bold">{{ generatedContent.humor_format ? 'Humor-Content generiert!' : 'Inhalt generiert!' }}</span>
          </div>
          <ul class="text-sm text-gray-600 dark:text-gray-400 space-y-1 list-disc list-inside">
            <li>{{ slides.length }} Slide(s) mit Texten</li>
            <li>Instagram Caption erstellt</li>
            <li>TikTok Caption erstellt</li>
            <li>Hashtags generiert</li>
            <li v-if="generatedContent.humor_format">Humor-Format: {{ generatedContent.humor_format }}</li>
            <li v-if="generatedContent.source">Quelle: {{ generatedContent.source === 'gemini' ? 'KI (Gemini)' : 'Vorlage' }}</li>
          </ul>
        </div>

        <!-- Hook / Attention-Grabber Selector (shown after content is generated) -->
        <div v-if="generatedContent" class="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <HookSelector
            :topic="topic"
            :country="country"
            :tone="tone"
            :platform="selectedPlatform"
            @hook-selected="onHookSelected"
          />
        </div>
      </div>
    </div>

    <!-- Pending AI generation banner (shown on steps 6-7 when user edited during generation) -->
    <div v-if="pendingGenerationData && (currentStep === 6 || currentStep === 7)" class="mb-4 p-4 bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-700 rounded-xl flex items-center gap-3" data-testid="pending-generation-banner">
      <span class="text-2xl">&#x26A0;&#xFE0F;</span>
      <div class="flex-1">
        <p class="text-amber-800 dark:text-amber-200 font-medium text-sm">Neue KI-Inhalte verfuegbar</p>
        <p class="text-amber-600 dark:text-amber-400 text-xs">Die KI hat neue Inhalte generiert. Moechtest du sie uebernehmen?</p>
      </div>
      <div class="flex gap-2">
        <button @click="dismissPendingGeneration" class="px-3 py-1.5 text-xs border border-amber-300 dark:border-amber-600 text-amber-700 dark:text-amber-300 rounded-lg hover:bg-amber-100 dark:hover:bg-amber-800/50 transition-colors" data-testid="banner-keep-edits-btn">Verwerfen</button>
        <button @click="acceptPendingGeneration" class="px-3 py-1.5 text-xs bg-[#3B7AB1] text-white rounded-lg hover:bg-[#2E6A9E] transition-colors" data-testid="banner-accept-ai-btn">Uebernehmen</button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 6: Live Preview -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 6">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">Schritt 6: Live-Vorschau <HelpTooltip :text="tooltipTexts.createPost.stepPreview" /></h2>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Preview -->
        <div class="flex flex-col items-center">
          <!-- Platform preview toggle -->
          <div class="flex items-center gap-1 mb-4 p-1 bg-gray-100 dark:bg-gray-800 rounded-xl" data-testid="platform-preview-toggle">
            <button
              v-for="p in platforms"
              :key="p.id"
              @click="previewPlatform = p.id"
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
              :class="effectivePreviewPlatform === p.id
                ? 'bg-white dark:bg-gray-700 text-[#3B7AB1] shadow-sm'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
              :data-testid="'preview-toggle-' + p.id"
            >
              <span>{{ p.icon }}</span>
              <span class="hidden sm:inline">{{ p.label }}</span>
              <span class="text-[10px] text-gray-400 dark:text-gray-500 hidden sm:inline">({{ p.format }})</span>
            </button>
          </div>

          <div
            id="post-preview-container"
            class="rounded-2xl overflow-hidden shadow-xl border border-gray-200 dark:border-gray-700 relative bg-gradient-to-br from-[#1A1A2E] to-[#2a2a4e]"
            :class="{
              'aspect-square w-full max-w-[400px]': effectivePreviewPlatform === 'instagram_feed',
              'aspect-[9/16] w-full max-w-[320px]': effectivePreviewPlatform === 'instagram_story' || effectivePreviewPlatform === 'tiktok',
            }"
          >
            <div v-if="slides[currentPreviewSlide]" class="absolute inset-0 p-6 flex flex-col justify-between">
              <!-- TREFF logo + Episode badge -->
              <div class="flex items-center gap-2">
                <div class="bg-[#3B7AB1] rounded-lg px-3 py-1"><span class="text-white text-sm font-bold">TREFF</span></div>
                <span class="text-gray-400 text-xs">Sprachreisen</span>
                <span v-if="selectedArcId" class="ml-auto bg-[#FDD000] text-[#1A1A2E] px-2 py-0.5 rounded-full text-[10px] font-bold" data-testid="episode-badge">E{{ selectedEpisodeNumber }}</span>
              </div>

              <!-- Previously text (Rueckblick) - shown on first slide -->
              <div v-if="selectedArcId && episodePreviouslyText && currentPreviewSlide === 0" class="mt-1 px-2 py-1 bg-white/10 rounded text-gray-300 text-[10px] italic leading-tight line-clamp-2" data-testid="preview-previously">
                {{ episodePreviouslyText }}
              </div>

              <!-- Content -->
              <div class="flex-1 flex flex-col justify-center py-4">
                <h3 class="text-[#3B7AB1] text-xl font-extrabold leading-tight mb-2">
                  {{ slides[currentPreviewSlide]?.headline || '' }}
                </h3>
                <p v-if="slides[currentPreviewSlide]?.subheadline" class="text-[#FDD000] text-sm font-semibold mb-2">
                  {{ slides[currentPreviewSlide].subheadline }}
                </p>
                <p v-if="slides[currentPreviewSlide]?.body_text" class="text-gray-300 text-xs leading-relaxed line-clamp-5">
                  {{ slides[currentPreviewSlide].body_text }}
                </p>

                <!-- Bullet points -->
                <ul v-if="slides[currentPreviewSlide]?.bullet_points?.length" class="mt-2 space-y-1">
                  <li
                    v-for="(bp, bpIdx) in (Array.isArray(slides[currentPreviewSlide].bullet_points) ? slides[currentPreviewSlide].bullet_points : [])"
                    :key="bpIdx"
                    class="text-gray-300 text-xs flex items-start gap-1.5"
                  >
                    <span class="text-[#FDD000] mt-0.5">&#9679;</span>
                    <span>{{ bp }}</span>
                  </li>
                </ul>
              </div>

              <!-- Cliffhanger text - shown on last slide -->
              <div v-if="selectedArcId && episodeCliffhangerText && currentPreviewSlide === slides.length - 1" class="mb-2 px-2 py-1 bg-white/10 rounded text-[#FDD000] text-[10px] font-semibold italic leading-tight line-clamp-2" data-testid="preview-cliffhanger">
                {{ episodeCliffhangerText }}
              </div>

              <!-- Next episode hint - shown on last slide -->
              <div v-if="selectedArcId && episodeNextHint && currentPreviewSlide === slides.length - 1" class="mb-2 px-2 py-1 bg-[#3B7AB1]/20 rounded text-blue-300 text-[10px] leading-tight line-clamp-2" data-testid="preview-nexthint">
                {{ episodeNextHint }}
              </div>

              <!-- CTA -->
              <div v-if="slides[currentPreviewSlide]?.cta_text">
                <div class="inline-block bg-[#FDD000] text-[#1A1A2E] px-5 py-2 rounded-full font-bold text-sm">
                  {{ slides[currentPreviewSlide].cta_text }}
                </div>
              </div>

              <!-- Slide dots -->
              <div v-if="slides.length > 1" class="flex justify-center gap-1.5 mt-3">
                <button
                  v-for="(s, sIdx) in slides"
                  :key="sIdx"
                  @click="currentPreviewSlide = sIdx"
                  class="w-2 h-2 rounded-full transition-colors"
                  :class="sIdx === currentPreviewSlide ? 'bg-[#3B7AB1]' : 'bg-gray-600'"
                ></button>
              </div>
            </div>

            <!-- Interactive Story Element Overlays (visual preview) -->
            <InteractiveElementPreview
              v-for="(el, ielIdx) in currentSlideInteractiveElements"
              :key="el.id || el._tempId || ielIdx"
              :element="el"
              :interactive="false"
            />
          </div>

          <!-- Slide navigation -->
          <div v-if="slides.length > 1" class="flex items-center justify-between w-full max-w-[400px] mt-4">
            <button @click="prevPreviewSlide" :disabled="currentPreviewSlide === 0"
              class="px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-30 transition-colors">
              &#8592; Vorherige
            </button>
            <span class="text-sm text-gray-500 dark:text-gray-400">Slide {{ currentPreviewSlide + 1 }} von {{ slides.length }}</span>
            <button @click="nextPreviewSlide" :disabled="currentPreviewSlide === slides.length - 1"
              class="px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-30 transition-colors">
              Naechste &#8594;
            </button>
          </div>
        </div>

        <!-- Captions & hashtags sidebar -->
        <div class="space-y-4">
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <h4 class="font-semibold text-sm text-gray-900 dark:text-white mb-2">📷 Instagram Caption</h4>
            <p class="text-xs text-gray-600 dark:text-gray-400 whitespace-pre-line max-h-32 overflow-auto">{{ captionInstagram }}</p>
          </div>
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <h4 class="font-semibold text-sm text-gray-900 dark:text-white mb-2"># Instagram Hashtags</h4>
            <p class="text-xs text-blue-600 dark:text-blue-400 break-words">{{ hashtagsInstagram }}</p>
          </div>
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <h4 class="font-semibold text-sm text-gray-900 dark:text-white mb-2">🎵 TikTok Caption</h4>
            <p class="text-xs text-gray-600 dark:text-gray-400">{{ captionTiktok }}</p>
          </div>
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <h4 class="font-semibold text-sm text-gray-900 dark:text-white mb-2">🎵 TikTok Hashtags</h4>
            <p class="text-xs text-blue-600 dark:text-blue-400 break-words">{{ hashtagsTiktok }}</p>
          </div>
          <div v-if="ctaText" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <h4 class="font-semibold text-sm text-gray-900 dark:text-white mb-2">📢 Call-to-Action</h4>
            <p class="text-xs text-gray-600 dark:text-gray-400">{{ ctaText }}</p>
          </div>
          <!-- Engagement Boost Panel -->
          <EngagementBoostPanel
            :post-content="engagementBoostPostContent"
            :platform="effectivePreviewPlatform"
            :format="effectivePreviewPlatform"
            :posting-time="''"
            @apply-suggestion="onApplyEngagementSuggestion"
          />

          <div class="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 text-center text-xs text-gray-500 dark:text-gray-400" data-testid="preview-platform-info">
            {{ effectivePreviewPlatformObj?.icon }} {{ effectivePreviewPlatformObj?.label }}
            <span v-if="effectivePreviewPlatform !== selectedPlatform" class="text-[#3B7AB1] font-medium">(Vorschau)</span>
            &middot; {{ selectedCategoryObj?.label }}
            <span v-if="selectedCountryObj"> &middot; {{ selectedCountryObj.flag }} {{ selectedCountryObj.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 7: Edit Generated Content (Headline etc.) -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 7">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">Schritt 7: Inhalt bearbeiten <HelpTooltip :text="tooltipTexts.createPost.stepEdit" /></h2>
        <!-- Undo / Redo buttons -->
        <div class="flex gap-2">
          <button
            @click="undo"
            :disabled="!canUndo"
            class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 border"
            :class="canUndo
              ? 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
              : 'border-gray-200 dark:border-gray-700 text-gray-300 dark:text-gray-600 cursor-not-allowed'"
            title="Rueckgaengig (Ctrl+Z)"
            data-testid="undo-btn"
          >
            &#8630; Undo
          </button>
          <button
            @click="redo"
            :disabled="!canRedo"
            class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 border"
            :class="canRedo
              ? 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
              : 'border-gray-200 dark:border-gray-700 text-gray-300 dark:text-gray-600 cursor-not-allowed'"
            title="Wiederherstellen (Ctrl+Y)"
            data-testid="redo-btn"
          >
            Redo &#8631;
          </button>
        </div>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Edit panel -->
        <div class="space-y-4">
          <!-- Slide tabs with drag-and-drop reordering + Add/Remove -->
          <div v-if="slides.length >= 1" class="mb-3">
            <div class="flex items-center justify-between mb-2">
              <span v-if="slides.length > 1" class="text-xs text-gray-500 dark:text-gray-400">&#8597; Slides per Drag &amp; Drop neu anordnen</span>
              <span v-else class="text-xs text-gray-500 dark:text-gray-400">{{ slides.length }} Slide</span>
              <span class="text-xs text-gray-400 dark:text-gray-500">{{ slides.length }} Slides</span>
            </div>
            <div class="flex items-center gap-2 flex-wrap">
              <draggable
                v-model="slides"
                item-key="dragId"
                handle=".drag-handle"
                animation="200"
                ghost-class="slide-ghost"
                class="flex gap-1 flex-wrap"
                @end="onSlideReorder"
              >
                <template #item="{ element, index }">
                  <button
                    @click="currentPreviewSlide = index"
                    class="px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 drag-handle cursor-grab active:cursor-grabbing"
                    :class="currentPreviewSlide === index
                      ? 'bg-[#3B7AB1] text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'"
                  >
                    <span class="opacity-50">&#10495;</span>
                    Slide {{ index + 1 }}
                    <span v-if="index === 0" class="font-normal">(Cover)</span>
                    <span v-if="index === slides.length - 1 && index > 0" class="font-normal">(CTA)</span>
                  </button>
                </template>
              </draggable>
              <!-- Add Slide button -->
              <button
                @click="addSlide"
                class="px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 border-2 border-dashed border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-[#3B7AB1] hover:text-[#3B7AB1] dark:hover:border-[#3B7AB1] dark:hover:text-[#3B7AB1]"
                title="Neue Slide hinzufuegen"
                data-testid="add-slide-btn"
              >
                <span>+</span> Slide
              </button>
            </div>
          </div>

          <!-- Current slide edit -->
          <div v-if="slides[currentPreviewSlide]" class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 space-y-3">
            <!-- Slide header with delete button -->
            <div class="flex items-center justify-between pb-2 border-b border-gray-100 dark:border-gray-700">
              <span class="text-sm font-semibold text-gray-700 dark:text-gray-300">
                Slide {{ currentPreviewSlide + 1 }}
                <span v-if="currentPreviewSlide === 0" class="text-xs font-normal text-gray-400">(Cover)</span>
                <span v-if="currentPreviewSlide === slides.length - 1 && currentPreviewSlide > 0" class="text-xs font-normal text-gray-400">(CTA)</span>
              </span>
              <button
                v-if="slides.length > 1"
                @click="requestRemoveSlide(currentPreviewSlide)"
                class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                title="Slide entfernen"
                data-testid="remove-slide-btn"
              >
                &#128465; Entfernen
              </button>
            </div>
            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Headline</label>
                <button
                  @click="regenerateField('headline', currentPreviewSlide)"
                  :disabled="!!regeneratingField"
                  class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-md bg-[#3B7AB1]/10 text-[#3B7AB1] hover:bg-[#3B7AB1]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  :title="'Headline neu generieren'"
                >
                  <span :class="{ 'animate-spin': regeneratingField === (currentPreviewSlide > 0 ? 'headline_' + currentPreviewSlide : 'headline') }" class="text-sm">&#x1F504;</span>
                  <span>Neu</span>
                </button>
              </div>
              <input
                v-model="slides[currentPreviewSlide].headline"
                class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
                :class="(slides[currentPreviewSlide].headline?.length || 0) > 40 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white' : (slides[currentPreviewSlide].headline?.length || 0) > 30 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-gray-900 dark:text-white' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white'"
              />
              <div class="flex items-center justify-between mt-0.5">
                <span v-if="(slides[currentPreviewSlide].headline?.length || 0) > 40" class="text-xs text-red-500 dark:text-red-400">Text kann den Template-Bereich ueberlaufen</span>
                <span v-else-if="(slides[currentPreviewSlide].headline?.length || 0) > 30" class="text-xs text-amber-500 dark:text-amber-400">Nahe am Zeichenlimit</span>
                <span v-else class="text-xs text-gray-400"></span>
                <span class="text-xs" :class="(slides[currentPreviewSlide].headline?.length || 0) > 40 ? 'text-red-500 dark:text-red-400 font-semibold' : (slides[currentPreviewSlide].headline?.length || 0) > 30 ? 'text-amber-500 dark:text-amber-400' : 'text-gray-400'">{{ slides[currentPreviewSlide].headline?.length || 0 }}/40</span>
              </div>
            </div>
            <div v-if="slides[currentPreviewSlide].subheadline !== undefined">
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Subheadline</label>
                <button
                  @click="regenerateField('subheadline', currentPreviewSlide)"
                  :disabled="!!regeneratingField"
                  class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-md bg-[#3B7AB1]/10 text-[#3B7AB1] hover:bg-[#3B7AB1]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  :title="'Subheadline neu generieren'"
                >
                  <span :class="{ 'animate-spin': regeneratingField === (currentPreviewSlide > 0 ? 'subheadline_' + currentPreviewSlide : 'subheadline') }" class="text-sm">&#x1F504;</span>
                  <span>Neu</span>
                </button>
              </div>
              <input
                v-model="slides[currentPreviewSlide].subheadline"
                class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
                :class="(slides[currentPreviewSlide].subheadline?.length || 0) > 60 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white' : (slides[currentPreviewSlide].subheadline?.length || 0) > 45 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-gray-900 dark:text-white' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white'"
              />
              <div class="flex items-center justify-between mt-0.5">
                <span v-if="(slides[currentPreviewSlide].subheadline?.length || 0) > 60" class="text-xs text-red-500 dark:text-red-400">Text kann den Template-Bereich ueberlaufen</span>
                <span v-else-if="(slides[currentPreviewSlide].subheadline?.length || 0) > 45" class="text-xs text-amber-500 dark:text-amber-400">Nahe am Zeichenlimit</span>
                <span v-else class="text-xs text-gray-400"></span>
                <span class="text-xs" :class="(slides[currentPreviewSlide].subheadline?.length || 0) > 60 ? 'text-red-500 dark:text-red-400 font-semibold' : (slides[currentPreviewSlide].subheadline?.length || 0) > 45 ? 'text-amber-500 dark:text-amber-400' : 'text-gray-400'">{{ slides[currentPreviewSlide].subheadline?.length || 0 }}/60</span>
              </div>
            </div>
            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Text</label>
                <button
                  @click="regenerateField('body_text', currentPreviewSlide)"
                  :disabled="!!regeneratingField"
                  class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-md bg-[#3B7AB1]/10 text-[#3B7AB1] hover:bg-[#3B7AB1]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  :title="'Text neu generieren'"
                >
                  <span :class="{ 'animate-spin': regeneratingField === (currentPreviewSlide > 0 ? 'body_text_' + currentPreviewSlide : 'body_text') }" class="text-sm">&#x1F504;</span>
                  <span>Neu</span>
                </button>
              </div>
              <textarea
                v-model="slides[currentPreviewSlide].body_text"
                rows="3"
                class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent resize-none"
                :class="(slides[currentPreviewSlide].body_text?.length || 0) > 200 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white' : (slides[currentPreviewSlide].body_text?.length || 0) > 150 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-gray-900 dark:text-white' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white'"
              ></textarea>
              <div class="flex items-center justify-between mt-0.5">
                <span v-if="(slides[currentPreviewSlide].body_text?.length || 0) > 200" class="text-xs text-red-500 dark:text-red-400">Text kann den Template-Bereich ueberlaufen</span>
                <span v-else-if="(slides[currentPreviewSlide].body_text?.length || 0) > 150" class="text-xs text-amber-500 dark:text-amber-400">Nahe am Zeichenlimit</span>
                <span v-else class="text-xs text-gray-400"></span>
                <span class="text-xs" :class="(slides[currentPreviewSlide].body_text?.length || 0) > 200 ? 'text-red-500 dark:text-red-400 font-semibold' : (slides[currentPreviewSlide].body_text?.length || 0) > 150 ? 'text-amber-500 dark:text-amber-400' : 'text-gray-400'">{{ slides[currentPreviewSlide].body_text?.length || 0 }}/200</span>
              </div>
            </div>
            <div v-if="slides[currentPreviewSlide].cta_text !== undefined">
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">CTA-Bibliothek <HelpTooltip :text="tooltipTexts.createPost.ctaLibrary" size="sm" /></label>
                <button
                  @click="regenerateField('cta_text', currentPreviewSlide)"
                  :disabled="!!regeneratingField"
                  class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-md bg-[#3B7AB1]/10 text-[#3B7AB1] hover:bg-[#3B7AB1]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  :title="'CTA neu generieren'"
                >
                  <span :class="{ 'animate-spin': regeneratingField === (currentPreviewSlide > 0 ? 'cta_text_' + currentPreviewSlide : 'cta_text') }" class="text-sm">&#x1F504;</span>
                  <span>Neu</span>
                </button>
              </div>
              <CtaPicker
                v-model="slides[currentPreviewSlide].cta_text"
                :category="selectedCategory"
                :platform="selectedPlatform"
                :topic="topic"
              />
            </div>
          </div>

          <!-- Background Color Picker -->
          <div v-if="slides[currentPreviewSlide]?.background_type !== 'image'" class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Hintergrundfarbe</label>
            <div class="flex items-center gap-3">
              <div class="flex gap-1.5 flex-wrap">
                <button
                  v-for="preset in ['#1A1A2E', '#3B7AB1', '#FDD000', '#2D6A4F', '#E63946', '#7B2CBF', '#FF6B35', '#264653']"
                  :key="preset"
                  @click="slides[currentPreviewSlide].background_value = preset; slides[currentPreviewSlide].background_type = 'color'"
                  class="w-7 h-7 rounded-lg border-2 transition-all hover:scale-110"
                  :class="slides[currentPreviewSlide].background_value === preset ? 'border-white ring-2 ring-[#3B7AB1] scale-110' : 'border-gray-300 dark:border-gray-600'"
                  :style="{ backgroundColor: preset }"
                  :title="preset"
                  data-testid="color-preset"
                ></button>
              </div>
              <div class="flex items-center gap-2 ml-auto">
                <input
                  type="color"
                  :value="slides[currentPreviewSlide].background_value || '#1A1A2E'"
                  @input="slides[currentPreviewSlide].background_value = $event.target.value; slides[currentPreviewSlide].background_type = 'color'"
                  class="w-8 h-8 rounded cursor-pointer border border-gray-300 dark:border-gray-600"
                  title="Eigene Farbe waehlen"
                  data-testid="color-picker-input"
                />
                <span class="text-xs text-gray-400 font-mono">{{ slides[currentPreviewSlide].background_value || '#1A1A2E' }}</span>
              </div>
            </div>
          </div>
          <div v-else class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Hintergrund</label>
            <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <span>&#x1F5BC;</span>
              <span>Bild als Hintergrund gesetzt</span>
              <button
                @click="slides[currentPreviewSlide].background_type = 'color'; slides[currentPreviewSlide].background_value = '#1A1A2E'"
                class="ml-auto text-xs text-[#3B7AB1] hover:underline"
              >Farbe verwenden</button>
            </div>
          </div>

          <!-- Captions editing -->
          <div class="space-y-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <div class="flex items-center justify-between mb-2">
                <label class="text-sm font-bold text-gray-700 dark:text-gray-300 flex items-center gap-1">&#x1F4F7; Instagram Caption <HelpTooltip :text="tooltipTexts.createPost.captionInstagram" size="sm" /></label>
                <button
                  @click="regenerateField('caption_instagram')"
                  :disabled="!!regeneratingField"
                  class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-md bg-[#3B7AB1]/10 text-[#3B7AB1] hover:bg-[#3B7AB1]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  :title="'Instagram Caption neu generieren'"
                >
                  <span :class="{ 'animate-spin': regeneratingField === 'caption_instagram' }" class="text-sm">&#x1F504;</span>
                  <span>Neu</span>
                </button>
              </div>
              <textarea v-model="captionInstagram" rows="3"
                class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent resize-none"
                :class="(captionInstagram?.length || 0) > 2200 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white' : (captionInstagram?.length || 0) > 1800 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-gray-900 dark:text-white' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white'"
              ></textarea>
              <div class="flex items-center justify-between mt-0.5">
                <span v-if="(captionInstagram?.length || 0) > 2200" class="text-xs text-red-500 dark:text-red-400">Instagram-Limit ueberschritten (max 2.200)</span>
                <span v-else-if="(captionInstagram?.length || 0) > 1800" class="text-xs text-amber-500 dark:text-amber-400">Nahe am Instagram-Limit</span>
                <span v-else class="text-xs text-gray-400"></span>
                <span class="text-xs" :class="(captionInstagram?.length || 0) > 2200 ? 'text-red-500 dark:text-red-400 font-semibold' : (captionInstagram?.length || 0) > 1800 ? 'text-amber-500 dark:text-amber-400' : 'text-gray-400'">{{ captionInstagram?.length || 0 }}/2.200</span>
              </div>
            </div>
            <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <div class="flex items-center justify-between mb-2">
                <label class="text-sm font-bold text-gray-700 dark:text-gray-300 flex items-center gap-1"># Instagram Hashtags <HelpTooltip :text="tooltipTexts.createPost.hashtagsInstagram" size="sm" /></label>
                <div class="flex items-center gap-1.5">
                  <button
                    @click="suggestHashtags"
                    :disabled="suggestingHashtags"
                    class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-md bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    title="KI-optimierte Hashtags vorschlagen"
                    data-testid="suggest-hashtags-btn"
                  >
                    <span :class="{ 'animate-spin': suggestingHashtags }" class="text-sm">&#x2728;</span>
                    <span>{{ suggestingHashtags ? 'Lade...' : 'Auto-Suggest' }}</span>
                  </button>
                  <button
                    @click="regenerateField('hashtags_instagram')"
                    :disabled="!!regeneratingField"
                    class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-md bg-[#3B7AB1]/10 text-[#3B7AB1] hover:bg-[#3B7AB1]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    :title="'Instagram Hashtags neu generieren'"
                  >
                    <span :class="{ 'animate-spin': regeneratingField === 'hashtags_instagram' }" class="text-sm">&#x1F504;</span>
                    <span>Neu</span>
                  </button>
                </div>
              </div>
              <textarea v-model="hashtagsInstagram" rows="2"
                class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent resize-none"
                :class="(hashtagsInstagram?.length || 0) > 2200 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-blue-600 dark:text-blue-400' : (hashtagsInstagram?.length || 0) > 1800 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-blue-600 dark:text-blue-400' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-blue-600 dark:text-blue-400'"
              ></textarea>
              <div class="flex items-center justify-between mt-0.5">
                <span v-if="(hashtagsInstagram?.length || 0) > 2200" class="text-xs text-red-500 dark:text-red-400">Hashtag-Limit ueberschritten</span>
                <span v-else class="text-xs text-gray-400"></span>
                <span class="text-xs" :class="(hashtagsInstagram?.length || 0) > 2200 ? 'text-red-500 dark:text-red-400 font-semibold' : 'text-gray-400'">{{ hashtagsInstagram?.length || 0 }} Zeichen</span>
              </div>
              <!-- Emoji Suggestions Row -->
              <div v-if="suggestedEmojis.length > 0" class="mt-2 flex items-center gap-1.5 flex-wrap" data-testid="emoji-suggestions">
                <span class="text-xs text-gray-500 dark:text-gray-400">Empfohlene Emojis:</span>
                <button
                  v-for="(emoji, eidx) in suggestedEmojis"
                  :key="eidx"
                  @click="captionInstagram += ' ' + emoji"
                  class="text-lg hover:scale-125 transition-transform cursor-pointer"
                  :title="'In Caption einfuegen: ' + emoji"
                >{{ emoji }}</button>
              </div>
            </div>
            <div class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <div class="flex items-center justify-between mb-2">
                <label class="text-sm font-bold text-gray-700 dark:text-gray-300 flex items-center gap-1">&#x1F3B5; TikTok Hashtags <HelpTooltip :text="tooltipTexts.createPost.hashtagsTiktok" size="sm" /></label>
                <button
                  @click="regenerateField('hashtags_tiktok')"
                  :disabled="!!regeneratingField"
                  class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-md bg-[#3B7AB1]/10 text-[#3B7AB1] hover:bg-[#3B7AB1]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  :title="'TikTok Hashtags neu generieren'"
                >
                  <span :class="{ 'animate-spin': regeneratingField === 'hashtags_tiktok' }" class="text-sm">&#x1F504;</span>
                  <span>Neu</span>
                </button>
              </div>
              <textarea v-model="hashtagsTiktok" rows="2"
                class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent resize-none"
                :class="(hashtagsTiktok?.length || 0) > 2200 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-blue-600 dark:text-blue-400' : (hashtagsTiktok?.length || 0) > 1800 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-blue-600 dark:text-blue-400' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-blue-600 dark:text-blue-400'"
              ></textarea>
              <div class="flex items-center justify-between mt-0.5">
                <span v-if="(hashtagsTiktok?.length || 0) > 2200" class="text-xs text-red-500 dark:text-red-400">Hashtag-Limit ueberschritten</span>
                <span v-else class="text-xs text-gray-400"></span>
                <span class="text-xs" :class="(hashtagsTiktok?.length || 0) > 2200 ? 'text-red-500 dark:text-red-400 font-semibold' : 'text-gray-400'">{{ hashtagsTiktok?.length || 0 }} Zeichen</span>
              </div>
            </div>
          </div>

          <!-- Interactive Story Elements Editor (only when Instagram Story is selected) -->
          <InteractiveElementEditor
            v-if="showInteractiveElements"
            :interactive-elements="interactiveElements"
            :slide-index="currentPreviewSlide"
            :topic="topic || slides[0]?.headline || ''"
            :country="country"
            @add="addInteractiveElement"
            @remove="removeInteractiveElement"
            @edit="editInteractiveElement"
          />

          <!-- Episode Fields (shown when post is part of a Story-Arc) -->
          <div v-if="selectedArcId" class="p-4 rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 space-y-3" data-testid="episode-edit-fields">
            <h4 class="text-sm font-bold text-[#3B7AB1] flex items-center gap-2">
              📖 Episoden-Texte
              <span class="text-xs font-normal text-gray-500">Episode {{ selectedEpisodeNumber }}</span>
            </h4>
            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-gray-600 dark:text-gray-400">Rueckblick</label>
                <button
                  @click="suggestEpisodeText('previously_text')"
                  :disabled="!!suggestingEpisodeField"
                  class="text-[10px] text-[#3B7AB1] hover:text-[#2E6A9E] font-medium disabled:opacity-50"
                >✨ KI</button>
              </div>
              <textarea v-model="episodePreviouslyText" rows="2" placeholder="Bisher bei..." class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent resize-none"></textarea>
            </div>
            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-gray-600 dark:text-gray-400">Cliffhanger</label>
                <button
                  @click="suggestEpisodeText('cliffhanger_text')"
                  :disabled="!!suggestingEpisodeField"
                  class="text-[10px] text-[#3B7AB1] hover:text-[#2E6A9E] font-medium disabled:opacity-50"
                >✨ KI</button>
              </div>
              <textarea v-model="episodeCliffhangerText" rows="2" placeholder="Cliffhanger am Ende..." class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent resize-none"></textarea>
            </div>
            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-gray-600 dark:text-gray-400">Teaser naechste Episode</label>
                <button
                  @click="suggestEpisodeText('next_episode_hint')"
                  :disabled="!!suggestingEpisodeField"
                  class="text-[10px] text-[#3B7AB1] hover:text-[#2E6A9E] font-medium disabled:opacity-50"
                >✨ KI</button>
              </div>
              <textarea v-model="episodeNextHint" rows="2" placeholder="Naechste Episode..." class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent resize-none"></textarea>
            </div>
          </div>

          <!-- Cliffhanger & Teaser System (when post is part of a Story-Arc and not the last episode) -->
          <CliffhangerPanel
            v-if="selectedArcId"
            :arc-id="selectedArcId"
            :episode-number="selectedEpisodeNumber"
            :planned-episodes="storyArcStore.storyArcs.find(a => a.id === selectedArcId)?.planned_episodes || 8"
            :episode-content="topic || slides[0]?.headline || ''"
            :initial-cliffhanger="episodeCliffhangerText"
            :initial-teaser="episodeNextHint"
            @update:cliffhanger="episodeCliffhangerText = $event"
            @update:teaser="episodeNextHint = $event"
            @generated="onCliffhangerGenerated"
          />
        </div>

        <!-- Mini live preview (sticky) -->
        <div class="lg:sticky lg:top-4 self-start">
          <!-- Platform preview toggle (mini version for step 7) -->
          <div class="flex items-center justify-between mb-2">
            <div class="text-sm font-medium text-gray-700 dark:text-gray-300">Live-Vorschau</div>
            <div class="flex items-center gap-0.5 p-0.5 bg-gray-100 dark:bg-gray-800 rounded-lg" data-testid="mini-platform-preview-toggle">
              <button
                v-for="p in platforms"
                :key="p.id"
                @click="previewPlatform = p.id"
                class="px-1.5 py-0.5 rounded text-xs transition-all"
                :class="effectivePreviewPlatform === p.id
                  ? 'bg-white dark:bg-gray-700 text-[#3B7AB1] shadow-sm font-medium'
                  : 'text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-400'"
                :data-testid="'mini-preview-toggle-' + p.id"
                :title="p.label + ' (' + p.format + ')'"
              >
                {{ p.icon }}
              </button>
            </div>
          </div>
          <div
            class="rounded-2xl overflow-hidden shadow-xl border border-gray-200 dark:border-gray-700 relative"
            :class="{
              'aspect-square': effectivePreviewPlatform === 'instagram_feed',
              'aspect-[9/16]': effectivePreviewPlatform === 'instagram_story' || effectivePreviewPlatform === 'tiktok',
            }"
            :style="{
              maxWidth: '320px',
              background: slides[currentPreviewSlide]?.background_type === 'image'
                ? `url(${slides[currentPreviewSlide].background_value}) center/cover`
                : slides[currentPreviewSlide]?.background_value || 'linear-gradient(135deg, #1A1A2E, #2a2a4e)',
            }"
            data-testid="live-preview-container"
          >
            <div v-if="slides[currentPreviewSlide]" class="absolute inset-0 p-5 flex flex-col justify-between">
              <div class="flex items-center gap-1.5">
                <div class="bg-[#3B7AB1] rounded px-2 py-0.5"><span class="text-white text-[10px] font-bold">TREFF</span></div>
                <span v-if="selectedArcId" class="ml-auto bg-[#FDD000] text-[#1A1A2E] px-1.5 py-0.5 rounded-full text-[8px] font-bold">E{{ selectedEpisodeNumber }}</span>
              </div>
              <div v-if="selectedArcId && episodePreviouslyText && currentPreviewSlide === 0" class="mt-1 px-1.5 py-0.5 bg-white/10 rounded text-gray-300 text-[8px] italic leading-tight line-clamp-1">{{ episodePreviouslyText }}</div>
              <div class="flex-1 flex flex-col justify-center py-3">
                <h3 class="text-white text-base font-extrabold leading-tight mb-1.5 drop-shadow-md" data-testid="preview-headline">{{ slides[currentPreviewSlide].headline }}</h3>
                <p v-if="slides[currentPreviewSlide].subheadline" class="text-[#FDD000] text-[11px] font-semibold mb-1.5 drop-shadow">{{ slides[currentPreviewSlide].subheadline }}</p>
                <p v-if="slides[currentPreviewSlide].body_text" class="text-gray-200 text-[10px] leading-relaxed line-clamp-4 drop-shadow" data-testid="preview-body">{{ slides[currentPreviewSlide].body_text }}</p>
              </div>
              <div v-if="selectedArcId && episodeCliffhangerText && currentPreviewSlide === slides.length - 1" class="mb-1 px-1.5 py-0.5 bg-white/10 rounded text-[#FDD000] text-[8px] font-semibold italic line-clamp-1">{{ episodeCliffhangerText }}</div>
              <div v-if="slides[currentPreviewSlide].cta_text">
                <div class="inline-block bg-[#FDD000] text-[#1A1A2E] px-4 py-1.5 rounded-full font-bold text-[11px]">{{ slides[currentPreviewSlide].cta_text }}</div>
              </div>
            </div>

            <!-- Interactive Story Element Overlays (mini preview) -->
            <InteractiveElementPreview
              v-for="(el, ielIdx) in currentSlideInteractiveElements"
              :key="'mini-' + (el.id || el._tempId || ielIdx)"
              :element="el"
              :interactive="true"
              @remove="removeInteractiveElement"
              @edit="(e) => { /* handled by editor panel */ }"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 8: Background Image Upload / AI Generation (Optional) -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 8">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">Schritt 8: Hintergrundbild (optional) <HelpTooltip :text="tooltipTexts.createPost.stepBackground" /></h2>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div class="space-y-6">

          <!-- AI Image Generation -->
          <div class="border-2 border-purple-300 dark:border-purple-600 rounded-xl p-6 bg-purple-50/50 dark:bg-purple-900/10">
            <div class="flex items-center gap-2 mb-3">
              <span class="text-2xl">🤖</span>
              <h3 class="text-sm font-semibold text-purple-800 dark:text-purple-300">KI-Bild generieren</h3>
            </div>

            <!-- Prompt Input -->
            <div class="mb-3">
              <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1">Bildbeschreibung (Prompt)</label>
              <textarea
                v-model="aiImagePrompt"
                rows="3"
                maxlength="500"
                class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-purple-400 focus:border-purple-400 resize-none"
                placeholder="z.B. American high school hallway with students"
                :disabled="generatingImage"
              ></textarea>
              <div class="flex justify-between items-center mt-1">
                <span class="text-xs text-gray-400">{{ aiImagePrompt.length }}/500</span>
              </div>
            </div>

            <!-- Prompt Suggestions -->
            <div class="mb-4">
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-2">Vorschlaege:</p>
              <div class="flex flex-wrap gap-1.5">
                <button
                  v-for="suggestion in promptSuggestions"
                  :key="suggestion"
                  @click="selectPromptSuggestion(suggestion)"
                  class="text-xs px-2.5 py-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-full hover:border-purple-400 hover:text-purple-700 dark:hover:text-purple-300 transition-colors truncate max-w-[200px]"
                  :disabled="generatingImage"
                >
                  {{ suggestion }}
                </button>
              </div>
            </div>

            <!-- Aspect Ratio Selection -->
            <div class="mb-4">
              <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2">Seitenverhaeltnis</label>
              <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mb-2">
                <span>Plattform: {{ selectedPlatformObj?.label || 'Nicht gewaehlt' }}</span>
                <span class="text-purple-500 font-medium">({{ platformAspectRatioLabel }})</span>
              </div>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="ar in aspectRatioOptions"
                  :key="ar.value"
                  @click="aiImageAspectRatio = aiImageAspectRatio === ar.value ? '' : ar.value"
                  :class="[
                    'px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
                    (aiImageAspectRatio === ar.value || (!aiImageAspectRatio && ar.value === platformDefaultAspectRatio))
                      ? 'bg-purple-600 text-white border-purple-600'
                      : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:border-purple-400'
                  ]"
                  :disabled="generatingImage"
                >
                  {{ ar.label }}
                  <span v-if="ar.value === platformDefaultAspectRatio && !aiImageAspectRatio" class="ml-1 opacity-75">(Auto)</span>
                </button>
              </div>
              <p v-if="aiImageAspectRatio && aiImageAspectRatio !== platformDefaultAspectRatio" class="text-xs text-amber-600 dark:text-amber-400 mt-1">
                Manuell ueberschrieben (Standard fuer {{ selectedPlatformObj?.label }}: {{ platformDefaultAspectRatio }})
              </p>
            </div>

            <!-- Generate Button -->
            <button
              @click="generateAiImage"
              :disabled="generatingImage || !aiImagePrompt.trim()"
              class="w-full px-4 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center gap-2"
            >
              <span v-if="generatingImage" class="flex items-center gap-2">
                <span class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                Bild wird generiert...
              </span>
              <span v-else>🎨 Bild generieren ({{ effectiveAspectRatio }})</span>
            </button>

            <!-- AI Error -->
            <div v-if="aiImageError" class="mt-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-sm text-red-700 dark:text-red-300" role="alert">
              {{ aiImageError }}
            </div>

            <!-- Generated Image Result -->
            <div v-if="generatedImageResult && generatedImageResult.status === 'success'" class="mt-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
              <div class="flex items-center gap-2 mb-2">
                <span class="text-green-600">✓</span>
                <span class="text-sm font-medium text-green-700 dark:text-green-300">{{ generatedImageResult.message }}</span>
              </div>
              <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 flex-wrap">
                <span>Quelle: {{ generatedImageResult.source === 'gemini' ? 'Gemini AI' : 'Lokale Generierung' }}</span>
                <span v-if="generatedImageResult.asset">| {{ generatedImageResult.asset.width }}x{{ generatedImageResult.asset.height }}px</span>
                <span v-if="generatedImageResult.aspect_ratio">| Verhaeltnis: {{ generatedImageResult.aspect_ratio }}</span>
                <span v-if="generatedImageResult.platform">| Plattform: {{ generatedImageResult.platform }}</span>
              </div>
            </div>
          </div>

          <!-- Divider -->
          <div class="relative">
            <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-gray-200 dark:border-gray-700"></div></div>
            <div class="relative flex justify-center"><span class="bg-white dark:bg-gray-900 px-3 text-sm text-gray-400">oder</span></div>
          </div>

          <!-- Upload -->
          <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-8 text-center hover:border-[#3B7AB1] transition-colors">
            <div class="text-4xl mb-3">📷</div>
            <p class="text-gray-600 dark:text-gray-400 mb-3">Hintergrundbild hochladen</p>
            <label class="inline-block px-6 py-2.5 bg-[#3B7AB1] text-white rounded-lg cursor-pointer hover:bg-[#2E6A9E] transition-colors font-medium">
              <span v-if="uploadingImage" class="flex items-center gap-2">
                <span class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                Hochladen...
              </span>
              <span v-else>Datei waehlen</span>
              <input type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="uploadBackgroundImage" :disabled="uploadingImage" />
            </label>
            <p class="text-xs text-gray-400 mt-2">JPG, PNG oder WebP (max. 20 MB)</p>
          </div>

          <!-- Existing assets -->
          <div v-if="assets.length > 0">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Vorhandene Bilder:</h3>
            <div class="grid grid-cols-3 sm:grid-cols-4 gap-3">
              <button
                v-for="asset in assets"
                :key="asset.id"
                @click="selectAssetAsBackground(asset)"
                class="aspect-square rounded-lg overflow-hidden border-2 border-gray-200 dark:border-gray-700 hover:border-[#3B7AB1] transition-all relative group"
              >
                <img :src="`/api/uploads/assets/${asset.filename}`" :alt="asset.original_filename" class="w-full h-full object-cover" />
                <div v-if="asset.source === 'ai_generated'" class="absolute top-1 right-1 bg-purple-600 text-white text-[8px] px-1.5 py-0.5 rounded font-bold">KI</div>
              </button>
            </div>
          </div>

          <div class="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 text-sm text-gray-500 dark:text-gray-400">
            💡 Dieser Schritt ist optional. Ohne Bild wird der Standard-Farbverlauf verwendet.
          </div>
        </div>

        <!-- Preview -->
        <div class="self-start">
          <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Vorschau</div>
          <div
            class="rounded-2xl overflow-hidden shadow-xl border border-gray-200 dark:border-gray-700 relative"
            :class="{
              'aspect-square': selectedPlatform === 'instagram_feed',
              'aspect-[9/16]': selectedPlatform === 'instagram_story' || selectedPlatform === 'tiktok',
            }"
            :style="{
              maxWidth: '320px',
              background: slides[currentPreviewSlide]?.background_type === 'image'
                ? `url(${slides[currentPreviewSlide].background_value}) center/cover`
                : 'linear-gradient(135deg, #1A1A2E, #2a2a4e)',
            }"
          >
            <div v-if="slides[currentPreviewSlide]" class="absolute inset-0 p-5 flex flex-col justify-between bg-black/20">
              <div class="flex items-center gap-1.5">
                <div class="bg-[#3B7AB1] rounded px-2 py-0.5"><span class="text-white text-[10px] font-bold">TREFF</span></div>
              </div>
              <div class="flex-1 flex flex-col justify-center py-3">
                <h3 class="text-white text-base font-extrabold leading-tight mb-1.5 drop-shadow">{{ slides[currentPreviewSlide].headline }}</h3>
                <p v-if="slides[currentPreviewSlide].subheadline" class="text-[#FDD000] text-[11px] font-semibold drop-shadow">{{ slides[currentPreviewSlide].subheadline }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- STEP 9: Export / Save -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="currentStep === 9">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">Schritt 9: Exportieren & Speichern <HelpTooltip :text="tooltipTexts.createPost.stepExport" /></h2>

      <!-- Pre-export summary -->
      <div v-if="!exportComplete" class="max-w-2xl mx-auto bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4">Zusammenfassung</h3>
        <div class="grid grid-cols-2 gap-3 text-sm mb-6">
          <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div class="text-gray-500 dark:text-gray-400 text-xs">Kategorie</div>
            <div class="font-medium text-gray-900 dark:text-white">{{ selectedCategoryObj?.icon }} {{ selectedCategoryObj?.label }}</div>
          </div>
          <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div class="text-gray-500 dark:text-gray-400 text-xs">Plattform{{ selectedPlatforms.length > 1 ? 'en' : '' }}</div>
            <div class="font-medium text-gray-900 dark:text-white">
              <span v-for="(pId, idx) in selectedPlatforms" :key="pId">
                {{ platforms.find(p => p.id === pId)?.icon }} {{ platforms.find(p => p.id === pId)?.label }}<span v-if="idx < selectedPlatforms.length - 1">, </span>
              </span>
            </div>
          </div>
          <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div class="text-gray-500 dark:text-gray-400 text-xs">Template</div>
            <div class="font-medium text-gray-900 dark:text-white">{{ selectedTemplate?.name }}</div>
          </div>
          <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div class="text-gray-500 dark:text-gray-400 text-xs">Slides</div>
            <div class="font-medium text-gray-900 dark:text-white">{{ slides.length }}</div>
          </div>
          <div v-if="selectedCountryObj" class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div class="text-gray-500 dark:text-gray-400 text-xs">Land</div>
            <div class="font-medium text-gray-900 dark:text-white">{{ selectedCountryObj.flag }} {{ selectedCountryObj.label }}</div>
          </div>
          <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div class="text-gray-500 dark:text-gray-400 text-xs">Headline</div>
            <div class="font-medium text-gray-900 dark:text-white truncate">{{ slides[0]?.headline }}</div>
          </div>
        </div>

        <!-- Interactive Elements Reminder (shown when elements exist) -->
        <div v-if="interactiveElements.length > 0" class="mb-6 p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800" data-testid="export-interactive-reminder">
          <div class="flex items-start gap-3">
            <span class="text-2xl">🎯</span>
            <div>
              <h4 class="font-bold text-amber-800 dark:text-amber-300 text-sm mb-1">Vergiss nicht die interaktiven Elemente!</h4>
              <p class="text-xs text-amber-700 dark:text-amber-400 leading-relaxed mb-2">
                Du hast {{ interactiveElements.length }} interaktive{{ interactiveElements.length > 1 ? ' Elemente' : 's Element' }} erstellt. Diese muessen beim echten Posten in Instagram manuell hinzugefuegt werden:
              </p>
              <ul class="space-y-1">
                <li v-for="(el, idx) in interactiveElements" :key="idx" class="flex items-center gap-2 text-xs text-amber-700 dark:text-amber-400">
                  <span>{{ { poll: '📊', quiz: '🧠', slider: '🎚️', question: '❓' }[el.element_type] }}</span>
                  <span class="font-medium">{{ { poll: 'Umfrage', quiz: 'Quiz', slider: 'Emoji-Slider', question: 'Fragen-Sticker' }[el.element_type] }}:</span>
                  <span class="truncate">{{ el.question_text }}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Export Quality Selector -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Export-Qualitaet</label>
          <div class="flex gap-3">
            <button
              @click="exportQuality = '1080'"
              data-testid="quality-1080"
              :class="[
                'flex-1 px-4 py-3 rounded-lg border-2 transition-all text-sm font-medium',
                exportQuality === '1080'
                  ? 'border-[#3B7AB1] bg-[#3B7AB1]/10 text-[#3B7AB1]'
                  : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-300'
              ]"
            >
              <div class="font-bold">Standard (1080px)</div>
              <div class="text-xs mt-0.5 opacity-70">Empfohlen fuer Social Media</div>
            </button>
            <button
              @click="exportQuality = '2160'"
              data-testid="quality-2160"
              :class="[
                'flex-1 px-4 py-3 rounded-lg border-2 transition-all text-sm font-medium',
                exportQuality === '2160'
                  ? 'border-[#3B7AB1] bg-[#3B7AB1]/10 text-[#3B7AB1]'
                  : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-300'
              ]"
            >
              <div class="font-bold">Hohe Qualitaet (2160px)</div>
              <div class="text-xs mt-0.5 opacity-70">Fuer Druck und hohe Aufloesung</div>
            </button>
          </div>
        </div>

        <div class="flex flex-col sm:flex-row gap-3">
          <!-- Multi-platform export button (shown when multiple platforms selected) -->
          <button
            v-if="selectedPlatforms.length > 1"
            @click="exportAllPlatforms"
            :disabled="exporting"
            data-testid="export-all-platforms-btn"
            class="flex-1 px-6 py-3 bg-[#3B7AB1] hover:bg-[#2E6A9E] disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <span v-if="exporting" class="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></span>
            {{ exporting ? 'Exportiere...' : `Alle ${selectedPlatforms.length} Plattformen exportieren` }}
          </button>
          <!-- Single-platform export button (shown when only one platform selected) -->
          <button
            v-else
            @click="saveAndExport"
            :disabled="exporting"
            class="flex-1 px-6 py-3 bg-[#3B7AB1] hover:bg-[#2E6A9E] disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <span v-if="exporting" class="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></span>
            {{ exporting ? 'Speichern...' : 'Post speichern & exportieren' }}
          </button>
          <button
            v-if="slides.length > 1"
            @click="downloadAsZip"
            :disabled="slides.length === 0"
            class="flex-1 px-6 py-3 bg-[#FDD000] hover:bg-[#e5c000] disabled:bg-gray-300 text-[#1A1A2E] font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            📦 Als ZIP herunterladen ({{ slides.length }} Slides)
          </button>
          <button
            v-else
            @click="downloadAsImage"
            :disabled="slides.length === 0"
            class="flex-1 px-6 py-3 bg-[#FDD000] hover:bg-[#e5c000] disabled:bg-gray-300 text-[#1A1A2E] font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            ⬇ Als PNG herunterladen
          </button>
        </div>
      </div>

      <!-- Export complete -->
      <div v-if="exportComplete" class="max-w-2xl mx-auto bg-white dark:bg-gray-800 rounded-xl border border-green-200 dark:border-green-800 p-8 text-center">
        <div class="text-6xl mb-4">🎉</div>
        <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">Post erfolgreich erstellt!</h3>
        <p class="text-gray-500 dark:text-gray-400 mb-4">
          Dein Post wurde in der Datenbank gespeichert und als exportiert markiert.
        </p>
        <div v-if="savedPost" class="text-sm text-gray-600 dark:text-gray-400 mb-6 space-y-1">
          <div>Post ID: <strong>#{{ savedPost.id }}</strong></div>
          <div>Status: <strong>{{ savedPost.status }}</strong></div>
          <div>Kategorie: <strong>{{ selectedCategoryObj?.label }}</strong></div>
          <div v-if="selectedPlatforms.length > 1">Plattformen: <strong>{{ selectedPlatforms.length }}</strong> ({{ selectedPlatforms.map(pId => platforms.find(p => p.id === pId)?.label).join(', ') }})</div>
        </div>
        <div class="flex flex-col sm:flex-row gap-3 justify-center">
          <button v-if="selectedPlatforms.length > 1" @click="exportAllPlatforms" class="px-6 py-3 bg-[#FDD000] hover:bg-[#e5c000] text-[#1A1A2E] font-bold rounded-lg transition-colors">
            📦 Alle Plattformen erneut herunterladen
          </button>
          <button v-else-if="slides.length > 1" @click="downloadAsZip" class="px-6 py-3 bg-[#FDD000] hover:bg-[#e5c000] text-[#1A1A2E] font-bold rounded-lg transition-colors">
            📦 ZIP herunterladen ({{ slides.length }} Slides)
          </button>
          <button v-else @click="downloadAsImage" class="px-6 py-3 bg-[#FDD000] hover:bg-[#e5c000] text-[#1A1A2E] font-bold rounded-lg transition-colors">
            ⬇ PNG herunterladen
          </button>
          <button @click="router.push('/dashboard')" class="px-6 py-3 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-900 dark:text-white font-bold rounded-lg transition-colors">
            Zum Dashboard
          </button>
          <button @click="resetWorkflow" class="px-6 py-3 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium rounded-lg transition-colors">
            Neuen Post erstellen
          </button>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- Validation Message -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div v-if="validationMessage" class="mt-4 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-300 dark:border-amber-700 rounded-lg text-amber-800 dark:text-amber-300 flex items-center gap-2" role="alert" data-testid="validation-message">
      <span class="text-lg">&#9888;&#65039;</span>
      <span>{{ validationMessage }}</span>
      <button @click="validationMessage = ''" class="ml-auto text-amber-600 hover:text-amber-800 dark:text-amber-400 dark:hover:text-amber-200 font-bold">&times;</button>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- Navigation Buttons -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div class="flex items-center justify-between mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
      <button
        v-if="currentStep > 1 && !exportComplete"
        @click="prevStep"
        class="px-6 py-3 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 font-medium transition-colors"
      >
        &#8592; Zurueck
      </button>
      <div v-else></div>

      <button
        v-if="currentStep < totalSteps && !exportComplete"
        @click="nextStep"
        class="px-6 py-3 rounded-lg font-medium transition-colors"
        :class="canProceed
          ? 'bg-[#3B7AB1] hover:bg-[#2E6A9E] text-white'
          : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'"
      >
        Weiter &#8594;
      </button>
    </div>

    <!-- Delete Slide Confirmation Modal -->
    <Teleport to="body">
      <div
        v-if="showDeleteSlideConfirm"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        @click.self="cancelRemoveSlide"
      >
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-6 max-w-sm w-full mx-4 transform transition-all" data-testid="delete-slide-modal">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <span class="text-lg">&#9888;</span>
            </div>
            <div>
              <h3 class="text-lg font-bold text-gray-900 dark:text-white">Slide entfernen?</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Slide {{ slideToDeleteIndex + 1 }} wird unwiderruflich entfernt.
              </p>
            </div>
          </div>
          <div class="flex gap-3">
            <button
              @click="cancelRemoveSlide"
              class="flex-1 px-4 py-2.5 rounded-lg text-sm font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              Abbrechen
            </button>
            <button
              @click="confirmRemoveSlide"
              class="flex-1 px-4 py-2.5 rounded-lg text-sm font-medium bg-red-600 text-white hover:bg-red-700 transition-colors"
              data-testid="confirm-delete-slide-btn"
            >
              Entfernen
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Unsaved Changes Warning Dialog -->
    <Teleport to="body">
      <div v-if="showLeaveDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" data-testid="unsaved-changes-dialog">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-6 max-w-sm mx-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Ungespeicherte Aenderungen</h3>
          <p class="text-gray-600 dark:text-gray-300 text-sm mb-6">
            Du hast ungespeicherte Aenderungen. Wenn du die Seite verlaesst, gehen diese verloren.
          </p>
          <div class="flex gap-3 justify-end">
            <button
              @click="cancelLeave"
              class="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors font-medium text-sm"
              data-testid="unsaved-stay-btn"
            >
              Auf Seite bleiben
            </button>
            <button
              @click="confirmLeave"
              class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors font-medium text-sm"
              data-testid="unsaved-leave-btn"
            >
              Verwerfen & Verlassen
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Overwrite Confirmation Dialog (race condition protection) -->
    <Teleport to="body">
      <div v-if="showOverwriteDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" data-testid="overwrite-dialog">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-6 max-w-md w-full mx-4 transform transition-all">
          <div class="text-center mb-4">
            <div class="text-4xl mb-2">&#x26A0;&#xFE0F;</div>
            <h3 class="text-lg font-bold text-gray-900 dark:text-white">Neue KI-Inhalte verfuegbar</h3>
          </div>
          <p class="text-gray-600 dark:text-gray-400 text-sm mb-6">
            Du hast Inhalte manuell bearbeitet, waehrend die KI neue Texte generiert hat.
            Moechtest du deine manuellen Aenderungen durch die neuen KI-Inhalte ersetzen?
          </p>
          <div class="flex gap-3">
            <button
              @click="dismissPendingGeneration"
              class="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors font-medium"
              data-testid="keep-manual-edits-btn"
            >
              Meine Aenderungen behalten
            </button>
            <button
              @click="acceptPendingGeneration"
              class="flex-1 px-4 py-2 bg-[#3B7AB1] hover:bg-[#2E6A9E] text-white rounded-lg transition-colors font-medium"
              data-testid="accept-ai-content-btn"
            >
              KI-Inhalte uebernehmen
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.slide-ghost {
  opacity: 0.4;
  background: #3B7AB1 !important;
  border-radius: 0.5rem;
}
</style>
