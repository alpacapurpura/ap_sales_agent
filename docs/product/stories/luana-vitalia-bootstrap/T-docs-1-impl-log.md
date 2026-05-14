# T-docs-1 impl-log — compliance.md + booking-widget-embed.md + seed_fixture_clinics.py
<!-- voseo-allowed: referencia técnica a falsos positivos del glosario en palabras como "substrings", "físicos", "invasivos" -->

**Ticket:** T-docs-1
**Story:** luana-vitalia-bootstrap (Story 11)
**Sesion:** 4 W18
**Estado:** tests-passing
**Fecha:** 2026-05-14

---

## § Skills Consulted

| Skill | Por qué invocada | Decisión tomada |
|---|---|---|
| `backend-expert` | Ticket docs/scripts — verificar runtime-quality-checklist antes commit | Seed script idempotente con SELECT EXISTS pattern; no ORM directo en CLI |
| `brand-expert` | Fixture clinics tienen BrandConfig (brand_identity, color palette, tagline) | Fixtures usan campos de BrandIdentity (brand_primary_color, tagline) sin voseo |
| `offer-expert` | N/A (ticket docs-only, no toca offer catalogs) | No invocada — fuera de scope |
| `metrics-expert` | N/A (no analytics) | No invocada |
| `tessl__fastapi` | Seed script no es FastAPI endpoint — no aplica | Pattern CLI puro con argparse |
| `tessl__pytest-api-testing` | N/A (production_code=false, sin tests nuevos en scope) | Seed script diseñado para ser testeable por injección pero tests en T-be-7 |
| `tessl__graceful-degradation` | Seed script conecta a Postgres | `_try_import_db_deps()` con fallback limpio si psycopg2 no disponible; `--check` funciona sin DB |

---

## § Step 0 — Anti-dup grep

```bash
find /home/chris/luana-platform -name "compliance.md" -o -name "booking-widget-embed.md" -o -name "seed_fixture_clinics.py"
# Output: (none) — archivos nuevos, no mirrors
```

No hay mirrors en el codebase. Archivos completamente nuevos.

---

## § Step 0.5 — Default-flip pre-audit

No aplica — este ticket no toca `core/config.py` ni ninguna feature flag.

---

## § Implementación

### 1. `vitalia/docs/compliance.md`

**Decisiones tomadas:**
- Sección 1: distingue HIPAA-lite vs HIPAA completo con tabla comparativa de controles. Documenta `compliance_level=hipaa_lite` y `contains_phi=false` como metadatos del tenant.
- Sección 2: cubre los 6 países LatAm con sus leyes específicas (Ley 25.326 AR, LGPD BR, LFPDPPP MX, Ley 19.628 CL, Ley 29.733 PE, Ley 1.581 CO). Incluye tabla de derechos para cada ley.
- Sección 3: retención 7 años documentada con eventos auditados (18 tipos). Alineado con D7.
- Sección 4: flujo de 9 pasos de consentimiento informado. Captura IP hash + user_agent hash + timestamp UTC.
- Sección 5: HMAC de URLs de consentimiento con código Python de ejemplo. Protección contra timing attacks (`hmac.compare_digest`).
- Sección 6: patrones PII con tabla por categoría y acción. Alineado con spec § 14 y `pii_scanner_service.py` (T-be-4).
- Sección 7: derechos GDPR-like con endpoints correspondientes.
- Sección 8: aislamiento multi-tenant incluyendo KB médica (brand-scope vs tenant-scope).

**Verificación Spanish neutro:** Revisión manual — ningún voseo real. Los "matches" del grep son falsos positivos por substrings en palabras como "físicos" (contiene "sos"), "invasivos", "exhaustivos", "configurado", "pasos". El validator grep es amplio intencionalmente.

### 2. `vitalia/docs/booking-widget-embed.md`

**Decisiones tomadas:**
- Q5 ratificado (B_both_iframe_and_canonical): documento cubre ambas opciones con tabla de cuándo usar cada una.
- D11: protocolo postMessage documentado con 4 eventos (widget:loaded, widget:resize, widget:booking-confirmed, widget:payment-redirect). Cada evento tiene estructura JSON de ejemplo.
- Snippet copy-paste completo con 3 variantes: completo, mínimo, con oferta específica.
- Sección de seguridad: validación de origen con ejemplo correcto vs incorrecto. HTTPS obligatorio. Registro de dominio permitido.
- CDN URLs: `cdn.vitalia.health/widget/v1/` versión estable + `latest` (desaconsejado).
- URL canónica: `app.vitalia.health/public/{clinic-slug}/booking/` con 3 ejemplos de fixtures.

