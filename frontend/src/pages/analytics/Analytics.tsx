import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useAuth } from "../../auth";
import { analyticsOverview, type AnalyticsOverview } from "../../api/analytics";
import { catalogDiseases, type Disease } from "../../api/catalog";
import { ErrorState, LoadingSkeleton, Page, StatusBadge } from "../../components/ui";

const DEFAULT = "Type 2 diabetes mellitus";

export default function Analytics() {
  const { user } = useAuth();
  const [disease, setDisease] = useState(DEFAULT);
  const [diseases, setDiseases] = useState<Disease[]>([]);
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!user) return;
    catalogDiseases(user.token).then(setDiseases).catch(() => setDiseases([]));
  }, [user]);

  function load(d = disease) {
    if (!user) return;
    setBusy(true);
    setErr("");
    analyticsOverview(user.token, d)
      .then(setData)
      .catch((e) => setErr(e instanceof Error ? e.message : "analytics failed"))
      .finally(() => setBusy(false));
  }

  useEffect(() => {
    load(DEFAULT);
  }, [user]);

  const timeline = useMemo(() => {
    return (data?.timeline || []).map((row) => ({
      year: row.year,
      total: row.total ?? 0,
      hospital_a: row.hospital_a ?? 0,
      hospital_b: row.hospital_b ?? 0,
      diagnostic_lab: row.diagnostic_lab ?? 0,
    }));
  }, [data]);

  return (
    <Page
      title="Federated analytics"
      subtitle="Yearly disease counts computed on each node. Only k-safe aggregates are shown."
    >
      <div className="mb-4 flex flex-wrap items-end gap-3">
        <label className="min-w-[280px] flex-1 text-xs font-medium text-[var(--text-secondary)]">
          Condition
          <select className="mt-1" value={disease} onChange={(e) => setDisease(e.target.value)}>
            {(diseases.length ? diseases : [{ disease_id: "x", disease_name: DEFAULT, disease_category: "", icd10_code: "" }]).map(
              (d) => (
                <option key={d.disease_id} value={d.disease_name}>
                  {d.disease_name} {d.icd10_code ? `(${d.icd10_code})` : ""}
                </option>
              )
            )}
          </select>
        </label>
        <button className="btn-primary" type="button" disabled={busy} onClick={() => load(disease)}>
          {busy ? "Computing…" : "Run federated trend"}
        </button>
      </div>

      {err && <ErrorState message={err} onRetry={() => load(disease)} />}
      {!data && !err && <LoadingSkeleton rows={6} />}

      {data && (
        <>
          <div className="grid md:grid-cols-3 gap-3 mb-5">
            {data.nodes.map((n) => (
              <div key={n.node_id} className="card">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-sm">{n.name.replace("Diagnostic Laboratory", "Diagnostic Lab")}</h3>
                  <StatusBadge status={n.healthy ? "ONLINE" : "OFFLINE"} />
                </div>
                <p className="mt-2 text-xs text-[var(--text-secondary)]">
                  Years {n.year_min ?? "—"}–{n.year_max ?? "—"} · k ≥ {n.k ?? 10}
                </p>
              </div>
            ))}
          </div>

          <section className="card h-72 mb-5">
            <h2 className="mb-2">Federated trend · {data.disease}</h2>
            <ResponsiveContainer width="100%" height="85%">
              <LineChart data={timeline}>
                <CartesianGrid stroke="#EEF1F5" vertical={false} />
                <XAxis dataKey="year" stroke="#667085" fontSize={12} />
                <YAxis stroke="#667085" fontSize={12} />
                <Tooltip contentStyle={{ background: "#fff", border: "1px solid #E4E7EC" }} />
                <Legend />
                <Line type="monotone" dataKey="total" name="Federated total" stroke="#2563EB" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="hospital_a" name="Hospital A" stroke="#0F766E" strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey="hospital_b" name="Hospital B" stroke="#D97706" strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey="diagnostic_lab" name="Lab" stroke="#7C3AED" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </section>

          <section className="card h-64 mb-5">
            <h2 className="mb-2">Hospital comparison</h2>
            <ResponsiveContainer width="100%" height="85%">
              <BarChart data={timeline}>
                <CartesianGrid stroke="#EEF1F5" vertical={false} />
                <XAxis dataKey="year" stroke="#667085" fontSize={12} />
                <YAxis stroke="#667085" fontSize={12} />
                <Tooltip contentStyle={{ background: "#fff", border: "1px solid #E4E7EC" }} />
                <Legend />
                <Bar dataKey="hospital_a" name="Hospital A" fill="#2563EB" radius={[3, 3, 0, 0]} />
                <Bar dataKey="hospital_b" name="Hospital B" fill="#0F766E" radius={[3, 3, 0, 0]} />
                <Bar dataKey="diagnostic_lab" name="Lab" fill="#7C3AED" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </section>

          <section className="card !p-0 overflow-hidden">
            <div className="px-5 pt-4 pb-2">
              <h2>Top diseases (sum of released node aggregates)</h2>
              <p className="text-xs text-[var(--text-secondary)]">{data.completeness_note}</p>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Disease</th>
                  <th>ICD-10</th>
                  <th>Category</th>
                  <th>Federated count</th>
                  <th>Nodes</th>
                </tr>
              </thead>
              <tbody>
                {data.top_diseases.map((d) => (
                  <tr key={d.disease_name}>
                    <td>{d.disease_name}</td>
                    <td className="font-mono text-xs">{d.icd10_code || "—"}</td>
                    <td className="text-[var(--text-secondary)]">{d.category || "—"}</td>
                    <td className="font-mono">{d.count}</td>
                    <td>{d.nodes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}
    </Page>
  );
}
