# Brand Studio Onboarding + Interview Engine

**Fecha:** 2026-04-12
**Scope:** Rediseño del onboarding de Brand Studio con wizard adaptativo, upload de documentos mejorado, y un motor de entrevista IA reutilizable.
**Implementación faseada:** 3 fases (wizard+docs+tabs → interview engine chat → voz opcional)

---

## 1. Problema

El onboarding actual del Brand Studio ofrece dos caminos rígidos: extracción desde website o configuración manual. Los usuarios que no tienen website (o cuyo sitio está incompleto) no tienen una buena opción. Además, la extracción desde documentos existe pero está escondida en un tab del SmartFillDialog, y no hay forma de que la IA "entreviste" al usuario para llenar los gaps que quedan después de la extracción automática.

## 2. Solución

### 2.1 Wizard Guiado Adaptativo

Reemplaza el `BrandEmptyState` actual con un wizard que adapta sus pasos según lo que el usuario tiene disponible.

**Paso 0 — "¿Qué tienes disponible?"**

Pantalla inicial con 3 opciones seleccionables (multi-select):
- ☐ Tengo un website
- ☐ Tengo documentos (PDF, DOCX, presentaciones)
- ☐ Prefiero que me entrevisten (Haciéndolo juntos)

Routing condicional:
- Website y/o docs seleccionados → pasos 1-2 (según selección) → paso 3 (review) → paso 4 (entrevista para gaps)
- Solo entrevista → directo a paso 4 (entrevista completa)
- Nada seleccionado → configuración manual (dismiss empty state, como hoy)

**Paso 1 — Website (condicional)**

Input de URL. Reutiliza el flujo existente del SmartFill:
- `BrandCrawler.crawl_content(url)` para scraping
- `BrandExtractionService.extract_all()` para extracción LLM por secciones
- `ExtractionOrchestrator` con progreso via Redis
- Sin cambios en el backend — solo nueva UX de wizard en vez del tab de SmartFillDialog

**Paso 2 — Documentos (condicional)**

Upload zone con drag & drop. Reutiliza `FileParsingService` (PDF, DOCX, TXT/MD).
- Archivos se parsean y concatenan como contenido adicional
- Se combinan con datos del paso 1 si ambos están seleccionados
- Misma extracción LLM por secciones que el paso 1
- El backend ya soporta `files` en el endpoint `POST /api/v1/brand/extract-full-brand`

**Paso 3 — Procesamiento + Review de Gaps**

Progreso en tiempo real (Redis polling existente). Al terminar:
- Muestra el Brand Studio con tabs + previews read-only
- Health scoring muestra qué se llenó (verde), qué está parcial (amarillo), qué falta (gris)
- Campos inferidos marcados con indicador ⚠️ "(inferido)"
- CTA prominente: "Completemos lo que falta con una entrevista" → paso 4

**Paso 4 — Entrevista IA (Interview Engine)**

Split View takeover: previews reales del Brand Studio (izquierda) + Copilot en modo entrevista (derecha).
- Si viene de pasos 1-3 → modo clarificación: primero resuelve ambigüedades/inferencias, luego llena gaps
- Si viene directo (sin web/docs) → entrevista completa por bloques temáticos

### 2.2 Interview Engine (Componente Reutilizable)

Motor agnóstico al dominio que conduce entrevistas semi-estructuradas. Diseñado para Brand Studio como primer caso, pero reutilizable para Buyer Personas, Offer Ladder, Sales Agent personality, etc.

#### Backend

**InterviewConfig** (dataclass inmutable):
```
objetivo: str                          # "Completar Brand Studio"
bloques: list[InterviewBlock]          # Bloques temáticos ordenados
output_schema: type[BaseModel]         # Pydantic model del resultado (BrandSettings, BuyerPersona, etc.)
datos_previos: dict | None             # Datos ya extraídos (de web/docs/DB)
gaps: list[GapItem] | None             # Campos vacíos o inferidos
tono: str                              # "amigable, guía experta"
max_mensajes: int = 60                 # Límite de seguridad
```

**InterviewBlock** (dataclass):
```
id: str                                # "identidad", "posicionamiento", etc.
label: str                             # Display name
campos_objetivo: list[str]             # Campos del output_schema que este bloque busca llenar
prompt_context: str                    # Instrucciones específicas para la IA sobre este bloque
```

**InterviewSession** (modelo persistido):
```
id: UUID
tenant_id: UUID
config_snapshot: dict                  # InterviewConfig serializado
conversation_id: UUID                  # FK a Copilot conversation
mapa_global: dict                      # Todo lo capturado hasta ahora, por campo
bloque_actual: str                     # ID del bloque en progreso
bloques_completados: list[str]
status: "active" | "paused" | "completed" | "abandoned"
created_at: datetime
updated_at: datetime
```

