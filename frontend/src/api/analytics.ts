import { api } from "./client";

export type TrendPoint = { year: number; count: number | null; suppressed?: boolean };

export type NodeAnalytics = {
  node_id: string;
  name: string;
  healthy: boolean;
  k?: number;
  year_min?: number;
  year_max?: number;
  top_diseases: Array<{
    disease_id?: string;
    disease_name: string;
    icd10_code?: string;
    category?: string;
    count: number;
  }>;
  trend: TrendPoint[];
};

export type AnalyticsOverview = {
  disease: string;
  nodes: NodeAnalytics[];
  timeline: Array<Record<string, number | null | string>>;
  top_diseases: Array<{
    disease_name: string;
    icd10_code?: string;
    category?: string;
    count: number;
    nodes: number;
  }>;
  completeness_note?: string;
};

export function analyticsOverview(token: string, disease: string) {
  const q = encodeURIComponent(disease);
  return api<AnalyticsOverview>(`/analytics/overview?disease=${q}`, token);
}

export function analyticsNode(token: string, nodeId: string) {
  return api<{
    node_id: string;
    node_name: string;
    k: number;
    year_min: number;
    year_max: number;
    top_diseases: Array<{ disease_name: string; icd10_code?: string; category?: string; count: number }>;
  }>(`/analytics/node/${nodeId}`, token);
}
