# SPARQL-MCP-Kel-2

Sistem analisis keamanan siber berbasis Agentic AI menggunakan SPARQL-MCP dan Cybersecurity Knowledge Graph (CSKG).

## Deskripsi

Proyek ini mengimplementasikan sistem agentic AI yang mengintegrasikan Large Language Model (LLM) dengan Cybersecurity Knowledge Graph (CSKG) melalui framework SPARQL-MCP. Pengguna dapat mengajukan pertanyaan dalam bahasa natural, sistem secara otomatis membuat query SPARQL terhadap knowledge graph yang berisi data **CVE, CWE, CPE, CAPEC, Snort Rule, MITRE ATT&CK (Enterprise & ICS), dan CISA ICS Advisory (ICSA)**, lalu menampilkan hasil beserta penjelasan dalam bahasa yang mudah dipahami dan visualisasi graf relasi.

Antarmuka pencarian terinspirasi dari [WU Search AI](https://search.ai.wu.ac.at/), dan basis knowledge graph menggunakan dataset [SEPSES CSKG](https://sepses.ifs.tuwien.ac.at/).

## Dokumentasi

Dokumentasi teknis lengkap tersedia di:

- [`main/sparqlmcp-main/README.md`](main/sparqlmcp-main/README.md) — setup backend, konfigurasi `.env`, dan cara menjalankan server
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — arsitektur multi-agent dan protokol komunikasi antar agen
- [`DIAGRAMS.md`](DIAGRAMS.md) — diagram arsitektur sistem, alur multi-agent, integrasi SPARQL-MCP, dan interaksi frontend-backend

## Struktur Folder

```
.
├─ ARCHITECTURE.md
├─ DIAGRAMS.md
├─ LICENSE
├─ README.md
├─ RELEASE_NOTES.md
└─ main/
   └─ sparqlmcp-main/
      ├─ .env                    ← konfigurasi lokal (salin dari .env.example)
      ├─ .env.example
      ├─ .gitignore
      ├─ .dockerignore
      ├─ Dockerfile
      ├─ docker-compose.yml      ← menjalankan backend + Fuseki sekaligus
      ├─ pyproject.toml
      ├─ README.md
      ├─ requirements.txt
      ├─ SPARQL_queries.md
      ├─ src/
      │  └─ sparql_mcp_server/
      │     ├─ __init__.py
      │     ├─ handlers.py       ← eksekusi SPARQL via requests
      │     ├─ server.py         ← MCP stdio server
      │     └─ web.py            ← FastAPI backend (NL→SPARQL, summary, graph)
      ├─ frontend/
      │  ├─ index.html
      │  ├─ package.json
      │  ├─ vite.config.js
      │  └─ src/
      │     ├─ App.vue
      │     ├─ main.js
      │     ├─ style.css
      │     ├─ components/       ← EntityCard, GraphCanvas, SearchBar,
      │     │                       SparqlAccordion, Header, Footer,
      │     │                       InfoPanel, StarBackground, dll.
      │     ├─ data/             ← mockData.js
      │     ├─ stores/           ← searchStore.js (Pinia)
      │     ├─ router/           ← index.js
      │     └─ views/            ← HomeView, ResultsView, AboutView,
      │                             DocumentationView
      └─ database/
         └─ seed data/
            ├─ capec/
            │  └─ capec_latest.zip-output.ttl
            ├─ cat/                           ← MITRE ATT&CK
            │  ├─ enterprise-attack.json-output.ttl
            │  └─ ics-attack.json-output.ttl
            ├─ cpe/
            │  ├─ cpe-shacl-result.ttl
            │  └─ official-cpe-dictionary_v2.3.xml.zip-output.ttl
            ├─ cve/
            │  ├─ nvdcve-1.1-2021.json.zip-output.ttl
            │  ├─ nvdcve-1.1-2022.json.zip-output.ttl
            │  ├─ nvdcve-1.1-2023.json.zip-output.ttl
            │  └─ nvdcve-1.1-2024.json.zip-output.ttl
            ├─ cwe/
            │  └─ cwec_latest.xml.zip-output.ttl
            ├─ icsa/                           ← CISA ICS Advisory
            │  └─ CISA_ICS_ADV_Master.csv-output.ttl
            └─ ifs tuwien/                     ← SEPSES original data
               ├─ graph0000001_cpe.ttl.gz
               ├─ graph0000001_cve.ttl.gz
               ├─ graph000001_*.ttl.gz          (CWE, CAPEC, Snort, dll.)
               └─ graph000002–000005_*.ttl.gz
```

## Anggota Kelompok

| Nama                             | NIM                | GitHub                                     | Role                  |
| -------------------------------- | ------------------ | ------------------------------------------ | --------------------- |
| Arnoldus Dharma Wasesa Mahasmara | 24/545535/PA/23182 | [@Arnold-XV](https://github.com/Arnold-XV) | Agent Developer (PIC) |
| Hafidz Kurniawan Nahruntoko      | 24/539859/PA/22920 | [@DaisyDazy](https://github.com/DaisyDazy) | Data Engineer         |
| Adzrha Auryn Alius               | 24/533582/PA/22594 | [@teksarin](https://github.com/teksarin)   | Web Developer         |
| Jessy Marcia Anabel              | 24/538431/PA/22846 | [@jsmarciaa](https://github.com/jsmarciaa) | Quality Assurance     |

## Setup & Menjalankan

### Prasyarat

- **Python 3.10+**
- **Node.js 18+** (untuk frontend)
- **Docker & Docker Compose** (direkomendasikan untuk triplestore)
  _atau_ **Java** (untuk Fuseki manual)

---

### Opsi A — Docker Compose (Direkomendasikan)

Cara paling mudah: jalankan backend Python + Fuseki triplestore sekaligus via Docker.

```bash
cd main/sparqlmcp-main

# Salin dan isi konfigurasi
cp .env.example .env
# Edit .env: isi OPENROUTER_API_KEY

# Jalankan backend + Fuseki
docker compose up -d
```

Setelah container berjalan:

- Backend API: `http://localhost:8765`
- Fuseki UI: `http://localhost:3030` (login: `admin` / `admin123`)

Buat dataset bernama `cskg` di Fuseki UI, lalu **muat seed data** (lihat bagian "Load Data" di bawah).

---

### Opsi B — Fuseki Manual + Backend Lokal

**1. Jalankan Fuseki**

1. Pastikan Java terinstal: `java --version`
2. Unduh `apache-jena-fuseki-6.x.x.zip` dari [jena.apache.org/download](https://jena.apache.org/download/)
3. Ekstrak dan jalankan `fuseki-server.bat` (Windows) atau `fuseki-server` (Linux/macOS)
4. Buka `http://localhost:3030`, buat dataset dengan nama **`cskg`**

**2. Instal dan jalankan backend**

```bash
cd main/sparqlmcp-main

# Install dependensi Python
python -m pip install -r requirements.txt
python -m pip install -e .

# Salin dan isi konfigurasi
cp .env.example .env
# Edit .env: isi OPENROUTER_API_KEY, pastikan:
#   DEFAULT_SPARQL_ENDPOINT=http://localhost:3030/cskg/sparql
#   FEDERATION_ENDPOINT=http://localhost:3030/cskg/sparql

# Jalankan backend API
sparql-mcp-web
# → http://localhost:8765
```

---

### Load Seed Data ke Fuseki

Seed data tersimpan di `main/sparqlmcp-main/database/seed data/` dengan struktur per-kategori:

| Subdirektori    | Deskripsi                               | Format         |
| --------------- | --------------------------------------- | -------------- |
| `capec/`        | CAPEC attack patterns                   | `.ttl`         |
| `cat/`          | MITRE ATT&CK (Enterprise + ICS)         | `.ttl`         |
| `cpe/`          | CPE dictionary + SHACL validation       | `.ttl`         |
| `cve/`          | NVD CVE 2021–2024                       | `.ttl`         |
| `cwe/`          | CWE weakness catalog                    | `.ttl`         |
| `icsa/`         | CISA ICS Advisories                     | `.ttl`         |
| `ifs tuwien/`   | SEPSES original data (compressed)       | `.ttl.gz`      |

**Cara memuat:**

1. Buka Fuseki UI → dataset `cskg` → **Add data**
2. Upload file `.ttl` dari masing-masing subdirektori di atas
3. Untuk file `.ttl.gz` (di `ifs tuwien/`), ekstrak terlebih dahulu menjadi `.ttl`
4. Verifikasi data termuat:
   ```sparql
   SELECT (COUNT(*) AS ?triples) WHERE { ?s ?p ?o }
   ```

---

### Menjalankan Frontend

```bash
cd main/sparqlmcp-main/frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Konfigurasi `.env`

File `.env` berada di `main/sparqlmcp-main/.env`. Variabel utama:

| Variabel                        | Deskripsi                             | Contoh                              |
| ------------------------------- | ------------------------------------- | ----------------------------------- |
| `DEFAULT_SPARQL_ENDPOINT`       | Endpoint SPARQL utama                 | `http://localhost:3030/cskg/sparql` |
| `FEDERATION_ENDPOINT`           | Endpoint untuk query multi-SERVICE    | `http://localhost:3030/cskg/sparql` |
| `LLM_PROVIDER`                  | Provider LLM (saat ini: `openrouter`) | `openrouter`                        |
| `OPENROUTER_API_KEY`            | API key dari openrouter.ai            | `sk-or-v1-...`                      |
| `OPENROUTER_MODEL`              | Model yang digunakan                  | `openai/gpt-oss-120b:free`          |
| `OPENROUTER_MAX_TOKENS`         | Batas token untuk NL→SPARQL           | `800`                               |
| `OPENROUTER_SUMMARY_MAX_TOKENS` | Batas token untuk ringkasan           | `250`                               |
| `CORS_ALLOW_ORIGINS`            | Origin yang diizinkan mengakses API   | `http://localhost:5173`             |
| `SPARQL_VERIFY_SSL`             | Verifikasi TLS pada request SPARQL    | `true`                              |

## API Backend

Backend FastAPI berjalan di `http://localhost:8765` dan menyediakan:

| Endpoint         | Method | Deskripsi                                                                                             |
| ---------------- | ------ | ----------------------------------------------------------------------------------------------------- |
| `/api/nl2sparql` | POST   | Terima query bahasa natural → generate SPARQL → eksekusi → kembalikan hasil + ringkasan + graf relasi |
| `/api/query`     | POST   | Eksekusi raw SPARQL query langsung                                                                    |
| `/api/health`    | GET    | Health check                                                                                          |

## Referensi

- Ekelhart, A. et al. (2019). SEPSES Knowledge Graph: An Integrated Resource for Cybersecurity. _ISWC 2019_. [Springer](https://link.springer.com/chapter/10.1007/978-3-030-30796-7_13)
- SEPSES CSKG SPARQL Endpoint and Vocabulary. [CEUR-WS Vol-4079](https://ceur-ws.org/Vol-4079/paper11.pdf)
- Ekelhart, A. et al. (2024). RAGE-KG: Retrieval-Augmented Generation with Enterprise Knowledge Graphs. [UniVie](https://eprints.cs.univie.ac.at/8178/)
- [SPARQL-MCP GitHub](https://github.com/semantisch/sparqlmcp)
- [WU Search AI](https://search.ai.wu.ac.at/)
- [OpenRouter.ai](https://openrouter.ai/)

---

> **Disclaimer:** All rights, intellectual property, credits, and original licenses for the SPARQL-MCP framework belong entirely to the original creators (<https://github.com/semantisch/sparqlmcp>). This repository is solely for integrating their work into our project. We do not claim ownership of these specific framework files.
