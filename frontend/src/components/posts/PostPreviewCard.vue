<script setup>
/**
 * PostPreviewCard.vue — Instagram Feed Mockup Preview Card
 *
 * Realistic Instagram-style feed post mockup showing how a post will appear
 * on Instagram. Includes:
 *  - Profile header (TREFF avatar + @treff_sprachreisen)
 *  - Image area (4:5 aspect ratio for Feed)
 *  - Like/Comment/Share/Save action icons
 *  - Caption preview (truncated)
 *  - Hashtag display
 *  - Carousel dots for multi-slide posts
 *  - Video thumbnail with play button overlay
 *  - Country accent coloring (based on destination country)
 *  - Status badge overlay (Draft, Scheduled, Published)
 *
 * @see PostPreviewCardTikTok.vue — TikTok mockup variant
 * @see PostPreviewGrid.vue — Grid layout for multiple previews
 */
import { computed } from 'vue'

const props = defineProps({
  /** Post object with title, caption, platform, country, status, slides, etc. */
  post: { type: Object, required: true },
  /** Target platform: 'instagram' (default) */
  platform: { type: String, default: 'instagram' },
  /** Card size variant: 'sm' | 'md' | 'lg' */
  size: { type: String, default: 'md', validator: v => ['sm', 'md', 'lg'].includes(v) },
  /** Whether to show the caption preview below the image */
  showCaption: { type: Boolean, default: true },
  /** Current slide index for carousel preview */
  currentSlideIndex: { type: Number, default: 0 },
})

const emit = defineEmits(['click', 'slide-change'])

// ── Country accent colors (matching tailwind config country palettes) ──
const countryAccents = {
  usa:       { border: '#B22234', bg: 'rgba(178,34,52,0.1)', text: '#B22234', label: 'USA', flag: '\uD83C\uDDFA\uD83C\uDDF8' },
  kanada:    { border: '#FF0000', bg: 'rgba(255,0,0,0.1)', text: '#FF0000', label: 'Kanada', flag: '\uD83C\uDDE8\uD83C\uDDE6' },
  canada:    { border: '#FF0000', bg: 'rgba(255,0,0,0.1)', text: '#FF0000', label: 'Kanada', flag: '\uD83C\uDDE8\uD83C\uDDE6' },
  australien:{ border: '#CC7722', bg: 'rgba(204,119,34,0.1)', text: '#CC7722', label: 'Australien', flag: '\uD83C\uDDE6\uD83C\uDDFA' },
  australia: { border: '#CC7722', bg: 'rgba(204,119,34,0.1)', text: '#CC7722', label: 'Australien', flag: '\uD83C\uDDE6\uD83C\uDDFA' },
  neuseeland:{ border: '#1B4D3E', bg: 'rgba(27,77,62,0.1)', text: '#1B4D3E', label: 'Neuseeland', flag: '\uD83C\uDDF3\uD83C\uDDFF' },
  nz:        { border: '#1B4D3E', bg: 'rgba(27,77,62,0.1)', text: '#1B4D3E', label: 'Neuseeland', flag: '\uD83C\uDDF3\uD83C\uDDFF' },
  irland:    { border: '#169B62', bg: 'rgba(22,155,98,0.1)', text: '#169B62', label: 'Irland', flag: '\uD83C\uDDEE\uD83C\uDDEA' },
  ireland:   { border: '#169B62', bg: 'rgba(22,155,98,0.1)', text: '#169B62', label: 'Irland', flag: '\uD83C\uDDEE\uD83C\uDDEA' },
}

// ── Status badge config ──
const statusConfig = {
  draft:     { label: 'Entwurf', bg: 'bg-gray-500', icon: '\u270F\uFE0F' },
  scheduled: { label: 'Geplant', bg: 'bg-blue-500', icon: '\uD83D\uDD52' },
  reminded:  { label: 'Erinnert', bg: 'bg-yellow-500', icon: '\uD83D\uDD14' },
  exported:  { label: 'Exportiert', bg: 'bg-purple-500', icon: '\uD83D\uDCE4' },
  posted:    { label: 'Ver\u00f6ffentlicht', bg: 'bg-green-500', icon: '\u2705' },
  published: { label: 'Ver\u00f6ffentlicht', bg: 'bg-green-500', icon: '\u2705' },
}

// ── Computed ──
const country = computed(() => {
  const c = props.post?.country?.toLowerCase?.() || ''
  return countryAccents[c] || null
})

