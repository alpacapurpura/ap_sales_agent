# PR-2-pure-expansion-providers — CONTRACT

> Owner: `nicolify-architect` (architect-empowered, ZERO open questions). Backend builder consume en serial. Audit obligatorio post-merge.

## Meta

| Campo | Valor |
|---|---|
| Architect-empowered | sí, ZERO open questions |
| Fecha | 2026-04-30 |
| Owner | nicolify-architect |
| PR padre | PR-2-pure-expansion-providers |
| Sprint | S2-copilot-cero-deuda-stack |
| PI | PI-2-copilot-improvement |
| Skills consultadas | `copilot-expert` (anchor cap 36/36 — reusar `[COPILOT-SUGGESTIONS-ENGINE]`, ratchet `copilot→módulo` 22 frozen, best-effort observability), `brand-expert` (BrandSettings JSONB shape, BuyerPersona repo, PersonalityProfile activeness check, SSoT field-contract reactive), `sales-agent-expert` (§3 protected: NO tocar Closer Studio / BufferService / OutputManager / enrollment lifecycle / FollowUp; solo LECTURA enrollments + messages tablas), `backend-expert` (Pydantic v2 ConfigDict, SA 2.0 select(), tenant_id filter required, structlog kwargs) |
| Anchor | `[COPILOT-SUGGESTIONS-ENGINE]` (existente — cap 36/36, NO bumpear) |
| current-state file impactado | `docs/pm-nico/current-state/copilot.md` (PM update post-merge — actualizar cap "Suggestion engine + provider registry" con 4 providers + lineage S2 PR-2) |
| Arch tests sensitivos | `test_no_new_copilot_module_imports.py` (ratchet 22 frozen — providers DEBEN consumir `shared/links/ports/*`, NUNCA `import src.modules.{brand,sales_agent}.*` desde `copilot/`), `test_copilot_anchors.py` (cap 36/36, sin nuevo anchor), `test_copilot_provider_compliance.py`, `test_copilot_registry.py`, `test_api_contracts.py` (no afecta — sin endpoint nuevo) |
| Coordinación PR-1 | PR-1 expone `POST /copilot/suggestions` consumiendo `engine.get_suggestions(ctx)`. PR-2 agrega 3 providers + reach al engine. Endpoint NO cambia shape. PR-1 contract DTOs intactos. PR-1 puede mergear antes/después de PR-2 sin coupling shape. |

## 0. Context Summary

### Estado pre-PR (verificado con grep + read directo, NO hipótesis)

| Surface | Estado | Path |
|---|---|---|
| `SuggestionEngine.get_suggestions(ctx) -> (chips, breakdown, latency_ms)` | live, sync, best-effort interno (per-provider try/except), confidence DESC + provider_priority DESC sort, cap `_DEFAULT_MAX_TOTAL=5` | `backend/src/modules/copilot/application/suggestions/engine.py:30` |
| `SuggestionEngine.register(provider)` | idempotent same-id-same-instance no-op; ValueError on conflict (mismo id, instancia distinta) | `engine.py:45` |
| Route prefix matching | `if provider.applies_to_routes and ctx.current_route is not None: any(ctx.current_route.startswith(p) for p in provider.applies_to_routes)`. Si `applies_to_routes=()` (empty) → siempre activo. Si `applies_to_routes` set + `current_route is None` → skip. | `engine.py:77-82` |
| `OfferSuggestionProvider` | live, `provider_id="offer"`, `provider_priority=0`, `applies_to_routes=("offer-studio",)`, 4 reglas: (1) no offers → "Crea tu primera oferta"; (2) HIGH_TICKET → 3-tier pricing; (3) RECURRING_BILLING → billing config; (4) IS_LEAD_MAGNET → vincular core; (5) `promise.headline` incomplete → variantes; (6) `detect_lead_magnet_without_core()` → vincular | `providers/offer.py` |
| `OfferSuggestionReader` | sync read-only, opens `SessionLocal` (provider-owned lifecycle), tenant-scoped, consume via `shared/links/ports/offer.py::get_offer_repository + get_offer_type_preset`. **Pattern de referencia para nuevos readers.** | `application/services/offer_suggestion_reader.py` |
| `get_default_engine()` | lazy singleton + Lock thread-safe + `_bootstrap_builtin(engine)` registra solo `OfferSuggestionProvider`. **3 nuevos providers se agregan AQUÍ.** | `registry.py:24-50` |
| `_reset_for_tests()` | live — tests fixture autouse limpia singleton entre runs | `registry.py:53` |
| `Suggestion.__post_init__` | invariantes: `confidence ∈ [0,1]`, `len(label) ≤ 60`, label+prompt non-empty stripped | `domain/suggestion.py:68-78` |
| `SuggestionContext` | frozen dataclass, slots: tenant_id (req), user_id, conversation_id, current_route, recent_message_ids tuple, incomplete_fields tuple, locale="es" | `domain/suggestion.py:26-41` |
| `SuggestionCategory` StrEnum | `FOLLOWUP`, `ACTION`, `CLARIFY`, `NAV` | `domain/suggestion.py:14-23` |
| `shared/links/ports/brand.py::BrandDataPort` + `create_brand_data_port(db)` | live — provee `get_brand_knowledge(tenant_id) -> BrandKnowledgeDTO{brand_data: dict, avatars: list, personality_profile: dict\|None}`. **`brand_data` es BrandSettings.model_dump(mode="json").** | `shared/links/ports/brand.py:34-71` |
| `shared/links/ports/sales_agent.py` | **NO EXISTE** — gap a llenar (raw read port nuevo, no infra-heavy) |
| `BrandRepository.get_settings(tenant_id) -> BrandSettings` | live, sync, retorna BrandSettings(model_validate JSONB) o BrandSettings() vacío si tenant ausente | `brand/infrastructure/repositories/brand_repository.py:27-55` |
| `BuyerPersonaRepository.list_by_tenant(tenant_id, scope=None) -> list[BuyerPersona]` | live, soft-delete filter, scope optional | `brand/infrastructure/repositories/buyer_persona_repository.py:79-103` |
| `PersonalityProfileRepository.get_active(*, tenant_id) -> PersonalityProfileModel \| None` | live — retorna profile activo (is_active + offer_id IS NULL + avatar_id IS NULL + deleted_at IS NULL) | `brand/infrastructure/repositories/personality_repository.py:194-204` |
| `EnrollmentRepository.list_all(tenant_id, *, status=None, ...)` | live, list_by_offer / list_waitlist / list_all / get_by_id / get_by_conversation. Filter chain `tenant_id` mandatory. | `sales_agent/infrastructure/repositories/enrollment_repository.py:175-196` |
| `MessageRepository.get_history(lead_id, tenant_id, limit=50)` | live — pero filtra por `lead_id` (user_id), no por timestamp ni tenant-wide. **Para "no leads en últimas 24h" necesitamos query custom o nuevo método agregado.** Decisión: query directa por SA reader sobre `MessageModel` con filtro `created_at > now-24h + tenant_id` (sin método nuevo en repo, evita scope creep en módulo §3). | `sales_agent/infrastructure/repositories/message_repository.py:53-73` |
| `MessageModel` | tabla `messages_sales_agent` (verificar nombre real), columns: `tenant_id` UUID nullable=True index, `user_id`, `created_at` TIMESTAMPTZ server_default | `sales_agent/infrastructure/models/message_model.py` |
| `EnrollmentModel` | tabla `enrollments`, indices: tenant + offer + edition + contact + status + waitlist + conversation. `created_at` no listed → **verificar BaseEntity Mixin provee created_at** | `sales_agent/infrastructure/models/enrollment_model.py` |
| `_engine_suggestions_for_context(tenant_id, current_route=None, incomplete_fields=(), max_hints=3) -> list[str]` | live helper en `offer_section_tools.py:30`. Llama engine + extrae `[s.label for s in chips[:max_hints]]`. Best-effort try/except. | `tools/offer_section_tools.py:30-63` |
| `offer_section_tools.py` line 163 — único `"suggestions": [hint]` literal hardcoded | EN `_no_data_response(section_slug, hint) -> str`: serializa JSON `{"section_slug": ..., "draft_fields": {}, "suggestions": [hint], "confidence": 0.0, "citations": []}`. **NO es smart-chip — es status-message del tool de regreso al LLM.** Conflate semántico = deuda S1. | `tools/offer_section_tools.py:155-167` |
| Otros `suggestions =` literales | `_ok_response(section_slug, draft_fields, suggestions, confidence, citations)` — `suggestions` es PARÁMETRO del helper, NO literal. Cada tool construye `suggestions: list[str]` localmente (líneas 257, 374, 474, 551, 629, 683, 827, 891, 960, 1027). **NO son hardcoded literals — son contenido derivado del tool.** Mantener (no mezclar tool output con engine output, ver D-7). | `tools/offer_section_tools.py` múltiples |
| `module_registry.get_module_registry()` | live, derived from `discover_providers()` — devuelve `dict[module_id, ModuleDescriptor]` con keywords, route_prefix, model_class. **CopilotSuggestionProvider transversal puede consumir registry para detectar "módulos vacíos".** | `copilot/domain/module_registry.py` |
| Ratchet `copilot → módulo` 22 entries frozen | Brand entries: 8 archivos. Sales_agent entries: **0** (ratchet PROHÍBE nuevo cross-module import desde `copilot/` a `sales_agent/`). | `tests/architecture/test_no_new_copilot_module_imports.py:50-77` |

### Skills consultadas — decisiones tomadas

