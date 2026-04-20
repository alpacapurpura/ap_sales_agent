# Prompt — pegar en conversación nueva

Copia y pega todo lo que está **debajo de la línea**. Te arranca una conversación limpia con todo el contexto para ejecutar el proyecto Social Proof SSoT end-to-end.

---

Voy a ejecutar un proyecto multi-fase full-stack: migrar `Team`, `Authority` y `Testimonials` de arrays JSON embebidos en `brand_settings` → **entidades DB de primer orden con placements M:N**, convirtiéndolas en **Single Source of Truth** compartido entre Brand Studio, Offer Studio, Landing Generator y Sales Agent.

El plan y las decisiones arquitectónicas ya están locked. Objetivo: solución técnicamente prolija, escalable para vender el producto — priorizo calidad de código y patrones DDD sobre velocidad.

## Lee primero (en este orden)

1. **Plan completo con decisiones finales:** `docs/ux-sessions/2026-04-20-brand-studio-finder-nav/PLAN-social-proof-ssot.md`
2. **Implementación Finder ya terminada (contexto previo):** `docs/ux-sessions/2026-04-20-brand-studio-finder-nav/IMPLEMENTATION-REPORT.md`
3. **Reglas proyecto — mandatorias:**
   - `.claude/rules/backend-ddd.md`
   - `.claude/rules/tenant-isolation.md`
   - `.claude/rules/backend-migrations.md`
   - `.claude/rules/tdd-mandatory.md`
   - `.claude/rules/frontend-quality.md`
   - `.claude/rules/frontend-fsd.md`
   - `.claude/rules/architectural-fitness.md`
   - `.claude/rules/spanish-text.md`
   - `.claude/rules/parallel-safety.md`
   - `.claude/rules/copilot-resilience.md`
4. **Pattern de referencia:** `buyer_personas` ya migrado al mismo estilo — estudia `backend/src/modules/brand/infrastructure/models/buyer_persona_model.py`, `backend/src/modules/brand/infrastructure/repositories/buyer_persona_repository.py`, `frontend/src/features/brand-studio/pages/PersonaDetailPage.tsx`, `frontend/src/features/brand-studio/components/BuyerPersonaInstancePicker.tsx`. Copialo con las adaptaciones del plan.

## Contexto del trabajo previo (ya commiteado en development — NO re-hacer)

La conversación anterior dejó implementada la navegación Finder-style en Brand Studio:

- Tokens `--brand`, `--success`, `--warning` en `frontend/src/app/globals.css` (light+dark) + 12 dimension tokens `--brand-*`
- Primitives nuevos en `frontend/src/components/form-runtime/`: `FinderColumn`, `CompletionDot`, `FieldContextPanel`, `NextEmptyFieldCta`, `InstancePicker`, `instance-display.ts`
- `frontend/src/components/ui/inline-editable.tsx` — chrome-less textarea/input con auto-grow
- `frontend/src/features/brand-studio/components/BrandStudioBreadcrumb.tsx` + `BuyerPersonaInstancePicker.tsx`
- `frontend/src/features/brand-studio/pages/BuyerPersonasLandingPage.tsx`
- Schema extensions: `FieldSchema.layout | group | formula | examples | downstreamUses | relatedFields | lengthHint`; `SectionSchema.kind | instanceDisplay`
- Buyer personas end-to-end en 4-col: `/brand-studio/publico` (landing) + `/brand-studio/publico/persona/{id}` (4-col edit)
- Prototipo HTML en `docs/ux-sessions/2026-04-20-brand-studio-finder-nav/prototype/` servido en `http://localhost:8888/` — usalo como contrato visual

**Quality gates al cierre de esa sesión:** `npx tsc --noEmit` 0 errors · ESLint 0 errors nuevos · vitest 1384/1384 · arch tests 16/16.

## Lo que hay que construir

Entidades nuevas, 3 tablas + 1 link table, bounded context propio:

```
backend/src/modules/social_proof/
├── domain/ · infrastructure/ · application/ · api/ · tests/
```

