"""Pre-computation of evacuation routes.

Two design points:

**One multi-source Dijkstra, not one search per origin-destination pair.**
A single Dijkstra seeded simultaneously from every safe zone gives each node
its cost to the *nearest* one in O(E log N), independent of how many safe
zones there are. Searching from each origin to each safe zone separately
would be O(S . N . E log N) for the same answer.

**Never write into ``data/``.**
Route tables live in ``cache/<zone>/``, keyed by a hash of the network they
were derived from, so a stale cache cannot be used silently. Writing derived
tables back over input data would make results depend on whether the model
had been run before.

The stored representation is a *next hop* per node, not a full path per agent:
memory is O(nodes), not O(agents x path length).
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd

def _project_root() -> Path:
    """Find the project root whether this module sits there or in src/.

    Anchored on the data/ folder, so the same file works unchanged in a flat
    working copy and in the packaged src/ layout.
    """
    here = Path(__file__).resolve().parent
    for base in (here, here.parent):
        if (base / "data").is_dir():
            return base
    return here


BASE_DIR = _project_root()
CACHE_DIR = BASE_DIR / "cache"

#: Bumped when the route-table format or the algorithm changes, so an old
#: cache is never silently reused with new code.
ROUTE_FORMAT_VERSION = 2


def _network_fingerprint(nodes: list[tuple[Any, Any]],
                         edges: list[tuple[Any, Any, Any]]) -> str:
    """Stable hash of the topology, edge costs and safe-zone flags."""
    digest = hashlib.sha256()
    digest.update(f"v{ROUTE_FORMAT_VERSION}\n".encode())
    for node_id, is_safe in sorted((str(a), str(b)) for a, b in nodes):
        digest.update(f"n:{node_id}:{is_safe}\n".encode())
    for start, end, cost in sorted((str(a), str(b), str(c)) for a, b, c in edges):
        digest.update(f"e:{start}:{end}:{cost}\n".encode())
    return digest.hexdigest()[:16]


def build_graph(nodes: list[tuple[Any, Any]],
                edges: list[tuple[Any, Any, Any]]) -> tuple[nx.Graph, set[int], set[int]]:
    """Undirected weighted graph plus the safe-zone and origin node sets."""
    graph = nx.Graph()
    safe_zones: set[int] = set()
    origins: set[int] = set()

    for node_id, is_safe in nodes:
        node = int(float(node_id))
        graph.add_node(node)
        (safe_zones if int(float(is_safe)) == 1 else origins).add(node)

    for start, end, cost in edges:
        u, v, w = int(float(start)), int(float(end)), float(cost)
        if u == v:
            continue
        # Parallel edges: keep the cheapest.
        existing = graph.get_edge_data(u, v, default=None)
        if existing is None or w < existing["weight"]:
            graph.add_edge(u, v, weight=w)

    return graph, safe_zones, origins


def solve_next_hops(graph: nx.Graph, safe_zones: set[int], origins: set[int]
                    ) -> tuple[list[dict[str, Any]], list[int]]:
    """One multi-source Dijkstra; then pick each node's best neighbour.

    Returns the route rows and the list of origins with no route at all.
    """
    reachable_sources = [s for s in safe_zones if s in graph]
    if not reachable_sources:
        return [], sorted(origins)

    # cost_to_safety[u] = cheapest cost from u to ANY safe zone.
    # The graph is undirected, so distance-from-sources equals distance-to-sources.
    cost_to_safety = nx.multi_source_dijkstra_path_length(
        graph, reachable_sources, weight="weight"
    )

    rows: list[dict[str, Any]] = []
    unroutable: list[int] = []
    for origin in sorted(origins):
        if origin not in cost_to_safety or origin not in graph:
            unroutable.append(origin)
            continue
        best_neighbour, best_total = None, float("inf")
        for neighbour, attrs in graph[origin].items():
            neighbour_cost = cost_to_safety.get(neighbour)
            if neighbour_cost is None:
                continue
            total = attrs["weight"] + neighbour_cost
            if total < best_total:
                best_neighbour, best_total = neighbour, total
        if best_neighbour is None:
            unroutable.append(origin)
            continue
        rows.append({
            "NodeID": origin,
            "NextNodeID": best_neighbour,
            "TotalCost": cost_to_safety[origin],
        })
    return rows, unroutable


def cache_paths(zone: str) -> tuple[Path, Path]:
    """Paths to a zone's cached route table and its metadata sidecar."""
    folder = CACHE_DIR / zone
    return folder / "routes.csv", folder / "routes.meta.json"


