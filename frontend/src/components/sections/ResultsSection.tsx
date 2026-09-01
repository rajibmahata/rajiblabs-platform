import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';

const outcomes = [
  { metric: '30%', label: 'Faster Processing', description: 'Automated pharmacy refill system eliminated manual phone calls for Fortune 500 healthcare.', icon: 'bolt', color: '#b5c4ff' },
  { metric: '40%', label: 'Fewer Medication Errors', description: 'Rule engine processing 500K+ daily events with CQRS on Azure — zero-tolerance.', icon: 'shield', color: '#7bd7c5' },
  { metric: '25%', label: 'Higher Patient Satisfaction', description: 'PWA pharmacy interfaces with barcode scanning and secure payment.', icon: 'star', color: '#eec04e' },
  { metric: '100%', label: 'Vendor Independence', description: 'Open API architecture eliminated vendor lock-in. Complete data sovereignty.', icon: 'lock_open', color: '#b5c4ff' },
  { metric: '95%', label: 'Issue Resolution in 24hrs', description: 'Automated ticket system for telecom provisioning. 30% less manual work.', icon: 'target', color: '#7bd7c5' },
  { metric: '6', label: 'Active Products', description: 'DocSignerHub, ARIA, LexVault, AI Tutor, Solicitor CMS, RajibLabs — .NET & AI.', icon: 'rocket', color: '#eec04e' },
];

const impactStats = [
  { value: '15+', label: 'Years Experience' },
  { value: '99.99%', label: 'Uptime Architected' },
  { value: '10M+', label: 'Users Supported' },
  { value: 'Azure', label: 'Certified Architect' },
];

export default function ResultsSection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  return (
    <section id="results" ref={sectionRef} className="relative">
      {/* Impact & Scale — stitch border-y */}
      <div className="px-6 py-12 border-y border-border-subtle bg-surface-container-lowest/30" style={{ borderColor: '#1E2D4A', background: 'rgba(9,14,27,0.3)' }}>
        <div className="max-w-[1200px] mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 divide-x-0 md:divide-x divide-border-subtle" style={{ borderColor: '#1E2D4A' }}>
            {impactStats.map(stat => (
              <div key={stat.label} className="text-center px-4">
                <div className="font-telemetry-stat text-[32px] text-primary-container mb-2" style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: '#1547be' }}>{stat.value}</div>
                <div className="font-label-caps text-[11px] text-text-muted uppercase tracking-widest" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6A7B9E' }}>{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="section-pad" style={{ background: 'var(--c-surface)' }}>
        <div className="container-site">
          <SectionLabel>PROVEN RESULTS</SectionLabel>
          <motion.div initial={{ opacity: 0, y: 30 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.5 }}>
            <div className="mb-12">
              <h2 className="font-section-title text-[42px] text-on-surface mb-3" style={{ fontFamily: 'Fraunces, serif', fontWeight: 700, color: '#F0F4FF', lineHeight: 1.1 }}>
                Real impact. <span style={{ color: '#8896B3', fontWeight: 400 }}>Measurable outcomes.</span>
              </h2>
              <p className="font-body-base text-text-secondary max-w-xl" style={{ fontFamily: 'DM Sans, sans-serif', color: '#8896B3' }}>
                Every project I deliver leaves a measurable footprint. Here's what that looks like for the businesses I've worked with.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {outcomes.map((item, i) => (
                <motion.div
                  key={item.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={inView ? { opacity: 1, y: 0 } : {}}
                  transition={{ delay: 0.1 + i * 0.08, duration: 0.5 }}
                  className="glass-card rounded-xl p-6 group hover-lift"
                >
                  <div className="flex items-start gap-4 mb-3">
                    <span className="w-10 h-10 rounded-lg bg-surface-inset flex items-center justify-center border border-border-subtle shrink-0" style={{ borderColor: '#1E2D4A' }}>
                      <span className="material-symbols-outlined text-[20px]" style={{ color: item.color }}>{item.icon}</span>
                    </span>
                    <div>
                      <div className="font-telemetry-stat text-[32px] leading-none mb-1" style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: item.color }}>{item.metric}</div>
                      <div className="font-card-heading text-[14px] font-semibold text-on-surface" style={{ fontFamily: 'DM Sans, sans-serif', color: '#F0F4FF' }}>{item.label}</div>
                    </div>
                  </div>
                  <p className="font-body-compact text-[14px] text-text-secondary" style={{ fontFamily: 'DM Sans, sans-serif', color: '#8896B3', lineHeight: 1.5 }}>{item.description}</p>
                </motion.div>
              ))}
            </div>

            <motion.div initial={{ opacity: 0, y: 16 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ delay: 0.6, duration: 0.5 }} className="text-center mt-10">
              <p className="font-body-base text-text-muted mb-4" style={{ fontFamily: 'DM Sans, sans-serif', color: '#6A7B9E' }}>Want results like these for your business?</p>
              <a
                href="#contact"
                onClick={e => { e.preventDefault(); document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' }); }}
                className="inline-flex items-center px-8 py-3 text-[15px] font-medium rounded-full transition-all duration-200"
                style={{ fontFamily: 'DM Sans, sans-serif', background: '#1547be', color: '#fff', borderRadius: '999px' }}
              >
                Let's Talk <span className="material-symbols-outlined text-sm ml-1">arrow_forward</span>
              </a>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
