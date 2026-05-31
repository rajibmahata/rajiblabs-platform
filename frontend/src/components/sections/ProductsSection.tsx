import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import StatusBadge from '../ui/StatusBadge';
import TechChip from '../ui/TechChip';

const products = [
  {
    name: 'DocSignerHub',
    status: 'live' as const,
    description: 'Enterprise electronic signature SaaS. Multi-signer workflows, audit trail, HMAC auth, Stripe payments, AI clause analysis.',
    techStack: ['.NET 8', 'Blazor', 'Azure', 'SQL'],
    liveUrl: 'https://docsignerhub.com',
    githubUrl: 'https://github.com/rajibmahata/DocumentSigningPlatform',
    featured: true,
  },
  {
    name: 'ARIA',
    status: 'beta' as const,
    description: 'AI Knowledge Platform with RAG-based enterprise search + Q&A. Avatar interface with hybrid vector search.',
    techStack: ['Python', 'RAG', 'GPT-4o', 'FastAPI', 'ChromaDB'],
    githubUrl: 'https://github.com/rajibmahata/AI-Avatar-RAG-Platform',
    demoUrl: null,
    featured: false,
  },
];

export default function ProductsSection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  return (
    <section className="section-pad" ref={sectionRef} id="products"
      style={{ background: 'var(--c-bg-secondary)' }}
    >
      <div className="container-site">
        <SectionLabel>PRODUCTS BY RAJIBLABS</SectionLabel>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-8"
        >
          {products.map(product => (
            <div
              key={product.name}
              className={`card p-6 group ${product.featured ? 'lg:col-span-2' : ''}`}
              style={{
                background: `linear-gradient(135deg, var(--c-bg-secondary), var(--c-bg-tertiary))`,
                transition: 'all 250ms var(--ease-spring)',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = product.featured ? 'var(--shadow-glow-blue)' : 'var(--shadow-lg)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '';
              }}
            >
              <div className="flex justify-between items-start mb-3">
                <h3 style={{
                  fontFamily: 'var(--font-heading)',
                  fontSize: product.featured ? 22 : 18,
                  fontWeight: 600,
                  color: 'var(--c-text-primary)',
                }}>
                  {product.name}
                </h3>
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
                    className="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-md transition-all"
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
                    className="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-md border transition-all"
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
                    className="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-md border transition-all"
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
