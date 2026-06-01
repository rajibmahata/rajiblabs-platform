import { useEffect, useState, useRef } from 'react';
import { motion, useInView } from 'framer-motion';

const skills = [
  { name: '.NET 8 / C#',  level: 95 },
  { name: 'Azure Cloud',  level: 90 },
  { name: 'AI / RAG',     level: 75 },
  { name: 'React / TS',   level: 80 },
];

function AnimatedBar({ label, target, delay }: { label: string; target: number; delay: number }) {
  const [width, setWidth] = useState(0);
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-50px' });

  useEffect(() => {
    if (inView) {
      const timer = setTimeout(() => setWidth(target), delay);
      return () => clearTimeout(timer);
    }
  }, [inView, target, delay]);

  const getLevel = (t: number) => (t >= 90 ? 'Expert' : t >= 75 ? 'Senior' : 'Mid');

  return (
    <div ref={ref} className="mb-3">
      <div className="flex justify-between items-center mb-1">
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--c-text-secondary)' }}>
          {label}
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--c-accent-teal)' }}>
          {getLevel(target)}
        </span>
      </div>
      <div className="h-1 rounded-full" style={{ background: 'var(--c-bg-tertiary)' }}>
        <motion.div
          className="h-full rounded-full"
          style={{
            background: 'linear-gradient(90deg, var(--c-accent-blue), var(--c-accent-teal))',
            width: `${width}%`,
            transition: 'width 1s var(--ease-out)',
          }}
        />
      </div>
    </div>
  );
}

function CountUpStat({ value, suffix, label, delay }: { value: number; suffix: string; label: string; delay: number }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-50px' });

  useEffect(() => {
    if (!inView) return;
    const timer = setTimeout(() => {
      const duration = 1500;
      const steps = 30;
      const inc = value / steps;
      let current = 0;
      const interval = setInterval(() => {
        current += inc;
        if (current >= value) {
          setDisplay(value);
          clearInterval(interval);
        } else {
          setDisplay(Math.floor(current));
        }
      }, duration / steps);
      return () => clearInterval(interval);
    }, delay);
    return () => clearTimeout(timer);
  }, [inView, value, delay]);

  return (
    <div ref={ref} className="flex items-baseline gap-0.5">
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 28, color: 'var(--c-accent-gold)', fontWeight: 500 }}>
        {display}{suffix}
      </span>
      <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--c-text-secondary)' }}>
        {label}
      </span>
    </div>
  );
}

interface HeroSectionProps {
  productCount?: number;
  companyCount?: number;
}

