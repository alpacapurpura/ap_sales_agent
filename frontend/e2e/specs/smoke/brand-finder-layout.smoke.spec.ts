import { expect, test } from "../../fixtures/auth.fixture";

/**
 * Smoke tests verifying the Finder-style layout introduced in 2026-04-20.
 * Pixel contract lives in
 * docs/ux-sessions/2026-04-20-brand-studio-finder-nav/UI-SPEC-locked-dimensions.md.
 */
test.describe("Brand Studio · Finder layout @smoke", () => {
  test("topbar breadcrumb renders with Brand Studio root", async ({ page, tenantId }) => {
    await page.goto(`/${tenantId}/brand-studio/identity`, { waitUntil: "domcontentloaded" });
    await expect(page.getByRole("navigation", { name: /Ruta/i }).first()).toBeVisible({
      timeout: 45_000,
    });
    await expect(page.getByText("Brand Studio").first()).toBeVisible();
    await expect(page.getByText("Identidad").first()).toBeVisible();
  });

  test("sections nav rail uses the locked 260px width", async ({ page, tenantId }) => {
    await page.goto(`/${tenantId}/brand-studio/identity`, { waitUntil: "domcontentloaded" });
    const rail = page.getByRole("region", { name: /Secciones de Brand Studio/i });
    await expect(rail).toBeVisible({ timeout: 45_000 });
    const width = await rail.evaluate((el) => el.getBoundingClientRect().width);
    expect(width).toBeGreaterThanOrEqual(258);
    expect(width).toBeLessThanOrEqual(262);
  });

  test("fields column shows one Finder-style row per field", async ({ page, tenantId }) => {
    await page.goto(`/${tenantId}/brand-studio/identity`, { waitUntil: "domcontentloaded" });
    const firstOption = page.getByRole("option").first();
    await expect(firstOption).toBeVisible({ timeout: 45_000 });
  });

  test("Recomendaciones panel renders collapsed and toggles open", async ({
    page,
    tenantId,
  }) => {
    await page.goto(`/${tenantId}/brand-studio/identity`, { waitUntil: "domcontentloaded" });
    const toggle = page.getByRole("button", { name: /Mostrar recomendaciones/i });
    await expect(toggle).toBeVisible({ timeout: 45_000 });
    await toggle.click();
    await expect(
      page.getByRole("button", { name: /Ocultar recomendaciones/i }),
    ).toBeVisible();
  });

  test("Siguiente vacío CTA or Sección completa is rendered", async ({ page, tenantId }) => {
    await page.goto(`/${tenantId}/brand-studio/identity`, { waitUntil: "domcontentloaded" });
    const locator = page.getByText(/Siguiente vacío|Sección completa/i).first();
    await expect(locator).toBeVisible({ timeout: 45_000 });
  });
});
