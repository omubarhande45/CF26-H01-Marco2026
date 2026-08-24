import { useEffect, useState } from "react";
import { useAuth } from "../../auth";
import { topology } from "../../api/federation";
import { ErrorState, LoadingSkeleton, Page, StatusBadge } from "../../components/ui";
import type { NodeInfo } from "../../types";

export default function Federation() {
  const { user } = useAuth();
  const [nodes, setNodes] = useState<NodeInfo[] | null>(null);
  const [err, setErr] = useState("");

  function load() {
    if (!user) return;
    topology(user.token)
      .then((t) => setNodes(t.nodes))
      .catch((e) => setErr(e.message));
  }
  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, [user]);

  return (
    <Page title="Federation monitor" subtitle="All connected institutions" actions={<button className="btn-ghost" onClick={load}>Refresh</button>}>
      {err && <ErrorState message={err} onRetry={load} />}
      {!nodes && !err && <LoadingSkeleton />}
      <div className="card mb-5">
        <svg viewBox="0 0 640 200" className="w-full h-44" role="img" aria-label="Federation topology">
          <text x="320" y="28" textAnchor="middle" fill="#667085" fontSize="12">Coordinator</text>
          <circle cx="320" cy="48" r="10" fill="#2563EB" />
          {(nodes || []).map((n, i) => {
            const count = (nodes || []).length;
            const x = count <= 1 ? 320 : 80 + (i * 480) / (count - 1);
            return (
              <g key={n.node_id}>
                <line x1="320" y1="58" x2={x} y2="120" stroke="#E4E7EC" />
                <circle cx={x} cy="132" r="9" fill={n.healthy ? "#16A34A" : "#DC2626"} />
                <text x={x} y="162" textAnchor="middle" fill="#172033" fontSize="11">{n.name.replace("Diagnostic Laboratory", "Lab")}</text>
                <text x={x} y="178" textAnchor="middle" fill="#667085" fontSize="10">{n.healthy ? "ONLINE" : n.status || "OFFLINE"}</text>
              </g>
            );
          })}
        </svg>
      </div>
      <div className="grid md:grid-cols-3 gap-3">
        {(nodes || []).map((n) => (
          <div key={n.node_id} className="card text-sm space-y-1.5">
            <div className="flex justify-between items-start">
              <h3 className="font-semibold">{n.name}</h3>
              <StatusBadge status={n.healthy ? "ONLINE" : n.status} />
            </div>
            <div className="flex justify-between text-[var(--text-secondary)]"><span>Latency</span><span>{n.latency_ms ?? "N/A"} ms</span></div>
            <div className="flex justify-between text-[var(--text-secondary)]"><span>Schema</span><span>{n.schema_version ?? "N/A"}</span></div>
            <div className="flex justify-between text-[var(--text-secondary)]"><span>Compatibility</span><span>{n.schema_compatibility ?? "N/A"}</span></div>
          </div>
        ))}
      </div>
    </Page>
  );
}
