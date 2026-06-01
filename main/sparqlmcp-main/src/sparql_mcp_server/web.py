from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import uuid
from pathlib import Path
from urllib.parse import unquote
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


def _extract_search_terms(nl_query: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]{2,}", nl_query.lower())
    stopwords = {
        "all", "the", "and", "for", "with", "from", "about", "show", "list", "find",
        "what", "which", "that", "this", "these", "those", "into", "related", "relation",
        "relations", "relationship", "relationships", "between", "entities", "entity", "records", "record", "data", "database", "any",
    }
    terms: list[str] = []
    for token in tokens:
        if token in stopwords:
            continue
        normalized = token
        if token.endswith("ies") and len(token) > 4:
            normalized = token[:-3] + "y"
        elif token.endswith("es") and len(token) > 4:
            normalized = token[:-2]
        elif token.endswith("s") and len(token) > 3:
            normalized = token[:-1]
        for candidate in (token, normalized):
            if candidate not in terms:
                terms.append(candidate)
    return terms[:3]


def _build_fallback_query(nl_query: str) -> str:
    query_text = nl_query.lower()

    wants_malware = any(keyword in query_text for keyword in ("malware", "emotet", "botnet", "threat", "family"))
    wants_vulnerability = "cve" in query_text or "vulnerabil" in query_text or "json" in query_text
    wants_target = any(keyword in query_text for keyword in ("cpe", "product", "vendor", "target"))

    if wants_malware and wants_vulnerability and wants_target:
        terms = _extract_search_terms(nl_query)
        if not terms:
            terms = [query_text]
        escaped_terms = [term.replace('"', '\\"') for term in terms[:4]]
        filters = " || ".join(
            f'CONTAINS(LCASE(STR(COALESCE(?label, ?description, ?vendor, ?product, ""))), "{term}")'
            for term in escaped_terms
        )
        if not filters:
            filters = 'true'
        return (
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
            "PREFIX dcterms: <http://purl.org/dc/terms/>\n"
            "PREFIX cve: <http://w3id.org/sepses/vocab/ref/cve#>\n"
            "PREFIX cpe: <http://w3id.org/sepses/vocab/ref/cpe#>\n"
            "PREFIX cwe: <http://w3id.org/sepses/vocab/ref/cwe#>\n"
            "PREFIX malware: <http://w3id.org/sepses/vocab/ref/malware#>\n"
            "SELECT DISTINCT ?entity ?label ?type ?description ?firstSeen ?vendor ?product WHERE {\n"
            "  {\n"
            "    ?entity a malware:MalwareFamily ;\n"
            "            rdfs:label ?label .\n"
            "    OPTIONAL { ?entity malware:firstSeen ?firstSeen }\n"
            "    OPTIONAL { ?entity dcterms:description ?description }\n"
            "    BIND('malware' AS ?type)\n"
            "  } UNION {\n"
            "    ?entity a cve:CVE ;\n"
            "            rdfs:label ?label .\n"
            "    OPTIONAL { ?entity dcterms:description ?description }\n"
            "    BIND('vulnerability' AS ?type)\n"
            "  } UNION {\n"
            "    ?entity a cpe:CPE ;\n"
            "            rdfs:label ?label .\n"
            "    OPTIONAL { ?entity cpe:hasVendor ?vendor }\n"
            "    OPTIONAL { ?entity cpe:hasProduct ?product }\n"
            "    OPTIONAL { ?entity dcterms:description ?description }\n"
            "    BIND('target' AS ?type)\n"
            "  }\n"
            f"  FILTER({filters})\n"
            "}\n"
            "LIMIT 100"
        )

    if "cve" in query_text or "vulnerabil" in query_text:
        # If the NL query contains additional terms (e.g. "frontend", "wordpress"),
        # prefer a filtered CVE query that searches labels/descriptions for those terms.
        terms = _extract_search_terms(nl_query)
        escaped_terms = [term.replace('"', '\\"') for term in terms[:4]] if terms else []
        filter_clause = ""
        if escaped_terms:
            filters = " || ".join(
                f'CONTAINS(LCASE(STR(COALESCE(?label, ?description, ""))), "{term}")'
                for term in escaped_terms
            )
            filter_clause = f"  FILTER({filters})\n"

        return (
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
            "PREFIX dcterms: <http://purl.org/dc/terms/>\n"
            "PREFIX cve: <http://w3id.org/sepses/vocab/ref/cve#>\n"
            "PREFIX cwe: <http://w3id.org/sepses/vocab/ref/cwe#>\n"
            "PREFIX cvss: <http://w3id.org/sepses/vocab/ref/cvss#>\n"
            "SELECT DISTINCT ?s ?label ?description ?issued ?modified WHERE {\n"
            "  ?s a cve:CVE .\n"
            "  OPTIONAL { ?s rdfs:label ?label }\n"
            "  OPTIONAL { ?s dcterms:description ?description }\n"
            "  OPTIONAL { ?s dcterms:issued ?issued }\n"
            "  OPTIONAL { ?s dcterms:modified ?modified }\n"
            f"{filter_clause}"
            "}\n"
            "LIMIT 100"
        )

    if "cwe" in query_text or "weakness" in query_text:
        return (
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
            "PREFIX dcterms: <http://purl.org/dc/terms/>\n"
            "PREFIX cwe: <http://w3id.org/sepses/vocab/ref/cwe#>\n"
            "SELECT DISTINCT ?s ?label ?description WHERE {\n"
            "  ?s a cwe:CWE .\n"
            "  OPTIONAL { ?s rdfs:label ?label }\n"
            "  OPTIONAL { ?s dcterms:description ?description }\n"
            "}\n"
            "LIMIT 100"
        )

    if "cpe" in query_text or "product" in query_text or "vendor" in query_text:
        return (
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
            "PREFIX dcterms: <http://purl.org/dc/terms/>\n"
            "PREFIX cpe: <http://w3id.org/sepses/vocab/ref/cpe#>\n"
            "SELECT DISTINCT ?s ?label ?title ?vendor ?product ?version WHERE {\n"
            "  ?s a cpe:CPE .\n"
            "  OPTIONAL { ?s rdfs:label ?label }\n"
            "  OPTIONAL { ?s cpe:title ?title }\n"
            "  OPTIONAL { ?s cpe:hasVendor ?vendor }\n"
            "  OPTIONAL { ?s cpe:hasProduct ?product }\n"
            "  OPTIONAL { ?s cpe:version ?version }\n"
            "}\n"
            "LIMIT 100"
        )

    terms = _extract_search_terms(nl_query)
    if not terms:
        terms = [nl_query.strip().lower()]
    escaped_terms = [term.replace('"', '\\"') for term in terms[:4]]
    filter_clause = " || ".join(
        f'CONTAINS(LCASE(STR(?s)), "{term}") || CONTAINS(LCASE(COALESCE(STR(?label), "")), "{term}")'
        for term in escaped_terms
    )

    return (
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
        "PREFIX skos: <http://www.w3.org/2004/02/skos/core#>\n"
        "SELECT DISTINCT ?s ?label WHERE {\n"
        "  OPTIONAL { ?s rdfs:label ?rdfsLabel }\n"
        "  OPTIONAL { ?s skos:prefLabel ?prefLabel }\n"
        "  OPTIONAL { ?s skos:altLabel ?altLabel }\n"
        "  BIND(COALESCE(?rdfsLabel, ?prefLabel, ?altLabel) AS ?label)\n"
        f"  FILTER({filter_clause})\n"
        "}\n"
        "LIMIT 100"
    )


