import { motion } from 'framer-motion';

function StatCard({ value, label, tone }: { value: string; label: string; tone?: 'blue' | 'teal' | 'gold' }) {
  const color = tone === 'teal' ? 'var(--c-accent-teal)' : tone === 'blue' ? 'var(--c-accent-blue-l)' : 'var(--c-accent-gold)';

  return (
    <div
      className="card p-5 text-left"
      style={{
        background: 'rgba(13, 31, 60, 0.55)',
        backdropFilter: 'blur(10px)',
      }}
    >
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 32, fontWeight: 600, color, lineHeight: 1 }}>
        {value}
      </div>
      <div style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--c-text-secondary)', marginTop: 6, lineHeight: 1.4 }}>
        {label}
      </div>
    </div>
  );
}

interface HeroSectionProps {
  productCount?: number;
  companyCount?: number;
}

export default function HeroSection({ productCount = 6, companyCount = 3 }: HeroSectionProps) {
  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section
      className="relative min-h-screen flex items-center overflow-hidden"
      style={{ minHeight: 620, paddingTop: 64 }}
    >
      {/* ── Background ── */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse 60% 50% at 50% -5%, rgba(13,31,60,0.7), transparent 70%)',
        }}
      />
      {/* Blue glow — top right */}
      <div
        className="absolute pointer-events-none"
        style={{
          width: 500, height: 500,
          background: 'radial-gradient(circle, rgba(21,71,190,0.20), transparent)',
          filter: 'blur(100px)',
          top: '-200px', right: '-150px',
        }}
      />
      {/* Teal glow — bottom left */}
      <div
        className="absolute pointer-events-none"
        style={{
          width: 400, height: 400,
          background: 'radial-gradient(circle, rgba(10,123,108,0.15), transparent)',
          filter: 'blur(80px)',
          bottom: '-120px', left: '-80px',
        }}
      />
      {/* Gold glow — top middle */}
      <div
        className="absolute pointer-events-none"
        style={{
          width: 300, height: 300,
          background: 'radial-gradient(circle, rgba(196,154,42,0.10), transparent)',
          filter: 'blur(90px)',
          top: '20%', left: '30%',
        }}
      />
      {/* Mesh grid */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(var(--c-border) 1px, transparent 1px),
            linear-gradient(90deg, var(--c-border) 1px, transparent 1px)
          `,
          backgroundSize: '64px 64px',
          opacity: 0.04,
        }}
      />

      {/* ── Content ── */}
      <div className="container-site relative z-10 py-16">
        <div className="max-w-3xl">
          {/* Consulting badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05, duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-8"
            style={{
              background: 'rgba(10,123,108,0.12)',
              border: '1px solid rgba(10,123,108,0.3)',
            }}
          >
            <span className="pulse-dot" style={{ backgroundColor: 'var(--c-accent-teal)', width: 8, height: 8, borderRadius: '50%' }} />
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              fontWeight: 500,
              color: 'var(--c-accent-teal)',
            }}>
              Available for consulting &amp; freelance
            </span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.12, duration: 0.6 }}
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'clamp(36px, 5.5vw, 64px)',
              fontWeight: 700,
              lineHeight: 1.08,
              letterSpacing: '-0.03em',
              color: 'var(--c-text-primary)',
              marginBottom: 20,
            }}
          >
            I build backend systems and SaaS products that{' '}
            <span style={{ color: 'var(--c-accent-blue-l)' }}>scale</span>
            {', '}
            <span style={{ color: 'var(--c-accent-teal)' }}>perform</span>
            , and{' '}
            <span style={{ color: 'var(--c-accent-gold)' }}>ship</span>.
          </motion.h1>

          {/* Sub-headline */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.22, duration: 0.6 }}
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: 'clamp(16px, 2vw, 19px)',
              fontWeight: 300,
              lineHeight: 1.65,
              color: 'var(--c-text-secondary)',
              maxWidth: 580,
              marginBottom: 12,
            }}
          >
            Senior .NET &amp; Azure engineer with 12+ years delivering enterprise systems.
            I've architected platforms processing 500K+ daily events for Fortune 500
            healthcare — cutting processing time by 30% and medication errors by 40%.
          </motion.p>

          {/* Metrics badge */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.28, duration: 0.5 }}
            className="inline-flex flex-wrap items-center gap-x-4 gap-y-1 px-0 mb-8"
          >
            {['30% faster processing', '40% fewer errors', '25% higher satisfaction'].map((metric, i) => (
              <span key={metric} className="flex items-center gap-2" style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 14,
                fontWeight: 500,
                color: 'var(--c-accent-gold)',
              }}>
                {i > 0 && <span style={{ color: 'var(--c-border)', fontWeight: 300 }}>|</span>}
                {metric}
              </span>
            ))}
          </motion.div>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.34, duration: 0.5 }}
            className="flex flex-wrap gap-3 mb-10"
          >
            <button
              onClick={() => scrollTo('projects')}
              className="inline-flex items-center px-7 py-3.5 text-[15px] font-medium rounded-md transition-all duration-200"
              style={{
                fontFamily: 'var(--font-heading)',
                fontWeight: 500,
                backgroundColor: 'var(--c-accent-blue)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                cursor: 'pointer',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.backgroundColor = 'var(--c-accent-blue-l)';
                e.currentTarget.style.boxShadow = 'var(--shadow-glow-blue)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.backgroundColor = 'var(--c-accent-blue)';
                e.currentTarget.style.boxShadow = '';
              }}
            >
              See My Work ↓
            </button>
            <a
              href="/Resume-RajibMahata.pdf"
              download
              className="inline-flex items-center px-7 py-3.5 text-[15px] font-medium rounded-md transition-all duration-200"
              style={{
                fontFamily: 'var(--font-heading)',
                fontWeight: 500,
                backgroundColor: 'var(--c-accent-gold)',
                color: '#080D1A',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                textDecoration: 'none',
                cursor: 'pointer',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.backgroundColor = 'var(--c-accent-gold-l)';
                e.currentTarget.style.boxShadow = 'var(--shadow-glow-gold)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.backgroundColor = 'var(--c-accent-gold)';
                e.currentTarget.style.boxShadow = '';
              }}
            >
              📄 Download Resume
            </a>
            <button
              onClick={() => scrollTo('contact')}
              className="inline-flex items-center px-7 py-3.5 text-[15px] font-medium rounded-md transition-all duration-200"
              style={{
                fontFamily: 'var(--font-heading)',
                fontWeight: 500,
                background: 'transparent',
                color: 'var(--c-text-primary)',
                border: '1px solid var(--c-border-hover)',
                borderRadius: 'var(--radius-md)',
                cursor: 'pointer',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.borderColor = 'var(--c-accent-blue)';
                e.currentTarget.style.color = 'var(--c-accent-blue-l)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = 'var(--c-border-hover)';
                e.currentTarget.style.color = 'var(--c-text-primary)';
              }}
            >
              Get in Touch
            </button>
          </motion.div>

          {/* Email */}
          <motion.a
            href="mailto:rajibmahata143@gmail.com"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.44, duration: 0.5 }}
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 13,
              color: 'var(--c-text-muted)',
              textDecoration: 'none',
              display: 'inline-block',
            }}
            onMouseEnter={e => { e.currentTarget.style.color = 'var(--c-accent-blue-l)'; }}
            onMouseLeave={e => { e.currentTarget.style.color = 'var(--c-text-muted)'; }}
          >
            ✉ rajibmahata143@gmail.com
          </motion.a>
        </div>

        {/* ── Stats Bar ── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.6 }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-4 pt-12 mt-12 border-t"
          style={{ borderColor: 'var(--c-border)' }}
        >
          <StatCard value="12+"   label="Years building enterprise systems" tone="gold" />
          <StatCard value={`${productCount}`} label="Active products & projects" tone="blue" />
          <StatCard value={`${companyCount}`} label="Enterprise clients delivered for" tone="teal" />
          <StatCard value="500K+" label="Daily events processed on Azure" tone="gold" />
        </motion.div>
      </div>
    </section>
  );
}
