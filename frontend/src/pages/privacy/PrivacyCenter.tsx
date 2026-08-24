import { useEffect, useState } from "react";
import { useAuth } from "../../auth";
import { privacyBudget } from "../../api/privacy";
import { listQueries } from "../../api/queries";
import { ErrorState, Page } from "../../components/ui";

export default function PrivacyCenter() {
  const { user } = useAuth();
  const [b, setB] = useState<Awaited<ReturnType<typeof privacyBudget>> | null>(null);
  const [sup, setSup] = useState(0);
  const [dpn, setDpn] = useState(0);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!user) return;
    privacyBudget(user.token)
      .then(setB)
      .catch((e) => setErr(e.message));
    listQueries(user.token)
      .then((qs) => {
        setSup(qs.filter((q) => q.status === "SUPPRESSED").length);
        setDpn(qs.filter((q) => q.differential_privacy).length);
      })
      .catch(() => {});
  }, [user]);

  const remaining = b ? Object.values(b.remaining) : [];
  const rem = remaining.length ? remaining.reduce((a, c) => a + c, 0) / remaining.length : b?.default;

  return (
    <Page title="Privacy center" subtitle="Enforcement is server-side. This page is read-only.">
      {err && <ErrorState message={err} />}
      <div className="grid md:grid-cols-3 gap-3 mb-6">
        <div className="card">
          <div className="text-xs text-[var(--text-secondary)]">k-anonymity</div>
          <div className="text-2xl font-semibold">10</div>
        </div>
        <div className="card">
          <div className="text-xs text-[var(--text-secondary)]">Remaining ε (avg)</div>
          <div className="text-2xl font-semibold">{rem ?? "N/A"}</div>
        </div>
        <div className="card">
          <div className="text-xs text-[var(--text-secondary)]">Default budget</div>
          <div className="text-2xl font-semibold">{b?.default ?? "N/A"}</div>
        </div>
      </div>
      <div className="card mb-6">
        <h2 className="mb-3">Privacy protection</h2>
        <ul className="text-sm space-y-1 text-[var(--text-secondary)]">
          <li>✓ Raw records remain local</li>
          <li>✓ k-anonymity enforced</li>
          <li>✓ Differential privacy available</li>
          <li>✓ Privacy budget monitored</li>
        </ul>
        <div className="mt-4 text-sm leading-7 text-center text-[var(--text-secondary)]">
          Local records → Local aggregate → k ≥ 10 → Differential privacy → Federated result
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-3 text-sm">
        <div className="card">Suppressed queries: {sup}</div>
        <div className="card">DP queries: {dpn}</div>
      </div>
      <p className="mt-4 text-sm text-[var(--text-secondary)]">
        If a local cohort is below k, the count is withheld. Noise is added only to eligible aggregates, never to patient rows.
      </p>
    </Page>
  );
}
