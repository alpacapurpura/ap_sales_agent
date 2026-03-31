---
name: sales-agent-expert
description: "Use when modifying, improving, or debugging the sales_agent module: LangGraph graph redesign, conversation prompts, tool implementation, multi-channel adaptation, closing flows, or sales conversion. Triggers: 'sales agent', 'mejorar ventas', 'no cierra', 'suena robótico', 'agregar tool al agente', 'flujo de ventas', 'prompt del agente', 'agente de ventas', 'no suena humano', 'calificación', 'cierre de ventas', 'scheduling tool', 'payment tool'."
---

# Sales Agent Expert

Expert skill for building human-sounding, high-converting conversational sales agents on LangGraph. Covers architecture (graph, state, tools, memory) and conversation craft (stages, psychology, humanization, voice).

**Module:** `backend/src/modules/sales_agent/`
**Runtime:** Docker (`visionarias_brain_dev`)
**Graph framework:** LangGraph (Python)

## Current → Target File Mapping

| Current File | Target |
|-------------|--------|
| `orchestrator/state.py` | Enhanced `SalesAgentState` with checkpointer |
| `orchestrator/graph.py` | `classify_intent → determine_stage → select_strategy → [generate\|tools\|escalate] → format_output` |
| `agents/sales/graph.py` | LLM + ToolNode with loop-back pattern |
| `agents/sales/nodes.py` | Separate nodes per concern (classify, stage, strategy, generate, format) |
| `templates/specialist_*.j2` | Per-stage prompts with humanization rules baked in |
| `templates/supervisor_routing.j2` | `classify_intent` prompt + `determine_stage` prompt (2 focused prompts) |
| `templates/agent_identity.j2` | Enhanced identity with voice profile section |
| `services/semantic_router.py` | Keep cosine similarity but add intent scoring to state |
| `external/output_manager.py` | Channel-aware formatter with strict constraints |
| (NEW) `tools/` | New directory with `@tool` decorated functions |

## Message Flow (Channel → Agent → Channel)

```
Channel (IG/WA/TG) → Webhook → Channel Adapter → normalize_payload()
  → SmartBufferService (Redis debounce) → semantic completeness check
  → ChatOrchestrator.process_chat_flow()
    → CRM: lookup/create customer
    → TenantKnowledgeBuilder: build agent_identity
    → SemanticRouter: detect_intent
    → LangGraph agent_app.ainvoke(state)
      → [classify_intent → determine_stage → select_strategy → generate/tool → format_output]
    → Extract response from state["messages"][-1]
    → AuditRepository: log assistant message
  → OutputManager.process_response()
    → Parse JSON array → chunk into bubbles
    → For each bubble: typing simulation → send via channel_adapter
```

When a tool returns a result (e.g., payment link, booking confirmation), `generate` incorporates it into a human-readable response, then `format_output` enforces channel constraints.

## SOP — Workflow

Before changing code, understand the current state:

1. **Diagnose:** Read current graph (`agents/sales/graph.py`), nodes (`nodes.py`), state (`state.py`), prompts (`templates/*.j2`), and identify which problem you're solving.
2. **Classify the change:** Architecture (graph/state/tools) vs. Conversation (prompts/stages/voice). Use the appropriate reference.
3. **Design:** Propose changes with the user. Sales agent changes affect real conversations — no cowboy coding.
4. **Implement:** Follow patterns below. Always work inside Docker.
5. **Test:** Verify with conversation simulation before deploying.

## Architecture Principles

### Graph Design — The Correct Pattern

The current graph is too rigid (supervisor → specialist → END, single turn). The correct pattern for a sales agent:

```
START → classify_intent → determine_stage → select_strategy
                                               ↓
                                    ┌──────────┼──────────┐
                                    ↓          ↓          ↓
                              generate_msg  use_tool   escalate
                                    ↓          ↓          ↓
                                    └──────────┼──────────┘
                                               ↓
                                         format_output → END
```

**Key differences from current:**
- `classify_intent` and `determine_stage` are SEPARATE nodes (not one supervisor deciding everything)
- `select_strategy` chooses HOW to respond (generate text vs. use a tool vs. escalate)
- `use_tool` is a first-class node: schedule, payment link, product recommendation, campaign detection
- `format_output` enforces message length/chunking/channel rules AFTER generation
- Tools can loop back to `generate_msg` to communicate results

### State Design — Store Raw Data, Not Formatted Text

