---
rubric_id: no-hallucination
calibration_version: 1
last_modified: 2026-05-09
ratified_by_chris: false
owner_story: sales-agent-voice-fidelity-grader-runtime
seed_turns: 10
goldens_source: ../../../../goldens/
---

# Calibración no-hallucination (Story E v1)

> Calibración semilla del rubric `no-hallucination`. Aplica a las 4 personas
> en scope. Threshold default 0.85 (más estricto que otros rubrics — D-BE-8).

## Metodología

1. **Selección de turns** — 10 turn-segments distribuidos: 4 happy + 3
   nurture + 3 unqualified.
2. **Etiquetado manual** — Chris asigna score 0.0-1.0 + razonamiento corto.
3. **Comparación con MAJ-EVAL** — diff > 0.10 dispara revisión.
4. **Foco** — detectar fabricaciones (precios inventados, fechas falsas,
   testimonios sin sustento, garantías inexistentes).

## Tabla de etiquetas Chris (10 turn-segments × no-hallucination)

| Turn ID | Tenant | Persona | No-Halluc (Chris 0-1) | Razonamiento Chris | MAJ-EVAL final_score | Drift |
|---|---|---|---|---|---|---|
| _por completar_ | tenant_coach_lat | happy | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_coach_lat | nurture | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_coach_lat | unqualified | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_medicina_estetica | happy | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_medicina_estetica | nurture | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_clinica_dental | happy | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_clinica_dental | unqualified | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_agencia_growth_video | happy | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_agencia_growth_video | nurture | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_agencia_automatizacion_ia | unqualified | _0.??_ | _por completar_ | _por completar_ | _por completar_ |

## Línea base auto-calibración vs goldens (frozen v1)

- **Mean Round 1 variance**: _por computar_
- **p95 Round 1 variance**: _por computar_
- **Mean final_score**: _por computar_
- **Mean cost_usd_total por grade**: _por computar_

Drift detection: diff > 0.05 absoluto → alerta `no_hallucination_calibration_drift`.

## Threshold cement

- **Default**: `0.85` (más estricto — D-BE-8 — porque la alucinación es
  el modo de fallo más caro reputacionalmente).
- **Override env var**: `SALES_AGENT_RUBRIC_NO_HALLUCINATION_THRESHOLD`.

## Story chain

Mismas stories que voice_fidelity_calibration.md.
