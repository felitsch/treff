<script setup>
/**
 * LivePreview.vue — Permanent real-time preview panel for the Post Creator.
 *
 * Shows a phone mockup frame with platform-specific UI overlays:
 *  - Instagram Feed: square post with header (avatar + @treff_sprachreisen), image, caption
 *  - Instagram Story: 9:16 portrait in phone frame with story indicators
 *  - TikTok: 9:16 portrait with TikTok-specific sidebar icons
 *
 * Debounces updates at 300ms so fast typing doesn't cause jank.
 * On desktop: rendered as a sticky right column.
 * On mobile: toggle-able bottom sheet / floating button.
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  /** Currently selected platform id: 'instagram_feed' | 'instagram_story' | 'tiktok' */
  platform: { type: String, default: 'instagram_feed' },
  /** Array of selected platform ids for the toggle pills */
  platforms: { type: Array, default: () => ['instagram_feed'] },
  /** Slides array from the content draft */
  slides: { type: Array, default: () => [] },
  /** Current slide index for preview */
  currentSlideIndex: { type: Number, default: 0 },
  /** Instagram caption */
  captionInstagram: { type: String, default: '' },
  /** TikTok caption */
  captionTiktok: { type: String, default: '' },
  /** Instagram hashtags string */
  hashtagsInstagram: { type: String, default: '' },
  /** TikTok hashtags string */
  hashtagsTiktok: { type: String, default: '' },
  /** CTA text */
  ctaText: { type: String, default: '' },
  /** Selected category label */
  categoryLabel: { type: String, default: '' },
  /** Country object { id, label, flag } */
  country: { type: Object, default: null },
  /** Background image URL (from asset or AI) */
  backgroundImage: { type: String, default: '' },
  /** Story arc episode number (optional) */
  episodeNumber: { type: Number, default: null },
  /** Episode previously text (optional) */
  episodePreviouslyText: { type: String, default: '' },
  /** Episode cliffhanger text (optional) */
  episodeCliffhangerText: { type: String, default: '' },
  /** Episode next hint (optional) */
  episodeNextHint: { type: String, default: '' },
  /** Template placeholder values object { fieldName: 'value' } for real-time substitution */
  templatePlaceholderValues: { type: Object, default: () => ({}) },
  /** Selected template object (with html_content, css_content, placeholder_fields) */
  selectedTemplate: { type: Object, default: null },
})

const emit = defineEmits(['update:platform', 'update:currentSlideIndex'])

// ── Debounced state ───────────────────────────────────────────────────
// We copy props into local refs with a 300ms debounce to avoid jank
const dSlides = ref([])
const dCaption = ref('')
const dHashtags = ref('')
const dCta = ref('')
let debounceTimer = null

function debounceUpdate() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    dSlides.value = props.slides
    dCaption.value = activePlatform.value === 'tiktok' ? props.captionTiktok : props.captionInstagram
    dHashtags.value = activePlatform.value === 'tiktok' ? props.hashtagsTiktok : props.hashtagsInstagram
    dCta.value = props.ctaText
  }, 300)
}

// Watch all content props for debounced updates
watch(
  () => [props.slides, props.captionInstagram, props.captionTiktok, props.hashtagsInstagram, props.hashtagsTiktok, props.ctaText, props.platform],
  debounceUpdate,
  { deep: true, immediate: true }
)

onUnmounted(() => clearTimeout(debounceTimer))

// ── Active platform ──────────────────────────────────────────────────
const activePlatform = computed(() => props.platform || 'instagram_feed')

function selectPlatform(pId) {
  emit('update:platform', pId)
}

// ── Slide navigation ──────────────────────────────────────────────────
const currentSlide = computed(() => dSlides.value[props.currentSlideIndex] || null)
const slideCount = computed(() => dSlides.value.length)

function prevSlide() {
  if (props.currentSlideIndex > 0) {
    emit('update:currentSlideIndex', props.currentSlideIndex - 1)
  }
}

function nextSlide() {
  if (props.currentSlideIndex < slideCount.value - 1) {
    emit('update:currentSlideIndex', props.currentSlideIndex + 1)
  }
}

function goToSlide(idx) {
  emit('update:currentSlideIndex', idx)
}

// ── Aspect ratio ─────────────────────────────────────────────────────
const isPortrait = computed(() => activePlatform.value === 'instagram_story' || activePlatform.value === 'tiktok')
const isSquare = computed(() => activePlatform.value === 'instagram_feed')

