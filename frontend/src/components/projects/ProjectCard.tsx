import type { Project } from '../../types';

const statusConfig: Record<string, { label: string; classes: string; dot: string }> = {
  planning:  { label: 'Planning',  classes: 'bg-amber-400/10 text-amber-400 border-amber-400/20', dot: 'bg-amber-400' },
  development: { label: 'In Dev', classes: 'bg-blue-400/10 text-blue-400 border-blue-400/20', dot: 'bg-blue-400' },
  qa:         { label: 'QA',       classes: 'bg-purple-400/10 text-purple-400 border-purple-400/20', dot: 'bg-purple-400' },
  deployed:   { label: 'Live',     classes: 'bg-emerald-400/10 text-emerald-400 border-emerald-400/20', dot: 'bg-emerald-400' },
};

export default function ProjectCard({ project, index }: { project: Project; index: number }) {
  const status = statusConfig[project.status] || statusConfig.planning;

  return (
    <a
      href={project.liveUrl || project.githubUrl}
      target="_blank"
      rel="noopener noreferrer"
      className={`block group glass-card rounded-2xl p-6 animate-in`}
      style={{ animationDelay: `${0.1 + index * 0.08}s`, opacity: 0 }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 to-cyan-400/20 border border-indigo-500/20 flex items-center justify-center text-lg font-bold text-indigo-400 group-hover:scale-110 transition-transform">
            {project.title.charAt(0)}
          </div>
          <h3 className="text-lg font-semibold text-white group-hover:text-indigo-300 transition-colors">
            {project.title}
          </h3>
        </div>
        <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border ${status.classes}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`}></span>
          {status.label}
        </span>
      </div>

      {/* Description */}
      <p className="text-sm text-[var(--color-text-secondary)] mb-5 line-clamp-2 leading-relaxed">
        {project.description}
      </p>

      {/* Tech stack */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {project.techStack.map(tech => (
          <span key={tech} className="text-xs px-2 py-1 rounded-md bg-white/[0.03] border border-[var(--color-border)] text-[var(--color-text-muted)]">
            {tech}
          </span>
        ))}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-[var(--color-border)]">
        {project.lastCommitAt ? (
          <span className="text-xs text-[var(--color-text-muted)]">
            Updated {new Date(project.lastCommitAt).toLocaleDateString('en-US', {
              month: 'short', day: 'numeric'
            })}
          </span>
        ) : (
          <span></span>
        )}
        <span className="text-xs text-indigo-400/70 group-hover:text-indigo-400 transition-colors flex items-center gap-1">
          {project.liveUrl ? 'Visit →' : 'View →'}
        </span>
      </div>
    </a>
  );
}
