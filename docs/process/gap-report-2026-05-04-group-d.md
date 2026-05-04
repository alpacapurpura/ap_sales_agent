# Gap Report — Group D (support/infra modules) — 2026-05-04

**Modules cubiertos:** crm · iam · commercial-calendar · tenant-domains
**Owner:** module-mapping agent (SDD Level 3 migration)
**Source of truth:** `docs/product/modules/{m}.md` + `backend/src/modules/{m}/` + `frontend/src/features/{m}/` + tests reales

## Resumen ejecutivo

| Module | Capabilities creadas | Stories creadas | UI? | Tests linkeados | Notas |
|---|---|---|---|---|---|
| crm | 2 (contacts-cdp, pipeline-lifecycle) | 4 (3 ui+service + 1 service) | sí (`crm-hub`) | 27 BE + Vitest FE + 1 e2e regression | PR-10/11/12 cierran S4 MVP |
| iam | 2 (auth-tenant-resolution, admin-billing-config) | 3 service | no (settings dispersos) | 13 BE | Casi todo backend; admin Streamlit `/planes-billing` |
| commercial-calendar | 1 (calendar-events) | 2 service | placeholder | 4 BE | Sin UI dedicada (gap doc en módulo) |
| tenant-domains | 1 (custom-domains) | 2 (1 ui + 1 service) | sí (`tenant-domains`) | 6 BE + Vitest FE | Worker `poll_domain_verification` background |

**Totales:** 6 capabilities + 11 stories + 4 module INDEX updates en capabilities/stories.

## Top 5 priorización (CRITICAL → MEDIUM)

### 1. CRITICAL — IAM webhook signature edge cases sin cobertura adversarial dedicada
- **Módulo:** iam
- **Story afectada:** `iam-clerk-webhook-sync.yaml`
- **Gap:** signature verification (svix) usa scenario `invalid-signature` documentado pero `backend/tests/modules/iam/test_webhooks.py` debería tener test específico que mande payload con header svix-id válido pero firma corrupta. Si se rompe, attacker puede inyectar fake user_created y crear user huérfano controlado.
- **Acción:** auditor dedicado del módulo iam, agregar 2 tests adversariales (signature mismatch + replay attack window).

### 2. CRITICAL — `iam-plan-effective-resolution` Redis pub/sub invalidation cross-instance sin test integration
- **Módulo:** iam
- **Story:** `iam-plan-effective-resolution.yaml`
- **Gap:** cache 5min in-process + Redis pub/sub invalidación cross-instance es invariante billing. No hay test integration que demuestre: pod A invalida → pod B ve cambio < 1s. Si falla en prod, BudgetGuard de un pod usa plan stale y costos se desbordan ese pod por hasta 5min.
- **Acción:** integration test multi-process o multi-event-loop. Agregar a backend test suite.

### 3. HIGH — Commercial Calendar sin UI dedicada (placeholder)
- **Módulo:** commercial-calendar
- **Capability:** `calendar-events`
- **Gap:** módulo sólo tiene API + copilot_provider. No hay screen `/[tenantId]/calendar` ni `/sales/timing` que muestre próximos eventos. Copilot puede consultarlos pero user tiene que confiar en agente. Module doc lo marca explícitamente: "FE: placeholder · No hay UI dedicada hoy".
- **Acción:** ui-story nueva en P9-P10 — `calendar-week-view`. Aprovecha dataset existente, baja complejidad. Crítico para PI-1 timing de campaigns.

### 4. HIGH — `tenant-domains-worker-poll` sin métric/alert si poll se atasca
- **Módulo:** tenant-domains
- **Story:** `tenant-domains-worker-poll.yaml`
- **Gap:** worker `poll_domain_verification` no expone métric `domain_pending_age_hours{tenant_id}`. Si Cloudflare CHM nunca activa SSL, dominio queda en `pending` forever sin alerting. Tenants pagan por feature que no funciona y nadie lo nota.
- **Acción:** agregar histogram + Prometheus alert (>24h en pending). Story nueva: `tenant-domains-stuck-pending-alert`.

### 5. MEDIUM — CRM sin tools copilot wrappeando PR-10/11/12 endpoints
- **Módulo:** crm
- **Stories afectadas:** `crm-list-contacts`, `crm-create-static-segment`, `crm-pipeline-stage-override`
- **Gap:** capability_status en module doc dice "Operable copilot: pendiente PI-3". Tools `crm_search_contacts(filters)`, `crm_get_contact_summary(id)`, `crm_create_segment`, `crm_pipeline_set_stage` no existen. Copilot no puede operar conversacionalmente sobre CRM aunque endpoints están live y verificados.
- **Acción:** PI-3 dedicado a "copilot tools wrapping" multi-módulo. CRM es candidato fuerte porque endpoints son los más maduros del producto (33 tests verde, 18 filters forward-compat).

## Otros gaps catalogados (sin top-5)

