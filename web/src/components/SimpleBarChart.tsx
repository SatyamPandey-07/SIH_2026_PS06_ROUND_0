import React from "react";

interface DataItem {
  name: string;
  count: number;
}

interface Props {
  data: DataItem[];
  color?: string;
}

export const SimpleBarChart: React.FC<Props> = ({ data, color = "#3b82f6" }) => {
  if (!data || data.length === 0) return null;
  const max = Math.max(...data.map(d => d.count), 1);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "10px", margin: "12px 0" }}>
      {data.map((item, idx) => {
        const pct = (item.count / max) * 100;
        return (
          <div key={idx} style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ width: "120px", fontSize: "13px", fontWeight: 500, color: "var(--color-ink)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {item.name}
            </span>
            <div style={{ flex: 1, height: "8px", background: "var(--color-surface-card)", borderRadius: "9999px", overflow: "hidden" }}>
              <div
                style={{
                  width: `${pct}%`,
                  height: "100%",
                  background: color,
                  borderRadius: "9999px",
                  transition: "width 0.5s ease",
                }}
              />
            </div>
            <span style={{ width: "50px", fontSize: "12px", fontWeight: 600, color: "var(--color-muted)", textAlign: "right" }}>
              {item.count.toLocaleString()}
            </span>
          </div>
        );
      })}
    </div>
  );
};
