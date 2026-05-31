import { useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import TechChip from './TechChip';
import Button from './Button';
import StatusBadge from './StatusBadge';

export interface ProjectDetail {
  name: string;
  shortDesc: string;
  longDesc: string;
  features: string[];
  techStack: string[];
  liveUrl?: string | null;
  githubUrl?: string | null;
  source: 'github' | 'claude_cb' | 'localhost' | 'enterprise';
  status?: 'live' | 'beta' | 'complete' | 'wip';
  role: string;
  impact: string;
}

interface ProjectModalProps {
  project: ProjectDetail | null;
  onClose: () => void;
}

export default function ProjectModal({ project, onClose }: ProjectModalProps) {
  const handleEscape = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  }, [onClose]);

  useEffect(() => {
    if (project) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [project, handleEscape]);

  return (
    <AnimatePresence>
      {project && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-start justify-center p-4 pt-12 sm:pt-16 overflow-y-auto"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          {/* Backdrop — fixed behind scroll */}
          <div
            className="fixed inset-0"
            style={{ background: 'rgba(8,13,26,0.88)', backdropFilter: 'blur(8px)' }}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            className="relative w-full max-w-xl sm:max-w-2xl mb-8 rounded-xl border shadow-2xl"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.25, ease: [0, 0, 0.2, 1] }}
            style={{
              background: 'var(--c-bg-secondary)',
              borderColor: 'rgba(30, 45, 74, 0.6)',
              boxShadow: '0 20px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(37, 99, 244, 0.06)',
            }}
          >
            {/* Close button — top-right corner of modal border */}
            <button
              onClick={onClose}
              className="absolute -top-3 -right-3 w-8 h-8 rounded-full flex items-center justify-center z-10 transition-colors"
              style={{
                background: 'var(--c-bg-elevated)',
                color: 'var(--c-text-secondary)',
                border: '1px solid rgba(30, 45, 74, 0.8)',
                cursor: 'pointer',
              }}
              aria-label="Close modal"
              onMouseEnter={e => {
                e.currentTarget.style.background = 'var(--c-accent-blue)';
                e.currentTarget.style.color = '#fff';
                e.currentTarget.style.borderColor = 'var(--c-accent-blue)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = 'var(--c-bg-elevated)';
                e.currentTarget.style.color = 'var(--c-text-secondary)';
                e.currentTarget.style.borderColor = 'rgba(30, 45, 74, 0.8)';
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
            </button>

            {/* Content — even padding, no overlap */}
            <div className="p-6 sm:p-8">
              {/* Header — title + badge, no overlap with close button */}
              <div className="flex items-start gap-3 mb-5 pr-6">
                <div className="flex-1 min-w-0">
                  <h2 style={{
                    fontFamily: 'var(--font-display)',
                    fontSize: 'clamp(22px, 3.5vw, 28px)',
                    fontWeight: 700,
                    color: 'var(--c-text-primary)',
                    lineHeight: 'var(--lh-display)',
                  }}>
                    {project.name}
                  </h2>
                  <p style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: 14,
                    color: 'var(--c-text-secondary)',
                    marginTop: 4,
                  }}>
                    {project.role}
                  </p>
                </div>
                {project.status && (
                  <div className="flex-shrink-0 mt-1">
                    <StatusBadge variant={project.status} />
                  </div>
                )}
              </div>

              {/* Description */}
              <p style={{
                fontFamily: 'var(--font-body)',
                fontSize: 14.5,
                color: 'var(--c-text-secondary)',
                lineHeight: 'var(--lh-body)',
                marginBottom: 24,
              }}>
                {project.longDesc}
              </p>

              {/* Features */}
              {project.features.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <h3 style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: 12,
                    fontWeight: 600,
                    color: 'var(--c-text-primary)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginBottom: 10,
                  }}>
                    Key Features
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {project.features.map((f, i) => (
                      <div key={i} className="flex items-start gap-2 px-3 py-2 rounded-md"
                        style={{ background: 'var(--c-bg-tertiary)', border: '1px solid rgba(30,45,74,0.4)' }}
                      >
                        <span style={{ color: 'var(--c-accent-teal)', fontSize: 10, marginTop: 3, flexShrink: 0 }}>◆</span>
                        <span style={{
                          fontFamily: 'var(--font-body)',
                          fontSize: 13,
                          color: 'var(--c-text-secondary)',
                          lineHeight: 'var(--lh-compact)',
                        }}>
                          {f}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Impact */}
              <div style={{ marginBottom: 20, padding: '14px 16px', borderRadius: 'var(--radius-md)', background: 'var(--c-bg-tertiary)', borderLeft: '3px solid var(--c-accent-gold)' }}>
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  color: 'var(--c-accent-gold)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                }}>
                  Business Impact
                </span>
                <p style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: 13.5,
                  color: 'var(--c-text-secondary)',
                  lineHeight: 'var(--lh-compact)',
                  marginTop: 3,
                }}>
                  {project.impact}
                </p>
              </div>

              {/* Tech Stack */}
              <div style={{ marginBottom: 24 }}>
                <h3 style={{
                  fontFamily: 'var(--font-heading)',
                  fontSize: 12,
                  fontWeight: 600,
                  color: 'var(--c-text-primary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: 10,
                }}>
                  Technology Stack
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {project.techStack.map(tech => (
                    <TechChip key={tech} label={tech} category={
                      /azure|docker|cloud/i.test(tech) ? 'cloud' :
                      /react|typescript|javascript|html|css|tailwind/i.test(tech) ? 'frontend' :
                      /ai|rag|openai|gpt|llm|chroma|vector/i.test(tech) ? 'ai' : 'backend'
                    } />
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-2.5 pt-4 border-t" style={{ borderColor: 'rgba(30, 45, 74, 0.6)' }}>
                {project.liveUrl && (
                  <Button variant="primary" size="sm" asLink href={project.liveUrl}>
                    ↗ Visit Site
                  </Button>
                )}
                {project.githubUrl && (
                  <Button variant="outline" size="sm" asLink href={project.githubUrl}>
                    ⌥ View on GitHub
                  </Button>
                )}
                <Button variant="ghost" size="sm" onClick={onClose}>
                  Close
                </Button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
