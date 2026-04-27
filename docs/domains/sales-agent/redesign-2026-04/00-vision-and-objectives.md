# 00 · Visión y objetivos

## §1 — Quién es sales_agent

`sales_agent` = **el mejor SDR + closer del mundo, que habla como la marca del tenant**.

- **SDR**: califica leads, descubre objeciones, agenda demos/llamadas, nurturea hasta cierre.
- **Closer**: maneja objeciones avanzadas, propone oferta correcta, manda link de pago, verifica pago, otorga acceso.
- **Multi-canal**: WhatsApp, Telegram, Instagram DM, web. Conoce el formato de cada uno.
- **Voz de marca**: NO suena a chatbot genérico. Lee el `Estilo Comunicacional` (Brand Studio) del tenant y replica tono, vocabulario, ritmo, emojis, ejemplos, frases prohibidas.
- **Autónomo, supervisado**: agente trabaja solo; humano interviene desde Closer Studio cuando quiere.

Diferencia clave vs copilot:
- **copilot**: asistente del operador del SaaS (in-app, multi-route, exploratorio, deepagents).
- **sales_agent**: vendedor de la empresa del operador (multi-canal externo, lineal con playbook, StateGraph determinístico).

Mismo stack (FastAPI + LangGraph + LangChain), distinto flujo. **NO migrar sales_agent a deepagents** — su valor es la predictibilidad del cierre.

---

## §2 — Objetivos del redesign

### §2.1 — Infraestructura (homologación con copilot)

| # | Objetivo | Métrica de éxito |
|---|---|---|
| O1 | Observabilidad event-sourced (callback handler + tablas tipadas) | Cada turn tiene 1 `turn_start` + 1 `turn_end` + N `llm_call` + N `tool_call` en DB |
| O2 | PII sanitization 100% writes | 0 emails / phones LATAM / tokens en raw |
| O3 | Pricing point-in-time + cost cycle 25-25 | `sales_agent_llm_call.cost_usd` poblado desde snapshot, no inline |
| O4 | Cache hit rate ≥60% en system prompt | Prefix ≥1024 tokens contiguos cacheable |
| O5 | Retention auditable | Worker diario; trace 90d, llm_call 365d |
| O6 | Architectural fitness tests | Ratchet `test_no_new_sales_agent_*` + anchors + invariants |
| O7 | Channel format determinístico | `register_channel` + `format_for_channel` sin LLM |

### §2.2 — Negocio (capacidades nuevas)

| # | Objetivo | Métrica de éxito |
|---|---|---|
| B1 | Voz de marca real (Estilo Comunicacional) | Goldens diff: respuesta del agente para tenant A ≠ tenant B con mismo input cuando sus brand voices difieren |
| B2 | Scheduler tool: link único por lead, tracking, follow-up | Lead reserva → confirmación auto + recordatorio 24h antes + verify-attended después |
| B3 | Payment lifecycle: link → verify → grant access | Lead paga → bot detecta dentro de N segundos → otorga acceso (key, link, código) automático |
| B4 | Quality eval loop | Judge multi-rubric mensual; regresiones detectadas antes de ship |

### §2.3 — No-objetivos del redesign (NO HACER)

1. **NO migrar StateGraph a deepagents.** El playbook lineal qualifier→product_expert→closer→tool_executor es correcto.
2. **NO eliminar Closer Studio + WS.** Es valor único; humanos aman supervisar.
3. **NO eliminar smart_debounce + buffer_service.** WhatsApp/Telegram mandan en bursts; sin buffer el agent pregunta sobre fragmentos.
4. **NO eliminar OutputManager** (typing simulation + chunking). Realismo en canales async.
5. **NO eliminar follow_up_engine + frozen_detection.** Cron-based específico de sales.
6. **NO eliminar PromptVersionModel** (overrides multi-tenant DB-backed). Sales NECESITA override por tenant; copilot resuelve diferente con lighthouse.
7. **NO ampliar scope a CRM** (ese es otro módulo). Sales_agent consume CRM via `shared/links/`.
8. **NO subagents deepagents.** El flujo lineal no se beneficia.

---

## §3 — Lo que NO se toca durante el redesign

| Capa | Razón |
|---|---|
| `closer_studio.py` API + WS endpoints | Live operations dependen. Cualquier cambio rompe Streamlit + frontend ops. |
| `BufferService.smart_debounce` lógica | Tuned con datos reales de canales LATAM. |
| `OutputManager.process_response` chunking | CPM_SPEED + caracter cap calibrados. |
| `enrollment_*` end-to-end | Pago + acceso ya producción. S9 EXTIENDE, no re-escribe. |
| `agent_state_checkpoint` schema | Persist multi-turn lead state. Migración riesgosa. |
| Webhook adapters (Telegram/WhatsApp/IG) | Auth + signature verification frágiles. |
| `follow_up_engine` cadence math | Lógica de timing horaria + zona horaria del tenant. |

Si una fase necesita tocar algo de §3 → **PARAR y preguntar al usuario** antes de proceder.

---

## §4 — Definition of Done por fase

Una fase está cerrada cuando:

1. ✅ Research mandate ejecutado (web + context7/Tessl + lectura code) — fuentes en learnings.
2. ✅ Decisiones de diseño documentadas en `phases/S{N}-*.md` con razones.
3. ✅ TDD: tests RED→GREEN cubriendo TODO el comportamiento target.
4. ✅ Quality gates verdes nativos (ruff, pytest, arch tests).
5. ✅ Verificación funcional manual (curl, browser, trace inspection si aplica).
6. ✅ §3 sigue funcionando (smoke check).
7. ✅ `learnings/S{N}-*.md` escrito (denso, accionable, sin filler).
8. ✅ `prompts/S{N+1}-start.md` actualizado con contexto fresco.
9. ✅ `05-tech-debt-log.md` actualizado si hubo hallazgos.
10. ✅ Commit conventional + push a `development` (solo archivos de la sesión, ver `.claude/rules/parallel-safety.md`).

Si **uno** de los 10 falla → fase NO cerrada.
