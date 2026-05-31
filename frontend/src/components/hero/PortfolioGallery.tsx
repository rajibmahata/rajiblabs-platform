const allProjects = [
  { title: 'DocSignerHub', desc: 'Digital signature SaaS with AI, blockchain, Stripe integration', source: 'GitHub', tech: ['.NET 8', 'React', 'Azure', 'OpenAI'], link: 'https://github.com/rajibmahata/DocumentSigningPlatform', live: 'https://docsignerhub.com' },
  { title: 'AI Avatar RAG Platform', desc: 'Enterprise RAG with avatar-based knowledge retrieval', source: 'GitHub', tech: ['Python', 'FastAPI', 'OpenAI', 'RAG'], link: 'https://github.com/rajibmahata/AI-Avatar-RAG-Platform', live: null },
  { title: 'Solicitor Case Management', desc: 'Legal workflow platform for case tracking', source: 'GitHub', tech: ['.NET 8', 'Blazor', 'SQL Server'], link: 'https://github.com/rajibmahata/SolicitorCaseManagementSystem', live: null },
  { title: 'Rajib Labs', desc: 'This portfolio — premium personal brand platform', source: 'GitHub', tech: ['React', '.NET 8', 'Tailwind', 'OpenClaw'], link: 'https://github.com/rajibmahata/rajiblabs-platform', live: 'https://rajiblabs.com' },
  { title: 'FoodFleet', desc: 'Multi-branch restaurant delivery platform', source: 'GitHub', tech: ['C#', 'ASP.NET', 'SQL Server'], link: 'https://github.com/rajibmahata/FoodFleet', live: null },
  { title: 'BudgetEase', desc: 'Event expense tracking and management', source: 'GitHub', tech: ['C#', 'ASP.NET', 'SQL'], link: 'https://github.com/rajibmahata/BudgetEase', live: null },
  { title: 'AI Resume Portfolio', desc: 'AI-powered resume to portfolio generator', source: 'GitHub', tech: ['Blazor', 'AI', 'C#'], link: 'https://github.com/rajibmahata/AI-Resume-Portfolio', live: null },
  { title: 'AI Blog Portfolio', desc: 'AI-assisted blogging platform', source: 'GitHub', tech: ['C#', 'AI', 'ASP.NET'], link: 'https://github.com/rajibmahata/AI-Powered-Blog-Portfolio', live: null },
];

const sourceColors: Record<string, string> = {
  GitHub: 'bg-slate-400/10 text-slate-400 border-slate-400/20',
  LinkedIn: 'bg-blue-400/10 text-blue-400 border-blue-400/20',
  Resume: 'bg-purple-400/10 text-purple-400 border-purple-400/20',
};

export default function PortfolioGallery() {
  return (
    <section className="max-w-7xl mx-auto px-6 pb-24">
      <div className="section-tag">Portfolio</div>
      <h2 className="text-3xl md:text-4xl font-bold text-white mb-10">All Projects</h2>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {allProjects.map((p, i) => (
          <a key={p.title} href={p.live || p.link} target="_blank" rel="noopener noreferrer"
            className="card p-5 group animate-fade-up" style={{ animationDelay: `${i*0.05}s`, opacity:0 }}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white group-hover:text-indigo-300 transition-colors">{p.title}</h3>
              <span className={`text-[9px] px-2 py-0.5 rounded-full border ${sourceColors[p.source] || sourceColors.GitHub}`}>{p.source}</span>
            </div>
            <p className="text-xs text-[var(--text-muted)] mb-3 line-clamp-2">{p.desc}</p>
            <div className="flex flex-wrap gap-1">
              {p.tech.slice(0, 4).map(t => <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.03] border border-[var(--border)] text-[var(--text-muted)]">{t}</span>)}
            </div>
          </a>
        ))}
      </div>
    </section>
  );
}
