# FLOW-SPEC — Offer Editions UI Revamp

> **Scope:** Rediseño visual y de navegación del Offer Studio + Closer Studio + Copilot para completar Phases 5-10 del FLOW-SPEC original (`docs/flow-specs/FLOW-SPEC-offer-studio-editions.md`, 2026-04-16).
>
> **Status:** Proposed · pending implementation.
>
> **Date:** 2026-04-17.
>
> **Author:** ux-flow-architect skill session.
>
> **Related rules:** `.claude/rules/backend-ddd.md`, `.claude/rules/frontend-fsd.md`, `.claude/rules/tdd-mandatory.md`, `.claude/rules/copilot-resilience.md`, `.claude/rules/tenant-isolation.md`.
>
> **Reference:** prototipo HTML clickeable en `prototype/` (servido en `localhost:8888`). Este spec **NO reemplaza** el HTML — lo documenta. El HTML es la fuente de verdad visual.

---

## 1. Context

### Lo shipped (Phases 0-4)
- Phase 0: `EditionPricingOverride` crash fix ✅
- Phase 1: `ArchetypeCatalog` SSoT + hooks ✅
- Phase 2: Edition placeholder lifecycle + `visibility` + migration 045 ✅
- Phase 3: Per-edition landing + assets + `EditionCloneService` + migration 046 ✅
- Phase 4: Temporal pricing tiers + migration 047 ✅

### Lo pendiente (Phases 5-10, ahora revisados)
| Phase | FLOW-SPEC original | Estado revisado |
|---|---|---|
| 5 | Enrollment entity | Sin cambios — se mantiene |
| 6 | Sales Agent edition tools | Sin cambios — se mantiene |
| 7 | Copilot rework | **Modificado:** interview obligatorio, focus mode fuera de scope de esta sesión |
| 8 | Public URL routing per edition | Sin cambios |
| 9 | Frontend UI revamp | **Re-diseñado completo en esta sesión** (es el foco) |
| 10 | Per-edition analytics compare | **Movido a Growth Studio** (sale del Offer Studio) |

### Lo nuevo en esta sesión

Paradigma de navegación repensado:
- Rail permanente de ediciones (secondary sidebar) entre app sidebar y main content.
- Tab bar del OfferShell reducido a 4 tabs (`Info · Ventas · Assets · Campañas`).
- Landing accedido via split-button estilo Webflow, no como tab.
- Knowledge es sección dentro de Info, no tab.
- Analytics fuera del Offer Studio — va a Growth Studio.
- Variante sin rail para archetypes sin ediciones (PRODUCTO, MEMBRESIA).
- Ventas = listado simple con deep-link a Closer Studio para operativa avanzada.
- Campañas = listado read-only de flights de ads asociados desde Growth Studio.
- Assets = placeholder para futuro editor tipo Canva.

---

## 2. Current Navigation Map (post Phases 0-4)

### App Sidebar groups (5)
```
├── Brand Studio (4 sub-items)
├── Offer Studio                        ← flat, sin sub-items
├── Growth Studio (5 stages)
├── Closer Studio
│   ├── Resumen
│   ├── Studio → /sales/studio/inbox
│   └── Contactos
└── Configuración (General · Conexiones)
```

### Offer Studio internal routes (actual)
```
/offer-studio                                      List
/offer-studio/interview                            Copilot interview
/offer-studio/offer/[id]                           Editor (tab)
/offer-studio/offer/[id]/assets                    Assets (tab)
/offer-studio/offer/[id]/campaigns                 Campaigns (tab)
/offer-studio/offer/[id]/knowledge                 Knowledge (tab)
```

### Closer Studio internal routes (actual)
```
/sales/resumen
/sales/studio/{inbox,pipeline,frozen}
/sales/contactos
/sales/mock                                        huérfana
```

---

## 3. Proposed Navigation

### App Sidebar (change: +1 item bajo Closer Studio)
```diff
Closer Studio
├── Resumen
├── Studio → /sales/studio/inbox
├── Contactos
+├── Inscripciones (NEW badge 6 meses)      /sales/enrollments
```

