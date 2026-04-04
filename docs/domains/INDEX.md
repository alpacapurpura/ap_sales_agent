# Module Index — Agent Routing Reference

> **How to use:** Scan the **Keywords** line to find the module matching your task.
> Load ONLY the linked doc — never load all docs at once.
> Cross-module work? Check **Reads from / Read by** to identify adjacent modules.
> Infra questions? Jump to `core` or `shared` at the bottom.

## Module Registry

### iam
- **Status:** active | **Doc:** [module_iam.md](./module_iam.md)
- **Purpose:** Clerk-based auth, tenant resolution, and session management for all API routes
- **Keywords:** auth, clerk, tenant, session, middleware, JWT, permissions, onboarding
- **Reads from:** — | **Read by:** all modules (`get_current_user`, `get_tenant_context`)
- **Backend:** `modules/iam/` | **Frontend:** `features/iam/`

### brand
- **Status:** active | **Doc:** [module_brand.md](./module_brand.md)
- **Purpose:** Brand identity capture via web scraping, reverse engineering, and guided forms
- **Keywords:** identity, scraping, logo, colors, story, positioning, BrandLoveKey, StoryBrand
- **Reads from:** copilot | **Read by:** sales_agent, copilot
- **Backend:** `modules/brand/` | **Frontend:** `features/brand/`

### offer
- **Status:** active | **Doc:** [module_offer.md](./module_offer.md)
- **Purpose:** Offer Ladder builder — products, pricing, archetypes, psychology, blueprints
- **Keywords:** product, pricing, archetype, blueprint, ladder, offer-wall, checkout
- **Reads from:** crm, copilot, landing, analytics (ports) | **Read by:** sales_agent, copilot, landing, crm, analytics
- **Backend:** `modules/offer/` | **Frontend:** `features/offer/`

### landing
- **Status:** active | **Doc:** [module_landing.md](./module_landing.md)
- **Purpose:** Auto-generated landing pages from brand + offer data, with preview and publish
- **Keywords:** page, template, slug, preview, publish, sections, hero
- **Reads from:** offer | **Read by:** copilot, offer
- **Backend:** `modules/landing/` | **Frontend:** `features/landing/`

### sales_agent
- **Status:** active | **Doc:** [module_sales_agent.md](./module_sales_agent.md)
- **Purpose:** Autonomous AI SDR — pre-qualifies leads, handles objections, schedules, closes
- **Keywords:** SDR, chat, qualification, objection, follow-up, RAG, semantic-router
- **Reads from:** crm, brand, offer, connections, scheduling | **Read by:** copilot, connections
- **Backend:** `modules/sales_agent/` | **Frontend:** `features/sales_agent/`

### copilot
- **Status:** active | **Doc:** [module_copilot.md](./module_copilot.md)
- **Purpose:** In-app AI assistant for configuration, form auto-completion, and guided procedures
- **Keywords:** assistant, form-fill, procedures, tools, LangGraph, nudges
- **Reads from:** brand, offer, connections, crm, analytics, landing, commercial_calendar, sales_agent | **Read by:** brand, offer
- **Backend:** `modules/copilot/` | **Frontend:** `features/copilot/`

### crm
- **Status:** active | **Doc:** [module_crm.md](./module_crm.md)
- **Purpose:** CDP — contacts, journey events, sales pipeline tracking, lifecycle scoring
- **Keywords:** contact, lead, journey, pipeline, lifecycle, identity, CDP
- **Reads from:** offer | **Read by:** sales_agent, copilot, scheduling, analytics, offer
- **Backend:** `modules/crm/` | **Frontend:** `features/crm/`

### scheduling
- **Status:** active | **Doc:** [module_scheduling.md](./module_scheduling.md)
- **Purpose:** Appointment booking with Google Calendar sync and public booking links
- **Keywords:** booking, calendar, availability, timezone, appointment, Google-Calendar
- **Reads from:** crm, connections, tenant_domains | **Read by:** sales_agent
- **Backend:** `modules/scheduling/` | **Frontend:** `features/scheduling/`

