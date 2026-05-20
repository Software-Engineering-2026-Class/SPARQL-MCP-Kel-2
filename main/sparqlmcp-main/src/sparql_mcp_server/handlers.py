from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from rdflib import Graph
import time
import requests

@dataclass
class QueryResult:
    mime_type: str
    payload_text: str
    preview: str


def _preview_rows(result_json: dict, max_rows: int = 10) -> str:
    bindings = result_json.get("results", {}).get("bindings", [])[:max_rows]
    if not bindings:
        return "(no rows)"
    lines = []
    for row in bindings:
        pairs = [f"{var}={cell.get('value')}" for var, cell in row.items()]
        lines.append(", ".join(pairs))
    return "\n".join(lines)


def _preview_graph(text: str, max_lines: int = 20) -> str:
    return "\n".join(text.splitlines()[:max_lines]) or "(empty graph)"


async def execute_sparql(
    endpoint: str,
    query: str,
    *,
    format: str = "sparql-results+json",
    timeout_ms: int = 100000,
) -> QueryResult:
    """
    Execute a SPARQL 1.1 query (including federated SERVICE) against a remote endpoint.
    Uses requests for reliable HTTP transport.
    """
    # Map format to Accept header
    accept_map = {
        "sparql-results+json": "application/sparql-results+json",
        "text/turtle": "text/turtle",
        "application/ld+json": "application/ld+json",
        "text/n3": "text/n3",
    }
    accept_header = accept_map.get(format, "application/sparql-results+json")
    
    params = {"query": query}
    headers = {"Accept": accept_header}
    
    t0 = time.perf_counter()
    
    try:
        response = requests.get(
            endpoint, 
            params=params, 
            headers=headers, 
            timeout=timeout_ms / 1000
        )
        response.raise_for_status()
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        
        if format == "sparql-results+json":
            data = response.json()
            preview = _preview_rows(data)
            return QueryResult(
                mime_type="application/sparql-results+json",
                payload_text=json.dumps(data),
                preview=f"elapsed_ms: {elapsed_ms}\n{preview}",
            )
        
        else:
            # Text formats (Turtle, N3, JSON-LD as text)
            text = response.text
            preview = _preview_graph(text)
            return QueryResult(
                mime_type=format, 
                payload_text=text, 
                preview=f"elapsed_ms: {elapsed_ms}\n{preview}"
            )
            
    except Exception as e:
        # Wrap error in a way that doesn't crash the server but returns error text
        # Ideally we raise, but for this tool we often want the model to see the error.
        # But the caller expects QueryResult or exception?
        # The server.py catches exceptions?
        # Let's raise and let server.py handle it or return error text.
        # If we raise, it becomes a ToolError in MCP.
        raise RuntimeError(f"SPARQL execution failed: {str(e)}")
