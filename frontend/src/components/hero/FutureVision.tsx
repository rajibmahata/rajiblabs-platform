export default function FutureVision() {
  return (
    <section id="future" className="max-w-7xl mx-auto px-6 pb-24">
      <div className="glass-card p-10 md:p-16 text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-purple-500/5 via-transparent to-transparent"></div>
        <div className="relative">
          <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--accent-light)] mb-4">Future Vision</h2>
          <p className="text-3xl md:text-4xl font-bold text-white mb-6">
            An AI-powered software factory
          </p>
          <p className="text-[var(--text-secondary)] max-w-2xl mx-auto mb-8 text-lg leading-relaxed">
            Rajib Labs is evolving into an autonomous software development platform where AI agents collaborate to analyze, design, develop, test, document, deploy, and maintain production software — with minimal human intervention.
          </p>
          <div className="flex flex-wrap justify-center gap-3 text-sm text-[var(--text-muted)]">
            <span className="px-3 py-1.5 rounded-lg bg-white/[0.03] border border-[var(--border)]">Autonomous Development</span>
            <span className="px-3 py-1.5 rounded-lg bg-white/[0.03] border border-[var(--border)]">AI Code Review</span>
            <span className="px-3 py-1.5 rounded-lg bg-white/[0.03] border border-[var(--border)]">Self-Healing Systems</span>
            <span className="px-3 py-1.5 rounded-lg bg-white/[0.03] border border-[var(--border)]">Agent Orchestration</span>
            <span className="px-3 py-1.5 rounded-lg bg-white/[0.03] border border-[var(--border)]">Continuous Delivery</span>
          </div>
        </div>
      </div>
    </section>
  );
}
