import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, Building2, Lock, MapPin, Shield, Stethoscope } from "lucide-react";
import { useAuth } from "../../auth";
import { institutionDetail } from "../../api/institutions";
import { catalogInstitutions, type CatalogInstitution } from "../../api/catalog";
import { listQueries } from "../../api/queries";
import { analyticsNode } from "../../api/analytics";
import { ErrorState, LoadingSkeleton, StatusBadge } from "../../components/ui";
import type { QueryListItem } from "../../types";

export const HOSPITALS: Record<
  string,
  { title: string; node: string; cluster: string; fallbackSites: number }
> = {
  hospital_a: {
    title: "Hospital A",
    node: "hospital_a",
    cluster: "Maharashtra cluster · Pune / Nashik / Aurangabad / Bengaluru / Jaipur / Indore",
    fallbackSites: 6,
  },
  hospital_b: {
    title: "Hospital B",
    node: "hospital_b",
    cluster: "Metro research cluster · Mumbai / Delhi / Ahmedabad",
    fallbackSites: 3,
  },
};

export default function HospitalNode({ nodeId }: { nodeId: "hospital_a" | "hospital_b" }) {
  const meta = HOSPITALS[nodeId];
  const { user } = useAuth();
  const [d, setD] = useState<Record<string, unknown> | null>(null);
  const [sites, setSites] = useState<CatalogInstitution[]>([]);
  const [qs, setQs] = useState<QueryListItem[]>([]);
  const [top, setTop] = useState<Array<{ disease_name: string; icd10_code?: string; count: number }>>([]);
  const [err, setErr] = useState("");

  function load() {
    if (!user) return;
    setErr("");
    Promise.all([
      institutionDetail(user.token, meta.node),
      catalogInstitutions(user.token).catch(() => [] as CatalogInstitution[]),
      listQueries(user.token).catch(() => [] as QueryListItem[]),
    ])
      .then(([detail, insts, queries]) => {
        setD(detail);
        setSites(insts.filter((i) => i.node_id === meta.node));
        setQs(queries.slice(0, 6));
      })
      .catch((e) => setErr(e instanceof Error ? e.message : `Unable to load ${meta.title}`));
  }

  useEffect(load, [user, nodeId]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!d) return <LoadingSkeleton rows={8} />;

  const priv = (d.privacy || {}) as Record<string, unknown>;
  const types = (d.allowed_query_types as string[]) || [];
  const other = nodeId === "hospital_a" ? { to: "/hospital-b", label: "Hospital B" } : { to: "/hospital-a", label: "Hospital A" };

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#EEF4FF] text-[#2563EB]">
            <Building2 size={22} />
          </span>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-[26px] font-bold tracking-tight">{meta.title}</h1>
              <StatusBadge status={d.healthy ? "ONLINE" : String(d.status || "OFFLINE")} />
            </div>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">
              Federation agent · {meta.node} · {meta.cluster}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to={other.to} className="btn-ghost">
            Open {other.label}
          </Link>
          <Link to="/query-builder" className="btn-primary">
            Query this node
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <Kpi label="Agent status" value={d.healthy ? "Reachable" : "Offline"} hint={String(d.status || "")} />
        <Kpi label="Schema" value={String(d.schema_version ?? "N/A")} hint={`Canonical ${String(d.canonical_model_version ?? "1.0")}`} />
        <Kpi label="Latency" value={d.latency_ms != null ? `${d.latency_ms}` : "N/A"} hint="ms last probe" />
        <Kpi label="k-anonymity" value={`k ≥ ${String(priv.minimum_cohort ?? 10)}`} hint="Local suppression" />
        <Kpi label="Source sites" value={sites.length || meta.fallbackSites} hint="Institutions on this agent" />
      </div>

      <div className="mt-5 grid lg:grid-cols-5 gap-4">
        <section className="card lg:col-span-3 !p-0 overflow-hidden">
          <div className="px-5 pt-4 pb-2">
            <h2>Source institutions</h2>
            <p className="text-xs text-[var(--text-secondary)]">
              Records stay on {meta.title}. Only counts leave the node.
            </p>
          </div>
          {!sites.length ? (
            <p className="px-5 pb-5 text-sm text-[var(--text-secondary)]">Catalog not loaded.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Location</th>
                </tr>
              </thead>
              <tbody>
                {sites.map((s) => (
                  <tr key={s.institution_id}>
                    <td className="font-mono text-xs">
                      <Link className="text-[var(--primary)]" to={`/institutions/${s.institution_id}`}>
                        {s.institution_id}
                      </Link>
                    </td>
                    <td>{s.institution_name}</td>
                    <td>{s.institution_type}</td>
                    <td className="text-[var(--text-secondary)]">
                      <span className="inline-flex items-center gap-1">
                        <MapPin size={12} /> {s.location}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="card lg:col-span-2 space-y-4">
          <h2>Node policy</h2>
          <ul className="space-y-3 text-[13px]">
            <li className="flex gap-2">
              <Shield size={16} className="mt-0.5 text-[#2563EB]" />
              <div>
                <div className="font-medium">k-anonymity</div>
                <div className="text-[var(--text-secondary)]">
                  Cohorts below k = {String(priv.minimum_cohort ?? 10)} are suppressed
                </div>
              </div>
            </li>
            <li className="flex gap-2">
              <Lock size={16} className="mt-0.5 text-emerald-600" />
              <div>
                <div className="font-medium">No patient export</div>
                <div className="text-[var(--text-secondary)]">IDs, names, and rows are never returned</div>
              </div>
            </li>
            <li className="flex gap-2">
              <Stethoscope size={16} className="mt-0.5 text-violet-600" />
              <div>
                <div className="font-medium">Allowed queries</div>
                <div className="text-[var(--text-secondary)]">{types.length ? types.join(", ") : "aggregate_count"}</div>
              </div>
            </li>
            <li className="flex gap-2">
              <Activity size={16} className="mt-0.5 text-sky-600" />
              <div>
                <div className="font-medium">Compatibility</div>
                <div className="text-[var(--text-secondary)]">
                  {String(d.schema_compatibility ?? "N/A")} · agent {String(d.agent_version ?? "1.0")}
                </div>
              </div>
            </li>
          </ul>
        </section>
      </div>

      {top.length > 0 && (
        <section className="card mt-5 !p-0 overflow-hidden">
          <div className="px-5 pt-4 pb-2">
            <h2>Top local disease aggregates</h2>
            <p className="text-xs text-[var(--text-secondary)]">k-safe counts computed on this node only</p>
          </div>
          <table>
            <thead>
              <tr>
                <th>Disease</th>
                <th>ICD-10</th>
                <th>Count</th>
              </tr>
            </thead>
            <tbody>
              {top.map((t) => (
                <tr key={t.disease_name}>
                  <td>{t.disease_name}</td>
                  <td className="font-mono text-xs">{t.icd10_code || "—"}</td>
                  <td className="font-mono">{t.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <section className="card mt-5 !p-0 overflow-hidden">
        <div className="flex items-center justify-between px-5 pt-4 pb-2">
          <h2>Recent federated queries</h2>
          <Link to="/query-history" className="text-xs font-semibold text-[var(--primary)]">
            View all
          </Link>
        </div>
        {!qs.length ? (
          <p className="px-5 pb-5 text-sm text-[var(--text-secondary)]">No queries yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Query</th>
                <th>Status</th>
                <th>Result</th>
                <th>Nodes</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {qs.map((q) => (
                <tr key={q.id}>
                  <td className="font-mono text-xs">{(q.query_id || q.id).slice(0, 8)}</td>
                  <td>
                    <StatusBadge status={q.status} />
                  </td>
                  <td className="font-mono">{q.aggregate ?? "—"}</td>
                  <td>
                    {q.nodes_successful ?? "—"} / {q.nodes_total ?? "—"}
                  </td>
                  <td>
                    <Link to={`/query/${q.id}`} className="text-[var(--primary)] text-xs">
                      Open
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

function Kpi({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="card !p-3">
      <div className="text-[10px] font-semibold uppercase tracking-wide text-[var(--text-secondary)]">{label}</div>
      <div className="mt-2 text-[20px] font-bold tabular-nums leading-none">{value}</div>
      {hint && <div className="mt-2 text-[11px] text-[var(--text-muted)]">{hint}</div>}
    </div>
  );
}

export function HospitalA() {
  return <HospitalNode nodeId="hospital_a" />;
}

export function HospitalB() {
  return <HospitalNode nodeId="hospital_b" />;
}
