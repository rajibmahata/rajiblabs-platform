const currentProjects = [
  { name: 'DocSignerHub', emoji: '📝', status: 'Building', progress: 85, sprint: 'Auth v2 + Blog engine', nextMilestone: 'Enterprise SSO', color: 'from-blue-500 to-cyan-500' },
  { name: 'AI Avatar RAG', emoji: '🧠', status: 'Building', progress: 60, sprint: 'Vector search optimization', nextMilestone: 'Multi-tenant RAG', color: 'from-purple-500 to-pink-500' },
  { name: 'Solicitor CMS', emoji: '⚖️', status: 'Planning', progress: 25, sprint: 'Workflow engine design', nextMilestone: 'Case tracker MVP', color: 'from-amber-500 to-orange-500' },
  { name: 'Rajib Labs', emoji: '⚡', status: 'Building', progress: 70, sprint: 'AI workforce integration', nextMilestone: 'Full platform launch', color: 'from-indigo-500 to-violet-500' },
];

export default function CurrentWork() {
  return (
    <section id="work" className="max-w-7xl mx-auto px-6 pb-24">
      <div className="text-center mb-14">
        <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--text-muted)] mb-4">Current Work</h2>
        <p className="text-3xl md:text-4xl font-bold text-white mb-4">
          What's being built right now
        </p>
        <p className="text-[var(--text-secondary)] max-w-xl mx-auto">
          Active projects with live status updates. Each project is managed by the AI workforce pipeline.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-5">
        {currentProjects.map((p, i) => (
          <div key={p.name} className="glass-card p-6 animate-fade-up" style={{ animationDelay: `${i * 0.08}s`, opacity: 0 }}>
            <div className="flex items-start gap-4 mb-4">
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${p.color} flex items-center justify-center text-2xl flex-shrink-0 shadow-lg`}>
                {p.emoji}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-base font-semibold text-white">{p.name}</h3>
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-400/10 text-blue-400 border border-blue-400/20">{p.status}</span>
                </div>
                <p className="text-xs text-[var(--text-muted)]">Sprint: {p.sprint}</p>
              </div>
            </div>

            {/* Progress bar */}
            <div className="mb-3">
              <div className="flex justify-between text-[11px] mb-1.5">
                <span className="text-[var(--text-muted)]">Progress</span>
                <span className="text-white font-medium">{p.progress}%</span>
              </div>
              <div className="h-1.5 bg-[var(--bg-hover)] rounded-full overflow-hidden">
                <div className={`h-full rounded-full bg-gradient-to-r ${p.color} transition-all duration-700`}
                  style={{ width: `${p.progress}%` }}>
                </div>
              </div>
            </div>

            <div className="text-[11px] text-[var(--text-muted)]">
              Next: <span className="text-[var(--text-secondary)]">{p.nextMilestone}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
