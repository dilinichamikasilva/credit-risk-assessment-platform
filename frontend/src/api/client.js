import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

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
  return err.message || "Request failed";
}

export function formatCurrency(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(value));
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