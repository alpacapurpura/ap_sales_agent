# PR-1 — Fix Broken Tests & Arch Snapshots

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-1-fix-broken-tests-and-arch-snapshots |
| Sprint padre | S1-test-integrity-and-coverage |
| PI padre | PI-11-backend-quality-guardrails |
| Estado | ready |
| Tipo | refactor |
| Esfuerzo | L |
| Owner PM | /pm |
| Claimed by session | — |

## Problema

~10 tests fallidos bloquean confianza en CI. La mitad son tests desactualizados por evolución del código; la otra mitad son fallos reales (outbox flags, temperatura Kimi, tabla SQLite faltante). Además, 4 violaciones de import cruzado DDD y 1 archivo con naming no-snake-case rompen los gates de arquitectura.

## Outcome esperado

`pytest` pasa 100% sin `--deselect` obligatorios. Arch fitness 78/78 verde.

## Walking skeleton

Fix mecánico de tests + snapshots. Sin cambio de comportamiento user-facing. Dividido en dos surfaces:
- **Business surface** (`brand`, `shared`, `arch fitness`): fix outbox flags, event bus, DDD boundaries, naming.
- **Agentic surface** (`sales_agent`, `copilot`): fix prompt fragments, voice API legacy 410, temperature clamping, offer section tools.

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A — Fix todo en un solo PR con 2 builders paralelos (business + agentic) | Cohesivo CI-verde en un solo merge; Opus aprovecha contexto 1M | Cross-surface requiere coordinación | **ELEGIDA** |
| B — Split por módulo (brand PR, copilot PR, sales_agent PR...) | Aisla blast radius | 4-5 PRs overhead; mismo sprint se satura | descartada — overhead PM > valor |

## Validación técnica preliminar

- Modules afectados: `brand`, `copilot`, `sales_agent`, `shared`, `campaigns`, `crm`.
- Blockers: decisión producto sobre default outbox True/False.
- Tiempo estimado: 1 iter architect (skip, puro fix) + 2 iter builders + audit.

## Existing systems audit

Skip. Este PR no crea nuevos subsistemas; solo fixea tests y snapshots de subsistemas existentes.

## Decisiones diferidas

- Default outbox: `True` actual vs `False` esperado por tests. Chris decide; builder implementa.
- Imports DDD cruzados: si son intencionales, agregar a allowlist; si no, refactor.

## Out of scope

- Aumentar cobertura (va en PR-2).
- Cambiar lógica de negocio.
- Remover endpoints legacy (solo adaptar tests).

## Copilot-first checklist

- [x] No aplica — este PR es infraestructura de calidad, no operable desde copilot.

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt | Entregable |
|---|---|---|---|
| Implementation (business) | `nicolify-backend` | `prompts/02-builder-start.md` (business variant) | code + tests + IMPL-LOG |
| Implementation (agentic) | `nicolify-agentic` | `prompts/02-builder-start.md` (agentic variant) | code + tests + IMPL-LOG |
| Audit (business) | `nicolify-backend-auditor` | `prompts/03-auditor-start.md` | REVIEW-backend.md |
| Audit (agentic) | `nicolify-agentic-auditor` | `prompts/03-auditor-start.md` | REVIEW-agentic.md |
| Cierre | `/pm` | `prompts/04-pm-close.md` | RESULT.md |

## Surface impactada

| Tipo | Path | Cambio |
|---|---|---|
| Tests | `tests/modules/brand/test_outbox_adapter_integration.py` | fix assertions / setup |
| Tests | `tests/modules/brand/test_brand_section_updated_event.py` | fix tabla outbox en SQLite |
| Tests | `tests/modules/copilot/test_voice_api.py` | adaptar a `410 Gone` legacy |
| Tests | `tests/modules/copilot/test_voice_combined.py` | adaptar a `410 Gone` legacy |
| Tests | `tests/modules/copilot/test_offer_section_tools.py` | fix `suggestions` empty |
| Tests | `tests/modules/copilot/test_deep_agent_factory_wire.py` | fix temperature clamp |
| Tests | `tests/modules/copilot/test_outbox_adapter_integration.py` | fix flag assertions |
| Tests | `tests/modules/sales_agent/prompts/test_compose_system_prompt.py` | agregar `CAMPAIGN_CONTEXT` |
| Tests | `tests/architecture/test_sales_agent_system_prompt_order.py` | agregar `CAMPAIGN_CONTEXT` |
| Tests | `tests/architecture/test_ddd_boundaries.py` | allowlist o refactor imports |
| Tests | `tests/architecture/test_sales_agent_anchors.py` | agregar `SALES-AGENT-OUTBOUND-PR7` |
| Tests | `tests/architecture/test_folder_naming.py` | exception `_dependencies.py` |
| Tests | `tests/shared/domain_events/test_event_bus_adapter.py` | fix default flag |
| Código (posible) | `src/shared/domain_events/...` | fix `_is_outbox_enabled` si bug real |
| Código (posible) | `src/modules/sales_agent/...` | fix temperature clamp si bug real |

## Tests requeridos (TDD)

- Todos los tests listados en Surface impactada deben pasar.
- 0 nuevos tests (puro fix).

## Aceptación

- [ ] `pytest` 0 failed, 0 deselected obligatorios.
- [ ] Arch fitness 78/78 PASS.
- [ ] `IMPL-LOG.md` completo por cada builder.
- [ ] `REVIEW-backend.md` + `REVIEW-agentic.md` sin FAIL.
- [ ] `RESULT.md` escrito por PM.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Fix de test revela bug de producto real → scope creep | Regla: si bug real → documentar en IMPL-LOG, no fixear comportamiento en este PR (salvo que sea trivial 1-línea). |
| Builders paralelos tocan mismo archivo (ej. `tests/architecture/...`) | Asignar archivos exclusivos por surface; `test_folder_naming.py` va a business builder. |
