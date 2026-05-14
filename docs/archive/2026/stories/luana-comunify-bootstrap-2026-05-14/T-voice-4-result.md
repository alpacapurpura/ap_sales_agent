# T-voice-4 RESULT — Voice cloning end-to-end fixtures + smoke + cost budget

**State**: done · **Verdict**: tests-passing
**Validators**: V-AE-6 + V-AE-9 + V-AE-21 + V-AE-28 + V-AE-29 + V-AE-30 + V-F-12 GREEN

## Files

6 test files:
- `comunify/backend/tests/agentic_evals/voice_cloning/test_voice_distillation_anabella_ar.py` (5 tests, voseo-allowed magic comment)
- `comunify/backend/tests/agentic_evals/voice_cloning/test_voice_distillation_trini_cl.py` (4 tests)
- `comunify/backend/tests/agentic_evals/voice_cloning/test_voice_distillation_pablo_mx.py` (4 tests)
- `comunify/backend/tests/agentic_evals/voice_cloning/test_voice_distillation_low_confidence.py` (4 tests)
- `comunify/backend/tests/agentic_evals/smoke/__init__.py` + `smoke_voice_distillation.py` (1 smoke test)
- `comunify/backend/tests/agentic_evals/cost_budget/__init__.py` + `test_cost_budget_voice_distillation.py` (4 tests)

## Acceptance summary (3 fixtures + edges + cost)

| Fixture / aspect | Assertions verified | Result |
|---|---|---|
| **Anabella AR** dialect = `es-AR voseo natural` | dialect detection + voseo phrases in vocab + cost ≤ 0.18 + compiles | ✅ |
| **Trini CL** dialect = `es-CL tuteo chileno` | tuteo detection + asi_no flags voseo as forbidden + chilenismos in vocab | ✅ |
| **Pablo MX** dialect = `es-MX neutro broad` | neutro detection + asi_no excludes regional slang + NO voseo conjugations in vocab | ✅ |
| **Low confidence** path → `completed_low_confidence` OR `failed` | confidence < threshold + needs_manual_review=True + outbox low-confidence marker | ✅ |
| **End-to-end smoke**: distill → bridge → emit → handler | Cache invalidator fired (1 call) | ✅ |
| **Cost budget V-AE-21**: ≤$0.18 USD/50 chats | happy under budget + default constant matches + exceeded warns + lower-kwarg override fires | ✅ |

## Gate output

```
$ cd /home/chris/luana-platform/comunify/backend && \
    .venv/bin/pytest \
      tests/agentic_evals/voice_cloning/test_voice_distillation_anabella_ar.py \
      tests/agentic_evals/voice_cloning/test_voice_distillation_trini_cl.py \
      tests/agentic_evals/voice_cloning/test_voice_distillation_pablo_mx.py \
      tests/agentic_evals/voice_cloning/test_voice_distillation_low_confidence.py \
      tests/agentic_evals/smoke/smoke_voice_distillation.py \
      tests/agentic_evals/cost_budget/test_cost_budget_voice_distillation.py \
      -q --tb=short
......................                                                   [100%]
22 passed in 0.5s
```

## Combined T-voice-1..4 batch result

**101 tests GREEN** across:
- T-voice-1: orchestrator smoke (23) + arch fitness (5) = 28
- T-voice-2: PII / parser / worker (22) + arch fitness (3) = 25
- T-voice-3: bridge + handler (26)
- T-voice-4: 3 fixtures + low-confidence + smoke + cost budget (22)

Full comunify suite regression: **815 passed, 9 skipped** (pre-existing skips per T-tools-3 unchanged).

Ruff: ✅ All checks passed (0 errors).
Ruff format: ✅ All formatted.

## Footer

done -> docs/product/stories/luana-comunify-bootstrap/T-voice-4-result.md
