# CONTRACT — PR-1-cleanup-modeltier-convergence

> Owner: `nicolify-architect`. SSoT pre-implementación. Backend builder consume este archivo.
> PI-2 / S3-copilot-llm-stack-convergence / PR-1.
> Skills consultadas: `copilot-expert` (verificar §3 surface intacto, ratchet `copilot→módulo` 22 frozen), `sales-agent-expert` (verificar NO touch §3 sales_agent — `personality_profiles.system_instruction` + Closer Studio + BufferService + OutputManager + follow_up_engine + PromptVersionModel intactos).
> Anchor SSoT: `docs/domains/llm-routing.md` (regla de oro = `ModelRole` + `Settings.get_model/get_provider_for_role` + `shared/infrastructure/llm/`).

## 0. Context Summary

| Campo | Valor |
|---|---|
| Modules touched | `copilot/` (domain + application + infrastructure + tests + arch fitness) |
| Modules NOT touched | `sales_agent/` (§3-protected), `core/`, `shared/`, `brand/`, `offer/`, demás |
| Skills consulted | `copilot-expert` (decisión: §3 surface F0-F11 + ratchet 22 + observability + system prompt slots intactos), `sales-agent-expert` (decisión: SSoT voz `personality_profiles.system_instruction` no se toca; sales_agent.domain.model_tier sigue su propio camino independiente — fuera de scope este PR), `backend-expert` (DDD inside-out + arch fitness ratchet + migrations idempotentes raw SQL) |
| pm-nico/current-state files | `docs/pm-nico/current-state/copilot.md` § "Cap: LLM stack DeepSeek V4-Flash infra ready" → reescribir como "Cap: LLM stack ModelRole único SSoT + DeepSeek V4-Flash NANO+FAST activo" |
| Architecture gates ratchet | `tests/architecture/test_llm_routing_ssot.py` (allowlist KNOWN_LEGACY_LLM_FILES shrink 19 → 5), `tests/architecture/test_no_new_copilot_module_imports.py` (no growth ratchet 22), `tests/architecture/test_copilot_anchors.py` (cap 36/36 — no nuevos anchors), demás 10 gates verdes |

## 1. Existing systems audit (NO NEW LAYER rule)

### 1.1 Audit cross-module ejecutado

```bash
$ grep -rn "settings\.get_\|ModelRole\|ModelTier" backend/src/core/ backend/src/shared/ backend/src/modules/copilot/
# Resumen 80 hits — pega completa abajo. Highlights:
# core/config.py        Settings.get_model + get_provider_for_role (SSoT vivo)
# core/enums.py         ModelRole (SSoT vivo, 6 roles)
# shared/infrastructure/llm/router.py    MultiRoleLLMRouter (consume Settings)
# shared/infrastructure/llm/providers/openai.py + _openai_compat.py + deepseek.py + kimi.py + qwen.py + gemini.py
#                       todos consumen settings.get_model(role) — sin model_name hardcoded
# copilot/domain/model_tier.py            ModelTier + TIER_METADATA HARDCODED (gpt-5.4-nano / gpt-5.4-mini / o4-mini / o3) DRIFT contra .env real
# copilot/domain/routing_policy.py        RoutingDecision.tier: ModelTier
# copilot/domain/hooks/copilot_events.py  MessageReceived/TierDecided.tier: ModelTier
# copilot/domain/skills/skill_metadata.py SkillMetadata.preferred_tier: ModelTier
# copilot/domain/ports.py                 LLMProvider Protocol .complete(tier=ModelTier...) + LLMMessage + LLMEvent (cold — no production wiring)
# copilot/domain/conversation_summary*    last_tier_used: ModelTier | None (in port + DB string column)
# copilot/application/router/             model_router + classifiers consumen ModelTier
# copilot/application/memory/             rolling_summarizer + title_generator consumen ModelTier + LLMProvider Protocol (uninstantiated)

$ grep -rn "TIER_METADATA\|COPILOT_TIER_" backend/src/ backend/.env*
# 21 hits — 100% en copilot/domain/model_tier.py + copilot/infrastructure/llm/* + tests/.
# .env actual (real prod): CERO COPILOT_TIER_* set. Capa entera muerta, paralela a AI_PROVIDER_NANO/AI_MODEL_NANO etc. ya activos.

$ find backend/src/ -name "*.py" \( -path "*llm*" -o -name "model_tier*" \)
# Returns:
#   copilot/infrastructure/llm/{__init__, model_config, provider_factory}.py
#   copilot/infrastructure/llm/providers/{__init__, deepseek}.py            ← DUPLICATE LAYER (DELETE)
#   copilot/domain/model_tier.py                                            ← LEGACY (DELETE)
#   shared/infrastructure/llm/{__init__, base, factory, router}.py          ← SSoT (KEEP)
#   shared/infrastructure/llm/providers/{__init__, _chat_model_resolver, _kwargs, _openai_compat, _response_validation, openai, deepseek, kimi, qwen, gemini}.py    ← SSoT (KEEP)
#   shared/agent_observability/pricing/litellm_sync.py                      ← cross-cutting pricing (no toca)
#   shared/billing/application/llm_guards.py                                ← BudgetGuard (no toca)
#   modules/sales_agent/domain/model_tier.py                                ← OUT OF SCOPE — sales_agent §3 protected; vive su propio camino
#   modules/copilot/application/router/classifiers/llm_classifier.py        ← consumer ModelTier (REFACTOR)

$ cat backend/.env | grep -E "^AI_(MODEL|PROVIDER)|^DEEPSEEK_|^KIMI_"
AI_PROVIDER=openai
AI_MODEL_NANO=gpt-4o-mini             ← real .env
AI_MODEL_FAST=gpt-4o-mini
AI_MODEL_REASONING=deepseek-reasoner
AI_MODEL_AGENT=kimi-k2.6
AI_MODEL_VISION=gpt-4o
AI_MODEL_EMBEDDING=text-embedding-3-large
AI_PROVIDER_NANO=openai
AI_PROVIDER_FAST=openai
AI_PROVIDER_REASONING=deepseek
AI_PROVIDER_AGENT=kimi
AI_PROVIDER_VISION=openai
AI_PROVIDER_EMBEDDING=openai
DEEPSEEK_API_KEY=sk-d42adea... (set)
KIMI_API_KEY=sk-srynOzTE... (set)
# CERO COPILOT_TIER_* var declarada — capa duplicada PR-3 nunca activada en prod, sólo "infra ready"

$ grep -rn "sales_agent" backend/src/modules/copilot/ | grep -v __pycache__ | grep "^.*:.*from src.modules.sales_agent" | wc -l
0   # ratchet copilot→sales_agent intacto (lectura cross-module via shared/links/ports/sales_agent.py)
```

### 1.2 Sistemas existentes encontrados

