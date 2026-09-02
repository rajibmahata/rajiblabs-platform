import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';

const services = [
  {
    icon: 'cloud',
    title: 'Azure Cloud Engineering',
    description: 'App Service, Functions, Logic Apps, Service Bus, Event Grid, Key Vault, Cosmos DB. Production-grade cloud infrastructure with CI/CD pipelines.',
    chips: ['Azure Kubernetes', 'Cosmos DB', 'API Management'],
    color: '#7bd7c5',
    span: 'lg:col-span-8',
  },
  {
    icon: 'terminal',
    title: 'Backend Architecture',
    description: '.NET 8 microservices, CQRS, event-driven systems. Scalable APIs that handle millions of requests.',
    chips: ['C#', 'ASP.NET Core'],
    color: '#b5c4ff',
    span: 'lg:col-span-4',
  },
  {
    icon: 'psychology',
    title: 'AI & LLM Integration',
    description: 'RAG systems, agentic pipelines, multi-agent workflows. OpenAI, Gemini, DeepSeek integration.',
    chips: ['Semantic Kernel', 'OpenAI'],
    color: '#eec04e',
    span: 'lg:col-span-5',
  },
  {
    icon: 'rocket_launch',
    title: 'SaaS Product Development',
    description: 'End-to-end product build: auth, payments (Stripe), APIs, frontend, deployment. DocSignerHub is live.',
    chips: ['Stripe', 'React', '.NET 8'],
    color: '#b5c4ff',
    span: 'lg:col-span-7',
  },
];

const process = [
  { step: '01', title: 'Understand Your Needs', description: 'We discuss your technical challenges, business goals, and timeline. I ask the right architecture questions upfront.' },
  { step: '02', title: 'Architect & Build', description: 'Clean architecture from day one. SOLID, CQRS, event-driven where it makes sense. Regular check-ins.' },
  { step: '03', title: 'Deliver & Support', description: 'Production-ready code with documentation. CI/CD pipelines, monitoring, and knowledge transfer.' },
];

export default function HowIWorkSection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  return (
    <section id="services" className="section-pad" ref={sectionRef} style={{ background: 'var(--c-surface)' }}>
      <div className="container-site">
        <SectionLabel>WHAT I BUILD</SectionLabel>
        <motion.div initial={{ opacity: 0, y: 30 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.5 }}>
          <div className="mb-12 border-b border-white/[0.06] pb-8">
            <h2 className="font-section-title text-[38px] md:text-[44px] text-on-surface mb-4" style={{ fontFamily: 'Fraunces, serif', fontWeight: 700, color: '#F0F4FF', lineHeight: 1.05, letterSpacing: '-0.02em' }}>
              Enterprise platforms, AI products, cloud-native systems.
            </h2>
            <p className="font-body-base text-text-secondary max-w-2xl" style={{ fontFamily: 'DM Sans, sans-serif', color: '#8896B3', lineHeight: 1.7 }}>
              Four core capabilities — proven across healthcare, telecom, legal and SaaS. Minimal, scalable, production-grade.
            </p>
          </div>

          {/* Bento Grid — stitch */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-6 mb-16">
            {services.map(card => (
              <div key={card.title} className={`${card.span} card-elegant rounded-2xl p-8 md:p-8 relative overflow-hidden group`}>
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative z-10">
                  <div className="card-icon-wrapper w-14 h-14 rounded-full flex items-center justify-center mb-6 border" style={{ background: 'rgba(255,255,255,0.05)', borderColor: `${card.color}33` }}>
                    <span className="material-symbols-outlined text-[24px]" style={{ color: card.color }}>{card.icon}</span>
                  </div>
                  <h3 className="font-card-heading text-[20px] font-semibold text-on-surface mb-3" style={{ fontFamily: 'DM Sans, sans-serif', color: '#F0F4FF' }}>{card.title}</h3>
                  <p className="font-body-base text-[16px] text-on-surface-variant mb-6" style={{ fontFamily: 'DM Sans, sans-serif', color: '#8896B3', lineHeight: 1.65 }}>{card.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {card.chips.map(chip => (
                      <span key={chip} className="font-tech-chip text-[11px] bg-surface-inset px-2 py-1 rounded border" style={{ fontFamily: 'JetBrains Mono, monospace', background: '#152B52', borderColor: `${card.color}30`, color: card.color }}>{chip}</span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* How I Work — stitch card */}
          <div className="card-elegant rounded-2xl p-8 md:p-12">
            <div className="text-center mb-10">
              <span className="font-label-caps text-[11px] tracking-widest uppercase block mb-2" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#eec04e' }}>HOW I WORK</span>
              <h3 className="font-section-title text-[28px] font-bold text-on-surface" style={{ fontFamily: 'Fraunces, serif', color: '#F0F4FF' }}>From conversation to production in three steps</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {process.map((step, i) => (
                <div key={step.step} className="text-center relative">
                  {i < process.length - 1 && <div className="hidden md:block absolute top-8 left-[60%] w-[80%] h-0.5" style={{ background: 'repeating-linear-gradient(90deg, #1E2D4A 0, #1E2D4A 4px, transparent 4px, transparent 8px)' }} />}
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center relative z-10" style={{ background: 'linear-gradient(135deg, #1547BE, #7bd7c5)', boxShadow: '0 0 24px rgba(21,71,190,0.25)' }}>
                    <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 20, fontWeight: 700, color: '#fff' }}>{step.step}</span>
                  </div>
                  <h4 className="font-card-heading text-[18px] font-semibold text-on-surface mb-2" style={{ fontFamily: 'DM Sans, sans-serif', color: '#F0F4FF' }}>{step.title}</h4>
                  <p className="font-body-compact text-[14px] text-text-secondary" style={{ fontFamily: 'DM Sans, sans-serif', color: '#8896B3' }}>{step.description}</p>
                </div>
              ))}
            </div>
            <div className="text-center mt-10">
              <a href="#contact" onClick={e => { e.preventDefault(); document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' }); }} className="inline-flex items-center px-8 py-3.5 text-[15px] font-medium rounded-full transition-all" style={{ fontFamily: 'DM Sans, sans-serif', background: '#1547be', color: '#fff', borderRadius: '999px' }}>
                Start a Conversation <span className="material-symbols-outlined text-sm ml-1">arrow_forward</span>
              </a>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
