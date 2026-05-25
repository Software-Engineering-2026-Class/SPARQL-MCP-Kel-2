<!-- =============================================================
  DocumentationCard.vue — Feature explanation card
  Used for side-by-side result type explanations on the
  Documentation page.
  ============================================================= -->
<template>
  <div class="doc-card">
    <!-- Icon area -->
    <div class="doc-card-icon" aria-hidden="true">
      <slot name="icon" />
    </div>

    <!-- Content -->
    <div class="doc-card-body">
      <h3 class="doc-card-title">{{ title }}</h3>
      <p class="doc-card-desc">{{ description }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title:       { type: String, required: true },
  description: { type: String, required: true }
})
</script>

<style scoped>
.doc-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.375rem 1.375rem 1.5rem;
  background-color: #0e1c2f;
  border: 1px solid #1e3554;
  border-radius: 0.5rem;
  transition: border-color 0.2s, transform 0.2s;
}

.doc-card:hover {
  border-color: rgba(56, 189, 248, 0.25);
  transform: translateY(-2px);
}

/* Icon circle */
.doc-card-icon {
  width: 40px;
  height: 40px;
  border-radius: 0.375rem;
  background-color: rgba(56, 189, 248, 0.07);
  border: 1px solid rgba(56, 189, 248, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #38bdf8;
  flex-shrink: 0;
}

.doc-card-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #f0f4f8;
  margin: 0 0 0.5rem;
  letter-spacing: -0.01em;
}

.doc-card-desc {
  font-size: 0.875rem;
  color: #94a3b8;
  line-height: 1.7;
  margin: 0;
}
</style>
