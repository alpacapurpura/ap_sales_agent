# Métricas + Targets F-pos

## Tabla por FP

### FP1 (B22 ProposalCard apply)

| Métrica | Pre-fix | Target post-fix |
|---|---|---|
| `mutation_journal` rows post-apply | 0 | ≥1 per ProposalCard apply |
| ProposalCard.handleApply network call | 0 (no-op silent) | 1 call POST /mutations/apply (cuando bridge ausente) |
| Form fields populated post-apply + reload | empty | values visible |
| UI status post-apply success | "applied" verde (mintiendo) | "applied" verde (real) |
| UI status post-apply failure | "applied" verde (mintiendo) | "failed" rojo + mensaje |
| Idempotency 2 clicks | 2 rows | 1 row |
| Tests añadidos | 0 | ≥6 (1 per AC) |

### FP2 (B24 channel auto-trigger)

| Métrica | Pre-fix | Target post-fix |
|---|---|---|
| `tool_call format_for_channel` rate cuando msg matches WhatsApp keyword | 0% | 100% |
| Detection accuracy regex parametrize | n/a | ≥95% true positive, ≤5% false positive |
| Tokens delta per turn (broad bind cost) | baseline | ≤+500 input tokens (acceptable) |
| Tests añadidos | 0 | ≥7 (1 per AC) |

### FP3 (B25 routing TTFB)

| Métrica | Pre-fix | Target post-fix |
|---|---|---|
| TTFB block_start p50 | ~2770ms | ≤800ms |
| TTFB block_start p95 | ~2900ms | ≤2000ms |
| Routing decision concurrent con model warm-up | secuencial | timestamps overlap |
| Quality regression (judge avg) | baseline 4.0+ | mantained ≥4.0 |
| `copilot_routing_log` rows | 1:1 turns | 1:1 turns (no regression) |
| Tests añadidos | 0 | ≥6 (1 per AC) + integration |

### FP4 (B23.1 voseo cleanup amplio)

| Métrica | Pre-fix | Target post-fix |
|---|---|---|
| Files con voseo en `copilot/` module | 9 (post B23-TP11) | 0 (excepto allowlist `output_sanitizer.py`) |
| Voseo tokens total module | ~50+ | 0 (allowlist excepted) |
| Arch fitness ratchet test | not exists | exists + PASS |
| Live re-run J4 voseo count | 1 instance | 0 instances |
| Tests añadidos | 0 | ≥10 + 1 arch fitness |

---

## Score post-FP1-FP4 (target)

| Heurística | TP11 | Post-FP1 | Post-FP2 | Post-FP3 | Post-FP4 |
|---|---|---|---|---|---|
| H1 inmediatez | ❌ | ❌ | ❌ | ✅ | ✅ |
| H2 planning | ✅ | ✅ | ✅ | ✅ | ✅ |
| H3 memoria | ✅ | ✅ | ✅ | ✅ | ✅ |
| H4 tono | ⚠ | ⚠ | ⚠ | ⚠ | ✅ |
| H5 confianza | ✅ | ✅ | ✅ | ✅ | ✅ |
| H6 recuperación | ⚠ | ✅ | ✅ | ✅ | ✅ |
| H7 canal | ❌ | ❌ | ✅ | ✅ | ✅ |
| H8 fricción | ⚠ | ✅ | ✅ | ✅ | ✅ |
| **Total** | **4.5/8** | **5.5/8** | **6.5/8** | **7.5/8** | **8/8** ✓ |

Target final post-FP4: 8/8 = "feel like Claude Code" cumplido.

---

## Diff vs baseline TP11

Cada FP debe NO regress ningún heurística previamente PASS. Verificar via re-run TP11 J{N} selectivo post-FP{N} fix.

---

## Cuándo escalar a sub-FP

Si dentro de un FP un fix requiere cambios en >3 archivos en >1 módulo + sub-bug abierto, **NO bundling**. Documenta sub-FP en results + abrir nuevo FP follow-up. Razón: traceability + commit-monstruo prevention.
