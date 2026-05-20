import asyncio
import json
import logging
import os
import re
import time
from urllib.parse import urlparse, urlunparse
from rdflib import BNode, Graph, RDF, URIRef
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent, ServerCapabilities, ToolsCapability

from .handlers import execute_sparql
import requests


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


def _looks_like_void(text: str) -> bool:
    lowered = text.lower()
    return "void#" in lowered or "void:" in lowered


def _looks_like_service_description(text: str) -> bool:
    lowered = text.lower()
    return "sparql-service-description" in lowered or "sd:service" in lowered


def _extract_void_linkset(text: str) -> str | None:
    formats = ["turtle", "xml", "json-ld", "n3"]
    graph = Graph()
    parsed = False
    for fmt in formats:
        try:
            graph.parse(data=text, format=fmt)
            parsed = True
            break
        except Exception:
            continue
    if not parsed:
        return None

    linkset_type = URIRef("http://rdfs.org/ns/void#Linkset")
    linkset_subjects = set(graph.subjects(predicate=RDF.type, object=linkset_type))
    if not linkset_subjects:
        # Fallback: detect any triples with void:linkset predicate
        void_linkset_pred = URIRef("http://rdfs.org/ns/void#linkset")
        linkset_subjects = set(graph.objects(predicate=void_linkset_pred))
        if not linkset_subjects:
            return None

    linkset_graph = Graph()
    for subject in linkset_subjects:
        for triple in graph.triples((subject, None, None)):
            linkset_graph.add(triple)
    if len(linkset_graph) == 0:
        return None
    return linkset_graph.serialize(format="turtle")


def _extract_void_from_graph(graph: Graph) -> str | None:
    void_dataset = URIRef("http://rdfs.org/ns/void#Dataset")
    void_linkset = URIRef("http://rdfs.org/ns/void#Linkset")
    void_triples = Graph()
    queue = []
    for subj in graph.subjects(RDF.type, void_dataset):
        queue.append(subj)
    for subj in graph.subjects(RDF.type, void_linkset):
        queue.append(subj)

    seen = set()
    while queue:
        node = queue.pop()
        if node in seen:
            continue
        seen.add(node)
        for triple in graph.triples((node, None, None)):
            void_triples.add(triple)
            obj = triple[2]
            if isinstance(obj, BNode):
                queue.append(obj)
    if len(void_triples) == 0:
        return None
    return void_triples.serialize(format="turtle")


def _extract_void_links_from_service_description(text: str) -> list[str]:
    formats = ["turtle", "xml", "json-ld", "n3"]
    graph = Graph()
    parsed = False
    for fmt in formats:
        try:
            graph.parse(data=text, format=fmt)
            parsed = True
            break
        except Exception:
            continue
    if not parsed:
        return []

    void_text = _extract_void_from_graph(graph)
    if void_text:
        return [void_text]

    candidate_urls: set[str] = set()
    for _s, _p, obj in graph.triples((None, None, None)):
        if not isinstance(obj, URIRef):
            continue
        url = str(obj)
        lowered = url.lower()
        if "void" in lowered or lowered.endswith(".ttl") or lowered.endswith(".rdf"):
            candidate_urls.add(url)
    return sorted(candidate_urls)


def _has_non_prefix_triples(text: str) -> bool:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("@prefix") or stripped.startswith("@base") or stripped.startswith("#"):
            continue
        return True
    return False


def _http_get_text(
    url: str,
    *,
    accept: str,
    timeout_s: float = 10.0,
    allow_non_void: bool = False,
) -> str | None:
    try:
        response = requests.get(url, headers={"Accept": accept}, timeout=timeout_s)
        if response.status_code != 200:
            return None
        text = response.text
        if not text.strip():
            return None
        content_type = response.headers.get("Content-Type", "").lower()
        if allow_non_void and _looks_like_service_description(text):
            return text
        if _looks_like_void(text):
            return text
        if any(mt in content_type for mt in ("text/turtle", "application/ld+json", "application/rdf+xml", "text/n3")):
            return text
        return None
    except Exception:
        return None


