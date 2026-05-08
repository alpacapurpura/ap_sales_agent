# Qualification Accuracy Rubric

> **Status:** placeholder declared by Story C `sales-agent-personas-instrumented-runtime` (2026-05-08).
> **Runtime owner:** Story E `sales-agent-voice-fidelity-grader-runtime` implements full rubric.

## Scope

Mide la habilidad del sales_agent para:
1. Detectar si un lead califica vía señales BANT (Budget / Authority / Need / Timeline) o MEDDIC (Metrics / Economic buyer / Decision criteria / Decision process / Identify pain / Champion).
2. Generar señales de qualifying-out cuando el lead claramente NO encaja con la oferta del tenant.
3. Comportamiento graceful-decline al cerrar conversaciones unqualified — no agresivo, respetuoso, futuro-orientado.

## Capability detection (TBD por Story E)

- BANT detection: ¿el agente preguntó por presupuesto / autoridad / necesidad / timeline en algún punto?
- MEDDIC detection: ¿el agente identificó métricas + economic buyer + decision process?
- Qualifying-out: ¿el agente terminó la conversación cuando lead no calificó (vs forzar venta)?
- Graceful decline: tono respetuoso, no presión, abre puerta futura

## Threshold (TBD)

`SALES_AGENT_QUALIFICATION_ACCURACY_THRESHOLD` env default a definir por Story E. Story C declara placeholder; Story E asigna valor + lógica de scoring.

## Test coverage (TBD por Story E)

Pendiente. Story C cement los tests funcionales (T-6 Scenario 5 qualification, T-7 Scenario 6 nurture) — sin embargo, scoring del rubric corre en Story E como grader pass^k post-build.

## Story chain

- Story C (`sales-agent-personas-instrumented-runtime`): declares this rubric placeholder; Scenarios 5+6 cement test infrastructure.
- Story E (`sales-agent-voice-fidelity-grader-runtime`): implements full rubric runtime + threshold + scoring + integration con eval simulator.
