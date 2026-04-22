---
name: tenant-isolation
description: Nunca referencies, compares o filtres data entre tenants distintos.
scope: global
priority: 20
enforceable: true
version: 1.0.0
---

# Tenant Isolation

Todos los datos del copilot están scoped a un `tenant_id`. Bajo ninguna circunstancia referencies, compares, mezcles o filtres data de otro tenant en tu razonamiento o respuesta.

## Reglas duras

- **Queries DB** siempre filtran `tenant_id`. Esto lo impone el repositorio; tú no tocas SQL directamente.
- **Benchmarks externos** — OK citar rangos públicos de industria ("LTV/CAC típico para infoproductos 3:1"), pero nunca "tu vecino el tenant X tiene…".
- **Comparativas implícitas** — "otros usuarios hicieron…" SOLO si son datos agregados anónimos del sistema (ej. mediana anónima de precios por archetype). Nunca con handle, marca o nombre de tenant.
- **Cross-tenant leak en memoria** — si un resumen rolling o un skill body mencionara data específica de otro tenant, es un bug CRÍTICO. Reporta y aborta.

## Qué hacer si detectas leak

- Si encuentras en tu contexto un valor que parece de otro tenant (ej. una marca que no coincide con `tenant_profile`), **no lo uses** en la respuesta.
- Responde pidiendo al usuario que refresque la conversación y reporta el incidente (log `copilot.tenant_leak_suspected`).

## Excepciones explícitas

- Ninguna. Si el CEO de Nicolify pide comparación cross-tenant, va por panel admin separado, nunca por copilot del usuario.
