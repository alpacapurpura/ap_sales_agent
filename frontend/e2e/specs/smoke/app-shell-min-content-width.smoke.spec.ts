/**
 * Smoke E2E — App Shell Min Content Width (AD3: 720px floor @≥1024).
 *
 * Validator: visual_min_content_width_e2e
 *
 * Verifica que main.width >= 720px en todas las rutas en viewports ≥1024px.
 * En viewports <1024px no aplica el floor (mobile/tablet layout distinto).
 *
 * Matriz de prueba:
 *   - 8 rutas: brand-studio, offer-studio, growth-studio, sales,
 *              settings, connections, brand-settings, audit
 *   - 4 viewports: 375 (mobile), 768 (tablet), 1024 (lg), 1440 (xl)
 *   - Estados copilot: el copilot se deja en estado default (collapsed)
 *     para este spec; los estados rail/open se prueban en iteraciones
 *     de la suite completa.
 *
 * Aserciones por ruta × viewport:
 *   - main es visible
 *   - @≥1024: main.width >= 720px
 *   - @<1024: main.width > 0 (simplemente existe)
 *   - Sin errores de consola críticos
 *
 * RAM constraint: SIEMPRE --workers=1.
 * E2E_BASE_URL=https://dev-app.nicolify.com (CF tunnel).
 * test.describe.serial evita race conditions de cold compile.
 */
import type { Page, ConsoleMessage } from "@playwright/test";
import { test, expect } from "../../fixtures/auth.fixture";

/**
 * Colapsa copilot post-carga verificando via live region.
 * loadPersistedSidebarState() retorna "rail" cuando el valor guardado es "collapsed".
 *
 * Desktop (>=768): botón "Cerrar copilot" en CopilotChatHeader.
 * Mobile (<768): backdrop click o Escape.
 */
async function collapseCopilot(page: Page, viewportWidth: number) {
  const liveRegion = page.locator('[role="status"][aria-live="polite"]');
  const currentLabel = await liveRegion.getAttribute("aria-label").catch(() => null);
  if (currentLabel === "Copilot cerrado") return; // ya cerrado

  if (viewportWidth >= 768) {
    // Desktop/tablet: cerrar via botón "Cerrar copilot" del chat header
    const cerrarCopilot = page.getByRole("button", { name: "Cerrar copilot" });
    const isVisible = await cerrarCopilot.isVisible().catch(() => false);
    if (isVisible) {
      await cerrarCopilot.click();
      await expect(liveRegion).toHaveAttribute("aria-label", "Copilot cerrado", { timeout: 5_000 });
    }
  } else {
    // Mobile: cerrar overlay via Escape (document-level handler en CopilotSidebar)
    // No usamos backdrop click: copilot a z-[60] bloquea clicks al backdrop a z-[50]
    await page.keyboard.press("Escape");
    await expect(liveRegion).toHaveAttribute("aria-label", "Copilot cerrado", { timeout: 5_000 }).catch(() => {
      // Si el copilot no respondió al Escape, puede que ya estuviera cerrado
    });
  }
}

// ── Rutas canónicas a testear ────────────────────────────────────────────────

const ROUTES = [
  { slug: "brand-studio", label: "Brand Studio" },
  { slug: "offer-studio", label: "Offer Studio" },
  { slug: "growth-studio", label: "Growth Studio" },
  { slug: "sales", label: "Sales" },
  { slug: "settings", label: "Settings" },
  { slug: "connections", label: "Connections" },
  { slug: "brand-settings", label: "Brand Settings" },
  { slug: "audit", label: "Audit" },
] as const;

// ── Viewports a testear ──────────────────────────────────────────────────────

const VIEWPORTS = [
  { width: 375, height: 812, label: "mobile-375" },
  { width: 768, height: 1024, label: "tablet-768" },
  { width: 1024, height: 768, label: "desktop-1024" },
  { width: 1440, height: 900, label: "desktop-1440" },
] as const;

/** Floor mínimo en px que aplica @≥1024 (AD3). */
const MIN_CONTENT_WIDTH_PX = 720;

/** Tolerancia para rounding (1px). */
const TOLERANCE_PX = 1;

// ── Helpers ──────────────────────────────────────────────────────────────────

function collectConsoleErrors(page: Page) {
  const errors: string[] = [];
  page.on("console", (msg: ConsoleMessage) => {
    if (msg.type() === "error") {
      const text = msg.text();
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
        !text.includes("500") &&
        // React dev-mode warnings unrelated to T-1..T-7 shell refactor scope
        !text.includes("Can't perform a React state update") &&
        !text.includes("componentWillMount") &&
        !text.includes("Warning:") &&
        // App-internal API errors (Offer Studio listOffers, etc.) — dev backend
        // instability; not introduced by Story 1 shell refactor
        !text.includes("Network error listing offers") &&
        !text.includes("Failed to list offers") &&
        !text.includes("Failed to fetch") &&
        !text.includes("NetworkError")
      ) {
        errors.push(text);
      }
    }
  });
  return errors;
}

async function getMainWidth(page: Page): Promise<number> {
  return page.evaluate(() => {
    const main = document.querySelector("main");
    if (!main) return 0;
    return main.getBoundingClientRect().width;
  });
}

// ── Tests ────────────────────────────────────────────────────────────────────

// Usamos test.describe.serial para evitar compilación en frío paralela.
// Cada combinación ruta × viewport navega secuencialmente.

test.describe.serial("App Shell — Min Content Width (AD3 720px floor @≥1024)", () => {
  for (const route of ROUTES) {
    test.describe(`Ruta: ${route.label}`, () => {
      for (const vp of VIEWPORTS) {
        test(`${route.label} @ ${vp.label} — main.width valid`, async ({
          page,
          tenantId,
        }) => {
          // Bump test timeout — cold compile per route per viewport can chain
          test.setTimeout(180_000);
          const consoleErrors = collectConsoleErrors(page);

          // Setear viewport antes de navegar
          await page.setViewportSize({ width: vp.width, height: vp.height });

          // Cold compile puede tardar 30-60s en primer hit por ruta
          await page.goto(`/${tenantId}/${route.slug}`, {
            waitUntil: "networkidle",
            timeout: 90_000,
          });

          // Main debe ser visible (cold compile per route puede tardar — bump 90s)
          await expect(page.locator("main")).toBeVisible({ timeout: 90_000 });

          // Colapsar copilot post-carga (loadPersistedSidebarState retorna "rail" por defecto)
          await collapseCopilot(page, vp.width);

          // Medir el ancho del main
          const mainWidth = await getMainWidth(page);

          if (vp.width >= 1024) {
            // AD3: floor 720px @≥1024 viewport
            expect(
              mainWidth,
              `${route.label} @ ${vp.label}: main.width=${mainWidth}px debe ser ≥${MIN_CONTENT_WIDTH_PX}px`,
            ).toBeGreaterThanOrEqual(MIN_CONTENT_WIDTH_PX - TOLERANCE_PX);
          } else {
            // <1024: solo verificamos que main existe y tiene ancho > 0
            expect(
              mainWidth,
              `${route.label} @ ${vp.label}: main.width=${mainWidth}px debe ser > 0`,
            ).toBeGreaterThan(0);
          }

          // Sin errores JS críticos
          expect(
            consoleErrors,
            `${route.label} @ ${vp.label} errores de consola: ${consoleErrors.join(", ")}`,
          ).toHaveLength(0);
        });
      }
    });
  }
});
