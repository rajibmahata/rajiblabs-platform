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
import LeadsManage from "./pages/admin/LeadsManage";
import KnowledgeManage from "./pages/admin/KnowledgeManage";
import LanguagesManage from "./pages/admin/LanguagesManage";
import TranslationsManage from "./pages/admin/TranslationsManage";
import AgentsManage from "./pages/admin/AgentsManage";
import CareerCompanies from "./pages/admin/CareerCompanies";
import CareerJobs from "./pages/admin/CareerJobs";
import CareerWorkspace from "./pages/admin/CareerWorkspace";
import CareerApplications from "./pages/admin/CareerApplications";
import ProfileAgent from "./pages/admin/ProfileAgent";
import Workbench from "./pages/admin/Workbench";
import LogsManage from "./pages/admin/LogsManage";
import Settings from "./pages/admin/Settings";
import AdminLayout from "./components/admin/AdminLayout";
import ProtectedRoute from "./components/admin/ProtectedRoute";
import ProjectDetail from "./pages/ProjectDetail";

const PortfolioDetail = () => <ProjectDetail kind="portfolio" />;
const ProductDetail = () => <ProjectDetail kind="product" />;

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
          <Route path="leads" element={<LeadsManage />} />
          <Route path="knowledge" element={<KnowledgeManage />} />
          <Route path="agents" element={<AgentsManage />} />
          <Route path="profile-agent" element={<ProfileAgent />} />
          <Route path="career" element={<CareerWorkspace />} />
          <Route path="career/jobs" element={<CareerJobs />} />
          <Route path="career/companies" element={<CareerCompanies />} />
          <Route path="career/applications" element={<CareerApplications />} />
          <Route path="ai-workbench" element={<Workbench />} />
          <Route path="ai-workbench/history" element={<Workbench initialView="history" />} />
          <Route path="languages" element={<LanguagesManage />} />
          <Route path="translations" element={<TranslationsManage />} />
          <Route path="logs" element={<LogsManage />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
