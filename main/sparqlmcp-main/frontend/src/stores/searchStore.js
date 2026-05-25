// =============================================================
// stores/searchStore.js — Global Search State (Pinia)
// CyberSec Search — SPARQL-MCP Frontend
// =============================================================

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { mockResults, mockSparqlQuery } from '@/data/mockData.js'

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
