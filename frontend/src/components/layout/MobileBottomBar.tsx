import { siteConfig } from '../../config/site';

export default function MobileBottomBar() {
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 rounded-t-xl md:hidden bg-surface-container/95 backdrop-blur-xl border-t border-outline-variant/20 shadow-[0_-8px_32px_rgba(0,0,0,0.4)]"
      style={{ background: 'rgba(22,27,41,0.95)', paddingBottom: 'env(safe-area-inset-bottom)' }}
      aria-label="Quick contact"
    >
      <div className="flex justify-around items-center h-16 px-6">
        <a
          href={siteConfig.callLink}
          className="flex flex-col items-center gap-1 active:scale-95 transition-transform text-on-surface-variant p-3 group"
          aria-label="Call"
        >
          <span className="material-symbols-outlined group-hover:text-primary transition-colors">call</span>
          <span className="font-label-caps text-[11px] opacity-0 h-0 group-hover:opacity-100 group-hover:h-auto transition-all text-primary">Call</span>
        </a>
        <a
          href={siteConfig.whatsappLink}
          target="_blank"
          rel="noopener noreferrer"
          className="bg-whatsapp text-white rounded-full p-3 active:scale-95 transition-transform flex items-center justify-center shadow-lg"
          style={{ background: '#25D366', color: '#fff' }}
          aria-label="WhatsApp"
        >
          <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>chat</span>
        </a>
        <a
          href={siteConfig.emailLink}
          className="flex flex-col items-center gap-1 active:scale-95 transition-transform text-on-surface-variant p-3 group"
          aria-label="Email"
        >
          <span className="material-symbols-outlined group-hover:text-primary transition-colors">mail</span>
          <span className="font-label-caps text-[11px] opacity-0 h-0 group-hover:opacity-100 group-hover:h-auto transition-all text-primary">Email</span>
        </a>
      </div>
    </nav>
  );
}
