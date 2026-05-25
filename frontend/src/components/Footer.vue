<!-- =============================================================
  Footer.vue — Persistent Site Footer
  Matches the minimal footer from both screenshots.
  ============================================================= -->
<template>
  <footer class="site-footer" role="contentinfo">
    <!-- Copyright -->
    <p class="footer-copy" aria-label="Copyright">
      &copy; {{ currentYear }} CyberSignal. All rights reserved.
    </p>

    <!-- Footer links -->
    <nav class="footer-links" aria-label="Footer navigation">
      <a id="footer-privacy"  href="#" class="footer-link" @click.prevent>Privacy Policy</a>
      <a id="footer-terms"    href="#" class="footer-link" @click.prevent>Terms of Service</a>
      <a id="footer-status"   href="#" class="footer-link footer-link-status" @click.prevent>
        <span class="status-dot" aria-hidden="true" />
        Status
      </a>
    </nav>
  </footer>
</template>

<script setup>
const currentYear = new Date().getFullYear()
</script>

<style scoped>
.site-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-top: 1px solid #1e3554;
  background-color: #050c1a;
  flex-wrap: wrap;
  gap: 0.5rem;
  position: relative;
  z-index: 1;
}

.footer-copy {
  font-size: 0.75rem;
  color: #475569;
}

.footer-links {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.footer-link {
  font-size: 0.75rem;
  color: #475569;
  text-decoration: underline;
  text-underline-offset: 2px;
  cursor: pointer;
  transition: color 0.15s;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.footer-link:hover {
  color: #94a3b8;
}

/* Status dot (green pulse) */
.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #34d399;
  animation: pulse-dot 2s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
}
</style>
