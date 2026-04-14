# Personality Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sales agent adopts a configurable, consistent personality — via preset selection or chat cloning — backed by 3 pillars (dimensions, patterns, examples) that produce verifiably different behavior.

**Architecture:** New `PersonalityProfile` entity in `brand/` module. 6 presets with full 3-pillar definitions. Evolved LangGraph pipeline for cloning. Qdrant style anchors for anti-drift RAG. `knowledge_builder` extended to inject compiled personality. UI in Brand Studio → Esencia → "Voz y Personalidad" section.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, LangGraph, Qdrant, OpenAI/Anthropic (configurable). Next.js 15, React 18, TypeScript, Tailwind, Shadcn UI.

**Spec:** `docs/superpowers/specs/2026-04-13-personality-engine-design.md`

---

## File Structure

### Backend — New Files
| File | Responsibility |
|------|---------------|
| `backend/src/modules/brand/domain/personality.py` | PersonalityProfile entity, PersonalityDimensions VO, DimensionContract (30 levels), LinguisticPatterns VO, PersonalityCompiler, PresetDefinition, PERSONALITY_PRESETS, SampleExchange |
| `backend/src/modules/brand/infrastructure/models/personality_model.py` | SQLAlchemy model for `personality_profiles` table |
| `backend/src/modules/brand/infrastructure/repositories/personality_repository.py` | CRUD + `get_active()` + `deactivate_others()` |
| `backend/src/modules/brand/infrastructure/qdrant/style_anchor_store.py` | Qdrant client: upsert, search_similar, delete_by_profile |
| `backend/src/modules/brand/infrastructure/parsers/base.py` | ChatParser protocol, Message dataclass |
| `backend/src/modules/brand/infrastructure/parsers/whatsapp_parser.py` | WhatsApp .txt → List[Message] |
| `backend/src/modules/brand/infrastructure/parsers/instagram_parser.py` | IG JSON → List[Message] |
| `backend/src/modules/brand/infrastructure/parsers/telegram_parser.py` | Telegram JSON → List[Message] |
| `backend/src/modules/brand/application/services/personality_service.py` | select_preset, clone_from_chat, get_active, update_dimensions, compile_instruction, delete_with_anchors |
| `backend/src/modules/brand/api/personality.py` | 7 REST endpoints |
| `backend/src/modules/sales_agent/application/services/style_anchor_retriever.py` | Qdrant per-turn similarity search |

### Backend — Modified Files
| File | Change |
|------|--------|
| `backend/src/modules/brand/application/agents/style_analyzer/state.py:16-36` | Add PersonalityProfile fields to state |
| `backend/src/modules/brand/application/agents/style_analyzer/prompts.py:24-55` | Evolve Psychologist prompt for structured 3-pillar output |
| `backend/src/modules/brand/application/agents/style_analyzer/nodes.py:90-122` | Evolve Psychologist + Architect nodes |
| `backend/src/modules/brand/application/agents/style_analyzer/graph.py:24-45` | Add Parser + Embedder nodes |
| `backend/src/modules/sales_agent/application/services/knowledge_builder.py:50,92` | Load PersonalityProfile, inject system_instruction |
| `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2:19-22` | Personality block + style anchors |
| `backend/src/modules/copilot/domain/navigation_map.py:48-91` | Add voice-personality section |
| `backend/src/main.py` | Mount personality router |

### Frontend — New Files
| File | Responsibility |
|------|---------------|
| `frontend/src/features/brand/sections/personality/personality-section.tsx` | Esencia preview card (empty + configured states) |
| `frontend/src/features/brand/sections/personality/personality-manager.tsx` | Edit sheet: preset selector + clone upload + sliders + preview |
| `frontend/src/features/brand/sections/personality/preset-catalog.tsx` | Grid of 6 preset cards with sample messages |
| `frontend/src/features/brand/sections/personality/clone-upload.tsx` | Chat file upload + processing state |
| `frontend/src/features/brand/sections/personality/dimension-sliders.tsx` | 6 sliders with level labels |
| `frontend/src/features/brand/sections/personality/personality-preview.tsx` | Simulated chat preview |
| `frontend/src/features/brand/api/personality.ts` | React Query hooks for personality endpoints |
| `frontend/src/features/brand/types/personality.ts` | TypeScript interfaces |

