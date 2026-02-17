<script setup>
// StudentsHubView - wrapper for the students section with nested routes
// This view acts as a simple pass-through for its child routes
</script>

<template>
  <router-view v-slot="{ Component, route: childRoute }">
    <Transition name="page-slide" mode="out-in">
      <div :key="childRoute.path">
        <component :is="Component" />
      </div>
    </Transition>
  </router-view>
</template>
