<!-- =============================================================
  GraphCanvas.vue — Knowledge Graph Visualization (vis-network)
  Interactive, draggable node graph with relationship edges.
  Matches the minimalist connected-circles aesthetic in the screenshot.
  ============================================================= -->
<template>
  <div class="graph-panel" role="region" aria-label="Knowledge Graph Visualization">
    <!-- Panel header -->
    <div class="graph-header">
      <h3 class="graph-title">Knowledge Graph Visualization</h3>
      <div class="graph-controls">
        <!-- Zoom in -->
        <button
          id="graph-zoom-in"
          class="graph-ctrl-btn"
          type="button"
          aria-label="Zoom in"
          title="Zoom In"
          @click="zoomIn"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3.5 h-3.5">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35M11 8v6M8 11h6" />
          </svg>
        </button>
        <!-- Zoom out -->
        <button
          id="graph-zoom-out"
          class="graph-ctrl-btn"
          type="button"
          aria-label="Zoom out"
          title="Zoom Out"
          @click="zoomOut"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3.5 h-3.5">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35M8 11h6" />
          </svg>
        </button>
        <!-- Fit / reset view -->
        <button
          id="graph-fit"
          class="graph-ctrl-btn"
          type="button"
          aria-label="Fit graph to view"
          title="Fit to View"
          @click="fitGraph"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3.5 h-3.5">
            <path d="M8 3H5a2 2 0 00-2 2v3M16 3h3a2 2 0 012 2v3M8 21H5a2 2 0 01-2-2v-3M16 21h3a2 2 0 002-2v-3" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Graph canvas container -->
    <div ref="graphContainer" class="graph-canvas" aria-label="Interactive knowledge graph" />

    <!-- Legend -->
    <div class="graph-legend" role="list" aria-label="Graph node legend">
      <div
        v-for="item in legend"
        :key="item.label"
        class="legend-item"
        role="listitem"
      >
        <span
          class="legend-dot"
          :style="{ borderColor: item.color, backgroundColor: item.fill }"
          aria-hidden="true"
        />
        <span class="legend-label">{{ item.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { Network, DataSet } from 'vis-network/standalone'
import { mockGraphNodes, mockGraphEdges } from '@/data/mockData.js'

// ── Refs ─────────────────────────────────────────────────────
const graphContainer = ref(null)
let network = null

// ── Legend Data ───────────────────────────────────────────────
const legend = [
  { label: 'Malware Core',  color: '#e2e8f0', fill: 'transparent' },
  { label: 'Vulnerability', color: '#f87171', fill: 'transparent' },
  { label: 'Target Sector', color: '#38bdf8', fill: 'transparent' },
]

// ── Node Style per Group ──────────────────────────────────────
const groupStyles = {
  malware: {
    color: {
      border:     '#e2e8f0',
      background: 'transparent',
      highlight:  { border: '#ffffff', background: 'rgba(255,255,255,0.08)' },
      hover:      { border: '#ffffff', background: 'rgba(255,255,255,0.06)' },
    },
    font:         { color: '#cbd5e1', size: 11, face: 'Inter, sans-serif' },
    borderWidth:  2,
    shape:        'circle',
  },
  vulnerability: {
    color: {
      border:     '#f87171',
      background: 'transparent',
      highlight:  { border: '#fca5a5', background: 'rgba(248,113,113,0.1)' },
      hover:      { border: '#fca5a5', background: 'rgba(248,113,113,0.08)' },
    },
    font:         { color: '#fca5a5', size: 11, face: 'Inter, sans-serif' },
    borderWidth:  2,
    shape:        'circle',
  },
  target: {
    color: {
      border:     '#38bdf8',
      background: 'transparent',
      highlight:  { border: '#7dd3fc', background: 'rgba(56,189,248,0.1)' },
      hover:      { border: '#7dd3fc', background: 'rgba(56,189,248,0.08)' },
    },
    font:         { color: '#7dd3fc', size: 11, face: 'Inter, sans-serif' },
    borderWidth:  2,
    shape:        'circle',
  },
}

// ── vis-network Options ───────────────────────────────────────
const networkOptions = {
  nodes: {
    shape: 'circle',
    size:  24,
    font: {
      size:  11,
      face:  'Inter, sans-serif',
      color: '#cbd5e1',
      vadjust: 0,
    },
    borderWidth: 2,
    borderWidthSelected: 3,
    chosen: true,
  },
  edges: {
    color: {
      color:     'rgba(100, 116, 139, 0.5)',
      highlight: 'rgba(148, 163, 184, 0.8)',
      hover:     'rgba(148, 163, 184, 0.6)',
    },
    width:  1,
    smooth: {
      type:       'curvedCW',
      roundness:  0.1,
    },
    arrows: {
      to: {
        enabled:   true,
        scaleFactor: 0.6,
      }
    },
    font: {
      size:       9,
      face:       'Inter, sans-serif',
      color:      '#475569',
      strokeWidth: 0,
      align:      'middle',
    },
    length: 180,
  },
  physics: {
    enabled: true,
    barnesHut: {
      gravitationalConstant: -5000,
      centralGravity:        0.1,
      springLength:          180,
      springConstant:        0.04,
      damping:               0.3,
    },
    stabilization: {
      iterations: 200,
      updateInterval: 25,
    },
  },
  interaction: {
    hover:         true,
    tooltipDelay:  200,
    zoomView:      true,
    dragView:      true,
    dragNodes:     true,
    multiselect:   false,
    navigationButtons: false,
    keyboard:      false,
  },
  layout: {
    randomSeed: 42, // deterministic layout
  },
  groups: groupStyles,
}

// ── Lifecycle ─────────────────────────────────────────────────
onMounted(async () => {
  await nextTick()

  if (!graphContainer.value) return

  // Build vis DataSets
  const nodes = new DataSet(
    mockGraphNodes.map(n => ({
      ...n,
      group: n.group,
    }))
  )

  const edges = new DataSet(mockGraphEdges)

  // Initialise network
  network = new Network(graphContainer.value, { nodes, edges }, networkOptions)

  // After stabilisation, disable physics for free drag
  network.once('stabilizationIterationsDone', () => {
    network.setOptions({ physics: { enabled: false } })
  })
})

onUnmounted(() => {
  if (network) {
    network.destroy()
    network = null
  }
})

// ── Graph Controls ─────────────────────────────────────────────
function zoomIn()  { network?.moveTo({ scale: network.getScale() * 1.25 }) }
function zoomOut() { network?.moveTo({ scale: network.getScale() * 0.8  }) }
function fitGraph() {
  network?.fit({
    animation: { duration: 400, easingFunction: 'easeInOutQuad' }
  })
}
</script>

<style scoped>
/* Panel */
.graph-panel {
  background-color: #0e1c2f;
  border: 1px solid #1e3554;
  border-radius: 0.5rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 420px;
}

/* Header */
.graph-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1.125rem;
  border-bottom: 1px solid #1e3554;
  flex-shrink: 0;
}

.graph-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #f0f4f8;
  margin: 0;
  letter-spacing: -0.01em;
}

.graph-controls {
  display: flex;
  gap: 0.375rem;
}

.graph-ctrl-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 0.25rem;
  border: 1px solid #1e3554;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}

.graph-ctrl-btn:hover {
  color: #94a3b8;
  border-color: #334155;
}

/* Canvas area */
.graph-canvas {
  flex: 1;
  min-height: 320px;
  background-color: #070f1d;
  cursor: grab;
}

.graph-canvas:active {
  cursor: grabbing;
}

/* Legend */
.graph-legend {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.625rem 1.125rem;
  border-top: 1px solid #1e3554;
  background-color: #0a1628;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border-width: 2px;
  border-style: solid;
  flex-shrink: 0;
}

.legend-label {
  font-size: 0.75rem;
  color: #64748b;
  white-space: nowrap;
}
</style>
