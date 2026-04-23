import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          if (id.includes('lucide-react')) return 'icons-vendor'
          if (id.includes('react-router')) return 'router-vendor'
        },
      },
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
  },
})
