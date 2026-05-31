// =============================================================
// stores/searchStore.js — Global Search State (Pinia)
// CyberSec Search — SPARQL-MCP Frontend
// =============================================================

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { mockResults, mockSparqlQuery } from '@/data/mockData.js'

function toTitleCase(value) {
  return String(value || '')
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function pickBindingValue(binding, keys) {
  for (const key of keys) {
    const value = binding?.[key]?.value
    if (value) return value
  }
  return ''
}

function shortenText(value, maxLength = 120) {
  if (!value) return ''
  if (value.length <= maxLength) return value
  return `${value.slice(0, maxLength - 1).trimEnd()}…`
}

function extractReadableId(value) {
  if (!value) return ''
  const text = String(value)
  const withoutAngles = text.replace(/^<|>$/g, '')
  const tail = withoutAngles.split(/[\/#+]/).filter(Boolean).pop() || withoutAngles
  return decodeURIComponent(tail)
}

function extractClassName(value) {
  const shortId = extractReadableId(value)
  const match = shortId.match(/(CVE-\d{4}-\d+|CWE-\d+|CPE)/i)
  if (match) return match[1].toUpperCase()
  return toTitleCase(shortId)
}

function compactUrlDisplay(value) {
  if (!value) return ''
  const text = String(value).replace(/^<|>$/g, '')
  const withoutProtocol = text.replace(/^https?:\/\//, '')
  const parts = withoutProtocol.split('/')
  if (parts.length <= 2) return withoutProtocol
  const tail = parts.slice(-2).join('/')
  return `${parts[0]}/…/${tail}`
}

function inferEntityGroup({ typeValue, readableId, entityUri, label }) {
  const haystack = [typeValue, readableId, entityUri, label].join(' ').toLowerCase()
  if (haystack.includes('cve') || haystack.includes('vulnerab') || haystack.includes('cwe')) return 'vulnerability'
  if (haystack.includes('cpe') || haystack.includes('product') || haystack.includes('vendor')) return 'target'
  if (haystack.includes('malware') || haystack.includes('family') || haystack.includes('threat')) return 'malware'
  return 'target'
}

function mapBindingsToEntities(payload) {
  const bindings = payload?.results?.bindings || payload?.results?.results?.bindings
  if (!Array.isArray(bindings) || bindings.length === 0) {
    return []
  }

  return bindings.slice(0, 8).map((binding, index) => {
    const label = pickBindingValue(binding, ['label', 'name', 'title', 'entityLabel', 'familyLabel'])
    const entityUri = pickBindingValue(binding, ['s', 'entity', 'subject', 'resource', 'uri', 'id'])
    const typeValue = pickBindingValue(binding, ['type', 'category', 'kind', 'class', 'cve', 'cwe', 'cpe'])
    const description = pickBindingValue(binding, ['description', 'summary', 'notes', 'comment'])
    const scoreValue = pickBindingValue(binding, ['cvss', 'score', 'severity', 'baseScore'])
    const aliases = [
      pickBindingValue(binding, ['alias', 'altLabel', 'synonym', 'title']),
      pickBindingValue(binding, ['vector', 'primaryVector', 'attackVector', 'accessVector'])
    ].filter(Boolean)

    const badge = scoreValue
      ? { label: `Score ${scoreValue}`, variant: 'cvss', score: Number(scoreValue) || scoreValue }
      : { label: typeValue ? extractClassName(typeValue) : 'Result', variant: 'danger' }

    const readableId = extractReadableId(entityUri) || extractReadableId(label) || `result-${index + 1}`
    const subtitle = typeValue
      ? extractClassName(typeValue)
      : readableId
        ? readableId.split('-')[0].toUpperCase()
        : 'Search Result'

    const normalizedDescription = description || ''
    const entityGroup = inferEntityGroup({ typeValue, readableId, entityUri, label })

    const fields = []
    for (const [fieldLabel, fieldValue] of [
      ['ID', readableId],
      ['Source', entityUri],
      ['Type', extractClassName(typeValue)],
      ['Issued', pickBindingValue(binding, ['issued'])],
      ['Modified', pickBindingValue(binding, ['modified'])]
    ]) {
      if (!fieldValue) continue
      fields.push({
        label: fieldLabel,
        value: fieldLabel === 'Source' ? fieldValue : shortenText(fieldValue, 120),
        wide: fieldLabel === 'Source'
      })
    }

    if (fields.length === 0) {
      fields.push({ label: 'Result', value: shortenText(label || `Row ${index + 1}`, 140) })
    }

    return {
      id: entityUri || `${readableId || label || 'result'}-${index}`,
      type: entityGroup,
      kind: extractClassName(typeValue),
      title: readableId || label || `Result ${index + 1}`,
      displayLabel: readableId || label || `Result ${index + 1}`,
      subtitle,
      badge,
      fields,
      tags: aliases.filter(Boolean),
      description: normalizedDescription || null,
      uri: entityUri || ''
    }
  })
}

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const useLiveApi = import.meta.env.VITE_USE_LIVE_API === 'true'
const shouldUseLiveApi = useLiveApi && apiBaseUrl.length > 0

/**
 * Search Store — manages the current query, loading state,
 * search results, and the generated SPARQL query string.
 */
export const useSearchStore = defineStore('search', () => {
  // ── State ──────────────────────────────────────────────────
  /** Current search query text */
  const query = ref('')

  /** Whether a search is in progress */
  const isLoading = ref(false)

  /** Resolved entity results after search */
  const results = ref([])

  /** Generated SPARQL query from the search */
  const sparqlQuery = ref('')

  /** Raw SPARQL results (live API) */
  const rawResults = ref(null)

  /** Graph data built from real SPARQL relations (live API) */
  const graphData = ref(null)

  /** Short extractive summary built from SPARQL results */
  const summary = ref(null)

  /** Last API error, if any */
  const lastError = ref(null)

  /** Whether the SPARQL accordion is open */
  const sparqlAccordionOpen = ref(false)

  /** Whether a search has been submitted at least once */
  const hasSearched = ref(false)

  // ── Computed ───────────────────────────────────────────────
  /** True when results are available */
  const hasResults = computed(() => results.value.length > 0)

  // ── Actions ────────────────────────────────────────────────

  /**
   * Simulates an async search operation.
   * In production this would call the MCP/SPARQL backend.
   *
   * @param {string} searchQuery - Natural language search query
   */
  async function performSearch(searchQuery) {
    if (!searchQuery.trim()) return

    query.value = searchQuery.trim()
    isLoading.value = true
    hasSearched.value = true
    results.value = []
    sparqlQuery.value = ''
    sparqlAccordionOpen.value = false
    rawResults.value = null
    graphData.value = null
    lastError.value = null

    if (shouldUseLiveApi) {
      try {
        const response = await fetch(`${apiBaseUrl}/api/nl2sparql`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            nl_query: searchQuery,
            options: { expose_sparql: true }
          })
        })

        const payload = await response.json()
        if (!response.ok || payload.error) {
          const message = payload.error?.message || 'Backend error'
          throw new Error(message)
        }

        sparqlQuery.value = payload.sparql || ''
        rawResults.value = payload.results || null
        graphData.value = payload.graph || null
        summary.value = payload.summary?.text || null

        const mappedResults = mapBindingsToEntities(payload)
        results.value = mappedResults.length > 0 ? mappedResults : []
        isLoading.value = false
        return
      } catch (error) {
        lastError.value = error?.message || 'Failed to reach backend'
        isLoading.value = false
        return
      }
    }

    // Simulate network latency (1.2 seconds)
    await new Promise((resolve) => setTimeout(resolve, 1200))

    // Load mock data — replace with real API call in production
    results.value = mockResults
    sparqlQuery.value = mockSparqlQuery(searchQuery)
    graphData.value = null

    isLoading.value = false
  }

  /**
   * Resets the store to initial state (navigating back to home)
   */
  function resetSearch() {
    query.value = ''
    isLoading.value = false
    results.value = []
    sparqlQuery.value = ''
    sparqlAccordionOpen.value = false
    hasSearched.value = false
  }

  /**
   * Toggles the SPARQL query accordion panel
   */
  function toggleSparqlAccordion() {
    sparqlAccordionOpen.value = !sparqlAccordionOpen.value
  }

  return {
    // State
    query,
    isLoading,
    results,
    sparqlQuery,
    rawResults,
    graphData,
    summary,
    lastError,
    sparqlAccordionOpen,
    hasSearched,
    // Computed
    hasResults,
    // Actions
    performSearch,
    resetSearch,
    toggleSparqlAccordion
  }
})
