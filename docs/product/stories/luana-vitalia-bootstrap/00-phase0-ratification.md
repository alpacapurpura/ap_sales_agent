---
story_id: luana-vitalia-bootstrap
phase: Phase 0 ratification
sesion: 1
date: 2026-05-13
ratified_by: chris
owner: /pm
---

# Phase 0 Ratification — Story 11 luana-vitalia-bootstrap

> Captura decisiones cardinales Sesion 1 Fase A antes de /po-ux 01-spec.md authoring. SSoT decision history.

## Contexto

- **Outcome:** luana-platform-migration (10/14 stories done, 71% complete)
- **Story 10 closure:** 2026-05-16 APPROVED 27/27 CHECKPOINTS (commit `cc508afb`)
- **Story 11 unblock:** Story 10 done → vitalia/comunify/lupulo bootstrap unblocked
- **Complejidad estimada:** very_high (25-35 tickets, 3-4 sem, AGENTIC production code → Opus mandatory)
- **Surface:** full-stack new brand app vertical-medical extensions

## Decisiones cardinales (ratified Chris 2026-05-13)

### Q1 — Scope = A. Full big-bang per 00-story.md

**Decisión:** Bootstrap completo Sesion 11 sin phase split.

**Implicación:**
- 25-35 tickets en Story 11 single
- Skeleton + BrandConfig + routes + vertical-medical agentic tools + extractors + workflow + KB packs + HIPAA-lite + payment + Clerk app #2 + K8s deploy + piloto fixtures all bundled
- Sonnet build BE/FE non-agentic + Opus build AGENTIC production code (R23)
- ETA target_state: developed by 2026-07-04 (~6 weeks from refining start)

**Rationale:** Pattern Story 10 (full big-bang) demostró efectivo. Re-scoping pattern Sesion 10 (-99% cost variance) compensa risk overshoot.

### Q2 — Agentic scope = A. Full per spec

**Decisión:** Implement ALL vertical-medical agentic Story 11.

**Tools (production AGENTIC):**
- `prepaid_payment_check` — verify payment_status pre-confirm booking
- `treatment_followup_check` — adherence tratamiento turn-by-turn
- `medical_consent_request` — consentimiento informado pre-procedimiento
- `appointment_reschedule_with_doctor` — re-agenda con disponibilidad doctor

**Extractors (copilot):**
- `MedicalKBExtractor` — historia médica desde PDFs
- `DentalHistoryExtractor` — historia dental specific

**Workflow (copilot):**
- `TreatmentFollowupWorkflow` — plan tratamiento turn-by-turn

**KB packs:**
- `medical_kb_dental_v1`
- `medical_kb_psychology_v1`
- `medical_kb_psychiatry_v1`

**Owner constraint:** ALL AGENTIC production code (tools + extractors + workflow) = Opus 4.7 mandatory (R23). Sonnet ban absolute. Tests/docs over AGENTIC OK Sonnet.

### Q3 — Deploy infra = B. Subdir luana-platform + extraction Story 11.bis

**Decisión:** Vitalia code lives en `luana-platform/vitalia/` durante Story 11. Brand extraction a `alpacapurpura/vitalia-brand-repo` como Story 11.bis post-validation.

**Pattern:** Replica Story 10 dual-state pattern (AISALESHT FE+BE → `luana-platform/nicolify/` durante Story 10; future "nicolify-brand-repo extraction" story extrae a separate repo).

**Implicación cross-repo:**
- Story 11 commits live en `luana-platform/vitalia/` 
- Consume `@luana/*` + `luana_core_*` via workspace symlinks (no GH Packages until Story 9 publishing stabilized)
- Future Story 11.bis: rsync + delete pattern (Story 10 T-13 precedent) extracts `vitalia/` to standalone brand-repo

**Per Chris framework "cada marca su propio deploy"** (ratified Story 10 Q2 Sesion 10 2026-05-16 — `docs/process/learnings.md`):
- luana-platform monorepo = shared `@luana/*` + `luana_core_*` packages ONLY
- Each brand eventually owns its own deploy stack (compose, Dockerfile, deploy workflow, CF tunnel, GHCR namespace, DNS)

### Q4 — Setup ownership = B. Chris UI manual cada step

**Decisión:** /pm prepara verification + commands; Chris ejecuta via external UI para irreversible/production-adjacent operations.

**Operations requiring Chris UI gate:**
- Clerk dashboard signup app #2 (VITALIA_CLERK_APP_ID provisioning + JWT issuer config)
- K8s cluster provision (DigitalOcean/Hetzner/AWS — Chris choice)
- DNS records vitalia.health (Cloudflare dashboard)
- Payment gateway production keys:
  - Stripe Healthcare flag activation (manual Stripe support request)
  - MercadoPago production credentials
- Domain registration if vitalia.health unavailable (alternative pick)

**/pm autonomous scope:**
- K8s manifest generation YAML
- Cloudflare API tunnel setup script (post Chris cluster + DNS)
- BrandConfig declarative YAML
- Application code (routes + agentic + UI + tests)
- Sandbox payment integration (Stripe test mode + MercadoPago test)

**Pattern:** Per Story 10 Q4=B precedent (T-14 GH archive AISALESHT, DROP DATABASE) — irreversible/production-adjacent = Chris UI gate. Story state can transition `done` while operational action remains `awaiting_chris`.

### Q5 — Piloto = Research-driven fixtures

