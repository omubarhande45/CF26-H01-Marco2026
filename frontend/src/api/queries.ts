import { api } from "./client";
import type { QueryListItem, QueryResult, QuerySpec } from "../types";

export function createQuery(token: string, spec: QuerySpec) {
  return api<{ id: string; query_id: string; status: string; spec: QuerySpec; policy: Record<string, unknown> }>(
    "/queries",
    token,
    { method: "POST", body: JSON.stringify(spec) }
  );
}

export function executeQuery(token: string, id: string) {
  return api<QueryResult>(`/queries/${id}/execute`, token, { method: "POST" });
}

export function executeAsync(token: string, id: string) {
  return api<{ query_id: string; status: string }>(`/queries/${id}/execute-async`, token, { method: "POST" });
}

export function cancelQuery(token: string, id: string) {
  return api<{ query_id: string; status: string }>(`/queries/${id}/cancel`, token, { method: "POST" });
}

export function getQuery(token: string, id: string) {
  return api<Record<string, unknown>>(`/queries/${id}`, token);
}

export function getResult(token: string, id: string) {
  return api<QueryResult>(`/queries/${id}/result`, token);
}

export function listQueries(token: string) {
  return api<QueryListItem[]>("/query-history", token);
}

export function explainQuery(token: string, id: string) {
  return api<{ query_id: string; plan?: unknown; explain?: unknown; lifecycle?: string[] }>(`/queries/${id}/explain`, token);
}

export function previewPolicy(token: string, spec: QuerySpec) {
  return api<Record<string, unknown>>("/queries/preview-policy", token, { method: "POST", body: JSON.stringify(spec) });
}

export function getProvenance(token: string, id: string) {
  return api<Record<string, unknown>>(`/queries/${id}/provenance`, token);
}
