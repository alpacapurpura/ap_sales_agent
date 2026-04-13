# Phase 3 — Interview Engine: Voice, Documents, Buyer Personas, Offer

> **Decisiones validadas con el usuario durante brainstorming.**
> Cada decisión lleva un ID para trazabilidad en el plan de implementación.

---

## 1. Alcance

Phase 3 extiende el Interview Engine (Phase 2) con 4 capacidades:

| ID | Capacidad | Descripción |
|----|-----------|-------------|
| V | **Voice (STT)** | Input por voz via Whisper. Toggle mic. Arquitectura abierta para TTS futuro. |
| D | **Document Processing** | Adjuntar documentos en la entrevista (inicio + mid-conversation). Procesamiento bloqueante. Componente vive en copilot. |
| BP | **Buyer Persona Interview** | Tercer dominio del engine. Entidad nueva `BuyerPersona` (depreca Avatar). Preview hybrid. |
| OI | **Offer Interview** | Cuarto dominio del engine. Escribe al `Offer` existente. Web research (inicial + on-demand). |

**Cross-cutting:**
- **Engine Generalization (EG):** Split view genérico + PreviewRegistry + InterviewConfig registry.
- **Entry Points (EP):** Dos modos (completa / enfocada). Botón "Modo Entrevista" en cada studio. Activable desde copilot.

---

## 2. Voice Service [V]

### 2.1 Decisiones

| Decisión | Elección | Razón |
|----------|----------|-------|
| STT provider | OpenAI Whisper API (`whisper-1`) | Calidad consistente en español, ya usamos OpenAI, ~$0.006/min despreciable |
| TTS | No implementar ahora | Arquitectura preparada con `SynthesisPort` para futuro |
| Mic UX | Toggle (click start / click stop) | Cómodo para respuestas largas (30+ seg), patrón WhatsApp conocido |

### 2.2 Backend

**Domain (ports — sin framework imports):**

```python
# copilot/domain/voice.py
@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str
    duration_seconds: float

class TranscriptionPort(Protocol):
    async def transcribe(self, audio: bytes, mime_type: str) -> TranscriptionResult: ...

class SynthesisPort(Protocol):
    """No implementado en Phase 3. Preparado para TTS futuro."""
    async def synthesize(self, text: str, voice: str) -> bytes: ...
```

**Infrastructure:**

```python
# copilot/infrastructure/voice/whisper_transcriber.py
class WhisperTranscriber(TranscriptionPort):
    async def transcribe(self, audio: bytes, mime_type: str) -> TranscriptionResult:
        # openai.audio.transcriptions.create(model="whisper-1", file=audio_buffer)
        # Formatos soportados: webm, mp4, wav, m4a (MediaRecorder produce webm)
        # Retorna TranscriptionResult con language detection automática
```

**API:**

```python
# copilot/api/voice.py
@router.post("/voice/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile,
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Recibe audio blob, retorna texto transcrito.
    El frontend decide qué hacer con el texto (sendMessage)."""
```

### 2.3 Frontend

**Hook:**

```typescript
// copilot/hooks/useVoiceRecorder.ts
// MediaRecorder API → audio blob → POST /voice/transcribe → transcript text
interface UseVoiceRecorderReturn {
  isRecording: boolean;
  isTranscribing: boolean;
  startRecording: () => void;
  stopRecording: () => Promise<string>;  // retorna transcript
  error: string | null;
  duration: number;  // segundos grabando (para UI timer)
}
```

**InterviewInput modificación:**

- Mic button: habilitar (remove `disabled`), wire toggle
- Estado `recording`: input text se oculta, aparece waveform + timer + stop button
- Estado `transcribing`: spinner "Transcribiendo..."
- Al obtener transcript: auto-envía via `onSend(transcript)`
- El mensaje en el chat se marca como `source: "voice"` (para TTS futuro: si source=voice, reproducir respuesta)

---

## 3. Document Processing [D]

### 3.1 Decisiones

| Decisión | Elección | Razón |
|----------|----------|-------|
| Componente vive en | `copilot/` (no brand/) | Reutilizable por cualquier dominio de entrevista |
| UX referencia | Claude Desktop (clip icon, chips inline) | Familiar, probado |
| Procesamiento | Bloqueante (síncrono en el request) | El agente necesita digerir todo antes de continuar |
| Inicio de entrevista | Paso 0 opcional: "¿Tienes documentos?" antes del primer mensaje | Pre-llena mapa_global, el consultor solo pregunta gaps |
| Mid-conversation | Clip icon siempre disponible en InterviewInput | Un solo doc por vez, procesamiento bloqueante ~5-15s |
| Extracción | Domain-specific via prompt template en InterviewConfig | Cada dominio tiene su propio prompt de extracción de documentos |

### 3.2 Backend

**InterviewConfig extensión:**