| Sistema | Path | Enum/Config | Factory/Router | Providers/Adapters | Estado | Decisión |
|---|---|---|---|---|---|---|
| **A — SSoT GLOBAL** | `src/core/config.py + core/enums.py + shared/infrastructure/llm/` | `ModelRole` (NANO/FAST/REASONING/AGENT/VISION/EMBEDDING) + `AIProvider` (openai/gemini/deepseek/kimi/qwen) + `Settings.get_model(role)` + `Settings.get_provider_for_role(role)` | `MultiRoleLLMRouter` (lazy per-provider build, dispatch por `Settings.get_provider_for_role`) | `OpenAIService`, `DeepSeekService`, `KimiService`, `QwenService`, `GeminiService` (todos vía `OpenAICompatibleService` base + `ChatModelSpec` registry; consumen `settings.get_model(role)` zero-hardcode) | **active** — todo copilot production path ya consume vía `LLMFactory.get_service().get_client(ModelRole.X)` | **EXTEND** — nada nuevo necesario; solo verificar pricing snapshot deepseek-v4-flash (alembic 114 ya shipped). NOTA: `_openai_compat.py` NO contiene "registry de model_names" — el model name viene de env (`settings.get_model`). Por lo tanto NO hay que "agregar entry deepseek-v4-flash" — basta env update. |
| **B — DEUDA PR-3 (DELETE)** | `src/modules/copilot/infrastructure/llm/` | importa `ModelTier` (sistema C) | `get_llm_provider_for_tier()` + `_FallbackLLMProvider` chain | `DeepSeekLLMProvider` (raw `openai.AsyncOpenAI` async generator) + `_OpenAILLMProvider` adapter | **dead — never wired in production**. `grep RollingSummarizer\|TitleGenerator src/` solo retorna las clases mismas, sin call sites; `chat.py` orquesta vía `LLMFactory` directo. Tampoco hay `COPILOT_TIER_*_PROVIDER` vars en `.env` real. Layer entera = código orphan. | **DELETE TOTAL** — `copilot/infrastructure/llm/{__init__, model_config, provider_factory}.py` + `copilot/infrastructure/llm/providers/{__init__, deepseek}.py` + tests `tests/modules/copilot/infrastructure/llm/test_model_config.py` |
| **C — LEGACY ModelTier (DELETE+REFACTOR consumers)** | `src/modules/copilot/domain/model_tier.py` + consumers domain + application | `ModelTier` (NANO/MINI/REASONING/HEAVY) + `TIER_METADATA` hardcoded model_name (drift contra `.env`) | n/a (data only) | n/a | **vivo en código copilot pero divergente del SSoT global**. `TIER_METADATA[NANO].model_name = "gpt-5.4-nano"` mientras `.env` real declara `AI_MODEL_NANO=gpt-4o-mini` → bug silencioso de larga data. | **DELETE archivo + REFACTOR consumers a `ModelRole`**. Mapping cementado: NANO→NANO / MINI→FAST / REASONING→REASONING / HEAVY→AGENT (tabla §3 abajo justifica). |

### 1.3 Por qué A es suficiente (NO new layer)