const accentBorderColor = computed(() => country.value?.border || '#3B7AB1')

const status = computed(() => {
  const s = props.post?.status?.toLowerCase?.() || 'draft'
  return statusConfig[s] || statusConfig.draft
})

const slides = computed(() => {
  if (Array.isArray(props.post?.slides)) return props.post.slides
  if (typeof props.post?.slide_data === 'string') {
    try { return JSON.parse(props.post.slide_data) } catch { return [] }
  }
  if (Array.isArray(props.post?.slide_data)) return props.post.slide_data
  return []
})

const currentSlide = computed(() => slides.value[props.currentSlideIndex] || null)

const slideCount = computed(() => slides.value.length)

const isVideo = computed(() => {
  const slide = currentSlide.value
  if (!slide) return false
  return slide.type === 'video' || slide.media_type === 'video' || (slide.url && /\.(mp4|mov|webm)$/i.test(slide.url))
})

const imageUrl = computed(() => {
  const slide = currentSlide.value
  if (!slide) return props.post?.thumbnail || props.post?.image_url || ''
  return slide.image_url || slide.url || slide.thumbnail || props.post?.thumbnail || ''
})

const caption = computed(() => {
  return props.post?.caption_instagram || props.post?.caption || ''
})

const hashtags = computed(() => {
  return props.post?.hashtags_instagram || props.post?.hashtags || ''
})

const title = computed(() => {
  return props.post?.title || ''
})

// ── Size classes ──
const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm': return { card: 'w-[200px]', text: 'text-[8px]', title: 'text-[9px]', avatar: 'w-5 h-5', avatarText: 'text-[5px]', iconSize: 'text-xs', captionLines: 1 }
    case 'lg': return { card: 'w-[400px]', text: 'text-xs', title: 'text-sm', avatar: 'w-9 h-9', avatarText: 'text-[10px]', iconSize: 'text-lg', captionLines: 3 }
    default:   return { card: 'w-[300px]', text: 'text-[10px]', title: 'text-[11px]', avatar: 'w-7 h-7', avatarText: 'text-[7px]', iconSize: 'text-sm', captionLines: 2 }
  }
})

// ── Slide navigation ──
function goToSlide(idx) {
  emit('slide-change', idx)
}
</script>

