import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';

const serviceCards = [
  {
    icon: '🏗️',
    title: 'Enterprise Architecture',
    description: 'Scalable cloud-native systems on .NET + Azure. From monolith-to-microservice migration to greenfield SaaS platforms.',
    color: 'var(--c-accent-blue)',
  },
  {
    icon: '🤖',
    title: 'AI Integration',
    description: 'RAG systems, LLM-powered workflows, agentic pipelines, and AI-augmented SaaS features — built for production.',
    color: 'var(--c-accent-teal)',
  },
  {
    icon: '🔧',
    title: 'Technical Consulting',
    description: 'Architecture reviews, code audits, technology selection, and technical advisory for startups and enterprises.',
    color: 'var(--c-accent-gold)',
  },
  {
    icon: '🚀',
    title: 'SaaS Product Development',
    description: 'End-to-end product building — from concept validation to live deployment with payment, auth, and AI features.',
    color: 'var(--c-accent-blue)',
  },
];

const processSteps = [
  { step: '01', title: 'Share Your Idea', description: 'Tell me what you need — a product, a feature, or a technical problem. No cost, no commitment.' },
  { step: '02', title: 'Receive a Proposal', description: 'I review your requirements and send back a clear proposal with timeline, budget, and deliverables.' },
  { step: '03', title: 'Build & Deliver', description: 'You pay only on milestone delivery. No upfront fees. Clean code, regular updates, on-time delivery.' },
];

export default function HowIWorkSection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  return (
    <section id="services" className="section-pad" ref={sectionRef}
      style={{ background: 'var(--c-bg-secondary)' }}
    >
      <div className="container-site">
        <SectionLabel>HOW I WORK</SectionLabel>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
        >
          {/* Service Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-16">
            {serviceCards.map(card => (
              <div
                key={card.title}
                className="card p-5 group"
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
                <span style={{ fontSize: 28, display: 'block', marginBottom: 12 }}>{card.icon}</span>
                <h3 style={{
                  fontFamily: 'var(--font-heading)',
                  fontSize: 16,
                  fontWeight: 600,
                  color: 'var(--c-text-primary)',
                  marginBottom: 8,
                }}>
                  {card.title}
                </h3>
                <p style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: 14,
                  color: 'var(--c-text-secondary)',
                  lineHeight: 'var(--lh-compact)',
                }}>
                  {card.description}
                </p>
              </div>
            ))}
          </div>

          {/* 3-Step Process */}
          <div className="card p-8" style={{
            background: 'linear-gradient(135deg, var(--c-bg-secondary), var(--c-bg-tertiary))',
          }}>
            <h3 style={{
              fontFamily: 'var(--font-display)',
              fontSize: 28,
              fontWeight: 700,
              color: 'var(--c-text-primary)',
              textAlign: 'center',
              marginBottom: 40,
            }}>
              Share Idea → Proposal → Build
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {processSteps.map((step, i) => (
                <div key={step.step} className="text-center relative">
                  {/* Step connector line (desktop) */}
                  {i < processSteps.length - 1 && (
                    <div className="hidden md:block absolute top-8 left-[60%] w-[80%] h-0.5"
                      style={{
                        background: `repeating-linear-gradient(90deg, var(--c-border) 0, var(--c-border) 4px, transparent 4px, transparent 8px)`,
                      }}
                    />
                  )}
                  {/* Step number */}
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center relative z-10"
                    style={{
                      background: 'linear-gradient(135deg, var(--c-accent-blue), var(--c-accent-teal))',
                      boxShadow: '0 0 20px rgba(21,71,190,0.3)',
                    }}
                  >
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 20,
                      fontWeight: 700,
                      color: '#fff',
                    }}>
                      {step.step}
                    </span>
                  </div>
                  <h4 style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: 18,
                    fontWeight: 600,
                    color: 'var(--c-text-primary)',
                    marginBottom: 8,
                  }}>
                    {step.title}
                  </h4>
                  <p style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: 14,
                    color: 'var(--c-text-secondary)',
                    lineHeight: 'var(--lh-compact)',
                  }}>
                    {step.description}
                  </p>
                </div>
              ))}
            </div>

            {/* CTA */}
            <div className="text-center mt-10">
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
                  const el = document.getElementById('contact');
                  if (el) el.scrollIntoView({ behavior: 'smooth' });
                }}
              >
                Start a Project →
              </a>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
