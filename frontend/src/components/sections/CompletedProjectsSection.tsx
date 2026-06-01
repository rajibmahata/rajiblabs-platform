import { useState, useRef, useEffect } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import ProjectCard from '../ui/ProjectCard';
import ProjectModal from '../ui/ProjectModal';
import { getProjects } from '../../services/api';
import type { Project } from '../../types';
import type { ProjectDetail } from '../ui/ProjectModal';

type FilterTab = 'all' | 'github' | 'enterprise' | 'claude_cb' | 'localhost';

// ── Fallback hardcoded projects (used when API is unavailable) ──

const fallbackProjects: ProjectDetail[] = [
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
    shortDesc: 'End-to-end digital transformation of a national US pharmacy chain — replacing vendor dependency with open Azure APIs, automating prescription processing, and deploying real-time patient notifications.',
    longDesc: 'A 48-week engagement to replace a third-party vendor system that had locked the pharmacy into high costs, limited data control, and brittle integrations. The core problem: every prescription refill relied on an external vendor for patient data processing. Staff were making hundreds of manual phone calls daily. There was no direct API control, no real-time visibility into patient status, and no ability to adapt the system to business rule changes without vendor approval. The solution was a comprehensive Azure-hosted platform: a Rule Engine that processed prescription data in real time, a set of Progressive Web Applications (PWAs) for staff and patients, and an API layer that integrated directly with all internal and external pharmacy systems. Patients received automated reminders via SMS and voice calls, and could confirm, reschedule, or cancel refills through a personalised online experience — no phone call required. The Rule Engine was the architectural centrepiece: it received prescription data from the data lake, applied business rules to identify upcoming refills, triggered the appropriate notification channel per patient, and updated status in real time. The system also integrated barcode scanning and payment processing at storefront for streamlined pickup.',
    features: ['Open APIs eliminating vendor dependency', 'Real-time Rule Engine processing prescription data', 'Multi-channel patient notifications (SMS/voice/online)', 'PWA for staff and patient workflows', 'Barcode scanning & payment integration at storefront', 'Full data ownership returned to pharmacy'],
    techStack: ['.NET Core', '.NET 6', 'Blazor', 'Azure Functions', 'Logic Apps', 'Service Bus', 'Event Grid', 'Cosmos DB', 'AngularJS', 'Node.js', 'C#'],
    source: 'enterprise', status: 'complete', role: 'Assistant Consultant — TCS (Healthcare, USA)',
    impact: '30% faster refill processing · 40% fewer medication errors · 25% higher patient satisfaction · Eliminated manual phone calls · 100% data ownership · Scaled for national COVID-19 vaccine rollout',
  },
  {
    name: 'Automated Prescription Refill System',
    shortDesc: 'Rule-engine-driven prescription refill automation that analyses dispensed medications, predicts upcoming refill windows, and triggers personalised multi-channel patient reminders — reducing staff phone call volume to near zero.',
    longDesc: 'Before this system, pharmacy staff were making hundreds of phone calls every day to remind patients about upcoming prescription refills. The process was entirely manual, didn\'t scale with patient volume, and was prone to missed calls, delayed refills, and patient dissatisfaction. The solution was an intelligent refill automation platform built on Azure. At its core was a custom Rule Engine that consumed prescription dispensing data from a data lake, identified patients with upcoming refills based on their medication schedules, and triggered the appropriate notification — SMS, voice call, or online reminder — at the right time. Patients received a personalised SMS link directing them to a secure priority checkout UI where they could confirm or cancel their refill in seconds. The system also gave pharmacy staff a real-time dashboard showing refill queue status, patient responses, and pending pickups — without any manual intervention required. The system integrated seamlessly with the pharmacy\'s existing infrastructure: prescription records, patient profiles, payment processing, and barcode scanning at storefront for collection. Every notification event and patient action was logged, creating an auditable trail for compliance and reporting.',
    features: ['Rule-based refill processing engine', 'Multi-channel patient notifications (SMS/voice/online)', 'Real-time staff dashboard with refill queue status', 'Integration with existing pharmacy infrastructure', 'Auditable compliance trail for every event', 'Scalable to future patient volume with zero rework'],
    techStack: ['.NET Core', 'Azure Functions', 'Logic Apps', 'Service Bus', 'Cosmos DB', 'C#', 'IVR Integration'],
    source: 'enterprise', status: 'complete', role: 'Assistant Consultant — TCS (Healthcare, USA)',
    impact: 'Eliminated 300+ daily manual phone calls · 30% faster refill processing · 40% reduction in medication errors · 25% improvement in patient satisfaction',
  },
  {
    name: 'Vaccine Appointment System',
    shortDesc: 'Configurable vaccine scheduling platform deployed nationally during COVID-19 immunisation — handling registration, time-slot scheduling, government guideline compliance, and automated notifications at national scale.',
    longDesc: 'During the COVID-19 pandemic, pharmacies became front-line vaccine distribution centres. The pharmacy chain needed a system — fast — that could handle appointment booking across hundreds of locations, enforce government prioritisation guidelines, manage time-slot capacity, and provide a seamless experience for customers who had never booked a pharmacy appointment before. I played a pivotal role in designing and building the configurable appointment booking system that powered this rollout. The platform was built to be configuration-first: each pharmacy location could set its own time-slot windows, capacity limits, and vaccine type availability without any code changes. Government guidelines for vaccine priority groups were enforced at the registration level. The customer experience was deliberately simple: register, select a time slot, receive a confirmation. The system sent automated notifications at booking, 24 hours before, and on the day — reducing no-shows and ensuring customers arrived prepared.',
    features: ['Configurable per-location scheduling without code changes', 'Government guideline enforcement at registration', 'Automated multi-touchpoint notifications', 'National-scale deployment across pharmacy network', 'Zero downtime during peak COVID-19 demand', 'Automated compliance reporting'],
    techStack: ['Blazor PWA', 'ASP.NET MVC', '.NET 6', 'Azure App Service', 'SQL Server', 'Azure Functions', 'C#'],
    source: 'enterprise', status: 'complete', role: 'Assistant Consultant — TCS (Healthcare, USA)',
    impact: 'National deployment across pharmacy network · Zero downtime during peak demand · Automated compliance reporting · Reduced no-show rates via multi-touchpoint notifications',
  },
  {
    name: 'CMT Platform — Accenture',
    shortDesc: 'Network equipment provisioning and order automation platform for a US regional telecommunications provider — automating provisioning workflow, reducing manual intervention by 30% and slashing order processing time by 40%.',
    longDesc: 'The client is a regional telecommunications provider serving Ohio, Hawaii, and the Dayton metro area. Their order management system for network equipment setup was a legacy platform — manual, fragmented, and unable to keep pace with business growth. Field engineers were spending significant time on configuration tasks that should have been automated, and order fulfilment was slow. During my time at Accenture (2016–2019), I was responsible for the design, development, and implementation of the Communication Media Technology (CMT) application — a complete overhaul of the order management and network provisioning workflow. The CMT platform captured and stored every processing detail from order initiation through to network provisioning. It automated the configuration steps that previously required manual engineer intervention, integrated with network devices for remote setup, and provided an issue resolution ticket system that tracked and resolved user-reported problems in real time.',
    features: ['Automated network equipment provisioning', 'Legacy system modernisation & workflow redesign', 'Automated issue tracking with 95% SLA compliance', 'Configuration templates replacing manual setup', 'Real-time operational monitoring dashboard'],
    techStack: ['ASP.NET MVC', 'Entity Framework', 'WCF', 'SQL Server', 'JavaScript', 'jQuery', 'AJAX', 'C#'],
    source: 'enterprise', status: 'complete', role: 'Software Developer — Accenture (Telecom, USA)',
    impact: '30% reduction in manual intervention · 40% decrease in order fulfilment time · 25% improvement in user satisfaction · 95% issue resolution within 24 hours',
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
  {
    name: 'MedRemind',
    shortDesc: 'AI-powered medication reminder app with two-stage OCR pipeline (Azure Document Intelligence + GPT-4o-mini) supporting 10 languages including full RTL — photograph a prescription label and get automated reminders.',
    longDesc: 'Medication non-adherence is one of the most costly and preventable problems in healthcare — patients miss doses because reminders are inconvenient, confusing, or set up incorrectly. MedRemind is an AI-first solution: point your phone camera at a prescription label, and the app does the rest. The two-stage OCR pipeline is the technical core. Stage one uses Azure Document Intelligence to extract raw text from the prescription label image — handling varied fonts, print quality, and label formats. Stage two passes the extracted text to GPT-4o-mini with a structured prompt that parses the medication name, dosage, frequency, and duration into a structured JSON schedule. This two-stage approach is significantly more accurate than single-model OCR on the varied formats of real-world prescription labels. Once the schedule is parsed, the app creates reminder entries and schedules notifications through the device\'s native notification system. The reminder text is localised into the patient\'s preferred language — the app supports 10 languages covering major Indian and global markets, with full RTL support for Arabic and Urdu.',
    features: ['Two-stage OCR: Azure Document Intelligence → GPT-4o-mini', '10-language support including full RTL for Arabic/Urdu', 'Cross-platform (iOS + Android) from single React Native codebase', 'Structured JSON extraction of medication details', 'Native push notification scheduling', 'No app store required — PWA installable'],
    techStack: ['React Native', 'Expo', 'Python FastAPI', 'Azure Document Intelligence', 'GPT-4o-mini', 'SQL Server', 'i18n (10 languages)'],
    githubUrl: 'https://github.com/rajibmahata/MedRemind',
    source: 'github', status: 'complete', role: 'Solo Architect & Full-Stack Developer',
    impact: 'Two-stage AI pipeline achieving higher accuracy than single-model OCR · 10-language accessibility · Cross-platform from single codebase',
  },
  {
    name: 'ArtForge',
    shortDesc: 'Agentic drawing portfolio platform with multi-agent AI validation pipeline — Duplicate Detector, Quality Validator, and Originality Scorer — ensuring portfolio quality at scale without human curation.',
    longDesc: 'ArtForge was built to solve a problem that every creative portfolio platform faces: how do you maintain quality at scale without a human curator reviewing every submission? The answer is a multi-agent validation pipeline. When an artist submits a drawing, it enters the ArtForge validation pipeline. The Duplicate Detector uses vector embedding similarity search (RAG) to check whether the submitted artwork is substantively similar to existing entries in the portfolio — catching both exact duplicates and near-duplicates. The Quality Validator analyses the image for technical quality indicators: resolution, composition, use of negative space, linework consistency. The Originality Scorer assesses whether the style and composition are derivative of a reference corpus or genuinely novel. Only artwork that passes all three agent stages is published to the portfolio. Artists whose work is rejected receive a specific reason from the relevant agent — not a generic rejection message.',
    features: ['Three-agent validation pipeline (Duplicate, Quality, Originality)', 'RAG-based similarity search for duplicate detection', 'Agent-level rejection feedback (not generic)', 'Vector embeddings stored in ChromaDB', 'Claude API for quality and originality scoring'],
    techStack: ['React 18', 'Python FastAPI', 'Claude API', 'ChromaDB', 'RAG', 'Vector embeddings', 'Azure'],
    githubUrl: 'https://github.com/rajibmahata/ArtForge',
    source: 'github', status: 'complete', role: 'AI Architect & Full-Stack Developer',
    impact: 'Multi-agent quality assurance at scale · Automated curation eliminating human reviewer bottleneck · Proof-of-concept for domain-agnostic agent pipelines',
  },
  {
    name: 'AI Resume Reviewer',
    shortDesc: 'Seven-agent AI career platform — reviews resumes, personalises feedback, and generates role-specific recommendations using RAG against a corpus of successful resumes.',
    longDesc: 'Most AI resume tools give generic feedback: "Add more keywords. Use action verbs." They don\'t know what a strong resume looks like for a .NET engineer applying to a senior role at an Indian IT consultancy versus a fintech startup. AIResumeReviewer does. The seven-agent pipeline breaks the resume review into specialised functions. The ATS Scanner checks whether the resume will pass applicant tracking system filters for the target role. The Keyword Gap Agent compares the resume against the target job description and identifies missing skills. The Achievement Phrasing Agent rewrites bullet points to follow the XYZ formula (Accomplished X, as measured by Y, by doing Z). The Formatting Agent flags structural issues that reduce readability. The Industry Calibration Agent benchmarks the resume against norms for the specific sector. The Role Matching Agent scores the overall fit. The Rewrite Agent produces a complete revised draft. The RAG system uses a corpus of high-quality resume examples (anonymised) to ground the agents\' recommendations.',
    features: ['Seven specialised AI agents for distinct review functions', 'ATS compatibility scanner', 'XYZ formula achievement rewriting', 'Industry-specific calibration against sector norms', 'Full revised resume draft as final output', 'RAG personalisation against high-quality resume corpus'],
    techStack: ['.NET 8 Minimal API', 'React 18', 'Python FastAPI', 'RAG', 'GPT-4o', 'ChromaDB'],
    githubUrl: 'https://github.com/rajibmahata/AIResumeReviewer',
    source: 'github', status: 'complete', role: 'AI Engineer & Full-Stack Developer',
    impact: 'Seven-agent pipeline providing role-specific, data-grounded resume feedback · Full rewrite draft produced as final output',
  },
  {
    name: 'AgentTube (SahajSeva)',
    shortDesc: 'AI-powered PWA that helps citizens fill Annapurna Yojana government welfare forms in Bengali, Hindi, and English — using agentic OCR and conversational AI for users with low digital literacy.',
    longDesc: 'The Annapurna Yojana scheme provides food security support to eligible households in India, but application forms present a significant barrier to the people who need the scheme most: those with low digital literacy, who may not read the form language fluently, and who have no one to help them navigate the process. AgentTube is a conversational form assistant. The user opens the PWA (no app store required — installable from a browser), selects their language (Bengali, Hindi, or English), and the app guides them through each field of the Annapurna Yojana form. If they have an existing document (identity card, ration card), they can photograph it and the GPT-4o OCR pipeline extracts the relevant information to pre-fill the form. The DeepSeek V3 Q&A layer handles questions: "What does this field mean?", "Do I qualify for this scheme?", "What documents do I need?" — answered in the user\'s chosen language. The conversational design means users with no experience of digital forms can complete the application without external help.',
    features: ['Three-language support: Bengali, Hindi, English', 'GPT-4o document OCR for ID/ration card pre-filling', 'DeepSeek V3 conversational Q&A', 'PWA — no app store, works on low-end Android', 'Designed for citizens with low digital literacy', 'Social impact: government services without intermediaries'],
    techStack: ['React PWA', 'GPT-4o (vision/OCR)', 'DeepSeek V3 (Q&A)', '.NET 8 API', 'SQL Server', 'Bengali/Hindi/English i18n'],
    githubUrl: 'https://github.com/rajibmahata/AgentTube',
    source: 'github', status: 'wip', role: 'AI Engineer & Full-Stack Developer',
    impact: 'Making government welfare accessible to digitally unfamiliar citizens · No intermediaries required · Three-language conversational assistance',
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

// ── Map API Project → ProjectDetail ──

function apiProjectToDetail(p: Project): ProjectDetail {
  const source = p.liveUrl?.includes('docsignerhub') || p.liveUrl?.includes('rajiblabs')
    ? 'localhost'
    : p.githubUrl ? 'github' : 'enterprise';

  let status: ProjectDetail['status'] = 'wip';
  if (p.status === 'deployed') status = 'live';
  else if (p.status === 'planning') status = 'wip';
  else if (p.status === 'development') status = 'wip';
  else if (p.status === 'qa') status = 'beta';

  return {
    name: p.title,
    shortDesc: p.description.length > 120 ? p.description.substring(0, 120) + '...' : p.description,
    longDesc: p.description,
    features: [],
    techStack: p.techStack,
    liveUrl: p.liveUrl,
    githubUrl: p.githubUrl,
    source,
    status,
    role: 'Developer',
    impact: '',
  };
}

// ── Tabs ──

const tabs: { key: FilterTab; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'enterprise', label: 'Enterprise' },
  { key: 'github', label: 'GitHub' },
  { key: 'claude_cb', label: 'AI/Claude' },
  { key: 'localhost', label: 'This Site' },
];

// ── Component ──

export default function CompletedProjectsSection() {
  const [activeFilter, setActiveFilter] = useState<FilterTab>('all');
  const [selectedProject, setSelectedProject] = useState<ProjectDetail | null>(null);
  const [projects, setProjects] = useState<ProjectDetail[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  useEffect(() => {
    let cancelled = false;
    getProjects()
      .then(apiProjects => {
        if (!cancelled) {
          const mapped = apiProjects.map(apiProjectToDetail);
          // If the API returned data, use it; otherwise stay with fallback
          setProjects(mapped.length > 0 ? mapped : fallbackProjects);
        }
      })
      .catch(() => {
        if (!cancelled) setProjects(fallbackProjects);
      })
      .finally(() => {
        if (!cancelled) setIsLoaded(true);
      });
    return () => { cancelled = true; };
  }, []);

  // While loading, show nothing (or a subtle skeleton)
  const displayProjects = isLoaded ? projects : fallbackProjects;

  const filtered = activeFilter === 'all'
    ? displayProjects
    : displayProjects.filter(p => p.source === activeFilter);

  const counts: Record<FilterTab, number> = {
    all: displayProjects.length,
    enterprise: displayProjects.filter(p => p.source === 'enterprise').length,
    github: displayProjects.filter(p => p.source === 'github').length,
    claude_cb: displayProjects.filter(p => p.source === 'claude_cb').length,
    localhost: displayProjects.filter(p => p.source === 'localhost').length,
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
