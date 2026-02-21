"""
Cycle Detection Module
======================
Detects simple directed cycles of length 3–5 using Johnson's algorithm
(via NetworkX). Each cycle is grouped into a RING_ID and scored based on
cycle length, total circulated amount, and time compactness.
"""

from typing import Any, Dict, List

import networkx as nx


def detect_cycles(
    G: nx.DiGraph, min_length: int = 3, max_length: int = 5
) -> List[Dict[str, Any]]:
    """Detect directed cycles and assign ring IDs with risk scores.

    Parameters
    ----------
    G : nx.DiGraph
        Transaction graph.
    min_length : int
        Minimum cycle length (inclusive).
    max_length : int
        Maximum cycle length (inclusive).

    Returns
    -------
    list[dict]
        Each dict contains ring_id, members, cycle_length, total_amount,
        time_compactness, risk_score, and pattern_type.
    """
    cycles: List[Dict[str, Any]] = []
    ring_counter = 0
    seen_sets: set = set()  # avoid duplicate cycle sets

    try:
        # NetworkX >= 3.1 supports length_bound
        raw_cycles = nx.simple_cycles(G, length_bound=max_length)
    except TypeError:
        # Fallback for older NetworkX
        raw_cycles = nx.simple_cycles(G)

    for cycle in raw_cycles:
        clen = len(cycle)
        if clen < min_length or clen > max_length:
            continue

        # De-duplicate rotations of the same cycle
        frozen = frozenset(cycle)
        if frozen in seen_sets:
            continue
        seen_sets.add(frozen)

        # Gather edge metrics along the cycle BEFORE assigning ring ID
        # so we can filter low-quality cycles early

        total_amount = 0.0
        timestamps = []
        for i in range(clen):
            u = cycle[i]
            v = cycle[(i + 1) % clen]
            if G.has_edge(u, v):
                edge = G[u][v]
                total_amount += edge["total_amount"]
                for txn in edge["transactions"]:
                    timestamps.append(txn["timestamp"])

        # Time compactness (0–1): tighter window ⇒ higher score
        time_compactness = 0.0
        if len(timestamps) >= 2:
            sorted_ts = sorted(timestamps)
            span_seconds = (sorted_ts[-1] - sorted_ts[0]).total_seconds()
            if span_seconds <= 3600:
                time_compactness = 1.0
            elif span_seconds >= 30 * 86400:
                time_compactness = 0.0
            else:
                time_compactness = 1.0 - (span_seconds / (30 * 86400))

        # Composite risk score
        length_factor = clen / max_length
        amount_factor = min(total_amount / 100_000, 1.0)

        risk_score = (
            length_factor * 0.3
            + amount_factor * 0.4
            + time_compactness * 0.3
        ) * 100

        # Skip low-quality cycles (incidental in random data)
        if risk_score < 25:
            continue

        ring_counter += 1
        ring_id = f"RING_{ring_counter:03d}"

        cycles.append(
            {
                "ring_id": ring_id,
                "members": list(cycle),
                "cycle_length": clen,
                "total_amount": round(total_amount, 1),
                "time_compactness": round(time_compactness, 2),
                "risk_score": round(min(risk_score, 100.0), 1),
                "pattern_type": "cycle",
            }
        )

        # Safety cap – avoid combinatorial explosion on dense graphs
        if ring_counter >= 100:
            break

    return cycles
