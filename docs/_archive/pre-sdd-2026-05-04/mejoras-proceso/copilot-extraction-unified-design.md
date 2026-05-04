# Diseño unificado — Extracción en Copilot (URL + Doc) con guided aware

> SSoT para implementación. Feed directo a backend + agentic + auditor agents.
> Contexto: traza `376850f5-27aa-42e6-8e70-a03a2e6a9501` mostró loop de 8 `extract_structured` porque guided bloquea `extract_from_url`. Además offer extraction carece de paridad con brand (orchestrator, per-wave save, trace).

## Decisiones acordadas

1. **`extraction` toolset disponible en guided** (`extract_from_url`, `extract_from_doc`).
2. **Guided aware del estado de extracción** — pausa preguntas cuando hay job activo, resume con campos pendientes cuando termina.
3. **Default scope "completar faltantes"** cuando user ya tiene progreso manual.
4. **Preservar bloque actual** durante pausa (`paused_at_block`).
5. **Offer ↔ Brand paridad arquitectónica**: orchestrator separado, per-wave save, trace collector, user_id passthrough.
6. **`extract_structured` retorna text informativo en skip** — corta loops.

---

## State contract — `procedure_state` JSONB

Extiende `copilot_conversations.procedure_state` con nuevo sibling key `active_extraction_job`:

```json
{
  "guided": {
    "domain": "offer",
    "entity_id": "a96403b5-...",
    "current_block_id": "identity",
    "completed_blocks": [],
    "started_at": "2026-04-23T21:34:14Z"
  },
  "active_extraction_job": {
    "job_id": "uuid",
    "module": "offer",
    "entity_id": "a96403b5-...",
    "source_kind": "url",
    "source_ref": "https://visionarias.lat/products/...",
    "scope": "full",
    "mode": "update",
    "paused_at_block": "identity",
    "started_at": "2026-04-23T22:01:00Z"
  }
}
```

**Reglas:**
- `active_extraction_job` se escribe cuando `extract_from_url` / `extract_from_doc` despachan ARQ job OK.
- `paused_at_block` copia `guided.current_block_id` si guided está activo; `null` si no.
- Se borra cuando `ExtractionJobCompletedEvent` llega al subscriber.
- `guided` y `active_extraction_job` son **siblings independientes**. Un flujo puede tener uno, el otro, ambos, o ninguno.

### Dataclass

Archivo nuevo: `backend/src/modules/copilot/application/extraction/active_job_state.py`

```python
@dataclass(slots=True)
class ActiveExtractionJob:
    job_id: str
    module: str              # "brand" | "offer"
    entity_id: str | None
    source_kind: str         # "url" | "doc"
    source_ref: str          # URL or asset_id
    scope: str               # "full" | "section" | "field" | "visuals"
    mode: str                # "initial" | "update" | "suggest"
    paused_at_block: str | None
    started_at: str

    @classmethod
    def from_json(cls, data: dict | None) -> ActiveExtractionJob | None: ...

    def to_json(self) -> dict: ...


ACTIVE_EXTRACTION_JOB_KEY = "active_extraction_job"


def load_active_job(procedure_state: dict | None) -> ActiveExtractionJob | None: ...

def merge_active_job(procedure_state: dict | None, job: ActiveExtractionJob | None) -> dict: ...
```

### Persistence helpers

Archivo nuevo: `backend/src/modules/copilot/application/extraction/active_job_persistence.py`

```python
def read_active_job(conversation_id: str | None) -> ActiveExtractionJob | None: ...

def write_active_job(conversation_id: str | None, job: ActiveExtractionJob | None) -> None: ...
```

Mismo patrón que `guided/persistence.py`: lee `procedure_state` completo, merge el key, UPDATE con CAST JSONB.

---

## Flujo de estado — 3 fases

### Fase 1 — Dispatch

**Dónde**: `copilot/application/tools/extraction_tools.py` en `_extract_from_url_impl` y `extract_from_doc`.

