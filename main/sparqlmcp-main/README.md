# SPARQL-MCP Server

A Model Context Protocol (MCP) server for SPARQL experiments. It provides two entry points for local testing and future expansion:

- `sparql-mcp-stdio`: stdio MCP server for local MCP clients (e.g., Claude Desktop)
- `sparql-mcp-web`: FastAPI app with a basic `/health` endpoint (for future WebSocket / HTTP bridging)

## Rationale

This project explores combining MCP with SPARQL to move from single-endpoint querying to agentic, federated SPARQL. MCP offers a JSON-RPC based, stateful interface for discovering and invoking server-provided capabilities (resources, prompts, tools). SPARQL 1.1 adds federated querying via `SERVICE`, but practical limitations remain (source selection, planning, heterogeneity, endpoint availability). The end goal is an MCP server that incrementally adds schema exploration, safe querying, and eventually federated planning tools.

## Installation & Setup

### 1. Prerequisites
- **Python 3.10+**

Install dependencies:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory (or update the existing one). **Note: The values below are examples; adjust them to match your local setup and endpoint configurations.**

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `LOCAL_STORE` | Path to store cached VoID descriptions | `local_store/void_descriptions` |
| `FEDERATION_ENDPOINT` | The primary SPARQL endpoint for federated queries | `http://localhost:3030/ds/sparql` |
| `DEFAULT_SPARQL_ENDPOINT` | Endpoint to use when a query has no `SERVICE` clause | `https://sepses.ifs.tuwien.ac.at/sparql` |
| `FORCE_FEDERATION` | Force all `SERVICE` queries through `FEDERATION_ENDPOINT` | `false` |
| `SPARQL_TIMEOUT_SECONDS` | Timeout for SPARQL queries in seconds | `60` |
| `SPARQL_VERIFY_SSL` | Verify TLS certificates for SPARQL HTTP requests | `true` |
| `SPARQL_CA_BUNDLE` | Path to a custom CA bundle (overrides `SPARQL_VERIFY_SSL`) | `` |
| `DEFAULT_QUERY_LIMIT` | Default LIMIT added to generated SPARQL | `100` |
| `MAX_QUERY_CHARS` | Maximum accepted SPARQL length | `8000` |
| `VOID_CACHE_TTL_SECONDS` | How long to cache VoID descriptions (seconds) | `604800` (7 days) |
| `VOID_HTTP_TIMEOUT_SECONDS`| Timeout for fetching VoID via HTTP | `60` |
| `VOID_SPARQL_TIMEOUT_SECONDS`| Timeout for fetching VoID via SPARQL | `60` |
| `EXPOSED_TOOLS` | Comma-separated list of tools to expose to the client | `run_sparql_query,get_void_descriptions` |
| `LLM_PROVIDER` | LLM backend | `openai_compat` |
| `OPENAI_COMPAT_API_KEY` | OpenAI-compatible API key (if `LLM_PROVIDER=openai_compat`) | `` |
| `OPENAI_COMPAT_BASE_URL` | Base URL for OpenAI-compatible router | `` |
| `OPENAI_COMPAT_MODEL` | Router model name | `smart-chat` |
| `OPENAI_COMPAT_MAX_TOKENS` | Max tokens for router responses | `800` |
| `OPENAI_COMPAT_TEMPERATURE` | Router temperature setting | `0.2` |
| `CORS_ALLOW_ORIGINS` | Comma-separated allowed origins for the API | `http://localhost:5173` |
| `ALLOWED_ENDPOINTS` | Comma-separated SERVICE endpoint allowlist | `` |

#### CSKG endpoint options

**Option A: SEPSES CSKG (remote Virtuoso)**

```
DEFAULT_SPARQL_ENDPOINT=https://sepses.ifs.tuwien.ac.at/sparql
FORCE_FEDERATION=false
```

**Option B: Local triple store (Virtuoso or Qlever)**

```
DEFAULT_SPARQL_ENDPOINT=http://localhost:8890/sparql
FORCE_FEDERATION=false
```

If your `SERVICE` URIs are only resolvable inside Docker, set `FORCE_FEDERATION=true` and point `FEDERATION_ENDPOINT` at your local federator.

#### Local Fuseki with Docker

This repo includes a minimal Fuseki Docker Compose file to run a local SPARQL endpoint.

Start Fuseki:

```bash
docker compose -f docker-compose.yml up -d
```

Open the admin UI:

- http://localhost:3030

Login with username `admin` and the password set in `docker-compose.yml` (`ADMIN_PASSWORD`).

