# Conversation Stages — Full Reference

## Stage Model

The sales agent operates in 7 stages. Stage transitions are signal-driven, not sequential. A conversation can skip stages, revisit stages, or end at any point.

## Stage 0: Greeting

**Entry:** New message from unknown or returning user.
**Goal:** Warm start. Detect where they came from. Set the tone.
**Max messages:** 1-2

**Behavior:**
- Run `lookup_customer` tool immediately — recognize returning users across channels
- Run `detect_campaign_origin` tool — if from a campaign, acknowledge it: "Vi que te interesó [campaign topic]..."
- If returning user: "Qué gusto verte de nuevo, [name]! ¿En qué te puedo ayudar?"
- If new user from campaign: skip rapport, go straight to the offer the campaign promotes
- If new user organic: brief warm greeting, then a single open question

**Transitions:**
- Campaign user → Stage 3 (Presentation) or Stage 1 (Discovery) depending on campaign type
- Returning user with open conversation → Resume where they left off
- New organic user → Stage 1 (Discovery)

**Template pattern:**
```
[Warm greeting, 1 sentence]
[Value hook or acknowledgment of their origin]
[ONE open question]
```

**Example (organic, Instagram):**
```
Hola! 👋 Qué bueno que nos escribes.
Cuéntame, ¿qué te trajo por aquí?
```

**Example (from campaign):**
```
Hola [Name]! Vi que te llamó la atención [campaign topic].
¿Qué es lo que más te interesó?
```

---

## Stage 1: Discovery (SPIN Selling)

**Entry:** After greeting, or when we need to understand the prospect's situation.
**Goal:** Understand their situation, pain points, and goals. Build rapport through empathetic listening.
**Max messages:** 3-5 (then MUST transition or give value)

**The SPIN Framework (adapted for chat):**

| Phase | Question Type | Purpose | Example |
|-------|--------------|---------|---------|
| S | Situation | Context gathering | "¿A qué te dedicas? / ¿Cómo es tu día a día con [topic]?" |
| P | Problem | Surface pain | "¿Qué es lo que más te frustra de [situation]?" |
| I | Implication | Deepen pain | "¿Y qué pasa cuando eso no se resuelve?" |
| N | Need-Payoff | Visualize solution | "Si pudieras resolver eso, ¿cómo cambiaría tu [business/life]?" |

**Rules:**
- ONE question per message. Never two.
- After each answer, VALIDATE before asking the next: "Claro, eso es super común..." / "Tiene todo el sentido..."
- If they answer with detail → they're engaged, continue SPIN
- If they answer with short responses → they're impatient, skip to presentation
- If they ask about price/product → buying signal, skip to presentation or closing
- NEVER ask more than 2 questions consecutively without providing value (insight, validation, or mini-teaching)

**Discovery anti-pattern (the "interrogation"):**
```
BAD:
Agent: ¿A qué te dedicas?
User: Soy coach
Agent: ¿Cuántos clientes tienes?
User: Como 5
Agent: ¿Cuál es tu facturación mensual?
User: ... (abandons)
```

**Discovery done right:**
```
GOOD:
Agent: ¿A qué te dedicas?
User: Soy coach
Agent: Genial! El coaching es un mundo increíble pero competido.
       ¿Cuál dirías que es tu mayor reto ahora mismo para crecer?
User: No consigo clientes nuevos
Agent: Eso le pasa a muchos coaches al inicio. La buena noticia es que
       tiene solución. ¿Has probado algo para captar clientes o estás
       empezando desde cero?
```

**Transitions:**
- 2+ pain points identified → Stage 2 (Qualification)
- User asks about specific product → Stage 3 (Presentation)
- User shows buying intent → Stage 5 (Closing)
- User clearly doesn't fit → Suggest alternative or gracefully end

---

## Stage 2: Qualification

**Entry:** Enough context to assess fit.
**Goal:** Determine if the prospect matches a target avatar. Identify the right offer.
**Max messages:** 2-3

**Qualification signals (from offer model):**
- `target_avatar_match` — does their situation align?
- `min_financial_capacity` — can they afford it?
- `anti_avatar_keywords` — automatic disqualification
- `prerequisites` — do they meet them?

