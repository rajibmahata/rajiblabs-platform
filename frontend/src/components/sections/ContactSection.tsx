import { useState, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import type { ContactForm } from '../../types';

export default function ContactSection() {
  const [form, setForm] = useState<ContactForm>({ name: '', email: '', company: '', message: '' });
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.message) return;
    setStatus('loading');

    try {
      const subject = encodeURIComponent(`Message from ${form.name} via rajiblabs.com`);
      const body = encodeURIComponent(
        `Name: ${form.name}\nEmail: ${form.email}\n${form.company ? `Company: ${form.company}\n` : ''}\n${form.message}`
      );
      window.location.href = `mailto:rajibmahata143@gmail.com?subject=${subject}&body=${body}`;
      setStatus('success');
      setForm({ name: '', email: '', company: '', message: '' });
      setTimeout(() => setStatus('idle'), 3000);
    } catch {
      setStatus('error');
    }
  };

  const contactItems = [
    {
      icon: '📧',
      label: 'Email',
      value: 'rajibmahata143@gmail.com',
      href: 'mailto:rajibmahata143@gmail.com',
    },
    {
      icon: '💼',
      label: 'LinkedIn',
      value: 'linkedin.com/in/rajib-mahata',
      href: 'https://linkedin.com/in/rajib-mahata',
    },
    {
      icon: '⌥',
      label: 'GitHub',
      value: 'github.com/rajibmahata',
      href: 'https://github.com/rajibmahata',
    },
  ];

  const inputStyle = {
    background: 'var(--c-bg-tertiary)',
    border: '1px solid var(--c-border)',
    borderRadius: 'var(--radius-md)',
    padding: '14px 16px',
    fontFamily: 'var(--font-body)',
    fontSize: 15,
    color: 'var(--c-text-primary)',
    outline: 'none',
    width: '100%',
    transition: 'border-color 200ms, box-shadow 200ms',
  };

  return (
    <section id="contact" className="section-pad" ref={sectionRef}
      style={{ background: 'var(--c-bg-primary)' }}
    >
      <div className="container-site">
        <SectionLabel>LET'S CONNECT</SectionLabel>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-start"
        >
          {/* LEFT — Copy + Info */}
          <div>
            <h2 style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'clamp(28px, 3.5vw, 42px)',
              fontWeight: 700,
              color: 'var(--c-text-primary)',
              lineHeight: 'var(--lh-display)',
              marginBottom: 20,
            }}>
              Have a project in mind?{' '}
              <span style={{ color: 'var(--c-text-secondary)', fontWeight: 400 }}>
                Let's talk.
              </span>
            </h2>

            <p style={{
              fontFamily: 'var(--font-body)',
              fontSize: 16,
              color: 'var(--c-text-secondary)',
              lineHeight: 'var(--lh-body)',
              marginBottom: 24,
            }}>
              I work with SaaS founders, agencies, and enterprises who need senior-level architecture and
              development. Whether it's a greenfield product, a complex integration, or an AI feature —
              I bring 12+ years of production experience to your project.
            </p>

            <div className="flex flex-wrap gap-2 mb-8">
              {[
                'Backend Architecture',
                'Azure Cloud',
                'AI / RAG Systems',
                'SaaS Development',
                'API Design',
                'Microservices',
              ].map(tag => (
                <span key={tag} style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(21,71,190,0.1)',
                  color: 'var(--c-accent-blue-l)',
                  border: '1px solid rgba(21,71,190,0.2)',
                }}>
                  {tag}
                </span>
              ))}
            </div>

            <div className="h-px mb-8" style={{ background: 'var(--c-border)' }} />

            <p style={{
              fontFamily: 'var(--font-heading)',
              fontSize: 13,
              fontWeight: 500,
              color: 'var(--c-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: 16,
            }}>
              Direct Contact
            </p>

            <div className="space-y-4">
              {contactItems.map(item => (
                <a
                  key={item.label}
                  href={item.href}
                  target={item.href.startsWith('http') ? '_blank' : undefined}
                  rel={item.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                  className="flex items-center gap-3 group transition-colors"
                  style={{ textDecoration: 'none' }}
                  onMouseEnter={e => { e.currentTarget.style.opacity = '0.8'; }}
                  onMouseLeave={e => { e.currentTarget.style.opacity = '1'; }}
                >
                  <span style={{ fontSize: 20 }}>{item.icon}</span>
                  <div>
                    <span style={{
                      fontFamily: 'var(--font-body)',
                      fontSize: 12,
                      color: 'var(--c-text-muted)',
                    }}>
                      {item.label}
                    </span>
                    <p style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 14,
                      color: 'var(--c-text-secondary)',
                    }}>
                      {item.value}
                    </p>
                  </div>
                </a>
              ))}
            </div>

            <p style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              color: 'var(--c-text-muted)',
              marginTop: 20,
            }}>
              📍 Kolkata, India · Available globally · Remote-first
            </p>

            {/* Resume download link */}
            <a
              href="/Resume-RajibMahata.pdf"
              download
              className="inline-flex items-center gap-2 mt-6 px-5 py-2.5 rounded-md border transition-all"
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: 14,
                fontWeight: 500,
                borderColor: 'var(--c-accent-gold)',
                color: 'var(--c-accent-gold)',
                borderRadius: 'var(--radius-md)',
                textDecoration: 'none',
                background: 'transparent',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.backgroundColor = 'var(--c-accent-gold)';
                e.currentTarget.style.color = '#080D1A';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.color = 'var(--c-accent-gold)';
              }}
            >
              📄 Download Resume (PDF)
            </a>
          </div>

          {/* RIGHT — Form */}
          <div>
            <form onSubmit={handleSubmit} className="card p-8 space-y-5"
              style={{ background: 'var(--c-bg-secondary)' }}
            >
              <div>
                <label htmlFor="name" style={{
                  fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--c-text-secondary)',
                  marginBottom: 6, display: 'block',
                }}>
                  Name *
                </label>
                <input id="name" name="name" type="text" required value={form.name}
                  onChange={handleChange} style={inputStyle}
                  onFocus={e => { e.currentTarget.style.borderColor = 'var(--c-accent-blue)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(21,71,190,0.15)'; }}
                  onBlur={e => { e.currentTarget.style.borderColor = 'var(--c-border)'; e.currentTarget.style.boxShadow = ''; }}
                  placeholder="Your name"
                />
              </div>

              <div>
                <label htmlFor="email" style={{
                  fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--c-text-secondary)',
                  marginBottom: 6, display: 'block',
                }}>
                  Email *
                </label>
                <input id="email" name="email" type="email" required value={form.email}
                  onChange={handleChange} style={inputStyle}
                  onFocus={e => { e.currentTarget.style.borderColor = 'var(--c-accent-blue)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(21,71,190,0.15)'; }}
                  onBlur={e => { e.currentTarget.style.borderColor = 'var(--c-border)'; e.currentTarget.style.boxShadow = ''; }}
                  placeholder="you@company.com"
                />
              </div>

              <div>
                <label htmlFor="company" style={{
                  fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--c-text-secondary)',
                  marginBottom: 6, display: 'block',
                }}>
                  Company (optional)
                </label>
                <input id="company" name="company" type="text" value={form.company}
                  onChange={handleChange} style={inputStyle}
                  onFocus={e => { e.currentTarget.style.borderColor = 'var(--c-accent-blue)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(21,71,190,0.15)'; }}
                  onBlur={e => { e.currentTarget.style.borderColor = 'var(--c-border)'; e.currentTarget.style.boxShadow = ''; }}
                  placeholder="Your company"
                />
              </div>

              <div>
                <label htmlFor="message" style={{
                  fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--c-text-secondary)',
                  marginBottom: 6, display: 'block',
                }}>
                  Tell me about your project *
                </label>
                <textarea id="message" name="message" required rows={5} value={form.message}
                  onChange={handleChange}
                  style={{ ...inputStyle, minHeight: 130, resize: 'vertical' }}
                  onFocus={e => { e.currentTarget.style.borderColor = 'var(--c-accent-blue)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(21,71,190,0.15)'; }}
                  onBlur={e => { e.currentTarget.style.borderColor = 'var(--c-border)'; e.currentTarget.style.boxShadow = ''; }}
                  placeholder="What are you building? What do you need help with?"
                />
              </div>

              {/* Honeypot */}
              <div style={{ position: 'absolute', left: '-9999px', opacity: 0 }} aria-hidden="true">
                <input type="text" name="website" tabIndex={-1} autoComplete="off" readOnly />
              </div>

              <button
                type="submit"
                disabled={status === 'loading' || status === 'success'}
                className="w-full flex items-center justify-center px-6 py-4 text-[15px] font-medium rounded-md transition-all duration-200 disabled:opacity-50"
                style={{
                  fontFamily: 'var(--font-heading)',
                  fontWeight: 500,
                  backgroundColor: status === 'success' ? 'var(--c-accent-teal)' : 'var(--c-accent-blue)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 'var(--radius-md)',
                  cursor: status === 'loading' ? 'wait' : 'pointer',
                }}
                onMouseEnter={e => {
                  if (status !== 'loading' && status !== 'success') {
                    e.currentTarget.style.backgroundColor = 'var(--c-accent-blue-l)';
                    e.currentTarget.style.boxShadow = 'var(--shadow-glow-blue)';
                  }
                }}
                onMouseLeave={e => {
                  if (status !== 'loading' && status !== 'success') {
                    e.currentTarget.style.backgroundColor = 'var(--c-accent-blue)';
                    e.currentTarget.style.boxShadow = '';
                  }
                }}
              >
                {status === 'loading' && (
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                )}
                {status === 'success' ? '✓ Message Sent!' : status === 'error' ? 'Try Again' : 'Send Message →'}
              </button>

              {status === 'error' && (
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#EF4444', textAlign: 'center' }}>
                  Something went wrong. Please try again or email me directly.
                </p>
              )}
            </form>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