**Después** de `arq_pool.enqueue_job(...)` exitoso, **antes** del return JSON:

```python
conv_id = get_conversation_id()
if conv_id:
    from src.modules.copilot.application.guided.persistence import read_state as read_guided
    from src.modules.copilot.application.extraction.active_job_persistence import write_active_job

    guided = read_guided(conv_id)
    job_state = ActiveExtractionJob(
        job_id=job_id,
        module=module,
        entity_id=entity_id,
        source_kind="url",  # or "doc"
        source_ref=url,     # or asset_id
        scope=scope,
        mode=mode,
        paused_at_block=guided.current_block_id if guided else None,
        started_at=started_at,
    )
    write_active_job(conv_id, job_state)
```

**Best-effort**: si falla write no revierte el dispatch.

### Fase 2 — Rehidratación en cada turno

**Dónde**: `copilot/application/orchestrator/chat.py` `_prepare_conversation`.

```python
# Junto a read_guided_state
active_job = read_active_job(conv_id)
client_ctx["active_extraction_job"] = active_job.to_json() if active_job else None

state = create_initial_copilot_state(...)
state["active_extraction_job"] = client_ctx["active_extraction_job"]
```

**Dónde**: `copilot/application/orchestrator/graph.py` `_build_guided_layer` (o wrapper nuevo `_build_extraction_layer`).

Leer `state["active_extraction_job"]` + pasar al prompt Jinja.

### Fase 3 — Completion

**Dónde**: `copilot/application/extraction_card_flow.py` `handle_job_completed`.

Antes de retornar el summary card, clear del state:

```python
conv_id = event.payload.get("conversation_id")
if conv_id:
    write_active_job(conv_id, None)  # clear
    # Summary card keeps coverage_by_section → LLM naturally knows what's pending
```

El `_build_guided_layer` del próximo turno inyectará campos pendientes del `paused_at_block` leyendo el form data actual.

---

## Prompt template — `copilot_guided.j2` reescrito

```jinja2
{% if active_extraction_job %}
--- EXTRACCIÓN EN CURSO ---
Hay un análisis corriendo en segundo plano ({{ active_extraction_job.source_kind }}: {{ active_extraction_job.source_ref }}).
Módulo: {{ active_extraction_job.module }} · Scope: {{ active_extraction_job.scope }} · Mode: {{ active_extraction_job.mode }}

Reglas mientras corre:
- NO llames `extract_structured` sobre el dominio "{{ active_extraction_job.module }}" (riesgo de conflicto con el worker).
- NO preguntes campos específicos aún — los estamos rellenando por ti.
- Conversá casual con el usuario. Si aporta contexto útil, acusa recibo y decile que se consolidará al terminar el análisis (~1-2 min).
- Cuando el análisis termine, verás "extracción completa" en este prompt y podrás reanudar preguntas solo sobre lo que quedó vacío.

--- FIN EXTRACCIÓN EN CURSO ---
{% endif %}

{% if guided_active %}
--- MODO GUIADO ACTIVO ---
Dominio: {{ domain }}
{% if entity_id %}Entidad: {{ entity_id }}
{% endif %}Bloque actual: **{{ current_block_label }}** (`{{ current_block_id }}`)
Progreso: {{ blocks_completed_count }} de {{ total_blocks }} bloques completados.
{% if current_block_field_paths %}
Campos objetivo del bloque:
{% for path in current_block_field_paths %}- `{{ path }}`
{% endfor %}
{% endif %}
{% if pending_field_paths %}
Campos PENDIENTES del bloque (los demás ya tienen valor):
{% for path in pending_field_paths %}- `{{ path }}`
{% endfor %}
{% endif %}

Reglas del modo guiado — obligatorias:

1. UNA PREGUNTA A LA VEZ. No bombardees.

2. CAPTURA GLOBAL. Si el usuario menciona datos de otra sección, usa
   `extract_structured` para guardarlos. Nunca pierdas información.

3. NUNCA REPITAS. Si un campo ya tiene valor, NO lo preguntes de nuevo.
   Pregunta solo por los `pending_field_paths` listados arriba.

4. CONFIRMA Y AVANZA. Cuando el bloque alcance cobertura alta (≈80%),
   presenta resumen compacto y llama a `advance_guided_block`.

5. FOCO. Todo lo que contestes debe relacionarse con la entidad en curso.

6. URL o DOCUMENTO recibido. Si user pasa URL o sube archivo:
   - Primero `clarify` scope (default "Completar faltantes" si ya hay progreso).
   - Luego `extract_from_url` o `extract_from_doc`.
   - Tras despacho, avisa breve ("inicié análisis, 1-2 min") y seguí conversando.
   - NO llames `extract_structured` en ese turno sobre el dominio activo.

7. DOCUMENTOS mid-flow. Si el user tiene progreso manual y sube doc,
   reconoce el progreso: "veo que ya avanzaste Identidad, voy a procesar
   el doc respetando eso".

8. SALIDA. User pide salir → `end_guided_setup`.

9. PROPUESTAS. Para escribir a la entidad real usa SIEMPRE
   `propose_field_updates` con paths del catálogo editable.

Español latinoamericano neutro (tuteo "tú"). Mensajes cortos.

--- FIN MODO GUIADO ---
{% endif %}
```

