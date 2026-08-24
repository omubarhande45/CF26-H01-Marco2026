const BASE = "/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function storedToken(): string | null {
  try {
    const raw = sessionStorage.getItem("fcqf.auth");
    if (!raw) return null;
    const u = JSON.parse(raw) as { token?: string; access_token?: string };
    return u.token || u.access_token || null;
  } catch {
    return null;
  }
}

export async function api<T = unknown>(path: string, token?: string | null, init?: RequestInit): Promise<T> {
  const bearer = (token || storedToken() || "").trim();
  const ctrl = new AbortController();
  const timer = window.setTimeout(() => ctrl.abort(), 25000);
  let res: Response;
  try {
    res = await fetch(BASE + path, {
      ...init,
      credentials: "include",
      signal: ctrl.signal,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...(bearer
          ? {
              Authorization: `Bearer ${bearer}`,
              "X-FCQF-Token": bearer,
            }
          : {}),
        ...(init?.headers || {}),
      },
    });
  } catch (e) {
    window.clearTimeout(timer);
    throw new ApiError(503, e instanceof Error && e.name === "AbortError" ? "Request timed out" : "Backend unavailable");
  }
  window.clearTimeout(timer);
  const text = await res.text();
  let body: unknown = text;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    /* keep text */
  }
  if (!res.ok) {
    const detail =
      typeof body === "object" && body && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : text || res.statusText;
    throw new ApiError(res.status, detail);
  }
  return body as T;
}