### Offer Studio routes (restructured)
```
/offer-studio                                      List (unchanged)
/offer-studio/interview                            Copilot (unchanged)
/offer-studio/offer/[id]                           Shell · default tab=Info
/offer-studio/offer/[id]?tab=ventas                Shell · tab=Ventas
/offer-studio/offer/[id]?tab=assets                Shell · tab=Assets
/offer-studio/offer/[id]?tab=campanas              Shell · tab=Campañas
/offer-studio/offer/[id]?edition={eid}             Shell · edición specifica seleccionada en rail
/offer-studio/offer/[id]?tab=X&edition={eid}       Tab + edition combinados
/offer-studio/offer/[id]/editions/[eid]/landing    Landing editor (full screen, new window)
```

**Removed routes:**
- `/offer-studio/offer/[id]/assets` → migrado a `?tab=assets`
- `/offer-studio/offer/[id]/campaigns` → migrado a `?tab=campanas`
- `/offer-studio/offer/[id]/knowledge` → eliminado (sección dentro de Info)

**Racional del query param `?edition={eid}`:** permite mantener el tab activo cuando cambiás de edición en el rail. Si usás path param `/editions/[eid]/`, el tab se resetea.

### Public routes (Phase 8)
```
/public/{tenant_slug}/{offer_slug}                  redirect → edición activa
/public/{tenant_slug}/{offer_slug}/edicion/{n}      landing scoped a edición
```

---

## 4. Journey Maps

### Journey 1 — Crear offer + primera edición (via Copilot)
**Prototype:** `copilot/interview-date.html` → `offer-studio/offer-info.html`

| # | Paso | Ruta | Estado |
|---|---|---|---|
| 1 | Click "Crear con IA" en `/offer-studio` | `/offer-studio/interview` | ⚠️ existe, se amplía |
| 2 | Copilot extrae info base (archetype, promise, audience, pricing, etc.) | chat | ✅ shipped Phase 7 previa |
| 3 | **NUEVO:** Copilot bloquea final con "¿cuándo tu primera edición?" | chat + quick-replies | ❌ implementar |
| 4a | Usuario da fecha → edición creada UPCOMING + PUBLIC | redirect a `/offer/[id]?edition={eid}` | ❌ implementar |
| 4b | Usuario skip → placeholder edición DRAFT + PRIVATE | redirect a `/offer/[id]` (sin edition, muestra el placeholder en rail) | ✅ Phase 2 shipped |
| 5 | Shell se monta con rail, edición activa seleccionada, Info completo | `/offer/[id]?edition={eid}` | ❌ implementar shell con rail |
| 6 | Usuario ve Info completo + waitlist banner si aplica | Info tab | ❌ implementar |

### Journey 2 — Crear edición N+1 (clone)
**Prototype:** `offer-studio/offer-info.html` (rail) → `offer-info-edition2.html` → [clone action]

| # | Paso | Ruta | Estado |
|---|---|---|---|
| 1 | Click `+ Nueva edición` en rail | opens modal "Clonar desde..." | ❌ implementar |
| 2 | Seleccionar edición source (default: última completada) | modal | ❌ implementar |
| 3 | Elegir strategy: literal · cambiar fechas · regenerar IA | modal | ❌ implementar (backend clone ya existe) |
| 4 | Si "cambiar fechas": date picker para nueva edición | modal | ❌ implementar |
| 5 | Confirmar → EditionCloneService corre | backend | ✅ Phase 3 shipped |
| 6 | Redirect a `?edition={newId}`, Info tab con datos clonados | shell | ❌ implementar |

### Journey 3 — Sales Agent enrolls lead
**Prototype:** `sales/inbox.html` (EnrollmentWidget)

