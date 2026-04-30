# IMPL-LOG — PR-1-drop-buyer-persona-fields

> Owner: builders. Append-only durante implementación.

## BE implementation

### Sesión 2026-04-29 — `nicolify-backend`

#### Contexto cargado
- `PR.md` ✓
- `CONTRACT.md` ✓ (migración + schema deltas)
- `current-state/brand.md` + `current-state/copilot.md` ✓
- Rules: backend-ddd, tenant-isolation, backend-migrations, tdd-mandatory, git-safety, parallel-safety ✓
- Skills: `brand-expert` + `copilot-expert` ✓

#### Decisiones implementación
- **Distinct objections preservados.** `offer.objections` (módulo distinto) y `sales_agent.objection_history` (session-state) NO se tocan. Solo cae `buyer_persona.objections` + `buyer_persona.preferred_channels`. Regression test `test_offer_list_paths_objections_still_present` blinda este límite.
- **Migración DROP COLUMN IF EXISTS.** Raw SQL idempotente (regla `backend-migrations.md`). Downgrade re-crea columnas vacías — data populada antes de upgrade NO se recupera. Documentado en docstring; aceptado por Chris (`can_propose=False` + sin downstream consumer real).
- **Slot order del template preservado.** `interview/buyer_persona_doc_extraction.j2` cae líneas de rule-4 (objections / preferred_channels) sin alterar pre/post para no romper cache prefix de Anthropic prompt cache.
- **Completeness denominator 9→7.** `_PROFILE_FIELDS` en `api/buyer_personas.py` ahora tiene 7 entries. Test `test_completeness_denominator_is_seven` blinda.
- **TDD layer-by-layer ejecutado.** RED tests primero (`test_buyer_persona_fields_dropped_regression.py` 21 cases) → GREEN domain → infrastructure → application → api → copilot.

#### Sub-deliverables completados
- [x] Domain: `BuyerPersona` Pydantic entity sin fields + `BUYER_PERSONA_SECTION_MAP` / `BUYER_PERSONA_FIELD_OVERRIDES` sin entries
- [x] Infrastructure: `BuyerPersonaModel` SQLA columns dropped + repository update methods
- [x] API: DTOs request + response sans fields, route `_PROFILE_FIELDS` 9→7
- [x] Copilot: `BuyerPersonaPersister._LIST_FIELDS`, `field_paths_hint._LIST_PATHS["buyer_persona"]`, prompt template rule-4, `extraction_domain_registry` comment
- [x] Migration: `acdcfa45d526_drop_buyer_persona_fields.py` raw SQL idempotente
- [x] Regression test suite: 21 cases en `test_buyer_persona_fields_dropped_regression.py`
- [x] Existing test fixtures actualizados: `test_buyer_persona_entity.py`, `test_buyer_persona_model.py`, `test_buyer_persona_repository.py`, `test_buyer_persona_extraction_template.py`, `test_editable_fields_integration.py`, `test_extract_validation.py`

#### Tests escritos (regression)
- `test_buyer_persona_entity_has_no_objections_field` — Pydantic entity
- `test_buyer_persona_entity_has_no_preferred_channels_field` — Pydantic entity
- `test_buyer_persona_model_has_no_objections_column` — SQLA model
- `test_buyer_persona_model_has_no_preferred_channels_column` — SQLA model
- `test_response_dto_excludes_objections|preferred_channels` — response DTO
- `test_update_dto_excludes_objections|preferred_channels` — update DTO
- `test_profile_fields_excludes_dropped_fields` — `_PROFILE_FIELDS` route
- `test_completeness_denominator_is_seven` — fields count 9→7
- `test_field_contract_section_map_excludes_*` — domain registry
- `test_field_contract_overrides_excludes_*` — domain registry
- `test_copilot_persister_list_fields_excludes_*` — persister
- `test_field_paths_hint_buyer_persona_excludes_*` — copilot hint
- `test_offer_list_paths_objections_still_present` — guard contra over-cleanup (offer.objections vive)
- `test_extraction_template_does_not_mention_*_as_list_field` — prompt template

