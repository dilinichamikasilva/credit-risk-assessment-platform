import { useState } from "react";
import {
  formatApiError,
  formatCurrency,
  predictRecommendedAmount,
} from "../api/client";
import NumberField from "../components/forms/NumberField";
import SelectField from "../components/forms/SelectField";

const INITIAL_VALUES = {
  applicant_name: "",
  no_of_dependents: "2",
  education: "Graduate",
  self_employed: "No",
  income_annum: "2400000",
  loan_term: "36",
  crib_score: "720",
  residential_assets_value: "9000000",
  commercial_assets_value: "0",
  luxury_assets_value: "1500000",
  bank_asset_value: "1200000",
  requested_amount: "3500000",
};

export default function RecommendedAmountPage() {
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
      const payload = {
        no_of_dependents: parseInt(values.no_of_dependents, 10),
        education: values.education,
        self_employed: values.self_employed,
        income_annum: parseFloat(values.income_annum),
        loan_term: parseInt(values.loan_term, 10),
        crib_score: parseInt(values.crib_score, 10),
        residential_assets_value: parseFloat(values.residential_assets_value),
        commercial_assets_value: parseFloat(values.commercial_assets_value),
        luxury_assets_value: parseFloat(values.luxury_assets_value),
        bank_asset_value: parseFloat(values.bank_asset_value),
        requested_amount: parseFloat(values.requested_amount),
      };
      if (values.applicant_name.trim()) {
        payload.applicant_name = values.applicant_name.trim();
      }
      // Guard: never send loan_amount as a model feature — API uses requested_amount for the cap only.
      const data = await predictRecommendedAmount(payload);
      setResult(data);
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
        <h1>Recommended Loan Amount</h1>
        <p>
          Get a safe loan amount (LKR) based on income, assets, and CRIB score.
          We'll never recommend more than they asked for.
        </p>
        <p className="data-disclosure">
          Models trained on synthetic Sri Lankan data (calibrated to CRIB / DCS HIES anchors)
          as of September 2026 — indicative only, not a substitute for a real credit decision.
        </p>
      </div>

      <form className="form-card" onSubmit={handleSubmit}>
        <div className="form-section-title">Applicant (optional save)</div>
        <div className="form-grid">
          <div className="field">
            <label htmlFor="applicant_name">Applicant name</label>
            <input
              id="applicant_name"
              type="text"
              name="applicant_name"
              value={values.applicant_name}
              placeholder="Leave blank to skip saving"
              maxLength={120}
              onChange={(e) => handleChange("applicant_name", e.target.value)}
            />
          </div>
        </div>

        <div className="form-section-title">Profile</div>
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
          <NumberField
            label="Requested amount (LKR)"
            name="requested_amount"
            min={1}
            value={values.requested_amount}
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
            {loading ? "Estimating amount..." : "Recommend amount"}
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
          <div className="result-card amount-result">
            <div className="amount-hero">
              <span className="amount-label">Recommended</span>
              <span className="amount-value">{formatCurrency(result.recommended_amount)}</span>
              {result.capped_at_requested && (
                <span className="badge medium">Capped at requested</span>
              )}
            </div>
            <div className="result-details">
              <h3>Amount breakdown</h3>
              <div className="result-row">
                Model's estimate: <strong>{formatCurrency(result.predicted_amount)}</strong>
              </div>
              <div className="result-row">
                Recommended: <strong>{formatCurrency(result.recommended_amount)}</strong>
              </div>
              {result.application_id != null && (
                <p className="result-meta">Saved as application #{result.application_id}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