**InterviewOrchestrator**:
- Extiende el ReAct loop del Copilot con un tool group "interview" que incluye:
  - `extract_structured`: Extrae datos estructurados de la última respuesta del usuario y los escribe al mapa_global
  - `checkpoint`: Genera resumen del bloque actual para confirmación del usuario
  - `advance_block`: Marca bloque como completado y avanza al siguiente
  - `clarify`: Presenta datos inferidos/ambiguos como clarify card
  - `complete_interview`: Persiste el mapa_global al modelo de dominio (BrandSettings, etc.)
- **Mapa global**: toda info capturada se registra en la sección correcta del output_schema, sin importar en qué bloque esté la conversación. Si el usuario menciona competidores al hablar de historia, va a posicionamiento.
- **Nunca repite**: antes de preguntar, verifica si el mapa_global ya tiene esa info.
- **Redacción experta**: la IA no guarda lo que el usuario dice literalmente — lo redacta siguiendo best practices de cada sección (StoryBrand, Brand Love Key, methodology frameworks, etc.)

**Reutilización del Copilot**:
- SSE streaming: sin cambios
- Conversation persistence: sin cambios
- Route-based tool selection: nuevo tool group `"interview"` registrado en `ROUTE_TOOL_MAP`
- System prompt: enriquecido con `InterviewConfig` cuando `mode == "interview"`

#### Frontend

**CopilotPanel — modo "interview"**:
- Store: nuevo campo `mode: "chat" | "interview"` + `interviewSessionId: string | null`
- Cuando `mode === "interview"`:
  - Panel se expande (de 380px a ~480px o lo que el split view necesite)
  - Header muestra "Entrevista — {objetivo}" con progress chips por bloque
  - Rail desaparece (el panel es el copilot)
  - Input incluye botón de micrófono (deshabilitado en Fase 1-2, funcional en Fase 3)
  - Footer muestra "🔒 Modo Entrevista"
  - Suggested actions y context chips ocultos

**InterviewSplitView** (nuevo componente):
- Layout: flex row, izquierda `flex-1` (previews) + derecha `w-[480px]` (copilot interview)
- Panel izquierdo:
  - Tab bar con las 4 vistas del Brand Studio + health % por vista
  - Previews reales (los 17 componentes existentes) renderizados SIN `onEdit` callback → read-only puro, sin cursor pointer, sin hover edit buttons
  - Auto-scroll a la sección correspondiente al bloque activo de la entrevista
  - Campos recién llenados con highlight verde (animación existente de WithCopilot adaptada)
  - Campos inferidos/ambiguos con indicador ⚠️
- Transición entrada: el Brand Studio "se abre" en split view con animación
- Transición salida: al completar, split view se cierra y queda el Brand Studio normal con todos los previews llenos

**Clarify Card** (nuevo tipo de generative UI):
- Se renderiza inline en el chat como un card amarillo
- Muestra los datos inferidos/ambiguos con contexto de dónde se extrajeron
- Preguntas numeradas para que el usuario responda
- Botones: "✓ Correcto" / "✏️ Corregir"

**Checkpoint Card** (nuevo tipo de generative UI):
- Se renderiza al terminar un bloque temático
- Muestra resumen de lo capturado en formato legible
- Botones: "✓ Correcto, siguiente" / "✏️ Quiero corregir algo"

### 2.3 Brand Studio Tabs Permanentes

Cambio permanente a la navegación del Brand Studio:
- Tab bar horizontal arriba del contenido (debajo del header de Brand Studio)
- 4 tabs: Esencia | Estrategia | Público | Identidad Creativa
- Cada tab muestra health % con color (verde/amarillo/gris)
- Coexiste con el sidebar — ambas formas de navegar funcionan
- El nav rail interno de cada vista se mantiene sin cambios
- Patrón visual: igual que Growth Studio (MetaAdsDashboard tabs)

### 2.4 Contención y Persistencia

**Escenario: usuario navega a otra página durante entrevista**
- Banner sticky global en la parte superior de cualquier página
- Contenido: "Entrevista Brand Studio en curso (X/Y bloques) — [Continuar]"
- El banner persiste mientras `interviewSession.status === "active"`
- Click en "Continuar" regresa al split view exactamente donde estaba

**Escenario: usuario intenta abrir Copilot normal**
- Mientras la entrevista está activa, el Copilot rail muestra estado diferente: ícono de entrevista pulsando
- Click en el rail reabre el split view de entrevista, no el copilot general
- El copilot normal se suspende hasta que la entrevista termine o se pause

**Escenario: usuario cierra el browser y vuelve después**
- `InterviewSession` persistida en DB con toda la conversación y mapa_global
- Al volver al Brand Studio, detecta sesión activa:
  - "Tienes una entrevista pausada (X/Y bloques completados). ¿Continuar o empezar de nuevo?"
- La IA retoma con resumen: "La última vez hablamos de X. Nos falta Y. ¿Seguimos?"

**Escenario: entrevista completada**
- Split view se cierra con animación
- Brand Studio queda con todos los previews llenos
- Copilot vuelve a modo "chat" normal
- Tabs permanecen
- `InterviewSession.status` → `"completed"`

## 3. Fases de Implementación

