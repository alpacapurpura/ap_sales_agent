# CONTRACT.md — Estilo Comunicacional (personality module)

**Scope:** single source of truth for BE/FE types and endpoints for the new "Estilo Comunicacional" section. Signed by both backend and frontend implementation.

---

## Existing state (do NOT recreate)

Already implemented and correct:

- Domain entity `PersonalityProfile` — `backend/src/modules/brand/domain/personality.py`
- DB model + migration — `personality_profiles` table (f86f848caefa)
- Repository — `backend/src/modules/brand/infrastructure/repositories/personality_repository.py`
- Service — `backend/src/modules/brand/application/services/personality_service.py` (sync methods: `select_preset`, `get_active`, `update_dimensions`; async: `delete_with_anchors`)
- API — `backend/src/modules/brand/api/personality.py` (7 endpoints; `/clone` is 501 stub)
- LangGraph `personality_app` — `backend/src/modules/brand/application/agents/style_analyzer/graph.py` (6 nodes: parser → janitor → psychologist → architect → embedder → simulator)
- Qdrant store — `backend/src/modules/brand/infrastructure/qdrant/style_anchor_store.py`
- FE types — `frontend/src/features/brand-studio/types/personality.ts`
- FE API client — `frontend/src/features/brand-studio/api/personality.ts`
- FE components — `DimensionSlidersAction.tsx`, `PresetCatalogAction.tsx`
- Downstream wiring — `sales_agent/application/services/knowledge_builder.py:132` reads `personality_profile.system_instruction` via `BrandDataPort.get_brand_knowledge` with fallback to legacy `voice_tone` string. No new port required.

---

## 1. Backend changes — summary

### 1.1 Endpoints (3 new + 2 bug fixes)

| Method | Path | Status | Notes |
|---|---|---|---|
| **POST** | `/api/v1/brand/personality/clone` | Replace 501 stub with full impl | Invoke `personality_app.ainvoke(state)`, persist with `is_active=false`, upsert Qdrant anchors, return DTO |
| **POST** | `/api/v1/brand/personality/{profile_id}/activate` | **NEW** | Deactivates current active profile, activates target. Idempotent. 404 if not found. |
| **POST** | `/api/v1/brand/personality/from-voice-tone` | **NEW** | Reads `BrandIdentity.voice_tone` legacy text, maps to nearest preset via LLM, creates profile with `profile_type="migrated_from_voice_tone"`, activates. 409 if migration already done. 404 if no legacy text. |
| PUT | `/api/v1/brand/personality/{profile_id}/dimensions` | **Keep PUT** (no change to BE) | FE will be fixed to match |
| PUT | Response model of all endpoints | **Audit** | Confirm PII compliance: every endpoint has `response_model=` or explicit return type. No raw dicts. |

### 1.2 New DTOs

```python
# backend/src/modules/brand/api/personality.py

class CloneRequest(BaseModel):
    """Body for POST /clone — either text_input OR file, not both."""
    model_config = ConfigDict(extra="forbid")
    text_input: str | None = None  # min 10 messages (validated server-side)
    user_name: str | None = None   # label for the resulting profile

# (file upload is separate multipart field — stays as UploadFile | None)

class ActivateRequest(BaseModel):
    """Body for POST /{id}/activate — empty body, path param only."""
    model_config = ConfigDict(extra="forbid")

class FromVoiceToneResponse(BaseModel):
    """Response for POST /from-voice-tone.

    On success: the newly created migrated profile.
    """
    model_config = ConfigDict(extra="forbid")
    profile: "PersonalityProfileDTO"
    source_voice_tone: str  # the original text that was migrated, for audit
    matched_preset_key: str | None  # nearest preset matched (may be null)
    match_confidence: float  # 0.0..1.0

class CloneProgressDTO(BaseModel):
    """Reserved for future SSE streaming. Keep out of V1."""
    # OMITTED — V1 uses synchronous await; polling not required for typical <4min jobs
```

