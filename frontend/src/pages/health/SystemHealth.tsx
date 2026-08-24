import { useEffect, useState } from "react";
import { useAuth } from "../../auth";
import { gatewayHealth, listNodes } from "../../api/federation";
import { Page, StatusBadge } from "../../components/ui";

export default function SystemHealth() {
  const { user } = useAuth();
  const [rows, setRows] = useState<Array<{ name: string; status: string; extra?: string }>>([]);

  async function load() {
    const gw = await gatewayHealth().catch(() => null);
    const nodes = user ? await listNodes(user.token).catch(() => []) : [];
    setRows([
      { name: "Gateway / coordinator", status: gw ? "Healthy" : "Offline", extra: gw?.version },
      { name: "Authentication", status: user ? "Healthy" : "Offline" },
      { name: "Policy engine", status: gw ? "Healthy" : "Offline" },
      { name: "Audit", status: gw ? "Healthy" : "Degraded" },
      ...nodes.map((n) => ({
        name: n.name,
        status: n.healthy ? "Healthy" : n.status || "Offline",
        extra: `${n.latency_ms ?? "?"} ms · ${n.schema_version ?? ""}`,
      })),
    ]);
  }

  useEffect(() => {
    load();
  }, [user]);

  return (
    <Page title="System health" actions={<button className="btn-ghost" onClick={load}>Retry</button>}>
      <div className="space-y-2">
        {rows.map((r) => (
          <div key={r.name} className="card flex justify-between text-sm">
            <span>{r.name}</span>
            <span>
              <StatusBadge status={r.status} /> <span className="text-[var(--text-muted)] text-xs">{r.extra}</span>
            </span>
          </div>
        ))}
      </div>
    </Page>
  );
}
