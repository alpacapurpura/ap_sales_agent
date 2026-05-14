# T-deploy-1 IMPL-LOG — K8s + Cloudflare Tunnel + DNS + Clerk

**Story:** luana-comunify-bootstrap  
**Ticket:** T-deploy-1  
**Date:** 2026-05-14  
**Executor:** builder-agentic (Sonnet 4.6, production_code=false per R23)

## Deliverables

### K8s manifests

- `luana-platform/comunify/deploy/k8s/deployment.yaml` — backend (2 replicas FastAPI) + frontend (2 replicas Next.js)
- `luana-platform/comunify/deploy/k8s/service.yaml` — ClusterIP services for backend:8000 + frontend:3000
- `luana-platform/comunify/deploy/k8s/ingress.yaml` — NGINX ingress: api.comunify.lat → backend, comunify.lat + widget.comunify.lat → frontend

### Cloudflare Tunnel

- `luana-platform/comunify/deploy/cloudflared/config.yml` — ingress rules + K8s deployment instructions inline
  - 3 hostnames: api.comunify.lat, widget.comunify.lat, comunify.lat
  - Routes to in-cluster K8s services (no direct IP exposure)

### DNS + Clerk setup

- `luana-platform/comunify/deploy/DNS-RECORDS.md` — CNAME records + verification commands + env vars
- `luana-platform/comunify/deploy/CLERK-APP-SETUP.md` — full Clerk app setup: org configuration, JWT template, webhook, testing tokens

## Design decisions

- TLS terminates at Cloudflare edge → no cert-manager needed inside cluster
- `X-Tenant-ID` = Clerk `org_slug` (maps JWT claim to tenant isolation invariant)
- Cloudflare WAF + rate limiting on `/api/v1/chat` (60 req/min) — documented in DNS-RECORDS.md

## No tests (infra config — not testable statically)
