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
    // If we are in a tenant route /[tenantId]/..., that ID overrides localStorage
    try {
        const pathSegments = window.location.pathname.split('/').filter(Boolean);
        const firstSegment = pathSegments[0];
        // Exclude known global routes
        const globals = ['sign-in', 'sign-up', 'forbidden', 'visit', 'api', 'p', 'onboarding', 'settings', 'admin', 'dashboard', '_next'];
        if (firstSegment && !globals.includes(firstSegment)) {
            tenantId = firstSegment;
            // Sync strictly to avoid drift
            if (localStorage.getItem('x-tenant-id') !== tenantId) {
                console.log(`[fetchClient] Syncing localStorage to URL tenant: ${tenantId}`);
                localStorage.setItem('x-tenant-id', tenantId);
            }
        }
    } catch (e) {
        // Ignore parsing errors
    }

    if (tenantId) {
      headers.set('X-Tenant-ID', tenantId);
      
      // CRITICAL: Cache Partitioning
      // Append tenant ID to GET requests to force browser cache isolation
      // This prevents "stale data" from previous tenants appearing
      if (!config.method || config.method.toUpperCase() === 'GET') {
          try {
              // Handle input if it's a string or URL
              let urlStr = input.toString();
              // If input is relative, we need a base to parse URL
              // If it starts with http, use it. If not, use window.location.origin (if browser) or dummy.
              const isAbsolute = urlStr.startsWith('http');
              const base = isAbsolute ? undefined : (typeof window !== 'undefined' ? window.location.origin : 'http://localhost');
              
              const urlObj = new URL(urlStr, base);
              if (!urlObj.searchParams.has('_t')) {
                  urlObj.searchParams.append('_t', tenantId);
                  // If we added the base just for parsing, remove it if original was relative
                  if (!isAbsolute && base) {
                      // urlObj.toString() returns full URL. 
                      // If input was relative, we want to keep it relative or use the full one?
                      // fetch accepts full URL. So returning full URL is safe.
                      input = urlObj.toString();
                  } else {
                      input = urlObj.toString();
                  }
              }
          } catch (e) {
              console.warn("[fetchClient] Failed to append cache buster:", e);
          }
      }

      console.log(`[fetchClient] Injected X-Tenant-ID: ${tenantId}`);
    } else {
        console.log(`[fetchClient] No X-Tenant-ID found`);
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
