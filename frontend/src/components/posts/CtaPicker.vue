<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/utils/api'

const props = defineProps({
  modelValue: { type: String, default: '' },
  category: { type: String, default: '' },
  platform: { type: String, default: '' },
  topic: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'cta-selected'])

// CTA library data
const allCtas = ref([])
const suggestedCtas = ref([])
const loading = ref(false)
const showDropdown = ref(false)
const selectedCategory = ref('')

// Category labels (German)
const categoryLabels = {
  engagement: 'Engagement',
  conversion: 'Conversion',
  awareness: 'Awareness',
  traffic: 'Traffic',
}

const categoryColors = {
  engagement: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300',
  conversion: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  awareness: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  traffic: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
}

// Filter CTAs by selected category
const filteredCtas = computed(() => {
  if (!selectedCategory.value) return allCtas.value
  return allCtas.value.filter(c => c.category === selectedCategory.value)
})

// Load all CTAs on mount
onMounted(async () => {
  await loadCtas()
  await loadSuggestions()
})

// Re-fetch suggestions when context changes
watch(() => [props.category, props.platform], () => {
  loadSuggestions()
})

async function loadCtas() {
  try {
    loading.value = true
    const res = await api.get('/api/ctas')
    allCtas.value = res.data.ctas || []
  } catch (e) {
    console.warn('Failed to load CTAs:', e)
  } finally {
    loading.value = false
  }
}

async function loadSuggestions() {
  try {
    const res = await api.post('/api/ctas/suggest', {
      category: props.category,
      platform: props.platform,
      topic: props.topic,
    })
    suggestedCtas.value = res.data.suggestions || []
  } catch (e) {
    console.warn('Failed to load CTA suggestions:', e)
  }
}

async function selectCta(cta) {
  emit('update:modelValue', cta.text)
  emit('cta-selected', cta)
  showDropdown.value = false

  // Track usage
  try {
    await api.post(`/api/ctas/${cta.id}/use`)
  } catch (e) {
    // Non-critical, ignore
  }
}

function toggleDropdown() {
  showDropdown.value = !showDropdown.value
}

function closeDropdown() {
  showDropdown.value = false
}
</script>

<template>
  <div class="relative" data-testid="cta-picker">
    <!-- CTA Input with Picker Toggle -->
    <div class="flex items-center gap-2">
      <input
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        placeholder="CTA eingeben oder aus Bibliothek waehlen..."
        class="flex-1 px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-[#3B7AB1] focus:border-transparent"
        :class="(modelValue?.length || 0) > 25 ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white' : (modelValue?.length || 0) > 20 ? 'border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-gray-900 dark:text-white' : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white'"
        data-testid="cta-input"
      />
      <button
        @click="toggleDropdown"
        class="px-3 py-2 rounded-lg border text-sm font-medium transition-colors"
        :class="showDropdown ? 'bg-[#3B7AB1] text-white border-[#3B7AB1]' : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'"
        title="CTA-Bibliothek oeffnen"
        data-testid="cta-picker-toggle"
      >
        <span>&#x1F4DA;</span>
      </button>
    </div>

    <!-- Character Count -->
    <div class="flex items-center justify-between mt-0.5">
      <span v-if="(modelValue?.length || 0) > 25" class="text-xs text-red-500 dark:text-red-400">Text kann den Template-Bereich ueberlaufen</span>
      <span v-else-if="(modelValue?.length || 0) > 20" class="text-xs text-amber-500 dark:text-amber-400">Nahe am Zeichenlimit</span>
      <span v-else class="text-xs text-gray-400"></span>
      <span class="text-xs" :class="(modelValue?.length || 0) > 25 ? 'text-red-500 dark:text-red-400 font-semibold' : (modelValue?.length || 0) > 20 ? 'text-amber-500 dark:text-amber-400' : 'text-gray-400'">{{ modelValue?.length || 0 }}/25</span>
    </div>

    <!-- Dropdown Panel -->
    <div
      v-if="showDropdown"
      class="absolute z-50 mt-2 w-full bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-xl max-h-80 overflow-hidden"
      data-testid="cta-dropdown"
    >
      <!-- Suggested CTAs -->
      <div v-if="suggestedCtas.length > 0" class="p-3 border-b border-gray-200 dark:border-gray-700">
        <div class="text-xs font-semibold text-[#3B7AB1] mb-2 flex items-center gap-1">
          <span>&#x2728;</span> Vorgeschlagene CTAs
        </div>
        <div class="space-y-1">
          <button
            v-for="cta in suggestedCtas.slice(0, 3)"
            :key="'s-' + cta.id"
            @click="selectCta(cta)"
            class="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-[#3B7AB1]/10 dark:hover:bg-[#3B7AB1]/20 transition-colors flex items-center gap-2 group"
            data-testid="cta-suggestion"
          >
            <span v-if="cta.emoji" class="text-base">{{ cta.emoji }}</span>
            <span class="flex-1 text-gray-800 dark:text-gray-200 group-hover:text-[#3B7AB1]">{{ cta.text }}</span>
            <span :class="categoryColors[cta.category]" class="text-[10px] px-1.5 py-0.5 rounded-full font-medium">{{ categoryLabels[cta.category] }}</span>
          </button>
        </div>
      </div>

      <!-- Category Filter Tabs -->
      <div class="px-3 pt-3 pb-2 flex gap-1.5 flex-wrap border-b border-gray-100 dark:border-gray-700">
        <button
          @click="selectedCategory = ''"
          class="px-2.5 py-1 rounded-full text-xs font-medium transition-colors"
          :class="!selectedCategory ? 'bg-[#3B7AB1] text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'"
        >Alle</button>
        <button
          v-for="(label, key) in categoryLabels"
          :key="key"
          @click="selectedCategory = key"
          class="px-2.5 py-1 rounded-full text-xs font-medium transition-colors"
          :class="selectedCategory === key ? 'bg-[#3B7AB1] text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'"
          :data-testid="'cta-filter-' + key"
        >{{ label }}</button>
      </div>

      <!-- CTA List -->
      <div class="overflow-y-auto max-h-44 p-2">
        <div v-if="loading" class="text-center py-4 text-sm text-gray-400">Lade CTAs...</div>
        <div v-else-if="filteredCtas.length === 0" class="text-center py-4 text-sm text-gray-400">Keine CTAs gefunden</div>
        <button
          v-for="cta in filteredCtas"
          :key="cta.id"
          @click="selectCta(cta)"
          class="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors flex items-center gap-2 group"
          data-testid="cta-library-item"
        >
          <span v-if="cta.emoji" class="text-base">{{ cta.emoji }}</span>
          <span class="flex-1 text-gray-700 dark:text-gray-300 group-hover:text-[#3B7AB1]">{{ cta.text }}</span>
          <span :class="categoryColors[cta.category]" class="text-[10px] px-1.5 py-0.5 rounded-full font-medium shrink-0">{{ categoryLabels[cta.category] }}</span>
          <span v-if="cta.usage_count > 0" class="text-[10px] text-gray-400 shrink-0">{{ cta.usage_count }}x</span>
        </button>
      </div>

      <!-- Close button -->
      <div class="p-2 border-t border-gray-100 dark:border-gray-700">
        <button
          @click="closeDropdown"
          class="w-full text-center text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 py-1"
        >Schliessen</button>
      </div>
    </div>

    <!-- Overlay to close dropdown on outside click -->
    <div v-if="showDropdown" class="fixed inset-0 z-40" @click="closeDropdown"></div>
  </div>
</template>
