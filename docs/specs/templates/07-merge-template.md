# 07-merge.md — Template (PM aplica diff a product/)

> Owner: `/pm`. SOLO escrito tras `REVIEW-final.md` con `verdict: APPROVED + ready_to_merge: true`.
> Documenta los CAMBIOS al producto (capabilities, stories status, modules.md, INDEX).

---
story_id: STORY_ID
sprint: SN
pi: PI-N
merged_at: 2026-05-04T19:00Z
merged_by: /pm
review_final_path: "../06-audit/REVIEW-final.md"
---

## Cambios al producto

### `docs/product/stories/{module}/{story-id}.yaml`

```diff
- status: planned
+ status: live
- pr_introduced: null
+ pr_introduced: PR-3
- pi_introduced: null
+ pi_introduced: PI-12
- date_introduced: null
+ date_introduced: 2026-05-04
- last_audit: 2026-05-04
+ last_audit: 2026-05-04

# Scenarios: type capability → regression (los que pasaron pass^3 >= threshold)
scenarios:
  - id: happy-path-typical-persona
-   type: capability
+   type: regression
  ...

# test_coverage llenado
test_coverage:
- eval_suite_path: null
+ eval_suite_path: backend/tests/agentic_evals/copilot/brand_audit_eval.py
- pass_k_last_run: null
+ pass_k_last_run: 0.83
- cost_last_run_usd: null
+ cost_last_run_usd: 0.31
+ last_run_at: 2026-05-04T18:30Z
```

### `docs/product/capabilities/{module}/{capability}.yaml`

```diff
- status: planned
+ status: live
stories_live: 3 (was 2)
stories_planned: 1 (was 2)
```

### `docs/product/modules/{module}.md`

[Sección de capabilities live actualizada — agregar entry para esta story.]

```diff
+ - **brand-audit** (capability `brand-audit`, story `copilot-brand-audit`) — live desde 2026-05-04 en PI-12 PR-3.
+   Copilot puede auditar marca conversacionalmente. Identifica gaps, prioriza por sales-impact.
```

### `docs/product/INDEX.md` (si aplica)

[Si nueva capability impacta routing principal — actualizar INDEX.]

## Tests promovidos a regression suite

| Scenario | De | A | Path |
|---|---|---|---|
| `happy-path-typical-persona` | capability | regression | `tests/agentic_evals/copilot/brand_audit_eval.py::test_happy_path` |
| `no-hallucination` | regression (was already) | regression | ... |

## Métricas de cierre

- Pass^3 final: 0.83 ✅
- Cost p95: $0.31 ✅
- Latency TTFT p95: 1.4s ✅
- Coverage delta: +6%

## Capability promotion

- `brand-audit` capability: status `planned` → `live`
- Trigger: 1 story `live` (de 3 planeadas) + pass^k >= threshold

> Nota: la capability `brand-audit` está en `live` aunque tiene 2 stories planned. El status capability se deriva: si AL MENOS 1 story está live → capability live (parcial). Si todas live → capability fully-live. Si todas planned → capability planned.

## Story → archive

- Story folder NO se mueve (queda en `projects/active/PI-12/sprints/S1/stories/`)
- Cuando PI-12 cierre → se mueve PI completa a `projects/archive/`

## Próximo paso

`→ /pm cierra checkpoint story.checkpoint.md → status: done`
`→ /pm verifica si sprint puede cerrarse (todas las stories del sprint con status: done?)`
`→ Si sprint cierra → checkpoint sprint = done. Si PI cierra → mover a archive.`

## Salida al user (Chris)

```
✅ Story brand-audit MERGED a producto
   - Capability brand-audit: live
   - Story copilot-brand-audit: live (pass^3=0.83)
   - Diff aplicado a product/stories + capabilities + modules/copilot.md
   - Tests promovidos a regression suite
   - PI-12 sprint S1: 1/3 stories done
```
