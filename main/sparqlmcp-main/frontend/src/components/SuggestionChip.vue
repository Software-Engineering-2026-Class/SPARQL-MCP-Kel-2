<!-- =============================================================
  SuggestionChip.vue — Pre-defined Search Suggestion Button
  Shown below the hero search bar on the Home page.
  ============================================================= -->
<template>
  <button
    :id="`chip-${chipId}`"
    class="suggestion-chip"
    type="button"
    :aria-label="`Search: ${label}`"
    @click="$emit('click', label)"
  >
    <!-- Clock icon -->
    <svg
      v-if="icon === 'clock'"
      class="chip-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6v6l4 2" />
    </svg>

    <!-- Network/users icon -->
    <svg
      v-else-if="icon === 'network'"
      class="chip-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      aria-hidden="true"
    >
      <circle cx="12" cy="5" r="2" />
      <circle cx="5"  cy="19" r="2" />
      <circle cx="19" cy="19" r="2" />
      <path d="M12 7v4M12 11l-5 6M12 11l5 6" />
    </svg>

    <!-- Layers/stack icon -->
    <svg
      v-else-if="icon === 'layers'"
      class="chip-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      aria-hidden="true"
    >
      <polygon points="12 2 22 8.5 12 15 2 8.5" />
      <polyline points="2 15.5 12 22 22 15.5" />
      <polyline points="2 12 12 18.5 22 12" />
    </svg>

    <span>{{ label }}</span>
  </button>
</template>

<script setup>
defineProps({
  chipId: { type: String, required: true },
  label:  { type: String, required: true },
  icon:   { type: String, default: 'clock' }
})

defineEmits(['click'])
</script>

<style scoped>
.suggestion-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.4rem 0.875rem;
  border-radius: 9999px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background-color: rgba(255, 255, 255, 0.06);
  color: #cbd5e1;
  font-family: 'Inter', sans-serif;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.15s, border-color 0.15s, color 0.15s;
}

.suggestion-chip:hover {
  background-color: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.3);
  color: #f0f4f8;
}

.chip-icon {
  width: 13px;
  height: 13px;
  flex-shrink: 0;
}
</style>
