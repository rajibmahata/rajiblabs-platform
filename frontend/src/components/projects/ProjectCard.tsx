import type { Project } from '../../types';

const statusMap: Record<string, { label: string; color: string; dot: string }> = {
  planning:    { label: 'Planning', color: 'text-amber-400', dot: 'bg-amber-400' },
  development: { label: 'In Development', color: 'text-blue-400', dot: 'bg-blue-400' },
  qa:          { label: 'In QA', color: 'text-purple-400', dot: 'bg-purple-400' },
  deployed:    { label: 'Live', color: 'text-emerald-400', dot: 'bg-emerald-400' },
};

const projectIcons: Record<string, string> = {
  docsignerhub: '📄',
  'ai-avatar-rag': '🤖',
  'solicitor-cms': '⚖️',
  rajiblabs: '⚡',
};

export default function ProjectCard({ project, index }: { project: Project; index: number }) {
  const s = statusMap[project.status] || statusMap.planning;
  const icon = projectIcons[project.slug] || '🚀';

  return (
    <a
      href={project.liveUrl || project.githubUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="group block p-6 rounded-2xl bg-[var(--bg-card)] border border-[var(--border)] hover:border-[var(--border-hover)] transition-all duration-300 animate-fade-up"
      style={{ animationDelay: `${0.1 + index * 0.1}s`, opacity: 0 }}
    >
      {/* Icon + Status */}
      <div className="flex items-start justify-between mb-5">
        <div className="w-12 h-12 rounded-xl bg-[var(--bg-hover)] border border-[var(--border)] flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
          {icon}
        </div>
        <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${s.color}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`}></span>
          {s.label}
        </span>
      </div>

      {/* Title + Description */}
      <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-[var(--accent-light)] transition-colors">
        {project.title}
      </h3>
      <p className="text-sm text-[var(--text-secondary)] mb-5 leading-relaxed line-clamp-2">
        {project.description}
      </p>

      {/* Tech tags */}
      <div className="flex flex-wrap gap-1.5 mb-5">
        {project.techStack.slice(0, 5).map(t => (
          <span key={t} className="text-xs px-2.5 py-1 rounded-md bg-[var(--bg-hover)] text-[var(--text-muted)] border border-[var(--border)]">
            {t}
          </span>
        ))}
        {project.techStack.length > 5 && (
          <span className="text-xs px-2.5 py-1 rounded-md text-[var(--text-muted)]">
            +{project.techStack.length - 5}
          </span>
        )}
      </div>

      {/* Footer */}
      <div className="pt-4 border-t border-[var(--border)] flex items-center justify-between text-xs text-[var(--text-muted)]">
        <span>
          {project.lastCommitAt
            ? `Updated ${timeAgo(project.lastCommitAt)}`
            : project.createdAt
              ? `Created ${new Date(project.createdAt).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}`
              : ''}
        </span>
        <span className="text-[var(--accent-light)] opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
          {project.liveUrl ? 'Visit site →' : 'View repo →'}
        </span>
      </div>
    </a>
  );
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
