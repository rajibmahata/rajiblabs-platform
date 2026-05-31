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
          className="fixed inset-0 z-[100] flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          {/* Backdrop */}
          <div
            className="absolute inset-0"
            style={{ background: 'rgba(8,13,26,0.85)', backdropFilter: 'blur(8px)' }}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            className="relative w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-xl border shadow-2xl"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.25, ease: [0, 0, 0.2, 1] }}
            style={{
              background: 'var(--c-bg-secondary)',
              borderColor: 'var(--c-border)',
              boxShadow: 'var(--shadow-lg)',
            }}
          >
            {/* Close button */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 rounded-full transition-colors z-10"
              style={{
                background: 'var(--c-bg-tertiary)',
                color: 'var(--c-text-secondary)',
                width: 36, height: 36,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                cursor: 'pointer',
                border: '1px solid var(--c-border)',
              }}
              aria-label="Close modal"
              onMouseEnter={e => {
                e.currentTarget.style.background = 'var(--c-bg-elevated)';
                e.currentTarget.style.color = 'var(--c-text-primary)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = 'var(--c-bg-tertiary)';
                e.currentTarget.style.color = 'var(--c-text-secondary)';
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
            </button>

            {/* Content */}
            <div className="p-6 sm:p-8">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 style={{
                    fontFamily: 'var(--font-display)',
                    fontSize: 'clamp(24px, 4vw, 32px)',
                    fontWeight: 700,
                    color: 'var(--c-text-primary)',
                    lineHeight: 'var(--lh-display)',
                  }}>
                    {project.name}
                  </h2>
                  <p style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: 15,
                    color: 'var(--c-text-secondary)',
                    marginTop: 4,
                  }}>
                    {project.role}
                  </p>
                </div>
                {project.status && <StatusBadge variant={project.status} />}
              </div>

              {/* Description */}
              <p style={{
                fontFamily: 'var(--font-body)',
                fontSize: 16,
                color: 'var(--c-text-secondary)',
                lineHeight: 'var(--lh-body)',
                marginBottom: 24,
              }}>
                {project.longDesc}
              </p>

              {/* Features */}
              {project.features.length > 0 && (
                <div className="mb-6">
                  <h3 style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: 14,
                    fontWeight: 600,
                    color: 'var(--c-text-primary)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginBottom: 12,
                  }}>
                    Key Features
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {project.features.map((f, i) => (
                      <div key={i} className="flex items-start gap-2.5 p-2.5 rounded-md"
                        style={{ background: 'var(--c-bg-tertiary)' }}
                      >
                        <span style={{ color: 'var(--c-accent-teal)', fontSize: 12, marginTop: 2 }}>◆</span>
                        <span style={{
                          fontFamily: 'var(--font-body)',
                          fontSize: 14,
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
              <div className="mb-6 p-4 rounded-lg" style={{ background: 'var(--c-bg-tertiary)', borderLeft: '3px solid var(--c-accent-gold)' }}>
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 11,
                  color: 'var(--c-accent-gold)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}>
                  Business Impact
                </span>
                <p style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: 14,
                  color: 'var(--c-text-secondary)',
                  lineHeight: 'var(--lh-compact)',
                  marginTop: 4,
                }}>
                  {project.impact}
                </p>
              </div>

              {/* Tech Stack */}
              <div className="mb-8">
                <h3 style={{
                  fontFamily: 'var(--font-heading)',
                  fontSize: 14,
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
              <div className="flex flex-wrap gap-3 pt-4 border-t" style={{ borderColor: 'var(--c-border)' }}>
                {project.liveUrl && (
                  <Button variant="primary" asLink href={project.liveUrl}>
                    ↗ Visit Site
                  </Button>
                )}
                {project.githubUrl && (
                  <Button variant="outline" asLink href={project.githubUrl}>
                    ⌥ View on GitHub
                  </Button>
                )}
                <Button variant="ghost" onClick={onClose}>
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