```python
class SalesAgentState(TypedDict):
    messages: Annotated[list, add_messages]  # Full conversation (LangGraph managed)

    # Intent & Stage (persisted between turns via checkpointer)
    current_stage: str          # "greeting" | "discovery" | "presentation" | "negotiation" | "closing" | "post_sale"
    detected_intent: str        # From semantic router
    intent_confidence: float    # Score from router
    buying_signals_count: int   # Accumulates across turns

    # Lead Intelligence (raw data, not formatted)
    lead_data: dict             # {"name": "Ana", "business": "coaching", "pain": "no clients"}
    qualification_score: int    # 0-100 based on avatar match + financial capacity
    objections_raised: list     # ["price", "time"] — track what they've objected to

    # Product Context (which offer, what close type)
    target_offer_id: str        # Which offer the conversation is about
    close_strategy: str         # "direct_payment" | "schedule_meeting" | "send_link" | "application"

    # Conversation Meta
    messages_this_session: int  # Counter — prevent over-questioning
    questions_asked_consecutively: int  # Reset when prospect responds substantively
    last_tool_used: str         # Prevent tool spam

    # Identity & Config
    agent_identity: str
    channel_type: str           # "instagram" | "whatsapp" | "telegram" | "messenger" | "tiktok"
    tenant_id: UUID
```

**Critical rules:**
- Use a **checkpointer** (Redis) for state persistence between turns — NEVER rebuild state from scratch each turn
- `current_stage` is PERSISTED, not always reset to "rapport"
- `buying_signals_count` ACCUMULATES — when it hits threshold (3+), auto-route to closer

### Tool System — First-Class Citizens

Tools are NOT optional. They are the primary way the agent ACTS, not just talks. See `references/tool-patterns.md` for implementation details.

**Required tools:**
| Tool | Purpose | When to Fire |
|------|---------|-------------|
| `check_schedule` | Query tenant's availability | User asks about meetings/calls |
| `book_appointment` | Create a booking | User confirms date/time |
| `send_payment_link` | Deliver checkout URL | User ready to buy (buying signals ≥ 3) |
| `recommend_product` | Suggest best-fit offer from catalog | User's need doesn't match current offer |
| `detect_campaign_origin` | Check if user came from an ad campaign | First message / new session |
| `lookup_customer` | Cross-channel identity resolution | Every new conversation |
| `escalate_to_human` | Hand off to real person | Safety trigger / complex situation |

### Memory — Use LangGraph's Native Memory

**Short-term (thread-level):** Use `RedisSaver` checkpointer. State persists across turns within a conversation thread.

**Long-term (cross-thread):** Use LangGraph's `Store` with semantic search. Store: customer preferences, past purchases, conversation summaries, objection patterns.

**Session detection:** 6-hour timeout. Use `thread_id = f"{tenant_id}:{customer_profile_id}"` so the SAME customer on different channels shares context.

## Conversation Stages

Seven stages. Each has entry conditions, exit conditions, max messages, and behavioral rules. See `references/conversation-stages.md` for full detail.

| # | Stage | Goal | Max Msgs | Key Rule |
|---|-------|------|----------|----------|
| 0 | **Greeting** | Warm start, detect origin | 1-2 | If from campaign, skip to relevant offer |
| 1 | **Discovery** | Understand situation + pain | 3-5 | ONE question per message. SPIN sequence. |
| 2 | **Qualification** | Assess fit + capacity | 2-3 | Match against avatar. If no fit, suggest alternatives. |
| 3 | **Presentation** | Show the right offer | 2-4 | Connect features to THEIR specific pain. Short. |
| 4 | **Negotiation** | Handle objections | As needed | Objections = buying signals. Aikido framework. |
| 5 | **Closing** | Drive to action (tool) | 1-3 | Use the RIGHT tool for the offer type. Don't ask, DO. |
| 6 | **Post-Sale** | Confirm + onboard | 1-2 | Deliver access/next steps. Set expectations. |

**Stage transitions are DRIVEN BY SIGNALS, not by message count.** If the user shows buying intent in message 2, skip to closing. If they have objections in discovery, handle them there — don't wait for "negotiation stage".

### Close Strategy Per Product Type

The offer's `archetype` + `value_level` + `checkout_page_url` / `calendar_type_id` determine the close:

| Value Level | Close Strategy | Tool |
|-------------|---------------|------|
| Level 0 (Free) | Send link directly, no friction | `send_payment_link` (free checkout) |
| Level 1 (Low ticket) | Send payment link after quick value pitch | `send_payment_link` |
| Level 2 (Mid ticket) | Brief qualification → payment link OR meeting | `send_payment_link` or `book_appointment` |
| Level 3+ (High ticket) | MUST qualify → schedule meeting | `book_appointment` |
| Recurring (Level 4) | Explain value → schedule strategy call | `book_appointment` |