def _query_looks_too_generic(nl_query: str, query: str) -> bool:
    query_text = query.lower()
    if not query_text.strip():
        return True

    terms = _extract_search_terms(nl_query)
    content_terms = [
        term for term in terms
        if term not in {"cve", "cwe", "cpe", "malware", "vulnerability", "vulnerabilities", "product", "target", "relation", "related"}
    ]
    if content_terms and any(term in query_text for term in content_terms):
        return False

    if re.search(r"\?s\s+a\s+cve:cve\b", query_text) and not re.search(r"\bfilter\b", query_text):
        return True
    if re.search(r"\?s\s+a\s+cpe:cpe\b", query_text) and not re.search(r"\bfilter\b", query_text):
        return True
    if re.search(r"\?s\s+a\s+cwe:cwe\b", query_text) and not re.search(r"\bfilter\b", query_text):
        return True
    return False


def _short_resource_label(value: str | None) -> str:
    if not value:
        return ""
    text = str(value).replace("<", "").replace(">", "")
    text = text.replace("http://", "").replace("https://", "")
    tail = re.split(r"[\/#+]", text)[-1]
    return _decode_uri_component(tail)


def _decode_uri_component(value: str) -> str:
    try:
        return unquote(value)
    except Exception:
        return value


def _classify_resource(value: str | None) -> str:
    text = (value or "").lower()
    if (
        "cve" in text
        or "vulnerab" in text
        or "cwe" in text
        or "cvss" in text
        or "reference" in text
        or "/cve/" in text
        or "/cwe/" in text
    ):
        return "vulnerability"
    if "cpe" in text or "vendor" in text or "product" in text:
        return "target"
    if "malware" in text or "family" in text or "threat" in text:
        return "malware"
    return "target"


