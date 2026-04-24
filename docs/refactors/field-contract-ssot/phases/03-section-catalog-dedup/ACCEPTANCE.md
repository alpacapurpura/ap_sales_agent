# Fase 03 — ACCEPTANCE

Criterios no-negociables. Todos deben quedar verde antes de cerrar la fase.

## A · BE offer — extender `SectionMetadata`

- [ ] `SectionMetadata` en `section_catalog.py` suma campo
  `kind: Literal["singleton", "collection"]`.
- [ ] Las 21 entries de `SECTION_CATALOG` declaran su `kind` (singleton
  vs collection). `testimonials`, `portfolio`, `faq`, `gallery`,
  `instructors` = collection; el resto singleton.
- [ ] DTO `SectionMetadataDTO` en `api/archetypes.py` emite `kind`.
- [ ] `_CATALOG_VERSION` bumped → evict client cache.
- [ ] Arch test `test_section_catalog_completeness.py` pasa con la nueva
  invariante (toda entry trae `kind` no-nulo).

## B · FE offer — hook + consumers

- [ ] Nuevo hook `useOfferSectionCatalog()` en
  `features/offer-studio/hooks/` (React Query; consume
  `/api/v1/offer/archetypes/catalog` existente).
- [ ] El hook expone: `sections` (21 entries), `getSection(slug)`,
  `getSectionLabel(slug)`, `getSectionIcon(slug)`, `isCollection(slug)`.
- [ ] `icon_name` string → componente via `resolveIconByName(iconName)`
  (ya existe).
- [ ] Consumers migrados:
  - `OfferStudioNavRail.tsx` → consume hook
  - `OfferStudioBreadcrumb.tsx` → consume hook
  - `copilot/components/cards/ExtractionSummaryCard.tsx` → rama offer
    consume hook
- [ ] `OFFER_SECTIONS` hardcoded array eliminado.
- [ ] `getOfferSection`, `getOfferSectionLabel`, `getOfferSectionIcon`,
  `isCollectionSection` helpers eliminados (o reexportados desde el hook).
- [ ] TSC clean.

## C · BE brand — section catalog nuevo

- [ ] `backend/src/modules/brand/domain/section_catalog.py` nuevo con
  `BrandSectionKey` (StrEnum), `BrandSectionMetadata` dataclass frozen,
  `BRAND_SECTION_CATALOG` dict con las 14 entries actuales.
- [ ] Campos de metadata: `key`, `label_es`, `subtitle_es`, `icon_name`,
  `kind` (singleton/collection).
- [ ] Endpoint versionado `GET /api/v1/brand/sections/catalog` retorna
  `{ version, sections: [...] }`.
- [ ] Arch test `test_brand_section_catalog_completeness` (mirror del
  offer): toda `BrandSectionKey` con entry, icons string válidos, kind
  no-nulo.

## D · FE brand — hook + consumers

- [ ] `useBrandSectionCatalog()` hook consume `/api/v1/brand/sections/catalog`.
- [ ] Consumers migrados:
  - `BrandStudioNavRail.tsx`
  - `BrandStudioBreadcrumb.tsx`
  - `ExtractionSummaryCard.tsx` (rama brand)
- [ ] `BRAND_SECTIONS` hardcoded array eliminado.
- [ ] `getBrandSection`, `getBrandSectionLabel` helpers eliminados.
- [ ] TSC clean.

## E · Arch test anti-drift

- [ ] Nuevo FE arch test `test-no-hardcoded-section-list.test.ts` que
  rechaza aparición de los símbolos `OFFER_SECTIONS` / `BRAND_SECTIONS`
  como `export const ... = [...]` fuera del hook que los consuma.
- [ ] Test pasa con allowlist vacía (no se permiten excepciones).

## F · Close

- [ ] `LEARNINGS.md` append sección Fase 03 (expectations /
  descubrimientos / decisiones / tech debt).
- [ ] `STATE.md` → `active_phase=04`, `last_green_commit` bumped.
- [ ] `STATUS.md` Fase 03 → `status: done` + `closed_at`.
- [ ] `phases/04-drop-offer-fields-by-fe-section/STATUS.md` abierto
  (`status: ready-to-start`).

## Cross-block (global)

- [ ] BE arch 425+ verdes (cero regresiones, +1 arch test nuevo para brand).
- [ ] FE arch 37+ verdes (+1 nuevo anti-drift section list).
- [ ] TSC noEmit clean.
- [ ] `KNOWN_UNRESOLVED_PATHS.size === 21` (Fase 02 cerrado, Fase 03 no
  toca la allowlist — sigue apuntando a cross-module federated).
- [ ] No nuevos imports cross-module (arch test
  `test_no_new_cross_module_imports` green).
- [ ] No hardcoded section list en offer-studio ni brand-studio
  (el arch test nuevo enforza).
- [ ] Sin Spanish voseo nuevo.
