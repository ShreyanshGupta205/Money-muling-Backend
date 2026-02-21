"""
Graph Builder Module
====================
Parses CSV transaction data and constructs a NetworkX directed graph.
Each account becomes a node with aggregated metrics; each transaction
becomes a directed edge with metadata.
"""

import io
from typing import Any, Dict, Tuple

import networkx as nx
import pandas as pd


def parse_csv(file_content: bytes) -> pd.DataFrame:
    """Parse and validate uploaded CSV content.

    Expected columns: transaction_id, sender_id, receiver_id, amount, timestamp
    """
    df = pd.read_csv(io.BytesIO(file_content))

    required = {"transaction_id", "sender_id", "receiver_id", "amount", "timestamp"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["amount"] = df["amount"].astype(float)
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


def build_graph(df: pd.DataFrame) -> Tuple[nx.DiGraph, Dict[str, Any]]:
    """Build a directed graph from transaction data.

    Returns
    -------
    G : nx.DiGraph
        Directed graph with node/edge attributes.
    metadata : dict
        Summary statistics about the graph.
    """
    G = nx.DiGraph()

    # Pre-collect all unique accounts
    all_accounts = set(df["sender_id"].unique()) | set(df["receiver_id"].unique())
    for acc in all_accounts:
        G.add_node(
            acc,
            total_sent=0.0,
            total_received=0.0,
            transaction_count=0,
            timestamps=[],
            sent_amounts=[],
            received_amounts=[],
            sent_timestamps=[],
            received_timestamps=[],
            counterparties_sent=set(),
            counterparties_received=set(),
        )

    # Vectorised iteration (itertuples is ~10x faster than iterrows)
    for row in df.itertuples(index=False):
        sender = row.sender_id
        receiver = row.receiver_id
        amount = float(row.amount)
        ts = row.timestamp

        # --- Update sender node ---
        sd = G.nodes[sender]
        sd["total_sent"] += amount
        sd["transaction_count"] += 1
        sd["timestamps"].append(ts)
        sd["sent_amounts"].append(amount)
        sd["sent_timestamps"].append(ts)
        sd["counterparties_sent"].add(receiver)

        # --- Update receiver node ---
        rd = G.nodes[receiver]
        rd["total_received"] += amount
        rd["transaction_count"] += 1
        rd["timestamps"].append(ts)
        rd["received_amounts"].append(amount)
        rd["received_timestamps"].append(ts)
        rd["counterparties_received"].add(sender)

        # --- Update or create edge ---
        if G.has_edge(sender, receiver):
            ed = G[sender][receiver]
            ed["transactions"].append({"amount": amount, "timestamp": ts})
            ed["total_amount"] += amount
            ed["count"] += 1
        else:
            G.add_edge(
                sender,
                receiver,
                transactions=[{"amount": amount, "timestamp": ts}],
                total_amount=amount,
                count=1,
            )

    # Store degree info on nodes
    for node in G.nodes:
        G.nodes[node]["in_degree"] = G.in_degree(node)
        G.nodes[node]["out_degree"] = G.out_degree(node)

    metadata = {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "total_transactions": len(df),
    }

    return G, metadata
