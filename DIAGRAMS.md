# System Architecture & Workflow Diagrams

Dokumen ini berisi diagram arsitektur dan alur kerja seluruh sistem SPARQL-MCP-Kel-2, mulai dari komponen high-level hingga detail komunikasi antar agen.

---

## 1. System Overview — Arsitektur High-Level

Gambaran besar seluruh komponen sistem dan hubungan di antaranya.

```mermaid
graph TB
    subgraph CLIENT["🖥️ Client Layer"]
        UI["Vue.js Frontend\n(localhost:5173)"]
    end

    subgraph BACKEND["⚙️ Backend Layer (FastAPI — localhost:8765)"]
        API["REST API\n/api/nl2sparql\n/api/query\n/api/health"]
        LLM_MOD["LLM Module\n_call_openrouter"]
        SPARQL_MOD["SPARQL Executor\nexecute_sparql"]
        SUMMARY["Summary Generator\n_generate_llm_summary"]
        GRAPH["Graph Builder\n_fetch_relation_graph"]
    end

    subgraph LLM["🤖 LLM Layer"]
        OR["OpenRouter.ai\ngpt-oss-120b / gemini / etc."]
    end

    subgraph DATA["🗄️ Data Layer"]
        FUSEKI["Apache Jena Fuseki\n(localhost:3030)"]
        MCP_STDIO["MCP stdio Server\nsparql-mcp-stdio"]
        SEPSES["SEPSES CSKG\n(remote, optional)"]
    end

    subgraph KG["📚 Knowledge Graph"]
        CVE["CVE\nVulnerabilities"]
        CWE["CWE\nWeaknesses"]
        CPE["CPE\nProducts"]
        CAPEC["CAPEC\nAttack Patterns"]
        SNORT["Snort Rules\nIDS Signatures"]
    end

    UI -->|"POST /api/nl2sparql"| API
    API --> LLM_MOD
    API --> SPARQL_MOD
    API --> SUMMARY
    API --> GRAPH
    LLM_MOD -->|"NL → SPARQL"| OR
    SUMMARY -->|"Results → NL"| OR
    SPARQL_MOD -->|"SPARQL query"| FUSEKI
    GRAPH -->|"Relation queries"| FUSEKI
    MCP_STDIO -->|"run_sparql_query"| FUSEKI
    MCP_STDIO -.->|"optional"| SEPSES
    FUSEKI --- CVE
    FUSEKI --- CWE
    FUSEKI --- CPE
    FUSEKI --- CAPEC
    FUSEKI --- SNORT
```

---

## 2. Multi-Agent Workflow — Alur Antar Agen

Setiap permintaan NL melewati rangkaian agen berikut secara berurutan.

```mermaid
flowchart TD
    USER(["👤 User\nNatural Language Query"])

    subgraph ORCH["Orchestrator"]
        O1["Terima query\nBuat trace_id"]
        O2["Validasi & routing"]
        O3["Kumpulkan hasil\nDari semua agen"]
        O4["Kirim respons\nke UI"]
    end

    subgraph QP["Query Planner Agent"]
        QP1["Analisis intent\npengguna"]
        QP2["Pilih endpoint\n& prefixes"]
        QP3["Generate SPARQL\nvia LLM (OpenRouter)"]
        QP4["Validasi query\n(keamanan & ukuran)"]
    end

    subgraph EXEC["SPARQL Executor Agent"]
        E1["Terima SPARQL\n+ routing params"]
        E2["Route ke endpoint\n(Fuseki / SEPSES)"]
        E3["Jalankan query\nHTTP GET"]
        E4["Kembalikan hasil\n+ elapsed_ms"]
    end

    subgraph REASON["Reasoning / Analysis Agent"]
        R1["Parse JSON bindings"]
        R2["Cek empty results\n→ fallback query?"]
        R3["Build relation graph\n(outgoing + incoming)"]
        R4["Normalize entities\n(label, group, IRI)"]
    end

    subgraph SYNTH["Response Synthesizer Agent"]
        S1["Kumpulkan bindings\n(top 5 rows)"]
        S2["Kirim ke LLM\nuntuk NL summary"]
        S3["Fallback extractive\njika LLM gagal"]
        S4["Susun respons akhir\n(results+graph+summary)"]
    end

    USER --> O1
    O1 --> O2
    O2 --> QP1
    QP1 --> QP2 --> QP3 --> QP4
    QP4 --> O3
    O3 --> E1
    E1 --> E2 --> E3 --> E4
    E4 --> O3
    O3 --> R1
    R1 --> R2 --> R3 --> R4
    R4 --> O3
    O3 --> S1
    S1 --> S2
    S2 -->|"LLM OK"| S4
    S2 -->|"LLM gagal"| S3 --> S4
    S4 --> O4
    O4 --> USER
```

