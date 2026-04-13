# Phase 3 Zero-Debt Audit — Plan de Ejecución

> **Para ejecutar en una nueva conversación de Claude Code.**
> Copia este prompt: "Ejecuta el plan de auditoría en `docs/superpowers/plans/2026-04-12-phase3-zero-debt-audit.md`. Cero deuda técnica, estos módulos deben ser el ejemplo a seguir."

**Goal:** Llevar los 33 archivos backend creados/modificados en Phase 3 a cero deuda técnica — máxima rigurosidad en Ruff, architecture fitness, DDD boundaries, y cross-references.

**Archivos scope (33 src + 15 test):**

```
# Source (33 archivos)
backend/src/core/config.py
backend/src/main.py
backend/src/shared/infrastructure/model_registry.py
backend/src/modules/brand/domain/buyer_persona.py
backend/src/modules/brand/infrastructure/models/buyer_persona_model.py
backend/src/modules/brand/infrastructure/repositories/buyer_persona_repository.py
backend/src/modules/copilot/api/document_dto.py
backend/src/modules/copilot/api/interview.py
backend/src/modules/copilot/api/voice.py
backend/src/modules/copilot/api/voice_dto.py
backend/src/modules/copilot/application/services/document_processor.py
backend/src/modules/copilot/application/services/interview_service.py
backend/src/modules/copilot/application/tools/interview/__init__.py
backend/src/modules/copilot/application/tools/interview/web_research.py
backend/src/modules/copilot/application/tools/registry.py
backend/src/modules/copilot/domain/interview_config.py
backend/src/modules/copilot/domain/interview_configs/buyer_persona_config.py
backend/src/modules/copilot/domain/interview_configs/offer_config.py
backend/src/modules/copilot/domain/interview_session.py
backend/src/modules/copilot/domain/voice.py
backend/src/modules/copilot/infrastructure/context/context_loader_registry.py
backend/src/modules/copilot/infrastructure/context/offer_context_loader.py
backend/src/modules/copilot/infrastructure/models/interview_session_model.py
backend/src/modules/copilot/infrastructure/persisters/offer_persister.py
backend/src/modules/copilot/infrastructure/persisters/persister_registry.py
backend/src/modules/copilot/infrastructure/repositories/interview_session_repository.py
backend/src/modules/copilot/infrastructure/voice/whisper_transcriber.py
backend/src/modules/copilot/infrastructure/web/tavily_search.py
backend/alembic/versions/f851363921c9_add_buyer_personas.py

# Tests (15 archivos)
backend/tests/modules/brand/test_buyer_persona_entity.py
backend/tests/modules/brand/test_buyer_persona_model.py
backend/tests/modules/brand/test_buyer_persona_repository.py
backend/tests/modules/copilot/test_buyer_persona_config.py
backend/tests/modules/copilot/test_context_loaders.py
backend/tests/modules/copilot/test_document_api.py
backend/tests/modules/copilot/test_document_processor.py
backend/tests/modules/copilot/test_interview_service_extensions.py
backend/tests/modules/copilot/test_offer_config.py
backend/tests/modules/copilot/test_offer_persister.py
backend/tests/modules/copilot/test_tavily_search.py
backend/tests/modules/copilot/test_voice_api.py
backend/tests/modules/copilot/test_voice_domain.py
backend/tests/modules/copilot/test_web_research_tool.py
backend/tests/modules/copilot/test_whisper_transcriber.py
```

---

## Problemas ya detectados

### 1. Ruff `--select ALL` (máxima rigurosidad)

Ejecutar `cd backend && .venv/bin/ruff check <archivos> --select ALL --no-cache` revela:

| Regla | Archivo | Problema |
|---|---|---|
| **RUF012** ×9 | `buyer_persona.py` | Mutable default values (`dict = {}`, `list = []`) en Pydantic model. Fix: usar `Field(default_factory=dict)` |
| **D1xx** (docstrings) | Múltiples | Módulos, clases, y funciones públicas sin docstrings |
| **ANN** (annotations) | Múltiples | Return types y parameter types sin annotations explícitas |
| **TC00x** | Varios | Imports que deberían estar en `TYPE_CHECKING` block |
| **S106** (hardcoded passwords) | Posible en config.py | `TAVILY_API_KEY: str = ""` podría flaggearse |

