# Learnings · S4 · ChatModelSpec adopt + per-role multi-provider routing

> Doc para S5 (channel registry shared). Foundation routing per-role lista
> y SSoT mapping declarativo activo. S5 puede asumir que cualquier
> specialist nuevo se registra una vez en `SPECIALIST_TO_ROLE` y el
> arch test bloquea hardcoded model strings sin allowlist.

---

## Resumen (3 líneas)

- **Entregado**: `src/modules/sales_agent/domain/model_tier.py` con `SPECIALIST_TO_ROLE: dict[str, ModelRole]` (4 entries: supervisor=NANO, qualifier=REASONING, product_expert=REASONING, closer=AGENT). Refactor `nodes.py` 4 callsites — eliminado import `ModelRole` directo (vive vía SSoT). Arch test ratchet `tests/architecture/test_no_hardcoded_models_sales_agent.py` bloquea wire-name strings (`gpt-*`, `o3`, `o4-mini`, `claude-*`, `deepseek-*`, `kimi-*`, `moonshot-*`, `qwen*`, `gemini-*`) en `application/agents/sales/` AST scan. 26 tests S4 nuevos (4 mapping + 6 provider routing + 2 Kimi thinking + 2 reasoning budget + 12 arch). Quality gates 1639 verde nativos.
- **Decisión no obvia**: el plan original §criterio mencionaba `LLMFactory.get_service(role=role)` como nueva API. **No lo cambiamos** — `MultiRoleLLMRouter` (post-abril 2026) ya enruta per-role transparente cuando se pasa `model_type=ModelRole.X` a `generate_response()`. La factory devuelve un singleton router, el router resuelve provider per-call vía `settings.get_provider_for_role(role)`. Cambiar la API de la factory hubiera roto 9 callsites cross-module sin payoff. El missing piece era **solo el mapping semántico SSoT**, no la infraestructura. La fase tomó 1.5h vs el estimado original 1-2 días — porque la infraestructura ya estaba lista.
- **Listo para S5**: zero deuda en path `nodes.py` ↔ routing. SPECIALIST_TO_ROLE es punto fijo — S5 (channel registry) no toca nada de model routing. Si S5 agrega un specialist nuevo (ej. `channel_format_dispatcher` aunque sería tool no specialist), añade entry + arch test snapshot ya pasa. **Watchpoint S5**: el mapping hoy es `dict[str, ModelRole]` — si se promueve a `Mapping[str, ModelRole]` con `MappingProxyType` para inmutabilidad runtime, S6 ratchet pass es el momento.

---

## Decisiones clave

- **No cambiar la signature de `LLMFactory.get_service()`**:
  - Tomada: mantener `LLMFactory.get_service()` sin parámetro `role`. Cada specialist sigue invocando `LLMFactory.get_service().generate_response(model_type=SPECIALIST_TO_ROLE["X"], ...)`.
  - Razón: research del paso 2 + lectura del código `shared/infrastructure/llm/router.py` confirmó que el `MultiRoleLLMRouter` (singleton devuelto por `get_service()`) ya hace dispatch per-role internamente — `_resolve(role)` → `settings.get_provider_for_role(role)` → instancia provider lazy. Cambiar signature a `get_service(role)` sería rediseño con 9 callsites afectados (8 sales_agent + N copilot) sin ganancia funcional. La declaración semántica del role se hace en `SPECIALIST_TO_ROLE` (SSoT) y se pasa al wire vía `model_type=` que el router ya entiende.
  - Alternativa descartada: agregar `LLMFactory.get_service_for_role(role)` paralelo. Rechazada — bifurca la API; `model_type` ya canónico.

