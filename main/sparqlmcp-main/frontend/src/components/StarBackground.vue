<!-- =============================================================
  StarBackground.vue — Animated Constellation/Star Canvas
  Renders a canvas with stars, faint connection lines, and
  subtle particle drift to match the screenshot aesthetic.
  ============================================================= -->
<template>
  <canvas
    ref="canvasRef"
    class="bg-stars-canvas"
    aria-hidden="true"
  />
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const canvasRef = ref(null)
let animationId = null
let ctx = null
let stars = []
let W = 0
let H = 0

// ── Star Configuration ──────────────────────────────────────

const STAR_COUNT     = 160   // total stars
const CONN_DIST      = 140   // max distance to draw a connection line
const CONN_COUNT_MAX = 3     // max connections per star (constellation feel)

/**
 * Creates a single star object with random position and drift velocity.
 */
function createStar() {
  return {
    x:        Math.random() * W,
    y:        Math.random() * H,
    r:        Math.random() * 1.4 + 0.3,   // radius 0.3–1.7px
    opacity:  Math.random() * 0.6 + 0.2,    // opacity 0.2–0.8
    vx:       (Math.random() - 0.5) * 0.08, // drift speed
    vy:       (Math.random() - 0.5) * 0.08,
    twinkle:  Math.random() * Math.PI * 2,  // twinkle phase offset
  }
}

/** Resizes canvas to full viewport */
function resize() {
  W = window.innerWidth
  H = window.innerHeight
  if (canvasRef.value) {
    canvasRef.value.width  = W
    canvasRef.value.height = H
  }
}

/** Initialises star field */
function initStars() {
  stars = Array.from({ length: STAR_COUNT }, createStar)
}

/** Main animation loop */
function draw(time) {
  ctx.clearRect(0, 0, W, H)

  // Update and draw each star
  for (let i = 0; i < stars.length; i++) {
    const s = stars[i]

    // Drift movement
    s.x += s.vx
    s.y += s.vy

    // Wrap around edges
    if (s.x < 0)  s.x = W
    if (s.x > W)  s.x = 0
    if (s.y < 0)  s.y = H
    if (s.y > H)  s.y = 0

    // Twinkle: subtle opacity oscillation
    const twinkleVal = Math.sin(time * 0.001 + s.twinkle) * 0.15
    const alpha = Math.max(0.05, s.opacity + twinkleVal)

    // Draw star dot
    ctx.beginPath()
    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(200, 220, 255, ${alpha})`
    ctx.fill()

    // Draw constellation lines (faint)
    let conns = 0
    for (let j = i + 1; j < stars.length && conns < CONN_COUNT_MAX; j++) {
      const dx   = s.x - stars[j].x
      const dy   = s.y - stars[j].y
      const dist = Math.sqrt(dx * dx + dy * dy)

      if (dist < CONN_DIST) {
        // Opacity fades with distance
        const lineAlpha = (1 - dist / CONN_DIST) * 0.06
        ctx.beginPath()
        ctx.moveTo(s.x, s.y)
        ctx.lineTo(stars[j].x, stars[j].y)
        ctx.strokeStyle = `rgba(150, 190, 240, ${lineAlpha})`
        ctx.lineWidth = 0.5
        ctx.stroke()
        conns++
      }
    }
  }

  animationId = requestAnimationFrame(draw)
}

onMounted(() => {
  if (!canvasRef.value) return
  ctx = canvasRef.value.getContext('2d')
  resize()
  initStars()
  animationId = requestAnimationFrame(draw)
  window.addEventListener('resize', resize)
})

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId)
  window.removeEventListener('resize', resize)
})
</script>
