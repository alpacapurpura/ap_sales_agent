# Story 13 — Lupulo Labs bootstrap

> **Outcome:** luana-platform-migration · **Sequence:** 13/14 · **Parallel-safe** · **Most agentic-heavy brand**

## What

Bootstrap brand `lupulo-labs` (gastronomy: booking + ordering + kitchen integration agentic) consumiendo Luana v0.1.0+.

## Setup

1. Repo `luana-platform/lupulo-labs`
2. Clerk App #4 (Lupulo signup)
3. K8s cluster + DB
4. Domain (lupulolabs.com)

## `vertical-gastronomy/` package

**El más agentic-intensive de las 4 brands.** Sales agent debe poder hacer end-to-end booking + ordering + payment sin hand-off humano.

### Tools (sales_agent)
- `book_table` — reserva mesa con `table_capacity`, `time_slot`, `kitchen_load` checks
- `place_order` — toma pedido (drinks, food, modifications)
- `query_menu` — busca menú (ingredients, allergens, vegetarian, prices)
- `kitchen_eta` — estima tiempo cocina actual
- `loyalty_check` — verifica programa fidelidad cliente
- `dietary_restrictions_handle` — maneja restricciones (gluten, vegan, allergies)
- `event_reservation` — reserva eventos privados
- `delivery_quote` — cotiza delivery via integración terceros

### Extractors (copilot)
- `MenuExtractor` — parsea menú PDF/imagen → estructura items + precios + categorías + ingredients
- `RecipeExtractor` — recetas internas con tiempo prep + ingredients
- `EventCalendarExtractor` — eventos especiales (fiestas, cenas temáticas)

### Workflows
- `ReservationToOrderWorkflow` — full flow booking → pre-order → confirm → seat → serve
- `KitchenLoadBalanceWorkflow` — ajusta booking confirmations basado en kitchen capacity
- `EventManagementWorkflow` — agentic event coordination

### Knowledge base packs
- `gastronomy_kb_v1` (terminology, common dietary, allergen mappings)

### Channel adapters (NEW)
- POS systems (Square, Toast — el otro Toast)
- Kitchen Display Systems
- Delivery aggregators (Rappi, PedidosYa, UberEats — webhooks)
- Reservation platforms (OpenTable export sync)

### Guardrails
- Allergen safety enforcement (NUNCA serve sin double-check)
- Capacity hard limits (kitchen NO over-load)
- Price freshness (menu prices must match POS in real-time)

## BrandConfig

```python
LUANA_BRAND_CONFIG = {
    "name": "Lupulo Labs",
    "domain": "lupulolabs.com",
    "theme_tokens": {...},
    "features": {"voice_cloning": False, "real_time_kitchen_sync": True},
    "scheduling": {
        "booking_policy": "lupulo_capacity_aware",   # checks table + kitchen load
        "default_slot_duration_min": 90,
    },
    "offer_studio": {"preset_pack": "gastronomy_offers_v1"},
    "plan_tiers": {
        "restaurant": {"price": 79, ...},
        "group": {"price": 249, ...},
        "franchise": {"price": 599, ...},
    },
    "clerk_app": {...},
    "sidebar_routes": [
        {"path": "/menu", "label": "Menú"},
        {"path": "/kitchen", "label": "Cocina"},
        {"path": "/tables", "label": "Mesas"},
    ],
}
```

## Routes brand-specific

- `/menu/` (menu builder + sync POS)
- `/kitchen/` (real-time kitchen load monitor)
- `/tables/` (table management + floor plan)
- `/events/` (private events bookings)
- `/loyalty/` (fidelidad customers)

## Acceptance

- Lupulo deployed
- 2-3 restaurantes piloto pueden signup + completar Brand Studio + crear menú + agente recibir reserva por WhatsApp + tomar orden + confirmar con kitchen + recordatorio cliente día antes
- Real-time kitchen load sync funcional
- Allergen safety enforcement: smoke test agente NUNCA confirma orden con allergen flagged sin double-check

## Effort: 28-38 tickets, ~4 sem (parallel)
