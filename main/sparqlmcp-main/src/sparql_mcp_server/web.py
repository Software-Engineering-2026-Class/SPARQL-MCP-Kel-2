from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .handlers import execute_sparql


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


def _get_env_list(name: str, default: str = "") -> list[str]:
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _get_env_bool(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    if "```" in cleaned:
        blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL)
        if blocks:
            cleaned = blocks[0]
    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("LLM response did not contain JSON.")
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def _extract_service_uris(query: str) -> list[str]:
    return re.findall(r"SERVICE\s*<([^>]+)>", query or "", flags=re.IGNORECASE)


def _ensure_limit(query: str, limit: int) -> str:
    if re.search(r"\bLIMIT\b", query, flags=re.IGNORECASE):
        return query
    return f"{query.rstrip()}\nLIMIT {limit}"


def _reject_unsafe_query(query: str) -> None:
    if re.search(r"\b(INSERT|DELETE|LOAD|CLEAR|CREATE|DROP|MOVE|COPY|ADD)\b", query, flags=re.IGNORECASE):
        raise HTTPException(status_code=400, detail="SPARQL update operations are not allowed.")


def _parse_elapsed_ms(preview: str) -> int | None:
    match = re.search(r"elapsed_ms:\s*(\d+)", preview)
    if not match:
        return None
    return int(match.group(1))


def _route_endpoint(query: str) -> str:
    service_uris = _extract_service_uris(query)
    federation_endpoint = os.environ.get("FEDERATION_ENDPOINT", "http://localhost:3030/ds/sparql")
    default_endpoint = os.environ.get("DEFAULT_SPARQL_ENDPOINT", "").strip()
    force_federation = _get_env_bool("FORCE_FEDERATION", "false")

    if service_uris:
        if force_federation:
            return federation_endpoint
        if len(service_uris) == 1:
            return service_uris[0]
        return federation_endpoint
    return default_endpoint or federation_endpoint


def _validate_endpoints(query: str) -> None:
    allowlist = _get_env_list("ALLOWED_ENDPOINTS", "")
    if not allowlist:
        return
    for service_uri in _extract_service_uris(query):
        if service_uri not in allowlist:
            raise HTTPException(status_code=400, detail=f"SERVICE endpoint not allowed: {service_uri}")


def _validate_query_size(query: str) -> None:
    max_chars = int(os.environ.get("MAX_QUERY_CHARS", "8000"))
    if len(query) > max_chars:
        raise HTTPException(status_code=400, detail="SPARQL query is too large.")


def _is_empty_results(results_payload: dict | None) -> bool:
    if not results_payload:
        return True
    bindings = results_payload.get("results", {}).get("bindings", [])
    return len(bindings) == 0


def _build_llm_prompt(nl_query: str, *, retry: bool, previous_query: str | None) -> str:
    prefix_block = (
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
        "PREFIX skos: <http://www.w3.org/2004/02/skos/core#>\n"
        "PREFIX cve: <https://w3id.org/sepses/vocab/ref/cve#>\n"
        "PREFIX cpe: <https://w3id.org/sepses/vocab/ref/cpe#>\n"
        "PREFIX cwe: <https://w3id.org/sepses/vocab/ref/cwe#>\n"
    )
    guidance = (
        "Return JSON only with keys: query, format, notes.\n"
        "Use SPARQL 1.1 SELECT queries only.\n"
        "If uncertain, use rdfs:label or skos:altLabel with CONTAINS/LCASE filters.\n"
        "Always include a LIMIT (<= 100).\n"
        "Use SERVICE only if necessary to target a specific endpoint.\n"
    )
    if retry:
        guidance += "If the previous query returned no results, relax constraints and broaden filters.\n"
    if previous_query:
        guidance += f"Previous query (empty results):\n{previous_query}\n"
    return (
        f"{guidance}\n"
        f"Helpful prefixes:\n{prefix_block}\n"
        f"Natural language question: {nl_query}\n"
        "Respond with JSON only."
    )


def _call_claude(nl_query: str, *, retry: bool, previous_query: str | None) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY is not set.")

    model = os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
    max_tokens = int(os.environ.get("CLAUDE_MAX_TOKENS", "800"))
    temperature = float(os.environ.get("CLAUDE_TEMPERATURE", "0.2"))

    prompt = _build_llm_prompt(nl_query, retry=retry, previous_query=previous_query)
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload,
        timeout=60,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Claude API error: {exc}") from exc

    data = response.json()
    content = data.get("content", [])
    combined = "".join(part.get("text", "") for part in content if part.get("type") == "text")
    if not combined:
        raise HTTPException(status_code=502, detail="Claude API returned empty content.")

    try:
        return _extract_json(combined)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _call_openai_compat(nl_query: str, *, retry: bool, previous_query: str | None) -> dict:
    api_key = os.environ.get("OPENAI_COMPAT_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_COMPAT_API_KEY is not set.")

    base_url = os.environ.get("OPENAI_COMPAT_BASE_URL", "").strip()
    if not base_url:
        raise HTTPException(status_code=500, detail="OPENAI_COMPAT_BASE_URL is not set.")

    model = os.environ.get("OPENAI_COMPAT_MODEL", "smart-chat")
    max_tokens = int(os.environ.get("OPENAI_COMPAT_MAX_TOKENS", "800"))
    temperature = float(os.environ.get("OPENAI_COMPAT_TEMPERATURE", "0.2"))

    prompt = _build_llm_prompt(nl_query, retry=retry, previous_query=previous_query)
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }

    headers = {
        "authorization": f"Bearer {api_key}",
        "content-type": "application/json",
    }

    url = base_url.rstrip("/") + "/chat/completions"
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"LLM API error: {exc}") from exc

    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        raise HTTPException(status_code=502, detail="LLM API returned empty choices.")
    message = choices[0].get("message", {})
    combined = message.get("content", "")
    if not combined:
        combined = choices[0].get("text", "")
    if not combined:
        raise HTTPException(status_code=502, detail="LLM API returned empty content.")

    try:
        return _extract_json(combined)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _call_llm(nl_query: str, *, retry: bool, previous_query: str | None) -> dict:
    provider = os.environ.get("LLM_PROVIDER", "claude").strip().lower()
    if provider in {"claude", "anthropic"}:
        return _call_claude(nl_query, retry=retry, previous_query=previous_query)
    if provider in {"openai_compat", "openai-compatible", "router", "multi"}:
        return _call_openai_compat(nl_query, retry=retry, previous_query=previous_query)
    raise HTTPException(status_code=500, detail=f"Unsupported LLM_PROVIDER: {provider}")


