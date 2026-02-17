<script setup>
/**
 * PostPreviewCardTikTok.vue — TikTok Mockup Preview Card
 *
 * Realistic TikTok-style vertical post mockup showing how a post will appear
 * on TikTok. Includes:
 *  - Vertical 9:16 format card
 *  - Right icon sidebar (Heart, Comment, Share, Bookmark)
 *  - Sound/music bar at the bottom
 *  - Username overlay (@treff_sprachreisen)
 *  - Video thumbnail with play button overlay
 *  - Country accent coloring
 *  - Status badge overlay (Draft, Scheduled, Published)
 *
 * @see PostPreviewCard.vue — Instagram mockup variant
 * @see PostPreviewGrid.vue — Grid layout for multiple previews
 */
import { computed } from 'vue'

const props = defineProps({
  /** Post object with title, caption, platform, country, status, slides, etc. */
  post: { type: Object, required: true },
  /** Target platform: 'tiktok' (default) */
  platform: { type: String, default: 'tiktok' },
  /** Card size variant: 'sm' | 'md' | 'lg' */
  size: { type: String, default: 'md', validator: v => ['sm', 'md', 'lg'].includes(v) },
  /** Whether to show the caption preview */
  showCaption: { type: Boolean, default: true },
})

const emit = defineEmits(['click'])

// ── Country accent colors ──
const countryAccents = {
  usa:       { border: '#B22234', bg: 'rgba(178,34,52,0.15)', text: '#B22234', label: 'USA', flag: '\uD83C\uDDFA\uD83C\uDDF8' },
  kanada:    { border: '#FF0000', bg: 'rgba(255,0,0,0.15)', text: '#FF0000', label: 'Kanada', flag: '\uD83C\uDDE8\uD83C\uDDE6' },
  canada:    { border: '#FF0000', bg: 'rgba(255,0,0,0.15)', text: '#FF0000', label: 'Kanada', flag: '\uD83C\uDDE8\uD83C\uDDE6' },
  australien:{ border: '#CC7722', bg: 'rgba(204,119,34,0.15)', text: '#CC7722', label: 'Australien', flag: '\uD83C\uDDE6\uD83C\uDDFA' },
  australia: { border: '#CC7722', bg: 'rgba(204,119,34,0.15)', text: '#CC7722', label: 'Australien', flag: '\uD83C\uDDE6\uD83C\uDDFA' },
  neuseeland:{ border: '#1B4D3E', bg: 'rgba(27,77,62,0.15)', text: '#1B4D3E', label: 'Neuseeland', flag: '\uD83C\uDDF3\uD83C\uDDFF' },
  nz:        { border: '#1B4D3E', bg: 'rgba(27,77,62,0.15)', text: '#1B4D3E', label: 'Neuseeland', flag: '\uD83C\uDDF3\uD83C\uDDFF' },
  irland:    { border: '#169B62', bg: 'rgba(22,155,98,0.15)', text: '#169B62', label: 'Irland', flag: '\uD83C\uDDEE\uD83C\uDDEA' },
  ireland:   { border: '#169B62', bg: 'rgba(22,155,98,0.15)', text: '#169B62', label: 'Irland', flag: '\uD83C\uDDEE\uD83C\uDDEA' },
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

const accentBorderColor = computed(() => country.value?.border || '#FE2C55')

const status = computed(() => {
  const s = props.post?.status?.toLowerCase?.() || 'draft'
  return statusConfig[s] || statusConfig.draft
})

const isVideo = computed(() => {
  const slide = slides.value[0]
  if (!slide) return true // TikTok posts are typically videos
  return slide.type === 'video' || slide.media_type === 'video' || (slide.url && /\.(mp4|mov|webm)$/i.test(slide.url))
})

const slides = computed(() => {
  if (Array.isArray(props.post?.slides)) return props.post.slides
  if (typeof props.post?.slide_data === 'string') {
    try { return JSON.parse(props.post.slide_data) } catch { return [] }
  }
  if (Array.isArray(props.post?.slide_data)) return props.post.slide_data
  return []
})

const imageUrl = computed(() => {
  const slide = slides.value[0]
  if (!slide) return props.post?.thumbnail || props.post?.image_url || ''
  return slide.image_url || slide.url || slide.thumbnail || props.post?.thumbnail || ''
})

const caption = computed(() => {
  return props.post?.caption_tiktok || props.post?.caption || ''
})

const hashtags = computed(() => {
  return props.post?.hashtags_tiktok || props.post?.hashtags || ''
})

const title = computed(() => {
  return props.post?.title || ''
})

// ── Size classes ──
const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm': return { card: 'w-[140px]', text: 'text-[7px]', title: 'text-[8px]', avatar: 'w-5 h-5', iconSize: 'text-[10px]', sidebarGap: 'gap-2' }
    case 'lg': return { card: 'w-[280px]', text: 'text-[10px]', title: 'text-xs', avatar: 'w-9 h-9', iconSize: 'text-base', sidebarGap: 'gap-4' }
    default:   return { card: 'w-[200px]', text: 'text-[8px]', title: 'text-[10px]', avatar: 'w-7 h-7', iconSize: 'text-sm', sidebarGap: 'gap-3' }
  }
})

