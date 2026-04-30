# Sprint S5 — copilot-eval-gate-pre-promote

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S5-copilot-eval-gate-pre-promote |
| PI padre | PI-2-copilot-improvement |
| Estado | in-progress — S4 shipped 2026-04-30, PR-1 claimed |
| Inicio estimado | post S4 |
| Cierre estimado | S4+1 semana |
| Owner PM | /pm |

## Objetivo (1 línea)

Habilitar eval gate pre-promote en admin UI: NO permitir activar modelo nuevo sin score ≥0.95 vs incumbente en 50+ goldens, escalable cuando lleguen 1000+ tenants y catastrofes regresión calidad cuesten exponencialmente más.

## Pre-handoff (input desde S4)

- DB registry runtime + admin Streamlit `/admin/llm-models` CRUD live
- GrowthBook per-tenant override + A/B funcionando
- Eval gate framework ya shipped S2 PR-3 (mantenido en S3 cleanup): `backend/src/modules/copilot/evals/{golden_dataset, runner, scorers, goldens}`

## Plan PRs

| PR | Folder | Descripción | Esfuerzo | Estado |
|---|---|---|---|---|
| PR-1 | `prs/PR-1-eval-gate-admin-wiring/` | Wire eval gate framework S2 al admin UI: botón "Test candidate" corre eval inline, botón "Promote" bloqueado si score <0.95. CI integration `@pytest.mark.eval_gate` corre pre-merge para cualquier model swap commit. | M-L | not-started |
| PR-2 | `prs/PR-2-deprecate-legacy-modeltier-final/` | Cleanup definitivo allowlist `test_llm_routing_ssot.py` a 0 entries. Eliminar archivos legacy ModelTier residuales. Audit final cero deuda LLM routing. | S | not-started |

## Criterio éxito

- [ ] Admin UI: botón "Test candidate" disponible para cualquier role/model. Click → eval gate runner ejecuta inline + score reportado.
- [ ] Promote bloqueado si score <0.95 — admin UI muestra error "Eval gate failed: 0.87 < 0.95 threshold"
- [ ] CI integration: PR commit `.env` con `AI_MODEL_<ROLE>=<new>` → CI corre eval gate marker → merge bloqueado si fail
- [ ] `test_llm_routing_ssot.py::KNOWN_LEGACY_LLM_FILES` allowlist = 0 entries (eliminado todo legacy ModelTier)
- [ ] Doc `docs/domains/llm-routing.md` actualizado: sección "Modelos activos hoy" + "Anti-patterns" reflect estado final post-S5
- [ ] PI-2 cierra: retro.md + mover a `pis/archive/`

## Out of scope

- Embeddings migration (PI dedicado)
- Sales_agent voice swap (Q3 2026)
- Specialist tier swap (specialist eval gate goldens >100 — PI futuro)
- Multicanal copilot Bloque A (PI separado o sub-task)

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Eval gate corre lento (>5min CI) | Parallel async client calls + cap 50 goldens |
| Goldens dataset stale (calidad models cambia) | Admin UI feature: "Refresh goldens" → curate new from prod copilot_trace_event sample |
| Score 0.95 threshold muy estricto / muy laxo | Per-role threshold configurable (NANO 0.95, REASONING 0.93 si más variabilidad aceptable) |
