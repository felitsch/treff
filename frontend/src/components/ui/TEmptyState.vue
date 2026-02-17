<script setup>
/**
 * TEmptyState.vue — TREFF Design System Empty State Component.
 *
 * Displays a centered placeholder when content is empty — e.g. empty lists,
 * no search results, first-time use states. Includes optional icon,
 * title, description, and call-to-action button or route link.
 *
 * Props:
 *   icon        (String)  — Heroicon name concept (rendered via slot or built-in icons)
 *   title       (String)  — Empty state headline
 *   description (String)  — Explanatory subtext
 *   actionLabel (String)  — CTA button text
 *   actionRoute (String|Object) — Vue Router link for the CTA
 *   compact     (Boolean) — Reduced padding for inline use
 *
 * Slots:
 *   icon    — Custom icon/illustration (replaces default icon)
 *   default — Additional content below description
 *   action  — Custom action area (replaces default button)
 *
 * Events:
 *   action — Emitted when action button is clicked (if no actionRoute)
 */
import { computed } from 'vue'

const props = defineProps({
  icon: {
    type: String,
    default: 'inbox',
    validator: (v) => ['inbox', 'search', 'document', 'photo', 'calendar', 'users', 'chart', 'video'].includes(v),
  },
  title: {
    type: String,
    default: '',
  },
  description: {
    type: String,
    default: '',
  },
  actionLabel: {
    type: String,
    default: '',
  },
  actionRoute: {
    type: [String, Object],
    default: null,
  },
  compact: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['action'])

function handleAction() {
  emit('action')
}

// Built-in SVG icon paths (Heroicon outlines)
const iconPaths = {
  inbox: 'M2.25 13.5a8.25 8.25 0 018.25-8.25.75.75 0 01.75.75v6.75H18a.75.75 0 01.75.75 8.25 8.25 0 01-16.5 0z M12.75 12.75a.75.75 0 00.75-.75V5.25a.75.75 0 00-.75-.75 8.25 8.25 0 00-8.25 8.25.75.75 0 00.75.75h7.5z',
  search: 'M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z',
  document: 'M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z',
  photo: 'M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0022.5 18.75V5.25A2.25 2.25 0 0020.25 3H3.75A2.25 2.25 0 001.5 5.25v13.5A2.25 2.25 0 003.75 21z',
  calendar: 'M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5',
  users: 'M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z',
  chart: 'M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z',
  video: 'm15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25z',
}
</script>

<template>
  <div
    :class="[
      'flex flex-col items-center justify-center text-center',
      compact ? 'py-8 px-4' : 'py-16 px-6',
    ]"
    data-testid="t-empty-state"
  >
    <!-- Icon / Illustration -->
    <div
      :class="[
        'flex items-center justify-center rounded-full mb-4',
        'bg-gray-100 dark:bg-gray-700/50',
        compact ? 'w-12 h-12' : 'w-16 h-16',
      ]"
    >
      <slot name="icon">
        <svg
          :class="[
            'text-gray-400 dark:text-gray-500',
            compact ? 'w-6 h-6' : 'w-8 h-8',
          ]"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            :d="iconPaths[icon] || iconPaths.inbox"
          />
        </svg>
      </slot>
    </div>

    <!-- Title -->
    <h3
      v-if="title"
      :class="[
        'font-semibold text-gray-900 dark:text-white',
        compact ? 'text-sm mb-1' : 'text-base mb-2',
      ]"
    >
      {{ title }}
    </h3>

    <!-- Description -->
    <p
      v-if="description"
      :class="[
        'text-gray-500 dark:text-gray-400 max-w-sm',
        compact ? 'text-xs' : 'text-sm',
      ]"
    >
      {{ description }}
    </p>

    <!-- Extra content slot -->
    <div v-if="$slots.default" class="mt-3">
      <slot />
    </div>

    <!-- Action -->
    <div v-if="actionLabel || $slots.action" :class="compact ? 'mt-3' : 'mt-6'">
      <slot name="action">
        <router-link
          v-if="actionRoute"
          :to="actionRoute"
          class="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
                 bg-primary-500 text-white hover:bg-primary-600
                 dark:bg-primary-400 dark:text-primary-950 dark:hover:bg-primary-300
                 transition-colors duration-200"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          {{ actionLabel }}
        </router-link>
        <button
          v-else
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
                 bg-primary-500 text-white hover:bg-primary-600
                 dark:bg-primary-400 dark:text-primary-950 dark:hover:bg-primary-300
                 transition-colors duration-200"
          @click="handleAction"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          {{ actionLabel }}
        </button>
      </slot>
    </div>
  </div>
</template>