// Fake engagement numbers for realism
const engagementLikes = computed(() => Math.floor(Math.random() * 900) + 100)
const engagementComments = computed(() => Math.floor(Math.random() * 50) + 5)
const engagementShares = computed(() => Math.floor(Math.random() * 20) + 1)
</script>

<template>
  <div
    class="relative rounded-xl overflow-hidden bg-black shadow-card hover:shadow-card-hover transition-shadow duration-200 cursor-pointer"
    :class="sizeClasses.card"
    :style="{ borderLeft: `3px solid ${accentBorderColor}` }"
    @click="emit('click', post)"
    data-testid="post-preview-card-tiktok"
  >
    <!-- 9:16 aspect ratio container -->
    <div class="relative aspect-[9/16] overflow-hidden">
      <!-- Background image / content -->
      <div class="absolute inset-0 bg-gradient-to-br from-[#1A1A2E] to-[#010101]">
        <img
          v-if="imageUrl"
          :src="imageUrl"
          :alt="title || 'TikTok preview'"
          class="absolute inset-0 w-full h-full object-cover"
          loading="lazy"
        />

        <!-- Fallback when no image -->
        <div v-else class="absolute inset-0 flex flex-col items-center justify-center p-3 text-center">
          <div class="text-2xl mb-2 opacity-40">&#x1F3B5;</div>
          <p v-if="title" class="text-white/70 font-semibold line-clamp-3" :class="sizeClasses.title">{{ title }}</p>
        </div>
      </div>

      <!-- Video play button overlay -->
      <div
        v-if="isVideo"
        class="absolute inset-0 flex items-center justify-center z-10"
        data-testid="post-preview-tiktok-video-overlay"
      >
        <div
          class="rounded-full bg-black/40 backdrop-blur-sm flex items-center justify-center border-2 border-white/50"
          :class="size === 'sm' ? 'w-8 h-8' : size === 'lg' ? 'w-16 h-16' : 'w-12 h-12'"
        >
          <svg class="text-white ml-0.5" :class="size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-7 h-7' : 'w-5 h-5'" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </div>
      </div>

      <!-- Status badge (top-left) -->
      <div
        class="absolute top-2 left-2 z-20 px-1.5 py-0.5 rounded-full text-white font-semibold flex items-center gap-0.5"
        :class="[status.bg, size === 'sm' ? 'text-[6px]' : 'text-[8px]']"
        data-testid="post-preview-tiktok-status-badge"
      >
        <span>{{ status.icon }}</span>
        <span>{{ status.label }}</span>
      </div>

      <!-- Country accent badge (top-right, below status) -->
      <div
        v-if="country"
        class="absolute top-2 right-2 z-20 px-1.5 py-0.5 rounded-full font-semibold flex items-center gap-0.5"
        :class="size === 'sm' ? 'text-[6px]' : 'text-[8px]'"
        :style="{ backgroundColor: country.bg, color: country.text, border: `1px solid ${country.border}` }"
        data-testid="post-preview-tiktok-country-badge"
      >
        <span>{{ country.flag }}</span>
        <span v-if="size !== 'sm'">{{ country.label }}</span>
      </div>

      <!-- Right sidebar icons (TikTok signature) -->
      <div
        class="absolute right-1.5 bottom-24 flex flex-col items-center z-20"
        :class="sizeClasses.sidebarGap"
        data-testid="post-preview-tiktok-sidebar"
      >
        <!-- Profile avatar -->
        <div class="relative">
          <div
            :class="sizeClasses.avatar"
            class="rounded-full bg-gradient-to-br from-[#3B7AB1] to-[#2E6A9E] ring-2 ring-white flex items-center justify-center"
          >
            <span class="text-white font-bold" :class="size === 'sm' ? 'text-[5px]' : 'text-[7px]'">T</span>
          </div>
          <div class="absolute -bottom-1 left-1/2 -translate-x-1/2 w-3 h-3 bg-[#FE2C55] rounded-full flex items-center justify-center">
            <span class="text-white text-[6px]">+</span>
          </div>
        </div>

        <!-- Heart -->
        <div class="flex flex-col items-center">
          <span class="text-white" :class="sizeClasses.iconSize">&#9825;</span>
          <span class="text-white" :class="size === 'sm' ? 'text-[5px]' : 'text-[7px]'">{{ engagementLikes }}</span>
        </div>

        <!-- Comment -->
        <div class="flex flex-col items-center">
          <span class="text-white" :class="sizeClasses.iconSize">&#128172;</span>
          <span class="text-white" :class="size === 'sm' ? 'text-[5px]' : 'text-[7px]'">{{ engagementComments }}</span>
        </div>

        <!-- Share -->
        <div class="flex flex-col items-center">
          <span class="text-white" :class="sizeClasses.iconSize">&#10148;</span>
          <span class="text-white" :class="size === 'sm' ? 'text-[5px]' : 'text-[7px]'">{{ engagementShares }}</span>
        </div>

        <!-- Bookmark -->
        <div class="flex flex-col items-center">
          <span class="text-white" :class="sizeClasses.iconSize">&#128278;</span>
        </div>

        <!-- Music disc -->
        <div
          class="rounded-full bg-gray-800 border-2 border-gray-600 flex items-center justify-center animate-spin-slow"
          :class="size === 'sm' ? 'w-5 h-5' : size === 'lg' ? 'w-9 h-9' : 'w-7 h-7'"
        >
          <div
            class="rounded-full bg-gradient-to-br from-[#3B7AB1] to-[#FDD000]"
            :class="size === 'sm' ? 'w-2 h-2' : size === 'lg' ? 'w-3.5 h-3.5' : 'w-2.5 h-2.5'"
          ></div>
        </div>
      </div>

      <!-- Bottom content overlay (username, caption, music) -->
      <div class="absolute bottom-0 left-0 right-10 p-3 pb-4 z-20 bg-gradient-to-t from-black/70 to-transparent">
        <!-- Username -->
        <p class="text-white font-semibold mb-0.5" :class="sizeClasses.text">@treff_sprachreisen</p>

        <!-- Caption -->
        <p
          v-if="showCaption && caption"
          class="text-white/90 leading-relaxed mb-1"
          :class="[sizeClasses.text, size === 'sm' ? 'line-clamp-1' : 'line-clamp-2']"
        >
          {{ caption.slice(0, size === 'sm' ? 30 : 80) }}
        </p>

        <!-- Hashtags -->
        <p
          v-if="hashtags"
          class="text-white/60 line-clamp-1 mb-1"
          :class="size === 'sm' ? 'text-[6px]' : 'text-[7px]'"
        >
          {{ hashtags.slice(0, 50) }}
        </p>

        <!-- Music ticker -->
        <div class="flex items-center gap-1.5">
          <span class="text-white/60" :class="size === 'sm' ? 'text-[7px]' : 'text-[8px]'">\u266A</span>
          <div class="overflow-hidden flex-1">
            <p class="text-white/50 whitespace-nowrap animate-marquee" :class="size === 'sm' ? 'text-[6px]' : 'text-[7px]'">Original Sound - TREFF Sprachreisen</p>
          </div>
        </div>
      </div>

      <!-- TikTok bottom navigation bar -->
      <div
        class="absolute bottom-0 left-0 right-0 bg-black/90 z-30 py-1 px-3 flex items-center justify-around text-white/50"
        :class="size === 'sm' ? 'text-[6px]' : 'text-[7px]'"
      >
        <span>Home</span>
        <span>Entdecken</span>
        <div class="w-5 h-3.5 bg-white rounded-sm flex items-center justify-center -mt-0.5">
          <span class="text-black font-bold" :class="size === 'sm' ? 'text-[7px]' : 'text-[8px]'">+</span>
        </div>
        <span>Posteingang</span>
        <span>Profil</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Slow spin for TikTok music disc */
@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin-slow {
  animation: spin-slow 4s linear infinite;
}

/* Marquee animation for music ticker */
@keyframes marquee {
  0% { transform: translateX(0); }
  100% { transform: translateX(-100%); }
}
.animate-marquee {
  animation: marquee 8s linear infinite;
}
</style>
