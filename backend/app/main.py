"""
Financial Forensics Engine — FastAPI Application
=================================================
Main API server with a single endpoint for CSV upload and analysis.
Returns structured JSON matching the exact required output format,
plus graph visualization data for the frontend.
"""

import time
from typing import Any, Dict, List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.graph_engine.builder import build_graph, parse_csv
from app.graph_engine.cycle_detection import detect_cycles
from app.graph_engine.false_positive import filter_false_positives
from app.graph_engine.shell_chain_detection import detect_shell_chains
from app.graph_engine.smurfing_detection import detect_smurfing
from app.scoring.suspicion_score import calculate_suspicion_scores

app = FastAPI(
    title="Financial Forensics Engine",
    description="Money Muling Network Detection via Graph Theory & Temporal Analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "engine": "Financial Forensics Engine v1.0"}


@app.post("/api/analyze")
async def analyze_transactions(file: UploadFile = File(...)):
    """Upload a CSV file and receive a full forensic analysis."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    start_time = time.time()

    try:
        content = await file.read()
        df = parse_csv(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parsing error: {e}")

    # Build the directed transaction graph
    G, metadata = build_graph(df)

    # Run all detection modules
    cycles = detect_cycles(G)
    smurfing = detect_smurfing(G, df)
    shell_chains = detect_shell_chains(G)
    fp_accounts = filter_false_positives(G, df)

    # Compute final suspicion scores and format output
    results = calculate_suspicion_scores(
        G, cycles, smurfing, shell_chains, fp_accounts, metadata
    )

    processing_time = round(time.time() - start_time, 1)
    results["summary"]["processing_time_seconds"] = processing_time

    # Attach graph data for Cytoscape.js visualization
    results["graph_data"] = _build_visualization_data(G, results)

    return results


def _build_visualization_data(
    G, results: Dict[str, Any]
) -> Dict[str, List[Dict[str, Any]]]:
    """Serialize graph into Cytoscape.js-compatible elements."""
    suspicious_ids = {a["account_id"] for a in results["suspicious_accounts"]}
    score_map = {
        a["account_id"]: a["suspicion_score"] for a in results["suspicious_accounts"]
    }

    nodes = []
    for node in G.nodes:
        nd = G.nodes[node]
        nodes.append(
            {
                "data": {
                    "id": node,
                    "total_sent": round(nd["total_sent"], 1),
                    "total_received": round(nd["total_received"], 1),
                    "suspicion_score": score_map.get(node, 0.0),
                    "is_suspicious": node in suspicious_ids,
                }
            }
        )

    edges = []
    for u, v, ed in G.edges(data=True):
        edges.append(
            {
                "data": {
                    "source": u,
                    "target": v,
                    "amount": round(ed["total_amount"], 1),
                    "count": ed["count"],
                }
            }
        )

    return {"nodes": nodes, "edges": edges}
