<script setup>
/**
 * VideoRepurposeView.vue — Standalone Video-First Content-Repurposing Page
 *
 * Wraps VideoRepurposeWizard component as a full-page view.
 * Can be accessed directly at /video/repurpose/:id or without an ID
 * to show a post selector.
 *
 * @see Feature #319 — V-09: Video-First Content-Repurposing Pipeline
 * @see components/video/VideoRepurposeWizard.vue
 */
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import VideoRepurposeWizard from '@/components/video/VideoRepurposeWizard.vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const route = useRoute()
const router = useRouter()
const toast = useToast()

const postId = ref(null)
const recentVideoPosts = ref([])
const loadingRecent = ref(false)

/** Load recent video/reel posts for the selector */
async function loadRecentVideoPosts() {
  loadingRecent.value = true
  try {
    const { data } = await api.get('/api/posts', {
      params: { limit: 20, sort: '-created_at' }
    })
    const posts = Array.isArray(data) ? data : (data.posts || data.items || [])
    recentVideoPosts.value = posts.filter(p => {
      const platform = (p.platform || '').toLowerCase()
      return platform.includes('reel') || platform.includes('tiktok') || platform === 'instagram_reels'
    })
  } catch (err) {
    console.error('Failed to load recent posts:', err)
  } finally {
    loadingRecent.value = false
  }
}

function selectPost(id) {
  postId.value = id
}

function onGenerated(result) {
  const count = result.derivative_count || result.derivatives?.length || 0
  toast.success(`${count} Video-Derivat(e) erfolgreich erstellt!`)
}

onMounted(() => {
  if (route.params.id) {
    postId.value = parseInt(route.params.id)
  } else {
    loadRecentVideoPosts()
  }
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-950 py-8">
    <!-- Page header -->
    <div class="max-w-6xl mx-auto px-6 mb-6">
      <div class="flex items-center gap-3 mb-1">
        <button
          @click="router.back()"
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7"/>
          </svg>
        </button>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <AppIcon name="film" class="w-6 h-6" /> Video-Content-Pipeline
        </h1>
      </div>
      <p class="text-sm text-gray-500 dark:text-gray-400 ml-8">
        1 Video &#8594; 4+ Formate: Reel, TikTok, Stories, Feed-Post, Carousel
      </p>
    </div>

    <!-- Wizard (when post is selected) -->
    <VideoRepurposeWizard
      v-if="postId"
      :post-id="postId"
      @generated="onGenerated"
      @close="router.back()"
    />

    <!-- Post selector (when no post ID) -->
    <div v-else class="max-w-4xl mx-auto px-6">
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Quell-Video auswaehlen
        </h3>

        <!-- Loading -->
        <div v-if="loadingRecent" class="flex items-center justify-center py-12">
          <div class="animate-spin w-8 h-8 border-3 border-[#3B7AB1] border-t-transparent rounded-full"></div>
        </div>

        <!-- Video posts list -->
        <div v-else-if="recentVideoPosts.length > 0" class="space-y-2">
          <button
            v-for="p in recentVideoPosts"
            :key="p.id"
            @click="selectPost(p.id)"
            class="w-full flex items-center gap-4 p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors text-left"
          >
            <!-- Thumbnail -->
            <div class="w-16 h-16 rounded-lg bg-gray-100 dark:bg-gray-700 overflow-hidden flex-shrink-0">
              <img
                v-if="p.thumbnail || p.image_url"
                :src="p.thumbnail || p.image_url"
                :alt="p.title"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                <AppIcon name="film" class="w-7 h-7" />
              </div>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ p.title || 'Kein Titel' }}</p>
              <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                <span>{{ p.platform }}</span>
                <span v-if="p.country">&#183; {{ p.country }}</span>
                <span>&#183; #{{ p.id }}</span>
              </div>
            </div>
            <span class="text-[#3B7AB1] text-sm font-medium">Auswaehlen &#8594;</span>
          </button>
        </div>

        <!-- Empty state -->
        <div v-else class="text-center py-12 text-gray-500 dark:text-gray-400">
          <AppIcon name="film" class="w-10 h-10 mx-auto mb-3" />
          <p class="text-sm">Keine Video-Posts (Reels/TikTok) gefunden.</p>
          <p class="text-xs mt-1">Erstelle zuerst einen Video-Post, um ihn in andere Formate umzuwandeln.</p>
        </div>
      </div>
    </div>
  </div>
</template>