### 1.3 Service methods (new)

```python
# backend/src/modules/brand/application/services/personality_service.py

async def clone_from_material(
    self,
    *,
    tenant_id: UUID,
    text_input: str | None,
    file_bytes: bytes | None,
    file_name: str | None,
    user_name: str | None,
) -> PersonalityProfileModel:
    """Run the personality_app LangGraph, persist the resulting profile with
    is_active=False, upsert Qdrant anchors. Does NOT activate — caller invokes
    activate() once user approves the preview.

    Raises:
      ValueError — insufficient material (<10 messages) or both inputs empty.
      RuntimeError — graph pipeline failed irrecoverably.
    """

def activate(
    self,
    *,
    profile_id: UUID,
    tenant_id: UUID,
) -> PersonalityProfileModel | None:
    """Activate a pre-existing profile (cloned/custom/migrated). Idempotent:
    if already active, returns the model unchanged. Deactivates any currently
    active global profile for the tenant in the same transaction. Returns None
    if profile not found or belongs to a different tenant.
    """

async def migrate_from_voice_tone(
    self,
    *,
    tenant_id: UUID,
    voice_tone_text: str,
) -> tuple[PersonalityProfileModel, str | None, float]:
    """Map a legacy BrandIdentity.voice_tone free-text to a PersonalityProfile
    by selecting the nearest preset via LLM similarity. Creates profile with
    profile_type="migrated_from_voice_tone", source_metadata={"legacy_text": ...},
    and auto-activates. Returns (profile, matched_preset_key, confidence).

    Raises:
      ValueError — voice_tone_text empty.
      RuntimeError — LLM call failed.
    """
```

### 1.4 Extra helpers

```python
# backend/src/modules/brand/domain/personality.py

def find_nearest_preset(
    text: str,
    llm_caller: Callable[[str], str] | None = None,
) -> tuple[str | None, float]:
    """Pure function: ranks the 6 PERSONALITY_PRESETS by similarity to `text`
    via LLM scoring prompt. Returns (preset_key, confidence in [0.0, 1.0]).
    Returns (None, 0.0) if LLM unavailable or text is empty.
    """
```

### 1.5 Tests (TDD mandatory)

| Layer | File | Must cover |
|---|---|---|
| Domain | `backend/tests/modules/brand/test_personality_domain.py` (extend) | `find_nearest_preset` determinism + preset bucketing |
| Service | `backend/tests/modules/brand/test_personality_service.py` (extend) | `clone_from_material` (success + insufficient material), `activate` (first-time + idempotent + wrong tenant), `migrate_from_voice_tone` (success + empty input) |
| Repository | `test_personality_repository.py` (extend) | — (no repo changes; `activate` already present) |
| API | `backend/tests/modules/brand/test_personality_api.py` (new or extend) | All 10 endpoints: 200/400/404/409 paths + tenant isolation + response_model shape |
| Arch | `backend/tests/architecture/test_ddd_boundaries.py` | No new cross-module imports |
| Arch | `backend/tests/architecture/test_api_contracts.py` | New endpoints declare `response_model=` (via return type annotation) |

---

## 2. Frontend changes — summary

### 2.1 New section registration

- `frontend/src/features/brand-studio/lib/section-catalog.ts` — insert `{ slug: "estilo", label: "Estilo Comunicacional", icon: MessageCircle, kind: "singleton" }` at **position 3** (between `identity` and `positioning`).
- `frontend/src/features/brand-studio/pages/section-page-map.ts` — register `estilo: CommunicationStylePage`.
- `frontend/src/features/brand-studio/pages/section-pages.tsx` — export `CommunicationStylePage` (NOT via `createPage` factory because data persists to `personality_profiles` table, not to `BrandIdentity` JSONB).
- Update docstring comment in `section-page-map.ts:26-30` — replace line `*   - voice        → subset of identity (voice_tone); renders under identity page.` with mention of new top-level `estilo` section.

