import { useEffect, useState, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import StatusBadge from '../ui/StatusBadge';
import CommitRow from '../ui/CommitRow';
import { getWorkInProgress } from '../../services/api';
import { fallbackWipData } from '../../services/fallbackData';
import type { WipData } from '../../types';

export default function WorkInProgressSection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });
  const [data, setData] = useState<WipData>(fallbackWipData);

  useEffect(() => {
    let cancelled = false;
    getWorkInProgress().then(result => {
      if (!cancelled) setData(result);
    });
    return () => { cancelled = true; };
  }, []);

  return (
    <section id="wip" className="section-pad" ref={sectionRef}
      style={{ background: 'var(--c-bg-secondary)' }}
    >
      <div className="container-site">
        <SectionLabel>CURRENTLY BUILDING</SectionLabel>

        <div className="mb-10">
          <h2 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'clamp(24px, 3vw, 36px)',
            fontWeight: 700,
            color: 'var(--c-text-primary)',
            lineHeight: 'var(--lh-display)',
            marginBottom: 8,
          }}>
            Active projects &amp; recent activity
          </h2>
          <p style={{
            fontFamily: 'var(--font-body)',
            fontSize: 15,
            color: 'var(--c-text-secondary)',
            lineHeight: 'var(--lh-body)',
          }}>
            {data.projects.length} projects in development, tracked from public GitHub activity.
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-8"
        >
          {/* LEFT — Project Cards */}
          <div className="space-y-4">
            {data.projects.map((project, i) => (
              <motion.div
                key={project.name}
                initial={{ opacity: 0, y: 16 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: 0.08 * i, duration: 0.4 }}
                className="card p-5 group"
                style={{ transition: 'all 250ms var(--ease-spring)' }}
                onMouseEnter={e => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = 'var(--shadow-md)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '';
                }}
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 style={{
                      fontFamily: 'var(--font-heading)',
                      fontSize: 16,
                      fontWeight: 600,
                      color: 'var(--c-text-primary)',
                      marginBottom: 4,
                    }}>
                      {project.name}
                    </h3>
                    <p style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 11,
                      color: 'var(--c-text-muted)',
                    }}>
                      {project.stack}
                    </p>
                  </div>
                  <StatusBadge variant={project.status} />
                </div>

                {/* Progress bar */}
                <div className="mb-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <span style={{
                      fontFamily: 'var(--font-body)',
                      fontSize: 12,
                      color: 'var(--c-text-secondary)',
                    }}>
                      Progress
                    </span>
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 13,
                      fontWeight: 600,
                      color: project.progress >= 70 ? 'var(--c-accent-teal)' : project.progress >= 30 ? 'var(--c-accent-blue-l)' : 'var(--c-accent-gold)',
                    }}>
                      {project.progress}%
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full" style={{ background: 'var(--c-bg-tertiary)' }}>
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{
                        width: `${project.progress}%`,
                        background: project.progress >= 70
                          ? 'linear-gradient(90deg, var(--c-accent-teal), var(--c-accent-teal-l))'
                          : project.progress >= 30
                          ? 'linear-gradient(90deg, var(--c-accent-blue), var(--c-accent-blue-l))'
                          : 'linear-gradient(90deg, var(--c-accent-gold), var(--c-accent-gold-l))',
                      }}
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2" style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 11,
                  color: 'var(--c-text-muted)',
                }}>
                  <span>Last activity:</span>
                  <span style={{ color: 'var(--c-text-secondary)' }}>{project.lastActivity}</span>
                </div>
              </motion.div>
            ))}
          </div>

          {/* RIGHT — Commit Feed */}
          <div className="card overflow-hidden" style={{ maxHeight: 420 }}>
            <div className="px-5 py-4 border-b flex items-center justify-between"
              style={{ borderColor: 'var(--c-border)', background: 'var(--c-bg-tertiary)' }}
            >
              <span style={{
                fontFamily: 'var(--font-heading)',
                fontSize: 13,
                fontWeight: 600,
                color: 'var(--c-text-primary)',
                textTransform: 'uppercase',
                letterSpacing: '0.03em',
              }}>
                Recent Commits
              </span>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                color: 'var(--c-text-muted)',
              }}>
                {data.commits.length} commits
              </span>
            </div>
            <div className="overflow-y-auto" style={{ maxHeight: 370 }}>
              {data.commits.map(commit => (
                <CommitRow
                  key={commit.hash}
                  hash={commit.hash}
                  message={commit.message}
                  repoName={commit.repoName}
                  timestamp={commit.timestamp}
                />
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