def read_cached(zone: str, fingerprint: str) -> Path | None:
    """Return the cached table only if it matches this exact network."""
    table, meta_path = cache_paths(zone)
    if not (table.is_file() and meta_path.is_file()):
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if meta.get("fingerprint") != fingerprint:
        return None
    if meta.get("format_version") != ROUTE_FORMAT_VERSION:
        return None
    return table


def compute_routes(link: Any, config: dict[str, Any], force: bool = False) -> Path:
    """Extract the network from NetLogo, solve, and cache the route table."""
    zone = str(config["input-zone"])
    print("Extracting network topology...")
    nodes = [(a, b) for a, b in link.report("[ (list node-id is-safe-zone) ] of nodes")]
    edges = [(a, b, c) for a, b, c in
             link.report("[ (list ([node-id] of end1) ([node-id] of end2) cost) ] of links")]

    fingerprint = _network_fingerprint(nodes, edges)
    if not force:
        cached = read_cached(zone, fingerprint)
        if cached is not None:
            print(f"Route cache hit ({fingerprint}) - {cached}")
            return cached

    graph, safe_zones, origins = build_graph(nodes, edges)
    print(f"Solving routes: {graph.number_of_nodes()} nodes, "
          f"{graph.number_of_edges()} edges, {len(safe_zones)} safe zones...")

    started = time.perf_counter()
    rows, unroutable = solve_next_hops(graph, safe_zones, origins)
    elapsed = time.perf_counter() - started

    table, meta_path = cache_paths(zone)
    table.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=["NodeID", "NextNodeID", "TotalCost"]).to_csv(
        table, index=False)

    # Record nodes that reach nothing, rather than dropping them.
    if unroutable:
        unroutable_path = table.parent / "unroutable_nodes.csv"
        pd.DataFrame({"NodeID": unroutable}).to_csv(unroutable_path, index=False)
        share = len(unroutable) / max(len(origins), 1) * 100
        print(f"  WARNING: {len(unroutable)} of {len(origins)} origin nodes "
              f"({share:.1f}%) have no route to any safe zone. "
              f"Listed in {unroutable_path.name}.")

    meta_path.write_text(json.dumps({
        "zone": zone,
        "fingerprint": fingerprint,
        "format_version": ROUTE_FORMAT_VERSION,
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "safe_zones": len(safe_zones),
        "origins": len(origins),
        "routed": len(rows),
        "unroutable": len(unroutable),
        "solve_seconds": round(elapsed, 4),
    }, indent=2), encoding="utf-8")

    print(f"  {len(rows)} routes solved in {elapsed:.3f} s -> {table}")
    return table


def resolve_route_tables(zone: str) -> tuple[Path | None, Path | None]:
    """Pick the route tables to run with, preferring the cache.

    Falls back to the table shipped in ``Inputs/`` so a fresh clone still runs
    without recomputation. ``Inputs/`` is only ever READ.
    """
    def pick(zone_name: str) -> Path | None:
        cached, _ = cache_paths(zone_name)
        if cached.is_file():
            return cached
        shipped = BASE_DIR / "data" / zone_name / f"rutas_{zone_name}.csv"
        return shipped if shipped.is_file() else None

    base_zone = zone.split("_colapso")[0]
    return pick(zone), pick(base_zone)
