"""
Suspicion Scoring Module
========================
Weighted composite score (0–100) per account:

  Cycle Participation   : 40 %
  Smurfing Pattern      : 30 %
  Shell Layering        : 20 %
  Velocity Abnormality  : 10 %

Accounts identified as false positives are excluded entirely.
"""

from typing import Any, Dict, List, Set

import networkx as nx
import numpy as np

# Minimum score to include in results
SCORE_THRESHOLD = 20.0


def calculate_suspicion_scores(
    G: nx.DiGraph,
    cycles: List[Dict[str, Any]],
    smurfing: Dict[str, List[Dict[str, Any]]],
    shell_chains: List[Dict[str, Any]],
    fp_accounts: Set[str],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute and format the final analysis JSON.

    Returns a dict matching the exact required output schema.
    """
    account_scores: Dict[str, Dict[str, Any]] = {}

    for account in G.nodes:
        # Skip false-positive accounts entirely
        if account in fp_accounts:
            continue

        scores = {"cycle": 0.0, "smurfing": 0.0, "shell": 0.0, "velocity": 0.0}
        patterns: List[str] = []
        ring_id = None

        # --- Cycle participation ---
        for cyc in cycles:
            if account in cyc["members"]:
                norm = cyc["risk_score"] / 100.0
                if norm > scores["cycle"]:
                    scores["cycle"] = norm
                    ring_id = cyc["ring_id"]
                patterns.append(f"cycle_length_{cyc['cycle_length']}")

        # --- Smurfing (fan-in) ---
        for fi in smurfing.get("fan_in", []):
            if fi["account_id"] == account:
                fan_score = min(fi["max_unique_senders"] / 20.0, 1.0) * (
                    0.5 + 0.5 * fi["amount_similarity"]
                )
                scores["smurfing"] = max(scores["smurfing"], fan_score)
                patterns.append("fan_in_smurfing")

        # --- Smurfing (fan-out) ---
        for fo in smurfing.get("fan_out", []):
            if fo["account_id"] == account:
                fan_score = min(fo["max_unique_receivers"] / 20.0, 1.0)
                scores["smurfing"] = max(scores["smurfing"], fan_score)
                patterns.append("fan_out_smurfing")

        # --- Shell layering ---
        for chain in shell_chains:
            if account in chain["path"]:
                norm = chain["risk_score"] / 100.0
                scores["shell"] = max(scores["shell"], norm)
                patterns.append("shell_layering")

        # --- Velocity abnormality ---
        vel = _calculate_velocity(G, account)
        scores["velocity"] = vel
        if vel > 0.7:
            patterns.append("high_velocity")

        # Weighted final score
        final = (
            scores["cycle"] * 40
            + scores["smurfing"] * 30
            + scores["shell"] * 20
            + scores["velocity"] * 10
        )
        final = round(min(final, 100.0), 1)

        if final >= SCORE_THRESHOLD and patterns:
            account_scores[account] = {
                "score": final,
                "patterns": list(dict.fromkeys(patterns)),  # dedupe, preserve order
                "ring_id": ring_id,
            }

    # --- Build output ---
    suspicious = sorted(
        [
            {
                "account_id": acc,
                "suspicion_score": data["score"],
                "detected_patterns": data["patterns"],
                "ring_id": data["ring_id"],
            }
            for acc, data in account_scores.items()
        ],
        key=lambda x: x["suspicion_score"],
        reverse=True,
    )

    fraud_rings = [
        {
            "ring_id": c["ring_id"],
            "member_accounts": c["members"],
            "pattern_type": c["pattern_type"],
            "risk_score": c["risk_score"],
        }
        for c in cycles
    ]

    return {
        "suspicious_accounts": suspicious,
        "fraud_rings": fraud_rings,
        "summary": {
            "total_accounts_analyzed": metadata["total_nodes"],
            "suspicious_accounts_flagged": len(suspicious),
            "fraud_rings_detected": len(fraud_rings),
            "processing_time_seconds": 0.0,  # set by caller
        },
    }


def _calculate_velocity(G: nx.DiGraph, account: str) -> float:
    """Transaction velocity score (0–1).  Rapid bursts ⇒ 1.0."""
    timestamps = G.nodes[account].get("timestamps", [])
    if len(timestamps) < 3:
        return 0.0

    sorted_ts = sorted(timestamps)
    intervals = np.array(
        [(sorted_ts[i + 1] - sorted_ts[i]).total_seconds() for i in range(len(sorted_ts) - 1)]
    )
    mean_interval = float(np.mean(intervals))

    if mean_interval < 60:
        return 1.0
    if mean_interval < 3600:
        return 0.7
    if mean_interval < 86400:
        return 0.3
    return 0.0
