# Interview Engine — Fase 2: Diseño Detallado

**Fecha:** 2026-04-12
**Scope:** Motor de entrevista IA reutilizable (chat semi-estructurado) integrado al Brand Studio como primer caso.
**Prerequisito:** Fase 1 completa (wizard + docs + tabs). Spec: `2026-04-12-brand-onboarding-interview-engine-design.md`

---

## Decisiones de Arquitectura

| Decisión | Elección | Alternativas descartadas |
|----------|----------|--------------------------|
| Session persistence | Tabla nueva `interview_sessions` | Extender conversations / Hybrid |
| Split view layout | Ruta nueva `/brand-studio/interview` | Overlay modal / In-place morph |
| Mapa global persistence | Por checkpoint (confirmación) | Solo al final / Cada turn |
| Preview updates | React Query + UIAction optimistic | SSE event / Polling / Solo client |
| Banner + restore | Endpoint `/interview/active` + banner global | Context-only / LocalStorage |
| Prompts expertise | Jinja2 base + RAG ejemplos + web search | Solo Jinja2 / Solo RAG |

---

## 1. InterviewSession — Modelo de Datos

### 1.1 Domain Entity

**Ubicación:** `backend/src/modules/copilot/domain/interview_session.py`

```python
class InterviewSession:
    id: UUID
    tenant_id: UUID
    domain: str                        # "brand", "offer", "buyer_persona", "campaign"
    config_snapshot: dict              # InterviewConfig serializado (inmutable post-creación)
    conversation_id: UUID              # FK a copilot conversations
    mapa_global: dict                  # JSONB — estructura mirrors output_schema
    bloque_actual: str                 # ID del bloque en progreso
    bloques_completados: list[str]     # IDs de bloques ya confirmados
    status: InterviewStatus            # "active" | "paused" | "completed" | "abandoned"
    messages_count: int                # Contador para límite de 60
    created_at: datetime
    updated_at: datetime
```

```python
class InterviewStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
```

### 1.2 InterviewConfig (Value Object inmutable)

**Ubicación:** `backend/src/modules/copilot/domain/interview_config.py`

```python
@dataclass(frozen=True)
class InterviewConfig:
    domain: str                          # "brand"
    objetivo: str                        # "Completar Brand Studio"
    bloques: list[InterviewBlock]        # Bloques temáticos ordenados
    output_schema_path: str              # "modules.brand.domain.BrandSettings"
    datos_previos_fields: list[str]      # Campos a cargar del modelo existente
    tono: str                            # "consultor senior, cercano, directo"
    max_mensajes: int = 60              # Límite de seguridad
    expertise_template: str              # Nombre del template Jinja2 base
    rag_collection: str | None           # Qdrant collection para ejemplos

@dataclass(frozen=True)
class InterviewBlock:
    id: str                              # "identidad", "posicionamiento", etc.
    label: str                           # "Tu Identidad"
    campos_objetivo: list[str]           # ["story.origin_story", "story.mission", ...]
    prompt_context: str                  # Instrucciones específicas para la IA
    coverage_threshold: float = 0.8      # % de campos para considerar completo
                                         # Cálculo: len(mapa_global[field] for field in campos_objetivo if filled) / len(campos_objetivo)
```

### 1.3 BrandInterviewConfig (instancia concreta)

**Ubicación:** `backend/src/modules/copilot/domain/interview_configs/brand_config.py`

5 bloques temáticos:
1. **identidad** — origin_story, mission, vision, brand_name, industry, values
2. **posicionamiento** — uvp, discriminator, competitors, consumer_insight, benefits
3. **narrativa** — hero, problem, guide, plan, cta, outcome (StoryBrand)
4. **publico** — buyer persona basics (demographics, pain points, desires)
5. **identidad_creativa** — archetype, tone_of_voice, personality_traits, visual direction

### Criterios de Aceptación — Modelo de Datos

- [ ] **AC-1.1:** Tabla `interview_sessions` existe con todas las columnas del schema. Migración idempotente (raw SQL + IF NOT EXISTS).
- [ ] **AC-1.2:** `mapa_global` es JSONB con estructura libre (el schema lo define el InterviewConfig, no la tabla).
- [ ] **AC-1.3:** FK `conversation_id` referencia `copilot_conversations.id`. ON DELETE SET NULL.
- [ ] **AC-1.4:** Índice único `(tenant_id, domain, status)` WHERE `status = 'active'` — solo una entrevista activa por tenant por dominio.
- [ ] **AC-1.5:** `InterviewConfig` es un frozen dataclass. Serializable a dict para `config_snapshot`.
- [ ] **AC-1.6:** `BrandInterviewConfig` tiene exactamente 5 bloques con los campos_objetivo listados arriba.
- [ ] **AC-1.7:** Soft delete (columna `deleted_at`). Queries filtran `deleted_at IS NULL`.
- [ ] **AC-1.8:** Toda query filtra por `tenant_id`.

---

## 2. Interview Tools (Backend)

### 2.1 Tool Group Registration

**Ubicación:** `backend/src/modules/copilot/application/tools/registry.py`

Nuevo tool group `"interview"` registrado en `TOOL_GROUPS`. Se activa en `ROUTE_TOOL_MAP` para la ruta `"brand-studio/interview"` (y futuras rutas de entrevista).

```python
ROUTE_TOOL_MAP = {
    ...existing,
    "brand-studio/interview": ["interview", "knowledge"],
}
```

### 2.2 extract_structured

**Ubicación:** `backend/src/modules/copilot/application/tools/interview/extract_structured.py`

**Propósito:** Extrae datos estructurados del último mensaje del usuario y actualiza el mapa_global. Se invoca en CADA turn. Es silencioso para el usuario (no genera texto visible).

