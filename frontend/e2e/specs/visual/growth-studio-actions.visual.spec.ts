/**
 * Visual Regression — Growth Studio Action Components (Story 2B).
 *
 * Captura baselines de los 5 action components en el playground page
 * `/playground/growth-studio-actions-test` con datos mock deterministas.
 *
 * Diseño:
 * - Playground page renderiza los 5 components con payloads fijos (no SSE real).
 * - Two breakpoints: mobile (375px) y desktop (1024px).
 * - Cada section tiene data-testid estable para locator preciso.
 * - test.describe.serial evita race conditions en compilación en frío.
 * - RAM constraint: SIEMPRE --workers=1.
 *
 * CRITICAL: No requiere autenticación real de copilot ni SSE stream.
 * La playground layout redirige en producción (guard en layout.tsx).
 * En dev (E2E_BASE_URL=dev-app.nicolify.com) es accesible directamente.
 *
 * Threshold: maxDiffPixelRatio ≤ 0.02 (2% — más permisivo que bowtie dado
 * que los action components pueden tener variaciones de renderizado menores
 * por fuentes/subpixel en distintos sistemas).
 *
 * Captura estados:
 * - StageMetricsAction normal (KPIs + channel_breakdown)
 * - StageMetricsAction truncated (role=alert "Datos parciales")
 * - ChannelOverviewAction (grilla de KPIs con currency)
 * - ETLRefreshAction queued (status badge + run_id)
 * - ETLRateLimitedAction (role=alert "Límite de tarifa" + minutos)
 * - ETLConfirmAction (role=alert + confirm button)
 *
 * E2E_BASE_URL=https://dev-app.nicolify.com (CF tunnel).
 */

import { test, expect } from "../../fixtures/auth.fixture";

// ─── Constants ────────────────────────────────────────────────────────────────

const PLAYGROUND_URL = "/playground/growth-studio-actions-test";

const VIEWPORTS = [
  { name: "mobile", width: 375, height: 812 },
  { name: "desktop", width: 1024, height: 768 },
] as const;

const ACTION_SECTIONS = [
  "action-stage-metrics-normal",
  "action-stage-metrics-truncated",
  "action-channel-overview",
  "action-etl-refresh",
  "action-etl-rate-limited",
  "action-etl-confirm",
] as const;

// ─── Suite ────────────────────────────────────────────────────────────────────

for (const viewport of VIEWPORTS) {
  test.describe.serial(
    `Growth Studio Actions VR — ${viewport.name} (${viewport.width}px)`,
    () => {
      test.use({ viewport: { width: viewport.width, height: viewport.height } });

      test.beforeEach(async ({ page }) => {
        // Silenciar llamadas opcionales de providers
        await page.route("**/api/v1/settings/**", (r) =>
          r.fulfill({ json: {}, status: 200 }),
        );
        await page.route("**/api/v1/analytics/**", (r) =>
          r.fulfill({ json: {}, status: 200 }),
        );
      });

      test(`playground page carga correctamente — ${viewport.name}`, async ({
        page,
      }) => {
        await page.goto(PLAYGROUND_URL, {
          waitUntil: "networkidle",
          timeout: 90_000,
        });

        // Verificar que la página no redirigió (solo ocurre en prod)
        await expect(page).toHaveURL(new RegExp("growth-studio-actions-test"));

        // Esperar que el contenido principal sea visible
        await expect(page.locator("main")).toBeVisible({ timeout: 30_000 });

        // Estabilizar animaciones CSS antes de capturar
        await page.waitForTimeout(1000);
      });

      for (const testId of ACTION_SECTIONS) {
        test(`${testId} — visual baseline ${viewport.name}`, async ({
          page,
        }) => {
          await page.goto(PLAYGROUND_URL, {
            waitUntil: "networkidle",
            timeout: 90_000,
          });

          const section = page.locator(`[data-testid="${testId}"]`);
          await expect(section).toBeVisible({ timeout: 30_000 });

          // Estabilizar antes de capturar
          await page.waitForTimeout(500);

          // Scroll to section para viewport screenshot
          await section.scrollIntoViewIfNeeded();
          await page.waitForTimeout(300);

          await expect(section).toHaveScreenshot(
            `${testId}-${viewport.name}.png`,
            {
              maxDiffPixelRatio: 0.02,
              // Enmascarar regiones dinámicas si existieran (estáticas aquí)
              animations: "disabled",
            },
          );
        });
      }

      test(`página completa — full page VR ${viewport.name}`, async ({
        page,
      }) => {
        await page.goto(PLAYGROUND_URL, {
          waitUntil: "networkidle",
          timeout: 90_000,
        });

        await expect(page.locator("main")).toBeVisible({ timeout: 30_000 });

        // Estabilizar todas las animaciones CSS
        await page.waitForTimeout(1500);

        await expect(page).toHaveScreenshot(
          `growth-studio-actions-full-${viewport.name}.png`,
          {
            maxDiffPixelRatio: 0.02,
            fullPage: true,
            animations: "disabled",
          },
        );
      });
    },
  );
}
