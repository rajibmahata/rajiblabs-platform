import { useState, useEffect, useRef } from 'react';

const navLinks = [
  { label: 'About',    href: '#about' },
  { label: 'WIP',      href: '#wip' },
  { label: 'Projects', href: '#projects' },
  { label: 'Services', href: '#services' },
  { label: 'GitHub',   href: '#github' },
  { label: 'Contact',  href: '#contact' },
];

export default function GlobalNav() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('');
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60);
    window.addEventListener('scroll', onScroll, { passive: true });

    // Intersection Observer for active section
    observerRef.current = new IntersectionObserver(
      entries => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        }
      },
      { rootMargin: '-20% 0px -70% 0px', threshold: 0 }
    );

    const sectionIds = navLinks.map(l => l.href.replace('#', ''));
    for (const id of sectionIds) {
      const el = document.getElementById(id);
      if (el) observerRef.current.observe(el);
    }

    return () => {
      window.removeEventListener('scroll', onScroll);
      observerRef.current?.disconnect();
    };
  }, []);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
    setMenuOpen(false);
  };

  return (
    <header
      className="fixed top-0 inset-x-0 z-50 transition-all duration-300"
      style={{
        height: '64px',
        background: scrolled ? 'var(--c-bg-secondary)' : 'transparent',
        backdropFilter: scrolled ? 'blur(16px) saturate(1.8)' : 'none',
        WebkitBackdropFilter: scrolled ? 'blur(16px) saturate(1.8)' : 'none',
        borderBottom: scrolled ? '1px solid var(--c-border)' : '1px solid transparent',
      }}
    >
      <nav
        className="container-site h-full flex items-center justify-between"
        aria-label="Main navigation"
      >
        {/* Logo / Wordmark */}
        <a
          href="#"
          onClick={e => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
          className="flex items-baseline gap-0.5 no-underline"
        >
          <span style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--c-text-primary)' }}>
            Rajib
          </span>
          <span style={{ fontFamily: 'var(--font-heading)', fontSize: 16, fontWeight: 400, color: 'var(--c-accent-gold)' }}>
            Labs
          </span>
        </a>

        {/* Desktop nav links */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map(link => (
            <button
              key={link.href}
              onClick={() => scrollTo(link.href.replace('#', ''))}
              className="relative pb-1 transition-colors"
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: 14,
                fontWeight: 500,
                color: activeSection === link.href.replace('#', '') ? 'var(--c-text-primary)' : 'var(--c-text-secondary)',
              }}
              onMouseEnter={e => { e.currentTarget.style.color = 'var(--c-text-primary)'; }}
              onMouseLeave={e => {
                if (activeSection !== link.href.replace('#', '')) {
                  e.currentTarget.style.color = 'var(--c-text-secondary)';
                }
              }}
              aria-current={activeSection === link.href.replace('#', '') ? 'page' : undefined}
            >
              {link.label}
              {activeSection === link.href.replace('#', '') && (
                <span
                  className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full"
                  style={{ backgroundColor: 'var(--c-accent-gold)' }}
                />
              )}
            </button>
          ))}
        </div>

        {/* CTA Button */}
        <button
          onClick={() => scrollTo('contact')}
          className="hidden md:inline-flex items-center px-4 py-2 text-sm font-medium rounded-md transition-all duration-200"
          style={{
            fontFamily: 'var(--font-heading)',
            fontSize: 13,
            fontWeight: 500,
            border: '1px solid var(--c-accent-blue)',
            color: 'var(--c-accent-blue)',
            borderRadius: 'var(--radius-md)',
            background: 'transparent',
            cursor: 'pointer',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.backgroundColor = 'var(--c-accent-blue)';
            e.currentTarget.style.color = '#fff';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.backgroundColor = 'transparent';
            e.currentTarget.style.color = 'var(--c-accent-blue)';
          }}
        >
          Get in Touch
        </button>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="md:hidden p-2 -mr-2"
          style={{ color: 'var(--c-text-secondary)', minWidth: 44, minHeight: 44 }}
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={menuOpen}
        >
          {menuOpen ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          )}
        </button>
      </nav>

      {/* Mobile full-screen overlay */}
      {menuOpen && (
        <div
          className="md:hidden fixed inset-0 z-[60] flex flex-col items-center justify-center gap-6"
          style={{
            background: 'rgba(8, 13, 26, 0.97)',
            backdropFilter: 'blur(20px)',
          }}
        >
          {navLinks.map(link => (
            <button
              key={link.href}
              onClick={() => scrollTo(link.href.replace('#', ''))}
              className="text-xl transition-colors"
              style={{
                fontFamily: 'var(--font-heading)',
                color: activeSection === link.href.replace('#', '') ? 'var(--c-text-primary)' : 'var(--c-text-secondary)',
              }}
            >
              {link.label}
            </button>
          ))}
          <button
            onClick={() => scrollTo('contact')}
            className="mt-4 px-8 py-3 text-base font-medium rounded-md transition-all"
            style={{
              fontFamily: 'var(--font-heading)',
              border: '1px solid var(--c-accent-blue)',
              color: 'var(--c-accent-blue)',
              borderRadius: 'var(--radius-md)',
              background: 'transparent',
            }}
          >
            Get in Touch
          </button>
        </div>
      )}
    </header>
  );
}
