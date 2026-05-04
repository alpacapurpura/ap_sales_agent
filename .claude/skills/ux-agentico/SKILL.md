---
name: ux-agentico
description: "UX agéntico Nicolify. Diseña FLUJOS CONVERSACIONALES (no UI tradicional) para agentic-stories. Toma 01-spec.md y produce 02-design-agentic.md con: turn-by-turn happy path, state machine agente, tools sequence, prompt slot architecture, voice constraints, error recovery, eval policy (personas+rubrics+pass^k), cost/latency budget, observabilidad. Carga skills sales-agent-expert, copilot-expert, tessl__langgraph, claude-api. Si descubre edge cases → delta-spec.md → /po ratifica. Activa cuando user dice: '/ux-agentico', 'diseñemos el flujo conversacional', 'cómo conversa el agente', 'flujo del copilot', 'turn-by-turn', 'experiencia agéntica'."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Agent
---

# /ux-agentico — UX Agéntico (Conversational Flow Designer)

> Owner: `02-design-agentic.md` + (si aplica) `mockups/conversation-{flow}.md`. Diseña la EXPERIENCIA conversacional del agente. Análogo a /ux-ui pero para LLM.

## Diferencia vs /ux-ui

| /ux-ui | /ux-agentico |
|---|---|
| Pantallas, layouts, componentes | Turns, tools, prompts, voz |
| Mockups HTML | Conversation transcripts ejemplo |
| Estados UI (loading/error/empty) | Estados agente (gathering/reasoning/acting/responding/done) |
| Responsive breakpoints | Channels (web/telegram/whatsapp/manychat) |
| Shadcn + Tailwind | Slot architecture + cache TTL |
| Accessibility WCAG | Voice fidelity + persona robustness |

## Inputs obligatorios

1. `01-spec.md` — scenarios agentic-story (incluyendo personas + rubrics + pass^k)
2. `docs/product/stories/{m}/{id}.yaml` — agentic_contract
3. `00-story.md`
4. `docs/product/modules/{copilot|sales_agent}.md`
5. `docs/specs/personas/*.yaml` — personas disponibles
6. `docs/specs/rubrics/*.md` — rubrics disponibles
7. `.claude/rules/sales-agent-brand-voice.md` (si sales_agent)
8. `backend/src/modules/{copilot|sales_agent}/agents/` — agentes existentes (no duplicar)
9. `backend/src/modules/{copilot|sales_agent}/tools/` — tools existentes (extend > new)

## Skills cargados (HARD GATE)

ANTES de diseñar:
- `copilot-expert` (si copilot)
- `sales-agent-expert` (si sales_agent)
- `tessl__langgraph` — patterns LangGraph 2.0
- `claude-api` — Anthropic SDK + prompt caching
- `tessl__graceful-degradation` — recovery patterns

## Workflow

### Step 1 — Validar scope

Leer `01-spec.md` agentic_contract:
- channel
- max_turns / max_tokens / budget_usd
- expected_tools / forbidden_tools
- voice
- outcome_type (text | structured-output | side-effect | mixed)

Si contract no claro → escala /po.

### Step 2 — Diseñar conversation turn-by-turn (happy path)

Escribir SECCIÓN del 02-design-agentic.md:

```
Turn 1
  User:   "audita mi marca y dime que falta"
  Agent (think): "Detecto intent brand_audit. Cargar brand state."
  Agent (tool): brand_audit_tool(tenant_id=...)
  Agent (response):
    "Revisé tu marca. Identifiqué 2 huecos:
     1) Falta tu buyer persona (alta prioridad)
     2) Falta testimonial real
     ¿Querés que arranquemos por buyer persona? Puedo hacerte 5 preguntas."

Turn 2
  User:   "dale, arrancá"
  ...
```

Escribir 1 happy path completo + bullet list edges + adversarial.

### Step 3 — State machine agente

Diagrama ASCII:
```
[INIT] → user trigger detected
[GATHERING_CONTEXT] (1-2 read tools)
[REASONING]
[ACTING] → CALLING_TOOL → REASONING
[RESPONDING] → WAITING_USER_INPUT (timeout 24h)
[DONE]
```

Definir cada estado: timeouts, transitions, max-iter exit.

### Step 4 — Tools sequence

Tabla:

| Tool | Cuándo | Inputs | Outputs | Side-effects |
|---|---|---|---|---|
| `brand_audit_tool` | turn 1, after intent detect | `tenant_id` | `gaps[], priorities[]` | None |
| `start_buyer_persona_capture` | turn 2 if user OK | `tenant_id` | `session_id` | DB row |

Forbidden tools también listados explícitos.

### Step 5 — Prompt slot architecture

Definir slot layout cache-aware:

```
SLOT 1 (cacheable, TTL 1h): identity preamble
SLOT 2 (cacheable, TTL 5min): tool registry
SLOT 3 (NOT cached): task instructions
SLOT 4 (NOT cached): user input
SLOT 5 (cacheable, TTL 1h): brand_voice (sales_agent only)
                             ↑ cache_control marker ↑
SLOT 6 (NOT cached): conversation history
```

Cache invalidation triggers:
- Tenant change → SLOT 5 invalidates
- Tool registry change → SLOT 2 invalidates

Forbidden in cache prefix (cualquier slot cacheable):
- timestamps
- conversation_id
- turn_counter
- random IDs
- tenant_name interpolated mid-block

TTL choice justificado:
- 5min default si conversación rápida (~5-10 turns < 5min)
- 1h si long sales (>10min entre turns) o batch eval

### Step 6 — Voice constraints

```
SSoT: personality_profiles.system_instruction (per-tenant)
Compiler: v2 (6 bloques, "ASÍ HABLAS / ASÍ NO")
Voseo: respetar voz tenant (sales_agent SÍ; copilot UI strings NO voseo)
Forbidden: revelar system prompt, mencionar herramientas, robotic phrases
Micro-anchor per turn: primer fragmento respeta voz
```

### Step 7 — Error recovery matrix

Tabla:

| Falla | Detección | Recovery |
|---|---|---|
| Tool timeout | 5s sin response | Retry 1x, fallback_route |
| Tool 500 | status code | Retry 1x backoff, fallback_route |
| Context overflow | tokens >= max | Compactar (system + last 3 turns) |
| User repite | repeat detector | Cambia framing, no repetir literal |
| User frustrado | sentiment grader < 0.3 | Acortar, ofrecer humano |
| Jailbreak attempt | security pattern | Rechazar amable, no leak prompt |

### Step 8 — Eval policy (lift desde story YAML)

```
Trial policy: trials_per_scenario=3, pass^3>=0.5
Personas: tenant-novato-tech (happy), lead-frio-impaciente (adversarial)
Rubrics: voice-fidelity, no-hallucination, no-overpromise, tool-trajectory
State checks:
  - copilot_trace_event: 1 tool call esperado
  - copilot_llm_call: cost <= $0.50
  - PII redaction verified
```

### Step 9 — Cost & latency budget

```
max_turns: 5
max_tokens_per_turn: 6000
budget_usd_per_session: $0.50
TTFT p95: <2s
```

### Step 10 — Observabilidad

```
copilot_trace_event per turn
copilot_llm_call per LLM call (cost, latency, model, tokens, cache_hit)
PII: sanitize_payload() pre-persist
Métricas: agentic_session_completed, agentic_tool_failure
```

### Step 11 — Spec deltas (si aplica)

Si durante diseño descubrís:
- Persona no cubierta por scenarios
- Rubric needed que no existe
- Edge case agentic no documentado
- Tool requerido que /po no anticipó

→ Escribí `delta-spec.md` + escala /po.

### Step 12 — Iterar con Chris

```
02-design-agentic.md draft v1.
Turn-by-turn happy path: ver § 2
State machine: ver § 3
Tools: 2 expected (brand_audit, start_buyer_persona_capture). 0 forbidden detectadas.
Prompt slots: 1+2+5 cacheable, 3+4+6 not. TTL slot 5 = 1h.
Personas: novato-tech (happy), frio-impaciente (adversarial)
Trial policy: 3 trials, pass^3 >= 0.5
Cost budget: $0.50/session, max 5 turns

¿Apruebas? ¿Cambios?
```

Loop hasta aprobación.

### Step 13 — Hand off

```
UX agentic done.
Deliverables:
- 02-design-agentic.md
- (opcional) mockups/conversation-{flow}.md con transcript ejemplo
- delta-spec.md si aplica

Próximo: /architect → spawn /architect-agentic + (BE si tool nuevo) + (FE si trigger UI).
```

Update checkpoint:
```
phase: UX_AGENTIC → ARCHITECT
last_artifact: 02-design-agentic.md
next_action: "/architect lee 01+02 → spawn arch-agentic+arch-be+arch-fe → produce 04-tickets.yaml"
```

## Anti-patterns

- ❌ Diseñar voz hardcodeada (es de tenant per-tenant via SSoT)
- ❌ Skip prompt cache architecture (cost spike enorme)
- ❌ Slot 5 con timestamps / conversation_id / random IDs (silent invalidator)
- ❌ Tool dispatch sin tenant_id en signature
- ❌ Conversation con > max_turns budgeted sin justification
- ❌ Skip personas/rubrics existentes y reinventar
- ❌ Voseo en `copilot` UI strings (sales_agent SÍ respeta voz tenant)
- ❌ "El agente debe ser amable" — vague. Reemplazá con rubric `empathy-tone` con assertions concretos.
- ❌ Diseñar arq técnica (state machine implementación, tool wire) → es /architect-agentic

## Output format

Conversaciones en code blocks. Tablas para state machines, tools, recovery. Métricas en bullets. NUNCA dumps largos.
