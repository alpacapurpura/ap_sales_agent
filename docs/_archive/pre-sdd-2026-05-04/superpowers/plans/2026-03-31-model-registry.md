# Plan: Model Registry — Gestión Centralizada de Modelos AI

## Problema

Los modelos AI están dispersos y mal configurados:
- `OPENAI_MODEL` y `OPENAI_FAST_MODEL` apuntan ambos a `gpt-4o-mini` (sin diferenciación real)
- `image_analysis.py:14` hardcodea `"gpt-4o"` fuera de cualquier configuración
- `copilot/graph.py:244` instancia `ChatOpenAI` directamente, bypaseando la factory
- `safety_service.py:19` instancia `OpenAIService()` directamente
- Solo 2 tiers (`"smart"`/`"fast"`) no capturan la realidad (falta `vision`, `agent`, `reasoning`)
- El bug de `gpt-4-turbo-preview` deprecado demostró que un solo env var mal cacheado rompe todo

## Solución

Un **Model Registry** que mapea **roles semánticos** a **modelos concretos**, configurable por env vars.

### Roles Semánticos

| Role | Default Model | Propósito | Consumidores |
|------|--------------|-----------|-------------|
| `reasoning` | `gpt-4o` | Razonamiento complejo, JSON estructurado largo | Brand extraction, Sales qualification/closing/presentation, Offer psychology, Style analyzer (psychologist, architect) |
| `fast` | `gpt-4o-mini` | Tareas simples, bajo costo, alta velocidad | Safety check, Supervisor routing, Janitor, Greeting, Style simulator |
| `vision` | `gpt-4o` | Análisis de imágenes (multimodal) | Image analysis service |
| `agent` | `gpt-4o` | Tool-calling + contexto largo | Copilot agent node |
| `embedding` | `text-embedding-3-large` | Vectores densos para RAG | Vector stores (copilot, sales_agent) |

### Env Vars

```env
# Model Registry (cada uno overridea el default del rol)
AI_MODEL_REASONING=gpt-4o
AI_MODEL_FAST=gpt-4o-mini
AI_MODEL_VISION=gpt-4o
AI_MODEL_AGENT=gpt-4o
AI_MODEL_EMBEDDING=text-embedding-3-large
```

---

## Pasos de Implementación

### Step 1: Crear `ModelRole` enum + model registry en config

**File:** `backend/src/core/enums.py`

Agregar:

```python
class ModelRole(str, Enum):
    """Semantic roles for AI model selection.

    Each role maps to a specific model via env vars (AI_MODEL_<ROLE>).
    Consumers declare WHAT they need, not WHICH model.
    """
    REASONING = "reasoning"  # Complex analysis, structured JSON extraction
    FAST = "fast"            # Simple/cheap tasks, low latency
    VISION = "vision"        # Multimodal (image analysis)
    AGENT = "agent"          # Tool-calling, long context
    EMBEDDING = "embedding"  # Dense vector embeddings
```

**File:** `backend/src/core/config.py`

Reemplazar las 3 líneas de modelo OpenAI (lines 47-49) con el nuevo registry:

```python
    # --- AI Model Registry ---
    # Each role maps to a concrete model. Override per-role via env vars.
    AI_MODEL_REASONING: str = "gpt-4o"
    AI_MODEL_FAST: str = "gpt-4o-mini"
    AI_MODEL_VISION: str = "gpt-4o"
    AI_MODEL_AGENT: str = "gpt-4o"
    AI_MODEL_EMBEDDING: str = "text-embedding-3-large"

    def get_model(self, role: "ModelRole") -> str:
        """Resolve a semantic role to a concrete model name."""
        from src.core.enums import ModelRole
        _map = {
            ModelRole.REASONING: self.AI_MODEL_REASONING,
            ModelRole.FAST: self.AI_MODEL_FAST,
            ModelRole.VISION: self.AI_MODEL_VISION,
            ModelRole.AGENT: self.AI_MODEL_AGENT,
            ModelRole.EMBEDDING: self.AI_MODEL_EMBEDDING,
        }
        return _map[role]
```

Mantener las variables legacy como aliases para backwards-compat durante la migración:

```python
    # Legacy aliases (read-only properties for any code that still reads these)
    @property
    def OPENAI_MODEL(self) -> str:
        return self.AI_MODEL_REASONING

    @property
    def OPENAI_FAST_MODEL(self) -> str:
        return self.AI_MODEL_FAST

    @property
    def OPENAI_EMBEDDING_MODEL(self) -> str:
        return self.AI_MODEL_EMBEDDING
```

Eliminar las 3 líneas originales:
```python
# DELETE these:
OPENAI_MODEL: str = "gpt-4o-mini"
OPENAI_FAST_MODEL: str = "gpt-4o-mini"
OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
```

### Step 2: Refactorizar `OpenAIService` para usar roles

**File:** `backend/src/shared/infrastructure/llm/providers/openai.py`

Cambiar el constructor para crear modelos por rol bajo demanda en vez de 2 fijos:

