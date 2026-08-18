import React from "react";

interface DataItem {
  name: string;
  count: number;
}

interface Props {
  data: DataItem[];
}

const PALETTE = [
  "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6",
  "#ec4899", "#6366f1", "#14b8a6", "#f97316"
];

export const SimplePieChart: React.FC<Props> = ({ data }) => {
  if (!data || data.length === 0) return null;
  const total = data.reduce((acc, d) => acc + d.count, 0);

  let cumulativeAngle = 0;

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "24px", margin: "16px 0", flexWrap: "wrap" }}>
      <svg width="140" height="140" viewBox="-1 -1 2 2" style={{ transform: "rotate(-90deg)" }}>
        {data.map((item, i) => {
          const sliceAngle = (item.count / total) * 2 * Math.PI;
          const x1 = Math.cos(cumulativeAngle);
          const y1 = Math.sin(cumulativeAngle);
          cumulativeAngle += sliceAngle;
          const x2 = Math.cos(cumulativeAngle);
          const y2 = Math.sin(cumulativeAngle);
          const largeArc = sliceAngle > Math.PI ? 1 : 0;
          const pathData = `M 0 0 L ${x1} ${y1} A 1 1 0 ${largeArc} 1 ${x2} ${y2} Z`;
          const color = PALETTE[i % PALETTE.length];

          return <path key={i} d={pathData} fill={color} stroke="#ffffff" strokeWidth="0.03" />;
        })}
        <circle cx="0" cy="0" r="0.5" fill="#ffffff" />
      </svg>

      <div style={{ display: "flex", flexDirection: "column", gap: "6px", flex: 1, minWidth: "160px" }}>
        {data.map((item, i) => {
          const pct = ((item.count / total) * 100).toFixed(1);
          const color = PALETTE[i % PALETTE.length];
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px" }}>
              <span style={{ width: 10, height: 10, borderRadius: "50%", background: color, flexShrink: 0 }} />
              <span style={{ color: "var(--color-ink)", fontWeight: 500, flex: 1 }}>{item.name}</span>
              <span style={{ color: "var(--color-muted)", fontSize: "12px", fontWeight: 600 }}>{pct}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
