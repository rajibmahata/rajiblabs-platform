import type { Project } from '../../types';

const statusColors: Record<string, string> = {
  planning: 'bg-yellow-400/10 text-yellow-400 border-yellow-400/20',
  development: 'bg-blue-400/10 text-blue-400 border-blue-400/20',
  qa: 'bg-purple-400/10 text-purple-400 border-purple-400/20',
  deployed: 'bg-green-400/10 text-green-400 border-green-400/20',
};

export default function ProjectCard({ project }: { project: Project }) {
  return (
    <a
      href={project.githubUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="block group p-6 rounded-xl border border-gray-800 bg-gray-900/50 hover:border-gray-700 hover:bg-gray-900 transition-all"
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-100 group-hover:text-blue-400 transition-colors">
          {project.title}
        </h3>
        <span className={`text-xs px-2 py-1 rounded-full border ${statusColors[project.status]}`}>
          {project.status}
        </span>
      </div>

      <p className="text-sm text-gray-400 mb-4 line-clamp-2">
        {project.description}
      </p>

      <div className="flex flex-wrap gap-2 mb-4">
        {project.techStack.map(tech => (
          <span key={tech} className="text-xs px-2 py-0.5 bg-gray-800 rounded text-gray-500">
            {tech}
          </span>
        ))}
      </div>

      {project.lastCommitAt && (
        <p className="text-xs text-gray-600">
          Last active: {new Date(project.lastCommitAt).toLocaleDateString('en-US', {
            month: 'short', day: 'numeric', year: 'numeric'
          })}
        </p>
      )}
    </a>
  );
}