### 2.2 New API client methods (extend `api/personality.ts`)

**Bug fix:** `useUpdateDimensions` uses `PATCH /dimensions` → must be `PUT /{profile_id}/dimensions` with body `{ dimensions: {...} }`. The hook signature changes to accept `{ profileId, dimensions }`.

**New hooks:**

```typescript
export function useClonePersonality(): UseMutationResult<
  PersonalityProfile,
  Error,
  { textInput?: string; file?: File; userName?: string }
>;

export function useActivateProfile(): UseMutationResult<PersonalityProfile, Error, string /* profileId */>;

export function useMigrateFromVoiceTone(): UseMutationResult<
  { profile: PersonalityProfile; matched_preset_key: string | null; match_confidence: number },
  Error,
  void  // body is empty; server reads BrandIdentity.voice_tone
>;
```

Query key additions: `PERSONALITY_KEYS.all = ["personality"] as const` (invalidate on any mutation).

### 2.3 New page + components

**Layout convention (match Brand Studio Finder layout):**
- Page: `frontend/src/features/brand-studio/pages/section-pages.tsx` exports `CommunicationStylePage` (thin Server Component that hydrates an internal Client component).
- Internal components: `frontend/src/features/brand-studio/components/communication-style/` (new folder, kebab-case inside).

| Component | Role |
|---|---|
| `CommunicationStyleView.tsx` | Main Client orchestrator. Reads `useActivePersonality` + optional `useBrandIdentity` for legacy voice_tone. Renders Empty / Active / migration card. |
| `empty-state.tsx` | Two CTA cards (preset / clone). |
| `migration-card.tsx` | Shown when active is null AND `brand_identity.voice_tone` is set. "Convertir" → `useMigrateFromVoiceTone`. "Empezar de cero" → dismiss via localStorage flag. |
| `active-state.tsx` | Active profile: header + dimensions + linguistic fingerprint + sample exchanges + actions. |
| `dimensions-panel.tsx` | Read-only by default; Edit mode uses the logic of `DimensionSlidersAction` (extract into reusable component `lib/personality/dimensions-form.tsx` — see §2.4). |
| `fingerprint-panel.tsx` | Read-only display of `LinguisticPatterns`. |
| `sample-exchanges-panel.tsx` | 3 exchange cards + Regenerar button using `useSimulatePersonality`. |
| `preset-picker-view.tsx` | Full page view accessed via `?view=preset` query. Uses `usePersonalityPresets` + `useSelectPreset`. |
| `clone-wizard-view.tsx` | Full page view accessed via `?view=clone`. 3 steps via internal state reducer: `material → analyzing → preview`. Integrates `useClonePersonality`. |
| `simulate-drawer.tsx` | Chat-style simulator triggered from ActiveState. Uses `useSimulatePersonality`. |
| `communication-style-nav.tsx` | Small back-to-Estilo link shown in preset-picker and clone-wizard views. |

### 2.4 Refactor (consistency)

`DimensionSlidersAction` and `PresetCatalogAction` are kept for backward compat with form-runtime but the core logic is extracted to:

- `frontend/src/features/brand-studio/components/communication-style/dimensions-form.tsx` — exports `<DimensionsForm />` consumed by both `DimensionSlidersAction` and the new `dimensions-panel.tsx`. Zero behavior change.
- `frontend/src/features/brand-studio/components/communication-style/preset-grid.tsx` — exports `<PresetGrid />` consumed by both `PresetCatalogAction` and the new `preset-picker-view.tsx`.

This keeps the action registry intact (for any in-flight callers) while the new page uses the extracted components directly.

### 2.5 Action registry cleanup

Remove from `BRAND_STUDIO_ACTION_KEYS` and `REGISTRY_ENTRIES`:

- `voice-clone` (placeholder Sprint-2 stub, no real consumer after identity schema cleanup)

Keep:

- `personality-clone` — placeholder, still referenced by no schema but safer to keep for graceful registry tests
- `personality-dimensions`, `personality-presets` — kept since their underlying components are kept

Delete:

- `frontend/src/features/brand-studio/actions/placeholders.tsx:VoiceClonePlaceholder` — dead code.

### 2.6 Schema cleanup

- `frontend/src/features/brand-studio/schemas/identity.schema.ts` — remove lines 42–70 (both `voice_tone` and `voice_tone_clone` fields). Arch test count decreases.
- `frontend/src/features/brand-studio/schemas/voice.schema.ts` — **delete the file** (orphan).
- `frontend/src/features/brand-studio/schemas/index.ts` — remove any `voiceSchema` export if present.
- `frontend/src/features/brand-studio/schemas/__tests__/schemas.test.ts` — update registry count expectation.
- `frontend/src/__tests__/architecture/test-field-help-coverage.test.ts` — update to remove voice_tone/voice_tone_clone fields expected-in-help-coverage.

### 2.7 Legacy query-param redirect (nice-to-have, optional)

`frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/[section]/page.tsx`:

```ts
// If the user lands on /identity?field=voice_tone or ?field=voice_tone_clone
// redirect to /estilo so legacy emails/bookmarks don't dead-end.
if (params.section === "identity" && (searchParams?.field === "voice_tone" || searchParams?.field === "voice_tone_clone")) {
  redirect(`/${params.tenantId}/brand-studio/estilo`);
}
```

### 2.8 Tests

- `frontend/src/features/brand-studio/api/__tests__/personality.test.ts` — extend: 3 new hooks + PUT fix.
- `frontend/src/features/brand-studio/components/communication-style/__tests__/` — new tests for `CommunicationStyleView` states (empty / migration / active) and wizard transitions (material → analyzing → preview).
- `frontend/src/__tests__/architecture/test-feature-structure.test.ts` — new folder `communication-style/` auto-detected; ensure kebab-case.
- `frontend/src/__tests__/architecture/test-no-duplicate-names.test.ts` — new component names don't collide with existing.

---

## 3. Spanish neutro (non-negotiable)

All user-facing strings (labels, hints, placeholders, toasts, error messages) use tuteo (`tú`/`te`/`tienes`/`puedes`). No voseo (`vos`/`tenés`/`podés`/`mirá`). Emit stroke-guide for agents:

- "Empezar" / "empieza" (not "empezá")
- "Clonar" / "clona" / "cloná" → **"clona"**
- "Pegar" / "pega" (not "pegá")
- "Elegir" / "elige" (not "elegí")
- "Tienes" (not "tenés")
- "Puedes" (not "podés")

---

## 4. Migration policy for `BrandIdentity.voice_tone`

- **Column stays.** Nullable in DB, stop writing from UI (the fields are removed from `identity.schema.ts`).
- **Not read anymore** from new consumers — `knowledge_builder` already prefers `personality_profile.system_instruction` with voice_tone as fallback (line 132). Once a tenant has any active personality, voice_tone is never read.
- **One-time migration card** in the new section offers to convert legacy text to a personality via LLM. User-initiated, opt-in. See §2.3.
- **Drop column is a future sprint** — not part of this change.

---

## 5. Error handling

All errors returned to FE:

| Code | Scenario | Message (Spanish) |
|---|---|---|
| 400 | Clone: fewer than 10 messages | "Necesitas pegar al menos 10 mensajes para clonar tu estilo." |
| 400 | Clone: both text and file provided | "Envía texto O archivo, no ambos." |
| 400 | Clone: file format unsupported | "El formato del archivo no es válido. Acepta .txt o export de chat." |
| 404 | Activate: profile not found | "Perfil no encontrado o no pertenece a este tenant." |
| 404 | From-voice-tone: no legacy text | "No hay tono de voz legado que migrar." |
| 409 | From-voice-tone: already migrated | "Este tenant ya tiene un perfil migrado activo." |
| 500 | Clone pipeline failure | "No pudimos analizar tu material. Intenta nuevamente en unos minutos." |

