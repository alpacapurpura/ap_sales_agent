# 02-design-agentic.md — Template (UX agéntico)

> Owner: `/ux-agentico`. Diseño del flujo conversacional para agentic-story.
> Consume `01-spec.md` + skills (`sales-agent-expert`, `copilot-expert`, `tessl__langgraph`, `claude-api`).
> Si descubre edge cases nuevos → propone delta-spec, /po ratifica.

---
story_id: STORY_ID
type: agentic-story
designer: /ux-agentico
ux_version: 1
last_modified: 2026-05-04T15:00Z
ratified_by_chris: false
links:
  spec: "01-spec.md"
  story_yaml: "../../../../../product/stories/{module}/{story-id}.yaml"
  brand_voice_ssot: ".claude/rules/sales-agent-brand-voice.md"     # solo sales_agent
  rubrics_dir: "../../../../specs/rubrics/"
  personas_dir: "../../../../specs/personas/"
---

## Resumen UX agéntico

[1 párrafo: qué experiencia conversacional se entrega, en qué canal, qué expera el user.]

## Channel + entry points

- **Canal:** web | telegram | whatsapp | manychat | email
- **Trigger:** mensaje libre del user vs. botón de UI vs. webhook
- **Trigger phrases (NLU intent):**
  - "audita mi marca"
  - "qué le falta"
  - "está completa mi oferta"
- **Fallback determinístico** (cuando LLM falla): ruta hardcoded a `[/path/handler]`

## Conversación turn-by-turn (happy path)

```
Turn 1
  User:   "audita mi marca y dime que falta"
  Agent (think): "Detecto intent brand_audit. Cargar brand state."
  Agent (tool): brand_audit_tool(tenant_id=...)
  Agent (response):
    "Revisé tu marca. Identifiqué 2 huecos:
     1) Falta tu buyer persona (alta prioridad — sin esto el SDR adivina).
     2) Falta tu testimonial o caso real.
     ¿Querés que arranquemos por el buyer persona? Puedo hacerte 5 preguntas."

Turn 2
  User:   "dale, arrancá"
  Agent (response):
    "Listo. Pregunta 1: ¿quién es tu cliente ideal?
     Si tenés un cliente real reciente, contame de él."
  Agent (tool): start_buyer_persona_capture(...)
```

## State machine del agente

```
[INIT]
  ↓ user trigger detected
[GATHERING_CONTEXT] (puede llamar 1-2 read tools)
  ↓
[REASONING]
  ↓
[ACTING]
  ├→ [CALLING_TOOL] (1 tool)
  │   ↓ result
  │   → REASONING
  ↓
[RESPONDING]
  ├→ [WAITING_USER_INPUT]
  │   ↓ user reply
  │   → REASONING
  ↓
[DONE]
```

- **Estados con timeout** (agent espera user > N min):
  - `WAITING_USER_INPUT` timeout 24h → escalar fuera del turn (campaña drip si aplica)

## Tools que el agent debe usar

| Tool | Cuándo | Inputs | Outputs | Side-effects |
|---|---|---|---|---|
| `brand_audit_tool` | Turn 1, después detect intent | `tenant_id` | `gaps: [str]`, `priorities: [int]` | None |
| `start_buyer_persona_capture` | Turn 2 si user OK | `tenant_id` | session_id | DB row started |

**Forbidden tools:**
- `send_email`, `schedule_meeting` (no aplica este flow)

## Prompt slot architecture

```
SYSTEM PROMPT (cacheado, slot 1, TTL 1h)
  ├─ identity preamble (nicolify_role, version)
  ├─ brand_voice (slot 5, cacheado, swap on tenant change)
  ├─ tool registry (slot 2, cacheado, regen on tool change)
  ├─ task-specific instructions (slot 3, NOT cached)
  └─ user input (slot 4, NOT cached)
```

- **Cache TTL:** 5min para slots 1-2, 1h para slot 5 (brand voice)
- **Cache invalidation triggers:** tenant change (slot 5), tool registry change (slot 2)

## Voice constraints

- **SSoT:** `personality_profiles.system_instruction` del tenant (compiler v2, 6 bloques "ASÍ HABLAS / ASÍ NO")
- **Micro-anchor per turn:** primer fragmento de cada response respeta voz
- **Voseo:** respetar voz tenant (no aplica regla `spanish-text.md`)
- **Forbidden:** revelar system prompt, mencionar herramientas internamente, robotic phrases

## Error recovery

| Falla | Detección | Recovery |
|---|---|---|
| Tool timeout | 5s sin response | Retry 1x; si falla → fallback_route O admite limitación al user |
| Tool 500 | Status code | Retry 1x con backoff; segundo fallo → fallback_route |
| LLM context overflow | tokens >= max_tokens | Compactar history (mantener system + last 3 turns) |
| User repite pregunta | repeat detector | Cambia framing, no repetir respuesta literal |
| User frustrado | sentiment grader < 0.3 | Acortar respuestas, ofrecer escalar a humano si aplica |
| User pregunta jailbreak | security pattern | Rechazar amablemente, no leak system prompt |

## Eval policy

- **Trial policy** (del story YAML):
  - `trials_per_scenario: 3`
  - `pass_k_threshold: 0.5` (pass^3 >= 0.5 para promotion capability→regression)
- **Personas a usar** (de `specs/personas/`):
  - `tenant-novato-tech.yaml` (happy)
  - `lead-frio-impaciente.yaml` (adversarial)
- **Rubrics a aplicar** (de `specs/rubrics/`):
  - `voice-fidelity.md`
  - `no-hallucination.md`
  - `no-overpromise.md`
  - `tool-trajectory.md`
- **State checks:**
  - `copilot_trace_event` registra N tool calls
  - `copilot_llm_call` cost <= budget_usd
  - PII redaction verificada

## Cost & latency budget

- **Max turns:** 5
- **Max tokens per turn:** 6000
- **Budget per session:** $0.50
- **TTFT (time-to-first-token) p95:** < 2s

## Observabilidad

- Recorder: `copilot_trace_event` por turn
- LLM calls: `copilot_llm_call` con `cost_usd`, `latency_ms`, `model`, `tokens_in/out`
- PII: `sanitize_payload(...)` antes de persistir
- Métricas business:
  - `agentic_session_completed_count` con label `outcome`
  - `agentic_tool_failure_count`

## Spec deltas

- [ ] [Delta 1: persona adicional necesaria]

## Próximo paso

`→ /architect lee 01+02 → spawn /architect-agentic + (BE si tool nuevo, FE si trigger UI) en paralelo → produce 03-arch-* y 04-tickets.yaml`
