# Nicolify

**Context:** Multitenant SaaS (AaaS) automating marketing/sales for creators.
**Stack:** FastAPI (Async/SQLAlchemy 2.0), Next.js 14 (App Router/FSD), Clerk (Auth), Qdrant (RAG).
**Pattern:** Modular Monolith (DDD) + Docker-First.

## Core Domains (if you are unsure about the domain, refer to the `docs/domains/INDEX.md` file)

| Studio | Purpose | Modules |
| :--- | :--- | :--- |
| **Brand/Offer** | Identity capture & Offer Ladder builder | `brand`, `offer` |
| **Assets** | Auto-gen Landing Pages/Copies | `landing`, `assets` |
| **Growth** | Funnel diagram & Analytics | `analytics`, `advertising` |
| **Sales** | AI SDR (chat/close/schedule) & Ops Hub | `sales_agent`, `scheduling` |
| **Config** | External integrations (Meta, Shopify, etc.) | `connections` |

## Dev Environment (Docker-First)

**CRITICAL: Always run in Docker. Do not assume local exec works.**

- **Up (Dev):** `docker compose up -d`
- **Shell (Back):** `docker exec -it visionarias_brain_dev bash`
- **Shell (Front):** `docker exec -it visionarias_client_dev bash`
- **Db Migration:** `docker exec -it visionarias_brain_dev alembic upgrade head`
- **Tests/Lint:** `pytest`, `ruff check src --fix` (inside container)

## Critical Constraints

1.  **Anti-Hallucination:** Read `docs/domains/INDEX.md` before coding. Never guess classes/fields.
2.  **Tenant Isolation:** ALL queries must filter by `X-Tenant-ID`. No data leaks.
3.  **Architecture:**
    *   **Backend:** `domain` -> `infrastructure` -> `application` -> `api`.
    *   **Frontend:** FSD (`shared` -> `entities` -> `features` -> `widgets` -> `pages`). No deep imports.
4.  **Data:** Soft deletes only (`deleted_at`). SQLAlchemy 2.0 syntax (`select(Model)`).
5.  **UX:** AI-first. Auto-fill buttons, guided flows.

## Product Vision 
- If you need to take a decision and need to know about the product vision: `docs/vision/product-vision.md`.