| # | Paso | Ruta | Estado |
|---|---|---|---|
| 1 | Lead chatea, agente detecta intent | `/sales/studio/inbox` | ⚠️ mejora prompt Phase 6 |
| 2 | Agente llama `list_public_editions(offer_id)` | tool | ❌ Phase 6 |
| 3 | Agente propone edición activa al lead | chat | ⚠️ prompt |
| 4 | Lead confirma → agente llama `create_enrollment` | tool | ❌ Phase 5 + 6 |
| 5 | Agente llama `generate_payment_link` | tool | ❌ Phase 6 |
| 6 | Agente envía link + estado se muestra en EnrollmentWidget | chat + widget | ❌ widget Phase 9 |
| 7 | Pago confirmado → webhook `EnrollmentPaid` → widget actualiza | webhook | ⚠️ Phase 5 + 6 |
| 8 | Usuario puede ver inscripción desde chat o ir a cohorte/enrollments | deep links | ❌ implementar |

### Journey 4 — Waitlist conversion
**Prototype:** `offer-studio/offer-info.html` (waitlist banner) + `sales/enrollments.html` (grouped "En lista de espera")

| # | Paso | Ruta | Estado |
|---|---|---|---|
| 1 | Lead sin edición pública disponible → agente ofrece waitlist | chat | ❌ Phase 6 prompt |
| 2 | Lead confirma → agente llama `create_enrollment(edition=null, status=WAITLIST)` | tool | ❌ Phase 5 + 6 |
| 3 | Usuario crea edición nueva, la publica (visibility=PUBLIC) | Info tab + lifecycle switcher | ❌ implementar publish flow en shell |
| 4 | Evento `EditionPublished` fires → handler notifica candidatos | backend | ❌ Phase 5 |
| 5 | Usuario ve waitlist banner en Info tab de la nueva edición | banner | ❌ implementar |
| 6 | Click "Notificar a todos" → bulk send | tool | ❌ Phase 6 |
| 7 | Leads reciben mensaje, convierten → normal enrollment flow | chat | ⚠️ Phase 6 |

---

## 5. Gap Analysis

### 5.1 Backend gaps (unchanged vs original FLOW-SPEC)
| # | Gap | Phase |
|---|---|---|
| 1 | No `Enrollment` entity | 5 |
| 2 | No domain events `EditionPublished`, `EnrollmentPaid` | 5 |
| 3 | No handlers `NotifyWaitlistOnEditionPublished`, `IncrementEditionEnrollmentCount` | 5 |
| 4 | Sales agent sin herramientas de enrollment (list/create/payment/waitlist) | 6 |
| 5 | Copilot interview no pregunta por fecha de primera edición | 7 |
| 6 | No public URL routing per edition | 8 |
| 7 | No integración Meta Ads/Stripe/MP webhooks → `EnrollmentPaid` event | 5 + conexiones |

### 5.2 Frontend gaps (re-diseñados en esta sesión)
| # | Gap | Prototype reference | UI-SPEC |
|---|---|---|---|
| A | Offer Shell no tiene rail de ediciones | `offer-info.html` | UI-SPEC-offer-studio-shell.md |
| B | Tab bar tiene tabs obsoletos (Editor/Assets/Campaigns/Knowledge) | `offer-info.html` | UI-SPEC-offer-studio-shell.md |
| C | Landing es botón textual, no split-button | `offer-info.html` header | UI-SPEC-offer-studio-shell.md |
| D | No existe waitlist banner | `offer-info.html` banner | UI-SPEC-offer-studio-shell.md |
| E | No existe Ventas tab con listado per-edición | `offer-ventas.html` | UI-SPEC-offer-studio-tabs.md |
| F | No existe Info unificado (actualmente disperso en Editor + varios) | `offer-info.html` | UI-SPEC-offer-studio-tabs.md |
| G | Campañas tab hoy es read-only de offer-level, no edition-scoped | `offer-campanas.html` | UI-SPEC-offer-studio-tabs.md |
| H | No existe Assets gallery edition-scoped con clone | `offer-assets.html` | UI-SPEC-offer-studio-tabs.md |
| I | No existe `/sales/enrollments` global | `sales/enrollments.html` | UI-SPEC-closer-studio.md |
| J | No existe EnrollmentWidget en inbox | `sales/inbox.html` | UI-SPEC-closer-studio.md |
| K | No existe bloque interview "fecha primera edición" | `copilot/interview-date.html` | UI-SPEC-copilot-interview.md |
| L | Sidebar no tiene entrada "Inscripciones" bajo Closer | app-sidebar | UI-SPEC-sidebar-restructure.md |
| M | No existe clone modal con strategy picker | falta en prototipo · ver § 7.6 | UI-SPEC-offer-studio-shell.md |
| N | Variant sin rail (PRODUCTO/MEMBRESIA) | `offer-no-editions.html` | UI-SPEC-offer-studio-shell.md |

