# Brand Studio — Fases 2 y 3: Handoff para Nueva Sesión

> **Para la próxima sesión:** Lee este documento + el spec completo antes de empezar brainstorming.
> Spec: `docs/superpowers/specs/2026-04-12-brand-onboarding-interview-engine-design.md`

---

## Estado Actual (post-Fase 1)

### Lo que ya existe

**Wizard Adaptativo (Fase 1 — COMPLETO):**
- Paso 0: `StepSourcePicker` — "¿Qué tienes disponible?" (website / documentos / entrevista)
- Paso 1: `StepWebsite` — input de URL
- Paso 2: `StepDocuments` — drag & drop upload (PDF, DOCX, TXT, MD, PPTX)
- Paso 3a: `StepProcessing` — polling de progreso en tiempo real
- Paso 3b: `StepGapReview` — review de resultados con health scoring
- `OnboardingWizard` — orchestrator que conecta todo
- `useOnboardingWizard` — hook de estado con routing adaptativo (11 tests)
- `BrandStudioTabs` — tabs permanentes con health % (como Growth Studio)

**La opción "Haciéndolo Juntos" está deshabilitada** (`isDisabled = id === "interview"` en `step-source-picker.tsx`). Fase 2 la habilita.

**Infraestructura del Copilot existente:**
- Panel fijo derecho: 380px expandido, 60px rail colapsado
- SSE streaming (`POST /api/v1/copilot/chat`)
- Route-based tool selection (`ROUTE_TOOL_MAP` en `copilot/application/tools/registry.py`)
- Generative UI cards: ProposalCard, NavigationCard, ProgressChecklist, ComparisonTable, MultiOptionSelector
- Conversation persistence (DB + Redis cache 1h)
- Zustand store (`copilot-store.ts`): `isOpen`, `messages`, `status`, `selectedFields`, `currentRoute`
- Custom events: `copilot:field-update`, `copilot:collect-values`, `copilot:open-form`
- WithCopilot wrapper con highlight verde en campos actualizados

**17 preview components read-only** en `frontend/src/features/brand/sections/*/`:
- StorySection, MethodologySection, ValuesEssencePreview, DifferentiationPreview
- NarrativePreview, MarketPreview, TeamSection, TestimonialsSection
- AvatarsSection, VisualsSection, VoiceSection, AssetsPreview
- HeaderSection, FooterSection, LogoKitPreview, AuthorityPreview
- Todos reciben `data` + `onEdit` callback. Sin `onEdit` → read-only puro.

### Archivos clave a leer antes de empezar

| Archivo | Qué contiene |
|---|---|
| `frontend/src/features/brand/components/onboarding/step-source-picker.tsx` | Habilitar opción "interview" (quitar `isDisabled`) |
| `frontend/src/features/brand/hooks/useOnboardingWizard.ts` | Step routing — el step `"interview-placeholder"` debe apuntar al Interview Engine |
| `frontend/src/features/copilot/store/copilot-store.ts` | Zustand store — agregar `mode: "chat" \| "interview"` |
| `frontend/src/features/copilot/components/CopilotPanel.tsx` | Panel principal — modificar para modo entrevista |
| `frontend/src/features/copilot/components/CopilotChat.tsx` | Chat messages — agregar ClarifyCard y CheckpointCard |
| `frontend/src/features/copilot/components/CopilotRail.tsx` | Rail — bloquear en modo entrevista |
| `backend/src/modules/copilot/application/tools/registry.py` | Registrar tool group "interview" |
| `backend/src/modules/copilot/application/orchestrator/graph.py` | ReAct agent — extender para Interview mode |
| `backend/src/modules/copilot/application/orchestrator/state.py` | State — agregar interview session fields |
| `backend/src/modules/copilot/api/dto.py` | DTOs — agregar interview request/response types |

---

## Fase 2: Interview Engine (Chat)

### Objetivo
Motor de entrevista IA reutilizable que conduce conversaciones semi-estructuradas por bloques temáticos, extrae datos estructurados, y los persiste en el modelo de dominio.

### Decisiones de diseño YA TOMADAS (no re-brainstormear)

1. **Chat híbrido** (texto + voz opcional) — voz es Fase 3
2. **Semi-estructurada con mapa global** — bloques temáticos pero info se captura en la sección correcta sin importar el bloque
3. **Nunca repite** — si el usuario mencionó competencia al hablar de historia, no re-pregunta en posicionamiento
4. **Copilot en modo exclusivo** — misma infraestructura, tool group restringido, panel más ancho
5. **Takeover split view** — previews reales read-only (izq) + chat (der)
6. **Previews sin edición** — Nicolify es el experto, la IA redacta con best practices
7. **Checkpoints** — resumen al terminar bloque, usuario confirma o corrige
8. **Clarify cards** — datos inferidos/ambiguos presentados como cards amarillos
9. **Redacción experta** — la IA no copia literal, redacta con StoryBrand, Brand Love Key, etc.
10. **Tabs con auto-scroll** — panel izquierdo auto-navega a la sección activa

### Temas pendientes de brainstorming para Fase 2

Estos temas NO se definieron en detalle y necesitan diseño:

