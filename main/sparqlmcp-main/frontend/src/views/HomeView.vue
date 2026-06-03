<!-- =============================================================
  HomeView.vue — STATE 1: Initial Search Screen
  Hero section with large title, subtitle, search bar,
  and suggestion chips. Matches screenshot 2.
  ============================================================= -->
<template>
  <div class="home-root content-layer">
    <!-- ── Top Navbar ─────────────────────────────────────── -->
    <Header />

    <!-- ── Hero Section ───────────────────────────────────── -->
    <main class="hero-section" id="main-content" role="main">
      <!-- Hero text group -->
      <div class="hero-text-group">
        <h1 class="hero-title">
          Search Engine for<br />Cybersecurity Data
        </h1>

        <p class="hero-subtitle">
          SEARCH ENGINE POWERED BY FEDERATED AGENTIC SPARQL
        </p>
      </div>

      <!-- Search bar -->
      <div class="hero-search-wrapper">
        <SearchBar
          v-model="localQuery"
          placeholder="Search for vulnerabilities, malware, or threats using natural language..."
          @search="handleSearch"
        />
      </div>
    </main>

    <!-- ── Footer ─────────────────────────────────────────── -->
    <Footer />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSearchStore } from '@/stores/searchStore.js'
import Header        from '@/components/Header.vue'
import SearchBar     from '@/components/SearchBar.vue'
import Footer        from '@/components/Footer.vue'

const router      = useRouter()
const store       = useSearchStore()
const localQuery  = ref('')

/**
 * Triggered when the user submits the search form.
 * Starts the async mock search and navigates to the results page.
 */
async function handleSearch(query) {
  // Kick off search (sets loading state in store)
  store.performSearch(query)
  // Navigate immediately — results page shows loading state
  router.push({ name: 'Results' })
}
</script>

<style scoped>
/* Full-height layout */
.home-root {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* Hero section — centered vertically and horizontally */
.hero-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 1.5rem 3rem;
  text-align: center;
}

/* Hero text */
.hero-text-group {
  margin-bottom: 2.5rem;
}

.hero-title {
  font-size: clamp(2.5rem, 6vw, 4rem);
  font-weight: 900;
  line-height: 1.08;
  letter-spacing: -0.03em;
  color: #f0f4f8;
  margin: 0 0 1.25rem;
}

.hero-subtitle {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.18em;
  color: #64748b;
  margin: 0;
  text-transform: uppercase;
}

/* Search wrapper */
.hero-search-wrapper {
  width: 100%;
  max-width: 600px;
  margin: 0;
}

/* ── Responsive ───────────────────────────────────────────── */
@media (max-width: 640px) {
  .hero-title {
    font-size: 2rem;
  }

  .hero-section {
    padding: 2rem 1rem 2rem;
  }
}
</style>
