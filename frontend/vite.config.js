import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Avoid localhost vs 127.0.0.1 / CORS surprises in local dev.
      '/health': 'http://127.0.0.1:8000',
      '/model-info': 'http://127.0.0.1:8000',
      '/predict': 'http://127.0.0.1:8000',
      '/applications': 'http://127.0.0.1:8000',
      '/analytics': 'http://127.0.0.1:8000',
    },
  },
})