1. **Prompts del InterviewOrchestrator** — ¿Qué system prompt recibe la IA? ¿Cómo sabe de StoryBrand/Brand Love Key? ¿Usa las mismas templates Jinja2 de extracción o nuevas?
2. **Tool schemas** — Definir exactamente los inputs/outputs de cada tool: `extract_structured`, `checkpoint`, `advance_block`, `clarify`, `complete_interview`
3. **InterviewSession persistence** — ¿Tabla nueva? ¿JSONB en tenant config? ¿Extiende Copilot conversation? Definir modelo de datos exacto.
4. **Mapa global implementation** — ¿Cómo se implementa? ¿Dict en session? ¿Se mergea con BrandSettings en cada turn? ¿Al final de cada bloque? ¿Solo al completar?
5. **Preview update mechanism** — ¿Cómo se actualizan los previews en vivo? ¿custom event desde el chat? ¿React Query invalidation? ¿Optimistic update?
6. **Split view layout** — ¿Nuevo route/page? ¿Overlay sobre el Brand Studio? ¿Cómo se maneja responsive/mobile?
7. **Banner sticky** — ¿Componente global en el dashboard layout? ¿Estado en Zustand? ¿En context?
8. **Session restoration UX** — ¿Cómo se ve "Tienes una entrevista pausada"? ¿Dónde aparece? ¿Modal? ¿Banner?
9. **Error handling** — ¿Qué pasa si el LLM falla mid-interview? ¿Retry? ¿Partial save?
10. **Max message limit** — Spec dice 60, ¿es suficiente? ¿Qué pasa si se llega al límite?

### Componentes nuevos necesarios (estimación)

**Backend (DDD en `modules/copilot/` o nuevo `modules/interview/`):**
- `InterviewConfig` — domain value object
- `InterviewBlock` — domain value object
- `InterviewSession` — domain entity + infra model
- `InterviewOrchestrator` — application service (extiende ReAct)
- 5 interview tools — application/tools/
- Prompts Jinja2 — infrastructure/prompts/templates/
- API endpoints — api/interview.py (o extend copilot/api/)

**Frontend:**
- `InterviewSplitView` — layout component
- `ClarifyCard` — generative UI
- `CheckpointCard` — generative UI
- `InterviewBanner` — global component
- Copilot store extensions — mode, sessionId
- CopilotPanel interview mode — UI changes

### Estimación de complejidad
- **Backend:** ALTO — nuevo orchestrator con tools, session persistence, prompt engineering
- **Frontend:** MEDIO — reutiliza mucho del copilot, pero split view y mode switching son nuevos
- **Total:** ~15-25 tasks en el plan

---

## Fase 3: Voz Opcional + Segundo Caso

### Objetivo
Agregar input por voz al Interview Engine y reutilizarlo para crear Buyer Personas.

### Temas para brainstorming

1. **STT provider** — ¿Web Speech API del browser? ¿Whisper API? ¿Deepgram? Trade-offs de costo/calidad/latencia
2. **TTS** — ¿La IA responde con voz? ¿Opcional? ¿Qué voz? ¿Eleven Labs? ¿Browser TTS?
3. **UX del micrófono** — ¿Push-to-talk? ¿Voice activity detection? ¿Cómo se ve grabando?
4. **Buyer Persona InterviewConfig** — ¿Qué bloques? ¿Qué output_schema? ¿Dónde se integra?
5. **Buyer Persona previews** — ¿Existen? ¿Se crean nuevos? (El `AvatarsSection` ya existe pero es básico)
6. **Reutilización real** — ¿El InterviewSplitView acepta cualquier preview component? ¿Cómo se configura?

### Estimación
- **Voz:** MEDIO — STT es el core, TTS es nice-to-have
- **Buyer Personas:** BAJO-MEDIO — el engine ya existe, solo config + prompts + previews
- **Total:** ~8-12 tasks

---

## Aprendizajes de Fase 1 (aplicar en Fases 2-3)

### Proceso
1. **Subagent-driven development funcionó bien** — 4 agentes en paralelo para componentes independientes, reviews asíncronos
2. **Tasks 4-7 (componentes UI simples) no necesitaron spec review** — el overhead no valió para "crea este archivo con este código exacto"
3. **La exploración profunda al inicio ahorró tiempo** — conocer los 17 previews, el copilot store, el route-based tool selection antes de diseñar evitó refactors
4. **El visual companion fue clave** — Chris tomó mejores decisiones viendo mockups que leyendo descripciones

### Arquitectura
1. **Reutilizar > crear** — el 80% de la infra de Fase 1 ya existía (SmartFill, FileParsingService, Redis polling, health validators)
2. **Los previews son stateless** — reciben data + onEdit, fácil de renderizar sin onEdit para read-only
3. **El copilot ya tiene mode system** — route-based tool selection es extensible, solo registrar nuevo tool group
4. **Clerk token refresh** — los tokens expiran en ~60s, cualquier polling largo necesita re-fetch token en cada iteración

### Código
1. **Tildes en español** — verificar siempre, el agente corrigió "Publico" → "Público" automáticamente
2. **Tests natively** — NUNCA docker exec, siempre `cd frontend && npx vitest run`
3. **Stage por nombre** — NUNCA `git add .`, múltiples agentes pueden tener WIP en el working tree
4. **`useMemo` para health** — los cálculos de health scoring se hacen en cada render si no se memoizan
