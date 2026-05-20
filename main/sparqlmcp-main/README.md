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
| `SPARQL_TIMEOUT_SECONDS` | Timeout for SPARQL queries in seconds | `60` |
| `VOID_CACHE_TTL_SECONDS` | How long to cache VoID descriptions (seconds) | `604800` (7 days) |
| `VOID_HTTP_TIMEOUT_SECONDS`| Timeout for fetching VoID via HTTP | `60` |
| `VOID_SPARQL_TIMEOUT_SECONDS`| Timeout for fetching VoID via SPARQL | `60` |
| `EXPOSED_TOOLS` | Comma-separated list of tools to expose to the client | `run_sparql_query,get_void_descriptions` |

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

## Available tools

Tools exposed by the MCP server (subject to `EXPOSED_TOOLS` in `.env`):

### `run_sparql_query`
Execute a SPARQL 1.1 query. Queries must include `SERVICE` operators naming target SPARQL endpoints. If the query contains exactly one `SERVICE`, it is sent directly to that endpoint. If the query contains more than one `SERVICE`, it is executed via a local SPARQL federation endpoint.

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
