---
module: iam
last_audit: 2026-05-04
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/iam/"
  stories_dir: "../stories/iam/"
  domain_doc: "../../domains/module_iam.md"
active_projects: []                              # auto-populated by /pm cuando hay PIs activos tocando este módulo
---

# iam — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Supporting |
| Estado | activo |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_iam.md` |

## Qué hace por el user
Identidad + acceso. User entra a Nicolify, se autentica, opera dentro de su tenant aislado. Sin esto nada existe.

## Capacidades
> Auto-list generated from `docs/product/capabilities/iam/`.
> See `docs/product/BACKLOG.md` "Capabilities snapshot" for current count + status.

## Capacidades operables desde copilot
- Update perfil negocio (vía `/settings/perfil-negocio`) — parcial
- **Gap:** invitar member nuevo conversacionalmente

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Auth Clerk | sólido | Estable. Token refresh OK. |
| Tenant resolution | sólido | `X-Tenant-ID` middleware en todas rutas |
| Onboarding | parcial | Existe pero dolorless onboarding flow podría ser conversacional |
| Roles avanzados | placeholder | Solo owner/member básico hoy |

## Conexiones cross-módulo
- **Lee de:** —
- **Lo lee:** todos los módulos (`get_current_user`, `get_tenant_context`)

## Dolor user / oportunidades detectadas
_Pendiente captura primera entrevista user._

## Capacidades admin (PI-1 S0 PR-2)

### plan_config + tenant_subscription + Streamlit /planes-billing
- Introducida: PR-2 (PI-1, S0, commit `14b8b38a`, 2026-04-29)
- Estado: live (admin-only — no user-facing API pública todavía)
- Operable copilot: no (infra admin)
- Surface admin: Streamlit `/planes-billing` — CRUD plans + suscripciones tenant + toggle `is_default` atómico
- Tablas: `plan_config` (5 planes: free/basic/intermediate/advanced/ultra) + `tenant_subscriptions` (1 row per tenant)
- Invariante: exactamente 1 plan con `is_default=TRUE` (partial unique index `uq_plan_config_one_default`; Streamlit toggle atómico; `BillingDefaultPlanMissingError` fail-fast)
- Overrides per-tenant: `tenant_subscriptions.custom_overrides JSONB` — soporta `{"llm_budget_total_usd": X, "max_outbound_msg_per_day": Y}` para enterprise; `PlanService.get_effective()` mergea sobre plan base con cache 5min + Redis pub/sub invalidación cross-instance
- Planes default: free ($5 LLM budget) / basic ($15) / intermediate ($30) / advanced ($45) / ultra ($95). Editables via admin sin migration.

## PIs históricos
| PI | Cambio | Fecha cierre |
|---|---|---|
| PI-1 S0 PR-2 | plan_config + tenant_subscription + /planes-billing admin | 2026-04-29 |

## Decisiones producto vinculadas
| Fecha | Decisión | Razón | PI/PR |
|---|---|---|---|
| 2026-04-20 | `business_types` migrado de BrandIdentity → tenant_profile BC | Separar config tenant de identidad marca | — |
