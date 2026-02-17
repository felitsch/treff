<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const toast = useToast()

const props = defineProps({
  selectedIntro: { type: Object, default: null },
  selectedOutro: { type: Object, default: null },
})

const emit = defineEmits(['update:selectedIntro', 'update:selectedOutro'])

// State
const templates = ref([])
const loading = ref(true)
const countryFilter = ref('')
const activeTab = ref('intro') // 'intro' | 'outro'

// Country info
const countries = {
  usa: { label: 'USA', flag: '🇺🇸', color: '#1B3A5C' },
  kanada: { label: 'Kanada', flag: '🇨🇦', color: '#C41E3A' },
  australien: { label: 'Australien', flag: '🇦🇺', color: '#00008B' },
  neuseeland: { label: 'Neuseeland', flag: '🇳🇿', color: '#00247D' },
  irland: { label: 'Irland', flag: '🇮🇪', color: '#169B62' },
}

// Computed
const filteredTemplates = computed(() => {
  let result = templates.value.filter(t => t.template_type === activeTab.value)
  if (countryFilter.value) {
    result = result.filter(t => t.country === countryFilter.value)
  }
  return result
})

const introCount = computed(() => templates.value.filter(t => t.template_type === 'intro').length)
const outroCount = computed(() => templates.value.filter(t => t.template_type === 'outro').length)

// Load templates
async function loadTemplates() {
  loading.value = true
  try {
    const { data } = await api.get('/api/video-templates')
    templates.value = data || []
  } catch (err) {
    console.error('Failed to load templates:', err)
  } finally {
    loading.value = false
  }
}

function selectTemplate(template) {
  if (template.template_type === 'intro') {
    const current = props.selectedIntro
    emit('update:selectedIntro', current?.id === template.id ? null : template)
  } else {
    const current = props.selectedOutro
    emit('update:selectedOutro', current?.id === template.id ? null : template)
  }
}

function isSelected(template) {
  if (template.template_type === 'intro') {
    return props.selectedIntro?.id === template.id
  }
  return props.selectedOutro?.id === template.id
}

onMounted(loadTemplates)
</script>

<template>
  <div class="space-y-4">
    <!-- Tab toggle -->
    <div class="flex gap-2">
      <button
        @click="activeTab = 'intro'"
        :class="[
          'px-4 py-2 rounded-lg text-sm font-medium transition-all',
          activeTab === 'intro'
            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200',
        ]"
      >
        Intro ({{ introCount }})
      </button>
      <button
        @click="activeTab = 'outro'"
        :class="[
          'px-4 py-2 rounded-lg text-sm font-medium transition-all',
          activeTab === 'outro'
            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200',
        ]"
      >
        Outro ({{ outroCount }})
      </button>
    </div>

    <!-- Country filter -->
    <div class="flex flex-wrap gap-2">
      <button
        @click="countryFilter = ''"
        :class="[
          'px-3 py-1.5 rounded-full text-xs font-medium transition-all',
          !countryFilter
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200',
        ]"
      >
        Alle
      </button>
      <button
        v-for="(info, key) in countries"
        :key="key"
        @click="countryFilter = countryFilter === key ? '' : key"
        :class="[
          'px-3 py-1.5 rounded-full text-xs font-medium transition-all',
          countryFilter === key
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200',
        ]"
      >
        {{ info.flag }} {{ info.label }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-8">
      <div class="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full" />
    </div>

    <!-- Templates grid -->
    <div v-else-if="filteredTemplates.length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <button
        v-for="tmpl in filteredTemplates"
        :key="tmpl.id"
        @click="selectTemplate(tmpl)"
        :class="[
          'relative text-left p-4 rounded-xl border-2 transition-all',
          isSelected(tmpl)
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 ring-2 ring-blue-300'
            : 'border-gray-200 dark:border-gray-700 hover:border-blue-300',
        ]"
        data-testid="branding-template-card"
      >
        <!-- Selection indicator -->
        <div v-if="isSelected(tmpl)" class="absolute top-2 right-2 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
          <span class="text-white text-xs">&#10003;</span>
        </div>

        <!-- Color preview bar -->
        <div class="flex gap-1 mb-3">
          <div
            class="h-2 flex-1 rounded-full"
            :style="{ backgroundColor: tmpl.primary_color || '#4C8BC2' }"
          />
          <div
            class="h-2 w-12 rounded-full"
            :style="{ backgroundColor: tmpl.secondary_color || '#FDD000' }"
          />
        </div>

        <!-- Template info -->
        <div class="flex items-start justify-between">
          <div>
            <h4 class="text-sm font-semibold text-gray-900 dark:text-white">{{ tmpl.name }}</h4>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {{ countries[tmpl.country]?.flag || '' }} {{ countries[tmpl.country]?.label || tmpl.country }}
              · {{ tmpl.duration_seconds }}s
              · {{ tmpl.style }}
            </p>
          </div>
          <span class="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
            {{ tmpl.template_type === 'intro' ? 'Intro' : 'Outro' }}
          </span>
        </div>

        <!-- CTA if present -->
        <p v-if="tmpl.cta_text" class="text-xs text-gray-500 mt-2 italic">"{{ tmpl.cta_text }}"</p>
      </button>
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-8 text-sm text-gray-500 dark:text-gray-400">
      <p>Keine {{ activeTab === 'intro' ? 'Intro' : 'Outro' }}-Templates gefunden.</p>
      <p class="text-xs mt-1">Erstelle Templates unter Video-Branding.</p>
    </div>

    <!-- Selection summary -->
    <div v-if="props.selectedIntro || props.selectedOutro" class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 space-y-2">
      <h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Ausgewaehlt</h4>
      <div v-if="props.selectedIntro" class="flex items-center gap-2 text-sm">
        <span class="text-green-500">&#10003;</span>
        <span class="text-gray-700 dark:text-gray-300">Intro: {{ props.selectedIntro.name }}</span>
        <button @click="emit('update:selectedIntro', null)" class="text-xs text-red-500 hover:text-red-700 ml-auto">Entfernen</button>
      </div>
      <div v-if="props.selectedOutro" class="flex items-center gap-2 text-sm">
        <span class="text-green-500">&#10003;</span>
        <span class="text-gray-700 dark:text-gray-300">Outro: {{ props.selectedOutro.name }}</span>
        <button @click="emit('update:selectedOutro', null)" class="text-xs text-red-500 hover:text-red-700 ml-auto">Entfernen</button>
      </div>
    </div>
  </div>
</template>