class NLQueryOptions(BaseModel):
    format: str = Field(default="sparql-results+json")
    timeout_ms: int = Field(default=30000, ge=1000, le=120000)
    expose_sparql: bool = True
    refine_on_empty: bool = True


class NLQueryRequest(BaseModel):
    nl_query: str = Field(min_length=1, max_length=2000)
    options: NLQueryOptions | None = None


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    format: str = Field(default="sparql-results+json")
    timeout_ms: int = Field(default=30000, ge=1000, le=120000)


_load_env_file()
app = FastAPI(title="SPARQL-MCP Web")

cors_origins = _get_env_list("CORS_ALLOW_ORIGINS", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/health")
def api_health() -> dict:
    return {"status": "ok"}


@app.post("/api/query")
async def api_query(request: QueryRequest) -> dict:
    trace_id = uuid.uuid4().hex
    query = request.query.strip()
    _reject_unsafe_query(query)
    _validate_query_size(query)
    _validate_endpoints(query)

    limit_default = int(os.environ.get("DEFAULT_QUERY_LIMIT", "100"))
    query = _ensure_limit(query, limit_default)
    endpoint = _route_endpoint(query)

    result = await execute_sparql(
        endpoint=endpoint,
        query=query,
        format=request.format,
        timeout_ms=request.timeout_ms,
    )

    payload: dict[str, Any] | None = None
    if request.format == "sparql-results+json":
        try:
            payload = json.loads(result.payload_text)
        except json.JSONDecodeError:
            payload = None

    return {
        "trace_id": trace_id,
        "sparql": query,
        "preview": result.preview,
        "results": payload or result.payload_text,
        "meta": {
            "endpoint": endpoint,
            "elapsed_ms": _parse_elapsed_ms(result.preview),
        },
    }


@app.post("/api/nl2sparql")
async def api_nl2sparql(request: NLQueryRequest) -> dict:
    trace_id = uuid.uuid4().hex
    options = request.options or NLQueryOptions()

    first = _call_llm(request.nl_query, retry=False, previous_query=None)
    query = str(first.get("query", "")).strip()
    if not query:
        raise HTTPException(status_code=502, detail="LLM response did not include a query.")

    _reject_unsafe_query(query)
    _validate_query_size(query)
    _validate_endpoints(query)

    limit_default = int(os.environ.get("DEFAULT_QUERY_LIMIT", "100"))
    query = _ensure_limit(query, limit_default)
    endpoint = _route_endpoint(query)

    result = await execute_sparql(
        endpoint=endpoint,
        query=query,
        format=options.format,
        timeout_ms=options.timeout_ms,
    )

    payload: dict[str, Any] | None = None
    if options.format == "sparql-results+json":
        try:
            payload = json.loads(result.payload_text)
        except json.JSONDecodeError:
            payload = None

    if options.refine_on_empty and _is_empty_results(payload):
        retry = _call_llm(request.nl_query, retry=True, previous_query=query)
        retry_query = str(retry.get("query", "")).strip()
        if retry_query:
            _reject_unsafe_query(retry_query)
            _validate_query_size(retry_query)
            _validate_endpoints(retry_query)
            retry_query = _ensure_limit(retry_query, limit_default)
            retry_endpoint = _route_endpoint(retry_query)
            retry_result = await execute_sparql(
                endpoint=retry_endpoint,
                query=retry_query,
                format=options.format,
                timeout_ms=options.timeout_ms,
            )
            query = retry_query
            endpoint = retry_endpoint
            result = retry_result
            if options.format == "sparql-results+json":
                try:
                    payload = json.loads(result.payload_text)
                except json.JSONDecodeError:
                    payload = None

    response_body = {
        "trace_id": trace_id,
        "preview": result.preview,
        "results": payload or result.payload_text,
        "meta": {
            "endpoint": endpoint,
            "elapsed_ms": _parse_elapsed_ms(result.preview),
        },
    }
    if options.expose_sparql:
        response_body["sparql"] = query
    return response_body


async def run() -> None:
    logging.basicConfig(level=logging.INFO)
    logging.info("SPARQL-MCP web server starting on http://0.0.0.0:8765 …")
    config = uvicorn.Config(app, host="0.0.0.0", port=8765, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
