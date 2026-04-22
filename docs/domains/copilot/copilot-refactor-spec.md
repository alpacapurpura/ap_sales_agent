# Copilot Refactor Spec

Versión inicial del refactor copilot. Cubre: model router, context window, UI sidebar,
decisión Interview/Focus, data model conversaciones. Actualizar a medida que se implementa.

**Estado:** diseño aprobado, pendiente implementación.
**Fecha:** 2026-04-21.
**Owner:** chris.
**Scope:** `backend/src/modules/copilot/*`, `frontend/src/features/copilot/*`.

---

## 1. Model Router (4 tiers)

Lineup oficial OpenAI abril 2026. Tiers ordenados por costo ascendente.

### Tabla maestra

| Tier | Modelo API | Input ($/1M) | Output ($/1M) | Cached Input ($/1M) | Ventana | Razonamiento | Fuente OpenAI |
|---|---|---|---|---|---|---|---|
| `NANO` | `gpt-5.4-nano` | 0.20 | 1.25 | 0.02 | 1M | no | [docs](https://openai.com/index/introducing-gpt-5-4-mini-and-nano/) |
| `MINI` | `gpt-5.4-mini` | 0.75 | 4.50 | 0.075 | 1M | no | [docs](https://openai.com/index/introducing-gpt-5-4-mini-and-nano/) |
| `REASONING` | `o4-mini` | 1.10 | 4.40 | — | 200K | sí (light) | [docs](https://platform.openai.com/docs/models/o4-mini) |
| `HEAVY` | `o3` | 2.00 | 8.00 | — | 200K | sí (deep) | [docs](https://developers.openai.com/api/docs/models/o3) |

**Descartado flagship `gpt-5.4` ($2.50/$15)** — mismo tier de precio que `o3` pero sin razonamiento. Agregar solo si aparece caso genuino que necesite calidad flagship sin multi-step reasoning.

### Cuándo usar cada tier — matriz decisión

Router evalúa en orden (primer match gana):

| Condición | Tier | Justificación OpenAI |
|---|---|---|
| Llamada interna: clasificar intent del user msg | `NANO` | "classification" |
| Llamada interna: generar título conversación (post msg 2) | `NANO` | "simple summarization" |
| Llamada interna: rolling summary de msg desplazado | `NANO` | "simple summarization" |
| Llamada interna: extraer estructura de web scrape | `NANO` | "data extraction, structured output" |
| Llamada user: field-fill simple (`propose_field_updates` ≤1 campo sin reasoning) | `NANO` | "tagging" |
| Llamada user: mensaje <40 chars sin tools | `NANO` | Bajo riesgo, alta latencia penalty |
| Llamada user: chat default con ≤2 tool calls | `MINI` | "best balance speed/accuracy, 2x faster" |
| Llamada user: propose_field_updates con 2-5 campos creativos (UVP, narrative, headline) | `MINI` | Calidad decente, 4.5x barato que HEAVY |
| Llamada user: interview block estándar (alternatives, clarify) | `MINI` | Latencia importa en UX interview |
| Llamada user: navegación + tool routing | `MINI` | Tool use |
| Llamada user: generación con constraints duras (≤X palabras, tono específico + cumple Y) | `REASONING` | Constraint reasoning |
| Llamada user: interview block complejo (web_research → sintetizar → propose 5+ campos) | `REASONING` | Multi-paso |
| Llamada user: keyword "¿por qué...?" + data comparison | `REASONING` | Causal reasoning |
| Llamada user: "audita/diagnostica [funnel/marca/oferta]" | `HEAVY` | "accuracy matters more than speed/cost" |
| Llamada user: "haz un plan estratégico de N [días/semanas]" | `HEAVY` | Multi-step planning |
| Llamada user: análisis cross-módulo (ej. funnel + marca + oferta juntos) | `HEAVY` | Deep reasoning |
| Default | `MINI` | Safe middle ground |

### Señales explícitas por keyword (español neutro latam)

Router detecta por regex case-insensitive sobre `user_message`:

- `HEAVY`: `audita|auditar|diagnostic[oa]|analiza a fondo|plan estrat[eé]gico|estrategia de|ad[oó]nde va mi|c[oó]mo mejorar (mi|la) (marca|oferta|funnel)`
- `REASONING`: `por qu[eé]|dame razones|comp[aá]rame|optimiza|razon[aá]|piensa paso a paso|c[oó]mo (puedo|podr[ií]a)|explica por qu[eé]`
- `NANO` override: `mensaje con <40 chars AND sin tools`

### Arquitectura

```
modules/copilot/
  domain/
    model_tier.py                 # ModelTier enum + TierMetadata frozen dc
    routing_policy.py             # RoutingPolicy (rules list, default tier)

  application/router/
    model_router.py               # ModelRouter orchestrator
    classifiers/
      rule_classifier.py          # keyword/length/tool heurísticas
      llm_classifier.py           # nano-powered fallback si rules inconclusive
    routing_telemetry.py          # log cada decisión a DB para ratchet
```

**Strategy pattern:**

```
ModelRouter.select(request) → RoutingDecision
  request: { user_msg, context, mode, available_tools }
  decision: {
    tier: ModelTier,
    reason: str,
    fallback_tier: ModelTier,
    classifier_used: str,
    confidence: float
  }

  Chain:
    1. RuleClassifier (cheap, deterministic)
       → if confident: return decision
    2. LLMClassifier (nano call, fallback)
       → if confident: return decision
    3. Default (MINI)
```

**Telemetry obligatorio:** cada decisión persiste en `copilot_routing_log` para ratchet futuro (afinar reglas con data real).

---

## 2. Context Window

### Config

`backend/src/modules/copilot/domain/context_window.py`:

```python
@dataclass(frozen=True)
class ContextWindowConfig:
    RAW_WINDOW_TOKENS: int = 2000           # ventana raw prioritaria
    RAW_WINDOW_MAX_MESSAGES: int = 10       # ceiling duro
    RAW_WINDOW_MIN_MESSAGES: int = 4        # floor duro
    SUMMARY_MAX_CHARS: int = 400            # caveman
    SUMMARY_TARGET_TOKENS: int = 150
    NUDGE_AFTER_TOTAL_TOKENS: int = 8000    # banner "empieza nueva"
    TOKEN_COUNTER: str = "tiktoken:cl100k_base"
```

### Algoritmo build context

```
messages = conversation.messages ordered by created_at ASC

raw = []
tokens_used = 0

# walk desde el más reciente
for msg in reversed(messages):
    candidate_tokens = count_tokens(msg)
    projected = tokens_used + candidate_tokens

    if len(raw) >= RAW_WINDOW_MAX_MESSAGES:
        break
    if projected > RAW_WINDOW_TOKENS and len(raw) >= RAW_WINDOW_MIN_MESSAGES:
        break

    raw.insert(0, msg)
    tokens_used = projected

# raw = mensajes recientes
# displaced = messages[: len(messages) - len(raw)]

if displaced and conversation.summary is None:
    # primera vez — sincronizar (bloqueante)
    conversation.summary = build_summary_from_scratch(displaced)
elif displaced:
    # async post-respuesta — solo si hay desplazamiento nuevo
    schedule_rolling_summary_update(conversation.id, newly_displaced)

final_messages = [
    system_prompt,
    summary_message if conversation.summary else None,
    *raw,
]
```

### Rolling summary — incremental

```
def update_summary(old_summary, newly_displaced_msgs, tier=NANO):
    prompt = f"""Actualiza este resumen caveman de conversación previa ≤400 chars.
    Conserva hechos clave (decisiones, campos modificados, objetivos). Caveman español.

    Resumen previo:
    {old_summary or "(ninguno)"}

    Nuevos mensajes desplazados a resumir:
    {format_messages(newly_displaced_msgs)}

    Responde SOLO el nuevo resumen (≤400 chars). Sin preámbulo."""

    result = llm(tier).complete(prompt)
    return result[:400]  # hard cap
```

**Trigger:**
- Ejecutar **async** post-respuesta (no bloquea UX).
- Dirty flag `summary_dirty_at` marca si hay desplazamientos desde último summary.
- Worker procesa batch cada 5s por tenant o al cerrar conversación.
- Si usuario envía msg antes de que summary termine → usa el resumen viejo (eventual consistency OK).

### Sustento

- LangChain `ConversationSummaryBufferMemory` usa `max_token_limit` — nuestro approach equivalente con token + message caps.
- Chroma "context rot" research: degradación medible sobre contexto largo, mantener ventana chica > max.
- Costo real con T2 MINI: 2K in + 500 out = **$0.00375/turno**, con prompt cache **$0.001/turno**. 100 turnos/día/usuario = $0.10/día.

---

## 3. UI Sidebar — 3 estados

Mockup aprobado: `docs/mockups/copilot-sidebar-states.html`.

### Spec

**Rail (siempre visible, 60 px, derecha).**

| Estado | history | chat | rail |
|---|---|---|---|
| `collapsed` | hidden | hidden | 60 px con: toggle, nueva, avatares conv. activas, "más" |
| `rail` | hidden | 380 px | 60 px con: toggle, nueva (avatares ocultos) |
| `full` | 280 px | 400 px | 60 px con: toggle, nueva |

**Rail contenidos según estado:**

`collapsed`:
1. Botón chevron (toggle → `rail`)
2. Botón `+` nueva conversación
3. Divider
4. Avatares 40×40 px con 2 letras (hasta 6) — active con halo morado
5. Texto "más" → clic abre `full`

`rail`:
1. Botón chevron (toggle → `full`)
2. Botón `+` nueva conversación
3. Divider
4. (avatares ocultos — están en chat header + full panel)

`full`:
1. Botón chevron (toggle → `collapsed`)
2. Botón `+` nueva
3. Divider

**Panel history (solo en full, 280 px):**
- Header "Conversaciones"
- Botón "Nueva conversación" prominente
- Secciones: `Hoy` / `Ayer` / `Últimos 7 días` / `Anterior`
- Items: título + meta (tiempo relativo · tier usado · msgs count)
- Footer "Cargar 6 más" paginación
- Active item con background accent soft + border accent

**Chat panel (rail y full, 380–400 px):**
- Header: título (editable click inline) + meta tiers usados
- Body: mensajes + proposal cards + interview cards
- Banner context-rot cuando `total_tokens ≥ 8000`
- Input textarea + send button

### Atajos teclado

| Key | Acción |
|---|---|
| `C` | Colapsar |
| `R` | Rail |
| `F` | Full |
| `N` | Nueva conversación |
| `K` (o `Cmd/Ctrl+K`) | Focus input (pendiente) |
| `Esc` en input | Colapsar a rail |

### Persistencia estado

- `sidebarState`: localStorage key `copilot.sidebarState`
- Default primer visit: `rail`
- Mobile (<640px): forced `collapsed` con overlay cuando expand

### Context-rot nudge

- Banner amarillo sutil sobre input cuando `conversation.total_tokens ≥ 8000` **o** `message_count ≥ 12` (lo que toque primero).
- Copy: *"Esta conversación ya está larga. Para que el copilot te entienda mejor, [empieza una nueva]."*
- Dismissible por conversación (flag en store).
- Si user ignora y llega a 16K tokens, banner se vuelve rojo.

---

## 4. Data Model — Conversaciones

### Cambios `copilot_conversation`

Agregar columnas:

```sql
ALTER TABLE copilot_conversation ADD COLUMN IF NOT EXISTS
  summary             TEXT NULL,
  summary_updated_at  TIMESTAMPTZ NULL,
  summary_dirty_at    TIMESTAMPTZ NULL,
  message_count       INT NOT NULL DEFAULT 0,
  total_tokens        INT NOT NULL DEFAULT 0,
  last_tier_used      TEXT NULL,
  title               TEXT NULL,
  title_auto_generated BOOLEAN NOT NULL DEFAULT false,
  archived_at         TIMESTAMPTZ NULL,
  procedure_id        UUID NULL,
  procedure_state     JSONB NULL;

CREATE INDEX IF NOT EXISTS ix_copilot_conv_tenant_user_active
  ON copilot_conversation(tenant_id, user_id, updated_at DESC)
  WHERE archived_at IS NULL;
```

### Tabla nueva `copilot_routing_log`

```sql
CREATE TABLE IF NOT EXISTS copilot_routing_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    conversation_id UUID NOT NULL,
    message_id UUID NOT NULL,
    tier_selected TEXT NOT NULL,          -- nano|mini|reasoning|heavy
    classifier_used TEXT NOT NULL,        -- rule|llm|default
    reason TEXT NOT NULL,
    confidence NUMERIC(4,3) NULL,
    user_msg_length INT NOT NULL,
    tools_available INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    INDEX (tenant_id, created_at DESC)
);
```

Sirve para ratcheting: analizar cada mes qué tier se eligió y si fue óptimo.

### Tabla nueva `copilot_mutation_journal`

Reemplaza session-level undo de focus mode. Por conversación, registra cada mutation aceptada:

```sql
CREATE TABLE IF NOT EXISTS copilot_mutation_journal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    conversation_id UUID NOT NULL,
    message_id UUID NOT NULL,
    domain TEXT NOT NULL,            -- brand|offer|landing|...
    entity_id UUID NULL,
    field_path TEXT NOT NULL,
    old_value JSONB NULL,
    new_value JSONB NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reverted_at TIMESTAMPTZ NULL,
    INDEX (conversation_id, applied_at)
);
```

Botón "Deshacer todo lo de esta conversación" lee journal → reaplica `old_value` en orden inverso → marca `reverted_at`.

### API nuevos endpoints

```
GET    /api/v1/copilot/conversations?limit=6&cursor=<cursor>
         -> 200 [{ id, title, updated_at, message_count, last_tier_used, procedure_state }]
POST   /api/v1/copilot/conversations
         -> 201 { id } (empty, new)
PATCH  /api/v1/copilot/conversations/{id}  body: { title?, archived? }
DELETE /api/v1/copilot/conversations/{id}  -> soft delete
POST   /api/v1/copilot/conversations/{id}/revert  body: { mutation_ids? }
         -> reaplica old_values en orden inverso
```

---

## 5. Interview vs Focus — Decisión

### Focus mode: **eliminar**

Razón: valor cubierto por historial + ProposalCard + selected_fields chips. El único unique = session-level undo, migrado a **mutation journal** por conversación (mejor UX).

**Acción:**
1. Retirar `FOCUS_TOOLS` del registry.
2. Eliminar `application/tools/focus/` (3 archivos).
3. Retirar rama `if context.focus` en `get_tools_for_context()`.
4. Eliminar `focus_entity_data` de `CopilotState`.
5. Eliminar `focusEntity` / `focusSnapshot` del frontend store.
6. Migrar feature UI (preview pane, undo session) → mutation journal en conversación.

Deprecación: marcar tools con `deprecated=True` 1 sprint, luego delete. Log calls.

### Interview mode: **conservar, refactorizar a Procedure**

Razón: es un producto (intake guiado), no una UX alternativa. Historial no resuelve el workflow, solo la persistencia.

**Cambios:**

Antes (3 conceptos paralelos):
```
conversation
  + session (free | interview)
  + interviewSession
  + procedure_progress
```

Después (1 concepto con overlay opcional):
```
conversation
  + procedure_state (nullable JSONB)
    { procedure_id, current_block, completed_blocks[], answers{}, coverage }
```

**Efectos:**
- `InterviewSession` deja de ser entidad separada → serializa dentro de `conversation.procedure_state`.
- `get_tools_for_context()` simplificado:
  ```python
  def get_tools_for_context(ctx):
      tools = get_tools_for_route(ctx.current_route)
      if ctx.procedure_state:
          tools += PROCEDURE_TOOLS[ctx.procedure_state.procedure_id]
      return dedupe(tools)
  ```
- UI: chat header muestra badge progreso cuando hay procedure activo (ej. `Buyer persona · bloque 3 de 5 · 60%`).
- Historial: items con procedure muestran icono 🎯 y % coverage.
- Usuario retoma conversación → `procedure_state.current_block` reanuda flujo sin cambio de UI.

**Migración datos:** backfill script convierte `InterviewSession` rows → `copilot_conversation.procedure_state`. Luego drop tabla `interview_session`.

---

## 6. Portabilidad — 4 puertos

Copilot detrás de interfaces, default impls = Nicolify, swappables para otros SaaS.

```python
# domain/ports.py
class LLMProvider(Protocol):
    async def complete(
        self,
        tier: ModelTier,
        messages: list[Message],
        tools: list[Tool] | None,
        stream: bool = True,
    ) -> AsyncIterator[LLMEvent]: ...

class ConversationStore(Protocol):
    async def list(self, user_id: str, limit: int, cursor: str | None) -> Page[Conversation]: ...
    async def get(self, conversation_id: UUID) -> Conversation | None: ...
    async def create(self, user_id: str, tenant_id: UUID) -> Conversation: ...
    async def append(self, conversation_id: UUID, message: Message) -> None: ...
    async def update_summary(self, conversation_id: UUID, summary: str) -> None: ...

class ToolRegistry(Protocol):
    def get_tools_for_context(self, ctx: CopilotContext) -> list[Tool]: ...

class IdentityProvider(Protocol):
    async def current_user(self) -> User: ...
    async def tenant_id_for(self, user_id: str) -> UUID: ...
```

Defaults Nicolify: `OpenAILLMProvider`, `PostgresConversationStore`, `RouteBasedToolRegistry`, `ClerkIdentityProvider`.

---

## 7. Plan implementación (5 sprints)

| Sprint | Scope | Criterio terminado |
|---|---|---|
| S1 | Data model (columnas + tablas nuevas) + migraciones idempotentes + backfill `title` nano gen | Migration pasa en clone prod, `/conversations` endpoint list 200 |
| S2 | Model router (4 tiers + rule classifier + telemetry) | Test unit cubre 15 escenarios matriz decisión, log telemetría en prod |
| S3 | Context window (token-based + rolling summary async) | Conversaciones >6 msgs tienen summary ≤400 chars, cost test <$0.001/turno promedio |
| S4 | UI sidebar 3 estados (collapsed/rail/full) + history pagination + context-rot nudge | Mockup implementado 1:1, atajos C/R/F/N funcionan |
| S5 | Eliminar Focus + refactor Interview → Procedure + mutation journal | Tests arch 0 referencias a `focus_*`, UI procedure progress renderea |

Cada sprint: tests primero (TDD), native lint/tests, `/test-backend` + `/test-frontend` verdes antes merge.

---

## 8. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Router clasifica mal (MINI cuando debe HEAVY) | Telemetry log + revisión semanal primeros 30 días, ajuste rules |
| Rolling summary corrompe hechos clave | Log summary antes/después, test unit golden comparisons, fallback a re-summary full si consecutive bad summaries |
| Context cache miss frecuente | Reusar system prompt + tools schema como prefix estable (cacheable). Telemetry hit rate |
| Migración Interview rompe onboardings en curso | Feature flag `PROCEDURE_V2_ENABLED` por tenant, rollout gradual |
| Mutation journal crece sin límite | TTL 90 días + archive table. Rollup mensual |
| Modelo o3 muy lento para usuario | Timeout 60s, fallback a o4-mini con mensaje transparente |

---

## 9. Métricas éxito

A medir post-deploy:

- **Costo por conversación**: objetivo ≤$0.05 promedio (vs baseline actual ~$0.15)
- **Latencia primer token**: p50 ≤800ms, p95 ≤2000ms
- **Cache hit rate**: ≥60% en system prompt + tools
- **Router accuracy**: ≤5% misrouting (medido sampling manual mensual)
- **Context rot nudge acceptance**: ≥30% usuarios abren nueva conv al ver banner
- **Procedure completion rate**: interviews completados / iniciados, objetivo ≥70%

---

## 10. Referencias

- [OpenAI GPT-5.4 mini/nano announcement](https://openai.com/index/introducing-gpt-5-4-mini-and-nano/)
- [OpenAI o4-mini docs](https://platform.openai.com/docs/models/o4-mini)
- [OpenAI o3 docs](https://developers.openai.com/api/docs/models/o3)
- [OpenAI pricing](https://developers.openai.com/api/docs/pricing)
- [LangChain ConversationSummaryBufferMemory](https://api.python.langchain.com/en/latest/memory/langchain.memory.summary_buffer.ConversationSummaryBufferMemory.html)
- [Chroma Context Rot research](https://research.trychroma.com/context-rot)
- [Multi-LLM routing AWS](https://aws.amazon.com/blogs/machine-learning/multi-llm-routing-strategies-for-generative-ai-applications-on-aws/)
- Mockup: `docs/mockups/copilot-sidebar-states.html`
