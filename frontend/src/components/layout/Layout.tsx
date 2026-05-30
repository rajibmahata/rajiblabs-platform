import { useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';

export default function Layout() {
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  const links = [
    { to: '/', label: 'Home' },
    { to: '/projects', label: 'Projects' },
  ];

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] relative">
      {/* Nav */}
      <nav className="fixed top-0 inset-x-0 z-50 bg-[var(--bg)]/80 backdrop-blur-xl border-b border-[var(--border)]">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-[var(--accent)] flex items-center justify-center text-white font-bold text-sm">
              R
            </div>
            <span className="font-semibold text-[15px] tracking-tight">
              <span className="text-white">rajib</span>
              <span className="text-[var(--text-muted)]">labs</span>
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-6">
            {links.map(l => (
              <Link
                key={l.to}
                to={l.to}
                className={`text-sm transition-colors ${
                  location.pathname === l.to
                    ? 'text-white font-medium'
                    : 'text-[var(--text-secondary)] hover:text-white'
                }`}
              >
                {l.label}
              </Link>
            ))}
            <a
              href="https://github.com/rajibmahata"
              target="_blank"
              rel="noopener noreferrer"
              className="ml-4 px-4 py-2 rounded-lg text-sm font-medium bg-white text-black hover:bg-gray-200 transition-colors"
            >
              GitHub
            </a>
          </div>

          <button className="md:hidden p-2" onClick={() => setMenuOpen(!menuOpen)}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {menuOpen
                ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/>
                : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16"/>}
            </svg>
          </button>
        </div>
        {menuOpen && (
          <div className="md:hidden border-t border-[var(--border)] px-6 py-4 space-y-3">
            {links.map(l => (
              <Link key={l.to} to={l.to} onClick={() => setMenuOpen(false)}
                className={`block text-sm ${location.pathname === l.to ? 'text-white font-medium' : 'text-[var(--text-secondary)]'}`}>
                {l.label}
              </Link>
            ))}
            <a href="https://github.com/rajibmahata" target="_blank" rel="noopener noreferrer"
              className="block text-sm text-[var(--text-secondary)] hover:text-white">GitHub →</a>
          </div>
        )}
      </nav>

      <main className="pt-16 relative z-10">
        <Outlet />
      </main>

      <footer className="border-t border-[var(--border)] py-10 text-center text-sm text-[var(--text-muted)]">
        <p>© {new Date().getFullYear()} Rajib Labs. Built with React + .NET 8. Managed by AI agents.</p>
      </footer>
    </div>
  );
}
