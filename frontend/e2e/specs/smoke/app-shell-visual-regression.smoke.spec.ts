/**
 * Smoke E2E — App Shell Visual Regression (pixel-perfect baselines).
 *
 * Validator: visual_regression_pixel_perfect
 *
 * Captura screenshots del app shell (bowtie + AppSidebar nav + CopilotSidebar)
 * con el área de main content ENMASCARADA (AD10 — main cambia por floor policy,
 * no es una regresión visual del shell).
 *
 * Primer run: captura baselines (--update-snapshots).
 * Runs posteriores: compara con baselines (maxDiffPixelRatio: 0.01).
 *
 * IMPORTANTE: El baseline capturado en este spec debe ser ratificado por Chris
 * antes de hacer merge del PR. El archivo .png se agrega al commit.
 *
 * Viewports testeados:
 *   - 1440×900 (desktop estándar, copilot colapsado)
 *   - 375×812 (mobile, sin copilot sidebar visible)
 *
 * Nota técnica (CopilotFAB + useViewport):
 * Para el test mobile 375: navegamos en desktop y luego hacemos resize a 375px
 * para disparar el media query change que activa isMobile: true → FAB aparece.
 *
 * RAM constraint: SIEMPRE --workers=1.
 * E2E_BASE_URL=https://dev-app.nicolify.com (CF tunnel).
 */
import { test, expect } from "../../fixtures/auth.fixture";

/**
 * Colapsa copilot en desktop cerrando via botón "Cerrar copilot" del chat header.
 * Verifica el cierre via live region "Copilot cerrado".
 */
async function collapseCopilotDesktop(page: import('@playwright/test').Page) {
  const liveRegion = page.locator('[role="status"][aria-live="polite"]');
  const currentLabel = await liveRegion.getAttribute("aria-label").catch(() => null);
  if (currentLabel === "Copilot cerrado") return;

  const cerrarCopilot = page.getByRole("button", { name: "Cerrar copilot" });
  const isVisible = await cerrarCopilot.isVisible().catch(() => false);
  if (isVisible) {
    await cerrarCopilot.click();
    await expect(liveRegion).toHaveAttribute("aria-label", "Copilot cerrado", { timeout: 5_000 });
  }
}

test.describe.serial("App Shell — Visual Regression (pixel-perfect baselines)", () => {
  test("shell desktop 1440 — bowtie + nav + copilot rail (main masked)", async ({
    page,
    tenantId,
  }) => {
    await page.setViewportSize({ width: 1440, height: 900 });

    await page.goto(`/${tenantId}/brand-studio`, {
      waitUntil: "networkidle",
      timeout: 90_000,
    });

    await expect(page.locator("main")).toBeVisible({ timeout: 45_000 });

    // Cerrar copilot rail post-carga (loadPersistedSidebarState retorna "rail" por defecto)
    await collapseCopilotDesktop(page);

    // Estabilizar la página antes del screenshot
    await page.waitForTimeout(500);

    // Screenshot con main content enmascarado (AD10)
    await expect(page).toHaveScreenshot("app-shell-desktop-1440.png", {
      mask: [page.locator("main")],
      maxDiffPixelRatio: 0.01,
      // Área del shell que NO se enmascara: AppSidebar (izquierda) + CopilotSidebar (derecha)
      // El main (centro) se enmascara porque su contenido varía.
      fullPage: false,
    });
  });

  test("shell mobile 375 — topbar + hamburger + FAB (main masked)", async ({
    page,
    tenantId,
  }) => {
    // Navegar en desktop para que React hidrate sin SSR mismatch en isMobile
    await page.setViewportSize({ width: 1440, height: 900 });

    await page.goto(`/${tenantId}/brand-studio`, {
      waitUntil: "networkidle",
      timeout: 90_000,
    });

    await expect(page.locator("main")).toBeVisible({ timeout: 45_000 });

    // Cerrar copilot rail en desktop
    await collapseCopilotDesktop(page);

    // Resize a mobile — dispara media query change → isMobile = true → FAB aparece
    await page.setViewportSize({ width: 375, height: 812 });
    await page.waitForTimeout(500);

    // Verificar que FAB es visible (estado: copilot colapsado, mobile)
    const fab = page.getByRole("button", { name: "Abrir asistente" });
    await expect(fab).toBeVisible({ timeout: 10_000 });

    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot("app-shell-mobile-375.png", {
      mask: [page.locator("main")],
      maxDiffPixelRatio: 0.01,
      fullPage: false,
    });
  });

  test("shell desktop 1280 — sidebar colapsado (main masked)", async ({
    page,
    tenantId,
  }) => {
    await page.setViewportSize({ width: 1280, height: 800 });

    await page.goto(`/${tenantId}/brand-studio`, {
      waitUntil: "networkidle",
      timeout: 90_000,
    });

    await expect(page.locator("main")).toBeVisible({ timeout: 45_000 });

    // Cerrar copilot rail post-carga
    await collapseCopilotDesktop(page);

    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot("app-shell-desktop-1280.png", {
      mask: [page.locator("main")],
      maxDiffPixelRatio: 0.01,
      fullPage: false,
    });
  });
});