### 2. Architecture fitness (62/62 pasan pero verificar)

- `test_no_new_cross_module_imports`: copilot importa de offer (OfferModel en offer_context_loader) y brand (BuyerPersonaRepository en buyer_persona_persister). Verificar que estén en allowlists o usar shared/links.
- `test_domain_layer_has_no_framework_imports`: voice.py domain está limpio, pero verificar interview_config.py
- `test_all_endpoints_have_response_model`: voice y document endpoints tienen, pero verificar
- `test_no_hard_deletes`: buyer_persona repo usa soft delete, verificar
- `test_no_sqlalchemy_1x_query_syntax`: buyer_persona repo usa SA 2.0, verificar

### 3. Cross-module imports conocidos

| Desde | Importa de | Justificación | Acción |
|---|---|---|---|
| `copilot/infrastructure/context/offer_context_loader.py` | `offer/infrastructure/models/offer_model.py` | Necesita leer offers del tenant | Evaluar: ¿debería ir por shared/links o es aceptable? |
| `copilot/infrastructure/persisters/offer_persister.py` | `offer/domain/offer.py` + `offer/infrastructure/` | Necesita escribir al Offer | Evaluar: ¿mover a shared/links interface? |
| `copilot/infrastructure/persisters/brand_persister.py` (existente) | `brand/` | Mismo patrón, ya en allowlist | Solo verificar |

---

## Plan de Ejecución (6 tareas)

### Tarea 1: Ruff ALL — Source files

**Comando:**
```bash
cd backend && .venv/bin/ruff check \
  src/modules/brand/domain/buyer_persona.py \
  src/modules/brand/infrastructure/models/buyer_persona_model.py \
  src/modules/brand/infrastructure/repositories/buyer_persona_repository.py \
  src/modules/copilot/api/document_dto.py \
  src/modules/copilot/api/voice.py \
  src/modules/copilot/api/voice_dto.py \
  src/modules/copilot/application/services/document_processor.py \
  src/modules/copilot/application/tools/interview/web_research.py \
  src/modules/copilot/domain/interview_config.py \
  src/modules/copilot/domain/interview_configs/buyer_persona_config.py \
  src/modules/copilot/domain/interview_configs/offer_config.py \
  src/modules/copilot/domain/voice.py \
  src/modules/copilot/infrastructure/context/context_loader_registry.py \
  src/modules/copilot/infrastructure/context/offer_context_loader.py \
  src/modules/copilot/infrastructure/persisters/offer_persister.py \
  src/modules/copilot/infrastructure/persisters/persister_registry.py \
  src/modules/copilot/infrastructure/voice/whisper_transcriber.py \
  src/modules/copilot/infrastructure/web/tavily_search.py \
  --select ALL --no-cache
```

**Fix cada violación:**
- **RUF012** (mutable defaults): `demographics: dict = Field(default_factory=dict)` etc.
- **D100-D107** (docstrings): Agregar docstrings a módulos, clases, funciones públicas
- **ANN001-ANN206** (annotations): Agregar type hints explícitos a todos los parámetros y returns
- **TC001-TC003** (type checking): Mover imports solo usados en hints a `if TYPE_CHECKING:`
- **S106** (hardcoded): Si aplica, usar `SecretStr` para API keys

**Criterio de éxito:** `ruff check --select ALL` = 0 errors en los 18 archivos.

### Tarea 2: Ruff ALL — Test files

**Comando:**
```bash
cd backend && .venv/bin/ruff check \
  tests/modules/brand/test_buyer_persona_entity.py \
  tests/modules/brand/test_buyer_persona_model.py \
  tests/modules/brand/test_buyer_persona_repository.py \
  tests/modules/copilot/test_buyer_persona_config.py \
  tests/modules/copilot/test_context_loaders.py \
  tests/modules/copilot/test_document_api.py \
  tests/modules/copilot/test_document_processor.py \
  tests/modules/copilot/test_interview_service_extensions.py \
  tests/modules/copilot/test_offer_config.py \
  tests/modules/copilot/test_offer_persister.py \
  tests/modules/copilot/test_tavily_search.py \
  tests/modules/copilot/test_voice_api.py \
  tests/modules/copilot/test_voice_domain.py \
  tests/modules/copilot/test_web_research_tool.py \
  tests/modules/copilot/test_whisper_transcriber.py \
  --select ALL --no-cache
```

