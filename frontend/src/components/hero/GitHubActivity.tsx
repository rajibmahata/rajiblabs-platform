const repos = [
  { name: 'rajiblabs-platform', desc: 'This platform — AI-powered portfolio & lab', lang: 'TypeScript', updated: '10m ago', stars: 1 },
  { name: 'DocumentSigningPlatform', desc: 'Digital signature SaaS — DocSignerHub', lang: 'C#', updated: '3h ago', stars: 3 },
  { name: 'AI-Avatar-RAG-Platform', desc: 'Enterprise RAG with avatar interaction', lang: 'Python', updated: '2d ago', stars: 2 },
  { name: 'SolicitorCaseManagementSystem', desc: 'Legal workflow & case tracking', lang: 'C#', updated: '1w ago', stars: 1 },
  { name: 'FoodFleet', desc: 'Multi-branch restaurant delivery platform', lang: 'C#', updated: '1mo ago', stars: 0 },
  { name: 'BudgetEase', desc: 'Modern event expense tracking & management', lang: 'C#', updated: '3mo ago', stars: 0 },
];

export default function GitHubActivity() {
  return (
    <section id="github" className="max-w-7xl mx-auto px-6 pb-24">
      <div className="text-center mb-14">
        <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--text-muted)] mb-4">GitHub Activity</h2>
        <p className="text-3xl md:text-4xl font-bold text-white mb-4">
          Live engineering feed
        </p>
        <p className="text-[var(--text-secondary)] max-w-xl mx-auto">
          Recent activity across all repositories. Real commits, real code, real products.
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {repos.map((r, i) => (
          <a key={r.name} href={`https://github.com/rajibmahata/${r.name}`} target="_blank" rel="noopener noreferrer"
            className="glass-card p-5 animate-fade-up group" style={{ animationDelay: `${i * 0.06}s`, opacity: 0 }}>
            <div className="flex items-center gap-2 mb-2">
              <svg className="w-4 h-4 text-[var(--text-muted)]" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              <h3 className="text-sm font-semibold text-white group-hover:text-indigo-300 transition-colors">{r.name}</h3>
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-400/10 text-amber-400 border border-amber-400/20 ml-auto">
                {r.stars > 0 ? `★ ${r.stars}` : 'New'}
              </span>
            </div>
            <p className="text-xs text-[var(--text-muted)] mb-3">{r.desc}</p>
            <div className="flex items-center gap-3 text-[11px]">
              <span className="flex items-center gap-1">
                <span className={`w-2 h-2 rounded-full ${r.lang === 'C#' ? 'bg-green-400' : r.lang === 'TypeScript' ? 'bg-blue-400' : 'bg-amber-400'}`}></span>
                {r.lang}
              </span>
              <span className="text-[var(--text-muted)]">{r.updated}</span>
            </div>
          </a>
        ))}
      </div>
    </section>
  );
}
