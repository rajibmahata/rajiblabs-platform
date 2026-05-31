export default function ResumeSection() {
  return (
    <section id="resume" className="max-w-7xl mx-auto px-6 pb-24">
      <div className="text-center mb-14">
        <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--text-muted)] mb-4">Resume & Credentials</h2>
        <p className="text-3xl md:text-4xl font-bold text-white mb-4">
          Professional journey
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* About */}
        <div className="lg:col-span-2 glass-card p-8 animate-fade-up">
          <h3 className="text-xl font-bold text-white mb-4">Rajib Mahata</h3>
          <p className="text-sm font-medium text-[var(--accent-light)] mb-6">Senior Software Architect | AI & SaaS Platform Builder | Independent Consultant</p>
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-6">
            Independent software architect with 10+ years of hands-on experience designing, building, and deploying production-grade software systems. I specialize in .NET ecosystem, Azure cloud architecture, microservices, and AI/LLM integrations. I've built complete SaaS platforms from scratch — handling everything from database design to CI/CD pipelines to frontend development.
          </p>
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
            Currently building DocSignerHub (digital signature SaaS), AI Avatar RAG Platform (enterprise knowledge retrieval), and Rajib Labs (autonomous AI workforce platform). I combine deep architecture knowledge with practical AI implementation — using LLMs, RAG systems, and AI agents to build smarter software faster.
          </p>
        </div>

        {/* Quick facts */}
        <div className="glass-card p-8 animate-fade-up delay-1">
          <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-muted)] mb-6">Quick Facts</h3>
          <div className="space-y-4">
            {[
              ['📍', 'Location', 'Kolkata, India (Remote)'],
              ['⏳', 'Experience', '10+ years'],
              ['🎯', 'Focus', 'SaaS, AI, Cloud'],
              ['🛠', 'Primary Stack', '.NET, React, Azure'],
              ['🤖', 'AI', 'LLMs, RAG, Agents'],
              ['🌍', 'Clients', 'International'],
            ].map(([icon, label, value]) => (
              <div key={label} className="flex items-center gap-3">
                <span className="text-lg">{icon}</span>
                <div>
                  <div className="text-[11px] text-[var(--text-muted)]">{label}</div>
                  <div className="text-sm text-white font-medium">{value}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
