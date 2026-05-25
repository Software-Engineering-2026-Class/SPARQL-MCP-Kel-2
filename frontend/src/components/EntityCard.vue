<!-- =============================================================
  EntityCard.vue — Cybersecurity Entity Display Card
  Reusable card for malware, vulnerabilities, and other
  cybersecurity entities returned from the SPARQL query.
  ============================================================= -->
<template>
  <article
    :id="`entity-card-${entity.id}`"
    class="entity-card"
    :class="`entity-card--${entity.type}`"
    role="article"
    :aria-label="`${entity.title} entity card`"
  >
    <!-- Card Header: title + badge -->
    <div class="card-header">
      <div class="card-title-group">
        <h2 class="card-title">{{ entity.title }}</h2>
        <p class="card-subtitle">{{ entity.subtitle }}</p>
      </div>

      <!-- Badge: Active Threat -->
      <span
        v-if="entity.badge.variant === 'danger'"
        class="badge badge-danger"
        role="status"
        :aria-label="entity.badge.label"
      >
        {{ entity.badge.label }}
      </span>

      <!-- Badge: CVSS score -->
      <span
        v-else-if="entity.badge.variant === 'cvss'"
        class="badge badge-cvss"
        role="status"
        :aria-label="`CVSS Score: ${entity.badge.score}`"
      >
        <span class="cvss-label">CVSS</span>
        <span class="cvss-score" :class="cvssColorClass">{{ entity.badge.score }}</span>
      </span>
    </div>

    <!-- Divider -->
    <hr class="card-divider" />

    <!-- Fields grid -->
    <div
      v-if="simpleFields.length"
      class="card-fields"
    >
      <div
        v-for="field in simpleFields"
        :key="field.label"
        class="card-field"
      >
        <dt class="field-label">{{ field.label }}</dt>
        <dd class="field-value">{{ field.value }}</dd>
      </div>
    </div>

    <!-- Description paragraph (for exploit status etc.) -->
    <div v-if="entity.description" class="card-description-block">
      <dt class="field-label">{{ descriptionFieldLabel }}</dt>
      <dd class="card-description">{{ entity.description }}</dd>
    </div>

    <!-- Aliases / Tags -->
    <div v-if="entity.tags && entity.tags.length" class="card-tags-block">
      <span class="field-label">Aliases / Tags</span>
      <div class="card-tags">
        <span
          v-for="tag in entity.tags"
          :key="tag"
          class="tag-chip"
        >
          {{ tag }}
        </span>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** Entity data object from mockData.js */
  entity: {
    type: Object,
    required: true
  }
})

/**
 * Fields that have a plain string value (not null/description).
 */
const simpleFields = computed(() =>
  props.entity.fields.filter(f => f.value !== null)
)

/**
 * Label for the description field (last field with null value).
 */
const descriptionFieldLabel = computed(() => {
  const f = props.entity.fields.find(f => f.value === null)
  return f ? f.label : 'Description'
})

/**
 * CVSS color: red >= 7, orange >= 4, green < 4
 */
const cvssColorClass = computed(() => {
  const score = props.entity.badge?.score ?? 0
  if (score >= 7)  return 'cvss-high'
  if (score >= 4)  return 'cvss-medium'
  return 'cvss-low'
})
</script>

<style scoped>
/* Card root */
.entity-card {
  background-color: #0e1c2f;
  border: 1px solid #1e3554;
  border-radius: 0.5rem;
  padding: 1.125rem 1.25rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
  transition: border-color 0.2s ease;
}

.entity-card:hover {
  border-color: rgba(56, 189, 248, 0.25);
}

/* Card header row */
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.card-title-group {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-size: 1rem;
  font-weight: 700;
  color: #f0f4f8;
  letter-spacing: -0.01em;
  margin: 0;
  line-height: 1.3;
}

.card-subtitle {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.125rem;
  margin-bottom: 0;
}

/* Badges */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}

.badge-danger {
  background-color: rgba(248, 113, 113, 0.12);
  border: 1px solid rgba(248, 113, 113, 0.3);
  color: #f87171;
}

.badge-cvss {
  background-color: rgba(15, 23, 42, 0.8);
  border: 1px solid #334155;
  color: #94a3b8;
}

.cvss-label {
  color: #64748b;
  font-size: 0.6875rem;
}

.cvss-score {
  font-weight: 700;
  font-size: 0.875rem;
}

.cvss-high   { color: #f87171; }
.cvss-medium { color: #fbbf24; }
.cvss-low    { color: #34d399; }

/* Divider */
.card-divider {
  border: none;
  border-top: 1px solid #1e3554;
  margin: 0.75rem 0;
}

/* Fields */
.card-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.card-field {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.field-label {
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #475569;
  margin-bottom: 0.25rem;
}

.field-value {
  font-size: 0.875rem;
  color: #cbd5e1;
  margin: 0;
}

/* Description block */
.card-description-block {
  margin-bottom: 0.75rem;
}

.card-description {
  font-size: 0.8125rem;
  color: #94a3b8;
  line-height: 1.6;
  margin: 0;
  margin-top: 0.35rem;
}

/* Tags block */
.card-tags-block {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.tag-chip {
  display: inline-block;
  padding: 0.2rem 0.625rem;
  border-radius: 9999px;
  border: 1px solid #1e3554;
  background-color: rgba(30, 53, 84, 0.4);
  font-size: 0.75rem;
  color: #94a3b8;
}
</style>
