export default function GlobalFooter() {
  const year = new Date().getFullYear();

  const footerLinks = [
    { label: 'GitHub',    href: 'https://github.com/rajibmahata' },
    { label: 'LinkedIn',  href: 'https://linkedin.com/in/rajib-mahata' },
    { label: 'Resume',    href: '/Resume-RajibMahata.pdf', download: true },
    { label: 'Email',     href: 'mailto:rajibmahata143@gmail.com' },
  ];

  return (
    <footer
      className="border-t"
      style={{
        borderColor: 'var(--c-border)',
        background: 'var(--c-bg-primary)',
      }}
    >
      <div className="container-site py-12">
        {/* CTA Row */}
        <div className="text-center mb-10">
          <h3 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 24,
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
            marginBottom: 16,
          }}>
            I'm available for consulting, freelance projects, and technical collaborations.
          </p>
          <a
            href="#contact"
            className="inline-flex items-center px-6 py-3 text-[14px] font-medium rounded-md transition-all duration-200"
            style={{
              fontFamily: 'var(--font-heading)',
              fontWeight: 500,
              backgroundColor: 'var(--c-accent-blue)',
              color: '#fff',
              borderRadius: 'var(--radius-md)',
              textDecoration: 'none',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.backgroundColor = 'var(--c-accent-blue-l)';
              e.currentTarget.style.boxShadow = 'var(--shadow-glow-blue)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.backgroundColor = 'var(--c-accent-blue)';
              e.currentTarget.style.boxShadow = '';
            }}
            onClick={e => {
              e.preventDefault();
              document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            Get in Touch →
          </a>
        </div>

        <div className="h-px mb-8" style={{ background: 'var(--c-border)' }} />

        {/* Bottom row */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
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

          <p style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            color: 'var(--c-text-muted)',
          }}>
            © {year} Rajib Mahata · Built with React + .NET 8
          </p>
        </div>
      </div>
    </footer>
  );
}
