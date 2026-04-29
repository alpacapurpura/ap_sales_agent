# analytics — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Growth |
| Estado | activo |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_analytics.md` |

## Qué hace por el user
ETL + dashboards. Visualiza desempeño marketing/ventas end-to-end via diagrama Bowtie (Vistas → Leads → Clientes → Reventas). User ve dónde está sangrando dinero, dónde puede optimizar.

## Capacidades actuales
- ETL pipeline 12+ providers (Meta, Google Ads, GA4, Shopify, MailerLite, Mercado Pago, Manychat, etc)
- Bowtie funnel visualization (interactive)
- Action triggers (clic en nodo → right slider con accion ejecutable)
- Stage services (Attraction, Capture, Nurture, Convert, Retain)
- Channel registry SSoT
- Progressive loading (4 tiers)
- Cache warming
- Verification layer (4-layer protocol: ETL execution → source probe → pipeline integrity → UI fidelity)
- Multi-currency (per-channel detection)
- Multi-timezone
- Period vs daily metrics correctness (Meta time_increment=1)
- Extraction contract (SSoT) sincronizado código + docs

## Capacidades operables desde copilot
- Preguntas sobre métricas (parcial)
- Diagnóstico "por qué bajó X" (parcial)
- **Gap:** crear campaña desde nodo Bowtie conversacionalmente
- **Gap:** ajustar copy ad desde Growth Studio conversacionalmente

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| ETL providers | sólido | 12+ providers, idempotente |
| Bowtie visual | sólido | Interactive, end-to-end |
| Verification layer | sólido | 4-layer protocol |
| Action triggers | parcial | UI existe, integraciones limitadas |
| Stage services | sólido | DDD compliant, progressive loading |
| Multi-currency | sólido | TenantLocale-driven |
| Email-stage channels | sólido | `email-{stage}` slugs |
| Meta provider | sólido | Period invariants enforced |
| Google providers | sólido | GA4 + Ads completos |

## Conexiones cross-módulo
- **Lee de:** connections, crm, offer (ports)
- **Lo lee:** copilot, connections, offer

## Dolor user / oportunidades detectadas
_Pendiente captura. Hipótesis: action triggers → expansión es siguiente palanca de valor._

## PIs históricos
| PI | Cambio | Fecha cierre |
|---|---|---|
| ETL Google complete | GA4 + Ads, 5 bugs fixed | 2026 |
| Verification layer | 4-layer protocol pipeline | 2026 |

## Decisiones producto vinculadas
| Fecha | Decisión | Razón |
|---|---|---|
| Permanente | Currency desde data source, nunca hardcoded | Multi-tenant LATAM |
| Permanente | Datetime UTC en DB siempre | Multi-timezone |