**Input (args de la IA):**
```python
class ExtractionItem(BaseModel):
    field_path: str          # "story.origin_story", "positioning.competitors"
    value: Any               # El valor redactado con expertise
    confidence: float        # 0.0-1.0 (< 0.8 = pendiente clarificación)
    source: str              # "user_explicit" | "inferred" | "recommended"

class ExtractStructuredInput(BaseModel):
    extractions: list[ExtractionItem]
```

**Lógica interna:**
1. Lee session.mapa_global de DB
2. Merge cada extraction al mapa_global usando `field_path` como clave (dot notation → nested dict)
3. Persiste mapa_global actualizado a DB
4. Retorna ui_action `preview_update` con el delta

**Output:**
```python
{
    "text": "",  # Vacío — extract es silencioso
    "ui_action": {
        "type": "preview_update",
        "session_id": "uuid",
        "delta": {"story.origin_story": "...", "positioning.competitors": [...]},
        "confidence_map": {"positioning.competitors": 0.7}
    }
}
```

### 2.3 clarify

**Ubicación:** `backend/src/modules/copilot/application/tools/interview/clarify.py`

**Propósito:** Presenta una contradicción o ambigüedad al usuario. Se usa SOLO cuando la IA detecta información contradictoria. NO se usa para confirmar datos.

**Input:**
```python
class ClarifyItem(BaseModel):
    field_path: str
    issue: str               # Descripción del problema detectado
    options: list[str]       # 2-4 opciones de resolución rápida

class ClarifyInput(BaseModel):
    items: list[ClarifyItem]   # Max 2 items por clarify (brevedad)
```

**Output:**
```python
{
    "text": "Noté algo que quiero aclarar:",
    "ui_action": {
        "type": "clarify_card",
        "items": [{"field_path": "...", "issue": "...", "options": [...]}]
    }
}
```

### 2.4 offer_alternatives

**Ubicación:** `backend/src/modules/copilot/application/tools/interview/offer_alternatives.py`

**Propósito:** Presenta 2-4 opciones con recomendación cuando el usuario no tiene claro algo. Es el tool principal de cocreación.

**Input:**
```python
class Alternative(BaseModel):
    id: str                  # "a", "b", "c"
    title: str               # Nombre corto
    description: str         # 1-2 líneas explicativas
    recommended: bool = False
    recommendation_reason: str | None = None

class OfferAlternativesInput(BaseModel):
    field_path: str          # Campo que se llenará con la selección
    question: str            # Contexto breve para el usuario
    alternatives: list[Alternative]  # 2-4 opciones
    allow_custom: bool = True        # "Otro que no está aquí"
```

**Output:**
```python
{
    "text": "",
    "ui_action": {
        "type": "alternatives_card",
        "field_path": "...",
        "question": "...",
        "alternatives": [...],
        "allow_custom": true
    }
}
```

### 2.5 checkpoint

**Ubicación:** `backend/src/modules/copilot/application/tools/interview/checkpoint.py`

**Propósito:** Genera síntesis breve del bloque actual para confirmación rápida. No es un resumen extenso — es un flash compacto.

**Input:**
```python
class CheckpointInput(BaseModel):
    block_id: str            # Bloque que se está cerrando
```

**Lógica interna:**
1. Lee mapa_global[campos del bloque]
2. Calcula health score del bloque
3. Genera síntesis compacta (field: valor, una línea por campo)
4. Retorna checkpoint_card

**Output:**
```python
{
    "text": "Tengo lo que necesito. Mira cómo quedó:",
    "ui_action": {
        "type": "checkpoint_card",
        "block_id": "identidad",
        "block_label": "Identidad",
        "summary": {"story.origin_story": "...", "story.mission": "..."},
        "health_score": 85,
        "blocks_progress": {"completed": 1, "total": 5}
    }
}
```

### 2.6 advance_block

**Ubicación:** `backend/src/modules/copilot/application/tools/interview/advance_block.py`

**Propósito:** Post-confirmación del checkpoint. Persiste al modelo de dominio y avanza.

**Input:**
```python
class AdvanceBlockInput(BaseModel):
    block_id: str
    corrections: dict | None = None   # Correcciones del usuario antes de confirmar
```

**Lógica interna:**
1. Si hay corrections → merge al mapa_global
2. Lee mapa_global[campos del bloque confirmado]
3. Escribe al modelo de dominio (`BrandSettings.update(tenant_id, partial_data)`)
4. Marca bloque como completado en InterviewSession
5. Actualiza `bloque_actual` al siguiente bloque
6. Si era el último bloque → invoca complete_interview internamente

**Output:**
```python
{
    "text": "¡Guardado! Pasemos a {next_block_label}.",
    "ui_action": {
        "type": "preview_update",
        "delta": {...persisted_fields},
        "persisted": true  # Frontend sabe que estos ya están en BrandSettings
    },
    "metadata": {
        "next_block": "posicionamiento",
        "blocks_completed": ["identidad"]
    }
}
```

### 2.7 complete_interview

**Ubicación:** `backend/src/modules/copilot/application/tools/interview/complete_interview.py`

**Propósito:** Cierra la sesión completa.

**Input:**
```python
class CompleteInterviewInput(BaseModel):
    session_id: UUID
```

**Lógica interna:**
1. Verifica que todos los bloques estén completados (o que el agente decidió cerrar por límite)
2. InterviewSession.status → COMPLETED
3. Calcula health score final del modelo de dominio
4. Retorna redirect

**Output:**
```python
{
    "text": "¡Tu marca está lista!",
    "ui_action": {
        "type": "interview_complete",
        "health_score": 92,
        "redirect": "/brand-studio"
    }
}
```

### Criterios de Aceptación — Tools

