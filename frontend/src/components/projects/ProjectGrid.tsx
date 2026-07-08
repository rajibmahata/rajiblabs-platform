import { useState, useEffect } from 'react';
import type { Project } from '../../types';
import { getProjects } from '../../services/api';
import ProjectCard from './ProjectCard';

// Static fallback projects — works without backend
const STATIC_PROJECTS: Project[] = [
  {
    id: '1', title: 'DocSignerHub', slug: 'docsignerhub',
    description: 'Digital signature SaaS platform with AI clause analysis, multi-signer workflows, blockchain notarisation, and Stripe payment integration. 140+ REST API endpoints, HMAC-signed auth.',
    techStack: ['.NET 8', 'Blazor', 'SQL Server', 'Azure', 'Stripe', 'OpenAI'],
    githubUrl: 'https://github.com/rajibmahata/DocumentSigningPlatform',
    liveUrl: 'https://docsignerhub.com', status: 'development',
    createdAt: new Date(Date.now() - 210 * 86400000).toISOString(),
    updatedAt: new Date().toISOString(),
    lastCommitAt: new Date(Date.now() - 2 * 3600000).toISOString(),
  },
  {
    id: '2', title: 'ARIA — AI Avatar RAG Platform', slug: 'ai-avatar-rag',
    description: 'Enterprise AI knowledge platform with RAG architecture, no-code multi-agent pipeline builder, and hybrid vector+BM25 search. Designed for on-premise deployment.',
    techStack: ['Python', 'FastAPI', 'GPT-4o', 'ChromaDB', 'LangChain', 'React'],
    githubUrl: 'https://github.com/rajibmahata/AI-Avatar-RAG-Platform',
    liveUrl: null, status: 'development',
    createdAt: new Date(Date.now() - 240 * 86400000).toISOString(),
    updatedAt: new Date().toISOString(),
    lastCommitAt: new Date(Date.now() - 1 * 86400000).toISOString(),
  },
  {
    id: '3', title: 'Solicitor Case Management', slug: 'solicitor-cms',
    description: 'Legal enterprise workflow platform with visual case flow builder, automated document generation, deadline tracking, and secure client portal for mid-size law firms.',
    techStack: ['.NET 8', 'Blazor', 'SQL Server', 'Azure', 'Cosmos DB'],
    githubUrl: 'https://github.com/rajibmahata/SolicitorCaseManagementSystem',
    liveUrl: null, status: 'development',
    createdAt: new Date(Date.now() - 300 * 86400000).toISOString(),
    updatedAt: new Date().toISOString(),
    lastCommitAt: new Date(Date.now() - 3 * 86400000).toISOString(),
  },
  {
    id: '4', title: 'Rajib Labs Platform', slug: 'rajiblabs',
    description: 'AI-powered portfolio and software lab. Auto-populated from GitHub, managed by 17 OpenClaw agents. This very platform.',
    techStack: ['.NET 8', 'React', 'TypeScript', 'Tailwind CSS', 'SQLite', 'OpenClaw'],
    githubUrl: 'https://github.com/rajibmahata/rajiblabs-platform',
    liveUrl: 'https://rajiblabs.com', status: 'deployed',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    lastCommitAt: new Date().toISOString(),
  },
  {
    id: '5', title: 'LexVault — Legal Document RAG', slug: 'lexvault',
    description: 'Legal document intelligence platform with dual-pipeline architecture: LLM-assisted knowledge base ingestion + zero-LLM confidence scoring using hybrid search (dense + sparse BM42) on Qdrant. On-premise Windows Server deployment.',
    techStack: ['.NET 8', 'Qdrant', 'RAG', 'Hybrid Search', 'Azure OpenAI', 'Redis'],
    githubUrl: 'https://github.com/rajibmahata/Legal-Document-RAG-System-LEXVAULT',
    liveUrl: null, status: 'development',
    createdAt: new Date(Date.now() - 3 * 86400000).toISOString(),
    updatedAt: new Date().toISOString(),
    lastCommitAt: new Date(Date.now() - 1 * 3600000).toISOString(),
  },
  {
    id: '6', title: 'AI Student Tutor', slug: 'math-tutor-ai',
    description: 'Multi-role AI-powered personalized learning platform with 12 AI agents — voice-first tutoring, content generation from PDFs, auto-assessment, gamification, and human-in-the-loop validation. Supports 4 languages.',
    techStack: ['Python', 'FastAPI', 'LangGraph', 'Next.js', 'PostgreSQL', 'Qdrant', 'OpenAI'],
    githubUrl: 'https://github.com/rajibmahata/Math-tutor-AI-Agent',
    liveUrl: null, status: 'development',
    createdAt: new Date(Date.now() - 7 * 86400000).toISOString(),
    updatedAt: new Date().toISOString(),
    lastCommitAt: new Date(Date.now() - 12 * 3600000).toISOString(),
  },
];

export default function ProjectGrid() {
  const [projects, setProjects] = useState<Project[]>(STATIC_PROJECTS);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Try API, use static if failed
    getProjects()
      .then(setProjects)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="max-w-6xl mx-auto px-6 pb-16" id="projects">
      <div className="flex items-center gap-4 mb-10">
        <h2 className="text-sm font-semibold uppercase tracking-[0.15em] text-[var(--text-muted)]">Projects</h2>
        <div className="h-px flex-1 bg-[var(--border)]"></div>
        <span className="text-xs text-[var(--text-muted)] tabular-nums">{projects.length}</span>
      </div>

      {loading ? (
        <div className="grid md:grid-cols-2 gap-5">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="p-6 rounded-2xl bg-[var(--bg-card)] border border-[var(--border)] animate-pulse">
              <div className="flex justify-between mb-5">
                <div className="w-12 h-12 rounded-xl bg-[var(--bg-hover)]"></div>
                <div className="h-5 w-24 rounded-full bg-[var(--bg-hover)]"></div>
              </div>
              <div className="h-5 w-48 bg-[var(--bg-hover)] rounded mb-2"></div>
              <div className="h-4 w-full bg-[var(--bg-hover)] rounded mb-1"></div>
              <div className="h-4 w-2/3 bg-[var(--bg-hover)] rounded mb-5"></div>
              <div className="flex gap-1.5 mb-5">
                <div className="h-6 w-16 bg-[var(--bg-hover)] rounded-md"></div>
                <div className="h-6 w-20 bg-[var(--bg-hover)] rounded-md"></div>
              </div>
              <div className="pt-4 border-t border-[var(--border)]"><div className="h-3 w-24 bg-[var(--bg-hover)] rounded"></div></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-5">
          {projects.map((p, i) => (
            <ProjectCard key={p.id} project={p} index={i} />
          ))}
        </div>
      )}
    </section>
  );
}
