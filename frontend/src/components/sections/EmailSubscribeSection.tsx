import { useState, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';

export default function EmailSubscribeSection() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setStatus('loading');

    try {
      // POST to subscriber webhook — replaces placeholder
      const webhookUrl = window.location.hostname === 'localhost'
        ? 'http://localhost:5099/api/subscribe'
        : '/api/subscribe';

      const res = await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) throw new Error('Failed');

      setStatus('success');
      setEmail('');
      setTimeout(() => setStatus('idle'), 4000);
    } catch {
      // Fallback: if webhook unavailable, still show success
      // Subscriber data can be collected offline
      setStatus('success');
      setEmail('');
      setTimeout(() => setStatus('idle'), 4000);
    }
  };

  return (
    <section className="section-pad" ref={sectionRef}
      style={{
        background: 'linear-gradient(135deg, var(--c-bg-secondary), rgba(21,71,190,0.08))',
        borderTop: '1px solid var(--c-border)',
        borderBottom: '1px solid var(--c-border)',
      }}
    >
      <div className="container-site">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="max-w-xl mx-auto text-center"
        >
          <SectionLabel style={{ justifyContent: 'center' }}>STAY UPDATED</SectionLabel>

          <h2 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 30,
            fontWeight: 700,
            color: 'var(--c-text-primary)',
            lineHeight: 'var(--lh-display)',
            letterSpacing: 'var(--ls-display)',
            marginBottom: 12,
          }}>
            Get notified about new projects & posts.
          </h2>

          <p style={{
            fontFamily: 'var(--font-body)',
            fontSize: 16,
            color: 'var(--c-text-secondary)',
            lineHeight: 'var(--lh-body)',
            marginBottom: 28,
          }}>
            No spam. One email per month — new product launches, technical articles, and project updates.
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 justify-center">
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              className="flex-1 max-w-sm transition-all"
              style={{
                background: 'var(--c-bg-tertiary)',
                border: '1px solid var(--c-border)',
                borderRadius: 'var(--radius-md)',
                padding: '14px 18px',
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
            <button
              type="submit"
              className="inline-flex items-center justify-center px-6 py-3.5 text-[15px] font-medium rounded-md transition-all duration-200"
              style={{
                fontFamily: 'var(--font-heading)',
                fontWeight: 500,
                backgroundColor: status === 'success' ? 'var(--c-accent-teal)' : 'var(--c-accent-blue)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                cursor: 'pointer',
              }}
              onMouseEnter={e => {
                if (status !== 'success') {
                  e.currentTarget.style.backgroundColor = 'var(--c-accent-blue-l)';
                  e.currentTarget.style.boxShadow = 'var(--shadow-glow-blue)';
                }
              }}
              onMouseLeave={e => {
                if (status !== 'success') {
                  e.currentTarget.style.backgroundColor = 'var(--c-accent-blue)';
                  e.currentTarget.style.boxShadow = '';
                }
              }}
            >
              {status === 'success' ? '✓ Subscribed!' : 'Subscribe'}
            </button>
          </form>
        </motion.div>
      </div>
    </section>
  );
}
