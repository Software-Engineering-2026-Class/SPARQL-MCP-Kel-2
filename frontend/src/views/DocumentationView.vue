<!-- =============================================================
  DocumentationView.vue — Documentation Page
  Three sections: NL Querying, Reading Results, SPARQL Transparency
  ============================================================= -->
<template>
  <div class="docs-root content-layer">
    <Header />

    <!-- ── Page Hero ───────────────────────────────────────── -->
    <section class="page-hero" aria-labelledby="docs-title">
      <div class="page-container">
        <p class="hero-eyebrow">Panduan Pengguna</p>
        <h1 id="docs-title" class="page-hero-title">CyberSec Search Documentation</h1>
        <p class="page-hero-subtitle">
          Panduan Penggunaan Sistem dan Analisis Knowledge Graph
        </p>
      </div>
    </section>

    <!-- ── Divider ─────────────────────────────────────────── -->
    <div class="section-divider" aria-hidden="true" />

    <!-- ── Main Content ───────────────────────────────────── -->
    <main id="docs-main" role="main" class="page-main">
      <div class="page-container">

        <!-- Table of contents (desktop sidebar concept as sticky label row) -->
        <nav class="toc-row" aria-label="Page sections">
          <a
            v-for="item in tocItems"
            :key="item.href"
            :href="item.href"
            class="toc-link"
          >
            <span class="toc-number">{{ item.num }}</span>
            {{ item.label }}
          </a>
        </nav>

        <!-- ── SECTION 1 — NATURAL LANGUAGE QUERYING ───────── -->
        <section id="section-nl" class="content-section" aria-labelledby="sec1-title">
          <SectionHeader
            id="sec1-title"
            eyebrow="Langkah 1"
            title="1. Melakukan Pencarian (Natural Language Querying)"
          />

          <InfoPanel accent="cyan">
            <template #icon>
              <!-- Search icon -->
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="w-5 h-5" aria-hidden="true">
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
              </svg>
            </template>
            <p>
              Anda tidak perlu menulis kode database untuk menggunakan sistem ini.
              Cukup ketik pertanyaan atau instruksi investigasi pada kolom pencarian menggunakan
              <strong>bahasa sehari-hari</strong>.
            </p>
          </InfoPanel>

          <!-- Example query card -->
          <div class="example-query-block">
            <p class="example-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="example-label-icon" aria-hidden="true">
                <path d="M9 11l3 3L22 4" />
                <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
              </svg>
              Contoh kueri:
            </p>
            <blockquote class="example-query">
              "Find the relationship between Emotet malware and CVE-2023-1234."
            </blockquote>
          </div>

          <!-- AI agent explanation -->
          <InfoPanel accent="none">
            <template #icon>
              <!-- CPU/agent icon -->
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="w-5 h-5" aria-hidden="true">
                <rect x="4" y="4" width="16" height="16" rx="2" />
                <rect x="9" y="9" width="6" height="6" />
                <path d="M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2" />
              </svg>
            </template>
            <p>
              Sistem AI (<strong>Query Agent</strong>) akan secara otomatis menerjemahkan pertanyaan
              menjadi kueri SPARQL yang valid dan menjalankannya terhadap Cybersecurity Knowledge Graph.
              Seluruh proses berlangsung di sisi server tanpa intervensi manual dari pengguna.
            </p>
          </InfoPanel>
        </section>

        <!-- ── SECTION 2 — UNDERSTANDING RESULTS ────────────── -->
        <section id="section-results" class="content-section" aria-labelledby="sec2-title">
          <SectionHeader
            id="sec2-title"
            eyebrow="Langkah 2"
            title="2. Membaca Hasil Analisis"
            description="Hasil pencarian disajikan dalam dua panel komplementer yang masing-masing memberikan perspektif berbeda terhadap data ancaman."
          />

          <div class="result-cards-grid">
            <!-- Card A: Extracted Entities -->
            <DocumentationCard
              title="Extracted Entities"
              description="Menampilkan kartu informasi ringkas mengenai entitas utama yang ditemukan, seperti tingkat keparahan (CVSS Score), malware activity, dan metadata ancaman lainnya."
            >
              <template #icon>
                <!-- Card / list icon -->
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="w-5 h-5" aria-hidden="true">
                  <rect x="2" y="3" width="20" height="14" rx="2" />
                  <path d="M8 21h8M12 17v4" />
                  <path d="M6 8h4M6 12h8" />
                </svg>
              </template>
            </DocumentationCard>

            <!-- Card B: Knowledge Graph -->
            <DocumentationCard
              title="Knowledge Graph Visualization"
              description="Menyediakan visualisasi relasi interaktif antar entitas seperti Malware, CVE, Server, atau Target Sector dalam sebuah diagram graf yang dapat di-drag dan di-zoom."
            >
              <template #icon>
                <!-- Graph/network icon -->
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="w-5 h-5" aria-hidden="true">
                  <circle cx="12" cy="5"  r="2" />
                  <circle cx="5"  cy="19" r="2" />
                  <circle cx="19" cy="19" r="2" />
                  <path d="M12 7v4M12 11l-5 6M12 11l5 6" />
                </svg>
              </template>
            </DocumentationCard>
          </div>

          <!-- Mini legend reference -->
          <div class="legend-reference" role="note" aria-label="Graph node types">
            <span class="legend-ref-label">Tipe Node Graf:</span>
            <span class="legend-ref-item">
              <span class="legend-ref-dot" style="border-color: #e2e8f0;" />
              Malware Core
            </span>
            <span class="legend-ref-item">
              <span class="legend-ref-dot" style="border-color: #f87171;" />
              Vulnerability
            </span>
            <span class="legend-ref-item">
              <span class="legend-ref-dot" style="border-color: #38bdf8;" />
              Target Sector
            </span>
          </div>
        </section>

        <!-- ── SECTION 3 — SPARQL TRANSPARENCY ──────────────── -->
        <section id="section-sparql" class="content-section" aria-labelledby="sec3-title">
          <SectionHeader
            id="sec3-title"
            eyebrow="Langkah 3"
            title="3. Transparansi Kueri (SPARQL Display)"
          />

          <InfoPanel accent="blue">
            <template #icon>
              <!-- Code icon -->
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="w-5 h-5" aria-hidden="true">
                <polyline points="16 18 22 12 16 6" />
                <polyline points="8 6 2 12 8 18" />
              </svg>
            </template>
            <p>
              Untuk keperluan audit atau modifikasi manual bagi <em>power user</em>, sistem menyediakan
              transparansi penuh terhadap kueri yang dihasilkan AI. Users dapat membuka dropdown
              <strong>"View Generated SPARQL Query"</strong> yang muncul tepat di bawah area pencarian
              pada halaman hasil.
            </p>
          </InfoPanel>

          <!-- Accordion preview indicator -->
          <div class="accordion-preview" aria-label="View Generated SPARQL Query preview">
            <div class="accordion-preview-bar">
              <span class="accordion-preview-label">View Generated SPARQL Query</span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="accordion-preview-chevron" aria-hidden="true">
                <path d="M6 9l6 6 6-6" />
              </svg>
            </div>
          </div>

          <!-- Example SPARQL snippet -->
          <CodeSnippet :code="exampleSparql" label="query.sparql · Contoh" />
        </section>

      </div>
    </main>

    <Footer />
  </div>
