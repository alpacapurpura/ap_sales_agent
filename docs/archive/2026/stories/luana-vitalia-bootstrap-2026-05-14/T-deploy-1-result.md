# T-deploy-1 result — K8s manifests + CF tunnel + DNS-RECORDS + CLERK-APP-SETUP

## Estado: GREEN

## Archivos creados

| Archivo | Descripción |
|---|---|
| `vitalia/deploy/k8s/configmap.yaml` | Config no-sensible: dominio, compliance (hipaa_lite), feature flags greenfield |
| `vitalia/deploy/k8s/secrets.template.yaml` | Plantilla secrets — `${VARNAME}` placeholders, sin valores reales |
| `vitalia/deploy/k8s/deployment.yaml` | 2 réplicas, RollingUpdate, image GHCR, todos los secrets montados |
| `vitalia/deploy/k8s/service.yaml` | ClusterIP vitalia-app port 80 → 8000 |
| `vitalia/deploy/k8s/ingress.yaml` | ingress-nginx hosts app.vitalia.health + cdn.vitalia.health |
| `vitalia/deploy/cloudflared/config.yml` | CF tunnel config — `<TUNNEL_ID>` placeholder para Chris |
| `vitalia/deploy/cloudflared/setup-tunnel.sh` | Script guiado 5 pasos (chmod +x) |
| `vitalia/deploy/DNS-RECORDS.md` | 2 CNAME records — Chris ejecuta en Cloudflare dashboard |
| `vitalia/deploy/CLERK-APP-SETUP.md` | Clerk app #2 — Chris ejecuta en Clerk dashboard |
| `vitalia/deploy/.env.template` | Todas las env vars con `replace_with_real_value` |

## Validators

| # | Validator | Resultado |
|---|---|---|
| A1 | YAML valid (python yaml.safe_load fallback) | PASS — `YAML valid` |
| A2 | DNS-RECORDS.md + CLERK-APP-SETUP.md present | PASS — `Chris gate docs present` |

Nota A1: `kubectl apply --dry-run=client` requiere cluster activo (WSL2 no tiene K8s).
Spec especifica fallback `python -c "import yaml; ..."` — ejecutado y PASS.

## Constraints cumplidos

- secrets.template.yaml: `${VARNAME}` placeholders ONLY — cero valores reales
- .env.template: `replace_with_real_value` placeholders — cero valores reales
- namespace `vitalia` en todos los manifests (aislado de nicolify namespace)
- Hosts: `app.vitalia.health` + `cdn.vitalia.health` (per prompt constraint)
- CF tunnel expone `app.vitalia.health` → servicio `vitalia-app:80`
- Spanish neutro tuteo: DNS-RECORDS.md + CLERK-APP-SETUP.md ✓
- Chris UI gate Q4=B — /dev-team scope boundary: manifests + scripts + docs ONLY
- Anti-duplication: no nicolify/deploy/ existía — archivos nuevos justificados

## Commit

`feat(story-11/T-deploy-1): vitalia K8s manifests + CF tunnel + DNS-RECORDS + CLERK-APP-SETUP (Chris UI gate)`
