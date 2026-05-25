<!-- =============================================================
  AboutView.vue — About Page
  Three sections: Project Description, Team, Technology
  Maintains the dark-navy cybersecurity aesthetic.
  ============================================================= -->
<template>
  <div class="about-root content-layer">
    <Header />

    <!-- ── Page Hero ───────────────────────────────────────── -->
    <section class="page-hero" aria-labelledby="about-title">
      <div class="page-container">
        <p class="hero-eyebrow">Kelompok 2 · MRPL · Semester 4</p>
        <h1 id="about-title" class="page-hero-title">About CyberSec Search</h1>
        <p class="page-hero-subtitle">
          Agentic AI-based Cybersecurity Knowledge Exploration Platform
        </p>
      </div>
    </section>

    <!-- ── Divider ─────────────────────────────────────────── -->
    <div class="section-divider" aria-hidden="true" />

    <!-- ── Main Content ───────────────────────────────────── -->
    <main id="about-main" role="main" class="page-main">
      <div class="page-container">

        <!-- SECTION 1 — PROJECT DESCRIPTION ─────────────── -->
        <section class="content-section" aria-labelledby="section-desc">
          <SectionHeader
            id="section-desc"
            eyebrow="Tentang Sistem"
            title="Tentang CyberSec Search"
          />

          <div class="desc-grid">
            <!-- Main description paragraphs -->
            <div class="desc-text">
              <p>
                CyberSec Search adalah antarmuka mesin pencari cerdas yang dibangun sebagai bagian dari
                implementasi proyek <strong>Agentic AI-based Security Analysis</strong>.
              </p>
              <p>
                Sistem ini dirancang untuk membantu analis keamanan siber dalam mengeksplorasi dan
                memahami data dari <strong>Cybersecurity Knowledge Graphs (CSKG)</strong> menggunakan
                pendekatan Model Context Protocol (MCP).
              </p>
              <p>
                Dengan memanfaatkan arsitektur Multi-Agent, pengguna dapat melakukan kueri keamanan
                siber kompleks menggunakan bahasa natural tanpa harus memahami sintaks database
                secara manual.
              </p>
            </div>

            <!-- Quick stats sidebar -->
            <div class="desc-stats">
              <div
                v-for="stat in projectStats"
                :key="stat.label"
                class="stat-item"
              >
                <span class="stat-value">{{ stat.value }}</span>
                <span class="stat-label">{{ stat.label }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- SECTION 2 — DEVELOPMENT TEAM ────────────────── -->
        <section class="content-section" aria-labelledby="section-team">
          <SectionHeader
            id="section-team"
            eyebrow="Tim Pengembang"
            title="Tim Pengembang (Kelompok 2)"
            description="Terdiri dari empat anggota dengan peran yang saling melengkapi dalam pengembangan platform ini."
          />

          <div class="team-grid">
            <TeamMemberCard
              v-for="(member, i) in teamMembers"
              :key="member.name"
              :name="member.name"
              :role="member.role"
              :color-index="i"
            />
          </div>
        </section>

        <!-- SECTION 3 — TECHNOLOGY & ATTRIBUTION ─────────── -->
        <section class="content-section" aria-labelledby="section-tech">
          <SectionHeader
            id="section-tech"
            eyebrow="Teknologi & Atribusi"
            title="Teknologi &amp; Atribusi"
          />

          <div class="tech-panels">
            <!-- UI/UX Attribution -->
            <InfoPanel title="UI/UX Inspirasi" accent="cyan">
              <template #icon>
                <!-- Globe icon -->
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="w-5 h-5" aria-hidden="true">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M2 12h20M12 2a15.3 15.3 0 010 20M12 2a15.3 15.3 0 000 20" />
                </svg>
              </template>
              <p>
                Antarmuka dan pengalaman pengguna (UI/UX) sistem ini terinspirasi oleh kebersihan dan
                fungsionalitas pencarian akademik dari <strong style="color: #f0f4f8;">WU Search AI</strong>
                — sistem pencarian berbasis pengetahuan yang dikembangkan oleh Wirtschaftsuniversität Wien.
              </p>
            </InfoPanel>

            <!-- Data & Backend -->
            <InfoPanel title="Data &amp; Infrastruktur" accent="blue">
              <template #icon>
                <!-- Database icon -->
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="w-5 h-5" aria-hidden="true">
                  <ellipse cx="12" cy="5" rx="9" ry="3" />
                  <path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5" />
                  <path d="M3 12c0 1.66 4.03 3 9 3s9-1.34 9-3" />
                </svg>
              </template>
              <p>
                Sistem pemrosesan data didukung oleh integrasi <strong style="color: #f0f4f8;">SPARQL-MCP</strong>
                dan memanfaatkan dataset <strong style="color: #f0f4f8;">SEPSES CSKG</strong> untuk memetakan
                entitas ancaman, kerentanan, dan relasi serangan siber dalam sebuah knowledge graph terstruktur.
              </p>
            </InfoPanel>
          </div>

          <!-- Tech stack chips -->
          <div class="tech-chips" role="list" aria-label="Technology stack">
            <span
              v-for="tech in techStack"
              :key="tech"
              class="tech-chip"
              role="listitem"
            >
              {{ tech }}
            </span>
          </div>
        </section>

      </div>
    </main>

    <Footer />
  </div>
</template>

<script setup>
import Header         from '@/components/Header.vue'
import Footer         from '@/components/Footer.vue'
import SectionHeader  from '@/components/SectionHeader.vue'
import InfoPanel      from '@/components/InfoPanel.vue'
import TeamMemberCard from '@/components/TeamMemberCard.vue'

// ── Data ──────────────────────────────────────────────────────

const teamMembers = [
  { name: 'Arnoldus Dharma Wasesa M.', role: 'Agent Developer'    },
  { name: 'Hafidz Kurniawan Nahruntoko', role: 'Data Engineer'    },
  { name: 'Adzrha Auryn Alius',        role: 'Web Developer'      },
  { name: 'Jessy Marcia Anabel',       role: 'Quality Assurance'  },
]

const projectStats = [
  { value: 'Vue 3',       label: 'Frontend Framework'      },
  { value: 'SPARQL',      label: 'Query Language'          },
  { value: 'SEPSES CSKG', label: 'Knowledge Graph Dataset' },
  { value: 'MCP',         label: 'Agent Protocol'          },
]

const techStack = [
  'Vue 3', 'Vite', 'Pinia', 'Vue Router', 'TailwindCSS',
  'vis-network', 'SPARQL-MCP', 'SEPSES CSKG'
]
</script>

<style scoped>
/* Root layout */
.about-root {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* Shared container */
.page-container {
  max-width: 900px;
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
  max-width: 900px;
  margin: 0 auto;
}

/* ── Main ────────────────────────────────────────────────── */
.page-main {
  flex: 1;
  padding: 2.5rem 0 3.5rem;
}

/* Content section */
.content-section {
  margin-bottom: 3.5rem;
}

.content-section:last-child {
  margin-bottom: 0;
}

/* ── Section 1: Description ──────────────────────────────── */
.desc-grid {
  display: grid;
  grid-template-columns: 1fr 200px;
  gap: 2rem;
  align-items: start;
}

.desc-text {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  font-size: 0.9375rem;
  color: #94a3b8;
  line-height: 1.75;
}

.desc-text strong {
  color: #f0f4f8;
  font-weight: 600;
}

/* Stats sidebar */
.desc-stats {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  padding: 0.875rem 1rem;
  background-color: #0e1c2f;
  border: 1px solid #1e3554;
  border-radius: 0.5rem;
  gap: 0.25rem;
}

.stat-value {
  font-size: 0.8125rem;
  font-weight: 700;
  color: #38bdf8;
  letter-spacing: -0.01em;
}

.stat-label {
  font-size: 0.6875rem;
  color: #475569;
  letter-spacing: 0.03em;
}

/* ── Section 2: Team ─────────────────────────────────────── */
.team-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

/* ── Section 3: Technology ───────────────────────────────── */
.tech-panels {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
  margin-bottom: 1.5rem;
}

/* Tech stack chips */
.tech-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tech-chip {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  border: 1px solid #1e3554;
  background-color: rgba(30, 53, 84, 0.3);
  font-size: 0.75rem;
  font-weight: 500;
  color: #64748b;
  transition: border-color 0.15s, color 0.15s;
}

.tech-chip:hover {
  border-color: rgba(56, 189, 248, 0.3);
  color: #94a3b8;
}

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 768px) {
  .desc-grid {
    grid-template-columns: 1fr;
  }

  .desc-stats {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .stat-item {
    flex: 1 1 calc(50% - 0.5rem);
  }

  .team-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .team-grid {
    grid-template-columns: 1fr;
  }

  .stat-item {
    flex: 1 1 100%;
  }

  .page-hero {
    padding: 2.5rem 0 1.75rem;
  }
}
</style>