### Variables que recibe el template

Nuevas:
- `active_extraction_job: dict | None`
- `pending_field_paths: list[str]` — calculado en `_build_guided_layer` leyendo form data actual (comparando `current_block_field_paths` contra campos con valor).

Existentes mantienen semántica.

---

## Tool unlock — `registry.py`

`copilot/application/tools/registry.py:267-268`:

```python
if context.get("guided_mode"):
    return _collect_groups(
        ("guided", "extraction", "knowledge", "shared_tools", "document"),
    )
```

Agregar `"extraction"`.

**Test arch** nuevo: `backend/tests/modules/copilot/test_guided_toolset.py` — assert `extract_from_url` en result de `get_tools_for_context({"guided_mode": True})`.

---

## Fix `extract_structured` skip feedback

`copilot/application/tools/extraction_tools.py:79-90`:

Reemplazar bloque `return json.dumps({...})` al final de `extract_structured`:

```python
text_msg = ""
if skipped and not delta:
    text_msg = (
        f"Todos los field_paths propuestos son inválidos para dominio '{domain}': {skipped}. "
        f"Revisa el catálogo con get_editable_fields y reintenta con paths válidos."
    )

return json.dumps({
    "text": text_msg,
    "ui_action": {
        "type": "preview_update",
        "domain": domain,
        "delta": delta,
        "confidence_map": confidence_map,
        "skipped": skipped,
    },
})
```

**Nota**: `skipped` en esta tool actualmente significa "path inválido", no "campo ya lleno". El loop real de la traza fue por LLM reinterpretando respuesta vacía. La fix principal es dar texto; el comportamiento "campo ya lleno" lo cubre la inyección de `pending_field_paths` en prompt.

---

## Offer extraction — paridad con brand

### 1. Endpoint `offer/api/offer_extraction.py:103-112`

Agregar:
```python
await arq_pool.enqueue_job(
    ExtractionJob.OFFER.value,
    job_id=job_id,
    tenant_id=tenant_id,
    offer_id=offer_id,
    url=url,
    text=combined_text or None,
    mode=mode,
    update_instructions=update_instructions,
    user_id=str(current_user.id),  # NEW
)
```

### 2. Worker `offer/workers/tasks.py`

Agregar `user_id: str | None = None` al signature de `run_offer_extraction`. Pasar al service (aunque hoy no se use, prepara para social-proof futuro).

### 3. Orchestrator nuevo

Crear `backend/src/modules/offer/application/offer_extraction_orchestrator.py` — port de `brand/application/extraction_orchestrator.py`:

**Signature**:
```python
class OfferExtractionOrchestrator:
    def __init__(self, service: OfferExtractionService): ...

    async def run(
        self,
        url: str | None = None,
        text: str | None = None,
        mode: Literal["initial", "update"] = "initial",
        update_instructions: str | None = None,
        progress_callback: ProgressCallback | None = None,
        trace: OfferExtractionTrace | None = None,
        user_id: UUID | None = None,
    ) -> Offer: ...
```

**Waves offer** (basadas en `offer/domain/copilot_editable_fields.py`):
- W1: `identity`, `promise`, `strategy`
- W2: `psychology`, `value_stack`, `pricing`
- W3: `closing_system`, `onboarding`, `classification`

Invariante: `_merge_and_save` guarda antes de `_announce_sections` (mirror de brand test).

### 4. Trace collector nuevo

`backend/src/modules/offer/application/offer_extraction_trace.py` — port de `brand_extraction_trace.py`.

### 5. Refactor service

`offer/application/offer_extraction_service.py:extract_all()` → delegar a `OfferExtractionOrchestrator`. Mantener signature pública.

### 6. Tests nuevos

- `backend/tests/modules/offer/test_extraction_orchestrator_per_wave_save.py` (mirror de `brand/test_extraction_orchestrator_per_wave_save.py`)
- `backend/tests/modules/offer/test_offer_extraction_service_delegates.py` (service delega a orchestrator)

---

## Orden de ejecución (agentes)

**Wave A** (paralelo, independientes):

- **nicolify-agentic** — copilot changes:
  - registry.py (tool unlock)
  - extraction tools (write active_extraction_job on dispatch)
  - extract.py (skip feedback)
  - orchestrator/graph.py + chat.py (state hydration + prompt variables)
  - copilot_guided.j2 (reescrito con 2 bloques)
  - extraction_card_flow.py (clear active_extraction_job on completion)
  - active_job_state.py + active_job_persistence.py (nuevos archivos)
  - Tests copilot del flujo

- **nicolify-backend** — offer parity:
  - offer_extraction_orchestrator.py (nuevo)
  - offer_extraction_trace.py (nuevo)
  - offer_extraction_service.py (refactor)
  - offer/api/offer_extraction.py (user_id)
  - offer/workers/tasks.py (user_id param)
  - Tests offer

**Wave B** (secuencial post-A):

- **nicolify-backend-auditor** — review completo DDD, tenant isolation, no regression.
- Correr `/test-backend` + `/test-frontend` nativo.
- Fix findings.

---

## Invariantes / Anti-patterns

- ❌ No leer `active_extraction_job` desde algo que no sea `procedure_state` (single source).
- ❌ No hardcodear waves offer sin leer catálogo editable.
- ❌ No pasar `tenant_id` como arg de tool (usar `get_tenant_id()`).
- ❌ No cross-module imports entre offer/copilot/brand (usar shared/links o events).
- ❌ No romper semantica existente de `guided` state.
- ❌ No Docker para tests — native WSL (CLAUDE.md rule).
- ❌ No commit con `.env`, secretos.
- ✅ Stage por nombre en commits (paralelo-safety).
- ✅ Spanish neutro en todo user-facing.
- ✅ TDD: tests ANTES de implementar cambio nuevo (CLAUDE.md rule 13).

---

## Success criteria

1. Traza reproducida con URL en guided offer muestra `tool_call: extract_from_url` en vez de 8× `extract_structured`.
2. Durante la extracción (fase 2), turns del user que chatean casual no gatillan `extract_structured` sobre campos del módulo activo.
3. Post completion: summary card aparece + próximo turn pregunta solo por `pending_field_paths`.
4. Offer tests per-wave save pasan (mirror brand).
5. `/test-backend` y `/test-frontend` 0 errores nuevos.
6. `nicolify-backend-auditor` sin findings CRITICAL.
