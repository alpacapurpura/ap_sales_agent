# F-pos Plan — 4 fases

## Mapa Bug → FP

| Bug | FP | TP origen | Capa stack |
|---|---|---|---|
| B22 ProposalCard apply silent | FP1 | TP11 J1 | FE (ProposalCard + useCopilotStore) + BE (mutations endpoint) |
| B24 format_for_channel auto-trigger | FP2 | TP11 J2.T2/T3 | BE (chat orchestrator middleware + tool binding) |
| B25 routing classifier sequential blocks TTFB | FP3 | TP11 J1.T1 | BE (chat orchestrator routing flow) |
| B23.1 voseo cleanup amplio | FP4 | TP11 J4 (residual) | BE (system prompts + subagents + tools + j2 templates) |

---

## DAG ejecución

```
TP11 cerrado
   │
   ├──► FP1 (B22 ProposalCard) ──┐
   │                              │
   ├──► FP4 (B23.1 voseo) ────────┤
   │     [paralelo OK con FP1]    │
   │                              │
   ▼                              ▼
   FP2 (B24 channel_format middleware)
   │
   ▼
   FP3 (B25 TTFB routing parallel)
   │
   ▼
   Re-run TP11 J1+J2+J4 selectivos → score 8/8
```

- **FP1 secuencial bloqueante** para B22 — sin esto el flow setup brand NO completa, y FP2 testeo necesita ProposalCard funcional.
- **FP4 paralelizable con FP1** — toques disjoint (FP1 = FE + BE mutation endpoint; FP4 = BE prompts/templates).
- **FP2 secuencial post FP1** — ambos tocan `chat.py` chat orchestrator. Evita merge conflicts.
- **FP3 secuencial post FP2** — introduce parallelism que cambia routing flow asunto del FP2.

---

## Recomendación orden ejecución (single-thread)

Si Chris ejecuta serialmente:

1. **FP1** (B22 ProposalCard) — crítico, bloquea J1 setup brand end-to-end. Cross-stack 1-2 días.
2. **FP4** (B23.1 voseo cleanup) — quick win 4 horas. Pattern B23-TP11 replicado 9 archivos. Bajo riesgo.
3. **FP2** (B24 channel_format) — H7 PASS. Middleware BE 4-8 horas.
4. **FP3** (B25 TTFB routing parallel) — H1 PASS. Optimization 1 día con race condition testing.

**Total estimado:** ~3-4 días serial.

Si Chris paraleliza FP1 || FP4 (2 instances): ~2.5 días.

---

## Una página por FP

| FP | Path doc | Tiempo | Pre-req | Output principal |
|---|---|---|---|---|
| FP1 | `phases/FP1-proposal-card-apply.md` | 1-2 días | TP11 cerrado | ProposalCard.handleApply persiste mutation cross-stack. UI feedback honesto. |
| FP2 | `phases/FP2-channel-format-trigger.md` | 4-8 hs | FP1 cerrado | Middleware en chat orchestrator force-bind `format_for_channel` cuando user msg matches canal-keywords. |
| FP3 | `phases/FP3-routing-parallel-ttfb.md` | 1 día | FP2 cerrado | Routing classifier corre parallel a model warm-up. TTFB ≤800ms p50. |
| FP4 | `phases/FP4-voseo-cleanup-amplio.md` | 4 hs | TP11 cerrado | 9 prompts files convertidos voseo→tuteo. Arch fitness ratchet "todos prompts/tools/subagents = 0 voseo". |

---

## Outputs cross-fase

Cada `results/FP{#}-{YYYY-MM-DD}.md` debe incluir:

```markdown
# FP{N} — {fecha}

## Pre-research
- Queries ejecutadas + insights nuevos.

## Acceptance criteria checklist
| AC | Descripción | Pre-fix | Post-fix |
|---|---|---|---|
| AC1 | ... | ❌ | ✅ |

## Before / After evidence
- Bug reproducción pre-fix (trace events / SQL probe / screenshot).
- Bug closure post-fix (mismo prueba pasa).

## Failures + root cause
- Si descubriste sub-bugs durante el FP.

## Métricas agregadas
- Latency / cost / tests added.

## Aprendizajes para FP{N+1}
- 1-3 bullets accionables.

## Handoff FP{N+1}
Prompt en `prompts/FP{N+1}-start.md`.
```
