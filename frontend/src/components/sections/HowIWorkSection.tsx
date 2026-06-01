import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';

const explorationAreas = [
  {
    icon: '🤖',
    title: 'AI & Automation',
    description: 'Building RAG systems, agentic pipelines, and multi-agent AI workflows. Exploring LLM-powered automation for real-world problems.',
    color: 'var(--c-accent-teal)',
  },
  {
    icon: '☁️',
    title: 'Cloud-Native Architecture',
    description: 'Designing scalable systems on .NET + Azure. Event-driven patterns, serverless workflows, and distributed system experiments.',
    color: 'var(--c-accent-blue)',
  },
  {
    icon: '🧪',
    title: 'SaaS Product Experiments',
    description: 'Building end-to-end SaaS products as learning sandboxes — from auth and payments to AI features and deployment.',
    color: 'var(--c-accent-gold)',
  },
  {
    icon: '🔬',
    title: 'LLM & API Integration',
    description: 'Experimenting with GPT-4o, DeepSeek, Gemini, and Claude APIs. Prompt engineering, function calling, and AI copilot patterns.',
    color: 'var(--c-accent-blue)',
  },
];

const buildProcess = [
  {
    step: '01',
    title: 'Share an Idea',
    description: 'A technical challenge, an AI experiment, or a product concept worth exploring. I build things purely for learning and curiosity.',
  },
  {
    step: '02',
    title: 'Build & Learn',
    description: 'I bring the idea to life using modern AI tooling, cloud infrastructure, and clean architecture — learning something new with every project.',
  },
  {
    step: '03',
    title: 'Ship & Share',
    description: 'The result goes live as an open-source project or a working prototype. Lessons learned become part of this portfolio.',
  },
];

export default function HowIWorkSection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  return (
    <section id="services" className="section-pad" ref={sectionRef}
      style={{ background: 'var(--c-bg-secondary)' }}
    >
      <div className="container-site">
        <SectionLabel>WHAT I EXPLORE</SectionLabel>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
        >
          {/* Exploration Areas */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-16">
            {explorationAreas.map(card => (
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

          {/* How I Build */}
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
              Share Idea → Build & Learn → Ship & Share
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {buildProcess.map((step, i) => (
                <div key={step.step} className="text-center relative">
                  {/* Step connector line (desktop) */}
                  {i < buildProcess.length - 1 && (
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
                Let's Connect →
              </a>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