```python
from src.core.enums import ModelRole

class OpenAIService(BaseLLMService):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self._models: Dict[str, ChatOpenAI] = {}  # cache by model name

        # Embedding model (always needed)
        self.embeddings = OpenAIEmbeddings(
            model=settings.get_model(ModelRole.EMBEDDING),
            api_key=self.api_key
        )

    def _get_chat_model(self, role: ModelRole) -> ChatOpenAI:
        """Get or create a ChatOpenAI instance for the given role."""
        model_name = settings.get_model(role)
        if model_name not in self._models:
            self._models[model_name] = ChatOpenAI(
                model=model_name,
                api_key=self.api_key,
                temperature=0.7,
            )
        return self._models[model_name]
```

Cambiar `generate_response` para aceptar `ModelRole` (con backwards-compat para `"smart"`/`"fast"` strings):

```python
    def generate_response(self, messages, system_prompt=None, model_type="smart", **kwargs) -> str:
        # Backwards-compat: map legacy strings to ModelRole
        if isinstance(model_type, str):
            _legacy_map = {
                "smart": ModelRole.REASONING,
                "fast": ModelRole.FAST,
                "vision": ModelRole.VISION,
                "agent": ModelRole.AGENT,
            }
            role = _legacy_map.get(model_type, ModelRole.REASONING)
        else:
            role = model_type  # Already a ModelRole

        selected_model = self._get_chat_model(role)
        # ... rest of method unchanged ...
```

Eliminar los atributos `self.chat_model`, `self.fast_chat_model`, `self.model_name`, `self.embedding_model_name`.

Actualizar `get_client()`:
```python
    def get_client(self, role: ModelRole = ModelRole.REASONING) -> ChatOpenAI:
        return self._get_chat_model(role)
```

### Step 3: Actualizar `BaseLLMService` interface

**File:** `backend/src/shared/infrastructure/llm/base.py`

Agregar import y actualizar signature de `generate_response`:

```python
from src.core.enums import ModelRole

class BaseLLMService(ABC):
    @abstractmethod
    def generate_response(self, messages, system_prompt=None, model_type="smart", **kwargs) -> str:
        pass

    # ... rest unchanged
```

No se rompe la interface porque `model_type` ya acepta strings por backwards-compat.

### Step 4: Actualizar `GeminiService`

**File:** `backend/src/shared/infrastructure/llm/providers/gemini.py`

Actualizar para aceptar `model_type` con el mismo patrón de legacy mapping (Gemini usa un solo modelo pero acepta el parámetro sin error).

### Step 5: Actualizar `AIModelPolicy` para usar `ModelRole`

**File:** `backend/src/shared/application/ai_action_service.py`

```python
from src.core.enums import ModelRole

@dataclass(frozen=True)
class AIModelPolicy:
    model_type: str | ModelRole = ModelRole.REASONING  # Accept both for migration
    temperature: float = 0.7
    max_output_tokens: int = 800
```

No se necesita cambiar nada más — `generate_response` maneja la conversión.

### Step 6: Fix `ImageAnalysisService` — eliminar hardcode

**File:** `backend/src/shared/infrastructure/files/image_analysis.py`

Reemplazar instancia directa de `ChatOpenAI` por uso de factory + role:

```python
from src.core.enums import ModelRole
from src.shared.infrastructure.llm.factory import LLMFactory

class ImageAnalysisService:
    def __init__(self):
        self.llm = LLMFactory.get_service().get_client(ModelRole.VISION)
        # Override specific params for vision tasks
        self.llm = self.llm.bind(
            temperature=0.2,
            max_tokens=500,
            response_format={"type": "json_object"},
        )
```

### Step 7: Fix `copilot/graph.py` — eliminar instancia directa

**File:** `backend/src/modules/copilot/application/orchestrator/graph.py`

Reemplazar líneas 244-249:

```python
# BEFORE (hardcoded):
llm = ChatOpenAI(
    model=settings.OPENAI_MODEL,
    api_key=settings.OPENAI_API_KEY,
    temperature=0.6,
    streaming=True,
)

# AFTER (via factory):
from src.core.enums import ModelRole
from src.shared.infrastructure.llm.factory import LLMFactory

llm = LLMFactory.get_service().get_client(ModelRole.AGENT)
llm = llm.bind(temperature=0.6)
```

### Step 8: Fix `safety_service.py` — usar factory

**File:** `backend/src/modules/sales_agent/infrastructure/external/safety_service.py`

Reemplazar línea 19:

```python
# BEFORE:
self.llm_service = OpenAIService()

# AFTER:
self.llm_service = LLMFactory.get_service()
```

### Step 9: Migrar consumidores de `"smart"` → `ModelRole.REASONING`

**Archivos y líneas exactas a cambiar:**

