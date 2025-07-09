import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/activities': {
        target: 'http://localhost:8080',  // Direct to FastAPI (bypasses Kong auth)
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/activities/, '/api/activities'),
      }
    }
  }
})