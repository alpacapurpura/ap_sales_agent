# Sales Agent Redesign 2026-04

Plan de evolución arquitectónica de `sales_agent` para alcanzar madurez de copilot a nivel de **infraestructura cross-cutting** (observabilidad event-sourced, PII sanitization, cost guardrails, cache-friendly prompts, fitness tests, registries) **sin perder identidad de dominio** (StateGraph lineal qualifier→closer, Closer Studio, smart debounce, multi-channel webhooks).

Adicionalmente expande capacidades de negocio:
- Voz de marca real (lee `Estilo Comunicacional` de Brand Studio → no más identidad genérica).
- Scheduler tool (lead-specific booking link, verificación de reserva, follow-up automático).
- Payment lifecycle tool (create link → verify paid → grant access).
- Eval loop (judge + goldens) para no regresar.

Estructura espejo del redesign de copilot. Cada fase = research fresco + diseño + TDD + ejecución + learnings + prompt para la siguiente.

---

## Mapa de documentos

| Doc | Para qué |
|---|---|
| [00-vision-and-objectives.md](00-vision-and-objectives.md) | Visión de negocio, objetivos, lo que NO se toca |
| [01-master-plan.md](01-master-plan.md) | DAG completo de 11 fases + dependencias |
| [02-architecture-target.md](02-architecture-target.md) | Topología destino: capas, módulos, contratos |
| [03-phase-protocol.md](03-phase-protocol.md) | Protocolo obligatorio por fase (9 pasos) |
| [04-principles.md](04-principles.md) | Principios senior: GoF, DRY, cohesión, acoplamiento, TDD, anti-parche |
| [05-tech-debt-log.md](05-tech-debt-log.md) | Registro vivo de deuda técnica detectada cross-fase |
| [06-glossary.md](06-glossary.md) | Términos clave |
| `phases/S{N}-*.md` | Una por fase: research mandate + diseño + plan TDD |
| `learnings/S{N}-*.md` | Aprendizajes generados al cerrar cada fase (fill in al final) |
| `prompts/S{N}-start.md` | Prompt exacto para iniciar conversación nueva en esa fase |

---

## Estado de fases

| # | Fase | Estado | Entregable principal |
|---|---|---|---|
| S0 | [shared/agent_observability extract](phases/S0-shared-observability-extract.md) | 📋 PLANNED | Módulo `src/shared/agent_observability/` (zero behavior change) |
| S1 | [sales_agent observability parity](phases/S1-sales-agent-observability-parity.md) | 📋 PLANNED | Callback handler + tablas event-sourced + PII sanitization |
| S2 | [cost guardrails cross-agent](phases/S2-cost-guardrails.md) | 📋 PLANNED | BillingCycleService + alerts + dashboard `/costo-agentes` |
| S3 | [prompt cache_boundary refactor](phases/S3-prompt-cache-boundary.md) | 📋 PLANNED | `compose_system_prompt` con prefix ≥1024 tokens, hit rate ≥60% |
| S4 | [ChatModelSpec + tier adoption](phases/S4-chatmodelspec-tier.md) | 📋 PLANNED | `CHAT_MODEL_SPEC` + tier system para sales_agent |
| S5 | [channel format registry](phases/S5-channel-registry.md) | 📋 PLANNED | `register_channel` cross-agent + format_for_channel determinístico |
| S6 | [fitness tests ratchet](phases/S6-fitness-tests-ratchet.md) | 📋 PLANNED | Anchors + ratchet imports + invariants |
| S7 | [brand voice integration](phases/S7-brand-voice-integration.md) | 📋 PLANNED | Lighthouse de Brand Studio → identity rendering |
| S8 | [tools: scheduler integration](phases/S8-tools-scheduler.md) | 📋 PLANNED | Booking link + verify + follow-up cadence |
| S9 | [tools: payment lifecycle](phases/S9-tools-payment-access.md) | 📋 PLANNED | Payment link + verify + grant access |
| S10 | [quality eval loop](phases/S10-quality-eval-loop.md) | 📋 PLANNED | Judge multi-rubric + goldens + weekly cron |

Estados: 📋 PLANNED / 🚧 IN_PROGRESS / ✅ DONE / ⛔ BLOCKED

---

## Cómo arrancar

1. Lee [03-phase-protocol.md](03-phase-protocol.md) — protocolo 9 pasos obligatorio.
2. Lee [04-principles.md](04-principles.md) — principios senior no negociables.
3. Abre `prompts/S0-start.md` — copia el contenido y pégalo en una conversación nueva.
4. Esa conversación ejecuta S0 completo, deja `learnings/S0-*.md` y `prompts/S1-start.md` listos.
5. Siguiente conversación: pega `prompts/S1-start.md`. Y así.

---

## Reglas anti-deriva

- **No saltarse research fresco.** Cada fase tiene "Research mandate" — ejecutar SIEMPRE (web + context7/Tessl + lectura code).
- **No ampliar scope.** Si se descubre oportunidad → `learnings/` como recomendación o `05-tech-debt-log.md` como ítem. No al código en curso.
- **No agregar parches.** Bug ajeno detectado → validar (¿es bug? ¿impacto?) → fix limpio + log en `05-tech-debt-log.md`. Sin band-aids.
- **No romper §3 de [00-vision-and-objectives.md](00-vision-and-objectives.md).**
- **TDD obligatorio.** Test reproductor antes de cualquier fix. RED → GREEN → REFACTOR.
- **Spanish neutro LATAM** en todo user-facing (sin voseo).