def _sparql_construct(
    endpoint: str,
    query: str,
    *,
    timeout_s: float = 10.0,
    allow_non_void: bool = False,
) -> str | None:
    try:
        response = requests.get(
            endpoint,
            params={"query": query},
            headers={"Accept": "text/turtle"},
            timeout=timeout_s,
        )
        if response.status_code != 200:
            return None
        text = response.text
        if not text.strip():
            return None
        if allow_non_void:
            return text
        if _looks_like_void(text):
            return text
        return None
    except Exception:
        return None


def _sparql_select_json(endpoint: str, query: str, *, timeout_s: float = 10.0) -> dict | None:
    try:
        response = requests.get(
            endpoint,
            params={"query": query},
            headers={"Accept": "application/sparql-results+json"},
            timeout=timeout_s,
        )
        if response.status_code != 200:
            return None
        return response.json()
    except Exception:
        return None


def _build_well_known_urls(endpoint: str) -> list[str]:
    parsed = urlparse(endpoint)
    base_netloc = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
    urls = [
        f"{base_netloc}/.well-known/void",
        f"{base_netloc}/void",
        f"{base_netloc}/void.ttl",
    ]
    if parsed.path.endswith("/sparql"):
        base_path = parsed.path[:-len("/sparql")]
        base_url = urlunparse((parsed.scheme, parsed.netloc, base_path, "", "", ""))
        urls.extend(
            [
                f"{base_url}/.well-known/void",
                f"{base_url}/void",
                f"{base_url}/void.ttl",
            ]
        )
    return urls


def _retrieve_void_via_endpoint_strategies(endpoint: str) -> str | None:
    http_timeout_s = float(os.environ.get("VOID_HTTP_TIMEOUT_SECONDS", "40"))
    sparql_timeout_s = float(os.environ.get("VOID_SPARQL_TIMEOUT_SECONDS", "20"))

    # Strategy 1: HTTP metadata files (well-known)
    for url in _build_well_known_urls(endpoint):
        text = _http_get_text(url, accept="text/turtle", timeout_s=http_timeout_s)
        if text:
            logging.info("VoID retrieval strategy: well_known_http (%s) for %s", url, endpoint)
            return text

    # Strategy 2: VoID triples in default graph
    void_query = (
        "PREFIX void: <http://rdfs.org/ns/void#>\n"
        "CONSTRUCT { ?s ?p ?o }\n"
        "WHERE {\n"
        "  { ?s a void:Dataset ; ?p ?o . }\n"
        "  UNION\n"
        "  { ?s ?p ?o . FILTER(CONTAINS(STR(?p), \"void#\")) }\n"
        "}"
    )
    void_text = _sparql_construct(endpoint, void_query, timeout_s=sparql_timeout_s)
    if void_text:
        logging.info("VoID retrieval strategy: void_default_graph for %s", endpoint)
        return void_text

    # Strategy 3: Named metadata graph containing VoID
    graph_query = (
        "PREFIX void: <http://rdfs.org/ns/void#>\n"
        "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s a void:Dataset } } LIMIT 5"
    )
    graph_results = _sparql_select_json(endpoint, graph_query, timeout_s=sparql_timeout_s)
    if graph_results:
        bindings = graph_results.get("results", {}).get("bindings", [])
        for row in bindings:
            g = row.get("g", {}).get("value")
            if not g:
                continue
            graph_void_query = (
                "PREFIX void: <http://rdfs.org/ns/void#>\n"
                "CONSTRUCT { ?s ?p ?o }\n"
                f"WHERE {{ GRAPH <{g}> {{ ?s a void:Dataset ; ?p ?o . }} }}"
            )
            graph_text = _sparql_construct(endpoint, graph_void_query, timeout_s=sparql_timeout_s)
            if graph_text:
                logging.info("VoID retrieval strategy: void_named_graph (%s) for %s", g, endpoint)
                return graph_text

    # Strategy 4: Service description to locate VoID docs
    sd_text = _http_get_text(
        endpoint,
        accept="text/turtle",
        timeout_s=http_timeout_s,
        allow_non_void=True,
    )
    if sd_text and _has_non_prefix_triples(sd_text) and _looks_like_service_description(sd_text):
        void_links = _extract_void_links_from_service_description(sd_text)
        for link in void_links:
            if _looks_like_void(link):
                logging.info("VoID retrieval strategy: service_description_inline for %s", endpoint)
                return link
            void_doc = _http_get_text(link, accept="text/turtle", timeout_s=http_timeout_s)
            if void_doc:
                logging.info("VoID retrieval strategy: service_description_link (%s) for %s", link, endpoint)
                return void_doc

    return None


