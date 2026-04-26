# Copilot F-pos 2026-04 — "Cerrar los gaps UX que TP11 destapó"

Plan dedicado para cerrar los 4 fixes diferidos de `testing-2026-04` (TP11) que llevan al copilot Nicolify de score 4.5/8 a potencial 8/8 "feel like Claude Code".

> **Estado:** plan aprobado, FP1 lista para ejecutar.
> **Owner:** Chris (alpacapurpura).
> **Branch único:** `development` (`.claude/rules/parallel-safety.md`).
> **Modelo de trabajo:** una conversación por FP, igual que el redesign + testing.
> **Plan padre archivado:** `docs/domains/copilot/testing-2026-04/` (12 TPs, 4.5/8 score).

---

## Por qué este plan

TP11 cerró el plan testing-2026-04 con score **4.5/8 = "redesign cumple a nivel código pero NO completamente a nivel UX. Iteración mayor requerida."**

Los 4 fixes deferred §4.4 son cross-stack o requieren coordinación que excedió scope TP11:

| ID | Bug | Impacto | TP origen |
|---|---|---|---|
| **B22** | ProposalCard "Aplicar" silent no-op cuando activeBridge no connected | Setup brand NO completa end-to-end. UI verde "Aplicado" pero `mutation_journal` vacío. | TP11 J1 |
| **B24** | `format_for_channel` tool NO auto-trigger cuando user msg matches WhatsApp/email/sms keywords | H7 canal-aware nunca PASS sin esto. | TP11 J2 |
| **B25** | Routing classifier NANO call sequencial bloquea TTFB ~2.7s | H1 inmediatez breaking point >1500ms 2026 conversational. | TP11 J1.T1 |
| **B23.1** | Voseo en 9 prompt files remaining (B23-TP11 cubrió 2). | H4 tono PARTIAL — final user-facing 0 voseo pero subagent intermediate output filtra. | TP11 J4 post-fix |

Cada bug = 1 fase F-pos (FP1-FP4) con investigación → ejecución → pruebas → aprendizaje → handoff próxima.

---

## Mapping bug → fase

| FP | Bug | Doc | Tiempo estimado | Pre-req hard |
|---|---|---|---|---|
| **FP1** | B22 ProposalCard apply | `phases/FP1-proposal-card-apply.md` | 1-2 días | TP11 cerrado |
| **FP2** | B24 channel_format middleware | `phases/FP2-channel-format-trigger.md` | 4-8 horas | FP1 cerrado (concurrent OK con FP4) |
| **FP3** | B25 routing parallel TTFB | `phases/FP3-routing-parallel-ttfb.md` | 1 día | FP2 cerrado (touch chat orchestrator) |
| **FP4** | B23.1 voseo cleanup amplio | `phases/FP4-voseo-cleanup-amplio.md` | 4 horas | TP11 cerrado (paralelizable con FP1) |

---

## DAG

```
TP11 (testing-2026-04 cerrado) ─┐
                                ├──► FP1 (B22 ProposalCard) ──┐
                                ├──► FP4 (B23.1 voseo) ───────┤
                                                              ├──► FP2 (B24 channel_format) ──► FP3 (B25 TTFB)
                                                              │
                                                              └──► (paralelo OK)
```

- **FP1 + FP4 paralelizables** tras TP11 (toques diferentes: FP1 = FE + BE mutations endpoint; FP4 = solo BE prompts).
- **FP2 secuencial post FP1** porque ambos tocan `chat.py` orchestrator y queremos evitar merge conflicts.
- **FP3 secuencial post FP2** porque introduce parallelism que cambia routing flow.

Si Chris ejecuta serialmente: **FP1 → FP4 → FP2 → FP3**.
Si paraleliza: **FP1 || FP4 → FP2 → FP3**.

---

## Misma lógica que testing-2026-04

Hereda integro `04-protocol.md` del plan padre. Cada FP cumple:

1. **Pre-lectura obligatoria** (igual que TP).
2. **Pre-research fresco** (mínimo 2 web searches del Research mandate).
3. **Plan ejecutable con TaskCreate**.
4. **Ejecución por scenario / acceptance criterion**.
5. **TDD obligatorio** (regla 13 CLAUDE.md): Test RED → fix → Test GREEN → live verification.
6. **Quality gates regresión** post fix arquitectónico.
7. **Reporte `results/FP{N}-{fecha}.md`** con: pre-research + scenarios + métricas + failures + recomendaciones + aprendizajes.
8. **Actualizar `phases/FP{N}-*.md`** si descubre escenarios nuevos.
9. **Commit + push conventional**.
10. **Generar `prompts/FP{N+1}-start.md`** (excepto FP3 que es último — cierre del F-pos batch).

