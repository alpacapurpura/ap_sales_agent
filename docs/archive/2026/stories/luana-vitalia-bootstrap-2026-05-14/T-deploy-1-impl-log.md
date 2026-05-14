# T-deploy-1 impl-log — K8s manifests + CF tunnel + DNS-RECORDS + CLERK-APP-SETUP

## § Skills Consulted

| Skill | Por qué invocada | Decisión tomada |
|---|---|---|
| `backend-expert` | Ticket type `k8s` — infra config, skills/rules per 05-guidelines § 4.1 "K8s manifests + deploy scripts" | General infrastructure, no module-specific rule SSoT. Arch ref: 03-arch.md § 5.3–§ 5.5. |
| `tessl__fastapi` | FastAPI app runs in container — confirmed `redirect_slashes=False` already in `vitalia/backend/src/main.py`. No change needed. | Verified existing main.py; no route changes in this ticket. |
| `tessl__graceful-degradation` | External calls in cloudflared (CF tunnel → K8s service). Verified: timeout annotations on ingress + cloudflared originRequest timeouts set per graceful-degradation Iron Rule. | `nginx.ingress.kubernetes.io/proxy-read-timeout: "60"` covers LLM agentic calls (30s+). cloudflared `connectTimeout: 10s` per rule. |
| `tessl__pytest-api-testing` | N/A — ticket type `k8s` (config, no Python code). No tests written. | production_code: false. |

## § Step 0 — Anti-duplication grep

Per 05-guidelines § 1.2:

```bash
find /home/chris/luana-platform/nicolify -path "*/deploy/*" 2>/dev/null  # no output
# Finding: no existing deploy structure to mirror. Fresh files justified.
```

No nicolify/deploy/ exists. Files in scope are entirely new. Not mirroring any pattern verbatim.

## § Step 0.5 — Default flip detection

N/A — Story 11 pure greenfield, no flag flips (05-guidelines § 2.1: "Add new feature flags or flip existing flag defaults — FORBIDDEN"). configmap.yaml feature flags hardcoded `=false` (greenfield defaults, not flips).

## § Claim and sync

```
git status --short && git branch --show-current
→ branch: main (luana-platform repo, Story 11 commits land in main per precedent)
→ parallel WIP files (core/ + pyproject.toml) — NOT touched
→ vitalia/deploy/ not yet created — clean scope
```

## § Implementation notes

### Files created

1. `vitalia/deploy/k8s/configmap.yaml` — Non-sensitive app config. App domain `app.vitalia.health` + `cdn.vitalia.health`. HIPAA-lite compliance flag hardcoded per Q6=B. Feature flags `=false` (greenfield — anti-default-flip.md N/A for greenfield).

2. `vitalia/deploy/k8s/secrets.template.yaml` — Secret template with `${VARNAME}` placeholders ONLY. Zero real values. Covers: Postgres password, Clerk app #2 (stand-alone from Nicolify per § 5.4), Stripe Connect (no Healthcare flag per Q6=B), MercadoPago (AR/MX/BR/CL/CO per § 5.5), WhatsApp, ManyChat, ConsentURL HMAC, Anthropic API, Redis, Qdrant.

3. `vitalia/deploy/k8s/deployment.yaml` — 2 replicas, RollingUpdate. Container image `ghcr.io/alpacapurpura/vitalia-backend:0.1.0` (Story 11.bis extraction target per § 5.1). All secrets from `vitalia-secrets` Secret. Health checks at `/health`. Resource limits: 256Mi–512Mi / 100m–500m. Non-root security context.

4. `vitalia/deploy/k8s/service.yaml` — ClusterIP, port 80 → targetPort 8000. Name `vitalia-app` (matches cloudflared config.yml egress reference).

5. `vitalia/deploy/k8s/ingress.yaml` — ingress-nginx. Hosts: `app.vitalia.health` + `cdn.vitalia.health`. SSL redirect off (CF tunnel handles external TLS). Proxy timeouts 60s (covers LLM agentic calls). Body size 50m (consent PDF uploads + KB ingestion).