Backend returns `{"detail": "..."}` following FastAPI convention. Frontend toasts relay detail verbatim when it's user-friendly.

---

## 5bis. Tech debt cleanup (mandatory in this session)

Discovered while auditing; user requested resolution in the same session.

### 5bis.1 Frontend (dead code + wrong wiring)

| # | Item | Action | Why |
|---|---|---|---|
| 1 | `useUpdateDimensions` uses `PATCH /dimensions` (no profile id), BE has `PUT /{profile_id}/dimensions` | Fix hook signature + HTTP verb | Broken as shipped — would 404 in prod |
| 2 | `frontend/src/features/brand-studio/schemas/personality.schema.ts` references action keys (`personality-presets`, `personality-dimensions`, `personality-clone`) but is NOT registered in `BRAND_SECTIONS` nor `SECTION_PAGE_MAP` | **Delete file** — its purpose is fully replaced by `CommunicationStylePage` | Orphan schema |
| 3 | `frontend/src/features/brand-studio/schemas/voice.schema.ts` — duplicates `voice_tone` + `voice_clone` action already in identity | **Delete file** | Redundant orphan |
| 4 | `frontend/src/features/brand-studio/actions/placeholders.tsx` — `VoiceClonePlaceholder`, `PersonalityClonePlaceholder` (Sprint-2 stubs) | **Delete both symbols** (keep the other placeholders in the file) | Dead stubs after section extraction |
| 5 | `frontend/src/features/brand-studio/actions/DimensionSlidersAction.tsx` (+ `.stories.tsx` + `__tests__/DimensionSlidersAction.test.tsx`) | **Replace with** `components/communication-style/dimensions-form.tsx` (extracted logic) + delete the action wrapper + stories + tests | Wrapper was only a form-runtime adapter. Direct component is cleaner |
| 6 | `frontend/src/features/brand-studio/actions/PresetCatalogAction.tsx` (+ `.stories.tsx` + `__tests__/PresetCatalogAction.test.tsx`) | Same: **replace with** `components/communication-style/preset-grid.tsx` + delete wrapper + stories + tests | Same rationale |
| 7 | Action registry keys: `voice-clone`, `personality-clone`, `personality-dimensions`, `personality-presets` | **Remove** from `BRAND_STUDIO_ACTION_KEYS` + `REGISTRY_ENTRIES` | After 5–6 no schema references these |
| 8 | `frontend/src/features/brand-studio/schemas/index.ts` — imports + exports `voiceSchema`, `personalitySchema`, `SCHEMA_REGISTRY["brand.voice"]`, `SCHEMA_REGISTRY["brand.personality"]` | Remove 4 entries | Orphan after file deletions |
| 9 | `frontend/src/__tests__/architecture/test-field-help-coverage.test.ts:22` — imports `voiceSchema` | Remove + ratchet down expected-count | Syncs with §8 |
| 10 | `frontend/src/features/brand-studio/schemas/__tests__/schemas.test.ts` — expects registry count `17` (includes voice + personality schemas) | Adjust to new count | Syncs with §8 |
| 11 | `identity.schema.ts:42-70` — `voice_tone` (textarea with `action: "voice-clone"` — bad mix) + `voice_tone_clone` (redundant custom custom duplicating path) | Remove both (replaces with migration card in new section) | Anti-pattern: textarea + action on same field |
| 12 | `frontend/src/features/brand-studio/api/personality.ts` — JSDoc stubs are empty (`/** *\n *\n */`) | Fill with proper docstrings (what it does + returns) | Codebase convention violation |
| 13 | Obsolete comments: `section-page-map.ts:26-30` + `section-pages.tsx:33-38` mention `voice → subset of identity` and `personality → own API via usePersonalityHooks (Sprint 2 deferred)` | Update to reflect new `estilo` section as top-level | Stale documentation |
| 14 | `frontend/src/features/brand-studio/actions/stories/PersonalityClonePlaceholder.stories.tsx` (if exists) | Delete | Stub stories |

