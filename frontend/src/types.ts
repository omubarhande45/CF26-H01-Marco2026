export type Role = "researcher" | "clinician" | "auditor" | "data_steward" | "admin";

export type AuthUser = { token: string; username: string; role: Role };

export type NodeInfo = {
  node_id: string;
  name: string;
  healthy: boolean;
  status?: string;
  schema_version?: string;
  patient_count?: number;
  latency_ms?: number;
  k_threshold?: number;
  policy?: Record<string, unknown>;
  schema_compatibility?: string;
  active?: boolean;
};

export type Contribution = {
  node_id: string;
  node_name: string;
  status: string;
  count: number | null;
  k_suppressed?: boolean;
  dp_applied?: boolean;
  latency_ms?: number;
  schema_version?: string;
  error?: string;
};

export type QueryResult = {
  query_id: string;
  status: string;
  aggregate: number | null;
  aggregate_kind?: string;
  completeness_guaranteed: boolean;
  completeness?: number;
  nodes_total?: number;
  nodes_successful?: number;
  nodes_failed?: number;
  contributions: Contribution[];
  privacy: Record<string, unknown>;
  policy?: Record<string, unknown>;
  provenance_id?: string;
  warnings: string[];
  executed_ms?: number;
  created_at: string;
};

export type QueryListItem = {
  id: string;
  query_id: string;
  owner?: string;
  role?: string;
  status?: string;
  created_at?: string;
  executed_ms?: number;
  completeness?: number;
  aggregate?: number | null;
  nodes_successful?: number;
  nodes_total?: number;
  privacy?: Record<string, unknown>;
  conditions?: string[];
  medications?: string[];
  differential_privacy?: boolean;
};

export type QuerySpec = {
  age_min: number;
  age_max: number;
  conditions: string[];
  medications: string[];
  lab_test: string | null;
  lab_op: string;
  lab_value: number | null;
  window_months: number;
  year: number | null;
  differential_privacy: boolean;
  epsilon: number | null;
  delta?: number | null;
  requested_fields?: string[];
};

export type AuditRow = {
  id: number;
  ts: string;
  actor: string;
  role: string;
  action: string;
  query_id?: string;
  detail?: string;
};