```python
# Agregar a InterviewConfig (copilot/domain/interview_config.py)
@dataclass(frozen=True)
class InterviewConfig:
    # ... campos existentes ...
    document_extraction_template: str | None = None  # Jinja2 template name
    supported_file_types: tuple[str, ...] = (".pdf", ".docx", ".txt", ".md", ".pptx")
```

**DocumentProcessor:**

```python
# copilot/application/services/document_processor.py
class DocumentProcessor:
    async def process_for_interview(
        self,
        files: list[UploadFile],
        config: InterviewConfig,
        existing_mapa: dict,
        tenant_id: UUID,
    ) -> DocumentProcessingResult:
        """
        1. FileParsingService.parse_file(file) → raw text (ya existe en shared/)
        2. Render extraction prompt: config.document_extraction_template + raw text
        3. LLM call: extraer campos estructurados → delta dict
        4. Merge delta into existing_mapa
        5. Return DocumentProcessingResult(updated_fields, summary, source_documents)
        """

@dataclass
class DocumentProcessingResult:
    delta: dict                # Campos extraídos (flat, dot-notation)
    summary: str               # Resumen legible de lo extraído
    source_documents: list[str] # Nombres de archivos procesados
    fields_extracted: int       # Para UI feedback
    fields_skipped: int         # Campos que ya tenían valor (no sobrescribir)
```

**API:**

```python
# copilot/api/interview.py (agregar al router existente)
@router.post("/interview/{session_id}/documents", response_model=DocumentProcessingResponse)
async def process_interview_documents(
    session_id: UUID,
    files: list[UploadFile] = File(...),
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Procesa documentos y actualiza mapa_global de la sesión.
    Bloqueante: retorna cuando toda la extracción termina."""
```

### 3.3 Frontend

**Componentes en copilot/ (reutilizables):**

```typescript
// copilot/components/shared/attachment-button.tsx
// Clip/paperclip icon. Click → file picker. Drag & drop en chat area.
// Props: { onFilesSelected: (files: File[]) => void; disabled?: boolean; accept?: string }

// copilot/components/shared/document-chip.tsx
// Chip inline que muestra: icono tipo archivo + nombre + estado (pending|processing|done|error)
// Props: { file: File; status: ProcessingStatus; onRemove?: () => void }
```

**InterviewInput modificación:**

- Agregar `AttachmentButton` junto al mic button
- Files seleccionados aparecen como `DocumentChip` entre el input y el área de mensajes
- Al enviar (send o voice): si hay archivos adjuntos, primero procesarlos (endpoint `/documents`), luego enviar mensaje con contexto actualizado
- Durante procesamiento: chips muestran spinner, input deshabilitado, mensaje "Analizando documentos..."

**Flujo inicio de entrevista:**

```
Usuario inicia entrevista
  → Modal: "¿Tienes documentos que puedan ayudar? (opcional)"
    → Sí: upload → procesamiento → mapa_global pre-llenado → consultor arranca con contexto
    → No / Skip: consultor arranca con mapa_global vacío (flujo actual)
```

**Flujo mid-conversation:**

```
Usuario adjunta doc + escribe mensaje (o solo adjunta)
  → Chat muestra: "Analizando [documento.pdf]..." (bloqueante)
  → Procesamiento completo → mapa_global actualizado
  → Preview panel se actualiza con datos nuevos
  → Si había mensaje: se envía con contexto ya actualizado
  → Si no había mensaje: el consultor genera respuesta reconociendo lo extraído
```

---

## 4. Engine Generalization [EG]

### 4.1 Backend — InterviewConfig Registry

```python
# copilot/domain/interview_config.py (existente, agregar registry)
DOMAIN_CONFIGS: dict[str, InterviewConfig] = {}

def register_interview_config(domain: str, config: InterviewConfig) -> None:
    DOMAIN_CONFIGS[domain] = config

def get_interview_config(domain: str) -> InterviewConfig:
    if domain not in DOMAIN_CONFIGS:
        raise ValueError(f"No interview config registered for domain: {domain}")
    return DOMAIN_CONFIGS[domain]
```

Cada config file se auto-registra al importarse:

```python
# copilot/domain/interview_configs/brand_config.py (existente, agregar registro)
register_interview_config("brand", BRAND_INTERVIEW_CONFIG)

# copilot/domain/interview_configs/buyer_persona_config.py (nuevo)
register_interview_config("buyer_persona", BUYER_PERSONA_INTERVIEW_CONFIG)

# copilot/domain/interview_configs/offer_config.py (nuevo)
register_interview_config("offer", OFFER_INTERVIEW_CONFIG)
```

### 4.2 Backend — Persister Registry extensión

```python
# copilot/infrastructure/persisters/persister_registry.py (existente, agregar)
PERSISTER_REGISTRY = {
    "brand": BrandPersister,
    "buyer_persona": BuyerPersonaPersister,  # nuevo
    "offer": OfferPersister,                 # nuevo
}
```

### 4.3 Backend — Web Research Tool [OI]

