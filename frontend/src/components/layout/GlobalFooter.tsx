export default function GlobalFooter() {
  const year = new Date().getFullYear();

  const footerLinks = [
    { label: 'GitHub',    href: 'https://github.com/rajibmahata' },
    { label: 'LinkedIn',  href: 'https://linkedin.com/in/rajib-mahata' },
    { label: 'Email',     href: 'mailto:rajib@rajiblabs.com' },
  ];

  return (
    <footer
      className="border-t"
      style={{
        borderColor: 'var(--c-border)',
        background: 'var(--c-bg-primary)',
      }}
    >
      <div className="container-site py-10 flex flex-col md:flex-row items-center justify-between gap-6">
        {/* Brand */}
        <div className="flex items-baseline gap-0.5">
          <span style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700, color: 'var(--c-text-primary)' }}>
            Rajib
          </span>
          <span style={{ fontFamily: 'var(--font-heading)', fontSize: 14, fontWeight: 400, color: 'var(--c-accent-gold)' }}>
            Labs
          </span>
        </div>

        {/* Links */}
        <div className="flex items-center gap-6">
          {footerLinks.map(link => (
            <a
              key={link.label}
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
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

        {/* Copyright */}
        <p style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 12,
          color: 'var(--c-text-muted)',
        }}>
          © {year} Rajib Mahata · Built with React + .NET 8 · Powered by OpenClaw AI
        </p>
      </div>
    </footer>
  );
}