---

## 3. NL to SPARQL — Alur Lengkap End-to-End

Sequence diagram dari saat pengguna mengetik query hingga UI menampilkan hasil.

```mermaid
sequenceDiagram
    actor User
    participant FE as Vue Frontend
    participant API as FastAPI Backend
    participant LLM as OpenRouter LLM
    participant FUSEKI as Fuseki Triplestore

    User->>FE: Ketik pertanyaan NL
    FE->>API: POST /api/nl2sparql { nl_query }

    Note over API: Buat trace_id

    API->>LLM: Prompt NL→SPARQL<br/>(sistem + prefixes + pertanyaan)
    LLM-->>API: { query, format, notes }

    Note over API: Validasi query:<br/>- Cek unsafe ops (INSERT/DELETE)<br/>- Cek ukuran (MAX_QUERY_CHARS)<br/>- Cek endpoint allowlist<br/>- Tambah LIMIT jika tidak ada

    API->>FUSEKI: GET /cskg/sparql?query=SELECT...
    FUSEKI-->>API: JSON bindings (results)

    alt Hasil kosong → refine
        API->>FUSEKI: GET /cskg/sparql?query=fallback...
        FUSEKI-->>API: JSON bindings (fallback)
    end

    par Paralel: Graph + Summary
        API->>FUSEKI: Graph queries (outgoing + incoming)
        FUSEKI-->>API: Relation triples
    and
        API->>LLM: Prompt NL summary<br/>(top 5 rows, max 250 tokens)
        LLM-->>API: Plain-text summary paragraph
    end

    API-->>FE: { trace_id, sparql, results, graph, summary, meta }
    FE->>User: Tampilkan EntityCards + GraphCanvas + Explanation
```

---

## 4. SPARQL-MCP Integration — Integrasi MCP Server

Bagaimana MCP stdio server berinteraksi dengan triplestore dan klien MCP.

```mermaid
flowchart LR
    subgraph MCP_CLIENT["MCP Client\n(Claude Desktop / Cursor)"]
        C1["Kirim tools/call\nJSON-RPC over stdio"]
    end

    subgraph MCP_SERVER["sparql-mcp-stdio\n(server.py)"]
        T1["list_tools()\n→ run_sparql_query\n→ get_void_descriptions"]
        T2["call_tool()\nrouting logic"]
        T3["Service URI\ndetection"]
    end

    subgraph ROUTING["Endpoint Routing"]
        R_SINGLE["1 SERVICE URI\n→ direct to that URI"]
        R_MULTI["2+ SERVICE URIs\n→ FEDERATION_ENDPOINT"]
        R_NONE["No SERVICE\n→ DEFAULT_SPARQL_ENDPOINT"]
    end

    subgraph ENDPOINTS["SPARQL Endpoints"]
        FUSEKI_E["Fuseki Local\nlocalhost:3030/cskg/sparql"]
        SEPSES_E["SEPSES Remote\nsepses.ifs.tuwien.ac.at/sparql"]
        FED_E["Federation Endpoint\nlocalhost:3030/ds/sparql"]
    end

    subgraph VOID["VoID Cache\n(local_store/)"]
        VOID_INDEX["void_index.json\n(TTL: 7 hari)"]
        VOID_STRAT["Retrieval Strategies:\n1. Well-known HTTP\n2. Default graph\n3. Named graph\n4. Service description"]
    end

    C1 -->|"stdio JSON-RPC"| T1
    T1 --> T2
    T2 --> T3
    T3 --> R_SINGLE
    T3 --> R_MULTI
    T3 --> R_NONE
    R_SINGLE --> FUSEKI_E
    R_SINGLE --> SEPSES_E
    R_MULTI --> FED_E
    R_NONE --> FUSEKI_E
    T2 -->|"get_void_descriptions"| VOID_INDEX
    VOID_INDEX -->|"stale / miss"| VOID_STRAT
    VOID_STRAT --> FUSEKI_E
```

---

## 5. Frontend–Backend Interaction — Komunikasi UI & API

Detail interaksi komponen Vue.js dengan backend FastAPI.

```mermaid
sequenceDiagram
    participant User
    participant SearchBar as SearchBar.vue
    participant Store as searchStore.js (Pinia)
    participant API as FastAPI /api/nl2sparql
    participant EntityCard as EntityCard.vue
    participant Graph as GraphCanvas.vue
    participant Summary as ResultsView (summary card)

    User->>SearchBar: Input query + Enter / klik Search
    SearchBar->>Store: performSearch(query)

    Store->>Store: isLoading = true<br/>hasSearched = true<br/>reset results/graph/summary

    Store->>API: POST { nl_query, options }

    Note over API: Proses NL → SPARQL → results<br/>+ graph + summary (2 LLM calls)

    API-->>Store: { sparql, results, graph, summary, meta }

    Store->>Store: Parse results → entities[]<br/>sparqlQuery = sparql<br/>graphData = graph<br/>summary = summary.text<br/>isLoading = false

    Store->>EntityCard: Render tiap entity<br/>(title, fields, description, badge)
    Store->>Graph: Render vis-network<br/>(nodes, edges, groups)
    Store->>Summary: Tampilkan teks NL<br/>dari LLM / extractive fallback
```