def _pick_binding_iri(binding: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = binding.get(key, {}).get("value")
        if value and str(value).startswith("http"):
            return str(value)
    return None


def _pick_any_binding_iri(binding: dict[str, Any]) -> str | None:
    for cell in binding.values():
        value = cell.get("value")
        if value and str(value).startswith("http"):
            return str(value)
    return None


def _normalize_relation_seed_uri(uri: str | None) -> str | None:
    if not uri:
        return None

    text = str(uri)
    match = re.match(r"^https?://w3id\.org/sepses/vocab/ref/([^#]+)#(.+)$", text)
    if not match:
        return text

    namespace = match.group(1)
    identifier = match.group(2)
    return f"http://w3id.org/sepses/resource/{namespace}/{identifier}"


def _is_relevant_relation(predicate: str | None) -> bool:
    return predicate != "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"


def _build_relation_graph_node(uri: str, *, label: str | None = None) -> dict[str, Any]:
    return {
        "id": uri,
        "label": label or _short_resource_label(uri),
        "group": _classify_resource(uri),
        "title": uri,
    }


def _build_relation_graph_rows(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not payload:
        return []
    bindings = payload.get("results", {}).get("bindings", [])
    return bindings if isinstance(bindings, list) else []


def _build_extractive_summary(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    """Build a short extractive summary from the top descriptions in SPARQL results.

    This is intentionally extractive (no LLM) and uses only data returned by the
    SPARQL results to avoid hallucination.
    """
    if not payload:
        return None
    bindings = payload.get("results", {}).get("bindings", []) or []
    descriptions: list[str] = []
    for b in bindings:
        # Common description fields used by queries
        desc = (
            b.get("description", {}) .get("value")
            if isinstance(b.get("description", {}), dict)
            else None
        )
        if not desc:
            desc = b.get("dcterms:description", {}).get("value") if isinstance(b.get("dcterms:description", {}), dict) else None
        if not desc:
            # fallback: try label to give short context
            desc = b.get("label", {}).get("value") if isinstance(b.get("label", {}), dict) else None
        if not desc:
            continue
        first_sentence = re.split(r"(?<=[.!?])\s+", str(desc).strip())[0]
        if first_sentence:
            descriptions.append(first_sentence)
        if len(descriptions) >= 3:
            break

    if not descriptions:
        return None

    summary_text = " — ".join(descriptions)
    return {"text": summary_text, "source_count": len(descriptions)}


async def _fetch_relation_graph(endpoint: str, payload: dict[str, Any] | None, *, timeout_ms: int) -> dict[str, Any]:
    bindings = _build_relation_graph_rows(payload)
    seed_uris: list[str] = []
    for binding in bindings[:4]:
        seed = _pick_binding_iri(binding, ("s", "entity", "subject", "resource", "uri", "id"))
        if not seed:
            seed = _pick_any_binding_iri(binding)
        seed = _normalize_relation_seed_uri(seed)
        if seed and seed not in seed_uris:
            seed_uris.append(seed)

    if not seed_uris:
        return {"nodes": [], "edges": []}

    iri_values = " ".join(f"<{uri}>" for uri in seed_uris)
    graph_queries = [
        (
            "outgoing",
            f"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?s ?p ?o ?sLabel ?oLabel WHERE {{
  VALUES ?s {{ {iri_values} }}
  ?s ?p ?o .
  FILTER(isIRI(?o))
  OPTIONAL {{ ?s rdfs:label ?sLabel }}
  OPTIONAL {{ ?o rdfs:label ?oLabel }}
}}
LIMIT 40
""".strip(),
        ),
        (
            "incoming",
            f"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?s ?p ?o ?sLabel ?oLabel WHERE {{
  VALUES ?o {{ {iri_values} }}
  ?s ?p ?o .
  FILTER(isIRI(?s))
  OPTIONAL {{ ?s rdfs:label ?sLabel }}
  OPTIONAL {{ ?o rdfs:label ?oLabel }}
}}
LIMIT 40
""".strip(),
        ),
    ]

    node_map: dict[str, dict[str, Any]] = {}
    edge_map: dict[tuple[str, str, str], dict[str, Any]] = {}

    for _, graph_query in graph_queries:
        graph_result = await execute_sparql(
            endpoint=endpoint,
            query=graph_query,
            format="sparql-results+json",
            timeout_ms=timeout_ms,
        )
        try:
            graph_payload = json.loads(graph_result.payload_text)
        except json.JSONDecodeError:
            continue

        for row in graph_payload.get("results", {}).get("bindings", []):
            subject = _pick_binding_iri(row, ("s",))
            obj = _pick_binding_iri(row, ("o",))
            predicate = _pick_binding_iri(row, ("p",))
            if not subject or not obj or not predicate:
                continue
            if not _is_relevant_relation(predicate):
                continue

            subject_label = row.get("sLabel", {}).get("value") or None
            object_label = row.get("oLabel", {}).get("value") or None

            if subject not in node_map:
                node_map[subject] = _build_relation_graph_node(subject, label=subject_label)
            if obj not in node_map:
                node_map[obj] = _build_relation_graph_node(obj, label=object_label)

            edge_key = (subject, predicate, obj)
            if edge_key not in edge_map:
                edge_map[edge_key] = {
                    "from": subject,
                    "to": obj,
                    "label": _short_resource_label(predicate),
                    "arrows": "to",
                    "title": predicate,
                }

    return {
        "nodes": list(node_map.values()),
        "edges": list(edge_map.values()),
    }


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


def _call_openrouter(nl_query: str, *, retry: bool, previous_query: str | None) -> dict:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY is not set.")

    base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()

    model = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
    max_tokens = int(os.environ.get("OPENROUTER_MAX_TOKENS", "800"))
    temperature = float(os.environ.get("OPENROUTER_TEMPERATURE", "0.2"))
    http_referer = os.environ.get("OPENROUTER_HTTP_REFERER", "http://localhost:5173").strip()
    app_title = os.environ.get("OPENROUTER_APP_TITLE", "SPARQL-MCP Kelompok 2").strip()

    prompt = _build_llm_prompt(nl_query, retry=retry, previous_query=previous_query)
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }

    headers = {
        "authorization": f"Bearer {api_key}",
        "http-referer": http_referer,
        "x-title": app_title,
        "content-type": "application/json",
    }

    url = base_url.rstrip("/") + "/chat/completions"
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"OpenRouter API error: {exc}") from exc

    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        raise HTTPException(status_code=502, detail="OpenRouter API returned empty choices.")

    message = choices[0].get("message", {})
    combined = message.get("content", "")
    if not combined:
        combined = choices[0].get("text", "")
    if not combined:
        raise HTTPException(status_code=502, detail="OpenRouter API returned empty content.")

    try:
        return _extract_json(combined)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _call_raw_llm(prompt: str) -> dict:
    """Call the configured LLM provider with a raw prompt and return parsed JSON.

    This is used only for optional summarization. If the provider isn't configured
    or the call fails, raise HTTPException so callers can fallback.
    """
    provider = os.environ.get("LLM_PROVIDER", "openrouter").strip().lower()
    if provider in {"claude", "anthropic"}:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY is not set for summary generation.")
        model = os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
        max_tokens = int(os.environ.get("CLAUDE_MAX_TOKENS", "300"))
        temperature = float(os.environ.get("CLAUDE_TEMPERATURE", "0.0"))
        payload = {"model": model, "max_tokens": max_tokens, "temperature": temperature, "messages": [{"role": "user", "content": prompt}]}
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=30)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Claude API error (summary): {exc}") from exc
        data = response.json()
        content = data.get("content", [])
        combined = "".join(part.get("text", "") for part in content if part.get("type") == "text")
    else:
        # default to openrouter-compatible endpoint
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY is not set for summary generation.")
        base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()
        model = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
        max_tokens = int(os.environ.get("OPENROUTER_MAX_TOKENS", "300"))
        temperature = float(os.environ.get("OPENROUTER_TEMPERATURE", "0.0"))
        payload = {"model": model, "max_tokens": max_tokens, "temperature": temperature, "messages": [{"role": "user", "content": prompt}]}
        headers = {"authorization": f"Bearer {api_key}", "content-type": "application/json"}
        url = base_url.rstrip("/") + "/chat/completions"
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"OpenRouter API error (summary): {exc}") from exc
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise HTTPException(status_code=502, detail="OpenRouter API returned empty choices for summary.")
        message = choices[0].get("message", {})
        combined = message.get("content", "") or choices[0].get("text", "")

    try:
        return _extract_json(combined)
    except ValueError:
        # If LLM didn't return parseable JSON, raise so caller can fallback
        raise HTTPException(status_code=502, detail="LLM summary did not return JSON")


