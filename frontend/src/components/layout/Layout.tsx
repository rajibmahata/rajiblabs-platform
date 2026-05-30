import { useState, useEffect } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';

export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Home' },
    { path: '/projects', label: 'Projects' },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold tracking-tight">
            <span className="text-blue-400">Rajib</span>
            <span className="text-gray-300">Labs</span>
          </Link>

          <nav className="hidden md:flex gap-8">
            {navItems.map(item => (
              <Link
                key={item.path}
                to={item.path}
                className={`text-sm font-medium transition-colors ${
                  isActive(item.path)
                    ? 'text-blue-400'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <button
            className="md:hidden text-gray-400"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? '✕' : '☰'}
          </button>
        </div>

        {mobileOpen && (
          <div className="md:hidden border-t border-gray-800 bg-gray-900 px-4 py-3">
            {navItems.map(item => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileOpen(false)}
                className={`block py-2 text-sm ${
                  isActive(item.path) ? 'text-blue-400' : 'text-gray-400'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>
        )}
      </header>

      <main className="max-w-6xl mx-auto px-4 py-12">
        <Outlet />
      </main>

      <footer className="border-t border-gray-800 text-center py-8 text-sm text-gray-500">
        © {new Date().getFullYear()} Rajib Labs — Built with AI. Managed by agents.
      </footer>
    </div>
  );
}
