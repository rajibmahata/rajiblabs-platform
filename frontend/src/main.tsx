import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { registerSW } from './pwa/registerSW'
import { LanguageProvider } from './i18n/LanguageContext'

// Register PWA Service Worker — works on all platforms (desktop, Android, iOS)
registerSW()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <LanguageProvider>
      <App />
    </LanguageProvider>
  </StrictMode>,
)