- [ ] **AC-2.1:** Tool group `"interview"` registrado en `TOOL_GROUPS` y `ROUTE_TOOL_MAP["brand-studio/interview"]`.
- [ ] **AC-2.2:** `extract_structured` escribe al mapa_global JSONB con merge profundo (dot notation → nested dict). Nunca sobreescribe campos no mencionados.
- [ ] **AC-2.3:** `extract_structured` retorna `text: ""` (silencioso). El ui_action `preview_update` contiene solo el delta, no el mapa_global completo.
- [ ] **AC-2.4:** `clarify` se limita a max 2 items por invocación. Cada item tiene max 4 options de resolución rápida.
- [ ] **AC-2.5:** `offer_alternatives` soporta 2-4 alternativas. Exactamente una puede tener `recommended: true`. `allow_custom: true` permite respuesta libre.
- [ ] **AC-2.6:** `checkpoint` genera síntesis compacta — max 1 línea por campo, no párrafos. Incluye health_score numérico.
- [ ] **AC-2.7:** `advance_block` persiste al modelo de dominio via service layer (no acceso directo a repo). Aplica corrections antes de persistir.
- [ ] **AC-2.8:** `advance_block` auto-avanza al siguiente bloque. Si era el último, invoca `complete_interview`.
- [ ] **AC-2.9:** `complete_interview` cambia status a COMPLETED y retorna redirect al Brand Studio.
- [ ] **AC-2.10:** Todos los tools filtran por `tenant_id`. Un tenant no puede acceder a sesiones de otro.
- [ ] **AC-2.11:** Todos los tools validan que la session esté en status ACTIVE antes de ejecutar. Si no → error descriptivo.
- [ ] **AC-2.12:** `messages_count` se incrementa en cada turn. A los 50 mensajes se inyecta aviso en system prompt. A los 60 se fuerza checkpoint + pausa.

---

## 3. InterviewOrchestrator — Lógica del Agente

### 3.1 System Prompt Structure

**Ubicación:** `backend/src/modules/copilot/infrastructure/prompts/templates/interview_system.j2`

```
{{ base_persona }}
{{ domain_expertise }}
{{ interview_config_context }}
{{ mapa_global_snapshot }}
{{ conversation_rules }}
```

### 3.2 base_persona

```
Eres un consultor senior de {{ domain_label }} trabajando con el dueño de un negocio.
Tu rol es COCREAR, no encuestar. Eres el experto — el usuario tiene el conocimiento de su negocio, tú tienes el conocimiento de {{ domain_label }}.

REGLAS ABSOLUTAS:
1. UNA pregunta por mensaje. Breve. Directa. Que invite reflexión.
2. NUNCA preguntes campo por campo como formulario. Preguntas estratégicas abiertas.
3. NUNCA repitas algo que el usuario ya mencionó — revisa el mapa_global antes de preguntar.
4. Extrae SIEMPRE con extract_structured después de cada mensaje del usuario. Es silencioso.
5. Si el usuario duda o dice "no sé" → usa offer_alternatives con tu recomendación.
6. Si detectas contradicción → usa clarify (max 2 items). NO para confirmar datos buenos.
7. Cuando el bloque tiene coverage > 80% → usa checkpoint. No te extiendas.
8. Tu texto visible es BREVE. 1-3 oraciones max. La profundidad va en los cards.
9. Redacta con expertise ({{ frameworks }}). No copies literal lo que dice el usuario.
10. Da tu recomendación cuando aplica. Eres el experto. El usuario espera tu opinión.
```

### 3.3 domain_expertise (Jinja2 template — Brand)

```
FRAMEWORKS QUE APLICAS:
- StoryBrand (Donald Miller): hero, problem, guide, plan, CTA, success/failure
- Brand Love Key: functional benefit, emotional benefit, brand character, reason to believe
- Arquetipos de Jung: 12 arquetipos, cómo se expresan en voz y visual

REDACCIÓN:
- origin_story: Narrativa en tercera persona, estructura problema→epifanía→acción
- mission: Verbo de acción + beneficiario + resultado transformador
- uvp: Formato "Para [quién] que [necesita], [producto] es [categoría] que [beneficio]"
- values: 3-5 sustantivos abstractos que guían decisiones
- tone_of_voice: Adjetivo + ejemplo de frase

{{ rag_examples if available }}
```

### 3.4 Flujo de Decisión (por turn)

```
RECIBE MENSAJE DEL USUARIO
    │
    ▼
SIEMPRE: invoke extract_structured
    (extrae todo lo posible, cross-sección, silencioso)
    │
    ▼
¿Hay contradicción en mapa_global? ─── SÍ ──→ invoke clarify
    │ NO                                          │
    ▼                                             ▼
¿Usuario dijo "no sé" / mostró duda? ── SÍ ──→ invoke offer_alternatives
    │ NO                                          │
    ▼                                             ▼
¿Bloque actual coverage > 80%? ──────── SÍ ──→ invoke checkpoint
    │ NO                                          │
    ▼                                             ▼
Siguiente pregunta estratégica              Espera respuesta del usuario
(1-3 oraciones, abierta, profunda)
```

### 3.5 Conversation Rules

```
CONTROL DE FLUJO:
- Mensajes restantes: {{ max_mensajes - messages_count }}
{% if messages_count >= 50 %}
- ⚠️ QUEDAN {{ max_mensajes - messages_count }} MENSAJES. Prioriza cerrar bloques pendientes. Usa checkpoint agresivamente.
{% endif %}
{% if messages_count >= 58 %}
- 🚨 ÚLTIMO MENSAJE POSIBLE. Ejecuta checkpoint del bloque actual AHORA.
{% endif %}

MAPA GLOBAL ACTUAL (no preguntar lo que ya sabes):
{{ mapa_global | tojson(indent=2) }}

BLOQUE ACTUAL: {{ bloque_actual }}
CAMPOS OBJETIVO DEL BLOQUE: {{ bloques[bloque_actual].campos_objetivo }}
CAMPOS YA LLENADOS: {{ filled_fields_for_block }}
COVERAGE: {{ coverage_percent }}%
```

