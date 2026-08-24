import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../auth";
import { listQueries, getProvenance } from "../../api/queries";
import { Page } from "../../components/ui";

export default function Provenance() {
  const { user } = useAuth();
  const [items, setItems] = useState<Array<{ id: string; prov: Record<string, unknown> | null }>>([]);

  useEffect(() => {
    if (!user) return;
    listQueries(user.token).then(async (qs) => {
      const out = [];
      for (const q of qs.slice(0, 8)) {
        const prov = await getProvenance(user.token, q.id).catch(() => null);
        out.push({ id: q.id, prov });
      }
      setItems(out);
    });
  }, [user]);

  return (
    <Page title="Provenance" subtitle="Query → canonical model → nodes → aggregation → privacy → result">
      {items.length === 0 && <p className="text-sm text-[var(--text-secondary)]">No data available.</p>}
      <div className="space-y-3">
        {items.map((i) => (
          <div key={i.id} className="card text-sm">
            <Link className="text-[var(--primary)] font-mono" to={`/query/${i.id}`}>
              {i.id.slice(0, 8)}
            </Link>
            <div className="text-[var(--text-secondary)] mt-1">
              digest {String(i.prov?.digest || i.prov?.result_digest || "N/A")} · status {String(i.prov?.status || "N/A")}
            </div>
          </div>
        ))}
      </div>
    </Page>
  );
}
