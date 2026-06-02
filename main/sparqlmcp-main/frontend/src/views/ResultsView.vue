<!-- =============================================================
  ResultsView.vue — STATE 2: Results Dashboard
  Compact header + SPARQL accordion + two-column entity/graph layout.
  Matches screenshot 1.
  ============================================================= -->
<template>
  <div class="results-root content-layer">
    <!-- ── Compact Header with Inline Search ──────────────── -->
    <Header compact>
      <template #search>
        <SearchBar
          v-model="localQuery"
          compact
          placeholder="Search..."
          @search="handleSearch"
        />
      </template>
    </Header>

    <!-- ── SPARQL Query Accordion ─────────────────────────── -->
    <SparqlAccordion v-if="store.sparqlQuery" />

    <!-- ── Main Content ───────────────────────────────────── -->
    <main id="results-main" role="main" class="results-main">

      <!-- Loading state -->
      <div v-if="store.isLoading" class="loading-state" aria-live="polite" aria-label="Loading results">
        <div class="loading-spinner" aria-hidden="true">
          <svg class="spin-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
          </svg>
        </div>
        <p class="loading-text">Querying knowledge graph…</p>
        <p class="loading-sub">Processing natural language with Federated Agentic SPARQL</p>
      </div>

      <!-- Results grid -->
      <Transition name="fade-slide-up">
        <div v-if="!store.isLoading && store.hasResults" class="results-grid">
          <!-- Left column: entity cards -->
          <section class="cards-column" aria-label="Search results">
            <div class="summary-card" role="region" aria-label="AI-generated explanation">
              <div class="summary-header">
                <!-- Bot / AI icon -->
                <svg class="summary-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
                  <rect x="3" y="8" width="18" height="13" rx="2" />
                  <path d="M8 8V5a4 4 0 0 1 8 0v3" />
                  <circle cx="9" cy="14" r="1.2" fill="currentColor" stroke="none" />
                  <circle cx="15" cy="14" r="1.2" fill="currentColor" stroke="none" />
                </svg>
                <span>Explanation</span>
              </div>
              <div class="summary-body">
                <template v-if="store.isLoading">
                  <span class="summary-dots" aria-label="Generating explanation">
                    <span /><span /><span />
                  </span>
                </template>
                <template v-else-if="store.summary">{{ store.summary }}</template>
                <template v-else>No summary available for this query.</template>
              </div>
            </div>
            <TransitionGroup name="card-list" tag="div" class="cards-list">
              <EntityCard
                v-for="entity in store.results"
                :key="entity.id"
                :entity="entity"
              />
            </TransitionGroup>
          </section>

          <!-- Right column: knowledge graph -->
          <section class="graph-column" aria-label="Knowledge graph">
            <GraphCanvas :entities="store.results" :graph="store.graphData" />
          </section>
        </div>
      </Transition>

      <!-- Empty state (searched but no results) -->
      <div
        v-if="!store.isLoading && store.hasSearched && !store.hasResults"
        class="empty-state"
        aria-live="polite"
      >
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="11" cy="11" r="8" />
          <path d="M21 21l-4.35-4.35M8 11h6" />
        </svg>
        <p class="empty-text">No results found</p>
        <p class="empty-sub">Try a different query.</p>
      </div>

    </main>

    <!-- ── Footer ─────────────────────────────────────────── -->
    <Footer />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSearchStore } from '@/stores/searchStore.js'
import Header          from '@/components/Header.vue'
import SearchBar       from '@/components/SearchBar.vue'
import SparqlAccordion from '@/components/SparqlAccordion.vue'
import EntityCard      from '@/components/EntityCard.vue'
import GraphCanvas     from '@/components/GraphCanvas.vue'
import Footer          from '@/components/Footer.vue'

const router     = useRouter()
const store      = useSearchStore()
const localQuery = ref(store.query)

// Redirect to home if accessed directly without a query
onMounted(() => {
  if (!store.hasSearched) {
    router.replace({ name: 'Home' })
  }
})

/**
 * Handles a new search from the compact header search bar.
 * Reuses the same results view without navigating away.
 */
async function handleSearch(query) {
  localQuery.value = query
  store.performSearch(query)
}
</script>

<style scoped>
/* Root layout */
.results-root {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* Main content area */
.results-main {
  flex: 1;
  padding: 1.25rem 1.5rem;
  max-width: 1280px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

/* Two-column results grid */
.results-grid {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 1rem;
  align-items: start;
}

/* Left column: cards stack */
.cards-column {
  display: flex;
  flex-direction: column;
}

.cards-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* Right column: graph fills remaining space */
.graph-column {
  position: sticky;
  top: 60px; /* below the compact header */
  height: calc(100vh - 100px);
  max-height: 640px;
}

/* ── Loading State ────────────────────────────────────────── */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  gap: 1rem;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  color: #38bdf8;
}

.spin-svg {
  width: 100%;
  height: 100%;
  animation: spin-anim 1s linear infinite;
}

@keyframes spin-anim {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

.loading-text {
  font-size: 1rem;
  font-weight: 600;
  color: #f0f4f8;
  margin: 0;
}

.loading-sub {
  font-size: 0.8125rem;
  color: #64748b;
  margin: 0;
  text-align: center;
}

/* ── Empty State ──────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  gap: 0.75rem;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: #334155;
}

.empty-text {
  font-size: 1rem;
  font-weight: 600;
  color: #475569;
  margin: 0;
}

.empty-sub {
  font-size: 0.8125rem;
  color: #334155;
  margin: 0;
  text-align: center;
}

/* ── Summary Card — matches EntityCard design system ──────── */
.summary-card {
  background-color: #0e1c2f;
  border: 1px solid #1e3554;
  border-left: 3px solid #38bdf8;
  border-radius: 0.5rem;
  padding: 1rem 1.125rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(30, 53, 84, 0.6);
  margin-bottom: 0.75rem;
  transition: border-color 0.2s ease;
}

.summary-card:hover {
  border-color: rgba(56, 189, 248, 0.35);
  border-left-color: #38bdf8;
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #38bdf8;
  margin-bottom: 0.6rem;
}

.summary-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  color: #38bdf8;
}

.summary-body {
  font-size: 0.8375rem;
  color: #94a3b8;
  line-height: 1.65;
}

/* Typing indicator dots */
.summary-dots {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  height: 1rem;
}

.summary-dots span {
  display: inline-block;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #38bdf8;
  opacity: 0.4;
  animation: dot-pulse 1.2s ease-in-out infinite;
}

.summary-dots span:nth-child(2) { animation-delay: 0.2s; }
.summary-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-pulse {
  0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
  40%           { opacity: 1;   transform: scale(1);   }
}

/* ── Transition: fade-slide-up ────────────────────────────── */
.fade-slide-up-enter-active {
  transition: all 0.45s cubic-bezier(0.16, 1, 0.3, 1);
}

.fade-slide-up-enter-from {
  opacity: 0;
  transform: translateY(16px);
}

/* ── Transition: card list staggered ─────────────────────── */
.card-list-enter-active {
  transition: all 0.4s ease;
}

.card-list-enter-from {
  opacity: 0;
  transform: translateX(-12px);
}

/* ── Responsive ───────────────────────────────────────────── */
@media (max-width: 960px) {
  .results-grid {
    grid-template-columns: 1fr;
  }

  .graph-column {
    position: static;
    height: 420px;
    max-height: none;
  }

  .results-main {
    padding: 1rem;
  }
}

@media (max-width: 640px) {
  .graph-column {
    height: 320px;
  }
}
</style>