### Criterios de Aceptación — Orchestrator Logic

- [ ] **AC-3.1:** El system prompt se construye dinámicamente con Jinja2. Incluye mapa_global actualizado en cada turn.
- [ ] **AC-3.2:** La IA invoca `extract_structured` en CADA turn sin excepción. Si no hay nada nuevo que extraer, pasa `extractions: []`. Puede invocar extract_structured + otro tool en el mismo turn (multi-tool-call).
- [ ] **AC-3.3:** La IA NUNCA genera texto visible cuando invoca extract_structured. El tool es silencioso.
- [ ] **AC-3.4:** Cuando el usuario responde a un AlternativesCard (click en opción), la IA extrae la selección sin pedir confirmación adicional.
- [ ] **AC-3.5:** Cuando el usuario confirma un CheckpointCard, la IA invoca `advance_block` sin texto extra.
- [ ] **AC-3.6:** Cuando el usuario dice "ajustar" en un checkpoint, la IA pregunta qué ajustar (1 pregunta) y luego re-genera checkpoint con la corrección.
- [ ] **AC-3.7:** El campo `messages_count` limita a 60. A 50 la IA prioriza cerrar. A 58 fuerza checkpoint. A 60 pausa elegante.
- [ ] **AC-3.8:** El agente NUNCA hace más de 1 pregunta por mensaje.
- [ ] **AC-3.9:** El agente NUNCA pregunta algo cuya respuesta ya está en mapa_global.
- [ ] **AC-3.10:** El agente usa `offer_alternatives` (no texto plano) cuando ofrece opciones al usuario.
- [ ] **AC-3.11:** El agente usa `clarify` SOLO para contradicciones reales, nunca para confirmar datos bien extraídos.
- [ ] **AC-3.12:** Los bloques se recorren en orden pero la extracción es cross-sección (si menciona competidores en bloque "identidad", va a positioning.competitors).

---

## 4. Frontend — Split View

### 4.1 Ruta

**Path:** `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/interview/page.tsx`

Server Component que:
1. Lee `searchParams.session` (session_id)
2. Renderiza `<InterviewSplitView sessionId={sessionId} />`

### 4.2 InterviewSplitView

**Ubicación:** `frontend/src/features/brand/components/interview/interview-split-view.tsx`

**Layout:**
```
<div className="flex h-[calc(100vh-64px)]">
  <!-- Left: Previews -->
  <div className="flex-1 flex flex-col overflow-hidden">
    <BrandStudioTabs activeTab={activeTab} onTabChange={setActiveTab} settings={previewData} />
    <div className="flex-1 overflow-y-auto p-4">
      {renderViewForTab(activeTab, previewData)}  <!-- Sin onEdit callbacks = read-only -->
    </div>
  </div>

  <!-- Right: Interview Chat -->
  <div className="w-[420px] border-l border-border flex flex-col">
    <InterviewChatPanel sessionId={sessionId} />
  </div>
</div>
```

**Datos de preview:**
- React Query key: `["interview", sessionId, "state"]`
- Endpoint: `GET /api/v1/copilot/interview/{sessionId}/state`
- Retorna: `{ mapa_global, bloque_actual, bloques_completados, config }`
- Los previews reciben `mapa_global` mergeado con `brandSettings` existentes
- Campos del mapa_global no persistidos se muestran con indicador "borrador" (borde amber)
- Campos persistidos (post-checkpoint) se muestran con highlight verde (animación 2s)

### 4.3 InterviewChatPanel

**Ubicación:** `frontend/src/features/copilot/components/interview/interview-chat-panel.tsx`

**Estructura:**
```
<div className="flex flex-col h-full">
  <!-- Header -->
  <InterviewHeader
    objetivo={config.objetivo}
    bloqueActual={session.bloque_actual}
    bloquesCompletados={session.bloques_completados}
    totalBloques={config.bloques.length}
  />

  <!-- Messages -->
  <div className="flex-1 overflow-y-auto p-4">
    {messages.map(msg => <InterviewMessage key={msg.id} message={msg} />)}
  </div>

  <!-- Input -->
  <InterviewInput onSend={handleSend} disabled={status === "thinking"} />
</div>
```

**Header:** Título "Cocreando tu Marca" + progress dots (done/current/pending por bloque).

**Input:** Text input + botón micrófono (disabled, placeholder para Fase 3) + send.

### 4.4 Preview States

| Estado | Visual | Condición |
|--------|--------|-----------|
| **Confirmado** | Borde izquierdo verde + badge "✓ confirmado" | Campo existe en BrandSettings (persistido) |
| **Borrador** | Borde izquierdo amber + badge "borrador" | Campo existe en mapa_global pero NO en BrandSettings |
| **Pendiente** | Opacidad 40% + texto "Pendiente..." | Campo no existe en ningún sitio |
| **Recién guardado** | Green glow animation (2s) | Campo acaba de ser persistido (post advance_block) |

### 4.5 Auto-scroll

Cuando el chat está en un bloque, el panel de previews auto-scrollea a la sección correspondiente:
- Bloque "identidad" → scroll a Story + Values previews
- Bloque "posicionamiento" → scroll a Differentiation + Market previews
- Bloque "narrativa" → scroll a Narrative preview
- etc.

Mapping definido en `interviewBlockToSection` config object.

### Criterios de Aceptación — Split View

