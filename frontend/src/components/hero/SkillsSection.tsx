const skills = [
  { category: 'Backend', items: ['.NET 8/10', 'C#', 'ASP.NET Core', 'Python FastAPI', 'REST APIs', 'Microservices'] },
  { category: 'Frontend', items: ['React', 'TypeScript', 'Blazor', 'Tailwind CSS', 'JavaScript'] },
  { category: 'Cloud & Data', items: ['Azure', 'SQL Server', 'Cosmos DB', 'Docker', 'GitHub Actions'] },
  { category: 'AI & ML', items: ['LLM Integration', 'RAG Systems', 'OpenAI API', 'Gemini API', 'Semantic Search'] },
];

export default function SkillsSection() {
  return (
    <section className="max-w-6xl mx-auto px-6 pb-20">
      <div className="flex items-center gap-4 mb-10">
        <h2 className="text-sm font-semibold uppercase tracking-[0.15em] text-[var(--text-muted)]">
          Expertise
        </h2>
        <div className="h-px flex-1 bg-[var(--border)]"></div>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {skills.map((group, i) => (
          <div
            key={group.category}
            className="p-5 rounded-2xl bg-[var(--bg-card)] border border-[var(--border)] animate-fade-up"
            style={{ animationDelay: `${0.1 + i * 0.1}s`, opacity: 0 }}
          >
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-4">
              {group.category}
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {group.items.map(skill => (
                <span key={skill} className="text-xs px-2.5 py-1.5 rounded-lg bg-[var(--bg-hover)] text-[var(--text-secondary)] border border-[var(--border)]">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
