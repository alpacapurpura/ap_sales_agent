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
10. Todos verdes en `make arch-test`.

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

> COMPLETAR.

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
8. Verificar `make arch-test` todos verdes.
9. Documentar cómo agregar exception (si genuina) en `.claude/rules/architectural-fitness.md`.

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

> COMPLETAR.
