export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

export async function apiGet<T>(path: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
  });
  if (!resp.ok) {
    let message = `Erro ${resp.status}`;
    try {
      const data = await resp.json();
      message = data.detail || message;
    } catch {
      // resposta sem JSON
    }
    throw new ApiError(resp.status, message);
  }
  return resp.json() as Promise<T>;
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    let message = `Erro ${resp.status}`;
    try {
      const data = await resp.json();
      message = data.detail || message;
    } catch {
      // resposta sem JSON
    }
    throw new ApiError(resp.status, message);
  }
  return resp.json() as Promise<T>;
}
