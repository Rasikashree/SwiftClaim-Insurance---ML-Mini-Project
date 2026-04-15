import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

export default defineConfig(({ mode }) => {
  const rootDirectory = dirname(fileURLToPath(import.meta.url))
  const env = loadEnv(mode, rootDirectory, '')

  return {
    plugins: [react()],
    base: env.VITE_BASE_PATH || '/',
  }
})
