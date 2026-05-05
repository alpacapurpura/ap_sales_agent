# Anti-Default-Flip Audit

**Origen:** failed `/pase-produccion` 2026-05-04. Commit `64738354` (PR-1 Sub-E PI-2, 2026-04-29) flipeó `USE_OUTBOX_PATTERN_*` False→True sin auditar tests que mockean path legacy `EventBus.publish` → 25 BE failures + 1 polluter no identificable + ~3h investigación + ~500k tokens. Ver PI-11 PR.md.

## Regla cardinal

ANTES de flipear default de feature flag (`USE_*_PATTERN_*`, `LITELLM_PROXY_ENABLED`, `USE_DEEPAGENTS_*`, `ENABLE_*`, etc.) que cambia call path side-effect (events, persistence, logging, observability, LLM provider routing, agent orchestration) → **OBLIGATORIO 4 STEPS**:

### Step 1 — Grep tests path viejo (cross-codebase)

```bash
# Para cada call path afectado por el flip, grep mocks legacy:
grep -rn "<legacy_call_path>" /home/chris/AISALESHT/backend/tests/ 2>/dev/null | grep -v __pycache__

# Ejemplo flag USE_OUTBOX_PATTERN_*:
grep -rln "src.shared.domain.events.EventBus.publish" /home/chris/AISALESHT/backend/tests/

# Ejemplo flag LITELLM_PROXY_ENABLED:
grep -rln "OpenAIService\|KimiService\|DeepSeekService" /home/chris/AISALESHT/backend/tests/
```

Output capture obligatorio en commit body sección `## Tests audited`.

### Step 2 — Update mocks path nuevo

Para cada test detectado:
- Migrar mocks al `<new_canonical_path>` (e.g., `adapter_bus.publish` for outbox)
- O capturar via observability/persistence sink (outbox table, traces, etc.)
- O bypass explícito si test prueba capability legacy mismo (magic comment `# arch-bypass: testing legacy capability`)

### Step 3 — Run full suite con BOTH old+new flag values

```bash
# Default value (post-flip):
cd backend && .venv/bin/pytest -x -q --tb=short

# Legacy value (pre-flip — confirmar no rotura cuando flag override False):
cd backend && USE_OUTBOX_PATTERN_DEFAULT=false .venv/bin/pytest -x -q --tb=short
```

Ambos valores deben pasar 100%. Si UNO falla → stop, no flip until fix.

### Step 4 — Documentar commit body

Bloque obligatorio en commit body cuando aplique flip:
```
flag <NAME> flipped <OLD_VALUE>→<NEW_VALUE>

## Tests audited
- N tests migrated to new canonical path
- M tests use bypass for legacy capability (magic comment)
- 0 tests use `monkeypatch.setattr(<flag>=<old_value>)` band-aid

## Path old: <full_path>
## Path new: <full_path>
## Verification: pytest passed both values (logs attached)
```

## Inventario flags side-effect (SSoT — actualizar al agregar nuevos)

| Flag | Default actual | Side-effect path | Path viejo | Path nuevo | Tests probe canonical |
|---|---|---|---|---|---|
| `USE_OUTBOX_PATTERN_SALES_AGENT` | `True` (post 2026-04-29) | events emission | `src.shared.domain.events.EventBus.publish` | `event_bus_adapter.adapter_bus.publish` (→ outbox table) | adapter_bus mock OR `select(DomainEventOutboxModel)...` |
| `USE_OUTBOX_PATTERN_COPILOT` | `True` (post 2026-04-29) | events emission | idem | idem | idem |
| `USE_OUTBOX_PATTERN_BRAND` | `True` (post 2026-04-29) | events emission | idem | idem | idem |
| `USE_OUTBOX_PATTERN_DEFAULT` | `False` | events emission (fallback per-module unspecified) | idem | idem | idem |
| `USE_DEEPAGENTS_*` (futuros) | TBD | agent orchestration | LangGraph plain `StateGraph.compile()` | deepagents `task` subagent harness | both paths probed (per-test or fixture parametrize) |
| Otros `ENABLE_*` flags | varies | varies | varies | varies | varies |

