# PR-3 — Anti-Default-Flip Enforcement (Rule + Arch Fitness Test)

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-3-anti-default-flip-enforcement |
| Sprint padre | S1-test-integrity-and-coverage |
| PI padre | PI-11-backend-quality-guardrails |
| Estado | ready |
| Tipo | architectural rule + enforcement test |
| Esfuerzo | M |
| Owner PM | /pm |
| Claimed by session | — |
| Created | 2026-05-04 |

## Problema

Failed `/pase-produccion` 2026-05-04 reveló patrón sin guardrail: **default flag flip = side-effect call path change** sin auditar tests asociados → 25 BE failures + polluter no identificable.

Causa: commit `64738354` flipeó `USE_OUTBOX_PATTERN_*` False→True. Tests seguían mockeando `LegacyEventBus.publish` (path muerto). Sin regla escrita ni enforcement automático.

**Sin PR-3:** próximo flip de `LITELLM_PROXY_ENABLED`, `USE_DEEPAGENTS_*`, `ENABLE_*` cualquier flag side-effect replicará el bug.

## Outcome esperado

| Outcome | Métrica |
|---|---|
| Regla escrita `.claude/rules/anti-default-flip-audit.md` | File existe + linkeado desde CLAUDE.md (conditional rule trigger "tocás `core/config.py` defaults") |
| Workflow obligatorio cementado | Doc tiene 4 steps mandatory: grep tests path viejo · update mocks path nuevo · run both flag values · documentar commit body |
| Arch fitness test bloqueador | `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py` — fail si test mockea `LegacyEventBus.publish` solo cuando outbox flag `True` |
| Bypass list documentado | Tests internos LegacyEventBus capability marker explícito |
| Failure message diagnostic | Test failure indica exact file:line + suggested migration pattern |

## Walking skeleton

### Step 1 — Rule design `.claude/rules/anti-default-flip-audit.md`

Estructura inspirada en `anti-duplication.md`:

```markdown
# Anti-Default-Flip Audit

**Origen:** failed `/pase-produccion` 2026-05-04. Commit `64738354` flipeó `USE_OUTBOX_PATTERN_*` False→True sin auditar tests que mockean path legacy → 25 BE failures + polluter no identificable.

## Regla cardinal

ANTES de flipear default de feature flag (`USE_*_PATTERN_*`, `LITELLM_PROXY_ENABLED`, `USE_DEEPAGENTS_*`, `ENABLE_*`, etc.) que cambia call path side-effect (events, persistence, logging, observability, LLM provider routing) → **OBLIGATORIO 4 STEPS**:

### Step 1 — Grep tests path viejo
{comando exacto}

### Step 2 — Update mocks path nuevo
- Migrar mocks al `adapter_bus` / nuevo path canónico
- O capturar via observability/persistence sink (outbox table, traces, etc.)

### Step 3 — Run full suite con BOTH old+new flag values
{commands}

### Step 4 — Documentar commit body
- "Flag X flipped Y→Z"
- "Tests audited: N tests migrated, M tests use bypass for legacy capability"
- "Path old: <path>, Path new: <path>"

## Inventario flags side-effect (SSoT)

| Flag | Side-effect path | Path viejo (False) | Path nuevo (True) | Tests probe |
|---|---|---|---|---|
| USE_OUTBOX_PATTERN_SALES_AGENT | events | LegacyEventBus.publish | adapter_bus.publish → outbox table | adapter_bus mock o outbox query |
| USE_OUTBOX_PATTERN_COPILOT | events | idem | idem | idem |
| USE_OUTBOX_PATTERN_BRAND | events | idem | idem | idem |
| LITELLM_PROXY_ENABLED | LLM routing | adapter providers/{kimi,deepseek,...}.py | litellm proxy provider | provider mock matching active path |
| USE_DEEPAGENTS_* (futuros) | agent orchestration | LangGraph plain | deepagents subagents | both paths probed |

## Anti-patterns prohibidos

- ❌ Flipear default sin grep tests path viejo
- ❌ Flipear default sin run full suite con ambos valores
- ❌ Commit body sin sección "Tests audited"
- ❌ Mockear path viejo cuando flag default es path nuevo (test no prueba nada real)
- ❌ Usar `monkeypatch.setattr(USE_*=False)` por test sin migrar mock — band-aid temporal solo

## Enforcement layers

| Layer | Mecanismo | Owner |
|---|---|---|
| 1 PM PR.md | Bloque "Default flips audited" mandatory cuando aplique | /pm skill |
| 2 Architect CONTRACT.md | Bloque "Tests audit: paths mockeados antes/después" obligatorio si CONTRACT propone flip | nicolify-architect |
| 3 Builder Step 0 | Grep tests path viejo antes flip code | nicolify-backend / nicolify-agentic |
| 4 Auditor Cat review | Cat 14 (business) / Cat 13 (agentic) "Default flip side-effect coverage" | nicolify-{backend,agentic}-auditor |
| 5 Arch fitness test | `test_no_legacy_eventbus_mock_when_outbox_on.py` (PR-3) bloquea automatic | tests/architecture/ |
| 6 TDD rule | `.claude/rules/tdd-mandatory.md` § "Default flag flips" obligatoria | /pm |

## Penalizaciones

- Builder skip Step 1 grep → REVERT
- Auditor skip Cat 14/13 → re-audit
- Architect CONTRACT sin "Tests audit" cuando propone flip → REJECT, re-spawn
- Arch fitness violation = build fail (gate hard)
```

