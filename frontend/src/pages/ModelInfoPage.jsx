import { useEffect, useState } from "react";
import { formatApiError, getHealth, getModelInfo } from "../api/client";

const MODEL_LABELS = {
  model_a: "Default risk (A)",
  model_b: "Approval (B)",
  model_c: "Amount (C)",
};

const MODEL_KEYS = ["model_a", "model_b", "model_c"];

function metricLabel(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatMetric(value) {
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(3);
  }
  if (value && typeof value === "object") {
    return Object.entries(value)
      .map(([subKey, subValue]) => `${metricLabel(subKey)}: ${formatMetric(subValue)}`)
      .join(" · ");
  }
  return String(value);
}

export default function ModelInfoPage() {
  const [models, setModels] = useState(null);
  const [loaded, setLoaded] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshedAt, setRefreshedAt] = useState(null);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [info, health] = await Promise.all([getModelInfo(), getHealth()]);
        if (!cancelled) {
          setModels(info.models || {});
          setLoaded(health.models_loaded || []);
          setRefreshedAt(new Date());
        }
      } catch (err) {
        if (!cancelled) setError(formatApiError(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshTick]);

  return (
    <div>
      <div className="page-header">
        <p className="eyebrow">Platform</p>
        <h1>Model info</h1>
        <p>Versions, tasks and metrics for every model behind the API.</p>
      </div>

      {loading && (
        <div className="form-card center-pad">
          <span className="spinner dark" /> Loading model info...
        </div>
      )}

      {error && (
        <div className="result-wrap">
          <div className="result-card error">
            <div className="result-details">
              <h3>Could not load model info</h3>
              <p className="error-text">{error}</p>
              <p className="result-meta">Needs the backend running (GET /model-info).</p>
            </div>
          </div>
        </div>
      )}

      {models && !loading && (
        <>
          <div className="dash-grid">
            {MODEL_KEYS.map((key) => {
              const entry = models[key];
              return (
                <div className="form-card" key={key}>
                  <h3 className="card-title">{MODEL_LABELS[key]}</h3>
                  {entry ? (
                    <>
                      {entry.task && <p className="result-meta">Task: <strong>{entry.task}</strong></p>}
                      <p className="result-meta">Version: <code>{entry.model_version}</code></p>
                      {Object.entries(entry.metrics || {}).map(([metric, value]) => (
                        <div className="result-row" key={metric}>
                            {metricLabel(metric)}:
                            {value && typeof value === "object" ? (
                            <div style={{ width: "100%" }}>
                                {Object.entries(value).map(([subKey, subValue]) => (
                                <div className="result-row" key={subKey}>
                                    <span className="muted">{metricLabel(subKey)}</span>
                                    <strong>{formatMetric(subValue)}</strong>
                                </div>
                                ))}
                            </div>
                            ) : (
                            <strong>{formatMetric(value)}</strong>
                            )}
                        </div>
                        ))}
                      {loaded.includes(key)
                        ? <span className="pill ready">loaded</span>
                        : <span className="pill soon">registered, not loaded</span>}
                    </>
                  ) : (
                    <p className="muted">Not available yet — model artifacts not committed.</p>
                  )}
                </div>
              );
            })}
          </div>
          <p className="result-meta">
            Last refreshed: {refreshedAt?.toLocaleTimeString()}{" "}
            <button
              type="button"
              className="submit-btn ghost-btn"
              onClick={() => setRefreshTick((t) => t + 1)}
              disabled={loading}
            >
              🔄 Refresh
            </button>
          </p>
        </>
      )}
    </div>
  );
}
