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

## Capacidades actuales
- Login / signup vía Clerk (email + password, OAuth Google)
- Onboarding inicial (datos básicos negocio)
- Resolver tenant correcto desde sesión
- Permisos por rol (owner, member — nivel básico)
- Settings de cuenta + perfil de negocio

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

## PIs históricos
| PI | Cambio | Fecha cierre |
|---|---|---|
| _ninguno aún_ | | |

## Decisiones producto vinculadas
| Fecha | Decisión | Razón | PI/PR |
|---|---|---|---|
| 2026-04-20 | `business_types` migrado de BrandIdentity → tenant_profile BC | Separar config tenant de identidad marca | — |
