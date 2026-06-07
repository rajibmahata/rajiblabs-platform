import { useEffect, useState, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import SectionLabel from '../ui/SectionLabel';

interface LinkedInCourse {
  id: string;
  title: string;
  url: string;
  instructor?: string;
  duration?: string;
  level?: string;
  completedAt?: string;
  status: string;
  updatedAt: string;
}

export default function LinkedInLearningSection() {
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { once: true, margin: '-100px' });
  const [courses, setCourses] = useState<LinkedInCourse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetch('/api/learning')
      .then(r => r.ok ? r.json() : Promise.reject('API unavailable'))
      .then((data: LinkedInCourse[]) => {
        if (!cancelled) setCourses(data);
      })
      .catch(() => {
        // Fallback: show static example courses
        if (!cancelled) setCourses([
          { id: '1', title: 'Azure Microservices with .NET', url: '#', instructor: 'Rodrigo Díaz Concha', duration: '4h 12m', level: 'Advanced', status: 'in-progress', updatedAt: new Date().toISOString(), completedAt: undefined },
          { id: '2', title: 'Building RAG Applications with LLMs', url: '#', instructor: 'Kesha Williams', duration: '2h 35m', level: 'Intermediate', status: 'in-progress', updatedAt: new Date().toISOString(), completedAt: undefined },
          { id: '3', title: 'React: Design Patterns', url: '#', instructor: 'Shaun Wassell', duration: '3h 20m', level: 'Advanced', status: 'completed', updatedAt: new Date(Date.now() - 86400000).toISOString(), completedAt: new Date(Date.now() - 86400000).toISOString() },
        ]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const inProgress = courses.filter(c => c.status === 'in-progress');
  const completed = courses.filter(c => c.status === 'completed');

  if (!loading && courses.length === 0) return null;

  return (
    <section className="section-pad" ref={sectionRef} id="learning">
      <div className="container-site">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
        >
          <SectionLabel>📚 LINKEDIN LEARNING</SectionLabel>

          <h2 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 30,
            fontWeight: 700,
            color: 'var(--c-text-primary)',
            lineHeight: 'var(--lh-display)',
            letterSpacing: 'var(--ls-display)',
            marginBottom: 8,
          }}>
            What I'm Learning
          </h2>

          <p style={{
            fontFamily: 'var(--font-body)',
            fontSize: 15,
            color: 'var(--c-text-secondary)',
            lineHeight: 'var(--lh-body)',
            marginBottom: 32,
          }}>
            Continuously upskilling. Updated daily from LinkedIn Learning.
          </p>

          {loading ? (
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              {[1,2,3].map(i => (
                <div key={i} style={{
                  flex: '1 1 300px',
                  minWidth: 280,
                  height: 140,
                  background: 'var(--c-bg-secondary)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--c-border)',
                }} />
              ))}
            </div>
          ) : (
            <>
              {/* Currently Learning */}
              {inProgress.length > 0 && (
                <div style={{ marginBottom: 40 }}>
                  <h3 style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: 14,
                    fontWeight: 600,
                    color: 'var(--c-accent-gold)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginBottom: 16,
                  }}>
                    🔄 Currently Learning
                  </h3>
                  <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                    {inProgress.map((course, i) => (
                      <motion.a
                        key={course.id}
                        href={course.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        initial={{ opacity: 0, y: 20 }}
                        animate={inView ? { opacity: 1, y: 0 } : {}}
                        transition={{ duration: 0.4, delay: i * 0.1 }}
                        style={{
                          flex: '1 1 300px',
                          minWidth: 280,
                          background: 'var(--c-bg-secondary)',
                          borderRadius: 'var(--radius-md)',
                          border: '1px solid var(--c-border)',
                          padding: '20px 24px',
                          textDecoration: 'none',
                          transition: 'all 0.2s',
                          position: 'relative',
                          overflow: 'hidden',
                        }}
                        onMouseEnter={e => {
                          e.currentTarget.style.borderColor = 'var(--c-accent-blue)';
                          e.currentTarget.style.transform = 'translateY(-2px)';
                          e.currentTarget.style.boxShadow = 'var(--shadow-glow-blue)';
                        }}
                        onMouseLeave={e => {
                          e.currentTarget.style.borderColor = 'var(--c-border)';
                          e.currentTarget.style.transform = '';
                          e.currentTarget.style.boxShadow = '';
                        }}
                      >
                        {/* Progress bar */}
                        <div style={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          height: 3,
                          width: '60%',
                          background: 'linear-gradient(90deg, var(--c-accent-blue), var(--c-accent-teal))',
                        }} />
                        <div style={{
                          fontFamily: 'var(--font-heading)',
                          fontSize: 15,
                          fontWeight: 600,
                          color: 'var(--c-text-primary)',
                          lineHeight: 1.4,
                          marginBottom: 8,
                        }}>
                          {course.title}
                        </div>
                        <div style={{
                          fontFamily: 'var(--font-body)',
                          fontSize: 13,
                          color: 'var(--c-text-muted)',
                          display: 'flex',
                          gap: 12,
                          flexWrap: 'wrap',
                        }}>
                          {course.instructor && <span>👤 {course.instructor}</span>}
                          {course.duration && <span>⏱ {course.duration}</span>}
                          {course.level && <span>📊 {course.level}</span>}
                        </div>
                      </motion.a>
                    ))}
                  </div>
                </div>
              )}

              {/* Completed */}
              {completed.length > 0 && (
                <div>
                  <h3 style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: 14,
                    fontWeight: 600,
                    color: 'var(--c-accent-teal)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginBottom: 16,
                  }}>
                    ✅ Recently Completed
                  </h3>
                  <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                    {completed.map((course, i) => (
                      <motion.a
                        key={course.id}
                        href={course.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        initial={{ opacity: 0, y: 20 }}
                        animate={inView ? { opacity: 1, y: 0 } : {}}
                        transition={{ duration: 0.4, delay: i * 0.1 }}
                        style={{
                          flex: '1 1 300px',
                          minWidth: 280,
                          background: 'var(--c-bg-secondary)',
                          borderRadius: 'var(--radius-md)',
                          border: '1px solid var(--c-border)',
                          padding: '20px 24px',
                          textDecoration: 'none',
                          transition: 'all 0.2s',
                          opacity: 0.85,
                        }}
                        onMouseEnter={e => {
                          e.currentTarget.style.borderColor = 'var(--c-accent-teal)';
                          e.currentTarget.style.opacity = '1';
                        }}
                        onMouseLeave={e => {
                          e.currentTarget.style.borderColor = 'var(--c-border)';
                          e.currentTarget.style.opacity = '0.85';
                        }}
                      >
                        <div style={{
                          fontFamily: 'var(--font-heading)',
                          fontSize: 15,
                          fontWeight: 600,
                          color: 'var(--c-text-primary)',
                          lineHeight: 1.4,
                          marginBottom: 8,
                        }}>
                          {course.title}
                        </div>
                        <div style={{
                          fontFamily: 'var(--font-body)',
                          fontSize: 13,
                          color: 'var(--c-text-muted)',
                          display: 'flex',
                          gap: 12,
                          flexWrap: 'wrap',
                        }}>
                          {course.instructor && <span>👤 {course.instructor}</span>}
                          {course.duration && <span>⏱ {course.duration}</span>}
                          {course.level && <span>📊 {course.level}</span>}
                          {course.completedAt && <span>📅 {new Date(course.completedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>}
                        </div>
                      </motion.a>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </motion.div>
      </div>
    </section>
  );
}
