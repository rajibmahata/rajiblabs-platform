import { useState, useEffect } from 'react';
import { Link, Outlet } from 'react-router-dom';

export default function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const links = [
    { to: '/#work', label: 'Work' },
    { to: '/#workforce', label: 'AI Agents' },
    { to: '/#projects', label: 'Projects' },
    { to: '/#activity', label: 'Activity' },
  ];

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] relative">
      <nav className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
        scrolled ? 'bg-[var(--bg)]/90 backdrop-blur-xl border-b border-[var(--border)]' : 'bg-transparent'
      }`}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-indigo-500/20">
              R
            </div>
            <span className="text-[15px] font-semibold tracking-tight">
              rajib<span className="text-[var(--text-muted)]">labs</span>
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-1">
            {links.map(l => (
              <button key={l.to} onClick={() => scrollTo(l.to.replace('/#', ''))}
                className="px-4 py-2 rounded-lg text-sm font-medium text-[var(--text-secondary)] hover:text-white hover:bg-white/[0.03] transition-all"
              >{l.label}</button>
            ))}
            <a href="https://github.com/rajibmahata" target="_blank" rel="noopener noreferrer"
              className="ml-4 px-4 py-2 rounded-lg text-sm font-medium bg-white text-black hover:bg-gray-200 transition-all">
              GitHub
            </a>
          </div>

          <button className="md:hidden p-2 text-[var(--text-secondary)]" onClick={() => setMenuOpen(!menuOpen)}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {menuOpen
                ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/>
                : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16"/>}
            </svg>
          </button>
        </div>
        {menuOpen && (
          <div className="md:hidden border-t border-[var(--border)] px-6 py-4 space-y-2 bg-[var(--bg)]/95 backdrop-blur-xl">
            {links.map(l => (
              <button key={l.to} onClick={() => { scrollTo(l.to.replace('/#', '')); setMenuOpen(false); }}
                className="block w-full text-left px-3 py-2 rounded-lg text-sm text-[var(--text-secondary)] hover:text-white"
              >{l.label}</button>
            ))}
          </div>
        )}
      </nav>

      <main className="relative z-10">
        <Outlet />
      </main>

      <footer className="relative z-10 border-t border-[var(--border)] py-8 text-center text-xs text-[var(--text-muted)]">
        © {new Date().getFullYear()} Rajib Labs — AI-powered innovation platform. Built with React + .NET 8. Managed by autonomous AI agents.
      </footer>
    </div>
  );
}
