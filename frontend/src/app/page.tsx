"use client";

import React, { useState, useCallback, useRef } from "react";

// ─── Types ──────────────────────────────────────────────────────────
interface SuspiciousAccount {
  account_id: string;
  suspicion_score: number;
  detected_patterns: string[];
  ring_id: string | null;
}
interface FraudRing {
  ring_id: string;
  member_accounts: string[];
  pattern_type: string;
  risk_score: number;
}
interface Summary {
  total_accounts_analyzed: number;
  suspicious_accounts_flagged: number;
  fraud_rings_detected: number;
  processing_time_seconds: number;
}
interface GraphNode {
  data: {
    id: string;
    total_sent: number;
    total_received: number;
    suspicion_score: number;
    is_suspicious: boolean;
  };
}
interface GraphEdge {
  data: { source: string; target: string; amount: number; count: number };
}
interface AnalysisResult {
  suspicious_accounts: SuspiciousAccount[];
  fraud_rings: FraudRing[];
  summary: Summary;
  graph_data: { nodes: GraphNode[]; edges: GraphEdge[] };
}

// Lazy-loaded heavy components
import dynamic from "next/dynamic";
const GraphVisualization = dynamic(
  () => import("@/components/GraphVisualization"),
  { ssr: false, loading: () => <GraphPlaceholder /> }
);
import FraudRingTable from "@/components/FraudRingTable";
import SummaryCards from "@/components/SummaryCards";

function GraphPlaceholder() {
  return (
    <div className="glass-card p-8 flex items-center justify-center h-[500px]">
      <div className="animate-spin-slow w-10 h-10 border-2 border-accent-cyan border-t-transparent rounded-full" />
    </div>
  );
}

const API_URL = process.env.NEXT_PUBLIC_API_URL
  || (typeof window !== 'undefined' ? `http://${window.location.hostname}:8000` : "http://localhost:8000");

