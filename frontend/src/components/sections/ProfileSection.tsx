import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import TechChip from '../ui/TechChip';

const timeline = [
  {
    company: 'Fortune 500 Healthcare',
    role: 'Solutions Architect',
    period: '2019 – Present',
    client: 'Pharmacy & Healthcare (USA)',
    color: 'var(--c-accent-blue)',
    highlight: 'Led platform processing 500K+ daily events',
  },
  {
    company: 'Telecom Enterprise',
    role: 'Platform Engineer',
    period: '2016 – 2019',
    client: 'Telecommunications (USA)',
    color: 'var(--c-accent-teal)',
    highlight: '30% less manual work, 40% faster processing',
  },
  {
    company: 'Product Studio',
    role: 'Full-Stack Developer',
    period: '2013 – 2016',
    client: 'B2B & Logistics Platforms',
    color: 'var(--c-accent-gold)',
    highlight: 'Built 4 products from concept to deployment',
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
    <section id="about" className="section-pad" ref={sectionRef}
      style={{ background: 'var(--c-bg-primary)' }}
    >
      <div className="container-site">
        <SectionLabel>ABOUT</SectionLabel>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-10 md:gap-16"
        >
          {/* LEFT — Identity Card */}
          <div>
            {/* Avatar */}
            <div
              className="w-44 h-44 flex items-center justify-center relative mb-6 mx-auto md:mx-0"
              style={{
                border: '1.5px solid var(--c-border)',
                borderRadius: 'var(--radius-xl)',
                background: 'linear-gradient(135deg, #080D1A 0%, #1547BE 100%)',
                boxShadow: '0 0 80px rgba(21,71,190,0.2)',
              }}
            >
              <span style={{
                fontFamily: 'var(--font-display)',
                fontSize: 48,
                fontWeight: 700,
                color: '#fff',
                textShadow: '0 2px 12px rgba(0,0,0,0.3)',
                letterSpacing: '0.04em',
              }}>
                RM
              </span>
              <div style={{
                position: 'absolute', bottom: 14, right: 14,
                width: 8, height: 8, borderRadius: '50%',
                backgroundColor: 'var(--c-accent-gold)',
                boxShadow: '0 0 10px rgba(196,154,42,0.6)',
              }} />
            </div>

            <div className="text-center md:text-left">
              <h3 style={{
                fontFamily: 'var(--font-display)',
                fontSize: 26,
                fontWeight: 700,
                color: 'var(--c-text-primary)',
                marginBottom: 4,
              }}>
                Rajib Mahata
              </h3>
              <p style={{
                fontFamily: 'var(--font-body)',
                fontSize: 15,
                color: 'var(--c-accent-blue-l)',
                marginBottom: 4,
              }}>
                Senior .NET &amp; Azure Engineer
              </p>
              <p style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 12,
                color: 'var(--c-text-muted)',
                marginBottom: 20,
              }}>
                Kolkata, India · Remote-first
              </p>

              {/* Quick stats */}
              <div className="grid grid-cols-2 gap-3 mb-6">
                {[
                  { value: '12+', label: 'Years' },
                  { value: '30+', label: 'Repos' },
                  { value: '6', label: 'Products' },
                  { value: '3', label: 'Enterprises' },
                ].map(stat => (
                  <div key={stat.label} className="card p-3 text-center"
                    style={{ background: 'rgba(13, 31, 60, 0.5)' }}
                  >
                    <div style={{
                      fontFamily: 'var(--font-mono)', fontSize: 20, fontWeight: 700,
                      color: 'var(--c-accent-gold)', lineHeight: 1,
                    }}>
                      {stat.value}
                    </div>
                    <div style={{
                      fontFamily: 'var(--font-body)', fontSize: 11,
                      color: 'var(--c-text-muted)', marginTop: 2,
                    }}>
                      {stat.label}
                    </div>
                  </div>
                ))}
              </div>

              {/* Links */}
              <div className="flex flex-wrap gap-2">
                {[
                  { label: 'LinkedIn', href: 'https://linkedin.com/in/rajib-mahata' },
                  { label: 'GitHub', href: 'https://github.com/rajibmahata' },
                  { label: 'Resume (PDF)', href: '/Resume-RajibMahata.pdf', download: true },
                ].map(link => (
                  <a
                    key={link.label}
                    href={link.href}
                    target={link.href.startsWith('http') ? '_blank' : undefined}
                    rel={link.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                    download={link.download ? '' : undefined}
                    className="inline-flex items-center px-4 py-2 rounded-md border transition-all text-xs"
                    style={{
                      fontFamily: 'var(--font-body)', fontSize: 12,
                      borderColor: 'var(--c-border)', color: 'var(--c-text-secondary)',
                      borderRadius: 'var(--radius-md)', textDecoration: 'none',
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.borderColor = 'var(--c-accent-blue)';
                      e.currentTarget.style.color = 'var(--c-text-primary)';
                      e.currentTarget.style.background = 'rgba(21,71,190,0.08)';
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.borderColor = 'var(--c-border)';
                      e.currentTarget.style.color = 'var(--c-text-secondary)';
                      e.currentTarget.style.background = 'transparent';
                    }}
                  >
                    {link.label}
                  </a>
                ))}
              </div>
            </div>
          </div>

          {/* RIGHT — Career + Tech */}
          <div className="md:col-span-2 space-y-10">
            {/* Bio */}
            <div>
              <p style={{
                fontFamily: 'var(--font-body)', fontSize: 16,
                lineHeight: 'var(--lh-body)', color: 'var(--c-text-secondary)',
                marginBottom: 12,
              }}>
                Independent software architect with 12+ years building production systems
                for Fortune 500 and enterprise clients. I specialise in .NET, Azure cloud,
                and AI/LLM integrations — delivering measurable impact: 30% faster processing,
                40% fewer errors, 25% higher satisfaction on a national pharmacy platform
                that ran during the COVID-19 vaccine rollout.
              </p>
              <p style={{
                fontFamily: 'var(--font-body)', fontSize: 16,
                lineHeight: 'var(--lh-body)', color: 'var(--c-text-secondary)',
              }}>
                RajibLabs is my independent engineering studio where I build AI-powered
                SaaS products and collaborate with clients worldwide. Available for
                consulting, architecture, and development — remote-first, global delivery.
              </p>
            </div>

            {/* Experience Timeline — cards style */}
            <div>
              <h3 style={{
                fontFamily: 'var(--font-heading)', fontSize: 14, fontWeight: 600,
                color: 'var(--c-text-muted)', textTransform: 'uppercase',
                letterSpacing: '0.06em', marginBottom: 16,
              }}>
                Career
              </h3>
              <div className="space-y-3">
                {timeline.map((item, i) => (
                  <motion.div
                    key={item.company}
                    initial={{ opacity: 0, x: -12 }}
                    animate={inView ? { opacity: 1, x: 0 } : {}}
                    transition={{ delay: 0.1 * i, duration: 0.4 }}
                    className="card p-4 group"
                    style={{
                      borderLeft: `3px solid ${item.color}`,
                      background: 'linear-gradient(90deg, rgba(13,31,60,0.6), transparent)',
                      transition: 'all 250ms var(--ease-spring)',
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.transform = 'translateX(4px)';
                      e.currentTarget.style.boxShadow = 'var(--shadow-md)';
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.transform = 'translateX(0)';
                      e.currentTarget.style.boxShadow = '';
                    }}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 mb-2">
                      <div className="flex items-center gap-3">
                        <span style={{
                          fontFamily: 'var(--font-heading)', fontSize: 16, fontWeight: 600,
                          color: 'var(--c-text-primary)',
                        }}>
                          {item.company}
                        </span>
                        <span style={{
                          fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--c-text-muted)',
                        }}>
                          {item.period}
                        </span>
                      </div>
                      <span style={{
                        fontFamily: 'var(--font-mono)', fontSize: 11,
                        color: item.color, fontWeight: 500,
                        padding: '2px 8px', borderRadius: 'var(--radius-sm)',
                        background: `${item.color}15`,
                      }}>
                        {item.role}
                      </span>
                    </div>
                    <p style={{
                      fontFamily: 'var(--font-body)', fontSize: 13,
                      color: 'var(--c-text-secondary)',
                    }}>
                      {item.client}
                    </p>
                    <p style={{
                      fontFamily: 'var(--font-mono)', fontSize: 12,
                      color: 'var(--c-text-muted)', marginTop: 4,
                    }}>
                      {item.highlight}
                    </p>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Tech Stack */}
            <div>
              <h3 style={{
                fontFamily: 'var(--font-heading)', fontSize: 14, fontWeight: 600,
                color: 'var(--c-text-muted)', textTransform: 'uppercase',
                letterSpacing: '0.06em', marginBottom: 16,
              }}>
                Technology
              </h3>
              <div className="space-y-4">
                {techCategories.map(group => (
                  <div key={group.label}>
                    <p style={{
                      fontFamily: 'var(--font-mono)', fontSize: 10,
                      color: 'var(--c-text-muted)', textTransform: 'uppercase',
                      letterSpacing: '0.06em', marginBottom: 6,
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
