# F8 — Routing + Cost optimization

**Pre-req:** F2-F7 cerradas (necesita base estable para medir).
**Sprints estimados:** 1.
**Valor entregado:** latencia primer token ↓, cost / conversación ↓, cache hit rate system prompt ↑.

---

## §1 Objetivo

1. Implementar `LLMClassifier` fallback (rule classifier sigue siendo first-line).
2. Reordenar system prompt para maximizar prompt cache hit (stable prefix first, dynamic last).
3. Eliminar ReAct legacy (post-F2 estable, ya no necesario).
4. Eliminar dual SSE (legacy + v2) → solo v2.
5. Telemetry analysis 30 días post-deploy → re-tune rules.

---

## §2 Pre-lectura específica

- `copilot-refactor-spec.md §1` (model router 4 tiers).
- `learnings/F2-*.md` (Deep Agent harness).
- Trace recorder + `copilot_routing_log` table.

---

## §3 Research mandate (abril 2026)

Queries WebSearch:

- `OpenAI prompt caching prefix strategy 2026 best practices`
- `LangGraph cache hit rate optimization 2026`
- `LLM classifier fallback intent detection 2026`

Productos:

- Confirmar prefix cache rules (≥1024 tokens) versión OpenAI vigente.
- Patrón LLMClassifier eficiente (NANO + structured output).

---

## §4 Lo que NO se toca

- 4 tiers (NANO/MINI/REASONING/HEAVY) — solo se afinan reglas.
- Trace recorder schema.

---

## §5 Deliverables

### 5.1 LLMClassifier

`backend/src/modules/copilot/application/router/classifiers/llm_classifier.py`:

- NANO call con structured output `{tier: "...", confidence: 0..1, reason: "..."}`.
- Solo invoked si rule classifier confidence < threshold.

### 5.2 System prompt reorder (cache-friendly)

Order final:

1. Static system instructions (Claude Code-style).
2. Tools schema (estable).
3. Brand lighthouse (cambia raro).
4. Editable catalog (estable por sesión).
5. Active providers list (estable por sesión).
6. — fin del prefix cacheable —
7. Studio snapshot (cambia per turn).
8. Workflow state (cambia per turn).
9. Inspirations table (cambia per turn).
10. Conversation messages.

Verificar cache hit rate via OpenAI usage stats.

### 5.3 Eliminar ReAct legacy

- Borrar `agent_node` ReAct path.
- Feature flag `COPILOT_DEEP_AGENT_V2` → siempre on, eliminar flag.

### 5.4 Eliminar dual SSE

- Eliminar emit legacy `text_chunk`. Solo v2.
- Confirmar FE no usa legacy (compat ya migrado).

### 5.5 Routing telemetry analysis

Admin Streamlit `/admin/copilot/routing`:

- Distribución tiers (% por tier).
- Avg cost / conversation.
- Latency p50/p95 por tier.
- Misroute samples (manual flag option).

### 5.6 Re-tune rules

Basado en 30 días telemetry:

- Ajustar keywords (abril neutro español).
- Promover/demover tier en casos identificados.

---

## §6 Quality gates

- Latencia p50 ≤800ms / p95 ≤2000ms.
- Cache hit rate ≥60%.
- Cost / conversación ≤ $0.05 promedio.
- `/test-backend` + `/test-frontend` verdes.

---

## §7 Definición de hecho

- [ ] LLMClassifier funcional.
- [ ] System prompt reordenado, cache hit medido.
- [ ] ReAct legacy eliminado.
- [ ] Dual SSE eliminado.
- [ ] Admin observability page.
- [ ] Métricas target alcanzadas.
- [ ] `learnings/F8-routing.md` + `prompts/F9-start.md`.