### Frontend — Modified Files
| File | Change |
|------|--------|
| `frontend/src/features/brand/config/sections.ts:105-141` | Add voice-personality nav item to esencia, remove voice from identidad-creativa |
| `frontend/src/features/brand/components/views/esencia-view.tsx:63-73` | Add PersonalitySection between ValuesEssence and Team |
| `frontend/src/features/brand/components/views/identidad-creativa-view.tsx` | Remove VoiceSection |
| `frontend/src/features/brand/types/edit-mode.ts:1-19` | Add "personality-profile" |
| `frontend/src/features/brand/components/edit/edit-sheet-manager.tsx` | Add PersonalityManager case |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/tono-y-voz/page.tsx` | Redirect to esencia#voice-personality |

### Tests
| File | What it tests |
|------|--------------|
| `backend/tests/modules/brand/test_personality_domain.py` | DimensionContract, PersonalityCompiler, presets, negative constraints |
| `backend/tests/modules/brand/test_personality_repository.py` | CRUD, get_active, unique constraint |
| `backend/tests/modules/brand/test_personality_service.py` | select_preset, clone flow, compile_instruction |
| `backend/tests/modules/brand/test_parsers.py` | WhatsApp/IG/Telegram parsing |
| `backend/tests/modules/brand/test_personality_compiler_output.py` | Verify compiled system_instruction produces distinct LLM behavior |
| `backend/tests/modules/sales_agent/test_knowledge_builder_personality.py` | PersonalityProfile integration |
| `frontend/src/features/brand/sections/personality/__tests__/personality-section.test.tsx` | Component rendering |
| `frontend/src/features/brand/api/__tests__/personality.test.ts` | API hooks |

---

## Task 1: Domain Models (PersonalityProfile + DimensionContract + Compiler)

**Files:**
- Create: `backend/src/modules/brand/domain/personality.py`
- Test: `backend/tests/modules/brand/test_personality_domain.py`

This is the heart of the system. The DimensionContract defines 30 concrete behavioral rules. The PersonalityCompiler translates dimensions → system_instruction text. Getting this right is what makes the personality actually work.

- [ ] **Step 1: Write failing tests for DimensionContract**

```python
# backend/tests/modules/brand/test_personality_domain.py
import pytest
from src.modules.brand.domain.personality import (
    DimensionContract,
    DimensionLevel,
    PersonalityDimensions,
    PersonalityCompiler,
    LinguisticPatterns,
    SampleExchange,
    PERSONALITY_PRESETS,
)


class TestDimensionContract:
    """DimensionContract resolves numeric values to concrete behavioral rules."""

    def test_energy_very_low_resolves_correctly(self):
        level = DimensionContract.resolve("energy", 0.1)
        assert level.name == "muy_baja"
        assert "Sin exclamaciones" in level.instruction
        assert len(level.negative_constraints) > 0
        assert "NUNCA uses signos de exclamación" in level.negative_constraints[0]

    def test_energy_high_resolves_correctly(self):
        level = DimensionContract.resolve("energy", 0.7)
        assert level.name == "alta"
        assert "exclamaciones frecuentes" in level.instruction.lower()
        assert level.negative_constraints == []

    def test_warmth_intimate_resolves_correctly(self):
        level = DimensionContract.resolve("warmth", 0.9)
        assert level.name == "intima"
        assert "yo también pasé por eso" in level.instruction.lower()

    def test_humor_serious_has_negative_constraints(self):
        level = DimensionContract.resolve("humor", 0.1)
        assert level.name == "serio"
        assert any("jaja" in c.lower() for c in level.negative_constraints)

    def test_all_dimensions_have_5_levels(self):
        for dim_name in ["energy", "warmth", "humor", "expressiveness", "narrative", "verbosity"]:
            levels = DimensionContract.get_levels(dim_name)
            assert len(levels) == 5, f"{dim_name} should have 5 levels"

    def test_boundary_values_resolve_to_correct_level(self):
        # 0.0 = first level, 0.2 = second level, etc.
        assert DimensionContract.resolve("energy", 0.0).name == "muy_baja"
        assert DimensionContract.resolve("energy", 0.2).name == "baja"
        assert DimensionContract.resolve("energy", 0.4).name == "media"
        assert DimensionContract.resolve("energy", 0.6).name == "alta"
        assert DimensionContract.resolve("energy", 0.8).name == "electrica"
        # Edge: exactly 1.0
        assert DimensionContract.resolve("energy", 1.0).name == "electrica"

    def test_invalid_dimension_raises(self):
        with pytest.raises(ValueError, match="Unknown dimension"):
            DimensionContract.resolve("invalid_dim", 0.5)

    def test_out_of_range_clamps(self):
        level_low = DimensionContract.resolve("energy", -0.5)
        assert level_low.name == "muy_baja"
        level_high = DimensionContract.resolve("energy", 1.5)
        assert level_high.name == "electrica"


