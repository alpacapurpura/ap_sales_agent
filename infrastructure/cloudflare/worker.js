/**
 * Nicolify Domain Router — Cloudflare Worker
 *
 * Routes incoming requests to the origin VPS based on hostname.
 * Resolves tenant identity from Workers KV, injects headers.
 *
 * KV entry format:
 *   Key:   "go.visionarias.lat"
 *   Value: {"tenant_id": "uuid", "slug": "visionarias", "type": "platform"|"custom"}
 *
 * Headers injected to origin:
 *   X-Tenant-ID:    tenant UUID
 *   X-Public-Site:  "true"
 *   X-Original-Host: original hostname
 *   X-Domain-Type:  "platform" | "custom"
 */
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const hostname = url.hostname;

    // Skip worker for first-party Nicolify domains — route directly to origin
    const FIRST_PARTY_DOMAINS = [
      "app.nicolify.com",
      "api.nicolify.com",
      "dev-app.nicolify.com",
      "dev-api.nicolify.com",
    ];
    if (FIRST_PARTY_DOMAINS.includes(hostname)) {
      return fetch(request);
    }

    // KV lookup: hostname → tenant data
    let tenantData;
    try {
      tenantData = await env.DOMAINS_KV.get(hostname, "json");
    } catch (err) {
      console.error("KV lookup failed", { hostname, error: err.message });
      return new Response("Service unavailable", { status: 503 });
    }

    if (!tenantData) {
      return new Response(
        JSON.stringify({ error: "Site not found", hostname }),
        {
          status: 404,
          headers: { "Content-Type": "application/json" },
        }
      );
    }

    // Build proxied request to origin
    const originUrl = new URL(url.pathname + url.search, `https://${env.ORIGIN_HOST}`);
    const originRequest = new Request(originUrl.toString(), {
      method: request.method,
      headers: new Headers(request.headers),
      body: ["GET", "HEAD"].includes(request.method) ? null : request.body,
      redirect: "follow",
    });

    // Inject tenant context headers
    originRequest.headers.set("X-Tenant-ID", tenantData.tenant_id);
    originRequest.headers.set("X-Public-Site", "true");
    originRequest.headers.set("X-Original-Host", hostname);
    originRequest.headers.set("X-Domain-Type", tenantData.type || "custom");

    // Forward to origin
    try {
      const response = await fetch(originRequest);
      return response;
    } catch (err) {
      console.error("Origin fetch failed", { hostname, error: err.message });
      return new Response("Bad gateway", { status: 502 });
    }
  },
};