async def run() -> None:
    _load_env_file()
    logging.basicConfig(level=logging.INFO)
    logging.info("SPARQL-MCP stdio server starting…")
    server = Server("sparql-mcp")

    def get_exposed_tools(all_tools: list[Tool]) -> list[Tool]:
        raw = os.environ.get("EXPOSED_TOOLS")
        if not raw or raw.strip() == "*":
            return all_tools
        allowed = {name.strip() for name in raw.split(",") if name.strip()}
        if not allowed:
            return []
        return [tool for tool in all_tools if tool.name in allowed]

    def is_tool_exposed(tool_name: str) -> bool:
        raw = os.environ.get("EXPOSED_TOOLS")
        if not raw or raw.strip() == "*":
            return True
        allowed = {name.strip() for name in raw.split(",") if name.strip()}
        return tool_name in allowed

    @server.list_tools()
    async def list_tools():
        tools = [
            # Tool disabled: direct endpoint queries are routed through Fuseki now.
            # Tool(
            #     name="run_sparql_query",
            #     description="Execute a SPARQL 1.1 query (supports SERVICE for federated parts)",
            #     inputSchema={
            #         "type": "object",
            #         "required": ["endpoint", "query"],
            #         "properties": {
            #             "endpoint": {"type": "string"},
            #             "query": {"type": "string"},
            #             "format": {
            #                 "type": "string",
            #                 "enum": [
            #                     "sparql-results+json",
            #                     "text/turtle",
            #                     "application/ld+json",
            #                     "text/n3",
            #                 ],
            #                 "default": "sparql-results+json",
            #             },
            #             "timeout_ms": {"type": "integer", "minimum": 1000, "maximum": 120000},
            #         },
            #     },
            # ),
            Tool(
                name="run_sparql_query",
                description=(
                    "Execute a SPARQL 1.1 query. Queries must include SERVICE operators naming target SPARQL endpoints. "
                    "If the query contains exactly one SERVICE, it is sent directly to that endpoint. "
                    "If the query contains more than one SERVICE, it is executed via a local SPARQL federation endpoint."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {"type": "string"},
                        "format": {
                            "type": "string",
                            "enum": [
                                "sparql-results+json",
                                "text/turtle",
                                "application/ld+json",
                                "text/n3",
                            ],
                            "default": "sparql-results+json",
                        },
                        "timeout_ms": {"type": "integer", "minimum": 1000, "maximum": 100000}
                    }
                }
            ),
            Tool(
                name="get_void_descriptions",
                description=(
                    "Retrieve cached VoID descriptions for one or more SPARQL endpoints. "
                    "If not cached, the tool will report a miss (retrieval strategies are not implemented yet)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "endpoint": {"type": "string"},
                        "endpoints": {"type": "array", "items": {"type": "string"}},
                    },
                },
            ),
        ]
        return get_exposed_tools(tools)

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "run_sparql_query":
            if not is_tool_exposed(name):
                raise ValueError(f"Tool not exposed: {name}")
            query = arguments.get("query")
            format = arguments.get("format", "sparql-results+json")
            timeout_ms_arg = arguments.get("timeout_ms")
            if timeout_ms_arg is None:
                timeout_ms = int(float(os.environ.get("SPARQL_TIMEOUT_SECONDS", "100")) * 1000)
            else:
                timeout_ms = int(timeout_ms_arg)

            if not query:
                raise ValueError("Missing required argument: query")

            # Determine how many SERVICE endpoints are in the query and route accordingly.
            service_uris = re.findall(r"SERVICE\s*<([^>]+)>", query or "", flags=re.IGNORECASE)
            
            # FORCE FEDERATION: Always route SERVICE queries through the local Fuseki Federator.
            # This is required because the SERVICE URIs (e.g. http://fuseki-nyt:3030) are only 
            # resolvable from within the Docker network, not from this host script.
            # The "single service optimization" previously here broke this because it tried to
            # connect to the internal Docker URI directly from the host.
            
            if service_uris:
                 endpoint = os.environ.get("FEDERATION_ENDPOINT", "http://localhost:3030/ds/sparql")
            else:
                 # If no SERVICE clause, default to localhost:3030 (or whatever is configured)
                 # In this setup, we expect the agent to always use SERVICE as per prompt.
                 endpoint = os.environ.get("FEDERATION_ENDPOINT", "http://localhost:3030/ds/sparql")

            result = await execute_sparql(
                endpoint=endpoint,
                query=query,
                format=format,
                timeout_ms=timeout_ms,
            )

            log_msg = f"Executed query via {endpoint}"
            logging.info(log_msg)

            return [
                TextContent(type="text", text=result.preview),
                TextContent(type="text", text=result.payload_text),
                TextContent(type="text", text=f"Log: {log_msg}"),
            ]

        if name == "get_void_descriptions":
            if not is_tool_exposed(name):
                raise ValueError(f"Tool not exposed: {name}")
            endpoints_arg = arguments.get("endpoints")
            endpoint_arg = arguments.get("endpoint")
            endpoints: list[str] = []
            if isinstance(endpoint_arg, str) and endpoint_arg.strip():
                endpoints.append(endpoint_arg.strip())
            if isinstance(endpoints_arg, list):
                endpoints.extend([e for e in endpoints_arg if isinstance(e, str) and e.strip()])

            if not endpoints:
                raise ValueError("Provide 'endpoint' or 'endpoints' with at least one value.")

            default_store = Path("local_store") / "void_descriptions"
            store_root = Path(os.environ.get("LOCAL_STORE", str(default_store)))
            index_path = store_root / "void_index.json"
            index_data = {}
            if index_path.exists():
                try:
                    index_data = json.loads(index_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    index_data = {}
            ttl_seconds = int(os.environ.get("VOID_CACHE_TTL_SECONDS", "604800"))
            now_ts = time.time()
            endpoint_results = []
            for endpoint in endpoints:
                if endpoint in index_data:
                    entry = index_data[endpoint]
                    if isinstance(entry, dict) and isinstance(entry.get("void_text"), str):
                        cached_at = entry.get("cached_at")
                        is_stale = False
                        if isinstance(cached_at, (int, float)):
                            is_stale = (now_ts - float(cached_at)) > ttl_seconds
                        else:
                            is_stale = True
                        if not is_stale:
                            void_linkset = entry.get("void_linkset")
                            endpoint_results.append(
                                {
                                    "endpoint": endpoint,
                                    "status": "found",
                                    "void_text": entry["void_text"],
                                    "void_linkset": void_linkset,
                                    "void_path": str(index_path),
                                    "store_root": str(store_root),
                                    "cached_at": cached_at,
                                    "cache_ttl_seconds": ttl_seconds,
                                    "note": (
                                        "Loaded from local_store index. If not cached: endpoint-specific "
                                        "retrieval strategies and SPARQL-based minimal VoID extraction "
                                        "are not implemented yet."
                                    ),
                                }
                            )
                            continue

                        refreshed = _retrieve_void_via_endpoint_strategies(endpoint)
                        if isinstance(refreshed, str) and refreshed:
                            void_linkset = _extract_void_linkset(refreshed)
                            payload = {"void_text": refreshed, "cached_at": now_ts}
                            if isinstance(void_linkset, str) and void_linkset:
                                payload["void_linkset"] = void_linkset
                            index_data[endpoint] = payload
                            index_path.parent.mkdir(parents=True, exist_ok=True)
                            index_path.write_text(
                                json.dumps(index_data, ensure_ascii=True, indent=2),
                                encoding="utf-8",
                            )
                            endpoint_results.append(
                                {
                                    "endpoint": endpoint,
                                    "status": "refreshed",
                                    "void_text": refreshed,
                                    "void_linkset": void_linkset,
                                    "void_path": str(index_path),
                                    "store_root": str(store_root),
                                    "cached_at": now_ts,
                                    "cache_ttl_seconds": ttl_seconds,
                                    "note": "VoID refreshed via endpoint-specific retrieval strategy.",
                                }
                            )
                            continue

                        endpoint_results.append(
                            {
                                "endpoint": endpoint,
                                "status": "stale",
                                "void_text": entry.get("void_text"),
                                "void_linkset": entry.get("void_linkset"),
                                "void_path": str(index_path),
                                "store_root": str(store_root),
                                "cached_at": cached_at,
                                "cache_ttl_seconds": ttl_seconds,
                                "note": (
                                    "Cached VoID is stale and should be re-retrieved. Returning stale "
                                    "value because endpoint-specific retrieval strategies are not implemented yet."
                                ),
                            }
                        )
                        continue

                    if isinstance(entry, str):
                        endpoint_results.append(
                            {
                                "endpoint": endpoint,
                                "status": "found",
                                "void_text": entry,
                                "void_linkset": None,
                                "void_path": str(index_path),
                                "store_root": str(store_root),
                                "note": (
                                    "Loaded from local_store index (no timestamp). If not cached: endpoint-specific "
                                    "retrieval strategies and SPARQL-based minimal VoID extraction "
                                    "are not implemented yet."
                                ),
                            }
                        )
                        continue

                match = re.search(r"/([^/]+)-shard(\d+)/sparql", endpoint)
                dataset = match.group(1) if match else None
                shard_id = match.group(2) if match else None
                void_text = None
                void_path = None
                status = "missing"

                if dataset is not None and shard_id is not None:
                    void_path = store_root / dataset / f"shard{shard_id}_void.ttl"
                    if void_path.exists():
                        void_text = void_path.read_text(encoding="utf-8")
                        status = "found"
                if void_text is None:
                    refreshed = _retrieve_void_via_endpoint_strategies(endpoint)
                    if isinstance(refreshed, str) and refreshed:
                        void_linkset = _extract_void_linkset(refreshed)
                        payload = {"void_text": refreshed, "cached_at": now_ts}
                        if isinstance(void_linkset, str) and void_linkset:
                            payload["void_linkset"] = void_linkset
                        index_data[endpoint] = payload
                        index_path.parent.mkdir(parents=True, exist_ok=True)
                        index_path.write_text(
                            json.dumps(index_data, ensure_ascii=True, indent=2),
                            encoding="utf-8",
                        )
                        endpoint_results.append(
                            {
                                "endpoint": endpoint,
                                "status": "retrieved",
                                "void_text": refreshed,
                                "void_linkset": void_linkset,
                                "void_path": str(index_path),
                                "store_root": str(store_root),
                                "cached_at": now_ts,
                                "cache_ttl_seconds": ttl_seconds,
                                "note": "VoID retrieved via endpoint-specific strategy and cached.",
                            }
                        )
                        continue

                endpoint_results.append(
                    {
                        "endpoint": endpoint,
                        "status": status,
                        "void_text": void_text,
                        "void_path": str(void_path) if void_path else None,
                        "store_root": str(store_root),
                        "note": (
                            "If not cached: endpoint-specific retrieval strategies and "
                            "SPARQL-based minimal VoID extraction are not implemented yet."
                        ),
                    }
                )

            payload = json.dumps({"results": endpoint_results}, ensure_ascii=True)
            return [TextContent(type="text", text=payload)]

        raise ValueError(f"Unknown tool: {name}")

    async with stdio_server() as (read, write):
        logging.info("SPARQL-MCP stdio transport ready; waiting for client…")
        init_opts = InitializationOptions(
            server_name="sparql-mcp",
            server_version="0.0.1",
            capabilities=ServerCapabilities(tools=ToolsCapability()),
            instructions="SPARQL-MCP: run SPARQL 1.1 queries (with SERVICE) via run_sparql_query.",
        )
        await server.run(read, write, initialization_options=init_opts)
    logging.info("SPARQL-MCP stdio server stopped.")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
