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
- **llm/factory.py** — `LLMFactory`: singleton o per-tenant, soporta OpenAI y Gemini. Resuelve API key del tenant o cae a platform keys.
- **llm/providers/** — Implementaciones concretas (`OpenAIService`, `GeminiService`).
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