class TestPersonalityCompiler:
    """PersonalityCompiler produces 5-block system_instruction from profile data."""

    @pytest.fixture
    def warm_dimensions(self):
        return PersonalityDimensions(
            energy=0.65, warmth=0.85, humor=0.6,
            expressiveness=0.7, narrative=0.5, verbosity=0.4,
        )

    @pytest.fixture
    def minimalist_dimensions(self):
        return PersonalityDimensions(
            energy=0.15, warmth=0.25, humor=0.1,
            expressiveness=0.1, narrative=0.2, verbosity=0.15,
        )

    @pytest.fixture
    def patterns(self):
        return LinguisticPatterns(
            emoji_style="frequent",
            favorite_emojis=["😊", "🔥", "💪"],
            greeting="¡Hola! ¿Cómo estás?",
            farewell="¡Un abrazo!",
            filler_phrases=["mira", "te cuento"],
            avg_message_length="short",
            punctuation_style="expressive",
            humor_type="playful",
            unique_vocabulary=["genial", "increíble"],
        )

    @pytest.fixture
    def sample_exchanges(self):
        return [
            SampleExchange(
                context="greeting",
                other_message="Hola, buenas tardes",
                author_response="¡Hola! ¿Cómo estás? 😊 Qué bueno que me escribes!",
            ),
            SampleExchange(
                context="objection",
                other_message="Es muy caro",
                author_response="Te entiendo perfecto, mira, te cuento lo que le pasó a Laura 💛",
            ),
        ]

    def test_compile_produces_5_blocks(self, warm_dimensions, patterns, sample_exchanges):
        result = PersonalityCompiler.compile(warm_dimensions, patterns, sample_exchanges)
        assert "REGLAS DE PERSONALIDAD" in result or "energía" in result.lower()
        assert "HUELLA LINGÜÍSTICA" in result or "mira" in result
        assert "NUNCA HACES" in result or "REGLA SUPREMA" in result
        assert "¡Hola! ¿Cómo estás? 😊" in result  # sample exchange
        assert "ESTA ES TU VOZ" in result  # identity anchor

    def test_compile_includes_negative_constraints_for_low_dims(self, minimalist_dimensions, patterns, sample_exchanges):
        result = PersonalityCompiler.compile(minimalist_dimensions, patterns, sample_exchanges)
        assert "NUNCA" in result
        assert "emojis" in result.lower()  # expressiveness=0.1 → no emojis
        assert "exclamación" in result.lower() or "exclamaciones" in result.lower()

    def test_compile_no_negative_constraints_for_high_dims(self, warm_dimensions, patterns, sample_exchanges):
        result = PersonalityCompiler.compile(warm_dimensions, patterns, sample_exchanges)
        # warm_close has no dims < 0.3, so NUNCA section should be minimal
        nunca_count = result.count("NUNCA")
        # Only the anchor at the end uses NUNCA
        assert nunca_count <= 3  # anchor has 1-2 NUNCAs

    def test_two_presets_produce_different_instructions(self):
        warm = PERSONALITY_PRESETS["warm_close"]
        mini = PERSONALITY_PRESETS["minimalist"]
        warm_result = PersonalityCompiler.compile(
            warm.dimensions, warm.linguistic_patterns, warm.sample_exchanges,
        )
        mini_result = PersonalityCompiler.compile(
            mini.dimensions, mini.linguistic_patterns, mini.sample_exchanges,
        )
        # They should be substantially different
        assert warm_result != mini_result
        assert "😊" in warm_result
        assert "😊" not in mini_result
        assert "NUNCA uses emojis" in mini_result
        assert "NUNCA uses emojis" not in warm_result


class TestPresets:
    """Verify all 6 presets are complete with 3 pillars."""

    def test_all_6_presets_exist(self):
        assert len(PERSONALITY_PRESETS) == 6
        expected_keys = {"warm_close", "electric", "serene", "direct", "narrative", "minimalist"}
        assert set(PERSONALITY_PRESETS.keys()) == expected_keys

    @pytest.mark.parametrize("key", ["warm_close", "electric", "serene", "direct", "narrative", "minimalist"])
    def test_preset_has_3_pillars(self, key):
        preset = PERSONALITY_PRESETS[key]
        # Pilar 1: Dimensions
        assert preset.dimensions is not None
        assert 0.0 <= preset.dimensions.energy <= 1.0
        # Pilar 2: Linguistic patterns
        assert preset.linguistic_patterns is not None
        assert len(preset.linguistic_patterns.filler_phrases) > 0
        assert preset.linguistic_patterns.greeting != ""
        # Pilar 3: Sample exchanges
        assert len(preset.sample_exchanges) >= 5
        contexts = {e.context for e in preset.sample_exchanges}
        assert "greeting" in contexts
        assert "objection" in contexts

    @pytest.mark.parametrize("key", ["warm_close", "electric", "serene", "direct", "narrative", "minimalist"])
    def test_preset_compiles_without_error(self, key):
        preset = PERSONALITY_PRESETS[key]
        result = PersonalityCompiler.compile(
            preset.dimensions, preset.linguistic_patterns, preset.sample_exchanges,
        )
        assert len(result) > 200  # Non-trivial output
        assert "ESTA ES TU VOZ" in result
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && .venv/bin/pytest tests/modules/brand/test_personality_domain.py -v --tb=short
```

Expected: ImportError — `personality` module doesn't exist yet.

- [ ] **Step 3: Implement domain models**

Create `backend/src/modules/brand/domain/personality.py` with:
- `DimensionLevel` dataclass (name, instruction, negative_constraints)
- `DimensionContract` class with static method `resolve(dim_name, value) → DimensionLevel` containing ALL 30 levels from spec section 4
- `PersonalityDimensions` Pydantic model (6 float fields: energy, warmth, humor, expressiveness, narrative, verbosity)
- `LinguisticPatterns` Pydantic model (emoji_style, favorite_emojis, greeting, farewell, filler_phrases, avg_message_length, punctuation_style, humor_type, unique_vocabulary)
- `SampleExchange` Pydantic model (context, other_message, author_response)
- `PersonalityCompiler` class with static `compile(dimensions, patterns, exchanges) → str` that produces the 5-block system_instruction from spec section 5
- `PresetDefinition` Pydantic model (key, name, icon, description, dimensions, linguistic_patterns, sample_exchanges)
- `PERSONALITY_PRESETS` dict with all 6 presets fully defined (dimensions + patterns + 5-8 sample_exchanges each)
- `PersonalityProfile` Pydantic model (the full entity with all fields from spec section 9)

**Critical:** The DimensionContract text MUST use the exact instructions from spec section 4. Copy them verbatim. The PersonalityCompiler MUST produce the 5-block format from spec section 5. The presets MUST include complete sample_exchanges (not placeholders).

Reference for DimensionContract text: spec section 4 (6 tables, 5 rows each = 30 entries).
Reference for compiler output format: spec section 5.
Reference for warm_close preset: spec section 6.

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd backend && .venv/bin/pytest tests/modules/brand/test_personality_domain.py -v --tb=short
```