### crm
- Stubs 501 deferred PI-3: `/contacts/{id}/journey`, `/contacts/{id}/campaigns` — esperar consumer ready antes promover a 200.
- Pipeline sin UI dedicada (kanban) — solo via API, baja prioridad.
- Lifecycle scoring sin transparencia para user (no se ve "porqué" del score).
- E2E filter combinations realistas ausente (solo 1 sanity smoke en `contactos.spec.ts`).

### iam
- Roles avanzados (RBAC granular por feature) ausentes — solo owner/member.
- Onboarding sin flow conversacional copilot.
- Sin tool copilot para invitar member nuevo.
- API user-facing pública "qué plan tengo" ausente (solo admin Streamlit).
- BudgetGuard wired a `custom_overrides` no exhaustivo (DR-7 pendiente).

### commercial-calendar
- Sin tool copilot que sugiera campaña basado en evento próximo.
- Country code filter sin default ni fallback documentado.
- Sin recurring events (Black Friday no auto-genera próxima iteración).

### tenant-domains
- Tool copilot para flow OAuth + verificación DNS conversacional ausente.
- Cloudflare API errors (rate limit, transient) no exponen retry policy clara al user.
- Sin E2E que exercise wizard completo.
- DNS conflict edge cases (wildcard subdominios no exhaustivo).

## Propuesta de slicing PI futuro

| PI candidato | Stories | Módulos | Tamaño |
|---|---|---|---|
| PI-3 "copilot CRM ops" | crm_search_contacts + crm_get_contact_summary + crm_create_segment + crm_pipeline_set_stage tools | crm + copilot | M |
| PI-X "calendar UI" | calendar-week-view + calendar-monthly-view + copilot_suggest_campaign_for_event | commercial-calendar + copilot | M |
| PI-Y "tenant-domains ops" | tenant-domains-stuck-pending-alert + tenant-domains-conversational-wizard (copilot) | tenant-domains + copilot | S |
| PI-Z "iam hardening" | iam-webhook-replay-protection + iam-plan-effective-cross-instance-test + iam-rbac-feature-matrix | iam | M |

## Anti-hallucination checks ejecutados

- Endpoints citados (`POST /api/v1/contacts`, `PUT /api/v1/crm/pipeline/...`, `POST /api/v1/iam/webhooks/clerk`, `GET /api/v1/commercial-calendar/events`, `POST /api/v1/domains/`, etc.) verificados grep en `backend/src/main.py` (lines 877-1109).
- Tests reales linkeados (no inventados). Confirmado vía `ls backend/tests/modules/{m}/`:
  - crm: `test_contacts_api.py`, `test_pipeline_api.py`, etc. (27 tests).
  - iam: `test_webhooks.py`, `test_dependencies.py`, `test_settings.py`.
  - commercial_calendar: `test_calendar_event_*.py` (4 tests).
  - tenant_domains: `test_domain_*.py` (5 tests).
- E2E spec citado existente: `frontend/e2e/specs/regression/sales/contactos.spec.ts` y `segment-create-and-launch-campaign.spec.ts`.
- IAM module doc reflejado: PR-2 plan_config + invariante "1 plan default" + `BillingDefaultPlanMissingError` capturados en story.
- CRM module doc reflejado: PR-10/PR-11/PR-12 + commits + 33 tests + 18 filters forward-compat capturados.

## Outputs

```
docs/product/capabilities/crm/contacts-cdp.yaml
docs/product/capabilities/crm/pipeline-lifecycle.yaml
docs/product/capabilities/iam/auth-tenant-resolution.yaml
docs/product/capabilities/iam/admin-billing-config.yaml
docs/product/capabilities/commercial-calendar/calendar-events.yaml
docs/product/capabilities/tenant-domains/custom-domains.yaml

docs/product/stories/crm/crm-list-contacts.yaml
docs/product/stories/crm/crm-contacts-page.yaml
docs/product/stories/crm/crm-create-static-segment.yaml
docs/product/stories/crm/crm-pipeline-stage-override.yaml
docs/product/stories/iam/iam-clerk-webhook-sync.yaml
docs/product/stories/iam/iam-current-user-tenant-resolution.yaml
docs/product/stories/iam/iam-plan-effective-resolution.yaml
docs/product/stories/commercial-calendar/calendar-list-events.yaml
docs/product/stories/commercial-calendar/calendar-event-crud.yaml
docs/product/stories/tenant-domains/tenant-domains-add-and-verify.yaml
docs/product/stories/tenant-domains/tenant-domains-worker-poll.yaml

docs/product/capabilities/{crm,iam,commercial-calendar,tenant-domains}/INDEX.md (updated)
docs/product/stories/{crm,iam,commercial-calendar,tenant-domains}/INDEX.md (updated)
```

**Total files:** 6 capability YAML + 11 story YAML + 8 INDEX updates + 1 gap report = 26 files