- **copilot-expert**: Anchor cap 36/36 → reusar `[COPILOT-SUGGESTIONS-ENGINE]` en docstring header de cada provider nuevo, NO bumpear cap. Engine es sync — providers son sync (mismo pattern OfferSuggestionProvider), wrap async vive en `api/suggestions.py` (PR-1). Ratchet `copilot → sales_agent` = 0 entries → providers DEBEN consumir port `shared/links/ports/sales_agent.py` (a crear). Best-effort observability: cada provider try/except interno con structlog warning + return `[]`. Sin invadir §3-protected.
- **brand-expert**: BrandSettings vive en `Tenant.config_json["brand_settings"]`. Sub-objetos: `identity` (con brand_name, tagline, voice_tone DEPRECATED, business_types removido a tenant_profile BC), `positioning` (con UVP, brand_essence, insight, RTB), `narrative` (StoryBrand: hero/problem/guide/plan/cta/outcome/one_liner), `brand_personality` (Jung archetype + core_values + traits), `story`, `strategy` (methodology), `team[]`, `testimonials[]`, `authority_vault[]`, `communication_assets`, `visuals`. PersonalityProfile (3-pilar engine) vive separado en `personality_profiles` table — `get_active()` retorna profile completo o None. Buyer personas multi-persona via `buyer_personas` table. **Heurística completion ratio**: contar campos populados de bloques clave (identity.brand_name + positioning.UVP + narrative.one_liner + brand_personality.archetype + ≥1 buyer_persona + personality_profile activo) sobre 6 → ratio ∈ [0,1]. **NO TOCAR** `voice_tone` (DEPRECATED), `BrandStrategy.unique_value_proposition` (DEPRECATED, migra a positioning).
- **sales-agent-expert**: §3 PROTECTED — NO tocar Closer Studio API/WS, BufferService, OutputManager.process_response chunking, enrollment lifecycle (create/update), webhook adapters, FollowUp engine, PromptVersionModel, agent_state_checkpoint schema. **Solo LECTURA** sobre tablas: `enrollments` (status+created_at+offer_id), `messages_sales_agent` (created_at+tenant_id). Heurísticas focus: pipeline observation (no leads recientes, conversion rate baja, agent paused). Si futura heurística requiere computar CONVERSION_RATE → consumir `mv_daily_llm_cost_per_tenant_v2` o tabla agregada existente, NUNCA recompute en provider. **Voz**: provider chips emiten en español neutro LatAm (chip → propmt para copilot UI, NO output del sales_agent — `.claude/rules/spanish-text.md` SÍ aplica al copilot suggestions).
- **backend-expert**: Pydantic v2 `ConfigDict` (no inner Config). SA 2.0 `select(Model).where(...)`. `tenant_id` filter required en cada query. structlog `event_name=` (no kwarg `event=`). Lazy imports dentro de métodos (no module-level cross-module).

## 1. Decisions (numeradas, justificadas — ARCHITECT-EMPOWERED)

### D-1: 3 providers nuevos en archivos separados — paridad con `OfferSuggestionProvider`

**Veredicto**: 3 nuevos archivos en `backend/src/modules/copilot/application/suggestions/providers/`:
- `brand.py` → `BrandSuggestionProvider`
- `sales_agent.py` → `SalesAgentSuggestionProvider`
- `copilot.py` → `CopilotSuggestionProvider`