Expected: ALL PASS.

- [ ] **Step 5: Run ruff lint**

```bash
cd backend && .venv/bin/ruff check src/modules/brand/domain/personality.py --no-cache
```

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/brand/domain/personality.py backend/tests/modules/brand/test_personality_domain.py
git commit -m "feat(brand): add PersonalityProfile domain — DimensionContract, Compiler, 6 presets

30-level DimensionContract, PersonalityCompiler producing 5-block
system_instruction, 6 complete presets with 3 pillars each.
21 tests covering contract resolution, compilation, negative constraints."
```

---

## Task 2: Infrastructure — SQLAlchemy Model + Migration + Repository

**Files:**
- Create: `backend/src/modules/brand/infrastructure/models/personality_model.py`
- Create: `backend/src/modules/brand/infrastructure/repositories/personality_repository.py`
- Create: alembic migration
- Test: `backend/tests/modules/brand/test_personality_repository.py`

- [ ] **Step 1: Write failing repository tests**

```python
# backend/tests/modules/brand/test_personality_repository.py
import pytest
from uuid import uuid4
from src.modules.brand.infrastructure.repositories.personality_repository import PersonalityProfileRepository
from src.modules.brand.infrastructure.models.personality_model import PersonalityProfileModel


@pytest.fixture
def repo(db):
    return PersonalityProfileRepository(db)


@pytest.fixture
def tenant_id():
    return uuid4()


class TestPersonalityProfileRepository:

    async def test_create_profile(self, repo, tenant_id):
        profile = await repo.create(
            tenant_id=tenant_id,
            name="Test Preset",
            profile_type="preset",
            preset_key="warm_close",
            dimensions={"energy": 0.65, "warmth": 0.85},
            linguistic_patterns={"greeting": "Hola!"},
            sample_exchanges=[],
            negative_constraints=[],
            system_instruction="test instruction",
        )
        assert profile.id is not None
        assert profile.tenant_id == tenant_id
        assert profile.is_active is False

    async def test_get_active_returns_none_when_no_active(self, repo, tenant_id):
        result = await repo.get_active(tenant_id)
        assert result is None

    async def test_activate_deactivates_others(self, repo, tenant_id):
        p1 = await repo.create(tenant_id=tenant_id, name="P1", profile_type="preset",
                                dimensions={}, linguistic_patterns={}, sample_exchanges=[],
                                negative_constraints=[], system_instruction="inst1")
        await repo.activate(p1.id, tenant_id)

        p2 = await repo.create(tenant_id=tenant_id, name="P2", profile_type="preset",
                                dimensions={}, linguistic_patterns={}, sample_exchanges=[],
                                negative_constraints=[], system_instruction="inst2")
        await repo.activate(p2.id, tenant_id)

        active = await repo.get_active(tenant_id)
        assert active.id == p2.id

        # p1 should be deactivated
        p1_refreshed = await repo.get_by_id(p1.id, tenant_id)
        assert p1_refreshed.is_active is False

    async def test_soft_delete(self, repo, tenant_id):
        profile = await repo.create(tenant_id=tenant_id, name="Del", profile_type="preset",
                                     dimensions={}, linguistic_patterns={}, sample_exchanges=[],
                                     negative_constraints=[], system_instruction="x")
        await repo.soft_delete(profile.id, tenant_id)
        result = await repo.get_by_id(profile.id, tenant_id)
        assert result is None  # Soft deleted = not found

    async def test_tenant_isolation(self, repo, tenant_id):
        other_tenant = uuid4()
        await repo.create(tenant_id=tenant_id, name="Mine", profile_type="preset",
                           dimensions={}, linguistic_patterns={}, sample_exchanges=[],
                           negative_constraints=[], system_instruction="x")
        result = await repo.get_active(other_tenant)
        assert result is None
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && .venv/bin/pytest tests/modules/brand/test_personality_repository.py -v --tb=short
```

- [ ] **Step 3: Implement SQLAlchemy model**

Create `backend/src/modules/brand/infrastructure/models/personality_model.py`:
- Table name: `personality_profiles`
- Columns from spec section 9 (id, tenant_id, offer_id, avatar_id, name, profile_type, preset_key, is_active, dimensions, linguistic_patterns, sample_exchanges, negative_constraints, system_instruction, source_metadata, qdrant_collection, anchor_count, llm_provider, llm_model, created_at, updated_at, deleted_at)
- All JSONB columns with server_default
- DateTime columns with timezone=True

- [ ] **Step 4: Implement repository**

Create `backend/src/modules/brand/infrastructure/repositories/personality_repository.py`:
- `create()` — insert new profile
- `get_by_id(id, tenant_id)` — get by id with tenant filter + deleted_at IS NULL
- `get_active(tenant_id)` — get where is_active=True + deleted_at IS NULL + offer_id IS NULL + avatar_id IS NULL
- `activate(id, tenant_id)` — set is_active=True, deactivate all others for same tenant
- `update_dimensions(id, tenant_id, dimensions, system_instruction)` — update dims + recompiled instruction
- `soft_delete(id, tenant_id)` — set deleted_at

All queries filter by `tenant_id`. SQLAlchemy 2.0 syntax (`select().where()`).

- [ ] **Step 5: Create migration**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && alembic revision --autogenerate -m 'add personality_profiles table'"
```

