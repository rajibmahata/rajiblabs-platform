import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { me } from "../../services/auth";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<"loading" | "ok" | "fail">("loading");
  useEffect(() => { me().then(() => setStatus("ok")).catch(() => setStatus("fail")); }, []);
  if (status === "loading") return <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--c-bg-primary)", color: "var(--c-text-secondary)" }}>Checking auth…</div>;
  if (status === "fail") return <Navigate to="/admin/login" replace />;
  return <>{children}</>;
}
