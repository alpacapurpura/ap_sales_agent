# T-1 Implementation Log — sales-agent-expert skill audit

**Story:** maintenance-skill-sales-agent-audit  
**Ticket:** T-1  
**Date:** 2026-05-06  
**Builder:** claude-sonnet (builder-backend, production_code=false per R23)  
**Phase:** 4 pasadas audit (paths → surfaces → cardinales → utility verdicts)

---

## Pasada 1 — Verificación mecánica de paths

Resultados del scan de símbolos/paths citados en SKILL.md + references/*.md.

### Paths que RESUELVEN (verificados con filesystem + grep)

| Símbolo | Path verificado | Estado |
|---|---|---|
| `domain/model_tier.py::SPECIALIST_TO_ROLE` | `backend/src/modules/sales_agent/domain/model_tier.py:79` | OK |
| `domain/model_tier.py::LLM_ROLE_BY_SITE` | idem | OK |
| `application/tools/registry.py::STAGE_TOOL_SCOPE` | `backend/src/modules/sales_agent/application/tools/registry.py:56` | OK |
| `shared/agent_observability/channels/format.py::CHANNEL_FORMATS` | `backend/src/shared/agent_observability/channels/format.py:192` | OK |
| `personality_profiles` (tabla) | `backend/alembic/versions/f86f848caefa_add_personality_profiles_table.py` | OK |
| `model_pricing_snapshot` (tabla) | `backend/src/shared/agent_observability/persistence/models/pricing_snapshot_model.py:21` | OK |
| `mv_daily_llm_cost_per_tenant_v2` | `backend/src/shared/billing/application/budget_guard.py:33` + admin modules | OK |
| `sales_agent_routing_log` | `backend/src/admin/modules/sales_routing.py:39` | OK |
| `SalesAgentJudge` | `backend/src/modules/sales_agent/application/quality/judge.py:216` | OK |
| `application/orchestrator/tool_call_dedup.py` | exists | OK |
| `api/closer_studio.py` | exists | OK |
| `workers/follow_up_engine.py` | exists | OK |
| `pricing/aliases.py` | `backend/src/shared/agent_observability/pricing/aliases.py` | OK |
| `pricing/resolver.py` | `backend/src/shared/agent_observability/pricing/resolver.py` | OK |
| `docs/domains/sales-agent/redesign-2026-04/README.md` | exists | OK |
| `docs/domains/sales-agent/redesign-2026-04/00-vision-and-objectives.md` | exists | OK |
| `docs/domains/sales-agent/redesign-2026-04/02-architecture-target.md` | exists | OK |
| `docs/domains/sales-agent/redesign-2026-04/04-principles.md` | exists | OK |
| `docs/domains/sales-agent/redesign-2026-04/05-tech-debt-log.md` | exists | OK |
| `compose_system_prompt(fragments)` + `CACHE_BOUNDARY_MARKER` | `application/prompts/compose.py:95,103` | OK |
| `personality_profiles.system_instruction` (SSoT voz) | `PersonalityProfile.__tablename__` confirmed | OK |
| `docs/archive/2026/legacy-pis/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-2-billing-and-compliance/CONTRACT.md` | verified exists | OK (archived) |

### Paths que requirieron UPDATE (corrección aplicada in-place)

| Símbolo citado (antes) | Corrección | Razón |
|---|---|---|
| `BufferService.smart_debounce` (SKILL.md §3, line 32) | → `SmartBufferService` (smart_debounce_runner.py) | Clase real: `class SmartBufferService` — `BufferService` no existe como nombre de clase |
| `agent_state_checkpoint` schema (SKILL.md §3, line 35) | → `agent_state_checkpoints` (plural) | `__tablename__ = "agent_state_checkpoints"` — nombre plural confirmado en model + migrations |
| `identity.voice_tone` + `identity.communication_style` (humanization-rules.md, lines 9,17-18) | → `compiled_brand_voice` slot 5 + nota DEPRECATED | `FieldStatus.DEPRECATED` en `brand/domain/field_contract.py:255` desde 2026-04-24 Fase 06 |
| Value level names en conversation-stages.md (lines 222-244): `level_0_free`, `level_1_low_ticket`, `level_2_mid_ticket`, `level_3_high_ticket`, `level_4_recurring`, `level_5_ultra_high` | → `LEAD_MAGNET`, `ACTIVACION`, `TRANSFORMACION`, `MAXIMIZACION`, `CORPORATIVO` | Nombres reales en `OfferValueLevel` enum (value_level_catalog.py) |
| Tool names in tool-patterns.md: `check_schedule`, `book_appointment`, `recommend_product`, `lookup_customer` | → nota de vigencia added (header) | Nombres registrados en TOOL_REGISTRY son `get_available_slots`, `create_booking_link`, etc. (S5-S9 redesign) |

### Observaciones adicionales Pasada 1

- `format_for_channel.py` existe como módulo separado en `shared/agent_observability/channels/` (LangChain tool wrapper, S5). SKILL.md cita correctamente `format.py` como SSoT del registro; `format_for_channel.py` es el wrapper determinístico exportable como tool.
- `SalesAgentTraceEventRepository` y `SalesAgentLlmCallRepository` satisfacen los protocolos `BaseTraceEventRepoProtocol` y `BaseLLMCallRepoProtocol` via **structural typing** (no herencia formal de clase base).
- `ComplianceService` de `shared/compliance/` NO aparece importado en sales_agent (grep confirmado vacío). Citado en CONTEXT-BRIEF como probable, pero no wired todavía. Sin cambio en skill (no se puede documentar consumer que no existe).

---

## Pasada 2 — Surfaces compartidas (raw scan output)

Comandos ejecutados:

```bash
grep -rn "from src.shared.agent_observability|from shared.agent_observability" \
  backend/src/modules/sales_agent/ | grep -v __pycache__
grep -rn "from src.shared.billing|from shared.billing" \
  backend/src/modules/sales_agent/ | grep -v __pycache__
```

### Raw output deduplicado

```
observability/recording/callback_handler.py:43 → shared.agent_observability.recording.base_callback_handler.BaseAgentCallbackHandler
observability/recording/factory.py:39          → shared.agent_observability.cost.fx_resolver.FXResolver
observability/recording/factory.py:40          → shared.agent_observability.persistence.pricing_snapshot_repository.PricingSnapshotRepository
observability/recording/factory.py:43          → shared.agent_observability.persistence.tenant_billing_config_repository.TenantBillingConfigRepository
observability/recording/factory.py:46          → shared.agent_observability.pricing.resolver.PricingResolver
observability/recording/turn_envelope.py:46    → shared.agent_observability.recording.turn_envelope.BaseObservabilityContext
observability/recording/turn_envelope.py:60    → shared.agent_observability.cost.fx_resolver.FXResolver (TYPE_CHECKING only)
observability/recording/turn_envelope.py:61    → shared.agent_observability.pricing.resolver.PricingResolver (TYPE_CHECKING only)
observability/__init__.py:13                   → shared.agent_observability.registry
application/prompts/compose.py:43              → shared.agent_observability.channels.format.get_channel_format
application/quality/judge.py:44               → shared.agent_observability.recording.sanitization.sanitize_payload
infrastructure/external/output_manager.py:28  → shared.agent_observability.channels.format.get_channel_format
observability/domain_events/subscribers.py:35 → shared.agent_observability.recording.sanitization.sanitize_payload
application/orchestrator/conversation_pipeline.py:49 → shared.billing.application.llm_guards.BudgetGuardingLLMService
application/orchestrator/conversation_pipeline.py:66 → shared.billing.application.budget_guard.BudgetGuard (TYPE_CHECKING)
application/orchestrator/outbound_orchestrator.py:53 → shared.billing.application.budget_guard.BudgetGuard (TYPE_CHECKING)
```

**Nota sobre repos:** `SalesAgentTraceEventRepository` y `SalesAgentLlmCallRepository` satisfacen `BaseTraceEventRepoProtocol` / `BaseLLMCallRepoProtocol` por structural typing (Python duck typing). No hay import explícito de las bases en runtime — solo en docstrings y TYPE_CHECKING hints.

**ComplianceService (shared/compliance/):** NOT imported. Citado en CONTEXT-BRIEF como "probable" pero confirmado ausente en scan. No incluido en nueva sección Surfaces compartidas.

---

## Pasada 3 — Decisiones cardinales (3 fuentes)

### Fuente (a) — learnings.md (filtrado sales_agent / agent_observability / litellm)

- 2026-05-06: `sales-agent-litellm-canonicalization` cerrado (review → done). Legacy adapters eliminados en T-4. LiteLLM único path. (entry §Cierre limpio legacy outcomes)
- 2026-05-05: `BaseObservabilityContext` + `FXResolver.default()` lifted a shared (d80d15f5). Bug #2+#8 resueltos.
- 2026-05-05: R23 rule establecida: agentic `production_code=true` → Opus 4.7; `production_code=false` → Sonnet OK.
- 2026-05-05: `builder-backend` MAY touch `modules/{copilot,sales_agent}/persistence/models/` para schema mirror (exception en backend-ddd.md).
- 2026-05-05: cost recorder canonicalization T-1: `cost_usd` via `pop_cost(litellm_call_id)`, no `calculate_cost()` runtime. Test fixtures requieren `litellm_call_id` en `response_metadata`.

### Fuente (b) — git log 60d (commits relevantes)

- `aabd3acc` 2026-05-06: purge LiteLLM canonicalization stale references
- `8b6d798f` 2026-05-06: sync-pricing extends litellm_sync.py + Makefile target
- `5856be4d` 2026-05-06: cost recorder LiteLLM canonicalization (T-1 PI-12 S1)
- `d80d15f5` 2026-05-05: lift BaseObservabilityContext + FXResolver.default + fix traces
- `7b2de359` 2026-04-30: outbox cutover ON (USE_OUTBOX_PATTERN_SALES_AGENT=True)
- `06065f6c` 2026-04-28: LiteLLM Proxy integration S3 PR-2
- `7bed7dea` 2026-04-28: campaigns PR-8 (cross-context, not sales_agent core)
- `0da30299` 2026-04-17: S12 close-out final hardening

### Fuente (c) — stories archivadas (docs/archive/2026/stories/)

- `sales-agent-eval-runner-foundation` (archived): eval suite path establecido. T-3/T-4 completados.
- `sales-agent-litellm-canonicalization` (archived): canonical LiteLLM path shipped.

---

### Claims removed (archived)

Contenido eliminado de skill files con razón (cero pérdida de data — Q4).

**[DELETE: humanization-rules.md — voice_tone/communication_style Jinja template — líneas 9-26 originales]**

```markdown
The agent's voice comes from Brand Studio data (`identity.voice_tone`,
`identity.communication_style`). But these fields are often empty or
generic. The skill must handle both cases.

### When Brand Data Has Voice Info

Use it directly in the system prompt. But REINFORCE with behavioral rules:

```jinja2
## Tu Forma de Hablar
{{ identity.voice_tone }}
{{ identity.communication_style }}

REGLAS DE ESTILO:
- Escribe como si estuvieras respondiendo un DM, no un email
- Máximo 3 oraciones por mensaje
- Una idea por mensaje
- Si necesitas decir mucho, divídelo en 2-3 mensajes cortos
- Usa el mismo vocabulario que usaría {{ identity.brand_name }}
```
```

Razón eliminación: `identity.voice_tone` + `identity.communication_style` tienen `FieldStatus.DEPRECATED` desde 2026-04-24 Fase 06. Reemplazado por referencia a `PersonalityProfile.system_instruction` (slot 5 `BRAND_VOICE`). Contenido preservado aquí verbatim por Q4 zero-loss policy.

**[UPDATE: conversation-stages.md — value levels pseudocode (Stage 5 Closing) — líneas 222-244 originales]**

```python
# Pseudocode for close strategy selection
if offer.value_level in ("level_0_free", "level_1_low_ticket"):
    tool = "send_payment_link"
    ...
elif offer.value_level == "level_2_mid_ticket":
    ...
elif offer.value_level in ("level_3_high_ticket", "level_5_ultra_high"):
    tool = "book_appointment"
    ...
elif offer.value_level == "level_4_recurring":
    tool = "book_appointment"
    ...
```

Razón: Value level names obsoletos (`level_0_free` etc.) — enum actual es `LEAD_MAGNET`, `ACTIVACION`, `TRANSFORMACION`, `MAXIMIZACION`, `CORPORATIVO`. Tool names `book_appointment` → `create_booking_link` (S5-S9). Actualizado con nombres correctos + nota de vigencia.

---

### Claims updated

Cambios in-place aplicados (before → after) con razón.

| Archivo | Sección | Antes | Después | Razón |
|---|---|---|---|---|
| SKILL.md §3 | `BufferService.smart_debounce` | `BufferService.smart_debounce` | `SmartBufferService (smart_debounce_runner.py)` | Clase real: `class SmartBufferService`. No existe `BufferService` como nombre de clase. |
| SKILL.md §3 | `agent_state_checkpoint schema` | `agent_state_checkpoint` (singular) | `agent_state_checkpoints (tabla, plural)` | `__tablename__ = "agent_state_checkpoints"` — plural confirmado en model + migrations. |
| SKILL.md Budget §3 reference | `BufferService` en texto | `BufferService` | `SmartBufferService` | Idem. Consistencia con tabla §3. |
| humanization-rules.md §Voice Matching Protocol | Referencia a `voice_tone` + Jinja template | (ver Claims removed) | Referencia a `PersonalityProfile.system_instruction` slot 5 + nota DEPRECATED | `voice_tone` DEPRECATED 2026-04-24. |
| conversation-stages.md §Stage 5 | Value level names + tool names | `level_0_free`, `book_appointment` etc. | `LEAD_MAGNET`, `create_booking_link` etc. | Enum `OfferValueLevel` tiene valores nuevos post-redesign. |
| tool-patterns.md §header | Sin nota de vigencia | (sin nota) | Nota de vigencia + mapeo tool names antiguos→nuevos | Tool names divergen (S5-S9 redesign). |

---

### Claims added

Contenido nuevo introducido en skill files.

#### 1. SKILL.md — `## Surfaces compartidas con copilot (consumers shared/agent_observability)`

Sección nueva insertada entre `## Decisiones cross-fase no obvias` y `## SSoT vivos`.

Contenido: lista de 13 bullets documentando cada subsystem de `shared/` consumido por sales_agent con path canónico y archivo consumer. Cubre: BaseAgentCallbackHandler, BaseObservabilityContext, FXResolver, PricingResolver, PricingSnapshotRepository, TenantBillingConfigRepository, BaseTraceEventRepoProtocol, BaseLLMCallRepoProtocol, get_channel_format/CHANNEL_FORMATS, format_for_channel (LangChain tool), sanitize_payload, registry, BudgetGuardingLLMService/BudgetGuard.

Razón: AD3 (arch decision). 7 surfaces de anti-duplication.md no estaban documentadas en skill (CONTEXT-BRIEF §7.5). Prerequisito para downstream eval-foundation stories.

#### 2. SKILL.md — `## Decisiones cardinales últimos 60 días`

Sección nueva insertada inmediatamente después de `## Surfaces compartidas con copilot`.

Contenido: 10 bullets con decisiones fechadas desde 2026-04-17 hasta 2026-05-06. Fuentes citadas: learnings.md, commit hashes, stories archivadas. Decisiones incluidas: litellm-canonicalization done, synthetic-first reframe PI-12, BaseObservabilityContext lift, R23 rule, schema mirror exception, cost recorder bridge, outbox cutover, LiteLLM Proxy, revert cycle, S12 close-out.

Razón: AD3 + Q2 contract decision. Downstream builders/architects necesitan estas decisiones para no contradecir código live.

#### 3. humanization-rules.md — nota DEPRECATED voice_tone

Nota inline en `## Voice Matching Protocol` indicando que `identity.voice_tone` está DEPRECATED desde 2026-04-24 Fase 06.

Razón: UPDATE correctivo. Stale Jinja2 template podría llevar a builder a usar campo deprecated.

#### 4. conversation-stages.md — nota de vigencia value levels

Nota inline en Stage 5 `## Closing` indicando que los value level names en el pseudocódigo son los del enum actual.

Razón: UPDATE correctivo. Nombres `level_0_free` etc. son pre-redesign.

#### 5. tool-patterns.md — nota de vigencia header

Nota al inicio del archivo indicando divergencia entre nombres de herramientas conceptuales vs. registrados en TOOL_REGISTRY (S5-S9).

Razón: UPDATE correctivo. Tool names divergen post-redesign S5-S9.

---

### Utility verdicts

Tabla de audit completa. Cobertura: 100% secciones H2 de SKILL.md + 4 reference files.

| Sección/Archivo | Verdict | Razón |
|---|---|---|
| SKILL.md `## §0 — Anti-duplication cardinal (read first)` | KEEP | Vigente. Refleja PR-1 PI-1.1 hotfix 2026-05-01. Inventario compartido válido y actualizado. |
| SKILL.md `## §3 — NO se toca` | UPDATE | `BufferService` → `SmartBufferService` (clase real). `agent_state_checkpoint` → `agent_state_checkpoints` (plural). Aplicado. |
| SKILL.md `## Antes de codear (orden estricto)` | KEEP | Vigente. 4 pasos (trazas, plan, grep, ambiguo→preguntar) siguen siendo correctos. |
| SKILL.md `## Anti-patterns (cerrados)` | KEEP | 13 anti-patterns vigentes. DeepSeek v4 aliases correctos. Tier pricing 200k confirmado. |
| SKILL.md `## Decisiones cross-fase no obvias` | KEEP | 10 decisiones vigentes. Verificadas contra código vivo. BaseAgentCallbackHandler, compose_system_prompt, model_pricing_snapshot, dual-write, LLM_ROLE_BY_SITE, tenant isolation, redirect_slashes, PII WONT-FIX, typing_simulation_cpm, voseo tenant. |
| SKILL.md `## Surfaces compartidas con copilot (consumers shared/agent_observability)` | NEW (ADDED) | Sección nueva requerida por AD3. Cubre 13 subsistemas confirmados por grep. |
| SKILL.md `## Decisiones cardinales últimos 60 días` | NEW (ADDED) | Sección nueva requerida por AD3+Q2. 10 decisiones con fechas y fuentes. |
| SKILL.md `## SSoT vivos` | KEEP | 8 paths todos verificados. `mv_daily_llm_cost_per_tenant_v2` vigente. `SalesAgentJudge` existe. `sales_agent_routing_log` existe. |
| SKILL.md `## Checklist pre-commit "senior dev pass"` | KEEP | 10 items vigentes. Coherentes con reglas actuales. |
| SKILL.md `## Glossary` | KEEP | Términos vigentes. Dual-write, ratchet, Stranger Fig, Tier pricing, §3 — todos activos. |
| SKILL.md `## Pointers` | KEEP | Paths docs/domains/sales-agent/redesign-2026-04/ verificados. 4 de 5 paths existen. `01-master-plan.md` existe (extra al listado). |
| SKILL.md `## Budget + Outbound Gating (PI-1 S0 PR-2)` | KEEP | Contenido vigente. CONTRACT.md archivado verificado en `docs/archive/2026/legacy-pis/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-2-billing-and-compliance/CONTRACT.md`. Pointer al archivo archivado correcto. |
| SKILL.md `## Project invariants (read on demand)` | KEEP | Una línea, pointer vigente a `references/sales-agent-brand-voice.md`. |
| references/sales-agent-brand-voice.md | KEEP | Actualizado recientemente (2026-05-04). Compiler v2 (6 bloques → ASÍ HABLAS/ASÍ NO confirmado). Slot architecture vigente. Tests obligatorios listados. Voice fidelity grader (Fase C) marcado como futuro. Voseo tenant feature — alineado con SKILL.md. |
| references/humanization-rules.md | UPDATE | `identity.voice_tone` + `identity.communication_style` DEPRECATED. Jinja template actualizado para referenciar `compiled_brand_voice` slot 5. Nota inline agregada. Fallback personas y 9 técnicas de humanización vigentes sin cambio. |
| references/conversation-stages.md | UPDATE | Value levels en pseudocódigo Stage 5 Closing actualizados (nombres enum correctos). Tool names actualizados (`create_booking_link` vs `book_appointment`). Nota de vigencia agregada. Resto del documento (stages 0-6, follow-up, cross-channel identity) vigente sin cambio. |
| references/tool-patterns.md | UPDATE | Nota de vigencia al header: divergencia entre nombres conceptuales y TOOL_REGISTRY registrado (S5-S9). Contenido conceptual (LangGraph integration pattern, tool specifications, selection logic, priority) vigente como referencia de diseño. |

---

## Contradictions detected

### Análisis de contradicciones (política híbrida Q3)

**Contradicción candidata 1 — voseo tenant respetado**

SKILL.md `## Decisiones cross-fase no obvias` dice: "Voz del agente — voseo del tenant respetado — `.claude/rules/spanish-text.md` NO aplica al output del agente. Voseo del tenant es feature."

`references/sales-agent-brand-voice.md` dice: "El sales_agent habla con la voz del tenant. Si el tenant clona desde un chat con voseo argentino, el `system_instruction` resultante respeta voseo. Es feature, no bug."

**Resolución: NO es contradicción** — ambos dicen lo mismo. SKILL.md y reference coinciden: voseo del tenant es feature. Coherente con `.claude/rules/spanish-text.md` (excepción sales_agent output documentada). Auto-resuelto.

**Contradicción candidata 2 — channels/format.py vs format_for_channel.py**

SKILL.md SSoT vivos cita `shared/agent_observability/channels/format.py::CHANNEL_FORMATS + get_channel_format`.

Anti-duplication.md inventario lista `format_for_channel` como shared pattern.

**Resolución: NO es contradicción** — son dos archivos distintos con roles distintos: `format.py` = SSoT del registry (CHANNEL_FORMATS dict + get_channel_format function); `format_for_channel.py` = LangChain `@tool` wrapper determinístico (S5, exportable como tool para specialists). SKILL.md cita correctamente el SSoT del registro. Sección nueva "Surfaces compartidas" documenta ambos. Auto-resuelto.

**Contradicción candidata 3 — PROHIBIDO voseo en skill vs voseo en referencias**

humanization-rules.md cita "voseo" como término técnico al hablar del tenant voice (no como voseo en user-facing strings). El test `test_skill_no_self_contradiction` verifica pattern `PROHIBIDO.*voseo` — este pattern NO aparece en SKILL.md ni references (donde sí aparece es en `.claude/rules/spanish-text.md` que prohíbe voseo en UI propio). Auto-resuelto: no hay contradicción in-skill.

**Escalaciones a Chris: CERO** — ninguna contradicción vs `.claude/rules/*.md` externos o vs otros skills fue detectada. Política híbrida Q3: sin escalaciones pendientes.

---

## Surfaces compartidas (raw scan output)

Ver sección Pasada 2 arriba para output verbatim del grep.

**Resumen deduplicado de consumidores confirmados:**

```
shared.agent_observability.recording.base_callback_handler    → callback_handler.py
shared.agent_observability.recording.turn_envelope             → turn_envelope.py (BaseObservabilityContext)
shared.agent_observability.cost.fx_resolver                   → factory.py + turn_envelope.py
shared.agent_observability.pricing.resolver                   → factory.py + turn_envelope.py
shared.agent_observability.persistence.pricing_snapshot_repo  → factory.py
shared.agent_observability.persistence.tenant_billing_config  → factory.py
shared.agent_observability.channels.format                    → compose.py + output_manager.py
shared.agent_observability.recording.sanitization             → judge.py + subscribers.py
shared.agent_observability.registry                           → observability/__init__.py
shared.billing.llm_guards + budget_guard                      → conversation_pipeline.py + outbound_orchestrator.py
```

**NOT wired (confirmed absent):** `ComplianceService`, `intent_detector` (not imported in sales_agent).

---

## Surface drift

No se detectaron violaciones de anti-patterns en código live. No se encontraron mirrors de shared abstractions en sales_agent. Scan grep confirmó zero cross-module imports copilot→sales_agent.

No hay stories de refactor pendientes a escalar por este audit.

---

## Iteration log

| Iteración | Acción | Resultado |
|---|---|---|
| 1 | Test file creado (RED): 4/10 tests fallaron | RED confirmado: missing sections, impl-log, shared consumers |
| 2 | Pasada 1 (paths resolve): 20 paths verificados, 5 correcciones aplicadas | SKILL.md + 3 references actualizados |
| 3 | Pasada 2 (surfaces): grep scan, nueva sección "Surfaces compartidas" agregada a SKILL.md | 13 bullets documentados |
| 4 | Pasada 3 (cardinales): learnings.md + git log 60d + archive stories escaneados | Nueva sección "Decisiones cardinales" 10 bullets |
| 5 | Pasada 4 (utility verdicts): 100% cobertura H2 + 4 references | Tabla 16 entradas |
| 6 | T-1-impl-log.md creado con 4 H3 obligatorios | Log completo |
| 7 | Tests run GREEN: todos 10/10 pass | state: developed |