- [ ] **AC-4.1:** Ruta `/[tenantId]/brand-studio/interview` existe y renderiza el split view.
- [ ] **AC-4.2:** Si no hay `?session=X` y existe sesión activa → muestra modal "¿Continuar o empezar de nuevo?"
- [ ] **AC-4.3:** Si no hay sesión activa ni query param → crea nueva sesión (POST) y redirige con `?session=newId`.
- [ ] **AC-4.4:** Panel izquierdo muestra los mismos preview components del Brand Studio sin `onEdit` callbacks (read-only puro, sin cursor pointer, sin hover edit buttons).
- [ ] **AC-4.5:** Tabs muestran health % calculado del mapa_global (no del BrandSettings) durante la entrevista.
- [ ] **AC-4.6:** Panel derecho tiene ancho fijo `w-[420px]` con chat completo.
- [ ] **AC-4.7:** Preview cards muestran los 3 estados correctamente (confirmado/borrador/pendiente) con los colores del mockup.
- [ ] **AC-4.8:** Al recibir `ui_action.preview_update`, el React Query cache se actualiza optimistamente. Los previews re-renderizan sin refetch.
- [ ] **AC-4.9:** Al recibir `ui_action.preview_update` con `persisted: true`, se dispara green glow animation (2s) en los campos afectados.
- [ ] **AC-4.10:** Auto-scroll funciona: al cambiar de bloque, el panel izquierdo scrollea suavemente a la sección correspondiente.
- [ ] **AC-4.11:** Si el usuario navega fuera (back button, sidebar click), la sesión pasa a PAUSED automáticamente.

---

## 5. Frontend — Generative UI Cards

### 5.1 AlternativesCard

**Ubicación:** `frontend/src/features/copilot/components/cards/alternatives-card.tsx`

**Props:**
```typescript
interface AlternativesCardProps {
  fieldPath: string;
  question: string;
  alternatives: Array<{
    id: string;
    title: string;
    description: string;
    recommended: boolean;
    recommendationReason?: string;
  }>;
  allowCustom: boolean;
  onSelect: (alternativeId: string) => void;
  onCustom: () => void;
  status: "pending" | "resolved";
}
```

**Visual:**
- Fondo púrpura oscuro (`bg-[#1e1b4b]`), borde púrpura (`border-purple-500`)
- Icono 💡 + título (question)
- Opciones como cards clickeables, hover con borde púrpura
- Opción recomendada: badge "✨ Recomendado — {reason}" en púrpura claro
- Selección: ring púrpura, fondo púrpura/10
- Botones: "Seleccionar" (primary) + "Otro" (ghost) si `allowCustom`
- Estado resolved: opciones no-clickeables, seleccionada con check verde

**Interacción:**
1. Usuario clickea opción → se resalta (ring visual)
2. Usuario clickea "Seleccionar" → `onSelect(id)` → envía mensaje automático al chat: `"Elegí: {title}"`
3. El agente recibe el mensaje como un HumanMessage normal → ejecuta `extract_structured` con el field_path del card y el valor seleccionado → luego continúa con siguiente pregunta (sin pedir confirmación adicional)
4. Si usuario clickea "Otro" → focus en input, usuario escribe texto libre → mismo flujo que (3)

### 5.2 ClarifyCard

**Ubicación:** `frontend/src/features/copilot/components/cards/clarify-card.tsx`

**Props:**
```typescript
interface ClarifyCardProps {
  items: Array<{
    fieldPath: string;
    issue: string;
    options: string[];
  }>;
  onResolve: (resolution: Record<string, string>) => void;
  status: "pending" | "resolved";
}
```

**Visual:**
- Fondo amber oscuro (`bg-[#422006]`), borde amber (`border-amber-500`)
- Icono ⚠️ + "Algo no cuadra"
- Cada item: issue text + botones de resolución rápida (ghost buttons)
- Max 2 items por card

**Interacción:**
1. Usuario clickea una opción de resolución → envía como mensaje al chat
2. O usuario escribe respuesta libre en el input
3. Estado resolved: card se colapsa con "✓ Aclarado"

### 5.3 CheckpointCard

**Ubicación:** `frontend/src/features/copilot/components/cards/checkpoint-card.tsx`

**Props:**
```typescript
interface CheckpointCardProps {
  blockId: string;
  blockLabel: string;
  summary: Record<string, string>;  // field_path → valor resumido
  healthScore: number;
  blocksProgress: { completed: number; total: number };
  onConfirm: () => void;
  onRevise: () => void;
  status: "pending" | "confirmed" | "revising";
}
```

**Visual:**
- Fondo púrpura oscuro (`bg-[#1e1b4b]`), borde púrpura
- Header: "✓ {blockLabel} completa" + progress dots
- Body: lista compacta `field_label: valor` (1 línea por campo, max 60 chars, truncado)
- Progress bar con health_score
- Botones: "👍 Perfecto, sigamos" (primary) + "Ajustar algo" (ghost)
- Estado confirmed: borde verde, badge "✓ Guardado"

**Interacción:**
1. "Perfecto, sigamos" → `onConfirm()` → envía mensaje especial `"[CHECKPOINT_CONFIRMED:blockId]"` → agente ejecuta `advance_block`
2. "Ajustar algo" → `onRevise()` → envía mensaje `"Quiero ajustar algo del bloque {blockLabel}"` → agente pregunta qué

### 5.4 Message Rendering

**En `InterviewMessage` component:** Switch por `ui_action.type`:
```typescript
switch (action.type) {
  case "alternatives_card": return <AlternativesCard {...} />;
  case "clarify_card": return <ClarifyCard {...} />;
  case "checkpoint_card": return <CheckpointCard {...} />;
  case "preview_update": return null;  // Silencioso — solo actualiza cache
  case "interview_complete": return <InterviewCompleteCard {...} />;
}
```

### Criterios de Aceptación — Cards

