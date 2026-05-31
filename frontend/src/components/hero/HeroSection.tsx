import { useState, useEffect } from 'react';

const highlights = [
  'DocSignerHub — Digital Signature SaaS',
  'AI Avatar RAG Platform',
  'Solicitor Case Management System',
  'AI Resume Portfolio',
  'Autonomous AI Workforce',
];

const stats = [
  { value: '10+', label: 'Years experience' },
  { value: '15+', label: 'Projects delivered' },
  { value: '7', label: 'AI agents running' },
  { value: '4K+', label: 'GitHub contributions' },
];

export default function HeroSection() {
  const [idx, setIdx] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const t = setInterval(() => {
      setVisible(false);
      setTimeout(() => { setIdx((idx + 1) % highlights.length); setVisible(true); }, 300);
    }, 3000);
    return () => clearInterval(t);
  }, [idx]);

  return (
    <section className="pt-24 pb-20 md:pt-36 md:pb-28 max-w-7xl mx-auto px-6">
      <div className="grid lg:grid-cols-2 gap-16 items-center">
        <div>
          <div className="animate-fade-up mb-6">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--accent-glow)] border border-purple-500/20">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--green)] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--green)]"></span>
              </span>
              <span className="text-xs font-medium text-[var(--accent-light)]">AI workforce active — 7 agents running</span>
            </div>
          </div>

          <h1 className="animate-fade-up delay-1 text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.05] mb-6">
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              Rajib Labs
            </span>
            <br />
            <span className="text-white text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-semibold">
              Building intelligent software, AI systems, and automation platforms.
            </span>
          </h1>

          {/* Rotating highlight */}
          <div className="animate-fade-up delay-2 mb-10 h-8">
            <p className={`text-lg text-[var(--accent-light)] font-medium transition-all duration-300 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'}`}>
              ▸ {highlights[idx]}
            </p>
          </div>

          <div className="animate-fade-up delay-3 flex flex-wrap gap-3 mb-14">
            <a href="#work" onClick={e => { e.preventDefault(); document.getElementById('work')?.scrollIntoView({ behavior:'smooth' }); }}
              className="px-5 py-3 rounded-xl bg-white text-black font-semibold text-sm hover:bg-gray-200 transition-all shadow-lg shadow-white/5">
              Explore Projects
            </a>
            <a href="#activity" onClick={e => { e.preventDefault(); document.getElementById('activity')?.scrollIntoView({ behavior:'smooth' }); }}
              className="px-5 py-3 rounded-xl border border-[var(--border)] text-[var(--text-secondary)] font-medium text-sm hover:border-[var(--text-muted)] hover:text-white transition-all">
              Current Work
            </a>
            <a href="https://linkedin.com/in/rajib-mahata" target="_blank" rel="noopener noreferrer"
              className="px-5 py-3 rounded-xl border border-[var(--border)] text-[var(--text-secondary)] font-medium text-sm hover:border-[var(--text-muted)] hover:text-white transition-all">
              View Resume
            </a>
          </div>

          <div className="grid grid-cols-4 gap-4 max-w-md">
            {stats.map((s, i) => (
              <div key={s.label} className="animate-fade-up delay-4" style={{ animationDelay: `${0.4 + i * 0.08}s`, opacity: 0 }}>
                <div className="text-2xl font-bold text-white mb-0.5 tabular-nums">{s.value}</div>
                <div className="text-[11px] text-[var(--text-muted)] leading-tight">{s.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Code block visual */}
        <div className="hidden lg:block relative">
          <div className="animate-fade-up delay-2 relative">
            <div className="rounded-2xl bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden shadow-2xl shadow-purple-500/5">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-elevated)]">
                <span className="w-3 h-3 rounded-full bg-red-500/60"></span>
                <span className="w-3 h-3 rounded-full bg-amber-500/60"></span>
                <span className="w-3 h-3 rounded-full bg-green-500/60"></span>
                <span className="text-[11px] text-[var(--text-muted)] ml-3 font-mono">rajiblabs.com</span>
              </div>
              <div className="p-5 font-mono text-sm leading-relaxed">
                <div className="mb-3"><span className="text-purple-400">class</span> <span className="text-blue-300">RajibLabs</span> <span className="text-[var(--text-muted)]">{'{'}</span></div>
                <div className="ml-4 mb-2"><span className="text-purple-400">stack</span> <span className="text-[var(--text-muted)]">=</span> <span className="text-green-400">[".NET", "React", "Azure", "AI"]</span></div>
                <div className="ml-4 mb-2"><span className="text-purple-400">experience</span> <span className="text-[var(--text-muted)]">=</span> <span className="text-amber-400">10</span><span className="text-[var(--text-muted)]">+</span> <span className="text-[var(--text-secondary)]">years</span></div>
                <div className="ml-4 mb-2"><span className="text-purple-400">focus</span> <span className="text-[var(--text-muted)]">=</span> <span className="text-green-400">"SaaS + AI/LLM + Automation"</span></div>
                <div className="ml-4 mb-2"><span className="text-purple-400">workforce</span> <span className="text-[var(--text-muted)]">=</span> <span className="text-amber-400">7</span> <span className="text-[var(--text-secondary)]">AI agents</span></div>
                <div className="ml-4"><span className="text-purple-400">status</span> <span className="text-[var(--text-muted)]">=</span> <span className="text-green-400">"Building the future"</span></div>
                <div><span className="text-[var(--text-muted)]">{'}'}</span></div>
              </div>
            </div>
            <div className="absolute -top-6 -right-6 w-24 h-24 bg-gradient-to-br from-purple-500/10 to-transparent rounded-full blur-2xl"></div>
            <div className="absolute -bottom-10 -left-10 w-32 h-32 bg-gradient-to-tr from-blue-500/10 to-transparent rounded-full blur-3xl"></div>
          </div>
        </div>
      </div>
    </section>
  );
}
