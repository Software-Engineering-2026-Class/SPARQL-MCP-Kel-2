<!-- =============================================================
  App.vue — Root Application Component
  Provides router-view with page transition animations
  and the persistent star/network background canvas.
  ============================================================= -->
<template>
  <!-- Star background canvas (fixed, behind all content) -->
  <StarBackground />

  <!-- Router view with fade transition -->
  <router-view v-slot="{ Component }">
    <transition name="page" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<script setup>
import StarBackground from '@/components/StarBackground.vue'
</script>
