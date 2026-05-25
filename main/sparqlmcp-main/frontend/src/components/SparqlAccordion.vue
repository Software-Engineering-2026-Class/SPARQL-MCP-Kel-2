<!-- =============================================================
  SparqlAccordion.vue — Collapsible SPARQL Query Panel
  Shown below the header in the Results view.
  Matches the dark-blue full-width bar from the screenshot.
  ============================================================= -->
<template>
  <div class="sparql-accordion" role="region" aria-label="SPARQL Query">
    <!-- Accordion header / toggle button -->
    <button
      id="sparql-accordion-toggle"
      class="sparql-header"
      type="button"
      :aria-expanded="isOpen"
      aria-controls="sparql-body"
      @click="toggle"
    >
      <span class="sparql-title">View Generated SPARQL Query</span>
      <span class="sparql-chevron" :class="{ 'rotate-180': isOpen }" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
          <path d="M6 9l6 6 6-6" />
        </svg>
      </span>
    </button>

    <!-- Accordion body — SPARQL code block -->
    <Transition name="accordion">
      <div
        v-if="isOpen"
        id="sparql-body"
        class="sparql-body"
      >
        <!-- Toolbar: file label + copy button -->
        <div class="sparql-toolbar">
          <span class="sparql-file-label">query.sparql</span>
          <button
            id="sparql-copy-btn"
            class="copy-btn"
            type="button"
            :aria-label="copied ? 'Copied!' : 'Copy SPARQL query'"
            @click="copyQuery"
          >
            <!-- Check icon when copied -->
            <svg v-if="copied" class="w-3.5 h-3.5 text-green-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M20 6L9 17l-5-5" />
            </svg>
            <!-- Copy icon -->
            <svg v-else class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" />
              <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
            </svg>
            <span>{{ copied ? 'Copied!' : 'Copy' }}</span>
          </button>
        </div>

        <!-- Syntax-highlighted SPARQL code -->
        <div class="sparql-code-wrapper">
          <pre class="sparql-code" aria-label="Generated SPARQL query"><code v-html="highlightedQuery" /></pre>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useSearchStore } from '@/stores/searchStore.js'

const store  = useSearchStore()
const copied = ref(false)

/** Whether the accordion is currently open */
const isOpen = computed(() => store.sparqlAccordionOpen)

/** Toggle via store action */
function toggle() {
  store.toggleSparqlAccordion()
}

/** Copy query to clipboard */
async function copyQuery() {
  try {
    await navigator.clipboard.writeText(store.sparqlQuery)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // Fallback for browsers without clipboard API
    const el = document.createElement('textarea')
    el.value = store.sparqlQuery
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }
}

/**
 * Simple SPARQL syntax highlighter.
 * Processes line-by-line to handle comments first, then applies
 * token classes to code lines only.
 *
 * IMPORTANT: We do NOT HTML-escape before injecting spans — instead
 * we escape each token's content, then wrap in spans. This avoids
 * double-encoding issues with v-html.
 */
