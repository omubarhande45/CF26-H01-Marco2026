import { Component, type ReactNode } from "react";

export class ErrorBoundary extends Component<{ children: ReactNode }, { err: string | null }> {
  state = { err: null as string | null };
  static getDerivedStateFromError(e: Error) {
    return { err: e.message };
  }
  render() {
    if (this.state.err) {
      return (
        <div style={{ fontFamily: "Inter, system-ui, sans-serif", padding: 32, maxWidth: 560 }}>
          <h1 style={{ fontSize: 20 }}>FCQF could not render</h1>
          <p style={{ color: "#667085" }}>{this.state.err}</p>
          <button
            type="button"
            onClick={() => {
              sessionStorage.clear();
              window.location.href = "/login";
            }}
            style={{ background: "#2563EB", color: "#fff", border: 0, padding: "10px 16px", borderRadius: 8 }}
          >
            Go to sign-in
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
