import type { Project, Activity, Profile, GitHubSummary, WipData } from '../types';

// ─────────────────────────────────────────────────────
// FALLBACK DATA — used when the backend API is unavailable
//
// ALL DATES are real (from GitHub API) or best-known estimates.
// No Date.now()-relative timestamps. No fabricated star counts.
// What you see reflects reality.
// ─────────────────────────────────────────────────────

export const fallbackProjects: Project[] = [
  {
    id: '1',
    title: 'DocSignerHub',
    slug: 'docsignerhub',
    description: 'Digital signature SaaS platform with AI clause analysis, multi-signer workflows, blockchain notarisation, and Stripe payment integration. 140+ REST API endpoints, HMAC-signed auth.',
    techStack: ['.NET 8', 'Blazor', 'SQL Server', 'Azure', 'Stripe', 'OpenAI'],
    githubUrl: 'https://github.com/rajibmahata/DocumentSigningPlatform',
    liveUrl: 'https://docsignerhub.com',
    status: 'development',
    createdAt: '2026-04-06T06:01:52.000Z',
    updatedAt: '2026-05-27T06:01:47.000Z',
    lastCommitAt: '2026-05-27T06:01:42.000Z',       // last push: May 27, 2026
  },
  {
    id: '2',
    title: 'ARIA — AI Avatar RAG Platform',
    slug: 'ai-avatar-rag',
    description: 'Enterprise AI knowledge platform with RAG architecture, no-code multi-agent pipeline builder, and hybrid vector+BM25 search. Designed for on-premise deployment with zero vendor lock-in.',
    techStack: ['Python', 'FastAPI', 'GPT-4o', 'ChromaDB', 'LangChain', 'React'],
    githubUrl: 'https://github.com/rajibmahata/AI-Avatar-RAG-Platform',
    liveUrl: null,
    status: 'planning',
    createdAt: '2026-05-01T00:00:00.000Z',
    updatedAt: '2026-05-01T00:00:00.000Z',
    lastCommitAt: null,                                // private repo — no public push data
  },
  {
    id: '3',
    title: 'Solicitor Case Management',
    slug: 'solicitor-cms',
    description: 'Legal enterprise workflow platform with visual case flow builder, automated document generation, deadline tracking, and secure client portal for mid-size law firms.',
    techStack: ['.NET 8', 'Blazor', 'SQL Server', 'Azure', 'Cosmos DB'],
    githubUrl: 'https://github.com/rajibmahata/SolicitorCaseManagementSystem',
    liveUrl: null,
    status: 'planning',
    createdAt: '2026-04-15T00:00:00.000Z',
    updatedAt: '2026-04-15T00:00:00.000Z',
    lastCommitAt: null,                                // private repo — no public push data
  },
  {
    id: '4',
    title: 'Rajib Labs Platform',
    slug: 'rajiblabs',
    description: 'AI-powered portfolio and software lab. Auto-populated from GitHub, managed by 17 OpenClaw agents. This very platform.',
    techStack: ['.NET 8', 'React', 'TypeScript', 'Tailwind CSS', 'SQLite', 'OpenClaw'],
    githubUrl: 'https://github.com/rajibmahata/rajiblabs-platform',
    liveUrl: 'https://rajiblabs.com',
    status: 'deployed',
    createdAt: '2026-05-30T15:11:41.000Z',
    updatedAt: '2026-07-06T05:16:37.000Z',
    lastCommitAt: '2026-07-06T05:16:34.000Z',         // last push: today
  },
  {
    id: '5',
    title: 'LexVault — Legal Document RAG',
    slug: 'lexvault',
    description: 'Legal document intelligence platform with dual-pipeline architecture: LLM-assisted knowledge base ingestion + zero-LLM confidence scoring using hybrid search (dense + sparse BM42) on Qdrant. On-premise Windows Server deployment.',
    techStack: ['.NET 8', 'Qdrant', 'RAG', 'Hybrid Search', 'Azure OpenAI', 'Redis'],
    githubUrl: 'https://github.com/rajibmahata/Legal-Document-RAG-System-LEXVAULT',
    liveUrl: null,
    status: 'development',
    createdAt: '2026-06-24T04:34:11.000Z',
    updatedAt: '2026-06-24T17:18:12.000Z',
    lastCommitAt: '2026-06-24T17:18:07.000Z',         // last push: Jun 24, 2026
  },
  {
    id: '6',
    title: 'AI Student Tutor',
    slug: 'math-tutor-ai',
    description: 'Multi-role AI-powered personalized learning platform with 12 AI agents — voice-first tutoring, content generation from PDFs, auto-assessment, gamification, and human-in-the-loop validation. Supports 4 languages.',
    techStack: ['Python', 'FastAPI', 'LangGraph', 'Next.js', 'PostgreSQL', 'Qdrant', 'OpenAI'],
    githubUrl: 'https://github.com/rajibmahata/Math-tutor-AI-Agent',
    liveUrl: null,
    status: 'development',
    createdAt: '2026-06-19T04:17:24.000Z',
    updatedAt: '2026-07-03T06:40:50.000Z',
    lastCommitAt: '2026-07-03T06:40:47.000Z',         // last push: Jul 3, 2026
  },
];

