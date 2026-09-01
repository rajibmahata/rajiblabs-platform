import { useEffect, useState, useRef, useMemo } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import { getGitHubSummary } from '../../services/api';
import { fallbackGitHubSummary } from '../../services/fallbackData';
import type { GitHubSummary } from '../../types';

export default function GitHubActivitySection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });
  const [data, setData] = useState<GitHubSummary>(fallbackGitHubSummary);

  // Seeded pseudo-random heatmap — illustrative, not live GitHub data
  const heatmapLevels = useMemo(() => {
    const seed = 2026_07_06;
    let s = seed;
    const rng = () => {
      // eslint-disable-next-line react-hooks/immutability -- intentional local mutation for deterministic RNG
      s = (s * 16807 + 0) % 2147483647;
      return s / 2147483647;
    };
    const cells = 52 * 7;
    return Array.from({ length: cells }, () => {
      const r = rng();
      // Weight toward lower activity (realistic distribution)
      if (r > 0.92) return 3;
      if (r > 0.78) return 2;
      if (r > 0.55) return 1;
      return 0;
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    getGitHubSummary().then(result => {
      if (!cancelled) setData(result);
    });
    return () => { cancelled = true; };
  }, []);

  return (
    <section
      id="github"
      className="section-pad"
      ref={sectionRef}
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
          <div className="card p-6 mb-8 overflow-x-auto">
            <div className="flex items-center justify-between mb-4">
              <span
                style={{
                  fontFamily: 'var(--font-heading)',
                  fontSize: 14,
                  fontWeight: 500,
                  color: 'var(--c-text-primary)',
                }}
              >
                Contribution Heatmap
              </span>
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 11,
                  color: 'var(--c-text-muted)',
                }}
              >
                Jan — Dec 2026
              </span>
            </div>

            {/* Custom heatmap grid */}
            <div className="flex flex-wrap gap-0.5" role="img" aria-label="GitHub contribution heatmap">
              {heatmapLevels.map((level, i) => {
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
                      width: 12,
                      height: 12,
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

          {/* Stats Row — from API or fallback */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
            {data.stats.map(stat => (
              <div key={stat.label} className="card p-4">
                <span style={{ fontSize: 20 }}>{stat.icon}</span>
                <div className="mt-2">
                  <p
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 24,
                      color: 'var(--c-accent-gold)',
                      fontWeight: 500,
                    }}
                  >
                    {stat.value}
                  </p>
                  <p
                    style={{
                      fontFamily: 'var(--font-body)',
                      fontSize: 13,
                      color: 'var(--c-text-secondary)',
                    }}
                  >
                    {stat.label}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Top Repositories — from API or fallback */}
          <div>
            <h3
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: 16,
                fontWeight: 600,
                color: 'var(--c-text-primary)',
                marginBottom: 16,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Top Repositories
            </h3>
            <div className="space-y-2">
              {data.topRepos.map(repo => (
                <a
                  key={repo.name}
                  href={`https://github.com/rajibmahata/${repo.name}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="card px-4 py-3 flex flex-wrap items-center justify-between gap-2"
                  style={{ textDecoration: 'none' }}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span
                      style={{
                        fontFamily: 'var(--font-heading)',
                        fontSize: 15,
                        fontWeight: 500,
                        color: 'var(--c-text-primary)',
                      }}
                    >
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
