# S6 · Architectural fitness tests ratchet

## Objetivo

Espejar los fitness tests de copilot para sales_agent. Congelar el estado limpio post-S0..S5. Anchors `[SALES-AGENT-*]` con cap. Ratchet de cross-module imports. Best-effort observability invariants. Cualquier regresión arquitectónica futura falla CI.

## Dependencias

- S0, S1, S2, S4, S5 cerrados (infra estable).
- S3 cerrado idealmente (prompts compose en su sitio).

## Criterios de éxito

1. `tests/architecture/test_no_new_sales_agent_module_imports.py` con allowlist actual frozen.
2. `tests/architecture/test_sales_agent_anchors.py` con `ANCHOR_REGISTRY` cap.
3. `tests/architecture/test_sales_agent_callback_handler_invariants.py` (best-effort writes).
4. `tests/architecture/test_pii_sanitization_coverage_sales_agent.py`.
5. `tests/architecture/test_sales_agent_system_prompt_order.py` (ya creado en S3 — verificar).
6. `tests/architecture/test_no_hardcoded_models_sales_agent.py` (de S4).
7. `tests/architecture/test_no_hardcoded_channels_sales_agent.py` (de S5).
8. `tests/architecture/test_sales_agent_tenant_isolation.py` — toda query a `sales_agent_*` filtra `tenant_id`.
9. `tests/architecture/test_sales_agent_provider_compliance.py` — `BaseAgentProvider` interface (si existe).
10. **`tests/architecture/test_no_legacy_agent_trace_reads.py` — bloquea reads/writes a `agent_trace_model` y `agent_log_model` post-cutover. Allowlist sólo: migración drop + tests legacy regression.**
11. **`tests/architecture/test_no_resumen_deprecated_references.py` (de S00) — re-verificar verde, whitelist `growth-studio/**/Resumen*`.**
12. **`tests/architecture/test_admin_no_legacy_table_reads.py` — `sales_audit.py` post-cutover no lee `agent_trace_model`.**
13. Todos verdes en `make arch-test`.

## Research mandate

### Queries WebSearch

1. `architectural fitness tests Python AST grep semgrep 2026 ratchet pattern` — herramientas vigentes.
2. `import-linter contract architecture python boundaries` — alternativa a AST custom.

### Tessl tiles

- N/A.

### Lectura obligatoria

- Aprendizajes S0-S5.
- `backend/tests/architecture/test_copilot_anchors.py`.
- `backend/tests/architecture/test_no_new_copilot_module_imports.py`.
- `backend/tests/architecture/test_subagent_isolation_invariants.py` (no aplica direct pero patrón ratchet relevante).
- `.claude/rules/architectural-fitness.md`.

### Hallazgos research

Fuentes consultadas (2026-04-28):