```python
# copilot/application/tools/interview/web_research.py
class WebResearchTool:
    """Busca información en internet: competencia, benchmarks, tendencias del nicho."""
    
    # Provider: Tavily API (purpose-built para AI agents, ~$5/1000 búsquedas)
    # Input: query (str), search_depth ("basic"|"advanced"), max_results (int)
    # Output: list[{title, url, content_snippet, relevance_score}]
    
    # Uso 1 (automático al inicio): OfferInterviewConfig.initial_research_queries
    #   → Se ejecutan antes del primer mensaje, resultados van al system prompt
    # Uso 2 (on-demand): LLM invoca cuando necesita investigar algo específico
    #   → Resultado se inyecta en contexto para la siguiente respuesta
```

**Infrastructure:**

```python
# copilot/infrastructure/web/tavily_search.py
class TavilySearchService:
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]: ...
    async def research_niche(self, niche: str, locale: str) -> NicheResearchReport: ...
```

### 4.4 Frontend — Preview Registry

```typescript
// copilot/config/interview-preview-registry.ts
import type { ComponentType } from "react";

interface PreviewConfig {
  summaryComponent: ComponentType<PreviewSummaryProps>;
  sectionsComponent: ComponentType<PreviewSectionsProps>;
  tabsComponent?: ComponentType<PreviewTabsProps>;  // Brand usa tabs, otros no
  emptyStateMessage: string;
}

interface PreviewSummaryProps {
  data: Record<string, unknown>;
  completenessScore: number;
}

interface PreviewSectionsProps {
  data: Record<string, unknown>;
  currentBlock: string;
  blocksCompleted: string[];
}

const PREVIEW_REGISTRY: Record<string, PreviewConfig> = {};

export function registerPreview(domain: string, config: PreviewConfig): void {
  PREVIEW_REGISTRY[domain] = config;
}

export function getPreview(domain: string): PreviewConfig {
  const config = PREVIEW_REGISTRY[domain];
  if (!config) throw new Error(`No preview registered for domain: ${domain}`);
  return config;
}
```

### 4.5 Frontend — InterviewSplitView Generalización

**Mover** de `brand/components/interview/` → `copilot/components/interview/interview-split-view.tsx`

**Cambios:**

```typescript
// ANTES: hardcoded brand
import { EsenciaView } from "@/features/brand/sections/...";
const BLOCK_TO_TAB = { identidad: "esencia", ... };

// DESPUÉS: registry-driven
interface InterviewSplitViewProps {
  domain: string;
  sessionId?: string;
  offerId?: string;       // Para offer interview
  personaId?: string;     // Para buyer persona interview
}

function InterviewSplitView({ domain, sessionId, ...props }: InterviewSplitViewProps) {
  const preview = getPreview(domain);
  const PreviewSummary = preview.summaryComponent;
  const PreviewSections = preview.sectionsComponent;
  
  // Left panel: <PreviewSummary /> + <PreviewSections />
  // Right panel: <InterviewChatPanel /> (sin cambios)
}
```

### 4.6 InterviewService.start_interview extensión

```python
# Cambios necesarios en copilot/application/services/interview_service.py
async def start_interview(
    self, tenant_id, user_id, domain,
    entity_id: UUID | None = None,     # NUEVO: offer_id, persona_id, etc.
    resume_session_id: UUID | None = None,
):
    config = get_interview_config(domain)
    
    # NUEVO: cargar datos previos de la entidad existente
    if entity_id and config.datos_previos_fields:
        persister = get_persister(domain, self.db)
        existing_data = await persister.load_existing(tenant_id, entity_id)
        initial_mapa = {k: v for k, v in existing_data.items() if v is not None}
    else:
        initial_mapa = {}
    
    # NUEVO: cargar contexto adicional (ej: otros offers del tenant)
    context_text = ""
    if config.context_loader:
        loader = get_context_loader(config.context_loader, self.db)
        context_text = await loader.load(tenant_id, entity_id)
    
    # NUEVO: ejecutar research inicial si habilitado
    research_text = ""
    if config.initial_research_enabled:
        research_text = await self._run_initial_research(tenant_id, config)
    
    session = InterviewSession.create(
        tenant_id, domain, config,
        initial_mapa=initial_mapa,       # NUEVO: pre-fill
        entity_id=entity_id,             # NUEVO: linked entity
    )
    # research_text y context_text se inyectan en el system prompt
```

### 4.7 Dos Modos de Entrevista

**Modo Completa (split view):**
- Ruta: `/brand-studio/interview?domain=brand|buyer_persona`
- Ruta: `/offer-studio/interview?offerId=xxx`
- Layout: InterviewSplitView genérico
- Usa InterviewSession con bloques y checkpoints
- Entry point: creación nueva o botón "Modo Entrevista" en header del studio