### 5.3 Priority Matrix
| # | Finding | Impact | Effort | Priority |
|---|---|---|---|---|
| 1-4 | Backend Phase 5 (Enrollment + events) | Critical | High | P1 |
| 5-7 | Backend Phases 6-8 (Sales agent, Copilot, URLs) | High | High | P1 |
| A-D | Shell/rail/tabs | Critical (UX) | High | P1 |
| F,H | Info + Assets tabs | High | Medium | P1 |
| E,G | Ventas + Campañas tabs | High | Medium | P2 |
| I,J | Closer Studio changes | High | Medium | P2 |
| K | Copilot interview block | High | Medium | P2 |
| L,M,N | Sidebar, clone modal, no-editions variant | Medium | Low | P3 |

---

## 6. Proposed Changes Table

### 6.1 Sidebar changes
| Action | Where | Spec |
|---|---|---|
| Add | Closer Studio > Inscripciones (NEW badge) | UI-SPEC-sidebar-restructure.md |

### 6.2 Component changes
| Component | Action | Scope | Spec |
|---|---|---|---|
| `AppSidebar.tsx` | Modify | +1 child bajo Closer Studio | UI-SPEC-sidebar-restructure.md |
| `OfferShell.tsx` | Rewrite | Agregar `EditionsRail`, cambiar tab bar a 4 tabs, agregar `LandingSplitButton`, agregar `WaitlistBanner` | UI-SPEC-offer-studio-shell.md |
| `OfferShellHeaderRow1.tsx` | Modify | Mostrar "Offer · Edición #N · fecha" + status+visibility badges | UI-SPEC-offer-studio-shell.md |
| `OfferShellHeaderRow2.tsx` | Modify | Quitar botón landing (ahora en split-button al nivel tab bar) | UI-SPEC-offer-studio-shell.md |
| `OfferTabBar.tsx` | Rewrite | 4 tabs: Info · Ventas · Assets · Campañas | UI-SPEC-offer-studio-shell.md |
| `EditionsRail.tsx` | Create | Secondary sidebar con 3 grupos + collapse + + button | UI-SPEC-offer-studio-shell.md |
| `EditionsRailCollapsed.tsx` | Create | Badges numéricos con coloring semántico | UI-SPEC-offer-studio-shell.md |
| `LandingSplitButton.tsx` | Create | Split button con 5 estados + dropdown menu | UI-SPEC-offer-studio-shell.md |
| `WaitlistBanner.tsx` | Create | Banner gradient con 2 acciones | UI-SPEC-offer-studio-shell.md |
| `OfferInfoTab.tsx` | Create | 7 secciones: Identidad, Fechas, Pricing, Entregables, Público, Garantía, Knowledge | UI-SPEC-offer-studio-tabs.md |
| `OfferVentasTab.tsx` | Create | KPIs + filters + table + closer deep-link | UI-SPEC-offer-studio-tabs.md |
| `OfferAssetsTab.tsx` | Create | Placeholder banner + filter pills + gallery + clone CTA | UI-SPEC-offer-studio-tabs.md |
| `OfferCampanasTab.tsx` | Create | KPIs + campaign cards + growth link + orgánico placeholder | UI-SPEC-offer-studio-tabs.md |
| `EditionCloneModal.tsx` | Create | Strategy picker: literal / date-replace / AI-regen | UI-SPEC-offer-studio-shell.md |
| `EnrollmentsPage.tsx` | Create | /sales/enrollments global con grouped table + waitlist block | UI-SPEC-closer-studio.md |
| `EnrollmentWidget.tsx` | Create | Inline widget en inbox side panel con estado + acciones | UI-SPEC-closer-studio.md |
| `InterviewDateBlock.tsx` | Create | Último bloque del interview copilot con quick-replies | UI-SPEC-copilot-interview.md |
| `LandingEditorPage.tsx` | Create (stub for now) | Full-screen editor en ruta separada | UI-SPEC-offer-studio-shell.md (stub) |