**Decisión:** Story 11 cierra con fixtures realistic basadas en research de clínicas reales LatAm. Defer real clínica piloto a Story 11.bis o future onboarding push.

**Mechanics (Q5b=A + Q5c=C — Mixed):**
- /pm Web research durante 01-spec.md authoring: 2-3 clínicas reales LatAm
  - 1 dental (Argentina o México)
  - 1 psychology (Chile o Colombia)
  - 1 psychiatry (LatAm broad)
- Chris agrega 1-2 URLs adicionales si tiene listas (referidos, conocidos, target market)
- /pm WebFetch extrae:
  - Brand identity (logo, paleta, voice tone)
  - Servicios + pricing tiers
  - Booking flow patterns
  - Voice/copy samples
- Fixture data populated en `vitalia/fixtures/clinics/` (3 archetypes: dental + psychology + psychiatry)

**Acceptance Story 11:**
- 3 clínicas fixtures programmatic complete flow: signup + Brand Studio + offer medical_services + booking prepaid + payment sandbox + agendar cita
- Sales agent responde con voz Vitalia (default archetype, no voice cloning per BrandConfig features.voice_cloning=False)
- Compliance guardrails ON (smoke test prompt-injection)
- HIPAA-lite disclaimers en respuestas sensibles

**Real clínica piloto:** Story 11.bis post-deploy con clientes onboard.

### Q6 — Halts = A. H1-H13 verbatim adaptados

**Decisión:** Reuse Story 10 halt triggers H1-H13 verbatim.

**H1-H13 inventory (from Story 10):**
- H1: cost variance >100% vs budget
- H2: validators bloqueados >cap iter (3 retries)
- H3: arch fitness violation introduced
- H4: spec drift detected (impl != spec ratified)
- H5: tenant isolation regression
- H6: PII leak detected
- H7: Spanish neutro violation user-facing (excepción sales_agent voice)
- H8: alembic consolidation conflict (NO aplica Story 11 — dormant)
- H9: cross-module import boundary violation
- H10: anti-duplication detection (shared abstraction needed)
- H11: anti-default-flip-audit violation (flag flip without test path migration)
- H12: hotfix repro_verified false
- H13: builder spawn refusal (e.g., AGENTIC production with Sonnet)

**Adaptación Story 11:**
- H8 dormant (no schema consolidation work)
- H11 dormant (no flag flips planned)
- H1-H7 + H9-H10 + H12-H13 active

**No nuevos H triggers Vitalia-specific.** Existing inventory cubre HIPAA (H7 Spanish + medical safety bleeding into H6 PII), payment (H10 duplication risk + H13 spawn refusal), Clerk (Q4 gate doesn't need halt — Chris UI manual is normal flow).

### Q7 — Sesion 1 scope = A. Spec only

**Decisión:** Sesion 1 Story 11 termina post-spec ratification.

**Sesion 1 deliverables:**
1. ✅ Phase 0 ratification doc (THIS file)
2. Checkpoint state parked → refining (DONE)
3. /po-ux drafts `01-spec.md` con Gherkin + wireframes inline + fixtures research-driven
4. Chris ratifica spec
5. Checkpoint state refining → refined
6. SESSION-1-CLOSE-2026-05-13.md

**Defer Sesion 2:**
- /ux-agentico drafts `02-design-agentic.md` (vertical-medical conversational flows + tool sequences + state machines + slot architecture)
- /architect orchestrator spawns architect-{be,fe,agentic} → 03-arch.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml
- State refined → ready

**Sesion 3+:**
- /dev-team autonomous build per 06-tickets.yaml
- State developing → developed

**Rationale:** Parallel pattern Story 10 Sesion 5 (Q&A + spec ratification + close). Avoid Sesion 1 overshoot 600k context budget + Opus cost. Phase 0 decisions capture sufficient context for Sesion 2 /ux-agentico + /architect entry.

## Hand-off Phase 2

Phase 2 owner: `/po-ux` skill (this same /pm orchestrator invokes skill protocol).

Phase 2 entry conditions:
- ✅ Phase 0 decisions ratified (Q1-Q7)
- ✅ Checkpoint state=refining
- ✅ Research mandate clear (Q5c=C mixed: /pm research 2-3 + Chris adds 1-2)

Phase 2 expected output:
- `01-spec.md` con:
  - Gherkin scenarios (signup + Brand Studio + offer + booking prepaid + payment + agentic tools surface + workflow + KB extractor surface)
  - Wireframes inline ASCII OR HTML mockup para pantallas principales (signup, Brand Studio simplificado medical, offer wizard medical_services, booking prepaid UI, treatment followup dashboard)
  - Fixtures section (3 LatAm clinics research-driven realistic data)
  - HIPAA-lite guardrails specification
  - Compliance gates (prompt-injection smoke test)
  - Acceptance criteria

## Sesion 1 cost tracking baseline

| Phase | Tokens spent | Cumulative | Notes |
|---|---|---|---|
| Fase A Q&A (Q1-Q7c) | ~15-20k | ~15-20k | Bootstrap 10 reads + 4 AskUserQuestion |
| Phase 1 prep | ~5k | ~20-25k | Docker check + archive verify + checkpoint update |
| Phase 2 spec authoring | TBD | TBD | /po-ux + WebSearch + WebFetch |
| Phase 3 ratification | TBD | TBD | Chris review loop |
| Phase 5 close doc | TBD | TBD | Sesion 1 close + handoff Sesion 2 |

Sin caps presupuestales (per prompt directive). Tracking only.
