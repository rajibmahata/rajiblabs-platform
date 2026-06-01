import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import TechChip from '../ui/TechChip';

const timeline = [
  {
    company: 'TCS',
    role: 'Assistant Consultant',
    period: '2019 – Present',
    client: 'TCS (Healthcare, USA)',
    color: 'var(--c-accent-blue)',
  },
  {
    company: 'Accenture',
    role: 'Software Developer',
    period: '2016 – 2019',
    client: 'Accenture (Telecom, USA)',
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
            {/* Avatar — styled dark gradient initials */}
            <div
              className="w-40 h-40 md:w-48 md:h-48 flex items-center justify-center mb-6 relative"
              style={{
                border: '2px solid var(--c-border)',
                borderRadius: 'var(--radius-xl)',
                background: 'linear-gradient(135deg, #080D1A 0%, #1547BE 100%)',
                boxShadow: '0 0 60px rgba(21,71,190,0.25)',
              }}
            >
              <span style={{
                fontFamily: 'var(--font-display)',
                fontSize: 52,
                fontWeight: 700,
                color: '#fff',
                textShadow: '0 2px 8px rgba(0,0,0,0.3)',
                letterSpacing: '0.02em',
              }}>
                RM
              </span>
              {/* Gold accent dot */}
              <div style={{
                position: 'absolute',
                bottom: 14,
                right: 14,
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: 'var(--c-accent-gold)',
                boxShadow: '0 0 8px rgba(196,154,42,0.6)',
              }} />
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
                { label: '↓ Download Resume (PDF)', href: '/Resume-RajibMahata.pdf', download: true },
              ].map(link => (
                <a
                  key={link.label}
                  href={link.href}
                  target={link.href.startsWith('http') ? '_blank' : undefined}
                  rel={link.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                  download={link.download ? '' : undefined}
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
                I'm Rajib Mahata — a Senior .NET and Azure Engineer based in Kolkata, with a B.Tech in Computer Science and 12 years of experience shipping production software for enterprise clients. I started building web applications at Keshri Software Solutions in 2013, moved to Accenture in 2016 where I modernised telecom platforms for a major US telecommunications provider, and since 2019 I've been at TCS as an Assistant Consultant, leading the digital transformation of a Fortune 500 pharmacy chain in the United States.
              </p>
              <p style={{
                fontFamily: 'var(--font-body)',
                fontSize: 16,
                lineHeight: 'var(--lh-body)',
                color: 'var(--c-text-secondary)',
                marginBottom: 12,
              }}>
                The work I'm most proud of is the pharmacy transformation platform I architected at TCS — an Azure-hosted automation system that eliminated manual phone calls for prescription refills, achieved 30% faster processing, reduced medication errors by 40%, and improved patient satisfaction scores by 25%. It ran nationally during the COVID-19 vaccine rollout. That kind of measurable, mission-critical impact is what I build towards.
              </p>
              <p style={{
                fontFamily: 'var(--font-body)',
                fontSize: 16,
                lineHeight: 'var(--lh-body)',
                color: 'var(--c-text-secondary)',
              }}>
                RajibLabs is my independent engineering studio where I build AI-powered SaaS products and experiment with new technologies purely for learning. My current products — DocSignerHub (enterprise e-signing) and ARIA (AI knowledge platform) — are live and available. If you have an interesting technical idea or want to connect, let's talk.
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
