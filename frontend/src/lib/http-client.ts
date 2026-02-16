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
    const tenantId = localStorage.getItem('x-tenant-id');
    if (tenantId) {
      headers.set('X-Tenant-ID', tenantId);
    }
  }

  config.headers = headers;

  // Ejecutar la petición original con headers inyectados
  const response = await fetch(input, config);

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
