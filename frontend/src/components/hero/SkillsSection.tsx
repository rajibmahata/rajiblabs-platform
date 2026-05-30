const skills = [
  { label: 'Backend', items: ['.NET 8/10', 'C#', 'ASP.NET Core', 'Python', 'REST APIs', 'Microservices'] },
  { label: 'Frontend', items: ['React', 'TypeScript', 'Blazor', 'Tailwind CSS', 'JavaScript'] },
  { label: 'Cloud', items: ['Azure', 'SQL Server', 'Cosmos DB', 'Docker', 'CI/CD'] },
  { label: 'AI & ML', items: ['LLMs', 'RAG', 'OpenAI', 'Vector DB', 'Semantic Search'] },
];

export default function SkillsSection() {
  return (
    <section className="max-w-7xl mx-auto px-6 pb-20">
      <div className="flex items-center gap-4 mb-8">
        <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--text-muted)]">Expertise</h2>
        <div className="h-px flex-1 bg-[var(--border)]"></div>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {skills.map((g, i) => (
          <div key={g.label} className="glass-card p-5 animate-fade-up"
            style={{ animationDelay: `${i * 0.08}s`, opacity: 0 }}>
            <h3 className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)] mb-4">{g.label}</h3>
            <div className="flex flex-wrap gap-1.5">
              {g.items.map(s => (
                <span key={s} className="text-[11px] px-2.5 py-1.5 rounded-lg bg-[var(--bg-hover)] text-[var(--text-secondary)] border border-[var(--border)]">
                  {s}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