// ── Activities: derived from real commits (GitHub API, 2026-07-06) ──
export const fallbackActivities: Activity[] = [
  {
    id: 'a1',
    projectId: '4',
    type: 'commit',
    title: 'feat: pre-flight checks, source audit, stats integrity verification',
    description: 'Portfolio agent self-improvement — mandatory pre-flight checks, GitHub stats cross-verification, expanded report format',
    timestamp: '2026-07-06T05:16:26.000Z',
  },
  {
    id: 'a2',
    projectId: '6',
    type: 'commit',
    title: 'feat: PWA support + responsive design overhaul',
    description: 'Added Progressive Web App manifest and service worker; responsive layout for mobile tutoring experience',
    timestamp: '2026-07-03T06:40:41.000Z',
  },
  {
    id: 'a3',
    projectId: '6',
    type: 'commit',
    title: 'feat: v2.1 complete — notifications, content pipeline, enhanced portals',
    description: 'Notification system, content generation pipeline, enhanced student/teacher portals, sprint 1 QA pass',
    timestamp: '2026-07-03T06:28:55.000Z',
  },
  {
    id: 'a4',
    projectId: '4',
    type: 'commit',
    title: 'feat: PO self-improve — GITHUB_TOKEN health check + bidder agent check',
    description: 'Daily standup enhancements: token health monitoring, bidder agent existence verification, state file cross-check',
    timestamp: '2026-06-30T03:38:03.000Z',
  },
  {
    id: 'a5',
    projectId: '5',
    type: 'commit',
    title: 'Initial code commit — LexVault RAG pipeline',
    description: 'Core project scaffold: Qdrant hybrid search setup, dual-pipeline architecture foundation, Azure OpenAI integration',
    timestamp: '2026-06-24T17:17:58.000Z',
  },
  {
    id: 'a6',
    projectId: '1',
    type: 'commit',
    title: 'Merge PR #67 — project description and documentation',
    description: 'Copilot-assisted README rewrite with architecture overview, API endpoint catalogue, and setup guide',
    timestamp: '2026-05-27T06:01:42.000Z',
  },
  {
    id: 'a7',
    projectId: '1',
    type: 'commit',
    title: 'Validate documentation update',
    description: 'Cross-checked documentation accuracy against current codebase; corrected endpoint signatures',
    timestamp: '2026-05-27T05:48:07.000Z',
  },
  {
    id: 'a8',
    projectId: '1',
    type: 'milestone',
    title: 'DocSignerHub — Multi-signer workflows operational',
    description: 'Sequential and parallel signing chains with visual workflow builder live on docsignerhub.com',
    timestamp: '2026-05-20T00:00:00.000Z',
  },
];

export const fallbackProfile: Profile = {
  id: 'p1',
  fullName: 'Rajib Mahata',
  title: 'Senior Software Architect | AI & SaaS Platform Builder',
  bio: 'Independent software architect with 10+ years building production SaaS platforms, AI systems, and cloud-native applications. Specialising in .NET, Azure, and AI/LLM integrations.',
  skills: ['.NET 8/10', 'C#', 'ASP.NET Core', 'Blazor', 'React', 'Python FastAPI', 'Azure Cloud', 'Azure DevOps', 'Microservices', 'CQRS & Design Patterns', 'SQL Server', 'Cosmos DB', 'OpenAI/Gemini APIs', 'RAG Systems', 'Docker', 'GitHub Copilot'],
  socialLinks: {
    github: 'https://github.com/rajibmahata',
    linkedin: 'https://linkedin.com/in/rajib-mahata',
  },
  career: [
    {
      company: 'Fortune 500 Healthcare',
      role: 'Solutions Architect',
      period: 'Aug 2019 – Present',
      client: 'Healthcare & Pharmacy (USA)',
      achievements: [
        'Led development of open APIs, reducing pharmacy vendor dependency by 100%',
        'Architected data lake on Azure for raw prescription/patient data ingestion and processing',
        'Automated Prescription Refill System — 30% faster processing, 40% fewer medication errors',
        'Vaccine Appointment System — streamlined COVID-19 immunization scheduling nationally',
        'Built Rule Engine (CQRS) on Azure PaaS processing 500K+ daily prescription events',
        'Deployed PWAs on Azure Cloud for secure, scalable pharmacy interfaces',
        'Integrated secure payment (MParks), barcode scanning, voice/SMS notifications',
      ],
      techStack: ['.NET 8', 'Blazor', 'Azure Functions', 'Logic Apps', 'Service Bus', 'Event Grid', 'Cosmos DB', 'Azure Data Factory', 'AngularJS', 'Open API'],
      color: 'var(--c-accent-blue)',
    },
    {
      company: 'Telecom Enterprise',
      role: 'Platform Engineer',
      period: 'Jul 2016 – Feb 2019',
      client: 'Telecommunications (USA)',
      achievements: [
        'Designed and built CMT application automating network equipment provisioning',
        'Reduced manual intervention by 30%, processing time by 40%',
        'Achieved 95% issue resolution within 24 hours via automated ticket system',
        'Built intuitive UI improving user satisfaction scores by 25%',
      ],
      techStack: ['ASP.NET MVC', 'WCF', 'Entity Framework', 'SQL Server', 'JavaScript'],
      color: 'var(--c-accent-teal)',
    },
    {
      company: 'Product Studio',
      role: 'Full-Stack Developer',
      period: 'Mar 2013 – Apr 2016',
      achievements: [
        'Built Corporate Hour — B2B media advertisement & trade platform',
        'Developed Cinematic Lens — product visual storytelling platform',
        'Created TRANSZOOM — car rental & TruckIt365 freight matching solution',
        'Full-stack ownership: database design to frontend deployment',
      ],
      techStack: ['ASP.NET MVC', 'SQL Server', 'JavaScript', 'HTML/CSS', 'AJAX'],
      color: 'var(--c-accent-gold)',
    },
  ],
};

