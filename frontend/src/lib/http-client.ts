import * as Sentry from "@sentry/nextjs";

import { config } from "./config";

const GLOBAL_PATH_SEGMENTS = new Set([
  "sign-in",
  "sign-up",
  "forbidden",
  "visit",
  "api",
  "p",
  "onboarding",
  "settings",
  "admin",
  "dashboard",
  "_next",
  "connections",
  "static",
  "favicon.ico",
]);

/** Extracts tenantId from URL path, falling back to localStorage. */
function resolveTenantId(): string | null {
  let tenantId = localStorage.getItem("x-tenant-id");
  try {
    const pathSegments = window.location.pathname.split("/").filter(Boolean);
    if (pathSegments.length > 0) {
      const firstSegment = pathSegments[0];
      if (!GLOBAL_PATH_SEGMENTS.has(firstSegment)) {
        tenantId = firstSegment;
      }
    }
  } catch {
    // unable to parse tenantId from pathname — proceed without header
  }
  return tenantId;
}

/** Sanitizes a URL for Sentry: strips query params and UUIDs. */
function sanitizeUrlForSentry(input: RequestInfo | URL): string {
  const rawUrl =
    input instanceof URL ? input.pathname : typeof input === "string" ? input : "request";
  return rawUrl
    .split("?")[0]
    .replace(/\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi, "/[id]");
}

/** Handles redirect side-effects for error responses. */
function handleErrorRedirects(status: number): void {
  if (status === 403) {
    window.location.href = "/forbidden";
  }
  if (status === 401 && !window.location.pathname.startsWith("/sign-in")) {
    window.location.href = "/sign-in";
  }
}

/**
 * Wrapper alrededor de fetch nativo que intercepta errores 403/401.
 * Si la respuesta es 403 (Forbidden), redirige a la página /forbidden.
 * Si la respuesta es 401, redirige a /sign-in.
 * Auto-inyecta X-Tenant-ID desde la URL o localStorage.
 */
export async function fetchClient(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const config = { ...init };
  const headers = new Headers(config.headers || {});

  if (typeof window !== "undefined") {
    const tenantId = resolveTenantId();
    if (tenantId) {
      headers.set("X-Tenant-ID", tenantId);
    }
  }

  const finalConfig: RequestInit = { ...config, headers };
  const response = await fetch(input, finalConfig);

  if (response.status >= 500) {
    const sanitizedUrl = sanitizeUrlForSentry(input);
    Sentry.captureMessage(`API ${response.status}: ${sanitizedUrl}`, {
      level: "error",
      extra: { status: response.status, method: finalConfig.method ?? "GET" },
    });
  }

  if (typeof window !== "undefined") {
    handleErrorRedirects(response.status);
  }

  return response;
}
