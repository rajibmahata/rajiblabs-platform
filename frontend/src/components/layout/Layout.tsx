import { useState, useEffect } from 'react';
import { Link, Outlet } from 'react-router-dom';

export default function Layout() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const nav = [
    { label: 'Projects', href: '#projects' },
    { label: 'Resume', href: '#resume' },
    { label: 'Contact', href: '#contact' },
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
          <Link to="/" className="text-[15px] font-semibold tracking-tight">
            <span className="text-white">Rajib</span>
            <span className="text-[var(--text-muted)]"> Mahata</span>
          </Link>
          <div className="flex items-center gap-6">
            {nav.map(item => (
              <button key={item.label} onClick={() => scrollTo(item.href.replace('#', ''))}
                className="text-sm text-[var(--text-secondary)] hover:text-white transition-colors">
                {item.label}
              </button>
            ))}
            <a href="https://github.com/rajibmahata" target="_blank" rel="noopener noreferrer"
              className="text-sm font-medium text-white hover:text-[var(--accent-light)] transition-colors">
              GitHub →
            </a>
          </div>
        </div>
      </nav>

      <main className="relative z-10">
        <Outlet />
      </main>

      <footer className="relative z-10 border-t border-[var(--border)] py-8 text-center text-xs text-[var(--text-muted)]">
        © {new Date().getFullYear()} Rajib Mahata. Built with care.
      </footer>
    </div>
  );
}
