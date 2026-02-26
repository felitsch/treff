<script setup>
/**
 * ContentSuggestions.vue - KI-Content-Vorschläge für das Dashboard
 *
 * Zeigt 3-5 KI-generierte Content-Vorschläge basierend auf:
 * - Aktuelle Jahreszeit (Bewerbungsfristen, Abflugzeiten)
 * - Anstehende Feiertage/Events
 * - Lücken im Content-Kalender
 * - Beliebte Themen / unterrepräsentierte Kategorien
 *
 * Jeder Vorschlag zeigt: Titel, Beschreibung, vorgeschlagenes Format, empfohlener Zeitpunkt.
 * "Post erstellen" navigiert zum Creator mit vorausgefülltem Thema.
 * "Nicht interessant" markiert den Vorschlag als dismissed.
 */
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import HelpTooltip from '@/components/common/HelpTooltip.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { tooltipTexts } from '@/utils/tooltipTexts'
import { formatDate } from '@/utils/dateUtils'

const props = defineProps({
  /** Initial suggestions loaded from dashboard API */
  initialSuggestions: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['suggestions-updated'])

const router = useRouter()

const suggestions = ref([...props.initialSuggestions])
const acceptingId = ref(null)
const dismissingId = ref(null)
const generatingSuggestions = ref(false)

// Watch for external updates to initialSuggestions
const updateSuggestions = (newSuggestions) => {
  suggestions.value = [...newSuggestions]
}

// ── Suggestion Type Helpers ──

function suggestionTypeIcon(type) {
  const icons = {
    seasonal: 'sparkles',
    country_rotation: 'globe',
    category_balance: 'adjustments-vertical',
    gap_fill: 'calendar',
    weekly_plan: 'clipboard-list',
    story_teaser: 'paper-airplane',
    holiday: 'trophy',
  }
  return icons[type] || 'light-bulb'
}

function suggestionTypeLabel(type) {
  const labels = {
    seasonal: 'Saisonal',
    country_rotation: 'Länder-Rotation',
    category_balance: 'Kategorie-Balance',
    gap_fill: 'Lücke füllen',
    weekly_plan: 'Wochenplan',
    story_teaser: 'Story-Teaser',
    holiday: 'Feiertag/Event',
  }
  return labels[type] || type
}

function suggestionTypeBadge(type) {
  const badges = {
    seasonal: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300',
    country_rotation: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    category_balance: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    gap_fill: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
    weekly_plan: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
    story_teaser: 'bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900/30 dark:text-fuchsia-300',
    holiday: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  }
  return badges[type] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
}

function categoryLabel(cat) {
  const labels = {
    laender_spotlight: 'Länder-Spotlight',
    erfahrungsberichte: 'Erfahrungsbericht',
    infografiken: 'Infografik',
    fristen_cta: 'Fristen/CTA',
    tipps_tricks: 'Tipps & Tricks',
    faq: 'FAQ',
    foto_posts: 'Foto-Post',
    reel_tiktok_thumbnails: 'Reel/TikTok',
    story_posts: 'Story',
  }
  return labels[cat] || cat
}

function countryFlag(country) {
  const flags = {
    usa: '🇺🇸',
    canada: '🇨🇦',
    australia: '🇦🇺',
    newzealand: '🇳🇿',
    ireland: '🇮🇪',
  }
  return flags[country] || ''
}

function formatLabel(format) {
  const labels = {
    instagram_feed: 'Instagram Feed',
    instagram_story: 'Instagram Story',
    instagram_stories: 'Instagram Story',
    instagram_reels: 'Instagram Reel',
    tiktok: 'TikTok',
    carousel: 'Karussell',
  }
  return labels[format] || format || ''
}

function formatIcon(format) {
  const icons = {
    instagram_feed: 'camera',
    instagram_story: 'device-mobile',
    instagram_stories: 'device-mobile',
    instagram_reels: 'film',
    tiktok: 'musical-note',
    carousel: 'stack',
  }
  return icons[format] || 'document-text'
}

// formatDate imported from @/utils/dateUtils

// ── Actions ──

async function acceptSuggestion(suggestion) {
  acceptingId.value = suggestion.id
  try {
    await api.put('/api/suggestions/' + suggestion.id + '/accept')
    suggestions.value = suggestions.value.filter((s) => s.id !== suggestion.id)
    emit('suggestions-updated', suggestions.value)

    // Navigate to create post with pre-filled data (category, country, topic)
    const query = {}
    if (suggestion.suggested_category) query.category = suggestion.suggested_category
    if (suggestion.suggested_country) query.country = suggestion.suggested_country
    if (suggestion.title) query.topic = suggestion.title

    router.push({
      path: '/create/quick',
      query,
    })
  } catch (err) {
    console.error('Failed to accept suggestion:', err)
  } finally {
    acceptingId.value = null
  }
}

async function dismissSuggestion(suggestion) {
  dismissingId.value = suggestion.id
  try {
    await api.put('/api/suggestions/' + suggestion.id + '/dismiss')
    suggestions.value = suggestions.value.filter((s) => s.id !== suggestion.id)
    emit('suggestions-updated', suggestions.value)
  } catch (err) {
    console.error('Failed to dismiss suggestion:', err)
  } finally {
    dismissingId.value = null
  }
}

async function generateSuggestions() {
  generatingSuggestions.value = true
  try {
    const res = await api.post('/api/ai/suggest-content', {})
    if (res.data.suggestions && res.data.suggestions.length > 0) {
      suggestions.value = [...res.data.suggestions, ...suggestions.value]
      emit('suggestions-updated', suggestions.value)
    }
  } catch (err) {
    console.error('Failed to generate suggestions:', err)
  } finally {
    generatingSuggestions.value = false
  }
}

defineExpose({ updateSuggestions, generateSuggestions })
</script>

<template>
  <BaseCard padding="none" data-tour="dashboard-suggestions" data-testid="content-suggestions">
    <template #header>
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
        <AppIcon name="light-bulb" class="w-5 h-5" /> Content-Vorschläge
        <HelpTooltip :text="tooltipTexts.dashboard.suggestions" size="sm" />
      </h2>
    </template>
    <template #headerAction>
      <div class="flex items-center gap-2">
        <span
          v-if="suggestions.length > 0"
          class="text-xs font-medium px-2.5 py-1 rounded-full bg-[#4C8BC2]/10 text-[#4C8BC2] dark:bg-[#4C8BC2]/20"
        >
          {{ suggestions.length }} offen
        </span>
        <button
          @click="generateSuggestions"
          :disabled="generatingSuggestions"
          data-testid="generate-suggestions-btn"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-[#4C8BC2] rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <AppIcon v-if="generatingSuggestions" name="clock" class="w-4 h-4 animate-spin" />
          <AppIcon v-else name="sparkles" class="w-4 h-4" />
          {{ generatingSuggestions ? 'Generiere...' : 'Neue Vorschläge' }}
        </button>
      </div>
    </template>
    <div class="p-5">
      <!-- Empty state -->
      <EmptyState
        v-if="suggestions.length === 0"
        svgIcon="sparkles"
        title="Keine Vorschläge vorhanden"
        description="Klicke auf 'Neue Vorschläge' um KI-gestützte Content-Vorschläge für deine nächsten Posts zu erhalten."
        actionLabel="Vorschläge generieren"
        :compact="true"
        @action="generateSuggestions"
      />

      <!-- Suggestions grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-for="suggestion in suggestions"
          :key="suggestion.id"
          data-testid="suggestion-card"
          class="border border-gray-100 dark:border-gray-700 rounded-lg p-4 hover:border-[#4C8BC2]/30 dark:hover:border-[#4C8BC2]/40 transition-colors"
        >
          <!-- Top row: type badge + category + country + format -->
          <div class="flex items-center gap-2 flex-wrap mb-2">
            <span
              class="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full"
              :class="suggestionTypeBadge(suggestion.suggestion_type)"
            >
              <AppIcon :name="suggestionTypeIcon(suggestion.suggestion_type)" class="w-3.5 h-3.5 inline-block" />
              {{ suggestionTypeLabel(suggestion.suggestion_type) }}
            </span>
            <span
              v-if="suggestion.suggested_category"
              class="text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300"
            >
              {{ categoryLabel(suggestion.suggested_category) }}
            </span>
            <span
              v-if="suggestion.suggested_country"
              class="text-xs"
            >
              {{ countryFlag(suggestion.suggested_country) }}
            </span>
            <!-- Suggested format badge -->
            <span
              v-if="suggestion.suggested_format"
              class="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-300"
              data-testid="suggestion-format"
            >
              <AppIcon :name="formatIcon(suggestion.suggested_format)" class="w-3.5 h-3.5 inline-block" />
              {{ formatLabel(suggestion.suggested_format) }}
            </span>
            <!-- Suggested date -->
            <span
              v-if="suggestion.suggested_date"
              class="text-xs text-gray-400 dark:text-gray-500 ml-auto"
              data-testid="suggestion-date"
            >
              <AppIcon name="calendar" class="w-3.5 h-3.5 inline-block" /> {{ formatDate(suggestion.suggested_date) }}
            </span>
          </div>

          <!-- Title -->
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-1" data-testid="suggestion-title">
            {{ suggestion.title }}
          </h3>

          <!-- Description -->
          <p
            v-if="suggestion.description"
            class="text-xs text-gray-500 dark:text-gray-400 mb-2 line-clamp-2"
            data-testid="suggestion-description"
          >
            {{ suggestion.description }}
          </p>

          <!-- Reason -->
          <div
            v-if="suggestion.reason"
            class="flex items-start gap-1.5 mb-3"
          >
            <AppIcon name="chat-bubble" class="w-3.5 h-3.5 text-gray-400 mt-0.5" />
            <p class="text-xs text-gray-400 dark:text-gray-500 italic">
              {{ suggestion.reason }}
            </p>
          </div>

          <!-- Action buttons -->
          <div class="flex items-center gap-2">
            <button
              @click="acceptSuggestion(suggestion)"
              :disabled="acceptingId === suggestion.id"
              data-testid="accept-suggestion-btn"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-[#4C8BC2] rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <AppIcon v-if="acceptingId === suggestion.id" name="clock" class="w-4 h-4 animate-spin" />
              <AppIcon v-else name="check-circle" class="w-4 h-4" />
              Post erstellen
            </button>
            <button
              @click="dismissSuggestion(suggestion)"
              :disabled="dismissingId === suggestion.id"
              data-testid="dismiss-suggestion-btn"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <AppIcon v-if="dismissingId === suggestion.id" name="clock" class="w-4 h-4 animate-spin" />
              <AppIcon v-else name="x-circle" class="w-4 h-4" />
              Nicht interessant
            </button>
          </div>
        </div>
      </div>
    </div>
  </BaseCard>
</template>
