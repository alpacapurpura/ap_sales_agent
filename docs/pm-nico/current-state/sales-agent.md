# sales_agent — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Sales |
| Estado | activo (en mejora — PI-3) |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_sales_agent.md` |

## Qué hace por el user
AI SDR autónomo. Conversa con leads en canales conectados, pre-califica, maneja objeciones, agenda citas, envía links de pago, da seguimiento. Reemplaza función de un setter humano.

## Capacidades actuales
- Multi-canal (IG/FB DM vía Manychat, WhatsApp via TODO)
- Conversación con tone propio del tenant (vía PersonalityProfile compilado)
- Pre-calificación de leads (extrae fit con buyer persona)
- Manejo objeciones (RAG + brand authority)
- Agendamiento (integra scheduling module)
- Envío link pago (Mercado Pago / Stripe / etc)
- Follow-up engine
- Specialist agents (closer, follow-up, eval-loop)
- Semantic router → tier pricing (Kimi K2.5 / DeepSeek V3 / GPT-4o por complejidad)
- Trazabilidad turn-a-turn
- Eval loop con goldens
- Per-tenant prompt caching (cache hit rate optimizado)
- Outbox migration ready behind `USE_OUTBOX_PATTERN_SALES_AGENT` flag (OFF default; PI-1 S0 PR-1) — emisores (`event_bus`, `scheduling/payment_event_handlers`, tools, orchestrator, workers, webhooks) routean vía `EventBusAdapter` que detecta flag y enquea a `domain_event_outbox` cuando ON

## Capacidades operables desde copilot
- Activar / pausar agente (sólido)
- Ver últimas conversaciones (parcial)
- Ajustar voz vía Brand Studio communication-style (sólido)
- **Gap:** conversación natural con copilot sobre cómo ajustar comportamiento agente

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Conversación core | sólido | Redesign 2026-04 finalizado |
| Voz marca | sólido | SSoT en `personality_profiles.system_instruction` |
| Tools (scheduler, payment) | sólido | |
| Observabilidad | sólido | trazas + cost tracking + cycle billing 25-25 |
| Multi-canal | parcial | IG/FB OK, WhatsApp pendiente |
| Prompt cache | sólido | Per-tenant key |

## Conexiones cross-módulo
- **Lee de:** crm, brand, offer, connections, scheduling
- **Lo lee:** copilot, connections

## Dolor user / oportunidades detectadas
_Pendiente captura._

## PIs históricos
| PI | Cambio | Fecha cierre |
|---|---|---|
| sales-agent-redesign-s12 | Redesign completo, 12 sprints | 2026-04 |

## Decisiones producto vinculadas
| Fecha | Decisión | Razón |
|---|---|---|
| 2026-04-28 | Voz vive en personality_profile compilado, slot 5 BRAND_VOICE | SSoT + cache per-tenant + sin fine-tune |
| 2026-04 | Tier pricing semantic routing | Optimizar costo (Kimi 200k context tier) |
