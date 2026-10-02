import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(import.meta.dirname, './src') },
  },
  server: {
    // A fixed port of its own, so this never collides with another project's Vite on 5173.
    port: 5180,
    strictPort: true,
    // The FastAPI backend runs on port 8000; the browser only ever talks to Vite, so the
    // session cookie stays same-origin. 127.0.0.1 rather than localhost, because Node resolves
    // localhost to the IPv6 address ::1 while uvicorn listens on IPv4 only.
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})
