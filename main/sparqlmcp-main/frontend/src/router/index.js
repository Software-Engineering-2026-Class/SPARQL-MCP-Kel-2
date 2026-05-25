// =============================================================
// router/index.js — Vue Router Configuration
// CyberSec Search — SPARQL-MCP Frontend
// =============================================================

import { createRouter, createWebHistory } from 'vue-router'
import HomeView          from '@/views/HomeView.vue'
import ResultsView       from '@/views/ResultsView.vue'
import AboutView         from '@/views/AboutView.vue'
import DocumentationView from '@/views/DocumentationView.vue'

/** Application route definitions */
const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomeView,
    meta: {
      title: 'CyberSec Search — Federated Agentic SPARQL'
    }
  },
  {
    path: '/results',
    name: 'Results',
    component: ResultsView,
    meta: {
      title: 'Search Results — CyberSec Search'
    }
  },
  {
    path: '/about',
    name: 'About',
    component: AboutView,
    meta: {
      title: 'About — CyberSec Search'
    }
  },
  {
    path: '/documentation',
    name: 'Documentation',
    component: DocumentationView,
    meta: {
      title: 'Documentation — CyberSec Search'
    }
  },
  // Catch-all: redirect unknown routes to home
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    // Always scroll to top on navigation
    return { top: 0 }
  }
})

// Update document title on each route change
router.afterEach((to) => {
  if (to.meta?.title) {
    document.title = to.meta.title
  }
})

export default router
