import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { formatApiError, formatNumber, getAnalyticsSummary, humanizeLabel } from "../api/client";
import BarList from "../components/charts/BarList";
import DonutChart from "../components/charts/DonutChart";

const MODEL_LABELS = {
  model_a: "Default risk",
  model_b: "Loan approval",
  model_c: "Recommended amount",
};

const BAND_LABELS = {
  low: "Low risk",
  medium: "Medium risk",
  high: "High risk",
  unknown: "Unknown",
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

  const isEmpty = summary && !summary.total_applications;

  return (
    <div>
      <div className="page-header">
        <p className="eyebrow">Insights</p>
        <h1>Analytics Dashboard</h1>
        <p>How many applications you've assessed, and how the risk breaks down.</p>
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
              <p className="error-text">{error}</p>
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
              <span className="stat-icon" aria-hidden="true">📄</span>
              <div className="stat-body">
                <span className="stat-label">Applications</span>
                <span className="stat-value">{formatNumber(summary.total_applications)}</span>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon" aria-hidden="true">🧮</span>
              <div className="stat-body">
                <span className="stat-label">Assessments</span>
                <span className="stat-value">{formatNumber(summary.total_assessments)}</span>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon" aria-hidden="true">📈</span>
              <div className="stat-body">
                <span className="stat-label">Avg default probability</span>
                <span className="stat-value">
                  {summary.avg_default_probability == null
                    ? "—"
                    : `${(summary.avg_default_probability * 100).toFixed(1)}%`}
                </span>
              </div>
            </div>
          </div>

          {isEmpty ? (
            <div className="form-card empty-state">
              <span className="empty-state-icon" aria-hidden="true">📭</span>
              <h3>No applications yet</h3>
              <p>
                Run your first assessment and this dashboard will fill in with your
                risk breakdown and application activity.
              </p>
              <Link to="/assessment" className="hero-cta">
                Start an assessment →
              </Link>
            </div>
          ) : (
            <div className="dash-grid">
              <div className="form-card">
                <h3 className="card-title">🎯 Risk distribution</h3>
                <DonutChart
                  segments={toItems(summary.assessments_by_risk_band).map((s) => ({
                    key: s.label,
                    label: BAND_LABELS[s.label] || humanizeLabel(s.label),
                    value: s.value,
                  }))}
                />
              </div>
              <div className="form-card">
                <h3 className="card-title">🧮 Assessments by type</h3>
                <BarList
                  items={toItems(summary.assessments_by_model, (k) => MODEL_LABELS[k] || k)}
                />
              </div>
              <div className="form-card">
                <h3 className="card-title">📋 Applications by status</h3>
                <BarList
                  items={toItems(summary.applications_by_status, humanizeLabel)}
                  color="var(--color-primary-dark)"
                />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