### 5bis.2 Backend

| # | Item | Action | Why |
|---|---|---|---|
| 15 | `backend/src/modules/copilot/application/tools/offer_section_tools.py:173-190` reads legacy `identity.voice_tone` free-text to compose suggestions | Migrate to read `personality_profile.system_instruction` (when available) via `BrandDataPort`; keep `voice_tone` as fallback only if no active profile | Copilot tool still consumes deprecated path |
| 16 | `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2:19-23` | Already correct: prefers personality, falls back to `voice_tone`. **Verify** no additional cleanup needed | Verify |
| 17 | Audit all `/personality/*` endpoints for `response_model=` compliance (PII rule) | Convert existing endpoints that use return-type annotation only to explicit `response_model=PersonalityProfileDTO` decorator form IF the arch test requires it | Tessl/Maria rule + arch test `test_all_endpoints_have_response_model` |
| 18 | Check if `personality_profiles.anchor_count` stays in sync when clone is deleted — currently `delete_with_anchors` removes Qdrant but doesn't reset `anchor_count` on the soft-deleted row (low prio, for audit cleanliness) | Verify + fix if drift found | Data hygiene |

### 5bis.3 Tests (repurpose/migrate, don't delete)

Existing tests that SHOULD be kept but must be adapted:

- `frontend/src/features/brand-studio/actions/__tests__/DimensionSlidersAction.test.tsx` → migrate the behaviour tests to `components/communication-style/__tests__/dimensions-form.test.tsx`.
- `frontend/src/features/brand-studio/actions/__tests__/PresetCatalogAction.test.tsx` → migrate to `components/communication-style/__tests__/preset-grid.test.tsx`.
- `frontend/src/lib/form-runtime/inputs/__tests__/inputs.test.tsx:129-142`, `parser.test.ts:48`, `registry.test.ts:13` — they use the **string literal** `"voice-clone"` as an arbitrary action key for registry/parser tests. **Keep as-is** — these are test-local fixtures that happen to share the old name; they don't depend on the production registry. Optional cosmetic: rename fixture to `"_test-action"` to avoid future confusion.

### 5bis.4 Not addressed (out of scope justification)

- **Avatar `voice_tone_config: dict`** (per-avatar overrides, JSONB, persisted in `avatars` table) — distinct concept from `BrandIdentity.voice_tone`. Avatar overrides may still be useful in the future. Keep intact.
- **`copilot/infrastructure/prompts/templates/brand_extract_identity.j2:40`** — LLM prompt that asks for `voice_tone` in web-scraping extraction. Still needed as the seed for the migration card. Keep intact.
- **Dropping `BrandIdentity.voice_tone` column** — future sprint after observing no reads for 30 days.

---

## 6. Out of scope (deferred)

- SSE streaming of clone progress — V1 is synchronous.
- Simulate with LLM-driven response (today returns stored `sample_exchanges`) — V1 unchanged.
- Saved-drafts / history UI — V1 has single active profile.
- Drop `BrandIdentity.voice_tone` column.
- Per-offer / per-avatar personality overrides (schema supports `offer_id`, `avatar_id` but UI is global-only in V1).

---

## 7. Commit plan

| # | Scope | Files |
|---|---|---|
| 1 | `feat(brand): implement personality clone + activate + migrate endpoints` | Backend API + service + tests + helper in domain/personality.py |
| 2 | `feat(brand-studio): add Estilo Comunicacional section + migrate from identity` | Frontend section catalog + page + components + API hook fixes + schema cleanup + tests |
| 3 | `docs(domains): document communication-style catalog + migration policy` | `docs/domains/brand/communication-style.md` + INDEX updates |

Do NOT commit until user approves.
