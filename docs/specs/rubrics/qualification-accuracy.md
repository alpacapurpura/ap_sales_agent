# Rubric — Qualification Accuracy

```yaml
---
id: qualification-accuracy
version: 1
applies_to: [agentic-story]
modules: [sales_agent]
threshold_default: 0.75                     # D13 cement — env override SALES_AGENT_RUBRIC_QUALIFICATION_ACCURACY_THRESHOLD
ssot:
  - "personality_profiles.system_instruction (BANT/MEDDIC heuristics if declared by tenant)"
  - "Story C personas: persona_kind ∈ {nurture, unqualified} require qualification capability"
  - "Story D goldens: expected_termination_reason + expected_tools_invoked ground truth"
last_modified: 2026-05-09
owner_story: sales-agent-voice-fidelity-grader-runtime
---
```

## Propósito

Verificar que el sales_agent ejecuta qualification correctamente por persona kind:

- `unqualified` persona: el agente DEBE invocar `qualify_lead` + etiquetar `not_qualified` + declinar de manera respetuosa.
- `nurture` persona: el agente DEBE invocar `qualify_lead` + hacer preguntas relevantes de BANT ANTES de intentos de cierre.
- `happy` persona: la qualification PUEDE ser implícita (`qualify_lead` opcional, pero el comportamiento de cierre es evaluable).

## Inputs al juez (slot 5 transcript)

- `transcript` completo del YAML de Story D (turnos cliente ↔ agente)
- `actor_profile.persona_kind` (Story C — happy / nurture / unqualified / adversarial)
- `tenant_voice_profile.system_instruction` (Story A — heurísticas BANT/MEDDIC si el tenant las declaró)
- `expected_termination_reason` (Story D — ground truth)
- `expected_tools_invoked` + `forbidden_tools` (Story D — ground truth)

## Assertions (4 ejes — los jueces asignan score 0.0-1.0 según violations)

### A1 — Qualifies-out unqualified leads (production-critical)

- ✅ **Pasa** (unqualified): `qualify_lead` invocado Y (`tag_lead_status` = `not_qualified` O decline respetuoso en el mensaje).
- ❌ **Falla** (unqualified): el agente invoca `enroll_*`, `send_payment_link` o `confirm_appointment_*` (cierre prematuro ante un lead incorrecto).
- Score 1.0 = qualify_lead + etiqueta correcta + tono de decline respetuoso.
- Score 0.5 = qualify_lead invocado pero sin etiqueta / decline en el límite.
- Score 0.0 = herramienta de cierre prohibida invocada.

### A2 — BANT order (nurture)

- ✅ **Pasa** (nurture): `qualify_lead` invocado en turnos 1-3 ANTES de intentos de cierre.
- ❌ **Falla** (nurture): herramientas de cierre invocadas antes del turno 4 sin qualification previa.
- Score 1.0 = qualify_lead en turno 1-2 + preguntas relevantes de BANT planteadas.
- Score 0.7 = qualify_lead en turno 3 + al menos 1 dimensión BANT explorada.
- Score 0.4 = qualify_lead presente pero tardío (turno 4+); algo de BANT inferido.
- Score 0.0 = qualify_lead no invocado en ejecución nurture.

### A3 — Graceful decline tone (unqualified principalmente)

- ✅ **Pasa**: la respuesta respeta la voz de marca (sin rechazo brusco — ofrece lead magnet alternativo, referido o canal futuro).
- ❌ **Falla**: `"no eres mi cliente"` sin alternativa.
- Score 1.0 = respetuoso + ofrece recurso alternativo.
- Score 0.7 = educado pero sin alternativa.
- Score 0.0 = rudo / desdeñoso / estigmatizante.

### A4 — No-overpromise during qualification (coherencia cross-rubric — nurture)

- Subsume el rubric `no-overpromise` para los intercambios BANT de nurture.
- Score: ver `no-overpromise.md` v1 — los jueces correlacionan; el peso de A4 es 0.1 del total de qualification-accuracy.

## Scoring methodology (por juez)

```
final_qualification_accuracy = 0.4 × A1 + 0.3 × A2 + 0.2 × A3 + 0.1 × A4
```

Likert por eje: 1.0 / 0.7 / 0.4 / 0.0 (el juez retorna float; el rubric MD documenta la escala para transparencia).

## Out of scope

- ❌ Precisión de ejecución de ventas más allá de la qualification (Story F pass^k consume tool-trajectory).
- ❌ Control de toxicidad (rubric `toxicity-control.md` de Story I).
- ❌ Implementación de heurísticas BANT/MEDDIC en el runtime de sales_agent — historia separada (fuera de PI-12).
- ❌ Override del framework de qualification por tenant (usa `personality_profile.system_instruction` declarado).

## Calibration

- Baseline de varianza congelado en v1 contra 20-30 goldens de Story D (cementado en el commit v1; ver `calibration/voice_fidelity_calibration.md`).
- Trigger de re-calibración: actualización del modelo de juez (D15) O bump de versión del rubric MD (invalidación automática de caché D16) O revisión semestral de Chris.

## Cache invalidation

`rubric_version: 1` cementado. Aumentar este campo invalida TODAS las entradas de caché del rubric (D16). Composición de la clave de caché: `hash(transcript + rubric_id + tenant_voice + judge_set + rubric_version)`.

## Story chain

- **Story C** (`sales-agent-personas-instrumented-runtime`): declaró el placeholder para esta ruta de rubric; los Scenarios 5+6 cementan la infraestructura de tests (prueba de capability de qualification).
- **Story E** (`sales-agent-voice-fidelity-grader-runtime`): **es la dueña de este rubric MD v1 + runtime grader**. Reemplaza el placeholder de Story C.
- **Story F** (`sales-agent-eval-pass-k-tracking`): consume `MajEvalScore[rubric=qualification-accuracy].final_score` para el bucketing de nurture/unqualified (etapas Bloom Ideation + Rollout).
- **Story G** (`sales-agent-voice-fidelity-ci-gate`): el CI gate aplica `final_score >= 0.75` sobre los goldens (env override `SALES_AGENT_RUBRIC_QUALIFICATION_ACCURACY_THRESHOLD`).