</template>

<script setup>
import Header            from '@/components/Header.vue'
import Footer            from '@/components/Footer.vue'
import SectionHeader     from '@/components/SectionHeader.vue'
import InfoPanel         from '@/components/InfoPanel.vue'
import DocumentationCard from '@/components/DocumentationCard.vue'
import CodeSnippet       from '@/components/CodeSnippet.vue'

// ── Data ──────────────────────────────────────────────────────

const tocItems = [
  { num: '01', label: 'Natural Language Querying', href: '#section-nl'      },
  { num: '02', label: 'Membaca Hasil Analisis',    href: '#section-results'  },
  { num: '03', label: 'Transparansi SPARQL',       href: '#section-sparql'   },
]

const exampleSparql = `PREFIX cyber:   <https://w3id.org/sepses/vocab/ref/cve#>
PREFIX malware: <https://w3id.org/sepses/vocab/ref/malware#>
PREFIX rdfs:    <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?entity ?label ?type ?cvss
WHERE {
  {
    ?entity a malware:MalwareFamily ;
            rdfs:label ?label .
    BIND("malware" AS ?type)
  }
  UNION
  {
    ?entity a cyber:CVE ;
            rdfs:label ?label ;
            cyber:cvssScore ?cvss .
    BIND("vulnerability" AS ?type)
  }
  FILTER(CONTAINS(LCASE(STR(?label)), "emotet"))
}
ORDER BY DESC(?cvss)
LIMIT 10`
</script>

