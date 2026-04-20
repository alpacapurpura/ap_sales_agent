import { expect, test } from "../../fixtures/auth.fixture";

/**
 * Smoke coverage for the three social-proof sections (testimonials,
 * authority, team). Each route mocks the list endpoint to return a single
 * seed row so the instance picker renders populated (dark/light) and
 * verifies the landing welcome pane copy.
 */
test.describe("Social Proof — Brand Studio @smoke", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/social-proof/testimonials**", (route) => {
      if (route.request().method() === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            {
              id: "ssp-t-0001",
              tenant_id: "00000000-0000-0000-0000-000000000001",
              author_name: "Juana Pérez",
              author_role: "CEO",
              author_avatar_url: null,
              content: "Excelente",
              media_type: "text",
              media_url: null,
              rating: 5,
              source_url: null,
              captured_at: null,
              language: "es",
              tags: [],
              is_active: true,
              created_at: null,
              updated_at: null,
            },
          ]),
        });
      }
      return route.continue();
    });

    await page.route("**/api/v1/social-proof/authority**", (route) => {
      if (route.request().method() === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            {
              id: "ssp-a-0001",
              tenant_id: "00000000-0000-0000-0000-000000000001",
              entity_name: "Forbes",
              authority_type: "media_mention",
              context: null,
              proof_url: null,
              logo_url: null,
              obtained_at: null,
              expires_at: null,
              is_active: true,
              created_at: null,
              updated_at: null,
            },
          ]),
        });
      }
      return route.continue();
    });

    await page.route("**/api/v1/social-proof/team**", (route) => {
      if (route.request().method() === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            {
              id: "ssp-m-0001",
              tenant_id: "00000000-0000-0000-0000-000000000001",
              name: "Chris Alpaca",
              role: "Fundador",
              bio: null,
              headshot_url: null,
              is_primary_voice: true,
              gender: null,
              communication_style: null,
              personal_website: null,
              personal_linkedin: null,
              personal_instagram: null,
              personal_tiktok: null,
              personal_facebook: null,
              work_whatsapp: null,
              gallery: [],
              sort_order: 0,
              created_at: null,
              updated_at: null,
            },
          ]),
        });
      }
      return route.continue();
    });
  });

  test("testimonials landing renders picker + welcome pane", async ({
    page,
    tenantId,
  }) => {
    await page.goto(`/${tenantId}/brand-studio/testimonials`, {
      waitUntil: "domcontentloaded",
    });
    await expect(page.getByText("Testimonios")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText(/Elige o crea un testimonio/i)).toBeVisible();
  });

  test("authority landing renders picker + welcome pane", async ({
    page,
    tenantId,
  }) => {
    await page.goto(`/${tenantId}/brand-studio/authority`, {
      waitUntil: "domcontentloaded",
    });
    await expect(page.getByText("Autoridad")).toBeVisible({ timeout: 30_000 });
    await expect(
      page.getByText(/Elige o agrega una señal de autoridad/i),
    ).toBeVisible();
  });

  test("team landing renders picker + welcome pane", async ({ page, tenantId }) => {
    await page.goto(`/${tenantId}/brand-studio/team`, {
      waitUntil: "domcontentloaded",
    });
    await expect(page.getByText("Equipo")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText(/Elige o agrega un miembro del equipo/i)).toBeVisible();
  });
});