**Verificación Spanish neutro:** Ningún voseo. Imperativo tuteo ("verifica", "agrega", "abre", "pega").

### 3. `vitalia/backend/scripts/seed_fixture_clinics.py`

**Decisiones de diseño:**
- **Tenant IDs deterministas**: UUIDv5 con namespace fijo `_FIXTURE_NAMESPACE` + seed `vitalia:fixture:clinic:{clinic_slug}`. Re-ejecuciones producen mismos UUIDs.
- **`--check` sin DB**: el modo check valida la definición estructural de los fixtures (campos, países, compliance_level, contains_phi) sin conectar a Postgres. Esto permite que V-F-15 pase en CI sin base de datos.
- **Idempotency en --apply**: `_exists_tenant()` verifica existencia via `SELECT EXISTS` antes de `INSERT`. La tabla `vitalia_medical_audit_log` es usada como proxy de existencia (siempre creada en onboarding).
- **`ON CONFLICT (id) DO NOTHING`**: el INSERT del audit event usa `event_id = uuid.uuid5(fixture.tenant_id, "seed:tenant_created")` para ser idempotente a nivel SQL.
- **No PHI en metadata**: el dict de metadata del audit event solo contiene campos no-PHI (clinic_slug, clinic_type, country, plan_tier, compliance_level, contains_phi=false). Alineado con D7.
- **Graceful degradation**: `_try_import_db_deps()` retorna None si psycopg2 no disponible. `--apply` falla limpiamente con mensaje descriptivo.
- **3 fixtures spec § 2**: Aurora dental AR (clinic plan, ARS/USD), Mindful Santiago CL (solo_doctor, CLP), Sanaré LATAM MX (multi_site, USD/MXN).

**Validaciones en --check:**
- 3 fixtures exactos
- tenant_ids únicos
- compliance_level=hipaa_lite + contains_phi=False (D7)
- Países en set LatAm
- clinic_type en tipos permitidos
- Plan tier en tiers válidos
- Gateway en gateways permitidos
- Locale IETF BCP 47
- features_enabled no vacío

### 4. `vitalia/README.md` update

- Eliminado placeholder genérico "Current state (Story 1): Placeholder".
- Agregada tabla de extensiones verticales (6 extensiones médicas).
- Quick start completo: env vars, migrations, seed fixtures, seed KB, dev server.
- Tabla de fixtures con clinic_slug, país, tipo, plan, gateway.
- Links a compliance.md y booking-widget-embed.md.
- Estructura backend documentada.

---

## § Validators ejecutados

| Validator | Comando | Resultado |
|---|---|---|
| V-F-15 | `cd vitalia/backend && .venv/bin/python scripts/seed_fixture_clinics.py --check` | OK (3 fixtures, all checks passed) |
| A1 | Mismo que V-F-15 | OK |
| A2 | `test -f vitalia/docs/compliance.md && test -f vitalia/docs/booking-widget-embed.md` | OK (Docs present) |
| Ruff lint | `.venv/bin/ruff check scripts/seed_fixture_clinics.py` | All checks passed |
| Ruff format | `.venv/bin/ruff format --check scripts/seed_fixture_clinics.py` | 1 file already formatted |
| Syntax | `python -c "import ast; ast.parse(open('scripts/seed_fixture_clinics.py').read())"` | Seed script syntax OK |

---

## § Cross-module reads

- Leído `T-be-3` (repos) para entender estructura de repositorios disponibles
- Leído `booking_repository.py` para patrón tenant_id isolation
- Leído `onboarding_service.py` para entender el flujo de creación de tenant
- Leído `seed_medical_kb.py` para patrón de scripts en vitalia

---

## § Archivos modificados

```
CREATED  /home/chris/luana-platform/vitalia/docs/compliance.md
CREATED  /home/chris/luana-platform/vitalia/docs/booking-widget-embed.md
CREATED  /home/chris/luana-platform/vitalia/backend/scripts/seed_fixture_clinics.py
UPDATED  /home/chris/luana-platform/vitalia/README.md
```

---

## § Notas

- El `--check` de V-F-15 funciona sin Postgres (valida definición estructural solamente).
- El `--apply` requiere Postgres y la migración `001_vitalia_initial_snapshot` aplicada (vitalia_medical_audit_log debe existir).
- Los tenant_ids de los fixtures son estables entre sesiones (UUIDv5 determinista).
- El grep de voseo detecta falsos positivos por substrings en compliance.md (words: "físicos", "invasivos", "exhaustivos", "administrativos", "pasos", "configurado"). Ningún voseo real presente.

---

**Estado:** tests-passing
