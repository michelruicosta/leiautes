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

function mensagemErroApi(data: unknown, fallback: string): string {
  if (data && typeof data === "object" && "detail" in data) {
    const detail = (data as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return "Verifique os campos obrigatórios e tente novamente.";
  }
  return fallback;
}

function filenameFromDisposition(disposition: string | null, fallback: string): string {
  const match = disposition?.match(/filename="?([^";]+)"?/i);
  return match?.[1] ?? fallback;
}

export async function apiDownload(path: string, fallbackName: string): Promise<void> {
  const resp = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
  });
  if (!resp.ok) {
    throw new ApiError(resp.status, `Erro ${resp.status}`);
  }
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filenameFromDisposition(
    resp.headers.get("Content-Disposition"),
    fallbackName,
  );
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export async function apiGet<T>(path: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
  });
  if (!resp.ok) {
    let message = `Erro ${resp.status}`;
    try {
      const data = await resp.json();
      message = mensagemErroApi(data, message);
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
      message = mensagemErroApi(data, message);
    } catch {
      // resposta sem JSON
    }
    throw new ApiError(resp.status, message);
  }
  return resp.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    let message = `Erro ${resp.status}`;
    try {
      const data = await resp.json();
      message = mensagemErroApi(data, message);
    } catch {
      // resposta sem JSON
    }
    throw new ApiError(resp.status, message);
  }
  return resp.json() as Promise<T>;
}
