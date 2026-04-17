# PLAN — Offer Editions UI Revamp · Execution

> Phased implementation plan. Each phase is independently shippable. TDD obligatorio (ver `.claude/rules/tdd-mandatory.md`).
>
> **Reference:** `FLOW-SPEC.md`, `DECISIONS.md`, `UI-SPEC-*.md`, y `prototype/` como referencia visual normativa.
>
> **Estrategia:** backend-first (Phases 5-8) antes de frontend (Phase 9) para que el frontend pueda consumir endpoints reales. Phase 9 se divide en sub-fases (9a shell, 9b tabs, 9c closer, 9d copilot) para permitir review intermedio.

---

## Dependency graph

```
       ┌─────────────────┐
       │ Phase 5         │   Enrollment entity + events
       │ (backend)       │
       └────────┬────────┘
                │
                ├──────────────┐
                │              │
       ┌────────▼──────┐  ┌────▼─────────┐
       │ Phase 6       │  │ Phase 8      │
       │ Sales agent   │  │ Public URL   │
       │ tools + prompt│  │ routing      │
       └────────┬──────┘  └──────────────┘
                │
       ┌────────▼──────┐
       │ Phase 7       │   Copilot interview date block
       │ (backend)     │
       └────────┬──────┘
                │
   ┌────────────┼────────────┬────────────┬────────────┐
   │            │            │            │            │
   ▼            ▼            ▼            ▼            ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ 9a     │ │ 9b     │ │ 9c     │ │ 9d     │ │ 9e     │
│ Shell+ │ │ Tabs   │ │ Closer │ │ Copilot│ │ Polish │
│ rail   │ │        │ │ Studio │ │ interv.│ │        │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

---

## Phase 5 — Enrollment Entity

**Goal:** Persistir leads inscriptos en ediciones con estado + payment tracking.

### Work
1. **Migration 048 — `create_enrollments`** (`backend/alembic/versions/048_create_enrollments.py`)
   - Tabla `enrollments` (ver § 4.4 del FLOW-SPEC original).
   - Indexes: `ix_enrollments_tenant`, `ix_enrollments_edition`, `ix_enrollments_contact`, `ix_enrollments_waitlist`, `ix_enrollments_status`.
   - Todo `IF NOT EXISTS`. Test con `pg_dump` a cloned DB.

2. **Domain** (`backend/src/modules/sales_agent/domain/enrollment.py`)
   - Entidad `Enrollment` Pydantic v2.
   - Enum `EnrollmentStatus`: `INTENT | WAITLIST | PAYMENT_PENDING | PAID | ATTENDED | REFUNDED | CANCELLED`.
   - Enum `PaymentProvider`: `STRIPE | MERCADOPAGO | CULQI | MANUAL`.
   - Invariants: `edition_id IS NULL ↔ status = WAITLIST`; `status=PAID → paid_at IS NOT NULL`; `status=ATTENDED → paid_at IS NOT NULL`; todas las queries con `tenant_id`.

3. **Events** (`backend/src/modules/sales_agent/domain/events.py`)
   - `EnrollmentCreated`
   - `EnrollmentPaid`
   - `EnrollmentStatusTransitioned`

4. **Infrastructure**
   - `enrollment_model.py`: SA model con `Base` async.
   - `enrollment_repository.py`: métodos `create`, `get_by_id(tenant_id)`, `list_by_offer(tenant_id, offer_id, filters)`, `list_waitlist(tenant_id, offer_id)`, `list_by_edition(tenant_id, edition_id, filters)`, `update_status`, `mark_paid`.

5. **Application** (`enrollment_service.py`)
   - `create(payload, tenant_id) → Enrollment` (valida edition si se provee, valida que offer existe).
   - `mark_paid(enrollment_id, provider, transaction_id, tenant_id) → Enrollment` (emite `EnrollmentPaid`).
   - `promote_waitlist(enrollment_ids, target_edition_id, tenant_id) → list[Enrollment]`.
   - `handle_edition_published(event)` handler: marca waitlisted como notifiables.

6. **API** (`api/enrollments.py`)
   - `POST /api/v1/sales-agent/enrollments` → crear (body: `EnrollmentCreateDTO`).
   - `GET /api/v1/sales-agent/enrollments?offer_id=&edition_id=&status=&contact_id=` → listado filtrable.
   - `GET /api/v1/sales-agent/enrollments/waitlist?offer_id=` → sólo waitlist.
   - `PATCH /api/v1/sales-agent/enrollments/{id}/status` → transición manual.
   - `POST /api/v1/sales-agent/enrollments/{id}/mark-paid` → mark paid manual.
   - `POST /api/v1/sales-agent/enrollments/promote-waitlist` → bulk promote (body: `{enrollment_ids, target_edition_id}`).
   - **Todos con `response_model=` Pydantic.**

### TDD (escribir PRIMERO)
- `tests/modules/sales_agent/test_enrollment_domain.py`
  - `test_enrollment_with_null_edition_must_be_waitlist`
  - `test_enrollment_paid_requires_paid_at`
  - `test_enrollment_attended_requires_paid`
- `tests/modules/sales_agent/test_enrollment_repository.py`
  - CRUD + tenant isolation
  - `test_list_waitlist_filters_by_null_edition_and_status_waitlist`
- `tests/modules/sales_agent/test_enrollment_service.py`
  - Happy paths + event emission
- `tests/modules/sales_agent/test_enrollment_api.py`
  - Endpoints + auth + response models

### Acceptance
- Todas las migraciones idempotentes (test con `pytest tests/infrastructure/test_migrations.py` si existe).
- Crear enrollment con edición, transition a PAID, query waitlist, promote — todo funciona.
- Tenant isolation verificado por test.
- 0 errores ruff, 0 errores arch tests.

### Verify commands
```bash
cd backend && .venv/bin/pytest tests/modules/sales_agent/ -x -q --tb=short
cd backend && .venv/bin/pytest tests/architecture/ -x -q
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test_phase5;"
# seed + apply migration, verify structure
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test_phase5;"
```

### UI-SPECs consumed
- Ninguna UI en Phase 5 (backend-only).

**Effort:** 10-12h · Commits: 3 · Files: 12

---

## Phase 6 — Sales Agent Edition Awareness

**Goal:** Agente conoce ediciones, puede inscribir leads, generar links de pago, manejar waitlist.

### Work
1. **Tools** (`backend/src/modules/sales_agent/application/tools/`)
   - `list_public_editions.py` → retorna `list[EditionPublicDTO]` filtrando `UPCOMING/ACTIVE + PUBLIC` (incluye ticker/precio activo calculado por `resolve_active_tier`).
   - `create_enrollment.py` → crea `Enrollment` vinculado a conversación, status `INTENT`.
   - `generate_payment_link.py` → delega a `ConnectionsService.create_payment_intent(provider, amount, metadata={enrollment_id})` y guarda `payment_link_url`.
   - `check_payment_status.py` → polling a provider API si webhook falló.
   - `mark_enrollment_paid_manual.py` → sin pasar por webhook, user marca manualmente.
   - `list_waitlist.py` → para cuando lead pregunta por oferta sin edición pública.
   - `promote_waitlist_to_edition.py` → bulk action "Notificar a todos".

2. **Prompt update** (`infrastructure/prompts/templates/agent_identity.j2`)
   - Bloque nuevo: "Edition awareness" con reglas:
     - "When a lead expresses purchase intent, always call `list_public_editions(offer_id)` first."
     - "Never propose an edition where `status ∈ {DRAFT, CANCELLED, COMPLETED}` o `visibility === PRIVATE`."
     - "If no public edition exists, offer waitlist con `list_waitlist + create_enrollment(edition_id=null)`."
     - "Cuando un lead confirma intent, emitir `create_enrollment` (INTENT) antes de pedir pago."
     - "Para generar pago, usar `generate_payment_link(enrollment_id)`; guarda `payment_link_url` en enrollment."

3. **Registry** (`copilot/application/tools/registry.py`, `module_registry.py`)
   - Agregar tools al route-based tool map.
   - Agregar `Enrollment` a `MODULE_REGISTRY`.

4. **Webhooks integration**
   - `connections/infrastructure/webhooks/stripe.py`: extender `webhook_handler` para parsear `payment_intent.succeeded` con `metadata.enrollment_id` → emitir `EnrollmentPaid`.
   - Mismo para `mercadopago.py` y `culqi.py` (si existen).
   - Handler `on_enrollment_paid` actualiza `enrollment.status = PAID`, `paid_at = utc_now()`, y `edition.enrollment_count += 1` (con row lock).

### TDD (escribir PRIMERO)
- Tests por tool con mock `ConnectionsService`.
- `test_list_public_editions_excludes_draft_and_private`
- `test_generate_payment_link_uses_active_tier_price`
- `test_promote_waitlist_bulk_transitions_to_payment_pending`
- Integration: simulate webhook → verify event → verify DB update.

### Acceptance
- E2E con Stripe test mode: lead chat → agente list → create enrollment → payment link → webhook simulate → status=PAID automatic.
- Waitlist flow: create with edition=null → list waitlist → promote with target edition → status transitions + message sent (mock).

### Verify commands
```bash
cd backend && .venv/bin/pytest tests/modules/sales_agent/tools/ -x -q
cd backend && .venv/bin/pytest tests/modules/sales_agent/test_agent_prompt.py -x -q
cd backend && .venv/bin/pytest tests/architecture/test_extraction_contract.py -x -q
```

**Effort:** 14-16h · Commits: 4-5 · Files: 18

---

## Phase 7 — Copilot Interview Date Block

**Goal:** Copiloto pregunta obligatoriamente "¿cuándo tu primera edición?" al final del wizard.

### Work
1. **Interview config** (`copilot/domain/interview_configs/offer_config.py`)
   - Agregar bloque final `first_edition_date` con schema:
     ```python
     {
       "id": "first_edition_date",
       "question_es": "Antes de cerrar, ¿cuándo planeas tu primera {edition_noun_es}?",
       "question_es_fallback": "Antes de cerrar, ¿cuándo planeas tu primera edición?",
       "quick_replies": [
         {"type": "date_suggestion", "label": "📅 El {suggested_date}", "auto_generated": true},
         {"type": "date_picker", "label": "📅 Elegir fecha..."},
         {"type": "skip", "label": "🤷 Todavía no sé"}
       ],
       "required": true,
       "skippable_with_warning": "Sin fecha la edición queda privada y los leads van a waitlist."
     }
     ```
   - Condicional: sólo aparece si `offer.archetype.supports_editions === true`.

2. **Schema extension** (`copilot/domain/schemas/offer_create_input.py`)
   - Agregar opcional `first_edition: FirstEditionInput | None`:
     ```python
     class FirstEditionInput(BaseModel):
         start_date: datetime | None = None
         location_override: dict[str, Any] | None = None
         # otros campos opcionales si el copilot los captura
     ```

3. **Procedure** (`copilot/application/procedures/offer_creation.py`)
   - Al completar interview:
     1. Crear offer (ya funciona, emite `OfferCreated`).
     2. `OfferCreated` handler crea placeholder edition (ya funciona Phase 2).
     3. **NUEVO:** si `first_edition.start_date` presente → update placeholder con `start_date`, transition a `UPCOMING` + `visibility=PUBLIC`.
     4. Redirect respuesta a `/offer-studio/offer/{id}?edition={editionId}`.

4. **Copy generation**
   - Generar "suggested_date" usando contexto (ej. si usuario dijo "Julio" en algún bloque, sugerir el 15 del mes siguiente-siguiente).
   - Si no hay hint, sugerir "+6 semanas desde hoy" (lunes más próximo).

### TDD
- `test_interview_offer_with_editions_captures_first_edition`
- `test_interview_offer_without_editions_skips_date_block` (archetype PRODUCTO → no bloque)
- `test_skip_keeps_placeholder_draft`
- `test_date_given_publishes_edition`

### Acceptance
- E2E: crear oferta PROGRAMA via interview con fecha → offer + edición UPCOMING + visible.
- Crear oferta PROGRAMA via interview sin fecha → offer + edición DRAFT placeholder.
- Crear oferta PRODUCTO → interview no pregunta fecha.

### UI-SPECs consumed
- `UI-SPEC-copilot-interview.md` § 3 (aunque es backend, el schema lo consume el frontend del interview).

**Effort:** 8-10h · Commits: 3 · Files: 6

---

## Phase 8 — Public URL Routing Per Edition

**Goal:** URL pública resuelve a edición activa y permite deep link a edición específica.

### Work
1. **Backend resolver** (`landing/api/public.py`)
   - `GET /public/{tenant_slug}/{offer_slug}` → buscar `offer` por slug, buscar edición ACTIVE (o UPCOMING más próxima si no hay ACTIVE) PUBLIC, 302 redirect a `/public/{tenant_slug}/{offer_slug}/edicion/{edition_number}`.
   - `GET /public/{tenant_slug}/{offer_slug}/edicion/{n}` → serve landing scoped a esa edición; fallback a offer-level si la edición no tiene landing propia.

2. **Slug lookup** (`landing/infrastructure/repositories/public_landing_repository.py`)
   - Metodo `find_active_edition_for_offer(tenant_slug, offer_slug)` → un query que joinea tenants + offers + launch_editions.

3. **Landing repo extension** — ya existe per-edition (Phase 3), agregar método `get_by_offer_and_edition_number`.

4. **Frontend (sólo shells)**
   - `app/_public/[tenantSlug]/[offerSlug]/page.tsx` → server component que hace fetch y redirect.
   - `app/_public/[tenantSlug]/[offerSlug]/edicion/[number]/page.tsx` → server component que renderiza la landing.

### TDD
- Test smoke: `/public/maca/masterclass-copy` → 302 → `/public/maca/masterclass-copy/edicion/3`.
- Test smoke: `/public/maca/masterclass-copy/edicion/2` → 200 con landing de #2 (completada, read-only).
- Test slug injection / tenant isolation.

### Acceptance
- Public URLs funcionan + son tenant-safe (no leak cross-tenant).

**Effort:** 4-6h · Commits: 2 · Files: 5

---

## Phase 9a — Offer Shell + Editions Rail

**Goal:** Nuevo shell layout con rail permanente de ediciones, tab bar de 4 tabs, landing split-button, waitlist banner, clone modal.

**UI-SPEC:** `UI-SPEC-offer-studio-shell.md` (todas las secciones).
**Prototype:** `prototype/offer-studio/offer-info.html` + `offer-info-edition2.html` + `offer-no-editions.html`.

### Work
1. **Components** (ver § 7 del FLOW-SPEC):
   - `EditionsRail.tsx` + `EditionsRailCollapsed.tsx`
   - `LandingSplitButton.tsx`
   - `WaitlistBanner.tsx`
   - `EditionCloneModal.tsx`

2. **Refactor** (existing components):
   - `OfferShell.tsx` — acepta `currentEditionId` y renderiza rail + collapsed variant; layout `grid` con 3 columnas (app sidebar fijo · rail · main).
   - `OfferTabBar.tsx` — 4 tabs fijos + badge counts + landing split-button a la derecha.
   - `OfferShellHeaderRow1.tsx` — title con nombre oferta + " · Edición #N · fecha" cuando edition presente.
   - `OfferShellHeaderRow2.tsx` — remover botón landing.

3. **Routing**:
   - Update `app/.../offer/[id]/page.tsx` → leer `?tab=` y `?edition=` de searchParams.
   - Delete `/assets/page.tsx`, `/campaigns/page.tsx`, `/knowledge/page.tsx`.

4. **Hooks**:
   - `use-offer-with-edition.ts` — resuelve edición activa (query param ?edition= o fallback a "próxima" computed).

### TDD (frontend)
- `EditionsRail.test.tsx`: renders 3 grupos correctamente, destaca próxima, muestra placeholder amber, toggle collapsed.
- `LandingSplitButton.test.tsx`: rendea correcto label según `landingStatus`, dropdown abre/cierra.
- `WaitlistBanner.test.tsx`: no visible si count=0, visible con 2 acciones si count>0.
- `OfferShell.test.tsx`: rail hidden cuando `offer.has_editions === false`, visible si true.
- `EditionCloneModal.test.tsx`: flujo seleccionar fuente + strategy + confirmar.

### E2E
- `smoke/offer-editions.spec.ts`: abre oferta, verifica rail visible, switch entre ediciones, tab switch.

### Acceptance
- Todas las 3 variants del prototipo funcionan en app (ed #3 activa, #2 read-only, PRODUCTO no-rail).
- 0 errores ESLint nuevos, 0 regresiones en vitest.
- Architecture tests pasan (file naming, hooks location, etc.).

### Verify commands
```bash
cd frontend && npx vitest run src/features/offer-studio/
cd frontend && npx tsc --noEmit
cd frontend && npx eslint src/features/offer-studio/ --cache
cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke --grep "offer-editions"
```

**Effort:** 18-22h · Commits: 6-8 · Files: 15

---

## Phase 9b — Offer Tabs Content

**Goal:** Content funcional de los 4 tabs: Info, Ventas, Assets, Campañas.

**UI-SPEC:** `UI-SPEC-offer-studio-tabs.md`.
**Prototype:** `offer-info.html`, `offer-ventas.html`, `offer-assets.html`, `offer-campanas.html`.

### Work por tab

**Info** (mayor esfuerzo):
- `OfferInfoTab.tsx` compone 7 secciones.
- `IdentitySection.tsx`, `DatesSection.tsx`, `PricingTiersSection.tsx`, `DeliverablesSection.tsx`, `AudienceSection.tsx`, `GuaranteeOnboardingSection.tsx`, `KnowledgeSection.tsx`.
- Cada section es editable inline (form con RHF + Zod).
- `PricingTiersSection` reutiliza timeline del prototipo y permite CRUD de tiers.

**Ventas**:
- `OfferVentasTab.tsx` con KPI strip + filters + table.
- `EnrollmentsTable.tsx` (scoped a edición actual).
- Deep-link CTA a `/sales/enrollments?edition={id}`.

**Assets**:
- `OfferAssetsTab.tsx` con placeholder banner + filter pills + gallery grid.
- `AssetGallery.tsx` scoped a edición actual.
- Click tile → abre modal "Próximamente" (editor Canva-like es fase 2).
- Botón "Jalar de Edición #N" → abre `AssetCloneModal` (ya existe).
- Botón "Generar con IA" → stub por ahora.

**Campañas**:
- `OfferCampanasTab.tsx` con explainer banner + KPI strip + campaign cards list.
- `CampaignCard.tsx` con platform icon + KPIs + link a Growth Studio.
- Botón "+ Asociar campaña existente" → abre picker (lista campañas sin asociar).
- Orgánico placeholder en el bottom.

### TDD
- Tests por section y por tab.
- Test integration: switch edición en rail → contenido del tab actualiza.

### Acceptance
- Pixel-close al prototipo.
- Inline editing funciona en Info con autosave.
- Ventas + Campañas muestran datos reales.
- Assets muestra gallery aunque stub del editor.

**Effort:** 24-30h · Commits: 8-10 · Files: 20

---

## Phase 9c — Closer Studio Changes

**Goal:** Página global `/sales/enrollments` + EnrollmentWidget en inbox.

**UI-SPEC:** `UI-SPEC-closer-studio.md`.
**Prototype:** `sales/enrollments.html`, `sales/inbox.html`.

### Work
1. Sidebar add entry (ver `UI-SPEC-sidebar-restructure.md`).
2. Route `/sales/enrollments/page.tsx`.
3. `EnrollmentsPage.tsx` con tabla grouped + filters + waitlist block + bulk actions.
4. `EnrollmentWidget.tsx` en inbox side panel.
5. `use-enrollments.ts` + `use-active-enrollment-for-conversation.ts` hooks.

### TDD
- `EnrollmentsPage.test.tsx`: filters, groups, bulk action.
- `EnrollmentWidget.test.tsx`: 4 states (none / pending / paid / attended), acciones inline.

### Acceptance
- /sales/enrollments muestra todas las inscripciones filtrable.
- Widget aparece automáticamente en inbox cuando hay enrollment asociada a conversation.

**Effort:** 10-14h · Commits: 4 · Files: 8

---

## Phase 9d — Copilot Interview Frontend

**Goal:** Renderear el bloque de fecha del interview con split view + live preview.

**UI-SPEC:** `UI-SPEC-copilot-interview.md`.
**Prototype:** `copilot/interview-date.html`.

### Work
1. `InterviewDateBlock.tsx` con quick-replies + date picker + skip.
2. Live preview pane con card de la edición proyectada.
3. Extender interview state machine para incluir este bloque.

### TDD
- `InterviewDateBlock.test.tsx`: quick-reply disparan callbacks correctos; skip muestra warning.

### Acceptance
- Interview muestra pregunta de fecha obligatoriamente para archetypes con supports_editions.
- Preview actualiza en tiempo real según la fecha elegida.

**Effort:** 6-8h · Commits: 2 · Files: 3

---

## Phase 9e — Landing Editor (stub)

**Goal:** Ruta separada full-screen para el editor Puck per-edition.

**Prototype:** `offer-landing-editor.html`.

### Work
1. Ruta `app/.../offer/[id]/editions/[eid]/landing/page.tsx`.
2. `LandingEditorPage.tsx` con layout fullscreen (sin app sidebar ni rail).
3. Integración con Puck existente.
4. Tokens vinculados dinámicos (`{start_date}`, `{tier_active.price}`, etc.) — se renderizan desde datos de la edición.

**Stub si Puck integration no termina esta phase:** solo mostrar mensaje "Editor en construcción" con link "Volver a oferta".

### Acceptance
- Ruta funciona, abre en nueva pestaña desde split button.
- Al menos hero + pricing block se renderizan con datos reales.

**Effort:** 10-14h (con Puck) · 2-3h (stub) · Commits: 2-3

---

## Phase 10 — Per-Edition Analytics (Growth Studio)

**Goal:** Comparar métricas entre ediciones dentro de Growth Studio.

**Nota:** Esta phase **NO tiene cambios** en el Offer Studio (moviendo el tab Analytics afuera). Se implementa como nuevo feature de Growth Studio. Queda fuera del scope visual de esta sesión pero se documenta en el PLAN por completitud.

### Work (outline, no spec detallado acá)
- Extender `metrics_service` + stage services con dimensión `edition_id`.
- Nuevo endpoint `GET /api/v1/analytics/editions/compare?offer_id=`.
- Nueva ruta Growth Studio `/growth-studio/offers/{offerId}/editions-compare`.
- ETL updates para hacer `edition_id` resoluble desde landing page view y enrollments.

**Effort:** 12-16h · Commits: 3 · Files: 10

---

## Execution order recomendado

1. **Semana 1:** Phase 5 (Enrollment entity) → Phase 6 (tools). 24-28h.
2. **Semana 2:** Phase 7 (copilot backend) + Phase 8 (public URLs). 12-16h.
3. **Semana 3:** Phase 9a (shell + rail). 18-22h.
4. **Semana 4:** Phase 9b (tabs content). 24-30h.
5. **Semana 5:** Phase 9c (closer) + Phase 9d (copilot frontend) + Phase 9e (landing stub). 26-36h.
6. **Semana 6 (opcional):** Phase 10 (analytics Growth Studio).

**Total:** ~100-130h para un dev a full-time · ~25-35 commits.

---

## Risk & rollback

| Risk | Mitigation |
|---|---|
| Cambio de route params (`?edition=`) rompe bookmarks viejos | Mantener backward compatibility temporal: paths `/assets`, `/campaigns`, `/knowledge` hacen redirect 308 a nuevo layout con query params |
| Canva-clone editor no se termina en Phase 2 | Stub Assets tab funciona: gallery + clone + generate IA básicos sin editor inline |
| Webhooks de payment provider fallan | Polling `check_payment_status` + manual `mark_enrollment_paid` como fallback |
| Rail acapara espacio en mobile | Auto-colapsado si viewport < 1024px, full app sidebar + main (sin rail visible) |
| Waitlist bulk notification falla parcial | Best-effort: reportar qué contactos recibieron vs cuáles fallaron; retry manual |

## Commit convention

`feat(offer): phase 9a — offer shell with editions rail`
`feat(sales-agent): phase 5 — enrollment entity + events`
`feat(copilot): phase 7 — interview asks first edition date`

Siempre referenciar el phase #.

---

## Definition of Done (global)

- ✅ Backend: 0 errores ruff, 0 arch tests fallidos, cobertura ≥43%.
- ✅ Frontend: 0 errores tsc, 0 ESLint errors, 0 regresiones vitest, cobertura ≥20% (actual 25%).
- ✅ E2E smoke tests pasan.
- ✅ Migraciones idempotentes testeadas en cloned DB.
- ✅ Prototype HTML sigue en `docs/ux-sessions/2026-04-17-offer-editions-ui-revamp/prototype/` como referencia viva.
- ✅ Cada phase documenta qué cambió en el commit message.
- ✅ User hace sign-off visual comparando cada page implementada vs prototipo correspondiente.

---

## Learnings Phase 5 (2026-04-17)

- **Pre-existing broken test**: `backend/tests/modules/sales_agent/test_conversation_context.py` (untracked) fails on import (`merge_history_with_current` not in chat orchestrator). Not created by this session — leave for owner. Confirmed by running enrollment tests in isolation.
- **Sessions are sync in sales_agent**: despite CLAUDE.md saying new code must use AsyncSession, 100% of offer/ and sales_agent/ repos use sync `Session` from `sqlalchemy.orm`. Following existing pattern (sync) for Enrollment to avoid a one-off outlier. Migration to AsyncSession is module-wide decision for later.
- **Arch test `test_all_endpoints_have_response_model` accepts typed return annotation** (`has_response_model OR has_return_type`). Ruff FAST001 complains if you pass `response_model=` AND have a return type, so for new code use only the return type. Keeps both gates green.
- **Migration naming prefix**: last real migration was `047_pricing_tiers.py` — confirmed `048_create_enrollments.py` is the right number. Older files use hash-based names (e.g. `f851363921c9_...`) but the numbered-prefix convention is the active one.
- **`db_engine` fixture in `backend/tests/conftest.py`**: new SA models must be imported in the try-block that calls `Base.metadata.create_all()`. Otherwise tests that use the in-memory SQLite engine can't create the table.
- **Event bus**: sales_agent has an async EventBus but no service in offer/ uses it directly. Chose `ServiceResult(enrollment, events: list)` tuple pattern so the API layer decides when to dispatch. Matches 'returned events' style without async contamination.