- [qntm — Ratchets in software development](https://qntm.org/ratchet) — define ratchet como "lock, not goal": fitness function se agrega *después* de limpiar el módulo, congela trabajo hecho. Allowlist crece sólo cuando entry se elimina (shrink-only). Confirmado: no escribir tests asumiendo el código que querés — son tests para el código que tenés. Aplica a S6 directo.
- [Hands On Architects — Protecting Architecture with Automated Tests in Python](https://handsonarchitects.com/blog/2026/protecting-architecture-with-automated-tests-in-python/) — patrón canónico para arch tests Python: AST parse + frozen baseline. PyTestArch mencionado como alternativa pero coincide con el approach AST custom que ya usa copilot. NO migrar a librería externa — aumenta dependencia sin ganar nada. Mantengo AST custom mirror del pattern copilot.
- [Import Linter — contract types](https://import-linter.readthedocs.io/en/v2.7/contract_types.html) — alternative a AST custom. Soporta forbidden / layered / independence contracts. Evaluado: NO migrar. (a) repo ya tiene 60+ arch tests AST funcionando, (b) import-linter no soporta nativamente "ratchet allowlist + shrinks-only" — habría que envolver con `frozenset` igual, (c) cost de deploy vs current zero-dep solution.
- [pytest-sqlalchemy-mock + Core27 transactional pytest async SA pattern](https://www.core27.co/post/transactional-unit-tests-with-pytest-and-async-sqlalchemy) — confirma el patrón canónico: conftest.py centraliza `SessionLocal` mock + autouse fixtures cross-test. Promover los 2 fixtures duplicados (`_mute_trace_node_writes` + `_stub_session_local`) a `tests/modules/sales_agent/conftest.py` cuando 3+ tests lo necesitan — hoy son 2, S6 ratchet pass los promueve preventivo porque las arch tests futuras (PII coverage, callback handler invariants) van a requerir mismo mock.
- [Semgrep AST custom rules](https://www.devzery.com/post/guide-to-understanding-python-s-ast-abstract-syntax-trees) — patrón "walk Compare/Dict/Call nodes". Aplicado en `test_no_hardcoded_channel_in_output_manager.py` (S5) + `test_no_hardcoded_models_sales_agent.py` (S4). Ratchet S6 sigue mismo patrón.

Decisiones derivadas del research:

1. **Mantener AST custom (no migrar a import-linter ni PyTestArch).** Pattern existente funciona; cambio es scope creep.
2. **Allowlist `KNOWN_VIOLATIONS = frozenset()` cuando posible.** Sólo cuando AST scan revela violations cross-fase mayor → docstring con razón + DEFERRED en tech-debt log.
3. **Sweeps oportunista ANTES del freeze.** Dropea allowlist size + match el principio "lock not goal".
4. **Tests AST NO importan src.modules.sales_agent.\*** en runtime — usan `ast.parse(file.read_text())` para evitar coupling a refactors internos. Confirmed via lectura de `test_copilot_anchors.py` + `test_no_new_copilot_module_imports.py`.

### Ajustes vs plan original

- **Step 2 (anchors test)**: el plan documenta `[SALES-AGENT-*]` anchors en code; los anchors actuales en sales son `[SALES-AGENT-CACHE-PREFIX-S3]` + `[SALES-AGENT-CHANNEL-REGISTRY-S5]` (declarados en docstrings de arch tests). Los anchors en sales sources están vacíos hoy — el ANCHOR_REGISTRY se sembrará con los slogans canónicos por subpaquete (callback handler, PII sanitize, compose prompt, channel registry, model tier) y la primera vez los matches aparezcan en src/.
- **Step 8-10 (legacy drop)**: el plan original incluía drop de `agent_trace_model` + `LLMLogModel` legacy + cutover `sales_audit.py`. Decisión actualizada — la **ventana dual-write** son 4 semanas desde S1 cierre (2026-04-28). Hoy estamos en mismo día — ventana NO cumplida. Drop legacy + cutover admin se difieren a una **fase posterior** (S6.5 o post-S10). S6 se enfoca en infra ratchet + sweeps + invariantes. `test_no_legacy_agent_trace_reads.py` se omite (early — bloquearía dual-read intencional). `test_admin_no_legacy_table_reads.py` se omite. Se documenta DEFERRED.
- **Step 11 verify (test_no_resumen_deprecated_references)**: ya existe, sólo correr.
- **Sweeps S5/S4 deferreds**: ejecutados en este S6 antes del freeze para reducir allowlist (shim cleanup copilot + LLM_ROLE_BY_SITE expansion + fixture conftest promotion).

---

## Diseño

### Ratchet pattern

```python
# tests/architecture/test_no_new_sales_agent_module_imports.py
KNOWN_VIOLATIONS_FROZEN = frozenset([
    # Allowlist congelada al final de S5.
    # Solo shrinks. Nuevo violator → fail.
])

def test_no_new_sales_agent_module_imports():
    current = scan_sales_agent_imports()
    new = current - KNOWN_VIOLATIONS_FROZEN
    assert not new, f"New cross-module imports: {new}"
```

### Anchors

```python
# tests/architecture/test_sales_agent_anchors.py
ANCHOR_REGISTRY = {
    "[SALES-AGENT-CALLBACK]": 1,
    "[SALES-AGENT-PII-SANITIZE]": 1,
    "[SALES-AGENT-COMPOSE-PROMPT]": 1,
    "[SALES-AGENT-CHANNEL-REGISTRY]": 1,
    # ...
}
ANCHOR_CAP = 20  # bumpear con justificación si excede

def test_anchors_within_cap():
    found = scan_anchors()
    assert len(found) <= ANCHOR_CAP
```

### Best-effort handler invariant

```python
def test_sales_agent_callback_handler_best_effort():
    """Handler exception NUNCA propaga al turn."""
    handler = SalesAgentCallbackHandler(...)
    handler._llm_call_repo.add = AsyncMock(side_effect=Exception("DB down"))
    # Should NOT raise:
    await handler.on_llm_end(response=fake_response, run_id=...)
```

### PII sanitization coverage

```python
def test_no_pii_writes_unsanitized():
    """AST scan: every `repo.add(...)` para tablas sales_agent_* tiene
    sanitize_payload() en el call site."""
    violations = []
    for file in glob("src/modules/sales_agent/**/*.py"):
        tree = ast.parse(read(file))
        for call in walk_calls(tree, target="add"):
            if not _has_sanitization_above(call):
                violations.append((file, call.lineno))
    assert not violations
```

### Tenant isolation

```python
def test_sales_agent_queries_filter_tenant():
    """Ratchet: every SELECT/UPDATE/DELETE en sales_agent_* tables tiene WHERE tenant_id=..."""
    # Scan via grep + AST verification.
```

---

## Plan TDD

Tests de arquitectura SON los tests. RED test = test escrito antes de pasar.

1. Escribir cada test asumiendo allowlist vacía.
2. Correr → verá violations actuales.
3. Volcar violations a `KNOWN_VIOLATIONS_FROZEN`.
4. Re-correr → GREEN.
5. (Opcional) eliminar violations triviales antes del freeze para reducir allowlist.

---

## Implementación step-by-step

1. `test_no_new_sales_agent_module_imports.py` — escan + freeze allowlist.
2. `test_sales_agent_anchors.py` — registry + cap.
3. `test_sales_agent_callback_handler_invariants.py` — best-effort.
4. `test_pii_sanitization_coverage_sales_agent.py` — AST scan.
5. `test_no_hardcoded_models_sales_agent.py` (verify exists from S4).
6. `test_no_hardcoded_channels_sales_agent.py` (verify exists from S5).
7. `test_sales_agent_tenant_isolation.py`.
8. **`test_no_legacy_agent_trace_reads.py`** — AST scan tras cutover.
9. **Migration drop** `agent_trace_model` + `agent_log_model` legacy (idempotente DROP IF EXISTS).
10. **`sales_audit.py` cutover** — borrar query legacy, dejar solo `sales_agent_trace_event`.
11. **`test_admin_no_legacy_table_reads.py`** — verifica admin Streamlit no lee tablas legacy.
12. Verificar `make arch-test` todos verdes.
13. Verificar admin smoke (`tests/admin/test_admin_smoke.py`) verde post-cutover.
14. Documentar cómo agregar exception en `.claude/rules/architectural-fitness.md`.

---

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Allowlist congela violations que deben fixear primero | Antes de freeze, identificar quick wins (3-5 fixes). |
| Tests demasiado estrictos rompen evolución legítima | Documentar cómo extender allowlist con justificación. |
| AST scan falsos positivos (sanitization en helper distinto) | Permitir `# pragma: sanitization-ok` con razón. Whitelist limitada. |

---

## Tech debt watchpoints

- Si quick wins del freeze son demasiados → diferir a fase nueva post-S6.
- Si scan detecta DDD violations difíciles → loggear como DEFERRED hacia un cleanup phase.

---

## Ajustes vs plan original

Ver sección "Ajustes vs plan original" dentro de "Hallazgos research" (arriba).
