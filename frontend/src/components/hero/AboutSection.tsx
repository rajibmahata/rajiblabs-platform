export default function AboutSection() {
  return (
    <section id="about" className="max-w-7xl mx-auto px-6 pb-24">
      <div className="max-w-3xl animate-fade-up">
        <div className="section-tag">About</div>
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-8">Professional Profile</h2>

        <div className="grid sm:grid-cols-2 gap-4 mb-8">
          {[
            ['📍', 'Location', 'Kolkata, India · Remote'],
            ['⏳', 'Experience', '10+ years'],
            ['🎯', 'Specialization', '.NET, Azure, AI/LLM'],
            ['🚀', 'Projects Delivered', '15+ production systems'],
          ].map(([icon, label, value]) => (
            <div key={label} className="card p-4 flex items-center gap-3">
              <span className="text-xl">{icon}</span>
              <div>
                <div className="text-[11px] text-[var(--text-muted)]">{label}</div>
                <div className="text-sm text-white font-medium">{value}</div>
              </div>
            </div>
          ))}
        </div>

        <p className="text-[var(--text-secondary)] leading-relaxed mb-4">
          Independent software architect specializing in the .NET ecosystem, Azure cloud architecture, and AI/LLM integrations. I build complete SaaS platforms — from database design to frontend development to CI/CD pipelines.
        </p>
        <p className="text-[var(--text-secondary)] leading-relaxed">
          Currently building DocSignerHub, AI Avatar RAG Platform, and Rajib Labs. I bring deep architecture knowledge with practical AI implementation — leveraging LLMs, RAG systems, and autonomous agents to build smarter software faster.
        </p>
      </div>
    </section>
  );
}
