const experiments = [
  { title: 'Autonomous Code Review', desc: 'AI agent that reviews PRs, suggests improvements, and catches bugs before merge', status: 'Research', color: 'from-purple-500' },
  { title: 'Self-Healing APIs', desc: 'APIs that detect failures and auto-recover using circuit breakers and AI diagnostics', status: 'Concept', color: 'from-blue-500' },
  { title: 'AI-Powered Documentation', desc: 'Real-time documentation generation from codebases and API definitions', status: 'Prototype', color: 'from-green-500' },
  { title: 'Multi-Agent Orchestration', desc: 'Framework for coordinating multiple AI agents working on complex software projects', status: 'Active', color: 'from-amber-500' },
  { title: 'Zero-Shot Code Migration', desc: 'AI system that migrates legacy .NET Framework code to .NET 8 with minimal human input', status: 'Idea', color: 'from-pink-500' },
];

const statusColors: Record<string, string> = {
  Active: 'bg-green-400/10 text-green-400 border-green-400/20',
  Prototype: 'bg-blue-400/10 text-blue-400 border-blue-400/20',
  Research: 'bg-purple-400/10 text-purple-400 border-purple-400/20',
  Concept: 'bg-amber-400/10 text-amber-400 border-amber-400/20',
  Idea: 'bg-slate-400/10 text-slate-400 border-slate-400/20',
};

export default function InnovationLab() {
  return (
    <section id="lab" className="max-w-7xl mx-auto px-6 pb-24">
      <div className="text-center mb-14">
        <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--text-muted)] mb-4">Innovation Lab</h2>
        <p className="text-3xl md:text-4xl font-bold text-white mb-4">
          Experiments & future ideas
        </p>
        <p className="text-[var(--text-secondary)] max-w-xl mx-auto">
          Research projects, prototypes, and forward-looking experiments. This is where tomorrow's products start.
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {experiments.map((exp, i) => (
          <div key={exp.title} className="glass-card p-5 animate-fade-up" style={{ animationDelay: `${i * 0.07}s`, opacity: 0 }}>
            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${exp.color} to-transparent opacity-20 absolute -top-1 -right-1`}></div>
            <div className="relative">
              <div className="flex items-center justify-between mb-3">
                <span className={`text-[10px] px-2 py-0.5 rounded-full border ${statusColors[exp.status]}`}>{exp.status}</span>
              </div>
              <h3 className="text-sm font-semibold text-white mb-2">{exp.title}</h3>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">{exp.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
