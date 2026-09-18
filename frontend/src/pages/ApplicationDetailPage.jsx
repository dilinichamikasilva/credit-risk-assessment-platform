import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  deleteApplication,
  formatApiError,
  formatCurrency,
  getApplication,
  updateApplication,
} from "../api/client";
import Gauge from "../components/Gauge";

const MODEL_LABELS = {
  model_a: "Default risk",
  model_b: "Loan approval",
  model_c: "Recommended amount",
};

const BAND_COPY = {
  low: { label: "Low risk", icon: "🟢" },
  medium: { label: "Medium risk", icon: "🟡" },
  high: { label: "High risk", icon: "🔴" },
};

function formatDate(iso) {
  return iso ? new Date(iso).toLocaleString() : "—";
}

function latestPerModel(assessments) {
  const byModel = {};
  for (const item of assessments) {
    if (!byModel[item.model_key]) byModel[item.model_key] = item; // list is newest-first
  }
  return byModel;
}

function OutputRows({ item }) {
  const out = item.outputs || {};
  if (item.model_key === "model_a") {
    return (
      <div className="result-row">
        Chance of defaulting: <strong>{(Number(out.probability) * 100).toFixed(1)}%</strong>
      </div>
    );
  }
  if (item.model_key === "model_b") {
    return (
      <>
        <div className="result-row">
          <span className={`badge ${out.approved ? "low" : "high"}`}>
            {out.approved ? "Approved" : "Rejected"}
          </span>
        </div>
        <div className="result-row">
          Confidence: <strong>{(Number(out.approval_probability) * 100).toFixed(1)}%</strong>
        </div>
      </>
    );
  }
  return (
    <>
      <div className="result-row">
        Recommended: <strong>{formatCurrency(out.recommended_amount)}</strong>
      </div>
      {out.capped_at_requested && <span className="badge medium">Capped at requested</span>}
    </>
  );
}

function AssessmentRow({ item }) {
  const band = BAND_COPY[item.risk_band];
  return (
    <div className="result-card">
      <div className="result-details">
        <h3>
          {MODEL_LABELS[item.model_key] || item.model_key}{" "}
          {band && (
            <span className={`badge ${item.risk_band}`}>
              {band.icon} {band.label}
            </span>
          )}
        </h3>
        <OutputRows item={item} />
        <p className="result-meta">{formatDate(item.created_at)}</p>
        <details>
          <summary className="muted">Show technical details</summary>
          <pre className="json-block">{JSON.stringify(item.inputs, null, 2)}</pre>
          <pre className="json-block">{JSON.stringify(item.outputs, null, 2)}</pre>
        </details>
      </div>
    </div>
  );
}

function LatestCard({ children, fallbackLabel }) {
  return (
    <div className="result-card">
      {children || (
        <div className="result-details">
          <h3>{fallbackLabel}</h3>
          <p className="muted">No run yet.</p>
        </div>
      )}
    </div>
  );
}