Create a dataset named `cskg`, then your SPARQL endpoint becomes:

- http://localhost:3030/cskg/sparql

Update `.env` to point to Fuseki:

```bash
DEFAULT_SPARQL_ENDPOINT=http://localhost:3030/cskg/sparql
FEDERATION_ENDPOINT=http://localhost:3030/cskg/sparql
FORCE_FEDERATION=false
```

Change the admin password in `docker-compose.yml` before any shared or production deployment.

#### Local Backend + Fuseki (Docker)

Run the backend API together with Fuseki using the local compose file:

```bash
docker compose -f docker-compose.local.yml up -d
```

This starts:
- Backend API: http://localhost:8765
- Fuseki UI: http://localhost:3030

Make sure `.env` includes your LLM provider key before starting the backend.

#### Load seed data into Fuseki (optional)

Seed files are in `database/seed data/` as `.ttl.gz`. Extract them to `.ttl`, then upload via the
Fuseki UI `add data` tab for dataset `cskg`.

Verify data was loaded:

```sparql
SELECT (COUNT(*) AS ?triples) WHERE { ?s ?p ?o }
```

### 3. Running with MCP Clients

#### For Cursor
Add this to your `mcp.json` (usually in `C:\Users\<User>\.cursor\mcp.json` or project-specific):

```json
{
  "mcpServers": {
    "sparql-mcp": {
      "command": "sparql-mcp-stdio",
      "args": []
    }
  }
}
```

#### For Claude Desktop
Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sparql-mcp": {
      "command": "sparql-mcp-stdio",
      "args": []
    }
  }
}
```

## Run Locally (Development)

- Stdio MCP server:
  ```bash
  sparql-mcp-stdio
  ```

- Web app (health only):
  ```bash
  sparql-mcp-web
  # visit http://localhost:8765/health
  ```

### Backend API (FastAPI)

When `sparql-mcp-web` is running, these endpoints are available:

- `POST /api/nl2sparql` - generate SPARQL with the configured LLM provider and execute it
- `POST /api/query` - execute raw SPARQL
- `GET /api/health` - API health check

## Available tools

Tools exposed by the MCP server (subject to `EXPOSED_TOOLS` in `.env`):

### `run_sparql_query`
Execute a SPARQL 1.1 query. If the query contains exactly one `SERVICE` and `FORCE_FEDERATION` is not enabled, it is sent directly to that endpoint. If the query contains more than one `SERVICE`, it is executed via `FEDERATION_ENDPOINT`. If no `SERVICE` is present, the query is sent to `DEFAULT_SPARQL_ENDPOINT` (or `FEDERATION_ENDPOINT` as a fallback).

Input parameters:
- `query` (string, required): SPARQL query text.
- `format` (string, optional): Response format. One of `sparql-results+json`, `text/turtle`, `application/ld+json`, `text/n3`. Default: `sparql-results+json`.
- `timeout_ms` (integer, optional): Request timeout in milliseconds. Minimum `1000`, maximum `100000`.

### `get_void_descriptions`
Retrieve cached VoID descriptions for one or more SPARQL endpoints. If not cached, the tool attempts retrieval via well-known VoID URLs, VoID triples in the default graph, VoID in named graphs, and service-description links.

Input parameters:
- `endpoint` (string, optional): Single endpoint URL.
- `endpoints` (array of strings, optional): Multiple endpoint URLs.

At least one of `endpoint` or `endpoints` is required.

## Verify NL to SPARQL roundtrip

This server executes SPARQL only. Natural language to SPARQL generation happens in your MCP client (Cursor, Claude, or another LLM-backed client).

1. Start the server: `sparql-mcp-stdio`.
2. Open your MCP client and connect to the `sparql-mcp` server.
3. Prompt the client to translate a natural language question into SPARQL and call `run_sparql_query`.

Example SPARQL query you can test with SEPSES (no schema assumptions):

```sparql
SELECT * WHERE {
  SERVICE <https://sepses.ifs.tuwien.ac.at/sparql> { ?s ?p ?o }
} LIMIT 1
```

You should see a preview plus JSON results in the tool response.

If you hit `SSLCertVerificationError` with SEPSES, either set `SPARQL_VERIFY_SSL=false`
for local testing or provide a valid CA bundle path in `SPARQL_CA_BUNDLE`.

For local Fuseki testing, you can use:

```sparql
SELECT * WHERE {
  SERVICE <http://localhost:3030/cskg/sparql> { ?s ?p ?o }
} LIMIT 1
```
