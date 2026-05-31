import { useState, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import ProjectCard from '../ui/ProjectCard';
import ProjectModal from '../ui/ProjectModal';
import type { ProjectDetail } from '../ui/ProjectModal';

type FilterTab = 'all' | 'github' | 'enterprise' | 'claude_cb' | 'localhost';

export const projects: ProjectDetail[] = [
  // ─── OWN PRODUCTS ──────────────────────────────────
  {
    name: 'DocSignerHub',
    shortDesc: 'Enterprise e-signature SaaS with AI clause analysis, multi-signer workflows & blockchain notarisation.',
    longDesc: 'A complete digital signature platform built from the ground up. DocSignerHub enables businesses to send, sign, and manage documents with enterprise-grade security. Features include a visual workflow builder for complex approval chains, HMAC-signed API authentication, Stripe payment integration within signing flows, AI-powered clause summarisation using GPT-4o, and optional blockchain notarisation on Polygon/Ethereum.',
    features: ['Multi-signer sequential & parallel workflows', 'Visual drag-drop workflow builder', 'AI clause analysis & summarisation (GPT-4o)', 'Blockchain notarisation (Polygon/Ethereum)', 'Stripe payment gate embedded in signing flow', '140+ REST API endpoints with HMAC auth', 'White-label branding & custom email templates', 'Automated reminder & expiry workflows'],
    techStack: ['.NET 8', 'Blazor', 'Azure', 'SQL Server', 'React', 'Stripe', 'OpenAI'],
    liveUrl: 'https://docsignerhub.com',
    githubUrl: 'https://github.com/rajibmahata/DocumentSigningPlatform',
    source: 'github', status: 'live', role: 'Solo Architect & Full-Stack Developer',
    impact: 'Production SaaS with 140+ API endpoints, eIDAS-compliant audit trail, and enterprise security. Built solo end-to-end — architecture, backend, frontend, DevOps, and AI integration.',
  },
  {
    name: 'ARIA Platform',
    shortDesc: 'Enterprise AI knowledge retrieval with RAG pipelines and avatar-based interaction.',
    longDesc: 'ARIA (AI Retrieval & Interaction Avatar) is an enterprise knowledge platform that combines retrieval-augmented generation with an interactive avatar interface. It ingests company documents, builds semantic indexes, and allows employees to ask natural-language questions and get accurate, sourced answers.',
    features: ['Hybrid search: vector + BM25 keyword ranking', 'Multi-tenant RAG with document-level access control', 'Interactive AI avatar with lip-sync animation', 'Semantic chunking with overlap for context preservation', 'Source citation with confidence scoring', 'Streaming responses via Server-Sent Events'],
    techStack: ['Python', 'FastAPI', 'RAG', 'GPT-4o', 'ChromaDB', 'React', 'LangChain'],
    githubUrl: 'https://github.com/rajibmahata/AI-Avatar-RAG-Platform', source: 'github', status: 'wip',
    role: 'AI Architect & Full-Stack Developer',
    impact: 'Enterprise-grade RAG system with multi-tenant isolation, designed for law firms and financial services. Reduces document research time by 70% in pilot testing.',
  },

  // ─── ENTERPRISE PROJECTS (Career) ──────────────────
  {
    name: 'Pharmacy Business Transformation',
    shortDesc: 'Led pharmacy modernisation at TCS — open APIs, Azure PaaS, prescription automation at Fortune 500 scale.',
    longDesc: 'Led the development of a large-scale pharmacy modernization initiative aimed at reducing dependency on third-party vendors and creating a scalable healthcare ecosystem for TCS, a Fortune 500 retail chain. Designed and developed Open APIs for pharmacy operations, implemented prescription processing and automated customer notifications, and built scalable cloud-native solutions using Azure PaaS services. Contributed to appointment scheduling and vaccine distribution platforms during the pandemic.',
    features: ['Open APIs for pharmacy operations eliminating 3rd-party vendor dependency', 'Automated prescription processing & customer notifications', 'Scalable cloud-native architecture on Azure PaaS', 'Rule-based refill engine processing 500K+ daily events', 'Vaccine appointment scheduling for COVID-19 national rollout', 'Secure healthcare data processing with HIPAA compliance'],
    techStack: ['.NET Core', 'Blazor', 'Azure Functions', 'Logic Apps', 'Service Bus', 'Event Grid', 'Cosmos DB'], source: 'enterprise', status: 'complete',
    role: 'Assistant Consultant — TCS (USA)',
    impact: 'Reduced pharmacy vendor dependency by 100%. Automated refill system delivered 30% faster processing and 40% fewer medication errors. Supported national COVID-19 immunization scheduling.',
  },
  {
    name: 'Automated Prescription Refill System',
    shortDesc: 'Intelligent refill automation — rule-based processing, patient reminders, 30% faster pharmacy workflows.',
    longDesc: 'Designed and implemented an intelligent prescription refill platform that transformed manual refill processing into a fully automated workflow at TCS Developed rule-based refill processing, automated patient reminders and confirmations, integrated secure healthcare data processing workflows, and improved pharmacy staff productivity through automation.',
    features: ['Rule-based refill processing engine', 'Automated patient reminders & confirmations', 'Secure healthcare data integration', 'Pharmacy staff productivity dashboard', 'Real-time refill status tracking'],
    techStack: ['.NET', 'Azure Functions', 'Cosmos DB', 'Service Bus', 'Logic Apps', 'Web API'], source: 'enterprise', status: 'complete',
    role: 'Assistant Consultant — TCS (USA)',
    impact: 'Reduced refill processing time by 30%. Increased patient engagement and satisfaction. Minimized manual follow-up efforts for pharmacy staff.',
  },
  {
    name: 'Vaccine Appointment Management',
    shortDesc: 'Configurable immunization scheduling platform supporting large-scale COVID-19 vaccine distribution.',
    longDesc: 'Developed a configurable appointment scheduling system used to support large-scale immunization programs including the COVID-19 national vaccine rollout. Participated in architecture and design discussions, developed scheduling and slot management capabilities, implemented notification and reporting workflows, and supported scalable cloud deployment.',
    features: ['Configurable scheduling & slot management', 'Automated notification & reporting workflows', 'Scalable cloud deployment for high-volume processing', 'Multi-location vaccine site management', 'Real-time availability tracking'],
    techStack: ['Blazor', '.NET', 'Azure Services', 'Web API', 'Cosmos DB'], source: 'enterprise', status: 'complete',
    role: 'Assistant Consultant — TCS (USA)',
    impact: 'Simplified vaccination scheduling for millions of citizens. Improved accessibility and operational efficiency. Supported high-volume appointment processing during national health emergency.',
  },
  {
    name: 'CMT Platform — Accenture',
    shortDesc: 'Modernised telecom network provisioning — automated workflows, 40% faster processing, 95% SLA compliance.',
    longDesc: 'Contributed to the modernization of network provisioning and order fulfillment systems for Accenture, serving a major US telecommunications provider. Redesigned legacy order management workflows, automated provisioning processes, improved issue tracking and operational monitoring, and enhanced user experience and system reliability.',
    features: ['Automated network equipment provisioning', 'Legacy system modernization & workflow redesign', 'Automated issue tracking with 95% SLA compliance', 'Intuitive UI improving user satisfaction by 25%', 'Real-time operational monitoring dashboard'],
    techStack: ['ASP.NET MVC', 'Entity Framework', 'WCF', 'SQL Server', 'JavaScript', 'jQuery'], source: 'enterprise', status: 'complete',
    role: 'Software Developer — Accenture at Accenture (USA)',
    impact: 'Reduced manual operational effort by 30%. Cut processing time by 40%. Achieved 95% issue resolution within 24 hours. Improved user satisfaction scores by 25%.',
  },
  {
    name: 'Corporate Hour',
    shortDesc: 'Complete B2B classified advertisement marketplace — user management, ad publishing, admin portal.',
    longDesc: 'Designed and developed a complete classified advertisement marketplace enabling businesses to buy, sell, and promote products and services. Created user management with role-based access, advertisement publishing workflows, administrative management portal, and database architecture.',
    features: ['Role-based user management & access control', 'Advertisement publishing with approval workflows', 'Administrative management portal', 'Scalable database architecture', 'REST API for third-party integrations'],
    techStack: ['ASP.NET MVC', 'Entity Framework', 'SQL Server', 'Web API', 'JavaScript'], source: 'enterprise', status: 'complete',
    role: 'Web Developer — Keshri Software Solutions',
    impact: 'Complete B2B marketplace handling classified advertisements. Demonstrated full-stack capability from database design to frontend deployment.',
  },
  {
    name: 'Empowering Weighs',
    shortDesc: 'Digital health & wellness platform — BMR calculator, personalised recommendations, progress tracking.',
    longDesc: 'Built a healthcare-focused application designed to support sustainable weight management through personalized recommendations. Developed BMR calculation engine, implemented personalized health recommendations, built user progress tracking capabilities, and created automation-driven health guidance workflows.',
    features: ['BMR (Basal Metabolic Rate) calculation engine', 'Personalised health & nutrition recommendations', 'Progress tracking with visual dashboards', 'Automation-driven health guidance workflows', 'User goal setting & milestone tracking'],
    techStack: ['ASP.NET MVC', 'Entity Framework', 'SQL Server', 'JavaScript'], source: 'enterprise', status: 'complete',
    role: 'Web Developer — Keshri Software Solutions',
    impact: 'Full-cycle health platform from concept to deployment. Combined complex calculation algorithms with user-friendly health tracking interface.',
  },
  {
    name: 'Budgro — Online Grocery Marketplace',
    shortDesc: 'E-commerce grocery platform — order management, location-based delivery slots, payment integration.',
    longDesc: 'Developed a complete e-commerce platform for grocery ordering and home delivery management. Implemented order management workflows, developed delivery slot allocation based on location, integrated third-party payment gateways, and built order tracking and fulfillment features.',
    features: ['Complete order management lifecycle', 'Location-based delivery slot allocation', 'Third-party payment gateway integration', 'Real-time order tracking & fulfillment', 'Multi-vendor product catalogue'],
    techStack: ['ASP.NET MVC', 'Entity Framework', 'SQL Server', 'NopCommerce'], source: 'enterprise', status: 'complete',
    role: 'Web Developer — Keshri Software Solutions',
    impact: 'End-to-end e-commerce platform with location-aware delivery logistics. Full order lifecycle from cart to doorstep managed within single platform.',
  },
  {
    name: 'TRANSZOOM',
    shortDesc: 'Transportation & car rental marketplace — booking, operator management, scalable transaction processing.',
    longDesc: 'Built an online transportation marketplace connecting customers with vehicle operators across India. Developed booking and transportation workflows, designed customer and operator management modules, and built scalable backend services for transaction processing.',
    features: ['Online booking & transportation workflows', 'Customer & operator management portals', 'Scalable transaction processing backend', 'Multi-city vehicle availability tracking', 'Fleet management dashboard'],
    techStack: ['ASP.NET MVC', 'Entity Framework', 'SQL Server', 'JavaScript'], source: 'enterprise', status: 'complete',
    role: 'Web Developer — Keshri Software Solutions',
    impact: 'Connected customers with vehicle operators nationwide. Scalable architecture handling concurrent bookings across multiple cities.',
  },

  // ─── MORE SIDE PROJECTS ──────────────────────────
  {
    name: 'Solicitor CMS',
    shortDesc: 'Legal case management with visual workflow builder, document automation & client portal.',
    longDesc: 'A comprehensive case management system for solicitors and law firms. Tracks cases from intake to resolution with configurable workflows, automated document generation, deadline tracking, and a secure client communication portal.',
    features: ['Visual workflow builder for case lifecycles', 'Automated legal document generation from templates', 'Client portal with secure messaging', 'Deadline & court date tracking with notifications', 'Time tracking & billing integration', 'Role-based access with matter-level permissions'],
    techStack: ['.NET 8', 'Blazor', 'SQL Server', 'Azure', 'Cosmos DB'], githubUrl: 'https://github.com/rajibmahata/SolicitorCaseManagementSystem', source: 'github', status: 'wip',
    role: 'Solution Architect & Lead Developer',
    impact: 'Designed to replace legacy desktop software for mid-size law firms. Modular architecture allows phased migration from existing systems.',
  },
  {
    name: 'FoodFleet',
    shortDesc: 'Multi-branch restaurant delivery platform with location-based menu & order routing.',
    longDesc: 'A delivery management platform for restaurant chains with multiple branches. Automatically detects customer location, serves the nearest branch menu, and routes orders to the appropriate kitchen.',
    features: ['GPS-based branch detection & menu serving', 'Real-time order tracking with status updates', 'Multi-branch inventory & menu management', 'Delivery zone configuration per branch', 'Branch-wise analytics & reporting dashboard'],
    techStack: ['.NET 8', 'React', 'Azure', 'SQL Server', 'TypeScript'], githubUrl: 'https://github.com/rajibmahata/FoodFleet', source: 'github', status: 'complete',
    role: 'Full-Stack Developer',
    impact: 'Reference architecture for multi-tenant restaurant platforms. Location-based routing logic reusable across delivery domains.',
  },
  {
    name: 'BudgetEase',
    shortDesc: 'Event expense tracker with vendor management, budget monitoring & financial reporting.',
    longDesc: 'A modern event budgeting application that helps planners track expenses, manage vendor payments, and monitor budgets in real-time.',
    features: ['Category-wise budget allocation & tracking', 'Vendor management with payment schedules', 'Real-time budget vs. actual dashboards', 'Invoice upload & tracking', 'Exportable financial reports (PDF/Excel)'],
    techStack: ['.NET 8', 'ASP.NET Core MVC', 'SQL Server', 'Bootstrap'], githubUrl: 'https://github.com/rajibmahata/BudgetEase', source: 'github', status: 'complete',
    role: 'Full-Stack Developer',
    impact: 'Complete event financial management solution built with clean MVC architecture.',
  },
  {
    name: 'AI Resume Portfolio',
    shortDesc: 'AI-powered resume parser that generates a professional single-page portfolio instantly.',
    longDesc: 'Upload a resume in PDF or DOC format and this tool uses AI to parse work history, skills, and education, then generates a clean single-page portfolio website.',
    features: ['PDF & DOC resume parsing with AI extraction', 'Auto-generated single-page portfolio', 'Customisable colour themes & layouts', 'Instant preview with real-time editing', 'One-click deploy to static hosting'],
    techStack: ['Blazor Server', 'AI', 'C#', '.NET 8', 'Azure'], githubUrl: 'https://github.com/rajibmahata/AI-Resume-Portfolio', source: 'claude_cb', status: 'complete',
    role: 'AI Engineer & Full-Stack Developer',
    impact: 'Demonstrates practical AI integration in traditional .NET stack. Reduces portfolio creation from hours to minutes.',
  },
  {
    name: 'AI Blog Portfolio',
    shortDesc: 'AI-augmented blogging platform where AI handles quality, SEO & discoverability.',
    longDesc: 'A blogging platform where authors focus purely on writing while AI handles everything else — grammar checks, readability scoring, SEO optimisation, tag suggestions, and content discoverability.',
    features: ['AI-powered content quality scoring', 'Automatic SEO optimisation & meta tag generation', 'Readability analysis with actionable suggestions', 'Smart tag & category recommendations', 'Engagement analytics with AI-driven insights'],
    techStack: ['ASP.NET Core', 'AI', 'C#', 'SQL Server', 'JavaScript'], githubUrl: 'https://github.com/rajibmahata/AI-Powered-Blog-Portfolio', source: 'claude_cb', status: 'complete',
    role: 'Full-Stack Developer & AI Integrator',
    impact: 'Showcases AI-as-an-assistant pattern — AI enhances human content rather than replacing it.',
  },
  {
    name: 'RajibLabs Platform',
    shortDesc: 'This portfolio — dark editorial design, AI-managed content & live activity tracking.',
    longDesc: 'The platform you are viewing right now. A professionally designed portfolio site with a dark editorial aesthetic, Framer Motion animations, real-time GitHub activity integration, and an AI-managed content pipeline.',
    features: ['Dark editorial design with Fraunces/DM Sans typography', 'Framer Motion staggered animations & scroll reveals', 'Live GitHub commit feed with polling', 'AI-managed content pipeline (8 OpenClaw agents)', 'One-command deployment via FTP', 'Responsive: mobile, tablet, desktop optimised'],
    techStack: ['React', 'TypeScript', 'Tailwind CSS', '.NET 8', 'OpenClaw', 'Framer Motion'], liveUrl: 'https://rajiblabs.com', githubUrl: 'https://github.com/rajibmahata/rajiblabs-platform', source: 'localhost', status: 'live',
    role: 'Designer & Developer',
    impact: 'Serves as both a portfolio and a living demo of the AI agent pipeline.',
  },
];

const tabs: { key: FilterTab; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'enterprise', label: 'Enterprise' },
  { key: 'github', label: 'GitHub' },
  { key: 'claude_cb', label: 'AI/Claude' },
  { key: 'localhost', label: 'This Site' },
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
    enterprise: projects.filter(p => p.source === 'enterprise').length,
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

      <ProjectModal project={selectedProject} onClose={() => setSelectedProject(null)} />
    </section>
  );
}
