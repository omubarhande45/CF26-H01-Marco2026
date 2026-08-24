import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "../../auth";
import { institutionDetail } from "../../api/institutions";
import { ErrorState, LoadingSkeleton, Page, StatusBadge } from "../../components/ui";

export default function InstitutionDetail() {
  const { institutionId } = useParams();
  const { user } = useAuth();
  const [d, setD] = useState<Record<string, unknown> | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!user || !institutionId) return;
    institutionDetail(user.token, institutionId)
      .then(setD)
      .catch((e) => setErr(e.message));
  }, [user, institutionId]);

  if (err) return <ErrorState message={err} />;
  if (!d) return <LoadingSkeleton />;
  const priv = (d.privacy || {}) as Record<string, unknown>;

  return (
    <Page title={String(d.name || institutionId)}>
      <div className="card space-y-2 text-sm">
        <StatusBadge status={d.healthy ? "ONLINE" : String(d.status)} />
        <div>Type: {String(d.type)}</div>
        <div>Schema version: {String(d.schema_version ?? "N/A")}</div>
        <div>Canonical model: {String(d.canonical_model_version ?? "N/A")}</div>
        <div>Agent: {String(d.agent_version ?? "N/A")}</div>
        <div>Compatibility: {String(d.schema_compatibility ?? "N/A")}</div>
        <div>
          Privacy: k ≥ {String(priv.minimum_cohort ?? "N/A")} · DP {priv.differential_privacy ? "enabled" : "optional"}
        </div>
        <div>Query types: {JSON.stringify(d.allowed_query_types || [])}</div>
        <p className="text-[var(--text-muted)] text-xs">Patient records are not available through this API.</p>
      </div>
    </Page>
  );
}
