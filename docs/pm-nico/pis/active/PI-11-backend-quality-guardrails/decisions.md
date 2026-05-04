# Decisiones — PI-11

> Append-only. Cada decisión se registra con fecha + PR + contexto.

| Fecha | Decisión | Contexto | PR |
|---|---|---|---|
| 2026-05-04 | D1: Outbox `USE_OUTBOX_PATTERN_*` queda `True` permanente | Escala 1000 clientes multi-worker; in-memory `LegacyEventBus` rompe entre workers FastAPI/Gunicorn | PR-1 |
| 2026-05-04 | D2: Tests migran a `adapter_bus` mock o outbox table probe (NO monkeypatch False) | Path nuevo es prod path; test path debe match | PR-1 |
| 2026-05-04 | D3: `LegacyEventBus.publish` runtime DeprecationWarning + deprecation gradual | Capability legacy compat solo; eliminación final post PI-12 | PR-1 |
| 2026-05-04 | D4: Polluter hunt sin band-aid `@pytest.mark.flaky` final | Fix at source obligatorio | PR-1 |
| 2026-05-04 | D5: Architect Opus 1 ejecución cubre PR-1 + PR-3 cross-linked | Acoplamiento técnico singleton fixture + arch fitness test | PR-1 + PR-3 |
| 2026-05-04 | D6: PR-4 = PM directo (no builder técnico) | Scope = markdown meta-process (`.claude/agents/*.md` + `.claude/skills/pm/SKILL.md` + `.claude/rules/tdd-mandatory.md`) | PR-4 |
| 2026-05-04 | D7: Stash apply en builder PR-1 Phase 1 Step 1 (business owner) | Evita conflict workflow paralelo | PR-1 |
| 2026-05-04 | **D8 (NEW post-impl): Polluter root cause = singleton leak (NO uuid4 hipótesis)** | Investigación iter 2 confirmó `ChatOrchestrator._instance.buffer_service` + `SemanticRouter._instance` leak cross-test; singleton fixture business iter 1 (commit `7652f1f8`) ya lo cubrió. Hipótesis original uuid4 del primer iter fue descartada | PR-1 |
| 2026-05-04 | **D9 (NEW post-impl): 4 copilot Caso A files DEFERIDOS — out-of-scope PR-1** | `test_extraction_event_handlers`, `observability/test_*`, `api/test_suggestions*` NO en stash original; PR-3 builder baseline-allowlist; migración real en PR futuro | PR-1 |
| 2026-05-04 | **D10 (NEW post-impl): Gate-runner subset iter 2 (NO full /test-backend) post crash machine** | Pytest validation nativa por agentic builder iter 2 (2490/2490 + 5x deterministic runs) = evidence equivalente a /test-backend pytest gate. Lint/format/interrogate/mypy/jscpd/pip-audit corridos como subset cheap | PR-1 |