---

## Diferencia vs TP

TPs validaban el redesign **funcionando** end-to-end (testing as exploration). FPs cierran **bugs específicos identificados** (testing as fix-validation).

| Aspecto | TP (testing-2026-04) | FP (fpos-2026-04) |
|---|---|---|
| Objetivo | Descubrir bugs + medir 5 ejes | Cerrar bug específico ya identificado |
| Métrica cierre | Score 8/8 heurísticas | Acceptance criteria específicos del bug |
| Live testing | Chrome DevTools journey real | Re-run scenario que destapó el bug |
| Doc output | `results/TP{N}` con scenarios run | `results/FP{N}` con before/after evidence |
| Handoff | Prompt next TP self-contained | Prompt next FP self-contained |

---

## Reglas non-negotiables (heredadas de testing-2026-04)

1. **Nunca parchar** — root cause obligatorio.
2. **Pre-research fresco** abril 2026.
3. **Native-first** lint/tests/eval WSL nativo, NUNCA `docker exec`.
4. **El plan vive** — nuevos hallazgos commiteados.
5. **Parallel-safety** — branch único `development`, stage por nombre.
6. **TDD mandatorio** (regla 13 CLAUDE.md) — test RED → fix → GREEN.
7. **5 ejes opcional** en FP (no son testing) pero **acceptance criteria SÍ obligatorios**: el bug DEBE quedar reproducible-fixed con evidencia.
8. **Spanish neutro LatAm** (regla 11) en cualquier user-facing tocado.
9. **Score post-FPs:** después de cerrar FP1-FP4, recomendable re-run TP11 J1+J2+J4 selectivos para confirmar score 8/8 alcanzado.

---

## Cómo se usa esta carpeta

Cada FP se ejecuta en **una conversación nueva** de Claude Code, igual que TPs.

1. Para arrancar FP{N}, abrís `prompts/FP{N}-start.md`, copiás fenced block, pegás en conversación nueva.
2. La conversación lee `04-protocol.md` (heredado de testing-2026-04) + `phases/FP{N}-*.md` + `results/FP{N-1}-*.md` (si N≥2).
3. Pre-research mandatorio.
4. Ejecuta scenarios + TDD inline.
5. Reporta findings en `results/FP{N}-{fecha}.md`.
6. Genera `prompts/FP{N+1}-start.md` (excepto FP3 = último).

---

## Score pre y post F-pos

| Heurística | Pre F-pos (TP11) | Post FP1 | Post FP2 | Post FP3 | Post FP4 |
|---|---|---|---|---|---|
| H1 inmediatez | ❌ FAIL (2.77s TTFB) | — | — | ✅ PASS (target ≤800ms) | — |
| H2 planning | ✅ PASS | — | — | — | — |
| H3 memoria | ✅ PASS | — | — | — | — |
| H4 tono | ⚠ PARTIAL | — | — | — | ✅ PASS |
| H5 confianza | ✅ PASS | — | — | — | — |
| H6 recuperación | ⚠ PARTIAL | ✅ PASS (Aplicar persists) | — | — | — |
| H7 canal | ❌ FAIL | — | ✅ PASS (auto-trigger) | — | — |
| H8 fricción | ⚠ PARTIAL | ✅ PASS (no silent fail) | — | — | — |
| **Score** | **4.5/8** | **5.5/8** | **6.5/8** | **7.5/8** | **8/8 ✓** |

Target: 8/8 al cerrar FP4 → "feel like Claude Code" cumplido.

---

## Decisión post-cierre F-pos

Cuando FP1-FP4 cierran:
1. Re-run TP11 selectivos (J1, J2, J4 — los que destaparon los bugs).
2. Si score 8/8 confirmado → archivar `fpos-2026-04/` + actualizar `redesign-2026-04/learnings/F-pos-summary.md` cerrando los items.
3. Si score <8/8 → root cause restante → potencial nuevo FP5 dedicado.
