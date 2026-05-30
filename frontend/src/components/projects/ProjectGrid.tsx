import { useState, useEffect } from 'react';
import type { Project } from '../../types';
import { getProjects } from '../../services/api';
import ProjectCard from './ProjectCard';

export default function ProjectGrid() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProjects()
      .then(setProjects)
      .catch(() => setProjects([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="max-w-6xl mx-auto px-6 pb-16">
      {/* Section header */}
      <div className="flex items-center gap-4 mb-10">
        <h2 className="text-sm font-semibold uppercase tracking-[0.15em] text-[var(--text-muted)]">
          Projects
        </h2>
        <div className="h-px flex-1 bg-[var(--border)]"></div>
        <span className="text-xs text-[var(--text-muted)] tabular-nums">
          {loading ? '...' : projects.length}
        </span>
      </div>

      {loading ? (
        <div className="grid md:grid-cols-2 gap-5">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="p-6 rounded-2xl bg-[var(--bg-card)] border border-[var(--border)] animate-pulse">
              <div className="flex justify-between mb-5">
                <div className="w-12 h-12 rounded-xl bg-[var(--bg-hover)]"></div>
                <div className="h-5 w-24 rounded-full bg-[var(--bg-hover)]"></div>
              </div>
              <div className="h-5 w-48 bg-[var(--bg-hover)] rounded mb-2"></div>
              <div className="h-4 w-full bg-[var(--bg-hover)] rounded mb-1"></div>
              <div className="h-4 w-2/3 bg-[var(--bg-hover)] rounded mb-5"></div>
              <div className="flex gap-1.5 mb-5">
                <div className="h-6 w-16 bg-[var(--bg-hover)] rounded-md"></div>
                <div className="h-6 w-20 bg-[var(--bg-hover)] rounded-md"></div>
                <div className="h-6 w-14 bg-[var(--bg-hover)] rounded-md"></div>
              </div>
              <div className="pt-4 border-t border-[var(--border)]">
                <div className="h-3 w-24 bg-[var(--bg-hover)] rounded"></div>
              </div>
            </div>
          ))}
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-20 rounded-2xl bg-[var(--bg-card)] border border-[var(--border)]">
          <div className="text-4xl mb-4">🚀</div>
          <h3 className="text-lg font-medium text-white mb-2">No projects yet</h3>
          <p className="text-sm text-[var(--text-muted)]">Projects will appear here as the AI workforce builds them.</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-5">
          {projects.map((p, i) => (
            <ProjectCard key={p.id} project={p} index={i} />
          ))}
        </div>
      )}
    </section>
  );
}
