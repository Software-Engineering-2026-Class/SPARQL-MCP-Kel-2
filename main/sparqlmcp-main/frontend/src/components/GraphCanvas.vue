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
    <div ref="graphContainer" class="graph-canvas" aria-label="Interactive knowledge graph"></div>

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
import { ref, onMounted, onUnmounted, nextTick, watch, computed } from 'vue'
import { Network, DataSet } from 'vis-network/standalone'
import { mockGraphNodes, mockGraphEdges } from '@/data/mockData.js'

// ── Refs ─────────────────────────────────────────────────────
const graphContainer = ref(null)
let network = null

const props = defineProps({
  entities: {
    type: Array,
    default: () => []
  },
  graph: {
    type: Object,
    default: null
  }
})

function normalizeGroup(type) {
  const value = String(type || '').toLowerCase()
  if (
    value.includes('vuln') ||
    value.includes('cve') ||
    value.includes('cwe') ||
    value.includes('cvss') ||
    value.includes('reference')
  ) return 'vulnerability'
  if (value.includes('malware') || value.includes('threat') || value.includes('family')) return 'malware'
  if (value.includes('cpe') || value.includes('product') || value.includes('vendor')) return 'target'
  return 'target'
}

function buildLiveGraph(entities) {
  if (!entities.length) {
    return { nodes: mockGraphNodes, edges: mockGraphEdges }
  }

  const root = {
    id: 'search-root',
    label: entities[0]?.displayLabel || entities[0]?.title || 'Search Results',
    group: normalizeGroup(entities[0]?.group || entities[0]?.type || entities[0]?.kind || entities[0]?.subtitle),
    size: 30
  }

  const nodes = [root]
  const edges = []
  const seen = new Set([root.id])

  entities.slice(0, 8).forEach((entity, index) => {
    const nodeId = entity.uri || entity.id || `entity-${index}`
    if (!seen.has(nodeId)) {
      seen.add(nodeId)
      nodes.push({
        id: nodeId,
        label: entity.displayLabel || entity.title || `Entity ${index + 1}`,
        group: normalizeGroup(entity.group || entity.type || entity.kind || entity.subtitle),
        size: index === 0 ? 24 : 20
      })
    }

    edges.push({
      from: root.id,
      to: nodeId,
      label: entity.subtitle || entity.type || 'result',
      arrows: 'to'
    })

    entity.tags?.slice(0, 2).forEach((tag, tagIndex) => {
      const tagId = `${nodeId}-tag-${tagIndex}-${tag}`
      if (!seen.has(tagId)) {
        seen.add(tagId)
        nodes.push({
          id: tagId,
          label: tag,
          group: 'target',
          size: 16
        })
      }
      edges.push({
        from: nodeId,
        to: tagId,
        label: 'tag',
        arrows: 'to'
      })
    })
  })

  return { nodes, edges }
}

const graphData = computed(() => buildLiveGraph(props.entities))

const liveGraphData = computed(() => {
  // Prefer a backend-provided graph only when it has proper nodes/edges arrays.
  if (
    props.graph &&
    props.graph.nodes &&
    props.graph.edges &&
    Array.isArray(props.graph.nodes) &&
    Array.isArray(props.graph.edges)
  ) {
    return props.graph
  }
  // Otherwise fall back to the entity-derived graph
  return graphData.value
})

const useSpiralLayout = computed(() => Boolean(liveGraphData.value.nodes.length > 0))

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
    enabled: false,
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
  renderGraph()
})

watch(
  () => [props.entities, props.graph],
  async () => {
    await nextTick()
    renderGraph()
  },
  { deep: true }
)

onUnmounted(() => {
  if (network) {
    network.destroy()
    network = null
  }
})

