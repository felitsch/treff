<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const route = useRoute()
const router = useRouter()
const toast = useToast()

const arc = ref(null)
const loading = ref(true)

const countryFlags = {
  usa: '\u{1F1FA}\u{1F1F8}',
  kanada: '\u{1F1E8}\u{1F1E6}',
  australien: '\u{1F1E6}\u{1F1FA}',
  neuseeland: '\u{1F1F3}\u{1F1FF}',
  irland: '\u{1F1EE}\u{1F1EA}',
}

const countryLabels = {
  usa: 'USA',
  kanada: 'Kanada',
  australien: 'Australien',
  neuseeland: 'Neuseeland',
  irland: 'Irland',
}

const statusConfig = {
  active: { label: 'Aktiv', color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300', dot: 'bg-green-500' },
  paused: { label: 'Pausiert', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300', dot: 'bg-yellow-500' },
  draft: { label: 'Entwurf', color: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300', dot: 'bg-gray-400' },
  completed: { label: 'Abgeschlossen', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300', dot: 'bg-blue-500' },
}

const episodeStatusConfig = {
  planned: { label: 'Geplant', color: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300', icon: '\u{1F4CB}', dot: 'bg-gray-400 border-gray-300' },
  draft: { label: 'Entwurf', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300', icon: '\u{270F}\u{FE0F}', dot: 'bg-yellow-400 border-yellow-300' },
  published: { label: 'Publiziert', color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300', icon: '\u{2705}', dot: 'bg-green-500 border-green-400' },
}

const progress = computed(() => {
  if (!arc.value) return 0
  const total = arc.value.total_episodes || arc.value.planned_episodes || 1
  const published = arc.value.published_episodes || 0
  return Math.round((published / total) * 100)
})

async function fetchArc() {
  loading.value = true
  try {
    const arcId = route.params.id
    const { data } = await api.get(`/api/story-arcs/${arcId}`, {
      params: { include_episodes: true }
    })
    arc.value = data
  } catch (err) {
    console.error('Failed to fetch story arc:', err)
    toast.error('Story-Arc konnte nicht geladen werden.')
    router.push('/story-arcs')
  } finally {
    loading.value = false
  }
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: 'short', year: 'numeric' })
}

function goToPost(postId) {
  if (postId) {
    router.push(`/posts/${postId}/edit`)
  }
}

function goBack() {
  router.push('/story-arcs')
}

onMounted(() => {
  fetchArc()
})
</script>

<template>
  <div class="p-6 max-w-5xl mx-auto">
    <!-- Loading -->
    <div v-if="loading" class="text-center py-16 text-gray-500">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
      <p class="mt-2">Lade Story-Arc...</p>
    </div>

    <template v-else-if="arc">
      <!-- Back button -->
      <button
        class="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-treff-blue transition-colors mb-4"
        @click="goBack"
      >
        <span>&#x2190;</span>
        <span>Zurueck zu Story-Arcs</span>
      </button>

      <!-- Header Section -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden mb-6">
        <!-- Cover Image or Gradient Header -->
        <div class="h-48 bg-gradient-to-br from-treff-blue/30 to-treff-yellow/30 relative overflow-hidden">
          <img
            v-if="arc.cover_image_url"
            :src="arc.cover_image_url"
            :alt="arc.title"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex items-center justify-center">
            <span class="text-7xl opacity-30">📖</span>
          </div>
          <!-- Status Badge -->
          <div class="absolute top-4 right-4">
            <span
              :class="['text-sm font-semibold px-3 py-1.5 rounded-full shadow-sm', statusConfig[arc.status]?.color || 'bg-gray-100 text-gray-600']"
            >
              {{ statusConfig[arc.status]?.label || arc.status }}
            </span>
          </div>
        </div>

        <!-- Arc Info -->
        <div class="p-6">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-1">{{ arc.title }}</h1>
              <p v-if="arc.subtitle" class="text-lg text-gray-500 dark:text-gray-400 mb-2">{{ arc.subtitle }}</p>
              <p v-if="arc.description" class="text-gray-600 dark:text-gray-300 mb-4 leading-relaxed">{{ arc.description }}</p>

              <!-- Meta Tags -->
              <div class="flex flex-wrap gap-3">
                <span v-if="arc.student_name" class="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 px-3 py-1.5 rounded-full">
                  <span>🎓</span> {{ arc.student_name }}
                </span>
                <span v-if="arc.country" class="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 px-3 py-1.5 rounded-full">
                  {{ countryFlags[arc.country] || '\u{1F30D}' }} {{ countryLabels[arc.country] || arc.country }}
                </span>
                <span v-if="arc.tone" class="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 px-3 py-1.5 rounded-full capitalize">
                  <span>🎤</span> {{ arc.tone }}
                </span>
                <span class="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 px-3 py-1.5 rounded-full">
                  <span>📅</span> Erstellt {{ formatDate(arc.created_at) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Progress Bar -->
          <div class="mt-5 pt-5 border-t border-gray-100 dark:border-gray-700">
            <div class="flex items-center justify-between text-sm text-gray-600 dark:text-gray-300 mb-2">
              <span class="font-medium">Gesamtfortschritt</span>
              <span class="font-bold">
                {{ arc.published_episodes || 0 }}/{{ arc.total_episodes || arc.planned_episodes || 0 }} Episoden publiziert ({{ progress }}%)
              </span>
            </div>
            <div class="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-700"
                :class="progress === 100 ? 'bg-green-500' : 'bg-treff-blue'"
                :style="{ width: `${progress}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Episode Timeline -->
      <div class="mb-6">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-4">
          Episoden-Timeline
          <span class="text-sm font-normal text-gray-500 dark:text-gray-400 ml-2">
            ({{ arc.episodes?.length || 0 }} Episoden)
          </span>
        </h2>

        <!-- Empty episodes -->
        <div
          v-if="!arc.episodes || arc.episodes.length === 0"
          class="text-center py-12 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700"
        >
          <p class="text-4xl mb-3">📝</p>
          <p class="text-gray-500 dark:text-gray-400">Noch keine Episoden erstellt</p>
          <p class="text-gray-400 dark:text-gray-500 text-sm mt-1">
            Episoden werden ueber den Story-Wizard oder die Kalender-Ansicht erstellt.
          </p>
        </div>

        <!-- Timeline -->
        <div v-else class="relative">
          <!-- Timeline line -->
          <div class="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700"></div>

          <!-- Episode cards -->
          <div
            v-for="(episode, index) in arc.episodes"
            :key="episode.id"
            class="relative flex items-start gap-4 mb-4 last:mb-0"
          >
            <!-- Timeline dot -->
            <div class="relative z-10 flex-shrink-0">
              <div
                :class="[
                  'w-12 h-12 rounded-full flex items-center justify-center border-2 text-sm font-bold shadow-sm',
                  episode.status === 'published' ? 'bg-green-50 dark:bg-green-900/30 border-green-400 text-green-700 dark:text-green-300' :
                  episode.status === 'draft' ? 'bg-yellow-50 dark:bg-yellow-900/30 border-yellow-400 text-yellow-700 dark:text-yellow-300' :
                  'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400'
                ]"
              >
                E{{ episode.episode_number }}
              </div>
            </div>

            <!-- Episode card -->
            <div
              :class="[
                'flex-1 bg-white dark:bg-gray-800 rounded-xl border p-4 transition-all duration-200',
                episode.post_id ? 'border-gray-200 dark:border-gray-700 hover:shadow-md cursor-pointer' : 'border-dashed border-gray-300 dark:border-gray-600'
              ]"
              @click="goToPost(episode.post_id)"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1">
                    <h3 class="font-semibold text-gray-900 dark:text-white truncate">
                      {{ episode.episode_title }}
                    </h3>
                    <span
                      :class="['text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap', episodeStatusConfig[episode.status]?.color || 'bg-gray-100 text-gray-600']"
                    >
                      {{ episodeStatusConfig[episode.status]?.label || episode.status }}
                    </span>
                  </div>

                  <!-- Teaser text -->
                  <p v-if="episode.teaser_text" class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 mb-2">
                    {{ episode.teaser_text }}
                  </p>

                  <!-- Post link info -->
                  <div v-if="episode.post_id" class="flex flex-wrap items-center gap-3 text-xs text-gray-400 dark:text-gray-500">
                    <span v-if="episode.post_title" class="flex items-center gap-1">
                      <span>📄</span> {{ episode.post_title }}
                    </span>
                    <span v-if="episode.post_scheduled_date" class="flex items-center gap-1">
                      <span>📅</span> {{ formatDate(episode.post_scheduled_date) }}
                    </span>
                    <span v-if="episode.post_platform" class="flex items-center gap-1">
                      <span>📱</span> {{ episode.post_platform }}
                    </span>
                    <span v-if="episode.post_status" class="flex items-center gap-1">
                      <span>{{ episode.post_status === 'posted' ? '\u{2705}' : episode.post_status === 'scheduled' ? '\u{1F551}' : '\u{270F}\u{FE0F}' }}</span>
                      {{ episode.post_status }}
                    </span>
                  </div>
                  <div v-else class="text-xs text-gray-400 dark:text-gray-500 italic">
                    Noch kein Post verknuepft
                  </div>
                </div>

                <!-- Arrow for linked posts -->
                <div v-if="episode.post_id" class="flex-shrink-0 ml-3 text-gray-400 dark:text-gray-500">
                  <span class="text-lg">→</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