---

## 6. Fallback Query Decision Tree — Logika Fallback

Alur keputusan saat LLM gagal menghasilkan query valid atau query menghasilkan hasil kosong.

```mermaid
flowchart TD
    START(["Query NL masuk"])

    LLM_CALL["Panggil LLM\n_call_openrouter"]
    LLM_OK{LLM berhasil?}
    QUERY_VALID{Query mengandung\nkata umum\n(tell/list/show)?}
    GENERIC{Query terlalu\ngenerik?\n_query_looks_too_generic}

    FALLBACK_BUILD["Bangun fallback query\n_build_fallback_query"]

    subgraph FALLBACK_LOGIC["Logika Fallback berdasarkan kata kunci NL"]
        F_CVE["CVE / vulnerabil\n→ SELECT CVE query\n+ filter label/desc"]
        F_CWE["CWE / weakness\n→ SELECT CWE query"]
        F_CPE["CPE / product / vendor\n→ SELECT CPE query"]
        F_CAPEC["CAPEC / attack pattern\n→ SELECT CAPEC query"]
        F_SNORT["snort / rule / signature\n→ SELECT SnortRule query"]
        F_MALWARE["malware+cve+cpe\n→ UNION multi-type query"]
        F_GENERIC["Generic\n→ CONTAINS label filter"]
    end

    EXEC["Eksekusi SPARQL\nexecute_sparql"]
    EXEC_OK{Eksekusi berhasil?}
    SAFE_RETRY["Retry dengan\nsafe CVE query\n(filter fallback_term)"]

    EMPTY{Hasil kosong?\n_is_empty_results}
    REFINE["Jalankan fallback query\nuntuk refinement"]

    FINAL(["Kembalikan hasil\nke Reasoning Agent"])

    START --> LLM_CALL
    LLM_CALL --> LLM_OK
    LLM_OK -->|"Tidak"| FALLBACK_BUILD
    LLM_OK -->|"Ya"| QUERY_VALID
    QUERY_VALID -->|"Ya (tidak valid)"| FALLBACK_BUILD
    QUERY_VALID -->|"Tidak (valid)"| GENERIC
    GENERIC -->|"Ya"| FALLBACK_BUILD
    GENERIC -->|"Tidak"| EXEC

    FALLBACK_BUILD --> F_MALWARE
    FALLBACK_BUILD --> F_CVE
    FALLBACK_BUILD --> F_CWE
    FALLBACK_BUILD --> F_CPE
    FALLBACK_BUILD --> F_CAPEC
    FALLBACK_BUILD --> F_SNORT
    FALLBACK_BUILD --> F_GENERIC
    F_MALWARE & F_CVE & F_CWE & F_CPE & F_CAPEC & F_SNORT & F_GENERIC --> EXEC

    EXEC --> EXEC_OK
    EXEC_OK -->|"Tidak"| SAFE_RETRY
    EXEC_OK -->|"Ya"| EMPTY
    SAFE_RETRY --> EMPTY

    EMPTY -->|"Ya"| REFINE
    EMPTY -->|"Tidak"| FINAL
    REFINE --> FINAL
```

---

## 7. Agent Communication Protocol — Protokol Pesan Antar Agen

Format envelope JSON yang digunakan untuk komunikasi internal antar agen.

```mermaid
sequenceDiagram
    participant ORC as Orchestrator
    participant PLAN as Query Planner
    participant EXEC as SPARQL Executor
    participant MCP as MCP Tool
    participant REAS as Reasoning Agent
    participant SYNTH as Response Synthesizer

    ORC->>PLAN: { trace_id, from: orchestrator,<br/>to: planner, intent: plan_query,<br/>input: { nl_query }, context: { endpoint_policy } }

    PLAN-->>ORC: { trace_id, from: planner,<br/>to: orchestrator, intent: query_ready,<br/>output: { sparql, endpoint, format } }

    ORC->>EXEC: { trace_id, from: orchestrator,<br/>to: executor, intent: execute_sparql,<br/>input: { query }, constraints: { timeout_ms, max_rows } }

    EXEC->>MCP: tools/call run_sparql_query<br/>{ query, format, timeout_ms }
    MCP-->>EXEC: [TextContent preview, TextContent payload]

    alt Sukses
        EXEC-->>ORC: { trace_id, intent: results,<br/>output: { bindings, elapsed_ms, row_count } }
    else Error
        EXEC-->>ORC: { trace_id, intent: error,<br/>error: { code: SPARQL_TIMEOUT,<br/>message: ..., recoverable: true } }
    end

    ORC->>REAS: { trace_id, intent: analyze,<br/>input: { bindings, sparql } }
    REAS-->>ORC: { trace_id, intent: findings,<br/>output: { entities, graph_nodes, graph_edges } }

    ORC->>SYNTH: { trace_id, intent: synthesize,<br/>input: { findings, nl_query } }
    SYNTH-->>ORC: { trace_id, intent: response,<br/>output: { summary_text, source: llm } }

    ORC-->>ORC: Gabungkan semua output\nBentuk response body akhir
```

