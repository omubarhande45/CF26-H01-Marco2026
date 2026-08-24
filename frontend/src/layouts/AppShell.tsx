import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import {
  Activity,
  BarChart3,
  Bell,
  BookOpen,
  Building2,
  ChevronDown,
  FileSearch,
  GitBranch,
  History,
  Home,
  Lock,
  Menu,
  Search,
  Settings,
  ShieldCheck,
  X,
} from "lucide-react";
import { useAuth } from "../auth";
import { can, type NavKey } from "../roles";
import { gatewayHealth, stats } from "../api/federation";
import { logout as apiLogout, publicConfig } from "../api/auth";
import Brand from "../components/Brand";

const NAV: { key: NavKey; to: string; label: string; group: string | null; icon: typeof Search }[] = [
  { key: "dashboard", to: "/dashboard", label: "Overview", group: null, icon: Home },
  { key: "query-builder", to: "/query-builder", label: "Query Builder", group: "QUERY", icon: Search },
  { key: "query-history", to: "/query-history", label: "Query History", group: "QUERY", icon: History },
  { key: "federation", to: "/federation", label: "Federation Monitor", group: "FEDERATION", icon: GitBranch },
  { key: "institutions", to: "/institutions", label: "Institutions", group: "FEDERATION", icon: Building2 },
  { key: "institutions", to: "/hospital-a", label: "Hospital A", group: "FEDERATION", icon: Building2 },
  { key: "institutions", to: "/hospital-b", label: "Hospital B", group: "FEDERATION", icon: Building2 },
  { key: "system-health", to: "/system-health", label: "System Health", group: "FEDERATION", icon: Activity },
  { key: "privacy", to: "/privacy", label: "Privacy Center", group: "PRIVACY & SECURITY", icon: ShieldCheck },
  { key: "audit", to: "/audit", label: "Audit Log", group: "PRIVACY & SECURITY", icon: FileSearch },
  { key: "provenance", to: "/provenance", label: "Provenance", group: "PRIVACY & SECURITY", icon: Lock },
  { key: "analytics", to: "/analytics", label: "Analytics", group: "ANALYTICS", icon: BarChart3 },
  { key: "benchmarks", to: "/benchmarks", label: "Benchmarks", group: "ANALYTICS", icon: BarChart3 },
  { key: "docs", to: "/docs", label: "Documentation", group: "RESOURCES", icon: BookOpen },
];

