<!-- =============================================================
  InfoPanel.vue — Styled text panel / information block
  Matches the card-surface design system.
  ============================================================= -->
<template>
  <div class="info-panel" :class="accentClass">
    <!-- Optional icon slot -->
    <div v-if="$slots.icon" class="panel-icon-wrap" aria-hidden="true">
      <slot name="icon" />
    </div>

    <div class="panel-body">
      <!-- Optional title -->
      <h3 v-if="title" class="panel-title">{{ title }}</h3>

      <!-- Default slot for content -->
      <div class="panel-content">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** Panel heading */
  title: { type: String, default: null },
  /** Left border accent color: 'cyan' | 'blue' | 'none' */
  accent: { type: String, default: 'none' }
})

const accentClass = computed(() => ({
  'panel--accent-cyan': props.accent === 'cyan',
  'panel--accent-blue': props.accent === 'blue'
}))
</script>

<style scoped>
.info-panel {
  background-color: #0e1c2f;
  border: 1px solid #1e3554;
  border-radius: 0.5rem;
  padding: 1.375rem 1.5rem;
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  transition: border-color 0.2s;
}

.info-panel:hover {
  border-color: rgba(56, 189, 248, 0.2);
}

/* Accent left-border variants */
.panel--accent-cyan {
  border-left: 3px solid #38bdf8;
}

.panel--accent-blue {
  border-left: 3px solid #60a5fa;
}

/* Icon wrapper */
.panel-icon-wrap {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(56, 189, 248, 0.08);
  border-radius: 0.375rem;
  color: #38bdf8;
}

.panel-body {
  flex: 1;
  min-width: 0;
}

.panel-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #f0f4f8;
  margin: 0 0 0.5rem;
  letter-spacing: -0.01em;
}

.panel-content {
  font-size: 0.875rem;
  color: #94a3b8;
  line-height: 1.7;
}

/* Typography inside content slot */
.panel-content :deep(p) {
  margin-bottom: 0.625rem;
}

.panel-content :deep(p:last-child) {
  margin-bottom: 0;
}
</style>
