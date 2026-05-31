const activeProjects = [
  { name: 'DocSignerHub', desc: 'Digital signature SaaS platform with AI clause analysis and blockchain notarisation.', status: 'Active', progress: 85, updated: '3h ago', tech: ['.NET 8', 'React', 'Azure', 'OpenAI'], live: 'https://docsignerhub.com' },
  { name: 'AI Avatar RAG Platform', desc: 'Enterprise AI knowledge retrieval with avatar interaction and semantic search.', status: 'Active', progress: 60, updated: '2d ago', tech: ['Python', 'FastAPI', 'RAG', 'Vector DB'], live: null },
  { name: 'Rajib Labs', desc: 'This portfolio — premium personal brand platform managed by AI agents.', status: 'Active', progress: 90, updated: '10m ago', tech: ['React', 'TypeScript', '.NET', 'Tailwind'], live: 'https://rajiblabs.com' },
];

export default function CurrentProjects() {
  return (
    <section id="projects" className="max-w-7xl mx-auto px-6 pb-24">
      <div className="section-tag">Current Work</div>
      <h2 className="text-3xl md:text-4xl font-bold text-white mb-10">Active Projects</h2>
      <div className="grid md:grid-cols-3 gap-5">
        {activeProjects.map((p, i) => (
          <div key={p.name} className="card p-6 animate-fade-up" style={{ animationDelay: `${i*0.1}s`, opacity:0 }}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">{p.name}</h3>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-400/10 text-emerald-400 border border-emerald-400/20">{p.status}</span>
            </div>
            <p className="text-sm text-[var(--text-secondary)] mb-4 leading-relaxed">{p.desc}</p>
            <div className="mb-4">
              <div className="flex justify-between text-[11px] mb-1.5"><span className="text-[var(--text-muted)]">Progress</span><span className="text-white font-medium">{p.progress}%</span></div>
              <div className="h-1 bg-[var(--border)] rounded-full overflow-hidden"><div className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all" style={{width:`${p.progress}%`}}></div></div>
            </div>
            <div className="flex flex-wrap gap-1.5 mb-4">
              {p.tech.map(t => <span key={t} className="text-[10px] px-2 py-1 rounded-md bg-white/[0.03] border border-[var(--border)] text-[var(--text-muted)]">{t}</span>)}
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-[var(--text-muted)]">Updated {p.updated}</span>
              {p.live && <a href={p.live} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-indigo-300">Visit →</a>}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
