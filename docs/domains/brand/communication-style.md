# Communication Style — Estilo Comunicacional

**Status:** active (2026-04-21).
**Module:** `brand`.
**Frontend slug:** `estilo` — `/brand-studio/estilo`.
**Owner:** brand team.

---

## Summary

"Estilo Comunicacional" is a top-level Brand Studio section that owns **how a brand talks** across every LLM-driven touchpoint: SDR (sales agent), landing copy generators, asset captions. It replaces the legacy `BrandIdentity.voice_tone` free-text field (textarea + unimplemented custom action) with a structured three-pillar `PersonalityProfile`.

The three pillars:

1. **Dimensions** — six continuous axes (`energy`, `warmth`, `humor`, `expressiveness`, `narrative`, `verbosity`), each `float ∈ [0.0, 1.0]`. Bucketed into 5 discrete levels for prompt generation.
2. **Linguistic patterns** — surface fingerprint: greeting, farewell, emoji style, filler phrases, unique vocabulary.
3. **Sample exchanges** — few-shot examples covering standard SDR contexts (greeting, price question, objection, interest, follow-up, closing).

All three compile into a 5-block `system_instruction` via `PersonalityCompiler` (blocks: personality rules → linguistic fingerprint → negative constraints → conversation examples → identity anchor).

---

## Catalog: 6 built-in presets

Source of truth: `backend/src/modules/brand/domain/personality.py::PERSONALITY_PRESETS`.

| Key | Name | Icon | Positioning |
|---|---|---|---|
| `warm_close` | Cálida y Cercana | ☀️ | Mentoras, coaches de bienestar, infoproductos femeninos |
| `electric` | Eléctrica y Expresiva | ⚡ | Fitness, emprendimiento, ventas de alto voltaje |
| `serene` | Serena y Articulada | 🧠 | Consultoría, servicios premium, audiencias sofisticadas |
| `direct` | Directa y Sin Filtro | 🔥 | B2B, audiencias masculinas, high ticket |
| `narrative` | Narrativa y Vívida | 📖 | Coaches, mentores, storytellers, marca personal |
| `minimalist` | Minimalista y Premium | 🖤 | Lujo, high-ticket, acceso restringido |

Each preset ships with fully populated dimensions, linguistic patterns, and 6–7 sample exchanges in Spanish neutro LatAm.

---

## API contract

Base: `/api/v1/brand/personality`.

| Method | Path | Role |
|---|---|---|
| GET | `/presets` | List 6 presets (summary shape: key, name, icon, description, sample_message, dimensions) |
| GET | `/active` | Current global active profile for the tenant (nullable) |
| POST | `/select-preset` | Body `{ preset_key }` — creates + activates from a preset |
| POST | `/clone` | Multipart: `text_input` (Form) **or** `file` (UploadFile) + optional `user_name`. Runs the LangGraph `personality_app` (parser → janitor → psychologist → architect → embedder → simulator). Returns the profile with `is_active=false` |
| POST | `/{profile_id}/activate` | Idempotent activation — deactivates any other active global profile in the same transaction |
| POST | `/from-voice-tone` | Body-less. Reads `BrandIdentity.voice_tone` legacy string, maps to nearest preset via LLM, creates + activates a profile with `profile_type="migrated_from_voice_tone"`. 404 if no legacy text, 409 if already migrated |
| PUT | `/{profile_id}/dimensions` | Body `{ dimensions: {...} }` — patches sliders and recompiles `system_instruction` |
| POST | `/{profile_id}/simulate` | Returns 3 canned sample exchanges (LLM-driven simulation is a future iteration) |
| DELETE | `/{profile_id}` | Soft-delete + Qdrant anchor cleanup |

All endpoints filter by `tenant_id` via `get_current_user` dependency. All return typed Pydantic DTOs (PII compliance).

---

## Downstream consumers

The active `PersonalityProfile.system_instruction` takes priority over the legacy `BrandIdentity.voice_tone` in every prompt-composition path:

| Consumer | File | Selection |
|---|---|---|
| SDR (sales agent) | `backend/src/modules/sales_agent/application/services/knowledge_builder.py:132` | `personality_profile.system_instruction` → fallback `identity.voice_tone` |
| SDR prompt template | `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2:19-23` | `{% if personality_instruction %} … {% elif identity.voice_tone %} …` |
| Offer section copilot tool | `backend/src/modules/copilot/application/tools/offer_section_tools.py:170-200` | Reads `BrandKnowledgeDTO.personality_profile.system_instruction` when present; falls back to `identity.voice_tone` when the tenant has no profile |

