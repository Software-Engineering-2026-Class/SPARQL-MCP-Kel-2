# Release Notes — SPARQL-MCP-Kel-2

---

## v1.0.0 — 14 Juni 2026

Rilis perdana SPARQL-MCP-Kel-2, sebuah platform Cybersecurity Knowledge Graph (CSKG) berbasis LLM (Agentic AI) yang memungkinkan pencarian keamanan siber menggunakan bahasa natural (NL2SPARQL).

### Fitur Utama

- **Agentic AI Cybersecurity Search:**
  Sistem pencarian keamanan siber berbasis LLM yang secara otomatis mengonversi pertanyaan bahasa natural menjadi SPARQL query terhadap SEPSES CSKG, mengeksekusinya, dan merangkum hasilnya dengan sitasi yang tepat.

- **Knowledge Graph Komprehensif (7 Dataset Keamanan Siber):**
  Mengintegrasikan data keamanan siber yang saling terhubung:
  - **CVE (Common Vulnerabilities and Exposures):** Informasi kerentanan keamanan (NVD CVE 2021–2024).
  - **CWE (Common Weakness Enumeration):** Katalog kelemahan perangkat lunak.
  - **CPE (Common Platform Enumeration):** Kamus produk/platform + validasi SHACL.
  - **CAPEC (Common Attack Pattern Enumeration and Classification):** Pola serangan umum.
  - **MITRE ATT&CK (Enterprise & ICS):** Teknik (techniques) dan taktik (tactics) serangan siber (disimpan di `database/seed data/cat/`).
  - **CISA ICS Advisory (ICSA):** Informasi advisory keamanan industri/SCADA/PLC (disimpan di `database/seed data/icsa/`).
  - **Snort Rules & SEPSES Original Data:** Aturan deteksi intrusi dan basis data relasi asli SEPSES.

- **Arsitektur Agen AI (Multi-Agent System):**
  - **LLM Agent (NL→SPARQL):** Mengubah pertanyaan menjadi query SPARQL valid dengan prefix & schema lengkap untuk semua 7 dataset (termasuk `attack:` dan `icsa:`).
  - **SPARQL Executor & Graph Builder:** Mengeksekusi query dan membangun visualisasi graf relasi interaktif.
  - **Summary Agent:** Merangkum hasil pencarian dan menyertakan sitasi ID dari dataset (CVE, CWE, CPE, CAPEC, ATT&CK, ICSA).
  - **Retry & Fallback Mechanism:** Auto-retry dengan LLM refinement dan programmatic fallback/keyword search untuk keandalan tinggi.

### Antarmuka Pengguna (Frontend Vue.js)

Antarmuka pencarian modern terinspirasi dari Search AI dengan fitur:
- Input pencarian bahasa natural yang responsif.
- **EntityCard:** Menampilkan detail entitas secara terstruktur.
- **GraphCanvas:** Visualisasi graf relasi interaktif untuk melihat hubungan antar entitas.
- **SparqlAccordion:** Menampilkan SPARQL query yang dihasilkan oleh AI untuk transparansi proses.
- Tampilan ringkasan jawaban dari LLM yang informatif.

### Backend & Integrasi

- **FastAPI Backend:** API endpoint berkinerja tinggi untuk NL→SPARQL (`/api/nl2sparql`), raw SPARQL (`/api/query`), dan health check (`/api/health`).
- **MCP Stdio Server:** Server Model Context Protocol (MCP) untuk integrasi langsung dengan Claude Desktop atau AI assistant lainnya via protocol stdio.
- **Docker Compose:** Setup instan untuk menjalankan backend FastAPI dan triplestore Apache Jena Fuseki.

### Struktur Direktori Database

Struktur data seed diatur secara rapi per kategori untuk mempermudah pemeliharaan:
| Direktori       | Konten                                  |
| --------------- | --------------------------------------- |
| `capec/`        | CAPEC attack patterns                   |
| `cat/`          | MITRE ATT&CK (Enterprise + ICS)         |
| `cpe/`          | CPE dictionary + SHACL validation       |
| `cve/`          | NVD CVE 2021–2024                       |
| `cwe/`          | CWE weakness catalog                    |
| `icsa/`         | CISA ICS Advisories                     |
| `ifs tuwien/`   | SEPSES original data (compressed)       |
