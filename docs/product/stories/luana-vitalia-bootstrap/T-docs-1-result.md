# T-docs-1 result — compliance.md + booking-widget-embed.md + seed_fixture_clinics.py

**Ticket:** T-docs-1
**Story:** luana-vitalia-bootstrap (Story 11)
**Sesion:** 4 W18
**Estado:** tests-passing
**Fecha:** 2026-05-14

---

## Deliverables

### 1. `vitalia/docs/compliance.md` — DONE

Archivo creado en `/home/chris/luana-platform/vitalia/docs/compliance.md`.

Cubre:
- HIPAA-lite vs HIPAA completo (tabla comparativa de controles)
- `compliance_level=hipaa_lite` + `contains_phi=false` documentados (D7)
- 6 leyes LatAm: Ley 25.326 AR, LGPD BR, LFPDPPP MX, Ley 19.628 CL, Ley 29.733 PE, Ley 1.581 CO
- Derechos de datos por país (acceso, rectificación, cancelación, portabilidad, oposición)
- Retención audit log 7 años con 18 tipos de eventos auditados
- Flujo de captura de consentimiento (9 pasos con IP hash + user_agent hash)
- Verificación HMAC de URLs de consentimiento (código Python + anti timing-attack)
- Patrones PII detectados por categoría (tabla aligned con spec § 14)
- Derechos de exportación y eliminación (endpoints vía API REST)
- Aislamiento multi-tenant

### 2. `vitalia/docs/booking-widget-embed.md` — DONE

Archivo creado en `/home/chris/luana-platform/vitalia/docs/booking-widget-embed.md`.

Cubre:
- Snippet copy-paste completo (3 variantes: completo, mínimo, oferta específica)
- Protocolo postMessage documentado con 4 eventos (D11):
  - `widget:loaded` — widget listo
  - `widget:resize` — ajuste de altura
  - `widget:booking-confirmed` — reserva completada (booking_id, amount, currency)
  - `widget:payment-redirect` — redirección a procesador de pago
- URL canónica alternativa: `app.vitalia.health/public/{clinic-slug}/booking/`
- CDN: `cdn.vitalia.health/widget/v1/vitalia-widget.js`
- Seguridad: validación de origen MUST (`event.origin !== 'https://cdn.vitalia.health'`), HTTPS obligatorio, registro de dominio permitido
- Opciones de configuración: `data-*` attributes documentados
- Tabla cuándo usar iframe vs URL canónica (Q5 B ratificado)
- Solución de problemas frecuentes

### 3. `vitalia/backend/scripts/seed_fixture_clinics.py` — DONE

Archivo creado en `/home/chris/luana-platform/vitalia/backend/scripts/seed_fixture_clinics.py`.

Fixtures seeded:

| Fixture | tenant_id (UUIDv5) | País | Tipo | Plan |
|---|---|---|---|---|
| `aurora-dental-ar` | `53fd1879-e76e-5311-a3c4-b7b10d7e734f` | AR | dental | clinic |
| `mindful-santiago-cl` | `562137bd-ea0a-5c04-9616-96d18f898a44` | CL | psychology | solo_doctor |
| `sanare-latam-mx` | `f426daa8-dc39-5515-811e-2c56b48246c9` | MX | psychiatry | multi_site |

Características:
- `--check`: valida definición sin DB (V-F-15 pasa en CI)
- `--apply`: idempotente via SELECT EXISTS + ON CONFLICT DO NOTHING
- `--reset`: elimina + re-inserta (para entornos de test)
- Tenant IDs deterministas via UUIDv5
- No PHI en metadata (D7: compliance_level=hipaa_lite, contains_phi=false)

### 4. `vitalia/README.md` — UPDATED

README actualizado con:
- Tabla de extensiones verticales (6 extensiones médicas)
- Quick start completo (env vars + migrations + seed fixtures + seed KB + dev server)
- Tabla de fixtures con todos los datos clave
- Links a compliance.md y booking-widget-embed.md
- Estructura del directorio backend documentada
- Comandos para tests y lint

---

## Validators

| ID | Descripción | Resultado |
|---|---|---|
| V-F-15 | `seed_fixture_clinics.py --check` idempotente | OK — 3 fixtures, all checks passed |
| A1 | Seed script `--check` sin DB | OK |
| A2 | compliance.md + booking-widget-embed.md presentes | OK — Docs present |
| Ruff lint | `ruff check scripts/seed_fixture_clinics.py` | All checks passed |
| Ruff format | `ruff format --check scripts/seed_fixture_clinics.py` | 1 file already formatted |
| Spanish neutro | Grep voseo en docs | OK — falsos positivos de substrings, cero voseo real |

---

## Notas para gate-runner / auditor

- `--apply` no se ejecutó porque requiere Postgres (A1 en el validator solo pide `--check`).
  `--check` valida la definición estructural y está diseñado para funcionar sin DB.
- El grep de voseo del validator produce falsos positivos por substrings ("físicos",
  "invasivos", "pasos", "exhaustivos"). El contenido real no tiene voseo — tuteo correcto.
- Los tenant_ids de fixtures son deterministas (UUIDv5) — mismos en toda ejecución.

---

**Estado:** tests-passing
