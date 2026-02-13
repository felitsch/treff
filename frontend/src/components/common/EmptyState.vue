<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const props = defineProps({
  icon: { type: String, default: '📭' },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  actionLabel: { type: String, default: '' },
  actionTo: { type: String, default: '' },
  secondaryLabel: { type: String, default: '' },
  secondaryTo: { type: String, default: '' },
  compact: { type: Boolean, default: false },
})

const emit = defineEmits(['action', 'secondary'])

function handleAction() {
  if (props.actionTo) {
    router.push(props.actionTo)
  } else {
    emit('action')
  }
}

function handleSecondary() {
  if (props.secondaryTo) {
    router.push(props.secondaryTo)
  } else {
    emit('secondary')
  }
}
</script>

<template>
  <div
    :class="[
      'text-center bg-white dark:bg-gray-800 rounded-xl border border-dashed border-gray-300 dark:border-gray-600',
      compact ? 'py-8 px-4' : 'py-14 px-6'
    ]"
    data-testid="empty-state"
  >
    <!-- Icon -->
    <div :class="compact ? 'text-4xl mb-2' : 'text-5xl mb-4'">{{ icon }}</div>

    <!-- Title -->
    <h3 :class="[
      'font-semibold text-gray-900 dark:text-white',
      compact ? 'text-base mb-1' : 'text-lg mb-2'
    ]">
      {{ title }}
    </h3>

    <!-- Description -->
    <p v-if="description" :class="[
      'text-gray-500 dark:text-gray-400 max-w-md mx-auto',
      compact ? 'text-xs mb-3' : 'text-sm mb-6'
    ]">
      {{ description }}
    </p>

    <!-- Actions -->
    <div v-if="actionLabel || secondaryLabel" class="flex items-center justify-center gap-3 flex-wrap">
      <!-- Primary Action -->
      <button
        v-if="actionLabel"
        @click="handleAction"
        :class="[
          'inline-flex items-center gap-2 font-medium rounded-lg transition-colors',
          compact
            ? 'px-4 py-2 text-xs bg-[#3B7AB1] text-white hover:bg-[#2E6A9E]'
            : 'px-5 py-2.5 text-sm bg-[#3B7AB1] text-white hover:bg-[#2E6A9E]'
        ]"
        data-testid="empty-state-action"
      >
        {{ actionLabel }}
      </button>

      <!-- Secondary Action -->
      <button
        v-if="secondaryLabel"
        @click="handleSecondary"
        :class="[
          'inline-flex items-center gap-2 font-medium rounded-lg transition-colors border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700',
          compact ? 'px-4 py-2 text-xs' : 'px-5 py-2.5 text-sm'
        ]"
        data-testid="empty-state-secondary"
      >
        {{ secondaryLabel }}
      </button>
    </div>
  </div>
</template>
