import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import { can, homeFor, type NavKey } from "./roles";
import AppShell from "./layouts/AppShell";
import Login from "./pages/auth/Login";
import Dashboard from "./pages/dashboard/Dashboard";
import QueryBuilder from "./pages/queries/QueryBuilder";
import QueryHistory from "./pages/queries/QueryHistory";
import QueryDetails from "./pages/queries/QueryDetails";
import Federation from "./pages/federation/Federation";
import Institutions from "./pages/institutions/Institutions";
import InstitutionDetail from "./pages/institutions/InstitutionDetail";
import { HospitalA, HospitalB } from "./pages/institutions/HospitalNode";
import PrivacyCenter from "./pages/privacy/PrivacyCenter";
import Audit from "./pages/audit/Audit";
import AuditDetail from "./pages/audit/AuditDetail";
import Provenance from "./pages/provenance/Provenance";
import Benchmarks from "./pages/benchmarks/Benchmarks";
import Analytics from "./pages/analytics/Analytics";
import SystemHealth from "./pages/health/SystemHealth";
import Docs from "./pages/docs/Docs";
import Settings from "./pages/settings/Settings";
import { Forbidden, NotFound, Unavailable } from "./pages/errors/Errors";
import type { Role } from "./types";

function Guard({ allow, children }: { allow: NavKey; children: React.ReactNode }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (!can(user.role as Role, allow)) return <Navigate to="/403" replace />;
  return <>{children}</>;
}

function Authed({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  const { user } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to={homeFor(user.role)} replace /> : <Login />} />
      <Route path="/" element={<Navigate to={user ? homeFor(user.role) : "/login"} replace />} />
      <Route
        element={
          <Authed>
            <AppShell />
          </Authed>
        }
      >
        <Route path="/dashboard" element={<Guard allow="dashboard"><Dashboard /></Guard>} />
        <Route path="/query-builder" element={<Guard allow="query-builder"><QueryBuilder /></Guard>} />
        <Route path="/query-history" element={<Guard allow="query-history"><QueryHistory /></Guard>} />
        <Route path="/query/:queryId" element={<Guard allow="dashboard"><QueryDetails /></Guard>} />
        <Route path="/federation" element={<Guard allow="federation"><Federation /></Guard>} />
        <Route path="/institutions" element={<Guard allow="institutions"><Institutions /></Guard>} />
        <Route path="/hospital-a" element={<Guard allow="institutions"><HospitalA /></Guard>} />
        <Route path="/hospital-b" element={<Guard allow="institutions"><HospitalB /></Guard>} />
        <Route path="/institutions/hospital_a" element={<Guard allow="institutions"><HospitalA /></Guard>} />
        <Route path="/institutions/hospital_b" element={<Guard allow="institutions"><HospitalB /></Guard>} />
        <Route path="/institutions/:institutionId" element={<Guard allow="institutions"><InstitutionDetail /></Guard>} />
        <Route path="/system-health" element={<Guard allow="system-health"><SystemHealth /></Guard>} />
        <Route path="/privacy" element={<Guard allow="privacy"><PrivacyCenter /></Guard>} />
        <Route path="/audit" element={<Guard allow="audit"><Audit /></Guard>} />
        <Route path="/audit/:eventId" element={<Guard allow="audit"><AuditDetail /></Guard>} />
        <Route path="/provenance" element={<Guard allow="provenance"><Provenance /></Guard>} />
        <Route path="/benchmarks" element={<Guard allow="benchmarks"><Benchmarks /></Guard>} />
        <Route path="/analytics" element={<Guard allow="analytics"><Analytics /></Guard>} />
        <Route path="/docs" element={<Guard allow="docs"><Docs /></Guard>} />
        <Route path="/settings" element={<Guard allow="settings"><Settings /></Guard>} />
        <Route path="/403" element={<Forbidden />} />
        <Route path="/unavailable" element={<Unavailable />} />
        <Route path="/" element={<Navigate to={user ? homeFor(user.role) : "/login"} replace />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