<style scoped>
/* Root layout */
.docs-root {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* Shared container */
.page-container {
  max-width: 860px;
  margin: 0 auto;
  padding: 0 1.5rem;
  width: 100%;
  box-sizing: border-box;
}

/* ── Hero ────────────────────────────────────────────────── */
.page-hero {
  padding: 3.5rem 0 2.5rem;
  text-align: center;
}

.hero-eyebrow {
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #38bdf8;
  margin-bottom: 0.875rem;
}

.page-hero-title {
  font-size: clamp(1.75rem, 4vw, 2.75rem);
  font-weight: 800;
  color: #f0f4f8;
  letter-spacing: -0.03em;
  line-height: 1.1;
  margin: 0 0 0.875rem;
}

.page-hero-subtitle {
  font-size: 0.9375rem;
  color: #64748b;
  margin: 0;
}

/* Hairline divider */
.section-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, #1e3554 20%, #1e3554 80%, transparent);
  max-width: 860px;
  margin: 0 auto;
}

/* ── Main ────────────────────────────────────────────────── */
.page-main {
  flex: 1;
  padding: 2.5rem 0 3.5rem;
}

/* ── Table of Contents Row ───────────────────────────────── */
.toc-row {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
  margin-bottom: 3rem;
  padding: 0.625rem;
  background-color: #0a1628;
  border: 1px solid #1e3554;
  border-radius: 0.5rem;
}

.toc-link {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.35rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: #64748b;
  text-decoration: none;
  transition: background-color 0.15s, color 0.15s;
}

.toc-link:hover {
  background-color: rgba(30, 53, 84, 0.5);
  color: #94a3b8;
}

.toc-number {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6875rem;
  color: #38bdf8;
  letter-spacing: 0.05em;
}

/* ── Content sections ────────────────────────────────────── */
.content-section {
  margin-bottom: 3.5rem;
  scroll-margin-top: 80px; /* offset for sticky header */
}

.content-section:last-child {
  margin-bottom: 0;
}

/* Gap between stacked InfoPanels */
.content-section > .info-panel + .info-panel,
.content-section > * + * {
  margin-top: 0.875rem;
}

/* ── Example Query Block ─────────────────────────────────── */
.example-query-block {
  margin: 1rem 0;
  padding: 1.125rem 1.375rem;
  background-color: #0e1c2f;
  border: 1px solid #1e3554;
  border-radius: 0.5rem;
  border-left: 3px solid rgba(56, 189, 248, 0.4);
}

.example-label {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #475569;
  margin-bottom: 0.625rem;
}

.example-label-icon {
  width: 13px;
  height: 13px;
  color: #34d399;
}

.example-query {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.875rem;
  color: #f0f4f8;
  font-style: italic;
  margin: 0;
  border: none;
  padding: 0;
  quotes: none;
}

/* ── Result Cards Grid ───────────────────────────────────── */
.result-cards-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

/* ── Legend Reference ────────────────────────────────────── */
.legend-reference {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 0.625rem 0.875rem;
  background-color: #0a1628;
  border: 1px solid #1e3554;
  border-radius: 0.375rem;
  font-size: 0.75rem;
}

.legend-ref-label {
  color: #475569;
  font-weight: 600;
  letter-spacing: 0.03em;
  margin-right: 0.25rem;
}

.legend-ref-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  color: #64748b;
}

.legend-ref-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid;
  background: transparent;
  flex-shrink: 0;
}

/* ── Accordion Preview Bar ───────────────────────────────── */
.accordion-preview {
  margin: 1rem 0;
  border-radius: 0.5rem;
  overflow: hidden;
  border: 1px solid #1e3554;
}

.accordion-preview-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.25rem;
  background-color: #0a1628;
  cursor: default;
}

.accordion-preview-label {
  font-size: 0.9rem;
  font-weight: 500;
  color: #94a3b8;
}

.accordion-preview-chevron {
  width: 16px;
  height: 16px;
  color: #475569;
}

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 640px) {
  .result-cards-grid {
    grid-template-columns: 1fr;
  }

  .toc-row {
    gap: 0;
  }

  .page-hero {
    padding: 2.5rem 0 1.75rem;
  }
}
</style>
