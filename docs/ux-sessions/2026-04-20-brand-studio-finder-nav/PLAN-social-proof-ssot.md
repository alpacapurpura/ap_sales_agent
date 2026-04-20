# PLAN — Social Proof SSoT (Opción C — FINAL)

**Fecha:** 2026-04-20
**Status:** APROBADO · listo para ejecución en conversación nueva
**Scope:** Migrar Team / Authority / Testimonials de arrays JSON embebidos en `brand_settings` → entidades DB de primer orden, con placements M:N para reutilización cross-surface (Brand / Offer / Landing).

---

## 0 · Principios rectores (no negociables)

1. **SSoT real** — una sola fuente de datos por entidad, consumida por Brand Studio, Offer Studio, Landing Generator, Sales Agent y Copilot.
2. **Escalabilidad primero** — arquitectura pensada para N surfaces (no solo brand+offer). Agregar un nuevo consumidor (ej. email sequences, meta ads) es zero-schema-migration.
3. **DDD puro** — bounded context propio, eventos de dominio, puertos/adaptadores, zero cross-module imports salvo shared links.
4. **Zero breaking changes progresivos** — migración con flags de compat; legacy queda read-only hasta cleanup final.
5. **Arch fitness tests** como contrato — ratchet pattern, nuevos tests solo pueden achicar allowlists.

---

## 1 · Decisiones arquitectónicas locked

### 1.1 · Nombre del bounded context: `social_proof`

Rationale: grupo semántico "señales de confianza" (Cialdini). Un solo equipo es dueño. Fácil de razonar. Se evita triplicar ceremonia DDD para 3 entidades con patrones idénticos.

### 1.2 · 3 tablas especializadas (no polimórficas)

`testimonials`, `authority_items`, `team_members` — campos distintos, queries distintos, índices precisos. Polimórfico + discriminator sería prematuro.

### 1.3 · Placements M:N desde día 1 (no `scope` column)

La SSoT real se logra con tabla link `social_proof_placements`. Cada entidad es **tenant-scoped sin dueño implícito**. El "dónde se muestra" vive en la tabla link.

```
┌──────────────┐        ┌────────────────────────────┐        ┌───────────────┐
│ testimonials │        │ social_proof_placements    │        │ offers        │
│  id          │◄───────┤  source_table              │        │  id           │
│  tenant_id   │        │  source_id                 │        └───────────────┘
│  fields...   │        │  surface_type              │
└──────────────┘        │  surface_ref_id (nullable) │
                        │  sort_order                │
┌──────────────┐        │  is_visible                │
│ authority_   │◄───────┤  created_at, deleted_at    │
│ items        │        └────────────────────────────┘
└──────────────┘
                        surface_type values:
┌──────────────┐            'brand_homepage'   — tenant-wide (surface_ref_id=NULL)
│ team_members │◄────────   'offer'            — surface_ref_id = offer.id
└──────────────┘            'landing_page'     — surface_ref_id = landing.id
                            'email_sequence'   — future-proof
                            'sales_agent_kb'   — available to AI SDR
```

**Consecuencia:** "ver testimonios de oferta X" = query a placements. "ver catálogo tenant" = todos los testimonios del tenant sin filtro por placement. Un mismo testimonio puede tener N placements sin duplicación. Remover un testimonio de una oferta = soft-delete del placement, el testimonio persiste.

### 1.4 · Eventos de dominio (desacople cross-module)

Cada mutación emite eventos publicados en el bus compartido:
- `TestimonialCreated`, `TestimonialUpdated`, `TestimonialDeleted`
- `AuthorityItemCreated/Updated/Deleted`
- `TeamMemberCreated/Updated/Deleted`
- `PlacementAdded`, `PlacementRemoved`

Consumidores (Sales Agent KB, Landing Generator cache, Copilot embeddings) suscriben sin import directo. Respeta `.claude/rules/backend-ddd.md` — cross-module via eventos.

### 1.5 · Puertos `shared/links` para lectura cross-module

`src/shared/links/ports/social_proof.py` expone interface que Offer Studio, Landing y Sales Agent consumen. Implementación vive en `social_proof/infrastructure/adapters/`. Evita que otros módulos importen directamente desde `social_proof.infrastructure`.

### 1.6 · Read model optimizado para "for-surface"

Query pattern más caliente: "dame toda la social proof visible en X". Se resuelve con servicio dedicado `SocialProofResolver`:

```python
resolver.for_surface(
    surface_type="offer",
    surface_ref_id=offer.id,
    include_brand=True,  # merge con brand_homepage placements
) -> ResolvedSocialProof  # {testimonials, authority, team_members}
```

Sin N+1, sin joins caóticos en el caller. Internamente usa eager loading via SA `selectinload`.

### 1.7 · Architecture fitness tests desde día 1