// ── Platform pill display data ───────────────────────────────────────
const platformData = {
  instagram_feed: { icon: '\uD83D\uDCF7', label: 'Feed', format: '1:1' },
  instagram_story: { icon: '\uD83D\uDCF1', label: 'Story', format: '9:16' },
  tiktok: { icon: '\uD83C\uDFB5', label: 'TikTok', format: '9:16' },
}

// ── Mobile toggle ────────────────────────────────────────────────────
const showMobilePreview = ref(false)
function toggleMobilePreview() {
  showMobilePreview.value = !showMobilePreview.value
}

// ── Has content ──────────────────────────────────────────────────────
const hasContent = computed(() => {
  return dSlides.value.length > 0 || dCaption.value || dCta.value || props.categoryLabel
})

// ── Effective caption (Instagram or TikTok) ──────────────────────────
const effectiveCaption = computed(() => {
  return activePlatform.value === 'tiktok' ? props.captionTiktok : props.captionInstagram
})

const effectiveHashtags = computed(() => {
  return activePlatform.value === 'tiktok' ? props.hashtagsTiktok : props.hashtagsInstagram
})

// ── Template Placeholder Substitution ────────────────────────────────
// Replace {{variable}} patterns in text with actual placeholder values in real-time
const placeholderRegex = /\{\{(\w+)\}\}/g

function substitutePlaceholders(text) {
  if (!text || typeof text !== 'string') return text
  const vals = props.templatePlaceholderValues
  if (!vals || Object.keys(vals).length === 0) return text
  return text.replace(placeholderRegex, (match, key) => {
    const val = vals[key]
    return (val && val.trim()) ? val : match // Keep original {{key}} if unfilled
  })
}

// Resolved current slide with placeholder values substituted into all text fields
const resolvedSlide = computed(() => {
  const slide = currentSlide.value
  if (!slide) return null
  const vals = props.templatePlaceholderValues
  if (!vals || Object.keys(vals).length === 0) return slide
  // Return a new object with substituted text fields
  return {
    ...slide,
    headline: substitutePlaceholders(slide.headline),
    subheadline: substitutePlaceholders(slide.subheadline),
    body_text: substitutePlaceholders(slide.body_text),
    cta_text: substitutePlaceholders(slide.cta_text),
    bullet_points: Array.isArray(slide.bullet_points)
      ? slide.bullet_points.map(bp => substitutePlaceholders(bp))
      : slide.bullet_points,
  }
})

// Resolved caption with placeholder substitution
const resolvedCaption = computed(() => substitutePlaceholders(dCaption.value))
const resolvedHashtags = computed(() => substitutePlaceholders(dHashtags.value))
const resolvedCta = computed(() => substitutePlaceholders(dCta.value))

// Template HTML preview with placeholders replaced — used for an inline template rendering mode
const resolvedTemplateHtml = computed(() => {
  if (!props.selectedTemplate?.html_content) return ''
  let html = props.selectedTemplate.html_content
  const vals = props.templatePlaceholderValues
  if (vals && Object.keys(vals).length > 0) {
    html = html.replace(placeholderRegex, (match, key) => {
      const val = vals[key]
      if (key === 'image' || key === 'bild') {
        // Image placeholders: show a placeholder box or actual image if uploaded
        return val ? `<img src="${val}" style="max-width:100%;height:auto;border-radius:8px;" alt="Bild" />` : '<div style="width:100%;height:120px;background:rgba(255,255,255,0.1);border-radius:8px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.4);font-size:12px;">🖼️ Bild</div>'
      }
      return (val && val.trim()) ? val : `<span style="opacity:0.4;font-style:italic;">${match}</span>`
    })
  }
  return html
})

// Whether the template has renderable HTML for an inline preview
const hasTemplateHtml = computed(() => {
  return !!props.selectedTemplate?.html_content && props.selectedTemplate.html_content.trim().length > 0
})
</script>

