import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Play } from "lucide-react";
import { useAuth } from "../../auth";
import { createQuery, executeAsync, previewPolicy } from "../../api/queries";
import { catalogDiseases, catalogYears, type Disease } from "../../api/catalog";
import { Page } from "../../components/ui";
import type { QuerySpec } from "../../types";

export default function QueryBuilder() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [diseases, setDiseases] = useState<Disease[]>([]);
  const [years, setYears] = useState<number[]>([]);
  const [year, setYear] = useState<number>(2024);
  const [d1, setD1] = useState("Type 2 diabetes mellitus");
  const [d2, setD2] = useState("");
  const [d3, setD3] = useState("");
  const [dp, setDp] = useState(false);
  const [epsilon, setEpsilon] = useState(1);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [policy, setPolicy] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    if (!user) return;
    catalogDiseases(user.token).then(setDiseases).catch(() => setDiseases([]));
    catalogYears(user.token).then((y) => setYears(y.years)).catch(() => setYears([]));
  }, [user]);

  const conditions = useMemo(() => [d1, d2, d3].map((s) => s.trim()).filter(Boolean), [d1, d2, d3]);
  const spec: QuerySpec = useMemo(
    () => ({
      age_min: 0,
      age_max: 120,
      conditions,
      medications: [],
      lab_test: null,
      lab_op: ">",
      lab_value: null,
      window_months: 12,
      year,
      differential_privacy: dp,
      epsilon: dp ? epsilon : null,
    }),
    [conditions, year, dp, epsilon]
  );

  async function validate() {
    if (!user) return;
    try {
      const p = await previewPolicy(user.token, spec);
      setPolicy(p);
      setMsg(p.allowed ? "Policy approved for institutional aggregate query" : String(p.reason));
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "validate failed");
    }
  }

  async function run() {
    if (!user) return;
    setBusy(true);
    setMsg("");
    try {
      const created = await createQuery(user.token, spec);
      await executeAsync(user.token, created.id);
      nav(`/query/${created.id}`);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "run failed");
    } finally {
      setBusy(false);
    }
  }

  const selected = diseases.find((d) => d.disease_name === d1);

  return (
    <Page title="Epidemiology query" subtitle="Federated counts from 12 Indian institutions (2015–2026). No patient records leave a node.">
      <div className="grid lg:grid-cols-2 gap-5">
        <section className="card space-y-4">
          <h2>Clinical criteria</h2>
          <label className="text-xs font-medium text-[var(--text-secondary)] block">
            Year
            <select className="mt-1" value={year} onChange={(e) => setYear(+e.target.value)}>
              {years.map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </label>
          <label className="text-xs font-medium text-[var(--text-secondary)] block">
            Primary condition
            <select className="mt-1" value={d1} onChange={(e) => setD1(e.target.value)}>
              {diseases.map((d) => (
                <option key={d.disease_id} value={d.disease_name}>
                  {d.disease_name} ({d.icd10_code})
                </option>
              ))}
            </select>
            {selected && (
              <span className="block mt-1 text-[11px] text-[var(--text-muted)]">
                ICD-10 {selected.icd10_code} · {selected.disease_category}
              </span>
            )}
          </label>
          <label className="text-xs font-medium text-[var(--text-secondary)] block">
            Co-condition (optional)
            <select className="mt-1" value={d2} onChange={(e) => setD2(e.target.value)}>
              <option value="">None</option>
              <option value="Hypertension">Hypertension</option>
              <option value="Chronic kidney disease">Chronic kidney disease</option>
              <option value="Obesity">Obesity</option>
              <option value="Diabetes">Diabetes</option>
              <option value="COVID-19">COVID-19</option>
              <option value="Ischemic heart disease">Ischemic heart disease</option>
              <option value="Generalized anxiety disorder">Generalized anxiety disorder</option>
            </select>
          </label>
          <label className="text-xs font-medium text-[var(--text-secondary)] block">
            Third condition (optional)
            <select className="mt-1" value={d3} onChange={(e) => setD3(e.target.value)}>
              <option value="">None</option>
              <option value="Hypertension">Hypertension</option>
              <option value="Diabetes">Diabetes</option>
              <option value="Chronic kidney disease">Chronic kidney disease</option>
            </select>
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" className="h-4 w-4" checked={dp} onChange={(e) => setDp(e.target.checked)} />
            Apply differential privacy to aggregates
          </label>
          {dp && (
            <label className="text-xs font-medium text-[var(--text-secondary)] block">
              Epsilon
              <input type="number" step="0.1" className="mt-1" value={epsilon} onChange={(e) => setEpsilon(+e.target.value)} />
            </label>
          )}
          <div className="flex flex-wrap gap-2">
            <button className="btn-ghost" type="button" onClick={validate}>Validate policy</button>
            <button className="btn-primary" type="button" disabled={busy || !d1} onClick={run}>
              <Play size={14} /> {busy ? "Starting…" : "Run federated query"}
            </button>
          </div>
        </section>
        <section className="card h-fit space-y-2">
          <h2>Query preview</h2>
          <ul className="text-sm text-[var(--text-secondary)] space-y-1">
            <li>Year: {year}</li>
            <li>Conditions: {conditions.join(" + ") || "—"}</li>
            <li>Aggregation: institutional disease counts (no patient IDs)</li>
            <li>Federation: 12 source institutions on 3 agents</li>
            <li>Privacy: k = 10 {dp ? `· DP ε=${epsilon}` : ""}</li>
          </ul>
          {msg && <p className="text-sm text-[var(--warning)]">{msg}</p>}
          {policy && <pre className="text-[11px] overflow-auto max-h-40">{JSON.stringify(policy, null, 2)}</pre>}
        </section>
      </div>
    </Page>
  );
}
