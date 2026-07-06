import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';

const outcomes = [
  {
    metric: '30%',
    label: 'Faster Processing',
    description: 'Automated pharmacy prescription refill system eliminated manual phone calls for a Fortune 500 healthcare client.',
    icon: '⚡',
    color: 'var(--c-accent-blue)',
  },
  {
    metric: '40%',
    label: 'Fewer Medication Errors',
    description: 'Rule engine processing 500K+ daily prescription events with CQRS on Azure PaaS — zero-tolerance for mistakes.',
    icon: '🛡️',
    color: 'var(--c-accent-teal)',
  },
  {
    metric: '25%',
    label: 'Higher Patient Satisfaction',
    description: 'PWA pharmacy interfaces with barcode scanning, secure payment integration, and voice/SMS notifications.',
    icon: '⭐',
    color: 'var(--c-accent-gold)',
  },
  {
    metric: '100%',
    label: 'Vendor Independence',
    description: 'Open API architecture eliminated external pharmacy vendor lock-in. Complete data sovereignty for the client.',
    icon: '🔓',
    color: 'var(--c-accent-blue)',
  },
  {
    metric: '95%',
    label: 'Issue Resolution in 24hrs',
    description: 'Automated ticket system for telecom network equipment provisioning. 30% less manual work, 40% faster processing.',
    icon: '🎯',
    color: 'var(--c-accent-teal)',
  },
  {
    metric: '6',
    label: 'Active Products',
    description: 'DocSignerHub, ARIA, LexVault, AI Tutor, Solicitor CMS, and RajibLabs — built with .NET, Python, and AI tooling.',
    icon: '🚀',
    color: 'var(--c-accent-gold)',
  },
];

export default function ResultsSection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  return (
    <section id="results" className="section-pad" ref={sectionRef}
      style={{ background: 'var(--c-bg-secondary)' }}
    >
      <div className="container-site">
        <SectionLabel>PROVEN RESULTS</SectionLabel>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
        >
          {/* Section header */}
          <div className="mb-12">
            <h2 style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'clamp(28px, 3.5vw, 42px)',
              fontWeight: 700,
              color: 'var(--c-text-primary)',
              lineHeight: 'var(--lh-display)',
              marginBottom: 12,
            }}>
              Real impact.{' '}
              <span style={{ color: 'var(--c-text-secondary)', fontWeight: 400 }}>Measurable outcomes.</span>
            </h2>
            <p style={{
              fontFamily: 'var(--font-body)',
              fontSize: 16,
              color: 'var(--c-text-secondary)',
              lineHeight: 'var(--lh-body)',
              maxWidth: 560,
            }}>
              Every project I deliver leaves a measurable footprint. Here's what that looks like for the businesses I've worked with.
            </p>
          </div>

          {/* Outcomes Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {outcomes.map((item, i) => (
              <motion.div
                key={item.label}
                initial={{ opacity: 0, y: 20 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: 0.1 + i * 0.08, duration: 0.5 }}
                className="card p-6 group"
                style={{ transition: 'all 250ms var(--ease-spring)' }}
                onMouseEnter={e => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.boxShadow = 'var(--shadow-lg)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '';
                }}
              >
                {/* Icon + Metric */}
                <div className="flex items-start gap-4 mb-3">
                  <span style={{ fontSize: 32 }}>{item.icon}</span>
                  <div>
                    <div style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 36,
                      fontWeight: 700,
                      color: item.color,
                      lineHeight: 1,
                      marginBottom: 2,
                    }}>
                      {item.metric}
                    </div>
                    <div style={{
                      fontFamily: 'var(--font-heading)',
                      fontSize: 14,
                      fontWeight: 600,
                      color: 'var(--c-text-primary)',
                    }}>
                      {item.label}
                    </div>
                  </div>
                </div>
                <p style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: 14,
                  color: 'var(--c-text-muted)',
                  lineHeight: 'var(--lh-compact)',
                }}>
                  {item.description}
                </p>
              </motion.div>
            ))}
          </div>

          {/* Bottom CTA */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.6, duration: 0.5 }}
            className="text-center mt-10"
          >
            <p style={{
              fontFamily: 'var(--font-body)',
              fontSize: 15,
              color: 'var(--c-text-muted)',
              marginBottom: 16,
            }}>
              Want results like these for your business?
            </p>
            <a
              href="#contact"
              className="inline-flex items-center px-8 py-3.5 text-[15px] font-medium rounded-md transition-all duration-200"
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
              Let's Talk →
            </a>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