**Modo Enfocada (copilot panel lateral):**
- No cambia la ruta actual — el usuario sigue en la página del studio
- Copilot se abre con interview tools activados + contexto de la sección actual
- No crea InterviewSession formal — usa el copilot normal con tools de interview
- El copilot detecta la ruta (ej: `/offer-studio/[id]/pricing`) y activa el contexto
- Entry point: botón "Conversar sobre esta sección" en cada sección, o desde el copilot

---

## 5. Buyer Persona [BP]

### 5.1 Entidad BuyerPersona

```python
# brand/domain/buyer_persona.py
class BuyerPersona(BaseEntity):
    tenant_id: UUID
    user_id: UUID
    name: str
    tagline: str | None           # Frase clave: "Quiere escalar sin perder autenticidad"
    scope: str = "GLOBAL"         # GLOBAL | OFFER | CAMPAIGN
    offer_id: UUID | None = None  # Si scope=OFFER
    is_primary: bool = False

    # Perfil (JSONB — flexible, evoluciona con la entrevista)
    demographics: dict = {}       # age_range, location, occupation, income_range, education
    psychographics: dict = {}     # values, beliefs, lifestyle, personality_traits
    pain_points: list[dict] = []  # [{description, intensity, context, emotional_impact}]
    desires: list[dict] = []      # [{description, priority, emotional_trigger, urgency}]
    objections: list[dict] = []   # [{objection, root_cause, rebuttal, evidence}]
    preferred_channels: list[dict] = []  # [{channel, usage_pattern, content_preference}]
    buyer_journey: dict = {}      # {awareness, consideration, decision} por etapa
    purchase_triggers: list[str] = []
    anti_patterns: list[str] = []  # Qué los hace NO comprar

    # Metadata
    completeness_score: float = 0.0
    interview_session_id: UUID | None = None

    # Soft delete
    is_active: bool = True
    deleted_at: datetime | None = None
```

### 5.2 Migración

```sql
CREATE TABLE IF NOT EXISTS buyer_personas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    tagline TEXT,
    scope VARCHAR(20) NOT NULL DEFAULT 'GLOBAL',
    offer_id UUID REFERENCES offers(id) ON DELETE SET NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    demographics JSONB NOT NULL DEFAULT '{}',
    psychographics JSONB NOT NULL DEFAULT '{}',
    pain_points JSONB NOT NULL DEFAULT '[]',
    desires JSONB NOT NULL DEFAULT '[]',
    objections JSONB NOT NULL DEFAULT '[]',
    preferred_channels JSONB NOT NULL DEFAULT '[]',
    buyer_journey JSONB NOT NULL DEFAULT '{}',
    purchase_triggers JSONB NOT NULL DEFAULT '[]',
    anti_patterns JSONB NOT NULL DEFAULT '[]',
    completeness_score FLOAT NOT NULL DEFAULT 0.0,
    interview_session_id UUID,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_buyer_personas_tenant_id ON buyer_personas(tenant_id);
CREATE INDEX IF NOT EXISTS ix_buyer_personas_tenant_scope ON buyer_personas(tenant_id, scope);
```

### 5.3 Avatar Deprecation Strategy

- Phase 3 **no toca Avatar**. `BuyerPersona` es una entidad nueva, paralela.
- Tarea separada post-Phase 3: migrar datos Avatar → BuyerPersona, actualizar consumidores (sales_agent, offer), deprecar Avatar.
- Esto evita riesgo de romper módulos existentes durante Phase 3.

### 5.4 InterviewConfig

```python
# copilot/domain/interview_configs/buyer_persona_config.py

BUYER_PERSONA_BLOCKS = [
    InterviewBlock(
        id="demographics",
        label="Demografía y Contexto",
        campos_objetivo=[
            "demographics.age_range", "demographics.location",
            "demographics.occupation", "demographics.income_range",
            "demographics.education", "demographics.family_status",
        ],
        prompt_context="Comienza entendiendo QUIÉN es esta persona...",
        coverage_threshold=0.8,
    ),
    InterviewBlock(
        id="psychographics",
        label="Psicografía y Personalidad",
        campos_objetivo=[
            "psychographics.values", "psychographics.beliefs",
            "psychographics.lifestyle", "psychographics.personality_traits",
            "psychographics.media_consumption",
        ],
        prompt_context="Ahora explora QUÉ PIENSA y SIENTE esta persona...",
        coverage_threshold=0.7,
    ),
    InterviewBlock(
        id="pain_desire",
        label="Dolores y Deseos",
        campos_objetivo=[
            "pain_points", "desires",
            "pain_points.emotional_impact", "desires.urgency",
        ],
        prompt_context="Profundiza en los DOLORES (frustraciones, miedos, obstáculos) y DESEOS (aspiraciones, sueños, metas)...",
        coverage_threshold=0.8,
    ),
    InterviewBlock(
        id="objections",
        label="Objeciones y Barreras",
        campos_objetivo=[
            "objections", "anti_patterns", "purchase_triggers",
        ],
        prompt_context="Identifica las OBJECIONES: qué razones da para NO comprar...",
        coverage_threshold=0.7,
    ),
    InterviewBlock(
        id="channels_journey",
        label="Canales y Journey de Compra",
        campos_objetivo=[
            "preferred_channels", "buyer_journey.awareness",
            "buyer_journey.consideration", "buyer_journey.decision",
        ],
        prompt_context="Mapea DÓNDE vive esta persona digitalmente y CÓMO compra...",
        coverage_threshold=0.7,
    ),
]

BUYER_PERSONA_INTERVIEW_CONFIG = InterviewConfig(
    domain="buyer_persona",
    objetivo="Construir un buyer persona detallado que guíe toda la estrategia de marketing y ventas",
    bloques=BUYER_PERSONA_BLOCKS,
    output_schema_path="modules.brand.domain.buyer_persona.BuyerPersona",
    datos_previos_fields=["name", "demographics", "pain_points", "desires"],
    tono="Eres un investigador de mercado experto. Haces preguntas profundas, no superficiales.",
    expertise_template="buyer_persona_expertise",
    document_extraction_template="buyer_persona_doc_extraction",
    rag_collection=None,
)
```