**Razón** (cohesión + criterio escalabilidad #1): mismo pattern `OfferSuggestionProvider`. 1 archivo 1 provider 1 responsabilidad. Audit aislado. Cada provider tiene su Reader companion en `application/services/` si necesita consultas multi-tabla complejas (paridad `OfferSuggestionReader`).

**Trade-off**: 3 archivos extra. Costo despreciable.

**Alternativa descartada**: 1 archivo `additional_providers.py` con 3 clases — confunde audit, viola single-responsibility-per-file.

### D-2: Cross-module reads via `shared/links/ports/*` — NO violar ratchet

**Veredicto**:
- `BrandSuggestionProvider` consume `shared/links/ports/brand.py::create_brand_data_port(db)` (ya existe) — extrae BrandKnowledgeDTO `{brand_data, avatars, personality_profile}`. **Para BuyerPersona count** (no expuesto en `BrandKnowledgeDTO`): EXTENDER `BrandDataPort` con nuevo método `get_buyer_persona_count(tenant_id) -> int` (additive, no breaking).
- `SalesAgentSuggestionProvider` consume **NUEVO** port `shared/links/ports/sales_agent.py::SalesAgentObservabilityPort` (a crear este PR). Métodos read-only: `count_leads_since(tenant_id, since: datetime) -> int`, `count_active_conversations_since(tenant_id, since: datetime) -> int`, `get_recent_enrollments(tenant_id, limit: int = 10) -> list[EnrollmentSummaryDTO]`.
- `CopilotSuggestionProvider` consume **`module_registry.get_module_registry()`** (mismo módulo, no cross-module) + `shared/links/ports/brand.py` (vía port existente) + `shared/links/ports/offer.py` (vía port existente).

**Razón** (criterio escalabilidad + cero deuda + arch fitness frozen): ratchet `copilot → módulo` 22 frozen. Si provider importa directo `from src.modules.brand.infrastructure.repositories.brand_repository import BrandRepository` → arch test FALLA (`copilot -> brand | copilot/application/suggestions/providers/brand.py` = NEW entry). Port `shared/links/ports/*` está **fuera del scan ratchet** (ALLOWED_TARGETS incluye `shared`). Ratchet sigue 22.

**Trade-off**: crear 1 nuevo port + extender 1 existente. Inversión chica para cumplir ratchet.

**Alternativa descartada A**: bumpear ratchet de 22 → 25 — viola "ratchet may only SHRINK" (test_no_new_copilot_module_imports.py header), requeriría justificación commit + romper invariante F1. Anti-pattern.
**Alternativa descartada B**: nuevo `copilot_provider/suggestion_provider.py` per módulo (brand + sales_agent) → discovery se encarga — escala mejor pero invierte la dirección de control (suggestions registry pasaría a leer providers desde `discover_providers()`). Cambio arquitectónico mayor fuera de scope PR-2 + invade pattern actual `_bootstrap_builtin`. Diferir a PR futuro si justifica (pj. cuando lleguen analytics + connections providers).

### D-3: `BrandSuggestionProvider` — heurísticas (6 reglas mínimas, prioridad determinística)

**Veredicto**: provider sync, `provider_id="brand"`, `provider_priority=10`, `applies_to_routes=("brand-studio",)`. 6 reglas heurísticas en orden de confidence DESC:

| # | Regla (predicado) | Chip label | Chip prompt | Confidence | Category |
|---|---|---|---|---|---|
| 1 | `not brand.identity or not brand.identity.brand_name` | "Empieza por tu marca" | "Ayudame a configurar la identidad de mi marca: nombre, tagline e industria." | 0.90 | `ACTION` |
| 2 | `brand.positioning is None or not brand.positioning.unique_value_proposition` | "Define tu propuesta única" | "Ayudame a redactar mi UVP usando el framework Brand Love Key." | 0.85 | `ACTION` |
| 3 | `brand.narrative is None or not brand.narrative.one_liner` | "Construye tu narrativa StoryBrand" | "Guíame para armar mi narrativa StoryBrand (hero, problem, guide, plan, CTA)." | 0.82 | `ACTION` |
| 4 | `brand.brand_personality is None or not brand.brand_personality.archetype` | "Elige tu arquetipo de marca" | "Ayudame a elegir el arquetipo Jung que mejor refleja mi marca y por qué." | 0.78 | `CLARIFY` |
| 5 | `personality_profile is None` (sin profile activo) | "Configura la voz del agente" | "Quiero configurar el perfil de personalidad para que el sales agent suene como mi marca." | 0.76 | `ACTION` |
| 6 | `buyer_persona_count == 0` | "Crea tu buyer persona principal" | "Ayudame a definir mi buyer persona principal (demographics, pain points, deseos)." | 0.75 | `ACTION` |
| 7 (bonus) | `brand_completion_ratio < 0.30` (≤2 de 6 bloques completos) | "Activa el modo guiado de marca" | "Quiero un recorrido guiado para completar mi marca paso a paso." | 0.70 | `NAV` |

**Cálculo `brand_completion_ratio`**: `populated_blocks / 6` donde populated_blocks cuenta:
1. `identity.brand_name` non-empty
2. `positioning.unique_value_proposition` non-empty
3. `narrative.one_liner` non-empty
4. `brand_personality.archetype` non-empty
5. `personality_profile is not None` (activo)
6. `buyer_persona_count >= 1`

**Razón** (criterio calidad invariantes + brand-expert SSoT): cubre 4 sub-objetos clave de BrandSettings + PersonalityProfile + BuyerPersona = la spine del Brand Studio según `brand-expert` skill mental model. Confidence ranking respeta dependency DAG (identity primero, luego positioning sobre identity, luego narrative sobre positioning). NO consume DEPRECATED `voice_tone` ni `BrandStrategy.unique_value_proposition`. Engine cap 5 chips totales — 6+1=7 reglas, engine devuelve top-5 by confidence (chips de menor confidence se descartan automáticamente — comportamiento correcto: no abrumar con 7 chips).

**Tenant isolation**: cada read pasa `tenant_id` explícito (`port.get_brand_knowledge(tenant_id)`, `port.get_buyer_persona_count(tenant_id)`, `port.get_active_personality_profile(tenant_id)`).

**Latency budget**: <3ms p99. Reads son JSONB single-row (BrandSettings) + 1 COUNT (buyer_personas) + 1 SELECT activo (personality_profiles). Sin joins.

**Fallback**: cada read en try/except → return `[]` per regla. Provider top-level try/except (paridad OfferSuggestionProvider) → return `[]` global on cualquier excepción.

### D-4: `SalesAgentSuggestionProvider` — heurísticas (5 reglas, foco pipeline observation)

**Veredicto**: provider sync, `provider_id="sales_agent"`, `provider_priority=10`, `applies_to_routes=("sales",)`. 5 reglas heurísticas:

| # | Regla (predicado) | Chip label | Chip prompt | Confidence | Category |
|---|---|---|---|---|---|
| 1 | `count_leads_since(tenant_id, now-7d) == 0` (semana sin leads) | "Sin leads esta semana" | "No tengo leads nuevos esta semana. ¿Cómo puedo activar canales de captación?" | 0.88 | `ACTION` |
| 2 | `count_active_conversations_since(tenant_id, now-24h) == 0` y `count_leads_since(tenant_id, now-30d) > 0` (leads viejos sin actividad reciente) | "Reactiva conversaciones inactivas" | "Tengo leads viejos sin actividad reciente. Ayudame a definir una secuencia de reactivación." | 0.85 | `ACTION` |
| 3 | `personality_profile is None` (sales agent sin voz configurada) | "Configura la voz del sales agent" | "El sales agent no tiene perfil de personalidad. Llévame al Brand Studio a configurarlo." | 0.83 | `NAV` |
| 4 | `pending_payments_count > 0` (enrollments en `PAYMENT_PENDING` >24h) | "Cobros pendientes acumulados" | "Tengo {N} enrollments con pago pendiente. Revisemos qué hacer con cada uno." | 0.80 | `CLARIFY` |
| 5 | `waitlist_count > 0 and no_active_edition` (waitlist con producto sin edición abierta) | "Tu lista de espera necesita una edición" | "Hay clientes en lista de espera sin edición programada. Ayudame a planificar la próxima cohorte." | 0.78 | `ACTION` |

**Datos consultados**:
- `count_leads_since(tenant_id, since)` → COUNT distinct `messages_sales_agent.user_id` WHERE `tenant_id = X AND created_at >= since`. Index `messages_sales_agent.tenant_id` ya existe.
- `count_active_conversations_since(tenant_id, since)` → COUNT distinct `messages_sales_agent.user_id` WHERE `tenant_id = X AND created_at >= since`. (Mismo query, ventana distinta).
- `personality_profile is None` → reusa `BrandDataPort.get_brand_knowledge(tenant_id).personality_profile` (port brand existente, evita duplicar query).
- `pending_payments_count` → `EnrollmentRepository.list_all(tenant_id, status=EnrollmentStatus.PAYMENT_PENDING)` filtrar `created_at < now-24h` en Python (lista chica, sin migrar el filtro al SQL). Si lista >100 rows → migrar filtro a SQL en port.
- `waitlist_count` → `EnrollmentRepository.list_all(tenant_id, status=EnrollmentStatus.WAITLIST)` len.
- `no_active_edition` (per offer con waitlist) → consume `shared/links/ports/offer.py::get_launch_edition_repository(db).list_active_by_tenant(tenant_id)` o equivalente. Si port no expone "active editions count per tenant" → agregar método (port additive).

**Razón** (criterio cero deuda + sales-agent-expert §3 strict): 5 reglas observan métricas pipeline derivables sin tocar §3-protected surfaces. Lecturas read-only sobre tablas `enrollments` + `messages_sales_agent`. NO computa conversion rate (requiere joins multi-tabla — defer si métrica necesaria a S3). NO toca personality_profiles.system_instruction (lectura solo de NULL/non-NULL flag).

**Tenant isolation**: cada query con `WHERE tenant_id = :tenant_id`.

**Latency budget**: <3ms p99. Queries son COUNT con index hit (tenant + created_at). Si latencia mide >5ms p99 en prod → cache 60s per (tenant, hour bucket) en Redis — DEFERRED hasta data prod (riesgo PR.md §riesgos).

**Fallback**: try/except per regla + provider top-level try/except → return `[]`.

**Voz output**: chip labels + prompts en **español neutro LatAm** (`.claude/rules/spanish-text.md` aplica — son chips para copilot UI, NO output del sales_agent). Verificación: chip 4 prompt usa "{N}" placeholder formateado server-side (NO inyectar tono tenant — chips son contexto-agnósticos).

### D-5: `CopilotSuggestionProvider` — heurísticas transversales (5 reglas, fallback global)

**Veredicto**: provider sync, `provider_id="copilot"`, `provider_priority=5` (LOWER que offer/brand/sales — fallback). `applies_to_routes=()` (empty tuple → siempre activo, todas las rutas). 5 reglas heurísticas:

| # | Regla (predicado) | Chip label | Chip prompt | Confidence | Category |
|---|---|---|---|---|---|
| 1 | `conversation_id is None` (pre-conversación, primera vez user) | "Empieza tu primer chat con el copiloto" | "¿Qué puedes hacer por mí? Cuéntame tus capacidades principales." | 0.65 | `CLARIFY` |
| 2 | `len(recent_message_ids) == 0 and conversation_id is not None` (conv abierta vacía) | "Retoma esta conversación" | "Resume lo que estuvimos viendo en esta conversación y propóneme próximos pasos." | 0.62 | `FOLLOWUP` |
| 3 | `current_route is None` (sin contexto de ruta — landing genérico) | "Explorar capacidades del copiloto" | "Muéstrame qué puedo hacer en cada módulo: brand, offer, sales y growth." | 0.60 | `NAV` |
| 4 | `current_route is not None and current_route.startswith(unknown_module)` (ruta no mapeada en `module_registry`) | "Volver a un módulo conocido" | "No reconozco esta ruta. Llévame al módulo más relevante para mi contexto." | 0.58 | `NAV` |
| 5 | `count_completed_modules(tenant_id) <= 1` (tenant con ≤1 módulo configurado — onboarding gap) | "Completa tu setup inicial" | "Quiero ver qué módulos faltan configurar para que el copiloto trabaje al 100%." | 0.56 | `NAV` |

**Cálculo `count_completed_modules(tenant_id)`**:
- Brand: `brand.identity.brand_name not None and brand.positioning.unique_value_proposition not None` → +1
- Offer: `len(get_offer_repository(db).get_all_by_tenant(tenant_id)) >= 1` → +1
- Sales agent: `port.get_active_personality_profile(tenant_id) is not None` → +1

(3 módulos clave; si futuro suma analytics/connections → extender port respectivo).

**Detección `unknown_module`**: `current_route.split("/")[0]` no matchea ningún `route_prefix` en `module_registry.get_module_registry().values()` (set de `descriptor.route_prefix`).

**Razón** (criterio cohesión + escalabilidad): provider transversal cubre estados base que ningún provider route-scoped cubre (pre-conv, ruta unknown, onboarding). Confidence baja (0.56-0.65) garantiza que cuando OfferProvider o BrandProvider tengan chips ranqueados (>0.70), CopilotProvider pasa a fondo del top-5. Cuando rutas son vacías o desconocidas, CopilotProvider asegura que user nunca ve `[]` chips (UX safety net).

**Tenant isolation**: aplica donde lee data (regla 5).

**Latency budget**: <2ms p99. Predicates 1-4 son context-only (no DB). Regla 5 son 3 reads (brand + offer + personality) — todos via ports ya consumidos por otros providers (potencial dedupe via per-request memoization, defer S3).

**Fallback**: try/except global → return `[]`.

### D-6: Sales agent port nuevo `shared/links/ports/sales_agent.py`

**Veredicto**: nuevo archivo en `backend/src/shared/links/ports/sales_agent.py`. Define abstracción + factory + DTO:

```python
"""SalesAgentObservabilityPort — read-only access for cross-module observability.

Used by ``copilot`` SuggestionProvider to compute pipeline heuristics
(leads, conversations, enrollments) WITHOUT taking a direct dependency
on ``sales_agent`` repositories. Keeps the F1 ratchet
``copilot → sales_agent`` at zero entries.

Tenant-scoped. Sync (engine is sync). Best-effort: implementations may
raise; callers (providers) catch and return ``[]``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from sqlalchemy.orm import Session


class EnrollmentSummaryDTO(BaseModel):
    """Lightweight enrollment view for observability purposes."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    offer_id: str
    status: str  # EnrollmentStatus.value
    created_at_iso: str
    edition_id: str | None = None


class SalesAgentObservabilityPort(ABC):
    """Read-only sales pipeline observability for the suggestion engine."""

    @abstractmethod
    def count_leads_since(self, tenant_id: UUID, since: datetime) -> int:
        """Distinct contacts (user_id) with at least one message since ``since``."""
        ...

    @abstractmethod
    def count_active_conversations_since(self, tenant_id: UUID, since: datetime) -> int:
        """Distinct conversations with messages since ``since``."""
        ...

    @abstractmethod
    def list_enrollments_by_status(
        self,
        tenant_id: UUID,
        statuses: tuple[str, ...],
    ) -> list[EnrollmentSummaryDTO]:
        """Lightweight enrollments filtered by status values."""
        ...

    @abstractmethod
    def has_active_edition_for_offer(self, tenant_id: UUID, offer_id: UUID) -> bool:
        """True if the offer has at least one active (non-cancelled) edition."""
        ...


def create_sales_agent_observability_port(db: Session) -> SalesAgentObservabilityPort:
    """Lazy-import the concrete adapter from sales_agent module."""
    from src.modules.sales_agent.application.services.observability_adapter import (
        SalesAgentObservabilityAdapter,
    )

    return SalesAgentObservabilityAdapter(db)
```

**Adapter en sales_agent**: `backend/src/modules/sales_agent/application/services/observability_adapter.py` implementa `SalesAgentObservabilityPort`. Lee de `MessageModel`, `EnrollmentModel` con `select(...).where(tenant_id == X)` SA 2.0. NO modifica §3 surfaces.

**Razón** (criterio escalabilidad + arch fitness): port abstracto en `shared/` evita cualquier nuevo `copilot → sales_agent` ratchet entry. Adapter vive en `sales_agent/application/services/` (DDD layer correcto — application orquesta read sobre infra repos). Factory `create_*_port(db)` paridad con `create_brand_data_port(db)`.

### D-7: NO refactorizar `_no_data_response` para usar engine — separar status hint de chips

**Veredicto**: `_no_data_response(section_slug, hint)` permanece como ESTÁ en líneas 155-167. NO refactor del helper. Eliminar línea 163 `"suggestions": [hint]` significaría romper contract con LLM consumer (deepagent lee `suggestions` field como guidance string list en sus tool outputs).

**Refactor real PR-2**: agregar campo `next_step_hint: str | None = None` al JSON output de `_no_data_response` Y `_ok_response`, y mover la guidance string al nuevo campo. `suggestions` queda RESERVADO para chips engine-driven (cuando aplique).

```python
def _no_data_response(section_slug: str, hint: str) -> str:
    """Status response cuando data faltante. ``next_step_hint`` reemplaza
    el legacy ``suggestions: [hint]`` que mezclaba semántica chip vs guidance.
    """
    import json
    return json.dumps({
        "section_slug": section_slug,
        "draft_fields": {},
        "suggestions": [],          # engine-only field, vacío en error path
        "next_step_hint": hint,     # NEW — status guidance for the LLM
        "confidence": 0.0,
        "citations": [],
    })


def _ok_response(
    section_slug: str,
    draft_fields: dict,
    suggestions: list[str],          # tool-derived insights (kept — D-7 rationale)
    confidence: float,
    citations: list[str] | None = None,
    *,
    next_step_hint: str | None = None,
) -> str:
    """OK response con suggestions tool-derived + optional engine hint."""
    import json
    return json.dumps({
        "section_slug": section_slug,
        "draft_fields": draft_fields,
        "suggestions": suggestions,
        "next_step_hint": next_step_hint,
        "confidence": confidence,
        "citations": citations or [],
    })
```

**`suggestions` field semántica POST-PR-2**:
- En `_ok_response`: contiene `list[str]` = INSIGHTS DERIVADOS DEL TOOL (variantes de promesa generadas por el tool, testimonios encontrados, issues detectados — semántica TOOL-OUTPUT). Estos NO son smart-chips; son resultado del tool que el LLM usa para componer su respuesta.
- En `_no_data_response`: SIEMPRE `[]`. Status guidance pasa a `next_step_hint`.
- Engine smart-chips viven SOLO en `POST /copilot/suggestions` (PR-1) — totalmente desacoplado de tool output.

**Helper `_engine_suggestions_for_context`**: queda PRESENTE en `offer_section_tools.py:30`. PRESERVAR como fuente opcional cuando un tool quiere enriquecer su `suggestions` field con context engine (ej. `adapt_from_brand_identity` línea 256-257 mantiene la concat). NO es deuda — es un legítimo "tool consume engine for richer hints".

**Verificación grep post-PR-2**:
- `grep -n '"suggestions": \[' offer_section_tools.py` → 0 hits CON datos hardcoded (línea 163 cambia a `"suggestions": []` que es semánticamente vacío inicial, NO data hardcoded).
- `grep -n '"suggestions": \[hint\]' offer_section_tools.py` → 0 hits (literal exacto del PR.md acceptance criterion).
- `grep -n '"suggestions": suggestions' offer_section_tools.py` → 1 hit (línea 184 nueva en `_ok_response`, parametrizado).
- `grep -n '"suggestions": \[\]' offer_section_tools.py` → 1 hit (línea 163 nueva en `_no_data_response`, vacío).

**Razón** (criterio cero deuda + cohesión real): el "static residual" del PR.md NO es una smart-chip data leak, es una sobrecarga semántica del field `suggestions` a nivel TOOL CONTRACT. Reusar el field para 2 conceptos distintos (chips engine vs status hints vs tool insights) es la deuda. Separar en `next_step_hint` resuelve la confusión sin tocar la semántica engine ni romper LLM consumers.

**Trade-off**: 1 nuevo field opcional en JSON output. Builders deben actualizar `_no_data_response` callers (interno al file, alcance acotado). Backwards-compat: LLM ignora fields desconocidos automáticamente — deepagent no revienta.

**Alternativa descartada A**: drop literal sin reemplazo → cambia tool contract, deepagent pierde guidance "qué hacer cuando data faltante". Regresión UX.
**Alternativa descartada B**: hacer que `_no_data_response` llame engine internamente y use sus chips → mezcla semántica DIFERENTE (chips engine son user-facing UI, hint es LLM-facing tool guidance), cross-talk peligroso.

### D-8: Extender `BrandDataPort` con métodos additive

**Veredicto**: agregar métodos abstractos al `BrandDataPort` existente:

```python
class BrandDataPort(ABC):
    @abstractmethod
    def get_brand_knowledge(self, tenant_id: UUID) -> BrandKnowledgeDTO:
        ...

    # NEW (PR-2)
    @abstractmethod
    def get_buyer_persona_count(self, tenant_id: UUID) -> int:
        """Active buyer personas count (soft-delete excluded)."""
        ...

    # NEW (PR-2)
    @abstractmethod
    def get_active_personality_profile_present(self, tenant_id: UUID) -> bool:
        """True iff there is an active global PersonalityProfile for the tenant."""
        ...
```

**Adapter `brand.application.services.brand_data_adapter.py::BrandDataAdapter`** implementa los nuevos métodos:
- `get_buyer_persona_count`: `len(BuyerPersonaRepository(db).list_by_tenant(tenant_id))` o COUNT query SQL si optimization needed.
- `get_active_personality_profile_present`: `PersonalityProfileRepository(db).get_active(tenant_id=tenant_id) is not None`.

**Razón** (extensibility + cohesión): port additive (no breaking — single owner: brand module + sales_agent which consumed it). Adapter gana 2 métodos chicos. Sales-agent ya usa `BrandDataPort.get_brand_knowledge` para identity builder — coupling existente, no deuda nueva. CopilotSuggestionProvider + BrandSuggestionProvider + SalesAgentSuggestionProvider los reúsan.

**Trade-off**: 2 métodos extra en port. Sin breaking change — todos los implementers actuales solo son `BrandDataAdapter` (single owner).

### D-9: Registry update — orden estable de registración

**Veredicto**: `_bootstrap_builtin(engine)` registra en este orden EXACTO:

```python
def _bootstrap_builtin(engine: SuggestionEngine) -> None:
    from src.modules.copilot.application.suggestions.providers.offer import (
        OfferSuggestionProvider,
    )
    from src.modules.copilot.application.suggestions.providers.brand import (
        BrandSuggestionProvider,
    )
    from src.modules.copilot.application.suggestions.providers.sales_agent import (
        SalesAgentSuggestionProvider,
    )
    from src.modules.copilot.application.suggestions.providers.copilot import (
        CopilotSuggestionProvider,
    )

    engine.register(OfferSuggestionProvider())     # priority 0
    engine.register(BrandSuggestionProvider())     # priority 10
    engine.register(SalesAgentSuggestionProvider())  # priority 10
    engine.register(CopilotSuggestionProvider())   # priority 5 (fallback)
```

**Razón** (estabilidad sort + forward-compat): orden de registración es **tiebreaker terciario** del engine sort (`confidence DESC, provider_priority DESC, registration order ASC`). Determinismo en chips empatadas. Test arch verifica el orden: `engine._providers[0].provider_id == "offer"`, etc.

**Idempotencia**: `register()` ya implementa `same-id-same-instance no-op`. Si test fixture llama `_reset_for_tests()` + `get_default_engine()` 2 veces → mismo resultado.

### D-10: Provider priority weights — final tabla

**Veredicto**: pesos finales:

| provider_id | provider_priority | applies_to_routes | Razón |
|---|---|---|---|
| `offer` | **0** | `("offer-studio",)` | Baseline. Mantener S1 default. |
| `brand` | **10** | `("brand-studio",)` | Mismo nivel que sales (route-scoped). |
| `sales_agent` | **10** | `("sales",)` | Mismo nivel que brand. |
| `copilot` | **5** | `()` (siempre) | LOWER que route-scoped — fallback. Garantiza que cuando route provider tiene chips, los suyos ganan tiebreak. |

**Razón**: cuando dos chips empatan en `confidence`, el `provider_priority` decide. Brand+Sales=10 > Copilot=5 garantiza que rutas específicas dominen. Offer=0 mantiene S1 baseline (S1 PR-2 cementó este valor — no romper). El gap (offer=0 vs brand/sales=10) es **intencional**: si hay ofertas + brand chips empatadas en confidence, brand tira con su priority 10 (más context-aware). En `offer-studio` route, solo OfferProvider activa (route filter) → priority irrelevante. En `brand-studio`, solo BrandProvider activa (route) + Copilot (siempre) → BrandProvider gana tiebreak.

**Tunear post métricas adopción real** — defer a S3 si data prod muestra desbalance.

### D-11: TDD test surfaces (pre-impl)

Lista cerrada (cada test RED first, GREEN después de implementar):

**Provider unit tests (`backend/tests/modules/copilot/application/suggestions/providers/`)**:

`test_brand_provider.py` (8 tests):
1. `test_brand_provider_metadata` — `provider_id="brand"`, `provider_priority=10`, `applies_to_routes=("brand-studio",)`
2. `test_brand_provider_empty_brand_emits_identity_chip` — port mock retorna BrandKnowledgeDTO con `brand_data={}` → chip "Empieza por tu marca" en output
3. `test_brand_provider_missing_uvp_emits_positioning_chip` — brand con identity.brand_name pero sin positioning.UVP → chip "Define tu propuesta única"
4. `test_brand_provider_missing_archetype_emits_archetype_chip` — brand con identity+positioning+narrative pero `brand_personality.archetype is None` → chip arquetipo
5. `test_brand_provider_no_buyer_persona_emits_persona_chip` — `get_buyer_persona_count` returns 0 → chip persona
6. `test_brand_provider_no_personality_profile_emits_voice_chip` — `get_active_personality_profile_present` returns False → chip voz
7. `test_brand_provider_full_brand_emits_zero_chips` — todos los blocks completos → returns `[]`
8. `test_brand_provider_port_exception_returns_empty_list` — port raises → caught + structlog warning + returns `[]`
9. `test_brand_provider_tenant_isolation` — provider call with tenant_a, port mock asserts called with `tenant_id == tenant_a` (no leak)

`test_sales_agent_provider.py` (7 tests):
1. `test_sales_provider_metadata` — `provider_id="sales_agent"`, `provider_priority=10`, `applies_to_routes=("sales",)`
2. `test_sales_provider_no_leads_7d_emits_chip` — port mock `count_leads_since` returns 0 → chip "Sin leads esta semana"
3. `test_sales_provider_inactive_24h_with_old_leads_emits_reactivation_chip` — counts: 24h=0, 30d=5 → chip reactivación
4. `test_sales_provider_no_personality_profile_emits_voice_chip` — brand port returns `personality_profile=None` → chip voz
5. `test_sales_provider_pending_payments_emits_chip` — port retorna 3 enrollments PAYMENT_PENDING >24h old → chip cobros
6. `test_sales_provider_waitlist_no_active_edition_emits_chip` — waitlist con offer sin edición activa → chip lista de espera
7. `test_sales_provider_port_exception_returns_empty_list`
8. `test_sales_provider_tenant_isolation` — same as brand

`test_copilot_provider.py` (6 tests):
1. `test_copilot_provider_metadata` — `provider_id="copilot"`, `provider_priority=5`, `applies_to_routes=()`
2. `test_copilot_provider_no_conversation_emits_first_chat_chip` — `ctx.conversation_id is None` → chip "Empieza tu primer chat"
3. `test_copilot_provider_empty_conversation_emits_resume_chip` — conv_id set + recent_message_ids empty → chip "Retoma esta conversación"
4. `test_copilot_provider_no_route_emits_explore_chip` — `current_route is None` → chip "Explorar capacidades"
5. `test_copilot_provider_unknown_route_emits_navigate_back_chip` — route="unknown-x" + module_registry returns no match → chip "Volver"
6. `test_copilot_provider_low_setup_emits_onboarding_chip` — count_completed_modules <= 1 → chip onboarding
7. `test_copilot_provider_tenant_isolation`

`test_registry_with_4_providers.py` (4 tests):
1. `test_get_default_engine_registers_4_providers` — `engine._providers` length == 4
2. `test_get_default_engine_registers_in_stable_order` — order: offer, brand, sales_agent, copilot
3. `test_get_default_engine_idempotent` — second call same engine instance
4. `test_get_default_engine_provider_ids_unique` — set of provider_id len == 4

**Integration test** (`test_engine_with_4_providers.py`):
1. `test_engine_route_brand_studio_returns_brand_chips` — ctx route=brand-studio, brand vacío → response includes brand provider chips, NO offer chips
2. `test_engine_route_sales_returns_sales_chips_plus_copilot` — ctx route=sales, no leads → sales chips + copilot fallback (low confidence)
3. `test_engine_unknown_route_returns_only_copilot_chips` — ctx route=unknown → only CopilotProvider chips
4. `test_engine_route_offer_studio_keeps_offer_provider_dominant` — backward compat: offer chips still surface
5. `test_engine_caps_at_5_total` — todos los providers full chips → engine returns max 5
6. `test_engine_provider_breakdown_per_provider_id` — breakdown dict has entries for each provider that contributed
7. `test_engine_provider_priority_breaks_tie` — 2 chips same confidence + different providers → higher priority wins

**Refactor offer_section_tools tests** (`test_offer_section_tools_refactor.py` extends existing):
1. `test_no_data_response_returns_empty_suggestions_and_next_step_hint` — `_no_data_response("identity", "Faltante")` → JSON `{"suggestions": [], "next_step_hint": "Faltante", ...}`
2. `test_ok_response_includes_optional_next_step_hint` — `_ok_response("section", {}, ["x"], 0.8, next_step_hint="hint")` → JSON includes both
3. `test_grep_no_static_suggestions_hint_literal` — read offer_section_tools.py source + assert `'"suggestions": [hint]'` NOT IN content (regression guard)
4. `test_existing_tools_still_pass_baseline` — re-run subset de tests pre-existentes de tools (adapt_from_brand_identity, etc.) → green after refactor

**SalesAgent observability port adapter test** (`test_sales_agent_observability_adapter.py`):
1. `test_count_leads_since_filters_by_tenant_and_date` — insert 3 messages tenant_a + 2 tenant_b + various dates → counts correct per tenant
2. `test_list_enrollments_by_status_filters` — insert mixed status enrollments → only requested statuses returned
3. `test_has_active_edition_for_offer_true_false` — insert active + cancelled editions → boolean correct
4. `test_adapter_implements_port_protocol` — `isinstance(adapter, SalesAgentObservabilityPort)`

**Brand port extension test** (`test_brand_data_adapter_pr2.py` extends existing):
1. `test_get_buyer_persona_count_excludes_soft_deleted` — insert 3 personas + 1 soft-deleted → returns 3
2. `test_get_active_personality_profile_present_true_false` — insert active profile vs no profile → True / False

### D-12: NO nuevo `[COPILOT-*]` anchor — reusar existente

**Veredicto**: 3 nuevos files (`brand.py`, `sales_agent.py`, `copilot.py`) usan `# [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md` en docstring header. Cap 36/36 NO bumpear.

**Razón**: anchor es categoría conceptual ("smart-chips engine"), no archivo. 4 providers comparten misma categoría → reusar. Bumpear cap requiere justificación commit + viola "shrink only" si futuro PR necesita anchor real nuevo.

### D-13: NO nuevo cross-module ratchet entry

**Veredicto**: builders verifican post-implementación con `make arch-test` que `KNOWN_COPILOT_TO_MODULE_IMPORTS` SIGUE siendo 22 entries. Si arch test falla por nuevo entry → fix obligatorio (mover read a port `shared/links/ports/`). NO commitear con bumpeo.

**Verificación**:
```bash
cd backend && .venv/bin/pytest tests/architecture/test_no_new_copilot_module_imports.py -x -v
# Expected: PASS, len(KNOWN_COPILOT_TO_MODULE_IMPORTS) == 22
```

### D-14: Spanish neutro LatAm — chips sin voseo

**Veredicto**: TODOS los chip labels + prompts respetan `.claude/rules/spanish-text.md`. Tildes + ñ + apertura `¿`/`¡`. Tuteo (`tú`, `ayudame` ✗ → `ayúdame`, `dame` ✓), NO voseo. Ejemplos verificados:
- ✓ "Empieza por tu marca" (imperativo neutro)
- ✓ "Ayúdame a redactar mi UVP usando el framework Brand Love Key" (tuteo via reflexivo)
- ✗ Evitar: "Empezá", "Ayudame" (sin tilde — voseo argentino), "querés", "tenés"

**Builder checklist**: pre-commit ejecuta `_VOSEO_RE` regex sweep manual sobre archivos providers nuevos. Cualquier match en chip label/prompt → corregir.

### D-15: Performance budget engine con 4 providers

**Veredicto**: target SLA p99 engine `get_suggestions()` con 4 providers activos = **<10ms**. Breakdown:

| Provider | Latency budget p99 | Reads |
|---|---|---|
| OfferSuggestionProvider | <3ms | 1 SELECT offers (índice tenant) + COUNT preset_flags |
| BrandSuggestionProvider | <3ms | 1 SELECT BrandSettings JSONB + 1 COUNT buyer_personas + 1 SELECT active personality_profile |
| SalesAgentSuggestionProvider | <3ms | 2 COUNT messages (índice tenant_id) + 1 SELECT enrollments status filter |
| CopilotSuggestionProvider | <2ms | 0 DB en regla 1-4 + 3 reads en regla 5 (SHARED con otros providers — TODO dedupe S3) |
| Engine sort + cap | <0.5ms | in-memory list ops |
| **Total** | **<11.5ms p99** | aceptable margin ~10ms target |

**Si latencia mide >15ms p99 en prod (post-merge medición vía `latency_ms` en breakdown)**: cache 60s per `(tenant_id, current_route)` en Redis con cache key `copilot:suggestions:{tenant}:{route}` — DEFERRED hasta data prod.

### D-16: Observability — provider_id en breakdown

**Veredicto**: engine ya emite `breakdown: dict[provider_id, count]` (engine.py:99). Cada provider contribuye con su `provider_id`. **Sin cambio engine code**. Endpoint `POST /copilot/suggestions` (PR-1) devuelve breakdown en response → FE potencialmente lo usa para analítica adopción per-provider (cuál provider chips conviertenmás).

**Trace event**: `SuggestionShown` ya emite `provider_breakdown` campo (events.py:194-220). Subscriber `domain_subscribers.py::on_suggestion_shown` ya persiste a `copilot_trace_event(event_type='copilot_suggestion_shown', data->provider_breakdown)`. **Sin cambio**.

**Métrica adopción per-provider**:
```sql
SELECT
  data->>'provider_breakdown' AS breakdown,
  COUNT(*) AS shown_count
FROM copilot_trace_event
WHERE event_type = 'copilot_suggestion_shown'
  AND tenant_id = :tenant_id
  AND created_at >= now() - interval '30 days'
GROUP BY breakdown;
```

## 2. SQLAlchemy 2.0 Models

**No aplica.** PR no introduce tablas nuevas. Persistencia events vía `copilot_trace_event` (existente, S1). Reads via SA 2.0 `select(...)` en adapters de port (mismo pattern existente).

## 3. Pydantic v2 DTOs

### `EnrollmentSummaryDTO` (NEW — en `shared/links/ports/sales_agent.py`)

```python
class EnrollmentSummaryDTO(BaseModel):
    """Lightweight enrollment view for observability purposes (D-6).

    Mirror MINUS PII fields (no contact_id en clear, no payment_link_url).
    """

    model_config = ConfigDict(from_attributes=True)

    id: str                          # UUID stringified
    offer_id: str
    status: str                      # EnrollmentStatus.value
    created_at_iso: str              # ISO 8601 UTC
    edition_id: str | None = None
```

**No hay nuevo DTO API público — endpoint `POST /copilot/suggestions` (PR-1) ya tiene su DTO completo.** PR-2 no agrega endpoint.

## 4. API Routes

**No aplica.** PR-2 NO agrega endpoint. Todo el surface API existente (PR-1 expone `POST /copilot/suggestions` + `POST /copilot/suggestions/accept`) consume engine via `get_default_engine()`. Después de mergear PR-2, el endpoint **automáticamente** devuelve más chips (engine tiene 4 providers en lugar de 1). Cero cambio shape API.

## 5. TypeScript Types (Frontend)

**No aplica.** FE locked desde PR-1 + S1 PR-2. `Suggestion` shape (id, label, prompt, confidence, category, source_module) ya soporta todos los providers. Nuevos `source_module` values (`brand`, `sales_agent`, `copilot`) son strings — type already `string`.

**Verificar PR-1 checklist post-PR-2**: si FE quiere mostrar badge per-provider (ej. icon brand vs sales), agregar mapping client-side (no requiere shape change).

## 6. Repository Interfaces

### `BrandDataPort` extension (`backend/src/shared/links/ports/brand.py`)

```python
class BrandDataPort(ABC):
    @abstractmethod
    def get_brand_knowledge(self, tenant_id: UUID) -> BrandKnowledgeDTO:
        """[EXISTING — unchanged]"""
        ...

    # ── NEW (PR-2) ─────────────────────────────────────────────────

    @abstractmethod
    def get_buyer_persona_count(self, tenant_id: UUID) -> int:
        """Active buyer personas count (soft-delete excluded)."""
        ...

    @abstractmethod
    def get_active_personality_profile_present(self, tenant_id: UUID) -> bool:
        """True iff there is an active global PersonalityProfile for the tenant.

        Uses the existing PersonalityProfileRepository.get_active filter
        (is_active + offer_id IS NULL + avatar_id IS NULL + deleted_at IS NULL).
        """
        ...
```

### `SalesAgentObservabilityPort` (NEW)

Ver D-6 para shape completa.

### Adapters

| Port | Adapter file | Adapter class |
|---|---|---|
| `BrandDataPort` (extended) | `backend/src/modules/brand/application/services/brand_data_adapter.py` (existing — extend) | `BrandDataAdapter` |
| `SalesAgentObservabilityPort` | `backend/src/modules/sales_agent/application/services/observability_adapter.py` (NEW) | `SalesAgentObservabilityAdapter` |

**Tenant isolation en adapters**: cada método recibe `tenant_id` explícito. SQL filters `WHERE tenant_id = :tenant_id` siempre. Confirmar en code review.

## 7. Application Services

### Provider files (NEW — 3 archivos)

**`backend/src/modules/copilot/application/suggestions/providers/brand.py`**

```python
"""BrandSuggestionProvider — heuristic, route-scoped, tenant-isolated.

Reads brand state via ``shared/links/ports/brand.py::BrandDataPort``
(no direct cross-module import — preserves the F1 ratchet at 22 entries).

Heuristic rules (D-3, 7 reglas):
 1. brand.identity.brand_name vacío            → "Empieza por tu marca"        (0.90)
 2. brand.positioning.UVP vacío                → "Define tu propuesta única"   (0.85)
 3. brand.narrative.one_liner vacío            → "Construye tu narrativa"      (0.82)
 4. brand.brand_personality.archetype vacío    → "Elige tu arquetipo"          (0.78)
 5. PersonalityProfile activo ausente          → "Configura la voz del agente" (0.76)
 6. buyer_persona_count == 0                   → "Crea tu buyer persona"       (0.75)
 7. brand_completion_ratio < 0.30              → "Activa el modo guiado"       (0.70)

[COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

import structlog

from src.core.database import SessionLocal
from src.modules.copilot.domain.suggestion import (
    Suggestion,
    SuggestionCategory,
    SuggestionContext,
)

logger = structlog.get_logger()


class BrandSuggestionProvider:
    """Heuristic suggestions for the Brand Studio route."""

    @property
    def provider_id(self) -> str:
        return "brand"

    @property
    def provider_priority(self) -> int:
        return 10

    @property
    def applies_to_routes(self) -> tuple[str, ...]:
        return ("brand-studio",)

    def get_suggestions(
        self,
        ctx: SuggestionContext,
        *,
        max_per_provider: int = 5,
    ) -> list[Suggestion]:
        """Compute heuristic suggestions. MUST NOT raise — returns [] on any error."""
        try:
            return self._compute(ctx, max_per_provider=max_per_provider)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "brand_suggestion_provider_failed",
                tenant_id=str(ctx.tenant_id),
                error=str(exc),
            )
            return []

    def _compute(
        self,
        ctx: SuggestionContext,
        *,
        max_per_provider: int,
    ) -> list[Suggestion]:
        from src.shared.links.ports.brand import create_brand_data_port

        db = SessionLocal()
        try:
            port = create_brand_data_port(db)

            # Lecturas tenant-scoped
            knowledge = self._safe_read(
                lambda: port.get_brand_knowledge(ctx.tenant_id),
                default=None,
            )
            persona_count = self._safe_read(
                lambda: port.get_buyer_persona_count(ctx.tenant_id),
                default=0,
            )
            personality_present = self._safe_read(
                lambda: port.get_active_personality_profile_present(ctx.tenant_id),
                default=False,
            )

            brand_data = (knowledge.brand_data if knowledge else {}) or {}
            identity = brand_data.get("identity") or {}
            positioning = brand_data.get("positioning") or {}
            narrative = brand_data.get("narrative") or {}
            brand_personality = brand_data.get("brand_personality") or {}

            suggestions: list[Suggestion] = []

            # Compute completion ratio (used by rule 7)
            populated = sum([
                bool(identity.get("brand_name")),
                bool(positioning.get("unique_value_proposition")),
                bool(narrative.get("one_liner")),
                bool(brand_personality.get("archetype")),
                bool(personality_present),
                persona_count >= 1,
            ])
            completion_ratio = populated / 6.0

            # Rule 1
            if not identity.get("brand_name"):
                suggestions.append(Suggestion(
                    label="Empieza por tu marca",
                    prompt=(
                        "Ayúdame a configurar la identidad de mi marca: "
                        "nombre, tagline e industria."
                    ),
                    confidence=0.90,
                    category=SuggestionCategory.ACTION,
                    source_module="brand",
                ))

            # Rule 2
            if identity.get("brand_name") and not positioning.get("unique_value_proposition"):
                suggestions.append(Suggestion(
                    label="Define tu propuesta única",
                    prompt=(
                        "Ayúdame a redactar mi propuesta única de valor "
                        "usando el framework Brand Love Key."
                    ),
                    confidence=0.85,
                    category=SuggestionCategory.ACTION,
                    source_module="brand",
                ))

            # Rule 3
            if positioning.get("unique_value_proposition") and not narrative.get("one_liner"):
                suggestions.append(Suggestion(
                    label="Construye tu narrativa StoryBrand",
                    prompt=(
                        "Guíame para armar mi narrativa StoryBrand "
                        "(hero, problem, guide, plan, CTA)."
                    ),
                    confidence=0.82,
                    category=SuggestionCategory.ACTION,
                    source_module="brand",
                ))

            # Rule 4
            if not brand_personality.get("archetype"):
                suggestions.append(Suggestion(
                    label="Elige tu arquetipo de marca",
                    prompt=(
                        "Ayúdame a elegir el arquetipo Jung que mejor "
                        "refleja mi marca y por qué."
                    ),
                    confidence=0.78,
                    category=SuggestionCategory.CLARIFY,
                    source_module="brand",
                ))

            # Rule 5
            if not personality_present:
                suggestions.append(Suggestion(
                    label="Configura la voz del agente",
                    prompt=(
                        "Quiero configurar el perfil de personalidad para "
                        "que el sales agent suene como mi marca."
                    ),
                    confidence=0.76,
                    category=SuggestionCategory.ACTION,
                    source_module="brand",
                ))

            # Rule 6
            if persona_count == 0:
                suggestions.append(Suggestion(
                    label="Crea tu buyer persona principal",
                    prompt=(
                        "Ayúdame a definir mi buyer persona principal "
                        "(demographics, pain points, deseos)."
                    ),
                    confidence=0.75,
                    category=SuggestionCategory.ACTION,
                    source_module="brand",
                ))

            # Rule 7
            if completion_ratio < 0.30:
                suggestions.append(Suggestion(
                    label="Activa el modo guiado de marca",
                    prompt=(
                        "Quiero un recorrido guiado para completar mi marca "
                        "paso a paso."
                    ),
                    confidence=0.70,
                    category=SuggestionCategory.NAV,
                    source_module="brand",
                ))

            suggestions.sort(key=lambda s: s.confidence, reverse=True)
            return suggestions[:max_per_provider]
        finally:
            db.close()

    @staticmethod
    def _safe_read(fn, default):  # noqa: ANN001, ANN205
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            logger.warning("brand_provider_safe_read_failed", error=str(exc))
            return default


__all__ = ["BrandSuggestionProvider"]
```

**`backend/src/modules/copilot/application/suggestions/providers/sales_agent.py`**

Mismo pattern. Consume `create_sales_agent_observability_port(db)` + `create_brand_data_port(db).get_active_personality_profile_present(tenant_id)`. 5 reglas D-4. Lecturas dentro de `try/except` per regla.

```python
"""SalesAgentSuggestionProvider — heuristic, route-scoped, tenant-isolated.

Reads sales pipeline observability via ``shared/links/ports/sales_agent.py``
(NEW PR-2 port — keeps F1 ratchet ``copilot → sales_agent`` at 0 entries).

§3 protected: this provider is READ-ONLY on enrollments + messages tables.
NEVER touches Closer Studio API/WS, BufferService, OutputManager, FollowUp,
PromptVersionModel, agent_state_checkpoint.

Heuristic rules (D-4, 5 reglas):
 1. count_leads_since(now-7d) == 0           → "Sin leads esta semana"     (0.88)
 2. inactive_24h + leads_30d > 0             → "Reactiva conversaciones"   (0.85)
 3. PersonalityProfile activo ausente        → "Configura voz del agente"  (0.83)
 4. pending_payments_count > 0               → "Cobros pendientes"         (0.80)
 5. waitlist_count > 0 + no_active_edition   → "Lista de espera necesita edición" (0.78)

[COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
"""
# ... (skeleton paridad BrandSuggestionProvider; full impl by builder following D-4 + heuristics table)
```

**`backend/src/modules/copilot/application/suggestions/providers/copilot.py`**

```python
"""CopilotSuggestionProvider — transversal, low-priority fallback.

Routes ``()`` (always active) — provides UX safety net when route-scoped
providers return [] (unknown routes, pre-conversation, onboarding gaps).

Reads:
 - `module_registry.get_module_registry()` (intra-module — no ratchet impact)
 - `shared/links/ports/brand.py` (existing port — for completeness check)
 - `shared/links/ports/offer.py::get_offer_repository` (existing port)

Heuristic rules (D-5, 5 reglas):
 1. conversation_id is None                 → "Empieza tu primer chat"      (0.65)
 2. conv set + recent_message_ids empty     → "Retoma esta conversación"    (0.62)
 3. current_route is None                   → "Explorar capacidades"        (0.60)
 4. unknown route (no module match)         → "Volver a módulo conocido"    (0.58)
 5. count_completed_modules <= 1            → "Completa tu setup inicial"   (0.56)

[COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
"""
# ... (skeleton paridad — full impl by builder following D-5)
```

### Adapter files (1 NEW + 1 EXTEND)

**NEW**: `backend/src/modules/sales_agent/application/services/observability_adapter.py`
```python
"""SalesAgentObservabilityAdapter — concrete port impl."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select

from src.modules.sales_agent.infrastructure.models.enrollment_model import (
    EnrollmentModel,
)
from src.modules.sales_agent.infrastructure.models.message_model import MessageModel
from src.shared.links.ports.sales_agent import (
    EnrollmentSummaryDTO,
    SalesAgentObservabilityPort,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class SalesAgentObservabilityAdapter(SalesAgentObservabilityPort):
    """Concrete adapter — read-only over enrollments + messages tables."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def count_leads_since(self, tenant_id: UUID, since: datetime) -> int:
        stmt = select(func.count(func.distinct(MessageModel.user_id))).where(
            MessageModel.tenant_id == tenant_id,
            MessageModel.created_at >= since,
        )
        result = self._db.execute(stmt).scalar_one()
        return int(result or 0)

    def count_active_conversations_since(self, tenant_id: UUID, since: datetime) -> int:
        # Distinct conversations approximated by distinct user_ids since
        # conversations table is a sales_agent-internal concept § (3-protected).
        # If a richer notion of "conversation" needed, add port method later.
        return self.count_leads_since(tenant_id, since)

    def list_enrollments_by_status(
        self,
        tenant_id: UUID,
        statuses: tuple[str, ...],
    ) -> list[EnrollmentSummaryDTO]:
        if not statuses:
            return []
        stmt = (
            select(EnrollmentModel)
            .where(
                EnrollmentModel.tenant_id == tenant_id,
                EnrollmentModel.status.in_(statuses),
            )
            .order_by(EnrollmentModel.created_at.desc())
            .limit(100)  # cap defensivo
        )
        rows = self._db.execute(stmt).scalars().all()
        return [
            EnrollmentSummaryDTO(
                id=str(r.id),
                offer_id=str(r.offer_id),
                status=r.status,
                created_at_iso=r.created_at.isoformat() if r.created_at else "",
                edition_id=str(r.edition_id) if r.edition_id else None,
            )
            for r in rows
        ]

    def has_active_edition_for_offer(self, tenant_id: UUID, offer_id: UUID) -> bool:
        # Defer to existing offer port (cross-module-OK — within shared/)
        from src.shared.links.ports.offer import get_launch_edition_repository

        repo = get_launch_edition_repository(self._db)
        editions = repo.list_by_offer(offer_id, tenant_id=tenant_id)  # type: ignore[attr-defined]
        return any(getattr(e, "status", "") not in ("cancelled", "draft") for e in editions)


__all__ = ["SalesAgentObservabilityAdapter"]
```

**Verificar `LaunchEditionRepository.list_by_offer` signature**: si el método actual no acepta `tenant_id` keyword o no existe → builder agrega método read-only respetando D-2 (vía shared port additive).

**EXTEND**: `backend/src/modules/brand/application/services/brand_data_adapter.py` agrega 2 métodos D-8.

```python
class BrandDataAdapter(BrandDataPort):
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_brand_knowledge(self, tenant_id: UUID) -> BrandKnowledgeDTO:
        """[EXISTING]"""
        ...

    # ── NEW (PR-2) ─────────────────────────────────────────────────

    def get_buyer_persona_count(self, tenant_id: UUID) -> int:
        from src.modules.brand.infrastructure.repositories.buyer_persona_repository import (
            BuyerPersonaRepository,
        )

        repo = BuyerPersonaRepository(self._db)
        return len(repo.list_by_tenant(tenant_id))

    def get_active_personality_profile_present(self, tenant_id: UUID) -> bool:
        from src.modules.brand.infrastructure.repositories.personality_repository import (
            PersonalityProfileRepository,
        )

        repo = PersonalityProfileRepository(self._db)
        profile = repo.get_active(tenant_id=tenant_id)
        return profile is not None
```

## 8. Agentic Surfaces

**No aplica.** PR no toca LangGraph state, tools, prompts, traces, deepagents harness, system_prompt order, channel format. Engine + provider pattern es service-layer agentic-adjacent (consumed by REST endpoint, not by graph nodes).

## 9. Migration Notes

**No aplica.** Cero migrations DB. Cero schema changes. Tablas leídas (`enrollments`, `messages_sales_agent`, `personality_profiles`, `buyer_personas`, `tenants.config_json`) son existentes — solo SELECT.

## 10. File Structure

### NEW (8 archivos)

**Backend src** (5 archivos):
```
backend/src/modules/copilot/application/suggestions/providers/
├── brand.py                                      # NEW — D-3
├── sales_agent.py                                # NEW — D-4
└── copilot.py                                    # NEW — D-5

backend/src/shared/links/ports/
└── sales_agent.py                                # NEW — D-6 (port + DTO + factory)

backend/src/modules/sales_agent/application/services/
└── observability_adapter.py                      # NEW — D-6 (concrete adapter)
```

**Backend tests** (6 archivos):
```
backend/tests/modules/copilot/application/suggestions/providers/
├── test_brand_provider.py                        # NEW — 9 tests
├── test_sales_agent_provider.py                  # NEW — 8 tests
└── test_copilot_provider.py                      # NEW — 7 tests

backend/tests/modules/copilot/application/suggestions/
├── test_registry_with_4_providers.py             # NEW — 4 tests
└── test_engine_with_4_providers.py               # NEW — 7 tests

backend/tests/modules/copilot/application/tools/
└── test_offer_section_tools_refactor.py          # NEW — 4 tests

backend/tests/modules/sales_agent/application/services/
└── test_observability_adapter.py                 # NEW — 4 tests

backend/tests/modules/brand/application/services/
└── test_brand_data_adapter_pr2.py                # NEW — 2 tests
```

### MODIFIED (4 archivos)

```
backend/src/modules/copilot/application/suggestions/registry.py
  └─ _bootstrap_builtin: registra 4 providers en orden estable (D-9)

backend/src/modules/copilot/application/tools/offer_section_tools.py
  └─ _no_data_response: refactor field semántica (D-7)
  └─ _ok_response: agrega next_step_hint kwarg
  └─ Líneas modificadas: 155-167 (helper) + sin tocar tools individuales (mantienen llamadas existentes — backwards compat)

backend/src/shared/links/ports/brand.py
  └─ BrandDataPort: agrega 2 métodos abstractos (D-8)

backend/src/modules/brand/application/services/brand_data_adapter.py
  └─ BrandDataAdapter: implementa 2 métodos nuevos (D-8)
```

## 11. Cross-Cutting Concerns

| Concern | Aplicación |
|---|---|
| **Tenant isolation** | Cada provider recibe `ctx.tenant_id` y lo pasa explícito a port. Cada adapter SQL filter `WHERE tenant_id == :tenant_id`. SuggestionContext es frozen — provider no puede mutar/leak tenant_id a otra request. |
| **Currency** | N/A (sin monetary fields en chips, prompts, dtos). |
| **Master data** | `created_at` se lee como `DateTime(timezone=True)` UTC (existing). `EnrollmentSummaryDTO.created_at_iso` serializa con `.isoformat()` UTC string. |
| **Spanish neutro LatAm** | Chips labels + prompts respetan rule (D-14). Pre-commit `_VOSEO_RE` sweep manual obligatorio. |
| **PII allowlist** | `EnrollmentSummaryDTO` excluye contact_id (PII), payment_link_url (URL puede contener token), pricing_amount + currency (data tier sensitive — no necesario para heurística). Sólo expone IDs internos + status + timestamps. Documentar en code comment. |
| **Native-first dev** | Tests run native: `cd backend && .venv/bin/pytest tests/modules/copilot/application/suggestions/ tests/modules/sales_agent/application/services/test_observability_adapter.py tests/modules/brand/application/services/test_brand_data_adapter_pr2.py tests/architecture/ -x -q`. NUNCA `docker exec`. |
| **structlog, no print** | Todos los providers + adapters usan `structlog.get_logger()`. Event names snake_case (`brand_suggestion_provider_failed`, `sales_agent_provider_no_leads_count_failed`). kwargs `tenant_id=str(...)`. NEVER use kwarg `event=`. |
| **§3 sales_agent protection** | SalesAgentObservabilityAdapter consume SOLO models read-only. NO toca Closer Studio API, WS, BufferService, OutputManager, FollowUp, PromptVersionModel, agent_state_checkpoint. Si build_phase requiere computar conversion rate o tasa de respuesta → STOP, escalar a Chris (no scope creep PR-2). |
| **Best-effort engine** | Cada provider top-level try/except + cada read interno try/except. Engine continúa con resto si 1 provider falla (engine.py:84-92 ya implementa). FE sigue recibiendo chips de los 3 providers vivos. |

## 12. Architecture Fitness Impact

| Test | Impact | Acción builder |
|---|---|---|
| `tests/architecture/test_no_new_copilot_module_imports.py` | **CRÍTICO** — ratchet 22 frozen. Si provider importa `from src.modules.brand.*` o `from src.modules.sales_agent.*` directo → arch test FAIL. **Builder verifica con `make arch-test` ANTES commit.** | Solo `from src.shared.links.ports.brand import ...` y `from src.shared.links.ports.sales_agent import ...` permitidos en providers. NO importar repos directos. |
| `tests/architecture/test_copilot_anchors.py` | Cap 36/36 — D-12 reusar anchor existente. NO bumpear. | Builder usa `[COPILOT-SUGGESTIONS-ENGINE]` en docstrings. |
| `tests/architecture/test_copilot_provider_compliance.py` | Validates `CopilotProvider` interface (módulo provider — F1 pattern). NO aplica a SuggestionProvider (Protocol distinto). | Pass automático. |
| `tests/architecture/test_copilot_registry.py` | Validates engine registry idempotency. **Engine extends 1 → 4 providers.** Test debe seguir verde. Si hay test que asserta length == 1 → ACTUALIZAR a 4. | Builder revisa post-impl. |
| `tests/architecture/test_api_contracts.py` | NO aplica (sin endpoint nuevo). | Pass automático. |
| `tests/architecture/test_redirect_slashes.py` | NO aplica (sin touch a `main.py FastAPI()` init). | Pass automático. |
| `tests/architecture/test_ddd_boundaries.py` | Ratchet `copilot` está en `CROSS_IMPORT_ALLOWED_SOURCES` (treated as infra). PR mantiene esto. **Sales_agent puede ahora ser importado por copilot vía port shared/ — NO direct.** | Builder confirma. |

**Allowlist shrinkage**: ninguna. Ratchet stays at 22.

## 13. pm-nico/current-state Updates Required

`docs/pm-nico/current-state/copilot.md` — PM ejecuta post-merge:

1. **Update cap "Suggestion engine + provider registry"** (línea ~86):
   - Cambiar "Inicial: `OfferSuggestionProvider` (preset-flag-driven)" → "**4 providers live**: `OfferSuggestionProvider` (route `offer-studio`, priority 0), `BrandSuggestionProvider` (route `brand-studio`, priority 10, 7 reglas), `SalesAgentSuggestionProvider` (route `sales`, priority 10, 5 reglas — solo lectura §3-respect), `CopilotSuggestionProvider` (siempre activo, priority 5 fallback, 5 reglas onboarding/state)"
   - Actualizar línea 91-92 "Providers pendientes: brand, sales_agent, copilot" → REMOVER (ya no pendientes)

2. **Append decisiones table**:
   ```md
   | 2026-04-30 | 4 providers heurísticos (no LLM) | Latencia engine <10ms p99 con 4 providers. LLM ranking sigue defer S3+ |
   | 2026-04-30 | SalesAgentObservabilityPort en shared/links/ports/ | Ratchet copilot→sales_agent stays 0; §3 protect intacto |
   | 2026-04-30 | BrandDataPort extendido (buyer_persona_count + personality_present) | Additive, NO breaking; reuso de port shared existente |
   ```

3. **Append nueva cap "Pure expansion offer_section_tools — fix semántica suggestions field"**:
   ```md
   ### Cap: Tool output semantic fix (suggestions vs next_step_hint)
   - Introducida: PR-2 (PI-2, S2, 2026-04-30)
   - Estado: refactored
   - Operable copilot: indirecto (mejora interpretación deepagent)
   - Cambio: `_no_data_response` ahora emite `suggestions: []` (engine-only) + `next_step_hint: str` (status guidance LLM)
   - Eliminó conflate semántico de `suggestions` field como dump-zone para 3 conceptos
   - grep verifica: `'"suggestions": [hint]'` literal = 0 hits post-merge
   ```

PM (no builder) ejecuta este update post-merge.

## 14. Test Surfaces (TDD-mandatory — RED first per layer)

Ver D-11 para lista cerrada (8 archivos test, 51 tests totales aprox).

**Orden TDD por capa**:
1. **Domain**: tests pre-existentes `test_suggestion_domain.py` siguen verdes (sin cambios `Suggestion`/`SuggestionContext`).
2. **Infrastructure**: `test_observability_adapter.py` + `test_brand_data_adapter_pr2.py` RED → GREEN. Tests usan SQLite in-memory + `Base.metadata.create_all()`.
3. **Application** (providers): `test_brand_provider.py`, `test_sales_agent_provider.py`, `test_copilot_provider.py`, `test_registry_with_4_providers.py` RED → GREEN. Tests mockean ports con `unittest.mock.MagicMock(spec=BrandDataPort)`.
4. **Application** (engine integration): `test_engine_with_4_providers.py` RED → GREEN. Usa real engine + mocked providers.
5. **Application** (tool refactor): `test_offer_section_tools_refactor.py` RED → GREEN. Test grep regression guard.
6. **API/E2E**: NO aplica (sin endpoint nuevo). PR-1 e2e ya cubre flow consumer.

**Comando ejecución completa**:
```bash
cd backend && .venv/bin/pytest \
  tests/modules/copilot/application/suggestions/ \
  tests/modules/copilot/application/tools/test_offer_section_tools_refactor.py \
  tests/modules/sales_agent/application/services/test_observability_adapter.py \
  tests/modules/brand/application/services/test_brand_data_adapter_pr2.py \
  tests/architecture/test_no_new_copilot_module_imports.py \
  tests/architecture/test_copilot_anchors.py \
  -x -q --tb=short
```

Esperado: GREEN. Si arch test FAIL por nuevo entry → builder fix moviendo read a port (NO bumpear allowlist).

## 15. Performance Budget

| Surface | Budget | Medición |
|---|---|---|
| `BrandSuggestionProvider.get_suggestions(ctx)` p99 | <3ms | 1 SELECT JSONB + 1 COUNT + 1 SELECT (index hits) |
| `SalesAgentSuggestionProvider.get_suggestions(ctx)` p99 | <3ms | 2 COUNT (índice tenant + created_at) + 1 SELECT enrollments status filter |
| `CopilotSuggestionProvider.get_suggestions(ctx)` p99 | <2ms | 0 DB en regla 1-4 + 3 reads compartidos en regla 5 |
| `SuggestionEngine.get_suggestions(ctx)` total p99 con 4 providers | <11ms | suma + sort + cap |
| Endpoint `POST /copilot/suggestions` p99 (PR-1 contract) | <50ms total | ~11ms engine + ~10ms async wrap + serialization |

**Stress test** (opt-in, post-merge): `python scripts/benchmark_suggestion_engine.py --providers 4 --iterations 1000` (script a crear si data prod muestra latencia issue).

**Mitigación si >15ms p99 prod**: Redis cache 60s key `copilot:suggestions:{tenant_id}:{current_route}` — DEFERRED (PR.md §riesgos).

## 16. Observability

| Métrica | Source | Query |
|---|---|---|
| Adopción per-provider | `copilot_trace_event(event_type='copilot_suggestion_shown', data->provider_breakdown)` | `SELECT data->>'provider_breakdown', COUNT(*) FROM copilot_trace_event WHERE event_type='copilot_suggestion_shown' GROUP BY 1` |
| Click ratio per-provider | `copilot_trace_event(event_type='copilot_suggestion_accepted', data->source_module)` | `SELECT data->>'source_module', COUNT(DISTINCT data->>'suggestion_id') FROM copilot_trace_event WHERE event_type='copilot_suggestion_accepted' GROUP BY 1` |
| Engine latency p99 | `SuggestionsResponse.latency_ms` (PR-1 endpoint response) | NEXT: agregar histograma Prometheus si volumen ≥10k/día |
| Provider failures | structlog warnings `*_suggestion_provider_failed` | `docker logs visionarias_brain_dev 2>&1 \| grep -E '_suggestion_provider_failed'` |

**No nuevos channels** ni trace events en PR-2. Reusa infra S1 + PR-1.

## 17. Out of Scope (CONTRACT lock)

- LLM-based ranking de suggestions — defer S3+ si métricas adopción <5%
- Cache Redis providers — defer hasta data prod p99 >15ms (PR.md §riesgos)
- Analytics SuggestionProvider (`/growth-studio` route) — PR.md decisión (out of scope explícito)
- Connections SuggestionProvider (`/connections` route) — PR.md decisión
- ML feedback loop persistencia tabla dedicada — defer
- Per-request memoization de reads compartidos (brand + offer) — defer S3
- Refactor `module_registry` para incluir SuggestionProvider discovery — defer
- Métricas Prometheus engine latency — defer hasta volumen lo justifique
- Streaming SSE de chips — endpoint REST simple (PR-1 D-1)

## 18. Rollback Plan

| Surface | Rollback |
|---|---|
| 3 providers nuevos | Additive — `git revert` del commit BE → `_bootstrap_builtin` solo registra `OfferSuggestionProvider` → engine devuelve solo offer chips. Endpoint `POST /copilot/suggestions` (PR-1) sigue 200 OK. UX regression: rutas `brand-studio` + `sales` no muestran chips brand/sales (degradación graceful — empty chips ya soportado FE). |
| Refactor `_no_data_response` | `git revert` → vuelve `"suggestions": [hint]` literal. Tools siguen funcionando (LLM ignora desconocido `next_step_hint`). |
| `BrandDataPort` extension | `git revert` → 2 métodos abstractos vuelven removidos. Si hay caller dependiente (BrandSuggestionProvider) → coupling se rompe. Pero si revert ambos commits (provider + port) en orden, todo limpio. |
| `SalesAgentObservabilityPort` (NEW file) | `git revert` → file desaparece. SalesAgentSuggestionProvider revert obligatorio (depende del port). |

**Feature flag NO necesario** — PR es additive desde perspectiva user-facing (más chips, no menos). Si bug crítico mid-roll → revert PR completo restablece UX S1.

**Recomendación deploy**: PR-2 mergea **DESPUÉS** de PR-1 (PR-1 expone endpoint que consume engine). Si PR-2 mergea primero: providers registrados pero sin endpoint que los exponga → no rompe runtime (engine sigue siendo singleton in-memory). Cero coupling deploy order.

## 19. Coordinación PR-1

PR-1 + PR-2 cohesivos:

| Aspecto | PR-1 | PR-2 |
|---|---|---|
| Endpoint API | Crea `POST /copilot/suggestions` + `/accept` | Sin cambios shape |
| FE | Consume real engine (drop stub) | Sin cambios |
| Engine | Sin cambios | Sin cambios |
| Providers registrados | 1 (offer) | 4 (offer + brand + sales + copilot) |
| Anchor reuso | `[COPILOT-SUGGESTIONS-ENGINE]` | `[COPILOT-SUGGESTIONS-ENGINE]` |
| Ratchet | 22 frozen, sin cambios | 22 frozen, sin cambios |

**Sin shape coupling**. PR-1 y PR-2 pueden mergear en cualquier orden. Cuando ambos están en main:
- FE smart-chips funcionan en `/offer-studio*` (PR-1 + offer provider)
- FE smart-chips funcionan en `/brand-studio*` (PR-1 + brand provider PR-2)
- FE smart-chips funcionan en `/sales*` (PR-1 + sales provider PR-2)
- FE smart-chips funcionan en `/` y otras rutas (PR-1 + copilot fallback PR-2)

**Sesión paralela** (PR-1 trabaja `copilot/api/suggestions.py`, FE `voice-api.ts`). PR-2 NO toca esos archivos. Cero conflicto filesystem. Regla M8 aplica: si descubris que PR-1 también modifica `_bootstrap_builtin` o `engine.py`, STOP + escalar a Chris.

## 20. Builder Execution Plan

Builder BE ejecuta en SECUENCIAL (no paralelo intra-PR — todos archivos BE):

1. **Crear ports** (no builder activity en otros archivos coupling):
   - `backend/src/shared/links/ports/sales_agent.py` (NEW — D-6)
   - `backend/src/shared/links/ports/brand.py` (EXTEND — D-8)
2. **Crear adapters**:
   - `backend/src/modules/sales_agent/application/services/observability_adapter.py` (NEW — D-6)
   - `backend/src/modules/brand/application/services/brand_data_adapter.py` (EXTEND — D-8)
3. **Tests adapters RED → GREEN**:
   - `test_observability_adapter.py` + `test_brand_data_adapter_pr2.py`
4. **Crear providers** (RED tests primero):
   - Tests: `test_brand_provider.py`, `test_sales_agent_provider.py`, `test_copilot_provider.py` (RED, mock ports)
   - Impl: `brand.py`, `sales_agent.py`, `copilot.py` (GREEN)
5. **Update registry**:
   - `registry.py::_bootstrap_builtin` (D-9)
   - Test: `test_registry_with_4_providers.py` GREEN
6. **Engine integration test**:
   - `test_engine_with_4_providers.py` GREEN
7. **Refactor offer_section_tools.py** (D-7):
   - Test RED: `test_offer_section_tools_refactor.py`
   - Impl: modify `_no_data_response` + `_ok_response` helpers
   - Test GREEN
   - Verificar tests pre-existentes de tools sigan verdes (no regresión)
8. **Arch tests verificación**:
   - `cd backend && .venv/bin/pytest tests/architecture/ -x -q`
   - **DEBE PASS** sin bumpear ratchet 22.
9. **Lint / format / type check native**:
   - `cd backend && .venv/bin/ruff check src/modules/copilot/ src/shared/links/ports/sales_agent.py src/modules/sales_agent/application/services/observability_adapter.py src/modules/brand/application/services/brand_data_adapter.py`
   - `cd backend && .venv/bin/ruff format --check src/modules/copilot/ ...`
10. **Commit conventional**:
    - 1 commit: `feat(copilot-suggestions): add brand+sales+copilot providers + pure expansion offer_section_tools`
    - O 2 commits si builder prefiere (ports/adapters separados de providers/tools)

**Auto-loop audit** (auditor):
1. Verifica grep `"suggestions": [hint]` = 0 hits en `offer_section_tools.py`
2. Verifica `len(KNOWN_COPILOT_TO_MODULE_IMPORTS) == 22` (ratchet inalterado)
3. Verifica anchor cap 36/36 (no nuevo `[COPILOT-*]`)
4. Verifica chips Spanish neutro LatAm (grep voseo en archivos providers)
5. Verifica tests cobertura ≥80% nuevos files
6. Verifica `EnrollmentSummaryDTO` sin PII fields (no contact_id, no payment_link_url)

## 21. Research Notes

Sin patterns nuevos. Todas decisiones backed por:

- Stack existente (FastAPI async + SA 2.0 + Pydantic v2 + structlog) — patterns establecidos en `OfferSuggestionProvider` + `OfferSuggestionReader` + `BrandDataAdapter`
- Skill `copilot-expert` ratchet status 22 frozen + anchor cap 36/36 + best-effort observability + §3 sales_agent protection
- Skill `brand-expert` SSoT BrandSettings JSONB + 11-aggregates mental model + PersonalityProfile 3-pilar separación
- Skill `sales-agent-expert` §3 protect rules + observability tables shape (enrollments + messages_sales_agent)
- Skill `backend-expert` Pydantic v2 + SA 2.0 + tenant_id mandatory
- Verificación directa código pre-existente (no hipótesis):
  - `engine.py:62` — sync `get_suggestions` retorna `(list, dict, int)`
  - `engine.py:77-82` — route prefix matching exact
  - `registry.py:44-50` — `_bootstrap_builtin` injection point
  - `providers/offer.py:36` — pattern provider class shape
  - `services/offer_suggestion_reader.py` — pattern reader companion
  - `shared/links/ports/brand.py:34-71` — port shape + factory
  - `shared/links/ports/offer.py` — port pattern lazy imports
  - `tests/architecture/test_no_new_copilot_module_imports.py:50-77` — 22 frozen entries
  - `tools/offer_section_tools.py:155-167` — `_no_data_response` único literal

## Open Questions for PM

**ZERO.** Architect-empowered. Todas las decisiones tomadas y justificadas en §1.

---

<!-- @pm: CONTRACT.md ready (architect-empowered). -->