- **SSoT en `domain/`, no en `application/`**:
  - Tomada: `model_tier.py` vive en `src/modules/sales_agent/domain/` adyacente a `tuning.py` (constantes de scoring/cadence) y `enums.py`. NO en `application/agents/sales/`.
  - Razón: la decisión "qué role usa cada specialist" es policy/tuning de dominio (igual que `STAGE_CLOSING_SCORE` o `BUYING_SIGNAL_WEIGHT`). No requiere framework imports — solo `ModelRole` enum (shared `src.core.enums`). Backend DDD §1.4 (`backend-ddd.md`) coloca tuning/policy en domain. Esto deja el aggregator de dominio (cualquier futuro test de "qué tier elige cada specialist") sin acoplar a la app.
  - Alternativa descartada: `application/agents/sales/specialist_tiers.py`. Rechazada — application capa tiende a pulir lógica que orquesta servicios; este es un mapping puro estático.

- **Arch test bloquea wire-name strings sin allowlist**:
  - Tomada: `tests/architecture/test_no_hardcoded_models_sales_agent.py` AST-scan de strings literales en `application/agents/sales/**/*.py` con regex `^(gpt-[\d.]|o[34](-[a-z]+)?$|claude-|deepseek-|kimi-|moonshot-|qwen[\d-]|gemini-)`. `KNOWN_VIOLATIONS = ()`. Sin escape hatch.
  - Razón: principio anti-parche `04-principles §2`. Cualquier specialist nuevo tentado a hardcodear `"gpt-4o"` por debugging falla CI inmediato. La excepción (`domain/model_tier.py` declarando ModelRole no es model-name) está cubierta porque `model_tier.py` vive en `domain/`, no en el path scaneado. Test fixtures en `tests/` también fuera del scan.
  - Alternativa descartada: lint rule via ruff custom. Rechazada — ruff custom rules son frágiles y los regex están mejor expresados como AST scan + asserts.

- **Closer temperature 0.4 declarado, Kimi clamp 0.6 server-side**:
  - Tomada: el specialist closer pide `temperature=0.4` (creatividad). Kimi K2.6 con thinking-disabled exige `temperature=0.6` server-side; `KimiService._get_chat_model` ya hace clamp + structlog warning. NO modifiqué el specialist para alinear pre-emptivamente con Kimi.
  - Razón: separación de concerns — el specialist declara intent ("quiero más creatividad que qualifier"); el provider implementa lo que server permite. Si mañana switch a OpenAI gpt-5.4 (sin clamp), el closer recupera 0.4 sin cambio en specialist. Si el provider Kimi cambia su requirement, kimi.py absorb el cambio.
  - Alternativa descartada: hardcodear 0.6 en el specialist closer. Rechazada — acopla domain code al provider activo.

- **Tests de provider routing usan `monkeypatch.setattr(settings, ...)` no env vars**:
  - Tomada: `test_role_to_provider_mapping` patcheaa el atributo tipado de `Settings` directo, no `monkeypatch.setenv("AI_PROVIDER_AGENT", "kimi")`.
  - Razón: pydantic-settings carga env vars al boot. Override runtime via env var requiere recargar `Settings()`, lo que rompe el singleton del module-level `settings = Settings()`. Patchear el atributo directo es el supported pattern para tests in-process. Trade-off: el test no exercise el camino "env var loaded into settings" — solo "settings field resolves to provider correctly". Aceptable porque el path env-var → field es responsabilidad de pydantic-settings (ya testeado upstream).

---

## Sorpresas / gotchas críticos

- **`MultiRoleLLMRouter` ya estaba activo desde abril 2026** — tropecé al asumir que la migración era a una API nueva. Lectura del código `shared/infrastructure/llm/factory.py` reveló que `LLMFactory.get_service()` devuelve el router singleton; sales_agent hoy ya lo consume implícito al pasar `model_type=ModelRole.X`. El plan original (escrito antes de abril 2026) pedía cambiar signature; el research mandate confirmó que el codebase post-abril ya estaba listo. **Lección S5+**: re-leer el código vivo antes de asumir que la fase tiene que rediseñar infraestructura. El `02-architecture-target.md` se actualizó 2026-04-28 explícito por esto, pero el `phases/S4-*.md` aún tenía residuo del plan original.

