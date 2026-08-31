// PWA Service Worker registration — works on all platforms (desktop, Android, iOS)
export function registerSW() {
  if (!('serviceWorker' in navigator)) return;

  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js', { scope: '/' })
      .then((reg) => {
        // Check for updates every 60 minutes
        setInterval(() => reg.update(), 60 * 60 * 1000);

        reg.addEventListener('updatefound', () => {
          const newWorker = reg.installing;
          if (!newWorker) return;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New version available — notify user
              window.dispatchEvent(new CustomEvent('pwa:update-available'));
            }
          });
        });
      })
      .catch((err) => console.warn('[PWA] SW registration failed:', err));
  });

  // Handle controller change (new SW activated)
  let refreshing = false;
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (refreshing) return;
    refreshing = true;
    window.location.reload();
  });
}

export function promptPWAUpdate() {
  if (!('serviceWorker' in navigator)) return;
  navigator.serviceWorker.ready.then((reg) => {
    reg.waiting?.postMessage({ type: 'SKIP_WAITING' });
  });
}
