# Visión + Coverage F-pos

## §1 Visión

> **Cerrar los 4 gaps UX que TP11 destapó para llegar a "feel like Claude Code" 8/8.**

TP11 cerró el plan testing-2026-04 con score 4.5/8. Los 4 fixes deferred §4.4 son cross-stack o requieren coordinación que excedió scope TP11 — viven en este plan F-pos como fases dedicadas (FP1-FP4).

---

## §2 Bugs target

| FP | Bug ID | Descripción | TP origen | Capa |
|---|---|---|---|---|
| FP1 | B22 | ProposalCard apply silent no-op sin activeBridge | TP11 J1 | FE+BE |
| FP2 | B24 | format_for_channel no auto-trigger por keyword | TP11 J2 | BE |
| FP3 | B25 | Routing classifier sequential bloquea TTFB | TP11 J1.T1 | BE |
| FP4 | B23.1 | Voseo cleanup en 9 prompts remaining | TP11 J4 residual | BE |

Detalle por bug en `phases/FP{N}-*.md`.

---

## §3 Lo que NO está en scope F-pos

### §3.1 Otros bugs deferred TP1-TP10

A1 (OpenAI quota), A3 (Lighthouse route-gated), A4 (TPM 30k), A5 (cost_usd cache discount), A6 (Qwen 401), TP4-B5 (llm_call event), TP4-B6 (intent classifier), TP5-B9 (F6 cutover), TP5-B10 (awareness narrow except), TP6-B11 (Kimi compliance), B12-TP7 (Qdrant version), B16-TP8 (F9 docstring), B19-TP9 (latency target unrealistic).

Estos son bugs heredados pero NO destapados como crítico en TP11. Plan separado o F-pos siguiente si vuelven.

### §3.2 Capacidades nuevas

NO se agregan capacidades nuevas. Solo cierre de bugs identificados.

### §3.3 Re-architecture

NO refactor estructural mayor (e.g. cambiar deepagents → langgraph nativo, o swap providers). Solo fixes pinpoint.

---

## §4 Definición de "FP terminado"

Un FP está cerrado **solo si**:

1. Pre-research ejecutado (`04-protocol.md` paso 1-2).
2. Cada AC del FP tiene **before/after evidence** documentada.
3. TDD: test regresión RED → fix → test GREEN.
4. Live verification — re-run del scenario original que destapó el bug PASA post-fix.
5. Quality gates regresión PASS (lint + tests + arch fitness).
6. Reporte `results/FP{#}-{fecha}.md` con AC checklist + métricas.
7. Commit + push conventional.
8. Handoff prompt FP{N+1} generado (excepto FP3 = último).
9. Spanish neutro LatAm en user-facing tocado (regla 11).

Sin alguno de los 9 puntos, FP **no está cerrado**.

---

## §5 Modelo de costo

F-pos consume tokens menos que TPs (no son journeys end-to-end exhaustivos). Estimación:

| FP | LLM calls testing | Provider mix | Cost USD |
|---|---|---|---|
| FP1 | ~6 turns (re-run J1 setup brand pre+post fix) | Kimi K2.6 + OpenAI NANO | ~$0.05 |
| FP2 | ~4 turns (J2 channel detection variants) | Kimi K2.6 | ~$0.03 |
| FP3 | ~10 turns (TTFB measurement + quality regression sample) | full mix | ~$0.08 |
| FP4 | ~2 turns (J4 + J2 voseo verification post-fix) | Kimi K2.6 | ~$0.015 |
| **Total** | ~22 calls | — | **~$0.18** |

vs target plan testing TP11 ~$0.117 — F-pos cuestan menos individual pero en agregado similar.

---

## §6 Anti-patrones

- Cerrar FP sin re-run live verification (bug puede seguir vivo aunque tests passen).
- Mockear ProposalCard / channel detection / routing en TDD pero NO probar end-to-end real.
- Spawnear sub-agentes para parallel ACs.
- Skipear schema parity BE↔FE en FP1 (similarmente a B18-TP9 lección).
- Reabrir scope ("ya que estoy aquí, fixeo Y también") — quedarse en el bug específico.
