import { motion } from 'framer-motion';
import { siteConfig } from '../../config/site';

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
      id="hero"
      className="relative min-h-[820px] flex items-center justify-center px-6 py-28 md:py-36 overflow-hidden grain"
      style={{ paddingTop: 72 }}
    >
      <div className="hero-glow" aria-hidden="true" />
      <div className="absolute inset-0 ambient-mesh opacity-35 pointer-events-none" aria-hidden="true" />
      <div className="absolute inset-0 bg-grid-pattern opacity-[0.16] pointer-events-none" aria-hidden="true" />
      <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/[0.06] to-transparent pointer-events-none" aria-hidden="true" />

      <div className="max-w-[1200px] mx-auto w-full text-center z-10">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.06, duration: 0.55 }}
          className="inline-flex items-center gap-2.5 bg-surface-inset/80 backdrop-blur px-4 py-2 rounded-full border border-border-subtle mb-8 shadow-sm"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-whatsapp opacity-30" style={{ background: '#25D366' }} />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-whatsapp" style={{ background: '#25D366' }} />
          </span>
          <span className="font-tech-chip text-[11px] text-text-secondary uppercase tracking-[0.14em]" style={{ fontFamily: 'JetBrains Mono, monospace' }}>
            Available for New Projects · Rajib Mahata
          </span>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.10, duration: 0.5 }}
          className="mb-4"
        >
          <span className="text-[13px] tracking-[0.14em] uppercase" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#eec04e', letterSpacing: '0.14em' }}>
            Rajib Mahata — Senior Software Architect
          </span>
          <div className="text-[13px] mt-1" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6A7B9E', letterSpacing: '0.06em' }}>
            .NET • Azure • AI/GenAI • Product Engineering
          </div>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.14, duration: 0.65 }}
          className="font-display-hero-mobile md:font-display-hero text-[40px] md:text-[72px] text-gradient mb-6 max-w-4xl mx-auto"
          style={{ fontFamily: 'Fraunces, serif', fontWeight: 700, lineHeight: 0.98, letterSpacing: '-0.045em' }}
        >
          Premium Software
          <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-tertiary italic font-medium" style={{ backgroundImage: 'linear-gradient(135deg, #b5c4ff 10%, #7bd7c5 92%)', WebkitBackgroundClip: 'text', letterSpacing: '-0.035em' }}>
            Architecture Studio
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.24, duration: 0.6 }}
          className="font-body-large text-[17px] md:text-[18px] text-text-muted max-w-2xl mx-auto mb-10"
          style={{ fontFamily: 'DM Sans, sans-serif', fontWeight: 300, lineHeight: 1.75, color: '#8896B3', letterSpacing: '0.01em' }}
        >
          I design and build enterprise software, cloud-native platforms, AI/GenAI products and SaaS systems — 10+ years, 500K+ daily events, 30% faster, 40% fewer errors.
        </motion.p>

        {/* Primary CTAs — stitch */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.34, duration: 0.5 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-8"
        >
          <a
            href="#projects"
            onClick={e => { e.preventDefault(); scrollTo('projects'); }}
            className="w-full sm:w-auto bg-primary-container text-white px-8 py-3.5 rounded-full font-body-base hover:bg-accent-blue-hover transition-all flex items-center justify-center gap-2 shadow-[0_8px_24px_rgba(21,71,190,0.28)] hover:shadow-[0_12px_32px_rgba(21,71,190,0.36)] hover:-translate-y-px"
            style={{ background: '#1547be', fontFamily: 'DM Sans, sans-serif' }}
          >
            View My Work <span className="material-symbols-outlined text-sm">arrow_downward</span>
          </a>
          <a
            href="#contact"
            onClick={e => { e.preventDefault(); scrollTo('contact'); }}
            className="w-full sm:w-auto border border-border-subtle text-text-primary px-8 py-3.5 rounded-full font-body-base hover:border-primary/30 hover:text-primary transition-all flex items-center justify-center backdrop-blur"
            style={{ borderColor: 'rgba(30,45,74,0.9)', fontFamily: 'DM Sans, sans-serif', background: 'rgba(255,255,255,0.02)' }}
          >
            Let's Build Something
          </a>
        </motion.div>

        {/* Secondary — WhatsApp / Call / CV (preserve existing functionality) */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.44, duration: 0.5 }}
          className="flex flex-wrap items-center justify-center gap-3 mb-8"
        >
          <a
            href={siteConfig.whatsappLink}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-medium transition-all"
            style={{ background: '#25D366', color: '#fff', fontFamily: 'DM Sans, sans-serif' }}
          >
            <span className="material-symbols-outlined text-[18px]">chat</span> WhatsApp
          </a>
          <a
            href={siteConfig.callLink}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-medium border transition-all"
            style={{ background: 'transparent', color: '#F0F4FF', borderColor: '#1E2D4A', fontFamily: 'DM Sans, sans-serif' }}
          >
            <span className="material-symbols-outlined text-[18px]">call</span> {siteConfig.contact.phone}
          </a>
          <a
            href="/Rajib-Mahata-Resume-2026.pdf"
            download
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-medium border transition-all"
            style={{ borderColor: '#eec04e', color: '#eec04e', fontFamily: 'DM Sans, sans-serif' }}
          >
            <span className="material-symbols-outlined text-[18px]">download</span> Download CV
          </a>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.54, duration: 0.5 }}
          className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-[11px] font-medium"
          style={{ fontFamily: 'JetBrains Mono, monospace', color: '#eec04e', letterSpacing: '0.05em' }}
        >
          <span>30% faster processing</span>
          <span style={{ color: '#1E2D4A' }}>|</span>
          <span>40% fewer errors</span>
          <span style={{ color: '#1E2D4A' }}>|</span>
          <span>25% higher satisfaction</span>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.5 }}
          className="mt-8 flex flex-col items-center gap-2"
        >
          <a
            href={`mailto:${siteConfig.contact.email}`}
            className="font-mono text-[13px] hover:text-primary transition-colors"
            style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6A7B9E' }}
          >
            {siteConfig.contact.email}
          </a>
          <span className="font-mono text-[11px]" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6A7B9E', letterSpacing: '0.06em' }}>
            {productCount} products · {companyCount} enterprises · 500K+ events/day
          </span>
        </motion.div>
      </div>
    </section>
  );
}
