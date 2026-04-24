# Fase 02 — ACCEPTANCE

Criterios no-negociables. Todos deben quedar verde antes de cerrar la fase.

## Bloque A — Authority

- [ ] `products.authority_positioning_for_sales` (TEXT NULL) existe (migration idempotente).
- [ ] `products.authority_notes` (TEXT NULL) existe.
- [ ] `Offer.authority_positioning_for_sales: str | None` y `authority_notes: str | None`.
- [ ] `ProductModel` mapea 1:1 ambas columnas.
- [ ] `OfferInstructorsUpdate` extendido con ambos campos.
- [ ] `FieldContract` tiene 2 entries sección `instructors`.
- [ ] `offer_field_paths.json` incluye 2 paths nuevos.
- [ ] `offer-field-paths.ts` codegen regenerado.
- [ ] Allowlist `KNOWN_UNRESOLVED_PATHS` -2 (cap baja 56 → 54).

## Bloque B — Value-stack anchor

- [ ] `products.total_perceived_value_anchor` (NUMERIC) y
  `stack_positioning_statement` (TEXT) existen.
- [ ] `Offer` suma ambos campos.
- [ ] `ProductModel` mapea 1:1.
- [ ] `OfferValueStackUpdate` extendido.
- [ ] `FieldContract` 2 entries `value_stack`.
- [ ] Regen paths + TS.
- [ ] Allowlist -2 (54 → 52).

## Bloque C — Program narratives

- [ ] `ProgramDetails.weekly_time_commitment_hours: int | None`.
- [ ] `ProgramDetails.prerequisites_text: str | None`.
- [ ] `FieldContract` 2 entries `program_details` con `archetype_filter=(PROGRAMA,)`.
- [ ] Regen paths incluye `specific_details.weekly_time_commitment_hours` y
  `specific_details.prerequisites_text`.
- [ ] Allowlist -2 (52 → 50).

## Bloque D — SubscriptionDetails

- [ ] Rename `billing_cycle` → `billing_frequency`.
- [ ] Rename `content_update_freq` → `content_update_frequency`.
- [ ] Alembic idempotent JSONB rewrite aplicable múltiples veces.
- [ ] `SubscriptionDetails` suma `auto_renewal_with_notice_days`,
  `cancellation_anticipation_days`, `grace_period_days_on_failed_payment`,
  `member_benefits`, `primary_communication_channel`.
- [ ] `FieldContract` 7 entries `subscription_details` con
  `archetype_filter=(MEMBRESIA,)`.
- [ ] Regen paths: todos los nuevos aparecen, los renombrados también.
- [ ] Allowlist -7 (50 → 43).
- [ ] Datos existentes con `billing_cycle`/`content_update_freq` se preservan
  via JSONB rewrite + PATCH/GET roundtrip verifica.

## Bloque E — ServiceDetails

- [ ] 3 nuevos campos (`response_time_hours`, `onboarding_flow`,
  `scope_excluded`).
- [ ] `FieldContract` 3 entries `service_details` con `archetype_filter=(SERVICIO,)`.
- [ ] Regen + allowlist -3 (43 → 40).

## Bloque F — ProductDetails

- [ ] 5 nuevos campos (`sample_preview_url`, `packaging_description`,
  `return_policy_days`, `shipping_carriers_accepted`,
  `shipping_estimate_by_region`).
- [ ] `FieldContract` 5 entries `product_details` con `archetype_filter=(PRODUCTO,)`.
- [ ] Regen + allowlist -5 (40 → 35).

## Bloque G — PlatformDetails composable

- [ ] `PlatformDetails` clase nueva en `offer/domain/details.py` con 14 campos
  tipados (bool, str, HttpUrl, list estructurado).
- [ ] `Offer.platform_details: PlatformDetails | None = None`.
- [ ] `ProductModel.platform_details` JSONB column (migration idempotente).
- [ ] `offer_repository` serializa/deserializa correctamente.
- [ ] `generate_offer_field_paths.py` extendido para emitir `platform_details.X`
  paths (14 nuevos).
- [ ] FE `platform-details.schema.ts` migra TODOS los 14 paths a
  `platform_details.X`.
- [ ] `FieldContract` 14 entries sección `platform_details`.
- [ ] Codegen TS + JSON regenerados.
- [ ] Allowlist -14 (35 → 21).
- [ ] `ADR-010` documentado en `DECISIONS.md`.

## Bloque H — Extraction (opcional)

- [ ] Si se agrega: prompts updates afectan `value_stack` y/o `details` waves,
  los wave-level schemas ya aceptan los campos vía update DTOs extendidos.
- [ ] `tests/modules/offer/test_extraction_*.py` pasa.
- [ ] Si se difiere: anotar en LEARNINGS tech debt Fase 05.

## Bloque I — Close

- [ ] Golden fixture `fixtures/offer_a96403b5_baseline.md` regenerada.
- [ ] `STATE.md` → `last_green_commit` al último commit, `active_phase=03`.
- [ ] `STATUS.md` Fase 02 → `status: done` + `closed_at`.
- [ ] `STATUS.md` Fase 03 abierto (`ready-to-start`).
- [ ] `LEARNINGS.md` bloque Fase 02 populado.
- [ ] `DECISIONS.md` ADR-010 agregado (PlatformDetails composable).

## Cross-block (global)

- [ ] BE arch 425+ verdes (cero regresiones).
- [ ] FE arch 37 verdes.
- [ ] TSC noEmit clean.
- [ ] Offer `a96403b5...` editor abre, guarda, recarga identico (baseline
  sin fields nuevos).
- [ ] Sales-agent prompt additive only (ningún campo vacío muta render).
- [ ] Ningún import cross-module nuevo (arch test `test_no_new_cross_module_imports`).
- [ ] `KNOWN_UNRESOLVED_PATHS.size === 21`.
- [ ] `ALLOWLIST_CAP` literal actualizado a `21` (o mantener shrink con
  assertion `lessThanOrEqual(21)`).
