const agents = [
  { role: 'Architect', emoji: '🧠', id: 'e441e421', status: 'Active', task: 'Planning platform evolution', color: 'from-purple-500 to-indigo-500' },
  { role: 'UX Designer', emoji: '🎨', id: '63c7532d', status: 'Active', task: 'Validating UI/UX standards', color: 'from-pink-500 to-rose-500' },
  { role: 'Developer', emoji: '👷', id: '87745ce0', status: 'Active', task: 'Building new features', color: 'from-blue-500 to-cyan-500' },
  { role: 'QA Engineer', emoji: '🧪', id: '7a4d415c', status: 'Active', task: 'Running test suites', color: 'from-amber-500 to-orange-500' },
  { role: 'DevOps', emoji: '🚀', id: '16954a53', status: 'Active', task: 'Managing infrastructure', color: 'from-green-500 to-emerald-500' },
  { role: 'Monitor', emoji: '👀', id: 'eb6f6a39', status: 'Active', task: 'Watching repositories', color: 'from-cyan-500 to-teal-500' },
  { role: 'Portfolio', emoji: '📊', id: '0a069639', status: 'Active', task: 'Managing content', color: 'from-violet-500 to-purple-500' },
];

export default function WorkforceSection() {
  return (
    <section id="workforce" className="max-w-7xl mx-auto px-6 pb-24">
      <div className="text-center mb-14 animate-fade-up">
        <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--text-muted)] mb-4">AI Workforce</h2>
        <p className="text-3xl md:text-4xl font-bold text-white mb-4">
          Autonomous agents powering the lab
        </p>
        <p className="text-[var(--text-secondary)] max-w-xl mx-auto">
          7 specialized AI agents work together — architecting, building, testing, deploying, and monitoring. An autonomous software factory.
        </p>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {agents.map((a, i) => (
          <div key={a.role} className="glass-card p-5 animate-fade-up" style={{ animationDelay: `${i * 0.06}s`, opacity: 0 }}>
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${a.color} flex items-center justify-center text-lg shadow-lg`}>
                {a.emoji}
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">{a.role}</h3>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--green)]"></span>
                  <span className="text-[11px] text-[var(--text-muted)]">{a.status}</span>
                </div>
              </div>
            </div>
            <p className="text-xs text-[var(--text-muted)] mb-3">{a.task}</p>
            <code className="text-[10px] text-[var(--text-muted)] bg-[var(--bg-hover)] px-2 py-1 rounded font-mono">{a.id}</code>
          </div>
        ))}
      </div>
    </section>
  );
}
