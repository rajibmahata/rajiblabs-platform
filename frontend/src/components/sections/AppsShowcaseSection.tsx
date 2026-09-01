import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';

// PestFlow-inspired: Everything you need to run your business — but for RajibLabs SaaS products
const apps = [
  {
    name: 'DocSignerHub',
    tagline: 'e-Signature SaaS · Live',
    desc: 'Multi-signer workflows, HMAC auth, AI clause analysis, 140+ API endpoints. Built for Indian enterprise.',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
    ),
    color: '#1547BE',
    bg: 'rgba(21,71,190,0.10)',
    border: 'rgba(21,71,190,0.20)',
    href: 'https://docsignerhub.com',
    status: 'Live',
    featured: true,
  },
  {
    name: 'ARIA',
    tagline: 'Enterprise RAG Platform · Beta',
    desc: 'Turn your docs into a conversational knowledge base. No-code multi-agent pipelines, hybrid vector + BM25 search.',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    ),
    color: '#0A7B6C',
    bg: 'rgba(10,123,108,0.10)',
    border: 'rgba(10,123,108,0.20)',
    href: 'https://github.com/rajibmahata/AI-Avatar-RAG-Platform',
    status: 'Beta',
  },
  {
    name: 'LexVault',
    tagline: 'Legal RAG · On-Premise',
    desc: 'Dual-pipeline legal scoring. Zero-LLM inference on Qdrant hybrid search. Windows Server, no cloud cost.',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
        <line x1="8" y1="7" x2="16" y2="7" />
        <line x1="8" y1="11" x2="14" y2="11" />
      </svg>
    ),
    color: '#C49A2A',
    bg: 'rgba(196,154,42,0.10)',
    border: 'rgba(196,154,42,0.20)',
    href: 'https://github.com/rajibmahata/Legal-Document-RAG-System-LEXVAULT',
    status: 'WIP',
  },
  {
    name: 'AI Student Tutor',
    tagline: 'EdTech · 12 Agents · WIP',
    desc: 'Voice-first tutoring in 4 languages, 8-step journey, human-in-the-loop validation. Nursery to Class 12.',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 10v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V10" />
        <rect x="2" y="6" width="20" height="8" rx="2" />
        <circle cx="12" cy="14" r="2" />
      </svg>
    ),
    color: '#1547BE',
    bg: 'rgba(21,71,190,0.10)',
    border: 'rgba(21,71,190,0.20)',
    href: 'https://github.com/rajibmahata/Math-tutor-AI-Agent',
    status: 'WIP',
  },
  {
    name: 'MedRemind',
    tagline: 'Healthcare PWA · Live',
    desc: 'Two-stage OCR (Azure DI + GPT-4o-mini) in 10 languages incl. RTL. Photo prescription → reminders.',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <line x1="12" y1="8" x2="12" y2="16" />
        <line x1="8" y1="12" x2="16" y2="12" />
      </svg>
    ),
    color: '#0A7B6C',
    bg: 'rgba(10,123,108,0.10)',
    border: 'rgba(10,123,108,0.20)',
    href: 'https://github.com/rajibmahata/MedRemind',
    status: 'Live',
  },
  {
    name: 'Solicitor CMS',
    tagline: 'Legal · Case Flows · WIP',
    desc: 'Visual workflow builder, document automation, client portal for mid-size law firms.',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="7" width="20" height="14" rx="2" />
        <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
        <line x1="12" y1="12" x2="12" y2="12" />
      </svg>
    ),
    color: '#C49A2A',
    bg: 'rgba(196,154,42,0.10)',
    border: 'rgba(196,154,42,0.20)',
    href: 'https://github.com/rajibmahata/SolicitorCaseManagementSystem',
    status: 'WIP',
  },
  {
    name: 'FoodFleet',
    tagline: 'Logistics · Multi-branch',
    desc: 'Location-based menu & order routing for restaurant chains. GPS branch detection.',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <polyline points="16 12 12 8 8 12" />
        <line x1="12" y1="16" x2="12" y2="8" />
      </svg>
    ),
    color: '#1547BE',
    bg: 'rgba(21,71,190,0.10)',
    border: 'rgba(21,71,190,0.20)',
    href: 'https://github.com/rajibmahata/FoodFleet',
    status: 'Live',
  },
  {
    name: 'ArtForge & AI Resume',
    tagline: 'AI Agentic · Portfolio',
    desc: 'Multi-agent pipelines for portfolio curation & 7-agent resume review with RAG grounding.',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
      </svg>
    ),
    color: '#0A7B6C',
    bg: 'rgba(10,123,108,0.10)',
    border: 'rgba(10,123,108,0.20)',
    href: 'https://github.com/rajibmahata/ArtForge',
    status: 'Live',
  },
];

