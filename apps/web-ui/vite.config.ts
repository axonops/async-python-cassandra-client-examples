import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3001,
    proxy: {
      '/api/async': {
        target: process.env.ASYNC_API_URL || 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/async/, '/api/v1')
      },
      '/api/sync': {
        target: process.env.SYNC_API_URL || 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/sync/, '/api/v1')
      },
      '/grafana': {
        target: process.env.GRAFANA_URL || 'http://localhost:3000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/grafana/, '')
      }
    }
  }
})