import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The config portal for Sollu operators. Built into dist/ and served by FastAPI under /config,
// so every asset URL is prefixed with that base. See app/main.py and app/routes/platform.py.
export default defineConfig({
  base: '/config/',
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(import.meta.dirname, './src') },
  },
  server: {
    // Next to the shop app's 5180, so both can run at once in development.
    port: 5181,
    strictPort: true,
    // Same as the shop app: the browser only talks to Vite, so the operator cookie stays
    // same-origin. 127.0.0.1 because Node resolves localhost to ::1 and uvicorn listens on IPv4.
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})