### 6.3 Removed artifacts
| Artifact | Reason |
|---|---|
| `/offer-studio/offer/[id]/assets/page.tsx` | Migrado a query param |
| `/offer-studio/offer/[id]/campaigns/page.tsx` | Migrado a query param |
| `/offer-studio/offer/[id]/knowledge/page.tsx` | Integrado como sección en Info |
| `EditionsSection.tsx` (card en Editor tab) | Reemplazado por rail |
| `EditionFormDialog.tsx` | Reemplazado por modal clone + edits inline en Info |
| `EditionPricingOverride.tsx` | Reemplazado por `PricingTiersEditor` (parte de Info) |

---

## 7. New Components Detail

### 7.1 `EditionsRail`
Ver UI-SPEC-offer-studio-shell.md § 3. Prototipo: `prototype/offer-studio/offer-info.html` aside `id="rail"`.

**Props:**
```ts
interface EditionsRailProps {
  offerId: string;
  currentEditionId: string | null;
  onSwitch: (editionId: string) => void;
  onCollapse: () => void;
  onCreateNew: () => void;  // abre EditionCloneModal
}
```

**Data fetch:** `useEditions(offerId)` (ya existe) devuelve `editions[]`. Agrupar client-side:
- `upcoming`: `status === UPCOMING && visibility === PUBLIC` (siempre solo 1 visible como "próxima" destacada)
- `drafts`: `status === DRAFT` (cualquier visibility)
- `past`: `status === COMPLETED || status === CANCELLED`
- `active`: `status === ACTIVE` → mostrar en grupo "En curso" arriba de "Próxima"

**Empty states:**
- Sin ediciones (no debería pasar post Phase 2 placeholder): CTA grande "Crear primera edición".
- Solo placeholder borrador: banner amber "Configurá fecha para publicar".

### 7.2 `EditionsRailCollapsed`
Mismos datos que `EditionsRail`, layout vertical de círculos 40×40. Badge `#N` donde N = `edition_number`.

### 7.3 `LandingSplitButton`
Ver UI-SPEC-offer-studio-shell.md § 5.

**Props:**
```ts
interface LandingSplitButtonProps {
  landingId: string | null;
  landingStatus: 'none' | 'draft' | 'published' | 'publishing' | 'dirty';
  publicUrl: string | null;
  editorUrl: string;           // ruta al editor (nueva pestaña)
  onRegenerate: () => void;
  onCloneFrom: (editionId: string) => void;
  onUnpublish: () => void;
  onPublish: () => void;
  onCopyUrl: () => void;
}
```

### 7.4 `WaitlistBanner`
Ver UI-SPEC-offer-studio-shell.md § 6.

**Props:**
```ts
interface WaitlistBannerProps {
  offerId: string;
  editionId: string;
  waitlistCount: number;
  onViewList: () => void;        // abre drawer con lista + bulk select
  onNotifyAll: () => Promise<void>; // llama promote_waitlist_to_edition
}
```

### 7.5 `EditionCloneModal`
Ver UI-SPEC-offer-studio-shell.md § 7.