> Note: `LITELLM_PROXY_ENABLED` row removed PI-12 S1 sales-agent-litellm-canonicalization T-5
> (legacy adapters deleted T-4). The LiteLLM Proxy is now the only runtime LLM dispatch path —
> there is no fallback toggle to audit.

**Cuando agregar nuevo flag side-effect → editar este inventario en mismo commit.** Auditor Cat 14/13 valida.

## Anti-patterns prohibidos

- ❌ Flipear default sin grep tests path viejo (Step 1 omitido)
- ❌ Flipear default sin run full suite con ambos valores (Step 3 omitido)
- ❌ Commit body sin sección "Tests audited" (Step 4 omitido)
- ❌ Mockear path viejo cuando flag default es path nuevo (test no prueba nada real — passes silenciosamente)
- ❌ Usar `monkeypatch.setattr(USE_*=False)` por test sin migrar mock al path nuevo — band-aid temporal solo (D2 PI-11)
- ❌ Bypass arch fitness sin magic comment justificado
- ❌ Agregar nuevo flag side-effect sin actualizar inventario SSoT este file

## Enforcement layers

| Layer | Mecanismo | Owner |
|---|---|---|
| 1 PM PR.md | Bloque "Default flips audited" mandatory cuando aplique flip | `/pm` skill (PR-4 alimenta template) |
| 2 Architect CONTRACT.md | Bloque "Tests audit: paths mockeados antes/después" obligatorio si CONTRACT propone flip | `nicolify-architect` (PR-4 alimenta prompt) |
| 3 Builder Step 0 | Grep tests path viejo antes flip code | `nicolify-backend` / `nicolify-agentic` (PR-4 alimenta agent prompt) |
| 4 Auditor Cat review | Cat 14 (business) / Cat 13 (agentic) "Default flip side-effect coverage" | `nicolify-{backend,agentic}-auditor` (PR-4 alimenta agent) |
| 5 Arch fitness test | `test_no_legacy_eventbus_mock_when_outbox_on.py` (PR-3) bloquea automatic | `tests/architecture/` |
| 6 TDD rule | `.claude/rules/tdd-mandatory.md` § "Default flag flips" obligatoria | `/pm` (PR-4) |
| 7 Runtime warning | `LegacyEventBus.publish` DeprecationWarning cuando flag True (PR-1 § 5) | shared/domain/events.py |

> Pattern análogo: `anti-duplication.md` (cross-module mirror detection). Anti-default-flip
> detecta side-effect path mismatch via flag flip + test-mock drift. Ambos defense in depth
> (PM PR.md → Architect CONTRACT.md → Builder Step 0 → Auditor Cat review → Arch fitness test).

## Penalizaciones

- Builder skip Step 1 grep → REVERT
- Auditor skip Cat 14/13 → re-audit
- Architect CONTRACT sin "Tests audit" cuando propone flip → REJECT, re-spawn
- Arch fitness violation = build fail (gate hard)
- Skip inventario update al agregar nuevo flag → process-learnings.md case study

## Ejemplos

### Ejemplo CORRECTO (commit hipotético):

```
feat(observability): flip LITELLM_PROXY_ENABLED default False→True

## Tests audited
- 12 tests migrated from `OpenAIService.generate_response` mock → `LiteLLMService.generate_response` mock
- 2 tests use `# arch-bypass: testing legacy capability` for adapter direct call validation
- 0 tests use `monkeypatch.setattr(LITELLM_PROXY_ENABLED=False)` band-aid

## Path old: backend/src/shared/infrastructure/llm/providers/{openai,kimi,...}.py direct
## Path new: backend/src/shared/infrastructure/llm/providers/litellm.py via proxy
## Verification:
- `pytest -x -q` PASS (default True)
- `LITELLM_PROXY_ENABLED=false pytest -x -q` PASS (legacy fallback)

[arch-fitness 79/79 PASS]
```

### Ejemplo INCORRECTO (lo que rompió 2026-05-04):

```
feat(events): switch emisores to outbox event bus adapter

# Sin sección "Tests audited"
# Sin grep tests path viejo
# Sin verify both flag values
# → 25 tests stale post-merge, polluter no detectado, 3h investigación
```