export default function HeroSection({ productCount = 16, companyCount = 3 }: HeroSectionProps) {
  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  const stats = [
    { value: 12, suffix: '', label: 'Yrs Exp' },
    { value: productCount, suffix: '', label: 'Products' },
    { value: companyCount, suffix: '', label: 'Companies' },
    { value: 40, suffix: '%', label: 'Less Errors' },
  ];

  return (
    <section
      className="relative min-h-screen flex items-center overflow-hidden"
      style={{ minHeight: 600, paddingTop: 64 }}
    >
      {/* ── Background Effects ── */}
      {/* Radial gradient */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse 70% 50% at 50% -10%, rgba(13,31,60,0.6), transparent)',
        }}
      />

      {/* Blue orb — top right */}
      <div
        className="absolute pointer-events-none"
        aria-hidden="true"
        style={{
          width: 400, height: 400,
          background: 'radial-gradient(circle, rgba(21,71,190,0.25), transparent)',
          filter: 'blur(80px)',
          top: '-150px', right: '-100px',
        }}
      />

      {/* Gold orb — bottom left */}
      <div
        className="absolute pointer-events-none"
        aria-hidden="true"
        style={{
          width: 400, height: 400,
          background: 'radial-gradient(circle, rgba(196,154,42,0.2), transparent)',
          filter: 'blur(80px)',
          bottom: '-100px', left: '-100px',
        }}
      />

      {/* Subtle grid mesh */}
      <div
        className="absolute inset-0 pointer-events-none"
        aria-hidden="true"
        style={{
          backgroundImage: `
            linear-gradient(var(--c-border) 1px, transparent 1px),
            linear-gradient(90deg, var(--c-border) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
          opacity: 0.06,
        }}
      />

      {/* ── Content ── */}
      <div className="container-site relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center py-16">
          {/* LEFT COLUMN — Text */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0, 0, 0.2, 1] }}
          >
            {/* Gold mono label */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.5 }}
              className="section-label"
            >
              SENIOR .NET &amp; AZURE ENGINEER
            </motion.p>

            {/* Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.6 }}
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 'clamp(36px, 5vw, 60px)',
                fontWeight: 700,
                lineHeight: 'var(--lh-display)',
                letterSpacing: 'var(--ls-display)',
                color: 'var(--c-text-primary)',
                marginBottom: 16,
              }}
            >
              Rajib Mahata.
              <br />
              I build <em style={{ fontStyle: 'italic' }}>software</em> that runs businesses.
            </motion.h1>

            {/* Sub-headline */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35, duration: 0.6 }}
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: 18,
                fontWeight: 300,
                lineHeight: 'var(--lh-body)',
                color: 'var(--c-text-secondary)',
                maxWidth: 500,
                marginBottom: 16,
              }}
            >
              12 years. Enterprise-grade. Fortune 500 delivery. AI Products.
            </motion.p>

            {/* Outcomes badge */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.42, duration: 0.5 }}
              className="inline-flex flex-wrap items-center gap-2 px-4 py-2.5 rounded-lg mb-6"
              style={{
                background: 'rgba(10,123,108,0.1)',
                border: '1px solid rgba(10,123,108,0.25)',
              }}
            >
              {['30% faster processing', '40% fewer medication errors', '25% higher patient satisfaction'].map((metric, i) => (
                <span key={metric} className="flex items-center gap-2">
                  {i > 0 && <span style={{ color: 'var(--c-border)', fontSize: 14 }}>·</span>}
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 13,
                    fontWeight: 500,
                    color: 'var(--c-accent-teal)',
                  }}>
                    {metric}
                  </span>
                </span>
              ))}
            </motion.div>

            {/* Email badge */}
            <motion.a
              href="mailto:rajibmahata143@gmail.com"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.46, duration: 0.5 }}
              className="inline-flex items-center gap-2 mb-6 transition-colors"
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 14,
                color: 'var(--c-text-muted)',
                textDecoration: 'none',
              }}
              onMouseEnter={e => { e.currentTarget.style.color = 'var(--c-accent-blue-l)'; }}
              onMouseLeave={e => { e.currentTarget.style.color = 'var(--c-text-muted)'; }}
            >
              ✉ rajibmahata143@gmail.com
            </motion.a>

            {/* CTAs */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.5 }}
              className="flex flex-wrap gap-3"
            >
              <button
                onClick={() => scrollTo('projects')}
                className="inline-flex items-center px-7 py-3 text-[15px] font-medium rounded-md transition-all duration-200"
                style={{
                  fontFamily: 'var(--font-heading)',
                  fontWeight: 500,
                  backgroundColor: 'var(--c-accent-blue)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.backgroundColor = 'var(--c-accent-blue-l)';
                  e.currentTarget.style.boxShadow = 'var(--shadow-glow-blue)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.backgroundColor = 'var(--c-accent-blue)';
                  e.currentTarget.style.boxShadow = '';
                }}
              >
                View My Work ↓
              </button>
              <button
                onClick={() => scrollTo('contact')}
                className="inline-flex items-center px-7 py-3 text-[15px] font-medium rounded-md transition-all duration-200"
                style={{
                  fontFamily: 'var(--font-heading)',
                  fontWeight: 500,
                  background: 'transparent',
                  color: 'var(--c-text-primary)',
                  border: '1px solid var(--c-border-hover)',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = 'var(--c-accent-blue)';
                  e.currentTarget.style.color = 'var(--c-accent-blue-l)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'var(--c-border-hover)';
                  e.currentTarget.style.color = 'var(--c-text-primary)';
                }}
              >
                Get in Touch
              </button>
            </motion.div>

            {/* Email */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.65, duration: 0.5 }}
              style={{ marginTop: 20 }}
            >
              <a
                href="mailto:rajibmahata143@gmail.com"
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 13,
                  color: 'var(--c-text-muted)',
                  textDecoration: 'none',
                  transition: 'color 0.2s',
                }}
                onMouseEnter={e => { e.currentTarget.style.color = 'var(--c-accent-blue-l)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = 'var(--c-text-muted)'; }}
              >
                ✉ rajibmahata143@gmail.com
              </a>
            </motion.p>
          </motion.div>

          {/* RIGHT COLUMN — Terminal Card */}
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.7, ease: [0, 0, 0.2, 1] }}
          >
            <div className="glass-card p-6">
              {/* Terminal header dots */}
              <div className="flex gap-2 mb-4">
                {['#FF5F56', '#FFBD2E', '#27C93F'].map((color, i) => (
                  <div key={i} className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                ))}
              </div>

              {/* Terminal content */}
              <div className="space-y-3">
                <div>
                  <span style={{ color: 'var(--c-accent-teal)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>$ </span>
                  <span style={{ color: 'var(--c-text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>whoami</span>
                </div>
                <div style={{ color: 'var(--c-text-primary)', fontFamily: 'var(--font-mono)', fontSize: 14, paddingLeft: 16 }}>
                  Rajib Mahata
                </div>

                <div className="mt-4">
                  <span style={{ color: 'var(--c-accent-teal)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>$ </span>
                  <span style={{ color: 'var(--c-text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>cat skills.txt</span>
                </div>

                <div style={{ paddingLeft: 16 }}>
                  {skills.map((skill, i) => (
                    <AnimatedBar key={skill.name} label={skill.name} target={skill.level} delay={600 + i * 150} />
                  ))}
                </div>

                <div className="mt-4">
                  <span style={{ color: 'var(--c-accent-teal)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>$ </span>
                  <span style={{ color: 'var(--c-text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>status</span>
                </div>
                <div style={{ paddingLeft: 16 }}>
                  <span className="pulse-dot" style={{ display: 'inline-block', backgroundColor: 'var(--c-accent-teal)', marginRight: 8 }} />
                  <span className="cursor-blink" style={{ color: 'var(--c-text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
                    3 projects in progress
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* ── Stats Bar ── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.6 }}
          className="flex flex-wrap justify-center gap-6 sm:gap-10 lg:gap-16 py-8 border-t"
          style={{
            borderColor: 'var(--c-border)',
          }}
        >
          {stats.map((stat, i) => (
            <div key={stat.label} className="flex items-center gap-6">
              {i > 0 && (
                <div className="hidden sm:block w-px h-8" style={{ background: 'var(--c-border)' }} />
              )}
              <CountUpStat value={stat.value} suffix={stat.suffix} label={stat.label} delay={900 + i * 120} />
            </div>
          ))}
        </motion.div>

        {/* ── Outcomes Strip ── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2, duration: 0.5 }}
          className="flex flex-wrap justify-center gap-x-6 gap-y-2 py-6 border-t text-center"
          style={{ borderColor: 'var(--c-border)' }}
        >
          {[
            { icon: '📊', text: '30% faster processing' },
            { icon: '🛡️', text: '40% fewer medication errors' },
            { icon: '⭐', text: '25% higher patient satisfaction' },
          ].map((item, i) => (
            <span key={i} className="flex items-center gap-1.5">
              <span className="text-base">{item.icon}</span>
              <span style={{ fontFamily: 'var(--font-body)', fontSize: 14, fontWeight: 500, color: 'var(--c-text-secondary)' }}>
                {item.text}
              </span>
              {i < 2 && (
                <span style={{ color: 'var(--c-accent-gold)', marginLeft: 8, opacity: 0.6 }}>·</span>
              )}
            </span>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
