<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const route = useRoute()
const router = useRouter()
const toast = useToast()

const loading = ref(true)
const student = ref(null)
const storyArcs = ref([])
const posts = ref([])
const stats = ref({ total_posts: 0, posted_count: 0, scheduled_count: 0, draft_count: 0, story_arcs_count: 0, episodes_count: 0 })

// Profile image upload
const uploadingImage = ref(false)
const fileInput = ref(null)

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

const statusLabels = {
  active: 'Aktiv',
  upcoming: 'Bevorstehend',
  completed: 'Abgeschlossen',
}

const statusColors = {
  active: 'bg-green-100 text-green-800',
  upcoming: 'bg-blue-100 text-blue-800',
  completed: 'bg-gray-100 text-gray-600',
}

const arcStatusColors = {
  draft: 'bg-gray-100 text-gray-600',
  active: 'bg-green-100 text-green-800',
  paused: 'bg-amber-100 text-amber-800',
  completed: 'bg-blue-100 text-blue-800',
}

const arcStatusLabels = {
  draft: 'Entwurf',
  active: 'Aktiv',
  paused: 'Pausiert',
  completed: 'Abgeschlossen',
}

const postStatusColors = {
  draft: 'bg-gray-100 text-gray-600',
  scheduled: 'bg-blue-100 text-blue-800',
  posted: 'bg-green-100 text-green-800',
  exported: 'bg-purple-100 text-purple-800',
}

const postStatusLabels = {
  draft: 'Entwurf',
  scheduled: 'Geplant',
  posted: 'Veroeffentlicht',
  exported: 'Exportiert',
}

const funFacts = computed(() => {
  if (!student.value?.fun_facts) return []
  try {
    const parsed = JSON.parse(student.value.fun_facts)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
})

const personalityInfo = computed(() => {
  if (!student.value?.personality_preset) return null
  try {
    const preset = typeof student.value.personality_preset === 'string'
      ? JSON.parse(student.value.personality_preset)
      : student.value.personality_preset
    return preset
  } catch {
    return null
  }
})

const toneLabels = {
  witzig: 'Witzig',
  emotional: 'Emotional',
  motivierend: 'Motivierend',
  jugendlich: 'Jugendlich',
  serioess: 'Serioess',
  storytelling: 'Storytelling',
  'behind-the-scenes': 'Behind-the-Scenes',
  provokant: 'Provokant',
  wholesome: 'Wholesome',
  informativ: 'Informativ',
}

const emojiLabels = {
  none: 'Keine Emojis',
  minimal: 'Wenig Emojis',
  moderate: 'Moderat',
  heavy: 'Viele Emojis',
}

async function loadDashboard() {
  loading.value = true
  try {
    const studentId = route.params.id
    const response = await api.get(`/api/students/${studentId}/dashboard`)
    student.value = response.data.student
    storyArcs.value = response.data.story_arcs
    posts.value = response.data.posts
    stats.value = response.data.stats
  } catch (err) {
    toast.error('Student konnte nicht geladen werden.')
    router.push('/students')
  } finally {
    loading.value = false
  }
}

function triggerFileUpload() {
  fileInput.value?.click()
}

async function handleFileUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return

  // Validate file type
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    toast.error('Bitte waehle ein Bild (JPEG, PNG oder WebP).')
    return
  }

  // Validate file size (max 20MB)
  if (file.size > 20 * 1024 * 1024) {
    toast.error('Das Bild darf maximal 20 MB gross sein.')
    return
  }

  uploadingImage.value = true
  try {
    // 1. Upload asset
    const formData = new FormData()
    formData.append('file', file)
    formData.append('category', 'photo')
    formData.append('source', 'upload')
    const uploadResponse = await api.post('/api/assets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    const assetId = uploadResponse.data.id

    // 2. Update student with new profile_image_id
    await api.put(`/api/students/${student.value.id}`, {
      profile_image_id: assetId,
    })

    toast.success('Profilbild erfolgreich aktualisiert.')
    await loadDashboard()
  } catch (err) {
    toast.error('Fehler beim Hochladen des Profilbilds.')
  } finally {
    uploadingImage.value = false
    // Reset file input
    if (fileInput.value) fileInput.value.value = ''
  }
}

function getArcPostCount(arcId) {
  return posts.value.filter(p => p.story_arc_id === arcId).length
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })
  } catch {
    return dateStr
  }
}

onMounted(() => {
  loadDashboard()
})
</script>