Consumers read through `shared/links/ports/brand.BrandDataPort.get_brand_knowledge(tenant_id)` which returns a `BrandKnowledgeDTO` that already includes `personality_profile`. **No new port was needed** for this feature.

---

## Migration policy for legacy `BrandIdentity.voice_tone`

- **Column stays.** Nullable in DB. Stop writing from UI (the fields were removed from `identity.schema.ts`).
- **Not read by new consumers.** Once a tenant has an active personality profile, `voice_tone` is never consulted.
- **One-time migration card** in `/brand-studio/estilo`: when active profile is null *and* legacy text exists, the user is offered "Convertir en estilo inicial" (→ `POST /from-voice-tone`) or "Empezar de cero" (dismisses via local flag).
- **Dropping the column** is deferred to a future sprint after observing no reads for 30 days.

---

## Frontend architecture

Top-level section registered in `frontend/src/features/brand-studio/lib/section-catalog.ts` at position 3 (between `identity` and `positioning`) with slug `estilo` and icon `MessageCircle`.

The page is **not** generated by `createPage<BrandIdentity>` factory — data lives in `personality_profiles` table, not in `BrandIdentity` JSONB. Implementation:

```
frontend/src/features/brand-studio/
├── pages/
│   ├── section-pages.tsx            (exports CommunicationStylePage)
│   └── section-page-map.ts          (registers estilo → CommunicationStylePage)
├── components/communication-style/
│   ├── CommunicationStyleView.tsx   (Client orchestrator; picks Empty/Active/PresetPicker/CloneWizard)
│   ├── EmptyState.tsx
│   ├── MigrationCard.tsx
│   ├── ActiveState.tsx
│   ├── DimensionsPanel.tsx          (consumes DimensionsForm)
│   ├── DimensionsForm.tsx           (the 6 sliders — save is explicit)
│   ├── FingerprintPanel.tsx
│   ├── SampleExchangesPanel.tsx
│   ├── PresetPickerView.tsx         (consumes PresetGrid)
│   ├── PresetGrid.tsx               (the 6 preset cards)
│   ├── CloneWizardView.tsx          (3-step state machine: material → analyzing → preview)
│   ├── SimulateDrawer.tsx
│   └── CommunicationStyleNav.tsx    (back-to-Estilo link)
├── api/personality.ts               (9 React Query hooks)
└── types/personality.ts             (TS mirror of domain DTOs)
```

All components follow the Brand Studio Finder layout: flat, `px-10 pt-7 pb-10`, `text-[13px]` base, `border-border/50` separators, `bg-muted/60` for active rows. Spanish neutro LatAm (tuteo: tú/tienes/puedes; no voseo).

---

## Debt removed in this cycle

- Deleted orphan `voice.schema.ts`.
- Cleaned `personality.schema.ts` (3 dead custom-action fields removed; archetype + core_values + personality_traits retained).
- Removed dead action keys from `actions/registry.ts`: `voice-clone`, `personality-clone`, `personality-dimensions`, `personality-presets`.
- Deleted action wrappers `DimensionSlidersAction.tsx` and `PresetCatalogAction.tsx` (logic extracted to `DimensionsForm.tsx` and `PresetGrid.tsx`).
- Deleted Sprint-2 stubs `VoiceClonePlaceholder` and `PersonalityClonePlaceholder`.
- Removed `voice_tone` and `voice_tone_clone` fields from `identity.schema.ts`.
- Fixed `useUpdateDimensions` hook: was `PATCH /dimensions` (broken, would 404 in prod), now `PUT /{profile_id}/dimensions` with body `{ dimensions: {...} }`.
- Filled empty JSDoc stubs in `api/personality.ts`.
- Added legacy-field query-param redirect in the `[section]/page.tsx` dispatcher.
- Migrated copilot tool `offer_section_tools.adapt_from_brand_identity` to read personality first, voice_tone as fallback.
- Fixed formatting issues in 5 pre-existing schema files (buyer-persona, methodology, narrative, positioning, testimonial-item) — autoformatted by prettier since they were touched during arch-test audit.

---

## Non-goals (deferred)

- SSE streaming of clone progress (V1 is synchronous; a 2–4 min job is acceptable for the modal).
- LLM-driven `/simulate` (returns canned exchanges for now).
- Per-offer / per-avatar personality overrides (domain supports `offer_id`, `avatar_id`; UI is global-only in V1).
- Dropping `BrandIdentity.voice_tone` column.

---

## Related rules

- `.claude/rules/backend-ddd.md` — module boundaries.
- `.claude/rules/tenant-isolation.md` — every query filtered.
- `.claude/rules/spanish-text.md` — Spanish neutro LatAm enforcement.
