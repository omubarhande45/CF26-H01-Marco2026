const BASE = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");

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
    throw new ApiError(res.status, humanizeError(res.status, body, text));
  }
  return body as T;
}

function humanizeError(status: number, body: unknown, text: string): string {
  if (body && typeof body === "object") {
    const rec = body as { detail?: unknown; error?: { message?: string; code?: string } };
    if (typeof rec.detail === "string" && rec.detail.trim()) return rec.detail;
    if (rec.error?.message) {
      if (String(rec.error.code) === "404" || /could not be found/i.test(rec.error.message)) {
        return "The API gateway is not on this Vercel site. Deploy the FastAPI backend and set GATEWAY_URL, or sign in on the local Dashboard (port 5173).";
      }
      return rec.error.message;
    }
  }
  if (status === 404) {
    return "Login API was not found (404). This static host has no /api/auth/login unless GATEWAY_URL is set.";
  }
  return text || "Request failed";
}
