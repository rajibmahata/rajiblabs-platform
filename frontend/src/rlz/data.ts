// RajibLabs homepage content — REAL data only (existing site + verified repos + resume).
// Never invent metrics, companies, repo URLs, or live links here.

export const HERO_STATS = [
  { value: 12, suffix: "+", label: "Years Experience" },
  { value: 30, suffix: "+", label: "Open Repositories" },
  { value: 6, suffix: "", label: "Products Live" },
];

export const TYPING_PHRASES = [
  "designing AI-native architectures...",
  "shipping LLM-powered products...",
  "scaling event-driven systems...",
  "turning ideas into intelligence.",
];

export interface MarqueeTech { name: string; icon: string }
export const MARQUEE_TECH: MarqueeTech[] = [
  { name: ".NET", icon: "code" },
  { name: "C#", icon: "data_object" },
  { name: "Azure", icon: "cloud" },
  { name: "React", icon: "hub" },
  { name: "TypeScript", icon: "terminal" },
  { name: "Python", icon: "memory" },
  { name: "FastAPI", icon: "bolt" },
  { name: "Docker", icon: "deployed_code" },
  { name: "Kubernetes", icon: "lan" },
  { name: "OpenAI", icon: "smart_toy" },
  { name: "SQL Server", icon: "database" },
  { name: "Cosmos DB", icon: "storage" },
];

export interface Expertise { icon: string; iconClass: string; title: string; desc: string; chips: string[]; span: string }
export const EXPERTISE: Expertise[] = [
  {
    icon: "smart_toy", iconClass: "rlz-icon-violet", title: "AI & LLM Engineering",
    desc: "Production-grade AI systems — RAG pipelines, multi-agent workflows and LLM orchestration wired directly into business workflows.",
    chips: ["RAG", "Agents", "Embeddings", "Vector DBs"], span: "rlz-b-6",
  },
  {
    icon: "account_tree", iconClass: "rlz-icon-cyan", title: "Software Architecture",
    desc: "Scalable system design for enterprise scale — .NET microservices, event-driven cores and domain boundaries that stay maintainable.",
    chips: ["Microservices", "DDD", "CQRS", "Event-Driven"], span: "rlz-b-6",
  },
  {
    icon: "cloud", iconClass: "rlz-icon-green", title: "Cloud-Native & DevOps",
    desc: "Azure-hosted platforms with data lakes, serverless functions and CI/CD pipelines built for resilience and zero-downtime delivery.",
    chips: ["Azure", "Docker", "CI/CD", "Serverless"], span: "rlz-b-4",
  },
  {
    icon: "rocket_launch", iconClass: "rlz-icon-amber", title: "SaaS Product Engineering",
    desc: "End-to-end product builds — auth, payments, multi-tenancy and white-label APIs. DocSignerHub and PestFlow are live.",
    chips: ["Multi-tenant", "Stripe", "White-label"], span: "rlz-b-4",
  },
  {
    icon: "hub", iconClass: "rlz-icon-blue", title: "API & Systems Integration",
    desc: "DocuSign, payment rails and pharmacy-system connectors — robust integrations that keep enterprise data flowing reliably.",
    chips: ["REST", "DocuSign", "Webhooks"], span: "rlz-b-4",
  },
];

export interface ArchLayer { icon: string; iconClass: string; title: string; desc: string; tag: string }
export const ARCH_LAYERS: ArchLayer[] = [
  { icon: "forum", iconClass: "rlz-icon-violet", title: "Experience Layer", desc: "Web, mobile & PWA interfaces", tag: "React · TypeScript · PWA" },
  { icon: "smart_toy", iconClass: "rlz-icon-fuchsia", title: "Intelligence Layer", desc: "LLM orchestration, RAG & agents", tag: "LangChain · OpenAI · RAG" },
  { icon: "account_tree", iconClass: "rlz-icon-cyan", title: "Service Mesh", desc: "Domain-driven services with event-driven backbone", tag: ".NET · FastAPI · Service Bus" },
  { icon: "database", iconClass: "rlz-icon-green", title: "Data Layer", desc: "Relational, vector & document stores", tag: "SQL Server · Cosmos DB · Qdrant" },
  { icon: "shield", iconClass: "rlz-icon-amber", title: "Trust Layer", desc: "Auth, audit trails & secure APIs", tag: "OAuth2 · JWT · HMAC" },
];

