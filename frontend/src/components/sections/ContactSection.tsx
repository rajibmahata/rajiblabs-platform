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
      icon: '📨',
      label: 'Outlook',
      value: 'rajibmahata143@outlook.com',
      href: 'mailto:rajibmahata143@outlook.com',
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

  return (
    <section id="contact" className="section-pad" ref={sectionRef}
      style={{
        background: 'var(--c-bg-secondary)',
        backgroundImage: 'radial-gradient(circle, var(--c-border) 1px, transparent 1px)',
        backgroundSize: '24px 24px',
      }}
    >
      <div className="container-site">
        <SectionLabel>GET IN TOUCH</SectionLabel>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-start"
        >
          {/* LEFT — Info */}
          <div>
            <h2 style={{
              fontFamily: 'var(--font-display)',
              fontSize: 36,
              fontWeight: 700,
              color: 'var(--c-text-primary)',
              lineHeight: 'var(--lh-display)',
              letterSpacing: 'var(--ls-display)',
              marginBottom: 24,
            }}>
              Let's build something together.
            </h2>

            <p style={{
              fontFamily: 'var(--font-body)',
              fontSize: 16,
              color: 'var(--c-text-secondary)',
              lineHeight: 'var(--lh-body)',
              marginBottom: 20,
            }}>
              I'm always open to:
            </p>

            <ul className="space-y-3 mb-10" style={{ listStyle: 'none' }}>
              {[
                'Technical discussions on AI, cloud, and SaaS architecture',
                'Collaborating on open-source or learning projects',
                'Sharing ideas for AI experiments and product concepts',
                'Connecting with fellow engineers and builders',
              ].map(item => (
                <li key={item} className="flex items-center gap-3" style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: 16,
                  color: 'var(--c-text-secondary)',
                }}>
                  <span style={{ color: 'var(--c-accent-gold)', fontSize: 14 }}>▸</span>
                  {item}
                </li>
              ))}
            </ul>

            <div className="h-px mb-8" style={{ background: 'var(--c-border)' }} />

            <p style={{
              fontFamily: 'var(--font-heading)',
              fontSize: 14,
              fontWeight: 500,
              color: 'var(--c-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: 12,
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
                >
                  <span className="text-lg">{item.icon}</span>
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
              marginTop: 16,
            }}>
              📍 Kolkata, India · Available globally
            </p>
          </div>

          {/* RIGHT — Form */}
          <div>
            <form onSubmit={handleSubmit} className="card p-6 space-y-4">
              {/* Name */}
              <div>
                <label
                  htmlFor="name"
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: 13,
                    fontWeight: 400,
                    color: 'var(--c-text-secondary)',
                    marginBottom: 4,
                    display: 'block',
                  }}
                >
                  Name *
                </label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  required
                  value={form.name}
                  onChange={handleChange}
                  className="w-full transition-all"
                  style={{
                    background: 'var(--c-bg-tertiary)',
                    border: '1px solid var(--c-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: '12px 16px',
                    fontFamily: 'var(--font-body)',
                    fontSize: 15,
                    color: 'var(--c-text-primary)',
                    outline: 'none',
                  }}
                  onFocus={e => {
                    e.currentTarget.style.borderColor = 'var(--c-accent-blue)';
                    e.currentTarget.style.boxShadow = '0 0 0 3px rgba(21,71,190,0.15)';
                  }}
                  onBlur={e => {
                    e.currentTarget.style.borderColor = 'var(--c-border)';
                    e.currentTarget.style.boxShadow = '';
                  }}
                />
              </div>

              {/* Email */}
              <div>
                <label
                  htmlFor="email"
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: 13,
                    fontWeight: 400,
                    color: 'var(--c-text-secondary)',
                    marginBottom: 4,
                    display: 'block',
                  }}
                >
                  Email *
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={form.email}
                  onChange={handleChange}
                  className="w-full transition-all"
                  style={{
                    background: 'var(--c-bg-tertiary)',
                    border: '1px solid var(--c-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: '12px 16px',
                    fontFamily: 'var(--font-body)',
                    fontSize: 15,
                    color: 'var(--c-text-primary)',
                    outline: 'none',
                  }}
                  onFocus={e => {
                    e.currentTarget.style.borderColor = 'var(--c-accent-blue)';
                    e.currentTarget.style.boxShadow = '0 0 0 3px rgba(21,71,190,0.15)';
                  }}
                  onBlur={e => {
                    e.currentTarget.style.borderColor = 'var(--c-border)';
                    e.currentTarget.style.boxShadow = '';
                  }}
                />
              </div>

              {/* Company (optional) */}
              <div>
                <label
                  htmlFor="company"
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: 13,
                    fontWeight: 400,
                    color: 'var(--c-text-secondary)',
                    marginBottom: 4,
                    display: 'block',
                  }}
                >
                  Company
                </label>
                <input
                  id="company"
                  name="company"
                  type="text"
                  value={form.company}
                  onChange={handleChange}
                  className="w-full transition-all"
                  style={{
                    background: 'var(--c-bg-tertiary)',
                    border: '1px solid var(--c-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: '12px 16px',
                    fontFamily: 'var(--font-body)',
                    fontSize: 15,
                    color: 'var(--c-text-primary)',
                    outline: 'none',
                  }}
                  onFocus={e => {
                    e.currentTarget.style.borderColor = 'var(--c-accent-blue)';
                    e.currentTarget.style.boxShadow = '0 0 0 3px rgba(21,71,190,0.15)';
                  }}
                  onBlur={e => {
                    e.currentTarget.style.borderColor = 'var(--c-border)';
                    e.currentTarget.style.boxShadow = '';
                  }}
                />
              </div>

              {/* Message */}
              <div>
                <label
                  htmlFor="message"
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: 13,
                    fontWeight: 400,
                    color: 'var(--c-text-secondary)',
                    marginBottom: 4,
                    display: 'block',
                  }}
                >
                  Your idea or question:
                </label>
                <textarea
                  id="message"
                  name="message"
                  required
                  rows={4}
                  value={form.message}
                  onChange={handleChange}
                  className="w-full transition-all"
                  style={{
                    background: 'var(--c-bg-tertiary)',
                    border: '1px solid var(--c-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: '12px 16px',
                    fontFamily: 'var(--font-body)',
                    fontSize: 15,
                    color: 'var(--c-text-primary)',
                    minHeight: 120,
                    resize: 'vertical',
                    outline: 'none',
                  }}
                  onFocus={e => {
                    e.currentTarget.style.borderColor = 'var(--c-accent-blue)';
                    e.currentTarget.style.boxShadow = '0 0 0 3px rgba(21,71,190,0.15)';
                  }}
                  onBlur={e => {
                    e.currentTarget.style.borderColor = 'var(--c-border)';
                    e.currentTarget.style.boxShadow = '';
                  }}
                />
              </div>

              {/* Honey pot (hidden) */}
              <div style={{ position: 'absolute', left: '-9999px', opacity: 0 }} aria-hidden="true">
                <input type="text" name="website" tabIndex={-1} autoComplete="off" readOnly />
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={status === 'loading' || status === 'success'}
                className="w-full flex items-center justify-center px-6 py-3.5 text-[15px] font-medium rounded-md transition-all duration-200 disabled:opacity-50"
                style={{
                  fontFamily: 'var(--font-heading)',
                  fontWeight: 500,
                  backgroundColor: status === 'success' ? 'var(--c-accent-teal)' : 'var(--c-accent-blue)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 'var(--radius-md)',
                  cursor: status === 'loading' ? 'wait' : 'pointer',
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
                <p style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: 13,
                  color: '#EF4444',
                  textAlign: 'center',
                }}>
                  Something went wrong. Please try again.
                </p>
              )}
            </form>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
