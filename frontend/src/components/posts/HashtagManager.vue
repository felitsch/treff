<script setup>
/**
 * HashtagManager.vue - Intelligent Hashtag Generator & Manager
 *
 * Features:
 * - AI-based hashtag generation via /api/ai/suggest-hashtags
 * - Clickable hashtag chips with toggle on/off
 * - Manual hashtag input (type + Enter)
 * - X/30 counter for Instagram limit
 * - Hashtag sets: Save, Load, Delete
 * - Category badges: Brand, Thema, Land, Trending
 * - Copy-to-clipboard button
 *
 * @emits update:modelValue - Emitted with the space-separated hashtag string
 */
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'
import { PREDEFINED_SETS, getHashtagLimit, buildOptimizedSet, PLATFORM_HASHTAG_LIMITS } from '@/config/hashtagSets'
import AppIcon from '@/components/icons/AppIcon.vue'

const props = defineProps({
  /** Space-separated hashtag string (v-model) */
  modelValue: { type: String, default: '' },
  /** Post topic for AI suggestions */
  topic: { type: String, default: '' },
  /** Selected country */
  country: { type: String, default: '' },
  /** Selected platform */
  platform: { type: String, default: 'instagram_feed' },
  /** Selected category */
  category: { type: String, default: '' },
  /** Tone of voice */
  tone: { type: String, default: 'jugendlich' },
  /** Max hashtags allowed (Instagram = 30) */
  maxHashtags: { type: Number, default: 30 },
  /** Platform label for display */
  platformLabel: { type: String, default: 'Instagram' },
  /** Whether the component is disabled */
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const toast = useToast()

// ── State ───────────────────────────────────────────────────────────────
const suggestedHashtags = ref([]) // { tag: '#xyz', selected: true/false, category: 'brand'|'thema'|'land'|'trending' }
const manualInput = ref('')
const generating = ref(false)
const savingSet = ref(false)
const loadingSets = ref(false)
const hashtagSets = ref([])
const showSets = ref(false)
const newSetName = ref('')
const showSaveDialog = ref(false)

// ── Category badges with colors ─────────────────────────────────────────
const CATEGORY_STYLES = {
  brand: { label: 'Brand', bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-300', border: 'border-blue-200 dark:border-blue-800' },
  thema: { label: 'Thema', bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-700 dark:text-purple-300', border: 'border-purple-200 dark:border-purple-800' },
  land: { label: 'Land', bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300', border: 'border-green-200 dark:border-green-800' },
  trending: { label: 'Trending', bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-300', border: 'border-amber-200 dark:border-amber-800' },
}

// ── Brand hashtags (always categorized as brand) ────────────────────────
const BRAND_HASHTAGS = ['#TREFFSprachreisen', '#TREFF', '#TREFFHighschool', '#Sprachreisen']
const COUNTRY_HASHTAGS = {
  usa: ['#HighschoolUSA', '#AuslandsjährUSA', '#AmerikaAbenteuer', '#USAExchange'],
  kanada: ['#HighschoolKanada', '#KanadaAbenteuer', '#CanadaExchange'],
  australien: ['#HighschoolAustralien', '#AustralienAbenteuer', '#AussieExchange'],
  neuseeland: ['#HighschoolNeuseeland', '#NeuseelandAbenteuer', '#NZExchange'],
  irland: ['#HighschoolIrland', '#IrlandAbenteuer', '#IrelandExchange'],
}

// ── Computed ────────────────────────────────────────────────────────────
const selectedHashtags = computed(() =>
  suggestedHashtags.value.filter(h => h.selected).map(h => h.tag)
)

const selectedCount = computed(() => selectedHashtags.value.length)

const hashtagString = computed(() => selectedHashtags.value.join(' '))

const isOverLimit = computed(() => selectedCount.value > props.maxHashtags)

const countColor = computed(() => {
  if (selectedCount.value > props.maxHashtags) return 'text-red-600 dark:text-red-400'
  if (selectedCount.value > props.maxHashtags - 5) return 'text-amber-600 dark:text-amber-400'
  return 'text-gray-500 dark:text-gray-400'
})

// ── Watch for external changes to modelValue ────────────────────────────
watch(() => props.modelValue, (newVal) => {
  if (newVal !== hashtagString.value) {
    syncFromModelValue(newVal)
  }
}, { immediate: true })

// Sync output back to parent
watch(hashtagString, (newVal) => {
  if (newVal !== props.modelValue) {
    emit('update:modelValue', newVal)
  }
})

// ── Methods ─────────────────────────────────────────────────────────────

function syncFromModelValue(val) {
  if (!val) {
    // Don't clear suggestions, just deselect all
    suggestedHashtags.value.forEach(h => { h.selected = false })
    return
  }
  const tags = val.split(/\s+/).filter(t => t.startsWith('#'))
  // Add any tags from modelValue that aren't in suggestions
  for (const tag of tags) {
    const existing = suggestedHashtags.value.find(h => h.tag.toLowerCase() === tag.toLowerCase())
    if (existing) {
      existing.selected = true
    } else {
      suggestedHashtags.value.push({ tag, selected: true, category: categorizeHashtag(tag) })
    }
  }
  // Deselect any that aren't in the model
  for (const h of suggestedHashtags.value) {
    h.selected = tags.some(t => t.toLowerCase() === h.tag.toLowerCase())
  }
}

function categorizeHashtag(tag) {
  const lower = tag.toLowerCase()
  if (BRAND_HASHTAGS.some(b => b.toLowerCase() === lower)) return 'brand'
  for (const [, countryTags] of Object.entries(COUNTRY_HASHTAGS)) {
    if (countryTags.some(ct => ct.toLowerCase() === lower)) return 'land'
  }
  if (lower.includes('trending') || lower.includes('fyp') || lower.includes('viral') || lower.includes('foryou')) return 'trending'
  return 'thema'
}

function toggleHashtag(hashtag) {
  if (props.disabled) return
  // Don't allow selecting more if at limit
  if (!hashtag.selected && selectedCount.value >= props.maxHashtags) {
    toast.warning(`Maximal ${props.maxHashtags} Hashtags erlaubt!`)
    return
  }
  hashtag.selected = !hashtag.selected
}

function addManualHashtag() {
  let tag = manualInput.value.trim()
  if (!tag) return
  if (!tag.startsWith('#')) tag = '#' + tag
  // Remove spaces within the tag
  tag = tag.replace(/\s+/g, '')

  const existing = suggestedHashtags.value.find(h => h.tag.toLowerCase() === tag.toLowerCase())
  if (existing) {
    existing.selected = true
    manualInput.value = ''
    return
  }

  if (selectedCount.value >= props.maxHashtags) {
    toast.warning(`Maximal ${props.maxHashtags} Hashtags erlaubt!`)
    return
  }

  suggestedHashtags.value.push({ tag, selected: true, category: categorizeHashtag(tag) })
  manualInput.value = ''
}

function removeHashtag(hashtag) {
  const idx = suggestedHashtags.value.indexOf(hashtag)
  if (idx !== -1) {
    suggestedHashtags.value.splice(idx, 1)
  }
}

function selectAll() {
  const maxToSelect = props.maxHashtags
  let count = 0
  for (const h of suggestedHashtags.value) {
    if (count < maxToSelect) {
      h.selected = true
      count++
    } else {
      h.selected = false
    }
  }
}

function deselectAll() {
  suggestedHashtags.value.forEach(h => { h.selected = false })
}

async function generateHashtags() {
  if (generating.value || props.disabled) return
  generating.value = true

  try {
    const res = await api.post('/api/ai/suggest-hashtags', {
      topic: props.topic || 'Auslandsjahr',
      country: props.country || null,
      platform: props.platform || 'instagram_feed',
      category: props.category || null,
      tone: props.tone || 'jugendlich',
    })

    if (res.data && res.data.hashtags) {
      const newTags = res.data.hashtags
      // Merge with existing: add new ones, keep existing selections
      for (const tag of newTags) {
        const normalized = tag.startsWith('#') ? tag : '#' + tag
        const existing = suggestedHashtags.value.find(h => h.tag.toLowerCase() === normalized.toLowerCase())
        if (!existing) {
          suggestedHashtags.value.push({ tag: normalized, selected: true, category: categorizeHashtag(normalized) })
        } else {
          existing.selected = true
        }
      }
      toast.success(`${newTags.length} Hashtags vorgeschlagen! (${res.data.source === 'gemini' ? 'KI' : 'Regel-basiert'})`)
    }
  } catch (err) {
    console.error('Hashtag generation failed:', err)
    toast.error('Hashtag-Generierung fehlgeschlagen. Bitte versuche es erneut.')
  } finally {
    generating.value = false
  }
}

async function copyToClipboard() {
  const text = hashtagString.value
  if (!text) {
    toast.warning('Keine Hashtags ausgewaehlt.')
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    toast.success(`${selectedCount.value} Hashtags kopiert!`)
  } catch {
    // Fallback for environments without clipboard API
    const textarea = document.createElement('textarea')
    textarea.value = text
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    toast.success(`${selectedCount.value} Hashtags kopiert!`)
  }
}

// ── Hashtag Sets ────────────────────────────────────────────────────────

async function loadHashtagSets() {
  loadingSets.value = true
  try {
    const res = await api.get('/api/hashtag-sets')
    hashtagSets.value = res.data.hashtag_sets || []
  } catch (err) {
    console.error('Failed to load hashtag sets:', err)
  } finally {
    loadingSets.value = false
  }
}

async function saveAsSet() {
  const name = newSetName.value.trim()
  if (!name) {
    toast.warning('Bitte gib einen Namen fuer das Set ein.')
    return
  }
  if (selectedHashtags.value.length === 0) {
    toast.warning('Waehle mindestens einen Hashtag aus.')
    return
  }
  savingSet.value = true
  try {
    await api.post('/api/hashtag-sets', {
      name,
      hashtags: selectedHashtags.value,
      category: props.category || null,
      country: props.country || null,
    })
    toast.success(`Set "${name}" gespeichert!`)
    newSetName.value = ''
    showSaveDialog.value = false
    await loadHashtagSets()
  } catch (err) {
    console.error('Failed to save hashtag set:', err)
    toast.error('Speichern fehlgeschlagen.')
  } finally {
    savingSet.value = false
  }
}

function applySet(set) {
  const tags = set.hashtags || []
  for (const tag of tags) {
    const normalized = tag.startsWith('#') ? tag : '#' + tag
    const existing = suggestedHashtags.value.find(h => h.tag.toLowerCase() === normalized.toLowerCase())
    if (!existing) {
      suggestedHashtags.value.push({ tag: normalized, selected: true, category: categorizeHashtag(normalized) })
    } else {
      existing.selected = true
    }
  }
  toast.success(`Set "${set.name}" angewendet (${tags.length} Hashtags)`)
}

async function deleteSet(set) {
  try {
    await api.delete(`/api/hashtag-sets/${set.id}`)
    hashtagSets.value = hashtagSets.value.filter(s => s.id !== set.id)
    toast.success(`Set "${set.name}" geloescht`)
  } catch (err) {
    if (err.response?.status === 404) {
      toast.error('Set nicht gefunden oder keine Berechtigung.')
    } else {
      toast.error('Loeschen fehlgeschlagen.')
    }
  }
}

function toggleSetsPanel() {
  showSets.value = !showSets.value
  if (showSets.value && hashtagSets.value.length === 0) {
    loadHashtagSets()
  }
}

// ── Predefined Sets (from hashtagSets.js config) ────────────────────────
const showPredefinedSets = ref(false)

/** Predefined sets filtered by current country/platform */
const filteredPredefinedSets = computed(() => {
  let sets = PREDEFINED_SETS
  // Prioritize sets matching the current country
  if (props.country) {
    const countryKey = props.country.toLowerCase()
    sets = [
      ...sets.filter(s => s.country === countryKey),
      ...sets.filter(s => !s.country),
    ]
  }
  return sets
})

/** Platform hashtag limits from config */
const platformLimit = computed(() => getHashtagLimit(props.platform))

/** Apply a predefined set from the config */
function applyPredefinedSet(set) {
  const tags = set.hashtags || []
  for (const tag of tags) {
    const normalized = tag.startsWith('#') ? tag : '#' + tag
    const existing = suggestedHashtags.value.find(h => h.tag.toLowerCase() === normalized.toLowerCase())
    if (!existing) {
      suggestedHashtags.value.push({ tag: normalized, selected: true, category: categorizeHashtag(normalized) })
    } else {
      existing.selected = true
    }
  }
  toast.success(`Vordefiniertes Set "${set.name}" geladen (${tags.length} Hashtags)`)
}

/** Build and apply an optimized set based on current context */
function applyOptimizedSet() {
  const countryKey = props.country?.toLowerCase() || ''
  const tags = buildOptimizedSet({
    platform: props.platform,
    country: countryKey,
    niche: 'auslandsjahr',
  })
  for (const tag of tags) {
    const existing = suggestedHashtags.value.find(h => h.tag.toLowerCase() === tag.toLowerCase())
    if (!existing) {
      suggestedHashtags.value.push({ tag, selected: true, category: categorizeHashtag(tag) })
    } else {
      existing.selected = true
    }
  }
  toast.success(`Optimiertes Set geladen (${tags.length} Hashtags)`)
}

// ── Init ────────────────────────────────────────────────────────────────
onMounted(() => {
  // Pre-load sets in background
  loadHashtagSets()
})
</script>

<template>
  <div class="space-y-3" data-testid="hashtag-manager">
    <!-- Header with counter and actions -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="text-sm font-bold text-gray-700 dark:text-gray-300"># Hashtags</span>
        <span :class="['text-xs font-semibold px-2 py-0.5 rounded-full', countColor,
          isOverLimit ? 'bg-red-100 dark:bg-red-900/30' : 'bg-gray-100 dark:bg-gray-800']"
          data-testid="hashtag-counter"
        >
          {{ selectedCount }}/{{ maxHashtags }}
        </span>
      </div>
      <div class="flex items-center gap-1.5">
        <!-- Generate button -->
        <button
          @click="generateHashtags"
          :disabled="generating || disabled"
          class="text-xs px-2.5 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors flex items-center gap-1"
          data-testid="generate-hashtags-btn"
          title="KI-Hashtags generieren"
        >
          <span :class="{ 'animate-spin': generating }" class="text-sm">&#x2728;</span>
          <span>{{ generating ? 'Generiere...' : 'KI-Vorschlaege' }}</span>
        </button>
        <!-- Copy button -->
        <button
          @click="copyToClipboard"
          :disabled="selectedCount === 0 || disabled"
          class="text-xs px-2 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
          title="Hashtags kopieren"
          data-testid="copy-hashtags-btn"
        >
          <AppIcon name="clipboard-list" class="w-4 h-4" />
        </button>
        <!-- Sets toggle -->
        <button
          @click="toggleSetsPanel"
          :class="['text-xs px-2 py-1.5 rounded-lg transition-colors',
            showSets ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600']"
          title="Hashtag-Sets verwalten"
          data-testid="toggle-sets-btn"
        >
          <AppIcon name="document" class="w-4 h-4 inline-block" /> Sets
        </button>
      </div>
    </div>

    <!-- Over-limit warning -->
    <div v-if="isOverLimit" class="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-3 py-1.5" role="alert">
      Zu viele Hashtags! Instagram erlaubt maximal {{ maxHashtags }}. Bitte entferne {{ selectedCount - maxHashtags }} Hashtag(s).
    </div>

    <!-- Tag Cloud: Suggested Hashtags -->
    <div v-if="suggestedHashtags.length > 0" class="flex flex-wrap gap-1.5" data-testid="hashtag-cloud">
      <button
        v-for="(hashtag, idx) in suggestedHashtags"
        :key="hashtag.tag + idx"
        @click="toggleHashtag(hashtag)"
        :class="[
          'group inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border transition-all duration-200',
          hashtag.selected
            ? CATEGORY_STYLES[hashtag.category]?.bg + ' ' + CATEGORY_STYLES[hashtag.category]?.text + ' ' + CATEGORY_STYLES[hashtag.category]?.border + ' border shadow-sm'
            : 'bg-gray-50 dark:bg-gray-800 text-gray-400 dark:text-gray-500 border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 line-through opacity-60'
        ]"
        :disabled="disabled"
        :title="hashtag.selected ? 'Klicken zum Abwaehlen' : 'Klicken zum Auswaehlen'"
        :data-testid="'hashtag-chip-' + hashtag.tag.replace('#', '')"
      >
        <span>{{ hashtag.tag }}</span>
        <span v-if="hashtag.selected" class="text-[9px] opacity-60">{{ CATEGORY_STYLES[hashtag.category]?.label }}</span>
        <!-- Remove button (appears on hover) -->
        <span
          @click.stop="removeHashtag(hashtag)"
          class="opacity-0 group-hover:opacity-100 ml-0.5 text-[10px] cursor-pointer hover:text-red-500 transition-opacity"
          title="Entfernen"
        >&times;</span>
      </button>
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-4 text-sm text-gray-400 dark:text-gray-500 border border-dashed border-gray-300 dark:border-gray-700 rounded-lg">
      Klicke "KI-Vorschlaege" um Hashtags zu generieren oder gib eigene ein.
    </div>

    <!-- Quick actions -->
    <div v-if="suggestedHashtags.length > 0" class="flex items-center gap-2 text-xs">
      <button @click="selectAll" class="text-blue-600 dark:text-blue-400 hover:underline" :disabled="disabled">Alle auswaehlen</button>
      <span class="text-gray-300">|</span>
      <button @click="deselectAll" class="text-gray-500 hover:underline" :disabled="disabled">Alle abwaehlen</button>
    </div>

    <!-- Manual input -->
    <div class="flex gap-2">
      <input
        v-model="manualInput"
        @keydown.enter.prevent="addManualHashtag"
        type="text"
        placeholder="Eigenen Hashtag eingeben..."
        class="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-purple-400 focus:border-purple-400"
        :disabled="disabled"
        data-testid="manual-hashtag-input"
      />
      <button
        @click="addManualHashtag"
        :disabled="!manualInput.trim() || disabled"
        class="px-3 py-1.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 text-sm transition-colors"
        data-testid="add-hashtag-btn"
      >
        + Hinzufuegen
      </button>
    </div>

    <!-- ═══════ Hashtag Sets Panel ═══════ -->
    <div v-if="showSets" class="border border-gray-200 dark:border-gray-700 rounded-xl p-4 bg-gray-50 dark:bg-gray-800/50 space-y-3" data-testid="hashtag-sets-panel">
      <div class="flex items-center justify-between">
        <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Gespeicherte Sets</h4>
        <button
          @click="showSaveDialog = !showSaveDialog"
          class="text-xs px-2.5 py-1 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          :disabled="selectedCount === 0 || disabled"
          data-testid="save-set-btn"
        >
          + Aktuelles speichern
        </button>
      </div>

      <!-- Save dialog -->
      <div v-if="showSaveDialog" class="flex gap-2">
        <input
          v-model="newSetName"
          @keydown.enter.prevent="saveAsSet"
          type="text"
          placeholder="Name fuer das Set..."
          class="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-green-400"
          :disabled="savingSet"
          data-testid="set-name-input"
        />
        <button
          @click="saveAsSet"
          :disabled="savingSet || !newSetName.trim()"
          class="px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm transition-colors"
        >
          {{ savingSet ? '...' : 'Speichern' }}
        </button>
        <button
          @click="showSaveDialog = false"
          class="px-2 py-1.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-sm"
        >
          &times;
        </button>
      </div>

      <!-- Sets list -->
      <div v-if="loadingSets" class="text-center py-3 text-sm text-gray-400">
        <AppIcon name="clock" class="w-4 h-4 animate-spin inline-block mr-1" /> Lade Sets...
      </div>
      <div v-else-if="hashtagSets.length === 0" class="text-center py-3 text-sm text-gray-400">
        Keine gespeicherten Sets vorhanden.
      </div>
      <div v-else class="space-y-2 max-h-[200px] overflow-y-auto">
        <div
          v-for="set in hashtagSets"
          :key="set.id"
          class="flex items-center justify-between p-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700 transition-colors"
          :data-testid="'hashtag-set-' + set.id"
        >
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">{{ set.name }}</div>
            <div class="text-xs text-gray-400 truncate">{{ (set.hashtags || []).slice(0, 5).join(' ') }}{{ (set.hashtags || []).length > 5 ? '...' : '' }}</div>
          </div>
          <div class="flex items-center gap-1 ml-2">
            <span class="text-[10px] text-gray-400 mr-1">{{ (set.hashtags || []).length }}</span>
            <button
              @click="applySet(set)"
              class="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800/50 transition-colors"
              title="Set anwenden"
              :disabled="disabled"
            >
              Laden
            </button>
            <button
              v-if="!set.is_default"
              @click="deleteSet(set)"
              class="text-xs px-1.5 py-1 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
              title="Set loeschen"
              :disabled="disabled"
            >
              <AppIcon name="trash" class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════ Predefined Sets (from hashtagSets.js config) ═══════ -->
    <div class="border-t border-gray-200 dark:border-gray-700 pt-3" data-testid="predefined-sets-section">
      <button
        @click="showPredefinedSets = !showPredefinedSets"
        class="w-full flex items-center justify-between text-xs font-semibold text-gray-600 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors"
      >
        <span class="flex items-center gap-1.5">
          <AppIcon name="clipboard-list" class="w-4 h-4" />
          Vordefinierte Hashtag-Sets
          <span class="text-[10px] text-gray-400">({{ filteredPredefinedSets.length }})</span>
        </span>
        <span>{{ showPredefinedSets ? '▲' : '▼' }}</span>
      </button>

      <div v-if="showPredefinedSets" class="mt-2 space-y-2">
        <!-- Quick optimized set button -->
        <button
          @click="applyOptimizedSet"
          :disabled="disabled"
          class="w-full px-3 py-2 text-xs font-semibold rounded-lg border-2 border-dashed border-purple-300 dark:border-purple-700 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-all flex items-center justify-center gap-1.5"
          data-testid="optimized-set-btn"
        >
          <AppIcon name="sparkles" class="w-4 h-4 inline" /> Optimiertes Set generieren ({{ platformLimit.ideal }} Hashtags)
        </button>

        <!-- Platform limit info -->
        <div class="text-[10px] text-gray-400 text-center">
          {{ props.platform === 'tiktok' ? 'TikTok' : 'Instagram' }}: {{ platformLimit.min }}-{{ platformLimit.max }} Hashtags, ideal {{ platformLimit.ideal }}
        </div>

        <!-- Predefined sets grid -->
        <div class="grid grid-cols-2 gap-2 max-h-[200px] overflow-y-auto">
          <button
            v-for="set in filteredPredefinedSets.slice(0, 8)"
            :key="set.id"
            @click="applyPredefinedSet(set)"
            :disabled="disabled"
            class="text-left p-2 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-purple-300 dark:hover:border-purple-700 hover:bg-purple-50/50 dark:hover:bg-purple-900/10 transition-all"
            :data-testid="'predefined-set-' + set.id"
          >
            <div class="text-[11px] font-semibold text-gray-800 dark:text-gray-200 truncate">{{ set.name }}</div>
            <div class="text-[10px] text-gray-400 truncate">{{ set.hashtags.slice(0, 3).join(' ') }}</div>
            <div class="flex items-center gap-1 mt-1">
              <span class="text-[9px] px-1.5 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500">{{ set.hashtags.length }} Tags</span>
              <span v-if="set.country" class="text-[9px] px-1.5 py-0.5 rounded-full bg-green-100 dark:bg-green-900/20 text-green-600 dark:text-green-400">{{ set.country }}</span>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Category legend -->
    <div class="flex flex-wrap gap-2 text-[10px]">
      <span v-for="(style, key) in CATEGORY_STYLES" :key="key" :class="['px-2 py-0.5 rounded-full border', style.bg, style.text, style.border]">
        {{ style.label }}
      </span>
    </div>
  </div>
</template>