---

## 8. Data Layer — Model Data Knowledge Graph

Entitas-entitas yang tersimpan di Fuseki dan hubungannya.

```mermaid
erDiagram
    CVE {
        string id PK
        string label
        string description
        date issued
        date modified
        string cvssV3Severity
        float cvssV3BaseScore
    }
    CWE {
        string id PK
        string label
        string description
        string abstraction
    }
    CPE {
        string id PK
        string label
        string title
        string vendor
        string product
        string version
    }
    CAPEC {
        string id PK
        string label
        string description
        string likelihoodOfAttack
        string typicalSeverity
    }
    SnortRule {
        string id PK
        string label
        string message
        string sid
        string ruleText
    }

    CVE }o--o{ CWE : "hasCWE"
    CVE }o--o{ CPE : "affectsProduct"
    CVE }o--o{ CAPEC : "relatedCAPEC"
    CVE }o--o{ SnortRule : "hasSnortRule"
    CWE }o--o{ CAPEC : "relatedAttackPattern"
```

---

## 9. Deployment — Topologi Container Docker

Konfigurasi container saat dijalankan dengan `docker compose up`.

```mermaid
graph LR
    subgraph HOST["Host Machine"]
        subgraph COMPOSE["docker-compose.yml"]
            subgraph BE["Container: sparql_mcp_backend"]
                PY["Python FastAPI\nport 8765"]
            end
            subgraph FK["Container: fuseki"]
                FJ["Apache Jena Fuseki\nport 3030"]
                VOL[("fuseki-data\nvolume")]
            end
        end
        FE_DEV["Vue Dev Server\nnpm run dev\nport 5173"]
        ENV[".env\nOPENROUTER_API_KEY\nDEFAULT_SPARQL_ENDPOINT\n..."]
    end

    subgraph CLOUD["Internet"]
        OR_API["OpenRouter API\nopenrouter.ai/api/v1"]
    end

    BROWSER(["Browser\nlocalhost:5173"]) --> FE_DEV
    FE_DEV -->|"POST /api/nl2sparql\nlocalhost:8765"| PY
    PY -->|"SPARQL HTTP\nhttp://fuseki:3030/cskg/sparql"| FJ
    FJ --- VOL
    PY -->|"HTTPS\nBearer token"| OR_API
    ENV -.->|"env_file"| PY

    style COMPOSE stroke:#38bdf8,stroke-width:2px
    style HOST stroke:#475569,stroke-width:1px,stroke-dasharray:5
```

---

## 10. Summary Generation Pipeline — Alur Pembuatan Ringkasan

Detail proses pembuatan penjelasan NL dari hasil SPARQL.

```mermaid
flowchart LR
    BINDINGS(["SPARQL Bindings\n(JSON rows)"])

    subgraph EXTRACT["Extractive Summary\n(instant fallback)"]
        EX1["Ambil field:\ndescription / message / label"]
        EX2["Ambil kalimat pertama\ntiap row (max 3)"]
        EX3["Gabungkan menjadi\nringkasan singkat"]
    end

    subgraph LLM_SUM["LLM Summary (OpenRouter)"]
        L1["Serialisasi top 5 rows\n(field=value, trunc 120 char)"]
        L2["Build prompt:\n- Peran: cybersecurity analyst\n- Pertanyaan user\n- Data rows\n- Instruksi NL 2-3 kalimat"]
        L3["Panggil OpenRouter\ntemp=0.1, max_tokens=250"]
        L4["Parse plain-text response"]
    end

    DECISION{"LLM berhasil?"}
    FINAL_SUM(["summary: {\n  text: '...',\n  source: 'llm'|'extractive',\n  source_count: N\n}"])

    BINDINGS --> EX1 --> EX2 --> EX3
    BINDINGS --> L1 --> L2 --> L3 --> L4

    L4 --> DECISION
    EX3 --> DECISION
    DECISION -->|"LLM OK"| FINAL_SUM
    DECISION -->|"LLM gagal / kosong"| FINAL_SUM
```
