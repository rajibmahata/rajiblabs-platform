import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import StatusBadge from '../ui/StatusBadge';
import TechChip from '../ui/TechChip';

const products = [
  {
    name: 'DocSignerHub',
    status: 'live' as const,
    description: 'Enterprise electronic signature SaaS — multi-signer sequential & parallel workflows, HMAC-SHA256 token auth, AI clause analysis, full audit trail, white-label API. 140+ REST endpoints. Built for the Indian enterprise market.',
    techStack: ['.NET 8', 'Blazor', 'Azure', 'SQL Server', 'HMAC-SHA256', 'Stripe', 'OpenAI'],
    liveUrl: 'https://docsignerhub.com',
    githubUrl: 'https://github.com/rajibmahata/DocumentSigningPlatform',
    featured: true,
    priority: 'CRITICAL',
  },
  {
    name: 'ARIA',
    status: 'beta' as const,
    description: 'Enterprise AI knowledge platform — RAG architecture with no-code multi-agent pipeline builder. Hybrid vector + BM25 search. Deployable on-premise with zero vendor lock-in. Proposed to Hyundai Motor India Ltd.',
    techStack: ['Python', 'FastAPI', 'GPT-4o', 'RAG', 'ChromaDB', 'LangChain', 'React'],
    githubUrl: 'https://github.com/rajibmahata/AI-Avatar-RAG-Platform',
    demoUrl: null,
    featured: false,
    priority: 'HIGH',
  },
  {
    name: 'Solicitor CMS',
    status: 'wip' as const,
    description: 'Legal case management platform for mid-size law firms — visual workflow builder, automated document generation from templates, deadline tracking, client portal, and time/billing integration.',
    techStack: ['.NET 8', 'Blazor', 'SQL Server', 'Azure', 'Cosmos DB'],
    githubUrl: 'https://github.com/rajibmahata/SolicitorCaseManagementSystem',
    liveUrl: null,
    featured: false,
    priority: 'MEDIUM',
  },
  {
    name: 'LexVault',
    status: 'wip' as const,
    description: 'Legal document intelligence platform — LLM-assisted knowledge base ingestion + zero-LLM confidence scoring via hybrid search (dense + sparse BM42) on Qdrant. On-premise Windows Server, no cloud dependency.',
    techStack: ['.NET 8', 'Qdrant', 'RAG', 'Hybrid Search', 'Azure OpenAI', 'Redis'],
    githubUrl: 'https://github.com/rajibmahata/Legal-Document-RAG-System-LEXVAULT',
    liveUrl: null,
    featured: false,
    priority: 'HIGH',
  },
  {
    name: 'AI Student Tutor',
    status: 'wip' as const,
    description: 'Multi-role AI learning platform — 12 specialized agents (Teacher, Assessment, Content Gen, Voice, Analytics), voice-first tutoring in 4 languages, human-in-the-loop validation. Nursery to Class 12.',
    techStack: ['FastAPI', 'LangGraph', 'Next.js', 'PostgreSQL', 'Qdrant', 'OpenAI'],
    githubUrl: 'https://github.com/rajibmahata/Math-tutor-AI-Agent',
    liveUrl: null,
    featured: false,
    priority: 'HIGH',
  },
];

export default function ProductsSection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  return (
    <section className="section-pad" ref={sectionRef} id="products"
      style={{ background: 'linear-gradient(180deg, var(--c-bg-secondary) 0%, #0D1F3C 100%)', borderTop: '0.5px solid rgba(30,45,74,0.28)' }}
    >
      <div className="container-site">
        <div className="max-w-3xl mb-2">
          <SectionLabel>PRODUCTS BY RAJIBLABS — SHIPPED & BUILDING</SectionLabel>
          <h2 className="font-display text-[34px] md:text-[42px] leading-[1.05] tracking-tight mt-3" style={{ fontFamily: 'Fraunces, serif', fontWeight: 700, letterSpacing: '-0.03em', color: 'var(--c-text-primary)' }}>
            Products, not just projects.
          </h2>
          <p className="text-[15px] md:text-[16px] mt-3 leading-relaxed" style={{ fontFamily: 'DM Sans, sans-serif', fontWeight: 300, color: 'var(--c-text-secondary)', lineHeight: 1.7 }}>
            Enterprise SaaS and AI systems designed for real businesses — audited, white-label ready, and built for scale.
          </p>
        </div>

          <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.55 }}
          className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-7 mt-10"
        >
          {products.map(product => (
            <div
              key={product.name}
              className={`card-elegant p-7 md:p-8 group ${product.featured ? 'lg:col-span-2' : ''}`}
              style={{
                transition: 'all 420ms cubic-bezier(0.25, 0.8, 0.25, 1)',
              }}
            >
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2">
                  <h3 style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: product.featured ? 22 : 18,
                    fontWeight: 600,
                    color: 'var(--c-text-primary)',
                  }}>
                    {product.name}
                  </h3>
                  {product.priority && (
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 10,
                      fontWeight: 600,
                      padding: '1px 6px',
                      borderRadius: 'var(--radius-sm)',
                      background: product.priority === 'CRITICAL' ? 'rgba(196,154,42,0.15)' : product.priority === 'HIGH' ? 'rgba(21,71,190,0.15)' : 'rgba(10,123,108,0.15)',
                      color: product.priority === 'CRITICAL' ? 'var(--c-accent-gold)' : product.priority === 'HIGH' ? 'var(--c-accent-blue-l)' : 'var(--c-accent-teal)',
                      letterSpacing: '0.05em',
                    }}>
                      {product.priority}
                    </span>
                  )}
                </div>
                <StatusBadge variant={product.status} />
              </div>

              <p style={{
                fontFamily: 'var(--font-body)',
                fontSize: product.featured ? 16 : 14,
                color: 'var(--c-text-secondary)',
                lineHeight: 'var(--lh-body)',
                marginBottom: 16,
              }}>
                {product.description}
              </p>

              {/* Tech stack */}
              <div className="flex flex-wrap gap-1.5 mb-5">
                {product.techStack.map(tech => (
                  <TechChip key={tech} label={tech} category={tech.includes('Azure') ? 'cloud' : tech.includes('React') ? 'frontend' : tech.includes('AI') || tech.includes('RAG') || tech.includes('GPT') ? 'ai' : 'backend'} />
                ))}
              </div>

              {/* Action buttons */}
              <div className="flex flex-wrap gap-3">
                {product.liveUrl && (
                  <a
                    href={product.liveUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-full transition-all"
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
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.backgroundColor = 'var(--c-accent-blue)';
                    }}
                  >
                    ↗ Visit Site
                  </a>
                )}
                {product.githubUrl && (
                  <a
                    href={product.githubUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-full border transition-all"
                    style={{
                      fontFamily: 'var(--font-heading)',
                      fontWeight: 500,
                      color: 'var(--c-text-secondary)',
                      borderColor: 'var(--c-border)',
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
                    View on GitHub
                  </a>
                )}
                {product.status === 'beta' && !product.liveUrl && (
                  <button
                    className="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-full border transition-all"
                    style={{
                      fontFamily: 'var(--font-heading)',
                      fontWeight: 500,
                      color: 'var(--c-accent-gold)',
                      borderColor: 'var(--c-accent-gold)',
                      borderRadius: 'var(--radius-md)',
                      background: 'transparent',
                      cursor: 'pointer',
                    }}
                  >
                    Request Demo
                  </button>
                )}
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
