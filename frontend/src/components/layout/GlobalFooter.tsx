import { siteConfig } from '../../config/site';

export default function GlobalFooter() {
  const year = new Date().getFullYear();

  const footerLinks = [
    { label: 'GitHub',    href: siteConfig.social.github },
    { label: 'LinkedIn',  href: siteConfig.social.linkedin },
    { label: 'Resume',    href: '/Resume-RajibMahata.pdf', download: true },
    { label: 'Email',     href: siteConfig.emailLink },
  ];

  return (
    <footer
      className="w-full border-t pb-24 md:pb-8"
      style={{
        borderColor: 'rgba(67,70,84,0.1)',
        background: '#090e1b',
        paddingBottom: 'max(3rem, env(safe-area-inset-bottom))',
      }}
    >
      <div className="container-site py-12">
        {/* CTA Row — PestFlow style: two primary CTAs with WhatsApp */}
        <div className="text-center mb-10">
          <h3 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 28,
            fontWeight: 700,
            color: 'var(--c-text-primary)',
            marginBottom: 8,
          }}>
            Ready to build something great?
          </h3>
          <p style={{
            fontFamily: 'var(--font-body)',
            fontSize: 15,
            color: 'var(--c-text-secondary)',
            marginBottom: 20,
            maxWidth: 640,
            marginInline: 'auto',
          }}>
            I’m available for consulting, freelance projects, and technical collaborations. Chat instantly on WhatsApp or call — or send a message below.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <a
              href={siteConfig.whatsappLink}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 text-[14px] font-semibold rounded-full transition-all"
              style={{
                fontFamily: 'var(--font-heading)',
                background: '#25D366',
                color: '#fff',
                borderRadius: '999px',
                textDecoration: 'none',
                boxShadow: '0 4px 20px rgba(37,211,102,0.3)',
              }}
              onMouseEnter={e => { e.currentTarget.style.background = '#1ebe5a'; e.currentTarget.style.transform = 'translateY(-1px)'; }}
              onMouseLeave={e => { e.currentTarget.style.background = '#25D366'; e.currentTarget.style.transform = 'translateY(0)'; }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M19.05 4.94A9.91 9.91 0 0 0 12.04 2C6.58 2 2.14 6.45 2.14 11.9c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38a9.87 9.87 0 0 0 4.79 1.22h.01c5.46 0 9.9-4.45 9.9-9.9 0-2.64-1.03-5.13-2.9-7zM12.04 19.8h-.01a8.13 8.13 0 0 1-4.15-1.14l-.3-.18-3.12.82.83-3.04-.2-.31a8.18 8.18 0 0 1-1.26-4.05c0-4.5 3.66-8.16 8.17-8.16 2.18 0 4.23.85 5.77 2.4a8.1 8.1 0 0 1 2.39 5.76c0 4.5-3.66 8.17-8.15 8.17z" /></svg>
              WhatsApp Me
            </a>
            <a
              href={siteConfig.callLink}
              className="inline-flex items-center gap-2 px-6 py-3 text-[14px] font-semibold rounded-full transition-all"
              style={{
                fontFamily: 'var(--font-heading)',
                background: 'var(--c-accent-blue)',
                color: '#fff',
                borderRadius: '999px',
                textDecoration: 'none',
                boxShadow: '0 4px 20px rgba(21,71,190,0.25)',
              }}
              onMouseEnter={e => { e.currentTarget.style.background = 'var(--c-accent-blue-l)'; e.currentTarget.style.transform = 'translateY(-1px)'; }}
              onMouseLeave={e => { e.currentTarget.style.background = 'var(--c-accent-blue)'; e.currentTarget.style.transform = 'translateY(0)'; }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" /></svg>
              Call {siteConfig.contact.phone}
            </a>
            <a
              href="#contact"
              className="inline-flex items-center px-6 py-3 text-[14px] font-medium rounded-full transition-all"
              style={{
                fontFamily: 'var(--font-heading)',
                background: 'transparent',
                color: 'var(--c-text-secondary)',
                border: '1px solid var(--c-border)',
                borderRadius: '999px',
                textDecoration: 'none',
              }}
              onClick={e => {
                e.preventDefault();
                document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' });
              }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--c-accent-blue)'; e.currentTarget.style.color = 'var(--c-text-primary)'; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--c-border)'; e.currentTarget.style.color = 'var(--c-text-secondary)'; }}
            >
              Send Message →
            </a>
          </div>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--c-text-muted)', marginTop: 12 }}>
            Typically replies within 2–4 hours · Available 9AM–9PM IST · Global remote
          </p>
        </div>

        <div className="h-px mb-8" style={{ background: 'var(--c-border)' }} />

        {/* Bottom row — richer footer */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Brand + PWA */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #1547BE, #0A7B6C)' }}>
                <span style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 700, color: '#fff' }}>R</span>
              </span>
              <span style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 700, color: 'var(--c-text-primary)' }}>Rajib<span style={{ color: 'var(--c-accent-gold)', fontWeight: 400 }}>Labs</span></span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold" style={{ background: 'rgba(37,211,102,0.12)', color: '#25D366', border: '1px solid rgba(37,211,102,0.2)', fontFamily: 'var(--font-mono)' }}>PWA</span>
            </div>
            <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--c-text-muted)', lineHeight: 1.6 }}>
              AI-powered portfolio & software lab. Senior .NET & Azure engineering, SaaS products, and AI systems. Installable PWA — works offline on Android, iOS, desktop.
            </p>
          </div>

          {/* Quick links */}
          <div className="grid grid-cols-2 gap-6">
            <div>
              <p style={{ fontFamily: 'var(--font-heading)', fontSize: 12, fontWeight: 600, color: 'var(--c-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>Explore</p>
              <div className="space-y-2">
                {[
                  { label: 'Applications', href: '#applications' },
                  { label: 'Projects', href: '#projects' },
                  { label: 'Services', href: '#services' },
                  { label: 'Contact', href: '#contact' },
                ].map(l => (
                  <a key={l.label} href={l.href} onClick={e => { e.preventDefault(); document.getElementById(l.href.replace('#',''))?.scrollIntoView({ behavior: 'smooth' }); }} style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--c-text-secondary)', textDecoration: 'none', display: 'block' }}>{l.label}</a>
                ))}
              </div>
            </div>
            <div>
              <p style={{ fontFamily: 'var(--font-heading)', fontSize: 12, fontWeight: 600, color: 'var(--c-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>Connect</p>
              <div className="space-y-2">
                <a href={siteConfig.whatsappLink} target="_blank" rel="noopener noreferrer" style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#25D366', textDecoration: 'none', display: 'block' }}>WhatsApp</a>
                <a href={siteConfig.callLink} style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--c-accent-blue-l)', textDecoration: 'none', display: 'block' }}>Call</a>
                <a href={siteConfig.emailLink} style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--c-text-secondary)', textDecoration: 'none', display: 'block' }}>Email</a>
                <a href={siteConfig.social.github} target="_blank" rel="noopener noreferrer" style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--c-text-secondary)', textDecoration: 'none', display: 'block' }}>GitHub</a>
              </div>
            </div>
          </div>

          {/* PWA install hint */}
          <div className="p-4 rounded-xl border" style={{ background: 'var(--c-bg-secondary)', borderColor: 'var(--c-border)' }}>
            <p style={{ fontFamily: 'var(--font-heading)', fontSize: 13, fontWeight: 600, color: 'var(--c-text-primary)', marginBottom: 6 }}>📲 Install RajibLabs App</p>
            <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: 'var(--c-text-muted)', lineHeight: 1.5, marginBottom: 10 }}>
              Add to home screen for offline access, push updates & native-like experience on any device.
            </p>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--c-text-muted)' }}>
              Android: Menu → Install app · iOS: Share → Add to Home Screen
            </p>
          </div>
        </div>

        <div className="h-px mb-6" style={{ background: 'var(--c-border)' }} />

        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--c-text-muted)' }}>
            © {year} Rajib Mahata · Built with React + .NET 8 · PWA · Offline-ready
          </p>
          <div className="flex items-center gap-5">
            {footerLinks.map(link => (
              <a
                key={link.label}
                href={link.href}
                target={link.href.startsWith('http') ? '_blank' : undefined}
                rel={link.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                download={link.download ? '' : undefined}
                className="transition-colors"
                style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: 13,
                  fontWeight: 400,
                  color: 'var(--c-text-muted)',
                  textDecoration: 'none',
                }}
                onMouseEnter={e => { e.currentTarget.style.color = 'var(--c-text-primary)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = 'var(--c-text-muted)'; }}
              >
                {link.label}
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
