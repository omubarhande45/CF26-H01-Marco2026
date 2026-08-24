import { useAuth } from "../../auth";
import { Page } from "../../components/ui";

export default function Settings() {
  const { user } = useAuth();
  return (
    <Page title="Settings">
      <div className="card text-sm space-y-2">
        <div>Profile: {user?.username}</div>
        <div>Role: {user?.role}</div>
        <div>Authentication: local JWT (OIDC-ready on the gateway)</div>
        <div>Privacy: k=10 enforced server-side — not editable here</div>
        <p className="text-[var(--text-muted)] text-xs">Secrets and service tokens are not exposed to the browser.</p>
      </div>
    </Page>
  );
}
