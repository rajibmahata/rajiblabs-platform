import { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/Home";
import AdminLayout from "./components/admin/AdminLayout";
import ProtectedRoute from "./components/admin/ProtectedRoute";
import ProjectDetail from "./pages/ProjectDetail";

// Admin pages are route-split so the public homepage bundle stays lean.
// (Bulk of the 500kB+ chunk was admin code shipped to every visitor.)
const Login = lazy(() => import("./pages/admin/Login"));
const Dashboard = lazy(() => import("./pages/admin/Dashboard"));
const ResumeManage = lazy(() => import("./pages/admin/ResumeManage"));
const PortfolioManage = lazy(() => import("./pages/admin/PortfolioManage"));
const GitHubManage = lazy(() => import("./pages/admin/GitHubManage"));
const ProductsManage = lazy(() => import("./pages/admin/ProductsManage"));
const ProfileManage = lazy(() => import("./pages/admin/ProfileManage"));
const ContentManage = lazy(() => import("./pages/admin/ContentManage"));
const LeadsManage = lazy(() => import("./pages/admin/LeadsManage"));
const CustomersManage = lazy(() => import("./pages/admin/CustomersManage"));
const CampaignsManage = lazy(() => import("./pages/admin/CampaignsManage"));
const TemplatesManage = lazy(() => import("./pages/admin/TemplatesManage"));
const KnowledgeManage = lazy(() => import("./pages/admin/KnowledgeManage"));
const LanguagesManage = lazy(() => import("./pages/admin/LanguagesManage"));
const TranslationsManage = lazy(() => import("./pages/admin/TranslationsManage"));
const AgentsManage = lazy(() => import("./pages/admin/AgentsManage"));
const CareerCompanies = lazy(() => import("./pages/admin/CareerCompanies"));
const CareerJobs = lazy(() => import("./pages/admin/CareerJobs"));
const CareerWorkspace = lazy(() => import("./pages/admin/CareerWorkspace"));
const CareerApplications = lazy(() => import("./pages/admin/CareerApplications"));
const ProfileAgent = lazy(() => import("./pages/admin/ProfileAgent"));
const LearningManage = lazy(() => import("./pages/admin/LearningManage"));
const Learning = lazy(() => import("./pages/Learning"));
const LearningPathDetail = lazy(() => import("./pages/LearningPathDetail"));
const DomainsManage = lazy(() => import("./pages/admin/DomainsManage"));
const SkillsManage = lazy(() => import("./pages/admin/SkillsManage"));
const DomainDetail = lazy(() => import("./pages/DomainDetail"));
const Workbench = lazy(() => import("./pages/admin/Workbench"));
const LogsManage = lazy(() => import("./pages/admin/LogsManage"));
const Settings = lazy(() => import("./pages/admin/Settings"));
const AgentOpsSummary = lazy(() => import("./pages/admin/AgentOpsSummaryPage"));
const AgentOpsConversations = lazy(() => import("./pages/admin/AgentOpsConversationsPage"));
const AgentOpsAgentDetail = lazy(() => import("./pages/admin/AgentOpsAgentDetailPage"));

const PortfolioDetail = () => <ProjectDetail kind="portfolio" />;
const ProductDetail = () => <ProjectDetail kind="product" />;

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div className="p-6">Loading…</div>}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/portfolio/:slug" element={<PortfolioDetail />} />
          <Route path="/products/:slug" element={<ProductDetail />} />
          <Route path="/learning" element={<Learning />} />
          <Route path="/learning/:slug" element={<LearningPathDetail />} />
          <Route path="/domains/:slug" element={<DomainDetail />} />
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
            <Route path="customers" element={<CustomersManage />} />
            <Route path="campaigns" element={<CampaignsManage />} />
            <Route path="templates" element={<TemplatesManage />} />
            <Route path="knowledge" element={<KnowledgeManage />} />
            <Route path="skills" element={<SkillsManage />} />
            <Route path="learning" element={<LearningManage />} />
            <Route path="domains" element={<DomainsManage />} />
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
            <Route path="ops/summary" element={<AgentOpsSummary />} />
            <Route path="ops/conversations" element={<AgentOpsConversations />} />
            <Route path="ops/conversations/:conversationId" element={<AgentOpsConversations />} />
            <Route path="ops/agents/:slug" element={<AgentOpsAgentDetail />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