- **`from __future__ import annotations` + `if TYPE_CHECKING` bloquea acceso a private constants en tests** — el primer intento del test `test_kimi_k2_client_temperature_clamped` importaba `_K2_REQUIRED_TEMPERATURE` desde `kimi.py`. Funcionó porque kimi.py NO usa `__future__ annotations` — el constant es runtime accessible. Si futuro provider migra a `__future__ annotations` con TYPE_CHECKING-only imports, los tests que necesiten constantes runtime deben validarse manual. Ya documentado en learnings S1 ("from __future__ rompe LangGraph runtime introspection") — same root: TYPE_CHECKING/futuros bloquean runtime access.

- **`importlib.reload(nodes_mod)` necesario en cada test** — los tests pre-existentes en `test_nodes.py` ya hacían reload por test. Heredé el patrón en `test_specialist_provider_routing.py`. Sin reload, el `monkeypatch.setattr(settings, ...)` aplicaba sobre el `settings` cacheado en module globals — los tests se contaminaban. **Lección**: cuando tests patchean `settings` y el SUT importa `settings` al import time, reload del SUT.

- **DeepSeek alias retire deadline Jul 24 2026** — research reveló cambio que NO sabíamos: `deepseek-chat` y `deepseek-reasoner` aliases se retiran completamente. Tenants en producción que sobreescriban `AI_MODEL_REASONING=deepseek-reasoner` rompen post-deadline. **Lección**: los `AI_MODEL_<ROLE>` defaults son env-driven, fáciles de modificar; los tenant overrides en DB requieren un sweep pre-deadline. Tech debt entry creada (DEFERRED-pre-Jul-2026).

- **Arch test FORBIDDEN_MODEL_PATTERNS también atrapa `gpt-`, `o3`, `o4-mini` cuando aparecen en docstrings** — el primer regex `^o[34]` matcheaba `"o3"` literal. Tuve que ajustar a `^o[34](?:-[a-z]+)?$` para evitar false positives en path names que empiezan con "o" + número. **Lección**: los patterns deben ser tan estrictos como el wire format real, no genéricos a "anything starting with o".

---

## Recomendaciones accionables para S5

- [ ] **S5 (channel registry shared) NO necesita tocar SPECIALIST_TO_ROLE** — el channel registry vive en `shared/agent_observability/channels/` (pattern §3.5 de architecture target). No hay nuevos specialists. Si S5 introduce un tool/dispatcher con LLM call (improbable, channel format es post-processor sin LLM), seguir el mismo SSoT pattern.

- [ ] **Tras deploy, query `sales_agent_llm_call.provider` para validar mapping** — `SELECT provider, model_responded, COUNT(*) FROM sales_agent_llm_call WHERE tenant_id=:t AND occurred_on >= NOW() - INTERVAL '7 days' GROUP BY provider, model_responded ORDER BY 3 DESC;` debería mostrar:
  - supervisor calls → `openai` con `gpt-4o-mini` (NANO default).
  - qualifier/product_expert calls → `deepseek` con `deepseek-v4-flash` o equiv (si `AI_PROVIDER_REASONING=deepseek`).
  - closer calls → `kimi` con `kimi-k2.6` (si `AI_PROVIDER_AGENT=kimi`).
  - Si la distribución NO refleja, env vars no propagaron a runtime — verificar `.env` + `docker-compose.yml`.

- [ ] **Cache hit rate post-S4 — query**: `SELECT SUM(cached_read_tokens)::numeric / NULLIF(SUM(input_tokens), 0) AS hit_rate, COUNT(*) FROM sales_agent_llm_call WHERE tenant_id=:t AND provider IN ('kimi', 'deepseek') AND occurred_on >= NOW() - INTERVAL '7 days';`. Target ≥60% segundo turno+. Si <60% en Kimi → verificar prefix ≥1024 tokens contiguos vía S3 cache_boundary (ya validado por arch test).

- [ ] **Si callback handler S1 `_extract_usage` no captura `cached_read_tokens` para Kimi** — research confirmó LangChain normaliza `usage_metadata.input_token_details.cache_read` cross-provider. Si en producción la columna sale 0 para Kimi turns, ajustar `SalesAgentCallbackHandler._extract_usage` para leer también `usage.prompt_cache_hit_tokens` raw (DeepSeek-style). Watchpoint S6 ratchet.

