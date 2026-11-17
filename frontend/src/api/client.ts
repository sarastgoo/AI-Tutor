// API client for AI English Tutor backend

const API_BASE = "/api/v1";

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
}

export interface HealthDbResponse {
  status: string;
  db: string;
  postgres_version: string | null;
  pgvector_version: string | null;
  error?: string;
}

async function fetchJSON<T>(path: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`);
  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
  }
  return resp.json() as Promise<T>;
}

export const api = {
  health: () => fetchJSON<HealthResponse>("/health"),
  healthDb: () => fetchJSON<HealthDbResponse>("/health/db"),
};