/**
 * Smoke Regression — Growth Studio post Story 2B integration.
 *
 * Verifica que las rutas de Growth Studio siguen renderizando correctamente
 * tras la integración de las 5 action components (Story 2B T-2) y los
 * 3 copilot tools (T-3).
 *
 * Incluye:
 * 1. Smoke de las 5 rutas canónicas — misma validación que growth-studio-stages.smoke.spec.ts
 *    pero como regresión post-2B (confirma que el registro de actions no rompe nada).
 * 2. Playground page smoke — verifica que las 5 action components renderizan correctamente
 *    en el entorno de playground (solo dev; layout redirect en prod garantiza seguridad).
 * 3. Verificación de la estructura de action registy en memoria (ningún error en console).
 *
 * CRITICAL: test.describe.serial para evitar race conditions de compilación en frío.
 * RAM constraint: SIEMPRE --workers=1.
 * E2E_BASE_URL=https://dev-app.nicolify.com (Clerk dev instance).
 */
import type { Page, ConsoleMessage } from "@playwright/test";
import { test, expect } from "../../fixtures/auth.fixture";
import { setupGrowthStudioBaseMocks } from "../../fixtures/growth-studio.fixture";

// ─── Slugs canónicos (2A SSoT) ───────────────────────────────────────────────

const STAGE_SLUGS = [
  "atraccion-captura",
  "nutricion-oportunidad",
  "ventas",
  "adopcion",
  "expansion-evangelizacion",
] as const;

// ─── Console error collector ─────────────────────────────────────────────────

/**
 * Colecta errores de consola, excluyendo los esperados en dev.
 */
function collectConsoleErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("console", (msg: ConsoleMessage) => {
    if (msg.type() === "error") {
      const text = msg.text();
      // Filtrar errores esperados / no-accionables en dev
      if (
        !text.includes("ClerkJS") &&
        !text.includes("clerk.com") &&
        !text.includes("Could not parse CSS") &&
        !text.includes("Loading failed for") &&
        !text.includes("Failed to load resource") &&
        !text.includes("Hydration") &&
        !text.includes("401") &&
        !text.includes("404") &&
        !text.includes("429") &&
        !text.includes("500")
      ) {
        errors.push(text);
      }
    }
  });
  return errors;
}

// ─── Suite 1: Rutas canónicas post-2B ────────────────────────────────────────

test.describe.serial(
  "Growth Studio Regresión 2B — Rutas de stage sin errores críticos",
  () => {
    for (const slug of STAGE_SLUGS) {
      test(`${slug} — renderiza sin errores post-2B`, async ({ page, tenantId }) => {
        const consoleErrors = collectConsoleErrors(page);

        await setupGrowthStudioBaseMocks(page);

        // Cold compile puede demorar 30-60s; damos 90s.
        await page.goto(`/${tenantId}/growth-studio/${slug}`, {
          waitUntil: "networkidle",
          timeout: 90_000,
        });

        await expect(page.locator("main")).toBeVisible({ timeout: 45_000 });
        await expect(page).toHaveURL(new RegExp(`growth-studio/${slug}`));

        expect(
          consoleErrors,
          `Errores JS en ${slug} post-2B: ${consoleErrors.join(", ")}`,
        ).toHaveLength(0);
      });
    }
  },
);

// ─── Suite 2: Playground page — 5 action components ─────────────────────────

/**
 * La playground page renderiza los 5 action components con datos mock deterministas.
 * No requiere autenticación real de copilot; valida que el import/registro de los
 * componentes no introduce errores en el árbol de React.
 *
 * Nota: la playground page redirige en producción (layout.tsx guard).
 * En dev (E2E_BASE_URL=dev-app.nicolify.com) es accesible directamente.
 */
