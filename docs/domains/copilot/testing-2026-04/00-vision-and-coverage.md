# Visión + Coverage del Plan de Testing

## §1 Visión

> **Validar que el copilot Nicolify se siente, opera y cuesta como Claude Code para marketing.**

El plan F0-F11 cerró con métricas internas (tests verde, arch fitness pass, judge avg ≥3.5/5). Faltan tres validaciones que solo se ven en uso real:

1. **Funcional end-to-end:** ¿el flujo crítico del usuario completa sin errores silenciosos? (no basta con que cada componente teste OK aislado).
2. **Económica:** ¿cuánto cuesta cada interacción? Sin esto Chris no puede dimensionar el budget OpenAI mensual.
3. **Experiencial:** ¿el usuario lo percibe natural, intuitivo, "como Claude Code"? Heurísticas observables.

Este plan cubre los tres con 12 TPs paralelos al redesign.

---

## §2 Capacidades target (heredadas del redesign)

| Capacidad redesign | TP que la valida | Métrica de cierre |
|---|---|---|
| URL contextual persistente (F4) | TP3 | Inspiration referenciable en turn 7 igual que turn 2 + judge `coherence` ≥4.0. |
| Brand "lighthouse" (F3) | TP2 | Brand summary aparece en system prompt sin que el user lo pida + judge `brand_coherence` ≥4.0. |
| Q&A datos tenant fuzzy (F5) | TP4 | 10/10 preguntas naturales devuelven respuesta correcta sin SQL crudo en prompt. |
| Workflows unificados (F6) | TP5 | Setup brand + setup offer + extract doc usan mismo runtime sin discrepancias UX. |
| Channel-aware (F7) | TP6 | "Para WhatsApp" devuelve texto copia-pega listo (sin markdown roto). |
| Routing/cost (F8) | TP1 | Cache hit rate ≥60% post-warmup; routing log popula + admin ve data real. |
| Quality observability (F9) | TP8 | Weekly judge tab muestra rows reales; alerta dispara si avg <3.5. |
| RAG curado (F10) | TP7 | 8/8 RAG goldens recall ≥0.8 + judge `citation_accuracy` ≥4.0. |
| Plug-in friendly (F1) | TP10 | Add tool dummy en módulo nuevo sin tocar `copilot/`. |
| Planning visible (F2) | TP9 | `plan_card` aparece en tareas multi-step + write_todos progresa visiblemente. |
| Telemetry routing (F11.1) | TP1 | `copilot_routing_log` populated post-turn + admin `/copilot-routing` muestra data. |
| RAG eval cron (F11.5) | TP8 | Manual run de `weekly_copilot_rag_eval` produce row con `extra_metadata` esperada. |

---

## §3 Lo que NO testeamos en este plan

> Si te encontrás dentro de un TP cuestionando algo de §3, paralo y preguntá al user. NO expandir scope unilateralmente.

### §3.1 Componentes infra ya estables pre-redesign

- **AssetsService + R2 storage + voice transcription** — testeados en sus suites propias. Solo verificamos que el copilot los CONSUME bien (tools `read_document`, `voice_transcribe_and_classify`).
- **SSE v2 protocol low-level** — covered en `tests/modules/copilot/test_streaming_integration.py`. Acá probamos UX percibida (TTFB, fluidez), no el wire format.
- **Clerk auth + tenant middleware** — pre-existente. Acá solo verificamos que `X-Tenant-ID` injection funciona end-to-end.
- **Sidebar 3-state, atajos teclado, mobile sheet, history pagination** — UX pre-redesign del front. Acá verificamos que NO se rompió, no que funcione (testeado en F0 baseline).

### §3.2 Cosas fuera del redesign 2026-04

- **Sales Agent** — módulo separado, plan propio.
- **Fine-tuning modelos propios** — fuera del scope explícito post-F10.
- **WhatsApp inbound del copilot** — el copilot solo emite formato whatsapp, no recibe; coverage en TP6 limitado a output.
- **MCP servers públicos** — provider pattern in-process es suficiente.
- **Generative multimodal** — el copilot solo hace lookup vía `search_assets`, no genera media.