export interface Project {
  num: string; name: string; desc: string; chips: string[];
  image?: string; icon: string; featured?: boolean; live?: boolean;
  liveUrl?: string | null; githubUrl?: string | null;
}
export const PROJECTS: Project[] = [
  {
    num: "01 / FLAGSHIP", name: "PestFlow", featured: true, live: true,
    desc: "Pest-control business platform — multi-tenant operations, GST quotations, online/cash payment plans, technician workflows with verification codes, real-time updates over SignalR and push via Firebase Cloud Messaging.",
    chips: [".NET", "SQL Server", "SignalR"],
    image: "/images/pestflow-app-home.png", icon: "bug_report",
    githubUrl: "https://github.com/rajibmahata/pestflow", liveUrl: null,
  },
  {
    num: "02", name: "ARIA", icon: "smart_toy",
    desc: "Enterprise knowledge platform — your documents become a queryable, conversational base via RAG with a no-code multi-agent pipeline builder. ChromaDB, deployable on-premise with zero vendor lock-in.",
    chips: ["LLM", "RAG", "ChromaDB"],
    githubUrl: "https://github.com/rajibmahata/AI-Avatar-RAG-Platform", liveUrl: null,
  },
  {
    num: "03", name: "DocSignerHub", icon: "draw",
    desc: "Digital signature SaaS — visual workflow builder for approval chains, HMAC-signed API auth, Stripe payments in signing flows, GPT-4o clause summaries and optional blockchain notarisation. 140+ REST endpoints.",
    chips: ["SaaS", ".NET", "Stripe"],
    githubUrl: "https://github.com/rajibmahata/DocumentSigningPlatform",
    liveUrl: "https://docsignerhub.com",
  },
  {
    num: "04", name: "ReturnGuard AI", icon: "assignment_return",
    desc: "AI service on FastAPI with WebSockets and Redis, ChromaDB retrieval over multilingual embeddings, GPT-4o analysis with Whisper voice input and a React + TypeScript frontend.",
    chips: ["FastAPI", "ChromaDB", "GPT-4o"],
    githubUrl: null, liveUrl: null,
  },
  {
    num: "05", name: "HistoriaAI", icon: "history_edu",
    desc: "Document intelligence with human-in-the-loop validation — FastAPI, PostgreSQL and ChromaDB with GPT extraction and Azure Document Intelligence.",
    chips: ["RAG", "Validation", "Azure"],
    githubUrl: null, liveUrl: null,
  },
  {
    num: "06", name: "LexVault", icon: "gavel",
    desc: "Legal document intelligence — hybrid dense + sparse retrieval over Qdrant with a deterministic clause engine, running fully on-premise with zero cloud dependency.",
    chips: [".NET", "Qdrant", "Hybrid Search"],
    githubUrl: "https://github.com/rajibmahata/Legal-Document-RAG-System-LEXVAULT", liveUrl: null,
  },
  {
    num: "07", name: "R.M. Enterprise", icon: "storefront",
    desc: "Business website with content management — live in production serving a real food business.",
    chips: ["Web", "CMS", "Production"],
    githubUrl: null, liveUrl: "https://fryyofoods.com/",
  },
];

export interface Demo { title: string; desc: string; videoId: string }
export const DEMOS: Demo[] = [
  {
    title: "ARIA — AI Research Assistant",
    desc: "Complete demo: semantic search, AI summarization and knowledge workflows, end to end.",
    videoId: "6p5-A9PWn0E",
  },
  {
    title: "DocuSign Hub — Workflow Demo",
    desc: "Template creation → smart routing → signing → audit trail, in one continuous flow.",
    videoId: "f4Y_l0h4Xt0",
  },
];

export interface Xp { date: string; title: string; org: string; desc: string; tags: string[] }
export const EXPERIENCE: Xp[] = [
  {
    date: "2019 — PRESENT", title: "Solutions Architect", org: "Fortune 500 Healthcare · Pharmacy (USA)",
    desc: "Azure data lake and CQRS Rule Engine processing 500K+ daily prescription events. Automated refill system — 30% faster processing, 40% fewer errors. Vaccine appointment rollout, pharmacy PWAs, barcode + payments integration.",
    tags: [".NET 8", "Azure", "CQRS", "Cosmos DB"],
  },
  {
    date: "2016 — 2019", title: "Platform Engineer", org: "Telecom Enterprise (USA)",
    desc: "Designed and built the CMT network-provisioning platform — 30% less manual effort, 40% faster processing, 95% of issues resolved within 24 hours.",
    tags: ["ASP.NET", "SQL Server", "WCF"],
  },
  {
    date: "2013 — 2016", title: "Full-Stack Developer", org: "Product Studio",
    desc: "Corporate Hour, Cinematic Lens, TRANSZOOM and TruckIt365 — full-stack ownership from database design to deployment.",
    tags: ["ASP.NET MVC", "SQL Server", "JavaScript"],
  },
];
