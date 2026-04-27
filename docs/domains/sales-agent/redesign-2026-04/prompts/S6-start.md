# Handoff prompt · S6 start

> **Refinado al cierre de S5.**

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S6 — Architectural fitness tests ratchet
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S6-fitness-tests-ratchet.md
📝 Aprendizajes: learnings/S0-*..S5-*.

CONTEXTO:
- S0..S5 cerradas. Infra estable, momento óptimo para freeze.
- Branch: development limpio.
- Último commit: {HASH}
- Hooks: callback handler, PII regex, channel registry, model tier, cache_boundary compose, dual-write cutover.
- Tech debt en radar: {LIST}

PROTOCOLO:
1. Lee README + 00 (§3) + 01 + 02 + 03 + 04 + 05 + learnings de S0-S5 + phases/S6.
2. Research mandate: arch fitness tests Python AST 2026, import-linter contracts, ratchet pattern.
3. Lectura: copilot tests/architecture/test_copilot_anchors.py, test_no_new_copilot_module_imports.py, test_subagent_isolation_invariants.py, .claude/rules/architectural-fitness.md.
4. TaskCreate.
5. TDD: tests de arquitectura SON los tests. Escribir asumiendo allowlist vacía → ver violations actuales → freeze (eliminar quick wins antes si posible).
6. Tests obligatorios:
   - test_no_new_sales_agent_module_imports (ratchet)
   - test_sales_agent_anchors (cap)
   - test_sales_agent_callback_handler_invariants (best-effort)
   - test_pii_sanitization_coverage_sales_agent (AST)
   - test_no_hardcoded_models_sales_agent (verify exists from S4)
   - test_no_hardcoded_channels_sales_agent (verify exists from S5)
   - test_sales_agent_tenant_isolation
   - test_sales_agent_system_prompt_order (verify exists from S3)
7. Quality gates: make arch-test todos verdes.
8. §3 sigue funcionando.
9. Tech debt log: si quick wins durante freeze → FIXED entries.
10. learnings/S6-* + prompts/S7-start.md refinado.

PRINCIPIOS: ratchet shrinks only. Documentar cómo extender allowlist con justificación.

Empieza con paso 1.
```
