<!-- =============================================================
  SearchBar.vue — Natural Language Query Input
  Used on both HomeView (hero) and ResultsView (compact header).
  Emits 'search' event with the query string.
  ============================================================= -->
<template>
  <form
    class="searchbar-form"
    :class="{ 'searchbar-compact': compact }"
    role="search"
    aria-label="Cybersecurity search"
    @submit.prevent="handleSubmit"
  >
    <!-- Search icon (left) -->
    <span class="searchbar-icon" aria-hidden="true">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        class="w-4 h-4"
      >
        <circle cx="11" cy="11" r="8" />
        <path d="M21 21l-4.35-4.35" />
      </svg>
    </span>

    <!-- Text input -->
    <input
      id="search-input"
      ref="inputRef"
      v-model="localQuery"
      type="search"
      class="searchbar-input"
      :placeholder="placeholder"
      autocomplete="off"
      autocorrect="off"
      spellcheck="false"
      aria-label="Search query"
      @keydown.enter.prevent="handleSubmit"
    />

    <!-- Submit button (right) -->
    <button
      id="search-submit"
      type="submit"
      class="searchbar-btn"
      :disabled="!localQuery.trim() || isLoading"
      aria-label="Submit search"
    >
      <!-- Loading spinner -->
      <svg
        v-if="isLoading"
        class="w-4 h-4 animate-spin"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
      >
        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
      </svg>

      <!-- Arrow icon -->
      <svg
        v-else
        class="w-4 h-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
      >
        <path d="M5 12h14M12 5l7 7-7 7" />
      </svg>
    </button>
  </form>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useSearchStore } from '@/stores/searchStore.js'

// ── Props & Emits ────────────────────────────────────────────
const props = defineProps({
  /** Initial value to pre-fill the input */
  modelValue: {
    type: String,
    default: ''
  },
  /** Compact mode for the results header */
  compact: {
    type: Boolean,
    default: false
  },
  /** Placeholder text */
  placeholder: {
    type: String,
    default: 'Search for vulnerabilities, malware, or threats using natural language...'
  }
})

const emit = defineEmits(['search', 'update:modelValue'])

// ── State ────────────────────────────────────────────────────
const store      = useSearchStore()
const inputRef   = ref(null)
const localQuery = ref(props.modelValue)

// Sync when parent updates modelValue
watch(() => props.modelValue, (val) => {
  localQuery.value = val
})

// Expose loading state from store
const isLoading = computed(() => store.isLoading)

// ── Handlers ─────────────────────────────────────────────────
function handleSubmit() {
  const q = localQuery.value.trim()
  if (!q || store.isLoading) return
  emit('update:modelValue', q)
  emit('search', q)
}

// ── Utils ─────────────────────────────────────────────────────
function focus() {
  inputRef.value?.focus()
}

defineExpose({ focus })

import { computed } from 'vue'
</script>

<style scoped>
/* Form wrapper */
.searchbar-form {
  display: flex;
  align-items: center;
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
  background-color: #ffffff;
  border-radius: 9999px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  transition: box-shadow 0.2s ease;
}

.searchbar-form:focus-within {
  box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
  border-color: rgba(56, 189, 248, 0.5);
}

/* Compact variant (inside header) */
.searchbar-compact {
  max-width: 100%;
  border-radius: 9999px;
  background-color: rgba(255, 255, 255, 0.96);
}

/* Left search icon */
.searchbar-icon {
  display: flex;
  align-items: center;
  padding: 0 0.75rem 0 1rem;
  color: #94a3b8;
  flex-shrink: 0;
}

/* Input field */
.searchbar-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-family: 'Inter', sans-serif;
  font-size: 0.9375rem;
  color: #1e293b;
  padding: 0.75rem 0.5rem;
  min-width: 0;
}

.searchbar-compact .searchbar-input {
  padding: 0.5rem 0.25rem;
  font-size: 0.875rem;
}

.searchbar-input::placeholder {
  color: #94a3b8;
}

/* Clear default search input appearance */
.searchbar-input::-webkit-search-cancel-button {
  display: none;
}

/* Submit button */
.searchbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  margin: 5px 6px;
  border-radius: 50%;
  background-color: #0f172a;
  color: #ffffff;
  border: none;
  cursor: pointer;
  flex-shrink: 0;
  transition: background-color 0.15s, transform 0.1s;
}

.searchbar-btn:hover:not(:disabled) {
  background-color: #1e293b;
  transform: scale(1.05);
}

.searchbar-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

.searchbar-compact .searchbar-btn {
  width: 30px;
  height: 30px;
  margin: 4px 5px;
}

/* Spin animation */
@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

.animate-spin {
  animation: spin 0.8s linear infinite;
}
</style>
