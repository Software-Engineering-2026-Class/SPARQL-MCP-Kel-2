# CyberSec Search — Frontend

> AI-Powered Cybersecurity Intelligence Platform using Federated Agentic SPARQL & Knowledge Graphs.

---

## Overview

This is the frontend-only module for the **SPARQL-MCP Kel-2** group project.
It provides a cinematic, dark-navy UI for natural language cybersecurity search,
SPARQL query visualization, entity cards, and an interactive knowledge graph.

All data in this module is **mocked locally** — no backend, API, or database is required.

---

## Tech Stack

| Technology     | Version |
|----------------|---------|
| Vue 3          | ^3.5    |
| Vite           | ^8.0    |
| TailwindCSS    | ^4.3    |
| Pinia          | ^3.0    |
| Vue Router     | ^5.0    |
| vis-network    | ^10.1   |
| @lucide/vue    | ^1.16   |
| JetBrains Mono | Google Fonts |
| Inter          | Google Fonts |

---

## Project Structure

```
frontend/
├── index.html                  # HTML entry with SEO meta + fonts
├── vite.config.js              # Vite + TailwindCSS v4 config
├── package.json
└── src/
    ├── main.js                 # App entry: Vue + Pinia + Router
    ├── App.vue                 # Root component + page transitions
    ├── style.css               # Global CSS + design tokens
    ├── router/
    │   └── index.js            # Vue Router (Home + Results)
    ├── stores/
    │   └── searchStore.js      # Pinia store (search state)
    ├── data/
    │   └── mockData.js         # All mock cybersecurity data
    ├── components/
    │   ├── StarBackground.vue  # Animated star/constellation canvas
    │   ├── Header.vue          # Sticky navbar (normal + compact)
    │   ├── SearchBar.vue       # NL query input (pill-style)
    │   ├── SuggestionChip.vue  # Pre-defined search suggestion buttons
    │   ├── SparqlAccordion.vue # Collapsible SPARQL query panel
    │   ├── EntityCard.vue      # Cybersecurity entity card
    │   ├── GraphCanvas.vue     # vis-network knowledge graph
    │   └── Footer.vue          # Site footer
    └── views/
        ├── HomeView.vue        # STATE 1: Hero search screen
        └── ResultsView.vue     # STATE 2: Results dashboard
```

---

## Getting Started

### Prerequisites
- Node.js >= 18.x
- npm >= 9.x

### Install & Run

```bash
# Navigate to this folder
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at: **http://localhost:5173**

### Build for Production

```bash
npm run build
npm run preview
```

---

## Backend Integration (Optional)

To use the live backend API (Claude + SPARQL), create a `.env` file in this folder:

```bash
VITE_API_BASE_URL=http://localhost:8765
VITE_USE_LIVE_API=true
```

When enabled, the UI will call the backend for SPARQL generation and keep the
mock entity cards until a full result mapping is implemented.

---

## Application States

### State 1 — Home / Search Screen (`/`)
- Animated star/constellation canvas background
- Large hero title: *"Search Engine for Cybersecurity Data"*
- Subtitle in spaced uppercase: *"Search Engine Powered by Federated Agentic SPARQL"*
- White pill-style search bar
- Three suggestion chips (Analyze CVE-2023-1234, Find Emotet relationships, Query Log4j impacts)
- Minimal footer

### State 2 — Results Dashboard (`/results`)
- Compact sticky header with inline search bar
- Collapsible "View Generated SPARQL Query" accordion (with syntax highlighting + copy button)
- **Left column**: Stacked entity cards (Emotet Botnet + CVE-2023-1234)
- **Right column**: Interactive knowledge graph (vis-network, draggable, zoomable)
- Loading spinner while mock query is "processing" (1.2s)
- Responsive: single column on tablets/mobile

---

## Mock Data

All cybersecurity data is defined in `src/data/mockData.js`:

- **Entity cards**: Emotet Botnet (malware) + CVE-2023-1234 (vulnerability)
- **Graph nodes**: Emotet, CVE-2023-1234, Banking Sector, Email Infrastructure, Malware Cluster
- **Graph edges**: exploits, targets, uses, memberOf, affects
- **SPARQL template**: Auto-generates a realistic SPARQL query from any input
- **Suggestion chips**: 3 pre-defined queries

---

## Design System

| Token          | Value         |
|----------------|---------------|
| Background     | `#050c1a`     |
| Card surface   | `#0e1c2f`     |
| Border         | `#1e3554`     |
| Text primary   | `#f0f4f8`     |
| Text muted     | `#64748b`     |
| Accent cyan    | `#38bdf8`     |
| Danger red     | `#f87171`     |
| Body font      | Inter         |
| Code font      | JetBrains Mono |

---

## Notes for Team

- This module is **frontend-only** and lives entirely inside `/frontend`
- No changes are made to root configs or other team folders
- To integrate with a real backend: replace `mockData.js` imports in `searchStore.js`
  with actual API calls to the MCP/SPARQL service
- The SPARQL accordion's `highlightedQuery` computed prop can be replaced with
  a real syntax highlighter (e.g., Prism.js or Shiki) in a future iteration

---

## Authors

SPARQL-MCP Kel-2 — Semester 4, MRPL  
*© 2024 CyberSignal. All rights reserved.*