export default function AppShell() {
  const { user, setUser } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const [env, setEnv] = useState("DEVELOPMENT");
  const [sys, setSys] = useState<"ok" | "degraded" | "down">("ok");
  const [open, setOpen] = useState(false);
  const [menu, setMenu] = useState(false);

  useEffect(() => {
    publicConfig()
      .then((c) => setEnv((c.environment || "development").toUpperCase()))
      .catch(() => {});
  }, []);

  useEffect(() => {
    let alive = true;
    async function ping() {
      const h = await gatewayHealth().catch(() => null);
      const s = user ? await stats(user.token).catch(() => null) : null;
      if (!alive) return;
      if (!h) setSys("down");
      else if (s && s.online_nodes < s.nodes_total) setSys("degraded");
      else setSys("ok");
    }
    ping();
    const id = setInterval(ping, 8000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [user]);

  useEffect(() => setOpen(false), [loc.pathname]);

  if (!user) return null;
  const items = NAV.filter((n) => can(user.role, n.key));
  const groups = [null, "QUERY", "FEDERATION", "PRIVACY & SECURITY", "ANALYTICS", "RESOURCES"];

  const sidebar = (
    <div className="flex h-full flex-col">
      <Brand />
      <nav className="mt-6 flex-1 space-y-3 overflow-y-auto text-[13px]">
        {groups.map((g) => {
          const list = items.filter((i) => i.group === g);
          if (!list.length) return null;
          return (
            <div key={g || "top"}>
              {g && <div className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-[#98A2B3]">{g}</div>}
              <ul>
                {list.map((i) => {
                  const Icon = i.icon;
                  return (
                    <li key={i.to}>
                      <NavLink
                        to={i.to}
                        className={({ isActive }) =>
                          `mx-1 flex items-center gap-2.5 rounded-lg px-3 py-2 ${
                            isActive ? "bg-[#EEF4FF] font-semibold text-[#2563EB]" : "text-[#344054] hover:bg-[#F9FAFC]"
                          }`
                        }
                      >
                        <Icon size={16} />
                        {i.label}
                      </NavLink>
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </nav>
      {can(user.role, "settings") && (
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `mt-2 flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] ${
              isActive ? "bg-[#EEF4FF] font-semibold text-[#2563EB]" : "text-[#344054] hover:bg-[#F9FAFC]"
            }`
          }
        >
          <Settings size={16} /> Settings
        </NavLink>
      )}
    </div>
  );

  return (
    <div className="min-h-screen flex bg-[#F6F8FB]">
      <aside className="hidden md:flex w-[248px] shrink-0 flex-col border-r border-[#E4E7EC] bg-white px-3 py-4">{sidebar}</aside>
      {open && (
        <div className="fixed inset-0 z-40 md:hidden">
          <button className="absolute inset-0 bg-black/30" aria-label="Close menu" onClick={() => setOpen(false)} />
          <aside className="relative z-50 h-full w-[248px] bg-white p-4">{sidebar}</aside>
        </div>
      )}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-14 items-center justify-between gap-3 border-b border-[#E4E7EC] bg-white px-4 md:px-6">
          <div className="flex items-center gap-3">
            <button className="rounded-lg p-1.5 text-[#667085] hover:bg-[#F9FAFC]" onClick={() => setOpen(true)} aria-label="Menu">
              {open ? <X size={18} /> : <Menu size={18} />}
            </button>
            <div>
              <div className="text-sm font-semibold">
                {NAV.find((n) => loc.pathname.startsWith(n.to))?.label ||
                  (loc.pathname.startsWith("/query/") ? "Query details" : loc.pathname.startsWith("/settings") ? "Settings" : "FCQF")}
              </div>
              <div className="text-[11px] text-[#98A2B3]">FCQF {loc.pathname}</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden sm:inline text-xs font-medium">
              {sys === "ok" && <span className="text-[#16A34A]">● All Systems Operational</span>}
              {sys === "degraded" && <span className="text-[#D97706]">● Degraded</span>}
              {sys === "down" && <span className="text-[#DC2626]">● Gateway unreachable</span>}
            </span>
            <span className="rounded-full border border-[#E4E7EC] px-2.5 py-0.5 text-[10px] font-semibold tracking-wide text-[#667085]">
              {env}
            </span>
            <button className="rounded-lg p-1.5 text-[#667085]" aria-label="Notifications">
              <Bell size={16} />
            </button>
            <div className="relative">
              <button className="flex items-center gap-2" onClick={() => setMenu((v) => !v)}>
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#EEF4FF] text-xs font-bold text-[#2563EB]">
                  {user.username.slice(0, 1).toUpperCase()}
                </span>
                <span className="hidden text-left sm:block">
                  <span className="block text-sm font-medium leading-tight">{user.username}</span>
                  <span className="block text-[11px] capitalize text-[#667085]">{user.role.replace("_", " ")}</span>
                </span>
                <ChevronDown size={14} className="text-[#98A2B3]" />
              </button>
              {menu && (
                <div className="absolute right-0 mt-2 w-36 rounded-lg border border-[#E4E7EC] bg-white py-1 text-sm shadow-md">
                  <button
                    className="w-full px-3 py-1.5 text-left hover:bg-[#F9FAFC]"
                    onClick={() => {
                      void apiLogout();
                      setUser(null);
                      nav("/login");
                    }}
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-5 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
