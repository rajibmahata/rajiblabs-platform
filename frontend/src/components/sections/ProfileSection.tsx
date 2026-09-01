import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import TechChip from '../ui/TechChip';

const timeline = [
  { company: 'Fortune 500 Healthcare', role: 'Solutions Architect', period: '2019 – Present', client: 'Pharmacy & Healthcare (USA)', color: '#1547be', highlight: 'Led platform processing 500K+ daily events' },
  { company: 'Telecom Enterprise', role: 'Platform Engineer', period: '2016 – 2019', client: 'Telecommunications (USA)', color: '#7bd7c5', highlight: '30% less manual work, 40% faster processing' },
  { company: 'Product Studio', role: 'Full-Stack Developer', period: '2013 – 2016', client: 'B2B & Logistics Platforms', color: '#eec04e', highlight: 'Built 4 products from concept to deployment' },
];

const techCategories = [
  { label: 'Backend', items: ['.NET 8', 'C#', 'ASP.NET Core', 'Blazor', 'Python', 'FastAPI', 'Entity Framework', 'SQL Server', 'Cosmos DB'], category: 'backend' as const },
  { label: 'Cloud', items: ['Azure', 'Service Bus', 'Event Grid', 'Docker', 'CI/CD', 'Key Vault', 'App Service', 'Functions'], category: 'cloud' as const },
  { label: 'Frontend', items: ['React', 'TypeScript', 'JavaScript', 'Tailwind CSS', 'HTML/CSS'], category: 'frontend' as const },
  { label: 'AI & Tools', items: ['AI/RAG', 'OpenAI', 'Gemini', 'LLM Integration', 'Git', 'GitHub Copilot', 'OpenClaw'], category: 'ai' as const },
];