### analytics
- **Status:** active | **Doc:** [module_analytics.md](./module_analytics.md)
- **Purpose:** ETL pipeline (12+ providers), Bowtie funnel visualization, metric catalog
- **Keywords:** ETL, metrics, funnel, bowtie, dashboard, KPI, provider, campaign
- **Reads from:** connections, crm, offer (ports) | **Read by:** copilot, connections, offer
- **Backend:** `modules/analytics/` | **Frontend:** `features/analytics/`

### connections
- **Status:** active | **Doc:** [module_connections.md](./module_connections.md)
- **Purpose:** External platform integrations (Meta, Shopify, Google, payment, email, messaging)
- **Keywords:** OAuth, Meta, Shopify, webhook, channel, adapter, credentials
- **Reads from:** sales_agent, analytics | **Read by:** sales_agent, copilot, scheduling, analytics
- **Backend:** `modules/connections/` | **Frontend:** `features/connections/`

### assets
- **Status:** active | **Doc:** [module_assets.md](./module_assets.md)
- **Purpose:** AI-generated marketing assets (copies, flyers, images) with R2 storage
- **Keywords:** copy, flyer, image, AI-generation, R2, MIME, template
- **Reads from:** — | **Read by:** —
- **Backend:** `modules/assets/` | **Frontend:** `features/assets/`

### tenant_domains
- **Status:** active | **Doc:** [module_tenant_domains.md](./module_tenant_domains.md)
- **Purpose:** Custom domain management via Cloudflare Custom Hostnames API
- **Keywords:** domain, DNS, Cloudflare, hostname, verification, SSL
- **Reads from:** — | **Read by:** scheduling
- **Backend:** `modules/tenant_domains/` | **Frontend:** `features/tenant_domains/`

### commercial_calendar
- **Status:** active (minimal) | **Doc:** [module_commercial_calendar.md](./module_commercial_calendar.md)
- **Purpose:** Commercial event calendar — system-wide holidays + tenant-specific promotions
- **Keywords:** events, holidays, promotions, calendar, country-code
- **Reads from:** — | **Read by:** copilot
- **Backend:** `modules/commercial_calendar/` | **Frontend:** —

### advertising / social_media
- **Status:** placeholder | **Docs:** [module_advertising.md](./module_advertising.md), [module_social_media.md](./module_social_media.md)
- **Purpose:** Not implemented; ad data lives in analytics ETL, social reading in connections channels
- **Keywords:** PLACEHOLDER — ads, ROAS, CPL, organic, content, moderation

### core
- **Status:** infra | **Doc:** [tech_module_core.md](./tech_module_core.md)
- **Purpose:** Config, database engine, Sentry, security middleware, base repository, exceptions
- **Keywords:** config, database, sentry, context, exceptions, base-repository
- **Backend:** `core/` | **Frontend:** —

### shared
- **Status:** infra | **Doc:** [tech_module_shared.md](./tech_module_shared.md)
- **Purpose:** Cross-module infrastructure — inter-module links, channel ABCs, LLM factory, event bus, model registry
- **Keywords:** links, channels, LLM, events, model-registry, messages
- **Backend:** `shared/` | **Frontend:** —

## Dependency Graph

```
iam ─────────────────────────── (universal: injected into all modules)

brand <─────> copilot ────────> offer, connections, crm, analytics,
      <─────> offer             landing, commercial_calendar, sales_agent

sales_agent ──> crm, brand, offer, connections, scheduling
connections ──> sales_agent, analytics
analytics   ──> connections, crm, offer (ports)
scheduling  ──> crm, connections, tenant_domains
landing    <──> offer
crm         ──> offer

assets, tenant_domains, commercial_calendar ── (leaf: no outbound deps)
core, shared ────────────────── (infra: imported by all modules)
```

Legend: `A ──> B` = A imports from B | `<──>` = bidirectional

## Product Context

**Nicolify** is a multitenant AaaS platform that automates the full marketing-and-sales lifecycle for content creators. AI agents replace an entire sales team — from brand capture through lead qualification to payment collection. See [`vision/product-vision.md`](./vision/product-vision.md).
