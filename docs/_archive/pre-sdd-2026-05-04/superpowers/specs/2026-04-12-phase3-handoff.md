# Brand Studio — Resumen Fases 1-2 + Gap para Fase 3

> **Para brainstorming de Fase 3:** Lee este documento completo. Contiene el estado actual, lo que ya existe, y las 6 preguntas abiertas de diseño.

---

## Estado Actual: Fase 1 + Fase 2 COMPLETAS

### Fase 1 — Wizard Adaptativo + Docs + Tabs (11 commits, 877 unit + 32 E2E)

**Lo que construimos:**
- `StepSourcePicker` — "¿Qué tienes disponible?" (website / documentos / entrevista)
- `StepWebsite` — Input de URL con validación
- `StepDocuments` — Drag & drop upload (PDF, DOCX, TXT, MD, PPTX)
- `StepProcessing` — Polling de progreso en tiempo real (Redis)
- `StepGapReview` — Review de resultados con health scoring por sección
- `OnboardingWizard` — Orchestrator que conecta todo
- `useOnboardingWizard` — Hook de estado con routing adaptativo
- `BrandStudioTabs` — Tabs permanentes con health % (Esencia / Estrategia / Público / Identidad Creativa)
- 17 preview components read-only en `brand/sections/*/`

### Fase 2 — Interview Engine Chat (15 commits, 2168 backend + 898 frontend tests)

**Backend:**

| Componente | Archivo | Qué hace |
|---|---|---|
| `InterviewSession` entity | `copilot/domain/interview_session.py` | Entidad con lifecycle (create/pause/resume/abandon/advance_block) |
| `InterviewConfig` VO | `copilot/domain/interview_config.py` | Config inmutable (bloques, campos_objetivo, expertise_template) |
| `BrandInterviewConfig` | `copilot/domain/interview_configs/brand_config.py` | 5 bloques: identidad, posicionamiento, narrativa, público, identidad_creativa |
| `InterviewSessionModel` | `copilot/infrastructure/models/interview_session_model.py` | SQLAlchemy + JSONB (mapa_global, config_snapshot) |
| `InterviewSessionRepository` | `copilot/infrastructure/repositories/interview_session_repository.py` | CRUD con tenant isolation, soft delete |
| `BrandPersister` | `copilot/infrastructure/persisters/brand_persister.py` | Escribe mapa_global → BrandSettings (dot notation → nested dict) |
| `persister_registry` | `copilot/infrastructure/persisters/persister_registry.py` | `get_persister("brand", db)` — extensible para nuevos dominios |
| 6 Interview tools | `copilot/application/tools/interview/*.py` | extract_structured, offer_alternatives, clarify, checkpoint, advance_block, complete_interview |
| Tool group registry | `copilot/application/tools/registry.py` | `"interview"` group en `ROUTE_TOOL_MAP["brand-studio/interview"]` |
| `InterviewService` | `copilot/application/services/interview_service.py` | Orchestration (start/pause/resume/abandon/get_active/get_state) |
| API endpoints | `copilot/api/interview.py` | 5 endpoints REST (start, active, state, pause, abandon) |
| DTOs | `copilot/api/interview_dto.py` | Pydantic v2 request/response models |
| System prompt | `copilot/infrastructure/prompts/templates/interview/system_base.j2` | Persona consultor + reglas + mapa_global dinámico |
| Brand expertise | `copilot/infrastructure/prompts/templates/interview/brand_expertise.j2` | StoryBrand + Brand Love Key + Arquetipos + reglas de redacción |
| Migration | `alembic/versions/3dbcf9737aa6_add_interview_sessions.py` | Tabla idempotente con unique(tenant_id, domain) WHERE active |

**Frontend:**

