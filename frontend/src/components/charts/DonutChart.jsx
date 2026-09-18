/** Simple SVG donut for risk-band distribution. */
const BAND_COLORS = {
  low: "#16a34a",
  medium: "#b45309",
  high: "#dc2626",
  unknown: "#94a3b8",
};

export default function DonutChart({ segments, size = 160 }) {
  const total = segments.reduce((sum, s) => sum + s.value, 0);
  const stroke = 22;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;

  if (!total) {
    return <p className="muted">No data yet.</p>;
  }

  return (
    <div className="donut-wrap">
      <svg width={size} height={size} className="donut">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#eef0f6"
          strokeWidth={stroke}
        />
        {segments.map((seg) => {
          const length = (seg.value / total) * circumference;
          const dashOffset = circumference * 0.25 - offset;
          offset += length;
          return (
            <circle
              key={seg.key || seg.label}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={BAND_COLORS[seg.key || seg.label] || seg.color || "#6366f1"}
              strokeWidth={stroke}
              strokeDasharray={`${length} ${circumference - length}`}
              strokeDashoffset={dashOffset}
              strokeLinecap="butt"
            />
          );
        })}
        <text
          x="50%"
          y="50%"
          textAnchor="middle"
          dominantBaseline="central"
          className="donut-center"
        >
          {total}
        </text>
      </svg>
      <ul className="donut-legend">
        {segments.map((seg) => (
          <li key={seg.key || seg.label}>
            <span
              className="swatch"
              style={{ background: BAND_COLORS[seg.key || seg.label] || seg.color || "#6366f1" }}
            />
            {seg.label}: <strong>{seg.value}</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}
