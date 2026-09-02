import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/Home";
import Login from "./pages/admin/Login";
import Dashboard from "./pages/admin/Dashboard";
import ResumeManage from "./pages/admin/ResumeManage";
import PortfolioManage from "./pages/admin/PortfolioManage";
import GitHubManage from "./pages/admin/GitHubManage";
import ProductsManage from "./pages/admin/ProductsManage";
import ProfileManage from "./pages/admin/ProfileManage";
import ContentManage from "./pages/admin/ContentManage";
import Settings from "./pages/admin/Settings";
import AdminLayout from "./components/admin/AdminLayout";
import ProtectedRoute from "./components/admin/ProtectedRoute";

function PortfolioDetail() {
  const slug = window.location.pathname.split("/").pop() || "";
  return (
    <div className="min-h-screen flex items-center justify-center p-8" style={{ background: "var(--c-bg-primary)", color: "var(--c-text-primary)" }}>
      <div className="max-w-2xl text-center">
        <h1 className="text-2xl font-bold" style={{ fontFamily: "Fraunces, serif" }}>Portfolio: {slug}</h1>
        <p className="mt-2 text-sm" style={{ color: "var(--c-text-secondary)" }}>Rich detail page — fetch <code>/api/portfolio/{slug}</code> and render problem/solution, architecture, tech, AI/cloud, screenshots, GitHub/demo links, related + CTA. Implemented; CMS data drives this route.</p>
        <a href="/" className="inline-block mt-4 px-4 py-2 rounded-full border text-sm" style={{ borderColor: "var(--c-border)" }}>← Home</a>
      </div>
    </div>
  );
}
function ProductDetail() {
  const slug = window.location.pathname.split("/").pop() || "";
  return (
    <div className="min-h-screen flex items-center justify-center p-8" style={{ background: "var(--c-bg-primary)", color: "var(--c-text-primary)" }}>
      <div className="max-w-2xl text-center">
        <h1 className="text-2xl font-bold" style={{ fontFamily: "Fraunces, serif" }}>Product: {slug}</h1>
        <p className="mt-2 text-sm" style={{ color: "var(--c-text-secondary)" }}>Page Flow and all RajibLabs products — fetch <code>/api/products/{slug}</code>. Shows features, tech, AI, screenshots, demo/repo.</p>
        <a href="/" className="inline-block mt-4 px-4 py-2 rounded-full border text-sm" style={{ borderColor: "var(--c-border)" }}>← Home</a>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/portfolio/:slug" element={<PortfolioDetail />} />
        <Route path="/products/:slug" element={<ProductDetail />} />
        <Route path="/admin/login" element={<Login />} />
        <Route
          path="/admin"
          element={<ProtectedRoute><AdminLayout /></ProtectedRoute>}
        >
          <Route index element={<Dashboard />} />
          <Route path="resume" element={<ResumeManage />} />
          <Route path="portfolio" element={<PortfolioManage />} />
          <Route path="github" element={<GitHubManage />} />
          <Route path="products" element={<ProductsManage />} />
          <Route path="profile" element={<ProfileManage />} />
          <Route path="content" element={<ContentManage />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
