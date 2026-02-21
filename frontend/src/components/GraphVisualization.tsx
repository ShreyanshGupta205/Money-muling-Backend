"use client";

import React, { useEffect, useRef } from "react";
import cytoscape from "cytoscape";

interface NodeData {
    data: {
        id: string;
        total_sent: number;
        total_received: number;
        suspicion_score: number;
        is_suspicious: boolean;
    };
}
interface EdgeData {
    data: { source: string; target: string; amount: number; count: number };
}

interface Props {
    nodes: NodeData[];
    edges: EdgeData[];
}

export default function GraphVisualization({ nodes, edges }: Props) {
    const containerRef = useRef<HTMLDivElement>(null);
    const cyRef = useRef<cytoscape.Core | null>(null);

    useEffect(() => {
        if (!containerRef.current) return;

        // Limit nodes for performance when dataset is large
        const MAX_NODES = 300;
        let displayNodes = nodes;
        let displayEdges = edges;

        if (nodes.length > MAX_NODES) {
            // Prioritize suspicious nodes + their neighbors
            const suspiciousIds = new Set(
                nodes
                    .filter((n) => n.data.is_suspicious)
                    .map((n) => n.data.id)
            );
            const neighborIds = new Set<string>();
            edges.forEach((e) => {
                if (suspiciousIds.has(e.data.source))
                    neighborIds.add(e.data.target);
                if (suspiciousIds.has(e.data.target))
                    neighborIds.add(e.data.source);
            });
            const keepIds = new Set([...suspiciousIds, ...neighborIds]);

            // Fill remaining slots with random nodes
            const remaining = nodes
                .filter((n) => !keepIds.has(n.data.id))
                .slice(0, MAX_NODES - keepIds.size);
            remaining.forEach((n) => keepIds.add(n.data.id));

            displayNodes = nodes.filter((n) => keepIds.has(n.data.id));
            displayEdges = edges.filter(
                (e) => keepIds.has(e.data.source) && keepIds.has(e.data.target)
            );
        }

        const cy = cytoscape({
            container: containerRef.current,
            elements: [
                ...displayNodes.map((n) => ({ group: "nodes" as const, data: n.data })),
                ...displayEdges.map((e) => ({ group: "edges" as const, data: e.data })),
            ],
            style: [
                {
                    selector: "node",
                    style: {
                        label: "data(id)",
                        "background-color": "#0ea5e9",
                        color: "#94a3b8",
                        "font-size": "9px",
                        "text-valign": "bottom",
                        "text-margin-y": 8,
                        width: 24,
                        height: 24,
                        "border-width": 2,
                        "border-color": "#0f172a",
                        "text-outline-width": 2.5,
                        "text-outline-color": "#020617",
                    },
                },
                {
                    selector: "node[?is_suspicious]",
                    style: {
                        "background-color": "#f43f5e",
                        "border-color": "#4c0519",
                        "border-width": 3,
                        width: 36,
                        height: 36,
                        color: "#fda4af",
                        "font-size": "11px",
                        "font-weight": "bold",
                    },
                },
                {
                    selector: "edge",
                    style: {
                        width: 1.5,
                        "line-color": "#334155",
                        "target-arrow-color": "#334155",
                        "target-arrow-shape": "triangle",
                        "curve-style": "bezier",
                        opacity: 0.5,
                        "arrow-scale": 0.85,
                    },
                },
                {
                    selector: "edge:active, edge:selected",
                    style: {
                        "line-color": "#06b6d4",
                        "target-arrow-color": "#06b6d4",
                        opacity: 1,
                        width: 2.5,
                    },
                },
                {
                    selector: "node:active, node:selected",
                    style: {
                        "border-color": "#22d3ee",
                        "border-width": 4,
                        "overlay-color": "#06b6d4",
                        "overlay-opacity": 0.15,
                    },
                },
            ],
            layout: {
                name: "cose",
                animate: false,
                nodeDimensionsIncludeLabels: true,
                idealEdgeLength: () => 120,
                nodeOverlap: 30,
                padding: 40,
                randomize: true,
                componentSpacing: 80,
            },
            minZoom: 0.15,
            maxZoom: 4,
            wheelSensitivity: 0.3,
        });

        // Tooltip on hover
        const tooltip = document.createElement("div");
        tooltip.className =
            "fixed pointer-events-none z-50 px-3 py-2 rounded-lg text-xs font-mono hidden";
        tooltip.style.background = "rgba(15, 23, 42, 0.95)";
        tooltip.style.border = "1px solid rgba(6, 182, 212, 0.3)";
        tooltip.style.color = "#e2e8f0";
        tooltip.style.backdropFilter = "blur(8px)";
        tooltip.style.maxWidth = "240px";
        document.body.appendChild(tooltip);

        cy.on("mouseover", "node", (e) => {
            const d = e.target.data();
            tooltip.innerHTML = `
        <div style="margin-bottom:4px;font-weight:600;color:#06b6d4">${d.id}</div>
        <div>Sent: <span style="color:#f59e0b">$${Number(d.total_sent).toLocaleString()}</span></div>
        <div>Received: <span style="color:#10b981">$${Number(d.total_received).toLocaleString()}</span></div>
        <div>Suspicion: <span style="color:${d.suspicion_score >= 70 ? "#f43f5e" : d.suspicion_score >= 40 ? "#f59e0b" : "#06b6d4"}">${d.suspicion_score}</span></div>
      `;
            tooltip.classList.remove("hidden");
        });

        cy.on("mousemove", "node", (e) => {
            const { x, y } = e.originalEvent as unknown as { x: number; y: number };
            tooltip.style.left = `${x + 14}px`;
            tooltip.style.top = `${y + 14}px`;
        });

        cy.on("mouseout", "node", () => {
            tooltip.classList.add("hidden");
        });

        cyRef.current = cy;

        return () => {
            cy.destroy();
            tooltip.remove();
        };
    }, [nodes, edges]);

    return (
        <div
            ref={containerRef}
            className="w-full rounded-b-2xl"
            style={{ height: "520px", background: "rgba(5, 8, 18, 0.6)" }}
        />
    );
}
