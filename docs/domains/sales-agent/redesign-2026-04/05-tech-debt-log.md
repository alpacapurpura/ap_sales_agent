# 05 · Tech Debt Log

Registro vivo de deuda técnica detectada durante el redesign. Fases agregan; nadie borra (solo marca FIXED con commit hash).

Formato:
```
## [SEVERITY] Título corto — YYYY-MM-DD — fase detectora — STATUS
- Path: `archivo:linea`
- Descripción: ...
- Impacto: ...
- Acción: FIXED en {commit} / DEFERRED a S{N} / FLAGGED para revisión
- Razón: ...
```

Severities: `CRITICAL` (security/data loss) · `HIGH` (functional bug visible) · `MEDIUM` (frágil, falla rara) · `LOW` (style, cosmético).

Statuses: `FIXED` · `DEFERRED-S{N}` · `FLAGGED` · `WONT-FIX`.

---

## Sembrado inicial (detectados en diagnóstico previo al redesign)

### [HIGH] Sales_agent sin PII sanitization en trace recorder — 2026-04-27 — diagnóstico — DEFERRED-S1
- Path: `backend/src/modules/sales_agent/infrastructure/monitoring/tracing.py`
- Descripción: `@trace_node` persiste `input_state` y `output_state` JSONB sin sanitizar. Mensajes de leads contienen emails, teléfonos, links de pago, posibles DNI/CURP/CUIT.
- Impacto: compliance LATAM (PDPA, LGPD, LFPDPPP). Riesgo legal + breach.
- Acción: DEFERRED-S1 — bloqueante de S1, debe activarse día 1.
- Razón: requiere callback handler para sustituir `@trace_node`. Hacerlo aislado sería parche.

### [HIGH] Sales_agent sin retention policy — 2026-04-27 — diagnóstico — DEFERRED-S1
- Path: `backend/src/modules/sales_agent/infrastructure/models/agent_trace_model.py` y `agent_log_model.py`
- Descripción: tablas `agent_trace_event` y `agent_log` crecen indefinido. No hay worker de purge.
- Impacto: storage cost + GDPR violation (mensajes de leads >1 año sin justificación).
- Acción: DEFERRED-S1 (90d trace) y DEFERRED-S2 (365d llm_call).
- Razón: depende de tablas event-sourced de S1.

### [MEDIUM] Sales_agent prompt sin cache_boundary — 2026-04-27 — diagnóstico — DEFERRED-S3
- Path: `backend/src/modules/sales_agent/application/agents/sales/nodes.py`
- Descripción: Jinja render fresh per turn. Cache hit rate ~0%. Sales_agent es el módulo más caro en LLM.
- Impacto: LLM cost. Estimado 25-30% reducción si hit rate sube a 60%.
- Acción: DEFERRED-S3.
- Razón: necesita CHAT_MODEL_SPEC (S4) y modelos tier definidos.

### [MEDIUM] OutputManager hardcodeado por canal — 2026-04-27 — diagnóstico — DEFERRED-S5
- Path: `backend/src/modules/sales_agent/infrastructure/external/output_manager.py`
- Descripción: chunk size, CPM, emoji policy hardcodeados en if-else por canal. Imposible agregar canal sin tocar el archivo.
- Impacto: extensibilidad. WhatsApp Business API, Webchat con websocket diferente, etc. requieren refactor.
- Acción: DEFERRED-S5.
- Razón: debe extraerse `ChannelFormat` registry compartido con copilot.

### [MEDIUM] Sales_agent identity sin lighthouse — 2026-04-27 — diagnóstico — DEFERRED-S7
- Path: `backend/src/modules/sales_agent/infrastructure/prompts/base.py` (PromptLoader)
- Descripción: `agent_identity` se compone fresh per turn desde `tenant_config` sin caching cross-turn. Brand voice cambia raro pero se re-renderiza siempre.
- Impacto: cache hit + costo. También: NO consume Brand Studio "Estilo Comunicacional" (campo nuevo).
- Acción: DEFERRED-S7.
- Razón: requiere lighthouse pattern + Brand Studio integration.

### [LOW] Cost_usd inline sin pricing snapshot — 2026-04-27 — diagnóstico — DEFERRED-S2
- Path: `backend/src/modules/sales_agent/infrastructure/models/llm_log_model.py`
- Descripción: `cost_usd` calculado al vuelo en `LLMFactory` con dict hardcoded de prices. Sin historical replay.
- Impacto: billing audit imposible si cambia precio del provider y se quiere re-cobrar histórico.
- Acción: DEFERRED-S2.
- Razón: requiere `model_pricing_snapshot` shared (S0/S1).

---

## Cómo agregar entrada (durante fase activa)

1. Detectaste algo durante S{N}.
2. Verificá que es real (test reproductor o evidencia clara).
3. Decidí severity + acción según `04-principles.md §2`.
4. Agregá entrada al final de la sección "Detectados durante S{N}" (creala si no existe).
5. Si FIXED: commit hash en la entrada. Si DEFERRED: target phase clara.
6. NO mover entradas FIXED a sección separada — el log es append-only auditable.
