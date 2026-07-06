import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';

const services = [
  {
    icon: '🏗️',
    title: 'Backend Architecture',
    description: '.NET 8 microservices, CQRS, event-driven systems. Scalable APIs that handle millions of requests. SQL Server, Cosmos DB, Redis — I choose the right tool for the job.',
    color: 'var(--c-accent-blue)',
  },
  {
    icon: '☁️',
    title: 'Azure Cloud Engineering',
    description: 'App Service, Functions, Logic Apps, Service Bus, Event Grid, Key Vault, Cosmos DB. Production-grade cloud infrastructure with CI/CD pipelines.',
    color: 'var(--c-accent-teal)',
  },
  {
    icon: '🤖',
    title: 'AI & LLM Integration',
    description: 'RAG systems, agentic pipelines, multi-agent workflows. OpenAI, Gemini, DeepSeek integration. Semantic search, vector databases, AI copilot patterns.',
    color: 'var(--c-accent-gold)',
  },
  {
    icon: '🚀',
    title: 'SaaS Product Development',
    description: 'End-to-end product build: auth, payments (Stripe), APIs, frontend, deployment. I ship working products — DocSignerHub is live and generating real interest.',
    color: 'var(--c-accent-blue)',
  },
];

const process = [
  {
    step: '01',
    title: 'Understand Your Needs',
    description: 'We discuss your technical challenges, business goals, and timeline. I ask the right architecture questions upfront to avoid costly rework later.',
  },
  {
    step: '02',
    title: 'Architect & Build',
    description: 'Clean architecture from day one. SOLID, CQRS, event-driven where it makes sense. Regular check-ins — you\'re never in the dark about progress.',
  },
  {
    step: '03',
    title: 'Deliver & Support',
    description: 'Production-ready code with documentation. CI/CD pipelines, monitoring, and knowledge transfer. I don\'t disappear after delivery.',
  },
];

export default function HowIWorkSection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  return (
    <section id="services" className="section-pad" ref={sectionRef}>
      <div className="container-site">
        <SectionLabel>WHAT I OFFER</SectionLabel>

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
              Services for{' '}
              <span style={{ color: 'var(--c-accent-blue-l)' }}>business owners</span>
              {' '}&amp;{' '}
              <span style={{ color: 'var(--c-accent-teal)' }}>technical teams</span>
            </h2>
            <p style={{
              fontFamily: 'var(--font-body)',
              fontSize: 16,
              color: 'var(--c-text-secondary)',
              lineHeight: 'var(--lh-body)',
              maxWidth: 540,
            }}>
              Whether you need an architect for a complex system, a developer to ship a SaaS MVP, or an AI engineer to integrate LLMs — I deliver production-grade work.
            </p>
          </div>

          {/* Service Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-16">
            {services.map(card => (
              <div
                key={card.title}
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
                <div className="flex items-start gap-4">
                  <span style={{ fontSize: 32, flexShrink: 0 }}>{card.icon}</span>
                  <div>
                    <h3 style={{
                      fontFamily: 'var(--font-heading)',
                      fontSize: 17,
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
                </div>
              </div>
            ))}
          </div>

          {/* How I Work — Process */}
          <div className="card p-8" style={{
            background: 'linear-gradient(135deg, var(--c-bg-secondary), var(--c-bg-tertiary))',
          }}>
            <div style={{ textAlign: 'center', marginBottom: 40 }}>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                fontWeight: 500,
                letterSpacing: 'var(--ls-caps)',
                textTransform: 'uppercase',
                color: 'var(--c-accent-gold)',
                display: 'block',
                marginBottom: 8,
              }}>
                HOW I WORK
              </span>
              <h3 style={{
                fontFamily: 'var(--font-display)',
                fontSize: 28,
                fontWeight: 700,
                color: 'var(--c-text-primary)',
              }}>
                From conversation to production in three steps
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {process.map((step, i) => (
                <div key={step.step} className="text-center relative">
                  {/* Connector line (desktop) */}
                  {i < process.length - 1 && (
                    <div className="hidden md:block absolute top-8 left-[60%] w-[80%] h-0.5"
                      style={{
                        background: `repeating-linear-gradient(90deg, var(--c-border) 0, var(--c-border) 4px, transparent 4px, transparent 8px)`,
                      }}
                    />
                  )}
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center relative z-10"
                    style={{
                      background: 'linear-gradient(135deg, var(--c-accent-blue), var(--c-accent-teal))',
                      boxShadow: '0 0 24px rgba(21,71,190,0.25)',
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
                  document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' });
                }}
              >
                Start a Conversation →
              </a>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
