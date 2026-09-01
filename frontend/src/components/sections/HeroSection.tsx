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
      className="relative min-h-[819px] flex items-center justify-center px-6 py-24 md:py-32 overflow-hidden"
      style={{ paddingTop: 72 }}
    >
      <div className="hero-glow" aria-hidden="true" />
      <div className="absolute inset-0 ambient-mesh opacity-40 pointer-events-none" aria-hidden="true" />
      <div className="absolute inset-0 bg-grid-pattern opacity-20 pointer-events-none" aria-hidden="true" />

      <div className="max-w-[1200px] mx-auto w-full text-center z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05, duration: 0.5 }}
          className="inline-flex items-center gap-2 bg-surface-inset px-4 py-1.5 rounded-full border border-border-subtle mb-8"
        >
          <span className="w-2 h-2 rounded-full bg-whatsapp animate-pulse" style={{ background: '#25D366' }} />
          <span className="font-tech-chip text-[11px] text-text-secondary uppercase tracking-widest" style={{ fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.10em' }}>
            Available for New Projects
          </span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.12, duration: 0.6 }}
          className="font-display-hero-mobile md:font-display-hero text-[42px] md:text-[72px] text-gradient mb-6 max-w-4xl mx-auto"
          style={{ fontFamily: 'Fraunces, serif', fontWeight: 700, lineHeight: 1.02, letterSpacing: '-0.04em' }}
        >
          Architecting
          <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-tertiary italic font-medium" style={{ backgroundImage: 'linear-gradient(135deg, #b5c4ff, #7bd7c5)', WebkitBackgroundClip: 'text', letterSpacing: '-0.03em' }}>
            Scalable Intelligence
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.22, duration: 0.6 }}
          className="font-body-large text-[18px] text-text-muted max-w-2xl mx-auto mb-10"
          style={{ fontFamily: 'DM Sans, sans-serif', fontWeight: 300, lineHeight: 1.7, color: '#6A7B9E' }}
        >
          Senior .NET &amp; Azure Architect bridging the gap between high-performance backend systems and next-generation AI integrations.
          <span className="hidden md:inline"> 12+ years delivering platforms processing 500K+ daily events — 30% faster, 40% fewer errors.</span>
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
            className="w-full sm:w-auto bg-primary-container text-white px-8 py-3 rounded-full font-body-base hover:bg-accent-blue-hover transition-colors flex items-center justify-center gap-2"
            style={{ background: '#1547be', fontFamily: 'DM Sans, sans-serif' }}
          >
            View Work <span className="material-symbols-outlined text-sm">arrow_downward</span>
          </a>
          <a
            href="#about"
            onClick={e => { e.preventDefault(); scrollTo('about'); }}
            className="w-full sm:w-auto border border-border-subtle text-text-primary px-8 py-3 rounded-full font-body-base hover:border-primary-container hover:text-primary-container transition-all flex items-center justify-center"
            style={{ borderColor: '#1E2D4A', fontFamily: 'DM Sans, sans-serif' }}
          >
            About Me
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
            href="/Resume-RajibMahata.pdf"
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
