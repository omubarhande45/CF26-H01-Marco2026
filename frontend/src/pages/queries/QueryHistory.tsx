import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth";
import { listQueries } from "../../api/queries";
import { ErrorState, LoadingSkeleton, Page, StatusBadge } from "../../components/ui";
import type { QueryListItem } from "../../types";

export default function QueryHistory() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [rows, setRows] = useState<QueryListItem[] | null>(null);
  const [err, setErr] = useState("");
  const [status, setStatus] = useState("");
  const [priv, setPriv] = useState("");

  function load() {
    if (!user) return;
    listQueries(user.token)
      .then(setRows)
      .catch((e) => setErr(e.message));
  }
  useEffect(load, [user]);

  const filtered = useMemo(() => {
    return (rows || []).filter((r) => {
      if (status && String(r.status) !== status) return false;
      if (priv === "dp" && !r.differential_privacy) return false;
      if (priv === "k" && r.differential_privacy) return false;
      return true;
    });
  }, [rows, status, priv]);

  return (
    <Page title="Query history">
      <div className="flex flex-wrap gap-2 mb-4">
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {["CREATED", "RUNNING", "COMPLETED", "PARTIAL", "SUPPRESSED", "DENIED", "FAILED", "CANCELLED"].map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
        <select value={priv} onChange={(e) => setPriv(e.target.value)}>
          <option value="">All privacy modes</option>
          <option value="dp">Differential privacy</option>
          <option value="k">k-anonymity only</option>
        </select>
      </div>
      {err && <ErrorState message={err} onRetry={load} />}
      {!rows && !err && <LoadingSkeleton />}
      {rows && !filtered.length && <p className="text-sm text-[var(--text-secondary)]">No data available.</p>}
      {filtered.length > 0 && (
        <div className="card overflow-auto">
          <table className="w-full text-sm">
            <thead className="text-xs text-[var(--text-secondary)]">
              <tr>
                <th className="text-left">Query ID</th>
                <th className="text-left">Type</th>
                <th>Status</th>
                <th>Completeness</th>
                <th>Privacy</th>
                <th>Duration</th>
                <th>Timestamp</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filtered.map((q) => (
                <tr key={q.id} className="border-t border-[var(--border)]">
                  <td className="py-2 font-mono">{(q.query_id || q.id || "—").toString().slice(0, 8)}</td>
                  <td>{(q.conditions || []).join(", ") || "count"}</td>
                  <td className="text-center">
                    <StatusBadge status={q.status} />
                  </td>
                  <td className="text-center font-mono">{q.completeness ?? "—"}</td>
                  <td className="text-center">{q.differential_privacy ? "DP" : "k"}</td>
                  <td className="text-center font-mono">{q.executed_ms ?? "—"}</td>
                  <td className="text-xs">{q.created_at?.slice(0, 19)}</td>
                  <td className="space-x-2">
                    <Link className="text-[var(--primary)] text-xs" to={`/query/${q.id}`}>
                      View
                    </Link>
                    <button className="text-xs text-[var(--text-secondary)]" onClick={() => nav("/query-builder")}>
                      Duplicate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Page>
  );
}
