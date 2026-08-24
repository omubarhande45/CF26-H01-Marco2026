import { api } from "./client";
import type { Role } from "../types";

export function login(username: string, password: string) {
  return api<{ access_token: string; role: Role; username: string }>("/auth/login", null, {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function me(token: string) {
  return api<{ username: string; role: Role; purpose?: string; permissions: string[] }>("/auth/me", token);
}

export function publicConfig() {
  return api<{ environment: string; demo_accounts: boolean; min_cohort: number; version: string }>("/config");
}

export function logout() {
  return api<{ ok: boolean }>("/auth/logout", null, { method: "POST" }).catch(() => ({ ok: false }));
}
