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

  if (loading) return <div className="text-center text-gray-500 py-12">Loading projects...</div>;

  return (
    <section>
      <h2 className="text-2xl font-bold mb-8">
        Projects{" "}
        <span className="text-gray-500 text-lg font-normal">
          ({projects.length})
        </span>
      </h2>

      {projects.length === 0 ? (
        <p className="text-gray-500 text-center py-12">
          No projects yet. The AI workforce will populate this soon.
        </p>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {projects.map(p => (
            <ProjectCard key={p.id} project={p} />
          ))}
        </div>
      )}
    </section>
  );
}
