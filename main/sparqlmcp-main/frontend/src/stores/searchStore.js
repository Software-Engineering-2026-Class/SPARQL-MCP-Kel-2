// =============================================================
// stores/searchStore.js — Global Search State (Pinia)
// CyberSec Search — SPARQL-MCP Frontend
// =============================================================

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { mockResults, mockSparqlQuery } from '@/data/mockData.js'

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

        // Keep mock cards until real mapping is implemented
        results.value = mockResults
        isLoading.value = false
        return
      } catch (error) {
        lastError.value = error?.message || 'Failed to reach backend'
      }
    }

    // Simulate network latency (1.2 seconds)
    await new Promise((resolve) => setTimeout(resolve, 1200))

    // Load mock data — replace with real API call in production
    results.value = mockResults
    sparqlQuery.value = mockSparqlQuery(searchQuery)

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
