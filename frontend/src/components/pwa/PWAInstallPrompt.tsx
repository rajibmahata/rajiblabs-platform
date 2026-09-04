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
      className="fixed z-40 left-4 right-4 sm:left-auto sm:right-6 bottom-6 sm:max-w-sm overflow-hidden"
      style={{
        background: 'rgba(255, 255, 255, 0.85)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        border: '1px solid rgba(15, 18, 34, 0.08)',
        borderRadius: 18,
        boxShadow: '0 20px 60px rgba(15, 18, 34, 0.12), 0 0 40px rgba(124, 58, 237, 0.08)',
        animation: 'slideUp 0.4s cubic-bezier(0,0,0.2,1)',
      }}
      role="dialog"
      aria-label="Install app"
    >
      <div className="p-5">
        <div className="flex gap-4">
          <div
            className="w-12 h-12 flex items-center justify-center flex-shrink-0"
            style={{
              borderRadius: 14,
              background: 'linear-gradient(135deg, #7c3aed, #06b6d4)',
              boxShadow: '0 8px 20px rgba(124, 58, 237, 0.35)',
            }}
          >
            <span style={{ fontFamily: "'Sora', sans-serif", fontSize: 22, fontWeight: 700, color: '#fff' }}>R</span>
          </div>
          <div className="flex-1 min-w-0">
            <h4
              style={{
                fontFamily: "'Sora', sans-serif",
                fontSize: 15,
                fontWeight: 700,
                color: '#0f1222',
                lineHeight: 1.3,
              }}
            >
              Install RajibLabs App
            </h4>
            <p
              style={{
                fontFamily: "'Inter', sans-serif",
                fontSize: 13,
                color: '#4b5065',
                lineHeight: 1.5,
                marginTop: 4,
              }}
            >
              {isIOSPrompt
                ? 'Tap Share → Add to Home Screen for offline access & faster loading.'
                : 'Install for offline access, faster loading & home-screen launch.'}
            </p>
          </div>
          <button
            onClick={handleDismiss}
            className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 transition-colors"
            style={{ color: '#8a8fa8', background: '#eef0f9' }}
            aria-label="Dismiss"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="flex gap-2 mt-4">
          <button
            onClick={handleInstall}
            className="flex-1 py-2.5 font-medium text-sm transition-all"
            style={{
              borderRadius: 14,
              background: 'linear-gradient(135deg, #7c3aed, #06b6d4)',
              boxShadow: '0 8px 24px rgba(124, 58, 237, 0.35)',
              color: '#fff',
              fontFamily: "'Inter', sans-serif",
              fontWeight: 600,
            }}
            onMouseEnter={(e) => {
              const el = e.currentTarget as HTMLButtonElement;
              el.style.transform = 'translateY(-2px)';
              el.style.boxShadow = '0 12px 32px rgba(124, 58, 237, 0.45)';
            }}
            onMouseLeave={(e) => {
              const el = e.currentTarget as HTMLButtonElement;
              el.style.transform = 'translateY(0)';
              el.style.boxShadow = '0 8px 24px rgba(124, 58, 237, 0.35)';
            }}
          >
            {isIOSPrompt ? 'Got it' : 'Install App'}
          </button>
          <button
            onClick={handleDismiss}
            className="px-4 py-2.5 text-sm font-medium transition-colors"
            style={{
              borderRadius: 14,
              background: 'transparent',
              color: '#4b5065',
              border: '1px solid rgba(15, 18, 34, 0.08)',
              fontFamily: "'Inter', sans-serif",
            }}
          >
            Later
          </button>
        </div>

        <p
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 10,
            color: '#8a8fa8',
            textAlign: 'center',
            marginTop: 10,
            letterSpacing: '0.04em',
          }}
        >
          Works on Android, iOS, Windows & macOS · Offline-ready
        </p>
      </div>

      <style>{`@keyframes slideUp { from { opacity:0; transform: translateY(16px)} to {opacity:1; transform:translateY(0)}}`}</style>
    </div>
  );
}
