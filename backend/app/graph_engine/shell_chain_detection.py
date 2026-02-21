"""
Shell Chain Detection Module
============================
Detects layered shell chains — directed paths of length ≥ 3 where
intermediate nodes have total degree ≤ 3, indicating pass-through
"shell" accounts used to obscure the money trail.

Uses bounded BFS path exploration for efficiency.
"""

from collections import deque
from typing import Any, Dict, List

import networkx as nx


MAX_PATH_LENGTH = 6  # max hops
MAX_CHAINS = 200     # safety cap


def detect_shell_chains(G: nx.DiGraph) -> List[Dict[str, Any]]:
    """Detect layered shell chains via BFS path exploration.

    Returns
    -------
    list[dict]
        Each dict contains chain_id, path, path_length, total_amount,
        risk_score, and time_score.
    """
    chains: List[Dict[str, Any]] = []
    chain_counter = 0
    visited_paths: set = set()

    # Start from nodes that have outgoing but few incoming edges (potential sources)
    source_candidates = [
        n
        for n in G.nodes
        if G.out_degree(n) >= 1 and G.in_degree(n) <= 2
    ]

    for source in source_candidates:
        if chain_counter >= MAX_CHAINS:
            break

        # BFS with path tracking
        queue: deque = deque()
        queue.append((source, [source], []))

        while queue and chain_counter < MAX_CHAINS:
            current, path, edge_timestamps = queue.popleft()

            if len(path) > MAX_PATH_LENGTH:
                continue

            for successor in G.successors(current):
                if successor in path:
                    continue  # no revisits

                edge_data = G[current][successor]
                new_path = path + [successor]
                new_ts = edge_timestamps + [
                    t["timestamp"] for t in edge_data["transactions"]
                ]

                # Check shell-chain criteria once path has ≥ 4 nodes (3 hops)
                if len(new_path) >= 4:
                    intermediates = new_path[1:-1]
                    all_low_degree = all(
                        G.degree(n) <= 3 for n in intermediates
                    )

                    if all_low_degree:
                        path_key = tuple(new_path)
                        if path_key not in visited_paths:
                            visited_paths.add(path_key)
                            chain_counter += 1

                            # Time score — rapid succession ⇒ higher suspicion
                            time_score = _compute_time_score(new_ts)

                            total_amount = sum(
                                G[new_path[i]][new_path[i + 1]]["total_amount"]
                                for i in range(len(new_path) - 1)
                            )

                            amount_score = min(total_amount / 50_000, 1.0)
                            length_score = min((len(new_path) - 3) / 3, 1.0)

                            risk_score = (
                                time_score * 0.4
                                + amount_score * 0.3
                                + length_score * 0.3
                            ) * 100

                            chains.append(
                                {
                                    "chain_id": f"CHAIN_{chain_counter:03d}",
                                    "path": list(new_path),
                                    "path_length": len(new_path) - 1,
                                    "total_amount": round(total_amount, 1),
                                    "risk_score": round(min(risk_score, 100.0), 1),
                                    "time_score": round(time_score, 2),
                                }
                            )

                # Continue BFS if path can still grow
                if len(new_path) <= MAX_PATH_LENGTH:
                    queue.append((successor, new_path, new_ts))

    return chains


def _compute_time_score(timestamps: list) -> float:
    """Score 0–1 based on how rapidly transactions occur."""
    if len(timestamps) < 2:
        return 0.0
    sorted_ts = sorted(timestamps)
    span = (sorted_ts[-1] - sorted_ts[0]).total_seconds()
    if span < 3600:
        return 1.0
    if span < 86400:
        return 0.7
    if span < 7 * 86400:
        return 0.3
    return 0.0
