const COLORS = {
  low: "#16a34a",
  medium: "#b45309",
  high: "#dc2626",
};

export default function Gauge({ probability, band, size = 120 }) {
  const stroke = 12;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(Math.max(probability, 0), 1);
  const offset = circumference * (1 - pct);
  const color = COLORS[band] ?? "#6366f1";

  return (
    <div className="gauge" style={{ width: size, height: size, position: "relative" }}>
      <svg width={size} height={size}>
        <circle
          className="gauge-track"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={stroke}
          fill="none"
        />
        <circle
          className="gauge-value"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={stroke}
          fill="none"
          stroke={color}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span className="gauge-label" style={{ fontSize: size * 0.19, color }}>
          {(pct * 100).toFixed(1)}%
        </span>
      </div>
    </div>
  );
}