**Props:**
```ts
interface EditionCloneModalProps {
  offerId: string;
  sourceEditions: LaunchEdition[];  // pasadas + completadas, descending
  open: boolean;
  onClose: () => void;
  onConfirm: (payload: {
    sourceEditionId: string;
    strategy: 'literal' | 'date_replace' | 'ai_regen';
    newStartDate?: string;
    newEndDate?: string;
    changesBrief?: string;
    attachments?: File[];
  }) => Promise<{ newEditionId: string }>;
}
```

**Copy del modal:**
- Title: "Crear edición nueva"
- Subtítulo: "Clonar desde una edición anterior acelera la configuración"
- Select edición fuente: dropdown con opciones "Edición #N · <mes año> (completada/activa)"
- Strategy radio: `literal` / `date_replace` / `ai_regen`
- Si `date_replace`: inputs `new_start_date` + `new_end_date` (pre-rellenados con +X meses de la fuente)
- Si `ai_regen`: textarea `changes_brief` + uploader `attachments[]`
- CTA: "Clonar y abrir Edición #{newNumber}"

### 7.6 Otros (detalle en UI-SPECs)
- `OfferInfoTab`, `OfferVentasTab`, `OfferAssetsTab`, `OfferCampanasTab`, `EnrollmentsPage`, `EnrollmentWidget`, `InterviewDateBlock`, `LandingEditorPage`.

---

## 8. File Changes Required

### Backend (Phases 5-8)
| File | Action | Purpose |
|---|---|---|
| `backend/alembic/versions/048_create_enrollments.py` | Create | Table enrollments (Phase 5) |
| `backend/src/modules/sales_agent/domain/enrollment.py` | Create | `Enrollment` entity + `EnrollmentStatus` enum (Phase 5) |
| `backend/src/modules/sales_agent/domain/events.py` | Create/extend | `EnrollmentCreated`, `EnrollmentPaid` events |
| `backend/src/modules/sales_agent/infrastructure/models/enrollment_model.py` | Create | SA model |
| `backend/src/modules/sales_agent/infrastructure/repositories/enrollment_repository.py` | Create | Repo with tenant isolation |
| `backend/src/modules/sales_agent/application/enrollment_service.py` | Create | Use cases |
| `backend/src/modules/sales_agent/api/enrollments.py` | Create | Routes `POST /enrollments`, `GET /enrollments`, `PATCH /{id}/status` |
| `backend/src/modules/sales_agent/application/tools/list_public_editions.py` | Create | Tool Phase 6 |
| `backend/src/modules/sales_agent/application/tools/create_enrollment.py` | Create | Tool Phase 6 |
| `backend/src/modules/sales_agent/application/tools/generate_payment_link.py` | Create | Tool Phase 6 |
| `backend/src/modules/sales_agent/application/tools/promote_waitlist.py` | Create | Tool Phase 6 |
| `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2` | Modify | Agregar edition awareness block |
| `backend/src/modules/connections/infrastructure/webhooks/stripe.py` | Modify | Emit `EnrollmentPaid` |
| `backend/src/modules/copilot/domain/interview_configs/offer_config.py` | Modify | Agregar bloque date final (Phase 7) |
| `backend/src/modules/copilot/application/procedures/offer_creation.py` | Modify | Leer first_edition input y crear edición con fecha |
| `backend/src/modules/landing/api/public.py` | Create | Routes `/public/{tenant}/{offer}`, `/public/{tenant}/{offer}/edicion/{n}` (Phase 8) |
| `backend/src/modules/offer/api/launch_editions.py` | Modify | Agregar endpoint `POST /{editionId}/publish` y `POST /{editionId}/clone` con strategy |
| Tests architecture | Modify | Update `test_ddd_boundaries` ratchets si hay imports nuevos |