Tablas:
- `testimonials` (id, tenant_id, author_name, author_role, author_avatar, content, media_type, rating, source_url, captured_at, ...)
- `authority_items` (id, tenant_id, entity_name, authority_type, context, proof_url, logo_url, obtained_at, ...)
- `team_members` (id, tenant_id, name, role, bio, headshot_url, is_primary_voice, gender, communication_style, socials..., gallery jsonb, sort_order, ...)
- `social_proof_placements` (id, source_table, source_id, surface_type, surface_ref_id, sort_order, is_visible, tenant_id, timestamps, soft delete)

Decisiones técnicas clave (ver plan §1 para detalles):

- **Placements M:N desde día 1** (no `scope` column) — entidades son tenant-scoped; dónde se muestran vive en `social_proof_placements` con `surface_type` (brand_homepage, offer, landing_page, email_sequence, sales_agent_kb) y `surface_ref_id` nullable
- **Eventos de dominio** publicados al bus compartido (`TestimonialCreated`, `PlacementAdded`, etc.) — consumidores suscriben sin import directo
- **Puerto `shared/links/ports/social_proof.py`** consumido por offer, landing, sales_agent, copilot — evita cross-module imports
- **Read model `SocialProofResolver.for_surface()`** para el query caliente "dame todo lo visible en superficie X" — sin N+1, con eager loading
- **Architecture fitness tests** nuevos desde el principio (tenant isolation, no cross-module imports, cascade behavior, enum completeness, response_model, domain purity, events emission)
- **3 tablas especializadas** (no polimórficas) — campos distintos, índices precisos
- **Clone vs link** ambos disponibles: link default (SSoT), clone como "customize this one"
- **Soft delete en ambas tablas** — delete testimonio cascade a placements; delete placement deja testimonio intacto
- **Copilot integration** via `ModuleDescriptor.collections` + `module_registry.py` — tools route-based reciben instance_state + placements actuales
- **Data migration Alembic en 3 pasos** idempotentes (CREATE TABLE IF NOT EXISTS, seed from legacy JSON, create default placements), con dry-run obligatorio en DB clonada antes de prod

## Ejecución — sigue el plan por fases, con checkpoints

El plan detalla 5 fases. Para cada fase:

1. Verifica quality gates previos (`cd backend && .venv/bin/pytest tests/architecture/ -x -q` y `cd frontend && npx vitest run src/__tests__/architecture/`)
2. Escribe tests PRIMERO (TDD mandatorio — regla `.claude/rules/tdd-mandatory.md`)
3. Implementa siguiendo DDD inside-out (domain → infrastructure → application → api)
4. Corre quality gates nativos (`.claude/rules/docker-first.md` — nunca docker exec para tests/lint/tsc)
5. **Detente en los checkpoints del usuario** (plan §7) y pide review explícito antes de continuar:
   - Pre-Fase 1.2: nombres de columnas + enum values
   - Pre-Fase 1 deploy: dry-run log en DB clonada
   - Post-Fase 2: validación visual browser vs prototipos `option-a-enhanced.html` y `option-a-personas.html` (servidos en http://localhost:8888/)
   - Pre-Fase 3: decisión final clone vs link default UX
   - Pre-Fase 5: deploy window + rollback plan

## Cómo ejecutar

**Usa el skill `nicolify-feature`** para orquestar el workflow multi-agente con checkpoints — es lo que está hecho para features full-stack como esta (architect → backend → backend-auditor → ux-designer → frontend, con puntos de pausa).

Si nicolify-feature no calza, alterna entre `/backend-expert` (fases 1, 3-backend, 4, 5) y `/frontend-expert` (fases 2, 3-frontend). **Nunca mezcles fases** — termina una antes de empezar la siguiente.

## Reglas de ejecución no-negociables

1. **Todo en rama `development`** — no crear feature branches ni worktrees (regla `parallel-safety.md`). Stagear por nombre (`git add path/to/file1 file2`), nunca `git add .`.
2. **TDD obligatorio** — tests antes de impl. Test regresión antes de fix. Sin excepciones.
3. **Tenant isolation** en TODA query. Arch test lo verifica.
4. **Migraciones idempotentes** — `CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`. Nunca `op.create_table()`. Test en DB clonada antes de prod.
5. **`response_model=`** en TODO endpoint. PII justificada en comentario cuando aplique.
6. **Soft delete siempre** — `deleted_at`, nunca `session.delete()`. Filtros WHERE `deleted_at IS NULL`.
7. **SA 2.0** — `select(Model).where(...)`, nunca `session.query()`.
8. **AsyncSession** en código nuevo.
9. **Cross-module comunicación** via eventos o `shared/links/ports/`. Nunca import directo.
10. **Spanish neutro LatAm** en todo texto user-facing — tuteo, sin voseo, tildes correctas. Aplica a DTOs con mensajes, prompts LLM con output visible, schemas con labels/hints/placeholders. No aplica a logs/errores técnicos internos.
11. **FastAPI `redirect_slashes=False`** ya está en main.py, no tocar.
12. **Native tests en WSL** — nunca docker exec para lint/tests/tsc.
13. **Arch tests ratchet** — allowlists solo pueden achicarse. Cualquier violación nueva falla build.
14. **0 ESLint errors nuevos, 0 TS errors, 0 Ruff errors** — pre-existentes quedan (no fix en este proyecto salvo si están en archivos que toques).
15. **Sin commit hasta que yo lo autorice** — al final de cada fase, reportá qué pasó y esperá aprobación visual antes de commitear.

## Deliverables por fase (resumen)

**Fase 1 — Backend (2 días)**
- Módulo `social_proof/` completo (domain + infra + application + api + tests)
- Alembic migration con 4 tablas + indexes + constraints + data seed desde JSON legacy + placements default
- Port adapter en `shared/links/`
- Registro en `main.py` con prefix `/api/v1/social-proof/`
- 8+ arch tests nuevos
- Copilot module_registry extendido
- Data migration dry-run validado en DB clonada

**Fase 2 — Frontend Brand Studio (2 días)**
- API clients `src/lib/api/{testimonial,authority-item,team-member,placement}.ts`
- 7 hooks React Query (list + single + placements)
- 3 Instance pickers + 3 Detail pages + 3 Landing pages (patrón `BuyerPersona*`)
- Schemas por-ítem en lugar de array wrappers viejos
- Catch-all route `/brand-studio/[section]/instance/[itemId]/[[...fieldId]]/page.tsx` con dispatcher
- Deprecar lectura de `useBrandSettings().{team,testimonials,authority_vault}` — quedan read-only
- E2E smoke para crear→editar→link→eliminar

**Fase 3 — Offer reuse (1-2 días)**
- Offer editor consume `SocialProofResolver.for_surface(type="offer", ref_id=X)`
- Componentes `OfferTestimonialsPicker`, `AddFromBrandVaultModal` + equivalentes
- Landing Generator y Sales Agent migrados al port shared
- E2E cross-surface: crear en brand → link a oferta → renderiza en landing

**Fase 4 — Cleanup (1 día)**
- Drop legacy JSON columns
- Delete VOs + schemas legacy
- Arch test `test_no_legacy_social_proof_refs`
- Documentación `docs/domains/social-proof/INDEX.md`

**Fase 5 — Rollout**
- `/pase-produccion` flow estándar
- Monitoreo post-deploy 24h
- Data validation

## Acceptance final (cierre de proyecto)

Checklist completo en plan §8. Resumido:
- 3 tablas nuevas + 1 link table operativas con data migrada (rowcount match)
- API `/api/v1/social-proof/*` documentada
- Brand Studio 4-col funcional en 3 secciones nuevas (testimonials, authority, team)
- Offer/Landing/Sales Agent usando el port shared
- Legacy droppeado
- Todos los quality gates verdes (backend + frontend + E2E + arch)
- Zero data loss verificado en prod
- `.claude/rules/*` respetadas al 100%

## Empezá así

1. `git status && git branch --show-current` — verificar development limpio (protocolo parallel-safety)
2. Leer los docs referenciados arriba (plan completo + IMPLEMENTATION-REPORT + reglas)
3. Estudiar el pattern de `buyer_personas` (frontend + backend) para imitar estilo
4. Crear tasks con `TaskCreate` para las 5 fases + sub-tareas de fase 1
5. Arrancar Fase 1.1 (models + migration) con TDD

Antes de cualquier commit o push, reportá avance y esperá confirmación. Entre fases hay checkpoints bloqueantes.

Preguntame si algo no queda claro del plan antes de empezar — prefiero 3 minutos de aclaración ahora que 2 horas de rework después.
