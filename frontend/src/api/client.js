import axios from "axios";

// Empty baseURL = same origin → Vite proxy (see vite.config.js).
// Set VITE_API_BASE_URL only when calling the API on another host.
const baseURL = import.meta.env.VITE_API_BASE_URL ?? "";

export const apiClient = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

export async function getHealth() {
  const { data } = await apiClient.get("/health");
  return data;
}

export async function getModelInfo() {
  const { data } = await apiClient.get("/model-info");
  return data;
}

export async function predictDefaultProbability(payload) {
  const { data } = await apiClient.post("/predict/default-probability", payload);
  return data;
}

/** SITHUMINI — Model B / Calls the standalone Loan Approval API */
export async function predictLoanApproval(payload) {
  const { data } = await apiClient.post("/predict/loan-approval", payload);
  return data;
}

/** SITHUMINI — History page: application list endpoint. */
export async function getApplications(params = {}) {
  const { data } = await apiClient.get("/applications", { params });
  return data;
}

/** Sasuni — Model C standalone */
export async function predictRecommendedAmount(payload) {
  const { data } = await apiClient.post("/predict/recommended-amount", payload);
  return data;
}

/** Sasuni — flagship A+B+C */
export async function predictFullAssessment(payload) {
  const { data } = await apiClient.post("/predict/full-assessment", payload);
  return data;
}

/** Sasuni — applicant detail (printable) */
export async function getApplication(id) {
  const { data } = await apiClient.get(`/applications/${id}`);
  return data;
}

/** Dashboard aggregates (Ilma's endpoint; Sasuni owns the page) */
export async function getAnalyticsSummary() {
  const { data } = await apiClient.get("/analytics/summary");
  return data;
}

export function formatApiError(err) {
  const detail = err.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => `${d.loc?.at(-1)}: ${d.msg}`).join(", ");
  }
  if (typeof detail === "string") return detail;
  if (err.code === "ERR_NETWORK" || err.message === "Network Error") {
    return (
      "Cannot reach the API. Start the backend with " +
      "`uvicorn app.main:app --reload` and confirm VITE_API_BASE_URL " +
      `(currently ${baseURL}).`
    );
  }
  if (err.response?.status) {
    return err.message || `Request failed (${err.response.status})`;
  }
  return err.message || "Request failed";
}

export function formatCurrency(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  // Prefer en-LK; fall back if the runtime lacks that locale data.
  try {
    return new Intl.NumberFormat("en-LK", {
      style: "currency",
      currency: "LKR",
      maximumFractionDigits: 0,
    }).format(Number(value));
  } catch {
    return new Intl.NumberFormat("en", {
      style: "currency",
      currency: "LKR",
      maximumFractionDigits: 0,
    }).format(Number(value));
  }
}

export function formatNumber(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  try {
    return new Intl.NumberFormat("en-LK").format(Number(value));
  } catch {
    return new Intl.NumberFormat("en").format(Number(value));
  }
}

export function humanizeLabel(value) {
  return String(value ?? "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

// Ilma
export async function updateApplication(id, patch) {
  const { data } = await apiClient.put(`/applications/${id}`, patch);
  return data;
}

// Ilma
export async function deleteApplication(id) {
  await apiClient.delete(`/applications/${id}`);
}