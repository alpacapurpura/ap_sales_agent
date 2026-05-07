# Tool Implementation Patterns — Full Reference

> **Nota de vigencia (2026-05-06 audit T-1):** Este archivo es la referencia conceptual de diseño de herramientas (S5–S9). Los nombres de herramientas en ejemplos de código pueden diferir de los registrados en producción. Para nombres canónicos actuales consultar: `application/agents/sales/tools.py::TOOL_REGISTRY` + `application/tools/registry.py::STAGE_TOOL_SCOPE`. Ejemplo de divergencia conocida: `check_schedule` → `get_available_slots`, `book_appointment` → `create_booking_link`, `recommend_product` → implementado via specialist routing, `lookup_customer` → `IdentityResolver` (S11B).

## Why Tools Are Critical

The current sales agent acts as a full AI SDR: books meetings, sends payment links, looks up products, recognizes customers. Tools are what enable this (S5–S9 redesign).

## LangGraph Tool Integration Pattern

Tools in LangGraph should be implemented as nodes that the graph can route to, not as inline function calls within a response node.

### Architecture

```python
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# Define tools as Python functions with @tool decorator
@tool
def check_schedule(tenant_id: str, date: str = None) -> dict:
    """Check available appointment slots for the tenant."""
    ...

@tool
def book_appointment(tenant_id: str, customer_id: str, datetime_iso: str) -> dict:
    """Book an appointment slot."""
    ...

@tool
def send_payment_link(tenant_id: str, offer_id: str, customer_id: str) -> dict:
    """Get the payment link for a specific offer."""
    ...

# Bind tools to the LLM
tools = [check_schedule, book_appointment, send_payment_link, ...]
llm_with_tools = llm.bind_tools(tools)

# Create tool node
tool_node = ToolNode(tools)

# In the graph
workflow.add_node("generate", generate_response)  # LLM decides to use tool or respond
workflow.add_node("tools", tool_node)               # Executes the tool
workflow.add_node("format", format_output)           # Formats final response

# Routing: if LLM called a tool → execute it → loop back
def should_use_tool(state):
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return "format"

workflow.add_conditional_edges("generate", should_use_tool, {
    "tools": "tools",
    "format": "format",
})
workflow.add_edge("tools", "generate")  # After tool execution, go back to generate
workflow.add_edge("format", END)
```

### Key Pattern: Tool Loop
After a tool executes, control returns to the `generate` node so the LLM can:
1. Interpret the tool result
2. Decide if another tool is needed
3. Generate a human-readable response incorporating the tool result

This avoids the anti-pattern of hardcoding tool result formatting.

---

## Tool Specifications

### 1. `lookup_customer` — Cross-Channel Identity Resolution

**Purpose:** Recognize returning customers across channels.
**When:** EVERY new conversation start.
**Data source:** CRM module (`CustomerProfileModel`, `IdentityService`)

```python
@tool
def lookup_customer(
    tenant_id: str,
    channel_type: str,
    channel_user_id: str,
    metadata: dict = None
) -> dict:
    """
    Look up a customer across all channels.
    Returns customer profile, conversation history summary, and last known stage.
    """
    # 1. Direct lookup by channel identity
    customer = identity_service.find_by_identity(
        tenant_id, IdentityType(channel_type), channel_user_id
    )

    # 2. If not found, try fuzzy match on name/traits
    if not customer and metadata:
        name = f"{metadata.get('first_name', '')} {metadata.get('last_name', '')}".strip()
        if name:
            customer = customer_repo.search_by_name(tenant_id, name)

    if customer:
        # Load conversation summary from last interaction
        last_summary = audit_repo.get_last_summary(customer.id)
        return {
            "found": True,
            "customer_id": str(customer.id),
            "name": customer.full_name,
            "returning": True,
            "last_stage": last_summary.get("stage") if last_summary else None,
            "last_offer": last_summary.get("offer_id") if last_summary else None,
            "qualification_score": last_summary.get("score", 0),
            "traits": customer.traits or {},
        }

    return {"found": False, "returning": False}
```

**How the agent uses it:**
- If returning: "Hola [name]! Qué bueno verte de nuevo. [Resume context]"
- If new: Normal greeting flow

---

### 2. `detect_campaign_origin` — Ad Campaign Detection

**Purpose:** Know if the user arrived from an advertising campaign.
**When:** First message of a new session.
**Data source:** UTM parameters, referral metadata, campaign tags from channel