Then replace the generated migration with idempotent raw SQL from spec section 9 (CREATE TABLE IF NOT EXISTS + indexes).

- [ ] **Step 6: Apply migration**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"
```

- [ ] **Step 7: Run tests — verify they pass**

```bash
cd backend && .venv/bin/pytest tests/modules/brand/test_personality_repository.py -v --tb=short
```

- [ ] **Step 8: Commit**

```bash
git add backend/src/modules/brand/infrastructure/models/personality_model.py \
        backend/src/modules/brand/infrastructure/repositories/personality_repository.py \
        backend/tests/modules/brand/test_personality_repository.py \
        backend/alembic/versions/*.py
git commit -m "feat(brand): add personality_profiles table + repository

SQLAlchemy model, idempotent migration, async repository with
tenant isolation, activate/deactivate logic, soft delete.
5 tests covering CRUD, activation, tenant isolation."
```

---

## Task 3: Chat Parsers (WhatsApp, Instagram, Telegram)

**Files:**
- Create: `backend/src/modules/brand/infrastructure/parsers/base.py`
- Create: `backend/src/modules/brand/infrastructure/parsers/whatsapp_parser.py`
- Create: `backend/src/modules/brand/infrastructure/parsers/instagram_parser.py`
- Create: `backend/src/modules/brand/infrastructure/parsers/telegram_parser.py`
- Test: `backend/tests/modules/brand/test_parsers.py`

- [ ] **Step 1: Write failing parser tests**

Tests with real sample data for each format. Include edge cases: multi-line messages, media attachments, system messages, unicode emojis, different date formats.

The WhatsApp regex from spec: `^\[?(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\]?\s*-?\s*(.+?):\s*(.+)$`

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && .venv/bin/pytest tests/modules/brand/test_parsers.py -v --tb=short
```

- [ ] **Step 3: Implement parsers**

Each parser implements `ChatParser` protocol with `parse(content: str, user_name: str | None) → list[Message]`. Auto-detect format via `detect_format(content)` in base.py. Only extract messages from the target user. Skip system messages, media, forwards.

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd backend && .venv/bin/pytest tests/modules/brand/test_parsers.py -v --tb=short
```

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/brand/infrastructure/parsers/ backend/tests/modules/brand/test_parsers.py
git commit -m "feat(brand): add chat parsers — WhatsApp, Instagram DM, Telegram

Protocol-based parsers with auto-format detection. Extracts user
messages only, skips system/media/forwards. Tested with real
sample data including edge cases."
```

---

## Task 4: Qdrant Style Anchor Store

**Files:**
- Create: `backend/src/modules/brand/infrastructure/qdrant/style_anchor_store.py`
- Create: `backend/src/modules/brand/infrastructure/qdrant/__init__.py`
- Test: `backend/tests/modules/brand/test_style_anchor_store.py`

- [ ] **Step 1: Write failing tests**

Test upsert_anchors, search_similar (with tenant_id filter), delete_by_profile. Use mock Qdrant client for unit tests.

- [ ] **Step 2: Implement StyleAnchorStore**

Collection: `personality_style_anchors`. Points with payload: tenant_id, profile_id, context_type, other_message, author_response. All queries MUST filter by tenant_id. Use existing Qdrant connection pattern from `shared/` or `copilot/` module.

- [ ] **Step 3: Run tests — verify pass**

- [ ] **Step 4: Commit**

---

## Task 5: Evolve Style Analyzer Pipeline (6 nodes)

**Files:**
- Modify: `backend/src/modules/brand/application/agents/style_analyzer/state.py`
- Modify: `backend/src/modules/brand/application/agents/style_analyzer/prompts.py`
- Modify: `backend/src/modules/brand/application/agents/style_analyzer/nodes.py`
- Modify: `backend/src/modules/brand/application/agents/style_analyzer/graph.py`
- Test: `backend/tests/modules/brand/test_personality_service.py`

- [ ] **Step 1: Write failing service tests**

Test `PersonalityService.clone_from_chat()` end-to-end: input raw chat → output PersonalityProfile with dimensions, patterns, sample_exchanges, compiled system_instruction.

- [ ] **Step 2: Update state.py**

Add to OnboardingState: `parsed_messages`, `personality_dimensions`, `linguistic_patterns`, `sample_exchanges`, `personality_profile`, `anchor_count`.

- [ ] **Step 3: Update prompts.py**

Replace PSYCHOLOGIST_PROMPT with the structured extraction prompt from spec section 7 (Psychologist nodo 3). This is the prompt that extracts the 3 pillars. Copy EXACTLY from spec — it requests JSON with dimensions (+ evidence citations), linguistic_patterns, sample_exchanges, and confidence.

- [ ] **Step 4: Update nodes.py**

- `node_parser`: NEW — calls ChatParser.parse() on raw input
- `node_psychologist`: EVOLVE — uses new prompt, parses JSON response into PersonalityDimensions + LinguisticPatterns + SampleExchange list
- `node_architect`: EVOLVE — calls PersonalityCompiler.compile() to produce 5-block system_instruction
- `node_embedder`: NEW — calls StyleAnchorStore.upsert_anchors()

- [ ] **Step 5: Update graph.py**

Add parser and embedder nodes. New flow: parser → janitor → psychologist → architect → embedder → simulator.

- [ ] **Step 6: Implement PersonalityService**

Create `backend/src/modules/brand/application/services/personality_service.py`:
- `select_preset(tenant_id, preset_key)` — look up preset, compile, create PersonalityProfile row, activate
- `clone_from_chat(tenant_id, file_content, file_format, user_name, llm_provider, llm_model)` — run pipeline, create PersonalityProfile, activate
- `get_active(tenant_id)` — delegate to repo
- `update_dimensions(profile_id, tenant_id, new_dimensions)` — update dims, recompile instruction, save
- `delete_with_anchors(profile_id, tenant_id)` — soft delete + clear Qdrant

- [ ] **Step 7: Run tests — verify pass**

- [ ] **Step 8: Commit**

---

## Task 6: API Endpoints

**Files:**
- Create: `backend/src/modules/brand/api/personality.py`
- Modify: `backend/src/main.py` (mount router)

- [ ] **Step 1: Implement 7 endpoints per spec section 12**

All with `response_model=`, `X-Tenant-ID` filter, proper DTOs. The `/clone` endpoint accepts file upload (multipart/form-data).

- [ ] **Step 2: Mount router in main.py**

- [ ] **Step 3: Run ruff + existing tests to verify no regressions**

```bash
cd backend && .venv/bin/ruff check src/ tests/ --no-cache && .venv/bin/pytest -x -q --tb=short
```

- [ ] **Step 4: Commit**

---

## Task 7: Sales Agent Integration

**Files:**
- Create: `backend/src/modules/sales_agent/application/services/style_anchor_retriever.py`
- Modify: `backend/src/modules/sales_agent/application/services/knowledge_builder.py:50,92`
- Modify: `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2:19-22`
- Test: `backend/tests/modules/sales_agent/test_knowledge_builder_personality.py`

- [ ] **Step 1: Write failing test**

Test that knowledge_builder loads PersonalityProfile when active and injects system_instruction. Test fallback to voice_tone when no profile exists.

- [ ] **Step 2: Implement style_anchor_retriever.py**

From spec section 8.2. Searches Qdrant per-turn with tenant_id + profile_id filter. Returns top 3 StyleAnchors.

- [ ] **Step 3: Extend knowledge_builder.py**

At line 50, after loading brand settings, also load PersonalityProfile via personality_repo. At line 92, inject `personality_instruction` if profile exists, else use `voice_tone`.

- [ ] **Step 4: Update agent_identity.j2**

At lines 19-22, replace the simple voice_tone block with the conditional personality injection + style anchors from spec section 8.3.

- [ ] **Step 5: Run tests — verify pass**

- [ ] **Step 6: Commit**

---

## Task 8: Personality Behavior Verification Tests

**Files:**
- Create: `backend/tests/modules/brand/test_personality_compiler_output.py`

**This is the critical task.** These tests verify that compiled system_instructions actually produce distinct, verifiable LLM behavior. They don't call a real LLM — they verify the text content of the compiled instruction against the DimensionContract.

- [ ] **Step 1: Write verification tests**

```python
# backend/tests/modules/brand/test_personality_compiler_output.py
"""
Verify that PersonalityCompiler output matches DimensionContract exactly.
These tests ensure the compiled system_instruction will actually make
the LLM behave differently for each personality.
"""
import pytest
from src.modules.brand.domain.personality import (
    PersonalityCompiler,
    DimensionContract,
    PERSONALITY_PRESETS,
)


class TestCompilerContractCompliance:
    """Each compiled instruction MUST contain the exact text from DimensionContract."""

    @pytest.mark.parametrize("preset_key", list(PERSONALITY_PRESETS.keys()))
    def test_compiled_instruction_contains_dimension_rules(self, preset_key):
        preset = PERSONALITY_PRESETS[preset_key]
        compiled = PersonalityCompiler.compile(
            preset.dimensions, preset.linguistic_patterns, preset.sample_exchanges,
        )
        # For each dimension, verify the resolved level's instruction text appears
        for dim_name in ["energy", "warmth", "humor", "expressiveness", "narrative", "verbosity"]:
            value = getattr(preset.dimensions, dim_name)
            level = DimensionContract.resolve(dim_name, value)
            # The compiled instruction should contain key phrases from the level
            assert any(
                phrase.lower() in compiled.lower()
                for phrase in level.instruction.split(". ")[:2]  # Check first 2 sentences
            ), f"Preset '{preset_key}': dimension '{dim_name}' level '{level.name}' instruction not found in compiled output"

    @pytest.mark.parametrize("preset_key", list(PERSONALITY_PRESETS.keys()))
    def test_compiled_instruction_contains_negative_constraints(self, preset_key):
        preset = PERSONALITY_PRESETS[preset_key]
        compiled = PersonalityCompiler.compile(
            preset.dimensions, preset.linguistic_patterns, preset.sample_exchanges,
        )
        # For dims < 0.3, verify negative constraints appear
        for dim_name in ["energy", "warmth", "humor", "expressiveness", "narrative", "verbosity"]:
            value = getattr(preset.dimensions, dim_name)
            if value < 0.3:
                level = DimensionContract.resolve(dim_name, value)
                for constraint in level.negative_constraints:
                    assert constraint in compiled, (
                        f"Preset '{preset_key}': negative constraint '{constraint}' "
                        f"for dim '{dim_name}'={value} not found in compiled output"
                    )

    @pytest.mark.parametrize("preset_key", list(PERSONALITY_PRESETS.keys()))
    def test_compiled_instruction_contains_linguistic_patterns(self, preset_key):
        preset = PERSONALITY_PRESETS[preset_key]
        compiled = PersonalityCompiler.compile(
            preset.dimensions, preset.linguistic_patterns, preset.sample_exchanges,
        )
        # Verify greeting appears
        assert preset.linguistic_patterns.greeting in compiled
        # Verify farewell appears
        assert preset.linguistic_patterns.farewell in compiled
        # Verify filler phrases appear
        for phrase in preset.linguistic_patterns.filler_phrases:
            assert phrase in compiled

    @pytest.mark.parametrize("preset_key", list(PERSONALITY_PRESETS.keys()))
    def test_compiled_instruction_contains_sample_exchanges(self, preset_key):
        preset = PERSONALITY_PRESETS[preset_key]
        compiled = PersonalityCompiler.compile(
            preset.dimensions, preset.linguistic_patterns, preset.sample_exchanges,
        )
        # Verify at least the author_response from sample exchanges appears
        for exchange in preset.sample_exchanges[:3]:  # Check first 3
            assert exchange.author_response in compiled, (
                f"Preset '{preset_key}': sample exchange response not found in compiled output"
            )

    @pytest.mark.parametrize("preset_key", list(PERSONALITY_PRESETS.keys()))
    def test_compiled_instruction_ends_with_identity_anchor(self, preset_key):
        preset = PERSONALITY_PRESETS[preset_key]
        compiled = PersonalityCompiler.compile(
            preset.dimensions, preset.linguistic_patterns, preset.sample_exchanges,
        )
        assert "ESTA ES TU VOZ" in compiled

    def test_minimalist_has_most_negative_constraints(self):
        """Minimalist preset has lowest dims → most NUNCA rules."""
        presets_nunca_count = {}
        for key, preset in PERSONALITY_PRESETS.items():
            compiled = PersonalityCompiler.compile(
                preset.dimensions, preset.linguistic_patterns, preset.sample_exchanges,
            )
            presets_nunca_count[key] = compiled.count("NUNCA")
        # Minimalist should have the most NUNCA rules
        assert presets_nunca_count["minimalist"] == max(presets_nunca_count.values())

    def test_warm_close_and_minimalist_are_opposites(self):
        """These two presets should produce maximally different instructions."""
        warm = PERSONALITY_PRESETS["warm_close"]
        mini = PERSONALITY_PRESETS["minimalist"]
        warm_compiled = PersonalityCompiler.compile(
            warm.dimensions, warm.linguistic_patterns, warm.sample_exchanges,
        )
        mini_compiled = PersonalityCompiler.compile(
            mini.dimensions, mini.linguistic_patterns, mini.sample_exchanges,
        )
        # Warm has emojis, minimalist forbids them
        assert "😊" in warm_compiled
        assert "NUNCA uses emojis" in mini_compiled
        # Warm has exclamations, minimalist forbids them
        assert "!" in warm_compiled
        assert "exclamación" in mini_compiled.lower()
        # Different lengths (minimalist = shorter messages)
        assert "1-2 oraciones" in mini_compiled.lower() or "2 oraciones" in mini_compiled.lower()
```

- [ ] **Step 2: Run tests — verify pass (they test against Task 1's domain code)**

```bash
cd backend && .venv/bin/pytest tests/modules/brand/test_personality_compiler_output.py -v --tb=short
```

- [ ] **Step 3: Commit**

---

## Task 9: Frontend — Types + API Hooks

**Files:**
- Create: `frontend/src/features/brand/types/personality.ts`
- Create: `frontend/src/features/brand/api/personality.ts`
- Test: `frontend/src/features/brand/api/__tests__/personality.test.ts`

- [ ] **Step 1: Create TypeScript types**

Interfaces matching backend DTOs: PersonalityProfileDTO, PresetSummaryDTO, PersonalityDimensions, LinguisticPatterns, SampleExchange, SimulationDTO.

- [ ] **Step 2: Create React Query hooks**

`usePersonalityPresets()`, `useActivePersonality()`, `useSelectPreset()`, `useClonePersonality()`, `useUpdateDimensions()`, `useSimulatePersonality()`, `useDeletePersonality()`. All using `fetchClient` for X-Tenant-ID injection.

- [ ] **Step 3: Write tests**

- [ ] **Step 4: Commit**

---

## Task 10: Frontend — UI Components

**Files:**
- Create: personality-section.tsx, personality-manager.tsx, preset-catalog.tsx, clone-upload.tsx, dimension-sliders.tsx, personality-preview.tsx
- Modify: sections.ts, esencia-view.tsx, identidad-creativa-view.tsx, edit-mode.ts, edit-sheet-manager.tsx, tono-y-voz/page.tsx
- Modify: `backend/src/modules/copilot/domain/navigation_map.py`

- [ ] **Step 1: Update sections.ts**

In esencia section config (lines 105-141):
- Rename nav item "personality" to "values-essence" (label: "Valores y Esencia")
- Add new nav item "voice-personality" (label: "Voz y Personalidad", icon: Theater, scrollTo: "#voice-personality", validator: validatePersonalityProfile)
- Remove "voice" nav item from identidad-creativa section

- [ ] **Step 2: Update edit-mode.ts**

Add `"personality-profile"` to the EditMode union type.

- [ ] **Step 3: Create PersonalitySection (Esencia preview)**

Two states: empty (dashed border + 2 CTAs) and configured (badge + dimension bars + sample message + pattern chips).

- [ ] **Step 4: Create PresetCatalog**

Grid of 6 cards with icon, name, description, sample message. Click selects and shows preview.

- [ ] **Step 5: Create DimensionSliders**

6 Shadcn Slider components with level name labels that update in real-time as the slider moves.

- [ ] **Step 6: Create CloneUpload**

File upload (drag & drop) accepting .txt and .json. Processing state with spinner. Result display.

- [ ] **Step 7: Create PersonalityPreview**

Simulated chat bubbles showing 2 exchanges. "Regenerar" button calls simulate endpoint.

- [ ] **Step 8: Create PersonalityManager (edit sheet orchestrator)**

Two tabs/modes: "Elegir Preset" and "Clonar". Both flow to the same result view (sliders + preview + save).

- [ ] **Step 9: Wire into esencia-view.tsx**

Add `<PersonalitySection />` between ValuesEssencePreview and TeamSection. Pass openEdit("personality-profile").

- [ ] **Step 10: Wire into edit-sheet-manager.tsx**

Add case for "personality-profile" → PersonalityManager.

- [ ] **Step 11: Remove VoiceSection from identidad-creativa-view.tsx**

- [ ] **Step 12: Update tono-y-voz redirect**

Change redirect target from `/identidad-creativa` to `/esencia#voice-personality`.

- [ ] **Step 13: Update navigation_map.py**

Add "voice-personality" section to the esencia page definition (after line 76 in navigation_map.py).

- [ ] **Step 14: Run frontend checks**

```bash
cd frontend && npx tsc --noEmit && npx eslint src/ && npx vitest run
```

- [ ] **Step 15: Commit**

---

## Task 11: Integration Test — Full Flow

**Files:**
- Create: `backend/tests/modules/brand/test_personality_integration.py`

- [ ] **Step 1: Write integration test**

Test the complete flow: select preset → verify system_instruction → verify knowledge_builder loads it → verify fallback when no profile. Also: create profile, update dimensions, verify recompilation produces different output.

- [ ] **Step 2: Run ALL tests**

```bash
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/pytest -x -q --tb=short
cd frontend && npx tsc --noEmit
cd frontend && npx vitest run
```

- [ ] **Step 3: Commit**

---

## Task 12: E2E Smoke Test

**Files:**
- Create: `frontend/e2e/specs/smoke/personality.smoke.spec.ts`
- Create: `frontend/e2e/pages/personality.page.ts`

- [ ] **Step 1: Create POM**

PersonalityPage with locators for: empty state CTAs, preset cards, dimension sliders, preview chat, save button.

- [ ] **Step 2: Write smoke test**

Navigate to Brand Studio → Esencia, verify personality section renders, click "Elegir personalidad", select a preset, verify preview shows sample message, save, verify section shows configured state.

- [ ] **Step 3: Run smoke test**

```bash
cd frontend && npx playwright test --project=smoke --grep personality
```

- [ ] **Step 4: Commit final**

```bash
git add -A  # This is the final commit, all files from this feature
git commit -m "feat(brand): complete Personality Engine — presets, cloning, sales agent integration

Implements the full Personality Engine (Fase 1):
- PersonalityProfile entity with DimensionContract (30 behavioral rules)
- PersonalityCompiler producing 5-block system_instruction
- 6 complete presets with 3 pillars (dimensions + patterns + examples)
- Chat parsers (WhatsApp, Instagram, Telegram)
- Qdrant style anchors for anti-drift RAG
- Evolved LangGraph pipeline (6 nodes)
- Sales agent integration (knowledge_builder + style_anchor_retriever)
- UI in Brand Studio → Esencia → Voz y Personalidad
- 50+ tests including contract compliance verification"
```