#### Quality gates
- [x] Ruff verde (3 import-sort fixes auto-aplicados, ahora clean)
- [x] Pytest brand + copilot — 1997 passed
- [x] Pytest architecture — 644 passed (1 deselected: `test_module_folders_have_ddd_layers` — falla pre-existente por dir vacía `modules/campaigns/observability` de sesión paralela PI-1, no PR-1)
- [x] Migration idempotente verde — clone DB `migration_test_pr1` ciclo `stamp 082 → upgrade head → downgrade -1 → upgrade head → upgrade head (no-op)`. Verificado columns desaparecen tras upgrade y reaparecen tras downgrade.

#### Bloqueadores encontrados
- Ninguno bloqueante. Note: arch test `test_module_folders_have_ddd_layers` falla por leftover dir `backend/src/modules/campaigns/observability/` (vacía, untracked) de sesión paralela PI-1. NO mío. Reportado intacto.

#### Decisiones diferidas durante implementación
- Backup script (CONTRACT lo flageó como opt-in): omitido — `can_propose=False` + zero downstream consumers + Chris explicitly accepted data loss.

#### Surface real entregada
| Tipo | Path | Estado |
|---|---|---|
| Domain entity | `backend/src/modules/brand/domain/buyer_persona.py` | objections + preferred_channels removed |
| Field contract | `backend/src/modules/brand/domain/buyer_persona_field_contract.py` | section_map + overrides cleaned |
| SQLA model | `backend/src/modules/brand/infrastructure/models/buyer_persona_model.py` | columns dropped |
| Repository | `backend/src/modules/brand/infrastructure/repositories/buyer_persona_repository.py` | update methods cleaned |
| DTO | `backend/src/modules/brand/api/dto/buyer_personas.py` | request + response sans fields |
| Route | `backend/src/modules/brand/api/buyer_personas.py` | `_PROFILE_FIELDS` 9→7 |
| Copilot persister | `backend/src/modules/copilot/infrastructure/persisters/buyer_persona_persister.py` | `_LIST_FIELDS` cleaned |
| Copilot hint | `backend/src/modules/copilot/domain/field_paths_hint.py` | `_LIST_PATHS["buyer_persona"]` cleaned (offer preserved) |
| Copilot template | `backend/src/modules/copilot/infrastructure/prompts/templates/interview/buyer_persona_doc_extraction.j2` | rule-4 lines 26-27 dropped, slot order preserved |
| Copilot registry | `backend/src/modules/copilot/domain/extraction_domain_registry.py` | comment updated |
| Migration | `backend/alembic/versions/acdcfa45d526_drop_buyer_persona_fields.py` | upgrade + downgrade + idempotent |
| Tests (new) | `backend/tests/modules/brand/test_buyer_persona_fields_dropped_regression.py` | 21 cases |
| Tests (updated) | `tests/modules/brand/test_buyer_persona_entity.py`, `_model.py`, `_repository.py` | fixtures cleaned |
| Tests (updated) | `tests/modules/copilot/test_buyer_persona_extraction_template.py`, `test_editable_fields_integration.py`, `test_extract_validation.py` | fixtures cleaned |

#### Commits
- `80551ec5` — `refactor(brand): drop buyer_persona objections + preferred_channels`
- `00fa55b0` — `refactor(copilot): cleanup buyer_persona extraction surface`
- `d047c10b` — `feat(alembic): add migration drop_buyer_persona_fields`
- `9b278cc0` — `docs(pm): PR-1 BE implementation log` (this commit, post-amend)

---

<!-- @pm: BE implementation done. Próximo paso: cuando FE termine también, ejecutar prompts/03-auditor-start.md o ejecutar /pm "PR-1 BE builder done". -->
