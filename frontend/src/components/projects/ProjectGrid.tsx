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
    <section id="projects">
      <div className="flex items-center gap-3 mb-10">
        <div className="h-px flex-1 bg-[var(--color-border)]"></div>
        <h2 className="text-sm font-semibold uppercase tracking-widest text-[var(--color-text-muted)]">
          Projects
        </h2>
        <span className="text-xs text-[var(--color-text-muted)] bg-white/[0.03] px-2 py-0.5 rounded-full border border-[var(--color-border)]">
          {loading ? '...' : projects.length}
        </span>
        <div className="h-px flex-1 bg-[var(--color-border)]"></div>
      </div>

      {loading ? (
        <div className="grid md:grid-cols-2 gap-6">
          {[1,2,3,4].map(i => (
            <div key={i} className="glass-card rounded-2xl p-6 animate-pulse">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-white/5"></div>
                <div className="h-5 w-32 bg-white/5 rounded"></div>
              </div>
              <div className="h-4 w-full bg-white/5 rounded mb-2"></div>
              <div className="h-4 w-2/3 bg-white/5 rounded mb-4"></div>
              <div className="flex gap-2 mb-4">
                <div className="h-6 w-16 bg-white/5 rounded-md"></div>
                <div className="h-6 w-20 bg-white/5 rounded-md"></div>
                <div className="h-6 w-14 bg-white/5 rounded-md"></div>
              </div>
            </div>
          ))}
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-16 glass-card rounded-2xl">
          <div className="text-4xl mb-4">⚡</div>
          <p className="text-[var(--color-text-secondary)] text-lg mb-2">No projects yet</p>
          <p className="text-[var(--color-text-muted)] text-sm">The AI workforce will populate this automatically.</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {projects.map((p, i) => (
            <ProjectCard key={p.id} project={p} index={i} />
          ))}
        </div>
      )}
    </section>
  );
}