test.describe.serial("Growth Studio 2B — Action components en playground", () => {
  const PLAYGROUND_URL = "/playground/growth-studio-actions-test";

  test.beforeEach(async ({ page }) => {
    // Silenciar llamadas de API opcionales que puedan originarse de providers
    await page.route("**/api/v1/settings/**", (r) => r.fulfill({ json: {}, status: 200 }));
  });

  test("playground page carga sin errores críticos de JS", async ({ page }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto(PLAYGROUND_URL, {
      waitUntil: "networkidle",
      timeout: 90_000,
    });

    // Verificar que la página no redirigió (solo ocurre en prod)
    await expect(page).toHaveURL(new RegExp("growth-studio-actions-test"));

    // Main content visible
    await expect(page.locator("main")).toBeVisible({ timeout: 30_000 });

    expect(
      consoleErrors,
      `Errores JS en playground 2B: ${consoleErrors.join(", ")}`,
    ).toHaveLength(0);
  });

  test("StageMetricsAction renderiza el nombre de etapa y KPIs", async ({ page }) => {
    await page.goto(PLAYGROUND_URL, {
      waitUntil: "networkidle",
      timeout: 90_000,
    });

    await expect(page.locator('[data-testid="action-stage-metrics-normal"]')).toBeVisible({
      timeout: 30_000,
    });
    // Stage name visible
    await expect(
      page.locator('[data-testid="action-stage-metrics-normal"]').getByText("Adopción"),
    ).toBeVisible();
    // KPI slug visible
    await expect(
      page
        .locator('[data-testid="action-stage-metrics-normal"]')
        .getByText("active_customers"),
    ).toBeVisible();
  });

  test("StageMetricsAction muestra alerta de datos parciales cuando truncated=true", async ({
    page,
  }) => {
    await page.goto(PLAYGROUND_URL, {
      waitUntil: "networkidle",
      timeout: 90_000,
    });

    const truncatedSection = page.locator('[data-testid="action-stage-metrics-truncated"]');
    await expect(truncatedSection).toBeVisible({ timeout: 30_000 });

    // role=alert debe existir para el estado truncado
    const alert = truncatedSection.locator('[role="alert"]');
    await expect(alert).toBeVisible();
    await expect(alert).toContainText("Datos parciales");
  });

  test("ChannelOverviewAction renderiza nombre de canal y KPIs en grilla", async ({ page }) => {
    await page.goto(PLAYGROUND_URL, {
      waitUntil: "networkidle",
      timeout: 90_000,
    });

    const section = page.locator('[data-testid="action-channel-overview"]');
    await expect(section).toBeVisible({ timeout: 30_000 });

    await expect(section.getByText("Meta Ads")).toBeVisible();
    await expect(section.getByText("Inversión")).toBeVisible();
  });

  test("ETLRefreshAction renderiza estado queued con nombre de canal", async ({ page }) => {
    await page.goto(PLAYGROUND_URL, {
      waitUntil: "networkidle",
      timeout: 90_000,
    });

    const section = page.locator('[data-testid="action-etl-refresh"]');
    await expect(section).toBeVisible({ timeout: 30_000 });

    await expect(section.getByText("meta-ads")).toBeVisible();
    await expect(section.getByText("Actualización en cola")).toBeVisible();
  });

  test("ETLRateLimitedAction usa role=alert y Spanish neutro (sin voseo)", async ({ page }) => {
    await page.goto(PLAYGROUND_URL, {
      waitUntil: "networkidle",
      timeout: 90_000,
    });

    const section = page.locator('[data-testid="action-etl-rate-limited"]');
    await expect(section).toBeVisible({ timeout: 30_000 });

    // Must have role=alert for a11y
    const alert = section.locator('[role="alert"]');
    await expect(alert).toBeVisible();

    // Spanish neutro — "Límite de tarifa" (no voseo)
    await expect(alert).toContainText("Límite de tarifa");
    // Tiempo en minutos — 1860s = 31 minutos
    await expect(alert).toContainText("31 minuto");
  });

  test("ETLConfirmAction muestra botón de confirmar (no en estado completed)", async ({
    page,
  }) => {
    await page.goto(PLAYGROUND_URL, {
      waitUntil: "networkidle",
      timeout: 90_000,
    });

    const section = page.locator('[data-testid="action-etl-confirm"]');
    await expect(section).toBeVisible({ timeout: 30_000 });

    // role=alert present
    await expect(section.locator('[role="alert"]')).toBeVisible();

    // Confirm button visible and accessible
    const confirmBtn = section.getByRole("button", { name: /confirmar/i });
    await expect(confirmBtn).toBeVisible();
    await expect(confirmBtn).toBeEnabled();
  });
});
