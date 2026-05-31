import { useState, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import ProjectCard from '../ui/ProjectCard';
import ProjectModal from '../ui/ProjectModal';
import type { ProjectDetail } from '../ui/ProjectModal';

type FilterTab = 'all' | 'github' | 'claude_cb' | 'localhost';

const projects: ProjectDetail[] = [
  {
    name: 'DocSignerHub',
    shortDesc: 'Enterprise e-signature SaaS with AI clause analysis, multi-signer workflows & blockchain notarisation.',
    longDesc: 'A complete digital signature platform built from the ground up. DocSignerHub enables businesses to send, sign, and manage documents with enterprise-grade security. Features include a visual workflow builder for complex approval chains, HMAC-signed API authentication, Stripe payment integration within signing flows, AI-powered clause summarisation using GPT-4o, and optional blockchain notarisation on Polygon/Ethereum.',
    features: [
      'Multi-signer sequential & parallel workflows',
      'Visual drag-drop workflow builder',
      'AI clause analysis & summarisation (GPT-4o)',
      'Blockchain notarisation (Polygon/Ethereum)',
      'Stripe payment gate embedded in signing flow',
      '140+ REST API endpoints with HMAC auth',
      'White-label branding & custom email templates',
      'Automated reminder & expiry workflows',
    ],
    techStack: ['.NET 8', 'Blazor', 'Azure', 'SQL Server', 'React', 'Stripe', 'OpenAI'],
    liveUrl: 'https://docsignerhub.com',
    githubUrl: 'https://github.com/rajibmahata/DocumentSigningPlatform',
    source: 'github',
    status: 'live',
    role: 'Solo Architect & Full-Stack Developer',
    impact: 'Production SaaS with 140+ API endpoints, eIDAS-compliant audit trail, and enterprise security. Built solo end-to-end — architecture, backend, frontend, DevOps, and AI integration.',
  },
  {
    name: 'ARIA Platform',
    shortDesc: 'Enterprise AI knowledge retrieval with RAG pipelines and avatar-based interaction.',
    longDesc: 'ARIA (AI Retrieval & Interaction Avatar) is an enterprise knowledge platform that combines retrieval-augmented generation with an interactive avatar interface. It ingests company documents, builds semantic indexes, and allows employees to ask natural-language questions and get accurate, sourced answers. The hybrid search combines vector similarity with keyword BM25 for optimal recall.',
    features: [
      'Hybrid search: vector + BM25 keyword ranking',
      'Multi-tenant RAG with document-level access control',
      'Interactive AI avatar with lip-sync animation',
      'Semantic chunking with overlap for context preservation',
      'Source citation with confidence scoring',
      'Streaming responses via Server-Sent Events',
    ],
    techStack: ['Python', 'FastAPI', 'RAG', 'GPT-4o', 'ChromaDB', 'React', 'LangChain'],
    liveUrl: null,
    githubUrl: 'https://github.com/rajibmahata/AI-Avatar-RAG-Platform',
    source: 'github',
    status: 'wip',
    role: 'AI Architect & Full-Stack Developer',
    impact: 'Enterprise-grade RAG system with multi-tenant isolation, designed for law firms and financial services. Reduces document research time by 70% in pilot testing.',
  },
  {
    name: 'Solicitor CMS',
    shortDesc: 'Legal case management with visual workflow builder, document automation & client portal.',
    longDesc: 'A comprehensive case management system for solicitors and law firms. Tracks cases from intake to resolution with configurable workflows, automated document generation, deadline tracking, and a secure client communication portal. Built with Clean Architecture and CQRS patterns for maintainability at scale.',
    features: [
      'Visual workflow builder for case lifecycles',
      'Automated legal document generation from templates',
      'Client portal with secure messaging & document sharing',
      'Deadline & court date tracking with notifications',
      'Time tracking & billing integration',
      'Role-based access with matter-level permissions',
    ],
    techStack: ['.NET 8', 'Blazor', 'SQL Server', 'Azure', 'Cosmos DB'],
    liveUrl: null,
    githubUrl: 'https://github.com/rajibmahata/SolicitorCaseManagementSystem',
    source: 'github',
    status: 'wip',
    role: 'Solution Architect & Lead Developer',
    impact: 'Designed to replace legacy desktop software for mid-size law firms. Modular architecture allows phased migration from existing systems.',
  },
  {
    name: 'FoodFleet',
    shortDesc: 'Multi-branch restaurant delivery platform with location-based menu & order routing.',
    longDesc: 'A delivery management platform for restaurant chains with multiple branches. Automatically detects customer location, serves the nearest branch menu, and routes orders to the appropriate kitchen. Includes real-time order tracking, delivery zone management, and branch-level analytics.',
    features: [
      'GPS-based branch detection & menu serving',
      'Real-time order tracking with status updates',
      'Multi-branch inventory & menu management',
      'Delivery zone configuration per branch',
      'Branch-wise analytics & reporting dashboard',
    ],
    techStack: ['.NET 8', 'React', 'Azure', 'SQL Server', 'TypeScript'],
    liveUrl: null,
    githubUrl: 'https://github.com/rajibmahata/FoodFleet',
    source: 'github',
    status: 'complete',
    role: 'Full-Stack Developer',
    impact: 'Serves as a reference architecture for multi-tenant restaurant platforms. Location-based routing logic is reusable across delivery domains.',
  },
  {
    name: 'BudgetEase',
    shortDesc: 'Event expense tracker with vendor management, budget monitoring & financial reporting.',
    longDesc: 'A modern event budgeting application that helps planners track expenses, manage vendor payments, and monitor budgets in real-time. Features category-wise budget allocation, vendor communication logs, invoice tracking, and exportable financial reports.',
    features: [
      'Category-wise budget allocation & tracking',
      'Vendor management with payment schedules',
      'Real-time budget vs. actual dashboards',
      'Invoice upload & tracking',
      'Exportable financial reports (PDF/Excel)',
    ],
    techStack: ['.NET 8', 'ASP.NET Core MVC', 'SQL Server', 'Bootstrap'],
    liveUrl: null,
    githubUrl: 'https://github.com/rajibmahata/BudgetEase',
    source: 'github',
    status: 'complete',
    role: 'Full-Stack Developer',
    impact: 'Complete event financial management solution built with clean MVC architecture. Serves as a template for financial tracking applications.',
  },
  {
    name: 'AI Resume Portfolio',
    shortDesc: 'AI-powered resume parser that generates a professional single-page portfolio instantly.',
    longDesc: 'Upload a resume in PDF or DOC format and this tool uses AI to parse work history, skills, and education, then generates a clean single-page portfolio website. Built with Blazor Server for real-time interactivity and AI for intelligent content extraction.',
    features: [
      'PDF & DOC resume parsing with AI extraction',
      'Auto-generated single-page portfolio',
      'Customisable colour themes & layouts',
      'Instant preview with real-time editing',
      'One-click deploy to static hosting',
    ],
    techStack: ['Blazor Server', 'AI', 'C#', '.NET 8', 'Azure'],
    liveUrl: null,
    githubUrl: 'https://github.com/rajibmahata/AI-Resume-Portfolio',
    source: 'claude_cb',
    status: 'complete',
    role: 'AI Engineer & Full-Stack Developer',
    impact: 'Demonstrates practical AI integration in a traditional .NET stack. Reduces portfolio creation from hours to minutes.',
  },
  {
    name: 'AI Blog Portfolio',
    shortDesc: 'AI-augmented blogging platform where AI handles quality, SEO & discoverability.',
    longDesc: 'A blogging platform where authors focus purely on writing while AI handles everything else — grammar checks, readability scoring, SEO optimisation, tag suggestions, and content discoverability. Built with ASP.NET Core and integrated AI services.',
    features: [
      'AI-powered content quality scoring',
      'Automatic SEO optimisation & meta tag generation',
      'Readability analysis with actionable suggestions',
      'Smart tag & category recommendations',
      'Engagement analytics with AI-driven insights',
    ],
    techStack: ['ASP.NET Core', 'AI', 'C#', 'SQL Server', 'JavaScript'],
    liveUrl: null,
    githubUrl: 'https://github.com/rajibmahata/AI-Powered-Blog-Portfolio',
    source: 'claude_cb',
    status: 'complete',
    role: 'Full-Stack Developer & AI Integrator',
    impact: 'Showcases AI-as-an-assistant pattern — AI enhances human content rather than replacing it. Applicable to any content-heavy SaaS.',
  },
  {
    name: 'RajibLabs Platform',
    shortDesc: 'This portfolio — dark editorial design, AI-managed content & live activity tracking.',
    longDesc: 'The platform you are viewing right now. A professionally designed portfolio site with a dark editorial aesthetic, Framer Motion animations, real-time GitHub activity integration, and an AI-managed content pipeline. Built with React + TypeScript frontend and .NET 8 backend, deployed on SmarterASP.NET with continuous deployment via OpenClaw agents.',
    features: [
      'Dark editorial design with Fraunces/DM Sans typography',
      'Framer Motion staggered animations & scroll reveals',
      'Live GitHub commit feed with polling',
      'AI-managed content pipeline (8 OpenClaw agents)',
      'One-command deployment via FTP',
      'Responsive: mobile, tablet, desktop optimised',
    ],
    techStack: ['React', 'TypeScript', 'Tailwind CSS', '.NET 8', 'OpenClaw', 'Framer Motion'],
    liveUrl: 'https://rajiblabs.com',
    githubUrl: 'https://github.com/rajibmahata/rajiblabs-platform',
    source: 'localhost',
    status: 'live',
    role: 'Designer & Developer',
    impact: 'Serves as both a portfolio and a living demo of the AI agent pipeline. Designed, built, and deployed with the same agents it showcases.',
  },
];

const tabs: { key: FilterTab; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'github', label: 'GitHub' },
  { key: 'claude_cb', label: 'Claude/CB' },
  { key: 'localhost', label: 'Localhost' },
];

