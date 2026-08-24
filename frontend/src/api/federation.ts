import { api } from "./client";
import type { NodeInfo } from "../types";

export function listNodes(token: string) {
  return api<NodeInfo[]>("/nodes", token);
}

export function nodeHealth(token: string, id: string) {
  return api<NodeInfo>(`/nodes/${id}/health`, token);
}

export function topology(token: string) {
  return api<{ coordinator: string; nodes: NodeInfo[] }>("/topology", token);
}

export function stats(token: string) {
  return api<{
    active_institutions: number;
    online_nodes: number;
    nodes_total: number;
    queries_today: number;
    queries_total: number;
    complete_queries: number;
    partial_queries: number;
    suppressed_results: number;
    privacy_budget_used_pct: number;
    average_query_ms: number | null;
    environment: string;
    nodes: NodeInfo[];
  }>("/stats", token);
}

export function gatewayHealth() {
  return api<{ ok: boolean; service: string; version: string }>("/health");
}
