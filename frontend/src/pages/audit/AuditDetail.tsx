import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "../../auth";
import { auditDetail } from "../../api/audit";
import { ErrorState, LoadingSkeleton, Page } from "../../components/ui";
import type { AuditRow } from "../../types";

export default function AuditDetail() {
  const { eventId } = useParams();
  const { user } = useAuth();
  const [row, setRow] = useState<AuditRow | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!user || !eventId) return;
    auditDetail(user.token, Number(eventId))
      .then(setRow)
      .catch((e) => setErr(e.message));
  }, [user, eventId]);

  if (err) return <ErrorState message={err} />;
  if (!row) return <LoadingSkeleton />;
  return (
    <Page title={`Audit event ${row.id}`}>
      <dl className="card text-sm grid gap-2">
        <div>Timestamp: {row.ts}</div>
        <div>
          Actor: {row.actor} / {row.role}
        </div>
        <div>Query: {row.query_id || "—"}</div>
        <div>Action: {row.action}</div>
        <div className="text-[var(--text-secondary)] break-all">Detail: {row.detail}</div>
      </dl>
    </Page>
  );
}