### Fase 1: Wizard + Documentos + Tabs
- Nuevo Empty State (paso 0 del wizard con routing adaptativo)
- Pasos 1-2 del wizard (website + documentos) reutilizando backend existente
- Paso 3 (review de gaps con previews + health scoring)
- Tabs permanentes en Brand Studio
- Sin entrevista IA — el paso 4 muestra "Próximamente" o dirige a configuración manual

### Fase 2: Interview Engine (Chat)
- `InterviewConfig`, `InterviewSession`, `InterviewBlock` (backend domain)
- `InterviewOrchestrator` con tools: extract_structured, checkpoint, advance_block, clarify, complete_interview
- Copilot modo "interview" (frontend store + UI)
- `InterviewSplitView` con previews reales read-only
- Clarify cards + checkpoint cards (generative UI)
- Contención: banner sticky, rail bloqueado, sesión pausable/restaurable
- Primer caso: Brand Studio

### Fase 3: Voz Opcional + Segundo Caso
- Speech-to-Text para input por micrófono (API del browser o servicio externo)
- Botón de micrófono funcional en el chat
- TTS opcional para respuestas de la IA
- Segundo caso de uso del Interview Engine: Buyer Personas

## 4. Infraestructura Reutilizada (no duplicar)

| Componente | Archivo | Se usa en |
|---|---|---|
| Copilot SSE streaming | `copilot/api/chat.py` | Interview chat |
| Copilot store (Zustand) | `copilot/store/copilot-store.ts` | Interview mode flag |
| Copilot message rendering | `copilot/components/CopilotChat.tsx` | Interview messages |
| Route-based tool selection | `copilot/application/tools/registry.py` | New "interview" group |
| Conversation persistence | `copilot/infrastructure/models/` | Interview conversations |
| BrandExtractionService | `brand/application/extraction_service.py` | Wizard pasos 1-2 |
| ExtractionOrchestrator | `brand/application/extraction_orchestrator.py` | Wizard pasos 1-2 |
| FileParsingService | `shared/infrastructure/files/` | Wizard paso 2 |
| Redis progress tracking | `brand/workers/tasks.py` | Wizard paso 3 |
| 17 preview components | `brand/sections/*/` | Split view izquierdo |
| Health scoring + validators | `brand/utils/brand-validation.ts` | Tabs + review |
| BrandSectionShell | `brand/components/layout/` | Tab bar container |
| Generative UI cards | `copilot/components/` | Clarify + checkpoint cards |

## 5. Componentes Nuevos

| Componente | Layer | Descripción |
|---|---|---|
| `InterviewConfig` | Backend domain | Configuración inmutable de una entrevista |
| `InterviewBlock` | Backend domain | Bloque temático con campos objetivo |
| `InterviewSession` | Backend domain + infra | Sesión persistida con mapa global |
| `InterviewOrchestrator` | Backend application | ReAct loop con tools de entrevista |
| Interview tools | Backend application | extract_structured, checkpoint, advance_block, clarify, complete_interview |
| `InterviewSplitView` | Frontend component | Layout split previews + copilot |
| Copilot interview mode | Frontend store + UI | mode flag, wider panel, progress chips |
| `ClarifyCard` | Frontend generative UI | Card amarillo para datos ambiguos |
| `CheckpointCard` | Frontend generative UI | Resumen de bloque con confirmación |
| `InterviewBanner` | Frontend global component | Banner sticky "entrevista en curso" |
| `BrandStudioTabs` | Frontend component | Tab bar permanente con health % |
| Wizard steps | Frontend components | Paso 0, paso 1, paso 2, paso 3 |

## 6. Reutilización Futura del Interview Engine

El Interview Engine se diseña agnóstico al dominio. Para usarlo en otro contexto:

1. Crear un `InterviewConfig` con bloques, output_schema, y prompt_context específicos
2. Proveer los preview components para el split view (o usar sin split view)
3. Registrar en el route map del copilot

**Próximos casos planificados:**
- Buyer Persona creation (Fase 3)
- Offer Ladder Builder
- Sales Agent personality configuration

## 7. Decisiones de Diseño

| Decisión | Alternativas consideradas | Razón de la elección |
|---|---|---|
| Wizard adaptativo (no lineal fijo) | Lineal con skip, Hub central | Se adapta al usuario sin abrumarlo |
| Chat híbrido (texto + voz opcional) | Solo chat, Solo voz | Implementación incremental, accesible |
| Semi-estructurada con mapa global | Guión rígido, Conversación libre | Balance entre estructura y naturalidad |
| Copilot en modo exclusivo | Modal separado, Expandir in-place | Reutiliza 100% la infra, inmersivo |
| Takeover split view | Panel expandido, Modal grande | Ve los previews llenándose en real-time |
| Previews read-only (sin onEdit) | Formularios editables, Preview nuevo | Cero duplicación, sin distracciones |
| Tabs permanentes | Solo en entrevista, Sin tabs | Mejora la navegación general del Brand Studio |
| IA redacta (no copia literal) | Guardar textual | Nicolify es el experto en marketing/branding |
