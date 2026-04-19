# Offer Studio Schemas — Latam Refinement

**Sprint:** Task B (2026-04-19)
**Scope:** 15 schemas revisados con lente microempresario Latam + sales-agent
grounding + post-venta + legal compliance.
**Resultado:** 6 commits atómicos, 7 arch tests ratchet nuevos, 97 schema
tests verdes, 0 typecheck errors.

## Filosofía del refactor

Los schemas no se reescribieron por escribir. Se aplicó una lente de 4 ejes
a **cada field** de los 22 schemas del registry (los 15 del scope de B +
los 7 ya refinados en Sprints previos — identity, promise, gallery,
location, pricing, knowledge, lifecycle):

1. **¿Un microempresario Latam entiende la pregunta sin jerga marketer?**
2. **¿El hint le da un ejemplo concreto de su rubro y geografía?**
3. **¿El sales-agent lo consume para cerrar / descalificar / negociar?**
4. **¿Genera dispute post-venta si queda vago o vacío?**

Schemas que ya eran sólidos (testimonials, portfolio) recibieron
enriquecimientos quirúrgicos. Schemas débiles (service-details sin
scope-out, product-details sin carriers Latam) recibieron adiciones
arquitectónicas justificadas.

## Principios técnicos aplicados

| Principio | Aplicación |
|---|---|
| **Zero dead fields** | Fields que vivían en zod sin exposición (revision_rounds, min_contract_months, trial_period_days, community_invite_link, lms_url) se surface al editor |
| **Enum tipado sobre text libre** | Nuevos enums: `ServiceCommunicationChannel`, `ContentUpdateFrequency`, `MealsIncludedLevel`, `EventLanguage` |
| **Dedup cross-module** | INSTRUCTORS delega a brand-studio/team (no duplica). PRICING referencia Connections (payment providers). LOCATION referencia Scheduling (event types) |
| **JSONB para flexibilidad** | Fields nuevos específicos a Latam (`shipping_carriers_accepted`, `cultural_trust_barriers`) persisten en `specific_details` JSONB sin migración backend |
| **Hints example-driven** | Placeholders y hints con ejemplos reales Latam (Nutri con consultorio en Lima, kinesiólogo con paquete de 10 sesiones) en vez de abstracciones |
| **Legal compliance explícito** | Permission to publish (LGPD/Habeas Data), auto-renewal notices (LFPC México), accessibility (AR Ley 26.378) |

## Cambios por grupo

### Grupo 1 — Archetype cores (5 schemas, commit `4e610c83`)

