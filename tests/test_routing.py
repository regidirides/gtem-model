"""Routing: the fast method must agree with the slow one it replaced.

The multi-source formulation is ~5,000x faster than searching each
origin-destination pair. Speed is worthless if the answers differ, so this
asserts equality of both the cost and the chosen next hop, on a fixture graph
and on the real shipped network.
"""

from __future__ import annotations

import struct
import time
from pathlib import Path

import networkx as nx
import pytest

from routing import build_graph, solve_next_hops

ROOT = Path(__file__).resolve().parent.parent
ZONE_DIR = ROOT / "data" / "Chimbote_Zona1"


def v08_nested_loop(nodes, edges):
    """The naive per-pair search, as a reference implementation."""
    graph = nx.DiGraph()
    shelters, origins = [], []
    for node_id, is_shelter in nodes:
        node = int(float(node_id))
        graph.add_node(node)
        (shelters if int(float(is_shelter)) == 1 else origins).append(node)
    for start, end, cost in edges:
        u, v, w = int(float(start)), int(float(end)), float(cost)
        graph.add_edge(u, v, weight=w)
        graph.add_edge(v, u, weight=w)
    out = {}
    for origin in origins:
        best_cost, best_path = 9999999, []
        for shelter in shelters:
            try:
                cost = nx.shortest_path_length(graph, origin, shelter, weight="weight")
                if cost < best_cost:
                    best_cost = cost
                    best_path = nx.shortest_path(graph, origin, shelter, weight="weight")
            except nx.NetworkXNoPath:
                continue
        if best_cost < 9999999:
            out[origin] = (best_path[1] if len(best_path) > 1 else best_path[0],
                           best_cost)
    return out


def read_dbf(path):
    with open(path, "rb") as fh:
        header = fh.read(32)
        n_records = struct.unpack("<I", header[4:8])[0]
        header_len = struct.unpack("<H", header[8:10])[0]
        record_len = struct.unpack("<H", header[10:12])[0]
        fields = []
        while True:
            raw = fh.read(32)
            if raw[0:1] == b"\r" or len(raw) < 32:
                break
            fields.append((raw[:11].rstrip(b"\x00").decode("latin1"), raw[16]))
        fh.seek(header_len)
        rows = []
        for _ in range(n_records):
            rec = fh.read(record_len)
            if len(rec) < record_len:
                break
            offset, row = 1, {}
            for name, size in fields:
                row[name] = rec[offset:offset + size].decode("latin1").strip()
                offset += size
            rows.append(row)
    return rows


def test_fixture_graph_has_the_known_answer():
    """A hand-checkable graph: 1-2-3 to safe zone 4, with a decoy branch."""
    nodes = [("1", 0), ("2", 0), ("3", 0), ("4", 1), ("5", 0)]
    edges = [("1", "2", "10"), ("2", "3", "10"), ("3", "4", "10"),
             ("2", "5", "1"), ("5", "3", "1")]
    graph, safe, origins = build_graph(nodes, edges)
    rows, unroutable = solve_next_hops(graph, safe, origins)
    result = {r["NodeID"]: (r["NextNodeID"], r["TotalCost"]) for r in rows}

    # 2 -> 5 -> 3 -> 4 costs 12; 2 -> 3 -> 4 costs 20. The detour wins.
    assert result[2] == (5, 12)
    assert result[5] == (3, 11)
    assert result[3] == (4, 10)
    assert result[1] == (2, 22)
    assert unroutable == []


def test_isolated_nodes_are_reported_not_dropped():
    """Unroutable nodes must be returned, never silently omitted."""
    nodes = [("1", 0), ("2", 1), ("9", 0)]
    edges = [("1", "2", "5")]
    graph, safe, origins = build_graph(nodes, edges)
    rows, unroutable = solve_next_hops(graph, safe, origins)
    assert [r["NodeID"] for r in rows] == [1]
    assert unroutable == [9]


def test_no_safe_zone_means_nothing_is_routable():
    nodes = [("1", 0), ("2", 0)]
    edges = [("1", "2", "5")]
    graph, safe, origins = build_graph(nodes, edges)
    rows, unroutable = solve_next_hops(graph, safe, origins)
    assert rows == []
    assert unroutable == [1, 2]


def test_parallel_edges_keep_the_cheapest():
    nodes = [("1", 0), ("2", 1)]
    edges = [("1", "2", "50"), ("1", "2", "5")]
    graph, safe, origins = build_graph(nodes, edges)
    rows, _ = solve_next_hops(graph, safe, origins)
    assert rows[0]["TotalCost"] == 5


@pytest.mark.slow
def test_matches_v08_on_the_real_network():
    """Full shipped network: identical costs to 1e-6 and identical next hops."""
    points = read_dbf(ZONE_DIR / "puntos_Chimbote_zona1.dbf")
    roads = read_dbf(ZONE_DIR / "rutas_Chimbote_zona1.dbf")
    nodes = [(r["fid"], r["is_shelter"] or 0) for r in points]
    edges = [(r["start_node"], r["end_node"], r["cost"]) for r in roads
             if r["start_node"] and r["end_node"] and r["cost"]]

    started = time.perf_counter()
    old = v08_nested_loop(nodes, edges)
    old_seconds = time.perf_counter() - started

    graph, safe, origins = build_graph(nodes, edges)
    started = time.perf_counter()
    rows, unroutable = solve_next_hops(graph, safe, origins)
    new_seconds = time.perf_counter() - started
    new = {r["NodeID"]: (r["NextNodeID"], r["TotalCost"]) for r in rows}

    assert set(old) == set(new), "different sets of routable nodes"
    worst = max(abs(old[k][1] - new[k][1]) for k in old)
    assert worst < 1e-6, f"cost disagreement {worst}"
    differing = [k for k in old if old[k][0] != new[k][0]]
    assert not differing, f"{len(differing)} nodes chose a different next hop"
    assert len(unroutable) == 884, "unroutable count changed for the shipped data"
    assert new_seconds < old_seconds, "the fast path is not faster"
    print(f"\n  per-pair {old_seconds:.2f}s -> multi-source {new_seconds:.4f}s "
          f"({old_seconds/new_seconds:,.0f}x), {len(new)} routes")
