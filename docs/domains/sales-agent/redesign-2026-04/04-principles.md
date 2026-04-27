# 04 · Principios senior — no negociables

## §1 — GoF + DRY + cohesión + acoplamiento

### §1.1 — GoF aplicable

| Patrón | Donde aplica |
|---|---|
| **Strategy** | Channel format (`ChannelFormat` por canal), payment provider (Mercado Pago vs Stripe) |
| **Adapter** | Webhooks de canal, payment providers, scheduler integrations (Cal.com / Calendly) |
| **Template Method** | `BaseAgentCallbackHandler._persist_llm_call/trace_event` (abstract), `BaseExtractionOrchestrator` |
| **Observer** | Domain event bus (`event_bus.publish` → subscribers en observability) |
| **Registry** | `tools/registry.py`, `CHANNEL_FORMATS`, `MODULE_REGISTRY`, `EXTRACTION_CONTRACTS` |
| **Factory** | `LLMFactory.get_service`, payment link factories |
| **Repository** | DDD layers — domain port, infrastructure impl |
| **State Machine** | Sales stages (rapport→discovery→presentation→closing) — ya implementado |

### §1.2 — DRY (don't repeat yourself)

- **Una sola SSoT por concept.** Pricing en `model_pricing_snapshot` (no hardcoded). Channel format en registry. Tools en registry.
- **No copy-paste de copilot a sales_agent.** Si lo necesitan ambos → `shared/agent_observability/`. Si lo usa uno → vive en el módulo.
- **Excepción**: tres líneas similares ≠ abstracción prematura. Esperar al 3er consumer real antes de extraer.

### §1.3 — Alta cohesión

- Cada subpaquete tiene UNA responsabilidad. `pricing/` solo pricing. `cost/` solo cálculo. `recording/` solo captura.
- Lógica nueva va donde corresponde semánticamente, NO donde es cómodo.
- Ejemplo: brand voice lighthouse vive en `brand/` (su SSoT), no en `sales_agent/` (consumer).

### §1.4 — Bajo acoplamiento

- Cross-module imports prohibidos fuera de `shared/links/` o ports declarados.
- Si sales_agent necesita data de brand → port en `shared/links/ports/brand.py` o domain event.
- `EventBus.publish(...)` desacopla productores y consumidores.
- Sales_agent NO importa `copilot/`. Copilot NO importa `sales_agent/`. Ambos consumen `shared/`.

---

## §2 — Anti-parche (CRÍTICO)

> "Senior dev con conceptos claros" = NO band-aids.

Si detectas bug ajeno durante el redesign:

1. **Verifica que es bug real.**
   - Reproducí con test RED.
   - Lee learnings + commits relevantes — quizás es comportamiento intencional documentado.
   - Si ambiguo → preguntar al usuario antes de tocar.

2. **Mide impacto.**
   - ¿Qué se rompe si fixeás? ¿Cuántos consumers? ¿Tests dependientes?
   - ¿Cuál es el blast radius? Idealmente fix afecta solo el archivo del bug.
   - Si afecta >3 archivos → elevar al usuario antes.

3. **Fix root cause, no síntoma.**
   - Test reproductor RED → fix → test GREEN.
   - NO `try/except: pass`. NO `# noqa`. NO disable lint rule sin razón documentada.
   - NO añadir defaults para "tapar" None inesperado — investigá por qué llega None.

4. **Loggear en `05-tech-debt-log.md`.**
   - Fecha + fase + path + descripción + impacto + acción + razón.

5. **Si requiere refactor cross-fase → DEFERRED.**
   - Loggear con detalle suficiente para que futuro tome el ítem.
   - NO meterlo en la fase actual (scope creep).

---

## §3 — TDD obligatorio

`.claude/rules/tdd-mandatory.md` aplica. Reglas extras:

- **Bug fix**: test que reproduce el bug ANTES del fix. Sin excepciones.
- **Feature nuevo**: test por capa (domain → repo → service → API).
- **Arch invariant**: fitness test en `tests/architecture/` antes de implementar el invariant.
- **Refactor**: tests verdes antes y después. Si tests cambian, son tests nuevos (no "ajustar test al refactor").

---

## §4 — Tenant isolation

Every query filter `tenant_id`. Sin excepciones.

- Repos reciben `tenant_id` como required param.
- Workers (cron) iteran tenants explícito; nunca query global sin filtro.
- Tabla shared (`model_pricing_snapshot`) excepción: es reference data global, no PII.

---

## §5 — PII safety

- TODO write a `*_trace_event` o `*_llm_call` pasa por `sanitize_payload(...)`.
- Regex extendible: emails, phones LATAM con/sin keyword, API tokens (sk-*, gsk_*, xai-*).
- Sales_agent NECESITA extender regex con: `nro de tarjeta`, `cvv`, `dni/curp/cuit`, `dirección`.
- Aún si pensás "no puede tener PII", llamálo igual.

---

## §6 — Best-effort observability

- Recorder NUNCA debe romper turn.
- Pattern obligatorio:
  ```python
  try:
      repo.add(...)
  except Exception as exc:
      logger.warning("obs_write_failed", error=str(exc))
      db.rollback()
  ```
- Validado por test arquitectónico.

---

## §7 — Spanish neutro LATAM

`.claude/rules/spanish-text.md`. Sin voseo.

Aplica a:
- Componentes React, schemas form-runtime (labels/hints/placeholders/options)
- Catálogos backend user-facing (archetype/preset/section)
- DTOs con mensajes
- Prompts LLM output user
- Emails, notificaciones
- Mensajes del sales_agent al lead (CRÍTICO — el agente vende, debe sonar profesional)

NO aplica a:
- Logs internos, errores técnicos dev
- Comentarios código, nombres variables
- Tests cuyo string no llega UI

Tools del sales_agent: descripciones (`@tool` description) son leídas por el LLM → idioma debe estar alineado con el system prompt (default spanish neutro).

---

## §8 — Native-first dev

Lint / tests / type-check NATIVE WSL. NUNCA `docker exec ... ruff|pytest|tsc|vitest|eslint`.

Docker SOLO para:
- Runtime (`docker compose up -d`)
- Migraciones (`alembic upgrade head`)
- Logs (`docker logs ...`)
- Fresh DB migration verify

---

## §9 — `response_model=` mandatory

Cada endpoint FastAPI declara `response_model=`. Pydantic actúa como allowlist. Sin excepciones.

PII en response → remove / mask / justify (en code comment).

Ver `.tessl/tiles/maria/fastapi/rules/pii-sanitisation.md`.

---

## §10 — Commit hygiene

- Conventional commits: `feat(sales-agent-redesign-s{N}): subject`.
- Stage por nombre. NUNCA `git add -A` ni `git add .`.
- Sólo archivos de la sesión actual. Otras sesiones paralelas pueden tener WIP.
- NO `--no-verify`. NO `--amend` published.

Ver `.claude/rules/parallel-safety.md` y `.claude/rules/git-safety.md`.
