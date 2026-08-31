import { motion } from 'framer-motion';
import { siteConfig } from '../../config/site';

function StatCard({ value, label, tone }: { value: string; label: string; tone?: 'blue' | 'teal' | 'gold' }) {
  const color = tone === 'teal' ? 'var(--c-accent-teal)' : tone === 'blue' ? 'var(--c-accent-blue-l)' : 'var(--c-accent-gold)';
  return (
    <div
      className="card p-5 text-left"
      style={{ background: 'rgba(13, 31, 60, 0.55)', backdropFilter: 'blur(10px)' }}
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
      className="relative overflow-hidden"
      style={{ minHeight: 620, paddingTop: 64 }}
    >
      {/* ── Background — PestFlow clean SaaS feel ── */}
      <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse 70% 60% at 50% -10%, rgba(13,31,60,0.65), transparent 65%)' }} />
      <div className="absolute pointer-events-none" style={{ width: 600, height: 600, background: 'radial-gradient(circle, rgba(21,71,190,0.16), transparent)', filter: 'blur(100px)', top: '-180px', right: '-120px' }} />
      <div className="absolute pointer-events-none" style={{ width: 420, height: 420, background: 'radial-gradient(circle, rgba(10,123,108,0.12), transparent)', filter: 'blur(80px)', bottom: '-100px', left: '-80px' }} />
      <div className="absolute pointer-events-none" style={{ width: 320, height: 320, background: 'radial-gradient(circle, rgba(196,154,42,0.08), transparent)', filter: 'blur(90px)', top: '28%', left: '32%' }} />
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(var(--c-border) 1px, transparent 1px), linear-gradient(90deg, var(--c-border) 1px, transparent 1px)`,
          backgroundSize: '64px 64px',
          opacity: 0.035,
        }}
      />

      {/* ── Content: PestFlow 2-col hero ── */}
      <div className="container-site relative z-10 py-12 lg:py-16">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-12 items-center">
          {/* LEFT — Copy (PestFlow left hero) */}
          <div className="max-w-2xl">
            {/* Available badge + PWA hint */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05, duration: 0.5 }}
              className="inline-flex flex-wrap items-center gap-2 mb-6"
            >
              <span className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full" style={{ background: 'rgba(10,123,108,0.12)', border: '1px solid rgba(10,123,108,0.3)' }}>
                <span className="pulse-dot" style={{ backgroundColor: 'var(--c-accent-teal)', width: 8, height: 8, borderRadius: '50%' }} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 500, color: 'var(--c-accent-teal)' }}>
                  Available for consulting & freelance
                </span>
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full" style={{ background: 'rgba(21,71,190,0.10)', border: '1px solid rgba(21,71,190,0.20)' }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--c-accent-blue-l)" strokeWidth="2"><rect x="2" y="7" width="20" height="14" rx="2" /><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" /></svg>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 500, color: 'var(--c-accent-blue-l)' }}>PWA · Installable · Offline</span>
              </span>
            </motion.div>

            {/* Headline — PestFlow large display */}
            <motion.h1
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.12, duration: 0.6 }}
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 'clamp(34px, 5vw, 56px)',
                fontWeight: 700,
                lineHeight: 1.05,
                letterSpacing: '-0.03em',
                color: 'var(--c-text-primary)',
                marginBottom: 16,
              }}
            >
              I build backend systems and SaaS products that{' '}
              <span style={{ color: 'var(--c-accent-blue-l)' }}>scale</span>
              {', '}
              <span style={{ color: 'var(--c-accent-teal)' }}>perform</span>
              , and <span style={{ color: 'var(--c-accent-gold)' }}>ship</span>.
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.22, duration: 0.6 }}
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: 'clamp(15px, 1.9vw, 18px)',
                fontWeight: 300,
                lineHeight: 1.65,
                color: 'var(--c-text-secondary)',
                maxWidth: 560,
                marginBottom: 10,
              }}
            >
              Senior .NET & Azure engineer with 12+ years delivering enterprise systems. Architected platforms
              processing 500K+ daily events for Fortune 500 healthcare — 30% faster, 40% fewer errors.
            </motion.p>

            {/* Metrics inline */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.28, duration: 0.5 }}
              className="inline-flex flex-wrap items-center gap-x-3 gap-y-1 mb-7"
            >
              {(['30% faster processing', '40% fewer errors', '25% higher satisfaction'] as const).map((metric, i) => (
                <span key={metric} className="flex items-center gap-2" style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 500, color: 'var(--c-accent-gold)' }}>
                  {i > 0 && <span style={{ color: 'var(--c-border)', fontWeight: 300 }}>|</span>}
                  {metric}
                </span>
              ))}
            </motion.div>

            {/* CTAs — PestFlow primary + secondary + WhatsApp/Call (like PestFlow trial) */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.34, duration: 0.5 }}
              className="flex flex-wrap gap-3 mb-6"
            >
              <a
                href={siteConfig.whatsappLink}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3.5 text-[14px] font-semibold rounded-full transition-all duration-200"
                style={{ fontFamily: 'var(--font-heading)', background: '#25D366', color: '#fff', borderRadius: '999px', textDecoration: 'none', boxShadow: '0 4px 20px rgba(37,211,102,0.30)' }}
                onMouseEnter={e => { e.currentTarget.style.background = '#1ebe5a'; e.currentTarget.style.transform = 'translateY(-1px)'; }}
                onMouseLeave={e => { e.currentTarget.style.background = '#25D366'; e.currentTarget.style.transform = 'translateY(0)'; }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M19.05 4.94A9.91 9.91 0 0 0 12.04 2C6.58 2 2.14 6.45 2.14 11.9c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38a9.87 9.87 0 0 0 4.79 1.22h.01c5.46 0 9.9-4.45 9.9-9.9 0-2.64-1.03-5.13-2.9-7zM12.04 19.8h-.01a8.13 8.13 0 0 1-4.15-1.14l-.3-.18-3.12.82.83-3.04-.2-.31a8.18 8.18 0 0 1-1.26-4.05c0-4.5 3.66-8.16 8.17-8.16 2.18 0 4.23.85 5.77 2.4a8.1 8.1 0 0 1 2.39 5.76c0 4.5-3.66 8.17-8.15 8.17z" /></svg>
                Chat on WhatsApp
              </a>
              <a
                href={siteConfig.callLink}
                className="inline-flex items-center gap-2 px-6 py-3.5 text-[14px] font-semibold rounded-full transition-all duration-200"
                style={{ fontFamily: 'var(--font-heading)', background: 'var(--c-accent-blue)', color: '#fff', borderRadius: '999px', textDecoration: 'none', boxShadow: '0 4px 20px rgba(21,71,190,0.25)' }}
                onMouseEnter={e => { e.currentTarget.style.background = 'var(--c-accent-blue-l)'; e.currentTarget.style.transform = 'translateY(-1px)'; }}
                onMouseLeave={e => { e.currentTarget.style.background = 'var(--c-accent-blue)'; e.currentTarget.style.transform = 'translateY(0)'; }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" /></svg>
                Call Now
              </a>
              <button
                onClick={() => scrollTo('applications')}
                className="inline-flex items-center px-6 py-3.5 text-[14px] font-medium rounded-full transition-all"
                style={{ fontFamily: 'var(--font-heading)', background: 'transparent', color: 'var(--c-text-primary)', border: '1px solid var(--c-border-hover)', borderRadius: '999px', cursor: 'pointer' }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--c-accent-blue)'; e.currentTarget.style.color = 'var(--c-accent-blue-l)'; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--c-border-hover)'; e.currentTarget.style.color = 'var(--c-text-primary)'; }}
              >
                View Apps ↓
              </button>
            </motion.div>

            {/* Secondary: Resume + Email line */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.42, duration: 0.5 }}
              className="flex flex-wrap items-center gap-4"
            >
              <a
                href="/Resume-RajibMahata.pdf"
                download
                className="inline-flex items-center gap-2 text-[13px] font-medium transition-colors"
                style={{ fontFamily: 'var(--font-heading)', color: 'var(--c-accent-gold)', textDecoration: 'none' }}
                onMouseEnter={e => { e.currentTarget.style.color = 'var(--c-accent-gold-l)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = 'var(--c-accent-gold)'; }}
              >
                📄 Download Resume
              </a>
              <span style={{ color: 'var(--c-border)', fontSize: 12 }}>|</span>
              <a
                href="mailto:rajibmahata143@gmail.com"
                style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--c-text-muted)', textDecoration: 'none' }}
                onMouseEnter={e => { e.currentTarget.style.color = 'var(--c-accent-blue-l)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = 'var(--c-text-muted)'; }}
              >
                ✉ rajibmahata143@gmail.com
              </a>
            </motion.div>
          </div>

          {/* RIGHT — PestFlow dashboard preview mock (PWA showcase) */}
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ delay: 0.45, duration: 0.7, ease: [0, 0, 0.2, 1] }}
            className="relative lg:pl-4"
          >
            {/* Browser chrome */}
            <div
              className="rounded-2xl border overflow-hidden"
              style={{
                background: 'var(--c-bg-secondary)',
                borderColor: 'var(--c-border)',
                boxShadow: '0 20px 80px rgba(0,0,0,0.45), 0 0 0 1px rgba(37,99,244,0.08)',
              }}
            >
              {/* Title bar */}
              <div className="flex items-center gap-2 px-4 py-3 border-b" style={{ background: 'var(--c-bg-tertiary)', borderColor: 'var(--c-border)' }}>
                <div className="flex gap-1.5">
                  <span className="w-3 h-3 rounded-full" style={{ background: '#FF5F56' }} />
                  <span className="w-3 h-3 rounded-full" style={{ background: '#FFBD2E' }} />
                  <span className="w-3 h-3 rounded-full" style={{ background: '#27C93F' }} />
                </div>
                <div className="flex-1 flex justify-center">
                  <span className="px-3 py-1 rounded-full text-xs flex items-center gap-1.5" style={{ background: 'var(--c-bg-secondary)', border: '1px solid var(--c-border)', color: 'var(--c-text-muted)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                    <span className="w-2 h-2 rounded-full" style={{ background: '#25D366' }} />
                    rajiblabs.com — PWA · Offline-ready
                  </span>
                </div>
              </div>

              {/* Mock dashboard content — like PestFlow screenshot */}
              <div className="p-4 sm:p-5 space-y-4" style={{ background: 'linear-gradient(180deg, var(--c-bg-secondary), var(--c-bg-primary))' }}>
                {/* Tabs */}
                <div className="flex gap-2">
                  {[
                    { label: 'DocSignerHub', active: true, color: 'var(--c-accent-blue)' },
                    { label: 'ARIA', active: false, color: 'var(--c-accent-teal)' },
                    { label: 'LexVault', active: false, color: 'var(--c-accent-gold)' },
                  ].map((tab) => (
                    <span
                      key={tab.label}
                      className="px-3 py-1.5 rounded-full text-xs font-medium"
                      style={{
                        fontFamily: 'var(--font-heading)',
                        background: tab.active ? tab.color : 'transparent',
                        color: tab.active ? '#fff' : 'var(--c-text-muted)',
                        border: `1px solid ${tab.active ? tab.color : 'var(--c-border)'}`,
                      }}
                    >
                      {tab.label}
                    </span>
                  ))}
                  <span className="ml-auto hidden sm:inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs" style={{ background: 'rgba(37,211,102,0.12)', color: '#25D366', border: '1px solid rgba(37,211,102,0.2)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                    ● Live
                  </span>
                </div>

                {/* Metric cards row — like PestFlow analytics */}
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { k: '140+', v: 'API endpoints', c: 'var(--c-accent-blue-l)' },
                    { k: '500K+', v: 'events / day', c: 'var(--c-accent-teal)' },
                    { k: '12+', v: 'years exp', c: 'var(--c-accent-gold)' },
                  ].map((m) => (
                    <div key={m.v} className="rounded-xl p-3 border text-center" style={{ background: 'var(--c-bg-tertiary)', borderColor: 'var(--c-border)' }}>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 700, color: m.c }}>{m.k}</div>
                      <div style={{ fontFamily: 'var(--font-body)', fontSize: 10, color: 'var(--c-text-muted)' }}>{m.v}</div>
                    </div>
                  ))}
                </div>

                {/* App list preview */}
                <div className="space-y-2">
                  {[
                    { name: 'DocSignerHub', stack: '.NET 8 · Blazor · Azure · Stripe', status: 'Live', dot: '#0A7B6C' },
                    { name: 'AI Student Tutor', stack: 'FastAPI · LangGraph · Next.js', status: 'WIP', dot: '#C49A2A' },
                    { name: 'LexVault', stack: '.NET 8 · Qdrant · Hybrid Search', status: 'WIP', dot: '#1547BE' },
                  ].map((row) => (
                    <div key={row.name} className="flex items-center gap-3 p-3 rounded-xl border" style={{ background: 'var(--c-bg-primary)', borderColor: 'var(--c-border)' }}>
                      <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: row.dot }} />
                      <div className="min-w-0 flex-1">
                        <div style={{ fontFamily: 'var(--font-heading)', fontSize: 13, fontWeight: 600, color: 'var(--c-text-primary)' }}>{row.name}</div>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--c-text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{row.stack}</div>
                      </div>
                      <span className="px-2 py-1 rounded text-[10px] font-semibold" style={{ background: row.status === 'Live' ? 'rgba(10,123,108,0.15)' : 'rgba(196,154,42,0.12)', color: row.status === 'Live' ? 'var(--c-accent-teal)' : 'var(--c-accent-gold)', border: `1px solid ${row.status === 'Live' ? 'rgba(10,123,108,0.25)' : 'rgba(196,154,42,0.2)'}`, fontFamily: 'var(--font-mono)' }}>{row.status}</span>
                    </div>
                  ))}
                </div>

                {/* Bottom CTA inside mock */}
                <div className="flex gap-2 pt-1">
                  <a href={siteConfig.whatsappLink} target="_blank" rel="noopener noreferrer" className="flex-1 py-2.5 rounded-lg text-center text-xs font-semibold" style={{ background: '#25D366', color: '#fff', fontFamily: 'var(--font-heading)', textDecoration: 'none' }}>
                    WhatsApp
                  </a>
                  <a href={siteConfig.callLink} className="flex-1 py-2.5 rounded-lg text-center text-xs font-semibold border" style={{ background: 'var(--c-accent-blue)', color: '#fff', borderColor: 'var(--c-accent-blue)', fontFamily: 'var(--font-heading)', textDecoration: 'none' }}>
                    Call
                  </a>
                </div>
              </div>
            </div>

            {/* Floating badge — PWA */}
            <div
              className="hidden sm:flex absolute -bottom-4 -left-4 items-center gap-2 px-3 py-2 rounded-full border shadow-lg"
              style={{ background: 'var(--c-bg-elevated)', borderColor: 'var(--c-border)', boxShadow: '0 8px 24px rgba(0,0,0,0.3)' }}
            >
              <span className="w-7 h-7 rounded-full flex items-center justify-center" style={{ background: '#25D366' }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="white"><path d="M12 2l7 4v6c0 5-3.5 7.74-7 10-3.5-2.26-7-5-7-10V6l7-4z" /></svg>
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--c-text-secondary)' }}>
                <strong style={{ color: 'var(--c-text-primary)' }}>PWA</strong> · Install & use offline
              </span>
            </div>

            {/* Glow behind */}
            <div className="absolute -z-10 inset-0 blur-3xl opacity-20 pointer-events-none" style={{ background: 'radial-gradient(ellipse 60% 40% at 50% 50%, var(--c-accent-blue), transparent)' }} />
          </motion.div>
        </div>

        {/* ── Stats Bar — PestFlow trust bar style ── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.6 }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-4 pt-10 mt-10 border-t"
          style={{ borderColor: 'var(--c-border)' }}
        >
          <StatCard value="12+" label="Years building enterprise systems" tone="gold" />
          <StatCard value={`${productCount}`} label="Active products & projects" tone="blue" />
          <StatCard value={`${companyCount}`} label="Enterprise clients delivered for" tone="teal" />
          <StatCard value="500K+" label="Daily events processed on Azure" tone="gold" />
        </motion.div>

        {/* Trust row — like PestFlow "Trusted by 500+ companies" */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.75, duration: 0.6 }}
          className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 pt-8 mt-6 border-t"
          style={{ borderColor: 'rgba(30,45,74,0.35)' }}
        >
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--c-text-muted)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>Trusted architecture for</span>
          {['Fortune 500 Healthcare', 'Telecom Enterprise', 'Product Studio', '30+ Repos Shipped'].map((t) => (
            <span key={t} style={{ fontFamily: 'var(--font-heading)', fontSize: 13, fontWeight: 600, color: 'var(--c-text-secondary)' }}>{t}</span>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
