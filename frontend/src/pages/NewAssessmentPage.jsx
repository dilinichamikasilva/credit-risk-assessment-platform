import { useState } from "react";
import { Link } from "react-router-dom";
import {
  formatApiError,
  formatCurrency,
  predictFullAssessment,
} from "../api/client";
import Gauge from "../components/Gauge";
import NumberField from "../components/forms/NumberField";
import SelectField from "../components/forms/SelectField";

const INT_FIELDS = new Set([
  "age",
  "times_30_59_days_late",
  "open_credit_lines",
  "times_90_days_late",
  "real_estate_loans",
  "times_60_89_days_late",
  "dependents",
  "no_of_dependents",
  "loan_term",
  "cibil_score",
]);

const INITIAL_VALUES = {
  applicant_name: "Demo Applicant",
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
  no_of_dependents: "2",
  education: "Graduate",
  self_employed: "No",
  income_annum: "9600000",
  loan_amount: "20000000",
  loan_term: "12",
  cibil_score: "778",
  residential_assets_value: "2400000",
  commercial_assets_value: "17600000",
  luxury_assets_value: "22700000",
  bank_asset_value: "8000000",
};

const BAND_COPY = {
  low: { label: "Low risk", icon: "🟢" },
  medium: { label: "Medium risk", icon: "🟡" },
  high: { label: "High risk", icon: "🔴" },
};