- `test_social_proof_tenant_isolation` — toda query filtra `tenant_id`
- `test_social_proof_no_cross_module_imports` — `social_proof` solo consume `shared/`
- `test_placements_cascade_on_source_delete` — eliminar testimonial cascade-soft-deletes sus placements
- `test_surface_type_enum_completeness` — catalog y enum alineados (como extraction_contract)
- `test_response_models_declared` — PII rule
- `test_domain_purity` — domain/ sin SQLAlchemy/FastAPI imports
- `test_every_mutation_emits_event` — services publican al bus

### 1.8 · Copilot integration locked

`copilot/domain/module_registry.py` agrega:
```python
MODULES["social_proof"] = ModuleDescriptor(
    collections={
        "testimonials": {...schema, repo, label_fn...},
        "authority_items": {...},
        "team_members": {...},
    },
    ports=SocialProofPort,  # shared/links port
)
```

Tools route-based:
- `/brand-studio/testimonials/instance/{id}/{fieldId}` → `[update_instance_field, delete_instance, create_instance, suggest_field_value, add_placement, remove_placement, clone_for_customization]`

Tool `suggest_field_value` recibe instance_state completo + placements actuales → sugerencias contextuales a cómo se usa la señal.

### 1.9 · Clone vs link — ambos disponibles

- **Link** (default) — agregar placement. Misma entidad en múltiples surfaces. Edits propagan.
- **Clone** — "customize this one just for offer X" — crea copia nueva, placement del clon solo en offer X. Original intacto.

UI muestra claramente: "Este testimonio se muestra en: [Brand · Offer A · Offer B]" antes de editar, para evitar sorpresas.

### 1.10 · Soft delete en ambas tablas

- `testimonials.deleted_at` → row gone everywhere (cascade soft-delete a placements)
- `placements.deleted_at` → row gone from that surface, testimonio persiste

### 1.11 · Tenant isolation via middleware + repository guard

Repos nunca aceptan queries sin `tenant_id`. Enforced por arch test + runtime assertion en repository `__init__`.

### 1.12 · Seed data migration con dry-run obligatorio

Alembic migration corre en 3 pasos:
1. Create tables + indexes + constraints
2. Seed rows desde `brand_settings.{team,testimonials,authority_vault}` JSON (idempotente con `ON CONFLICT DO NOTHING`)
3. Create default placement `brand_homepage` para cada row seeded

**Dry run en DB clonada** obligatorio, con rowcount assertion (suma de items JSON == count de rows creadas).

---

## 2 · Estructura del módulo backend

```
backend/src/modules/social_proof/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── testimonial.py                    # TestimonialEntity (Pydantic)
│   ├── authority_item.py                 # AuthorityItemEntity
│   ├── team_member.py                    # TeamMemberEntity
│   ├── placement.py                      # PlacementEntity
│   ├── enums.py                          # SurfaceType, AuthorityType, TestimonialMediaType
│   ├── events.py                         # Domain events
│   ├── exceptions.py                     # SocialProofNotFound, PlacementConflict, etc.
│   └── repositories.py                   # Repository interfaces (ports)
├── infrastructure/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── testimonial_model.py          # SQLAlchemy
│   │   ├── authority_item_model.py
│   │   ├── team_member_model.py
│   │   └── placement_model.py
│   ├── repositories/
│   │   ├── testimonial_repository.py     # impls
│   │   ├── authority_item_repository.py
│   │   ├── team_member_repository.py
│   │   └── placement_repository.py
│   └── adapters/
│       └── social_proof_port_adapter.py  # implements shared/links/ports/social_proof.py
├── application/
│   ├── services/
│   │   ├── testimonial_service.py
│   │   ├── authority_service.py
│   │   ├── team_service.py
│   │   ├── placement_service.py
│   │   └── social_proof_resolver.py      # read model "for_surface"
│   └── dto/
│       ├── testimonial_dto.py            # request + response DTOs
│       ├── authority_dto.py
│       ├── team_dto.py
│       └── placement_dto.py
├── api/
│   ├── router.py                         # mounted at /api/v1/social-proof/
│   ├── testimonials.py
│   ├── authority.py
│   ├── team_members.py
│   └── placements.py
└── tests/
    ├── unit/                             # domain + service unit tests
    ├── integration/                      # repo + API integration
    └── fixtures.py                       # factory-boy factories
```

Y en `shared/`:
```
backend/src/shared/links/ports/
└── social_proof.py                       # Port interface consumida por offer, landing, sales_agent, copilot
```

---

## 3 · API endpoints

