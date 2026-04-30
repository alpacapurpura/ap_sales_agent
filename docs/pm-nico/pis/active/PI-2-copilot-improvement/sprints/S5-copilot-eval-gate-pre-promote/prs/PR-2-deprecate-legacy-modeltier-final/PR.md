# PR-2-deprecate-legacy-modeltier-final

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-2-deprecate-legacy-modeltier-final |
| Sprint padre | S5-copilot-eval-gate-pre-promote |
| PI padre | PI-2-copilot-improvement |
| Estado | ready (depends PR-1) |
| Tipo | refactor (cleanup definitivo allowlist) |
| Esfuerzo | S (~5 archivos, audit final) |
| Owner PM | /pm |

## Problema

Post-S3 PR-1 cleanup convergencia ModelTier→ModelRole, allowlist `KNOWN_LEGACY_LLM_FILES` quedó shrunk a ~5 archivos (verify post-S3 actual count). Si quedan archivos residuales legacy, son deuda permanente. PI-2 cierre cero deuda obliga 0 entries.

JTBD Chris: "Cero deuda final. Sin asteriscos pendientes. Sistema listo para 1000+ tenants sin sorpresas."

## Outcome esperado

- `KNOWN_LEGACY_LLM_FILES` allowlist en `test_llm_routing_ssot.py` = 0 entries.
- Audit final: `grep -rn "ModelTier\|TIER_METADATA\|COPILOT_TIER_" backend/src/ docs/` = 0 hits (excepto `docs/domains/llm-routing.md` sección "Anti-patterns documentados" + process-learnings histórico).
- `docs/domains/llm-routing.md` sección "Migration timeline" actualizada: PI-2 closed.
- PI-2 retro.md escrito + folder migrado a `pis/archive/PI-2-copilot-improvement/`.

## Walking skeleton

1. **Audit grep cross-codebase** identifica residuales legacy.
2. **Refactor/eliminar** cada residual (probable archivos test legacy, hooks observability tier=role rename).
3. **Update arch fitness test SSoT**: shrink allowlist a 0 (test verifica explícitamente).
4. **Update doc** `docs/domains/llm-routing.md`:
   - Sección "Modelos activos hoy" reflect estado final post-S3+S4+S5
   - Sección "Migration timeline" — marca S5 shipped
   - Sección "Anti-patterns" mantiene histórico para learnings
5. **PI-2 retro**:
   - Escribir `docs/pm-nico/pis/active/PI-2-copilot-improvement/retro.md` (5 sprints, ~15 PRs total, learnings consolidados)
   - Mover folder a `docs/pm-nico/pis/archive/PI-2-copilot-improvement/`
   - Update `roadmap.md` Done section + Now/Next adjust

## Existing systems audit

```bash
grep -rn "ModelTier\|TIER_METADATA\|COPILOT_TIER_" backend/src/ docs/ tests/
cat backend/tests/architecture/test_llm_routing_ssot.py | grep -A 30 "KNOWN_LEGACY_LLM_FILES"
```

**Sistemas:** post-S3+S4 esto es solo cleanup residual. NO new layers.

## Surface impactada

| Tipo | Path | Cambio |
|---|---|---|
| BE refactor | residuales identified by audit | DELETE/refactor |
| Arch fitness | `test_llm_routing_ssot.py` | KNOWN_LEGACY_LLM_FILES = set() |
| Doc | `docs/domains/llm-routing.md` | sección Migration timeline updated |
| PI archive | `docs/pm-nico/pis/active/PI-2-copilot-improvement/` → `archive/` | mv + retro.md |
| Roadmap | `docs/pm-nico/roadmap.md` | PI-2 Now → Done |

## Tests requeridos

- `test_llm_routing_ssot.py::test_no_new_modeltier_imports` PASS con allowlist vacío
- `test_llm_routing_ssot.py::test_no_new_llm_factory_layers` PASS
- `test_llm_routing_ssot.py::test_no_copilot_tier_env_vars` PASS

## Aceptación

- [ ] Tests verde con allowlist = 0
- [ ] Grep cero residuales en src/
- [ ] retro.md escrito
- [ ] PI folder en archive/
- [ ] roadmap.md updated
- [ ] PI-2 cap "LLM stack convergencia + hot-swap + per-tenant + eval gate" lineage completo en current-state/copilot.md

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Audit identifica más residuales que esperado → scope crece | Si scope >10 archivos → split en PR-2a + PR-2b. Si <10 → ship single PR |
| PI-2 retro mueve folder pero deja archivos linked desde otros docs (broken references) | grep `pis/active/PI-2-copilot-improvement` post-mv → update referencias a `pis/archive/PI-2-copilot-improvement` |
