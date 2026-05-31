import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import StatusBadge from '../ui/StatusBadge';
import CommitRow from '../ui/CommitRow';

const wipProjects = [
  {
    name: 'DocSignerHub v2',
    stack: '.NET 8 · Blazor · Azure · SQL',
    progress: 68,
    lastActivity: '2 hours ago',
    status: 'live' as const,
  },
  {
    name: 'ARIA Phase 2',
    stack: 'FastAPI · GPT-4o · ChromaDB · React',
    progress: 45,
    lastActivity: '3 hours ago',
    status: 'wip' as const,
  },
  {
    name: 'rajiblabs-site',
    stack: 'React · TypeScript · Vite · Tailwind',
    progress: 80,
    lastActivity: 'Yesterday',
    status: 'wip' as const,
  },
];

const mockCommits = [
  { hash: 'd4f7c2a', message: 'feat: multi-signer workflow with HMAC auth', repoName: 'DocSignerHub', timestamp: '2 minutes ago' },
  { hash: 'a9e1b3f', message: 'fix: token expiry bug in middleware pipeline', repoName: 'ARIA', timestamp: '1 hour ago' },
  { hash: '3c8d912', message: 'feat: RAG pipeline v2 with hybrid vector search', repoName: 'ARIA', timestamp: '3 hours ago' },
  { hash: '7f2a134', message: 'chore: update deps and migrate to Tailwind v4', repoName: 'rajiblabs-site', timestamp: 'Yesterday' },
  { hash: 'b5c6e8f', message: 'feat: add global navigation component with scroll blur', repoName: 'rajiblabs-site', timestamp: 'Yesterday' },
  { hash: '2e4a7d1', message: 'refactor: extract service layer for document processing', repoName: 'DocSignerHub', timestamp: '2 days ago' },
];

export default function WorkInProgressSection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  return (
    <section id="wip" className="section-pad" ref={sectionRef}
      style={{ background: 'var(--c-bg-secondary)' }}
    >
      <div className="container-site">
        <div className="flex items-center justify-between mb-2">
          <SectionLabel>CURRENTLY BUILDING</SectionLabel>
        </div>

        <div className="flex items-center gap-2 mb-8">
          <span className="pulse-dot" style={{ backgroundColor: 'var(--c-accent-teal)' }} />
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            color: 'var(--c-accent-teal)',
            fontWeight: 500,
            letterSpacing: '0.05em',
          }}>
            ● LIVE — updates on every commit
          </span>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            color: 'var(--c-text-muted)',
            marginLeft: 'auto',
          }}>
            {wipProjects.length} Active
          </span>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-6"
        >
          {/* LEFT — Project Cards */}
          <div className="space-y-4">
            {wipProjects.map(project => (
              <div
                key={project.name}
                className="card p-5"
                style={{
                  borderLeft: `3px solid ${project.status === 'live' ? 'var(--c-accent-teal)' : project.status === 'wip' ? 'var(--c-accent-blue)' : 'var(--c-accent-gold)'}`,
                }}
              >
                <div className="flex justify-between items-start mb-2">
                  <h3 style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: 16,
                    fontWeight: 500,
                    color: 'var(--c-text-primary)',
                  }}>
                    {project.name}
                  </h3>
                  <StatusBadge variant={project.status} />
                </div>
                <p style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  color: 'var(--c-text-muted)',
                  marginBottom: 12,
                }}>
                  {project.stack}
                </p>

                {/* Progress bar */}
                <div className="flex items-center gap-3 mb-1">
                  <p style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: 13,
                    color: 'var(--c-text-secondary)',
                  }}>
                    Progress: {project.progress}%
                  </p>
                  <div className="flex-1 h-1 rounded-full" style={{ background: 'var(--c-bg-tertiary)' }}>
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${project.progress}%`,
                        background: 'linear-gradient(90deg, var(--c-accent-blue), var(--c-accent-teal))',
                        transition: 'width 1s var(--ease-out)',
                      }}
                    />
                  </div>
                </div>
                <p style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  color: 'var(--c-text-muted)',
                }}>
                  Last: {project.lastActivity}
                </p>
              </div>
            ))}
          </div>

          {/* RIGHT — Commit Feed */}
          <div
            className="rounded-lg overflow-y-auto border"
            style={{
              background: 'var(--c-bg-secondary)',
              borderColor: 'var(--c-border)',
              maxHeight: 360,
            }}
            aria-live="polite"
            aria-label="Live commit feed"
          >
            <div className="px-4 py-3 border-b flex items-center justify-between"
              style={{ borderColor: 'var(--c-border)' }}
            >
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                fontWeight: 500,
                color: 'var(--c-text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}>
                Recent Commits
              </span>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: 'var(--c-text-muted)',
              }}>
                {mockCommits.length} commits
              </span>
            </div>
            {mockCommits.map(commit => (
              <CommitRow
                key={commit.hash}
                hash={commit.hash}
                message={commit.message}
                repoName={commit.repoName}
                timestamp={commit.timestamp}
              />
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
