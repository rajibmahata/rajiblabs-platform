import { useState, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import ProjectCard from '../ui/ProjectCard';

type FilterTab = 'all' | 'github' | 'claude_cb' | 'localhost';

const projects = [
  {
    name: 'DocSignerHub',
    description: 'Enterprise electronic signature SaaS platform. Multi-signer workflows, audit trail, HMAC auth.',
    techStack: ['.NET 8', 'Blazor', 'Azure', 'SQL Server', 'Stripe', 'OpenAI'],
    liveUrl: 'https://docsignerhub.com',
    githubUrl: 'https://github.com/rajibmahata/DocumentSigningPlatform',
    source: 'github' as const,
  },
  {
    name: 'ARIA Platform',
    description: 'AI RAG knowledge platform for enterprise. Semantic search with avatar-based interaction.',
    techStack: ['Python', 'FastAPI', 'RAG', 'GPT-4o', 'ChromaDB', 'React'],
    liveUrl: null,
    githubUrl: 'https://github.com/rajibmahata/AI-Avatar-RAG-Platform',
    source: 'github' as const,
  },
  {
    name: 'FoodFleet',
    description: 'Multi-platform restaurant delivery app with location detection and branch routing.',
    techStack: ['.NET 8', 'React', 'Azure', 'SQL Server'],
    liveUrl: null,
    githubUrl: 'https://github.com/rajibmahata/FoodFleet',
    source: 'github' as const,
  },
  {
    name: 'Solicitor CMS',
    description: 'Legal enterprise workflow platform. Case tracking, document management, visual workflow builder.',
    techStack: ['.NET 8', 'Blazor', 'SQL Server', 'Cosmos DB'],
    liveUrl: null,
    githubUrl: 'https://github.com/rajibmahata/SolicitorCaseManagementSystem',
    source: 'github' as const,
  },
  {
    name: 'AI Resume Portfolio',
    description: 'AI-powered resume to portfolio generator. Upload PDF/DOC, AI generates single-page portfolio.',
    techStack: ['Blazor', 'AI', 'C#', '.NET'],
    liveUrl: null,
    githubUrl: 'https://github.com/rajibmahata/AI-Resume-Portfolio',
    source: 'claude_cb' as const,
  },
  {
    name: 'AI Blog Portfolio',
    description: 'Seamless blogging platform where AI ensures content quality, engagement, and discoverability.',
    techStack: ['C#', 'AI', 'ASP.NET Core', 'SQL'],
    liveUrl: null,
    githubUrl: 'https://github.com/rajibmahata/AI-Powered-Blog-Portfolio',
    source: 'claude_cb' as const,
  },
  {
    name: 'BudgetEase',
    description: 'Modern event expense tracking application. Budget management, vendor communications.',
    techStack: ['C#', 'ASP.NET Core', 'SQL Server'],
    liveUrl: null,
    githubUrl: 'https://github.com/rajibmahata/BudgetEase',
    source: 'github' as const,
  },
  {
    name: 'rajiblabs-platform',
    description: 'This portfolio — premium personal brand, AI-managed content, real-time activity tracking.',
    techStack: ['React', 'TypeScript', 'Tailwind CSS', '.NET 8', 'OpenClaw'],
    liveUrl: 'https://rajiblabs.com',
    githubUrl: 'https://github.com/rajibmahata/rajiblabs-platform',
    source: 'localhost' as const,
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
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  const filtered = activeFilter === 'all'
    ? projects
    : projects.filter(p => p.source === activeFilter);

  const counts = {
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
        <div className="flex flex-wrap gap-6 mb-8 border-b" style={{ borderColor: 'var(--c-border)' }}>
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveFilter(tab.key)}
              className="pb-2 transition-colors"
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: 14,
                fontWeight: activeFilter === tab.key ? 600 : 400,
                color: activeFilter === tab.key ? 'var(--c-text-primary)' : 'var(--c-text-muted)',
                borderBottom: activeFilter === tab.key ? '2px solid var(--c-accent-blue)' : '2px solid transparent',
                background: 'transparent',
                cursor: 'pointer',
              }}
            >
              {tab.label}
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 12,
                color: 'var(--c-text-muted)',
                marginLeft: 4,
              }}>
                ({counts[tab.key]})
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
              name={project.name}
              description={project.description}
              techStack={project.techStack}
              liveUrl={project.liveUrl}
              githubUrl={project.githubUrl}
              source={project.source}
            />
          ))}
        </motion.div>
      </div>
    </section>
  );
}
