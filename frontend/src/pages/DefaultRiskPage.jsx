import { useState } from "react";
import { predictDefaultProbability } from "../api/client";
import NumberField from "../components/forms/NumberField";
import Gauge from "../components/Gauge";

const INT_FIELDS = new Set([
  "age",
  "times_30_59_days_late",
  "open_credit_lines",
  "times_90_days_late",
  "real_estate_loans",
  "times_60_89_days_late",
  "dependents",
]);

const SECTIONS = [
  {
    title: "💳 Credit profile",
    fields: [
      { name: "revolving_utilization", label: "Revolving credit utilization", min: 0, max: 2, slider: true },
      { name: "debt_ratio", label: "Debt-to-income ratio", min: 0, max: 5, slider: true },
      { name: "monthly_income", label: "Monthly income", min: 0 },
      { name: "open_credit_lines", label: "Open credit lines", min: 0 },
      { name: "real_estate_loans", label: "Real-estate loans", min: 0 },
    ],
  },
  {
    title: "⏱️ Payment history",
    fields: [
      { name: "times_30_59_days_late", label: "Times 30-59 days late", min: 0 },
      { name: "times_60_89_days_late", label: "Times 60-89 days late", min: 0 },
      { name: "times_90_days_late", label: "Times 90+ days late", min: 0 },
    ],
  },
  {
    title: "🧑 Personal",
    fields: [
      { name: "age", label: "Age", min: 18, max: 100 },
      { name: "dependents", label: "Number of dependents", min: 0 },
    ],
  },
];

const INITIAL_VALUES = {
  revolving_utilization: "0.3",
  age: "45",
  times_30_59_days_late: "0",
  debt_ratio: "0.35",
  monthly_income: "5000",
  open_credit_lines: "6",
  times_90_days_late: "0",
  real_estate_loans: "1",
  times_60_89_days_late: "0",
  dependents: "2",
};

const BAND_COPY = {
  low: { label: "Low risk", icon: "🟢" },
  medium: { label: "Medium risk", icon: "🟡" },
  high: { label: "High risk", icon: "🔴" },
};

export default function DefaultRiskPage() {
  const [values, setValues] = useState(INITIAL_VALUES);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  function handleChange(name, value) {
    setValues((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const payload = Object.fromEntries(
        Object.entries(values).map(([key, val]) => [
          key,
          INT_FIELDS.has(key) ? parseInt(val, 10) : parseFloat(val),
        ])
      );
      const data = await predictDefaultProbability(payload);
      setResult(data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        Array.isArray(detail)
          ? detail.map((d) => `${d.loc?.at(-1)}: ${d.msg}`).join(", ")
          : detail || err.message
      );
    } finally {
      setLoading(false);
    }
  }

  const band = result ? BAND_COPY[result.risk_band] : null;

  return (
    <div>
      <div className="page-header">
        <h1>Default Probability Check</h1>
        <p>
          Enter an applicant's financial profile to estimate their probability
          of serious default within the next 2 years.
        </p>
      </div>

      <form className="form-card" onSubmit={handleSubmit}>
        {SECTIONS.map((section) => (
          <div key={section.title}>
            <div className="form-section-title">{section.title}</div>
            <div className="form-grid">
              {section.fields.map((f) => (
                <NumberField
                  key={f.name}
                  label={f.label}
                  name={f.name}
                  min={f.min}
                  max={f.max}
                  slider={f.slider}
                  value={values[f.name]}
                  onChange={handleChange}
                />
              ))}
            </div>
          </div>
        ))}

        <div className="form-grid form-actions">
          <button type="submit" className="submit-btn" disabled={loading}>
            {loading && <span className="spinner" />}
            {loading ? "Scoring applicant..." : "Get risk assessment"}
          </button>
        </div>
      </form>

      {error && (
        <div className="result-wrap">
          <div className="result-card error">
            <div className="result-details">
              <h3>Something needs fixing</h3>
              <p className="error-text">{error}</p>
            </div>
          </div>
        </div>
      )}

      {result && (
        <div className="result-wrap">
          <div className="result-card">
            <Gauge probability={result.probability} band={result.risk_band} />
            <div className="result-details">
              <h3>Assessment result</h3>
              <div className="result-row">
                <span className={`badge ${result.risk_band}`}>
                  {band.icon} {band.label}
                </span>
              </div>
              <div className="result-row">
                Chance of defaulting: <strong>{(result.probability * 100).toFixed(1)}%</strong>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
