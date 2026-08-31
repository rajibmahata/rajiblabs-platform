import { useEffect, useState } from 'react';
import { promptPWAUpdate } from '../../pwa/registerSW';

export default function PWAUpdatePrompt() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const handler = () => setVisible(true);
    window.addEventListener('pwa:update-available', handler);
    return () => window.removeEventListener('pwa:update-available', handler);
  }, []);

  if (!visible) return null;

  return (
    <div
      className="fixed z-50 top-4 left-4 right-4 sm:left-auto sm:right-4 sm:max-w-md rounded-xl border shadow-xl flex items-center gap-3 p-4"
      style={{
        background: 'var(--c-bg-secondary)',
        borderColor: 'var(--c-accent-blue)',
        boxShadow: '0 12px 40px rgba(0,0,0,0.4)',
      }}
      role="alert"
    >
      <div
        className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0"
        style={{ background: 'var(--c-accent-blue)' }}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
          <polyline points="17 6 23 6 23 12" />
        </svg>
      </div>
      <div className="flex-1 min-w-0">
        <p style={{ fontFamily: 'var(--font-heading)', fontSize: 13, fontWeight: 600, color: 'var(--c-text-primary)' }}>
          Update available
        </p>
        <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: 'var(--c-text-secondary)' }}>
          A new version of RajibLabs is ready.
        </p>
      </div>
      <button
        onClick={() => promptPWAUpdate()}
        className="px-4 py-2 rounded-lg text-xs font-semibold transition-colors"
        style={{ background: 'var(--c-accent-blue)', color: '#fff', fontFamily: 'var(--font-heading)' }}
      >
        Update
      </button>
      <button
        onClick={() => setVisible(false)}
        className="px-3 py-2 rounded-lg text-xs"
        style={{ color: 'var(--c-text-muted)', fontFamily: 'var(--font-heading)' }}
      >
        Later
      </button>
    </div>
  );
}