function renderGraph() {
  if (!graphContainer.value) return

  if (network) {
    network.destroy()
    network = null
  }

  // Normalize nodes/edges: backend may send arrays, objects, or proxy-like values — coerce to safe arrays.
  const rawNodes = (liveGraphData.value && liveGraphData.value.nodes) || []
  const rawEdges = (liveGraphData.value && liveGraphData.value.edges) || []

  let nodesList
  let edgesList
  try {
    if (Array.isArray(rawNodes)) nodesList = rawNodes
    else if (rawNodes && typeof rawNodes === 'object' && typeof rawNodes.length === 'number') nodesList = Array.from(rawNodes)
    else if (rawNodes && typeof rawNodes === 'object') nodesList = Object.values(rawNodes)
    else nodesList = []

    if (Array.isArray(rawEdges)) edgesList = rawEdges
    else if (rawEdges && typeof rawEdges === 'object' && typeof rawEdges.length === 'number') edgesList = Array.from(rawEdges)
    else if (rawEdges && typeof rawEdges === 'object') edgesList = Object.values(rawEdges)
    else edgesList = []
  } catch (e) {
    console.warn('GraphCanvas: failed to normalize raw graph shapes, falling back to empty arrays', { rawNodes, rawEdges, err: e })
    nodesList = []
    edgesList = []
  }

  // Build spiral positions from normalized nodes list using a defensive loop (avoid relying on .map)
  const spiralNodes = []
  for (let index = 0; index < (nodesList && nodesList.length ? nodesList.length : 0); index++) {
    const node = nodesList[index] || {}
    const angle = index * 2.399963229728653
    const radius = 70 + index * 42
    const x = Math.cos(angle) * radius
    const y = Math.sin(angle) * radius

    spiralNodes.push({
      ...(typeof node === 'object' ? node : {}),
      group: node?.group,
      x,
      y,
      fixed: { x: false, y: false },
    })
  }
  // Simple collision-avoidance to reduce node overlap while keeping spiral order.
  // This nudges nodes apart if they are closer than `minDist` for a few iterations.
  // Lightweight collision-avoidance: reduce overlap but keep nodes near spiral.
  // Lowered minDist and fewer iterations to avoid excessive displacement.
  (function resolveCollisions(nodesArray) {
    const minDist = 40 // minimum distance between node centers (reduced)
    const iterations = 2 // fewer passes to avoid pushing nodes off-screen
    for (let it = 0; it < iterations; it++) {
      for (let i = 0; i < nodesArray.length; i++) {
        for (let j = i + 1; j < nodesArray.length; j++) {
          const a = nodesArray[i]
          const b = nodesArray[j]
          const dx = b.x - a.x
          const dy = b.y - a.y
          let dist = Math.sqrt(dx * dx + dy * dy) || 0.0001
          if (dist < minDist) {
            const overlap = (minDist - dist) / 2
            const nx = dx / dist
            const ny = dy / dist
            a.x -= nx * overlap * 0.6
            a.y -= ny * overlap * 0.6
            b.x += nx * overlap * 0.6
            b.y += ny * overlap * 0.6
          }
        }
      }
    }
  })(spiralNodes)

  // Detect connected components so we can separate them spatially and avoid overlapping
  // Build adjacency map from edgesList (defensive: edges may be objects with from/to)
  const adjacency = {}
  try {
    for (let i = 0; i < edgesList.length; i++) {
      const e = edgesList[i] || {}
      const a = e.from || e.source || e.f || null
      const b = e.to   || e.target || e.t || null
      if (!a || !b) continue
      if (!adjacency[a]) adjacency[a] = new Set()
      if (!adjacency[b]) adjacency[b] = new Set()
      adjacency[a].add(b)
      adjacency[b].add(a)
    }
  } catch (e) {
    console.warn('GraphCanvas: adjacency build failed', e)
  }

  // BFS to enumerate components
  const visited = new Set()
  const components = []
  for (let i = 0; i < spiralNodes.length; i++) {
    const nid = spiralNodes[i].id
    if (!nid || visited.has(nid)) continue
    const comp = []
    const queue = [nid]
    visited.add(nid)
    while (queue.length) {
      const cur = queue.shift()
      comp.push(cur)
      const neighbors = adjacency[cur]
      if (neighbors) {
        for (const nb of neighbors) {
          if (!visited.has(nb)) {
            visited.add(nb)
            queue.push(nb)
          }
        }
      }
    }
    components.push(comp)
  }

  // Place each component spatially so they don't overlap by computing per-component
  // bounding radius and laying out component centers on a circle with enough separation.
  if (components.length > 1) {
    // map node id -> node object for quick lookup
    const nodeById = {}
    for (const n of spiralNodes) nodeById[n.id] = n

    // compute per-component centroid and radius (max distance from centroid)
    const compMeta = components.map((comp) => {
      const nodes = comp.map((id) => nodeById[id]).filter(Boolean)
      if (!nodes.length) return { nodes: [], cx: 0, cy: 0, r: 0 }
      const cx = nodes.reduce((s, p) => s + (p.x || 0), 0) / nodes.length
      const cy = nodes.reduce((s, p) => s + (p.y || 0), 0) / nodes.length
      let r = 0
      for (const p of nodes) {
        const dx = (p.x || 0) - cx
        const dy = (p.y || 0) - cy
        const d = Math.sqrt(dx * dx + dy * dy)
        if (d > r) r = d
      }
      // add padding so edges and labels don't collide
      return { nodes, cx, cy, r: r + 60 }
    })

    const k = compMeta.length
    // when k is small, use a minimum circle radius; otherwise compute radius to satisfy separation
    const paddingBetween = 80
    let circleR = 800
    if (k > 1) {
      // compute max required separation between adjacent component centers
      let maxReq = 0
      for (let i = 0; i < k; i++) {
        for (let j = i + 1; j < k; j++) {
          const req = compMeta[i].r + compMeta[j].r + paddingBetween
          if (req > maxReq) maxReq = req
        }
      }
      const angle = Math.PI / k
      const denom = Math.max(Math.sin(angle), 0.001)
      circleR = Math.max(circleR, (maxReq) / (2 * denom))
    }

    // place component centers evenly on the circle
    const centerOffsetX = 0
    const centerOffsetY = 0
    for (let i = 0; i < compMeta.length; i++) {
      const theta = (i / compMeta.length) * Math.PI * 2
      const cx = Math.cos(theta) * circleR + centerOffsetX
      const cy = Math.sin(theta) * circleR + centerOffsetY
      for (const node of compMeta[i].nodes) {
        node.x = (node.x || 0) - compMeta[i].cx + cx
        node.y = (node.y || 0) - compMeta[i].cy + cy
      }
    }

    // Adjust edge lengths: short inside component, longer between components
    const compIndexById = {}
    components.forEach((comp, ci) => { for (const id of comp) compIndexById[id] = ci })
    for (let i = 0; i < edgesList.length; i++) {
      try {
        const e = edgesList[i]
        const from = e.from || e.source || e.f
        const to = e.to || e.target || e.t
        const ciFrom = compIndexById[from]
        const ciTo = compIndexById[to]
        if (ciFrom !== undefined && ciTo !== undefined && ciFrom === ciTo) {
          e.length = e.length || 120
        } else {
          e.length = e.length || 360
        }
      } catch (ee) {
        // ignore
      }
    }
  }

  let nodes
  let edges
  try {
    nodes = new DataSet(spiralNodes)
  } catch (err) {
    console.error('GraphCanvas: failed to build nodes DataSet', err)
    nodes = new DataSet([])
  }

  try {
    edges = new DataSet(edgesList)
  } catch (err) {
    console.error('GraphCanvas: failed to build edges DataSet', err)
    edges = new DataSet([])
  }

  const options = {
    ...networkOptions,
    layout: {
      ...networkOptions.layout,
      improvedLayout: false,
    },
    physics: {
      enabled: false,
    },
  }

  network = new Network(graphContainer.value, { nodes, edges }, options)
  // Debug: log number of nodes/edges so we can see rendering in browser console
  try {
    console.info('GraphCanvas: rendering graph', {
      nodeCount: Array.isArray(nodesList) ? nodesList.length : (nodesList && nodesList.length) || 0,
      edgeCount: Array.isArray(edgesList) ? edgesList.length : (edgesList && edgesList.length) || 0,
      useSpiral: useSpiralLayout.value,
      rawNodesType: Array.isArray(rawNodes) ? 'array' : typeof rawNodes,
    })
  } catch (e) {
    console.warn('GraphCanvas: logging failed', e)
  }

  // Auto-fit the graph to the viewport so nodes are visible
  try {
    network.fit({ animation: { duration: 250 } })
  } catch (e) {
    // ignore
  }
  // expose for debugging
  try { window.__GraphNetwork = network } catch (_) {}
}

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