<template>
  <div
    class="relative rounded-xl overflow-hidden bg-white dark:bg-gray-900 shadow-card hover:shadow-card-hover transition-shadow duration-200 cursor-pointer"
    :class="sizeClasses.card"
    :style="{ borderLeft: `3px solid ${accentBorderColor}` }"
    @click="emit('click', post)"
    data-testid="post-preview-card-instagram"
  >
    <!-- Status badge -->
    <div
      class="absolute top-2 right-2 z-10 px-2 py-0.5 rounded-full text-white font-semibold flex items-center gap-1"
      :class="[status.bg, size === 'sm' ? 'text-[7px]' : 'text-[9px]']"
      data-testid="post-preview-status-badge"
    >
      <span>{{ status.icon }}</span>
      <span>{{ status.label }}</span>
    </div>

    <!-- Country accent badge (top-left) -->
    <div
      v-if="country"
      class="absolute top-2 left-2 z-10 px-1.5 py-0.5 rounded-full font-semibold flex items-center gap-1"
      :class="size === 'sm' ? 'text-[7px]' : 'text-[9px]'"
      :style="{ backgroundColor: country.bg, color: country.text, border: `1px solid ${country.border}` }"
      data-testid="post-preview-country-badge"
    >
      <span>{{ country.flag }}</span>
      <span>{{ country.label }}</span>
    </div>

    <!-- IG Profile header -->
    <div class="flex items-center gap-2 px-3 py-2 border-b border-gray-100 dark:border-gray-800">
      <div
        :class="sizeClasses.avatar"
        class="rounded-full bg-gradient-to-br from-[#3B7AB1] to-[#2E6A9E] flex items-center justify-center flex-shrink-0"
      >
        <span class="text-white font-bold" :class="sizeClasses.avatarText">T</span>
      </div>
      <div class="flex-1 min-w-0">
        <div class="font-semibold text-gray-900 dark:text-white truncate" :class="sizeClasses.text">treff_sprachreisen</div>
        <div class="text-gray-400" :class="size === 'sm' ? 'text-[6px]' : 'text-[8px]'">
          {{ country ? country.flag + ' ' + country.label : 'Gesponsert' }}
        </div>
      </div>
      <div class="text-gray-400" :class="sizeClasses.iconSize">&#8943;</div>
    </div>

    <!-- Image area (4:5 aspect ratio for Feed) -->
    <div class="relative aspect-[4/5] bg-gradient-to-br from-[#1A1A2E] to-[#2a2a4e] overflow-hidden">
      <!-- Background image -->
      <img
        v-if="imageUrl"
        :src="imageUrl"
        :alt="title || 'Post preview'"
        class="absolute inset-0 w-full h-full object-cover"
        loading="lazy"
      />

      <!-- Fallback when no image -->
      <div v-else class="absolute inset-0 flex flex-col items-center justify-center p-4 text-center">
        <div class="text-3xl mb-2 opacity-40">&#x1F4F7;</div>
        <p v-if="title" class="text-white/70 font-semibold line-clamp-3" :class="sizeClasses.title">{{ title }}</p>
        <p v-else class="text-white/40" :class="sizeClasses.text">Kein Bild</p>
      </div>

      <!-- Video play button overlay -->
      <div
        v-if="isVideo"
        class="absolute inset-0 flex items-center justify-center z-10"
        data-testid="post-preview-video-overlay"
      >
        <div class="w-14 h-14 rounded-full bg-black/50 backdrop-blur-sm flex items-center justify-center border-2 border-white/60 hover:bg-black/70 transition-colors">
          <svg class="w-6 h-6 text-white ml-1" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </div>
      </div>

      <!-- Carousel dots for multi-slide posts -->
      <div
        v-if="slideCount > 1"
        class="absolute bottom-2 left-0 right-0 flex justify-center gap-1 z-20"
        data-testid="post-preview-carousel-dots"
      >
        <button
          v-for="(s, sIdx) in slides"
          :key="sIdx"
          @click.stop="goToSlide(sIdx)"
          class="rounded-full transition-all"
          :class="[
            sIdx === currentSlideIndex
              ? 'bg-[#3B7AB1] w-2 h-2'
              : 'bg-white/50 hover:bg-white/70 w-1.5 h-1.5'
          ]"
          :aria-label="'Slide ' + (sIdx + 1)"
        ></button>
      </div>

      <!-- Slide counter badge -->
      <div
        v-if="slideCount > 1"
        class="absolute top-2 right-2 z-10 bg-black/60 text-white rounded-full px-2 py-0.5"
        :class="size === 'sm' ? 'text-[7px]' : 'text-[9px]'"
      >
        {{ currentSlideIndex + 1 }}/{{ slideCount }}
      </div>
    </div>

    <!-- IG Action bar (Like, Comment, Share, Save) -->
    <div class="px-3 py-1.5 border-t border-gray-100 dark:border-gray-800">
      <div class="flex items-center gap-3 text-gray-700 dark:text-gray-300" :class="sizeClasses.iconSize">
        <span class="hover:text-red-500 transition-colors cursor-pointer" title="Gefaellt mir">&#9825;</span>
        <span class="hover:text-blue-500 transition-colors cursor-pointer" title="Kommentieren">&#128172;</span>
        <span class="hover:text-green-500 transition-colors cursor-pointer" title="Teilen">&#10148;</span>
        <span class="ml-auto hover:text-yellow-500 transition-colors cursor-pointer" title="Speichern">&#9734;</span>
      </div>
    </div>

    <!-- IG Caption preview -->
    <div
      v-if="showCaption"
      class="px-3 py-1.5 border-t border-gray-50 dark:border-gray-800"
      :class="sizeClasses.text"
    >
      <div class="max-h-[60px] overflow-hidden">
        <span class="font-semibold text-gray-900 dark:text-white">treff_sprachreisen</span>
        <span class="text-gray-600 dark:text-gray-400 ml-1">
          {{ caption ? caption.slice(0, size === 'sm' ? 40 : size === 'lg' ? 150 : 80) : '' }}{{ caption.length > (size === 'sm' ? 40 : size === 'lg' ? 150 : 80) ? '...' : '' }}
        </span>
      </div>
      <div
        v-if="hashtags"
        class="text-blue-500 dark:text-blue-400 mt-0.5"
        :class="{ 'line-clamp-1': size === 'sm', 'line-clamp-2': size !== 'sm' }"
      >
        {{ hashtags.slice(0, size === 'sm' ? 30 : 80) }}
      </div>
    </div>
  </div>
</template>