<template>
  <div class="p-6 max-w-7xl mx-auto">
    <!-- Loading -->
    <div v-if="loading" class="text-center py-16">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto"></div>
      <p class="mt-3 text-gray-500 dark:text-gray-400">Lade Studenten-Profil...</p>
    </div>

    <template v-else-if="student">
      <!-- Back button -->
      <button
        class="flex items-center gap-2 text-gray-500 dark:text-gray-400 hover:text-treff-blue mb-6 transition-colors"
        @click="router.push('/students')"
      >
        <span class="text-lg">&larr;</span>
        <span class="text-sm">Zurueck zur Uebersicht</span>
      </button>

      <!-- Profile Header Card -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <div class="flex flex-col md:flex-row gap-6">
          <!-- Profile Image -->
          <div class="flex-shrink-0 relative group">
            <div class="w-32 h-32 rounded-2xl bg-treff-blue/10 flex items-center justify-center overflow-hidden border-2 border-gray-200 dark:border-gray-600">
              <img
                v-if="student.profile_image_url"
                :src="student.profile_image_url"
                :alt="student.name"
                class="w-full h-full object-cover"
              />
              <span v-else class="text-5xl">{{ countryFlags[student.country] || '\u{1F30D}' }}</span>
            </div>
            <!-- Upload overlay -->
            <button
              class="absolute inset-0 w-32 h-32 rounded-2xl bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
              :disabled="uploadingImage"
              @click="triggerFileUpload"
            >
              <span v-if="uploadingImage" class="text-white text-sm">Laden...</span>
              <span v-else class="text-white text-sm font-medium">Bild aendern</span>
            </button>
            <input
              ref="fileInput"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              class="hidden"
              @change="handleFileUpload"
            />
          </div>

          <!-- Profile Info -->
          <div class="flex-1">
            <div class="flex items-start justify-between">
              <div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
                  {{ student.name }}
                </h1>
                <p class="text-gray-500 dark:text-gray-400 mt-1 flex items-center gap-2">
                  <span class="text-xl">{{ countryFlags[student.country] }}</span>
                  <span>{{ countryLabels[student.country] || student.country }}</span>
                  <span v-if="student.city">&middot; {{ student.city }}</span>
                </p>
              </div>
              <span :class="['text-xs font-medium px-3 py-1 rounded-full', statusColors[student.status]]">
                {{ statusLabels[student.status] || student.status }}
              </span>
            </div>

            <!-- Detail Fields -->
            <div class="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <div v-if="student.school_name" class="flex items-center gap-2">
                <span class="text-gray-400">Schule:</span>
                <span class="text-gray-700 dark:text-gray-300">{{ student.school_name }}</span>
              </div>
              <div v-if="student.host_family_name" class="flex items-center gap-2">
                <span class="text-gray-400">Gastfamilie:</span>
                <span class="text-gray-700 dark:text-gray-300">{{ student.host_family_name }}</span>
              </div>
              <div v-if="student.start_date || student.end_date" class="flex items-center gap-2">
                <span class="text-gray-400">Zeitraum:</span>
                <span class="text-gray-700 dark:text-gray-300">
                  {{ formatDate(student.start_date) }} - {{ formatDate(student.end_date) }}
                </span>
              </div>
            </div>

            <!-- Bio -->
            <p v-if="student.bio" class="mt-3 text-sm text-gray-600 dark:text-gray-300">
              {{ student.bio }}
            </p>

            <!-- Fun Facts -->
            <div v-if="funFacts.length > 0" class="mt-3 flex flex-wrap gap-2">
              <span
                v-for="(fact, i) in funFacts"
                :key="i"
                class="inline-block px-2.5 py-1 bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300 rounded-full text-xs font-medium"
              >
                {{ fact }}
              </span>
            </div>

            <!-- Personality Preset Summary -->
            <div v-if="personalityInfo" class="mt-3 flex flex-wrap gap-2">
              <span class="inline-block px-2.5 py-1 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 rounded-full text-xs font-medium">
                {{ toneLabels[personalityInfo.tone] || personalityInfo.tone }}
              </span>
              <span class="inline-block px-2.5 py-1 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 rounded-full text-xs font-medium">
                Humor {{ personalityInfo.humor_level || 3 }}/5
              </span>
              <span class="inline-block px-2.5 py-1 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 rounded-full text-xs font-medium">
                {{ emojiLabels[personalityInfo.emoji_usage] || personalityInfo.emoji_usage }}
              </span>
              <span class="inline-block px-2.5 py-1 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 rounded-full text-xs font-medium">
                {{ personalityInfo.perspective === 'first_person' ? 'Ich-Perspektive' : 'Dritte Person' }}
              </span>
              <span
                v-for="(phrase, i) in (personalityInfo.catchphrases || [])"
                :key="'cp-' + i"
                class="inline-block px-2.5 py-1 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300 rounded-full text-xs font-medium"
              >
                "{{ phrase }}"
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Statistics Cards -->
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center">
          <p class="text-2xl font-bold text-treff-blue">{{ stats.total_posts }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Gesamt Posts</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center">
          <p class="text-2xl font-bold text-green-600">{{ stats.posted_count }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Veroeffentlicht</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center">
          <p class="text-2xl font-bold text-blue-600">{{ stats.scheduled_count }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Geplant</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center">
          <p class="text-2xl font-bold text-gray-500">{{ stats.draft_count }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Entwuerfe</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center">
          <p class="text-2xl font-bold text-amber-600">{{ stats.story_arcs_count }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Story-Serien</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center">
          <p class="text-2xl font-bold text-purple-600">{{ stats.episodes_count }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Episoden</p>
        </div>
      </div>

      <!-- Story Arcs Section -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-4">
          Story-Serien ({{ storyArcs.length }})
        </h2>

        <div v-if="storyArcs.length === 0" class="text-center py-8 text-gray-400 dark:text-gray-500">
          <p class="text-3xl mb-2">&#x1F4D6;</p>
          <p>Noch keine Story-Serien fuer diesen Studenten.</p>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="arc in storyArcs"
            :key="arc.id"
            class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
          >
            <div class="flex-1">
              <div class="flex items-center gap-2">
                <h3 class="font-medium text-gray-900 dark:text-white">{{ arc.title }}</h3>
                <span :class="['text-xs font-medium px-2 py-0.5 rounded-full', arcStatusColors[arc.status] || 'bg-gray-100 text-gray-600']">
                  {{ arcStatusLabels[arc.status] || arc.status }}
                </span>
              </div>
              <p v-if="arc.subtitle" class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                {{ arc.subtitle }}
              </p>
              <div class="flex items-center gap-4 mt-1.5 text-xs text-gray-400">
                <span>{{ arc.current_episode }}/{{ arc.planned_episodes }} Episoden</span>
                <span>{{ getArcPostCount(arc.id) }} Posts</span>
                <span v-if="arc.country">{{ countryFlags[arc.country] }} {{ countryLabels[arc.country] }}</span>
              </div>
            </div>
            <!-- Progress bar -->
            <div class="w-24 ml-4">
              <div class="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                <div
                  class="bg-treff-blue rounded-full h-2 transition-all"
                  :style="{ width: `${Math.min(100, (arc.current_episode / Math.max(1, arc.planned_episodes)) * 100)}%` }"
                ></div>
              </div>
              <p class="text-xs text-gray-400 text-right mt-1">
                {{ Math.round((arc.current_episode / Math.max(1, arc.planned_episodes)) * 100) }}%
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Posts Section -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-4">
          Zugehoerige Posts ({{ posts.length }})
        </h2>

        <div v-if="posts.length === 0" class="text-center py-8 text-gray-400 dark:text-gray-500">
          <p class="text-3xl mb-2">&#x1F4DD;</p>
          <p>Noch keine Posts fuer diesen Studenten.</p>
        </div>

        <div v-else class="space-y-2">
          <div
            v-for="post in posts"
            :key="post.id"
            class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
            @click="router.push(`/create/post/${post.id}/edit`)"
          >
            <div class="flex items-center gap-3 flex-1 min-w-0">
              <!-- Episode badge -->
              <span
                v-if="post.episode_number"
                class="flex-shrink-0 w-8 h-8 rounded-full bg-treff-blue/10 text-treff-blue text-xs font-bold flex items-center justify-center"
              >
                E{{ post.episode_number }}
              </span>
              <div class="min-w-0">
                <p class="font-medium text-gray-900 dark:text-white truncate">
                  {{ post.title || 'Ohne Titel' }}
                </p>
                <div class="flex items-center gap-2 mt-0.5 text-xs text-gray-400">
                  <span v-if="post.category">{{ post.category }}</span>
                  <span v-if="post.platform">&middot; {{ post.platform }}</span>
                  <span v-if="post.scheduled_date">&middot; {{ formatDate(post.scheduled_date) }}</span>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-2 ml-3">
              <span v-if="post.country" class="text-sm">{{ countryFlags[post.country] }}</span>
              <span :class="['text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap', postStatusColors[post.status] || 'bg-gray-100 text-gray-600']">
                {{ postStatusLabels[post.status] || post.status }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
