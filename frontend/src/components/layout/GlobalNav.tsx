import { useState, useEffect, useRef } from 'react';
import { siteConfig } from '../../config/site';

const navLinks = [
  { label: 'Apps',     href: '#applications' },
  { label: 'About',    href: '#about' },
  { label: 'Projects', href: '#projects' },
  { label: 'Services', href: '#services' },
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
        {/* Logo / Wordmark — PestFlow-style with icon */}
        <a
          href="#"
          onClick={e => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
          className="flex items-center gap-3 no-underline"
        >
          <span className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'linear-gradient(135deg, #1547BE, #0A7B6C)', border: '1px solid rgba(255,255,255,0.08)', boxShadow: '0 2px 12px rgba(21,71,190,0.25)' }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 700, color: '#fff' }}>R</span>
          </span>
          <span className="flex items-baseline gap-0.5">
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 19, fontWeight: 700, color: 'var(--c-text-primary)', letterSpacing: '-0.02em' }}>
              Rajib
            </span>
            <span style={{ fontFamily: 'var(--font-heading)', fontSize: 15, fontWeight: 400, color: 'var(--c-accent-gold)' }}>
              Labs
            </span>
            <span className="hidden sm:inline-flex ml-2 px-1.5 py-0.5 rounded text-[10px] font-semibold tracking-widest" style={{ background: 'rgba(37,211,102,0.12)', color: '#25D366', border: '1px solid rgba(37,211,102,0.2)', fontFamily: 'var(--font-mono)' }}>PWA</span>
          </span>
        </a>

        {/* Desktop nav links — PestFlow clean spacing */}
        <div className="hidden lg:flex items-center gap-7">
          {navLinks.map(link => (
            <button
              key={link.href}
              onClick={() => scrollTo(link.href.replace('#', ''))}
              className="relative pb-1 transition-colors"
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: 13.5,
                fontWeight: 500,
                color: activeSection === link.href.replace('#', '') ? 'var(--c-text-primary)' : 'var(--c-text-secondary)',
                letterSpacing: '0.01em',
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
                  style={{ backgroundColor: 'var(--c-accent-blue)' }}
                />
              )}
            </button>
          ))}
        </div>

        {/* Right actions — WhatsApp, Call, Hire (PestFlow top CTA pattern) */}
        <div className="hidden md:flex items-center gap-2">
          <a
            href={siteConfig.whatsappLink}
            target="_blank"
            rel="noopener noreferrer"
            className="w-9 h-9 rounded-full flex items-center justify-center transition-all"
            style={{ background: 'rgba(37,211,102,0.12)', border: '1px solid rgba(37,211,102,0.25)', color: '#25D366' }}
            onMouseEnter={e => { e.currentTarget.style.background = '#25D366'; e.currentTarget.style.color = '#fff'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'rgba(37,211,102,0.12)'; e.currentTarget.style.color = '#25D366'; }}
            aria-label="Chat on WhatsApp"
            title="Chat on WhatsApp"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M19.05 4.94A9.91 9.91 0 0 0 12.04 2C6.58 2 2.14 6.45 2.14 11.9c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38a9.87 9.87 0 0 0 4.79 1.22h.01c5.46 0 9.9-4.45 9.9-9.9 0-2.64-1.03-5.13-2.9-7zM12.04 19.8h-.01a8.13 8.13 0 0 1-4.15-1.14l-.3-.18-3.12.82.83-3.04-.2-.31a8.18 8.18 0 0 1-1.26-4.05c0-4.5 3.66-8.16 8.17-8.16 2.18 0 4.23.85 5.77 2.4a8.1 8.1 0 0 1 2.39 5.76c0 4.5-3.66 8.17-8.15 8.17zm6.7-5.99c-.37-.18-2.17-1.07-2.5-1.19-.34-.12-.58-.18-.82.18-.24.37-.94 1.19-1.16 1.44-.21.24-.42.27-.79.09-.37-.18-1.55-.57-2.96-1.82-1.09-.97-1.83-2.17-2.05-2.54-.21-.37-.02-.57.16-.75.16-.16.37-.42.55-.63.18-.21.24-.37.37-.61.12-.24.06-.46-.03-.64-.09-.18-.82-1.98-1.12-2.71-.29-.7-.59-.61-.82-.62l-.7-.01c-.24 0-.64.09-.97.46-.34.37-1.28 1.25-1.28 3.05s1.31 3.54 1.49 3.78c.18.24 2.58 3.94 6.25 5.53.87.38 1.55.6 2.08.77.87.28 1.67.24 2.3.15.7-.1 2.17-.89 2.47-1.75.31-.86.31-1.59.21-1.75-.09-.15-.34-.24-.7-.42z" /></svg>
          </a>
          <a
            href={siteConfig.callLink}
            className="w-9 h-9 rounded-full flex items-center justify-center transition-all"
            style={{ background: 'rgba(21,71,190,0.10)', border: '1px solid rgba(21,71,190,0.20)', color: 'var(--c-accent-blue-l)' }}
            onMouseEnter={e => { e.currentTarget.style.background = 'var(--c-accent-blue)'; e.currentTarget.style.color = '#fff'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'rgba(21,71,190,0.10)'; e.currentTarget.style.color = 'var(--c-accent-blue-l)'; }}
            aria-label="Call Rajib"
            title="Call Rajib"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" /></svg>
          </a>
          <a
            href="#contact"
            onClick={e => { e.preventDefault(); scrollTo('contact'); }}
            className="ml-1 inline-flex items-center gap-2 px-5 py-2 text-sm font-semibold rounded-full transition-all duration-200"
            style={{
              fontFamily: 'var(--font-heading)',
              fontSize: 13,
              fontWeight: 600,
              backgroundColor: 'var(--c-accent-blue)',
              color: '#fff',
              borderRadius: '999px',
              textDecoration: 'none',
              boxShadow: '0 2px 12px rgba(21,71,190,0.25)',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.backgroundColor = 'var(--c-accent-blue-l)';
              e.currentTarget.style.boxShadow = 'var(--shadow-glow-blue)';
              e.currentTarget.style.transform = 'translateY(-1px)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.backgroundColor = 'var(--c-accent-blue)';
              e.currentTarget.style.boxShadow = '0 2px 12px rgba(21,71,190,0.25)';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            Hire Me <span aria-hidden="true">→</span>
          </a>
        </div>

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

      {/* Mobile full-screen overlay — PestFlow style with contact CTAs */}
      {menuOpen && (
        <div
          className="md:hidden fixed inset-0 z-[60] flex flex-col items-center justify-center gap-5 p-6"
          style={{
            background: 'rgba(8, 13, 26, 0.98)',
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
          <div className="flex gap-3 mt-2">
            <a
              href={siteConfig.whatsappLink}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setMenuOpen(false)}
              className="flex items-center gap-2 px-5 py-3 rounded-full text-sm font-semibold"
              style={{ background: '#25D366', color: '#fff', fontFamily: 'var(--font-heading)', textDecoration: 'none' }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M19.05 4.94A9.91 9.91 0 0 0 12.04 2C6.58 2 2.14 6.45 2.14 11.9c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38a9.87 9.87 0 0 0 4.79 1.22h.01c5.46 0 9.9-4.45 9.9-9.9 0-2.64-1.03-5.13-2.9-7zM12.04 19.8h-.01a8.13 8.13 0 0 1-4.15-1.14l-.3-.18-3.12.82.83-3.04-.2-.31a8.18 8.18 0 0 1-1.26-4.05c0-4.5 3.66-8.16 8.17-8.16 2.18 0 4.23.85 5.77 2.4a8.1 8.1 0 0 1 2.39 5.76c0 4.5-3.66 8.17-8.15 8.17z" /></svg>
              WhatsApp
            </a>
            <a
              href={siteConfig.callLink}
              onClick={() => setMenuOpen(false)}
              className="flex items-center gap-2 px-5 py-3 rounded-full text-sm font-semibold"
              style={{ background: 'var(--c-accent-blue)', color: '#fff', fontFamily: 'var(--font-heading)', textDecoration: 'none' }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" /></svg>
              Call
            </a>
          </div>
          <button
            onClick={() => scrollTo('contact')}
            className="mt-1 px-8 py-3 text-base font-medium rounded-full transition-all"
            style={{
              fontFamily: 'var(--font-heading)',
              background: 'var(--c-accent-blue)',
              color: '#fff',
              borderRadius: '999px',
            }}
          >
            Hire Me →
          </button>
        </div>
      )}
    </header>
  );
}
