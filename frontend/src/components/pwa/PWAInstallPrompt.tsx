import { useEffect, useState } from 'react';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export default function PWAInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [visible, setVisible] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    // Check if already installed / standalone
    const standalone =
      window.matchMedia('(display-mode: standalone)').matches ||
      // @ts-ignore iOS
      window.navigator.standalone === true;
    setIsStandalone(standalone);
    if (standalone) return;

    // Check dismiss history (session)
    if (sessionStorage.getItem('pwa-dismissed')) {
      setDismissed(true);
      return;
    }

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
    if (isIOS && !standalone) {
      timer = window.setTimeout(() => setVisible(true), 8000);
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
      if (timer) clearTimeout(timer);
    };
  }, []);

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
      className="fixed z-40 left-4 right-4 sm:left-auto sm:right-6 bottom-6 sm:max-w-sm rounded-2xl border shadow-2xl overflow-hidden"
      style={{
        background: 'var(--c-bg-secondary)',
        borderColor: 'var(--c-border)',
        boxShadow: '0 20px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(37,99,244,0.08)',
        animation: 'slideUp 0.4s cubic-bezier(0,0,0.2,1)',
      }}
      role="dialog"
      aria-label="Install app"
    >
      <div className="p-5">
        <div className="flex gap-4">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{
              background: 'linear-gradient(135deg, var(--c-accent-blue), var(--c-accent-teal))',
              boxShadow: '0 4px 16px rgba(21,71,190,0.3)',
            }}
          >
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 700, color: '#fff' }}>R</span>
          </div>
          <div className="flex-1 min-w-0">
            <h4
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: 15,
                fontWeight: 600,
                color: 'var(--c-text-primary)',
                lineHeight: 1.3,
              }}
            >
              Install RajibLabs App
            </h4>
            <p
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: 13,
                color: 'var(--c-text-secondary)',
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
            style={{ color: 'var(--c-text-muted)', background: 'var(--c-bg-tertiary)' }}
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
            className="flex-1 py-2.5 rounded-lg font-medium text-sm transition-all"
            style={{
              background: 'var(--c-accent-blue)',
              color: '#fff',
              fontFamily: 'var(--font-heading)',
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = 'var(--c-accent-blue-l)';
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = 'var(--c-accent-blue)';
            }}
          >
            {isIOSPrompt ? 'Got it' : 'Install App'}
          </button>
          <button
            onClick={handleDismiss}
            className="px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
            style={{
              background: 'transparent',
              color: 'var(--c-text-secondary)',
              border: '1px solid var(--c-border)',
              fontFamily: 'var(--font-heading)',
            }}
          >
            Later
          </button>
        </div>

        <p
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--c-text-muted)',
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
