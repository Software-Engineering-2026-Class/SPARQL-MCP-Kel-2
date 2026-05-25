<!-- =============================================================
  Header.vue — Persistent Top Navigation Bar
  Appears on both Home and Results views.
  Props control which variant is rendered.
  ============================================================= -->
<template>
  <header
    class="header-root"
    :class="{ 'header-compact': compact }"
    role="banner"
  >
    <div class="header-inner">
      <!-- Logo / Brand -->
      <router-link
        id="nav-logo"
        to="/"
        class="brand-link"
        aria-label="CyberSec Search — Home"
        @click="handleLogoClick"
      >
        <!-- Shield icon SVG -->
        <svg
          class="brand-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          aria-hidden="true"
        >
          <path
            d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z"
          />
        </svg>
        <span class="brand-name">CyberSec Search</span>
      </router-link>

      <!-- Center search bar (compact/results mode) -->
      <div v-if="compact" class="header-search-slot">
        <slot name="search" />
      </div>

      <!-- Navigation links (shown on home / desktop) -->
      <nav
        class="nav-links"
        :class="{ 'nav-links-hidden-sm': compact }"
        aria-label="Primary navigation"
      >
        <router-link
          id="nav-about"
          to="/about"
          class="nav-link"
          active-class="nav-link-active"
        >About</router-link>
        <router-link
          id="nav-docs"
          to="/documentation"
          class="nav-link"
          active-class="nav-link-active"
        >Documentation</router-link>

        <!-- User/profile icon -->
        <button
          id="nav-profile"
          class="profile-btn"
          aria-label="User profile"
          type="button"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            class="w-5 h-5"
            aria-hidden="true"
          >
            <circle cx="12" cy="8" r="4" />
            <path d="M4 20c0-4 3.58-7 8-7s8 3 8 7" />
          </svg>
        </button>
      </nav>
    </div>
  </header>
</template>

<script setup>
import { useSearchStore } from '@/stores/searchStore.js'
import { useRouter } from 'vue-router'

// ── Props ───────────────────────────────────────────────────
const props = defineProps({
  /** When true, renders the compact header with search slot */
  compact: {
    type: Boolean,
    default: false
  }
})

const store  = useSearchStore()
const router = useRouter()

/** Clicking the logo resets search and navigates home */
function handleLogoClick() {
  store.resetSearch()
}
</script>

<style scoped>
/* Header root */
.header-root {
  position: sticky;
  top: 0;
  z-index: 50;
  width: 100%;
  background-color: #0a1628;
  border-bottom: 1px solid #1e3554;
  backdrop-filter: blur(12px);
}

/* Normal header height */
.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 1.5rem;
  height: 52px;
  gap: 1rem;
}

/* Compact mode: smaller height */
.header-compact .header-inner {
  height: 52px;
}

/* Center search slot grows to fill available space */
.header-search-slot {
  flex: 1;
  max-width: 600px;
  margin: 0 1.5rem;
}

/* Brand */
.brand-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: #f0f4f8;
  flex-shrink: 0;
}

.brand-icon {
  width: 22px;
  height: 22px;
  color: #38bdf8;
}

.brand-name {
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  white-space: nowrap;
}

/* Nav links */
.nav-links {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex-shrink: 0;
}

.nav-link {
  font-size: 0.875rem;
  font-weight: 500;
  color: #94a3b8;
  text-decoration: none;
  transition: color 0.15s ease;
}

.nav-link:hover {
  color: #f0f4f8;
}

/* Active route indicator */
.nav-link-active {
  color: #f0f4f8;
}

.nav-link-active::after {
  content: '';
  display: block;
  height: 2px;
  border-radius: 1px;
  background-color: #38bdf8;
  margin-top: 2px;
}

/* Profile button */
.profile-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid #1e3554;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.profile-btn:hover {
  border-color: #38bdf8;
  color: #f0f4f8;
}

/* Hide nav links on compact mobile */
@media (max-width: 640px) {
  .nav-links-hidden-sm {
    display: none;
  }
  .header-search-slot {
    margin: 0 0.5rem;
  }
}
</style>