### Frontend (Phase 9 revamped)
| File | Action | Purpose |
|---|---|---|
| `frontend/src/components/shared/layout/AppSidebar.tsx` | Modify | +1 entry bajo Closer |
| `frontend/src/features/offer-studio/components/container/OfferShell.tsx` | Rewrite | Agregar rail + nuevas props |
| `frontend/src/features/offer-studio/components/container/OfferShellHeaderRow1.tsx` | Modify | Title con edición |
| `frontend/src/features/offer-studio/components/container/OfferShellHeaderRow2.tsx` | Modify | Quitar landing button |
| `frontend/src/features/offer-studio/components/container/OfferTabBar.tsx` | Rewrite | 4 tabs + landing split-button |
| `frontend/src/features/offer-studio/components/container/EditionsRail.tsx` | Create | Secondary sidebar |
| `frontend/src/features/offer-studio/components/container/EditionsRailCollapsed.tsx` | Create | Collapsed variant |
| `frontend/src/features/offer-studio/components/container/LandingSplitButton.tsx` | Create | Webflow-style button |
| `frontend/src/features/offer-studio/components/container/WaitlistBanner.tsx` | Create | Banner |
| `frontend/src/features/offer-studio/components/container/EditionCloneModal.tsx` | Create | Modal |
| `frontend/src/features/offer-studio/components/info/OfferInfoTab.tsx` | Create | Tab content |
| `frontend/src/features/offer-studio/components/info/IdentitySection.tsx` | Create | Section 1 |
| `frontend/src/features/offer-studio/components/info/DatesSection.tsx` | Create | Section 2 (edition-scoped) |
| `frontend/src/features/offer-studio/components/info/PricingTiersSection.tsx` | Create | Section 3 (timeline + editor) |
| `frontend/src/features/offer-studio/components/info/DeliverablesSection.tsx` | Create | Section 4 |
| `frontend/src/features/offer-studio/components/info/AudienceSection.tsx` | Create | Section 5 |
| `frontend/src/features/offer-studio/components/info/GuaranteeOnboardingSection.tsx` | Create | Section 6 |
| `frontend/src/features/offer-studio/components/info/KnowledgeSection.tsx` | Create | Section 7 (antes tab separado) |
| `frontend/src/features/offer-studio/components/ventas/OfferVentasTab.tsx` | Create | Tab content |
| `frontend/src/features/offer-studio/components/ventas/EnrollmentsTable.tsx` | Create | Table con status + filters |
| `frontend/src/features/offer-studio/components/assets/OfferAssetsTab.tsx` | Create | Placeholder tab |
| `frontend/src/features/offer-studio/components/assets/AssetGallery.tsx` | Create | Grid con filtros |
| `frontend/src/features/offer-studio/components/campanas/OfferCampanasTab.tsx` | Create | Tab content |
| `frontend/src/features/offer-studio/components/campanas/CampaignCard.tsx` | Create | Card con platform icon + KPIs |
| `frontend/src/features/offer-studio/hooks/use-offer-with-edition.ts` | Create | Hook que resuelve edición activa (query param + fallback a próxima) |
| `frontend/src/features/offer-studio/hooks/use-edition-waitlist.ts` | Create | Hook para waitlist count + notify action |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/page.tsx` | Rewrite | Default render = Info tab, lee query params `?tab` y `?edition` |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/assets/page.tsx` | Delete | Migrado a query param |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/campaigns/page.tsx` | Delete | Migrado a query param |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/knowledge/page.tsx` | Delete | Migrado a sección en Info |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/editions/[editionId]/landing/page.tsx` | Create | Landing editor full-screen |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/enrollments/page.tsx` | Create | NEW global enrollments page |
| `frontend/src/features/closer-studio/components/EnrollmentsPage.tsx` | Create | Page body con tabla + filtros + waitlist block |
| `frontend/src/features/closer-studio/components/EnrollmentWidget.tsx` | Create | Widget en inbox side panel |
| `frontend/src/features/closer-studio/hooks/use-enrollments.ts` | Create | Hook React Query |
| `frontend/src/features/closer-studio/hooks/use-active-enrollment-for-conversation.ts` | Create | Hook usado en inbox widget |
| `frontend/src/features/sales/components/inbox/InboxSidePanel.tsx` | Modify | Integrar `<EnrollmentWidget />` |
| `frontend/src/features/copilot/components/interview/InterviewDateBlock.tsx` | Create | Último bloque interview copilot |