### 5.5 Expertise Template

```
# copilot/infrastructure/prompts/templates/interview/buyer_persona_expertise.j2

Frameworks a aplicar:

**Jobs-to-be-Done (Clayton Christensen):**
- "¿Para qué TRABAJO contratan tu producto/servicio?"
- Functional job, emotional job, social job

**Empathy Map:**
- Piensa/Siente, Ve, Oye, Dice/Hace, Dolores, Ganancias

**Buyer Persona Canvas:**
- Trigger → Search → Evaluate → Decide → Use → Advocate

Reglas de extracción:
- pain_points: Siempre incluir emotional_impact (cómo les HACE SENTIR)
- desires: Distinguir entre lo que DICEN querer vs lo que REALMENTE quieren
- objections: Identificar root_cause (la objeción real detrás de la excusa)
- channels: Capturar CÓMO usan el canal, no solo cuál (ej: "Instagram stories para inspiración, no para comprar")
```

### 5.6 BuyerPersonaPersister

```python
# copilot/infrastructure/persisters/buyer_persona_persister.py
class BuyerPersonaPersister:
    """Escribe mapa_global → BuyerPersona entity."""
    
    async def persist(
        self, tenant_id: UUID, user_id: UUID,
        mapa_global: dict, fields_to_persist: list[str],
        entity_id: UUID | None = None,
    ) -> UUID:
        # Si entity_id: actualizar BuyerPersona existente
        # Si no: crear nuevo
        # Mapeo: mapa_global["demographics.age_range"] → persona.demographics["age_range"]
        # Calcular completeness_score basado en campos llenos / campos esperados
```

### 5.7 Preview (Frontend)

**Hybrid: Ficha resumen + secciones scrollables**

```typescript
// brand/components/interview/previews/persona-preview-summary.tsx
// Muestra: avatar circle + name + tagline + % completado

// brand/components/interview/previews/persona-preview-sections.tsx
// Secciones: Demographics, Psychographics, Pain Points, Desires,
//            Objections, Channels, Journey
// Cada sección con progress indicator y contenido llenándose en real-time
// Pain points: cards con border-left rojo
// Desires: cards con border-left verde
// Campos vacíos: "Pendiente..." en gris italic
```

Registrado en PreviewRegistry como `"buyer_persona"`.

---

## 6. Offer Interview [OI]

### 6.1 Decisiones

| Decisión | Elección | Razón |
|----------|----------|-------|
| Target | Offer existente en tabla `offers` | El interview enriquece, no crea desde cero |
| Contexto | Carga otros offers del tenant al iniciar | El consultor sabe dónde encaja en el ladder |
| Web research | Tavily API, inicial + on-demand | Análisis de competencia y benchmarks del nicho |
| Preview | Vista completa (7 secciones con progress) | Consistencia con editor existente |

### 6.2 InterviewConfig

