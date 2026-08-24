import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useAuth } from "../../auth";
import { getBenchmarks } from "../../api/benchmarks";
import { Page } from "../../components/ui";

export default function Benchmarks() {
  const { user } = useAuth();
  const [data, setData] = useState<{ available: boolean; results: any } | null>(null);

  useEffect(() => {
    if (!user) return;
    getBenchmarks(user.token).then(setData);
  }, [user]);

  const runs = data?.results?.runs as Array<Record<string, unknown>> | undefined;

  return (
    <Page title="Benchmarks" subtitle="Measurements from scripts/benchmark.py — never invented in the UI.">
      {!data?.available && <p className="text-sm text-[var(--text-secondary)]">No benchmark available. Run python3 scripts/benchmark.py</p>}
      {runs && (
        <div className="card h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={runs.map((r, i) => ({ name: `run ${i + 1}`, ms: r.wall_ms }))}>
              <CartesianGrid stroke="#EEF1F5" vertical={false} />
              <XAxis dataKey="name" stroke="#667085" />
              <YAxis stroke="#667085" />
              <Tooltip contentStyle={{ background: "#fff", border: "1px solid #E4E7EC" }} />
              <Bar dataKey="ms" fill="#2563EB" name="wall_ms" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      {runs && (
        <table className="w-full text-sm mt-4">
          <thead className="text-xs text-[var(--text-secondary)]">
            <tr>
              <th className="text-left">Status</th>
              <th>Aggregate</th>
              <th>Wall ms</th>
              <th>Completeness</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r, i) => (
              <tr key={i} className="border-t border-[var(--border)]">
                <td className="py-2">{String(r.status)}</td>
                <td className="text-center">{String(r.aggregate)}</td>
                <td className="text-center">{String(r.wall_ms)}</td>
                <td className="text-center">{String(r.completeness)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Page>
  );
}