```python
@tool
def detect_campaign_origin(
    tenant_id: str,
    channel_type: str,
    metadata: dict
) -> dict:
    """
    Detect if the user came from an advertising campaign.
    Checks: UTM params, ManyChat tags, referral data, ad_id.
    """
    campaign_info = {
        "from_campaign": False,
        "campaign_name": None,
        "target_offer_id": None,
        "ad_creative_context": None,
    }

    # Check ManyChat tags/custom fields
    manychat_tags = metadata.get("tags", [])
    manychat_custom = metadata.get("custom_fields", {})

    # Check UTM parameters (if available from landing page referral)
    utm_campaign = metadata.get("utm_campaign")
    utm_source = metadata.get("utm_source")

    # Check ad_id (Meta Ads)
    ad_id = metadata.get("ad_id")

    if utm_campaign or ad_id or any("campaign" in t.lower() for t in manychat_tags):
        campaign_info["from_campaign"] = True
        campaign_info["campaign_name"] = utm_campaign or ad_id

        # Try to resolve which offer the campaign promotes
        # (campaigns are linked to offers via advertising module)
        if ad_id:
            offer = advertising_repo.get_offer_for_ad(tenant_id, ad_id)
            if offer:
                campaign_info["target_offer_id"] = str(offer.id)

    return campaign_info
```

**How the agent uses it:**
- If from campaign: Skip to presentation of the linked offer
- If organic: Normal discovery flow

---

### 3. `check_schedule` — Availability Lookup

**Purpose:** Query the tenant's calendar availability.
**When:** User asks about meeting/calls, or closing a high-ticket offer.
**Data source:** Scheduling module (`CalendarType`, Google Calendar integration)

```python
@tool
def check_schedule(
    tenant_id: str,
    calendar_type_id: str = None,
    preferred_date: str = None,
    days_ahead: int = 7
) -> dict:
    """
    Check available appointment slots.
    Returns next N available slots within the timeframe.
    """
    # If no calendar_type_id, use the one from the active offer
    if not calendar_type_id:
        # Resolve from state.target_offer_id
        pass

    slots = scheduling_service.get_available_slots(
        tenant_id=tenant_id,
        calendar_type_id=calendar_type_id,
        from_date=preferred_date or today(),
        days_ahead=days_ahead,
        limit=5,
    )

    if not slots:
        return {
            "available": False,
            "message": "No hay espacios disponibles en los próximos días.",
            "booking_link": scheduling_service.get_booking_page_url(tenant_id, calendar_type_id),
        }

    return {
        "available": True,
        "slots": [
            {"date": s.date.isoformat(), "time": s.time.strftime("%H:%M"), "duration_min": s.duration}
            for s in slots
        ],
        "booking_link": scheduling_service.get_booking_page_url(tenant_id, calendar_type_id),
    }
```

**How the agent uses it:**
- Present 2-3 specific slots: "¿Te funciona el martes a las 10am o el jueves a las 3pm?"
- If no slots: Send booking page link

---

### 4. `book_appointment` — Create Booking

**Purpose:** Actually book a meeting slot.
**When:** User confirms a specific date/time.
**Data source:** Scheduling module

```python
@tool
def book_appointment(
    tenant_id: str,
    customer_id: str,
    calendar_type_id: str,
    datetime_iso: str,
    customer_name: str = None,
    customer_email: str = None,
    notes: str = None,
) -> dict:
    """
    Book an appointment in the tenant's calendar.
    Returns confirmation details.
    """
    result = scheduling_service.create_booking(
        tenant_id=tenant_id,
        calendar_type_id=calendar_type_id,
        datetime_iso=datetime_iso,
        attendee={
            "customer_id": customer_id,
            "name": customer_name,
            "email": customer_email,
        },
        notes=notes,
    )

    if result.success:
        return {
            "booked": True,
            "date": result.date.isoformat(),
            "time": result.time.strftime("%H:%M"),
            "meeting_link": result.meeting_url,  # Zoom/Meet link
            "confirmation_sent": result.email_sent,
        }
    return {"booked": False, "reason": result.error}
```

---

### 5. `send_payment_link` — Deliver Checkout URL

**Purpose:** Send the appropriate payment link for an offer.
**When:** User ready to buy (buying signals threshold met).
**Data source:** Offer module (`checkout_page_url`, Shopify integration)

```python
@tool
def send_payment_link(
    tenant_id: str,
    offer_id: str,
    customer_id: str = None,
    pricing_option_index: int = 0,
) -> dict:
    """
    Retrieve the payment/checkout link for a specific offer.
    Supports: Shopify, Mercado Pago, custom landing pages.
    """
    offer = offer_repo.get_by_id(tenant_id, offer_id)
    if not offer:
        return {"success": False, "reason": "Offer not found"}

    # Determine payment source
    if offer.checkout_page_url:
        return {
            "success": True,
            "link": offer.checkout_page_url,
            "offer_name": offer.public_name,
            "price": offer.pricing_options[pricing_option_index].total_amount if offer.pricing_options else None,
            "currency": offer.currency,
        }

    # Fallback: try Shopify integration
    shopify_link = connections_service.get_shopify_checkout(tenant_id, offer_id)
    if shopify_link:
        return {"success": True, "link": shopify_link, "offer_name": offer.public_name}

    return {"success": False, "reason": "No payment link configured for this offer"}
```

**How the agent uses it:**
- Direct: "Aquí tienes el link para inscribirte: {link}"
- With context: "La inversión es de ${price}. Aquí puedes completar tu inscripción: {link}"
- NEVER say "¿Quieres que te mande el link?" — just send it when the buying signals are clear

