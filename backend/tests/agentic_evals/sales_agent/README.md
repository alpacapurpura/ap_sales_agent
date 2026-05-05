# Agentic Eval Harness — sales_agent

> Stub creado por T-1 (PI-12 Sprint S1 — story `sales-agent-eval-runner-foundation`).
> T-6 reescribe este README con docs operativos completos. Por ahora solo orientación mínima.

## Qué es esta carpeta

Harness de evaluaciones end-to-end del agente `sales_agent` (módulo
`backend/src/modules/sales_agent/`). Cada smoke invoca `agent_app.ainvoke`
real contra un tenant real (Visionarias) con un golden YAML versionado, y
verifica capas múltiples (trayectoria, herramientas, output, costo,
latencia) usando `TrajectorySpy` + asserts.

**Alcance:** este harness cubre únicamente `sales_agent`. Otros agentes
(p. ej. `copilot`) tendrían su propio harness hermano si fuera necesario
en el futuro.

**Diferencia con `tests/quality/sales_agent_goldens/`:** ese directorio
(S10, redesign abril 2026) corre `SalesAgentJudge` LLM-as-judge sobre
20+ conversaciones canned. No invoca al agente real. Este harness sí
invoca el agente real punto a punto (LangGraph + LiteLLM + DB) y mide
comportamiento observable.

## Costo

Cada smoke real cuesta aproximadamente **USD 0.005** por corrida (1
turno, modelo `deepseek-v4-flash` vía LiteLLM proxy). Para evitar quemar
budget en CI por defecto, el suite está gateado por la flag
`pytest --run-evals`. Sin la flag, los tests con marker `@pytest.mark.eval`
quedan en `SKIPPED`.

## Cómo correr (preview)

```bash
# Suite default — los evals se saltan (SKIPPED), no gastan budget
cd backend && .venv/bin/pytest tests/agentic_evals/

# Suite con evals reales (T-5 en adelante)
cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/ -v --run-evals

# Atajo (T-6 agrega target Make)
make eval-smoke
```

Pre-condiciones para `--run-evals`:

- Tenant `Visionarias` existe en la DB de dev con al menos una oferta
  activa y un `PersonalityProfile` compilado.
- LiteLLM proxy levantado (`visionarias_litellm:4000`).
- Variable de entorno `VISIONARIAS_TENANT_ID` apuntando al UUID correcto.

Si falta cualquiera, las fixtures hacen `pytest.skip` con razón explícita
(no auto-seedean). Ver T-2 conftest.

## Goldens

Los goldens viven en `goldens/` como YAML versionado y checkeado en git
(decisión B7 del spec). Schema documentado en T-5 (`golden_loader.py`)
y `03-arch-be.md` § "Golden YAML schema".

`runner/regenerate_golden.py` (T-5) re-escribe el YAML cuando cambia el
`offer_id` (oferta vieja soft-deleted): nunca corre automático, sólo
acción humana deliberada.

## Estructura

```
agentic_evals/sales_agent/
├── README.md                   ← este archivo (T-1 stub, T-6 expande)
├── __init__.py
├── conftest.py                 ← T-2: fixtures (visionarias_tenant_session,
│                                  eval_run_id, sales_agent_entrypoint, ...)
├── runner/                     ← T-3..T-5
│   ├── trajectory_spy.py       ← T-3: callback observador (LangChain)
│   ├── artifacts.py            ← T-3: writer trace.json/response.txt/assertions.json
│   ├── assertions.py           ← T-4: 5 capas + placeholder Story 7 voice grader
│   ├── golden_loader.py        ← T-5: GoldenSpec + load_yaml
│   └── regenerate_golden.py    ← T-5: CLI re-genera offer_id
├── fixtures/                   ← T-2
│   └── synthetic_tenant.py     ← T-2: T2_synthetic para Scenario 4 (cross-tenant)
├── goldens/                    ← T-5: visionarias-smoke-golden.yaml + futuros
├── _artifacts/                 ← runtime, gitignored (sólo .gitignore se checkea)
├── test_eval_runner_fixtures.py  ← T-2: meta-tests TDD baseline
└── test_eval_runner_smoke.py     ← T-5: 4 scenarios end-to-end
```

## Pila pendiente (siguientes tickets)

| Ticket | Alcance |
|---|---|
| T-2 | Pytest plumbing (`--run-evals` flag + marker), 4 fixtures, meta-tests TDD |
| T-3 | `TrajectorySpy` callback + writer de artifacts (con `sanitize_payload`) |
| T-4 | Librería de asserts multicapa + placeholder voice grader (Story 7) |
| T-5 | Smoke golden YAML + `golden_loader` + `regenerate_golden.py` + 4 scenarios |
| T-6 | Target `make eval-smoke` + reescritura completa de este README |

## Cleanup

`_artifacts/` está completamente gitignored (sólo el `.gitignore` se
trackea). Borrar contenido cuando ocupe espacio, sin temor de perder
historia versionada.

## Out of scope (foundations no, futuras stories)

- Pass^k tracking → Story 2.
- Budget cap por run → Story 3.
- Goldens reales de 3 tenants → Story 5.
- Personas como simulators → Story 6.
- Voice fidelity grader (LLM-as-judge para voz tenant) → Story 7.
- CI gate cron nightly → Story 8.
- Adversarial scenarios extendidos → Story 9.

Ver `docs/projects/active/PI-12-sales-agent-eval-foundation/PI.md`.
