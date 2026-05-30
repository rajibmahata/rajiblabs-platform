import type { Project } from '../../types';

const statusMap: Record<string, { label: string; color: string; dot: string; bg: string }> = {
  planning:    { label: 'Planning', color: 'text-amber-300', dot: 'bg-amber-400', bg: 'bg-amber-400/5 border-amber-400/15' },
  development: { label: 'Building', color: 'text-blue-300', dot: 'bg-blue-400', bg: 'bg-blue-400/5 border-blue-400/15' },
  qa:          { label: 'In QA', color: 'text-purple-300', dot: 'bg-purple-400', bg: 'bg-purple-400/5 border-purple-400/15' },
  deployed:    { label: 'Live', color: 'text-emerald-300', dot: 'bg-emerald-400', bg: 'bg-emerald-400/5 border-emerald-400/15' },
};

const icons: Record<string, string> = {
  docsignerhub: '📝', 'ai-avatar-rag': '🧠', 'solicitor-cms': '⚖️', rajiblabs: '⚡',
};

export default function ProjectCard({ project, index }: { project: Project; index: number }) {
  const s = statusMap[project.status] || statusMap.planning;

  return (
    <a href={project.liveUrl || project.githubUrl} target="_blank" rel="noopener noreferrer"
      className={`block group glass-card p-6 animate-fade-up`}
      style={{ animationDelay: `${index * 0.08}s`, opacity: 0 }}
    >
      {/* Top: Icon + Status + Title */}
      <div className="flex items-start gap-4 mb-4">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 flex items-center justify-center text-2xl flex-shrink-0 group-hover:scale-110 transition-transform">
          {icons[project.slug] || '🚀'}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-base font-semibold text-white group-hover:text-indigo-300 transition-colors truncate">
              {project.title}
            </h3>
          </div>
          <span className={`inline-flex items-center gap-1.5 text-[11px] font-medium px-2 py-0.5 rounded-full border ${s.bg} ${s.color}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`}></span>
            {s.label}
          </span>
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-[var(--text-secondary)] mb-4 leading-relaxed line-clamp-2">
        {project.description}
      </p>

      {/* Tech tags */}
      <div className="flex flex-wrap gap-1.5 mb-5">
        {project.techStack.map(t => (
          <span key={t} className="text-[11px] px-2 py-1 rounded-md bg-[var(--bg-hover)] text-[var(--text-muted)] border border-[var(--border)]">
            {t}
          </span>
        ))}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-[var(--border)]">
        <span className="text-[11px] text-[var(--text-muted)]">
          {project.lastCommitAt ? timeAgo(project.lastCommitAt) : ''}
        </span>
        <span className="text-[11px] font-medium text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity">
          {project.liveUrl ? 'Visit →' : 'GitHub →'}
        </span>
      </div>
    </a>
  );
}

function timeAgo(d: string): string {
  const diff = Date.now() - new Date(d).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'Just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const days = Math.floor(h / 24);
  if (days < 7) return `${days}d ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
