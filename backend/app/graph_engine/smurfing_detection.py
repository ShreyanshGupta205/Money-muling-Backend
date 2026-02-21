"""
Smurfing Detection Module
=========================
Detects structuring patterns:
  • Fan-In:  10+ unique senders  → 1 receiver within a 72-hour window
  • Fan-Out: 1 sender → 10+ unique receivers within a 72-hour window

Uses a sliding-window approach with similarity scoring on transaction amounts.
"""

from datetime import timedelta
from typing import Any, Dict, List, Optional

import networkx as nx
import numpy as np
import pandas as pd

WINDOW_HOURS = 72
MIN_COUNTERPARTIES = 10


def detect_smurfing(
    G: nx.DiGraph, df: pd.DataFrame
) -> Dict[str, List[Dict[str, Any]]]:
    """Detect fan-in and fan-out smurfing patterns.

    Returns
    -------
    dict  with keys ``fan_in`` and ``fan_out``, each a list of flagged accounts.
    """
    fan_in_accounts: List[Dict[str, Any]] = []
    fan_out_accounts: List[Dict[str, Any]] = []

    for node in G.nodes:
        # ---- Fan-In: many senders → this node ----
        received_txns = _collect_predecessor_txns(G, node)
        if len(received_txns) >= MIN_COUNTERPARTIES:
            received_txns.sort(key=lambda t: t["timestamp"])
            result = _sliding_window_check(
                received_txns, "sender", WINDOW_HOURS, MIN_COUNTERPARTIES
            )
            if result is not None:
                fan_in_accounts.append(
                    {
                        "account_id": node,
                        "pattern": "fan_in",
                        "max_unique_senders": result["max_unique"],
                        "amount_similarity": result["amount_similarity"],
                    }
                )

        # ---- Fan-Out: this node → many receivers ----
        sent_txns = _collect_successor_txns(G, node)
        if len(sent_txns) >= MIN_COUNTERPARTIES:
            sent_txns.sort(key=lambda t: t["timestamp"])
            result = _sliding_window_check(
                sent_txns, "receiver", WINDOW_HOURS, MIN_COUNTERPARTIES
            )
            if result is not None:
                fan_out_accounts.append(
                    {
                        "account_id": node,
                        "pattern": "fan_out",
                        "max_unique_receivers": result["max_unique"],
                        "amount_similarity": result["amount_similarity"],
                    }
                )

    return {"fan_in": fan_in_accounts, "fan_out": fan_out_accounts}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _collect_predecessor_txns(G: nx.DiGraph, node: str) -> list:
    txns = []
    for pred in G.predecessors(node):
        for txn in G[pred][node]["transactions"]:
            txns.append(
                {
                    "sender": pred,
                    "amount": txn["amount"],
                    "timestamp": txn["timestamp"],
                }
            )
    return txns


def _collect_successor_txns(G: nx.DiGraph, node: str) -> list:
    txns = []
    for succ in G.successors(node):
        for txn in G[node][succ]["transactions"]:
            txns.append(
                {
                    "receiver": succ,
                    "amount": txn["amount"],
                    "timestamp": txn["timestamp"],
                }
            )
    return txns


def _sliding_window_check(
    txns: list,
    counterparty_key: str,
    window_hours: int,
    min_count: int,
) -> Optional[Dict[str, Any]]:
    """Two-pointer sliding window for counterparty clustering."""
    if not txns:
        return None

    window_delta = timedelta(hours=window_hours)
    best: Optional[Dict[str, Any]] = None
    best_unique = 0

    n = len(txns)
    right = 0

    for left in range(n):
        # Expand right pointer
        while right < n and txns[right]["timestamp"] - txns[left]["timestamp"] <= window_delta:
            right += 1

        window_slice = txns[left:right]
        unique_cps = {t[counterparty_key] for t in window_slice}

        if len(unique_cps) >= min_count and len(unique_cps) > best_unique:
            amounts = [t["amount"] for t in window_slice]
            mean_amt = float(np.mean(amounts))
            cv = float(np.std(amounts) / mean_amt) if mean_amt > 0 else 1.0
            similarity = round(max(0.0, 1.0 - cv), 2)

            best_unique = len(unique_cps)
            best = {
                "max_unique": len(unique_cps),
                "amount_similarity": similarity,
            }

    return best