**Criterio:** Mismas reglas que source, excepto D100 (module docstrings opcionales en tests).

### Tarea 3: Architecture Fitness — Cross-module imports

**Comando:**
```bash
cd backend && .venv/bin/pytest tests/architecture/test_no_new_cross_module_imports.py -v --tb=long
```

**Verificar:**
1. ¿`offer_context_loader.py` importando de `offer/` está en KNOWN_CROSS_MODULE_IMPORTS?
2. ¿`offer_persister.py` importando de `offer/` está en KNOWN_CROSS_MODULE_IMPORTS?
3. Si NO están, decidir:
   - **Opción A:** Agregar a allowlist con justificación (copilot es orchestrator, patrón documentado)
   - **Opción B:** Crear interfaces en `shared/links/` para desacoplar

**Recomendación:** Opción A — copilot ya tiene excepción documentada en `CLAUDE.md` regla 4: "copilot may import from other modules (it's an infra-like orchestrator)".

### Tarea 4: DDD Layer Validation

Verificar manualmente que cada archivo respeta su capa:

| Capa | Regla | Archivos a verificar |
|---|---|---|
| `domain/` | NO framework imports (no SQLAlchemy, no FastAPI, no httpx) | `voice.py`, `interview_config.py`, `buyer_persona.py`, `interview_session.py`, configs |
| `infrastructure/` | Puede importar frameworks, implementa interfaces del domain | `whisper_transcriber.py`, `tavily_search.py`, `offer_context_loader.py`, persisters, repos |
| `application/` | Orquesta domain + infra, no expone framework details | `document_processor.py`, `interview_service.py`, tools |
| `api/` | Solo FastAPI + Pydantic DTOs, thin layer, delega a application | `voice.py`, `interview.py`, DTOs |

**Comando:**
```bash
cd backend && .venv/bin/pytest tests/architecture/test_domain_layer_has_no_framework_imports.py -v --tb=long
```

### Tarea 5: Endpoint Contract Validation

Verificar todos los endpoints nuevos:

| Endpoint | response_model | tenant_id | Auth |
|---|---|---|---|
| `POST /voice/transcribe` | `TranscriptionResponse` | `get_tenant_context` | Verificar |
| `POST /interview/{id}/documents` | `DocumentProcessingResponse` | `get_tenant_context` | Verificar |

**Comando:**
```bash
cd backend && .venv/bin/pytest tests/architecture/test_all_endpoints_have_response_model.py -v --tb=long
```

### Tarea 6: Full Test Suite + Regression

**Comandos (ejecutar en orden):**
```bash
# 1. Backend lint (configuración actual)
cd backend && .venv/bin/ruff check src/ tests/ --no-cache

# 2. Backend format
cd backend && .venv/bin/ruff format --check src/ tests/

# 3. Backend tests completos
cd backend && .venv/bin/pytest -x -q --tb=short

# 4. Architecture tests
cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short

# 5. Frontend type check
cd frontend && npx tsc --noEmit

# 6. Frontend tests
cd frontend && npx vitest run
```

**Criterio de éxito:** 0 errors, 0 warnings nuevos en todos los comandos.

---

## Resultado esperado

Al terminar esta auditoría, los 48 archivos de Phase 3 tendrán:
- Cero violaciones Ruff con `--select ALL`
- Docstrings en toda función/clase pública
- Type annotations completas
- Imports correctamente organizados (TYPE_CHECKING)
- Cross-module imports documentados en allowlists
- DDD boundaries respetadas (verificado por arch tests)
- Todos los endpoints con response_model + tenant_id
- Full test suite verde

Estos módulos serán el estándar de calidad para todo código futuro.
