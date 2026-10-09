import { defineConfig } from 'vite'
import process from 'node:process'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss(), react()],
  // GH Pages base: override with VITE_BASE_PATH. Defaults to this repo's
  // Pages path (/Ai_log_platform/). Old fork used /Ai-integrated-log-platform/.
  base: process.env.VITE_BASE_PATH || "/Ai_log_platform/",
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
