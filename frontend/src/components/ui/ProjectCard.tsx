import TechChip from './TechChip';

interface ProjectCardProps {
  name: string;
  description: string;
  techStack: string[];
  liveUrl?: string | null;
  githubUrl?: string | null;
  cbUrl?: string | null;
  source: 'github' | 'claude_cb' | 'localhost';
  isFeatured?: boolean;
  className?: string;
}

const sourceConfig = {
  github:     { label: 'GitHub',     color: '#22C55E', bgOpacity: 0.15, borderOpacity: 0.4 },
  claude_cb:  { label: 'Claude/CB',  color: '#8B5CF6', bgOpacity: 0.15, borderOpacity: 0.4 },
  localhost:  { label: 'Localhost',  color: 'var(--c-accent-gold)', bgOpacity: 0.15, borderOpacity: 0.4 },
};

export default function ProjectCard({
  name,
  description,
  techStack,
  liveUrl,
  githubUrl,
  cbUrl,
  source,
  isFeatured = false,
  className = '',
}: ProjectCardProps) {
  const src = sourceConfig[source];

  return (
    <div
      className={`card p-5 group ${isFeatured ? 'ring-1 ring-[var(--c-accent-blue)]/30' : ''} ${className}`}
      style={{
        minHeight: 280,
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
      {/* Source badge */}
      <div className="flex justify-between items-start mb-3">
        <h3 style={{
          fontFamily: 'var(--font-heading)',
          fontSize: 16,
          fontWeight: 500,
          color: 'var(--c-text-primary)',
        }}>
          {name}
        </h3>
        <span
          className="font-mono text-[10px] px-2 py-0.5 rounded-sm border"
          style={{
            backgroundColor: `${src.color} / ${src.bgOpacity * 100}`,
            borderColor: src.color,
            borderColor: `${src.color} / ${src.borderOpacity * 100}`,
            color: src.color,
          }}
        >
          {src.label}
        </span>
      </div>

      <p style={{
        fontFamily: 'var(--font-body)',
        fontSize: 14,
        color: 'var(--c-text-secondary)',
        lineHeight: 'var(--lh-body)',
        marginBottom: 12,
      }}>
        {description}
      </p>

      {/* Tech stack */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {techStack.slice(0, 5).map(t => (
          <TechChip key={t} label={t} category={getCategory(t)} />
        ))}
        {techStack.length > 5 && (
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: 'var(--c-text-muted)',
            padding: '2px 8px',
            border: '1px solid var(--c-border)',
            borderRadius: 'var(--radius-sm)',
          }}>
            +{techStack.length - 5} more
          </span>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex flex-wrap gap-2 mt-auto">
        {liveUrl && (
          <a
            href={liveUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[13px] font-medium inline-flex items-center gap-1 transition-colors"
            style={{ color: 'var(--c-accent-blue)' }}
            onMouseEnter={e => { e.currentTarget.style.color = 'var(--c-accent-blue-l)'; }}
            onMouseLeave={e => { e.currentTarget.style.color = 'var(--c-accent-blue)'; }}
          >
            ↗ Live
          </a>
        )}
        {githubUrl && (
          <a
            href={githubUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[13px] font-medium inline-flex items-center gap-1 transition-colors"
            style={{ color: 'var(--c-text-muted)' }}
            onMouseEnter={e => { e.currentTarget.style.color = 'var(--c-text-primary)'; }}
            onMouseLeave={e => { e.currentTarget.style.color = 'var(--c-text-muted)'; }}
          >
            ⌥ GitHub
          </a>
        )}
        {cbUrl && (
          <a
            href={cbUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[13px] font-medium inline-flex items-center gap-1 transition-colors"
            style={{ color: 'var(--c-text-muted)' }}
            onMouseEnter={e => { e.currentTarget.style.color = '#8B5CF6'; }}
            onMouseLeave={e => { e.currentTarget.style.color = 'var(--c-text-muted)'; }}
          >
            ⌥ CB
          </a>
        )}
      </div>
    </div>
  );
}

function getCategory(tech: string): 'backend' | 'cloud' | 'frontend' | 'ai' | 'tools' {
  const t = tech.toLowerCase();
  if (/\.net|c#|asp\.net|blazor|python|fastapi|entity|sql|cosmos|wcf/.test(t)) return 'backend';
  if (/azure|docker|kubernetes|aws|cloud|terraform/.test(t)) return 'cloud';
  if (/react|typescript|javascript|next|vue|angular|html|css/.test(t)) return 'frontend';
  if (/ai|rag|openai|gpt|llm|claude|ml|machine|chroma|vector|embed/.test(t)) return 'ai';
  return 'tools';
}
