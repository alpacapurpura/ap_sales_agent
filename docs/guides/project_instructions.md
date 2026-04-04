# Nicolify - Project Instructions

## What is Nicolify?

Nicolify is a multitenant SaaS platform (AaaS - Agent as a Service) that automates the full marketing and sales lifecycle for content creators, infoproductors, and expert businesses. It uses AI Agents to handle lead capture, qualification, closing, and retention — replacing an entire marketing & sales team at the cost of an intern.

**Target user:** Entrepreneurs who are experts in their field but lack time/knowledge to manage marketing funnels, integrate tools, and scale customer attention.

For the complete product vision, see: `docs/domains/vision/product-vision.md`

## Core Modules (Business Domains)

| Studio               | What it does                                                                                                                                                                                                                                                                       | Backend modules                            |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| **Brand Studio**     | AI-assisted brand identity capture (forms, web scraping, doc upload, reverse engineering)                                                                                                                                                                                          | `brand`                                    |
| **Offer Studio**     | Visual Offer Ladder Builder + per-offer Blueprint forms with AI assistant                                                                                                                                                                                                          | `offer`                                    |
| **Asset Generation** | Auto-generate Landing Pages, copies, flyers, brochures from Brand/Offer data                                                                                                                                                                                                       | `landing`, `assets`                        |
| **Growth Studio**    | Interactive Bowtie funnel diagram (Views->Leads->Clients->Resales) with Action Triggers                                                                                                                                                                                            | `analytics`, `advertising`, `social_media` |
| **Sales Studio**     | Operations hub where the business owner monitors and manages all sales as if they had their own commercial team                                                                                                                                                                    | `sales_agent`, `scheduling`                |
| **Sales Agent**      | Autonomous AI SDR that chats with leads, pre-qualifies, handles objections, schedules meetings, sends payment links, follows up, and delivers ad-hoc value content. The best setter, commercial consultant, and closer a business can hire: intelligent, perceptive, and proactive | `sales_agent`                              |
| **Ecosystem Config** | Connect external services (Meta, IG, TikTok, Manychat, Telegram, Shopify, payment processors, Google Calendar, Gmail, Mailerlite)                                                                                                                                                  | `connections`                              |
| **Copilot**          | In-app AI assistant for system config and form auto-completion                                                                                                                                                                                                                     | `copilot`                                  |

Full domain map: `docs/domains/INDEX.md`

## Architecture

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (Async), Alembic, Pydantic v2
- **Frontend:** Next.js 14+ (App Router), React 18+, TypeScript, Tailwind CSS, Shadcn UI
- **Auth:** Clerk (multitenant, X-Tenant-ID header isolation)
- **DB:** PostgreSQL 15 | Redis (cache/sessions) | Qdrant (vector search/RAG)
- **Architecture pattern:** Modular Monolith with DDD (Domain-Driven Design)
- **Frontend pattern:** Feature-Sliced Design (FSD)
- **Dev environment:** Docker

## Key Conventions

### Docker-First Environment

**All development and production code runs in Docker Compose. Never assume code works locally without Docker verification.**

- Development: `docker compose up -d` (uses `.env` and `docker-compose.yml`)
- Production: `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d`
- Backend commands run inside container: `docker exec -it visionarias_brain_dev bash`
- Frontend commands run inside container: `docker exec -it visionarias_client_dev bash`
- Database migrations: `docker exec -it visionarias_brain_dev alembic upgrade head`
- Tests: `docker exec -t visionarias_brain_dev pytest`
- Linting: `docker exec -it visionarias_brain_dev ruff check src --fix`

### Code Quality

- **Anti-hallucination:** Always read `docs/domains/INDEX.md` and verify code existence before implementing. Never assume a class, method, or field exists without checking.
- **Multitenant isolation:** Every API call must include `X-Tenant-ID`. Backend filters all queries by tenant. Never leak data across tenants.
- **AI-assisted UX:** The platform assumes users don't know marketing/sales tech. Forms should have AI auto-fill buttons and guided flows to make complex setup simple.
- **Backend layers (inside-out):** `domain/` -> `infrastructure/` -> `application/` -> `api/`
- **Frontend layers (FSD):** `shared` -> `entities` -> `features` -> `widgets` -> `pages`
- **No deep imports:** Use Public API (`index.ts` barrel files) for cross-feature imports.
- **Server Components by default:** Only add `"use client"` when strictly needed.
- **Soft deletes only:** Never hard-delete records. Use `deleted_at` or `is_active`.
- **SQLAlchemy 2.0 syntax only:** `session.execute(select(Model))`, never `Session.query()`.

## Skills

Three Claude Code skills provide detailed architectural guidance:

- `/backend-expert` — DDD, FastAPI, SQLAlchemy patterns
- `/frontend-expert` — Next.js, React, FSD, Tailwind patterns
- `/front-back-integrator` — API contract validation, tenant propagation, integration testing