export default function ProfileSection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  return (
    <section id="about" className="section-pad" ref={sectionRef} style={{ background: 'var(--c-surface)' }}>
      <div className="container-site">
        <SectionLabel>ABOUT RAJIB</SectionLabel>
        <motion.div initial={{ opacity: 0, y: 30 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.5 }} className="grid grid-cols-1 md:grid-cols-3 gap-10 md:gap-16">
          <div>
            <div className="w-44 h-44 flex items-center justify-center relative mb-8 mx-auto md:mx-0 glass-card" style={{ borderRadius: '24px', background: 'linear-gradient(135deg, #0e1320 0%, #1547be 100%)', boxShadow: '0 0 80px rgba(21,71,190,0.2)' }}>
              <span style={{ fontFamily: 'Fraunces, serif', fontSize: 48, fontWeight: 700, color: '#fff' }}>RM</span>
              <div style={{ position: 'absolute', bottom: 14, right: 14, width: 8, height: 8, borderRadius: '50%', background: '#eec04e', boxShadow: '0 0 10px rgba(238,192,78,0.6)' }} />
            </div>
            <div className="text-center md:text-left">
              <h3 className="font-section-title text-[26px] font-bold text-on-surface mb-1" style={{ fontFamily: 'Fraunces, serif', color: '#F0F4FF' }}>Rajib Mahata</h3>
              <p className="font-body-base text-[15px] text-primary mb-1" style={{ fontFamily: 'DM Sans, sans-serif', color: '#b5c4ff' }}>Senior .NET &amp; Azure Architect</p>
              <p className="font-label-caps text-[12px] text-text-muted mb-6" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6A7B9E' }}>Kolkata, India · Remote-first</p>
              <div className="grid grid-cols-2 gap-3 mb-6">
                {[{ value: '12+', label: 'Years' }, { value: '30+', label: 'Repos' }, { value: '6', label: 'Products' }, { value: '3', label: 'Enterprises' }].map(stat => (
                  <div key={stat.label} className="glass-card p-3 text-center rounded-xl">
                    <div className="font-telemetry-stat text-[20px] font-bold" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#eec04e' }}>{stat.value}</div>
                    <div className="font-body-compact text-[11px] text-text-muted mt-1" style={{ fontFamily: 'DM Sans, sans-serif', color: '#6A7B9E' }}>{stat.label}</div>
                  </div>
                ))}
              </div>
              <div className="flex flex-wrap gap-2 justify-center md:justify-start">
                {[{ label: 'LinkedIn', href: 'https://linkedin.com/in/rajib-mahata' }, { label: 'GitHub', href: 'https://github.com/rajibmahata' }, { label: 'Resume (PDF)', href: '/Resume-RajibMahata.pdf', download: true }].map(link => (
                  <a key={link.label} href={link.href} target={link.href.startsWith('http') ? '_blank' : undefined} rel={link.href.startsWith('http') ? 'noopener noreferrer' : undefined} download={link.download ? '' : undefined} className="inline-flex items-center px-4 py-2 rounded-full border text-xs hover:border-primary hover:text-primary transition-all" style={{ fontFamily: 'DM Sans, sans-serif', borderColor: '#1E2D4A', color: '#8896B3', borderRadius: '999px' }}>{link.label}</a>
                ))}
              </div>
            </div>
          </div>

          <div className="md:col-span-2 space-y-10">
            <div>
              <h3 className="font-section-title text-[28px] font-bold text-on-surface mb-4" style={{ fontFamily: 'Fraunces, serif', color: '#F0F4FF' }}>Professional Overview</h3>
              <p className="font-body-large text-[18px] text-text-secondary mb-4" style={{ fontFamily: 'DM Sans, sans-serif', fontWeight: 300, lineHeight: 1.7, color: '#8896B3' }}>
                Independent software architect with 12+ years building production systems for Fortune 500 and enterprise clients. I specialise in .NET, Azure cloud, and AI/LLM integrations — delivering measurable impact: 30% faster processing, 40% fewer errors, 25% higher satisfaction on a national pharmacy platform that ran during the COVID-19 vaccine rollout.
              </p>
              <p className="font-body-base text-text-secondary" style={{ fontFamily: 'DM Sans, sans-serif', color: '#8896B3', lineHeight: 1.65 }}>
                RajibLabs is my independent engineering studio where I build AI-powered SaaS products and collaborate with clients worldwide. Available for consulting, architecture, and development — remote-first, global delivery.
              </p>
            </div>

            <div>
              <h3 className="font-label-caps text-[11px] font-semibold text-text-muted uppercase tracking-widest mb-4" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6A7B9E' }}>Professional Experience</h3>
              <div className="relative">
                <div className="hidden sm:block absolute left-[15px] top-3 bottom-3 w-px" style={{ background: '#1E2D4A' }} />
                <div className="space-y-6">
                  {timeline.map((item, i) => (
                    <motion.div key={item.company} initial={{ opacity: 0, x: -12 }} animate={inView ? { opacity: 1, x: 0 } : {}} transition={{ delay: 0.1 * i, duration: 0.4 }} className="relative sm:pl-12">
                      <div className="hidden sm:flex absolute left-[8px] top-5 w-[15px] h-[15px] rounded-full z-10 items-center justify-center" style={{ background: '#0e1320', border: `2.5px solid ${item.color}` }} />
                      <div className="glass-card p-5 rounded-xl hover-lift">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 mb-2">
                          <div className="flex items-center gap-3">
                            <span className="font-card-heading text-[16px] font-semibold text-on-surface" style={{ fontFamily: 'DM Sans, sans-serif', color: '#F0F4FF' }}>{item.company}</span>
                            <span className="font-label-caps text-[12px] text-text-muted" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6A7B9E' }}>{item.period}</span>
                          </div>
                          <span className="font-label-caps text-[11px] font-medium px-2 py-1 rounded" style={{ fontFamily: 'JetBrains Mono, monospace', color: item.color, background: `${item.color}15`, border: `1px solid ${item.color}30` }}>{item.role}</span>
                        </div>
                        <p className="font-body-compact text-[13px] text-text-secondary" style={{ fontFamily: 'DM Sans, sans-serif', color: '#8896B3' }}>{item.client}</p>
                        <p className="font-label-caps text-[12px] text-text-muted mt-2" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6A7B9E' }}>{item.highlight}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-label-caps text-[11px] font-semibold text-text-muted uppercase tracking-widest mb-4" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6A7B9E' }}>Technology Expertise</h3>
              <div className="space-y-4">
                {techCategories.map(group => (
                  <div key={group.label}>
                    <p className="font-label-caps text-[10px] text-text-muted uppercase tracking-widest mb-2" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6A7B9E' }}>{group.label}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {group.items.map(t => <TechChip key={t} label={t} category={group.category} />)}
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
