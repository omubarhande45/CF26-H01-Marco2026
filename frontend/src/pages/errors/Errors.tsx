import { Link } from "react-router-dom";

export function Forbidden() {
  return (
    <div className="card max-w-lg">
      <h1 className="text-xl font-semibold">403 Access denied</h1>
      <p className="text-sm text-[var(--text-secondary)] mt-2">You do not have permission to access this resource.</p>
      <Link className="btn-primary mt-4 inline-flex" to="/dashboard">
        Return to dashboard
      </Link>
    </div>
  );
}

export function NotFound() {
  return (
    <div className="card max-w-lg">
      <h1 className="text-xl font-semibold">404 Page not found</h1>
      <Link className="btn-primary mt-4 inline-flex" to="/dashboard">
        Return to FCQF
      </Link>
    </div>
  );
}

export function Unavailable() {
  return (
    <div className="card max-w-lg">
      <h1 className="text-xl font-semibold">FCQF services are temporarily unavailable</h1>
      <p className="text-sm text-[var(--text-secondary)] mt-2">Gateway: OFFLINE</p>
      <button className="btn-primary mt-4" onClick={() => window.location.reload()}>
        Retry
      </button>
    </div>
  );
}
