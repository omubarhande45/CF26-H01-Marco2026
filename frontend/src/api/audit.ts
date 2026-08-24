import { api } from "./client";
import type { AuditRow } from "../types";

export function auditLogs(token: string) {
  return api<AuditRow[]>("/audit/logs", token);
}

export function auditDetail(token: string, id: number) {
  return api<AuditRow>(`/audit/logs/${id}`, token);
}
