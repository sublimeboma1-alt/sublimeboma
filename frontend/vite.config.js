import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Les fichiers compiles sont servis par Django depuis STATIC_URL.
  base: '/static/',
})
