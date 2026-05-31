import { useState, useEffect } from 'react';
import { Link, Outlet } from 'react-router-dom';

export default function Layout() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const links = [
    { label: 'Projects', id: 'projects' },
    { label: 'Resume', id: 'resume' },
    { label: 'Contact', id: 'contact' },
  ];

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
    setMenuOpen(false);
  };

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] relative">
      <nav className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
        scrolled ? 'bg-[#050508]/90 backdrop-blur-xl border-b border-[var(--border)]' : ''
      }`}>
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          <Link to="/" className="text-sm sm:text-[15px] font-semibold tracking-tight">
            <span className="text-white">Rajib</span>
            <span className="text-[var(--text-muted)]"> Mahata</span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden sm:flex items-center gap-6">
            {links.map(l => (
              <button key={l.id} onClick={() => scrollTo(l.id)}
                className="text-sm text-[var(--text-secondary)] hover:text-white transition-colors">
                {l.label}
              </button>
            ))}
            <a href="https://github.com/rajibmahata" target="_blank" rel="noopener noreferrer"
              className="text-sm font-medium text-white hover:text-[var(--accent-light)] transition-colors">
              GitHub ↗
            </a>
          </div>

          {/* Mobile menu button */}
          <button onClick={() => setMenuOpen(!menuOpen)} className="sm:hidden p-2 -mr-2 text-[var(--text-secondary)]">
            {menuOpen ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/></svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16"/></svg>
            )}
          </button>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="sm:hidden border-t border-[var(--border)] bg-[#050508]/95 backdrop-blur-xl px-4 py-3 space-y-1">
            {links.map(l => (
              <button key={l.id} onClick={() => scrollTo(l.id)}
                className="block w-full text-left px-3 py-2.5 rounded-lg text-sm text-[var(--text-secondary)] hover:text-white hover:bg-white/[0.03]">
                {l.label}
              </button>
            ))}
            <a href="https://github.com/rajibmahata" target="_blank" rel="noopener noreferrer"
              className="block px-3 py-2.5 rounded-lg text-sm font-medium text-white hover:bg-white/[0.03]">
              GitHub ↗
            </a>
          </div>
        )}
      </nav>

      <main className="relative z-10">
        <Outlet />
      </main>

      <footer className="relative z-10 border-t border-[var(--border)] py-6 sm:py-8 text-center">
        <p className="text-xs text-[var(--text-muted)] px-4">© {new Date().getFullYear()} Rajib Mahata. Senior Software Architect. Built with React + .NET 8.</p>
      </footer>
    </div>
  );
}
