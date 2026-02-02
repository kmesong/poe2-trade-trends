import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
      },
      '/analyze': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
      },
      '/history': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
      },
      '/save': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
