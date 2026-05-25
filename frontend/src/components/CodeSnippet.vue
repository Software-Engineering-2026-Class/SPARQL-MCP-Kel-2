<!-- =============================================================
  CodeSnippet.vue — Inline SPARQL / code example block
  Lightweight version of the SparqlAccordion for static examples.
  ============================================================= -->
<template>
  <div class="snippet-root">
    <!-- Toolbar -->
    <div class="snippet-toolbar">
      <span class="snippet-label">{{ label }}</span>
      <button
        class="snippet-copy"
        type="button"
        :aria-label="copied ? 'Copied!' : 'Copy code'"
        @click="copyCode"
      >
        <!-- Check -->
        <svg v-if="copied" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="icon">
          <path d="M20 6L9 17l-5-5" />
        </svg>
        <!-- Copy icon -->
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon">
          <rect x="9" y="9" width="13" height="13" rx="2" />
          <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
        </svg>
        <span>{{ copied ? 'Copied' : 'Copy' }}</span>
      </button>
    </div>

    <!-- Code body -->
    <pre class="snippet-code"><code>{{ code }}</code></pre>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  /** Code string to display */
  code:  { type: String, required: true },
  /** File-type label shown in the toolbar */
  label: { type: String, default: 'SPARQL' }
})

const copied = ref(false)

async function copyCode() {
  try {
    await navigator.clipboard.writeText(props.code)
  } catch {
    /* fallback — silent fail for demo */
  }
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}
</script>

<style scoped>
.snippet-root {
  border-radius: 0.5rem;
  overflow: hidden;
  border: 1px solid #1e3554;
}

/* Toolbar */
.snippet-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.4rem 1rem;
  background-color: #0d1e35;
  border-bottom: 1px solid #1e3554;
}

.snippet-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #475569;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.snippet-copy {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-family: 'Inter', sans-serif;
  font-size: 0.7rem;
  color: #64748b;
  background: transparent;
  border: 1px solid #1e3554;
  border-radius: 0.25rem;
  padding: 0.2rem 0.5rem;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}

.snippet-copy:hover {
  color: #38bdf8;
  border-color: #38bdf8;
}

.icon {
  width: 11px;
  height: 11px;
}

/* Code */
.snippet-code {
  background-color: #070f1d;
  padding: 1rem 1.125rem;
  margin: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78125rem;
  line-height: 1.75;
  color: #94a3b8;
  white-space: pre;
  overflow-x: auto;
  tab-size: 2;
}
</style>
