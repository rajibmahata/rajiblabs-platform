export default function HeroSection() {
  const stats = [
    { value: '10+', label: 'Years building software' },
    { value: '15+', label: 'Projects delivered' },
    { value: '3', label: 'Live SaaS products' },
    { value: '4K+', label: 'GitHub contributions' },
  ];

  return (
    <section className="pt-24 pb-20 md:pt-36 md:pb-28 max-w-7xl mx-auto px-6">
      <div className="grid lg:grid-cols-2 gap-16 items-center">
        {/* Left — Text */}
        <div>
          {/* Status pill */}
          <div className="animate-fade-up mb-6">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--accent-glow)] border border-purple-500/20">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--green)] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--green)]"></span>
              </span>
              <span className="text-xs font-medium text-[var(--accent-light)]">Open to opportunities</span>
            </div>
          </div>

          {/* Headline */}
          <h1 className="animate-fade-up delay-1 text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.05] mb-6">
            Architecting{" "}
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              products
            </span>
            <br />that actually ship.
          </h1>

          {/* Subtitle */}
          <p className="animate-fade-up delay-2 text-lg text-[var(--text-secondary)] max-w-lg mb-10 leading-relaxed">
            I design and build production SaaS platforms, AI systems, and cloud-native applications.
            10+ years in .NET, Azure, and LLM integrations. Every project here is real code — not portfolio filler.
          </p>

          {/* CTA */}
          <div className="animate-fade-up delay-3 flex flex-wrap gap-3 mb-12">
            <a href="https://github.com/rajibmahata" target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-white text-black font-semibold text-sm hover:bg-gray-200 transition-all shadow-lg shadow-white/5">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              GitHub
            </a>
            <a href="https://linkedin.com/in/rajib-mahata" target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl border border-[var(--border)] text-[var(--text-secondary)] font-medium text-sm hover:border-[var(--text-muted)] hover:text-white transition-all">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
              LinkedIn
            </a>
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-4 gap-4 max-w-md">
            {stats.map(s => (
              <div key={s.label} className="animate-fade-up delay-4" style={{ animationDelay: `${0.4 + stats.indexOf(s) * 0.08}s`, opacity: 0 }}>
                <div className="text-2xl font-bold text-white mb-0.5 tabular-nums">{s.value}</div>
                <div className="text-[11px] text-[var(--text-muted)] leading-tight">{s.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right — Visual element */}
        <div className="hidden lg:block relative">
          <div className="animate-fade-up delay-2 relative">
            {/* Code block aesthetic */}
            <div className="rounded-2xl bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden shadow-2xl shadow-purple-500/5">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-elevated)]">
                <span className="w-3 h-3 rounded-full bg-red-500/60"></span>
                <span className="w-3 h-3 rounded-full bg-amber-500/60"></span>
                <span className="w-3 h-3 rounded-full bg-green-500/60"></span>
                <span className="text-[11px] text-[var(--text-muted)] ml-3 font-mono">rajiblabs.com</span>
              </div>
              <div className="p-5 font-mono text-sm leading-relaxed">
                <div className="mb-3">
                  <span className="text-purple-400">class</span>{' '}
                  <span className="text-blue-300">RajibLabs</span>{' '}
                  <span className="text-[var(--text-muted)]">{'{'}</span>
                </div>
                <div className="ml-4 mb-2">
                  <span className="text-purple-400">stack</span>{' '}
                  <span className="text-[var(--text-muted)]">=</span>{' '}
                  <span className="text-green-400">[".NET", "React", "Azure", "AI"]</span>
                </div>
                <div className="ml-4 mb-2">
                  <span className="text-purple-400">experience</span>{' '}
                  <span className="text-[var(--text-muted)]">=</span>{' '}
                  <span className="text-amber-400">10</span>
                  <span className="text-[var(--text-muted)]">+</span>{' '}
                  <span className="text-[var(--text-secondary)]">years</span>
                </div>
                <div className="ml-4 mb-2">
                  <span className="text-purple-400">focus</span>{' '}
                  <span className="text-[var(--text-muted)]">=</span>{' '}
                  <span className="text-green-400">"SaaS + AI/LLM"</span>
                </div>
                <div className="ml-4">
                  <span className="text-purple-400">status</span>{' '}
                  <span className="text-[var(--text-muted)]">=</span>{' '}
                  <span className="text-green-400">"Building"</span>
                </div>
                <div>
                  <span className="text-[var(--text-muted)]">{'}'}</span>
                </div>
              </div>
            </div>

            {/* Floating accent elements */}
            <div className="absolute -top-6 -right-6 w-24 h-24 bg-gradient-to-br from-purple-500/10 to-transparent rounded-full blur-2xl"></div>
            <div className="absolute -bottom-10 -left-10 w-32 h-32 bg-gradient-to-tr from-blue-500/10 to-transparent rounded-full blur-3xl"></div>
          </div>
        </div>
      </div>
    </section>
  );
}
