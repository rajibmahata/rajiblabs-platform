const experience = [
  { role: 'Senior Software Architect', period: '2019 — Present', desc: 'Independent consultant. Designed and built multiple SaaS platforms, AI systems, and enterprise applications from scratch. Leading AI workforce initiative with autonomous development agents.' },
  { role: 'Senior Software Engineer', period: '2015 — 2019', desc: 'Led .NET development teams building enterprise applications. Architected microservices, designed REST APIs, managed Azure cloud infrastructure.' },
  { role: 'Software Engineer', period: '2012 — 2015', desc: 'Full-stack .NET development. Built web applications, APIs, and database systems for enterprise clients.' },
];

const skills = ['.NET 8/10', 'C#', 'ASP.NET Core', 'Blazor', 'React', 'TypeScript', 'Azure Cloud', 'Microservices', 'SQL Server', 'Cosmos DB', 'Docker', 'REST APIs', 'AI/LLM Integration', 'RAG Systems', 'OpenAI API', 'GitHub Copilot'];

export default function ResumeSection() {
  return (
    <section id="resume" className="max-w-7xl mx-auto px-6 pb-24">
      <div className="section-tag">Resume</div>
      <h2 className="text-3xl md:text-4xl font-bold text-white mb-10">Experience & Skills</h2>

      <div className="grid lg:grid-cols-2 gap-10">
        {/* Experience */}
        <div className="animate-fade-up">
          <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-muted)] mb-6">Work History</h3>
          <div className="space-y-5">
            {experience.map((exp, i) => (
              <div key={i} className="card p-5">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-semibold text-white">{exp.role}</h4>
                  <span className="text-[11px] text-[var(--text-muted)]">{exp.period}</span>
                </div>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{exp.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Skills */}
        <div className="animate-fade-up delay-2">
          <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-muted)] mb-6">Technical Skills</h3>
          <div className="card p-5">
            <div className="flex flex-wrap gap-2">
              {skills.map(s => (
                <span key={s} className="text-xs px-3 py-2 rounded-lg bg-white/[0.03] border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--border-hover)] hover:text-white transition-colors">
                  {s}
                </span>
              ))}
            </div>
          </div>

          <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-muted)] mb-6 mt-8">Certifications & Education</h3>
          <div className="card p-5 space-y-3">
            {[
              'Microsoft Certified: Azure Solutions Architect',
              'Microsoft Certified: Azure Developer Associate',
              'Bachelor of Technology in Computer Science',
            ].map((c, i) => (
              <div key={i} className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                <span className="text-emerald-400">✓</span> {c}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