- [ ] **AC-5.1:** AlternativesCard renderiza 2-4 opciones. Exactamente 1 tiene badge "Recomendado".
- [ ] **AC-5.2:** AlternativesCard click en opción + "Seleccionar" envía mensaje automático al chat (no requiere que el usuario escriba).
- [ ] **AC-5.3:** AlternativesCard con `allowCustom: true` muestra botón "Otro" que pone focus en el input del chat.
- [ ] **AC-5.4:** ClarifyCard muestra max 2 items. Cada item tiene max 4 botones de resolución.
- [ ] **AC-5.5:** ClarifyCard click en opción envía como mensaje al chat. Card pasa a resolved.
- [ ] **AC-5.6:** CheckpointCard muestra síntesis compacta (1 línea por campo, no párrafos).
- [ ] **AC-5.7:** CheckpointCard "Perfecto, sigamos" envía mensaje especial que triggerea advance_block.
- [ ] **AC-5.8:** CheckpointCard "Ajustar algo" envía mensaje de texto que inicia conversación de corrección.
- [ ] **AC-5.9:** Cards resueltos son no-interactivos (botones disabled, opacidad reducida o badge de estado).
- [ ] **AC-5.10:** `preview_update` ui_action NO renderiza card visible — solo actualiza React Query cache.

---

## 6. Frontend — Banner Global + Session Restore

### 6.1 InterviewBanner

**Ubicación:** `frontend/src/components/shared/interview-banner.tsx`

**Montaje:** En `app/(main)/[tenantId]/(dashboard)/layout.tsx`, ANTES del children.

**Query:** `GET /api/v1/copilot/interview/active` con `staleTime: 60_000` (1 min).

**Renderiza solo si:**
- Hay sesión activa (response !== null)
- La ruta actual NO es `/brand-studio/interview`

**Visual:**
- Full-width bar, fixed top (debajo del header del dashboard)
- Background púrpura oscuro, borde púrpura
- Dot pulsante + "Entrevista {domain_label} en curso ({completed}/{total} bloques)" + botón "Continuar →"
- Click "Continuar" → navega a `/brand-studio/interview?session={id}`

### 6.2 Session Restore Modal

**Ubicación:** `frontend/src/features/brand/components/interview/session-restore-modal.tsx`

**Se muestra cuando:** Usuario llega a `/brand-studio/interview` sin `?session=` pero existe sesión activa.

**Visual:**
- Modal centrado, backdrop blur
- "Tienes una entrevista pausada (3/5 bloques completados)"
- Botones: "Continuar donde quedé" + "Empezar de nuevo"
- "Continuar" → redirige con `?session={existing_id}`
- "Empezar de nuevo" → POST nueva sesión (la anterior se marca ABANDONED) → redirige

### 6.3 Endpoint: GET /interview/active

**Ubicación:** `backend/src/modules/copilot/api/interview.py`

**Response:**
```python
class ActiveInterviewDTO(BaseModel):
    session_id: UUID
    domain: str
    domain_label: str          # "Brand Studio"
    bloque_actual: str
    bloques_completados: list[str]
    total_bloques: int
    updated_at: datetime

# Returns None (204) if no active session
```

### Criterios de Aceptación — Banner + Restore

- [ ] **AC-6.1:** Banner se muestra en CUALQUIER página del dashboard cuando hay sesión activa, excepto la propia página de interview.
- [ ] **AC-6.2:** Banner query usa `staleTime: 60_000` para no saturar el backend.
- [ ] **AC-6.3:** Click "Continuar" navega correctamente con session_id.
- [ ] **AC-6.4:** Session restore modal aparece si hay sesión activa y no hay `?session=` en URL.
- [ ] **AC-6.5:** "Empezar de nuevo" marca la sesión anterior como ABANDONED y crea nueva.
- [ ] **AC-6.6:** El endpoint `/interview/active` filtra por tenant_id y retorna solo sesiones con status ACTIVE.
- [ ] **AC-6.7:** Solo puede haber 1 sesión activa por tenant por dominio (constraint de DB).

---

## 7. Frontend — Copilot Store Extensions

### 7.1 Store Changes

**Ubicación:** `frontend/src/features/copilot/store/copilot-store.ts`

**Nuevos campos:**
```typescript
// Agregar al state
interviewMode: boolean;              // true cuando está en modo interview
interviewSessionId: string | null;   // UUID de la sesión activa
interviewPreviewData: Record<string, unknown> | null;  // mapa_global para previews

// Agregar acciones
setInterviewMode: (active: boolean, sessionId?: string) => void;
updateInterviewPreview: (delta: Record<string, unknown>) => void;
clearInterview: () => void;
```

### 7.2 UIAction Handler Extension

En el hook `useCopilotChat` (o nuevo `useInterviewChat`), agregar handling para:
- `"preview_update"` → `updateInterviewPreview(delta)` + React Query cache update
- `"alternatives_card"` → renderiza AlternativesCard
- `"clarify_card"` → renderiza ClarifyCard
- `"checkpoint_card"` → renderiza CheckpointCard
- `"interview_complete"` → `clearInterview()` + redirect

### Criterios de Aceptación — Store

- [ ] **AC-7.1:** `interviewMode: true` bloquea el copilot rail normal (click en rail navega a interview, no abre copilot).
- [ ] **AC-7.2:** `updateInterviewPreview` hace merge profundo (no reemplaza todo el objeto).
- [ ] **AC-7.3:** `clearInterview` resetea todos los campos interview a sus defaults.
- [ ] **AC-7.4:** El copilot normal (mode chat) sigue funcionando sin regresión cuando `interviewMode: false`.

---

## 8. Backend — API Endpoints

### 8.1 Nuevos Endpoints

**Ubicación:** `backend/src/modules/copilot/api/interview.py`

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/copilot/interview/start` | Crear nueva sesión |
| GET | `/api/v1/copilot/interview/active` | Obtener sesión activa (para banner) |
| GET | `/api/v1/copilot/interview/{session_id}/state` | Estado completo (mapa_global + metadata) |
| POST | `/api/v1/copilot/interview/{session_id}/message` | Enviar mensaje (SSE stream) |
| POST | `/api/v1/copilot/interview/{session_id}/pause` | Pausar sesión |
| POST | `/api/v1/copilot/interview/{session_id}/abandon` | Abandonar sesión |

### 8.2 Start Interview

**Request:**
```python
class StartInterviewRequest(BaseModel):
    domain: str = "brand"                # Dominio del interview
    resume_session_id: UUID | None = None  # Si quiere retomar una pausada
