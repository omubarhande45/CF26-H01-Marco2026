export default function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <svg width="32" height="32" viewBox="0 0 32 32" aria-hidden>
        <circle cx="8" cy="8" r="3.2" fill="#2563EB" />
        <circle cx="24" cy="8" r="3.2" fill="#0F766E" />
        <circle cx="16" cy="24" r="3.2" fill="#0284C7" />
        <path d="M10.2 10.2 L14.2 21.2 M21.8 10.2 L17.8 21.2 M11.2 8 H20.8" stroke="#98A2B3" strokeWidth="1.4" fill="none" />
      </svg>
      <div>
        <div className="text-[15px] font-bold tracking-tight text-[var(--text-primary)]">FCQF</div>
        {!compact && <div className="text-[11px] text-[var(--text-secondary)] leading-tight">Federated Clinical Query Fabric</div>}
      </div>
    </div>
  );
}
