# Cloudflare Domain Router — Setup Guide

## Architecture

```
Custom Domain / *.nicolify.com
        ↓
  Cloudflare Worker (this)
        ↓ injects X-Tenant-ID, X-Public-Site
  Traefik → Next.js
```

## One-Time Setup

### 1. Create Workers KV Namespace

```bash
wrangler kv:namespace create "nicolify-domains"
wrangler kv:namespace create "nicolify-domains" --preview
```

Copy the returned `id` values into `wrangler.toml`.

Add to `.env` and `.env.prod`:
```
CLOUDFLARE_KV_NAMESPACE_ID=<namespace-id>
```

### 2. Deploy the Worker

```bash
cd infrastructure/cloudflare
wrangler deploy
```

### 3. Configure DNS — Platform Subdomains

In Cloudflare DNS for `nicolify.com`:
- Add record: `* CNAME app.nicolify.com` (Proxied ✅)
- This makes `{slug}.nicolify.com` resolve through Cloudflare

### 4. Add Worker Route

In Cloudflare Workers → Triggers → Routes:
- `*.nicolify.com/*` → `nicolify-domain-router`

For `app.nicolify.com`, the worker passes through directly (line 12 of worker.js).

### 5. Configure Cloudflare for SaaS (Custom Domains)

1. Go to your zone → SSL/TLS → Custom Hostnames
2. Set fallback origin to: `app.nicolify.com`
3. Enable "Cloudflare for SaaS"

Custom hostnames registered via the API (Phase 2) will auto-provision SSL.

### 6. Set Env Vars in Backend

Add to `.env` (dev, no real values needed) and `.env.prod` (real values):
```
CLOUDFLARE_ZONE_ID=your-zone-id
CLOUDFLARE_API_TOKEN=your-api-token-with-custom-hostname-write
CLOUDFLARE_KV_NAMESPACE_ID=your-kv-namespace-id
CLOUDFLARE_ACCOUNT_ID=your-account-id  # already set for R2
```

## KV Entry Format

```json
{
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "slug": "visionarias",
  "type": "platform"
}
```

Key = hostname (e.g., `visionarias.nicolify.com` or `go.visionarias.lat`).

## Testing Locally

```bash
# Simulate Worker behavior with curl
curl -s -H "X-Tenant-ID: <uuid>" -H "X-Public-Site: true" \
  https://app.nicolify.com/landing/test-slug
```

## Updating KV Entries

KV entries are managed automatically by the backend `DomainService`:
- `create_platform_domain()` → writes KV entry
- `create_custom_domain()` + `verify_domain()` → writes KV after verification
- `delete_domain()` → deletes KV entry
