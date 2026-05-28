import { Component } from "react";

// Catches render-time errors anywhere below it so a single broken component
// doesn't blank the whole app. Class component because error boundaries have
// no hook equivalent.
export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    // Surfaced to the console here; in prod this is where Sentry.captureException
    // would go (the backend already wires Sentry via SENTRY_DSN).
    console.error("Unhandled UI error:", error, info);
  }

  handleReload = () => {
    this.setState({ error: null });
    window.location.reload();
  };

  render() {
    if (this.state.error) {
      return (
        <div className="error-screen">
          <div className="error-card">
            <h1>Something went wrong</h1>
            <p className="muted">
              The page hit an unexpected error. Reloading usually fixes it.
            </p>
            <button className="btn btn--primary" onClick={this.handleReload}>
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