export default function AppsShowcaseSection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section id="applications" className="section-pad relative overflow-hidden" ref={ref} style={{ background: 'var(--c-surface)' }}>
      <div id="ai" className="absolute -top-20" aria-hidden="true" />
      <div className="absolute inset-0 bg-grid-pattern opacity-10 pointer-events-none" aria-hidden="true" />
      <div className="container-site relative">
        <SectionLabel>APPLICATIONS BY RAJIBLABS</SectionLabel>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
        >
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-10">
            <div>
              <h2 className="font-section-title text-[42px] text-on-surface" style={{ fontFamily: 'Fraunces, serif', fontWeight: 700, color: '#F0F4FF', lineHeight: 1.1 }}>
                Everything you need
                <br />
                <span style={{ color: '#8896B3', fontWeight: 400 }}>shipped as products.</span>
              </h2>
            </div>
            <p className="font-body-base text-[16px] text-text-secondary max-w-[460px]" style={{ fontFamily: 'DM Sans, sans-serif', color: '#8896B3', lineHeight: 1.6 }}>
              From e-signatures to legal RAG, healthcare PWA to EdTech — each app is a production SaaS, PWA or platform built on .NET, Azure & AI.
            </p>
          </div>

          {/* Stitch swipe-friendly on mobile, bento grid on desktop */}
          <div className="flex overflow-x-auto gap-4 pb-4 no-scrollbar snap-x snap-mandatory -mx-6 px-6 md:mx-0 md:px-0 md:grid md:grid-cols-2 lg:grid-cols-4 md:gap-4 md:overflow-visible md:pb-0">
            {apps.map((app, i) => (
              <motion.a
                key={app.name}
                href={app.href}
                target={app.href.startsWith('http') ? '_blank' : undefined}
                rel={app.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                initial={{ opacity: 0, y: 16 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: i * 0.06, duration: 0.4 }}
                className={`group relative flex flex-col p-6 rounded-2xl border text-left transition-all duration-300 card-elegant min-w-[280px] snap-center md:min-w-0 ${
                  app.featured ? 'lg:col-span-2' : ''
                }`}
                style={{ borderColor: app.border, textDecoration: 'none' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.boxShadow = `0 12px 40px rgba(0,0,0,0.25), 0 0 0 1px ${app.color}18`;
                  e.currentTarget.style.borderColor = `${app.color}40`;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '';
                  e.currentTarget.style.borderColor = app.border;
                }}
              >
                {/* Top row: icon + status */}
                <div className="flex items-start justify-between mb-4">
                  <span
                    className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                    style={{ background: app.bg, color: app.color, border: `1px solid ${app.border}` }}
                  >
                    {app.icon}
                  </span>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 10,
                      fontWeight: 600,
                      padding: '3px 8px',
                      borderRadius: 'var(--radius-sm)',
                      background: app.status === 'Live' ? 'rgba(10,123,108,0.15)' : app.status === 'Beta' ? 'rgba(21,71,190,0.15)' : 'rgba(196,154,42,0.15)',
                      color: app.status === 'Live' ? 'var(--c-accent-teal)' : app.status === 'Beta' ? 'var(--c-accent-blue-l)' : 'var(--c-accent-gold)',
                      border: `1px solid ${app.status === 'Live' ? 'rgba(10,123,108,0.25)' : app.status === 'Beta' ? 'rgba(21,71,190,0.25)' : 'rgba(196,154,42,0.25)'}`,
                      letterSpacing: '0.04em',
                    }}
                  >
                    {app.status.toUpperCase()}
                  </span>
                </div>

                <h3
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: app.featured ? 20 : 16,
                    fontWeight: 600,
                    color: 'var(--c-text-primary)',
                    marginBottom: 4,
                  }}
                >
                  {app.name}
                </h3>
                <p
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 11,
                    color: app.color,
                    fontWeight: 500,
                    marginBottom: 8,
                    letterSpacing: '0.02em',
                  }}
                >
                  {app.tagline}
                </p>
                <p
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: 13.5,
                    color: 'var(--c-text-secondary)',
                    lineHeight: 1.5,
                    flex: 1,
                  }}
                >
                  {app.desc}
                </p>

                <div
                  className="flex items-center gap-1 mt-4 transition-all group-hover:gap-2"
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: 13,
                    fontWeight: 500,
                    color: app.color,
                  }}
                >
                  Explore <span aria-hidden="true">→</span>
                </div>
              </motion.a>
            ))}
            <div className="min-w-[1px] md:hidden snap-center" aria-hidden="true" />
          </div>

          {/* Bottom CTA — stitch card-elegant */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.6, duration: 0.4 }}
            className="mt-10 flex flex-col sm:flex-row items-center justify-between gap-4 p-6 rounded-2xl border"
            style={{ background: 'var(--c-bg-primary)', borderColor: 'var(--c-border)' }}
          >
            <div>
              <p style={{ fontFamily: 'var(--font-heading)', fontSize: 15, fontWeight: 600, color: 'var(--c-text-primary)' }}>
                Need a custom SaaS or PWA like these?
              </p>
              <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--c-text-muted)', marginTop: 2 }}>
                I build production-grade platforms — .NET, Azure, AI. Available for freelance & consulting.
              </p>
            </div>
            <div className="flex gap-3 flex-shrink-0">
              <a
                href="#contact"
                onClick={(e) => {
                  e.preventDefault();
                  document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' });
                }}
                className="px-6 py-2.5 rounded-lg text-sm font-medium transition-all"
                style={{ background: 'var(--c-accent-blue)', color: '#fff', fontFamily: 'var(--font-heading)', textDecoration: 'none' }}
                onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--c-accent-blue-l)'; e.currentTarget.style.boxShadow = 'var(--shadow-glow-blue)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--c-accent-blue)'; e.currentTarget.style.boxShadow = ''; }}
              >
                Start a Project →
              </a>
              <a
                href="https://github.com/rajibmahata"
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-2.5 rounded-lg text-sm font-medium transition-colors"
                style={{ background: 'transparent', color: 'var(--c-text-secondary)', border: '1px solid var(--c-border)', fontFamily: 'var(--font-heading)', textDecoration: 'none' }}
              >
                View GitHub
              </a>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
