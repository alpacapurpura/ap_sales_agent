---
rubric_id: qualification-accuracy
calibration_version: 1
last_modified: 2026-05-09
ratified_by_chris: false
owner_story: sales-agent-voice-fidelity-grader-runtime
seed_turns: 10
goldens_source: ../../../../goldens/
---

# Calibración qualification-accuracy (Story E v1)

> Calibración semilla del rubric `qualification-accuracy` (NEW Story E owns v1).
> Threshold default 0.75 (D-BE-7 cement). Aplica a personas `nurture` y
> `unqualified` (D7 cement — happy excluida porque qualification ya pasó).

## Metodología

1. **Selección de turns** — 10 turn-segments distribuidos: 5 nurture + 5
   unqualified (happy excluida — D7).
2. **Etiquetado manual** — Chris asigna score 0.0-1.0 sobre las 4 axes
   A1-A4 del rubric:
   - A1 — Qualifies-out (peso 0.4): identificación correcta cuando el lead
     no califica
   - A2 — BANT order (peso 0.3): orden lógico Budget → Authority → Need → Timing
   - A3 — Graceful decline (peso 0.2): tono respetuoso al rechazar
   - A4 — No-overpromise cross-rubric (peso 0.1): coherencia con el rubric
     vecino
3. **Comparación con MAJ-EVAL** — corremos grader contra los mismos turns;
   verificamos `final_score` ≥ threshold default 0.75 antes de promover
   un turn como golden.
4. **Tolerancia de drift** — diff absoluto medio |chris - maj_eval| > 0.10
   dispara revisión de prompts del juez (T-7).

## Tabla de etiquetas Chris (10 turn-segments × qualification-accuracy)

| Turn ID | Tenant | Persona | Qualif-Acc (Chris 0-1) | A1 | A2 | A3 | A4 | MAJ-EVAL final_score | Drift |
|---|---|---|---|---|---|---|---|---|---|
| _por completar_ | tenant_coach_lat | nurture | _0.??_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_coach_lat | nurture | _0.??_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_coach_lat | unqualified | _0.??_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_medicina_estetica | nurture | _0.??_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_medicina_estetica | unqualified | _0.??_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_clinica_dental | nurture | _0.??_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_clinica_dental | unqualified | _0.??_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_agencia_growth_video | nurture | _0.??_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_agencia_automatizacion_ia | nurture | _0.??_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_agencia_automatizacion_ia | unqualified | _0.??_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ | _por completar_ |

## Línea base auto-calibración vs goldens (frozen v1)

- **Mean Round 1 variance**: _por computar_
- **p95 Round 1 variance**: _por computar_
- **Mean final_score (nurture)**: _por computar_
- **Mean final_score (unqualified)**: _por computar_
- **Mean cost_usd_total por grade**: _por computar_

Drift detection: diff > 0.05 absoluto → alerta `qualification_accuracy_calibration_drift`.

## Triggers de re-calibración

Mismos triggers que `voice_fidelity_calibration.md` § Triggers de re-calibración
+ override env var `SALES_AGENT_RUBRIC_QUALIFICATION_ACCURACY_THRESHOLD` para
runtime tuning (D-BE-8 cement).

## Threshold cement

- **Default**: `0.75` (D-BE-7).
- **Override env var**: `SALES_AGENT_RUBRIC_QUALIFICATION_ACCURACY_THRESHOLD`.
- **Bump policy**: bump → ratificación Chris + ciclo de re-calibración + bump
  `rubric_version` → invalidación automática del cache (D16).

## Story chain

Mismas stories que voice_fidelity_calibration.md.
