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
        // Phase 4 Milestone 1: 20% (achieved 2026-04-15: actual ~25%/21%/22%/25%)
        // Milestone 2 target: 40% — focus on hooks (React Query) and lib/utils
        statements: 20,
        branches: 20,
        functions: 20,
        lines: 20,
      },
    },
  },
})
