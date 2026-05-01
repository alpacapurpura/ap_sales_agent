# Handoff — S1-cascade-bugs-fix → PI-7 close

## Estado al cierre

| Campo | Valor |
|---|---|
| Sprint | shipped 2026-05-01 |
| PRs | 1/1 PASS |
| Métrica única éxito PI-7 | ✅ CUMPLIDA — bot Telegram responde voice-tenant Visionarias |

## Decisiones congeladas

D-1 a D-5 en `pis/active/PI-7-app-stability-restore/decisions.md`. Resumen:

- SPLIT scope PR cross-surface mid-flight (builder Sonnet vs PM ad-hoc) cuando una surface no requiere code
- EXTEND existing DTO con `from_attributes=True` (canonical Pydantic v2 ORM→DTO)
- Multi-causa fix infra (env propagation + memory limit) cuando architect missed
- `cost_usd=0` aceptado deuda separada (no bloquea PI-7)
- Telegram Web typing NO es bug nuestro (cliente bug)

## Surface entregada

- `backend/src/modules/brand/application/services/brand_data_adapter.py` — Bug #7 fix
- `backend/tests/modules/brand/application/services/test_brand_data_adapter_pr2.py` — RED→GREEN regression tests
- `docker-compose.yml` — Bug #9 LITELLM_ENVIRONMENT propagation + memory 1536M
- `.env.example` — gap template fix
- `.env` (local gitignored) — 5 vars LITELLM agregadas ad-hoc

## Siguiente paso (Chris decision)

PI-7 cierra. Chris explícito: si encuentra más bugs → abrirá NUEVO PI dedicado a pruebas E2E pre-pase-producción.

Posibles candidatos PI siguiente (Chris decide):

| Opción | Tipo | Trigger |
|---|---|---|
| **PI-8 E2E pre-prod** | testing | Chris flagea bugs adicionales smoke |
| Continuar PI-3 sales-agent-improvement | feature | Discovery validado |
| Continuar PI-4 brand-evolutive-maintenance S1 | maintenance | PR-1 ready |
| Continuar PI-5 copilot-multicanal-telegram S3 (HITL pending) | feature | S2 shipped |

## Deudas técnicas detectadas (NO scope PI-7)

| # | Deuda | Severidad | Tracking |
|---|---|---|---|
| 1 | `cost_usd=0` pricing resolution falla provider mapping (deepseek tagged openai) | MED | Backlog separado — abrir PR follow-up módulo sales_agent observability |
| 2 | `BrandDataAdapter` sin try/except graceful-degradation fallback | LOW | Backlog separado — PR follow-up brand application |
| 3 | LiteLLM healthcheck CMD `curl` no existe en imagen Chainguard wolfi-base | LOW | Backlog separado — fix infra próximo PR |
| 4 | Architect/Haiku context-builder process improvement: forzar `docker logs` + `docker events` en CONTRACT cuando container exited | LEARNING | Process update `.claude/skills/pm/SKILL.md` o template prompts |

## Process learnings consolidados (escalate `process-learnings.md`)

L-1 (architect missed root causes infra), L-4 (compose `environment:` propagation explícita), L-5 (OOM 137 silent en logs app), L-7 (smoke Chris-mediated > synthetic) → migrar a `docs/pm-nico/process/process-learnings.md` post-archive.