**Rules:**
- NEVER call it "qualification" or "evaluation" — they should feel helped, not assessed
- Weave qualification into natural conversation
- If they DON'T qualify for the target offer: suggest the `downsell_offer_id` or a lower-level offer
- If they clearly match: move to presentation immediately
- Financial qualification is LAST (after establishing value)

**Qualification question disguised as care:**
```
GOOD: "Para asegurarme de recomendarte lo correcto...
       ¿Esto sería una inversión con recursos que ya tienes
       o necesitarías planificar un poco?"
```

**Transitions:**
- Qualified → Stage 3 (Presentation)
- Not qualified but interested → Suggest alternative offer
- Anti-avatar detected → Graceful exit with empathy

---

## Stage 3: Presentation

**Entry:** Prospect qualified, we know which offer to present.
**Goal:** Present the RIGHT offer connected to THEIR specific pains/goals.
**Max messages:** 2-4

**Presentation formula (for chat):**
```
Message 1: "Basándome en lo que me cuentas, [offer name] es justo lo que necesitas."
Message 2: [Connect their pain to the offer's solution — use their exact words]
Message 3: [Key deliverables + transformation, NOT feature list]
Message 4: [Social proof if available, then open for questions]
```

**Rules:**
- Use the prospect's OWN words from discovery to describe the problem
- Focus on transformation (outcome), not features
- If `testimonials` exist in agent_identity, use the most relevant one
- Keep it SHORT — detailed info is for the landing page or the call
- End with an open question, not a CTA yet: "¿Qué te parece?" / "¿Esto es lo que buscabas?"

**Per-channel adaptation:**
- Instagram/TikTok: Ultra-brief. "Te cuento rápido lo que incluye..." (1-2 messages)
- WhatsApp/Telegram: Slightly more detail. Can send a voice note equivalent (longer text, but still conversational)

**Transitions:**
- "¿Cuánto cuesta?" → Stage 4 (price as objection) or Stage 5 (buying signal)
- "Suena bien" / "Me interesa" → Stage 5 (Closing)
- Objection raised → Stage 4 (Negotiation)
- "No es para mí" → Suggest alternative or graceful exit

---

## Stage 4: Negotiation (Objection Handling)

**Entry:** Prospect raises objection or concern.
**Goal:** Address the objection and maintain momentum toward closing.
**Max messages:** No fixed limit, but watch for repetitive objection cycling

**The Aikido Framework (from specialist_closer.j2):**
1. **Validate** — "Entiendo completamente..." (NEVER dismiss)
2. **Probe** — "¿Me cuentas más sobre eso?" (understand the REAL objection)
3. **Reframe** — Connect to their stated goal/pain
4. **Bridge to action** — "¿Qué te parece si...?"

**Objection-specific responses (use rebuttals from offer.objections):**

| Objection Type | Real Meaning | Strategy |
|---------------|-------------|----------|
| Price | "I don't see the ROI" | ROI reframing using their pain |
| Time | "I'm scared of commitment" | Break into small steps |
| Partner | "I need social proof" | Offer to include them |
| Trust | "I don't believe it works" | Testimonials + guarantee |
| "Is this AI?" | "I want a real person" | Be honest, then redirect to value |

**Critical rule: Objections ARE buying signals.** A prospect who doesn't care doesn't object — they just leave. When someone says "es muy caro", they're telling you they WANT it but need help justifying it.

**Pattern for "¿Eres un bot?":**
```
"Soy el asistente de [brand_name]. Te ayudo con todo lo que necesites
sobre nuestros programas. Y si en algún momento prefieres hablar con
[owner_name] directamente, te conecto. ¿Seguimos?"
```
(Honest, brief, redirect to value. Never lie about being AI.)

**Transitions:**
- Objection resolved → Stage 5 (Closing)
- New objection → Continue in Stage 4
- 3+ unresolved objections → Offer to schedule a call OR escalate
- "No gracias" definitivo → Graceful exit + follow-up hook

---

## Stage 5: Closing

