export default function HeroSection() {
  return (
    <section className="min-h-[90vh] flex items-center max-w-7xl mx-auto px-6 pt-20 pb-16">
      <div className="max-w-3xl">
        <div className="animate-fade-up mb-8">
          <span className="text-sm font-medium text-[var(--accent-light)]">Rajib Labs</span>
        </div>

        <h1 className="animate-fade-up delay-1 text-5xl sm:text-6xl md:text-7xl font-bold tracking-tight leading-[1.08] mb-4">
          Rajib Mahata
        </h1>

        <p className="animate-fade-up delay-2 text-xl sm:text-2xl md:text-3xl text-white font-medium mb-4 leading-snug">
          Building modern software, products, and digital experiences
        </p>

        <p className="animate-fade-up delay-2 text-lg text-[var(--text-secondary)] max-w-xl mb-10">
          Senior Software Architect with 10+ years crafting production SaaS platforms, AI systems, and cloud-native applications.
        </p>

        <div className="animate-fade-up delay-3 flex flex-wrap gap-4">
          <a href="#projects" onClick={e => { e.preventDefault(); document.getElementById('projects')?.scrollIntoView({ behavior:'smooth' }); }}
            className="px-6 py-3 rounded-xl bg-white text-black font-semibold text-sm hover:bg-gray-200 transition-all">
            View Projects
          </a>
          <a href="#resume" onClick={e => { e.preventDefault(); document.getElementById('resume')?.scrollIntoView({ behavior:'smooth' }); }}
            className="px-6 py-3 rounded-xl border border-[var(--border)] text-white font-medium text-sm hover:border-[var(--text-muted)] transition-all">
            View Resume
          </a>
          <a href="#contact" onClick={e => { e.preventDefault(); document.getElementById('contact')?.scrollIntoView({ behavior:'smooth' }); }}
            className="px-6 py-3 rounded-xl border border-[var(--border)] text-[var(--text-secondary)] font-medium text-sm hover:border-[var(--text-muted)] hover:text-white transition-all">
            Contact
          </a>
        </div>
      </div>
    </section>
  );
}
