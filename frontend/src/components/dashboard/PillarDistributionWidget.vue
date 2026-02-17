<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/utils/api'
import AppIcon from '@/components/icons/AppIcon.vue'

const loading = ref(true)
const error = ref('')
const distribution = ref(null)

async function loadDistribution() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.get('/api/content-pillars/distribution/check')
    distribution.value = res.data
  } catch (e) {
    error.value = 'Pillar-Verteilung konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

onMounted(loadDistribution)

const hasWarnings = computed(() => distribution.value?.warnings?.length > 0)
const pillars = computed(() => distribution.value?.distribution || [])
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
        <AppIcon name="chart-bar" class="w-5 h-5" />
        Content-Pillar-Verteilung
      </h3>
      <button
        v-if="!loading"
        @click="loadDistribution"
        class="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        title="Aktualisieren"
      >
        ↻
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-2">
      <div v-for="i in 4" :key="i" class="h-6 bg-gray-100 dark:bg-gray-700 rounded animate-pulse"></div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-xs text-red-500 dark:text-red-400">{{ error }}</div>

    <!-- Data -->
    <div v-else-if="distribution">
      <!-- Warnings -->
      <div v-if="hasWarnings" class="mb-3 p-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
        <div class="text-xs font-medium text-amber-700 dark:text-amber-300 mb-1 flex items-center gap-1">
          <AppIcon name="exclamation-triangle" class="w-4 h-4 inline text-amber-600 dark:text-amber-400" /> Verteilungs-Hinweise
        </div>
        <ul class="text-xs text-amber-600 dark:text-amber-400 space-y-0.5">
          <li v-for="(w, i) in distribution.warnings.slice(0, 3)" :key="i">{{ w }}</li>
        </ul>
      </div>

      <!-- Pillar bars -->
      <div class="space-y-2">
        <div v-for="p in pillars" :key="p.pillar_id" class="group">
          <div class="flex items-center justify-between text-xs mb-0.5">
            <span class="text-gray-700 dark:text-gray-300 truncate flex items-center gap-1">
              <AppIcon :name="p.icon" class="w-4 h-4 inline-block" />
              <span class="truncate">{{ p.name }}</span>
            </span>
            <span class="flex items-center gap-1 text-gray-500 dark:text-gray-400 flex-shrink-0 ml-2">
              <span :class="{
                'text-red-500 dark:text-red-400 font-medium': p.status === 'critical',
                'text-amber-500 dark:text-amber-400 font-medium': p.status === 'warning',
                'text-green-600 dark:text-green-400': p.status === 'ok',
              }">{{ p.actual_percentage }}%</span>
              <span class="text-gray-400 dark:text-gray-500">/</span>
              <span>{{ p.target_percentage }}%</span>
            </span>
          </div>
          <!-- Progress bar -->
          <div class="relative h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
            <!-- Target marker -->
            <div
              class="absolute top-0 bottom-0 w-0.5 bg-gray-400 dark:bg-gray-500 z-10"
              :style="{ left: Math.min(p.target_percentage, 100) + '%' }"
              :title="'Ziel: ' + p.target_percentage + '%'"
            ></div>
            <!-- Actual bar -->
            <div
              class="h-full rounded-full transition-all duration-500"
              :style="{ width: Math.min(p.actual_percentage, 100) + '%', backgroundColor: p.color }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Total info -->
      <div class="mt-3 pt-2 border-t border-gray-100 dark:border-gray-700 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
        <span>{{ distribution.total_posts }} Posts gesamt</span>
        <span v-if="distribution.unassigned_count > 0" class="text-amber-500">
          {{ distribution.unassigned_count }} ohne Pillar
        </span>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="text-xs text-gray-500 dark:text-gray-400 text-center py-4">
      Keine Daten verfuegbar.
    </div>
  </div>
</template>
