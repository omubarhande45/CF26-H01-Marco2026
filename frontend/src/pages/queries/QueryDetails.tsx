import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useAuth } from "../../auth";
import { cancelQuery, explainQuery, getProvenance, getQuery } from "../../api/queries";
import { ErrorState, LoadingSkeleton, Page, StatusBadge } from "../../components/ui";

const STEPS = ["CREATED", "VALIDATING", "PLANNING", "DISPATCHING", "RUNNING", "AGGREGATING", "PRIVACY_CHECK", "COMPLETED"];

export default function QueryDetails() {
  const { queryId } = useParams();
  const { user } = useAuth();
  const [rec, setRec] = useState<Record<string, unknown> | null>(null);
  const [err, setErr] = useState("");
  const [prov, setProv] = useState<Record<string, unknown> | null>(null);

  function load() {
    if (!user || !queryId) return;
    getQuery(user.token, queryId)
      .then(setRec)
      .catch((e) => setErr(e.message));
    getProvenance(user.token, queryId)
      .then(setProv)
      .catch(() => setProv(null));
    explainQuery(user.token, queryId).catch(() => {});
  }

  useEffect(() => {
    load();
    const id = window.setInterval(() => {
      if (!user || !queryId) return;
      getQuery(user.token, queryId).then((r) => {
        setRec(r);
        const st = String(r.status || "");
        if (["COMPLETED", "COMPLETE", "PARTIAL", "SUPPRESSED", "FAILED", "DENIED", "CANCELLED", "TIMEOUT"].includes(st)) {
          window.clearInterval(id);
        }
      }).catch(() => {});
    }, 1200);
    return () => window.clearInterval(id);
  }, [user, queryId]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!rec) return <LoadingSkeleton rows={6} />;

  const result = (rec.result || {}) as Record<string, unknown>;
  const status = String(result.status || rec.status || "");
  const contribs = (result.contributions || []) as Array<Record<string, unknown>>;
  const life = (rec.lifecycle as string[]) || [];
  const complete = Number(result.completeness ?? 0);
  const privacy = (result.privacy || {}) as Record<string, unknown>;

  return (
    <Page
      title="Query details"
      subtitle={String(queryId)}
      actions={
        user && queryId && !["COMPLETED", "PARTIAL", "SUPPRESSED", "FAILED", "CANCELLED"].includes(String(rec.status)) ? (
          <button className="btn-ghost" onClick={() => cancelQuery(user.token, queryId).then(load)}>
            Cancel
          </button>
        ) : null
      }
    >
      <div className="flex flex-wrap gap-2 mb-4">
        {STEPS.map((s) => {
          const done = life.includes(s) || (s === "COMPLETED" && ["COMPLETED", "PARTIAL", "SUPPRESSED"].includes(String(rec.status)));
          const current = String(rec.status) === s;
          return (
                <span key={s} className={`text-xs ${done || current ? "text-[var(--primary)] font-semibold" : "text-[var(--text-muted)]"}`}>
              {done ? "✓" : current ? "●" : "○"} {s}
            </span>
          );
        })}
      </div>

      <div className="grid md:grid-cols-4 gap-3 mb-4">
        <div className="card">
          <div className="text-xs text-[var(--text-secondary)]">Status</div>
          <StatusBadge status={status} />
        </div>
        <div className="card">
          <div className="text-xs text-[var(--text-secondary)]">Completeness</div>
          <div className="text-xl font-semibold">{String(result.completeness ?? "N/A")}%</div>
        </div>
        <div className="card">
          <div className="text-xs text-[var(--text-secondary)]">Institutions</div>
          <div className="text-xl font-semibold">
            {String(result.nodes_successful ?? "—")} / {String(result.nodes_total ?? "—")}
          </div>
        </div>
        <div className="card">
          <div className="text-xs text-[var(--text-secondary)]">Execution</div>
          <div className="text-xl font-semibold">{String(result.executed_ms ?? rec.executed_ms ?? "N/A")} ms</div>
        </div>
      </div>

      {status.toUpperCase() === "PARTIAL" && (
        <div className="card mb-4 text-sm bg-[var(--warning-soft)] border-[var(--warning)]/30">
          <strong>Partial federation result.</strong> {String(result.nodes_successful ?? "—")} of {String(result.nodes_total ?? "—")} institutions responded.
          Completeness {complete}%. This result is incomplete and must not be interpreted as a full federation result.
        </div>
      )}
      {status.toUpperCase() === "SUPPRESSED" && (
        <div className="card border-fuchsia-500/30 mb-4 text-sm">
          Result suppressed. The eligible cohort is below the configured privacy threshold (k=10).
        </div>
      )}

      <div className="card mb-4">
        <div className="text-xs text-[var(--text-secondary)]">Eligible federated cohort</div>
        <div className="text-[32px] font-bold tabular-nums">{String(result.aggregate ?? "—")}</div>
        {privacy.differential_privacy ? (
          <p className="text-xs text-[var(--primary)] mt-2">Differential privacy applied · ε = {String(privacy.epsilon ?? "—")}</p>
        ) : null}
      </div>

      <div className="grid md:grid-cols-3 gap-3 mb-4">
        {contribs.map((c) => (
          <div key={String(c.node_id)} className="card text-sm">
            <div className="flex justify-between">
              <strong>{String(c.node_name)}</strong>
              <StatusBadge status={c.k_suppressed ? "SUPPRESSED" : String(c.status)} />
            </div>
            <div className="mt-2 font-mono text-xs">
              count {String(c.count ?? "—")} · {String(c.latency_ms ?? "—")} ms · schema {String(c.schema_version ?? "—")}
            </div>
          </div>
        ))}
      </div>

      {contribs.length > 0 && (
        <div className="card h-48 mb-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={contribs.map((c) => ({ name: String(c.node_name).replace("Diagnostic Laboratory", "Lab"), count: c.status === "OK" && !c.k_suppressed ? Number(c.count || 0) : 0 }))}>
              <CartesianGrid stroke="#EEF1F5" vertical={false} />
              <XAxis dataKey="name" stroke="#667085" fontSize={12} />
              <YAxis stroke="#667085" fontSize={12} />
              <Tooltip contentStyle={{ background: "#fff", border: "1px solid #E4E7EC" }} />
              <Bar dataKey="count" fill="#2563EB" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <h2 className="font-medium mb-2">Provenance / events</h2>
      <ol className="text-sm text-[var(--text-secondary)] space-y-1 mb-4">
        {((rec.events as string[]) || []).map((e) => (
          <li key={e}>↓ {e}</li>
        ))}
      </ol>
      {prov && (
        <pre className="card text-[11px] overflow-auto max-h-64 text-[var(--text-secondary)]">{JSON.stringify(prov, null, 2)}</pre>
      )}
    </Page>
  );
}