// ── GitHubSummary: real stats from GitHub API (2026-07-06) ──
export const fallbackGitHubSummary: GitHubSummary = {
  stats: [
    { value: '30', label: 'repos', icon: '📦' },
    { value: '8', label: 'languages', icon: '🔤' },
    { value: '6', label: 'active projects', icon: '🚀' },
    { value: 'Kolkata', label: 'location', icon: '📍' },
  ],
  topRepos: [
    { name: 'rajiblabs-platform',    language: 'TypeScript', stars: 0, forks: 0, updated: '6 Jul 2026',    langColor: '#3178C6' },
    { name: 'Math-tutor-AI-Agent',    language: 'Python',     stars: 0, forks: 0, updated: '3 Jul 2026',    langColor: '#3572A5' },
    { name: 'AI_Student_Tutor',       language: 'TypeScript', stars: 0, forks: 0, updated: '28 Jun 2026',   langColor: '#3178C6' },
    { name: 'Legal-Document-RAG-System-LEXVAULT', language: 'C#', stars: 0, forks: 0, updated: '24 Jun 2026', langColor: '#178600' },
    { name: 'DocumentSigningPlatform',language: 'C#',          stars: 0, forks: 0, updated: '27 May 2026',   langColor: '#178600' },
    { name: 'FoodFleet',              language: 'C#',          stars: 0, forks: 0, updated: '1 May 2026',    langColor: '#178600' },
  ],
};

// ── WipData: real commits + conservative progress estimates ──
export const fallbackWipData: WipData = {
  projects: [
    {
      name: 'DocSignerHub',
      stack: '.NET 8 · Blazor · Azure · SQL Server · HMAC-SHA256',
      progress: 70,
      lastActivity: '27 May 2026',
      status: 'live' as const,
    },
    {
      name: 'AI Student Tutor',
      stack: 'FastAPI · LangGraph · Next.js · PostgreSQL · Qdrant',
      progress: 40,
      lastActivity: '3 Jul 2026',
      status: 'wip' as const,
    },
    {
      name: 'ARIA Platform',
      stack: 'FastAPI · GPT-4o · ChromaDB · React · LangChain',
      progress: 30,
      lastActivity: 'May 2026',
      status: 'wip' as const,
    },
    {
      name: 'LexVault',
      stack: '.NET 8 · Qdrant · Hybrid Search · RAG · Azure OpenAI',
      progress: 15,
      lastActivity: '24 Jun 2026',
      status: 'wip' as const,
    },
    {
      name: 'Solicitor CMS',
      stack: '.NET 8 · Blazor · SQL Server · Azure · Cosmos DB',
      progress: 10,
      lastActivity: 'Apr 2026',
      status: 'wip' as const,
    },
  ],
  commits: [
    { hash: 'bb22975', message: 'feat: pre-flight checks, source audit, stats integrity verification', repoName: 'rajiblabs-platform', timestamp: '6 Jul 2026' },
    { hash: 'cc26e21', message: 'feat: PWA support + responsive design overhaul', repoName: 'Math-tutor-AI-Agent', timestamp: '3 Jul 2026' },
    { hash: '372dc57', message: 'feat: v2.1 — notifications, content pipeline, enhanced portals', repoName: 'Math-tutor-AI-Agent', timestamp: '3 Jul 2026' },
    { hash: '007e893', message: 'fix: openai dependency conflict — bump 1.51.0→>=1.52.0', repoName: 'Math-tutor-AI-Agent', timestamp: '3 Jul 2026' },
    { hash: 'dd692f8', message: 'feat: PO self-improve — GITHUB_TOKEN health check', repoName: 'rajiblabs-platform', timestamp: '30 Jun 2026' },
    { hash: '38337d3', message: 'Initial code commit — LexVault RAG pipeline', repoName: 'Legal-Document-RAG-System-LEXVAULT', timestamp: '24 Jun 2026' },
  ],
};
