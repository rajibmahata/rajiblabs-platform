import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';

const githubStats = [
  { value: '247', label: 'contributions', icon: '📊' },
  { value: '12', label: 'repos', icon: '📦' },
  { value: '3', label: 'languages', icon: '🔤' },
  { value: 'Kolkata', label: 'location', icon: '📍' },
];

const topRepos = [
  { name: 'DocSignerHub', language: 'C#', stars: 12, forks: 3, updated: '2 days ago', langColor: '#178600' },
  { name: 'AI-Avatar-RAG-Platform', language: 'Python', stars: 8, forks: 2, updated: '5 hours ago', langColor: '#3572A5' },
  { name: 'FoodFleet', language: 'TypeScript', stars: 6, forks: 1, updated: '3 weeks ago', langColor: '#3178C6' },
  { name: 'SolicitorCaseManagementSystem', language: 'C#', stars: 5, forks: 1, updated: '1 month ago', langColor: '#178600' },
  { name: 'rajiblabs-platform', language: 'TypeScript', stars: 4, forks: 0, updated: 'just now', langColor: '#3178C6' },
  { name: 'BudgetEase', language: 'C#', stars: 3, forks: 0, updated: '2 months ago', langColor: '#178600' },
];

export default function GitHubActivitySection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  return (
    <section id="github" className="section-pad" ref={sectionRef}
      style={{ background: 'var(--c-bg-secondary)' }}
    >
      <div className="container-site">
        <SectionLabel>GITHUB ACTIVITY</SectionLabel>

        <a
          href="https://github.com/rajibmahata"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block mb-8"
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 13,
            color: 'var(--c-text-muted)',
            textDecoration: 'none',
          }}
        >
          github.com/rajibmahata ↗
        </a>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
        >
          {/* Contribution Heatmap (placeholder) */}
          <div
            className="card p-6 mb-8 overflow-x-auto"
          >
            <div className="flex items-center justify-between mb-4">
              <span style={{
                fontFamily: 'var(--font-heading)',
                fontSize: 14,
                fontWeight: 500,
                color: 'var(--c-text-primary)',
              }}>
                Contribution Heatmap
              </span>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                color: 'var(--c-text-muted)',
              }}>
                Jan — Dec 2026
              </span>
            </div>

            {/* Custom heatmap grid */}
            <div className="flex flex-wrap gap-0.5" role="img" aria-label="GitHub contribution heatmap">
              {Array.from({ length: 52 * 7 }).map((_, i) => {
                const levels = [0, 1, 2, 3];
                const level = levels[Math.floor(Math.random() * levels.length)];
                const colors = [
                  'var(--c-bg-tertiary)',
                  'rgba(10,123,108,0.3)',
                  'rgba(10,123,108,0.6)',
                  'var(--c-accent-teal)',
                ];
                return (
                  <div
                    key={i}
                    className="rounded-sm"
                    style={{
                      width: 12, height: 12,
                      backgroundColor: colors[level],
                    }}
                    title={`${level} contributions`}
                  />
                );
              })}
            </div>

            {/* Legend */}
            <div className="flex items-center gap-2 mt-3 justify-end">
              <span style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--c-text-muted)' }}>Less</span>
              {['var(--c-bg-tertiary)', 'rgba(10,123,108,0.3)', 'rgba(10,123,108,0.6)', 'var(--c-accent-teal)'].map((color, i) => (
                <div key={i} className="w-3 h-3 rounded-sm" style={{ backgroundColor: color }} />
              ))}
              <span style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--c-text-muted)' }}>More</span>
            </div>
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
            {githubStats.map(stat => (
              <div key={stat.label} className="card p-4">
                <span style={{ fontSize: 20 }}>{stat.icon}</span>
                <div className="mt-2">
                  <p style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 24,
                    color: 'var(--c-accent-gold)',
                    fontWeight: 500,
                  }}>
                    {stat.value}
                  </p>
                  <p style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: 13,
                    color: 'var(--c-text-secondary)',
                  }}>
                    {stat.label}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Top Repositories */}
          <div>
            <h3 style={{
              fontFamily: 'var(--font-heading)',
              fontSize: 16,
              fontWeight: 600,
              color: 'var(--c-text-primary)',
              marginBottom: 16,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}>
              Top Repositories
            </h3>
            <div className="space-y-2">
              {topRepos.map(repo => (
                <a
                  key={repo.name}
                  href={`https://github.com/rajibmahata/${repo.name}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="card px-4 py-3 flex flex-wrap items-center justify-between gap-2"
                  style={{ textDecoration: 'none' }}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span style={{
                      fontFamily: 'var(--font-heading)',
                      fontSize: 15,
                      fontWeight: 500,
                      color: 'var(--c-text-primary)',
                    }}>
                      {repo.name}
                    </span>
                    <span className="flex items-center gap-1.5" style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: 'var(--c-text-muted)' }}>
                      <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: repo.langColor }} />
                      {repo.language}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 ml-auto">
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--c-text-muted)' }}>
                      ★ {repo.stars}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--c-text-muted)' }}>
                      🍴 {repo.forks}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--c-text-muted)' }}>
                      Updated: {repo.updated}
                    </span>
                  </div>
                </a>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
