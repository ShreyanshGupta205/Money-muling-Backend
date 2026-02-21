# 💰 Financial Forensics Engine

> **Money Muling Network Detection** using Graph Theory & Temporal Analysis

A production-ready forensic analysis tool that detects money muling networks in
financial transaction data. Upload a CSV of transactions and instantly receive
graph-based pattern analysis with interactive visualization.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  Next.js  ·  TailwindCSS  ·  Cytoscape.js                   │
│                                                              │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────┐      │
│  │ CSV      │  │ Interactive  │  │ Fraud Ring Table +  │      │
│  │ Upload   │──│ Graph Viz    │  │ Suspicious Accounts │      │
│  │ (D&D)    │  │ (Cytoscape)  │  │ + JSON Download     │      │
│  └──────────┘  └──────────────┘  └────────────────────┘      │
└──────────────────┬───────────────────────────────────────────┘
                   │  POST /api/analyze  (multipart CSV)
┌──────────────────▼───────────────────────────────────────────┐
│                        BACKEND                               │
│  FastAPI  ·  NetworkX  ·  Pandas  ·  NumPy                   │
│                                                              │
│  ┌────────────┐  ┌──────────────────────────────────────┐    │
│  │ CSV Parser │──│         Graph Engine                  │    │
│  │ + Builder  │  │                                      │    │
│  └────────────┘  │  ┌────────────┐  ┌───────────────┐   │    │
│                  │  │ Cycle Det. │  │ Smurfing Det. │   │    │
│                  │  │ (Johnson)  │  │ (Sliding Win) │   │    │
│                  │  └────────────┘  └───────────────┘   │    │
│                  │  ┌────────────┐  ┌───────────────┐   │    │
│                  │  │ Shell Chain│  │ False Positive│   │    │
│                  │  │ (BFS)      │  │ Control       │   │    │
│                  │  └────────────┘  └───────────────┘   │    │
│                  └──────────────────────────────────────┘    │
│                           │                                  │
│                  ┌────────▼───────┐                           │
│                  │ Suspicion      │                           │
│                  │ Score (0–100)  │                           │
│                  └────────────────┘                           │
└──────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
Money/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entry point
│   │   ├── graph_engine/
│   │   │   ├── builder.py              # CSV → NetworkX DiGraph
│   │   │   ├── cycle_detection.py      # Johnson's algorithm (cycles 3–5)
│   │   │   ├── smurfing_detection.py   # Fan-in / fan-out sliding window
│   │   │   ├── shell_chain_detection.py # BFS layered path detection
│   │   │   └── false_positive.py       # Salary / merchant / payroll filters
│   │   ├── scoring/
│   │   │   └── suspicion_score.py      # Weighted composite scoring
│   │   └── models/
│   │       └── schemas.py              # Pydantic response models
│   ├── generate_test_data.py           # Synthetic test data generator
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx              # Root layout + metadata
│   │   │   ├── page.tsx                # Main app: upload + dashboard
│   │   │   └── globals.css             # Design system + animations
│   │   └── components/
│   │       ├── GraphVisualization.tsx   # Cytoscape.js interactive graph
│   │       ├── FraudRingTable.tsx       # Detected rings table
│   │       └── SummaryCards.tsx         # Summary statistics cards
│   └── package.json
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**

### 1. Backend

```bash
cd backend
# On Windows:
pip install -r requirements.txt
python generate_test_data.py

# On Mac/Linux, you may need to use pip3 and python3:
# pip3 install -r requirements.txt
# python3 generate_test_data.py

# Start server (binding to 0.0.0.0 to allow mobile/cross-device access)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit **http://localhost:3000** and upload a CSV.

---

## 🔍 Detection Algorithms

### 1. Cycle Detection (40% weight)
- **Algorithm**: Johnson's Algorithm via `networkx.simple_cycles()`
- **Complexity**: O(V + E) × (number of cycles) — bounded by `length_bound=5`
- **Criteria**: Simple directed cycles of length 3–5
- **Scoring**: Based on cycle length, total circulated amount, and time compactness

### 2. Smurfing Detection (30% weight)
- **Algorithm**: Two-pointer sliding window over 72-hour intervals
- **Complexity**: O(V × E_max) where E_max is max edges per node
- **Fan-In**: ≥10 unique senders → 1 receiver within 72 hours
- **Fan-Out**: 1 sender → ≥10 unique receivers within 72 hours
- **Scoring**: Based on counterparty count and amount similarity (CV)

### 3. Shell Chain Detection (20% weight)
- **Algorithm**: Bounded BFS with path tracking
- **Complexity**: O(V × B^D) where B = branching factor, D = max depth (6)
- **Criteria**: Paths ≥ 3 hops with intermediate nodes having total degree ≤ 3
- **Scoring**: Based on time compactness, total amount, and path length

### 4. Velocity Abnormality (10% weight)
- **Metric**: Mean inter-transaction interval per account
- **Scoring**: < 1 min = 1.0, < 1 hour = 0.7, < 1 day = 0.3, else 0.0

---

## 🛡️ False Positive Control

| Pattern | Heuristic | Threshold |
|---------|-----------|-----------|
| Salary | CV of received amounts ≤ 0.05 + monthly intervals | ≥ 3 payments, 70% monthly |
| Merchant | High in-degree + low amount entropy | in_degree ≥ 50, entropy < 2.5 |
| Payroll Hub | Fixed amounts to many recipients | out_degree ≥ 20, CV < 0.15 |

Flagged false-positive accounts are **completely excluded** from suspicious results.

---

## 📊 Suspicion Score Formula

```
final_score = (cycle × 40) + (smurfing × 30) + (shell × 20) + (velocity × 10)
```

Each component is normalized to [0, 1] before weighting. Final score is capped at 100.
Accounts below a threshold of 10 are excluded from the report.

---

## ⚡ Performance

| Metric | Target | Implementation |
|--------|--------|---------------|
| 10K transactions | < 10 seconds | itertuples, bounded searches |
| Cycle detection | O(V+E) bounded | length_bound=5, cap 500 cycles |
| Smurfing | O(V×E) | Two-pointer window |
| Shell chains | O(V×B^D) | Max depth 6, cap 200 chains |
| Graph rendering | < 300 nodes | Auto-filters to suspicious subgraph |

---

## 🌐 Deployment

### Backend → Render

1. Add a `Procfile` or set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
2. Set Python 3.10+ runtime
3. Install from `requirements.txt`

### Frontend → Vercel

1. Set root directory to `frontend/`
2. Set env var `NEXT_PUBLIC_API_URL` to your Render backend URL
3. Deploy — Vercel auto-detects Next.js

---

## ⚠️ Known Limitations

1. **Simple cycles only** — does not detect complex multi-hop laundering topologies
2. **Static thresholds** — fan-in/fan-out min count (10) is hardcoded
3. **No persistence** — results are ephemeral; no database storage
4. **Single-file upload** — no batch/streaming ingestion
5. **No authentication** — open API, needs auth layer for production

---

## 🔮 Future Improvements

- **Machine Learning**: Train anomaly detection models on labeled fraud data
- **Temporal GNN**: Graph Neural Networks with temporal attention
- **Real-time streaming**: Kafka/Redis-based live transaction monitoring
- **Case management**: Flag → investigate → resolve workflow
- **Multi-currency support**: Normalize amounts across currencies
- **Database persistence**: PostgreSQL + Redis caching
- **Role-based access**: JWT auth with investigator/admin roles

---

## 📜 License

MIT — Built for hackathon use.
