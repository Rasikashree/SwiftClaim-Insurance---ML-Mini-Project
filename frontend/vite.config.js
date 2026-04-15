import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// VITE_BASE_PATH is set by the CD pipeline for GitHub Pages deployment.
// Falls back to '/' for local development.
export default defineConfig({
  plugins: [react()],
  base: '/',
})