```
# Testimonials (mismo pattern para authority + team_members)
GET    /api/v1/social-proof/testimonials
       ?surface_type=offer&surface_ref_id={uuid}   # scoped to specific surface
       ?include_brand=true                          # merge brand_homepage + surface-specific
POST   /api/v1/social-proof/testimonials            # create (optionally with initial placement)
GET    /api/v1/social-proof/testimonials/{id}
PATCH  /api/v1/social-proof/testimonials/{id}
DELETE /api/v1/social-proof/testimonials/{id}
POST   /api/v1/social-proof/testimonials/{id}/clone

# Placements
GET    /api/v1/social-proof/placements
       ?source_table=testimonial&source_id={uuid}
POST   /api/v1/social-proof/placements               # link existing entity to surface
DELETE /api/v1/social-proof/placements/{id}
PATCH  /api/v1/social-proof/placements/{id}          # edit sort_order, is_visible

# Resolver (read model "for surface")
GET    /api/v1/social-proof/for-surface
       ?surface_type=offer&surface_ref_id={uuid}&include_brand=true
       → { testimonials[], authority_items[], team_members[] }
```

Todos con `response_model=` Pydantic DTO. PII justificada (author_name, work_whatsapp).

---

## 4 · Fases de ejecución (8 días aprox)

### Fase 1 · Backend foundation (2 días)

**Artefactos:**
- 4 modelos SQLAlchemy + Alembic migration (idempotente, CREATE TABLE IF NOT EXISTS)
- Enums + domain entities Pydantic
- 4 repositorios async + interfaces
- Events + event publishing helper
- 5 services (crud x3, placement, resolver)
- API routers + request/response DTOs
- Port adapter en `shared/links/`
- Arch fitness tests (mín 8 casos nuevos)
- Unit + integration tests
- Data migration script con dry-run
- Registrar módulo en `main.py` con prefix `/api/v1/social-proof/`

**Acceptance:**
- `cd backend && .venv/bin/pytest tests/architecture/ -x -q` pasa con los nuevos tests
- `cd backend && .venv/bin/pytest tests/modules/social_proof/ -v` pasa (>80% coverage)
- Data migration dry-run: rowcount matches JSON items por tenant
- `docker exec visionarias_brain_dev alembic upgrade head` sin errores
- Port adapter consumible desde offer/landing sin import directo
- `.claude/rules/backend-ddd.md` + `tenant-isolation.md` respetadas

**User checkpoint:**
- Review del dry-run log antes de correr migration en prod
- Validación de nombres de campos + enum values antes de continuar (son API contract)

### Fase 2 · Frontend Brand Studio migration (2 días)

**Artefactos:**
- API clients `src/lib/api/{testimonial,authority-item,team-member,placement}.ts`
- Hooks React Query: `useTestimonials`, `useTestimonial`, `useAuthorityItems`, `useAuthorityItem`, `useTeamMembers`, `useTeamMember`, `usePlacements`
- 3 Instance pickers (Testimonial, Authority, TeamMember) siguiendo patrón de `BuyerPersonaInstancePicker`
- 3 Detail pages + 3 Landing pages (mismo patrón que Persona)
- Schemas por-ítem (`testimonial-item.schema.ts`, etc.) — incluyen `formula`, `examples`, `downstreamUses`, `lengthHint` cuando aplique
- Catch-all route `/brand-studio/[section]/instance/[itemId]/[[...fieldId]]/page.tsx` con dispatcher
- Breadcrumb extendido para nuevos patrones
- Deprecar lectura de `useBrandSettings().{team,testimonials,authority_vault}` — queda read-only hasta cleanup
- Redirects legacy si hubiese deep-links antiguos
- Tests vitest por hook + por componente
- E2E smoke: crear testimonio → editar → eliminar → aparece en offer editor

**Acceptance:**
- `cd frontend && npx tsc --noEmit` → 0 errors
- `cd frontend && npx eslint src/` → 0 new errors
- `cd frontend && npx vitest run` → all green (nuevos + pre-existentes)
- Arch tests frontend pasan (ratchet solo achica)
- Browser flow: `/brand-studio/testimonials` → picker + welcome → click persona → 4-col edit
- Mismo patrón validado para `/authority` y `/team`
- Dark/light mode correctos

**User checkpoint:**
- Review visual contra prototipos `option-a-enhanced.html` + `option-a-personas.html`
- Confirmar copy en Landing Pages (español neutro Latam)

### Fase 3 · Offer Studio reuse (1-2 días)

**Artefactos:**
- Offer editor consume `SocialProofResolver.for_surface(type="offer", ref_id=X)`
- Nuevos componentes en Offer Studio:
  - `OfferTestimonialsPicker` — lista testimonios con placement en esta oferta
  - `AddFromBrandVaultModal` — picker paginado de testimonios sin placement aquí, checkboxes múltiples, acción "Linkear" o "Clonar"
  - Equivalentes para authority + team
- Landing Generator lee via port `social_proof.for_surface`
- Sales Agent KB escucha eventos `TestimonialCreated/Updated` y refresca embeddings
- E2E: crear testimonio en brand → linkearlo a oferta → aparece en landing renderizado