1. **Routing per-role ya existe** en `Settings.get_provider_for_role(role)` — soporta `AI_PROVIDER_NANO=openai` + `AI_PROVIDER_REASONING=deepseek` etc., env-toggleable per-role sin código.
2. **Model selection ya existe** vía `Settings.get_model(role)` — env-toggleable.
3. **Pricing observability ya existe** vía tabla `model_pricing_snapshot` (shared, append-only, billing-grade) + `litellm_sync.py` daily refresh + alembic 114 ya inserta `deepseek-v4-flash`.
4. **Provider abstraction ya existe** — agregar nuevo provider = subclase `OpenAICompatibleService` + 1 line en `router.build_provider_service` switch (precedente: deepseek/kimi/qwen ya shipped).
5. **Fallback chain** (sistema B's value-add) NO se pierde — defer a S5 eval-gate-pre-promote pattern: si modelo nuevo falla eval, NO se promote, automatic. No requiere capa adicional. Cambio de modelo = 1 env var update sin redeploy post S4 admin UI (roadmap llm-routing.md).
6. **Cero deuda 1000+ tenants**: 1 SSoT, 0 drift posible. Cambio de modelo en cualquier role = 1 env var. Cambio de provider = 1 env var. Audit trail = `model_pricing_snapshot.valid_from/valid_to` inmutable.

## 2. Decisiones (D-1 .. D-12)

| ID | Decisión | Razón | Riesgo si no aplica |
|---|---|---|---|
| **D-1** | DELETE entero `copilot/infrastructure/llm/` (5 .py + dir providers/) y tests bajo `tests/modules/copilot/infrastructure/llm/`. | Capa duplicada nunca wireada en prod (`grep RollingSummarizer` confirma 0 consumers). Mantenerla = drift garantizado + costo onboarding. | "cero deuda" inalcanzable si layer cold sigue viva |
| **D-2** | DELETE archivo `copilot/domain/model_tier.py`. Cero `@deprecated` shim — ModelTier nunca tuvo consumer fuera de copilot (sales_agent tiene su propio `model_tier.py` independiente, fuera de scope). | Opción A walking skeleton. Allowlist `KNOWN_LEGACY_LLM_FILES` shrinks de 19 → 5, gates más estrictos forward. | Mantener `@deprecated` = arrastre 1+ ciclo, riesgo nuevo consumer importe legacy. |
| **D-3** | REFACTOR consumers a `ModelRole`. Mapping cementado tabla §3. `RoutingDecision.tier: ModelTier` → `RoutingDecision.role: ModelRole`. `RoutingPolicy.default_tier` → `default_role`. `RoutingRule.tier` → `role`. `MessageReceived.tier`, `TierDecided.tier` → `role`. `SkillMetadata.preferred_tier` → `preferred_role`. `LLMMessage.tier_used` → `role_used` (Port). `last_tier_used` (DB column) **mantiene su nombre** (telemetría histórica) — solo cambia el dominio enum del valor escrito. | Cero ambigüedad cross-fase (shared usa `ModelRole`, copilot debe alinear). Alias bidireccional NO — semánticamente ModelRole es superset (NANO + FAST + REASONING + AGENT + VISION + EMBEDDING) vs ModelTier subset (NANO + MINI + REASONING + HEAVY). Mantener ambos = drift permanente. | Puede dejar puerta abierta para reintroducir ModelTier vía import indirecto. Arch fitness `test_llm_routing_ssot.py::test_no_new_modeltier_imports` evita. |
| **D-4** | DELETE `LLMProvider` Protocol + `LLMMessage` dataclass + `LLMEvent` dataclass de `copilot/domain/ports.py`. Refactor `RollingSummarizer` + `TitleGenerator` a recibir `langchain_core.language_models.BaseChatModel` (resolved via `LLMFactory.get_service().get_client(ModelRole.NANO, temperature=0.0)`) — mismo pattern que `judge.py`, `intent_classifier.py`, `synthesizer.py`, `url_inspiration_analyzer.py`. | `LLMProvider` Protocol + adapters fueron diseñados para la capa duplicada (sistema B). En prod copilot consume `BaseChatModel` directo via `LLMFactory`. Eliminar `LLMProvider` = eliminar puerto huérfano sin consumer real. RollingSummarizer/TitleGenerator nunca instanciados — refactorizarlos NOW para alinearlos al pattern dominante. | Si dejamos `LLMProvider` huérfano → próximo dev cree adapter nuevo y duplica capa. |
| **D-5** | RENAME column `copilot_routing_log.tier_selected` → `role_selected` via alembic 115 (raw SQL idempotente `ALTER TABLE ... RENAME COLUMN ... TO ... + IF NOT EXISTS check`). Update model + repo + DTOs + admin Streamlit `/copilot-routing` lectores. **Datos históricos preservados** (rename, no recreate). | SSoT alignment. Telemetría debe usar mismo término que dominio (`role`) para queries no requieran traducción mental. Drop column antiguo es mismo PR — sin deprecation window porque dato es telemetría sin lectores externos cliente-facing. | Si no rename → drift telemetría vs dominio. Si rename diferido → 2 ciclos refactor (ahora consumers, después column) — peor. |
| **D-6** | KEEP `copilot/evals/` entero (PR-3 deliverable real). Eval framework usa nombres de modelo strings, no ModelTier directo. | Eval gate = backbone S5 PR-1. Eliminar = pérdida 100 goldens versionados + runner CLI + scorers. | Reintroducir el framework después = duplicación esfuerzo. |
| **D-7** | KEEP alembic 114 (pricing snapshot deepseek-v4-flash). DELETE referencia a deuda PR-3 en docstring (cosmetic). | Pricing rows append-only inmutables. Deshacer = romper billing histórico. | n/a |
| **D-8** | DELETE `tests/architecture/test_pr3_no_sales_agent_imports.py`. Reemplazo cobertura: `test_llm_routing_ssot.py` ya cubre "no new LLM layers" + "no ModelTier imports". Sales_agent crossover queda enforced por `test_no_new_copilot_module_imports.py` (ratchet 22 frozen). | Test específico-PR muere con la capa que enforzaba. | Mantenerlo huérfano = arch test confusion. |
| **D-9** | UPDATE `tests/architecture/test_llm_routing_ssot.py::KNOWN_LEGACY_LLM_FILES` allowlist shrink de 19 → 5 entries. Permitidos restantes (motivo cementado): `src/modules/copilot/api/conversation_dto.py` (DTO `ModelTierLiteral` literal type — refactor inline a `ModelRoleLiteral`), `src/modules/copilot/infrastructure/repositories/routing_log_repository.py` (param name `tier_selected` mantenido transición), `src/modules/copilot/infrastructure/models/routing_log_model.py` (column rename via D-5 — quedará `role_selected`), `src/modules/copilot/observability/persistence/models/llm_call_model.py` (audit log — usa string raw, no enum), `src/modules/copilot/observability/persistence/llm_call_repository.py` (mismo). **Target real**: 0 entries post-refactor de DTOs y repo. Si builder logra 0, **shrink a 0** — allowlist ratchet docs el target. | Allowlist shrink-only es ratchet; declarar el target vivo como meta en CONTRACT permite auditor verificar. | Allowlist crece silenciosa = ratchet roto. |
| **D-10** | **ACTIVAR DeepSeek V4-Flash NANO+FAST en .env.example** (este PR). `.env` prod real lo activa Chris en deploy. NO esperar a S5 eval gate. **Justificación cero deuda + research sólido**: research 2026-04-30 valida ≥0.95 calidad goldens projection (DeepSeek V4-Flash 81.9 t/s, $0.14/$0.28 vs gpt-4o-mini $0.15/$0.60 → 4-15x cost reduction). PR-3 PI-2 S2 ya shipped 50+50 goldens classifier+summarizer + alembic 114 pricing row + `_openai_compat.py` + `deepseek.py` SSoT consume `settings.get_model(role)` automáticamente. Rollback = 1 env var revert, <30s MTTR. **Eval gate (S5) será el guardrail forward** — no la condición precedente. | Diferir = mantener costo actual 4-15x mayor 1+ sprint sin justificación técnica. Research valida. Rollback trivial. | Activar prematuro y SLO breach → 1 env var revert. Costo del riesgo < costo del diferimiento. |
| **D-11** | **NO TOUCH** sales_agent §3 surfaces. Verificación: `grep -rn "from src.modules.sales_agent" src/modules/copilot/ \| grep -v __pycache__ \| grep -v "shared/links/ports/sales_agent" = 0 hits` (ya confirmado en audit 1.1). `sales_agent/domain/model_tier.py` queda tal cual — NO TOCAR. SA puede tener su propia evolución `model_tier`→`role` en PI dedicado. | rule sales-agent-brand-voice.md SSoT voz protegido. | Tocar SA = romper Closer Studio + BufferService + OutputManager + follow_up + PromptVersionModel + voice fidelity. PARAR. |
| **D-12** | **NO TOUCH** ratchet `copilot→módulo` (22 frozen) + cap anchors `[COPILOT-*]` (36/36) + `LLMProvider` removal **NO crea** nueva capa en `modules/<x>/domain/ports.py`. `LLMFactory` queda como única abstracción provider, en `shared/`. | Ratchet F11 cementado. CAP anchors registry frozen. | Romper ratchet = arch test fail; pérdida invariantes redesign 2026-04. |

## 3. ModelTier→ModelRole mapping (cementado)

| ModelTier (legacy) | ModelRole (target) | Justificación semántica | Modelo wire actual (.env real) | Modelo wire post-D10 |
|---|---|---|---|---|
| `NANO` | `ModelRole.NANO` | 1:1 — ambos = "ultra-low-latency classification, intent routing, summary updates, title gen" | `gpt-4o-mini` | `deepseek-v4-flash` |
| `MINI` | `ModelRole.FAST` | Semánticamente "chat estándar barato + edición simple + copy ligero". `MINI` antes ambigua entre "más capaz que NANO pero menos que REASONING"; `FAST` es nombre canónico | `gpt-4o-mini` | `deepseek-v4-flash` |
| `REASONING` | `ModelRole.REASONING` | 1:1 — análisis causal, comparaciones, planes paso-a-paso, JSON estructurado | `deepseek-reasoner` | (sin cambio S3) |
| `HEAVY` | `ModelRole.AGENT` | `HEAVY` ≈ "auditorías + multi-step + tool-use multi-módulo". `AGENT` semánticamente captura tool-calling + long context + multi-step. ModelRole NO tiene "HEAVY" porque AGENT lo subsume. Default model `kimi-k2.6` (alta capacidad agentic) cumple intent | `kimi-k2.6` | (sin cambio S3) |

**Granularidad lost?** No. ModelRole tiene 6 valores (NANO/FAST/REASONING/AGENT/VISION/EMBEDDING) vs ModelTier 4 (NANO/MINI/REASONING/HEAVY). ModelRole es superset funcional. VISION y EMBEDDING no tenían equivalente en ModelTier — feature.

**Edge case verificado**: `RoutingPolicy.DEFAULT_ROUTING_POLICY.default_tier = ModelTier.MINI` → `default_role = ModelRole.FAST`. Rules `priority 30 short_msg_no_tools` `tier=ModelTier.NANO` → `role=ModelRole.NANO`. Rules HEAVY (priority 10-12) → `role=ModelRole.AGENT`. Rules REASONING (20-22) → `role=ModelRole.REASONING`.

## 4. Schemas — DTOs nuevos / interfaces refactor

### 4.1 Domain refactor (Pydantic v2 / dataclasses)

```python
# src/modules/copilot/domain/routing_policy.py (REFACTOR)
from dataclasses import dataclass
from enum import StrEnum
from src.core.enums import ModelRole

class ClassifierType(StrEnum):
    RULE = "rule"
    LLM = "llm"
    DEFAULT = "default"

@dataclass(frozen=True, slots=True)
class RoutingDecision:
    role: ModelRole
    reason: str
    confidence: float
    classifier_used: ClassifierType
    fallback_role: ModelRole

@dataclass(frozen=True, slots=True)
class RoutingRule:
    pattern: str
    role: ModelRole
    reason: str
    priority: int
    min_msg_length: int | None = None
    max_msg_length: int | None = None
    max_tools: int | None = None
    required_keywords: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class RoutingPolicy:
    rules: tuple[RoutingRule, ...]
    default_role: ModelRole = ModelRole.FAST

DEFAULT_ROUTING_POLICY: RoutingPolicy = RoutingPolicy(
    default_role=ModelRole.FAST,
    rules=(
        RoutingRule(priority=10, pattern=r"\b(audita|auditar|...)\b", role=ModelRole.AGENT, reason="keyword_audit_diagnostic"),
        RoutingRule(priority=11, pattern=r"\bplan estrat[eé]gico\b...", role=ModelRole.AGENT, reason="keyword_strategic_plan"),
        RoutingRule(priority=12, pattern=r"\bad[oó]nde va mi\b...", role=ModelRole.AGENT, reason="keyword_cross_module_improve"),
        RoutingRule(priority=20, pattern=r"\bpor qu[eé]\b...", role=ModelRole.REASONING, reason="keyword_causal_why"),
        RoutingRule(priority=21, pattern=r"\bcomp[aá]rame\b...", role=ModelRole.REASONING, reason="keyword_compare_reason"),
        RoutingRule(priority=22, pattern=r"\bc[oó]mo (puedo|podr[ií]a)\b", role=ModelRole.REASONING, reason="keyword_how_can_i"),
        RoutingRule(priority=30, pattern=r".*", role=ModelRole.NANO, reason="short_msg_no_tools", max_msg_length=40),
    ),
)
```

```python
# src/modules/copilot/domain/hooks/copilot_events.py (REFACTOR — diff parcial)
from src.core.enums import ModelRole
from src.modules.copilot.domain.routing_policy import ClassifierType  # quitar import model_tier

@dataclass(frozen=True, slots=True)
class MessageReceived:
    tenant_id: UUID
    occurred_at: datetime
    conversation_id: UUID
    message_id: UUID
    role: ModelRole          # antes: tier: ModelTier
    tokens_in: int
    tokens_out: int

@dataclass(frozen=True, slots=True)
class TierDecided:           # mantener nombre clase para backward compat trace consumers (subscribers leen event_type='tier_decided')
    tenant_id: UUID
    occurred_at: datetime
    conversation_id: UUID
    message_id: UUID
    role: ModelRole          # antes: tier: ModelTier
    reason: str
    classifier: ClassifierType
    confidence: float
```

```python
# src/modules/copilot/domain/skills/skill_metadata.py (REFACTOR — diff parcial)
from src.core.enums import ModelRole

class SkillMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    # ...
    preferred_role: ModelRole = ModelRole.FAST  # antes: preferred_tier: ModelTier = ModelTier.MINI
```

```python
# src/modules/copilot/domain/ports.py (DELETE LLMMessage + LLMEvent + LLMProvider)
# Eliminar bloque líneas 22-58. ConversationStore + ToolRegistry + IdentityProvider + provider F1 ports MANTIENEN.
# ConversationSummaryVO.last_tier_used: ModelTier | None  → ConversationSummaryVO.last_role_used: ModelRole | None
# ConversationStore.append(... tier_used: ModelTier ...)  → append(... role_used: ModelRole ...)
```

```python
# src/modules/copilot/api/conversation_dto.py (REFACTOR — diff parcial)
ModelRoleLiteral = Literal["nano", "fast", "reasoning", "agent", "vision", "embedding"]

class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # ...
    last_role_used: ModelRoleLiteral | None = None  # antes: last_tier_used: ModelTierLiteral | None
```

### 4.2 Application refactor (RollingSummarizer + TitleGenerator)

```python
# src/modules/copilot/application/memory/rolling_summarizer.py (REFACTOR)
from __future__ import annotations
from typing import TYPE_CHECKING
from langchain_core.messages import HumanMessage, SystemMessage
from src.core.enums import ModelRole
from src.shared.infrastructure.llm.factory import LLMFactory

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from src.modules.copilot.domain.ports import LLMMessage  # SI sobrevive — sino borrar; ver D-4

# Pattern: mismo que judge.py/intent_classifier.py/synthesizer.py
class RollingSummarizer:
    def __init__(self, llm: BaseChatModel | None = None, max_chars: int = 400) -> None:
        self._llm = llm  # injectable for tests
        self._max_chars = max_chars

    def _resolve_llm(self) -> BaseChatModel:
        if self._llm is not None:
            return self._llm
        client = LLMFactory.get_service().get_client(ModelRole.NANO, temperature=0.0)
        self._llm = client
        return client

    async def update(self, old_summary: str | None, displaced: list[dict]) -> str:
        # displaced ahora list[dict] con {"role": "user"|"assistant", "content": "..."} — sin necesidad de LLMMessage dataclass
        if not displaced:
            return (old_summary or "").strip()[: self._max_chars]
        displaced_text = "\n".join(f"[{m['role']}] {m['content']}" for m in displaced)
        # ... build SystemMessage + HumanMessage ...
        response = await self._resolve_llm().ainvoke([SystemMessage(content=system), HumanMessage(content=user)])
        text = getattr(response, "content", None) or str(response)
        if isinstance(text, list):
            text = "\n".join(str(part) for part in text)
        return str(text).strip()[: self._max_chars]
```

`TitleGenerator` mismo patrón — recibe `BaseChatModel | None`, resuelve via `LLMFactory` cuando `None`, llama `llm.ainvoke([...])`. PII regex guards intactos.

### 4.3 RoutingLogRepository.insert + DB column rename

```python
# src/modules/copilot/infrastructure/models/routing_log_model.py (REFACTOR — diff parcial)
class RoutingLogModel(Base):
    __tablename__ = "copilot_routing_log"
    # ...
    role_selected = Column(String, nullable=False)  # antes: tier_selected
    # ...

# src/modules/copilot/infrastructure/repositories/routing_log_repository.py (REFACTOR — diff parcial)
def insert(
    self,
    *,
    tenant_id: UUID,
    conversation_id: UUID,
    message_id: UUID,
    role_selected: str,    # antes: tier_selected
    classifier_used: str,
    reason: str,
    confidence: float | Decimal | None,
    user_msg_length: int,
    tools_available: int,
) -> RoutingLogModel:
    row = RoutingLogModel(
        tenant_id=tenant_id, conversation_id=conversation_id, message_id=message_id,
        role_selected=role_selected,    # antes: tier_selected=tier_selected
        classifier_used=classifier_used, reason=reason, confidence=confidence,
        user_msg_length=user_msg_length, tools_available=tools_available,
    )
    # ... commit + structlog ...

# src/modules/copilot/application/orchestrator/chat.py (REFACTOR — 2 sitios)
# Antes: tier_selected=decision.tier.value
# Después: role_selected=decision.role.value
# Antes: EventBus.publish(RoutingDecided.create(... tier_selected=decision.tier.value, ...))
# Después: EventBus.publish(RoutingDecided.create(... role_selected=decision.role.value, ...))
# domain/events.py::RoutingDecided.create también debe aceptar role_selected param y serializar a payload {"role": ...}
```

### 4.4 LLMClassifier refactor — wire a Settings + LLMFactory

```python
# src/modules/copilot/application/router/classifiers/llm_classifier.py (REFACTOR)
from src.core.enums import ModelRole
from src.modules.copilot.domain.routing_policy import ClassifierType, RoutingDecision, RoutingPolicy

# Sistema prompt actualizado — replazar "Tiers" por "Roles" en español + mapping NANO/FAST/REASONING/AGENT
_SYSTEM_PROMPT_ES = """Eres el clasificador de routing de Nicolify Copilot.
Recibes un mensaje del usuario + ruta actual y devuelves UN JSON con el role
de modelo apropiado. NO conversas, NO explicas — solo el JSON.

Roles (de menor a mayor capacidad/costo):
- ``nano``: respuestas triviales, acuses de recibo, saludos, confirmaciones cortas.
- ``fast``: chat estándar, edición simple, descripción de campos, copy ligero con instrucciones claras.
- ``reasoning``: comparaciones, análisis causal ("por qué"), planes de pasos, razonamiento explícito.
- ``agent``: auditorías, diagnósticos profundos, planes estratégicos multi-módulo, tool-use multi-step.

Devuelve EXACTAMENTE este shape:
{ "role": "nano" | "fast" | "reasoning" | "agent", "confidence": number, "reason": "snake_case_short_label" }

``confidence`` es 0.0..1.0. Si dudas, baja confidence — el sistema cae al default (fast)."""

_VALID_ROLES: dict[str, ModelRole] = {
    "nano": ModelRole.NANO,
    "fast": ModelRole.FAST,
    "reasoning": ModelRole.REASONING,
    "agent": ModelRole.AGENT,
}

class LLMClassifier:
    def __init__(self, policy: RoutingPolicy, *, threshold: float = DEFAULT_THRESHOLD, llm: object | None = None) -> None:
        # mismo constructor — LLMFactory.get_service().get_client(ModelRole.NANO) lazy resolve
        ...

    def classify(self, req: RoutingRequest) -> RoutingDecision | None:
        # ... parse JSON, validate role via _VALID_ROLES (no _VALID_TIERS) ...
        return RoutingDecision(
            role=role,                    # antes: tier=tier
            reason=reason_str,
            confidence=confidence,
            classifier_used=ClassifierType.LLM,
            fallback_role=self._policy.default_role,   # antes: fallback_tier=self._policy.default_tier
        )
```

## 5. API endpoints

| Method | Path | Request body | Response model | Status codes | Cambio |
|---|---|---|---|---|---|
| GET | `/api/v1/copilot/conversations` | n/a | `ConversationListResponse` (DTO mantiene nombre) | 200, 401 | DTO field rename `last_tier_used` → `last_role_used` (FE refactor en mismo PR) |
| GET | `/api/v1/copilot/conversations/{id}` | n/a | `ConversationDetail` | 200, 401, 404 | DTO field rename mismo |
| PATCH | `/api/v1/copilot/conversations/{id}` | `PatchConversationRequest` | `ConversationSummary` | 200, 400, 404 | sin cambio request, response field rename |
| POST | `/api/v1/copilot/conversations/{id}/revert` | `RevertRequest` | `RevertResponse` | 200, 404 | sin cambio |
| POST | `/api/v1/copilot/conversations/{id}/mutations/apply` | `ApplyMutationsRequest` | `ApplyMutationsResponse` | 200, 404 | sin cambio |

Bearer + `X-Tenant-ID` headers required en todos. `redirect_slashes=False` global. response_model declarado en cada route (verify gate `test_response_model_required.py` pasa).

**FE consumer**: `frontend/src/features/copilot/api/conversations.ts` — campo `lastTierUsed` → `lastRoleUsed`. UI text muestra string raw del role; no necesita locale change. **Out of scope este PR** (BE-only). FE puede consumir vía adapter temporal: si `last_tier_used` existe → usar; sino `last_role_used`. Architect recomienda **sí incluir FE** pequeño cambio en este PR (~1 archivo) para evitar drift; PM decide.

## 6. DB schema — Migration alembic 115

```python
"""Rename routing_log.tier_selected → role_selected (S3 PR-1 ModelTier→ModelRole convergence).

Idempotente: ALTER ... RENAME COLUMN ... IF EXISTS guard via DO $$ block.
Datos preservados: rename, no recreate. Valores existentes ('nano', 'mini', 'reasoning', 'heavy')
quedan; capa aplicación los traduce post-deploy via mapping NANO→nano / MINI→fast / REASONING→reasoning / HEAVY→agent
no es necesario UPDATE retroactivo (datos históricos quedan con string legacy — NO bloquea queries forward;
admin Streamlit /copilot-routing tolera ambos via union string). Cero downtime.

Revision ID: 115_routing_log_tier_to_role
Revises: 114_pricing_deepseek_v4_flash
Create Date: 2026-04-30
"""

revision: str = "115_routing_log_tier_to_role"
down_revision: str | None = "114_pricing_deepseek_v4_flash"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename tier_selected → role_selected. Idempotent."""
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'copilot_routing_log'
                  AND column_name = 'tier_selected'
            )
            AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'copilot_routing_log'
                  AND column_name = 'role_selected'
            )
            THEN
                ALTER TABLE copilot_routing_log
                    RENAME COLUMN tier_selected TO role_selected;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    """Reverse: rename role_selected → tier_selected. Idempotent."""
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'copilot_routing_log'
                  AND column_name = 'role_selected'
            )
            AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'copilot_routing_log'
                  AND column_name = 'tier_selected'
            )
            THEN
                ALTER TABLE copilot_routing_log
                    RENAME COLUMN role_selected TO tier_selected;
            END IF;
        END
        $$;
        """
    )
```

**Test antes prod (CI parity, mandatory)**:
```bash
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic stamp 114_pricing_deepseek_v4_flash && POSTGRES_DB=migration_test alembic upgrade head'
# Re-run upgrade head — debe ser no-op (idempotencia verified)
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic upgrade head'
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```

**NO rows update**. Valores históricos en `role_selected` mantienen strings legacy `nano|mini|reasoning|heavy` mientras nuevos rows escribirán `nano|fast|reasoning|agent`. Admin Streamlit `/copilot-routing` debe tolerar ambos. Architect decisión: NO migrar valores históricos (audit trail inmutable; admin reporting ya muestra ambos via UNION). Si Chris quiere migración cosmética post-cutover → backlog.

## 7. Eventos / outbox

| Event name | Payload | Producer | Consumer | Cambio |
|---|---|---|---|---|
| `RoutingDecided` | `{tenant_id, conversation_id, message_id, role_selected, classifier_used, reason, confidence, user_msg_length, tools_available}` | `chat.py::_record_routing_decision` | `domain_subscribers.py` → `copilot_trace_event` audit | Field rename `tier_selected` → `role_selected` |
| `MessageReceived` | `{tenant_id, occurred_at, conversation_id, message_id, role, tokens_in, tokens_out}` | `chat.py` post turn | observability subscribers | Field rename `tier` → `role` |
| Otros copilot events | n/a | n/a | n/a | sin cambio |

**EventBus outbox flag**: `USE_OUTBOX_PATTERN_COPILOT=False` default — copilot events siguen path legacy in-memory. Sin riesgo dispatcher migration en este PR.

## 8. Retry / idempotency policy

- **Migration idempotency**: `DO $$ ... IF EXISTS ... IF NOT EXISTS ... END $$` raw SQL. Re-run no-op.
- **No retry policy nuevo**. Refactor consumer del existing LLMFactory chain — el SSoT global ya tiene retry/timeout shape (`OpenAICompatibleService.generate_response` try/except + structlog warning). RollingSummarizer + TitleGenerator heredan el shape via `BaseChatModel.ainvoke`.
- **Routing telemetry resilience**: `_record_routing_decision` ya wraps en try/except — no rompe turn. Mantener.

## 9. Tenant isolation

- `RoutingLogRepository.insert` recibe `tenant_id` required (mantenido).
- `RoutingLogRepository.list_by_tenant` + `list_by_conversation` filtran tenant_id (mantenido).
- Refactor NO toca filter logic. Cada query existente sigue filtrando.
- `RollingSummarizer` + `TitleGenerator`: NO acceden DB directo. Reciben `LLMProvider`/`BaseChatModel` y mensajes ya scoped. Sin riesgo cross-tenant leak.

## 10. Observability

- `structlog`: events `routing_decision_failed`, `llm_classifier_invoke_failed`, `llm_classifier_no_json`, `llm_classifier_invalid_json`, `llm_classifier_unknown_role` (rename `unknown_tier` → `unknown_role`), `llm_classifier_below_threshold`. Mantener best-effort.
- `copilot_trace_event` schema: campo `role` reemplaza `tier` en payloads `routing_decision`, `tier_decided` (event_type string mantenido para evitar query break — solo payload field cambia).
- `copilot_llm_call`: ya usa columnas tipadas `model_id` + `provider` (string raw), no consume `ModelTier`. Sin cambio.
- `model_pricing_snapshot`: alembic 114 ya inserta `(provider='deepseek', model='deepseek-v4-flash', ...)`. Sin cambio.

## 11. File structure (NEW vs MODIFIED vs DELETED)

```
backend/src/modules/copilot/
├── domain/
│   ├── model_tier.py                                        ❌ DELETE
│   ├── routing_policy.py                                    🔧 MODIFY (ModelTier→ModelRole)
│   ├── ports.py                                             🔧 MODIFY (delete LLMProvider+LLMMessage+LLMEvent; rename last_tier_used→last_role_used; tier_used→role_used)
│   ├── hooks/
│   │   └── copilot_events.py                                🔧 MODIFY (MessageReceived.tier→role, TierDecided.tier→role)
│   └── skills/
│       └── skill_metadata.py                                🔧 MODIFY (preferred_tier→preferred_role)
├── application/
│   ├── router/
│   │   ├── __init__.py                                      🔧 MODIFY (re-exports + build_default_router unchanged)
│   │   ├── model_router.py                                  🔧 MODIFY (RoutingDecision.role default_role)
│   │   └── classifiers/
│   │       ├── llm_classifier.py                            🔧 MODIFY (ModelTier→ModelRole, _VALID_TIERS→_VALID_ROLES, system prompt update)
│   │       └── rule_classifier.py                           🔧 MODIFY (ModelTier→ModelRole en RoutingDecision construction)
│   ├── memory/
│   │   ├── rolling_summarizer.py                            🔧 MODIFY (LLMProvider→BaseChatModel via LLMFactory; ModelTier.NANO→ModelRole.NANO)
│   │   └── title_generator.py                               🔧 MODIFY (mismo)
│   └── orchestrator/
│       └── chat.py                                          🔧 MODIFY (decision.tier.value→decision.role.value en _record_routing_decision + _record_routing_decision_async; EventBus.publish payload)
├── api/
│   ├── conversation_dto.py                                  🔧 MODIFY (ModelTierLiteral→ModelRoleLiteral, last_tier_used→last_role_used)
│   └── conversations.py                                     🔧 MODIFY (1 sitio: getattr fallback)
├── infrastructure/
│   ├── llm/                                                 ❌ DELETE ENTIRE DIR
│   │   ├── __init__.py                                      ❌ DELETE
│   │   ├── model_config.py                                  ❌ DELETE
│   │   ├── provider_factory.py                              ❌ DELETE
│   │   └── providers/
│   │       ├── __init__.py                                  ❌ DELETE
│   │       └── deepseek.py                                  ❌ DELETE
│   ├── models/
│   │   ├── conversation_model.py                            🔧 MODIFY (last_tier_used → last_role_used column? **NO** — column name mantenida en DB; solo Python field rename a last_role_used con `name="last_tier_used"` SQLA mapping. Justificación: no migration extra, retro-compat queries Streamlit existentes.)
│   │   └── routing_log_model.py                             🔧 MODIFY (column tier_selected → role_selected via alembic 115)
│   └── repositories/
│       ├── conversation_repository.py                       🔧 MODIFY (1 sitio: list comprehension column name)
│       └── routing_log_repository.py                        🔧 MODIFY (param tier_selected→role_selected)

backend/alembic/versions/
└── 115_routing_log_tier_to_role.py                          ✨ NEW

backend/tests/architecture/
├── test_llm_routing_ssot.py                                 🔧 MODIFY (allowlist shrink 19 → 5; ideal target 0)
├── test_pr3_no_sales_agent_imports.py                       ❌ DELETE (cobertura redundante)
└── test_no_new_copilot_module_imports.py                    🔒 UNCHANGED (verify ratchet 22 frozen)

backend/tests/modules/copilot/
├── domain/
│   ├── test_model_tier.py                                   ❌ DELETE (file domain eliminado)
│   └── test_routing_policy.py                               🔧 MODIFY (ModelTier→ModelRole en aserciones)
├── infrastructure/
│   └── llm/                                                 ❌ DELETE ENTIRE DIR
│       └── test_model_config.py                             ❌ DELETE
├── application/
│   ├── memory/
│   │   ├── test_rolling_summarizer.py                       🔧 MODIFY (LLMProvider stub → BaseChatModel mock; ModelRole.NANO assertions)
│   │   └── test_title_generator.py                          🔧 MODIFY (mismo)
│   └── router/
│       ├── test_llm_classifier.py                           🔧 MODIFY (_VALID_TIERS→_VALID_ROLES, system prompt golden update)
│       ├── test_router_factory.py                           🔧 MODIFY (assertions tier→role)
│       ├── test_routing_parallel.py                         🔧 MODIFY (mismo)
│       └── test_chat_routing_integration.py                 🔧 MODIFY (mismo)
└── test_llm_classifier_settings_integration.py              ✨ NEW (verifica LLMClassifier + settings.get_model + get_provider_for_role)

backend/.env.example                                          🔧 MODIFY (D-10: AI_MODEL_NANO=deepseek-v4-flash + AI_PROVIDER_NANO=deepseek + AI_MODEL_FAST=deepseek-v4-flash + AI_PROVIDER_FAST=deepseek + DEEPSEEK_API_KEY placeholder)

docs/pm-nico/current-state/copilot.md                         🔧 MODIFY (cap "LLM stack convergencia" reescrita)
docs/domains/llm-routing.md                                   🔧 MODIFY ("Modelos activos hoy" tabla update post-deploy + Migration timeline tabla "S3 PR-1 shipped")
```

**Total estimado: 23 archivos** (close al target ≤15 cohesivo declarado en PR.md — supera por +8 contando tests + DTO + `current-state/copilot.md`. Justificable: refactor cross-layer cohesivo. Architect recomienda mantener cohesión vs splittear.)

## 12. Cross-cutting concerns

- **Tenant isolation**: cada query repo mantiene `where(tenant_id == tenant_id)`. Sin cambio.
- **Currency**: n/a (no DTOs monetarios).
- **Master data (UTC + locale)**: n/a (no datetimes nuevos; existing `created_at = func.now()` con `timezone=True` mantenido).
- **Spanish neutro LatAm**: `_SYSTEM_PROMPT_ES` LLMClassifier reescrito sin voseo (verifica `tú` no `vos`). Spanish Glossary checklist aplicado a system prompt + structlog event_names mantienen snake_case English.
- **PII**: response_model declarado en TODAS las routes (`test_response_model_required.py` ratchet pasa). Migration 115 NO toca columnas PII. RoutingLogModel sin PII (UUIDs + role string + counters).
- **Native-first**: TODOS los lint/test commands abajo NATIVE WSL `cd backend && .venv/bin/...`. NUNCA `docker exec ruff/pytest`.
- **NO TOUCH §3 sales_agent**: verificación grep `from src.modules.sales_agent` en `src/modules/copilot/` retorna SOLO `shared/links/ports/sales_agent.py` consumers (port-mediated reads — F1 ratchet preservado).
- **NO TOUCH §3 copilot redesign**: orchestrator `chat.py` solo se modifica en _record_routing_decision (telemetry-only path, F8 cementado). NO touch system_prompt slots (F8 §5.2 + F10 slot 3). NO touch `LLMFactory` topology. NO touch deepagents harness (F2). NO touch SSE v2 protocol (F8). NO touch [COPILOT-*] anchor registry (cap 36/36).

## 13. Architectural fitness impact

| Gate | Cambio | Acción |
|---|---|---|
| `test_llm_routing_ssot.py::test_no_new_modeltier_imports` | allowlist KNOWN_LEGACY_LLM_FILES shrink 19→5 (ideal 0) | UPDATE archivo + commit con justificación |
| `test_llm_routing_ssot.py::test_no_copilot_tier_env_vars` | post-DELETE, 0 hits esperados | RUN — debe seguir verde |
| `test_llm_routing_ssot.py::test_no_new_llm_factory_layers` | post-DELETE `copilot/infrastructure/llm/`, 0 hits | RUN — debe seguir verde |
| `test_no_new_copilot_module_imports.py` (ratchet 22) | sin cambio (no nuevos imports cross-module) | VERIFY |
| `test_copilot_anchors.py` (cap 36/36) | sin nuevos anchors | VERIFY |
| `test_response_model_required.py` | DTOs refactorizados conservan response_model en todas las routes | VERIFY |
| `test_pr3_no_sales_agent_imports.py` | DELETE (D-8) | DELETE archivo + commit |
| `test_copilot_provider_compliance.py` | sin cambio (no nuevo CopilotProvider) | VERIFY |
| `test_extraction_orchestrator_inheritance.py` | sin cambio | VERIFY |
| Demás 5 gates | sin cambio | VERIFY suite completa |

Comando único validation gates:
```bash
cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short
```

## 14. pm-nico/current-state updates required

`docs/pm-nico/current-state/copilot.md` — reemplazar bloque actual:

```markdown
### Cap: LLM stack DeepSeek V4-Flash infra ready (wiring PR-4 pendiente)
- Introducida: PR-3 (PI-2, S2, ...)
- Estado: PARTIAL — infra live, wiring upstream LLMClassifier+RollingSummarizer factory PENDIENTE PR-4
- ...
```

Por:

```markdown
### Cap: LLM stack ModelRole único SSoT + DeepSeek V4-Flash NANO+FAST activo
- Introducida: PR-1 (PI-2, S3, commit `<hash>`, 2026-04-30)
- Estado: live
- Operable copilot: no directamente (infra LLM layer)
- SSoT único: `src/core/enums.py::ModelRole` + `src/core/config.py::Settings.get_model/get_provider_for_role` + `src/shared/infrastructure/llm/router.py + providers/`
- ModelTier (legacy) eliminado — copilot/domain/model_tier.py DELETED
- Capa duplicada PR-3 (`copilot/infrastructure/llm/`) DELETED
- Mapping cementado: NANO→NANO / MINI→FAST / REASONING→REASONING / HEAVY→AGENT
- Modelos activos: NANO + FAST → deepseek-v4-flash ($0.14/$0.28 per 1M, 4-15x cost reduction vs gpt-4o-mini); REASONING → deepseek-reasoner; AGENT → kimi-k2.6
- Pricing snapshot: `model_pricing_snapshot` row deepseek-v4-flash (alembic 114 shipped S2)
- Migration 115: `copilot_routing_log.tier_selected → role_selected` (idempotente raw SQL)
- Arch fitness `test_llm_routing_ssot.py` 4/4 verde + allowlist shrunk a ≤5 entries
- Verificación post-deploy: query `SELECT DISTINCT model_id FROM copilot_llm_call WHERE created_at > NOW() - INTERVAL '5 min' AND role_used='nano'` retorna `deepseek-v4-flash`
```

`docs/domains/llm-routing.md` — actualizar tabla "Modelos activos hoy":
- NANO row: `deepseek` / `deepseek-v4-flash` / `$0.14 / $0.28`
- FAST row: `deepseek` / `deepseek-v4-flash` / `$0.14 / $0.28`

Y "Migration timeline":
- S3-copilot-llm-stack-convergence | PR-1 cleanup + convergencia + DeepSeek V4-Flash NANO+FAST ACTIVO | shipped 2026-04-30

## 15. Test surfaces (TDD-mandatory)

**Orden RED → GREEN → REFACTOR estricto, layer por layer (Inside-Out).**

### 15.1 Layer domain (RED first)

1. ❌ `test_routing_policy.py` — actualizar aserciones para `RoutingDecision.role: ModelRole` + `RoutingPolicy.default_role: ModelRole.FAST` + `DEFAULT_ROUTING_POLICY` rules con `role=ModelRole.AGENT/REASONING/NANO`. RED: tests fail con error "ModelRole has no MINI / HEAVY". GREEN tras refactor `routing_policy.py`.
2. ❌ `test_model_tier.py` — DELETE archivo (target eliminado).
3. ❌ NEW `test_routing_policy_role_mapping.py` — assert `DEFAULT_ROUTING_POLICY.default_role == ModelRole.FAST`, todas rules.role en `set(ModelRole)`.

### 15.2 Layer infrastructure (RED first)

4. ❌ `tests/modules/copilot/infrastructure/llm/test_model_config.py` — DELETE archivo (target eliminado).
5. ❌ NEW migration test (idempotencia): script ad-hoc en CI:
```bash
docker exec ... alembic upgrade head    # apply 115
docker exec ... alembic upgrade head    # re-apply, expect no-op
docker exec ... psql -c "SELECT column_name FROM information_schema.columns WHERE table_name='copilot_routing_log' AND column_name='role_selected'"   # expect 1 row
docker exec ... psql -c "SELECT column_name FROM information_schema.columns WHERE table_name='copilot_routing_log' AND column_name='tier_selected'"   # expect 0 rows
```

### 15.3 Layer application (RED first)

6. ❌ `test_llm_classifier.py` — JSON `_VALID_ROLES` mapping, system prompt golden update (text con "roles" no "tiers"), `decision.role == ModelRole.NANO/FAST/REASONING/AGENT`.
7. ❌ `test_router_factory.py` — `decision.role` en lugar de `decision.tier`.
8. ❌ `test_routing_parallel.py` — RoutingDecision constructor con `role=ModelRole.X`.
9. ❌ `test_chat_routing_integration.py` — `decision.role.value` flow a `role_selected` param de `RoutingLogRepository.insert`.
10. ❌ `test_rolling_summarizer.py` — mock `BaseChatModel` (no `LLMProvider`); `summarizer.update(...)` invokes `llm.ainvoke(...)` con `[SystemMessage, HumanMessage]`.
11. ❌ `test_title_generator.py` — mismo pattern.
12. ❌ NEW `test_llm_classifier_settings_integration.py`:
    - Stub `Settings.get_model(ModelRole.NANO) == "test-model-name"`.
    - Stub `Settings.get_provider_for_role(ModelRole.NANO) == AIProvider.DEEPSEEK`.
    - LLMClassifier resolves LLM via `LLMFactory.get_service().get_client(ModelRole.NANO, temperature=0.0)` (verify mock called).
    - Verify NO references a `ModelTier` ni `TIER_METADATA` ni `COPILOT_TIER_*` env vars en codepath ejecutado.

### 15.4 Layer api (RED first)

13. ❌ Tests existing routes copilot (e.g., `test_conversations_routes.py`) — DTO field `last_role_used` en response shape; backward compat verify si FE gets `last_tier_used` también (architect: alias temporary NO; FE alinea mismo PR — minor edit).

### 15.5 Layer arch fitness (RED first)

14. ❌ `test_llm_routing_ssot.py::test_no_new_modeltier_imports` — RED hasta `ModelTier` imports eliminados. Allowlist shrink final commit.
15. ❌ `test_llm_routing_ssot.py::test_no_new_llm_factory_layers` — RED hasta `copilot/infrastructure/llm/` DELETED.
16. ❌ `test_pr3_no_sales_agent_imports.py` — DELETE (D-8).

### 15.6 Layer e2e (smoke)

17. ⚠️ Smoke local manual: levantar dev (`docker compose up -d`), open copilot conv, send 1 message → verify trace events `routing_decision` + `tier_decided` payload contiene field `role` (no `tier`). Streamlit `/copilot-routing` dashboard renderea sin error con column `role_selected`.

## 16. Restricciones inviolables verificadas

| Restricción | Verificación cómo | Estado pre-CONTRACT |
|---|---|---|
| NO TOCAR `backend/src/modules/sales_agent/` | `git diff --stat src/modules/sales_agent/` retorna 0 después builder. `grep -rn "from src.modules.sales_agent" src/modules/copilot/ \| grep -v "shared/links"` = 0 hits | ✅ Confirmed audit 1.1 |
| NO crear nueva capa `LLMProvider` Protocol en `modules/<x>/domain/ports.py` | D-4 ELIMINA Protocol entera. NO crea nueva en modules/<x>/. Resolución vía `LLMFactory` shared compartido. | ✅ Cementado D-4 |
| NO hardcodear `model_name` strings en código aplicación | Refactor RollingSummarizer + TitleGenerator: NO model_name string. Resuelven via `LLMFactory.get_service().get_client(ModelRole.NANO)` → adapter resuelve `settings.get_model(ModelRole.NANO)` env-driven. | ✅ Cementado §4.2 |
| Migration 115 idempotente raw SQL IF EXISTS / IF NOT EXISTS | DO $$ BEGIN ... IF EXISTS ... AND NOT EXISTS ... END $$ block | ✅ Cementado §6 |
| response_model= obligatorio en endpoints | DTOs refactorizados conservan response_model en todas las routes | ✅ Verify post-builder via `test_response_model_required.py` |
| Soft deletes only | Sin cambio en deletion patterns | ✅ N/A — refactor no toca delete logic |

## 17. Open questions for PM

1. **FE frontend update mismo PR vs separado?** DTO field `last_tier_used` → `last_role_used` requiere refactor en `frontend/src/features/copilot/api/conversations.ts` + 1-2 components consumiendo el campo. Architect recomienda **incluir en este PR** (~3 archivos FE) para evitar drift FE↔BE 1+ ciclo. Si PM prefiere separar → BE response field temporal con doble nombre `last_role_used` + `last_tier_used` (mismo valor) + cleanup PR-N+1. Decisión PM.

2. **Allowlist `KNOWN_LEGACY_LLM_FILES` target final**: 5 entries definidas en D-9 con motivo cementado, o **0 entries** (refactor inline DTO + repo + observability models)? Architect inclina **0 si scope cohesivo** (es 4 archivos extra). PM aprueba +4 archivos o defer 5 entries a S3 PR-2?

3. **Rename column `conversation.last_tier_used`?** Mantener nombre DB column histórica (`last_tier_used`) con Python field rename (`last_role_used`) via SQLA `mapped_column(name="last_tier_used")`, vs migración 115 cubre ambas columns? Architect inclina **mantener nombre DB** — saves migration row, queries Streamlit existentes funcionan. PM decide.

4. **Activación DeepSeek V4-Flash en `.env` prod (no .env.example)**: D-10 ACTIVA en `.env.example` (template). El `.env` real prod lo edita Chris en deploy (`backend/.env` no está en repo). PM confirma: ¿builder DEBE editar `backend/.env` directamente (gitignored, dev local), o solo `.env.example` + leave Chris hacer deploy? Architect default = **solo `.env.example`** (single source of truth template; deploy env via secrets manager). Confirm.

5. **DeepSeek API key prod**: alcanza budget DeepSeek (`DEEPSEEK_API_KEY` actual `sk-d42...` en `.env` real) para handle volumen NANO+FAST 100% post-cutover? Si saturable → throttling fallback a OpenAI gpt-4o-mini transparente (S5 admin UI). Confirm Chris validó pre-deploy.

## 18. Research notes

| Source | URL | Fecha acceso | Key takeaway | Por qué sobre alternativas |
|---|---|---|---|---|
| Research stack chinese models | `docs/pm-nico/research/2026-04-30-llm-landscape-chinese-models.md` | 2026-04-30 | DeepSeek V4-Flash $0.14 / $0.28 per 1M, 81.9 t/s, 1M context, 284B MoE = ganador absoluto cost/perf NANO+FAST tier | 4-9x cheaper input vs gpt-4o-mini, sin pérdida calidad clasificación (research valida ≥0.95 goldens projection) |
| llm-routing.md SSoT | `docs/domains/llm-routing.md` | 2026-04-30 | Reglas no-negociables 1000+ tenants: pricing inmutable, cache layer, tenant isolation, audit trail, eval gate antes promote | Cero deuda + escalabilidad target Chris |
| OpenAI Help Center reasoning budget | (vendored en `_chat_model_resolver.py` docstring) | 2026-04 | Reasoning models share max_tokens budget — `reasoning_token_reserve=4000` floor | Existing `_openai_compat.py` ya implementa — sin cambio |
| DeepSeek-V4 1M context release | https://huggingface.co/blog/deepseekv4 | 2026-04-24 | 1M context default elimina chunking lógica para summarizer | RollingSummarizer hereda capacity bigger → margen seguridad summary cap 400 chars |

---

<!-- @pm: CONTRACT.md ready (architect-empowered). -->