### Step 2 — Arch fitness test `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py`

Detection logic via AST walk:

```python
"""Arch fitness: bloquea tests que mockean LegacyEventBus.publish solo cuando outbox flag está True por default.

Origen: PR-3 PI-11 — anti-default-flip enforcement.
"""

import ast
import pathlib

# Mock targets prohibidos cuando outbox flag True default
LEGACY_MOCK_TARGETS = {
    "LegacyEventBus.publish",
    "EventBus.publish",  # legacy path
    "shared.domain_events.legacy_event_bus.LegacyEventBus.publish",
}

# Paths nuevos canónicos esperados
ALLOWED_MOCK_TARGETS = {
    "adapter_bus.publish",
    "shared.domain_events.outbox.application.event_bus_adapter.publish",
}

# Bypass list — tests internos que prueban capability LegacyEventBus
BYPASS_FILES = {
    # tests que prueban LegacyEventBus.publish capability mismo (legitimately mock target)
    "tests/shared/domain_events/test_legacy_event_bus_capability.py",  # ej
    # marker explícito en file con comment "# arch-bypass: testing legacy capability"
}

def _walks_mocks(tree: ast.AST) -> set[str]:
    """Extrae mock targets de patches/mocks en un test file."""
    targets = set()
    for node in ast.walk(tree):
        # @patch("path.to.X")
        if isinstance(node, ast.Call):
            func = node.func
            is_patch = (
                (isinstance(func, ast.Name) and func.id in ("patch",))
                or (isinstance(func, ast.Attribute) and func.attr in ("patch", "object"))
            )
            if is_patch and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    targets.add(first.value)
        # mocker.patch(...) etc. similar
    return targets

def test_no_legacy_eventbus_mock_when_outbox_flag_default_on():
    """Bloquea tests que mockean LegacyEventBus.publish cuando default outbox = True.

    Workflow esperado: tests deben mockear adapter_bus o probe outbox table.
    Bypass: tests en BYPASS_FILES o con comment '# arch-bypass: testing legacy capability'.
    """
    repo = pathlib.Path(__file__).parent.parent
    violations = []
    for test_file in repo.rglob("tests/**/*.py"):
        if not test_file.name.startswith("test_"):
            continue
        rel_path = test_file.relative_to(repo)
        if str(rel_path) in BYPASS_FILES:
            continue
        source = test_file.read_text(encoding="utf-8")
        if "# arch-bypass: testing legacy capability" in source:
            continue
        try:
            tree = ast.parse(source, filename=str(test_file))
        except SyntaxError:
            continue
        mocks = _walks_mocks(tree)
        legacy_mocks = mocks & LEGACY_MOCK_TARGETS
        if legacy_mocks:
            violations.append(f"{rel_path}: legacy mock targets {legacy_mocks}")
    assert not violations, (
        "Tests mockean LegacyEventBus.publish cuando outbox flag default = True.\n"
        "Migrar a adapter_bus mock o outbox table probe. Ver `.claude/rules/anti-default-flip-audit.md`.\n"
        "Violations:\n" + "\n".join(f"  - {v}" for v in violations)
    )
```

(Code real lo escribe builder; spec acá es contractual.)

### Step 3 — Bypass mechanism

Tests legítimos que prueban capability legacy → bypass via:
- File path en `BYPASS_FILES` constant del test arch fitness
- O comment magic `# arch-bypass: testing legacy capability` en el test file

### Step 4 — Failure message diagnostic

Cuando test falla, mensaje debe:
- Listar exact file:line con mock target offendor
- Suggested migration: link a `.claude/rules/anti-default-flip-audit.md`
- Indicar bypass mechanism si aplica

### Step 5 — Performance budget

