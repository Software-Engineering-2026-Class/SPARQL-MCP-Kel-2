<!-- =============================================================
  SectionHeader.vue — Reusable section title + optional subtitle
  Used on About and Documentation pages.
  ============================================================= -->
<template>
  <div class="section-header" :class="{ 'section-header--center': center }">
    <!-- Optional eyebrow label -->
    <span v-if="eyebrow" class="section-eyebrow">{{ eyebrow }}</span>

    <!-- Section title -->
    <h2 class="section-title">{{ title }}</h2>

    <!-- Optional description -->
    <p v-if="description" class="section-desc">{{ description }}</p>
  </div>
</template>

<script setup>
defineProps({
  /** Main heading text */
  title: { type: String, required: true },
  /** Small label shown above the title */
  eyebrow: { type: String, default: null },
  /** Paragraph below the title */
  description: { type: String, default: null },
  /** Center-align the content */
  center: { type: Boolean, default: false }
})
</script>

<style scoped>
.section-header {
  margin-bottom: 1.75rem;
}

.section-header--center {
  text-align: center;
}

.section-eyebrow {
  display: inline-block;
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #38bdf8;
  margin-bottom: 0.5rem;
}

.section-title {
  font-size: 1.375rem;
  font-weight: 700;
  color: #f0f4f8;
  letter-spacing: -0.02em;
  line-height: 1.25;
  margin: 0;
}

.section-desc {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #64748b;
  line-height: 1.6;
  max-width: 56ch;
}

.section-header--center .section-desc {
  margin-left: auto;
  margin-right: auto;
}
</style>