### E2E tests
| File | Purpose |
|---|---|
| `frontend/e2e/specs/smoke/offer-editions.spec.ts` | Smoke del flujo completo |
| `frontend/e2e/specs/regression/offer-info-rail-switch.spec.ts` | Test de switch de edición via rail |
| `frontend/e2e/specs/regression/closer-enrollments.spec.ts` | Test global enrollments page |
| `frontend/e2e/specs/regression/copilot-interview-date.spec.ts` | Test interview pregunta fecha obligatoriamente |

---

## 9. Prototype Reference

Serve:
```bash
python3 -m http.server 8888 -d "docs/ux-sessions/2026-04-17-offer-editions-ui-revamp/prototype/" &
```

Open http://localhost:8888.

| File | Represents | Primary Journey |
|---|---|---|
| `index.html` | meta-refresh → offers-list | — |
| `offer-studio/offers-list.html` | `/offer-studio` (unchanged) | 1 entry |
| `offer-studio/offer-info.html` | `/offer/[id]?tab=info&edition={#3}` (próxima) | 1, 2 |
| `offer-studio/offer-info-edition2.html` | `/offer/[id]?tab=info&edition={#2}` (pasada, read-only) | 2 |
| `offer-studio/offer-no-editions.html` | `/offer/[id]` para PRODUCTO (no rail) | N/A |
| `offer-studio/offer-ventas.html` | `/offer/[id]?tab=ventas&edition={#3}` | 3 |
| `offer-studio/offer-assets.html` | `/offer/[id]?tab=assets&edition={#3}` | — |
| `offer-studio/offer-campanas.html` | `/offer/[id]?tab=campanas&edition={#3}` | — |
| `offer-studio/offer-landing-editor.html` | `/offer/[id]/editions/{#3}/landing` (new window) | 1, 2 |
| `sales/enrollments.html` | `/sales/enrollments` (NEW route) | 3, 4 |
| `sales/inbox.html` | `/sales/studio/inbox` + EnrollmentWidget | 3 |
| `copilot/interview-date.html` | `/offer-studio/interview` step final | 1 |

---

## 10. Companion Files (same session folder)

- `PLAN.md` — Execution phases ordered by dependency
- `DECISIONS.md` — Log of 14 decisions taken during session
- `UI-SPEC-sidebar-restructure.md` — Sidebar changes (1 entry add)
- `UI-SPEC-offer-studio-shell.md` — Shell + rail + tab bar + landing button + banner + clone modal (biggest spec)
- `UI-SPEC-offer-studio-tabs.md` — Content of each of 4 tabs
- `UI-SPEC-closer-studio.md` — EnrollmentsPage + EnrollmentWidget
- `UI-SPEC-copilot-interview.md` — InterviewDateBlock
- `prototype/` — clickable HTML reference (served on 8888)

---

## 11. Open Questions

Ninguna. 14 decisiones consolidadas en `DECISIONS.md`. Las ambigüedades técnicas (ej. cómo implementar el date picker del clone modal) quedan a cargo del equipo de implementación siguiendo las convenciones del codebase.

## 12. Integration notes

- **Con `nicolify-feature` skill:** esta sesión produce input. Invocar `nicolify-feature` por fase (5, 6, 7, 8, 9a, 9b, …). Los architect/backend/frontend agents leen `PLAN.md` + los UI-SPECs correspondientes.
- **Con `ux-disruptivo`:** no se invoca — todas las pantallas del scope están diseñadas en el prototipo HTML. Si aparecen pantallas nuevas durante implementación, derivar a `ux-disruptivo`.
- **Con `backend-expert`:** invocar directamente para Phases 5-8. Cada phase es un feature shippable.
- **Con `frontend-expert`:** invocar por-tab en Phase 9 siguiendo los UI-SPECs.