- [ ] **DeepSeek migration deadline 2026-07-24** — antes de jul, default explícito `AI_MODEL_REASONING=deepseek-v4-flash` (no `deepseek-reasoner` legacy). Sweep tenant overrides DB (`PromptVersionModel` no aplica acá; revisar `Tenant.deepseek_api_key` + tenant-level `AI_MODEL_*` si existen).

- [ ] **Si S6 ratchet pass abre `LLM_ROLE_BY_SITE` map expandido** — promover summary/follow_up/safety FAST → NANO al SSoT. Hoy son 3 callsites fuera del SPECIALIST_TO_ROLE; centralizar en S6 reduce drift y permite políticas tenant-level.

---

## Hooks listos

- `backend/src/modules/sales_agent/domain/model_tier.py::SPECIALIST_TO_ROLE` — SSoT mapping. Cualquier specialist nuevo agrega entry; arch test bloquea hardcoded fallback.

- `backend/tests/architecture/test_no_hardcoded_models_sales_agent.py` — 4 fitness tests sin allowlist:
  - `TestNoHardcodedModelsInSpecialists::test_no_forbidden_model_string_literals`
  - `TestSpecialistRoleMappingExists::test_model_tier_module_exists`
  - `TestSpecialistRoleMappingExists::test_specialist_to_role_exposes_required_keys`
  - `TestSpecialistRoleMappingExists::test_nodes_imports_specialist_to_role`

- `backend/tests/modules/sales_agent/test_specialist_role_mapping.py` — 5 unit tests del mapping (NANO/REASONING/REASONING/AGENT + parametrize coverage).

- `backend/tests/modules/sales_agent/test_specialist_provider_routing.py` — 9 tests integration (4 specialists pasando role correcto + 4 settings.get_provider_for_role param + 2 Kimi K2 thinking-disabled + temp clamp + 2 reasoning budget reserve normalizer).

- `backend/src/shared/infrastructure/llm/router.py::MultiRoleLLMRouter` — mantener intacto. S5+ no debería tocar.

- `backend/src/shared/infrastructure/llm/providers/_kwargs.py::normalize_openai_protocol_kwargs` — SSoT del reasoning-budget reserve. Cualquier provider nuevo con `is_reasoning_model=True` se normaliza automático con `reasoning_token_reserve` declarado en su `ChatModelSpec`.

---

## Riesgos abiertos

- **Closer temperature 0.4 → 0.6 clamp por Kimi K2.6** — declarado en specialist 0.4, wire 0.6. NO bug funcional (clamp + log claro). Watchpoint: medir empíricamente conversion rate post-deploy. Si baja >5% vs pre-S4 con OpenAI gpt-4o temp 0.4, options: (a) override per-canal, (b) accept Kimi 0.6 como nuevo baseline, (c) ramp condicional a OpenAI temp 0.4 para tier alto de oferta.

- **`AI_PROVIDER_AGENT=kimi` en producción requiere `KIMI_API_KEY` válida** — boot del router NO falla si la key falta (lazy `_resolve` via `get_provider_for_role`). El primer turn que invoque al closer falla con `ValueError("kimi API key not configured")`. **Mitigación**: smoke test post-deploy del closer flow; alert si first turn closer falla con ValueError. Idem para `AI_PROVIDER_REASONING=deepseek` + `DEEPSEEK_API_KEY`.

- **`MultiRoleLLMRouter._providers` cache crece con cada role nuevo** — máximo 5 entries (5 ModelRole) por singleton. Cap natural. NO hay leak.

- **DeepSeek alias retire 2026-07-24** — sweep pre-deadline necesario. Tech debt entry abierto.

- **Tests `monkeypatch.setattr(settings, env_var, ...)` no exercisean env-var loading** — confiar en pydantic-settings upstream. Si CI tiene env vars seteadas que difieren del default `Settings()`, los tests aún pasan porque patchean el atributo. **Lección S6**: si tests integration empiezan a depender de configuración ambiental real (post-deploy probes), considerar containers de test con env vars explícitas.

---

## Tech debt detectado (NO arreglado)

