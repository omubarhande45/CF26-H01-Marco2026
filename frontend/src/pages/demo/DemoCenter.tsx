import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../auth";
import { createQuery, executeQuery } from "../../api/queries";
import { Page } from "../../components/ui";
import type { QuerySpec } from "../../types";

function base(): QuerySpec {
  return {
    age_min: 40,
    age_max: 70,
    conditions: ["Type 2 Diabetes"],
    medications: ["Metformin"],
    lab_test: "HbA1c",
    lab_op: ">",
    lab_value: 8,
    window_months: 12,
    year: 2024,
    differential_privacy: false,
    epsilon: null,
  };
}

export default function DemoCenter() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [out, setOut] = useState("");

  async function run(spec: QuerySpec, go = true) {
    if (!user) return;
    setOut("Running…");
    try {
      const c = await createQuery(user.token, spec);
      const r = await executeQuery(user.token, c.id);
      setOut(`${r.status} · aggregate ${r.aggregate ?? "—"} · completeness ${r.completeness ?? "—"}`);
      if (go) nav(`/query/${c.id}`);
    } catch (e) {
      setOut(e instanceof Error ? e.message : "failed");
    }
  }

  return (
    <Page title="Demo center" subtitle="Each button calls the live gateway. No simulated React results.">
      <div className="grid md:grid-cols-2 gap-3">
        <button className="card text-left" onClick={() => run(base())}>
          A · Complete federation
        </button>
        <button className="card text-left" onClick={() => run({ ...base(), age_min: 89, age_max: 90, lab_value: 11.5 })}>
          B · Small cohort (expect SUPPRESSED)
        </button>
        <button className="card text-left" onClick={() => run(base())}>
          C · Node failure — stop a node, then run (expect PARTIAL)
        </button>
        <button
          className="card text-left"
          onClick={() => run({ ...base(), requested_fields: ["patient_id", "name", "phone", "address"] }, false)}
        >
          D · Raw-data attack (expect DENIED)
        </button>
        <button className="card text-left" onClick={() => run({ ...base(), differential_privacy: true, epsilon: 1 })}>
          E · Differential privacy
        </button>
        <div className="card text-sm text-[var(--text-secondary)]">
          F · Schema mismatch: set FORCE_INCOMPATIBLE=1 on a node and re-run A.
          <br />
          G · Recovery: restart the node and re-run A for COMPLETE.
        </div>
      </div>
      {out && <p className="mt-4 text-sm text-[var(--warning)]">{out}</p>}
    </Page>
  );
}
