const ecosystem = [
  { category: 'Backend', color: 'from-green-500 to-emerald-500', items: ['.NET 8/10', 'C#', 'ASP.NET Core', 'REST APIs', 'Microservices', 'Entity Framework'] },
  { category: 'Cloud & DevOps', color: 'from-blue-500 to-cyan-500', items: ['Azure', 'Functions', 'Service Bus', 'Cosmos DB', 'Docker', 'CI/CD'] },
  { category: 'AI & Machine Learning', color: 'from-purple-500 to-pink-500', items: ['OpenAI', 'Gemini', 'RAG Systems', 'Vector DB', 'LLM Agents', 'Semantic Search'] },
  { category: 'Frontend', color: 'from-amber-500 to-orange-500', items: ['React', 'TypeScript', 'Blazor', 'Tailwind CSS', 'JavaScript', 'Bootstrap'] },
];

export default function TechEcosystem() {
  return (
    <section id="tech" className="max-w-7xl mx-auto px-6 pb-24">
      <div className="text-center mb-14">
        <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--text-muted)] mb-4">Technology Ecosystem</h2>
        <p className="text-3xl md:text-4xl font-bold text-white mb-4">
          Architecture & technology map
        </p>
        <p className="text-[var(--text-secondary)] max-w-xl mx-auto">
          The full technology landscape powering Rajib Labs — from backend infrastructure to AI systems.
        </p>
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        {ecosystem.map((eco, i) => (
          <div key={eco.category} className="glass-card p-6 animate-fade-up" style={{ animationDelay: `${i * 0.08}s`, opacity: 0 }}>
            <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gradient-to-r ${eco.color} text-white text-xs font-medium mb-5`}>
              {eco.category}
            </div>
            <div className="grid grid-cols-2 gap-2">
              {eco.items.map(item => (
                <div key={item} className="flex items-center gap-2 text-sm">
                  <div className={`w-1.5 h-1.5 rounded-full bg-gradient-to-r ${eco.color}`}></div>
                  <span className="text-[var(--text-secondary)]">{item}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