const highlightedQuery = computed(() => {
  if (!store.sparqlQuery) return ''

  /** Escape a plain-text value for safe HTML insertion */
  function esc(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
  }

  const KEYWORDS = [
    'SELECT', 'WHERE', 'FILTER', 'OPTIONAL', 'UNION', 'BIND',
    'DISTINCT', 'LIMIT', 'OFFSET', 'ORDER\\s+BY', 'ASC', 'DESC',
    'PREFIX', 'AS', 'GROUP\\s+BY', 'HAVING', 'CONSTRUCT', 'ASK',
    'DESCRIBE', 'FROM', 'NAMED'
  ]
  const KW_RE  = new RegExp(`\\b(${KEYWORDS.join('|')})\\b`, 'g')
  const VAR_RE = /\?[a-zA-Z_][a-zA-Z0-9_]*/g
  const PFX_RE = /\b([a-zA-Z][a-zA-Z0-9]*:)(?!\s*\/\/)/g  // prefix: but not http://
  const URI_RE = /<[^>\s]+>/g
  const STR_RE = /"[^"]*"|'[^']*'/g

  /**
   * Tokenize a single code line and return HTML with highlight spans.
   * We walk through the line character-by-character collecting tokens.
   */
  function highlightLine(line) {
    // Collect token positions: [{start, end, cls, raw}]
    const tokens = []

    // URIs first (< > delimited)
    let m
    URI_RE.lastIndex = 0
    while ((m = URI_RE.exec(line)) !== null) {
      tokens.push({ start: m.index, end: URI_RE.lastIndex, cls: 'sparql-uri', raw: m[0] })
    }

    // Strings
    STR_RE.lastIndex = 0
    while ((m = STR_RE.exec(line)) !== null) {
      // Skip if overlaps with URI token
      if (!tokens.some(t => m.index >= t.start && m.index < t.end)) {
        tokens.push({ start: m.index, end: STR_RE.lastIndex, cls: 'sparql-string', raw: m[0] })
      }
    }

    // Variables (?name)
    VAR_RE.lastIndex = 0
    while ((m = VAR_RE.exec(line)) !== null) {
      if (!tokens.some(t => m.index >= t.start && m.index < t.end)) {
        tokens.push({ start: m.index, end: VAR_RE.lastIndex, cls: 'sparql-var', raw: m[0] })
      }
    }

    // Keywords (only in non-overlapping positions)
    KW_RE.lastIndex = 0
    while ((m = KW_RE.exec(line)) !== null) {
      if (!tokens.some(t => m.index >= t.start && m.index < t.end)) {
        tokens.push({ start: m.index, end: KW_RE.lastIndex, cls: 'sparql-keyword', raw: m[0] })
      }
    }

    // Sort by start position
    tokens.sort((a, b) => a.start - b.start)

    // Build HTML string
    let html = ''
    let cursor = 0
    for (const tok of tokens) {
      if (tok.start < cursor) continue // skip overlapping
      // Plain text before token
      if (tok.start > cursor) html += esc(line.slice(cursor, tok.start))
      html += `<span class="${tok.cls}">${esc(tok.raw)}</span>`
      cursor = tok.end
    }
    // Remaining text
    if (cursor < line.length) html += esc(line.slice(cursor))
    return html
  }

  // Process line by line
  return store.sparqlQuery
    .split('\n')
    .map(line => {
      // Comment lines — entire line is a comment
      const trimmed = line.trimStart()
      if (trimmed.startsWith('#')) {
        return `<span class="sparql-comment">${esc(line)}</span>`
      }
      // Check for inline comment (# after code)
      const hashIdx = line.indexOf(' #')
      if (hashIdx > 0) {
        const codePart    = line.slice(0, hashIdx)
        const commentPart = line.slice(hashIdx)
        return highlightLine(codePart) + `<span class="sparql-comment">${esc(commentPart)}</span>`
      }
      return highlightLine(line)
    })
    .join('\n')
})
</script>

<style>
/* SPARQL syntax token styles — must be non-scoped so v-html injected
   spans are styled correctly (they don't carry the scoped attribute). */
.sparql-keyword { color: #60a5fa; font-weight: 600; }
.sparql-prefix  { color: #818cf8; }
.sparql-var     { color: #34d399; }
.sparql-uri     { color: #f59e0b; }
.sparql-string  { color: #fb923c; }
.sparql-comment { color: #475569; font-style: italic; }
</style>

<style scoped>
/* Accordion root */
.sparql-accordion {
  width: 100%;
  background-color: #0a1628;
  border-bottom: 1px solid #1e3554;
}

/* Header/trigger */
.sparql-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0.875rem 1.5rem;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #f0f4f8;
  text-align: left;
  transition: background-color 0.15s;
}

.sparql-header:hover {
  background-color: rgba(30, 53, 84, 0.4);
}

.sparql-title {
  font-size: 0.9375rem;
  font-weight: 500;
  letter-spacing: -0.01em;
}

.sparql-chevron {
  color: #64748b;
  transition: transform 0.25s ease;
  display: flex;
  align-items: center;
}

.rotate-180 {
  transform: rotate(180deg);
}

/* Body */
.sparql-body {
  border-top: 1px solid #1e3554;
  overflow: hidden;
}

/* Toolbar */
.sparql-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 1.5rem;
  background-color: #0d1e35;
  border-bottom: 1px solid #1e3554;
}

.sparql-file-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #475569;
}

/* Copy button */
.copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.25rem 0.625rem;
  border-radius: 0.25rem;
  border: 1px solid #1e3554;
  background: transparent;
  color: #64748b;
  font-family: 'Inter', sans-serif;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s;
}

.copy-btn:hover {
  border-color: #38bdf8;
  color: #38bdf8;
}

/* Code block */
.sparql-code-wrapper {
  overflow-x: auto;
  padding: 1.25rem 1.5rem;
  background-color: #070f1d;
}

.sparql-code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8125rem;
  line-height: 1.7;
  color: #94a3b8;
  margin: 0;
  white-space: pre;
  tab-size: 2;
}

/* Accordion transition */
.accordion-enter-active,
.accordion-leave-active {
  transition: max-height 0.3s ease, opacity 0.25s ease;
  max-height: 600px;
  overflow: hidden;
}

.accordion-enter-from,
.accordion-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