**If offer has `calendar_type_id` → meeting required. If only `checkout_page_url` → direct payment. If both → agent decides based on value level.**

## Humanization Rules (Quick Reference)

Full details in `references/humanization-rules.md`.

### The 5 Anti-Patterns (NEVER do these)
1. **Interview mode** — asking 3+ questions in a row without giving value
2. **Wall of text** — messages longer than 3 sentences in chat
3. **Bullet lists in chat** — nobody talks like that
4. **Ignoring emotions** — prospect says "estoy frustrada" and agent asks about budget
5. **Announcing stages** — "Ahora voy a calificarte" / "Pasemos a la fase de cierre"

### Message Format Rules Per Channel
| Channel | Max length | Style | Emoji |
|---------|-----------|-------|-------|
| Instagram DM | 2-3 sentences, < 300 chars | Ultra casual, direct | 1-2 max |
| WhatsApp | 3-4 sentences | Conversational, warm | Moderate |
| Telegram | 3-4 sentences | Semi-casual | Optional |
| Messenger | 2-3 sentences | Casual like IG | 1-2 max |
| TikTok DM | 1-2 sentences, very short | Gen-Z casual | Depends on brand |

### The Golden Rule of Sales Chat
**Give before you ask.** Every question should be preceded by a value statement, validation, or insight.

```
BAD:  "¿A qué te dedicas?"
GOOD: "Me encanta que hayas llegado hasta aquí. Cuéntame, ¿en qué área trabajas?"

BAD:  "¿Cuál es tu presupuesto?"
GOOD: "Tenemos opciones que se adaptan a diferentes situaciones. ¿Qué rango de inversión manejas para esto?"

BAD:  "¿Quieres agendar una llamada?"
GOOD: "Creo que una llamada rápida de 15 min te va a aclarar todo. ¿Te funciona esta semana?"
```

## Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| **Response Rate** | > 90% | |
| **Engagement Depth** | 6-15 msgs | Varies by product |
| **Qualification Rate** | > 30% | |
| **Meeting Book Rate** | > 40% | High ticket only |
| **Conversion Rate** | > 10% low ticket, > 5% high ticket | |
| **Time to Close** | < 24h low, < 72h high | |
| **Drop-off Point** | Identify & fix | Primary diagnostic signal — stage where conversations die |
| **Human Escalation Rate** | < 15% | |
| **Sentiment Score** | > 80% positive | |

## Intent Detection — Semantic Router

The existing `SemanticRouter` (`services/semantic_router.py`) uses cosine similarity with `paraphrase-multilingual-MiniLM-L12-v2`. Enhancements needed:

1. **Add soft buying signals** to `SYSTEM_ROUTES`: logistics questions post-price ("¿cuándo empieza?", "¿qué incluye?") should score as buying signals, not just "quiero comprar"
2. **Accumulate intent scores** in state: `buying_signals_count` increments on each detected buying/schedule signal, even below threshold
3. **Tenant routes from offer objections** already work via `SemanticRouter.register_tenant_routes()` — keep this
4. **When adding new intents**: add anchor phrases to `SYSTEM_ROUTES` dict, minimum 4-6 phrases per intent for reliable cosine matching
5. **Threshold tuning**: current 0.65 is good for explicit intents; for soft signals, use 0.50 with lower weight in `buying_signals_count`

## References (read when implementing specific changes)

- **Stage behavior + closing flows:** `references/conversation-stages.md`
- **Message formatting + voice matching:** `references/humanization-rules.md`
- **Tool implementation patterns:** `references/tool-patterns.md`

## Checklist — Before Deploying Any Sales Agent Change

- [ ] Prompts are in `.j2` templates (NEVER hardcode in Python)
- [ ] State changes are persisted via checkpointer (not rebuilt per turn)
- [ ] Max 1 question per message in qualifying stages
- [ ] Messages fit channel constraints (see format rules)
- [ ] Tools are implemented for ALL close strategies used by active offers
- [ ] Voice profile is loaded from brand data (not generic)
- [ ] Buying signals trigger stage advancement (not message count)
- [ ] Cross-channel identity works (`lookup_customer` tool)
- [ ] Test with real-sounding conversation (minimum 5 turns)
- [ ] OutputManager chunks are correct (JSON array format)
- [ ] Run backend tests: `docker exec -t visionarias_brain_dev bash -c "cd /app && pytest -x -q --tb=short"`
