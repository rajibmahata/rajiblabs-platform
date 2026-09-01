import { useState, useEffect, useRef } from 'react';
import { siteConfig } from '../../config/site';

const navLinks = [
  { label: 'Overview',     href: '#hero' },
  { label: 'Architecture', href: '#applications' },
  { label: 'AI',           href: '#ai' },
  { label: 'Experience',   href: '#about' },
  { label: 'RajibLabs',    href: '#projects' },
];

export default function GlobalNav() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('');
  const [hidden, setHidden] = useState(false);
  const lastScroll = useRef(0);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const headerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const onScroll = () => {
      const current = window.pageYOffset;
      if (current <= 0) {
        setHidden(false);
      } else if (current > lastScroll.current && current > 100) {
        setHidden(true);
      } else {
        setHidden(false);
      }
      lastScroll.current = current;
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      entries => {
        for (const entry of entries) {
          if (entry.isIntersecting) setActiveSection(entry.target.id);
        }
      },
      { rootMargin: '-20% 0px -70% 0px', threshold: 0 }
    );
    // Watch all relevant sections for active state
    ['hero', 'applications', 'about', 'projects', 'services', 'contact', 'wip', 'github', 'results', 'ai'].forEach(id => {
      const el = document.getElementById(id);
      if (el) observerRef.current?.observe(el);
    });
    return () => observerRef.current?.disconnect();
  }, []);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [menuOpen]);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
    setMenuOpen(false);
  };

  return (
    <>
      <header
        ref={headerRef}
        className={`fixed top-0 w-full z-50 bg-surface/90 backdrop-blur-lg border-b border-outline-variant/30 transition-transform duration-300 ease-in-out ${hidden && !menuOpen ? 'nav-hidden' : ''}`}
        style={{ background: 'rgba(14,19,32,0.9)' }}
      >
        <div className="flex justify-between items-center px-6 py-4 max-w-[1200px] mx-auto h-[72px] pt-safe">
          <a
            href="#"
            onClick={e => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
            className="font-section-title text-[20px] font-bold text-on-surface no-underline"
            style={{ fontFamily: 'Fraunces, serif' }}
          >
            Rajib Mahata
          </a>

          <nav className="hidden md:flex items-center gap-8" aria-label="Primary">
            {navLinks.map(link => (
              <a
                key={link.href}
                href={link.href}
                onClick={e => { e.preventDefault(); scrollTo(link.href.replace('#', '')); }}
                className={`font-body-compact text-[13px] transition-colors px-2 py-1 rounded ${activeSection === link.href.replace('#', '') ? 'text-primary font-bold border-b-2 border-primary pb-1' : 'text-on-surface-variant hover:text-primary hover:bg-surface-bright/50'}`}
                aria-current={activeSection === link.href.replace('#', '') ? 'page' : undefined}
              >
                {link.label}
              </a>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-3">
            <a
              href={siteConfig.whatsappLink}
              target="_blank"
              rel="noopener noreferrer"
              className="w-9 h-9 rounded-full hidden lg:flex items-center justify-center transition-all"
              style={{ background: 'rgba(37,211,102,0.12)', border: '1px solid rgba(37,211,102,0.25)', color: '#25D366' }}
              aria-label="WhatsApp"
              title="WhatsApp"
            >
              <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>chat</span>
            </a>
            <a
              href="#contact"
              onClick={e => { e.preventDefault(); scrollTo('contact'); }}
              className="hidden md:inline-flex bg-primary-container text-white px-6 py-2 rounded-full font-body-compact text-[13px] hover:bg-accent-blue-hover transition-colors items-center gap-2"
            >
              Contact
            </a>
          </div>

          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden text-on-surface p-2 active:scale-95 transition-transform"
            style={{ minWidth: 44, minHeight: 44 }}
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={menuOpen}
          >
            <span className="material-symbols-outlined">{menuOpen ? 'close' : 'menu'}</span>
          </button>
        </div>
      </header>

      {/* Mobile Full-Screen Menu — stitch native-style */}
      <div
        id="mobile-menu"
        className={`fixed inset-0 bg-surface/95 backdrop-blur-xl z-[60] flex flex-col pt-safe ${menuOpen ? 'active visible opacity-100' : 'invisible opacity-0'}`}
        style={{ transition: 'opacity 0.3s ease, visibility 0.3s ease' }}
        aria-hidden={!menuOpen}
      >
        <div className="flex justify-between items-center px-6 py-4 h-[72px]">
          <span className="font-section-title text-[20px] font-bold text-on-surface" style={{ fontFamily: 'Fraunces, serif' }}>Rajib Mahata</span>
          <button onClick={() => setMenuOpen(false)} className="text-primary p-2 active:scale-95 transition-transform" aria-label="Close menu">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        <div className="flex flex-col justify-center flex-1 px-6 gap-8">
          {navLinks.map((link, i) => (
            <a
              key={link.href}
              href={link.href}
              onClick={e => { e.preventDefault(); scrollTo(link.href.replace('#', '')); }}
              className={`menu-item font-display-hero-mobile text-[34px] font-bold transition-colors ${activeSection === link.href.replace('#', '') ? 'text-primary' : 'text-on-surface-variant hover:text-primary'}`}
              style={{ fontFamily: 'Fraunces, serif', transitionDelay: `${50 + i * 50}ms`, transform: menuOpen ? 'translateY(0)' : 'translateY(20px)', opacity: menuOpen ? 1 : 0, transition: 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)' }}
            >
              {link.label}
            </a>
          ))}
          <div className="flex gap-3 mt-8 menu-item" style={{ transitionDelay: '300ms', transform: menuOpen ? 'translateY(0)' : 'translateY(20px)', opacity: menuOpen ? 1 : 0 }}>
            <a href={siteConfig.whatsappLink} target="_blank" rel="noopener noreferrer" onClick={() => setMenuOpen(false)} className="flex-1 bg-whatsapp text-white rounded-full py-4 px-8 font-body-large flex items-center justify-center gap-2" style={{ background: '#25D366' }}>
              <span className="material-symbols-outlined">chat</span> WhatsApp
            </a>
            <a href={siteConfig.callLink} onClick={() => setMenuOpen(false)} className="flex-1 bg-surface-inset border border-border-subtle text-on-surface rounded-full py-4 px-8 font-body-large flex items-center justify-center gap-2">
              <span className="material-symbols-outlined">call</span> Call
            </a>
          </div>
          <a href="#contact" onClick={e => { e.preventDefault(); scrollTo('contact'); }} className="menu-item bg-primary-container text-white rounded-full py-4 px-8 w-full font-body-large flex items-center justify-center gap-2" style={{ transitionDelay: '350ms', transform: menuOpen ? 'translateY(0)' : 'translateY(20px)', opacity: menuOpen ? 1 : 0 }}>
            <span className="material-symbols-outlined">mail</span> Contact
          </a>
        </div>
      </div>
    </>
  );
}
