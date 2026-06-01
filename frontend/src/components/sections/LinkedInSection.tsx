import { useEffect, useState, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import TechChip from '../ui/TechChip';
import Button from '../ui/Button';
import { getProfile } from '../../services/api';
import type { CareerEntry } from '../../types';

export default function LinkedInSection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });
  const [careerEntries, setCareerEntries] = useState<CareerEntry[]>([]);

  useEffect(() => {
    let cancelled = false;
    getProfile().then(profile => {
      if (!cancelled && profile.career && profile.career.length > 0) {
        setCareerEntries(profile.career);
      }
    });
    return () => { cancelled = true; };
  }, []);

  if (careerEntries.length === 0) {
    return (
      <section className="section-pad" ref={sectionRef} id="career">
        <div className="container-site">
          <SectionLabel>CAREER EXPERIENCE</SectionLabel>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 14, color: 'var(--c-text-muted)' }}>
            Loading career data…
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="section-pad" ref={sectionRef} id="career">
      <div className="container-site">
        {/* Header — fixed layout, no overlap */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-8">
          <SectionLabel style={{ marginBottom: 0 }}>CAREER EXPERIENCE</SectionLabel>
          <Button variant="ghost" size="sm" asLink href="https://linkedin.com/in/rajib-mahata">
            ↗ View LinkedIn Profile
          </Button>
        </div>

        {/* Timeline */}
        <div className="relative">
          {/* Vertical line — desktop only */}
          <div className="hidden sm:block absolute left-[15px] top-3 bottom-3 w-px"
            style={{ background: 'var(--c-border)' }}
          />

          <div className="space-y-8 sm:space-y-6">
            {careerEntries.map((entry, i) => (
              <motion.div
                key={entry.company}
                initial={{ opacity: 0, x: -20 }}
                animate={inView ? { opacity: 1, x: 0 } : {}}
                transition={{ delay: i * 0.12, duration: 0.4 }}
                className="relative sm:pl-12"
              >
                {/* Timeline node — desktop only */}
                <div
                  className="hidden sm:flex absolute left-[8px] top-5 w-[15px] h-[15px] rounded-full z-10 items-center justify-center"
                  style={{
                    backgroundColor: 'var(--c-bg-primary)',
                    border: `2.5px solid ${entry.color}`,
                  }}
                />

                {/* Card */}
                <div className="card p-5 sm:p-6">
                  {/* Header row */}
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-0.5 mb-3">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 style={{
                          fontFamily: 'var(--font-heading)',
                          fontSize: 17,
                          fontWeight: 600,
                          color: 'var(--c-text-primary)',
                        }}>
                          {entry.company}
                        </h3>
                        <span style={{
                          fontFamily: 'var(--font-body)',
                          fontSize: 14,
                          fontWeight: 400,
                          color: 'var(--c-text-secondary)',
                        }}>
                          · {entry.role}
                        </span>
                      </div>
                      {entry.client && (
                        <p style={{
                          fontFamily: 'var(--font-body)',
                          fontSize: 13,
                          color: 'var(--c-text-muted)',
                          marginTop: 2,
                        }}>
                          {entry.client}
                        </p>
                      )}
                    </div>
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 12,
                      color: 'var(--c-text-muted)',
                      flexShrink: 0,
                      marginTop: 2,
                    }}>
                      {entry.period}
                    </span>
                  </div>

                  {/* Achievements */}
                  <ul className="space-y-1.5 mb-4" style={{ listStyle: 'none' }}>
                    {entry.achievements.map((ach, j) => {
                      const parts = ach.split(/(\d+%?)/g);
                      return (
                        <li key={j} className="flex items-start gap-2"
                          style={{
                            fontFamily: 'var(--font-body)',
                            fontSize: 13.5,
                            color: 'var(--c-text-secondary)',
                            lineHeight: 'var(--lh-compact)',
                          }}
                        >
                          <span style={{ color: entry.color, fontSize: 10, marginTop: 3, flexShrink: 0 }}>◆</span>
                          <span>
                            {parts.map((part, k) =>
                              /\d+%?/.test(part) ? (
                                <strong key={k} style={{ color: 'var(--c-accent-teal)', fontWeight: 600 }}>{part}</strong>
                              ) : part
                            )}
                          </span>
                        </li>
                      );
                    })}
                  </ul>

                  {/* Tech stack */}
                  <div className="flex flex-wrap gap-1.5 pt-3 border-t" style={{ borderColor: 'var(--c-border)' }}>
                    {entry.techStack.map(tech => (
                      <TechChip key={tech} label={tech} category={
                        /azure|cloud|docker/i.test(tech) ? 'cloud' :
                        /angular|javascript|html|css|ajax/i.test(tech) ? 'frontend' : 'backend'
                      } />
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
