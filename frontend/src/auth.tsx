import { createContext, useContext, useMemo, useState } from "react";
import type { AuthUser } from "./types";

const KEY = "fcqf.auth";

const Ctx = createContext<{
  user: AuthUser | null;
  setUser: (u: AuthUser | null) => void;
}>({ user: null, setUser: () => {} });

function normalize(raw: unknown): AuthUser | null {
  if (!raw || typeof raw !== "object") return null;
  const u = raw as { token?: string; access_token?: string; username?: string; role?: AuthUser["role"] };
  const token = u.token || u.access_token || "";
  if (!token || !u.username || !u.role) return null;
  return { token, username: u.username, role: u.role };
}

function load(): AuthUser | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    const user = raw ? normalize(JSON.parse(raw)) : null;
    if (!user) sessionStorage.removeItem(KEY);
    return user;
  } catch {
    sessionStorage.removeItem(KEY);
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUserState] = useState<AuthUser | null>(load);
  const setUser = (u: AuthUser | null) => {
    const next = u ? normalize(u) : null;
    setUserState(next);
    if (next) sessionStorage.setItem(KEY, JSON.stringify(next));
    else sessionStorage.removeItem(KEY);
  };
  const v = useMemo(() => ({ user, setUser }), [user]);
  return <Ctx.Provider value={v}>{children}</Ctx.Provider>;
}

export function useAuth() {
  return useContext(Ctx);
}