def _call_llm(nl_query: str, *, retry: bool, previous_query: str | None) -> dict:
    provider = os.environ.get("LLM_PROVIDER", "openrouter").strip().lower()
    if provider in {"claude", "anthropic"}:
        return _call_claude(nl_query, retry=retry, previous_query=previous_query)
    if provider in {"openrouter", "openrouter.ai", "openrouter-ai", "openai_compat", "openai-compatible", "router", "multi"}:
        return _call_openrouter(nl_query, retry=retry, previous_query=previous_query)
    raise HTTPException(status_code=500, detail=f"Unsupported LLM_PROVIDER: {provider}")


class NLQueryOptions(BaseModel):
    format: str = Field(default="sparql-results+json")
    timeout_ms: int = Field(default=30000, ge=1000, le=120000)
    expose_sparql: bool = True
    refine_on_empty: bool = True
    use_llm_summary: bool = True


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

    # Allow opt-out of LLM-based NL->SPARQL generation via env var for stability/testing.
    disable_llm = os.environ.get("DISABLE_LLM_NL2SPARQL", "").strip().lower() in {"1", "true", "yes"}
    if disable_llm:
        query = _build_fallback_query(request.nl_query)
    else:
        first = _call_llm(request.nl_query, retry=False, previous_query=None)
        query = str(first.get("query", "")).strip()
        if not query:
            raise HTTPException(status_code=502, detail="LLM response did not include a query.")

    # If the LLM returned a query that still contains natural-language tokens
    # (e.g., 'tell', 'about', 'list'), treat it as a failure and use the
    # programmatic fallback query builder instead. This avoids returning
    # queries that embed user prompt text and produce generic results.
    if re.search(r"\b(tell|about|list|show|find|what|which)\b", query, flags=re.IGNORECASE):
        query = _build_fallback_query(request.nl_query)

    if _query_looks_too_generic(request.nl_query, query):
        query = _build_fallback_query(request.nl_query)

    _reject_unsafe_query(query)
    _validate_query_size(query)
    _validate_endpoints(query)

    limit_default = int(os.environ.get("DEFAULT_QUERY_LIMIT", "100"))
    query = _ensure_limit(query, limit_default)
    endpoint = _route_endpoint(query)

    logging.info("Executing SPARQL (truncated): %s", (query or '')[:400])
    try:
        result = await execute_sparql(
            endpoint=endpoint,
            query=query,
            format=options.format,
            timeout_ms=options.timeout_ms,
        )
    except Exception as exc:
        # If the first query fails (e.g., malformed or unsupported constructs),
        # retry with a minimal, safer query that filters on the first meaningful
        # search term. This prevents a 500 response and returns something useful.
        logging.warning("Initial SPARQL execution failed: %s; retrying with safe query", exc)
        terms = _extract_search_terms(request.nl_query)
        fallback_term = terms[0] if terms else "cve"
        safe_query = (
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
            "PREFIX dcterms: <http://purl.org/dc/terms/>\n"
            "PREFIX cve: <https://w3id.org/sepses/vocab/ref/cve#>\n"
            "SELECT DISTINCT ?s ?label ?description ?issued ?modified WHERE {\n"
            "  ?s a cve:CVE .\n"
            "  OPTIONAL { ?s rdfs:label ?label }\n"
            "  OPTIONAL { ?s dcterms:description ?description }\n"
            f"  FILTER(CONTAINS(LCASE(COALESCE(?label, ?description, "")), \"{fallback_term}\"))\n"
            "}\n"
            "LIMIT 100"
        )
        try:
            result = await execute_sparql(
                endpoint=endpoint,
                query=safe_query,
                format=options.format,
                timeout_ms=options.timeout_ms,
            )
            query = safe_query
        except Exception as exc2:
            logging.exception("Safe fallback SPARQL also failed: %s", exc2)
            raise HTTPException(status_code=502, detail=f"SPARQL execution failed: {exc2}") from exc2

    payload: dict[str, Any] | None = None
    if options.format == "sparql-results+json":
        try:
            payload = json.loads(result.payload_text)
        except json.JSONDecodeError:
            payload = None

    if options.refine_on_empty and _is_empty_results(payload):
        fallback_query = _build_fallback_query(request.nl_query)
        _reject_unsafe_query(fallback_query)
        _validate_query_size(fallback_query)
        _validate_endpoints(fallback_query)
        fallback_query = _ensure_limit(fallback_query, limit_default)
        fallback_endpoint = _route_endpoint(fallback_query)
        fallback_result = await execute_sparql(
            endpoint=fallback_endpoint,
            query=fallback_query,
            format=options.format,
            timeout_ms=options.timeout_ms,
        )
        query = fallback_query
        endpoint = fallback_endpoint
        result = fallback_result
        if options.format == "sparql-results+json":
            try:
                payload = json.loads(result.payload_text)
            except json.JSONDecodeError:
                payload = None

    graph = await _fetch_relation_graph(endpoint, payload, timeout_ms=options.timeout_ms)
    summary = _build_extractive_summary(payload)

    # If relation-graph extraction returned no nodes, build a minimal graph
    # from the top result bindings so the frontend can display something.
    try:
        if (not graph) or (isinstance(graph, dict) and len(graph.get("nodes", [])) == 0):
            bindings = (payload or {}).get("results", {}).get("bindings", []) or []
            nodes = []
            edges = []
            root_id = "search-root"
            if bindings:
                nodes.append({"id": root_id, "label": "Search Results", "group": "target", "title": root_id})
                seen = set()
                for b in bindings[:12]:
                    uri = b.get("s", {}).get("value") or b.get("entity", {}).get("value")
                    label = None
                    if isinstance(b.get("label", {}), dict):
                        label = b.get("label", {}).get("value")
                    elif isinstance(b.get("rdfs:label", {}), dict):
                        label = b.get("rdfs:label", {}).get("value")
                    if not uri:
                        continue
                    if uri in seen:
                        continue
                    seen.add(uri)
                    nodes.append({
                        "id": uri,
                        "label": label or _short_resource_label(uri),
                        "group": _classify_resource(uri),
                        "title": uri,
                    })
                    edges.append({"from": root_id, "to": uri, "label": "result", "arrows": "to"})
            graph = {"nodes": nodes, "edges": edges}
    except Exception:
        # If fallback graph generation fails, leave graph as-is (None)
        pass

    # Optionally produce an enhanced summary (Option B) built from top results.
    if options.use_llm_summary:
        bindings = (payload or {}).get("results", {}).get("bindings", []) or []
        if bindings:
            # Collect up to three top items with id/label and a short description sentence
            items: list[tuple[str, str]] = []  # (id_or_label, short_desc)
            for b in bindings[:3]:
                label = None
                # prefer label fields, fall back to rdfs:label or the 's' IRI tail
                if isinstance(b.get("label", {}), dict):
                    label = b.get("label", {}).get("value")
                elif isinstance(b.get("rdfs:label", {}), dict):
                    label = b.get("rdfs:label", {}).get("value")
                if not label:
                    s = b.get("s", {}).get("value") or b.get("entity", {}).get("value")
                    if s:
                        label = _short_resource_label(s)

                desc = None
                if isinstance(b.get("description", {}), dict):
                    desc = b.get("description", {}).get("value")
                elif isinstance(b.get("dcterms:description", {}), dict):
                    desc = b.get("dcterms:description", {}).get("value")

                short_desc = ""
                if desc:
                    short_desc = re.split(r"(?<=[.!?])\s+", str(desc).strip())[0]

                if label:
                    items.append((label, short_desc))

            # Build Option B paragraph when we have at least one item
            if items:
                # Sentence 1: list items
                names = [it[0] for it in items]
                if len(names) == 1:
                    first_sent = f"The data shows the following related CVE: {names[0]}."
                elif len(names) == 2:
                    first_sent = f"The data shows the following related CVEs: {names[0]} and {names[1]}."
                else:
                    first_sent = f"The data shows several related CVEs: {names[0]}, {names[1]}, and {names[2]}."

                # Sentence 2: brief explanation per item when available
                explanations = []
                for name, sd in items:
                    if sd:
                        explanations.append(f"{name} involves {sd}")
                    else:
                        explanations.append(f"{name} involves a security-related issue")
                if len(explanations) == 1:
                    second_sent = explanations[0] + "."
                else:
                    second_sent = ", ".join(explanations[:-1]) + ", and " + explanations[-1] + "."

                third_sent = "Use the CVE IDs to view details and mitigation steps."

                summary_text = " ".join([first_sent, second_sent, third_sent])
                summary = {"text": summary_text, "source": "auto", "source_count": len(items)}

    response_body = {
        "trace_id": trace_id,
        "preview": result.preview,
        "results": payload or result.payload_text,
        "graph": graph,
        "summary": summary,
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
