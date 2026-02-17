<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const toast = useToast()

const drafts = ref([])
const loading = ref(false)
const deletingId = ref(null)
const confirmDeleteId = ref(null)

async function loadDrafts() {
  loading.value = true
  try {
    const res = await api.get('/api/posts/drafts/list')
    drafts.value = res.data?.drafts || []
  } catch (err) {
    // Error toast shown by API interceptor
    toast.error('Entwuerfe konnten nicht geladen werden.', 4000)
  } finally {
    loading.value = false
  }
}

async function deleteDraft(id) {
  deletingId.value = id
  try {
    await api.delete(`/api/posts/drafts/${id}`)
    drafts.value = drafts.value.filter(d => d.id !== id)
    confirmDeleteId.value = null
    toast.success('Entwurf geloescht.', 3000)
  } catch (err) {
    toast.error('Loeschen fehlgeschlagen: ' + (err.response?.data?.detail || err.message), 4000)
  } finally {
    deletingId.value = null
  }
}

function openDraft(draft) {
  // Navigate to the advanced creator which supports auto-save restoration
  router.push('/create/advanced')
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function categoryLabel(cat) {
  const map = {
    laender_spotlight: 'Laender-Spotlight',
    erfahrungsberichte: 'Erfahrungsberichte',
    infografiken: 'Infografiken',
    fristen_cta: 'Fristen & CTA',
    tipps_tricks: 'Tipps & Tricks',
    faq: 'FAQ',
    foto_posts: 'Foto-Posts',
    reel_tiktok_thumbnails: 'Reel/TikTok',
    story_posts: 'Story-Posts',
    story_teaser: 'Story-Teaser',
    story_series: 'Story-Serien',
    allgemein: 'Allgemein',
  }
  return map[cat] || cat || 'Allgemein'
}

function countryFlag(c) {
  const map = { usa: '🇺🇸', canada: '🇨🇦', australia: '🇦🇺', newzealand: '🇳🇿', ireland: '🇮🇪' }
  return map[c] || ''
}

const hasDrafts = computed(() => drafts.value.length > 0)

onMounted(() => {
  loadDrafts()
})
</script>

<template>
  <div class="max-w-4xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Gespeicherte Entwuerfe</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Automatisch gespeicherte Entwuerfe aus dem Post-Creator
        </p>
      </div>
      <button
        @click="loadDrafts"
        :disabled="loading"
        class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
      >
        {{ loading ? 'Laden...' : 'Aktualisieren' }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading && drafts.length === 0" class="space-y-4">
      <div v-for="i in 3" :key="i" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 animate-pulse">
        <div class="h-5 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-3"></div>
        <div class="h-4 bg-gray-100 dark:bg-gray-700 rounded w-2/3"></div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!loading && !hasDrafts" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-12 text-center">
      <div class="text-5xl mb-4">&#x1F4DD;</div>
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Keine Entwuerfe vorhanden</h3>
      <p class="text-gray-500 dark:text-gray-400 text-sm mb-6 max-w-md mx-auto">
        Wenn du im Post-Creator arbeitest, werden deine Aenderungen automatisch als Entwurf gespeichert.
        Du kannst jederzeit dort weitermachen, wo du aufgehoert hast.
      </p>
      <button
        @click="router.push('/create/advanced')"
        class="px-6 py-2.5 bg-[#3B7AB1] hover:bg-[#2E6A9E] text-white font-medium rounded-lg transition-colors"
      >
        Neuen Post erstellen
      </button>
    </div>

    <!-- Drafts List -->
    <div v-else class="space-y-3">
      <div
        v-for="draft in drafts"
        :key="draft.id"
        class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:border-[#3B7AB1]/40 dark:hover:border-blue-500/40 transition-all group"
      >
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1 min-w-0 cursor-pointer" @click="openDraft(draft)">
            <div class="flex items-center gap-2 mb-1.5">
              <h3 class="font-semibold text-gray-900 dark:text-white truncate group-hover:text-[#3B7AB1] dark:group-hover:text-blue-400 transition-colors">
                {{ draft.title || 'Unbenannter Entwurf' }}
              </h3>
              <span v-if="draft.country" class="text-base flex-shrink-0">{{ countryFlag(draft.country) }}</span>
            </div>
            <div class="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400 flex-wrap">
              <span v-if="draft.category" class="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-full">
                {{ categoryLabel(draft.category) }}
              </span>
              <span v-if="draft.platform" class="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full">
                {{ draft.platform }}
              </span>
              <span>
                Zuletzt bearbeitet: {{ formatDate(draft.updated_at) }}
              </span>
            </div>
          </div>

          <div class="flex items-center gap-2 flex-shrink-0">
            <button
              @click="router.push(`/create/post/${draft.id}/edit`)"
              class="px-3 py-1.5 text-xs font-medium text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/40 transition-colors"
              title="Fuer andere Plattform anpassen"
              data-testid="repurpose-draft-btn"
            >
              🔄 Anpassen
            </button>
            <button
              @click="openDraft(draft)"
              class="px-3 py-1.5 text-xs font-medium text-[#3B7AB1] dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors"
            >
              Fortsetzen
            </button>
            <div class="relative">
              <button
                v-if="confirmDeleteId !== draft.id"
                @click="confirmDeleteId = draft.id"
                class="px-2.5 py-1.5 text-xs text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                title="Loeschen"
              >
                &#x1F5D1;
              </button>
              <div v-else class="flex items-center gap-1">
                <button
                  @click="deleteDraft(draft.id)"
                  :disabled="deletingId === draft.id"
                  class="px-2.5 py-1.5 text-xs font-medium text-white bg-red-500 hover:bg-red-600 disabled:bg-red-300 rounded-lg transition-colors"
                >
                  {{ deletingId === draft.id ? '...' : 'Ja' }}
                </button>
                <button
                  @click="confirmDeleteId = null"
                  class="px-2.5 py-1.5 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  Nein
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