export default function ApplicationDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notFound, setNotFound] = useState(false);

  const [editing, setEditing] = useState(false);
  const [nameDraft, setNameDraft] = useState("");
  const [actionError, setActionError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setNotFound(false);
      setError(null);
      try {
        const data = await getApplication(id);
        if (!cancelled) setApplication(data);
      } catch (err) {
        if (cancelled) return;
        if (err.response?.status === 404) setNotFound(true);
        else setError(formatApiError(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  async function handleRename(e) {
    e.preventDefault();
    setBusy(true);
    setActionError(null);
    try {
      // Backend accepts ONLY applicant_name (extra="forbid") — send nothing else.
      const data = await updateApplication(id, { applicant_name: nameDraft.trim() });
      setApplication(data);
      setEditing(false);
    } catch (err) {
      setActionError(formatApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    const ok = window.confirm(
      `Delete application #${id}? Every assessment logged for this applicant is permanently removed.`
    );
    if (!ok) return;
    setBusy(true);
    setActionError(null);
    try {
      await deleteApplication(id);
      navigate("/");
    } catch (err) {
      setBusy(false);
      setActionError(formatApiError(err));
    }
  }

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <p className="eyebrow">Applications</p>
          <h1>Application detail</h1>
        </div>
        <div className="form-card center-pad">
          <span className="spinner dark" /> Loading applicant file...
        </div>
      </div>
    );
  }

  if (notFound) {
    return (
      <div>
        <div className="page-header">
          <p className="eyebrow">Applications</p>
          <h1>Application detail</h1>
        </div>
        <div className="result-wrap">
          <div className="result-card error">
            <div className="result-details">
              <h3>Application #{id} not found</h3>
              <p className="error-text">
                It may have been deleted, or the link is stale.
              </p>
              <p className="result-meta">
                <Link to="/">Back to home</Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <div className="page-header">
          <p className="eyebrow">Applications</p>
          <h1>Application detail</h1>
        </div>
        <div className="result-wrap">
          <div className="result-card error">
            <div className="result-details">
              <h3>Could not load application</h3>
              <p className="error-text">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const sorted = [...(application.assessments || [])].sort(
    (x, y) => new Date(y.created_at) - new Date(x.created_at)
  );
  const latest = latestPerModel(sorted);
  const a = latest.model_a;
  const b = latest.model_b;
  const c = latest.model_c;

  return (
    <div>
      <div className="page-header">
        <p className="eyebrow">Applications</p>
        <h1>
          {application.applicant_name} <span className="muted">#{application.id}</span>
        </h1>
        <p>
          <span className={`badge ${application.status === "assessed" ? "low" : "medium"}`}>
            {application.status}
          </span>{" "}
          submitted {formatDate(application.created_at)}
        </p>
      </div>

      {actionError && (
        <div className="result-wrap">
          <div className="result-card error">
            <div className="result-details">
              <h3>Action failed</h3>
              <p className="error-text">{actionError}</p>
            </div>
          </div>
        </div>
      )}

      <div className="form-card">
        <h3 className="card-title">Applicant file</h3>
        <div className="detail-grid">
          <div><span className="muted">Education</span><strong>{application.education || "—"}</strong></div>
          <div><span className="muted">Self-employed</span><strong>{application.self_employed || "—"}</strong></div>
          <div><span className="muted">Income / annum</span><strong>{formatCurrency(application.income_annum)}</strong></div>
          <div><span className="muted">Loan amount</span><strong>{formatCurrency(application.loan_amount)}</strong></div>
          <div><span className="muted">Loan term (months)</span><strong>{application.loan_term ?? "—"}</strong></div>
          <div><span className="muted">CIBIL score</span><strong>{application.cibil_score ?? "—"}</strong></div>
          <div><span className="muted">Dependents</span><strong>{application.no_of_dependents}</strong></div>
          <div><span className="muted">Last updated</span><strong>{formatDate(application.updated_at)}</strong></div>
        </div>
        <div className="app-actions">
          {editing ? (
            <form onSubmit={handleRename} className="rename-row">
              <input
                type="text"
                value={nameDraft}
                maxLength={120}
                onChange={(e) => setNameDraft(e.target.value)}
                required
              />
              <button type="submit" className="submit-btn" disabled={busy}>Save name</button>
              <button type="button" className="submit-btn ghost-btn" onClick={() => setEditing(false)}>
                Cancel
              </button>
            </form>
          ) : (
            <button
              type="button"
              className="submit-btn ghost-btn"
              onClick={() => {
                setNameDraft(application.applicant_name);
                setEditing(true);
              }}
            >
              Rename applicant
            </button>
          )}
          <button type="button" className="submit-btn danger-btn" onClick={handleDelete} disabled={busy}>
            Delete application
          </button>
        </div>
        <p className="result-meta">
          Only the name can be changed here — assessment results are kept as a
          permanent record and can't be edited.
        </p>
      </div>

      <div className="section-heading"><h2>Latest results</h2></div>
      <div className="report-grid">
        <LatestCard fallbackLabel="Default risk">
          {a && (
            <>
              <Gauge probability={a.outputs.probability} band={a.risk_band} />
              <div className="result-details">
                <h3>Default risk</h3>
                <div className="result-row">
                  <span className={`badge ${a.risk_band}`}>
                    {BAND_COPY[a.risk_band]?.icon} {BAND_COPY[a.risk_band]?.label}
                  </span>
                </div>
                <div className="result-row">
                  Chance of defaulting: <strong>{(Number(a.outputs.probability) * 100).toFixed(1)}%</strong>
                </div>
              </div>
            </>
          )}
        </LatestCard>
        <LatestCard fallbackLabel="Loan approval">
          {b && (
            <>
              <div className={`decision-orb ${b.outputs.approved ? "approved" : "rejected"}`}>
                {b.outputs.approved ? "✓" : "✕"}
              </div>
              <div className="result-details">
                <h3>Loan approval</h3>
                <div className="result-row">
                  Confidence: <strong>{(Number(b.outputs.approval_probability) * 100).toFixed(1)}%</strong>
                </div>
              </div>
            </>
          )}
        </LatestCard>
        <LatestCard fallbackLabel="Recommended amount">
          {c && (
            <>
              <div className="amount-hero compact">
                <span className="amount-label">Recommended</span>
                <span className="amount-value">{formatCurrency(c.outputs.recommended_amount)}</span>
                {c.outputs.capped_at_requested && (
                  <span className="badge medium">Capped at what was requested</span>
                )}
              </div>
              <div className="result-details">
                <h3>Recommended amount</h3>
              </div>
            </>
          )}
        </LatestCard>
      </div>

      <div className="section-heading"><h2>Assessment history ({sorted.length})</h2></div>
      <div className="result-wrap">
        {sorted.map((item) => (
          <AssessmentRow key={item.id} item={item} />
        ))}
        {sorted.length === 0 && <p className="muted">No assessments logged yet.</p>}
      </div>
    </div>
  );
}
