import type { ReactNode } from "react";
import { AlertTriangle, CheckCircle2, Circle, XCircle } from "lucide-react";

export function KpiCard({
  label,
  value,
  hint,
  icon,
}: {
  label: string;
  value: string | number | null | undefined;
  hint?: string;
  icon?: ReactNode;
}) {
  return (
    <div className="card transition-transform duration-150 hover:-translate-y-px">
      <div className="flex items-start justify-between">
        <div className="text-[11px] font-semibold uppercase tracking-wide text-[var(--text-secondary)]">{label}</div>
        {icon && <span className="text-[var(--primary)]">{icon}</span>}
      </div>
      <div className="mt-2 text-[28px] font-bold tabular-nums leading-none">{value ?? "N/A"}</div>
      {hint && <div className="mt-2 text-xs text-[var(--text-muted)]">{hint}</div>}
    </div>
  );
}

export function StatusBadge({ status }: { status?: string }) {
  const s = (status || "UNKNOWN").toUpperCase();
  let cls = "bg-[var(--danger-soft)] text-[var(--danger)]";
  let Icon = XCircle;
  if (s.includes("COMPLETE") || s === "OK" || s === "ONLINE" || s === "AVAILABLE" || s === "HEALTHY" || s === "APPROVED") {
    cls = "bg-[var(--success-soft)] text-[var(--success)]";
    Icon = CheckCircle2;
  } else if (s.includes("PARTIAL") || s === "DEGRADED" || s === "TIMEOUT") {
    cls = "bg-[var(--warning-soft)] text-[var(--warning)]";
    Icon = AlertTriangle;
  } else if (s === "RUNNING") {
    cls = "bg-[var(--primary-soft)] text-[var(--primary)]";
    Icon = Circle;
  } else if (s.includes("SUPPRESS") || s.includes("CANCEL")) {
    cls = "bg-[var(--info-soft)] text-[var(--info)]";
    Icon = Circle;
  } else if (s === "DENIED" || s.includes("FAIL") || s === "OFFLINE" || s === "ERROR") {
    cls = "bg-[var(--danger-soft)] text-[var(--danger)]";
    Icon = XCircle;
  }
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${cls}`}>
      <Icon size={12} aria-hidden />
      <span>{s}</span>
    </span>
  );
}

export function EmptyState({ title, body, action }: { title: string; body?: string; action?: ReactNode }) {
  return (
    <div className="card py-14 text-center">
      <div className="font-semibold">{title}</div>
      {body && <p className="mt-1 text-sm text-[var(--text-secondary)]">{body}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="card border-[var(--danger)]/20 bg-[var(--danger-soft)] text-sm">
      <p className="font-medium text-[var(--danger)]">Unable to load data</p>
      <p className="mt-1 text-[var(--text-secondary)]">{message}</p>
      {onRetry && (
        <button className="btn-ghost mt-3" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export function LoadingSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-2" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="skel h-11" />
      ))}
    </div>
  );
}

export function Page({
  title,
  subtitle,
  children,
  actions,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1>{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-[var(--text-secondary)]">{subtitle}</p>}
        </div>
        {actions}
      </div>
      {children}
    </div>
  );
}
