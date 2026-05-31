import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import TechChip from '../ui/TechChip';

const timeline = [
  {
    company: 'TCS',
    role: 'Assistant Consultant',
    period: '2019 – Present',
    client: 'Meijer Inc. (Healthcare, USA)',
    color: 'var(--c-accent-blue)',
  },
  {
    company: 'Accenture',
    role: 'Software Developer',
    period: '2016 – 2019',
    client: 'Cincinnati Bell (Telecom, USA)',
    color: 'var(--c-accent-teal)',
  },
  {
    company: 'Keshri Software',
    role: 'Web Developer',
    period: '2013 – 2016',
    client: 'Own Products',
    color: 'var(--c-accent-gold)',
  },
];

const techCategories = [
  {
    label: 'Backend',
    items: ['.NET 8', 'C#', 'ASP.NET Core', 'Blazor', 'Python', 'FastAPI', 'Entity Framework', 'SQL Server', 'Cosmos DB'],
    category: 'backend' as const,
  },
  {
    label: 'Cloud',
    items: ['Azure', 'Service Bus', 'Event Grid', 'Docker', 'CI/CD', 'Key Vault', 'App Service', 'Functions'],
    category: 'cloud' as const,
  },
  {
    label: 'Frontend',
    items: ['React', 'TypeScript', 'JavaScript', 'Tailwind CSS', 'HTML/CSS'],
    category: 'frontend' as const,
  },
  {
    label: 'AI & Tools',
    items: ['AI/RAG', 'OpenAI', 'Gemini', 'LLM Integration', 'Git', 'GitHub Copilot', 'OpenClaw'],
    category: 'ai' as const,
  },
];

export default function ProfileSection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  return (
    <section id="about" className="section-pad" ref={sectionRef}>
      <div className="container-site">
        <SectionLabel>ABOUT RAJIB</SectionLabel>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-10 md:gap-16"
        >
          {/* LEFT — Avatar + Social */}
          <div className="flex flex-col items-center md:items-start">
            {/* Avatar placeholder */}
            <div
              className="w-40 h-40 md:w-48 md:h-48 flex items-center justify-center mb-6"
              style={{
                border: '2px solid var(--c-border)',
                borderRadius: 'var(--radius-xl)',
                background: 'linear-gradient(135deg, var(--c-bg-secondary), var(--c-bg-tertiary))',
              }}
            >
              <span style={{
                fontFamily: 'var(--font-display)',
                fontSize: 48,
                fontWeight: 700,
                color: 'var(--c-accent-gold)',
              }}>
                RM
              </span>
            </div>

            <h3 style={{
              fontFamily: 'var(--font-display)',
              fontSize: 28,
              fontWeight: 700,
              color: 'var(--c-text-primary)',
            }}>
              Rajib Mahata
            </h3>
            <p style={{
              fontFamily: 'var(--font-body)',
              fontSize: 16,
              color: 'var(--c-text-secondary)',
              marginBottom: 16,
            }}>
              Senior .NET &amp; Azure Engineer
            </p>
            <p style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 13,
              color: 'var(--c-text-muted)',
              marginBottom: 20,
            }}>
              Kolkata, India
            </p>

            {/* Social links */}
            <div className="flex flex-wrap gap-2">
              {[
                { label: '↗ LinkedIn', href: 'https://linkedin.com/in/rajib-mahata' },
                { label: '↗ GitHub', href: 'https://github.com/rajibmahata' },
                { label: '↓ Resume', href: '#resume' },
              ].map(link => (
                <a
                  key={link.label}
                  href={link.href}
                  target={link.href.startsWith('http') ? '_blank' : undefined}
                  rel={link.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                  className="inline-flex items-center px-4 py-2 text-xs font-medium rounded-md border transition-all"
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: 13,
                    borderColor: 'var(--c-border)',
                    color: 'var(--c-text-secondary)',
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
                  {link.label}
                </a>
              ))}
            </div>
          </div>

          {/* RIGHT — Bio + Timeline + Tech */}
          <div className="md:col-span-2 space-y-10">
            {/* Bio */}
            <div>
              <p style={{
                fontFamily: 'var(--font-body)',
                fontSize: 16,
                lineHeight: 'var(--lh-body)',
                color: 'var(--c-text-secondary)',
                marginBottom: 12,
              }}>
                B.Tech CSE, West Bengal University of Technology, 2012. 12 years of enterprise software delivery.
                Built systems for Meijer Inc (Fortune 500), Cincinnati Bell, Keshri Software.
              </p>
              <p style={{
                fontFamily: 'var(--font-body)',
                fontSize: 16,
                lineHeight: 'var(--lh-body)',
                color: 'var(--c-text-secondary)',
              }}>
                Now building AI-powered products under RajibLabs: DocSignerHub, ARIA, and more.
              </p>
            </div>

            {/* Experience Timeline */}
            <div>
              <h3 style={{
                fontFamily: 'var(--font-heading)',
                fontSize: 16,
                fontWeight: 600,
                color: 'var(--c-text-primary)',
                marginBottom: 16,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}>
                Experience Timeline
              </h3>
              <div className="flex flex-col sm:flex-row items-center gap-0 sm:gap-0 relative">
                {/* Connector line (desktop) */}
                <div className="hidden sm:block absolute top-5 left-0 right-0 h-0.5"
                  style={{ background: `repeating-linear-gradient(90deg, var(--c-border) 0, var(--c-border) 4px, transparent 4px, transparent 8px)` }}
                />
                {timeline.map((item) => (
                  <div key={item.company} className="relative flex flex-col items-center sm:flex-1 z-10">
                    {/* Node */}
                    <div
                      className="w-3 h-3 rounded-full mb-2 sm:mb-3"
                      style={{ backgroundColor: item.color }}
                    />
                    <div className="text-center">
                      <p style={{
                        fontFamily: 'var(--font-heading)',
                        fontSize: 14,
                        fontWeight: 600,
                        color: 'var(--c-text-primary)',
                      }}>
                        {item.company}
                      </p>
                      <p style={{
                        fontFamily: 'var(--font-body)',
                        fontSize: 12,
                        color: 'var(--c-text-secondary)',
                      }}>
                        {item.period}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Tech Stack */}
            <div>
              <h3 style={{
                fontFamily: 'var(--font-heading)',
                fontSize: 16,
                fontWeight: 600,
                color: 'var(--c-text-primary)',
                marginBottom: 16,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}>
                Tech Stack
              </h3>
              <div className="space-y-4">
                {techCategories.map(group => (
                  <div key={group.label}>
                    <p style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 11,
                      color: 'var(--c-text-muted)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      marginBottom: 6,
                    }}>
                      {group.label}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {group.items.map(t => (
                        <TechChip key={t} label={t} category={group.category} />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