```

**Response:**
```python
class StartInterviewResponse(BaseModel):
    session_id: UUID
    conversation_id: UUID
    config: InterviewConfigDTO
    initial_message: str               # Primer mensaje de la IA
```

**Lógica:**
1. Si `resume_session_id` → cargar sesión existente, cambiar status a ACTIVE
2. Si no → crear nueva InterviewSession + nueva Conversation
3. Cargar datos_previos del modelo de dominio (BrandSettings existentes) → mapa_global inicial
4. Generar primer mensaje de bienvenida según estado (entrevista nueva vs retomada)

### 8.3 Message (SSE Stream)

Reutiliza la misma infraestructura de SSE del copilot (`stream_chat`), pero con:
- System prompt enriquecido con InterviewConfig + mapa_global
- Tool group filtrado a `["interview", "knowledge"]`
- Auto-incremento de `messages_count`

### Criterios de Aceptación — API

- [ ] **AC-8.1:** Todos los endpoints tienen `response_model=` (PII rule).
- [ ] **AC-8.2:** Todos los endpoints filtran por `tenant_id` del header `X-Tenant-ID`.
- [ ] **AC-8.3:** `POST /start` con sesión activa existente retorna 409 Conflict (solo 1 activa por domain).
- [ ] **AC-8.4:** `POST /start` con `resume_session_id` valida que la sesión pertenezca al tenant y esté en PAUSED.
- [ ] **AC-8.5:** `GET /active` retorna 204 (no 404) si no hay sesión activa.
- [ ] **AC-8.6:** `GET /{session_id}/state` retorna el mapa_global completo + metadata de la sesión.
- [ ] **AC-8.7:** `POST /{session_id}/message` usa SSE streaming con los mismos event types del copilot.
- [ ] **AC-8.8:** `POST /{session_id}/pause` cambia status a PAUSED. Solo funciona si status es ACTIVE.
- [ ] **AC-8.9:** `POST /{session_id}/abandon` cambia status a ABANDONED. Funciona desde ACTIVE o PAUSED.

---

## 9. Prompts — Templates Jinja2

### 9.1 Estructura de archivos

```
backend/src/modules/copilot/infrastructure/prompts/templates/
  interview/
    system_base.j2          # Persona + reglas universales
    brand_expertise.j2      # StoryBrand + Brand Love Key + frameworks
    offer_expertise.j2      # (futuro) Value Ladder + Offer Stack
    persona_expertise.j2    # (futuro) Jobs-to-be-Done + Empathy Map
