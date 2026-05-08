/**
 * Smoke E2E — Growth Studio Stages (5 rutas canónicas).
 *
 * Verifica que el StageDispatcher delega correctamente a cada per-stage page
 * tras el refactor de growth-studio-folder-parity (T-2/T-3/T-4).
 *
 * CRITICAL: test.describe.serial para evitar race conditions de compilación
 * en frío (cold compile Turbopack puede tardar 30-60s por ruta).
 *
 * Slugs canónicos (confirmados por grep 2026-05-07):
 *   atraccion-captura, nutricion-oportunidad, ventas,
 *   adopcion, expansion-evangelizacion
 *
 * E2E_BASE_URL=https://dev-app.nicolify.com (CF tunnel — Clerk dev instance).
 * RAM constraint: SIEMPRE --workers=1.
 */
import type { Page, ConsoleMessage } from '@playwright/test';
import { test, expect } from '../../fixtures/auth.fixture';

const STAGE_SLUGS = [
  'atraccion-captura',
  'nutricion-oportunidad',
  'ventas',
  'adopcion',
  'expansion-evangelizacion',
] as const;

/**
 * Nombre de cada etapa para mensajes de error descriptivos.
 */
const STAGE_LABELS: Record<(typeof STAGE_SLUGS)[number], string> = {
  'atraccion-captura': 'Atracción y Captura',
  'nutricion-oportunidad': 'Nutrición y Oportunidad',
  ventas: 'Ventas',
  adopcion: 'Adopción',
  'expansion-evangelizacion': 'Expansión y Evangelización',
};

/**
 * Colecta errores de consola durante el test. Excluye warnings de Next.js
 * y errores esperados de API (401 autenticación sin datos) en dev.
 */
function collectConsoleErrors(page: Page) {
  const errors: string[] = [];
  page.on('console', (msg: ConsoleMessage) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      // Filtrar errores esperados / no-accionables en dev:
      // - Clerk auth token refreshes
      // - Next.js HMR noise
      // - Analytics API 401/404/429/500 por tenant sin datos o rate limit dev
      // - "Failed to load resource" = errores de red de API (no JS crítico)
      if (
        !text.includes('ClerkJS') &&
        !text.includes('clerk.com') &&
        !text.includes('Could not parse CSS') &&
        !text.includes('Loading failed for') &&
        !text.includes('Failed to load resource') &&
        !text.includes('Hydration') &&
        !text.includes('401') &&
        !text.includes('404') &&
        !text.includes('429') &&
        !text.includes('500')
      ) {
        errors.push(text);
      }
    }
  });
  return errors;
}

// Serial para evitar race de cold-compile paralelo entre rutas
test.describe.serial('Growth Studio — Rutas de Stage (StageDispatcher)', () => {
  for (const slug of STAGE_SLUGS) {
    const label = STAGE_LABELS[slug];

    test(`${label} — main content visible, sin errores críticos`, async ({ page, tenantId }) => {
      const consoleErrors = collectConsoleErrors(page);

      // Cold compile puede demorar 30-60s en primer hit; damos 90s.
      await page.goto(`/${tenantId}/growth-studio/${slug}`, {
        waitUntil: 'networkidle',
        timeout: 90_000,
      });

      // Main content del stage debe ser visible
      await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });

      // URL debe contener el slug canónico
      await expect(page).toHaveURL(new RegExp(`growth-studio/${slug}`));

      // Sin errores JS críticos (filtro aplicado arriba)
      expect(consoleErrors, `Errores de consola en ${label}: ${consoleErrors.join(', ')}`).toHaveLength(0);
    });
  }
});
