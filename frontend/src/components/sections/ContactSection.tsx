import { useState, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';
import { siteConfig } from '../../config/site';
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
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" /></svg>
      ),
      label: 'Call',
      value: siteConfig.contact.phone,
      href: siteConfig.callLink,
      accent: 'var(--c-accent-blue)',
    },
    {
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M19.05 4.94A9.91 9.91 0 0 0 12.04 2C6.58 2 2.14 6.45 2.14 11.9c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38a9.87 9.87 0 0 0 4.79 1.22h.01c5.46 0 9.9-4.45 9.9-9.9 0-2.64-1.03-5.13-2.9-7zM12.04 19.8h-.01a8.13 8.13 0 0 1-4.15-1.14l-.3-.18-3.12.82.83-3.04-.2-.31a8.18 8.18 0 0 1-1.26-4.05c0-4.5 3.66-8.16 8.17-8.16 2.18 0 4.23.85 5.77 2.4a8.1 8.1 0 0 1 2.39 5.76c0 4.5-3.66 8.17-8.15 8.17zm6.7-5.99c-.37-.18-2.17-1.07-2.5-1.19-.34-.12-.58-.18-.82.18-.24.37-.94 1.19-1.16 1.44-.21.24-.42.27-.79.09-.37-.18-1.55-.57-2.96-1.82-1.09-.97-1.83-2.17-2.05-2.54-.21-.37-.02-.57.16-.75.16-.16.37-.42.55-.63.18-.21.24-.37.37-.61.12-.24.06-.46-.03-.64-.09-.18-.82-1.98-1.12-2.71-.29-.7-.59-.61-.82-.62l-.7-.01c-.24 0-.64.09-.97.46-.34.37-1.28 1.25-1.28 3.05s1.31 3.54 1.49 3.78c.18.24 2.58 3.94 6.25 5.53.87.38 1.55.6 2.08.77.87.28 1.67.24 2.3.15.7-.1 2.17-.89 2.47-1.75.31-.86.31-1.59.21-1.75-.09-.15-.34-.24-.7-.42z" /></svg>
      ),
      label: 'WhatsApp',
      value: siteConfig.contact.phone,
      href: siteConfig.whatsappLink,
      accent: '#25D366',
      external: true,
    },
    {
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><polyline points="22,6 12,13 2,6" /></svg>
      ),
      label: 'Email',
      value: siteConfig.contact.email,
      href: siteConfig.emailLink,
      accent: 'var(--c-accent-gold)',
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

            {/* Pill-style quick contact — 2 prominent CTAs like PestFlow */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-8">
              <a
                href={siteConfig.whatsappLink}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 p-4 rounded-xl border transition-all group"
                style={{ background: 'rgba(37,211,102,0.08)', borderColor: 'rgba(37,211,102,0.25)' }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(37,211,102,0.14)'; e.currentTarget.style.borderColor = '#25D366'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
                onMouseLeave={e => { e.currentTarget.style.background = 'rgba(37,211,102,0.08)'; e.currentTarget.style.borderColor = 'rgba(37,211,102,0.25)'; e.currentTarget.style.transform = 'translateY(0)'; }}
              >
                <span className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: '#25D366', color: '#fff' }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M19.05 4.94A9.91 9.91 0 0 0 12.04 2C6.58 2 2.14 6.45 2.14 11.9c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38a9.87 9.87 0 0 0 4.79 1.22h.01c5.46 0 9.9-4.45 9.9-9.9 0-2.64-1.03-5.13-2.9-7zM12.04 19.8h-.01a8.13 8.13 0 0 1-4.15-1.14l-.3-.18-3.12.82.83-3.04-.2-.31a8.18 8.18 0 0 1-1.26-4.05c0-4.5 3.66-8.16 8.17-8.16 2.18 0 4.23.85 5.77 2.4a8.1 8.1 0 0 1 2.39 5.76c0 4.5-3.66 8.17-8.15 8.17zm6.7-5.99c-.37-.18-2.17-1.07-2.5-1.19-.34-.12-.58-.18-.82.18-.24.37-.94 1.19-1.16 1.44-.21.24-.42.27-.79.09-.37-.18-1.55-.57-2.96-1.82-1.09-.97-1.83-2.17-2.05-2.54-.21-.37-.02-.57.16-.75.16-.16.37-.42.55-.63.18-.21.24-.37.37-.61.12-.24.06-.46-.03-.64-.09-.18-.82-1.98-1.12-2.71-.29-.7-.59-.61-.82-.62l-.7-.01c-.24 0-.64.09-.97.46-.34.37-1.28 1.25-1.28 3.05s1.31 3.54 1.49 3.78c.18.24 2.58 3.94 6.25 5.53.87.38 1.55.6 2.08.77.87.28 1.67.24 2.3.15.7-.1 2.17-.89 2.47-1.75.31-.86.31-1.59.21-1.75-.09-.15-.34-.24-.7-.42z" /></svg>
                </span>
                <div className="min-w-0 flex-1">
                  <div style={{ fontFamily: 'var(--font-heading)', fontSize: 14, fontWeight: 600, color: '#25D366' }}>WhatsApp</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--c-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{siteConfig.contact.phone}</div>
                </div>
                <span style={{ color: '#25D366', fontSize: 16 }} className="group-hover:translate-x-1 transition-transform">→</span>
              </a>
              <a
                href={siteConfig.callLink}
                className="flex items-center gap-3 p-4 rounded-xl border transition-all group"
                style={{ background: 'rgba(21,71,190,0.08)', borderColor: 'rgba(21,71,190,0.25)' }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(21,71,190,0.14)'; e.currentTarget.style.borderColor = 'var(--c-accent-blue)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
                onMouseLeave={e => { e.currentTarget.style.background = 'rgba(21,71,190,0.08)'; e.currentTarget.style.borderColor = 'rgba(21,71,190,0.25)'; e.currentTarget.style.transform = 'translateY(0)'; }}
              >
                <span className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: 'var(--c-accent-blue)', color: '#fff' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" /></svg>
                </span>
                <div className="min-w-0 flex-1">
                  <div style={{ fontFamily: 'var(--font-heading)', fontSize: 14, fontWeight: 600, color: 'var(--c-accent-blue-l)' }}>Call Now</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--c-text-secondary)' }}>{siteConfig.contact.phone}</div>
                </div>
                <span style={{ color: 'var(--c-accent-blue-l)', fontSize: 16 }} className="group-hover:translate-x-1 transition-transform">→</span>
              </a>
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

            <div className="space-y-3">
              {contactItems.map(item => (
                <a
                  key={item.label}
                  href={item.href}
                  target={item.href.startsWith('http') ? '_blank' : undefined}
                  rel={item.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                  className="flex items-center gap-3 p-3 rounded-lg border transition-all"
                  style={{ textDecoration: 'none', background: 'var(--c-bg-secondary)', borderColor: 'var(--c-border)' }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = item.accent; e.currentTarget.style.transform = 'translateX(4px)'; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--c-border)'; e.currentTarget.style.transform = 'translateX(0)'; }}
                >
                  <span className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: `${item.accent}18`, color: item.accent, border: `1px solid ${item.accent}30` }}>{item.icon}</span>
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
                      fontSize: 13,
                      color: 'var(--c-text-secondary)',
                    }}>
                      {item.value}
                    </p>
                  </div>
                </a>
              ))}
              {/* Additional LinkedIn & GitHub */}
              <div className="grid grid-cols-2 gap-3">
                <a href="https://linkedin.com/in/rajib-mahata" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 p-3 rounded-lg border transition-all" style={{ background: 'var(--c-bg-secondary)', borderColor: 'var(--c-border)', textDecoration: 'none' }} onMouseEnter={e => e.currentTarget.style.borderColor = '#0A66C2'} onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--c-border)'}>
                  <span style={{ fontSize: 16 }}>💼</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--c-text-secondary)' }}>LinkedIn</span>
                </a>
                <a href="https://github.com/rajibmahata" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 p-3 rounded-lg border transition-all" style={{ background: 'var(--c-bg-secondary)', borderColor: 'var(--c-border)', textDecoration: 'none' }} onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--c-text-secondary)'} onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--c-border)'}>
                  <span style={{ fontSize: 16 }}>⌥</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--c-text-secondary)' }}>GitHub</span>
                </a>
              </div>
            </div>

            <p style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              color: 'var(--c-text-muted)',
              marginTop: 20,
            }}>
              📍 {siteConfig.contact.location}
            </p>

            {/* Resume download link */}
            <a
              href="/Resume-RajibMahata.pdf"
              download
              className="inline-flex items-center gap-2 mt-6 px-5 py-2.5 rounded-xl border transition-all"
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
            <form onSubmit={handleSubmit} className="card p-8 space-y-6"
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
                className="w-full flex items-center justify-center px-6 py-4 text-[15px] font-medium rounded-xl transition-all duration-200 disabled:opacity-50"
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
