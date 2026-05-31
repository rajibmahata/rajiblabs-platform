import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import TechChip from '../ui/TechChip';

const careerEntries = [
  {
    company: 'TCS · Assistant Consultant',
    period: 'Aug 2019 – Present',
    client: 'Meijer Inc. (Healthcare, USA)',
    achievements: [
      'Pharmacy Business Transformation — Azure PaaS, Blazor',
      'Automated Refill System — 30% faster, 40% fewer errors',
      'Vaccine Appointment System — COVID-19 national rollout',
    ],
    techStack: ['.NET 8', 'Azure', 'Blazor', 'Cosmos DB', 'Service Bus'],
    color: 'var(--c-accent-blue)',
  },
  {
    company: 'Accenture · Software Developer',
    period: 'Jul 2016 – Feb 2019',
    client: 'Cincinnati Bell (Telecom, USA)',
    achievements: [
      'CMT Platform — 40% less processing time, 95% ticket SLA',
      'Automated order provisioning and network configuration',
    ],
    techStack: ['ASP.NET MVC', 'WCF', 'EF', 'SQL Server'],
    color: 'var(--c-accent-teal)',
  },
  {
    company: 'Keshri Software · Web Developer',
    period: 'Mar 2013 – Apr 2016',
    client: 'Own products: Cinematic Lens, Corporate Hour, TRANSZOOM',
    achievements: [
      'Built complete B2B products from scratch',
      'Full-stack development with MSSQL and JavaScript',
    ],
    techStack: ['ASP.NET MVC', 'SQL Server', 'JavaScript'],
    color: 'var(--c-accent-gold)',
  },
];

export default function LinkedInSection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  return (
    <section className="section-pad" ref={sectionRef}>
      <div className="container-site">
        <div className="flex items-start justify-between">
          <SectionLabel>CAREER EXPERIENCE</SectionLabel>
          <a
            href="https://linkedin.com/in/rajib-mahata"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 px-4 py-2 text-xs font-medium rounded-md border transition-all"
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: 13,
              color: 'var(--c-text-secondary)',
              borderColor: 'var(--c-border)',
              borderRadius: 'var(--radius-md)',
              textDecoration: 'none',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.borderColor = 'var(--c-accent-blue)';
              e.currentTarget.style.color = 'var(--c-text-primary)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.borderColor = 'var(--c-border)';
              e.currentTarget.style.color = 'var(--c-text-secondary)';
            }}
          >
            View Full Profile ↗
          </a>
        </div>

        <div className="mt-8 relative">
          {/* Vertical timeline line */}
          <div className="absolute left-[11px] top-2 bottom-2 w-0.5 hidden sm:block"
            style={{ background: 'var(--c-border)' }}
          />

          <div className="space-y-10">
            {careerEntries.map((entry, i) => (
              <motion.div
                key={entry.company}
                initial={{ opacity: 0, x: -30 }}
                animate={inView ? { opacity: 1, x: 0 } : {}}
                transition={{ delay: i * 0.15, duration: 0.5 }}
                className="relative pl-8 sm:pl-12"
              >
                {/* Timeline node */}
                <div
                  className="absolute left-[4px] sm:left-[4px] top-2 w-4 h-4 rounded-full border-2 z-10 hidden sm:block"
                  style={{
                    backgroundColor: 'var(--c-bg-primary)',
                    borderColor: entry.color,
                  }}
                />

                {/* Content */}
                <div className="card p-5 sm:p-6">
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-1 mb-3">
                    <div>
                      <h3 style={{
                        fontFamily: 'var(--font-heading)',
                        fontSize: 17,
                        fontWeight: 600,
                        color: 'var(--c-text-primary)',
                      }}>
                        {entry.company}
                      </h3>
                      <p style={{
                        fontFamily: 'var(--font-heading)',
                        fontSize: 15,
                        fontWeight: 400,
                        color: 'var(--c-text-secondary)',
                      }}>
                        {entry.client}
                      </p>
                    </div>
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 13,
                      color: 'var(--c-text-muted)',
                      flexShrink: 0,
                    }}>
                      {entry.period}
                    </span>
                  </div>

                  {/* Achievements */}
                  <ul className="space-y-2 mb-4">
                    {entry.achievements.map((ach, j) => {
                      // Highlight metric numbers
                      const parts = ach.split(/(\d+%?)/g);
                      return (
                        <li key={j} style={{
                          fontFamily: 'var(--font-body)',
                          fontSize: 14,
                          color: 'var(--c-text-secondary)',
                          lineHeight: 'var(--lh-compact)',
                          paddingLeft: 16,
                          position: 'relative',
                        }}>
                          <span className="absolute left-0" style={{ color: entry.color }}>•</span>
                          {parts.map((part, k) =>
                            /\d+%?/.test(part) ? (
                              <strong key={k} style={{
                                color: 'var(--c-accent-teal)',
                                fontWeight: 600,
                              }}>
                                {part}
                              </strong>
                            ) : (
                              part
                            )
                          )}
                        </li>
                      );
                    })}
                  </ul>

                  {/* Tech stack chips */}
                  <div className="flex flex-wrap gap-1.5">
                    {entry.techStack.map(tech => (
                      <TechChip key={tech} label={tech} category="backend" />
                    ))}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
