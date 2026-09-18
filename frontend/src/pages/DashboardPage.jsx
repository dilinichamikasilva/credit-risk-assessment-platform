import { useEffect, useState } from "react";
import { formatApiError, getAnalyticsSummary } from "../api/client";
import BarList from "../components/charts/BarList";
import DonutChart from "../components/charts/DonutChart";

const MODEL_LABELS = {
  model_a: "Default risk (A)",
  model_b: "Approval (B)",
  model_c: "Amount (C)",
};

function toItems(map, labelFn = (k) => k) {
  return Object.entries(map || {})
    .map(([label, value]) => ({ label: labelFn(label), value: Number(value) || 0 }))
    .sort((a, b) => b.value - a.value);
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getAnalyticsSummary();
        if (!cancelled) setSummary(data);
      } catch (err) {
        if (!cancelled) setError(formatApiError(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <div className="page-header">
        <p className="eyebrow">Insights</p>
        <h1>Analytics Dashboard</h1>
        <p>Assessment volume, risk mix, and model usage at a glance.</p>
      </div>

      {loading && (
        <div className="form-card center-pad">
          <span className="spinner dark" /> Loading analytics...
        </div>
      )}

      {error && (
        <div className="result-wrap">
          <div className="result-card error">
            <div className="result-details">
              <h3>Could not load dashboard</h3>
              <p style={{ color: "#991b1b", margin: 0 }}>{error}</p>
              <p className="result-meta">
                Needs the backend running with <code>GET /analytics/summary</code>.
              </p>
            </div>
          </div>
        </div>
      )}

      {summary && !loading && (
        <>
          <div className="stat-grid">
            <div className="stat-card">
              <span className="stat-label">Applications</span>
              <span className="stat-value">{summary.total_applications}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Assessments</span>
              <span className="stat-value">{summary.total_assessments}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Avg default probability</span>
              <span className="stat-value">
                {summary.avg_default_probability == null
                  ? "—"
                  : `${(summary.avg_default_probability * 100).toFixed(1)}%`}
              </span>
            </div>
          </div>

          <div className="dash-grid">
            <div className="form-card">
              <h3 className="card-title">Risk distribution</h3>
              <DonutChart
                segments={toItems(summary.assessments_by_risk_band).map((s) => ({
                  ...s,
                  label: s.label,
                }))}
              />
            </div>
            <div className="form-card">
              <h3 className="card-title">Assessments by model</h3>
              <BarList
                items={toItems(summary.assessments_by_model, (k) => MODEL_LABELS[k] || k)}
              />
            </div>
            <div className="form-card">
              <h3 className="card-title">Applications by status</h3>
              <BarList
                items={toItems(summary.applications_by_status)}
                color="var(--color-primary-dark)"
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
