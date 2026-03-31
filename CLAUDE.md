# Nicolify

**Context:** Multitenant SaaS (AaaS) automating marketing/sales for creators.
**Stack:** FastAPI (Async/SQLAlchemy 2.0), Next.js 15 (App Router/FSD), Clerk (Auth), Qdrant (RAG).
**Pattern:** Modular Monolith (DDD) + Docker-First.

## Core Domains

| Studio | Purpose | Modules |
| :--- | :--- | :--- |
| **Brand/Offer** | Identity capture & Offer Ladder builder | `brand`, `offer` |
| **Assets** | Auto-gen Landing Pages/Copies | `landing`, `assets` |
| **Growth** | Funnel diagram & Analytics | `analytics`, `advertising` |
| **Sales** | AI SDR (chat/close/schedule) & Ops Hub | `sales_agent`, `scheduling` |
| **Config** | External integrations (Meta, Shopify, etc.) | `connections` |

Unsure about a domain? Read `docs/domains/INDEX.md` first.

## Quick Reference

| Action | Command |
|---|---|
| Start dev | `/dev-up` or `docker compose up -d` |
| Backend CI | `/test-backend` |
| Frontend CI | `/test-frontend` |
| Full CI | `/test-all` |
| New migration | `/migrate <message>` |
| Explore module | `/explore-module <name>` |
| Review PR | `/review-pr` |

## Critical Rules

1. **Anti-Hallucination:** Read `docs/domains/INDEX.md` before coding. Never guess classes/fields.
2. **Docker-First:** All commands run inside Docker. See `.claude/rules/docker-first.md`.
3. **Tenant Isolation:** ALL queries filter by `X-Tenant-ID`. See `.claude/rules/tenant-isolation.md`.
4. **Architecture:** Backend DDD + Frontend FSD. See rules in `.claude/rules/`.
5. **Data:** Soft deletes only (`deleted_at`). SQLAlchemy 2.0 syntax.
6. **Migrations:** Must be idempotent (raw SQL). See `.claude/rules/backend-migrations.md`.

## Product Vision

For product decisions: `docs/vision/product-vision.md`.

@AGENTS.md
