import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../auth";
import { catalogInstitutions, type CatalogInstitution } from "../../api/catalog";
import { ErrorState, LoadingSkeleton, Page, StatusBadge } from "../../components/ui";

export default function Institutions() {
  const { user } = useAuth();
  const [rows, setRows] = useState<CatalogInstitution[] | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!user) return;
    catalogInstitutions(user.token)
      .then(setRows)
      .catch((e) => setErr(e.message));
  }, [user]);

  return (
    <Page title="Institutions" subtitle="12 source healthcare organizations. Data stays on the assigned federation agent.">
      {err && <ErrorState message={err} />}
      {!rows && !err && <LoadingSkeleton />}
      <div className="grid md:grid-cols-3 gap-3">
        {(rows || []).map((c) => (
          <Link key={c.institution_id} to={`/institutions/${c.institution_id}`} className="card block">
            <div className="flex justify-between items-start">
              <h3 className="font-semibold text-sm">{c.institution_name}</h3>
              <StatusBadge status="LOCAL" />
            </div>
            <p className="text-sm text-[var(--text-secondary)] mt-2">{c.institution_type} · {c.location}</p>
            <p className="text-xs text-[var(--text-muted)] mt-1">Agent {c.node_id || "unassigned"} · {c.institution_id}</p>
          </Link>
        ))}
      </div>
    </Page>
  );
}
