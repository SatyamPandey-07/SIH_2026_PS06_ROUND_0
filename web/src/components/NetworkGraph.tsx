import React, { useEffect, useRef } from "react";
import type { GraphData } from "../api";

interface Props {
  data: GraphData;
  proposedTitle: string;
}

export const NetworkGraph: React.FC<Props> = ({ data, proposedTitle }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !data || !data.nodes || data.nodes.length === 0) return;

    // Dynamically load Vis.js if not present
    const scriptId = "vis-network-script";
    let script = document.getElementById(scriptId) as HTMLScriptElement;

    const initNetwork = () => {
      if (!containerRef.current || !(window as any).vis) return;

      const nodes = data.nodes.map(n => {
        let color = { background: "#78909c", border: "#cfd8dc" };
        let shape = "dot";
        let size = 14;
        let font = { color: "#111111", size: 12, face: "Inter" };

        if (n.type === "proposed_title") {
          color = { background: "#111111", border: "#3b82f6" };
          shape = "box";
          size = 28;
          font = { color: "#ffffff", size: 14, face: "Inter" };
        } else if (n.type === "registered_title") {
          const score = n.score || 0.8;
          color = score > 0.85
            ? { background: "#ef4444", border: "#fca5a5" }
            : { background: "#f59e0b", border: "#fde68a" };
          shape = "ellipse";
          size = 20;
          font = { color: "#ffffff", size: 12, face: "Inter" };
        } else if (n.type === "owner") {
          color = { background: "#3b82f6", border: "#93c5fd" };
          shape = "dot";
          size = 14;
          font = { color: "#374151", size: 11, face: "Inter" };
        } else if (n.type === "state") {
          color = { background: "#10b981", border: "#6ee7b7" };
          shape = "dot";
          size = 14;
          font = { color: "#374151", size: 11, face: "Inter" };
        }

        return {
          id: n.id,
          label: n.label || n.id,
          shape,
          color,
          size,
          font,
          title: `${n.type.replace("_", " ").toUpperCase()}: ${n.label || n.id}`,
        };
      });

      const edges = data.edges.map(e => ({
        from: e.source,
        to: e.target,
        label: e.relation.replace("_", " "),
        color: { color: "#cbd5e1", highlight: "#3b82f6" },
        font: { color: "#64748b", size: 10, align: "middle" },
        arrows: e.relation !== "similar_to" ? "to" : "",
        smooth: { type: "continuous" },
      }));

      const vis = (window as any).vis;
      const networkData = {
        nodes: new vis.DataSet(nodes),
        edges: new vis.DataSet(edges),
      };

      const options = {
        nodes: { borderWidth: 2, shadow: true },
        edges: { width: 1.5, shadow: false },
        physics: {
          solver: "forceAtlas2Based",
          forceAtlas2Based: {
            gravitationalConstant: -40,
            centralGravity: 0.01,
            springLength: 90,
            springConstant: 0.08,
            damping: 0.4,
          },
          timestep: 0.5,
          stabilization: { iterations: 100 },
        },
        interaction: { hover: true, zoomView: true, dragView: true },
      };

      new vis.Network(containerRef.current, networkData, options);
    };

    if (!script) {
      script = document.createElement("script");
      script.id = scriptId;
      script.src = "https://unpkg.com/vis-network/standalone/umd/vis-network.min.js";
      script.onload = initNetwork;
      document.head.appendChild(script);
    } else if ((window as any).vis) {
      initNetwork();
    } else {
      script.addEventListener("load", initNetwork);
    }
  }, [data, proposedTitle]);

  if (!data || !data.nodes || data.nodes.length === 0) {
    return (
      <div style={{ padding: "32px", textAlign: "center", color: "var(--color-muted)" }}>
        No co-registration network graph available for this query.
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: "flex", gap: "16px", marginBottom: "12px", flexWrap: "wrap" }}>
        <span className="caption" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#111111" }} /> Proposed Title ({proposedTitle})
        </span>
        <span className="caption" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#ef4444" }} /> High Collision Match (&gt;85%)
        </span>
        <span className="caption" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#f59e0b" }} /> Moderate Similarity Match
        </span>
        <span className="caption" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#3b82f6" }} /> Publisher / Entity
        </span>
        <span className="caption" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#10b981" }} /> State Jurisdiction
        </span>
      </div>
      <div
        ref={containerRef}
        style={{
          width: "100%",
          height: "440px",
          border: "1px solid var(--color-hairline)",
          borderRadius: "var(--radius-lg)",
          background: "#fafafa",
        }}
      />
    </div>
  );
};