Test arch fitness debe completar <2s en suite. AST walk single-pass por archivo.

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A — Solo regla escrita (sin arch fitness) | Mínimo blast radius | No enforza automático; humanos olvidan | descartada — recurrencia garantizada |
| B — Solo arch fitness (sin regla escrita) | Enforza automático | No documenta workflow para futuros flags; agentes/skills no internalizan | descartada — falta context |
| C — Regla + arch fitness + integration agentes/skills (PR-4) | Defense in depth: layer humano + layer automático + layer agentes | Scope grande dividido | **ELEGIDA** — PR-3 owns rule + arch fitness; PR-4 owns agentes/skills integration |

## Validación técnica preliminar

- Modules afectados: `.claude/rules/`, `tests/architecture/`
- Blockers: ninguno (depende de PR-1 EventBus migration completa para que arch fitness no rompa baseline existente)
- Tiempo estimado: 1 architect Opus (compartido con PR-1) + 1 builder backend Sonnet + 1 auditor backend Opus

## Existing systems audit

| Sistema | Path | Decisión |
|---|---|---|
| Anti-duplication rule | `.claude/rules/anti-duplication.md` | Inspiración estructura. NO modificar — referencia cross |
| Existing arch fitness tests | `tests/architecture/test_*.py` | Patrón ratchet allowlist consistente |
| `LegacyEventBus` | `backend/src/shared/domain_events/legacy_event_bus.py` | Path real validar pre-test |

## Decisiones diferidas

- ¿Bypass via file path constant o solo via magic comment? Builder propone, auditor valida.
- ¿Arch fitness corre en `make verify` además de pytest? Default sí (parte de gate-runner standard).

## Out of scope

- Update agentes/skills (PR-4)
- Otros flags side-effect (workflow general aplicable, pero arch fitness inicial cubre solo `LegacyEventBus.publish` por ahora — extensión incremental futuro)
- TDD rule update (PR-4)

## Copilot-first checklist

- [x] No aplica — PR meta-arquitectural.

## Agentes / skills recomendados

| Fase | Agente/skill | Modelo | Prompt | Entregable |
|---|---|---|---|---|
| Pre-flight | `nicolify-context-builder` | Haiku | `prompts/00-context-prep.md` | CONTEXT-BRIEF.md |
| Architect | `nicolify-architect` (compartido PR-1) | Opus | (PR-1 prompt cubre PR-3 § 13 cross-link) | CONTRACT.md PR-3 |
| Build | `nicolify-backend` | Sonnet | `prompts/02-builder-start.md` | code + IMPL-LOG |
| Audit | `nicolify-backend-auditor` | Opus | `prompts/03-auditor-start.md` (auto-spawned) | REVIEW.md |
| Cierre | `/pm` | — | `prompts/04-pm-close.md` | RESULT.md |

## Surface impactada

| Tipo | Path | Cambio |
|---|---|---|
| Rule | `.claude/rules/anti-default-flip-audit.md` | NEW file |
| Arch fitness | `backend/tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py` | NEW file |
| CLAUDE.md | `/home/chris/AISALESHT/CLAUDE.md` | Conditional rule trigger entry |

## Tests requeridos (TDD)

- Arch fitness test mismo es el test (TDD: red baseline = tests existentes con legacy mock; green post-PR-1 = todos migrated)
- Test del test (meta): `test_no_legacy_eventbus_mock_when_outbox_on_bypass_works.py` — verifica bypass mechanism funciona

## Aceptación

- [ ] `.claude/rules/anti-default-flip-audit.md` creado
- [ ] CLAUDE.md update con conditional rule trigger
- [ ] `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py` creado
- [ ] Arch fitness test PASS post-PR-1 (sin violations)
- [ ] Bypass mechanism funcional + documentado
- [ ] Failure message diagnostic linkea regla
- [ ] Performance <2s
- [ ] `IMPL-LOG.md` completo
- [ ] `REVIEW.md` verdict PASS
- [ ] `RESULT.md` PM

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Arch fitness rompe baseline existente (tests aún no migrated PR-1) | PR-3 builder espera PR-1 build PASS antes shipping. O test arch fitness inicialmente con allowlist temporal que shrinks a 0 conforme PR-1 progress. Recomendado: PR-3 ship POST PR-1 PASS para evitar deadlock |
| AST walk false positives | Auditor valida + builder agrega bypass list expandible |
| Regla muy estricta bloquea futuros tests legítimos | Bypass mechanism documentado expande sin re-auditar regla |

## Notas operativas

- Builder PR-3 corre en paralelo a PR-1 si CONTRACT compartido permite, pero **arch fitness test deploy condicional**: se activa solo POST PR-1 PASS (cuando baseline está migrated). Mecanismo: variable env `STRICT_ANTI_LEGACY_MOCK=1` o PR-3 builder espera señal PR-1 before push final
- PR-4 referencia este PR-3 cuando agrega bloque PR.md template y agent prompts