| Componente | Archivo | Qué hace |
|---|---|---|
| Store extensions | `copilot/store/copilot-store.ts` | `interviewMode`, `interviewSessionId`, `interviewPreviewData` + actions |
| API client | `copilot/api/interview-api.ts` | 5 funciones typed (start, active, state, pause, abandon) |
| `AlternativesCard` | `copilot/components/cards/alternatives-card.tsx` | 2-4 opciones con recomendación, selección clickeable |
| `ClarifyCard` | `copilot/components/cards/clarify-card.tsx` | Contradicciones/ambigüedades con resolución rápida |
| `CheckpointCard` | `copilot/components/cards/checkpoint-card.tsx` | Resumen de bloque + confirm/revise |
| `InterviewCompleteCard` | `copilot/components/cards/interview-complete-card.tsx` | Health score + redirect |
| `useInterviewChat` | `copilot/hooks/useInterviewChat.ts` | SSE streaming + card action handling + store updates |
| `InterviewChatPanel` | `copilot/components/interview/interview-chat-panel.tsx` | Panel de chat (derecha del split view) |
| `InterviewMessage` | `copilot/components/interview/interview-message.tsx` | Renderiza mensajes + switch de cards |
| `InterviewInput` | `copilot/components/interview/interview-input.tsx` | Input + mic (disabled) + send |
| `InterviewSplitView` | `brand/components/interview/interview-split-view.tsx` | Layout principal: previews (izq) + chat (der) |
| `InterviewHeader` | `brand/components/interview/interview-header.tsx` | Título + progress dots por bloque |
| `SessionRestoreModal` | `brand/components/interview/session-restore-modal.tsx` | "¿Continuar o empezar de nuevo?" |
| Page route | `app/.../brand-studio/interview/page.tsx` | Server Component (entry point) |
| `InterviewBanner` | `components/shared/interview-banner.tsx` | Banner global "entrevista en curso" |

**Lógica del agente IA (system prompt):**
- Consultor senior, NO encuestador
- 1 pregunta por mensaje, abierta, estratégica
- `extract_structured` SIEMPRE (silencioso, cross-sección)
- `offer_alternatives` cuando el usuario duda (con recomendación)
- `clarify` SOLO para contradicciones reales
- `checkpoint` cuando coverage > 80% del bloque
- Nunca repite lo que ya está en mapa_global
- Redacta con frameworks (StoryBrand, Brand Love Key, arquetipos)
- Límite 60 mensajes (warning a 50, fuerza checkpoint a 58)

---

## Qué falta para Fase 3

### 3A. Voz Opcional (STT + TTS)

**Lo que ya existe:**
- `InterviewInput` tiene un botón de micrófono deshabilitado (`title="Disponible en Fase 3"`)
- El hook `useInterviewChat.sendMessage(text)` acepta texto — una vez transcrito, el flujo es idéntico
- El SSE streaming ya retorna `text_chunk` — convertirlo a audio es un layer encima

**Lo que falta construir:**
1. **Speech-to-Text (STT)** — Capturar audio del mic, transcribir, enviar como texto
2. **Text-to-Speech (TTS)** — Opcional: leer la respuesta de la IA en voz
3. **UX del micrófono** — Estados: idle, recording, transcribing, error
4. **Infra de audio** — ¿Client-side (Web Speech API) o server-side (Whisper/Deepgram)?

**Preguntas abiertas:**

| # | Pregunta | Opciones | Trade-offs |
|---|----------|----------|------------|
| 1 | **¿STT client o server?** | A) Web Speech API (browser) / B) Whisper API (OpenAI) / C) Deepgram (real-time) | A: gratis, OK calidad, no todos los browsers / B: mejor calidad, ~$0.006/min, requiere upload / C: real-time streaming, ~$0.005/min |
| 2 | **¿TTS sí o no?** | A) Solo STT (la IA escribe) / B) STT + TTS (conversación por voz) / C) TTS opcional (toggle) | A: más simple / B: experiencia más inmersiva pero más caro / C: balance |
| 3 | **¿UX del micrófono?** | A) Push-to-talk (hold button) / B) VAD (voice activity detection) / C) Toggle (click start, click stop) | A: más control / B: más natural pero puede captar ruido / C: simple |

### 3B. Buyer Persona Interview (Segundo caso del engine)