// ─── Main Page ──────────────────────────────────────────────────────
export default function HomePage() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.endsWith(".csv")) {
      setError("Please upload a .csv file.");
      return;
    }
    setFileName(file.name);
    setError(null);
    setLoading(true);
    setResult(null);

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Server error ${res.status}`);
      }
      const data: AnalysisResult = await res.json();
      setResult(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setError(`${msg} (Attempted to connect to: ${API_URL})`);
    } finally {
      setLoading(false);
    }
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const downloadJSON = () => {
    if (!result) return;
    const { graph_data: _, ...clean } = result;
    const blob = new Blob([JSON.stringify(clean, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "forensics_report.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <main className="min-h-screen px-4 py-8 md:px-8 lg:px-16 max-w-[1600px] mx-auto">
      {/* ── Header ────────────────────────────────────────────── */}
      <header className="text-center mb-14 animate-fade-in-up">
        <div className="flex items-center justify-center gap-4 mb-4">
          <svg width="48" height="48" viewBox="0 0 40 40" fill="none" className="filter drop-shadow-[0_0_10px_rgba(6,182,212,0.6)]">
            <circle cx="20" cy="20" r="18" stroke="#06b6d4" strokeWidth="2.5" opacity="0.8" />
            <circle cx="12" cy="16" r="3" fill="#06b6d4" className="animate-pulse" />
            <circle cx="28" cy="16" r="3" fill="#f43f5e" className="animate-pulse" style={{ animationDelay: "1s" }} />
            <circle cx="20" cy="28" r="3" fill="#06b6d4" className="animate-pulse" style={{ animationDelay: "0.5s" }} />
            <line x1="14" y1="17" x2="26" y2="17" stroke="#475569" strokeWidth="1.5" />
            <line x1="13" y1="18" x2="19" y2="26" stroke="#475569" strokeWidth="1.5" />
            <line x1="27" y1="18" x2="21" y2="26" stroke="#475569" strokeWidth="1.5" />
          </svg>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight">
            <span className="bg-gradient-to-r from-accent-cyan via-accent-violet to-accent-rose bg-clip-text text-transparent drop-shadow-[0_0_20px_rgba(6,182,212,0.3)]">
              Financial Forensics Engine
            </span>
          </h1>
        </div>
        <p className="text-text-secondary text-base md:text-lg max-w-2xl mx-auto tracking-wide">
          Detect money muling networks using graph theory and temporal analysis.
          Upload a transaction CSV to begin.
        </p>
      </header>

      {/* ── Upload Zone ───────────────────────────────────────── */}
      {!result && (
        <section
          className={`dropzone glass-card glow-cyan max-w-2xl mx-auto p-12 text-center cursor-pointer transition-all ${dragOver ? "drag-over" : ""
            } ${loading ? "pointer-events-none opacity-60" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => fileRef.current?.click()}
          role="button"
          tabIndex={0}
          aria-label="Upload CSV file"
        >
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
          />

          {loading ? (
            <div className="flex flex-col items-center gap-4">
              <div className="relative w-16 h-16">
                <div className="absolute inset-0 border-4 border-accent-cyan/20 rounded-full" />
                <div className="absolute inset-0 border-4 border-accent-cyan border-t-transparent rounded-full animate-spin" />
                <svg className="absolute inset-0 m-auto w-6 h-6 text-accent-cyan" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.1-1.3 2-3 2s-3-.9-3-2 1.3-2 3-2 3 .9 3 2zm12-3c0 1.1-1.3 2-3 2s-3-.9-3-2 1.3-2 3-2 3 .9 3 2z" />
                </svg>
              </div>
              <p className="text-accent-cyan font-medium">
                Analyzing {fileName}...
              </p>
              <p className="text-text-secondary text-sm">
                Running graph algorithms and pattern detection
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-5">
              <div className="w-20 h-20 rounded-3xl bg-accent-cyan/15 flex items-center justify-center animate-pulse-glow shadow-inner border border-accent-cyan/20">
                <svg
                  className="w-10 h-10 text-accent-cyan"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
              </div>
              <div>
                <p className="text-xl font-bold text-text-primary tracking-wide">
                  Drop your CSV here
                </p>
                <p className="text-text-secondary text-sm mt-2">
                  or click to browse —{" "}
                  <span className="text-accent-cyan font-mono text-xs px-2 py-0.5 rounded bg-accent-cyan/10">
                    transaction_id, sender_id, receiver_id, amount, timestamp
                  </span>
                </p>
              </div>
            </div>
          )}
        </section>
      )}

      {error && (
        <div className="max-w-2xl mx-auto mt-6 glass-card glow-rose p-4 text-accent-rose text-sm text-center">
          ⚠ {error}
        </div>
      )}

      {/* ── Results Dashboard ─────────────────────────────────── */}
      {result && (
        <div className="animate-fade-in-up space-y-8">
          {/* Action bar */}
          <div className="flex flex-wrap items-center justify-between gap-4">
            <button
              onClick={() => {
                setResult(null);
                setFileName(null);
              }}
              className="px-6 py-2.5 rounded-xl bg-white/5 border border-border-glass text-text-primary hover:bg-white/10 hover:shadow-[0_0_15px_rgba(255,255,255,0.1)] transition-all text-sm font-semibold tracking-wide"
            >
              ← New Analysis
            </button>
            <div className="flex items-center gap-4">
              <span className="px-3 py-1.5 rounded-lg bg-black/30 border border-white/5 text-text-secondary text-sm font-mono flex items-center gap-2">
                <svg className="w-4 h-4 text-accent-cyan" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {result.summary.processing_time_seconds}s
              </span>
              <button
                onClick={downloadJSON}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-accent-cyan to-accent-violet text-white font-semibold text-sm hover:opacity-90 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)] transition-all flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download JSON
              </button>
            </div>
          </div>

          {/* Summary cards */}
          <SummaryCards summary={result.summary} />

          {/* Graph visualization */}
          <div className="glass-card glow-cyan p-1">
            <div className="flex items-center justify-between px-5 pt-4 pb-2">
              <h2 className="text-lg font-semibold text-accent-cyan">
                Transaction Graph
              </h2>
              <span className="text-xs text-text-secondary">
                {result.graph_data.nodes.length} nodes ·{" "}
                {result.graph_data.edges.length} edges
              </span>
            </div>
            <GraphVisualization
              nodes={result.graph_data.nodes}
              edges={result.graph_data.edges}
            />
          </div>

          {/* Fraud ring table */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-accent-rose mb-4">
              Detected Fraud Rings
            </h2>
            <FraudRingTable rings={result.fraud_rings} />
          </div>

          {/* Suspicious accounts table */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-accent-amber mb-4">
              Suspicious Accounts
            </h2>
            {result.suspicious_accounts.length === 0 ? (
              <p className="text-text-secondary text-sm">
                No suspicious accounts detected.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full forensic-table">
                  <thead>
                    <tr>
                      <th>Account ID</th>
                      <th>Suspicion Score</th>
                      <th>Detected Patterns</th>
                      <th>Ring ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.suspicious_accounts.map((acc) => (
                      <tr key={acc.account_id}>
                        <td className="font-mono text-text-primary">
                          {acc.account_id}
                        </td>
                        <td>
                          <span
                            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${acc.suspicion_score >= 70
                              ? "bg-accent-rose/15 text-accent-rose"
                              : acc.suspicion_score >= 40
                                ? "bg-accent-amber/15 text-accent-amber"
                                : "bg-accent-cyan/15 text-accent-cyan"
                              }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${acc.suspicion_score >= 70
                                ? "bg-accent-rose"
                                : acc.suspicion_score >= 40
                                  ? "bg-accent-amber"
                                  : "bg-accent-cyan"
                                }`}
                            />
                            {acc.suspicion_score}
                          </span>
                        </td>
                        <td className="text-text-secondary text-xs">
                          {acc.detected_patterns.join(", ")}
                        </td>
                        <td className="font-mono text-accent-violet text-xs">
                          {acc.ring_id || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
