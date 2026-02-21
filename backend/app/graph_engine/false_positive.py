"""
False Positive Control Module
=============================
Identifies accounts that should NOT be flagged as suspicious:
  • Salary receivers – fixed-amount monthly incoming transfers
  • Merchant accounts – high in-degree with stable amount distribution
  • Payroll hubs – one sender distributing similar amounts to many receivers

Uses entropy, coefficient-of-variation, and time-interval heuristics.
"""

from typing import Set

import networkx as nx
import numpy as np
import pandas as pd


def filter_false_positives(G: nx.DiGraph, df: pd.DataFrame) -> Set[str]:
    """Return the set of account IDs that are likely legitimate."""
    fp_accounts: Set[str] = set()

    for node in G.nodes:
        data = G.nodes[node]

        if _is_salary_pattern(data):
            fp_accounts.add(node)
        elif _is_merchant_pattern(G, node, data):
            fp_accounts.add(node)
        elif _is_payroll_hub(G, node, data):
            fp_accounts.add(node)

    return fp_accounts


# ---------------------------------------------------------------------------
# Heuristic detectors
# ---------------------------------------------------------------------------

def _is_salary_pattern(data: dict) -> bool:
    """Fixed-amount, roughly monthly incoming transfers."""
    amounts = data.get("received_amounts", [])
    timestamps = data.get("received_timestamps", [])

    if len(amounts) < 3:
        return False

    arr = np.array(amounts, dtype=float)
    mean_val = float(np.mean(arr))
    if mean_val == 0:
        return False

    # Low coefficient of variation ⇒ consistent amounts
    cv = float(np.std(arr) / mean_val)
    if cv > 0.05:
        return False

    # Check roughly monthly cadence (25–35 day gaps)
    sorted_ts = sorted(timestamps)
    if len(sorted_ts) < 3:
        return False

    intervals_days = [
        (sorted_ts[i + 1] - sorted_ts[i]).days
        for i in range(len(sorted_ts) - 1)
    ]
    monthly = [d for d in intervals_days if 25 <= d <= 35]
    return len(monthly) >= len(intervals_days) * 0.7


def _is_merchant_pattern(G: nx.DiGraph, node: str, data: dict) -> bool:
    """High in-degree with low entropy — many small purchases."""
    in_deg = data.get("in_degree", 0)
    if in_deg < 50:
        return False

    amounts = data.get("received_amounts", [])
    if not amounts:
        return False

    entropy = _amount_entropy(amounts)
    # Merchants have somewhat standardized pricing ⇒ low entropy
    return entropy < 2.5


def _is_payroll_hub(G: nx.DiGraph, node: str, data: dict) -> bool:
    """Distributes similar amounts to many receivers regularly."""
    out_deg = data.get("out_degree", 0)
    if out_deg < 20:
        return False

    amounts = data.get("sent_amounts", [])
    if not amounts:
        return False

    mean_val = float(np.mean(amounts))
    if mean_val == 0:
        return False

    cv = float(np.std(amounts) / mean_val)
    return cv < 0.15


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _amount_entropy(amounts: list) -> float:
    """Shannon entropy of the amount distribution (binned)."""
    if not amounts:
        return 0.0
    arr = np.array(amounts, dtype=float)
    n_bins = min(50, max(5, len(arr) // 5))
    hist, _ = np.histogram(arr, bins=n_bins)
    probs = hist / hist.sum()
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log2(probs)))
