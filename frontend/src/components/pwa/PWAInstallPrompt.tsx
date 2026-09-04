import { useEffect, useState } from 'react';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export default function PWAInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [visible, setVisible] = useState(false);
  const [dismissed, setDismissed] = useState(() => {
    if (typeof window === 'undefined') return false;
    return sessionStorage.getItem('pwa-dismissed') !== null;
  });
  const [isStandalone] = useState(() => {
    if (typeof window === 'undefined') return false;
    return (
      window.matchMedia('(display-mode: standalone)').matches ||
      (window.navigator as unknown as { standalone?: boolean }).standalone === true
    );
  });

  useEffect(() => {
    if (isStandalone || dismissed) return;

    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      // Show after 3s if not dismissed
      setTimeout(() => setVisible(true), 3000);
    };

    window.addEventListener('beforeinstallprompt', handler);

    // iOS fallback — show manual install hint after 8s
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    let timer: number | undefined;
    if (isIOS && !isStandalone) {
      timer = window.setTimeout(() => setVisible(true), 8000);
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
      if (timer) clearTimeout(timer);
    };
  }, [isStandalone, dismissed]);

  const handleInstall = async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      const choice = await deferredPrompt.userChoice;
      if (choice.outcome === 'accepted') {
        setVisible(false);
      }
      setDeferredPrompt(null);
    } else {
      // iOS manual
      setVisible(false);
    }
  };

  const handleDismiss = () => {
    setVisible(false);
    setDismissed(true);
    sessionStorage.setItem('pwa-dismissed', '1');
  };

  if (isStandalone || dismissed || !visible) return null;

  const isIOSPrompt = !deferredPrompt;

  return (
    <div
      className="fixed z-40 left-4 right-4 sm:left-auto sm:right-6 sm:max-w-md"
      style={{
        top: 88,
        background: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        border: '1px solid rgba(15, 18, 34, 0.08)',
        borderRadius: 16,
        boxShadow: '0 8px 30px rgba(15, 18, 34, 0.08), 0 0 30px rgba(124, 58, 237, 0.06)',
        animation: 'slideDown 0.4s cubic-bezier(0,0,0.2,1)',
      }}
      role="dialog"
      aria-label="Install app"
    >
      <div className="flex items-center gap-3" style={{ padding: '12px 12px 12px 14px' }}>
        <div
          className="w-10 h-10 flex items-center justify-center flex-shrink-0"
          style={{
            borderRadius: 12,
            background: 'linear-gradient(135deg, #7c3aed, #06b6d4)',
            boxShadow: '0 8px 20px rgba(124, 58, 237, 0.35)',
          }}
        >
          <span style={{ fontFamily: "'Sora', sans-serif", fontSize: 18, fontWeight: 700, color: '#fff' }}>R</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span
              style={{
                fontFamily: "'Sora', sans-serif",
                fontSize: 13,
                fontWeight: 700,
                color: '#0f1222',
                lineHeight: 1.3,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              Install RajibLabs App
            </span>
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 9,
                fontWeight: 500,
                color: '#7c3aed',
                background: '#ede9fe',
                border: '1px solid rgba(124, 58, 237, 0.2)',
                padding: '1px 7px',
                borderRadius: 100,
                letterSpacing: '0.06em',
                flexShrink: 0,
              }}
            >
              PWA
            </span>
          </div>
          <p
            style={{
              fontFamily: "'Inter', sans-serif",
              fontSize: 12,
              color: '#4b5065',
              lineHeight: 1.4,
              marginTop: 2,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {isIOSPrompt ? 'Share → Add to Home Screen' : 'Offline access · Faster loading'}
          </p>
        </div>
        <button
          onClick={handleInstall}
          className="text-sm transition-all flex-shrink-0"
          style={{
            borderRadius: 10,
            padding: '8px 16px',
            background: 'linear-gradient(135deg, #7c3aed, #06b6d4)',
            boxShadow: '0 8px 20px rgba(124, 58, 237, 0.35)',
            color: '#fff',
            fontFamily: "'Inter', sans-serif",
            fontWeight: 600,
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 12px 28px rgba(124, 58, 237, 0.45)';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 8px 20px rgba(124, 58, 237, 0.35)';
          }}
        >
          {isIOSPrompt ? 'Got it' : 'Install'}
        </button>
        <button
          onClick={handleDismiss}
          className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 transition-colors"
          style={{ color: '#8a8fa8', background: '#eef0f9' }}
          aria-label="Dismiss"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <style>{`@keyframes slideDown { from { opacity:0; transform: translateY(-16px)} to {opacity:1; transform:translateY(0)}}`}</style>
    </div>
  );
}
