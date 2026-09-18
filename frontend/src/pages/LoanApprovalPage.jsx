import { useState } from "react";
import {
  formatApiError,
  predictLoanApproval,
} from "../api/client";
import NumberField from "../components/forms/NumberField";
import SelectField from "../components/forms/SelectField";

/** MODEL B: LOAN APPROVAL */

const INITIAL_VALUES = {
  applicant_name: "",
  no_of_dependents: "",
  education: "Graduate",
  self_employed: "No",
  income_annum: "",
  loan_amount: "",
  loan_term: "",
  crib_score: "",
  residential_assets_value: "",
  commercial_assets_value: "",
  luxury_assets_value: "",
  bank_asset_value: "",
};

const INT_FIELDS = new Set([
  "no_of_dependents",
  "loan_term",
  "crib_score",
]);

const TIER_COPY = {
  Poor: "Higher credit-risk tier",
  Fair: "Fair credit-risk tier",
  Good: "Good credit-risk tier",
  Excellent: "Excellent credit-risk tier",
};

function toPayload(values) {
  const payload = Object.fromEntries(
    Object.entries(values)
      .filter(([key]) => key !== "applicant_name")
      .map(([key, value]) => [
      key,
      INT_FIELDS.has(key) ? parseInt(value, 10) : (
        key === "education" || key === "self_employed"
          ? value
          : parseFloat(value)
      ),
    ])
  );
  if (values.applicant_name.trim()) {
    payload.applicant_name = values.applicant_name.trim();
  }
  return payload;
}

export default function LoanApprovalPage() {
  const [values, setValues] = useState(INITIAL_VALUES);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  function handleChange(name, value) {
    setValues((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await predictLoanApproval(toPayload(values));
      setResult(data);
      setValues(INITIAL_VALUES);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <p className="eyebrow">Advanced tool</p>
        <h1>Loan Approval Prediction</h1>
        <p>
          Enter the applicant's loan profile (LKR amounts, CRIB score 250–900) to check
          whether their loan would likely be approved, and see their credit risk tier.
        </p>
        <p className="data-disclosure">
          Models trained on synthetic Sri Lankan data (calibrated to CRIB / DCS HIES anchors)
          as of September 2026 — indicative only, not a substitute for a real credit decision.
        </p>
      </div>

      <form className="form-card" onSubmit={handleSubmit}>
        <div className="form-section-title">Applicant</div>
        <div className="form-grid">
          <div className="field">
            <label htmlFor="applicant_name">Applicant name (optional)</label>
            <input
              id="applicant_name"
              type="text"
              value={values.applicant_name}
              placeholder="Leave blank to skip saving"
              maxLength={120}
              onChange={(event) => handleChange("applicant_name", event.target.value)}
            />
          </div>
        </div>

        <div className="form-section-title">Applicant profile</div>
        <div className="form-grid">
          <NumberField
            label="Number of dependents"
            name="no_of_dependents"
            min={0}
            max={20}
            value={values.no_of_dependents}
            onChange={handleChange}
          />
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
          <NumberField
            label="Annual income (LKR)"
            name="income_annum"
            min={1}
            value={values.income_annum}
            onChange={handleChange}
          />
          <NumberField
            label="Requested loan amount (LKR)"
            name="loan_amount"
            min={1}
            value={values.loan_amount}
            onChange={handleChange}
          />
          <NumberField
            label="Loan term (months)"
            name="loan_term"
            min={1}
            value={values.loan_term}
            onChange={handleChange}
          />
          <NumberField
            label="CRIB score"
            name="crib_score"
            min={250}
            max={900}
            value={values.crib_score}
            onChange={handleChange}
          />
        </div>

        <div className="form-section-title">Assets</div>
        <div className="form-grid">
          <NumberField
            label="Residential assets"
            name="residential_assets_value"
            min={0}
            value={values.residential_assets_value}
            onChange={handleChange}
          />
          <NumberField
            label="Commercial assets"
            name="commercial_assets_value"
            min={0}
            value={values.commercial_assets_value}
            onChange={handleChange}
          />
          <NumberField
            label="Luxury assets"
            name="luxury_assets_value"
            min={0}
            value={values.luxury_assets_value}
            onChange={handleChange}
          />
          <NumberField
            label="Bank assets"
            name="bank_asset_value"
            min={0}
            value={values.bank_asset_value}
            onChange={handleChange}
          />
        </div>

        <div className="form-grid form-actions">
          <button type="submit" className="submit-btn" disabled={loading}>
            {loading && <span className="spinner" />}
            {loading ? "Predicting approval..." : "Predict loan approval"}
          </button>
        </div>
      </form>

      {error && (
        <div className="result-wrap">
          <div className="result-card error">
            <div className="result-details">
              <h3>Could not score this application</h3>
              <p className="error-text">{error}</p>
            </div>
          </div>
        </div>
      )}

      {result && (
        <div className="result-wrap">
          <div className="result-card">
            <div className={`decision-orb ${result.approved ? "approved" : "rejected"}`}>
              {result.approved ? "✓" : "✕"}
            </div>
            <div className="result-details">
              <h3>{result.status}</h3>
              <div className="result-row">
                <span className={`badge ${result.approved ? "low" : "high"}`}>
                  {result.approved ? "Approved" : "Rejected"}
                </span>
              </div>
              <div className="result-row">
                Approval confidence:{" "}
                <strong>{(result.approval_probability * 100).toFixed(1)}%</strong>
              </div>
              <div className="result-row">
                Credit risk tier: <strong>{result.risk_tier}</strong>
              </div>
              <p className="result-meta">
                {TIER_COPY[result.risk_tier] || "Based on their credit score"}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