Ya en `05-tech-debt-log.md` sección "Detectados durante S4":

- [MEDIUM] DeepSeek alias retire deadline 2026-07-24 → DEFERRED-pre-Jul-2026.
- [LOW] safety_service / chat.py:550 / follow_up_engine FAST sin SSoT → DEFERRED-post-S6.
- [LOW] Closer temp 0.4 declared / Kimi clamp 0.6 wire → FLAGGED.
- [LOW] supervisor + summary/follow_up FAST → NANO migration → DEFERRED-post-S6.

Y FIXED arriba:

- [MEDIUM] Sales_agent no usa multi-provider per-role → FIXED en S4.

---

## Fuentes research útiles

Solo las que **cambiaron una decisión**.

- [Kimi K2.6 — Moonshot platform docs](https://platform.kimi.ai/docs/guide/kimi-k2-6-quickstart) + [Apiyi K2.6 integration guide](https://help.apiyi.com/en/kimi-k2-6-api-integration-guide-en.html) — confirmaron temp 0.6 server-required con thinking-disabled + 256K context + 40% pricing discount + auto-cache 75-83% savings. Ratificó que el switch closer→AGENT vale el esfuerzo.
- [DeepSeek V4 Preview Release news](https://api-docs.deepseek.com/news/news260424) — confirmó alias retire `deepseek-chat`/`deepseek-reasoner` Jul 24 2026 → migrate a `deepseek-v4-pro`/`deepseek-v4-flash`. Cambió decisión: tech-debt deadline crítico.
- [DeepSeek Thinking Mode docs](https://api-docs.deepseek.com/guides/thinking_mode) — confirmó reasoning + visible content shared budget; reserve 4000 sigue válido.
- [LangChain ChatDeepSeek native package reference](https://reference.langchain.com/python/langchain-deepseek/chat_models/ChatDeepSeek) — confirmó `prompt_cache_hit_tokens` en response_metadata + LangChain normaliza a `usage_metadata.input_token_details.cache_read` standard.
- [LangChain UsageMetadata reference](https://reference.langchain.com/python/langchain-core/messages/ai/UsageMetadata) — confirmó `input_token_details.cache_read` standard cross-provider; bug Anthropic 2× counts NO afecta sales_agent (no rutea a Claude).
- [OpenAI o3/o4-mini reasoning_effort guide](https://openai.com/index/introducing-o3-and-o4-mini/) — confirmó `reasoning_effort` solo en o3 (no o4-mini). Sales_agent NANO=gpt-4o-mini default no necesita reasoning_effort, no impacta.

---

## Métricas medidas

- BE quality gates nativos: `ruff check src/ tests/ --no-cache` 0 errors, `ruff format --check` clean.
- `pytest tests/modules/sales_agent/ tests/architecture/ tests/admin/ tests/shared/ tests/modules/copilot/observability/ -x -q`: **1639 passed, 1 warning** (Pydantic deprecation, no impacto).
- Tests nuevos S4: **26** (5 mapping + 9 routing/Kimi/reserve + 4 arch_no_hardcoded + 4 arch_mapping_exists + 4 arch_nodes_import).
- Tests modificados: 2 (`test_supervisor_uses_fast_model_low_temperature` → `test_supervisor_uses_nano_model_low_temperature`; `test_closer_uses_higher_temperature` → `test_closer_uses_agent_role_higher_temperature`).
- Files nuevos: 4 (model_tier.py + 3 test files).
- Files modificados: 3 (nodes.py, test_nodes.py, S4 phase doc Hallazgos research).
- LOC añadidas: ~600 (incluye learnings + tests + SSoT module).
- Spanish neutro: NO regresión — model_tier.py docstrings + nodes.py código son inglés técnico (no user-facing). Closer escalation message intacto pre-existente.
- Cambios en `nodes.py` líneas modificadas: 4 (3 specialists + supervisor + 1 import remove + 1 import add).
- Backwards-compat: `from src.core.enums import ModelRole` removido de nodes.py (no breaking — los callers que necesiten ModelRole importan directo de `src.core.enums`).