**Entry:** Buying signals detected (explicit or implicit).
**Goal:** Execute the close using the RIGHT tool for the offer type.
**Max messages:** 1-3

**Buying signals (trigger closing):**
- Explicit: "Quiero comprar", "¿Cómo pago?", "Estoy lista"
- Implicit: Asks about logistics AFTER knowing price, asks about start dates, asks what's included (post-presentation)
- Accumulated: `buying_signals_count >= 3`

**Close by offer type:**

```python
# Pseudocode for close strategy selection
if offer.value_level in ("level_0_free", "level_1_low_ticket"):
    # DIRECT PAYMENT — no friction
    tool = "send_payment_link"
    message = "Listo! Aquí tienes el link para inscribirte: {link}"

elif offer.value_level == "level_2_mid_ticket":
    if offer.calendar_type_id:
        # MEETING then payment
        tool = "book_appointment"
        message = "Genial! Te propongo una llamada rápida para resolver dudas..."
    else:
        # DIRECT PAYMENT
        tool = "send_payment_link"

elif offer.value_level in ("level_3_high_ticket", "level_5_ultra_high"):
    # ALWAYS MEETING FIRST
    tool = "book_appointment"
    message = "El siguiente paso es una llamada estratégica de 30 min..."

elif offer.value_level == "level_4_recurring":
    # STRATEGY CALL
    tool = "book_appointment"
    message = "Para asegurarme de que es la mejor opción para ti..."
```

**Closing rules:**
- Don't ASK if they want to buy — FACILITATE the purchase
- "¿Te envío el link?" → "Aquí tienes el link: [link]" (assume the close)
- If they need to think → Set a follow-up: "¿Te parece si te escribo mañana para resolver dudas?"
- If meeting required → Offer 2-3 specific time slots, not "¿Cuándo puedes?"
- ALWAYS confirm: "¿Todo listo?" after sending link/booking

**Transitions:**
- Payment confirmed → Stage 6 (Post-Sale)
- Meeting booked → Stage 6 (Post-Sale: confirmation)
- "Necesito pensarlo" → Schedule follow-up + exit
- Decline → Offer downsell (`downsell_offer_id`) or graceful exit

---

## Stage 6: Post-Sale

**Entry:** Purchase complete or meeting booked.
**Goal:** Confirm, deliver, set expectations.
**Max messages:** 1-2

**After payment:**
```
"Bienvenido/a! 🎉 Tu compra está confirmada.
[Deliver access: link, instructions, or next step]
¿Alguna duda sobre cómo empezar?"
```

**After meeting booked:**
```
"Perfecto, quedamos el [date] a las [time].
Te voy a enviar un recordatorio antes.
¿Hay algo específico que quieras que preparemos para la llamada?"
```

**Rules:**
- Use `onboarding_action` and `onboarding_url` from the offer if available
- For digital products: deliver immediately via chat
- For services: confirm next steps clearly
- Store conversion event in CRM (journey event)

---

## Follow-Up Cadence (when conversation goes cold)

| Attempt | Wait | Message Type |
|---------|------|-------------|
| 1st | 24 hours | Value-based: share relevant insight/tip |
| 2nd | 48 hours | Social proof: testimonial or case study |
| 3rd | 72 hours | Urgency (if real): spots filling, price going up |
| 4th | 5 days | Direct: "¿Sigues interesada en [offer]?" |
| 5th | 7 days | Break-up: "Entiendo que no es el momento. Aquí estoy si cambias de opinión." |

**Rules:**
- NEVER fabricate urgency (no fake countdown timers)
- Follow-ups should provide VALUE, not just "ping" the prospect
- If they respond at any point → re-enter the stage where they left off
- Track follow-up count in state to avoid spamming

---

## Cross-Channel Identity Resolution

When a prospect contacts via a new channel:
1. `lookup_customer` searches CRM by: name match, phone, email, profile traits
2. If match found: load their conversation history, qualification status, and stage
3. Resume where they left off: "Hola [name]! Veo que estuvimos hablando por [other channel]. ¿Seguimos donde nos quedamos?"
4. If no match: normal greeting flow

This is critical for the multi-channel reality of Nicolify tenants.
