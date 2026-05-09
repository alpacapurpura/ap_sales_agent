<!-- voseo-allowed: mockup table cita es-AR voseo en transcript subject (sales_agent voice exception per .claude/rules/sales-agent-brand-voice.md) -->
---
rubric_id: voice-fidelity
calibration_version: 1
last_modified: 2026-05-09
ratified_by_chris: false
owner_story: sales-agent-voice-fidelity-grader-runtime
seed_turns: 10                      # 10 turn-segments × 1 rubric = 10 manual labels
goldens_source: ../../../../goldens/    # Story D 20-30 goldens
---

# Calibración voice-fidelity (Story E v1)

> Calibración semilla del rubric `voice-fidelity`. Chris aporta 10 etiquetas
> manuales sobre turn-segments seleccionados de los goldens de Story D
> (`backend/tests/agentic_evals/sales_agent/goldens/`).

## Metodología

1. **Selección de turns** — 10 turn-segments (no transcripts completos)
   distribuidos de forma representativa: 5 happy + 3 nurture + 2 unqualified.
2. **Etiquetado manual** — Chris asigna score 0.0-1.0 + razonamiento corto
   (1-2 oraciones) por cada turn × rubric.
3. **Comparación con MAJ-EVAL** — corremos el grader contra los mismos turns
   y comparamos ground-truth Chris vs ensamble de jueces.
4. **Tolerancia de drift** — diferencia absoluta media |chris - maj_eval| > 0.10
   dispara revisión de prompts del juez (T-7) o re-ratificación de pesos (D2).

## Tabla de etiquetas Chris (10 turn-segments × voice-fidelity)

| Turn ID | Tenant | Persona | Voice-Fidelity (Chris 0-1) | Razonamiento Chris | MAJ-EVAL final_score | Drift |
|---|---|---|---|---|---|---|
| _por completar_ | tenant_coach_lat | happy | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_coach_lat | happy | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_coach_lat | happy | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_medicina_estetica | nurture | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_medicina_estetica | nurture | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_clinica_dental | happy | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_clinica_dental | nurture | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_agencia_growth_video | happy | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_agencia_automatizacion_ia | unqualified | _0.??_ | _por completar_ | _por completar_ | _por completar_ |
| _por completar_ | tenant_agencia_automatizacion_ia | unqualified | _0.??_ | _por completar_ | _por completar_ | _por completar_ |

> Chris completa esta tabla después de la primera ejecución exitosa del
> grader sobre los goldens (Story D build done) — ~30 minutos manual.

## Línea base auto-calibración vs goldens (frozen v1)

Para cada `golden_id × turn_n × voice-fidelity`, el sistema computa MAJ-EVAL
Round 1 variance + final_score. Distribución base capturada al commit v1:

- **Mean Round 1 variance**: _por computar (post primera corrida)_
- **p95 Round 1 variance**: _por computar_
- **Mean final_score**: _por computar_
- **p95 final_score**: _por computar_
- **Mean cost_usd_total por grade**: _por computar_

Drift detection: ejecuciones futuras comparan contra esta base. Diff > 0.05
absoluto en mean → alerta `voice_fidelity_calibration_drift`.

## Triggers de re-calibración (D11 cement)

1. **Bump de modelo de juez** (D15) — Sonnet/GPT-4o/Kimi version bump.
2. **Bump de versión del rubric MD** (D16 — invalidación automática del cache).
3. **Revisión semestral Chris** — auditoría del presupuesto de varianza.
4. **Drift detectado** — diff base > 0.10 absoluto en mean final_score.

## Pista de auditoría

Cada métrica de la línea base se commitea a git. Eventos de drift se loggean
al `structlog` con event `voice_fidelity_calibration_drift`. La tabla de
etiquetas Chris se actualiza únicamente con ratificación explícita
(versión = +1 + frontmatter `ratified_by_chris: true`).

## Story chain

- Story C — `personas-instrumented-runtime` provee `actor_profile.metadata.persona_gym_axes`
- Story D — `goldens-3-tenants-dataset` provee transcripts + `expected_voice_attributes`
- Story E — esta calibración (T-9 + T-10 SSoT seed)
- Story G — `voice-fidelity-ci-gate` consume threshold default 0.7 + override env
- Story I — `adversarial-jailbreak-suite` extiende con rubric `toxicity-control`