```python
# copilot/domain/interview_configs/offer_config.py

OFFER_BLOCKS = [
    InterviewBlock(
        id="identity_strategy",
        label="Identidad y Estrategia",
        campos_objetivo=[
            "public_name", "archetype", "delivery_model",
            "value_level", "format_hint",
        ],
        prompt_context="Define QUÉ es este offer y DÓNDE encaja en el ladder de valor...",
        coverage_threshold=0.8,
    ),
    InterviewBlock(
        id="promise",
        label="Promesa y Resultado",
        campos_objetivo=[
            "headline_promise", "primary_outcome",
            "time_to_value", "target_avatar_match",
        ],
        prompt_context="Construye la PROMESA — el resultado específico y medible que el cliente obtiene...",
        coverage_threshold=0.8,
    ),
    InterviewBlock(
        id="psychology",
        label="Psicología de Venta",
        campos_objetivo=[
            "marketing_pain_points", "marketing_desires",
            "objections",
        ],
        prompt_context="Mapea la psicología de compra: qué dolor activa la búsqueda, qué deseo motiva la acción, qué objeciones frenan...",
        coverage_threshold=0.8,
    ),
    InterviewBlock(
        id="pricing",
        label="Pricing y Garantía",
        campos_objetivo=[
            "pricing_options", "price_pay_in_full",
            "guarantee_type", "guarantee_terms",
        ],
        prompt_context="Diseña la estructura de precio, opciones de pago, y garantía que reduzca riesgo percibido...",
        coverage_threshold=0.7,
    ),
    InterviewBlock(
        id="value_stack",
        label="Value Stack y Entregables",
        campos_objetivo=[
            "deliverables", "includes_offers",
            "access_duration_text", "support_duration_days",
        ],
        prompt_context="Construye el VALUE STACK: qué recibe el cliente, cuánto vale cada pieza, cómo anclar el precio...",
        coverage_threshold=0.7,
    ),
    InterviewBlock(
        id="closing",
        label="Cierre y Acción",
        campos_objetivo=[
            "onboarding_action", "prerequisites",
            "requires_application", "anti_avatar_keywords",
        ],
        prompt_context="Define el CIERRE: CTA, proceso de onboarding, calificación, urgencia/escasez legítima...",
        coverage_threshold=0.6,
    ),
]

OFFER_INTERVIEW_CONFIG = InterviewConfig(
    domain="offer",
    objetivo="Diseñar un offer irresistible, diferenciado, y alineado con el ladder de valor del negocio",
    bloques=OFFER_BLOCKS,
    output_schema_path="modules.offer.domain.offer.Offer",
    datos_previos_fields=["public_name", "archetype", "pricing_options", "headline_promise"],
    tono="Eres un estratega de producto con experiencia en info-productos, SaaS, y servicios premium.",
    expertise_template="offer_expertise",
    document_extraction_template="offer_doc_extraction",
    rag_collection=None,
    # Extensiones para offer:
    initial_research_enabled=True,
    context_loader="offer_context",  # Carga otros offers del tenant
)
```

### 6.3 InterviewConfig extensión para research y contexto

```python
# Agregar a InterviewConfig (copilot/domain/interview_config.py)
@dataclass(frozen=True)
class InterviewConfig:
    # ... campos existentes ...
    document_extraction_template: str | None = None
    supported_file_types: tuple[str, ...] = (".pdf", ".docx", ".txt", ".md", ".pptx")
    initial_research_enabled: bool = False   # Ejecutar web research al inicio
    context_loader: str | None = None        # Key para cargar contexto adicional
```

### 6.4 Context Loader

```python
# copilot/infrastructure/context/offer_context_loader.py
class OfferContextLoader:
    """Carga contexto de otros offers del tenant para el system prompt."""
    
    async def load(self, tenant_id: UUID, offer_id: UUID) -> str:
        # 1. Cargar todos los offers del tenant
        # 2. Construir resumen del ladder (value_level → offer name + price + status)
        # 3. Identificar gaps en el ladder
        # 4. Formatear como contexto para el system prompt
        # Resultado: "El usuario tiene 3 offers: Lead Magnet ($0), Programa Core ($997)...
        #             Gap: no tiene offer de ACTIVACIÓN entre gratuito y core."
```

```python
# copilot/infrastructure/context/context_loader_registry.py
CONTEXT_LOADERS = {
    "offer_context": OfferContextLoader,
}
```

### 6.5 Initial Research Flow

```
start_interview(domain="offer", offer_id=xxx)
  → config.initial_research_enabled == True
  → Cargar BrandSettings del tenant (nicho, industria, competidores)
  → TavilySearchService.research_niche(nicho, locale)
  → Queries automáticas:
    - "{nicho} pricing benchmark {año}"
    - "{nicho} best {archetype} offers"
    - Competidores nombrados en BrandSettings → buscar sus offers
  → Resultados se inyectan en system prompt como research_context
  → El consultor arranca "preparado" con datos del mercado
```

### 6.6 OfferPersister

```python
# copilot/infrastructure/persisters/offer_persister.py
class OfferPersister:
    """Escribe mapa_global → Offer entity existente."""
    
    async def persist(
        self, tenant_id: UUID, user_id: UUID,
        mapa_global: dict, fields_to_persist: list[str],
        entity_id: UUID | None = None,  # offer_id — REQUIRED para offer
    ) -> UUID:
        # Cargar Offer por entity_id + tenant_id
        # Mapeo: mapa_global["pricing_options"] → offer.pricing_options
        # Tipos complejos: "objections" → list[ObjectionItem], "pricing_options" → list[PricingStructure]
        # Validar: archetype-specific_details coherence
```

### 6.7 Expertise Template