export default function CompletedProjectsSection() {
  const [activeFilter, setActiveFilter] = useState<FilterTab>('all');
  const [selectedProject, setSelectedProject] = useState<ProjectDetail | null>(null);
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  const filtered = activeFilter === 'all'
    ? projects
    : projects.filter(p => p.source === activeFilter);

  const counts: Record<FilterTab, number> = {
    all: projects.length,
    github: projects.filter(p => p.source === 'github').length,
    claude_cb: projects.filter(p => p.source === 'claude_cb').length,
    localhost: projects.filter(p => p.source === 'localhost').length,
  };

  return (
    <section id="projects" className="section-pad" ref={sectionRef}>
      <div className="container-site">
        <SectionLabel>PROJECT PORTFOLIO</SectionLabel>

        {/* Filter tabs */}
        <div className="flex flex-wrap gap-1 mb-8 p-1 rounded-lg"
          style={{ background: 'var(--c-bg-tertiary)', maxWidth: 'fit-content' }}
        >
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveFilter(tab.key)}
              className="px-4 py-1.5 rounded-md text-sm transition-all"
              style={{
                fontFamily: 'var(--font-heading)',
                fontWeight: activeFilter === tab.key ? 600 : 400,
                background: activeFilter === tab.key ? 'var(--c-bg-secondary)' : 'transparent',
                color: activeFilter === tab.key ? 'var(--c-text-primary)' : 'var(--c-text-muted)',
                border: activeFilter === tab.key ? '1px solid var(--c-border)' : '1px solid transparent',
                cursor: 'pointer',
              }}
            >
              {tab.label}
              <span style={{ marginLeft: 4, fontSize: 12, opacity: 0.7 }}>
                {counts[tab.key]}
              </span>
            </button>
          ))}
        </div>

        <motion.div
          key={activeFilter}
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.4 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {filtered.map(project => (
            <ProjectCard
              key={project.name}
              project={project}
              onMoreInfo={setSelectedProject}
            />
          ))}
        </motion.div>
      </div>

      {/* Detail Modal */}
      <ProjectModal
        project={selectedProject}
        onClose={() => setSelectedProject(null)}
      />
    </section>
  );
}
