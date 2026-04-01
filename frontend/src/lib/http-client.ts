import * as Sentry from "@sentry/nextjs";
import { config } from "./config";

/**
 * Wrapper alrededor de fetch nativo que intercepta errores 403.
 * Si la respuesta es 403 (Forbidden), redirige a la página /forbidden.
 */
export async function fetchClient(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  // Clone init to avoid mutation side effects, or create new if undefined
  const config = { ...init };
  const headers = new Headers(config.headers || {});

  // Inject Tenant ID from LocalStorage for strict multi-tenancy
  if (typeof window !== "undefined") {
    let tenantId = localStorage.getItem('x-tenant-id');

    // PRIORITIZE URL Source of Truth
    try {
        const pathSegments = window.location.pathname.split('/').filter(Boolean);
        if (pathSegments.length > 0) {
            const firstSegment = pathSegments[0];
            const globals = ['sign-in', 'sign-up', 'forbidden', 'visit', 'api', 'p', 'onboarding', 'settings', 'admin', 'dashboard', '_next', 'connections', 'static', 'favicon.ico'];
            if (!globals.includes(firstSegment)) {
                 tenantId = firstSegment;
            }
        }
    } catch (e) { }

    if (tenantId) {
      headers.set('X-Tenant-ID', tenantId);
    }
  }

  const finalConfig: RequestInit = { 
      ...config,
      headers: headers
  };

  // Ejecutar la petición original con headers inyectados
  const response = await fetch(input, finalConfig);

  // Capturar errores 5xx en Sentry (sanitize URL: strip query params and UUIDs)
  if (response.status >= 500) {
    const rawUrl = input instanceof URL ? input.pathname : typeof input === "string" ? input : "request";
    const sanitizedUrl = rawUrl
      .split("?")[0]
      .replace(/\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi, "/[id]");
    Sentry.captureMessage(`API ${response.status}: ${sanitizedUrl}`, {
      level: "error",
      extra: { status: response.status, method: finalConfig.method ?? "GET" },
    });
  }

  // Interceptor de errores
  if (response.status === 403) {
    // Redirección del lado del cliente
    if (typeof window !== "undefined") {
      // Usamos window.location para asegurar una redirección completa
      window.location.href = "/forbidden";
    }
  }

  // Interceptor de sesión expirada (401)
  if (response.status === 401) {
    if (typeof window !== "undefined") {
      // Redirigir al login si el token es inválido o expiró
      // Clerk manejará la redirección de vuelta tras el login
      window.location.href = "/sign-in";
    }
  }

  return response;
}
