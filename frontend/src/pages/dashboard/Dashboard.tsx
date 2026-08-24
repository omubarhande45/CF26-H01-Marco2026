import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import {
  Activity,
  AlertTriangle,
  Building2,
  CheckCircle2,
  Clock,
  FileSearch,
  FlaskConical,
  GitBranch,
  Plus,
  RefreshCw,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { useAuth } from "../../auth";
import { stats } from "../../api/federation";
import { listQueries } from "../../api/queries";
import { catalogInstitutions } from "../../api/catalog";
import { privacyBudget } from "../../api/privacy";
import { ErrorState, LoadingSkeleton, StatusBadge } from "../../components/ui";
import type { NodeInfo, QueryListItem } from "../../types";

function relTime(iso?: string) {
  if (!iso) return "—";
  const ms = Date.now() - new Date(iso).getTime();
  if (ms < 60_000) return "Just now";
  if (ms < 3600_000) return `${Math.floor(ms / 60_000)}m ago`;
  if (ms < 86400_000) return `${Math.floor(ms / 3600_000)}h ago`;
  return `${Math.floor(ms / 86400_000)}d ago`;
}

function nodeIcon(name: string) {
  if (/lab/i.test(name)) return FlaskConical;
  return Building2;
}

export default function Dashboard() {
  const { user } = useAuth();
  const [s, setS] = useState<Awaited<ReturnType<typeof stats>> | null>(null);
  const [qs, setQs] = useState<QueryListItem[]>([]);
  const [instCount, setInstCount] = useState<number | null>(null);
  const [budgetRem, setBudgetRem] = useState<number | null>(null);
  const [err, setErr] = useState("");
  const [updated, setUpdated] = useState<Date | null>(null);
  const hour = new Date().getHours();
  const greet = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  function load() {
    const token = user?.token;
    if (!token) {
      setErr("Your session has no access token. Sign out and sign in again.");
      return;
    }
    setErr("");
    Promise.all([
      stats(token),
      listQueries(token).catch(() => [] as QueryListItem[]),
      catalogInstitutions(token).catch(() => []),
      privacyBudget(token).catch(() => null),
    ])
      .then(([st, queries, insts, bud]) => {
        setS(st);
        setQs(queries);
        setInstCount(insts.length || st.active_institutions);
        if (bud) {
          const vals = Object.values(bud.remaining || {});
          const rem = vals.length ? vals.reduce((a, b) => a + b, 0) / (vals.length * (bud.default || 8)) : 1;
          setBudgetRem(Math.max(0, Math.min(100, Math.round(rem * 100))));
        } else {
          setBudgetRem(st.privacy_budget_used_pct != null ? Math.max(0, 100 - st.privacy_budget_used_pct) : null);
        }
        setUpdated(new Date());
      })
      .catch((e) => {
        const msg = e instanceof Error ? e.message : "Unable to load data";
        if (/missing token|invalid token|401/i.test(msg)) {
          setErr("Session expired. Sign out and sign in again.");
        } else {
          setErr(msg);
        }
      });
  }

  useEffect(load, [user]);

  const remaining = budgetRem ?? (s ? Math.max(0, 100 - (s.privacy_budget_used_pct || 0)) : null);
  const used = remaining != null ? 100 - remaining : null;
  const pie = useMemo(
    () => [
      { name: "Used", value: used ?? 0 },
      { name: "Remaining", value: remaining ?? 100 },
    ],
    [used, remaining]
  );

  const totalQ = s ? Math.max(1, s.queries_total || 1) : 1;

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-[26px] font-bold tracking-tight">
            {greet}, {user?.role === "auditor" ? "Auditor" : "Researcher"}{" "}
            <span aria-hidden>👋</span>
          </h1>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">
            Federated analytics overview across connected institutions.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
          Last updated: {updated ? updated.toLocaleTimeString() : "—"}
          <button className="btn-ghost h-9 w-9 p-0" onClick={load} aria-label="Refresh">
            <RefreshCw size={15} />
          </button>
        </div>
      </div>

      {err && <ErrorState message={err} onRetry={load} />}
      {!s && !err && <LoadingSkeleton rows={6} />}

      {s && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-8 gap-3">
            <MiniKpi
              label="Active Institutions"
              value={instCount ?? s.active_institutions}
              hint="Source organizations"
              icon={<Building2 size={16} className="text-[var(--primary)]" />}
            />
            <MiniKpi
              label="Online Nodes"
              value={`${s.online_nodes} / ${s.nodes_total}`}
              hint={s.online_nodes === s.nodes_total ? "100% online" : "Some offline"}
              icon={<GitBranch size={16} className="text-emerald-600" />}
            />
            <MiniKpi
              label="Queries Today"
              value={s.queries_today}
              hint={`${s.queries_total} total`}
              icon={<Search size={16} className="text-[var(--primary)]" />}
            />
            <MiniKpi
              label="Complete Queries"
              value={s.complete_queries}
              hint={`${Math.round((s.complete_queries / totalQ) * 100)}%`}
              icon={<CheckCircle2 size={16} className="text-emerald-600" />}
            />
            <MiniKpi
              label="Partial Queries"
              value={s.partial_queries}
              hint={`${Math.round((s.partial_queries / totalQ) * 100)}%`}
              icon={<AlertTriangle size={16} className="text-amber-600" />}
            />
            <MiniKpi
              label="Suppressed Results"
              value={s.suppressed_results}
              hint="k-anonymity"
              icon={<ShieldAlert size={16} className="text-rose-500" />}
            />
            <MiniKpi
              label="Avg. Query Time"
              value={s.average_query_ms != null ? s.average_query_ms : "N/A"}
              hint={s.average_query_ms != null ? "ms" : "No runs yet"}
              icon={<Clock size={16} className="text-sky-600" />}
            />
            <MiniKpi
              label="Privacy Budget"
              value={remaining != null ? `${remaining}%` : "N/A"}
              hint="Remaining"
              icon={<Shield size={16} className="text-[var(--primary)]" />}
            />
          </div>

          <section className="card mt-5">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2>Federation Health</h2>
                <p className="text-xs text-[var(--text-secondary)]">All connected institutions</p>
              </div>
              <Link to="/institutions" className="text-xs font-semibold text-[var(--primary)]">
                View all institutions
              </Link>
            </div>
            <div className="grid md:grid-cols-3 gap-3">
              {s.nodes.map((n: NodeInfo) => {
                const Icon = nodeIcon(n.name);
                return (
                  <Link
                    key={n.node_id}
                    to={
                      n.node_id === "hospital_a"
                        ? "/hospital-a"
                        : n.node_id === "hospital_b"
                          ? "/hospital-b"
                          : `/institutions/${n.node_id}`
                    }
                    className="rounded-xl border border-[var(--border)] p-4 block hover:border-[#2563EB]/40"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--primary-soft)] text-[var(--primary)]">
                          <Icon size={16} />
                        </span>
                        <div>
                          <div className="text-[13px] font-semibold">{n.name.replace("Diagnostic Laboratory", "Diagnostic Lab")}</div>
                        </div>
                      </div>
                      <StatusBadge status={n.healthy ? "ONLINE" : n.status || "OFFLINE"} />
                    </div>
                    <dl className="mt-4 space-y-2 text-[13px] text-[var(--text-secondary)]">
                      <div className="flex justify-between border-t border-[var(--border-light)] pt-2">
                        <dt>Schema Version</dt>
                        <dd className="font-medium text-[var(--text-primary)]">{n.schema_version ?? "N/A"}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt>Latency</dt>
                        <dd>
                          <span className="rounded-full bg-[var(--success-soft)] px-2 py-0.5 text-[11px] font-semibold text-[var(--success)]">
                            {n.latency_ms ?? "N/A"} ms
                          </span>
                        </dd>
                      </div>
                      <div className="flex justify-between">
                        <dt>Last Query</dt>
                        <dd className="font-medium text-[var(--text-primary)]">{qs[0] ? relTime(qs[0].created_at) : "—"}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt>Agent</dt>
                        <dd className="font-medium text-[var(--text-primary)]">{n.healthy ? "Reachable" : "Offline"}</dd>
                      </div>
                    </dl>
                  </Link>
                );
              })}
            </div>
          </section>

          <div className="mt-5 grid lg:grid-cols-5 gap-4">
            <section className="card lg:col-span-3 !p-0 overflow-hidden">
              <div className="flex items-center justify-between px-5 pt-4 pb-2">
                <h2>Recent Queries</h2>
                <Link to="/query-history" className="text-xs font-semibold text-[var(--primary)]">
                  View all
                </Link>
              </div>
              {!qs.length ? (
                <p className="px-5 pb-5 text-sm text-[var(--text-secondary)]">No queries yet. Create a federated query to populate this table.</p>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Query ID</th>
                      <th>Status</th>
                      <th>Institutions</th>
                      <th>Result</th>
                      <th>Duration</th>
                      <th>Time</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {qs.slice(0, 5).map((q) => (
                      <tr key={q.id}>
                        <td className="font-mono text-xs">{q.query_id?.slice(0, 8)}</td>
                        <td>
                          <StatusBadge status={q.status} />
                        </td>
                        <td>
                          {q.nodes_successful ?? "—"} / {q.nodes_total ?? "—"}
                        </td>
                        <td className="font-mono">{q.aggregate ?? "—"}</td>
                        <td className="font-mono">{q.executed_ms != null ? `${Math.round(q.executed_ms)} ms` : "—"}</td>
                        <td className="text-[var(--text-secondary)]">{relTime(q.created_at)}</td>
                        <td>
                          <Link to={`/query/${q.id}`} className="text-[var(--text-muted)]">
                            ›
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>

            <section className="card lg:col-span-2">
              <h2 className="mb-3">Privacy & System Overview</h2>
              <div className="flex gap-3">
                <ul className="flex-1 space-y-3 text-[13px]">
                  <li className="flex gap-2">
                    <ShieldCheck size={16} className="mt-0.5 text-emerald-600" />
                    <div>
                      <div className="font-medium">k-Anonymity Threshold</div>
                      <div className="text-[var(--text-secondary)]">k = 10 · Enforced across all nodes</div>
                    </div>
                  </li>
                  <li className="flex gap-2">
                    <Shield size={16} className="mt-0.5 text-[var(--primary)]" />
                    <div>
                      <div className="font-medium">Differential Privacy</div>
                      <div className="text-[var(--text-secondary)]">Optional on aggregates · ε configurable</div>
                    </div>
                  </li>
                  <li className="flex gap-2">
                    <Activity size={16} className="mt-0.5 text-violet-600" />
                    <div>
                      <div className="font-medium">Privacy Budget</div>
                      <div className="text-[var(--text-secondary)]">
                        {remaining != null ? `${remaining}% remaining` : "N/A"}
                      </div>
                    </div>
                  </li>
                </ul>
                <div className="relative h-32 w-32 shrink-0">
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie data={pie} dataKey="value" innerRadius={38} outerRadius={56} stroke="none">
                        <Cell fill="#BFDBFE" />
                        <Cell fill="#2563EB" />
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                    <div className="text-lg font-bold">{remaining ?? "—"}%</div>
                    <div className="text-[10px] text-[var(--text-muted)]">Remaining</div>
                  </div>
                </div>
              </div>
            </section>
          </div>

          <section className="mt-5">
            <h2 className="mb-3">Quick Actions</h2>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <Quick to="/analytics" icon={<Activity size={16} />} title="Disease analytics" sub="Trends across hospitals" />
              <Quick to="/query-builder" icon={<Plus size={16} />} title="Create New Query" sub="Build a federated query" />
              <Quick to="/federation" icon={<GitBranch size={16} />} title="Federation Monitor" sub="View node status" />
              <Quick to="/privacy" icon={<ShieldCheck size={16} />} title="Privacy Center" sub="Privacy settings & budget" />
              <Quick to="/audit" icon={<FileSearch size={16} />} title="Audit Log" sub="View audit events" />
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function MiniKpi({
  label,
  value,
  hint,
  icon,
}: {
  label: string;
  value: string | number;
  hint?: string;
  icon: ReactNode;
}) {
  return (
    <div className="card !p-3">
      <div className="text-[10px] font-semibold uppercase tracking-wide text-[var(--text-secondary)]">{label}</div>
      <div className="mt-2 flex items-end justify-between gap-1">
        <div className="text-[22px] font-bold tabular-nums leading-none">{value}</div>
        {icon}
      </div>
      {hint && <div className="mt-2 text-[11px] text-[var(--text-muted)]">{hint}</div>}
    </div>
  );
}

function Quick({ to, icon, title, sub }: { to: string; icon: React.ReactNode; title: string; sub: string }) {
  return (
    <Link to={to} className="card flex items-start gap-3 !p-4 hover:-translate-y-px">
      <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--primary-soft)] text-[var(--primary)]">
        {icon}
      </span>
      <span>
        <span className="block text-sm font-semibold">{title}</span>
        <span className="block text-xs text-[var(--text-secondary)]">{sub}</span>
      </span>
    </Link>
  );
}
