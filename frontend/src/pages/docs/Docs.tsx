import { useEffect, useState } from "react";
import { useAuth } from "../../auth";
import { api } from "../../api/client";
import { Page } from "../../components/ui";

export default function Docs() {
  const { user } = useAuth();
  const [list, setList] = useState<Array<{ id: string; title: string }>>([]);
  const [body, setBody] = useState("");
  const [title, setTitle] = useState("What is FCQF?");

  useEffect(() => {
    if (!user) return;
    api<Array<{ id: string; title: string }>>("/docs/catalog", user.token)
      .then(setList)
      .catch(() => setList([]));
  }, [user]);

  async function open(id: string, t: string) {
    if (!user) return;
    setTitle(t);
    const d = await api<{ markdown: string }>(`/docs/catalog/${id}`, user.token).catch(() => ({ markdown: "" }));
    setBody(d.markdown);
  }

  return (
    <Page title="Documentation">
      <div className="grid md:grid-cols-4 gap-4">
        <ul className="text-sm space-y-1">
          <li className="text-[var(--text-secondary)]">What is FCQF? We move the query, not the records.</li>
          {list.map((d) => (
            <li key={d.id}>
              <button className="text-[var(--primary)] text-left" onClick={() => open(d.id, d.title)}>
                {d.title}
              </button>
            </li>
          ))}
        </ul>
        <pre className="card md:col-span-3 text-xs whitespace-pre-wrap text-[var(--text-secondary)] max-h-[70vh] overflow-auto">
          {body || `${title}\n\nSelect a document from the catalog (served from /docs via the gateway).`}
        </pre>
      </div>
    </Page>
  );
}
