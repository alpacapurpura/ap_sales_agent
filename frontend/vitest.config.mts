import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    setupFiles: './src/test/setup.ts',
    globals: true,
    exclude: ['e2e/**', 'node_modules/**'],
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
    coverage: {
      provider: 'v8',
      include: ['src/features/**', 'src/lib/**', 'src/components/shared/**'],
      exclude: ['src/components/ui/**', '**/*.d.ts', '**/*.test.*'],
      reporter: ['text', 'text-summary'],
      thresholds: {
        statements: 8,
        branches: 5,
        functions: 5,
        lines: 8,
      },
    },
  },
})
