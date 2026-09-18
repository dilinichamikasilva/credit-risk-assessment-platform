/** Tiny horizontal bar list for dashboard breakdowns — no chart library. */
export default function BarList({ items, color = "var(--color-primary)" }) {
  const max = Math.max(1, ...items.map((i) => i.value));

  if (!items.length) {
    return <p className="muted">No data yet.</p>;
  }

  return (
    <ul className="bar-list">
      {items.map((item) => (
        <li key={item.label}>
          <div className="bar-list-meta">
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </div>
          <div className="bar-track">
            <div
              className="bar-fill"
              style={{
                width: `${(item.value / max) * 100}%`,
                background: item.color || color,
              }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}
