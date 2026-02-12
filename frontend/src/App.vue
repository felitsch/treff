<script setup>
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ToastContainer from '@/components/common/ToastContainer.vue'

const auth = useAuthStore()
</script>

<template>
  <RouterView />
  <ToastContainer />
</template>