**Lo que ya existe:**
- `InterviewConfig` es domain-agnostic (cualquier `domain`, `bloques`, `output_schema_path`)
- `persister_registry.py` con patrón extensible (`get_persister(domain, db)`)
- `InterviewSplitView` acepta previews del Brand Studio — necesita generalizarse
- `AvatarsSection` en brand/sections/ muestra buyer personas básicos
- El tool group `"interview"` es genérico (mismos 6 tools para cualquier dominio)

**Lo que falta construir:**
1. **`BuyerPersonaInterviewConfig`** — Definir bloques temáticos (demografía, pain points, desires, objections, channels, journey)
2. **`BuyerPersonaPersister`** — Escribe mapa_global al modelo de Buyer Persona (¿dónde vive? ¿BrandSettings.avatars? ¿tabla propia?)
3. **Buyer Persona expertise template** — Jinja2 con frameworks: Jobs-to-be-Done, Empathy Map
4. **Buyer Persona previews** — Componentes que muestren la persona en construcción (¿AvatarsSection extendido? ¿Nuevos componentes?)
5. **`InterviewSplitView` generalizado** — Actualmente hardcodea las views del Brand Studio. Debe aceptar cualquier set de previews via config.
6. **Ruta** — `/brand-studio/interview?domain=buyer_persona` o ruta separada `/brand-studio/buyer-personas/interview`

**Preguntas abiertas:**

| # | Pregunta | Contexto |
|---|----------|----------|
| 4 | **¿Dónde vive el Buyer Persona?** | ¿Es parte de BrandSettings.avatars (ya existe)? ¿Tabla nueva? ¿Modelo propio en brand/ o nuevo módulo? |
| 5 | **¿Qué previews muestra el split view?** | ¿AvatarsSection actual es suficiente? ¿O se crea un PersonaDetailView más rico (demographics, journey map, pain/desire cards)? |
| 6 | **¿Cómo se generaliza el split view?** | Opción: InterviewConfig incluye un campo `preview_component` que dice qué componente renderizar. O: una ruta por dominio con su propio split view. |

---

## Estimación de Esfuerzo

| Componente | Complejidad | Tasks estimados |
|---|---|---|
| STT integration | MEDIO | 3-4 (provider, hook, UX states, tests) |
| TTS integration (si aplica) | BAJO-MEDIO | 2-3 (provider, toggle, playback) |
| BuyerPersonaInterviewConfig | BAJO | 1 (dataclass + tests) |
| BuyerPersonaPersister | BAJO | 1 (similar a BrandPersister) |
| Buyer Persona expertise template | BAJO | 1 (Jinja2) |
| Buyer Persona previews | MEDIO | 2-3 (componentes nuevos o extensiones) |
| Split view generalización | BAJO-MEDIO | 1-2 (abstracción del component mapping) |
| Ruta + integración | BAJO | 1 |
| **Total** | | **~8-12 tasks** |

---

## Aprendizajes de Fases 1-2 para aplicar en Fase 3

### Proceso
1. **Subagent-driven development funciona** — Tasks 4+5 y 8+9 corrieron en paralelo sin conflictos
2. **El visual companion acelera decisiones** — Las preguntas de layout (split view, cards) se resolvieron rápido con mockups
3. **Spec reviews no fueron necesarios para tasks mecánicos** — Los tools son funciones puras, el plan tenía el código exacto
4. **La exploración profunda al inicio pagó dividendos** — Conocer el copilot store, el route-based tool selection, y los 17 previews antes de diseñar evitó refactors

### Arquitectura
1. **El patrón `persister_registry` es el punto de extensión** — Para Buyer Personas solo se agrega un persister + config
2. **Los 6 tools son 100% genéricos** — No importan nada de brand/. Funcionan para cualquier dominio.
3. **El split view está acoplado a Brand** — Hardcodea EsenciaView, EstrategiaView, etc. Esto es el gap principal para reutilización.
4. **El InterviewInput ya tiene el placeholder del mic** — Solo hay que habilitarlo e inyectar el transcribed text.
