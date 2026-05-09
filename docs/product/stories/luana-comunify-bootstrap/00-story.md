# Story 12 — Comunify bootstrap

> **Outcome:** luana-platform-migration · **Sequence:** 12/14 · **Parallel-safe**

## What

Bootstrap brand `comunify` (creator/expert economy + community) consumiendo Luana v0.1.0+.

## Setup

1. Repo `luana-platform/comunify`
2. Clerk App #3 (Comunify signup)
3. K8s cluster + DB
4. Domain (comunify.io)

## `vertical-creator-economy/` package

### Tools (sales_agent)
- `qualify_for_cohort` — califica lead vs cohort criteria
- `link_to_community` — invita a Discord/Circle/etc post-purchase
- `nurture_via_authority_content` — sirve content path personalizado
- `book_discovery_call` — agenda call gratuita

### Extractors (copilot)
- `OfferLadderAdvisor` — analiza oferta actual + sugiere niveles faltantes
- `AuthorityVaultExtractor` — extrae credenciales/casos/PR mencionables

### Workflows
- `CommunityEngagementWorkflow` — agentic re-engagement community drift members
- `CohortEnrollmentWorkflow` — flow inscripción cohorte

### Knowledge base packs
- `creator_economy_kb_v1` (frameworks, terminology, common questions)

## BrandConfig

```python
LUANA_BRAND_CONFIG = {
    "name": "Comunify",
    "domain": "comunify.io",
    "theme_tokens": {...},
    "features": {"voice_cloning": True},        # ON per ADR-001 §2.4
    "brand_studio": {
        "enabled_sections": ["identity", "story", "narrative", "voice", "buyer_persona", "authority_vault", "team", "testimonials", "communication_assets", "contact"],
        "field_overrides": {
            "buyer_persona": {"min_count": 3},   # multi-persona mandatory
            "authority_vault": {"required": True},
        },
    },
    "offer_studio": {"preset_pack": "coaching_offers_v1"},
    "plan_tiers": {
        "creator": {"price": 29, ...},
        "pro": {"price": 99, ...},
        "agency": {"price": 299, ...},
    },
    "clerk_app": {...},
    "sidebar_routes": [{"path": "/cohorts", "label": "Cohortes", "vertical_only": True}, {"path": "/community", "label": "Comunidad"}],
}
```

## Routes brand-specific

- `/cohorts/` (CRUD cohortes)
- `/community/` (members management)
- `/authority/` (authority vault)
- `/ladder/` (offer ladder visualizer)

## Acceptance

- Comunify deployed
- 2-3 creators piloto pueden signup + completar Brand Studio full (10 sections + voice cloning) + ladder con 4 niveles + sales agent operando con voz clonada de chats reales
- Voice cloning pipeline funcional (50+ chats samples → distilled system_instruction)

## Effort: 25-35 tickets, ~3-4 sem (parallel)