```
# copilot/infrastructure/prompts/templates/interview/offer_expertise.j2

Frameworks a aplicar:

**Value Stacking (Russell Brunson):**
- Cada deliverable tiene un valor percibido individual
- La suma de valores > precio total → oferta irresistible
- "Si cada pieza valiera X y tú pagaras solo Y..."

**Pricing Psychology:**
- Anclaje: mostrar valor total vs precio real
- Fraccionamiento: cuotas que parezcan accesibles
- Comparación: "menos que un café al día" o vs costo de NO resolver

**Guarantee Framework:**
- Condicional (requiere acción del cliente) vs Incondicional (money-back)
- Risk reversal: reduce fricción de compra
- Alinear tipo de garantía con delivery_model

**Objection Mapping:**
- Identificar trigger_phrases (qué dice el prospecto)
- Encontrar root_cause (el miedo real detrás)
- Construir rebuttal (respuesta + evidencia)

{% if research_context %}
**Investigación de Mercado:**
{{ research_context }}
{% endif %}

{% if other_offers_context %}
**Ladder de Valor del Negocio:**
{{ other_offers_context }}
Regla: este offer debe complementar el ladder, no competir con otros offers propios.
{% endif %}

Reglas de redacción:
- headline_promise: MAX 15 palabras. Resultado específico + tiempo (si aplica)
- primary_outcome: Lo que cambia en la vida del cliente DESPUÉS
- objections: Siempre incluir trigger_phrases (frases textuales del prospecto)
- deliverables: Nombre atractivo + formato + valor individual percibido
```

### 6.8 Preview (Frontend)

**Hybrid: Ficha resumen + 7 secciones completas**

```typescript
// offer-studio/components/interview/previews/offer-preview-summary.tsx
// Muestra: icono arquetipo + nombre + tags (arquetipo, value_level) + precio + % completado

// offer-studio/components/interview/previews/offer-preview-sections.tsx
// 7 secciones: Identity, Strategy, Promise, Psychology, Pricing, Value Stack, Closing
// Cada una con progress indicator
// Psychology: pain cards (rojo), desire cards (verde), objection cards (amarillo)
// Value Stack: deliverables como checklist con valor percibido
// Campos vacíos: "Pendiente..." en gris italic
```

Registrado en PreviewRegistry como `"offer"`.

---

## 7. Entry Points [EP]

### 7.1 Modo Completa — Rutas

| Dominio | Ruta | Cómo llega |
|---------|------|------------|
| Brand | `/brand-studio/interview` | Wizard "Haciéndolo Juntos" (existente) o botón header |
| Buyer Persona | `/brand-studio/interview?domain=buyer_persona&personaId=xxx` | Tab Público → "Crear/Editar con entrevista" |
| Offer | `/offer-studio/interview?offerId=xxx` | Card offer → "Diseñar con consultor" o botón header |

### 7.2 Modo Enfocada — Copilot Panel Lateral

- El copilot detecta la ruta actual via `ROUTE_TOOL_MAP` (ya existe)
- Si el usuario está en una sección editable, los interview tools se activan automáticamente
- El copilot muestra un badge "Modo Entrevista" cuando tiene interview tools activos
- El usuario puede pedir: "ayúdame con la promesa", "mejora mis objeciones", etc.
- No crea InterviewSession — el copilot recibe el `entity_id` y `domain` via route context, carga la entidad, y los interview tools (extract_structured, offer_alternatives, clarify) operan directamente sobre ella via el persister correspondiente. Los cambios se persisten inmediatamente (no hay mapa_global intermedio en modo enfocado)

### 7.3 Botón "Modo Entrevista"

```typescript
// Componente reutilizable: copilot/components/shared/interview-mode-button.tsx
// Props: { domain: string; entityId?: string; label?: string }
// Renderiza: botón con icono de chat/consultor
// Al click: navega a la ruta de entrevista completa con los params correctos
// Se coloca en el header de cada studio
```

### 7.4 Botón "Conversar sobre esta sección"

```typescript
// Componente reutilizable: copilot/components/shared/section-chat-trigger.tsx
// Props: { sectionId: string; sectionLabel: string }
// Renderiza: icono pequeño junto al título de la sección
// Al click: abre el copilot panel con contexto de la sección pre-cargado
```

---

## 8. Mapa de Dependencias para Multi-Agent

```
                    ┌─────────────────┐
                    │  EG: Engine     │
                    │  Generalization │
                    │  (backend)      │
                    └───────┬─────────┘
                            │ depende de EG:
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐
     │ BP: Buyer  │ │ OI: Offer  │ │ EG: Split  │
     │ Persona    │ │ Interview  │ │ View + Reg │
     │ (backend)  │ │ (backend)  │ │ (frontend) │
     └─────┬──────┘ └─────┬──────┘ └──────┬─────┘
           │              │               │
           ▼              ▼               ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐
     │ BP Preview │ │ OI Preview │ │ EP: Entry  │
     │ (frontend) │ │ (frontend) │ │ Points     │
     └────────────┘ └────────────┘ └────────────┘

  ┌──────────────┐  ┌──────────────┐
  │ V: Voice     │  │ D: Document  │
  │ (indepen-    │  │ Processing   │
  │  diente)     │  │ (indepen-    │
  └──────────────┘  │  diente)     │
                    └──────────────┘
```

