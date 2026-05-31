import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import TechChip from '../ui/TechChip';
import Button from '../ui/Button';

const careerEntries = [
  {
    company: 'Tata Consultancy Services',
    role: 'Assistant Consultant',
    period: 'Aug 2019 – Present',
    client: 'Meijer Inc. — Fortune 500 Retail (Michigan, USA)',
    achievements: [
      'Led development of open APIs, reducing pharmacy vendor dependency by 100%',
      'Automated Prescription Refill System — 30% faster processing, 40% fewer medication errors',
      'Vaccine Appointment System — streamlined COVID-19 immunization scheduling nationally',
      'Built Rule Engine on Azure PaaS processing 500K+ daily prescription events',
      'Integrated MParks secure payment, barcode scanning, voice/SMS notifications',
    ],
    techStack: ['.NET 8', 'Blazor', 'Azure Functions', 'Logic Apps', 'Service Bus', 'Event Grid', 'Cosmos DB', 'AngularJS'],
    color: 'var(--c-accent-blue)',
  },
  {
    company: 'Accenture',
    role: 'Software Developer',
    period: 'Jul 2016 – Feb 2019',
    client: 'Cincinnati Bell Inc. — Telecom (Ohio, USA)',
    achievements: [
      'Designed and built CMT application automating network equipment provisioning',
      'Reduced manual intervention by 30%, processing time by 40%',
      'Achieved 95% issue resolution within 24 hours via automated ticket system',
      'Built intuitive UI improving user satisfaction scores by 25%',
    ],
    techStack: ['ASP.NET MVC', 'WCF', 'Entity Framework', 'SQL Server', 'JavaScript'],
    color: 'var(--c-accent-teal)',
  },
  {
    company: 'Keshri Software Solutions',
    role: 'Web Developer',
    period: 'Mar 2013 – Apr 2016',
    achievements: [
      'Built Corporate Hour — B2B media advertisement & trade platform',
      'Developed Cinematic Lens — product visual storytelling platform',
      'Created TRANSZOOM — car rental & TruckIt365 freight matching solution',
      'Full-stack ownership: database design to frontend deployment',
    ],
    techStack: ['ASP.NET MVC', 'SQL Server', 'JavaScript', 'HTML/CSS', 'AJAX'],
    color: 'var(--c-accent-gold)',
  },
];

export default function LinkedInSection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  return (
    <section className="section-pad" ref={sectionRef}>
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
                      <p style={{
                        fontFamily: 'var(--font-body)',
                        fontSize: 13,
                        color: 'var(--c-text-muted)',
                        marginTop: 2,
                      }}>
                        {entry.client}
                      </p>
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
