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
