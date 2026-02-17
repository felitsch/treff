<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      enabled: false,
      name: '',
      title: '',
      fontFamily: 'Inter',
      fontSize: 24,
      textColor: '#FFFFFF',
      bgColor: '#1A1A2E',
      bgOpacity: 0.85,
      position: 'bottom-left', // bottom-left, bottom-center, bottom-right
      animation: 'slide_in_left',
      startTime: 0,
      endTime: 0, // 0 = full duration
    }),
  },
})

const emit = defineEmits(['update:modelValue'])

// Local reactive copy
const config = ref({ ...props.modelValue })

watch(() => props.modelValue, (val) => {
  config.value = { ...val }
}, { deep: true })

function update(key, value) {
  config.value[key] = value
  emit('update:modelValue', { ...config.value })
}

const fontOptions = [
  { value: 'Inter', label: 'Inter' },
  { value: 'Helvetica', label: 'Helvetica' },
  { value: 'Georgia', label: 'Georgia' },
  { value: 'monospace', label: 'Monospace' },
]

const positionOptions = [
  { value: 'bottom-left', label: 'Links unten', icon: '↙️' },
  { value: 'bottom-center', label: 'Mitte unten', icon: '⬇️' },
  { value: 'bottom-right', label: 'Rechts unten', icon: '↘️' },
]

const animationOptions = [
  { value: 'none', label: 'Keine' },
  { value: 'fade_in', label: 'Einblenden' },
  { value: 'slide_in_left', label: 'Links einfahren' },
  { value: 'slide_in_bottom', label: 'Unten einfahren' },
  { value: 'pop_in', label: 'Pop-In' },
]

// Preview style
const previewStyle = computed(() => {
  const pos = config.value.position
  const align = pos === 'bottom-left' ? 'left' : pos === 'bottom-right' ? 'right' : 'center'
  const bgRgba = hexToRgba(config.value.bgColor, config.value.bgOpacity)
  return {
    textAlign: align,
    backgroundColor: bgRgba,
    color: config.value.textColor,
    fontFamily: config.value.fontFamily,
    fontSize: `${Math.max(10, config.value.fontSize * 0.6)}px`,
    padding: '8px 16px',
    borderRadius: '6px',
  }
})

function hexToRgba(hex, opacity) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${opacity})`
}
</script>

<template>
  <div class="space-y-4">
    <!-- Enable toggle -->
    <div class="flex items-center justify-between">
      <label class="text-sm font-medium text-gray-700 dark:text-gray-300">Lower Third aktivieren</label>
      <button
        @click="update('enabled', !config.enabled)"
        :class="[
          'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
          config.enabled ? 'bg-blue-500' : 'bg-gray-300 dark:bg-gray-600',
        ]"
      >
        <span
          :class="[
            'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
            config.enabled ? 'translate-x-6' : 'translate-x-1',
          ]"
        />
      </button>
    </div>

    <div v-if="config.enabled" class="space-y-4">
      <!-- Live Preview -->
      <div class="bg-gray-900 rounded-lg p-4" data-testid="lower-third-preview">
        <p class="text-xs text-gray-500 mb-2">Vorschau:</p>
        <div class="relative aspect-video bg-gray-800 rounded-lg overflow-hidden flex items-end">
          <div class="w-full p-3">
            <div :style="previewStyle" class="inline-block max-w-[80%]">
              <p class="font-bold" :style="{ fontSize: `${Math.max(10, config.fontSize * 0.6)}px` }">
                {{ config.name || 'Name' }}
              </p>
              <p v-if="config.title" class="opacity-80" :style="{ fontSize: `${Math.max(8, config.fontSize * 0.45)}px` }">
                {{ config.title }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Text fields -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Name</label>
          <input
            :value="config.name"
            @input="update('name', $event.target.value)"
            type="text"
            placeholder="z.B. Max Mustermann"
            class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Titel / Untertitel</label>
          <input
            :value="config.title"
            @input="update('title', $event.target.value)"
            type="text"
            placeholder="z.B. Austauschschueler USA"
            class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      <!-- Font & Size -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Schriftart</label>
          <select
            :value="config.fontFamily"
            @change="update('fontFamily', $event.target.value)"
            class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            <option v-for="f in fontOptions" :key="f.value" :value="f.value">{{ f.label }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Schriftgroesse ({{ config.fontSize }}px)</label>
          <input
            :value="config.fontSize"
            @input="update('fontSize', parseInt($event.target.value) || 24)"
            type="range"
            min="12"
            max="48"
            class="w-full accent-blue-500"
          />
        </div>
      </div>

      <!-- Colors -->
      <div class="grid grid-cols-3 gap-3">
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Textfarbe</label>
          <div class="flex items-center gap-2">
            <input
              :value="config.textColor"
              @input="update('textColor', $event.target.value)"
              type="color"
              class="w-8 h-8 rounded cursor-pointer border-0"
            />
            <span class="text-xs text-gray-500">{{ config.textColor }}</span>
          </div>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Hintergrund</label>
          <div class="flex items-center gap-2">
            <input
              :value="config.bgColor"
              @input="update('bgColor', $event.target.value)"
              type="color"
              class="w-8 h-8 rounded cursor-pointer border-0"
            />
            <span class="text-xs text-gray-500">{{ config.bgColor }}</span>
          </div>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Deckkraft ({{ Math.round(config.bgOpacity * 100) }}%)</label>
          <input
            :value="config.bgOpacity"
            @input="update('bgOpacity', parseFloat($event.target.value))"
            type="range"
            min="0"
            max="1"
            step="0.05"
            class="w-full accent-blue-500"
          />
        </div>
      </div>

      <!-- Position -->
      <div>
        <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Position</label>
        <div class="flex gap-2">
          <button
            v-for="pos in positionOptions"
            :key="pos.value"
            @click="update('position', pos.value)"
            :class="[
              'flex-1 px-3 py-2 rounded-lg text-xs font-medium text-center transition-all',
              config.position === pos.value
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 ring-1 ring-blue-300'
                : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200',
            ]"
          >
            {{ pos.icon }} {{ pos.label }}
          </button>
        </div>
      </div>

      <!-- Animation -->
      <div>
        <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Animation</label>
        <select
          :value="config.animation"
          @change="update('animation', $event.target.value)"
          class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option v-for="a in animationOptions" :key="a.value" :value="a.value">{{ a.label }}</option>
        </select>
      </div>
    </div>
  </div>
</template>
