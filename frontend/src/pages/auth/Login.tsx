import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../../api/auth";
import { useAuth } from "../../auth";
import { homeFor } from "../../roles";
import { ApiError } from "../../api/client";
import Brand from "../../components/Brand";

export default function Login() {
  const { setUser } = useAuth();
  const nav = useNavigate();
  const [user, setU] = useState("");
  const [pass, setP] = useState("");
  const [err, setErr] = useState("");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr("");
    try {
      const data = await login(user, pass);
      const token = data.access_token || (data as { token?: string }).token;
      if (!token) throw new Error("Sign-in did not return an access token");
      setUser({ token, username: data.username, role: data.role });
      nav(homeFor(data.role));
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "login failed");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="card max-w-md w-full">
        <Brand />
        <h1 className="mt-5">Institutional sign-in</h1>
        <p className="mt-2 text-sm text-[var(--text-secondary)]">
          Authorized access to federated epidemiology queries. Patient-level records are never returned.
        </p>
        <form className="mt-6 space-y-3" onSubmit={onSubmit}>
          <label className="block text-xs font-medium text-[var(--text-secondary)]">
            Username
            <input className="mt-1" autoComplete="username" value={user} onChange={(e) => setU(e.target.value)} />
          </label>
          <label className="block text-xs font-medium text-[var(--text-secondary)]">
            Password
            <input className="mt-1" type="password" autoComplete="current-password" value={pass} onChange={(e) => setP(e.target.value)} />
          </label>
          {err && <p className="text-sm text-[var(--danger)] whitespace-pre-wrap">{err}</p>}
          <button className="btn-primary w-full" type="submit">
            Sign in
          </button>
        </form>
      </div>
    </div>
  );
}