```

### 9.2 RAG Enhancement

Cuando `InterviewConfig.rag_collection` no es null:
1. Antes de generar respuesta, buscar en Qdrant: `collection={rag_collection}`, query=último mensaje del usuario, top_k=3
2. Inyectar resultados como `{{ rag_examples }}` en el template
3. La IA usa estos ejemplos para dar recomendaciones más específicas

### 9.3 Web Search Enhancement

El tool group `"knowledge"` ya incluye `search_web`. La IA puede usarlo cuando:
- El usuario menciona una industria específica y la IA necesita benchmarks
- El usuario pregunta "¿cómo lo hacen otros?" y el RAG no tiene suficiente

### Criterios de Aceptación — Prompts

- [ ] **AC-9.1:** Templates Jinja2 existen en la ruta especificada y se renderizan sin error.
- [ ] **AC-9.2:** El system prompt incluye el mapa_global completo serializado como JSON (para que la IA no repita preguntas).
- [ ] **AC-9.3:** El system prompt incluye los campos_objetivo del bloque actual y el coverage actual.
- [ ] **AC-9.4:** Si `rag_collection` está configurado y Qdrant está disponible, se inyectan hasta 3 ejemplos relevantes.
- [ ] **AC-9.5:** Si Qdrant no está disponible, la IA funciona sin error (graceful degradation).
- [ ] **AC-9.6:** El template `brand_expertise.j2` incluye las reglas de redacción para cada campo (format de mission, UVP, etc.).
- [ ] **AC-9.7:** El system prompt NO excede 4000 tokens (comprimir mapa_global si es necesario, mostrando solo campos llenados).

---

## 10. Wizard Integration — Habilitar opción "Interview"

### 10.1 Cambios al Wizard existente

**Archivo:** `frontend/src/features/brand/components/onboarding/step-source-picker.tsx`
- Remover `isDisabled` de la opción `"interview"`
- Cambiar label de "Próximamente" a "Haciéndolo Juntos"

**Archivo:** `frontend/src/features/brand/hooks/useOnboardingWizard.ts`
- Cuando `selectedSources === ["interview"]` only → navegar a `/brand-studio/interview` (nueva sesión)
- Cuando sources incluyen website/docs + interview → después del gap-review, CTA "Completar con entrevista" navega a `/brand-studio/interview` con datos previos

### Criterios de Aceptación — Wizard

- [ ] **AC-10.1:** Opción "Haciéndolo Juntos" es clickeable (no disabled, no "Próximamente").
- [ ] **AC-10.2:** Seleccionar solo "interview" → navega directamente a interview (sin pasos intermedios).
- [ ] **AC-10.3:** Seleccionar website/docs + interview → flujo normal de extracción → gap-review → CTA navega a interview con datos previos cargados en mapa_global.
- [ ] **AC-10.4:** La entrevista post-extracción empieza con los datos ya extraídos en el mapa_global (no empieza vacía).

---

## 11. Error Handling & Edge Cases

| Escenario | Comportamiento |
|-----------|---------------|
| LLM falla mid-turn | Mapa_global ya persistido. Frontend muestra "Hubo un problema. ¿Reintentar?" con botón retry. Re-envía último mensaje. |
| SSE disconnect | Frontend detecta, muestra "Reconectando...". Al reconectar, refetch `/state`. Chat se reconstruye desde conversation history. |
| User refresh page | React Query refetch de `/state` + conversation messages. Entrevista continúa exactamente donde estaba. |
| User cierra browser | Session queda ACTIVE (no PAUSED inmediatamente). Al volver, detecta sesión activa via restore modal o banner. |
| Timeout 30min inactividad | No hay timeout automático. La sesión queda ACTIVE indefinidamente hasta que el user la pause, complete, o abandone. |
| Token de Clerk expira | El `fetchClient` ya maneja refresh de token. No afecta la entrevista. |
| Dos tabs abiertas | Constraint de DB: 1 sesión activa por tenant+domain. Segunda tab detecta sesión existente y la retoma. |
| advance_block falla (DB error) | Retry automático (1 intento). Si falla de nuevo, checkpoint card muestra "Error guardando. Intentar de nuevo." Los datos NO se pierden (están en mapa_global). |

### Criterios de Aceptación — Error Handling

- [ ] **AC-11.1:** Si el LLM falla, el mapa_global del turn anterior está seguro en DB. No se pierde progreso.
- [ ] **AC-11.2:** Retry button en caso de error re-envía el último mensaje del usuario (no crea duplicado en conversation).
- [ ] **AC-11.3:** Page refresh restaura el estado completo (messages + mapa_global + bloque actual).
- [ ] **AC-11.4:** No hay timeout automático que mate sesiones activas.
- [ ] **AC-11.5:** Constraint `unique(tenant_id, domain) WHERE status='active'` previene sesiones duplicadas.

---

## 12. Reusabilidad — Patrón para nuevos dominios

Para agregar Interview Engine a un nuevo dominio (ej: Offer), se necesita:

1. **Crear `OfferInterviewConfig`** en `copilot/domain/interview_configs/offer_config.py` con bloques y campos_objetivo
2. **Crear template** `offer_expertise.j2` con frameworks del dominio
3. **Agregar ruta** `/offer-studio/interview` + entry en `ROUTE_TOOL_MAP`
4. **Crear split view** que use los preview components del Offer Studio
5. **Configurar endpoint** de persist en `advance_block` (OfferSettings en vez de BrandSettings)

NO se necesita:
- Nuevos tools (los 5 tools son genéricos)
- Nuevo orchestrator (el mismo graph + system prompt adaptado)
- Nuevas cards (AlternativesCard, ClarifyCard, CheckpointCard son domain-agnostic)
- Nueva tabla (InterviewSession.domain diferencia)

### Criterios de Aceptación — Reusabilidad

- [ ] **AC-12.1:** Los 5 interview tools NO importan nada de `modules/brand/`. Usan interfaces genéricas.
- [ ] **AC-12.2:** `InterviewSession.domain` es un string libre (no enum hardcodeado). Nuevos dominios no requieren migración.
- [ ] **AC-12.3:** El persist en `advance_block` se resuelve via un registry de persisters: `DOMAIN_PERSISTERS = {"brand": BrandPersister, "offer": OfferPersister, ...}`.
- [ ] **AC-12.4:** Los templates Jinja2 se seleccionan por `config.expertise_template` (string → archivo).
- [ ] **AC-12.5:** El split view acepta cualquier set de preview components via prop (no hardcodea los del Brand Studio).

---

## Resumen de Archivos Nuevos (estimación)

### Backend (~15 archivos)
```
modules/copilot/
  domain/
    interview_session.py         # Entity + Status enum
    interview_config.py          # InterviewConfig + InterviewBlock VOs
    interview_configs/
      brand_config.py            # BrandInterviewConfig instance
  infrastructure/
    models/interview_session_model.py  # SQLAlchemy model
    repositories/interview_session_repo.py
    prompts/templates/interview/
      system_base.j2
      brand_expertise.j2
    persisters/
      brand_persister.py         # Writes mapa_global → BrandSettings
      persister_registry.py      # DOMAIN_PERSISTERS dict
  application/
    services/interview_service.py  # Orchestration
    tools/interview/
      __init__.py
      extract_structured.py
      clarify.py
      offer_alternatives.py
      checkpoint.py
      advance_block.py
      complete_interview.py
  api/
    interview.py                 # REST endpoints
    dto/interview_dto.py         # Request/Response DTOs
```

### Frontend (~12 archivos)
```
app/(main)/[tenantId]/(dashboard)/brand-studio/interview/
  page.tsx                       # Server component (route entry)

features/brand/components/interview/
  interview-split-view.tsx       # Main layout
  interview-header.tsx           # Header with progress dots
  session-restore-modal.tsx      # "Continue or restart?" modal

features/copilot/components/interview/
  interview-chat-panel.tsx       # Chat panel (interview mode)
  interview-message.tsx          # Message renderer with card switch
  interview-input.tsx            # Input with mic placeholder

features/copilot/components/cards/
  alternatives-card.tsx          # AlternativesCard
  clarify-card.tsx               # ClarifyCard
  checkpoint-card.tsx            # CheckpointCard
  interview-complete-card.tsx    # Completion redirect card

components/shared/
  interview-banner.tsx           # Global banner
```

### Migration (1 archivo)
```
alembic/versions/xxxx_add_interview_sessions.py  # Idempotent migration
```

---

## Visual Reference

Los mockups de todos los componentes están en:
`.superpowers/brainstorm/48751-1776031160/content/interview-full-experience.html`

Abrir con cualquier browser local para referencia visual durante implementación.
