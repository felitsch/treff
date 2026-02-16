<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

/**
 * Breadcrumb items from route meta.
 * Each item: { label: string, path: string }
 * The last item is the current page and is not clickable.
 */
const breadcrumbs = computed(() => {
  const meta = route.meta?.breadcrumb
  if (!meta || !Array.isArray(meta) || meta.length === 0) return []
  return meta
})

const isLast = (index) => index === breadcrumbs.value.length - 1
</script>

<template>
  <nav
    v-if="breadcrumbs.length > 1"
    aria-label="Breadcrumb"
    class="flex items-center px-6 py-2 text-sm bg-gray-50 border-b border-gray-200 dark:bg-gray-900/50 dark:border-gray-700"
    data-testid="breadcrumb-nav"
  >
    <ol class="flex items-center gap-1.5">
      <li
        v-for="(crumb, index) in breadcrumbs"
        :key="crumb.path || index"
        class="flex items-center gap-1.5"
      >
        <!-- Separator (chevron) before all items except the first -->
        <svg
          v-if="index > 0"
          class="h-3.5 w-3.5 flex-shrink-0 text-gray-400 dark:text-gray-500"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd" />
        </svg>

        <!-- Last item: plain text (current page) -->
        <span
          v-if="isLast(index)"
          class="font-medium text-gray-700 dark:text-gray-200"
          :aria-current="'page'"
        >
          {{ crumb.label }}
        </span>

        <!-- Other items: clickable links -->
        <router-link
          v-else
          :to="crumb.path"
          class="text-gray-500 hover:text-treff-blue dark:text-gray-400 dark:hover:text-treff-blue-300 transition-colors"
        >
          {{ crumb.label }}
        </router-link>
      </li>
    </ol>
  </nav>
</template>
