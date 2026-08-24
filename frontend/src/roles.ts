import type { Role } from "./types";

export type NavKey =
  | "dashboard"
  | "query-builder"
  | "query-history"
  | "federation"
  | "institutions"
  | "system-health"
  | "privacy"
  | "audit"
  | "provenance"
  | "benchmarks"
  | "analytics"
  | "docs"
  | "settings";

const ALL: NavKey[] = [
  "dashboard",
  "query-builder",
  "query-history",
  "federation",
  "institutions",
  "system-health",
  "privacy",
  "audit",
  "provenance",
  "benchmarks",
  "analytics",
  "docs",
  "settings",
];

export const ROLE_NAV: Record<Role, NavKey[]> = {
  researcher: [
    "dashboard",
    "query-builder",
    "query-history",
    "federation",
    "institutions",
    "system-health",
    "privacy",
    "audit",
    "provenance",
    "benchmarks",
    "docs",
    "settings",
  ],
  clinician: [
    "dashboard",
    "query-builder",
    "query-history",
    "federation",
    "privacy",
    "docs",
    "settings",
  ],
  auditor: ["dashboard", "federation", "privacy", "audit", "provenance", "system-health", "benchmarks", "docs", "settings"],
  data_steward: ["dashboard", "federation", "institutions", "system-health", "audit", "docs", "settings"],
  admin: ALL,
};

export function can(role: Role, key: NavKey) {
  return ROLE_NAV[role]?.includes(key) ?? false;
}

export function homeFor(role: Role) {
  if (role === "auditor") return "/audit";
  return "/dashboard";
}
