import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../auth";
import { auditLogs } from "../../api/audit";
import { ErrorState, LoadingSkeleton, Page } from "../../components/ui";
import type { AuditRow } from "../../types";

export default function Audit() {
  const { user } = useAuth();
  const [rows, setRows] = useState<AuditRow[] | null>(null);
  const [err, setErr] = useState("");
  const [actor, setActor] = useState("");
  const [action, setAction] = useState("");

  useEffect(() => {
    if (!user) return;
    auditLogs(user.token)
      .then(setRows)
      .catch((e) => setErr(e.message));
  }, [user]);

  const filtered = useMemo(
    () =>
      (rows || []).filter(
        (r) => (!actor || r.actor.includes(actor)) && (!action || r.action.includes(action))
      ),
    [rows, actor, action]
  );

  return (
    <Page title="Audit log" subtitle="Immutable control-plane events. No patient records.">
      {err && <ErrorState message={err} />}
      <div className="flex gap-2 mb-3">
        <input placeholder="Actor" value={actor} onChange={(e) => setActor(e.target.value)} />
        <input placeholder="Action" value={action} onChange={(e) => setAction(e.target.value)} />
      </div>
      {!rows && !err && <LoadingSkeleton />}
      {rows && (
        <div className="card overflow-auto">
          <table className="w-full text-xs">
            <thead className="text-[var(--text-secondary)]">
              <tr>
                <th className="text-left py-1">Time</th>
                <th className="text-left">Actor</th>
                <th className="text-left">Action</th>
                <th className="text-left">Query</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.id} className="border-t border-[var(--border)]">
                  <td className="py-2 font-mono">{r.ts?.slice(0, 19)}</td>
                  <td>
                    {r.actor} ({r.role})
                  </td>
                  <td>{r.action}</td>
                  <td className="font-mono">{r.query_id?.slice(0, 8) || "—"}</td>
                  <td>
                    <Link className="text-[var(--primary)]" to={`/audit/${r.id}`}>
                      Detail
                    </Link>
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
