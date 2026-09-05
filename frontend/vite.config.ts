import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // FastAPI backend (native `uvicorn app.main:app` runs on :8000;
      // Docker maps it to :8090 — see docker-compose.yml)
      '/api': 'http://localhost:8000',
      // Uploaded catalog images (same backend; lets admin previews work in dev)
      '/uploads': 'http://localhost:8000'
    }
  },
  build: {
    // PWA: Ensure assets are cache-friendly
    rollupOptions: {
      output: {
        manualChunks: undefined,
      },
    },
  },
})
