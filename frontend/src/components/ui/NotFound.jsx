import { Link } from "react-router-dom";

// Catch-all for unmatched client routes.
export function NotFound() {
  return (
    <div className="error-screen">
      <div className="error-card">
        <h1>404</h1>
        <p className="muted">That page doesn&apos;t exist.</p>
        <Link className="btn btn--primary" to="/dashboard">
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