---

### 6. `recommend_product` — Product Matching

**Purpose:** Find the best offer for the prospect's needs.
**When:** During qualification when no specific offer is targeted, or when prospect doesn't qualify for current offer.
**Data source:** Offer module (all active offers)

```python
@tool
def recommend_product(
    tenant_id: str,
    prospect_situation: str,
    budget_range: str = None,
    pain_points: list = None,
) -> dict:
    """
    Analyze prospect profile against all active offers and recommend the best fit.
    Returns top 1-3 matching offers with reasoning.
    """
    offers = offer_repo.get_all_active(tenant_id)

    # Score each offer against prospect profile
    recommendations = []
    for offer in offers:
        score = 0

        # Avatar match
        for avatar in offer.target_avatar_match:
            if any(kw.lower() in prospect_situation.lower() for kw in avatar.keywords):
                score += 30

        # Pain point match
        if pain_points and offer.marketing_pain_points:
            overlap = set(p.lower() for p in pain_points) & set(p.lower() for p in offer.marketing_pain_points)
            score += len(overlap) * 20

        # Budget match
        if budget_range and offer.pricing_options:
            lowest = min(p.total_amount for p in offer.pricing_options)
            if budget_fits(budget_range, lowest):
                score += 20

        # Anti-avatar check
        if any(kw.lower() in prospect_situation.lower() for kw in offer.anti_avatar_keywords):
            score = -100  # Disqualify

        if score > 0:
            recommendations.append({
                "offer_id": str(offer.id),
                "name": offer.public_name,
                "score": score,
                "price_range": f"${min(p.total_amount for p in offer.pricing_options)} - ${max(p.total_amount for p in offer.pricing_options)}" if offer.pricing_options else "N/A",
                "key_benefit": offer.primary_outcome,
                "close_type": "meeting" if offer.calendar_type_id else "direct_payment",
            })

    recommendations.sort(key=lambda x: x["score"], reverse=True)
    return {"recommendations": recommendations[:3]}
```

---

### 7. `escalate_to_human` — Human Handoff

**Purpose:** Transfer conversation to a real person.
**When:** Safety trigger, complex situation, explicit request, or persistent unresolved objections.
**Data source:** Channel adapter

```python
@tool
def escalate_to_human(
    tenant_id: str,
    customer_id: str,
    reason: str,
    conversation_summary: str,
) -> dict:
    """
    Hand off conversation to human agent.
    Notifies the business owner and sets a flag to stop auto-responses.
    """
    # 1. Set flag in Redis to pause AI responses for this customer
    redis_client.set(f"human_takeover:{tenant_id}:{customer_id}", "active", ex=86400)

    # 2. Notify business owner (via their preferred channel)
    notification_service.notify_owner(
        tenant_id=tenant_id,
        subject=f"Conversación requiere atención: {reason}",
        body=conversation_summary,
        customer_id=customer_id,
    )

    return {
        "escalated": True,
        "message_to_prospect": "Te conecto con [owner_name] para que pueda ayudarte personalmente.",
    }
```

---

## Tool Selection Logic

The `select_strategy` node in the graph determines which approach to take:

```python
def select_strategy(state: SalesAgentState) -> dict:
    """Decide: generate text response, use a tool, or escalate."""

    intent = state["detected_intent"]
    stage = state["current_stage"]
    buying_signals = state["buying_signals_count"]
    offer = state.get("target_offer")

    # 1. Always check identity first (new conversations)
    if state["messages_this_session"] <= 1:
        return {"next_action": "lookup_customer"}

    # 2. Buying signals threshold → close
    if buying_signals >= 3 and offer:
        if offer.get("calendar_type_id"):
            return {"next_action": "check_schedule"}
        elif offer.get("checkout_page_url"):
            return {"next_action": "send_payment_link"}

    # 3. Explicit intent signals
    if intent == "buying_signal":
        return {"next_action": "send_payment_link"}
    if intent == "schedule_signal":
        return {"next_action": "check_schedule"}
    if intent == "security_breach":
        return {"next_action": "escalate_to_human"}

    # 4. No specific product identified yet
    if not state.get("target_offer_id") and stage in ("discovery", "qualification"):
        return {"next_action": "recommend_product"}

    # 5. Default: generate conversational response
    return {"next_action": "generate_response"}
```

## Implementation Priority

| Priority | Tool | Impact | Effort |
|----------|------|--------|--------|
| P0 | `send_payment_link` | Enables actual sales | Low (data already exists in offers) |
| P0 | `lookup_customer` | Cross-channel recognition | Medium (CRM integration) |
| P1 | `check_schedule` | Enables meeting-based closes | Medium (scheduling module exists) |
| P1 | `book_appointment` | Completes the scheduling flow | Medium |
| P1 | `recommend_product` | Multi-product matching | Medium |
| P2 | `detect_campaign_origin` | Campaign-aware conversations | Low-Medium |
| P2 | `escalate_to_human` | Safety + complex cases | Low |