**Streams paralelos:**

| Stream | Qué incluye | Dependencias | Agent type |
|--------|-------------|-------------|------------|
| **S1: Voice** | Domain ports, Whisper infra, API endpoint, useVoiceRecorder hook, InterviewInput mic | Ninguna | backend + frontend |
| **S2: Documents** | DocumentProcessor, extraction templates, API endpoint, AttachmentButton, DocumentChip, InterviewInput clip | Ninguna | backend + frontend |
| **S3: Engine General (backend)** | Config registry, InterviewConfig extensions, context loaders, web research tool + Tavily service | Ninguna | backend |
| **S4: BuyerPersona (backend)** | Entity, model, repo, migration, config, persister, expertise template | S3 (registry) | backend |
| **S5: Offer (backend)** | Config, persister, expertise template, research queries | S3 (registry + web research) | backend |
| **S6: Frontend Generalization** | PreviewRegistry, InterviewSplitView genérico, BrandPreview refactor | S3 (architecture) | frontend |
| **S7: BP Preview** | PersonaPreviewSummary, PersonaPreviewSections, registry entry | S4 + S6 | frontend |
| **S8: OI Preview** | OfferPreviewSummary, OfferPreviewSections, registry entry | S5 + S6 | frontend |
| **S9: Entry Points** | InterviewModeButton, SectionChatTrigger, routing, focused mode wiring | S6 + S7 + S8 | frontend |

**Fases de ejecución:**

| Fase | Streams | Parallelizable |
|------|---------|---------------|
| **A** | S1, S2, S3 | Sí (3 agentes) |
| **B** | S4, S5, S6 | Sí (3 agentes, dependen de S3) |
| **C** | S7, S8 | Sí (2 agentes, dependen de S4/S5 + S6) |
| **D** | S9 | Secuencial (depende de todo) |

---

## 9. Testing Strategy

| Stream | Tests |
|--------|-------|
| S1 Voice | `test_whisper_transcriber.py` (mock OpenAI), `test_voice_api.py`, `useVoiceRecorder.test.ts` |
| S2 Docs | `test_document_processor.py` (mock LLM), `test_documents_api.py`, `attachment-button.test.tsx`, `document-chip.test.tsx` |
| S3 Engine | `test_config_registry.py`, `test_web_research_tool.py` (mock Tavily), `test_context_loaders.py` |
| S4 BP | `test_buyer_persona_entity.py`, `test_buyer_persona_repository.py`, `test_buyer_persona_persister.py`, `test_buyer_persona_config.py` |
| S5 Offer | `test_offer_persister.py`, `test_offer_config.py`, `test_offer_context_loader.py` |
| S6-S8 Frontend | `interview-split-view.test.tsx`, `preview-registry.test.ts`, `persona-preview.test.tsx`, `offer-preview.test.tsx` |
| S9 Entry | `interview-mode-button.test.tsx`, E2E smoke por ruta |
| Arch | Agregar `buyer_persona` y `offer` a fitness tests existentes |

---

## 10. Resumen de Decisiones

| # | Decisión | Elección |
|---|----------|----------|
| 1 | Scope Phase 3 | Voice + Docs + Buyer Persona + Offer (todo junto) |
| 2 | Doc integration | Inicio (paso 0 opcional) + mid-conversation (clip icon) |
| 3 | Doc processing | Bloqueante — el agente digiere todo antes de continuar |
| 4 | Doc component lives in | copilot/ (reutilizable, estilo Claude Desktop) |
| 5 | STT provider | OpenAI Whisper API |
| 6 | TTS | No ahora. SynthesisPort preparado para futuro |
| 7 | Mic UX | Toggle (click start / click stop) |
| 8 | BuyerPersona model | Entidad nueva en brand/domain/, tabla `buyer_personas` |
| 9 | Avatar | No se toca en Phase 3. Deprecación en tarea separada posterior |
| 10 | Offer interview target | Offer existente en tabla `offers` |
| 11 | Offer context | Carga otros offers del tenant (ladder awareness) |
| 12 | Web research | Tavily API, inicial automático + on-demand durante conversación |
| 13 | Split view | Genérico + PreviewRegistry (copilot/config/) |
| 14 | Persona preview | Hybrid: ficha resumen + secciones scrollables |
| 15 | Offer preview | Vista completa: 7 secciones con progress |
| 16 | Entry points | Creación + botón "Modo Entrevista" en header + desde copilot |
| 17 | Dos modos | Completa (split view + session) / Enfocada (copilot panel + tools) |
| 18 | Entrevista enfocada UI | Panel lateral (copilot al costado) |
| 19 | Registrar nuevo dominio | 4 piezas: Config + Persister + ExpertiseTemplate + PreviewComponent |
| 20 | Paralelización | 9 streams en 4 fases (A→B→C→D) |