**Acceptance:**
- Offer editor muestra solo testimonios con placement en esa oferta
- Toggle "Incluir brand-level" visible y funcional
- Linkear desde brand vault no duplica data
- Clone sí crea copia editable independiente
- Sales Agent usa catálogo nuevo via port (no import directo)

**User checkpoint:**
- Probar clone vs link en oferta real
- Validar UX del "used in N surfaces" warning antes de editar

### Fase 4 · Cleanup (1 día)

**Artefactos:**
- Alembic migration drop de columnas legacy en `brand_settings` y `offer.settings`
- Delete de Pydantic VOs legacy (`KeyFigure`, `BrandTestimonial`, `BrandAuthorityItem`)
- Delete de schemas `team.schema.ts`, `authority.schema.ts`, `testimonials.schema.ts` obsoletos
- Arch test nuevo `test_no_legacy_social_proof_refs` — imposible volver al JSON
- Documentación actualizada (`docs/domains/social-proof/INDEX.md`)
- Update `CLAUDE.md` / section-catalog references si hace falta

**Acceptance:**
- 0 referencias a `brand_settings.team/testimonials/authority_vault` en código
- 0 referencias a `offer.settings.testimonials` etc.
- Arch test nuevo verde
- Documentación publicada

### Fase 5 · Production rollout

**Artefactos:**
- Pase a producción via `/pase-produccion` standard workflow
- Monitoreo post-deploy (sentry + Grafana) 24h
- Data validation post-migration: queries comparando count vs legacy JSON

**Acceptance:**
- Zero user-visible regressions
- Zero data loss (rowcount validation)
- Todos los surfaces (brand, offer, landing, sales agent) consumen la nueva API

---

## 5 · Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Data loss en migración | Dry-run obligatorio + rowcount validator + legacy columns read-only hasta fase 4 |
| Drift legacy vs nueva tabla | Worker periódico detecta divergencia y alerta Sentry; fase 2 siempre lee DB |
| Tenant isolation breach | Arch test + runtime assertion en repository `__init__` + middleware |
| Cascade on delete edge cases | Soft-delete en ambas + test de integración específico |
| Placement conflicts (duplicados) | Unique constraint `(source_table, source_id, surface_type, surface_ref_id, deleted_at)` |
| Performance con muchos testimonios | Índices `(tenant_id, surface_type, surface_ref_id)` + pagination en endpoints |
| Copilot context stale | Event-driven refresh de embeddings en Sales Agent KB |
| Breaking deep-links | Redirects legacy mantenidos 2 sprints post-cleanup |

---

## 6 · Stack técnico y cumplimiento reglas proyecto

- SA 2.0 async, Pydantic v2, FastAPI, Alembic idempotente
- Python 3.12, Ruff 70+ rules, 0 errors
- Next.js 16 App Router, React 19, Tailwind v4, Shadcn UI, React Query
- TypeScript strict, ESLint 60+ rules, 0 new errors
- Native tests en WSL (no docker exec)
- Spanish neutro Latam en copy user-facing
- Todas las rutas DDD inside-out (domain → infrastructure → application → api)
- FSD-Lite en frontend (features/ agrupado por dominio)
- Tenant isolation en TODA query
- `response_model=` en TODOS los endpoints
- Soft deletes (`deleted_at`), nunca `session.delete()`
- Events publicados via shared event bus

---

## 7 · Checkpoints user (bloqueantes)

1. **Pre-Fase 1.2:** revisar nombres de columnas + enum values (API contract)
2. **Pre-Fase 1 deploy:** revisar dry-run log en DB clonada (rowcount + sample rows)
3. **Post-Fase 2:** validación visual browser vs prototipos (`option-a-enhanced.html` + `option-a-personas.html`)
4. **Pre-Fase 3:** decisión final clone vs link como default UX (propuesta: Link default, Clone como menú "Customize this one")
5. **Pre-Fase 5:** review deploy window + rollback plan

---

## 8 · Done criteria (para cerrar proyecto)

- [ ] 3 nuevas tablas con datos migrados desde legacy JSON (rowcount match)
- [ ] `/api/v1/social-proof/*` endpoints operativos + documentados
- [ ] Brand Studio: 4-col picker funcional en `/testimonials`, `/authority`, `/team`
- [ ] Offer Studio: sus 3 secciones consumen el catálogo shared via port
- [ ] Landing Generator + Sales Agent migrados al port nuevo
- [ ] Legacy JSON columns droppeadas
- [ ] 0 ESLint errors nuevos, 0 TS errors, 0 ruff errors
- [ ] Todos los tests (backend + frontend + E2E + arch) verdes
- [ ] Data migration verificada en prod sin pérdida
- [ ] `.claude/rules/*` respetadas al 100%
- [ ] Documentación en `docs/domains/social-proof/INDEX.md`