| File | Line | Before | After |
|------|------|--------|-------|
| `brand/application/extraction_service.py` | 55, 66 | `model_type="smart"` | `model_type=ModelRole.REASONING` |
| `sales_agent/.../nodes.py` | 137, 154, 168 | `model_type="smart"` | `model_type=ModelRole.REASONING` |
| `sales_agent/.../nodes.py` | 106 | `model_type="fast"` | `model_type=ModelRole.FAST` |
| `copilot/.../style_analyzer/nodes.py` | 59 | `model_type="fast"` | `model_type=ModelRole.FAST` |
| `copilot/.../style_analyzer/nodes.py` | 85, 125 | `model_type="smart"` | `model_type=ModelRole.REASONING` |
| `copilot/.../style_analyzer/nodes.py` | 150 | `model_type="fast"` | `model_type=ModelRole.FAST` |
| `copilot/.../offer_psychology_service.py` | 52 | `model_type="smart"` | `model_type=ModelRole.REASONING` |
| `safety_service.py` | 97 | `model_type="fast"` | `model_type=ModelRole.FAST` |

**NOTA:** Este paso es OPCIONAL en la primera iteración porque la backwards-compat maneja `"smart"`/`"fast"` strings automáticamente. Se puede hacer en un segundo commit como cleanup.

### Step 10: Actualizar `.env`

**File:** `.env`

Reemplazar:
```env
OPENAI_MODEL=gpt-4o-mini
```

Con:
```env
# AI Model Registry (role → model)
AI_MODEL_REASONING=gpt-4o
AI_MODEL_FAST=gpt-4o-mini
AI_MODEL_VISION=gpt-4o
AI_MODEL_AGENT=gpt-4o
AI_MODEL_EMBEDDING=text-embedding-3-large
```

### Step 11: Verificación

```bash
# 1. Rebuild containers
docker compose up -d --build api_dev
docker compose --profile extended up -d --force-recreate worker

# 2. Verify models
docker exec -t visionarias_brain_dev bash -c 'python -c "
from src.core.config import settings
from src.core.enums import ModelRole
print(f\"reasoning: {settings.get_model(ModelRole.REASONING)}\")
print(f\"fast:      {settings.get_model(ModelRole.FAST)}\")
print(f\"vision:    {settings.get_model(ModelRole.VISION)}\")
print(f\"agent:     {settings.get_model(ModelRole.AGENT)}\")
print(f\"embedding: {settings.get_model(ModelRole.EMBEDDING)}\")
# Legacy compat
print(f\"legacy OPENAI_MODEL: {settings.OPENAI_MODEL}\")
print(f\"legacy OPENAI_FAST_MODEL: {settings.OPENAI_FAST_MODEL}\")
"'

# 3. Run tests
docker exec -t visionarias_brain_dev bash -c "cd /app && ruff check src --no-cache"
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest -x -q --tb=short"

# 4. Test brand extraction (the original bug)
# Trigger from UI and check worker logs for success
docker logs visionarias_worker --tail 50
```

---

## Commit Strategy

**Commit 1:** `refactor(core): add ModelRole enum and AI model registry`
- `enums.py` — add `ModelRole`
- `config.py` — add registry settings + `get_model()` + legacy properties
- `.env` — new env vars

**Commit 2:** `refactor(llm): migrate OpenAIService to role-based model selection`
- `openai.py` — lazy model cache by role, backwards-compat mapping
- `base.py` — docstring update
- `gemini.py` — accept model_type param
- `ai_action_service.py` — update type hint

**Commit 3:** `fix(shared): eliminate hardcoded models in image analysis and copilot`
- `image_analysis.py` — use factory + `ModelRole.VISION`
- `copilot/graph.py` — use factory + `ModelRole.AGENT`
- `safety_service.py` — use factory instead of direct `OpenAIService()`

**Commit 4 (optional cleanup):** `refactor: migrate model_type strings to ModelRole enum`
- All consumer files: `"smart"` → `ModelRole.REASONING`, `"fast"` → `ModelRole.FAST`
- Remove legacy backwards-compat mapping once all consumers are migrated

---

## Archivos Afectados (Scope)

### Core (must change):
- `backend/src/core/enums.py`
- `backend/src/core/config.py`
- `.env`

### LLM Layer (must change):
- `backend/src/shared/infrastructure/llm/base.py`
- `backend/src/shared/infrastructure/llm/providers/openai.py`
- `backend/src/shared/infrastructure/llm/providers/gemini.py`
- `backend/src/shared/application/ai_action_service.py`

### Fix Hardcodes (must change):
- `backend/src/shared/infrastructure/files/image_analysis.py`
- `backend/src/modules/copilot/application/orchestrator/graph.py`
- `backend/src/modules/sales_agent/infrastructure/external/safety_service.py`

### Consumer Migration (optional, commit 4):
- `backend/src/modules/brand/application/extraction_service.py`
- `backend/src/modules/sales_agent/application/agents/sales/nodes.py`
- `backend/src/modules/copilot/application/agents/style_analyzer/nodes.py`
- `backend/src/modules/copilot/application/services/offer_psychology_service.py`

### NOT changed (no code changes needed):
- `backend/src/shared/infrastructure/llm/factory.py` — factory delegates to service, no model knowledge
- `backend/src/modules/brand/workers/tasks.py` — calls extraction_service, no direct model ref
- Vector stores — use `get_embedding_model()` which is already abstracted
- Semantic router — uses local sentence-transformer, not OpenAI
