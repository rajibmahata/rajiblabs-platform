import { useState, useEffect } from 'react';
import { siteConfig } from '../../config/site';

export default function FloatingContact() {
  const [expanded, setExpanded] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Show after scroll past hero
    const onScroll = () => setVisible(window.scrollY > 400);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <div
      className="hidden md:flex fixed z-40 flex-col items-end gap-3 pointer-events-none"
      style={{ bottom: 20, right: 20 }}
      aria-label="Quick contact"
    >
      {/* Expanded options */}
      <div
        className={`flex flex-col gap-3 transition-all duration-300 pointer-events-auto ${
          expanded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'
        }`}
      >
        {/* WhatsApp */}
        <a
          href={siteConfig.whatsappLink}
          target="_blank"
          rel="noopener noreferrer"
          className="group flex items-center gap-3 pl-4 pr-3 py-3 rounded-full shadow-lg transition-all duration-200 hover:scale-[1.02]"
          style={{
            background: '#25D366',
            color: '#fff',
            boxShadow: '0 8px 32px rgba(37,211,102,0.35), 0 4px 12px rgba(0,0,0,0.3)',
          }}
          aria-label="Chat on WhatsApp"
        >
          <span
            className="hidden sm:inline"
            style={{ fontFamily: 'var(--font-heading)', fontSize: 13, fontWeight: 600 }}
          >
            Chat on WhatsApp
          </span>
          <span
            className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0"
            style={{ background: 'rgba(255,255,255,0.2)' }}
          >
            {/* WhatsApp SVG */}
            <svg width="20" height="20" viewBox="0 0 24 24" fill="white" aria-hidden="true">
              <path d="M19.05 4.94A9.91 9.91 0 0 0 12.04 2C6.58 2 2.14 6.45 2.14 11.9c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38a9.87 9.87 0 0 0 4.79 1.22h.01c5.46 0 9.9-4.45 9.9-9.9 0-2.64-1.03-5.13-2.9-7zM12.04 19.8h-.01a8.13 8.13 0 0 1-4.15-1.14l-.3-.18-3.12.82.83-3.04-.2-.31a8.18 8.18 0 0 1-1.26-4.05c0-4.5 3.66-8.16 8.17-8.16 2.18 0 4.23.85 5.77 2.4a8.1 8.1 0 0 1 2.39 5.76c0 4.5-3.66 8.17-8.15 8.17zm6.7-5.99c-.37-.18-2.17-1.07-2.5-1.19-.34-.12-.58-.18-.82.18-.24.37-.94 1.19-1.16 1.44-.21.24-.42.27-.79.09-.37-.18-1.55-.57-2.96-1.82-1.09-.97-1.83-2.17-2.05-2.54-.21-.37-.02-.57.16-.75.16-.16.37-.42.55-.63.18-.21.24-.37.37-.61.12-.24.06-.46-.03-.64-.09-.18-.82-1.98-1.12-2.71-.29-.7-.59-.61-.82-.62l-.7-.01c-.24 0-.64.09-.97.46-.34.37-1.28 1.25-1.28 3.05s1.31 3.54 1.49 3.78c.18.24 2.58 3.94 6.25 5.53.87.38 1.55.6 2.08.77.87.28 1.67.24 2.3.15.7-.1 2.17-.89 2.47-1.75.31-.86.31-1.59.21-1.75-.09-.15-.34-.24-.7-.42z" />
            </svg>
          </span>
        </a>

        {/* Call */}
        <a
          href={siteConfig.callLink}
          className="group flex items-center gap-3 pl-4 pr-3 py-3 rounded-full shadow-lg transition-all duration-200 hover:scale-[1.02]"
          style={{
            background: 'var(--c-accent-blue)',
            color: '#fff',
            boxShadow: '0 8px 32px rgba(21,71,190,0.35), 0 4px 12px rgba(0,0,0,0.3)',
          }}
          aria-label="Call Rajib"
        >
          <span
            className="hidden sm:inline"
            style={{ fontFamily: 'var(--font-heading)', fontSize: 13, fontWeight: 600 }}
          >
            Call Now
          </span>
          <span className="hidden sm:inline" style={{ fontFamily: 'var(--font-mono)', fontSize: 11, opacity: 0.85 }}>
            {siteConfig.contact.phone}
          </span>
          <span
            className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0"
            style={{ background: 'rgba(255,255,255,0.2)' }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
            </svg>
          </span>
        </a>
      </div>

      {/* Main FAB — morphs when expanded */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={`pointer-events-auto w-14 h-14 rounded-full flex items-center justify-center shadow-xl transition-all duration-300 hover:scale-105 active:scale-95 ${
          visible || expanded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6 pointer-events-none'
        }`}
        style={{
          background: expanded ? 'var(--c-bg-elevated)' : 'linear-gradient(135deg, var(--c-accent-blue), var(--c-accent-teal))',
          border: expanded ? '1px solid var(--c-border)' : 'none',
          boxShadow: expanded ? '0 4px 20px rgba(0,0,0,0.2)' : '0 8px 32px rgba(21,71,190,0.4), 0 4px 12px rgba(0,0,0,0.3)',
          color: '#fff',
          cursor: 'pointer',
        }}
        aria-label={expanded ? 'Close contact menu' : 'Open contact menu'}
        aria-expanded={expanded}
      >
        {expanded ? (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        ) : (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
          </svg>
        )}
      </button>

      {/* Pulse ring when not expanded */}
      {!expanded && visible && (
        <span
          className="absolute bottom-0 right-0 w-14 h-14 rounded-full pointer-events-none"
          style={{
            border: '2px solid rgba(21,71,190,0.3)',
            animation: 'pulse 2s ease-out infinite',
          }}
          aria-hidden="true"
        />
      )}
    </div>
  );
}
