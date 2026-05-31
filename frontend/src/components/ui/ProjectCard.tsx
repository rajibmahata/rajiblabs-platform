import TechChip from './TechChip';
import Button from './Button';
import type { ProjectDetail } from './ProjectModal';

interface ProjectCardProps {
  project: ProjectDetail;
  onMoreInfo: (project: ProjectDetail) => void;
  className?: string;
}

const sourceConfig = {
  github:     { label: 'GitHub',     color: '#22C55E' },
  claude_cb:  { label: 'Claude/CB',  color: '#8B5CF6' },
  localhost:  { label: 'Localhost',  color: '#C49A2A' },
};

export default function ProjectCard({ project, onMoreInfo, className = '' }: ProjectCardProps) {
  const src = sourceConfig[project.source];

  return (
    <div
      className={`card p-5 group flex flex-col ${className}`}
      style={{
        minHeight: 260,
        transition: 'all 250ms var(--ease-spring)',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.transform = 'translateY(-4px)';
        e.currentTarget.style.boxShadow = 'var(--shadow-lg)';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = '';
      }}
    >
      {/* Source badge + Name */}
      <div className="flex justify-between items-start gap-2 mb-2">
        <h3 style={{
          fontFamily: 'var(--font-heading)',
          fontSize: 16,
          fontWeight: 500,
          color: 'var(--c-text-primary)',
          lineHeight: 1.3,
        }}>
          {project.name}
        </h3>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            fontWeight: 500,
            padding: '2px 8px',
            borderRadius: 'var(--radius-sm)',
            backgroundColor: `${src.color}18`,
            border: `1px solid ${src.color}40`,
            color: src.color,
            whiteSpace: 'nowrap',
            flexShrink: 0,
          }}
        >
          {src.label}
        </span>
      </div>

      {/* Short description */}
      <p style={{
        fontFamily: 'var(--font-body)',
        fontSize: 14,
        color: 'var(--c-text-secondary)',
        lineHeight: 'var(--lh-compact)',
        marginBottom: 10,
        flex: '0 0 auto',
      }}>
        {project.shortDesc}
      </p>

      {/* Tech stack — limited to 4 */}
      <div className="flex flex-wrap gap-1 mb-4" style={{ flex: '0 0 auto' }}>
        {project.techStack.slice(0, 4).map(t => (
          <TechChip key={t} label={t} category={
            /azure|docker|cloud/i.test(t) ? 'cloud' :
            /react|typescript|javascript|html|css|tailwind/i.test(t) ? 'frontend' :
            /ai|rag|openai|gpt|llm|chroma|vector/i.test(t) ? 'ai' : 'backend'
          } />
        ))}
        {project.techStack.length > 4 && (
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: 'var(--c-text-muted)',
            padding: '2px 8px',
            border: '1px solid var(--c-border)',
            borderRadius: 'var(--radius-sm)',
          }}>
            +{project.techStack.length - 4}
          </span>
        )}
      </div>

      {/* Spacer pushes buttons to bottom */}
      <div style={{ flex: 1 }} />

      {/* Action buttons — pinned to bottom */}
      <div className="flex items-center gap-2 pt-2 border-t" style={{ borderColor: 'var(--c-border)', flex: '0 0 auto' }}>
        <button
          onClick={(e) => { e.preventDefault(); e.stopPropagation(); onMoreInfo(project); }}
          className="text-xs font-medium transition-all"
          style={{
            fontFamily: 'var(--font-heading)',
            padding: '6px 14px',
            borderRadius: 'var(--radius-md)',
            background: 'transparent',
            color: 'var(--c-text-secondary)',
            border: '1px solid var(--c-border)',
            cursor: 'pointer',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.borderColor = 'var(--c-accent-blue)';
            e.currentTarget.style.color = 'var(--c-text-primary)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.borderColor = 'var(--c-border)';
            e.currentTarget.style.color = 'var(--c-text-secondary)';
          }}
          data-testid={`more-info-${project.name.replace(/\s+/g, '-').toLowerCase()}`}
        >
          ℹ More Info
        </button>
        {project.liveUrl && (
          <Button variant="primary" size="sm" asLink href={project.liveUrl}>
            ↗ Live
          </Button>
        )}
        {project.githubUrl && (
          <Button variant="ghost" size="sm" asLink href={project.githubUrl}>
            ⌥ Code
          </Button>
        )}
      </div>
    </div>
  );
}
