---
module: Tenant Domains
status: active
---

# Tenant Domains

Gestiona dominios personalizados y subdominios de plataforma (`{slug}.nicolify.com`) para cada tenant. Integra con Cloudflare Custom Hostnames para SSL automatico y Workers KV para el routing hostname-to-tenant.

## Conceptos de Dominio

- **DomainType**: `platform` (subdominio `*.nicolify.com`) o `custom` (dominio propio del tenant).
- **DomainStatus**: ciclo de vida `pending_verification` -> `verifying` -> `active` | `failed` | `suspended`.
- **Verificacion**: los dominios custom pasan por verificacion DNS via Cloudflare (CNAME + TXT records). Un worker ARQ (`poll_domain_verification`) re-verifica cada 5 minutos los dominios pendientes.
- **is_primary**: flag que determina cual dominio usa el tenant como URL principal (booking pages, landing pages).

## Decisiones de Arquitectura

- **Cloudflare Custom Hostnames API** para SSL SaaS (DV certificates automaticos).
- **Workers KV** como tabla de routing: hostname -> tenant_id. Permite que un Cloudflare Worker resuelva el tenant sin golpear la DB.
- **Deteccion de conflictos**: antes de registrar un dominio custom, se resuelve el DNS del root domain contra IPs conocidas (e.g. Shopify) y se sugiere un subdominio alternativo.
- **Graceful degradation**: si Cloudflare no esta configurado (dev/staging), las operaciones CF son no-ops silenciosos.

## Reglas de Negocio

- Solo un dominio puede ser `is_primary=true` por tenant. Al marcar uno como primary, los demas se desmarcan.
- Los subdominios platform se crean en estado `ACTIVE` (no requieren verificacion). Los custom inician en `PENDING_VERIFICATION`.
- Soft delete: al eliminar un dominio se limpia el Custom Hostname en CF y la entrada en KV.

## Dependencia Cruzada

- `scheduling.application.booking_url` importa `tenant_domains` para resolver la URL base de booking pages: si el tenant tiene un dominio primary activo, lo usa; si no, cae a `DASHBOARD_DOMAIN`.

## CRITICO — No Violar

- Todo query filtra por `tenant_id` (excepto `get_by_hostname` que es lookup global para routing).
- Nunca hard-delete: usar `deleted_at` + `soft_delete()`.
- Nunca exponer `cloudflare_hostname_id` ni tokens internos de CF en respuestas publicas.