### §3.3 Tests heredados que NO promovemos a TP

- `test_streaming_integration` flaky heredado F0+ — F11 no lo reprodujo. Cubierto como riesgo abierto en F11 learnings; no es TP scope.
- Migration backfill F6 (`procedure_state → workflow_state`) — F12 dedicado. NO se testea en este plan.

---

## §4 Definición de "TP terminado"

Un TP está cerrado **solo si**:

1. Pre-research ejecutado (`04-protocol.md` paso 1).
2. Cada escenario corrió y reportó los **5 ejes** (flujo / calidad / tokens / latencia / UX).
3. Failures con root cause identificado. Fix aplicado o documentado en plan separado.
4. Reporte en `results/TP{#}-{fecha}.md` con: scenarios run, pass/fail, métricas observadas vs targets, diff vs baseline, recomendaciones.
5. `phases/TP#-*.md` actualizado si se descubrieron escenarios nuevos durante la corrida.
6. Quality gates de la suite F0-F11 siguen verde post-cualquier fix arquitectónico (`/test-all` o equivalente).
7. Spanish neutro LatAm en cualquier output user-facing tocado (regla 11).

Sin alguno de los 7 puntos, el TP **no está cerrado**.

---

## §5 Modelo de costo del propio plan (post Sprint 0)

Testing consume tokens. Budget post Sprint 0 (REASONING en DeepSeek,
AGENT en Kimi, NANO/FAST en OpenAI):

| TP | Calls LLM real | Provider mix dominante | Cost estimado USD |
|---|---|---|---|
| TP0 | 0 (smoke infra) | — | $0 |
| TP1 | 30 (routing scenarios) | OpenAI NANO | <$0.001 |
| TP2 | 20 (brand variations) | DeepSeek REASONING | ~$0.005 |
| TP3 | 25 (URL types) | DeepSeek REASONING + Kimi AGENT | ~$0.012 |
| TP4 | 30 (data queries) | DeepSeek REASONING (intent + synth) | ~$0.006 |
| TP5 | 20 (workflows) | DeepSeek + Kimi AGENT | ~$0.012 |
| TP6 | 16 (4 canales × 4 contenidos) | OpenAI FAST + Kimi AGENT | ~$0.008 |
| TP7 | 20 (RAG goldens) | OpenAI NANO judge | <$0.001 |
| TP8 | 50 (quality samples) | OpenAI NANO judge | ~$0.002 |
| TP9 | 15 (planning multi-step) | Kimi AGENT (deepagents harness) | ~$0.020 |
| TP10 | 5 (provider extension) | — | $0 |
| TP11 | 30 (e2e UX flows) | mix Kimi+DeepSeek+OpenAI | ~$0.030 |
| **Total** | ~256 real | — | **~$0.10/run** (3x cheaper que pre-Sprint 0) |

Una corrida full ≈ 10 centavos (vs 30 anterior). Re-run ilimitada.
Si añadís stress (50x scenarios), ≈ $5 (vs $15 anterior).

> Nota anomalías: TP3 A1 (OpenAI quota) ya NO bloquea TPs porque
> REASONING + AGENT no dependen de OpenAI billing. Si OpenAI vuelve a
> 429, sólo NANO/FAST/VISION/EMBEDDING se ven afectados — y con
> `unset AI_PROVIDER_NANO` y similares fallback a global... actually no
> ayuda si global sigue en openai. Preferible pasar AI_PROVIDER_NANO=deepseek
> temporalmente con AI_MODEL_NANO=deepseek-chat para destrabar (más caro
> pero llega a TTFB ~1.5s desde LATAM, aceptable contra ningún servicio).

---

## §6 Anti-patrones (prohibido)

- Cerrar un TP sin medir uno de los 5 ejes "porque no aplica" → si no aplica, eliminar el escenario, no skippear el eje.
- Reportar "todo bien" sin números → cada eje pide número.
- Fixear un failure cambiando el test sin tocar el bug.
- Spawn paralelo de TPs en sub-agentes — cada TP necesita context completo + capacidad de iterar fix; agentes pierden contexto entre exec.
- Mock LLM real cuando el TP exige real-LLM (ver `01-tooling.md`).