export default function NewAssessmentPage() {
  const [values, setValues] = useState(INITIAL_VALUES);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  function handleChange(name, value) {
    setValues((prev) => {
      const next = { ...prev, [name]: value };
      // Keep Model A dependents and loan-form dependents in sync when one changes.
      if (name === "dependents") next.no_of_dependents = value;
      if (name === "no_of_dependents") next.dependents = value;
      return next;
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const payload = Object.fromEntries(
        Object.entries(values).map(([key, val]) => {
          if (key === "applicant_name" || key === "education" || key === "self_employed") {
            return [key, typeof val === "string" ? val.trim() : val];
          }
          return [key, INT_FIELDS.has(key) ? parseInt(val, 10) : parseFloat(val)];
        })
      );
      const data = await predictFullAssessment(payload);
      setResult(data);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }

  const band = result ? BAND_COPY[result.default.risk_band] : null;

  return (
    <div>
      <div className="page-header">
        <p className="eyebrow">All-in-one</p>
        <h1>New Risk Assessment</h1>
        <p>
          Enter one applicant once. We run default risk, approval, and recommended
          amount together and save the full report.
        </p>
      </div>

      <form className="form-card" onSubmit={handleSubmit}>
        <div className="form-section-title">Applicant</div>
        <div className="form-grid">
          <div className="field">
            <label htmlFor="applicant_name">Applicant name</label>
            <input
              id="applicant_name"
              type="text"
              name="applicant_name"
              value={values.applicant_name}
              required
              minLength={1}
              maxLength={120}
              onChange={(e) => handleChange("applicant_name", e.target.value)}
            />
          </div>
        </div>

        <div className="form-section-title">💳 Credit & payment history</div>
        <div className="form-grid">
          <NumberField label="Revolving utilization" name="revolving_utilization" min={0} max={2} slider value={values.revolving_utilization} onChange={handleChange} />
          <NumberField label="Debt-to-income ratio" name="debt_ratio" min={0} max={5} slider value={values.debt_ratio} onChange={handleChange} />
          <NumberField label="Monthly income" name="monthly_income" min={0} value={values.monthly_income} onChange={handleChange} />
          <NumberField label="Open credit lines" name="open_credit_lines" min={0} value={values.open_credit_lines} onChange={handleChange} />
          <NumberField label="Real-estate loans" name="real_estate_loans" min={0} value={values.real_estate_loans} onChange={handleChange} />
          <NumberField label="Times 30-59 days late" name="times_30_59_days_late" min={0} value={values.times_30_59_days_late} onChange={handleChange} />
          <NumberField label="Times 60-89 days late" name="times_60_89_days_late" min={0} value={values.times_60_89_days_late} onChange={handleChange} />
          <NumberField label="Times 90+ days late" name="times_90_days_late" min={0} value={values.times_90_days_late} onChange={handleChange} />
          <NumberField label="Age" name="age" min={18} max={120} value={values.age} onChange={handleChange} />
          <NumberField label="Dependents" name="dependents" min={0} value={values.dependents} onChange={handleChange} />
        </div>

        <div className="form-section-title">📝 Loan details</div>
        <div className="form-grid">
          <SelectField
            label="Education"
            name="education"
            value={values.education}
            onChange={handleChange}
            options={[
              { value: "Graduate", label: "Graduate" },
              { value: "Not Graduate", label: "Not Graduate" },
            ]}
          />
          <SelectField
            label="Self-employed"
            name="self_employed"
            value={values.self_employed}
            onChange={handleChange}
            options={[
              { value: "No", label: "No" },
              { value: "Yes", label: "Yes" },
            ]}
          />
          <NumberField label="Annual income" name="income_annum" min={1} value={values.income_annum} onChange={handleChange} />
          <NumberField label="Requested loan amount" name="loan_amount" min={1} value={values.loan_amount} onChange={handleChange} />
          <NumberField label="Loan term (months)" name="loan_term" min={1} value={values.loan_term} onChange={handleChange} />
          <NumberField label="CIBIL score" name="cibil_score" min={300} max={900} value={values.cibil_score} onChange={handleChange} />
          <NumberField label="Residential assets" name="residential_assets_value" min={0} value={values.residential_assets_value} onChange={handleChange} />
          <NumberField label="Commercial assets" name="commercial_assets_value" min={0} value={values.commercial_assets_value} onChange={handleChange} />
          <NumberField label="Luxury assets" name="luxury_assets_value" min={0} value={values.luxury_assets_value} onChange={handleChange} />
          <NumberField label="Bank assets" name="bank_asset_value" min={0} value={values.bank_asset_value} onChange={handleChange} />
        </div>

        <div className="form-grid form-actions">
          <button type="submit" className="submit-btn" disabled={loading}>
            {loading && <span className="spinner" />}
            {loading ? "Running full assessment..." : "Run full assessment"}
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
        <div className="result-wrap combined-report">
          <div className="report-banner">
            <div>
              <h2>Combined risk report</h2>
              <p>
                Saved as{" "}
                <Link to={`/applications/${result.application_id}`}>application #{result.application_id}</Link>
              </p>
            </div>
          </div>

          <div className="report-grid">
            <div className="result-card">
              <Gauge probability={result.default.probability} band={result.default.risk_band} />
              <div className="result-details">
                <h3>Default risk</h3>
                <div className="result-row">
                  <span className={`badge ${result.default.risk_band}`}>
                    {band.icon} {band.label}
                  </span>
                </div>
                <div className="result-row">
                  Chance of defaulting: <strong>{(result.default.probability * 100).toFixed(1)}%</strong>
                </div>
              </div>
            </div>

            <div className="result-card">
              <div className={`decision-orb ${result.approval.approved ? "approved" : "rejected"}`}>
                {result.approval.approved ? "✓" : "✕"}
              </div>
              <div className="result-details">
                <h3>Loan approval</h3>
                <div className="result-row">
                  <span className={`badge ${result.approval.approved ? "low" : "high"}`}>
                    {result.approval.approved ? "Approved" : "Rejected"}
                  </span>
                </div>
                <div className="result-row">
                  Confidence:{" "}
                  <strong>{(result.approval.approval_probability * 100).toFixed(1)}%</strong>
                </div>
              </div>
            </div>

            <div className="result-card amount-result">
              <div className="amount-hero compact">
                <span className="amount-label">Recommended</span>
                <span className="amount-value">{formatCurrency(result.amount.recommended_amount)}</span>
                {result.amount.capped_at_requested && (
                  <span className="badge medium">Capped at what you requested</span>
                )}
              </div>
              <div className="result-details">
                <h3>Recommended amount</h3>
                <div className="result-row">
                  Model's estimate: <strong>{formatCurrency(result.amount.predicted_amount)}</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
