import { createBrowserRouter, Navigate, RouterProvider } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { useAuth } from "@/features/auth/AuthContext";
import { LoginPage } from "@/features/auth/LoginPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { IngestionPage } from "@/features/ingestion/IngestionPage";
import { ReviewPage } from "@/features/review/ReviewPage";
import { SourcesPage } from "@/features/sources/SourcesPage";
import { AuditPage } from "@/features/audit/AuditPage";
import { NotFound } from "@/components/ui/NotFound";

// Gate the app behind auth: no token -> bounce to /login.
function RequireAuth({ children }) {
  const { token, ready } = useAuth();
  if (!ready) return null;
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: (
      <RequireAuth>
        <AppLayout />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "sources", element: <SourcesPage /> },
      { path: "ingestion", element: <IngestionPage /> },
      { path: "review", element: <ReviewPage /> },
      { path: "audit", element: <AuditPage /> },
      { path: "*", element: <NotFound /> },
    ],
  },
  { path: "*", element: <NotFound /> },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
