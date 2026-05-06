---
module: Technical Module Shared
status: active
---

# Shared (`backend/src/shared/`)

ADN transversal del negocio. Contiene abstracciones, protocolos y utilidades que todos los modulos pueden importar sin generar acoplamiento entre ellos.

## Componentes

### domain/
- **base_entity.py** — `Base` (SQLAlchemy declarative base) y `BaseEntity` (Pydantic base model).
- **events.py** — `DomainEvent` dataclass + `EventBus` singleton (subscribe/publish con deferred dispatch post-commit).
- **messages.py** — Protocolo de mensajeria: `IncomingMessage` y `OutgoingMessage` (channel-agnostic).
- **value_objects.py** — Value Objects comunes reutilizables.

### infrastructure/
- **channels/base.py** — `BaseChannel` ABC: port para adaptadores de canal externo (`normalize_payload`, `send_message`, `set_typing_status`).
- **llm/router.py** — Dispatch único de roles LLM. Toma `(role, messages)`, resuelve provider+model vía `Settings.get_provider_for_role` + `Settings.get_model`, delega a `LiteLLMService`.
- **llm/factory.py** — `LLMFactory`: singleton del adapter LLM. Resuelve API keys de provider desde env vars (consumidas por LiteLLM proxy vía `litellm_config.yaml`). Las columnas tenant `{openai,deepseek,kimi,dashscope}_api_key` están deprecadas (PI-12 S1 T-6a, drop final en T-6c).
- **llm/providers/litellm.py** — `LiteLLMService`: único adapter runtime. Llama al proxy LiteLLM (Docker svc `visionarias_litellm`) vía interfaz OpenAI-compat. Detalle completo del routing → `docs/domains/llm-routing.md`.
- **llm/providers/{_kwargs,_chat_model_resolver,_response_validation}.py** — Helpers consumidos por `LiteLLMService` (normalización de kwargs cross-provider, selección de wrapper LangChain `ChatModel`, validación de payload de respuesta).
- **agent_observability/recording/cost_recorder.py** — `CostRecorderCustomLogger`: hook LiteLLM que captura `kwargs["response_cost"]` en cache TTL 60s. El callback handler LangChain consume el valor vía `pop_cost(litellm_call_id)` y persiste en `*_llm_call.cost_usd`. Detalle → `docs/domains/llm-routing.md` § "CustomLogger pattern".
- **model_registry.py** — Importa todos los SQLAlchemy models para garantizar registro en el mapper antes de `configure_mappers()`.
- **database/types.py** — Tipos custom de SQLAlchemy.
- **external/clerk.py** — Cliente Clerk para operaciones server-side.
- **files/** — `file_parsing_service`, `image_analysis`.

### application/
- **ai_action_service.py** — Orquestador de acciones IA compartidas.

### links/
- **LinkService** + **ShareableLink** model: generacion de URLs seguras con token, expiracion, visit tracking y revocacion. Usado por scheduling (booking links) y otros modulos.

## CRITICO — No Violar

- `shared` puede importar de `core`, pero NUNCA de `modules`.
- Cambios en `Base` o `BaseEntity` tienen efecto domino en toda la aplicacion — requieren revision cuidadosa.
