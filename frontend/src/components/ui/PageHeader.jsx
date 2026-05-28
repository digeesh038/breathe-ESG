// Consistent page heading: title + subtitle on the left, optional actions right.
// Actions can come in via the `actions` prop or be passed as children.
export function PageHeader({ title, subtitle, actions, children }) {
  const trailing = actions ?? children;
  return (
    <header className="page-header">
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {trailing && <div className="page-actions">{trailing}</div>}
    </header>
  );
}
