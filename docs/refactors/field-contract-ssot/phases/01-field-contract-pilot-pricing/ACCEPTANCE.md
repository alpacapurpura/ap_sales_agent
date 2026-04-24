# Fase 01 — Acceptance

Fase cierra cuando TODOS los criterios pasan. Cada uno verificable con
comando concreto.

## Migration

- [ ] `backend/alembic/versions/062_offer_pricing_latam.py` existe.
- [ ] Revision chain: `down_revision = "061_offer_narrative_fields"`.
- [ ] Usa `op.execute("ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...")` para las 3 columnas.
- [ ] `downgrade()` es no-op explícito (additive-only, no data loss).
- [ ] `docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"` sube sin error.
- [ ] Correr migration dos veces seguidas no falla (idempotente).

## Domain + DTO + Model

- [ ] `Offer.tax_included: bool | None = None`.
- [ ] `Offer.installments_available: str | None = None`.
- [ ] `Offer.accepted_payment_providers: list[str] = []` (default factory).
- [ ] Mismos 3 en `OfferPricingUpdate` con `None` default.
- [ ] `ProductModel` tiene las 3 columnas mapeadas (tipos SA idénticos).
- [ ] Repository `to_model` / `from_model` copia los 3 fields.

## FieldContract

- [ ] `backend/src/modules/offer/domain/field_contract.py`: dataclass frozen con campos mínimos: `path`, `type`, `owner`, `section`, `required`, `archetype_filter`.
- [ ] `PRICING_FIELD_CONTRACTS: tuple[FieldContract, ...]` incluye los 3 nuevos + `pricing_options`, `currency`, `price_pay_in_full`.
- [ ] `GET /api/v1/offer/field-contract` retorna 200 con `{"version": 1, "contracts": [...]}`.
- [ ] Router mounteado en `main.py`.
- [ ] Smoke test pytest `tests/modules/offer/api/test_field_contract_endpoint.py` valida shape.

## Extraction

- [ ] `offer_extract_pricing.j2` existe bajo `modules/copilot/infrastructure/prompts/templates/`.
- [ ] Spanish neutro LATAM (sin voseo). Tuteo.
- [ ] `_extract_pricing` en `OfferExtractionService` + `PricingWaveOutput` en `extraction_schemas.py`.
- [ ] Orchestrator W2 incluye pricing concurrente con psychology/value_stack/closing.
- [ ] Prompt extrae solo `tax_included` + `installments_available` (no `accepted_payment_providers` — UI-only).

## Codegen + FE typing

- [ ] `scripts/generate_offer_field_paths.py` regenerado → 126 paths (123 + 3).
- [ ] Nuevo script `scripts/generate_offer_field_paths_ts.py` o flag que emite `frontend/src/features/offer-studio/api/__generated__/offer-field-paths.ts` con `type OfferFieldPath = "tax_included" | ...`.
- [ ] `pricing.schema.ts` importa `OfferFieldPath` y tipa field.path. `path: "inexistente"` genera TSC error.
- [ ] Baseline 37 arch tests FE → sigue passed.

## Allowlist shrink

- [ ] `KNOWN_UNRESOLVED_PATHS` ya NO contiene `tax_included`, `installments_available`, `accepted_payment_providers`.
- [ ] `KNOWN_UNRESOLVED_PATHS.size === 56`.
- [ ] `ALLOWLIST_CAP === 56`.
- [ ] Test `toBeLessThanOrEqual(59)` baja a `toBeLessThanOrEqual(56)`.

## Sales-agent additive

- [ ] `agent_identity.j2` tiene bloque condicional: `{% if offer.tax_included is not none %}` / `{% if offer.installments_available %}` / `{% if offer.accepted_payment_providers %}`.
- [ ] `knowledge_builder.py` expone los 3 fields en el dict `offer` entregado al template.
- [ ] Offer sin data seteada (a96403b5 baseline) NO agrega líneas al prompt → INVARIANT 7 (additive only).

## Golden fixture

- [ ] `offer_a96403b5_baseline.json` regenerado vía script en container.
- [ ] Nuevas keys: `tax_included=null`, `installments_available=null`, `accepted_payment_providers=[]`.
- [ ] Test `test_offer_state_round_trips_through_pydantic` verde — Pydantic valida payload.
- [ ] Nuevo test `test_pricing_latam_fields_roundtrip`: PATCH sets los 3 → GET retorna seteados (unit de domain o service).
- [ ] Rendered prompt sigue conteniendo `public_name` (INVARIANT 3).

## Arch tests + quality gates

- [ ] `cd backend && .venv/bin/pytest tests/architecture/ -x -q` — verde, 425+ passed.
- [ ] `cd backend && .venv/bin/ruff check src/ tests/ --no-cache` — 0 errors.
- [ ] `cd backend && .venv/bin/ruff format --check src/ tests/` — clean.
- [ ] `cd frontend && npx vitest run src/__tests__/architecture/` — verde.
- [ ] `cd frontend && npx tsc --noEmit` — 0 errors.
- [ ] `cd frontend && npx eslint src/` — 0 errors.
- [ ] `cd backend && .venv/bin/pytest tests/modules/offer/ -q` — unit suite verde (nuevos tests incluidos).

## STATE + Fase 02

- [ ] `STATE.md`: `active_phase: 02-migrate-sections`, `last_green_commit` = hash J, `sub_step: 0/?`.
- [ ] `LEARNINGS.md` Fase 01 agrega Descubrimientos + Decisiones nuevas (ADR-008, ADR-009).
- [ ] `phases/01-.../STATUS.md`: `status: done`, `closed_at: <date>`.
- [ ] `phases/02-.../STATUS.md` creado con `status: ready-to-start`.
- [ ] Prompt de continuación entregado al user para nueva sesión.

## Definition of Rollback

Si cualquier commit falla CI o rompe golden fixture:
1. `git revert <hash>` — commits atómicos revertibles.
2. Diagnose en PR comment / LEARNINGS.md.
3. Repite sub-step sin avanzar el siguiente.