| Schema | Antes | Después | Cambios clave |
|---|---|---|---|
| service-details | 121 líneas, 12 fields | ~220 líneas, 17 fields | +scope_excluded (anti scope creep), +response_time_hours (SLA), +primary_communication_channel, surface revision_rounds + min_contract_months |
| program-details | 153 líneas, 10 fields | ~270 líneas, 14 fields | +weekly_time_commitment_hours (pregunta #1 prospecto), +prerequisites_text, surface is_application_required + community_invite_link + lms_url + homework_submission_required |
| subscription-details | 68 líneas, 5 fields | ~160 líneas, 10 fields | +auto_renewal_with_notice_days (legal LATAM), +grace_period_days_on_failed_payment, +cancellation_anticipation_days, +content_update_frequency enum, surface tier_name + trial_period_days |
| event-details | 115 líneas, 12 fields | ~250 líneas, 21 fields | +what_to_bring, +meals_included enum, +language_spoken enum, +accessibility_notes (legal AR/CL), +refund_deadline_days, +rsvp_deadline, +checkin_start_time, +is_family_friendly, +age_restrictions, +live_streamed_secondary_url |
| product-details | 90 líneas, 8 fields | ~185 líneas, 14 fields | +shipping_carriers_accepted (Latam real), +shipping_estimate_by_region, +return_policy_days, +sample_preview_url, +packaging_description, surface is_downloadable + sku_inventory_code + shipping_weight_grams |

Zod schemas extendidos: ServiceDetailsSchema, ProgramDetailsSchema,
SubscriptionDetailsSchema, EventDetailsSchema, ProductDetailsSchema.

### Grupo 2 — Pre-venta universal (4 schemas, commit `9257c490`)

| Schema | Cambios clave |
|---|---|
| strategy | Placeholders con ejemplos Latam reales (Nutri Ale 32 años); hints en avatar_id, pain_points, desires, anti_avatar_keywords con ejemplos 5+ líneas |
| psychology | +cultural_trust_barriers captura 5 barreras Latam específicas que el agent ignora sin este field; 8 ejemplos de objections Latam honest |
| value-stack | +total_perceived_value_anchor (headline USD), +stack_positioning_statement (frase cierre), +item_type enum (core/bonus/fast_action) |
| closing | +refund_process_description (crítico Latam — cómo se devuelve por método), +scarcity_reason_honest (anti-fake), +bonus_if_act_now, +support_duration_days |

### Grupo 3 — Social proof (3 schemas, commit `df2d0980`)

| Schema | Cambios clave |
|---|---|
| instructors | +authority_positioning_for_sales (narrativa que el agent lee al presentar al equipo) |
| testimonials | +permission_to_publish + consent_date por item (legal LGPD/Habeas Data/LOPD) |
| portfolio | +case_period_start/end (contexto temporal), +team_involvement, +permission_to_publish |

Patrón senior aplicado: estos schemas ya eran sólidos — enriquecimiento
quirúrgico sin inflación.

### Grupo 4 — Post-venta + soporte (2 schemas, commit `ddca9479`)

| Schema | Cambios clave |
|---|---|
| resources | +availability_window_description (evita tickets "no encuentro el recurso") |
| faq | +is_answered_by_agent flag (distingue FAQs críticas pagos/devoluciones donde el agent NO puede improvisar vs informativas solo-landing) |

### Grupo 5 — SaaS + arch tests ratchet (commit `a8c5f72e`)

| Schema / test | Cambios clave |
|---|---|
| platform-details | +ai_features_disclosure (transparencia IA — exigencia creciente Latam), +data_export_capability (derecho portabilidad), security_compliance país-por-país (LGPD/Habeas Data/PDPL) |
| quality.test.ts | 7 arch tests ratchet nuevos |

## Arch tests ratchet agregados

Archivo: `frontend/src/features/offer-studio/schemas/__tests__/quality.test.ts`

| Test | Enforza | Por qué importa |
|---|---|---|
| `hint-coverage` | Todo field no-custom tiene hint o placeholder | Microempresarios Latam necesitan guía — sin hint es pregunta a ciegas |
| `no-technical-jargon-in-labels` | Labels no contienen "specific_details", "path", "enum value" | Leaks de vocabulario interno pierden al usuario |
| `unique-paths-within-schema` | No 2 fields con mismo path en mismo schema | Silent overwrites al guardar |
| `enum-≥2-options` | Enums tienen al menos 2 opciones | Enum de 1 opción es constant disfrazado |
| `enum-labels-non-empty` | Toda option tiene label | Renderizado roto |
| `mixed-scope-owner-required` | MIXED schemas declaran owner per field | Dispatcher del form runtime lo requiere |
| `single-owner-no-redundant-owner` | offer_level / edition_level no declaran owner redundante | Owner implícito en scope |

**Ratchet pattern:** una vez que estos tests pasan, cualquier cambio futuro
que los rompa falla CI. Ratchet solo puede encogerse — no agregar legacy.

## Impacto cross-layer

| Layer | Archivo | Cambios |
|---|---|---|
| Backend zod-adjacent types | `types/schema.ts` | +10 fields zod en 5 schemas + 4 enums nuevos (ServiceCommunicationChannel, ContentUpdateFrequency, MealsIncludedLevel, EventLanguage) |
| Frontend form schemas | `schemas/*.schema.ts` | 15 schemas actualizados, 1.460 líneas originales → ~2.000 líneas post-refinement (+37% por hints ricos) |
| Arch tests | `schemas/__tests__/quality.test.ts` | Nuevo — 7 tests |

Commits totales:
- `4e610c83` — Grupo 1 archetype cores
- `9257c490` — Grupo 2 pre-venta universal
- `df2d0980` — Grupo 3 social proof
- `ddca9479` — Grupo 4 post-venta
- `a8c5f72e` — Grupo 5 + quality ratchet

## Validación final

- Frontend arch tests: **16/16** pasan
- Frontend schema tests: **97/97** pasan (90 pre + 7 ratchet nuevos)
- Backend arch tests: **332/332** pasan (preset catalog + extraction contract + DDD + todos los demás)
- TypeScript: **0 errors**
- Lint: **0 errors**

## Relación con Sprint 12 (Preset Catalog)

Los refinamientos de schemas están alineados con los `suitability_note_es`
de los 76 presets del catalog:

- Preset `salud_paquete_tratamiento` dice "documentá qué incluye cada
  sesión" → schema `program-details` ahora tiene `curriculum` con hint
  específico + `weekly_time_commitment_hours`
- Preset `consultor_proyecto_scope` dice "scope-in/scope-out con brutal
  claridad" → schema `service-details` ahora tiene `scope_excluded` como
  field dedicado
- Preset `anfitrion_retiro` dice "alojamiento incluido vs no es
  decisivo" → schema `event-details` ahora tiene `accommodation_type`
  (existente) + `meals_included` (nuevo) + `what_to_bring` (nuevo)
- Preset `salud_consulta_unica` dice "obras sociales aceptadas" → schema
  `pricing` ya tenía field custom para payment providers referenciando
  Connections module

Esta alineación es lo que permite al sales-agent tener grounding rico:
cuando un lead pregunta "¿qué incluye?", "¿cuántas horas por semana?",
"¿cómo se devuelve el dinero si no me sirve?", el agent tiene respuestas
específicas en lugar de improvisar.

## Pending / futuro

- **Sprint 13** (wizard integration): el wizard rehecho debe renderizar
  estos schemas refinados. Los hints tan ricos son un regalo para la UX.
- **Backend DTO extensions** (opcional): los fields nuevos persisten hoy
  en `specific_details` JSONB. Si en Sprint 14+ el sales-agent necesita
  indexarlos o query-ear por ellos, promover a columnas backend.
- **i18n**: los labels y hints están en español Latam. Si se internacionaliza
  a otros idiomas, extraer a locale files — no hacer todavía (YAGNI).
- **Copilot integration**: el copilot debería leer `hint` + `placeholder`
  para asistir al usuario a llenar cada field. Sprint 14+.