<template>
  <!-- ═══════════════════════════════════════════════════════════════════ -->
  <!-- DESKTOP: Sticky right panel (hidden on mobile, shown on lg+)     -->
  <!-- ═══════════════════════════════════════════════════════════════════ -->
  <div class="hidden lg:block w-[300px] shrink-0" data-testid="live-preview-desktop">
    <div class="sticky top-4">
      <!-- Panel header -->
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          Live-Vorschau
        </h3>
        <span class="text-[10px] text-gray-400 dark:text-gray-500">Echtzeit</span>
      </div>

      <!-- Platform toggle pills -->
      <div class="flex items-center gap-1 mb-3 p-1 bg-gray-100 dark:bg-gray-800 rounded-xl" data-testid="live-preview-platform-toggle">
        <button
          v-for="pId in platforms"
          :key="pId"
          @click="selectPlatform(pId)"
          class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium transition-all"
          :class="activePlatform === pId
            ? 'bg-white dark:bg-gray-700 text-[#3B7AB1] shadow-sm'
            : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
          :data-testid="'live-preview-toggle-' + pId"
        >
          <span>{{ platformData[pId]?.icon }}</span>
          <span>{{ platformData[pId]?.label }}</span>
        </button>
      </div>

      <!-- Phone mockup frame -->
      <div class="flex justify-center">
        <div
          class="relative bg-black rounded-[2.5rem] p-2 shadow-2xl ring-1 ring-gray-800"
          :class="isPortrait ? 'w-[260px]' : 'w-[280px]'"
          data-testid="live-preview-phone-frame"
        >
          <!-- Phone notch -->
          <div class="absolute top-0 left-1/2 -translate-x-1/2 w-24 h-5 bg-black rounded-b-2xl z-10"></div>

          <!-- Phone screen -->
          <div
            class="relative bg-white dark:bg-[#1A1A2E] rounded-[2rem] overflow-hidden"
            :class="{
              'aspect-square': isSquare,
              'aspect-[9/16]': isPortrait,
            }"
          >
            <!-- ═══ EMPTY STATE ═══ -->
            <div v-if="!hasContent" class="absolute inset-0 flex flex-col items-center justify-center p-6 text-center">
              <div class="text-3xl mb-3 opacity-40">
                {{ activePlatform === 'tiktok' ? '\uD83C\uDFB5' : '\uD83D\uDCF7' }}
              </div>
              <p class="text-xs text-gray-400 dark:text-gray-500 leading-relaxed">
                Waehle Kategorie, Template &amp; erstelle Inhalte — die Vorschau aktualisiert sich in Echtzeit.
              </p>
            </div>

            <!-- ═══ INSTAGRAM FEED MOCKUP ═══ -->
            <div v-else-if="activePlatform === 'instagram_feed'" class="absolute inset-0 flex flex-col" data-testid="preview-instagram-feed">
              <!-- IG Header -->
              <div class="flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800">
                <div class="w-7 h-7 rounded-full bg-gradient-to-br from-[#3B7AB1] to-[#2E6A9E] flex items-center justify-center">
                  <span class="text-white text-[8px] font-bold">T</span>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-[10px] font-semibold text-gray-900 dark:text-white truncate">treff_sprachreisen</div>
                  <div class="text-[8px] text-gray-400">{{ country?.label || 'Gesponsert' }}</div>
                </div>
                <div class="text-gray-400 text-xs">&#8943;</div>
              </div>

              <!-- IG Image area (slide content) -->
              <div class="flex-1 relative bg-gradient-to-br from-[#1A1A2E] to-[#2a2a4e] overflow-hidden">
                <!-- Background image -->
                <img
                  v-if="backgroundImage"
                  :src="backgroundImage"
                  class="absolute inset-0 w-full h-full object-cover opacity-30"
                  alt=""
                />

                <div v-if="resolvedSlide" class="absolute inset-0 p-4 flex flex-col justify-between z-10">
                  <!-- TREFF badge + Episode -->
                  <div class="flex items-center gap-1.5">
                    <div class="bg-[#3B7AB1] rounded px-2 py-0.5">
                      <span class="text-white text-[8px] font-bold">TREFF</span>
                    </div>
                    <span v-if="episodeNumber" class="bg-[#FDD000] text-[#1A1A2E] px-1.5 py-0.5 rounded-full text-[7px] font-bold">E{{ episodeNumber }}</span>
                  </div>

                  <!-- Previously text -->
                  <div v-if="episodePreviouslyText && props.currentSlideIndex === 0" class="mt-1 px-1.5 py-0.5 bg-white/10 rounded text-gray-300 text-[7px] italic leading-tight line-clamp-2">
                    {{ episodePreviouslyText }}
                  </div>

                  <!-- Content -->
                  <div class="flex-1 flex flex-col justify-center py-2">
                    <h4 class="text-[#3B7AB1] text-sm font-extrabold leading-tight mb-1 line-clamp-3">
                      {{ resolvedSlide.headline || '' }}
                    </h4>
                    <p v-if="resolvedSlide.subheadline" class="text-[#FDD000] text-[9px] font-semibold mb-1 line-clamp-2">
                      {{ resolvedSlide.subheadline }}
                    </p>
                    <p v-if="resolvedSlide.body_text" class="text-gray-300 text-[8px] leading-relaxed line-clamp-4">
                      {{ resolvedSlide.body_text }}
                    </p>
                    <ul v-if="resolvedSlide.bullet_points?.length" class="mt-1 space-y-0.5">
                      <li
                        v-for="(bp, bpIdx) in (Array.isArray(resolvedSlide.bullet_points) ? resolvedSlide.bullet_points : []).slice(0, 4)"
                        :key="bpIdx"
                        class="text-gray-300 text-[8px] flex items-start gap-1"
                      >
                        <span class="text-[#FDD000] mt-0.5 text-[6px]">&#9679;</span>
                        <span class="line-clamp-1">{{ bp }}</span>
                      </li>
                    </ul>
                  </div>

                  <!-- Cliffhanger -->
                  <div v-if="episodeCliffhangerText && props.currentSlideIndex === dSlides.length - 1" class="mb-1 px-1.5 py-0.5 bg-white/10 rounded text-[#FDD000] text-[7px] font-semibold italic line-clamp-2">
                    {{ episodeCliffhangerText }}
                  </div>

                  <!-- CTA -->
                  <div v-if="resolvedSlide.cta_text || resolvedCta" class="mt-1">
                    <div class="inline-block bg-[#FDD000] text-[#1A1A2E] px-3 py-1 rounded-full font-bold text-[8px]">
                      {{ resolvedSlide.cta_text || resolvedCta }}
                    </div>
                  </div>
                </div>

                <!-- Slide dots inside image -->
                <div v-if="slideCount > 1" class="absolute bottom-2 left-0 right-0 flex justify-center gap-1 z-20">
                  <button
                    v-for="(s, sIdx) in dSlides"
                    :key="sIdx"
                    @click="goToSlide(sIdx)"
                    class="w-1.5 h-1.5 rounded-full transition-colors"
                    :class="sIdx === props.currentSlideIndex ? 'bg-[#3B7AB1]' : 'bg-white/40'"
                  ></button>
                </div>
              </div>

              <!-- IG Action bar -->
              <div class="px-3 py-1.5 bg-white dark:bg-gray-900 border-t border-gray-100 dark:border-gray-800">
                <div class="flex items-center gap-3 text-gray-700 dark:text-gray-300 text-sm">
                  <span>&#9825;</span>
                  <span>&#128172;</span>
                  <span>&#10148;</span>
                  <span class="ml-auto">&#9734;</span>
                </div>
              </div>

              <!-- IG Caption preview -->
              <div class="px-3 py-1.5 bg-white dark:bg-gray-900 text-[8px] max-h-[50px] overflow-hidden">
                <span class="font-semibold text-gray-900 dark:text-white">treff_sprachreisen</span>
                <span class="text-gray-600 dark:text-gray-400 ml-1">{{ resolvedCaption ? resolvedCaption.slice(0, 80) : '' }}{{ resolvedCaption?.length > 80 ? '...' : '' }}</span>
                <div v-if="resolvedHashtags" class="text-blue-500 dark:text-blue-400 mt-0.5 line-clamp-1">{{ resolvedHashtags.slice(0, 60) }}</div>
              </div>
            </div>

            <!-- ═══ INSTAGRAM STORY MOCKUP ═══ -->
            <div v-else-if="activePlatform === 'instagram_story'" class="absolute inset-0 flex flex-col" data-testid="preview-instagram-story">
              <!-- Story progress bars -->
              <div class="absolute top-2 left-3 right-3 flex gap-1 z-20">
                <div
                  v-for="(s, sIdx) in (dSlides.length > 0 ? dSlides : [{}])"
                  :key="sIdx"
                  class="flex-1 h-0.5 rounded-full overflow-hidden"
                  :class="sIdx <= props.currentSlideIndex ? 'bg-white' : 'bg-white/30'"
                ></div>
              </div>

              <!-- Story header -->
              <div class="absolute top-4 left-3 right-3 flex items-center gap-2 z-20">
                <div class="w-6 h-6 rounded-full bg-gradient-to-br from-[#3B7AB1] to-[#2E6A9E] ring-2 ring-[#FDD000] flex items-center justify-center">
                  <span class="text-white text-[7px] font-bold">T</span>
                </div>
                <span class="text-white text-[9px] font-semibold drop-shadow">treff_sprachreisen</span>
                <span class="text-white/60 text-[8px] drop-shadow">{{ Math.floor(Math.random() * 23) + 1 }}h</span>
                <span class="ml-auto text-white/80 text-xs drop-shadow">&#10005;</span>
              </div>

              <!-- Story content area -->
              <div class="absolute inset-0 bg-gradient-to-br from-[#1A1A2E] to-[#2a2a4e]">
                <img
                  v-if="backgroundImage"
                  :src="backgroundImage"
                  class="absolute inset-0 w-full h-full object-cover opacity-30"
                  alt=""
                />
                <div v-if="resolvedSlide" class="absolute inset-0 flex flex-col justify-center p-5 pt-14 z-10">
                  <!-- Episode badge -->
                  <div v-if="episodeNumber" class="mb-2">
                    <span class="bg-[#FDD000] text-[#1A1A2E] px-2 py-0.5 rounded-full text-[8px] font-bold">Episode {{ episodeNumber }}</span>
                  </div>

                  <!-- Previously -->
                  <div v-if="episodePreviouslyText && props.currentSlideIndex === 0" class="mb-2 px-2 py-1 bg-white/10 rounded text-gray-300 text-[7px] italic leading-tight line-clamp-2">
                    {{ episodePreviouslyText }}
                  </div>

                  <h4 class="text-white text-base font-extrabold leading-tight mb-2 drop-shadow line-clamp-3">
                    {{ resolvedSlide.headline || '' }}
                  </h4>
                  <p v-if="resolvedSlide.subheadline" class="text-[#FDD000] text-[10px] font-semibold mb-2 drop-shadow line-clamp-2">
                    {{ resolvedSlide.subheadline }}
                  </p>
                  <p v-if="resolvedSlide.body_text" class="text-white/80 text-[9px] leading-relaxed line-clamp-5 drop-shadow">
                    {{ resolvedSlide.body_text }}
                  </p>
                  <ul v-if="resolvedSlide.bullet_points?.length" class="mt-2 space-y-1">
                    <li
                      v-for="(bp, bpIdx) in (Array.isArray(resolvedSlide.bullet_points) ? resolvedSlide.bullet_points : []).slice(0, 4)"
                      :key="bpIdx"
                      class="text-white/80 text-[8px] flex items-start gap-1 drop-shadow"
                    >
                      <span class="text-[#FDD000] mt-0.5 text-[6px]">&#9679;</span>
                      <span>{{ bp }}</span>
                    </li>
                  </ul>

                  <!-- Cliffhanger -->
                  <div v-if="episodeCliffhangerText && props.currentSlideIndex === dSlides.length - 1" class="mt-3 px-2 py-1 bg-white/10 rounded text-[#FDD000] text-[8px] font-semibold italic line-clamp-2">
                    {{ episodeCliffhangerText }}
                  </div>

                  <!-- CTA button -->
                  <div v-if="resolvedSlide.cta_text || resolvedCta" class="mt-3">
                    <div class="inline-block bg-[#FDD000] text-[#1A1A2E] px-4 py-1.5 rounded-full font-bold text-[9px] shadow-lg">
                      {{ resolvedSlide.cta_text || resolvedCta }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- Story bottom: reply bar + swipe-up hint -->
              <div class="absolute bottom-3 left-3 right-3 z-20">
                <div v-if="resolvedSlide?.cta_text || resolvedCta" class="text-center mb-2">
                  <div class="inline-flex items-center gap-1 text-white/70 text-[8px] animate-bounce">
                    <span>&#8679;</span>
                    <span>Mehr erfahren</span>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <div class="flex-1 bg-white/10 rounded-full px-3 py-1.5 text-[8px] text-white/40 border border-white/20">Nachricht senden...</div>
                  <span class="text-white/60 text-[10px]">&#10084;</span>
                  <span class="text-white/60 text-[10px]">&#10148;</span>
                </div>
              </div>
            </div>

            <!-- ═══ TIKTOK MOCKUP ═══ -->
            <div v-else-if="activePlatform === 'tiktok'" class="absolute inset-0 flex flex-col" data-testid="preview-tiktok">
              <!-- TikTok content area -->
              <div class="absolute inset-0 bg-gradient-to-br from-[#1A1A2E] to-[#010101]">
                <img
                  v-if="backgroundImage"
                  :src="backgroundImage"
                  class="absolute inset-0 w-full h-full object-cover opacity-30"
                  alt=""
                />
                <div v-if="resolvedSlide" class="absolute inset-0 flex flex-col justify-end p-4 pb-16 z-10">
                  <!-- Episode badge -->
                  <div v-if="episodeNumber" class="mb-2">
                    <span class="bg-[#FDD000] text-[#1A1A2E] px-2 py-0.5 rounded-full text-[8px] font-bold">Ep. {{ episodeNumber }}</span>
                  </div>

                  <h4 class="text-white text-sm font-extrabold leading-tight mb-1 drop-shadow line-clamp-2">
                    {{ resolvedSlide.headline || '' }}
                  </h4>
                  <p v-if="resolvedSlide.subheadline" class="text-[#FDD000] text-[9px] font-semibold mb-1 drop-shadow line-clamp-1">
                    {{ resolvedSlide.subheadline }}
                  </p>
                  <p v-if="resolvedSlide.body_text" class="text-white/80 text-[8px] leading-relaxed line-clamp-3 drop-shadow">
                    {{ resolvedSlide.body_text }}
                  </p>

                  <!-- Caption + hashtags at bottom -->
                  <div class="mt-2">
                    <p class="text-white text-[8px] leading-relaxed line-clamp-2">
                      <span class="font-semibold">@treff_sprachreisen</span>
                      {{ resolvedCaption ? ' ' + resolvedCaption.slice(0, 60) : '' }}
                    </p>
                    <p v-if="resolvedHashtags" class="text-white/70 text-[7px] mt-0.5 line-clamp-1">{{ resolvedHashtags.slice(0, 50) }}</p>
                  </div>

                  <!-- Music ticker -->
                  <div class="mt-1.5 flex items-center gap-1.5">
                    <span class="text-white/60 text-[8px]">&#9834;</span>
                    <div class="overflow-hidden flex-1">
                      <p class="text-white/50 text-[7px] whitespace-nowrap animate-marquee">Original Sound - TREFF Sprachreisen</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- TikTok right sidebar icons -->
              <div class="absolute right-2 bottom-20 flex flex-col items-center gap-3 z-20">
                <!-- Profile -->
                <div class="relative">
                  <div class="w-8 h-8 rounded-full bg-gradient-to-br from-[#3B7AB1] to-[#2E6A9E] ring-2 ring-white flex items-center justify-center">
                    <span class="text-white text-[7px] font-bold">T</span>
                  </div>
                  <div class="absolute -bottom-1 left-1/2 -translate-x-1/2 w-3.5 h-3.5 bg-[#FE2C55] rounded-full flex items-center justify-center">
                    <span class="text-white text-[6px]">+</span>
                  </div>
                </div>
                <!-- Heart -->
                <div class="flex flex-col items-center">
                  <span class="text-white text-sm">&#9825;</span>
                  <span class="text-white text-[7px]">{{ Math.floor(Math.random() * 900) + 100 }}</span>
                </div>
                <!-- Comment -->
                <div class="flex flex-col items-center">
                  <span class="text-white text-sm">&#128172;</span>
                  <span class="text-white text-[7px]">{{ Math.floor(Math.random() * 50) + 5 }}</span>
                </div>
                <!-- Share -->
                <div class="flex flex-col items-center">
                  <span class="text-white text-sm">&#10148;</span>
                  <span class="text-white text-[7px]">{{ Math.floor(Math.random() * 20) + 1 }}</span>
                </div>
                <!-- Music disc -->
                <div class="w-7 h-7 rounded-full bg-gray-800 border-2 border-gray-600 flex items-center justify-center animate-spin-slow">
                  <div class="w-2.5 h-2.5 rounded-full bg-gradient-to-br from-[#3B7AB1] to-[#FDD000]"></div>
                </div>
              </div>

              <!-- TikTok bottom nav -->
              <div class="absolute bottom-0 left-0 right-0 bg-black/90 z-20 py-1 px-4 flex items-center justify-around text-white/50 text-[8px]">
                <span>Home</span>
                <span>Entdecken</span>
                <div class="w-7 h-5 bg-white rounded-sm flex items-center justify-center -mt-1">
                  <span class="text-black text-[10px] font-bold">+</span>
                </div>
                <span>Posteingang</span>
                <span>Profil</span>
              </div>
            </div>
          </div>

          <!-- Phone home indicator -->
          <div class="absolute bottom-1 left-1/2 -translate-x-1/2 w-24 h-1 bg-gray-600 rounded-full"></div>
        </div>
      </div>

      <!-- Slide navigation (below phone) -->
      <div v-if="slideCount > 1" class="flex items-center justify-center gap-3 mt-3">
        <button
          @click="prevSlide"
          :disabled="props.currentSlideIndex === 0"
          class="px-2 py-1 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-30 transition-colors"
          data-testid="live-preview-prev-slide"
        >&#8592;</button>
        <span class="text-[10px] text-gray-500 dark:text-gray-400">{{ props.currentSlideIndex + 1 }} / {{ slideCount }}</span>
        <button
          @click="nextSlide"
          :disabled="props.currentSlideIndex === slideCount - 1"
          class="px-2 py-1 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-30 transition-colors"
          data-testid="live-preview-next-slide"
        >&#8594;</button>
      </div>

      <!-- Platform info badge -->
      <div class="mt-2 text-center text-[10px] text-gray-400 dark:text-gray-500">
        {{ platformData[activePlatform]?.icon }} {{ platformData[activePlatform]?.label }}
        ({{ platformData[activePlatform]?.format }})
        <span v-if="categoryLabel"> &middot; {{ categoryLabel }}</span>
        <span v-if="country"> &middot; {{ country.flag }} {{ country.label }}</span>
      </div>
    </div>
  </div>

  <!-- ═══════════════════════════════════════════════════════════════════ -->
  <!-- MOBILE: Floating toggle button + Bottom sheet (shown on < lg)    -->
  <!-- ═══════════════════════════════════════════════════════════════════ -->

  <!-- Floating preview button (mobile) -->
  <button
    class="lg:hidden fixed bottom-20 right-4 z-40 w-12 h-12 rounded-full bg-[#3B7AB1] text-white shadow-lg flex items-center justify-center hover:bg-[#2E6A9E] transition-colors"
    :class="showMobilePreview ? 'ring-4 ring-[#3B7AB1]/30' : ''"
    @click="toggleMobilePreview"
    data-testid="live-preview-mobile-toggle"
    aria-label="Live-Vorschau anzeigen"
  >
    <span class="text-lg">&#128065;</span>
  </button>

  <!-- Mobile bottom sheet -->
  <Teleport to="body">
    <Transition name="slide-up">
      <div
        v-if="showMobilePreview"
        class="lg:hidden fixed inset-0 z-50"
        data-testid="live-preview-mobile-sheet"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="showMobilePreview = false"></div>

        <!-- Sheet -->
        <div class="absolute bottom-0 left-0 right-0 bg-white dark:bg-gray-900 rounded-t-2xl shadow-2xl max-h-[85vh] overflow-auto">
          <!-- Handle -->
          <div class="flex justify-center pt-2 pb-1">
            <div class="w-10 h-1 rounded-full bg-gray-300 dark:bg-gray-700"></div>
          </div>

          <!-- Header -->
          <div class="flex items-center justify-between px-4 pb-3">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              Live-Vorschau
            </h3>
            <button
              @click="showMobilePreview = false"
              class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >&#10005;</button>
          </div>

          <!-- Platform pills (mobile) -->
          <div class="flex items-center gap-1 mx-4 mb-3 p-1 bg-gray-100 dark:bg-gray-800 rounded-xl">
            <button
              v-for="pId in platforms"
              :key="pId"
              @click="selectPlatform(pId)"
              class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium transition-all flex-1 justify-center"
              :class="activePlatform === pId
                ? 'bg-white dark:bg-gray-700 text-[#3B7AB1] shadow-sm'
                : 'text-gray-500 dark:text-gray-400'"
            >
              <span>{{ platformData[pId]?.icon }}</span>
              <span>{{ platformData[pId]?.label }}</span>
            </button>
          </div>

          <!-- Phone frame (mobile - centered, smaller) -->
          <div class="flex justify-center pb-6 px-4">
            <div
              class="relative bg-black rounded-[2rem] p-1.5 shadow-2xl ring-1 ring-gray-800"
              :class="isPortrait ? 'w-[220px]' : 'w-[240px]'"
            >
              <div class="absolute top-0 left-1/2 -translate-x-1/2 w-20 h-4 bg-black rounded-b-xl z-10"></div>
              <div
                class="relative bg-white dark:bg-[#1A1A2E] rounded-[1.75rem] overflow-hidden"
                :class="{
                  'aspect-square': isSquare,
                  'aspect-[9/16]': isPortrait,
                }"
              >
                <!-- Re-use same content rendering (simplified for mobile) -->
                <div v-if="!hasContent" class="absolute inset-0 flex flex-col items-center justify-center p-4 text-center">
                  <p class="text-[10px] text-gray-400">Noch kein Inhalt</p>
                </div>

                <!-- IG Feed mobile -->
                <div v-else-if="activePlatform === 'instagram_feed'" class="absolute inset-0 flex flex-col">
                  <div class="flex items-center gap-1.5 px-2 py-1.5 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800">
                    <div class="w-5 h-5 rounded-full bg-[#3B7AB1] flex items-center justify-center">
                      <span class="text-white text-[6px] font-bold">T</span>
                    </div>
                    <span class="text-[8px] font-semibold text-gray-900 dark:text-white">treff_sprachreisen</span>
                  </div>
                  <div class="flex-1 relative bg-gradient-to-br from-[#1A1A2E] to-[#2a2a4e]">
                    <img v-if="backgroundImage" :src="backgroundImage" class="absolute inset-0 w-full h-full object-cover opacity-30" alt="" />
                    <div v-if="resolvedSlide" class="absolute inset-0 p-3 flex flex-col justify-center z-10">
                      <h4 class="text-[#3B7AB1] text-[11px] font-extrabold leading-tight mb-1 line-clamp-2">{{ resolvedSlide.headline }}</h4>
                      <p v-if="resolvedSlide.body_text" class="text-gray-300 text-[7px] line-clamp-3">{{ resolvedSlide.body_text }}</p>
                    </div>
                  </div>
                  <div class="px-2 py-1 bg-white dark:bg-gray-900 text-[7px]">
                    <span class="font-semibold text-gray-900 dark:text-white">treff_sprachreisen</span>
                    <span class="text-gray-500 ml-1">{{ resolvedCaption?.slice(0, 40) }}...</span>
                  </div>
                </div>

                <!-- IG Story mobile -->
                <div v-else-if="activePlatform === 'instagram_story'" class="absolute inset-0 bg-gradient-to-br from-[#1A1A2E] to-[#2a2a4e]">
                  <img v-if="backgroundImage" :src="backgroundImage" class="absolute inset-0 w-full h-full object-cover opacity-30" alt="" />
                  <div class="absolute top-2 left-2 right-2 flex gap-0.5 z-20">
                    <div v-for="(s, i) in (dSlides.length > 0 ? dSlides : [{}])" :key="i" class="flex-1 h-0.5 rounded-full" :class="i <= props.currentSlideIndex ? 'bg-white' : 'bg-white/30'"></div>
                  </div>
                  <div v-if="resolvedSlide" class="absolute inset-0 flex flex-col justify-center p-4 pt-8 z-10">
                    <h4 class="text-white text-[11px] font-extrabold leading-tight mb-1 drop-shadow line-clamp-2">{{ resolvedSlide.headline }}</h4>
                    <p v-if="resolvedSlide.body_text" class="text-white/70 text-[7px] line-clamp-3 drop-shadow">{{ resolvedSlide.body_text }}</p>
                  </div>
                </div>

                <!-- TikTok mobile -->
                <div v-else-if="activePlatform === 'tiktok'" class="absolute inset-0 bg-gradient-to-br from-[#1A1A2E] to-[#010101]">
                  <img v-if="backgroundImage" :src="backgroundImage" class="absolute inset-0 w-full h-full object-cover opacity-30" alt="" />
                  <div v-if="resolvedSlide" class="absolute inset-0 flex flex-col justify-end p-3 pb-10 z-10">
                    <h4 class="text-white text-[10px] font-extrabold leading-tight mb-1 drop-shadow line-clamp-2">{{ resolvedSlide.headline }}</h4>
                    <p class="text-white/70 text-[7px] line-clamp-2">@treff_sprachreisen {{ resolvedCaption?.slice(0, 40) }}</p>
                  </div>
                  <div class="absolute right-1.5 bottom-14 flex flex-col items-center gap-2 z-20">
                    <div class="w-6 h-6 rounded-full bg-[#3B7AB1] ring-1 ring-white flex items-center justify-center">
                      <span class="text-white text-[5px] font-bold">T</span>
                    </div>
                    <span class="text-white text-[10px]">&#9825;</span>
                    <span class="text-white text-[10px]">&#128172;</span>
                    <span class="text-white text-[10px]">&#10148;</span>
                  </div>
                </div>
              </div>
              <div class="absolute bottom-0.5 left-1/2 -translate-x-1/2 w-20 h-0.5 bg-gray-600 rounded-full"></div>
            </div>
          </div>

          <!-- Slide nav (mobile) -->
          <div v-if="slideCount > 1" class="flex items-center justify-center gap-3 pb-4">
            <button @click="prevSlide" :disabled="props.currentSlideIndex === 0" class="px-2 py-1 text-xs rounded border border-gray-300 dark:border-gray-600 disabled:opacity-30">&#8592;</button>
            <span class="text-[10px] text-gray-500">{{ props.currentSlideIndex + 1 }} / {{ slideCount }}</span>
            <button @click="nextSlide" :disabled="props.currentSlideIndex === slideCount - 1" class="px-2 py-1 text-xs rounded border border-gray-300 dark:border-gray-600 disabled:opacity-30">&#8594;</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* Slide-up transition for mobile bottom sheet */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
}
.slide-up-enter-from > div:last-child,
.slide-up-leave-to > div:last-child {
  transform: translateY(100%);
}

/* Slow spin for TikTok music disc */
@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin-slow {
  animation: spin-slow 4s linear infinite;
}

/* Marquee animation for TikTok music ticker */
@keyframes marquee {
  0% { transform: translateX(0); }
  100% { transform: translateX(-100%); }
}
.animate-marquee {
  animation: marquee 8s linear infinite;
}
</style>