6. `vitalia/deploy/cloudflared/config.yml` — CF tunnel config. `<TUNNEL_ID>` placeholder (Chris creates tunnel). Egress: both hosts → `http://vitalia-app.vitalia.svc.cluster.local:80`. `connectTimeout: 10s` per graceful-degradation. Metrics on `:2000`.

7. `vitalia/deploy/cloudflared/setup-tunnel.sh` — 5-step guided script. Guards: aborts if `<TUNNEL_ID>` not filled, checks credentials file exists, uses `--dry-run=client` to apply cloudflared Deployment. Inline cloudflared Deployment manifest (2 replicas, liveness on `:2000/ready`).

8. `vitalia/deploy/DNS-RECORDS.md` — Spanish neutro (tuteo). 2 CNAME records: `app` + `cdn` → `<TUNNEL_ID>.cfargotunnel.com`. CLI alternative. Verification step. Arch reference.

9. `vitalia/deploy/CLERK-APP-SETUP.md` — Spanish neutro (tuteo). 4-step guide: create app, copy API keys, configure webhook endpoint `/api/v1/vitalia/webhooks/clerk`, JWT notes. Env var summary table. Arch reference to `clerk_webhook_adapter.py`.

10. `vitalia/deploy/.env.template` — All env vars with `replace_with_real_value` placeholders. Includes dev-friendly localhost defaults for Postgres/Redis/Qdrant. Security note.

### Decisions honored (per 05-guidelines § 6)

- **D1** (vitalia subdir `luana-platform/vitalia/`): all files under `vitalia/deploy/`.
- **D7** (compliance_level=hipaa_lite NOT hipaa_full): configmap + secrets.template note "NO Stripe Healthcare flag" + comment "Q6=B ratified".
- **D8** (voice_cloning=False): `VITALIA_VOICE_CLONING_ENABLED=false` in configmap + .env.template.
- **D9** (Spanish neutro tuteo): DNS-RECORDS.md + CLERK-APP-SETUP.md both use tuteo.
- **D10** (RedisSaver cross-brand): Redis env vars present (shared Redis — no per-brand isolation).
- **D11** (booking widget BOTH iframe + canonical): `cdn.vitalia.health` ingress rule covers widget bundle endpoint.
- **D13** (multi-site UI federation DEFER): `VITALIA_MULTI_SITE_FEDERATION_ENABLED=false`.
- **D14** (insurance integration DEFER): `VITALIA_INSURANCE_INTEGRATION_ENABLED=false`.

### Chris UI gate Q4=B — /dev-team scope boundary honored

- K8s cluster provisioning → Chris (cloud dashboard).
- Container registry push → Chris (post Story 11.bis GHCR setup).
- DNS records creation → Chris (Cloudflare dashboard — guided by DNS-RECORDS.md).
- CF tunnel creation → Chris (`cloudflared tunnel create` — guided by setup-tunnel.sh).
- Clerk app #2 creation + keys → Chris (Clerk dashboard — guided by CLERK-APP-SETUP.md).
- MercadoPago production credentials → Chris (MP developers portal).
- Stripe Connect onboarding → Chris (Stripe dashboard).
- K8s apply final command → Chris (`kubectl apply -f vitalia/deploy/k8s/ -n vitalia`).

## § Validators

- **A1 (YAML valid):** `python3 -c "import yaml; ..."` → all 5 K8s YAML files parse clean → `YAML valid` ✓
  - Note: `kubectl apply --dry-run=client` requires live cluster (WSL2 dev has no K8s cluster). Fallback python yaml validation confirmed per validator spec.
- **A2 (Chris gate docs):** `test -f DNS-RECORDS.md && test -f CLERK-APP-SETUP.md` → `Chris gate docs present` ✓

## § Parallel session safety

- Files this session modified: `vitalia/deploy/` (entirely new directory).
- Parallel WIP files (NOT touched): `core/DEFERRED-FILES.md`, `core/luana-core-platform/src/...`, `core/tests/architecture/test_*.py`, `pyproject.toml`, `nicolify/backend/uv.lock`, `vitalia/frontend/coverage/`.
