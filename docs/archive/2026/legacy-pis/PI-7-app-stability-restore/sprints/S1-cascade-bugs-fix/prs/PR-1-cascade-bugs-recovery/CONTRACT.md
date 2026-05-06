# CONTRACT — PR-1-cascade-bugs-recovery

> Architect: `nicolify-architect` (Opus 4.7 [1M])
> Run: 2026-05-01 (live `date -u +%Y-%m-%d`)
> Phase: design
> Branch: `development`
> CONTEXT-BRIEF source: ✅ used § 7 + § 8 from `nicolify-context-builder` (Haiku) + self-supplemented Bug #9 docker diagnostics (CONTEXT-BRIEF flagged `[partial]` for runtime).
> Scope decision: **2 PRs paralelos** (split Bug #7 backend + Bug #9 infra). Justified in § 0.

---

## 0. Context Summary

### 0.1 PR identity

- **PR ID**: `PR-1-cascade-bugs-recovery` (PI-7 / S1-cascade-bugs-fix)
- **Bugs in scope**: #7 (brand_data_adapter `model_dump` AttributeError) + #9 (visionarias_litellm exited 127 OCI mount error)
- **User-facing problem**: Telegram bot responde "ocurrió un error técnico interno" en lugar del greeting voice-tenant.
- **Smoke target**: Chris manda "hola" al `visionarias_bot` → bot responde greeting voz Visionarias (tenant `6347e21e-…`, lead Telegram `cb711aea-…`).

### 0.2 Modules touched

| Module | Surface | Type of change |
|---|---|---|
| `backend/src/modules/brand/application/services/brand_data_adapter.py` | application service | Bug #7 fix — wrap SQLA ORM `PersonalityProfileModel` with existing Pydantic `PersonalityProfileDTO` before `model_dump` |
| `backend/tests/modules/brand/application/services/test_brand_data_adapter_pr2.py` | unit tests | RED reproducer + GREEN regression for Bug #7 |
| `docker-compose.yml` (litellm service) | infra | Bug #9 — recreate container; **NO syntax change** (mount syntax is correct, root cause is stale WSL2 bind-mount cache) |
| `docs/pm-nico/current-state/sales-agent.md` | SSoT funcional | post-fix lineage: "LLM call functional → live" |
| `docs/pm-nico/current-state/brand.md` | SSoT funcional | post-fix lineage: "Knowledge adapter → live (PersonalityProfileDTO conversion)" |

### 0.3 Surface → Builder → Auditor mapping (PM uses to spawn correct agents)

| Surface | Builder | Auditor | Skills consulted |
|---|---|---|---|
| `modules/brand/application/services/brand_data_adapter.py` | `nicolify-backend` (Sonnet) | `nicolify-backend-auditor` (Opus) | `backend-expert` + `brand-expert` |
| `backend/tests/modules/brand/**` | `nicolify-backend` (Sonnet) | `nicolify-backend-auditor` (Opus) | `backend-expert` |
| `docker-compose.yml` litellm restart (infra) | **PM ad-hoc** (no builder) | PM verifica `docker compose ps` → `Up healthy` + `:4000/v1/health` 200 | `tessl__graceful-degradation` (deferred — explicit timeout/fallback NOT in scope of this hotfix) |
| Smoke E2E Telegram | **Chris-mediated** post-merge | PM verifica trazas `sales_agent_trace_event.turn_end.status='ok'` + `cost_usd > 0` | n/a |

**Frontend builders/auditors NOT spawned** — PR no toca FE.
**Agentic builders/auditors NOT spawned** — PR no toca `modules/copilot/` ni `modules/sales_agent/` source (sólo lee trazas post-fix).

### 0.4 Skills consulted — decisions taken

| Skill | Decision adoptada |
|---|---|
| `backend-expert` (SOP bug fix Outside-In) | Fix at the deepest layer possible = adapter (line 41 conversion), not the repository (PR-2 shipped 2026-04-30 already returns ORM and is consumed elsewhere — touching repo widens blast radius). |
| `brand-expert` (SOP "Quiero modificar voice/tone/personality") | `PersonalityProfileDTO` ya existe en `backend/src/modules/brand/api/personality.py:45-63` con `ConfigDict(from_attributes=True)`. **EXTEND existing DTO, NO crear nuevo.** PersonalityCompiler regenera runtime — sin cache invalidation. |
| `sales-agent-expert` (downstream impact verify) | `knowledge_builder.build_identity` (line 71) consume `BrandKnowledgeDTO.personality_profile` como `dict | None` → fix transparente downstream. `agent_identity.j2` no requiere cambio. Slot 5 (BRAND_VOICE) sigue leyendo `personality_profile.system_instruction` runtime. |
| `tessl__graceful-degradation` | NOT applied this PR — Bug #7 es bug de tipo, no resilience. Recommendation deferred to backlog: `BrandDataAdapter.get_brand_knowledge` debería envolver en try/except con fallback DTO vacío (current behavior raises → cascade error en sales_agent). PM decide si crea PR follow-up. |

### 0.5 Scope decision — split into 2 PRs (justified)

**Decisión: Bug #7 = builder PR. Bug #9 = PM ad-hoc infra fix (no CONTRACT/builder needed).**

Razones:
1. **Diferente surface owner**: Bug #7 = code change (brand module, builder + auditor + tests). Bug #9 = stale Docker bind-mount cache (PM `docker compose down/up litellm` — zero code).
2. **Diferente blast radius**: Bug #7 toca application service + tests (~30 LOC). Bug #9 = container restart (0 LOC).
3. **Sequencing**: Bug #9 fix INDEPENDENT — `docker compose down litellm && docker compose up -d litellm` resuelve sin tocar Bug #7. Bug #7 fix INDEPENDENT — unit test mock-based no requiere LiteLLM.
4. **Smoke validation requiere AMBOS** — sin LLM stack (Bug #9) NO podemos verify Bug #7 end-to-end vía Telegram. Por eso PM debe ejecutar Bug #9 fix (container restart) **PRIMERO** para des-bloquear smoke, y Bug #7 builder corre en paralelo.

**Order of execution recommendation**:
1. **PM step 0** (immediate, ~1 min): `docker compose down litellm && docker compose up -d litellm` → verify `docker compose ps litellm` shows `Up`. Smoke `curl localhost:4000/v1/health` → 200.
2. **PM spawns builder for Bug #7** (parallel to step 1). Builder writes RED test (mock SQLA `PersonalityProfileModel` → AttributeError reproducer), GREEN fix, regression complete in ~15 min.
3. **PM verifica end-to-end** post-merge: Chris manda "hola" Telegram → bot respond + query `sales_agent_trace_event` for `turn_end.status='ok'` + `sales_agent_llm_call.cost_usd > 0`.

### 0.6 CONTEXT-BRIEF source

✅ Read `CONTEXT-BRIEF.md` (Haiku 4.5, faithfulness=partial). Used § 7 (existing systems) + § 8 (EXTEND-only recommendations) verbatim. Self-supplemented § 11 flagged `[partial]` items via:
- Self-ran `docker compose ps`, `docker logs visionarias_litellm | tail -100`, `docker inspect visionarias_litellm` → § 7 row "LiteLLM mount" enriched with **OCI runtime root cause confirmed** (stale bind-mount cache, not mount syntax).
- Self-ran `find backend/src/modules/brand/api/dto -name "*.py"` + read `brand/api/personality.py` → confirmed `PersonalityProfileDTO` exists at `:45-63` with `ConfigDict(from_attributes=True)`.

### 0.7 Cross-session overlap check (M7 parallel-sessions)

| Active session | PR | Files modified | Collision risk | Mitigation |
|---|---|---|---|---|
| PI-3 sales-agent-improvement | discovery | unknown (no in-progress files) | LOW | none |
| PI-4-brand-evolutive-maintenance / S1 / **PR-1-drop-buyer-persona-fields** | in-progress | `brand/domain/buyer_persona.py`, `brand/infrastructure/models/buyer_persona_model.py`, `brand/api/buyer_personas.py`, `brand/infrastructure/repositories/buyer_persona_repository.py` | **MEDIUM** — same module (brand), different files | M8 rule applies: no overlap on `brand_data_adapter.py` ni `personality_repository.py`. PI-7 PR-1 builder **PROHIBIDO tocar buyer_persona files**. Coordinate merge order: PI-4 (migration drop col) and PI-7 (adapter fix) can merge in **either order** — independent. |
| PI-5-copilot-multicanal-telegram / S2 | active (sales_agent + copilot wiring) | sales_agent + copilot | LOW — no `brand/` overlap | none, but PR-1 fix removes the Telegram bot blocker → unblocks PI-5 smoke. |

**Action**: PI-7 builder receives `brand/application/services/brand_data_adapter.py` + `tests/modules/brand/application/services/test_brand_data_adapter_pr2.py` as PRIMARY paths. Read-only on every other file. Extend, no destroy.

### 0.8 pm-nico/current-state files affected (post-merge)

- `docs/pm-nico/current-state/brand.md` — `Knowledge adapter (Bug #7)` row state: `broken` → `live` + lineage ref `PI-7 S1 PR-1` commit.
- `docs/pm-nico/current-state/sales-agent.md` — `LLM call functional` row state: `degraded` → `live` + lineage refs (Bug #7 + Bug #9 both fixed).

### 0.9 Architecture fitness gates that must keep passing

- `backend/tests/architecture/test_response_model_compliance.py` — no impact (no FastAPI route added/modified; `BrandKnowledgeDTO` is a Pydantic model, route unchanged).
- `backend/tests/architecture/test_tenant_isolation_*.py` — no impact (adapter signature unchanged; tenant_id filter preserved).
- `backend/tests/architecture/test_extraction_orchestrator_inheritance.py` — no impact (BrandDataAdapter is not an extraction orchestrator).
- `backend/tests/modules/copilot/application/suggestions/providers/test_brand_provider.py` — must continue green (mocks `BrandKnowledgeDTO` directly — fix is transparent at adapter level).
- `backend/tests/modules/sales_agent/test_knowledge_builder_personality.py` — must continue green (mocks `BrandKnowledgeDTO` with `personality_profile=dict | None` — fix preserves contract).
- `backend/tests/modules/sales_agent/test_knowledge_builder_legal.py` — must continue green (same mocking pattern).

---

## 1. Domain Entities

**No new domain entities.** Bug #7 is a serialization bug at the adapter boundary — domain layer untouched.

Existing entities consumed (read-only reference):
- `PersonalityProfileModel` (SQLAlchemy ORM) — `backend/src/modules/brand/infrastructure/models/personality_model.py:14`. Returns from `PersonalityProfileRepository.get_active(tenant_id=...)`. Has columns `id, tenant_id, dimensions JSONB, linguistic_patterns JSONB, sample_exchanges JSONB, system_instruction Text, ...`. Does NOT inherit `pydantic.BaseModel`.
- `PersonalityProfileDTO` (Pydantic v2 DTO — **EXISTS, will be reused**) — `backend/src/modules/brand/api/personality.py:45-63`. `model_config = ConfigDict(from_attributes=True)`. Fields: `id, name, profile_type, preset_key, is_active, dimensions, linguistic_patterns, sample_exchanges, negative_constraints, system_instruction, source_metadata, anchor_count, created_at, updated_at`.

---

## 2. SQLAlchemy 2.0 Models

**No new models.** No migration needed.

---

## 3. Pydantic v2 DTOs

**No new DTOs.** Reuses `PersonalityProfileDTO` already defined.

**Cross-module port DTO unchanged**: `BrandKnowledgeDTO` (`backend/src/shared/links/ports/brand.py:26-31`) keeps shape:
```python
class BrandKnowledgeDTO(BaseModel):
    brand_data: dict = {}
    avatars: list[dict] = []
    personality_profile: dict | None = None  # ← unchanged shape — fix preserves dict
```

The fix is purely **how `personality_profile` dict is constructed**: instead of `personality_profile.model_dump(mode="json")` on an ORM model (which lacks `model_dump`), wrap with `PersonalityProfileDTO.model_validate(personality_profile).model_dump(mode="json")`.

**Decision rule (brand-expert SOP)**: `PersonalityProfileDTO.model_config = ConfigDict(from_attributes=True)` enables ORM → DTO conversion via `model_validate(orm_instance)`. This is the canonical Pydantic v2 path for SQLA→Pydantic.

---

## 4. API Routes

**No route changes.** Bug #7 is below the API boundary.

---

## 5. TypeScript Types (Frontend)

**No FE changes.** PR backend-only.

---

## 6. Repository Interfaces

**Unchanged.** `PersonalityProfileRepository.get_active(tenant_id)` continues to return `PersonalityProfileModel | None` (SQLA ORM). Adapter is responsible for ORM→DTO conversion.

**Why not change repository return type to DTO?** PR-2-pure-expansion-providers (commit `97780627`, 2026-04-30) shipped `get_active_personality_profile_present` consuming the same ORM. Other consumers in `personality_service.py` may also rely on ORM identity for relationships. Touching repo widens blast radius beyond the bug. Per `backend-expert` SOP "Bugs (Outside-In)": fix at the deepest layer possible **without expanding scope**. Adapter is the correct boundary.

---

## 7. Application Services — Fix Specification

### 7.1 Target file

`backend/src/modules/brand/application/services/brand_data_adapter.py`

### 7.2 Current shape (broken — lines 37-47)

```python
def get_brand_knowledge(self, tenant_id: UUID) -> BrandKnowledgeDTO:
    """Return pre-serialized brand data for the agent identity builder."""
    brand = self.brand_repo.get_settings(tenant_id)
    avatars = self.avatar_repo.get_by_tenant(tenant_id)
    personality_profile = self.personality_repo.get_active(tenant_id=tenant_id)

    return BrandKnowledgeDTO(
        brand_data=brand.model_dump(mode="json") if brand else {},
        avatars=[a.model_dump(mode="json") for a in avatars] if avatars else [],
        personality_profile=personality_profile.model_dump(mode="json") if personality_profile else None,
        #                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        #                   AttributeError: 'PersonalityProfileModel' object has no attribute 'model_dump'
    )
```

### 7.3 Target shape (fixed)

```python
def get_brand_knowledge(self, tenant_id: UUID) -> BrandKnowledgeDTO:
    """Return pre-serialized brand data for the agent identity builder."""
    brand = self.brand_repo.get_settings(tenant_id)
    avatars = self.avatar_repo.get_by_tenant(tenant_id)
    personality_profile = self.personality_repo.get_active(tenant_id=tenant_id)

    # PersonalityProfileRepository.get_active returns SQLA ORM
    # (PersonalityProfileModel) — convert via existing Pydantic DTO
    # (`brand/api/personality.py::PersonalityProfileDTO`,
    # `ConfigDict(from_attributes=True)`) before serialising.
    # Bug #7 fix — PR-1 PI-7 S1 (2026-05-01).
    personality_dict: dict | None = None
    if personality_profile is not None:
        personality_dict = PersonalityProfileDTO.model_validate(
            personality_profile,
        ).model_dump(mode="json")

    return BrandKnowledgeDTO(
        brand_data=brand.model_dump(mode="json") if brand else {},
        avatars=[a.model_dump(mode="json") for a in avatars] if avatars else [],
        personality_profile=personality_dict,
    )
```

### 7.4 Import to add (top of file)

```python
from src.modules.brand.api.personality import PersonalityProfileDTO
```

**DDD note** — application layer importing from api layer is **acceptable for DTO reuse** (DTOs are public surface of the module). Confirmed via `backend-expert` reference `architecture-rules.md`: api/ layer holds Pydantic DTOs; application/ may import them when no domain DTO exists. Alternative — define `PersonalityProfileDTO` in `brand/domain/personality.py` — would require shipping a new module-level DTO and migration of all current callers. Out of scope for hotfix.

If `nicolify-backend-auditor` flags this import as DDD violation, the auditor MUST cite the specific arch test it fails. The test `test_no_cross_module_imports.py` allows `application → api` within the same module (verified PI-2 S2 PR-2 commits).

### 7.5 Idempotency — N/A

Pure read operation, no writes to side-effect.

---

## 8. Agentic Surfaces

**N/A — PR no toca `modules/copilot/` ni `modules/sales_agent/` source.**

Downstream impact (read-only, transparent):
- `sales_agent.knowledge_builder.build_identity` (line 71): receives `BrandKnowledgeDTO` with `personality_profile: dict | None` — shape unchanged → no template rebuild.
- `copilot.suggestions.providers.brand` (line 86): receives same DTO — no change.
- `copilot.suggestions.providers.copilot` (line 171): receives same DTO — no change.
- `agent_identity.j2` template: renders `brand_knowledge.personality_profile.system_instruction` defensively (slot 5 BRAND_VOICE) — dict access unchanged.

**Slot 5 cache prefix integrity preserved**: `personality_profile.system_instruction` is the cache anchor for sales_agent (compiler v2). The fix produces an **identical dict shape** as the broken code intended → no cache invalidation, no goldens drift, no slot reorder.

---

## 9. Migration Notes

**No migrations required.** Pure code fix at application layer.

---

## 10. File Structure

```
backend/src/modules/brand/
├── application/
│   └── services/
│       └── brand_data_adapter.py       MODIFIED — Bug #7 fix (lines 41, 46-50, +1 import)
├── api/
│   └── personality.py                  READ-ONLY (PersonalityProfileDTO consumed)
└── infrastructure/
    └── models/
        └── personality_model.py        READ-ONLY (PersonalityProfileModel ORM)

backend/tests/modules/brand/application/services/
└── test_brand_data_adapter_pr2.py      MODIFIED — append RED+GREEN regression class

docker-compose.yml                       READ-ONLY (no edit — root cause is stale WSL2 bind-mount cache, not syntax)

docs/pm-nico/current-state/
├── brand.md                             MODIFIED post-merge — Knowledge adapter row → live
└── sales-agent.md                       MODIFIED post-merge — LLM call functional row → live
```

---

## 11. Cross-Cutting Concerns

| Concern | Status |
|---|---|
| **Tenant isolation** | ✅ preserved — `personality_repo.get_active(tenant_id=tenant_id)` already filters tenant. Adapter signature unchanged. |
| **Currency** | N/A — no monetary fields. |
| **Master data (UTC + tenant locale)** | N/A — `created_at/updated_at` already `DateTime(timezone=True)` in PersonalityProfileModel. DTO inherits. |
| **Spanish neutro LatAm** | N/A — no user-facing strings. |
| **PII** | ✅ `BrandKnowledgeDTO.personality_profile` already `dict` (not raw ORM). DTO drops nothing previously not exposed. `system_instruction` is voice config, NOT PII. |
| **Native-first dev** | ✅ tests run native: `cd backend && .venv/bin/pytest tests/modules/brand/application/services/test_brand_data_adapter_pr2.py -v` |
| **structlog** | N/A — no log statements added. |
| **TDD** | ✅ § 14 specifies RED test FIRST. |
| **Anti-duplication** | ✅ verified — no parallel layer created. EXTEND existing `PersonalityProfileDTO`. |

---

## 12. Architecture Fitness Impact

**Gates that will run** (auditor consumes both this contract + `gate-output.json` from `nicolify-gate-runner` Haiku):

| Gate | Expected outcome | Notes |
|---|---|---|
| `tests/architecture/test_response_model_compliance.py` | PASS unchanged | No FastAPI route touched |
| `tests/architecture/test_no_cross_module_imports.py` | PASS unchanged | Import is intra-module (`brand/application` → `brand/api`) |
| `tests/architecture/test_tenant_isolation_*.py` | PASS unchanged | tenant_id filter preserved at repo |
| `tests/architecture/test_ddd_layer_purity.py` | PASS — verify intra-module application→api allowed | If FAIL, auditor must cite specific assertion (architect's fallback: define DTO duplicated in `brand/domain/personality.py` — heavier scope, escalate to PM) |
| `tests/architecture/test_budget_guard_pre_llm_call.py` | PASS unchanged | No LLM call surface added |
| `tests/modules/brand/application/services/test_brand_data_adapter_pr2.py` | NEW class GREEN | RED reproducer + GREEN regression |
| `tests/modules/copilot/application/suggestions/providers/test_brand_provider.py` | PASS unchanged | Mock BrandKnowledgeDTO directly — fix transparent |
| `tests/modules/sales_agent/test_knowledge_builder_personality.py` | PASS unchanged | Mock BrandKnowledgeDTO directly |
| `tests/modules/sales_agent/test_knowledge_builder_legal.py` | PASS unchanged | Mock BrandKnowledgeDTO directly |

**Allowlist updates**: NONE expected. Allowlists shrink only — this PR does not introduce a new violation requiring allowlist entry.

---

## 13. pm-nico/current-state Updates Required (post-merge by PM)

**`docs/pm-nico/current-state/brand.md`** — section "Capacidades" row "Knowledge adapter (Bug #7)":
- Before: `**broken** | BrandDataAdapter.get_brand_knowledge line 46 calls .model_dump() en SQLA ORM model, not Pydantic DTO`
- After: `**live** | BrandDataAdapter wraps PersonalityProfileModel → PersonalityProfileDTO via from_attributes before serialising. Lineage: PI-7 S1 PR-1 commit <hash> 2026-05-01.`

**`docs/pm-nico/current-state/sales-agent.md`** — row "LLM call functional":
- Before: `**degraded** | Bug #9 — visionarias_litellm:4000 exited mount conflict. Bug #7 breaks knowledge_builder identity construction.`
- After: `**live** | Bug #7 fixed (brand adapter ORM→DTO conversion, PI-7 S1 PR-1). Bug #9 fixed (PM container restart 2026-05-01 — stale WSL2 bind-mount cache cleared). Verified end-to-end Telegram smoke <hash>.`

---

## 14. Test Surfaces (TDD-mandatory)

### 14.1 RED reproducer (write FIRST)

`backend/tests/modules/brand/application/services/test_brand_data_adapter_pr2.py` — **append new class** at bottom:

```python
class TestGetBrandKnowledgeHandlesORMPersonalityProfile:
    """Bug #7 regression — PI-7 S1 PR-1 (2026-05-01).

    PersonalityProfileRepository.get_active returns SQLA ORM
    (PersonalityProfileModel), NOT Pydantic. Adapter must convert
    via PersonalityProfileDTO.model_validate before model_dump.
    """

    def test_get_brand_knowledge_with_orm_personality_returns_dict(self) -> None:
        """RED: real ORM instance via from_attributes → dict serialisation succeeds."""
        from datetime import datetime, timezone
        from uuid import uuid4

        from src.modules.brand.application.services.brand_data_adapter import (
            BrandDataAdapter,
        )
        from src.modules.brand.infrastructure.models.personality_model import (
            PersonalityProfileModel,
        )

        # Arrange — real ORM instance (NOT MagicMock — would mask the bug)
        orm_profile = PersonalityProfileModel(
            id=uuid4(),
            tenant_id=_TENANT,
            name="Visionarias",
            profile_type="preset",
            preset_key="sage",
            is_active=True,
            dimensions={"warmth": 0.8, "energy": 0.5},
            linguistic_patterns={"greeting": "Hola"},
            sample_exchanges=[],
            negative_constraints=[],
            system_instruction="Sos Visionarias.",
            source_metadata={},
            anchor_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        mock_db = MagicMock()
        mock_brand_repo = MagicMock()
        mock_brand_repo.get_settings.return_value = None
        mock_avatar_repo = MagicMock()
        mock_avatar_repo.get_by_tenant.return_value = []
        mock_pers_repo = MagicMock()
        mock_pers_repo.get_active.return_value = orm_profile

        with patch(
            "src.modules.brand.application.services.brand_data_adapter.BrandRepository",
            return_value=mock_brand_repo,
        ), patch(
            "src.modules.brand.application.services.brand_data_adapter.AvatarRepository",
            return_value=mock_avatar_repo,
        ), patch(
            "src.modules.brand.application.services.brand_data_adapter.PersonalityProfileRepository",
            return_value=mock_pers_repo,
        ):
            adapter = BrandDataAdapter(mock_db)
            knowledge = adapter.get_brand_knowledge(_TENANT)

        # Assert
        assert knowledge.personality_profile is not None
        assert isinstance(knowledge.personality_profile, dict)
        assert knowledge.personality_profile["name"] == "Visionarias"
        assert knowledge.personality_profile["dimensions"]["warmth"] == 0.8
        assert knowledge.personality_profile["system_instruction"] == "Sos Visionarias."

    def test_get_brand_knowledge_with_no_personality_returns_none(self) -> None:
        """get_active returns None → personality_profile field is None."""
        from src.modules.brand.application.services.brand_data_adapter import (
            BrandDataAdapter,
        )

        mock_db = MagicMock()
        mock_brand_repo = MagicMock()
        mock_brand_repo.get_settings.return_value = None
        mock_avatar_repo = MagicMock()
        mock_avatar_repo.get_by_tenant.return_value = []
        mock_pers_repo = MagicMock()
        mock_pers_repo.get_active.return_value = None

        with patch(
            "src.modules.brand.application.services.brand_data_adapter.BrandRepository",
            return_value=mock_brand_repo,
        ), patch(
            "src.modules.brand.application.services.brand_data_adapter.AvatarRepository",
            return_value=mock_avatar_repo,
        ), patch(
            "src.modules.brand.application.services.brand_data_adapter.PersonalityProfileRepository",
            return_value=mock_pers_repo,
        ):
            adapter = BrandDataAdapter(mock_db)
            knowledge = adapter.get_brand_knowledge(_TENANT)

        assert knowledge.personality_profile is None
```

### 14.2 RED → GREEN order

1. Append the test class above to existing test file.
2. Run native: `cd backend && .venv/bin/pytest tests/modules/brand/application/services/test_brand_data_adapter_pr2.py::TestGetBrandKnowledgeHandlesORMPersonalityProfile -v`
3. Expect RED: `AttributeError: 'PersonalityProfileModel' object has no attribute 'model_dump'`.
4. Apply fix § 7.3 + import § 7.4.
5. Run native again → GREEN.
6. Run full module suite: `cd backend && .venv/bin/pytest tests/modules/brand/ tests/modules/sales_agent/test_knowledge_builder_personality.py tests/modules/sales_agent/test_knowledge_builder_legal.py tests/modules/copilot/application/suggestions/providers/ -x -q` → ALL GREEN.
7. Run arch fitness gates: `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short` → ALL GREEN.

### 14.3 Smoke E2E (post-merge, PM + Chris)

1. PM ejecuta Bug #9 fix:
   ```bash
   docker compose -f /home/chris/AISALESHT/docker-compose.yml down litellm
   docker compose -f /home/chris/AISALESHT/docker-compose.yml up -d litellm
   docker compose ps litellm   # expect: Up
   docker exec visionarias_litellm wget -q -O - http://localhost:4000/health 2>&1 | head -5
   # expect: 200 OK or healthcheck-equivalent JSON
   ```
2. PM verifica brand adapter fix merged en `development`:
   ```bash
   git -C /home/chris/AISALESHT log --oneline -3 backend/src/modules/brand/application/services/brand_data_adapter.py
   ```
3. PM restart backend container (pick up code change):
   ```bash
   docker compose -f /home/chris/AISALESHT/docker-compose.yml restart api_dev
   ```
4. Chris manda "hola" al `visionarias_bot` Telegram.
5. PM verifica trazas tenant `6347e21e-8112-4aa1-80d3-6adaa73bf6f9`:
   ```sql
   SELECT created_at, name, status, duration_ms, LEFT(data::text, 200)
   FROM sales_agent_trace_event
   WHERE tenant_id = '6347e21e-8112-4aa1-80d3-6adaa73bf6f9'
     AND created_at > NOW() - INTERVAL '5 minutes'
   ORDER BY created_at DESC LIMIT 20;

   SELECT COUNT(*) AS llm_calls, SUM(cost_usd) AS total_cost
   FROM sales_agent_llm_call
   WHERE tenant_id = '6347e21e-8112-4aa1-80d3-6adaa73bf6f9'
     AND created_at > NOW() - INTERVAL '5 minutes';
   ```
   Expect: `turn_end status='ok'`, `llm_calls >= 1`, `total_cost > 0`.

### 14.4 Test surface coverage matrix

| Layer | File | Test type |
|---|---|---|
| application service | `tests/modules/brand/application/services/test_brand_data_adapter_pr2.py` | unit (RED→GREEN regression) |
| sales_agent integration | `tests/modules/sales_agent/test_knowledge_builder_personality.py` | already covers DTO contract; verify still GREEN post-fix |
| copilot integration | `tests/modules/copilot/application/suggestions/providers/test_brand_provider.py` | already covers DTO contract; verify still GREEN |
| arch fitness | `tests/architecture/` (full suite) | ratchet |
| smoke E2E | manual Chris-mediated Telegram | post-merge, PM verifies trazas |

---

## 15. Research Notes (DATE-AWARE)

| Topic | Source | Accessed | Takeaway | Why over alternatives |
|---|---|---|---|---|
| Pydantic v2 ORM → DTO conversion | https://docs.pydantic.dev/latest/concepts/models/#arbitrary-class-instances + `brand-expert` skill SOP | 2026-05-01 | `model_config = ConfigDict(from_attributes=True)` + `Model.model_validate(orm_instance)` is canonical Pydantic v2 path. Replaces v1 `from_orm()`. | Existing `PersonalityProfileDTO` already uses this config — zero new code, zero parallel layer. |
| Docker WSL2 stale bind-mount cache | https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/topics/#bind-mounts-not-mounting + observed runtime error: `OCI runtime create failed ... not a directory` for a path that IS a file | 2026-05-01 | WSL2 + Docker Desktop bind-mount cache (`/run/desktop/mnt/host/wsl/docker-desktop-bind-mounts/Ubuntu/<hash>`) can become stale when WSL distro restarts. Fix: container recreate (down + up) forces re-resolution from compose. NO syntax change required. | Verified via `docker inspect`: Mounts.Source = `/home/chris/aisalesht/litellm_config.yaml` (lowercase, both paths resolve identically per `readlink -f` to `/home/chris/AISALESHT`). File exists, is regular file. Docker's internal bind-mount stub is stale, not the host path. |
| LangGraph patterns | NOT applicable this PR | — | — | No agentic surface change |
| FastAPI patterns | https://fastapi.tiangolo.com/tutorial/response-model/ | 2026-05-01 | `response_model=` mandatory — no impact this PR (no route added) | — |
| `tessl__graceful-degradation` Iron Rule | bundled skill | 2026-05-01 | Every external call needs timeout + fallback. **Recommendation deferred**: `BrandDataAdapter.get_brand_knowledge` should wrap repo calls in try/except returning empty `BrandKnowledgeDTO()` fallback so a single corrupt row does NOT cascade an AttributeError to the agent. PR follow-up, NOT in scope here. | Bug #7 root cause is type mismatch, not transient failure. Adding fallback now bundles unrelated change. |

**Knowledge cutoff disclosure**: Opus 4.7 cutoff = January 2026. Topics researched here (Pydantic v2, Docker WSL2 bind-mount cache, FastAPI) are stable since well before cutoff. No live WebSearch required. Research backed by direct file inspection of canonical implementations in repo.

---

## 16. Open Questions for PM

1. **Auditor scope for Bug #9 ad-hoc fix**: Should `nicolify-backend-auditor` verify Bug #9 container is `Up healthy` before issuing PASS verdict on the PR? Or is that PM's smoke responsibility outside the auditor pipeline? (Recommendation: PM responsibility — auditor scope = code only.)

2. **Follow-up resilience PR**: Should we open a backlog item for `BrandDataAdapter.get_brand_knowledge` to wrap each repo call in try/except returning empty `BrandKnowledgeDTO()` (per `tessl__graceful-degradation` Iron Rule)? Current behavior raises uncaught → cascade fault. Defer or schedule?

3. **PI-4 PR-1 merge order coordination**: PI-4-brand-evolutive-maintenance/S1/PR-1 is also `in-progress` on `development` modifying `buyer_persona*` files in same module. Files do NOT overlap with this PR's `brand_data_adapter.py`, but `tests/architecture/` ratchet may shrink concurrently. Recommendation: merge in **commit order** (whoever lands first wins; second adapts arch test allowlist if needed). No hard blocker.

4. **`docker compose down litellm` risk**: Healthcheck logs show `curl: executable file not found in $PATH` — the LiteLLM image doesn't ship `curl`. Healthcheck has been failing all along (silent). Recommendation: file backlog item to switch healthcheck to `wget` or `python -c "import urllib.request; urllib.request.urlopen('http://localhost:4000/health')"`. Out of scope for this hotfix.

5. **Lazy import pattern for `PersonalityProfileDTO`**: An alternative to top-level import is lazy import inside `get_brand_knowledge` to avoid potential circular import (`brand/application` → `brand/api` → `brand/application/services/personality_service`). Recommendation: top-level import is fine because `brand/api/personality.py` only imports `PersonalityService` at module top, and `PersonalityService` does NOT import `BrandDataAdapter` (verified via grep). If builder hits circular import at runtime, fall back to lazy import inside the method.

---

<!-- @pm: CONTRACT.md ready. Surface mapping declared in § 0. Próximo paso: ejecutar prompts/02-builder-backend.md o ejecutar /pm "PR-1 architect done" para review. -->
