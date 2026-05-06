---
story_id: sales-agent-goldens-3-tenants-dataset
outcome: pi-12-sales-agent-eval-foundation
state: refining
phase: PM_DRAFT_REFRAMED
last_artifact: 01-spec.md  # v1 archivado-en-repo (committed f7624c9f), reframe v2 pendiente
last_modified: 2026-05-06T17:11:00Z
next_action: "Esperar A/B/C (tenant-seed + simulator-homologation + personas-as-simulators) refined. Después /po redacta 01-spec.md v2 (reframe synthetic-first). Ya NO es 'extraer 12 goldens de prod' — es 'generar 20-30 goldens desde simulator + curar manualmente'."
ratified_by_chris: false
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: false
blocked_reason: "Reframe synthetic-first 2026-05-06 — depende de stories upstream A/B/C. 01-spec.md v1 (extracción de prod) quedó archivado-en-repo per commit f7624c9f. Spec v2 awaiting A/B/C refined."
audit_iterations: 0
legacy_exempt: true
migrated_from: docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/*/stories/sales-agent-goldens-3-tenants-dataset/
reframe_history:
  - date: 2026-05-06T17:11:00Z
    by: /pm + Chris ratificación
    from: "v1 — extraer 12 goldens de tablas sales_agent_session producción (12 = 3 tenants × 4 escenarios)"
    to: "v2 — generar 20-30 goldens desde simulator dual-LLM + curación manual Chris (state-of-the-art mayo 2026)"
    reason: "Sales_agent NO está en producción + clientes reales NO usan el sistema. Imposible extraer goldens reales. Synthetic-first es el patrón canónico research mayo 2026 (Anthropic Bloom + AWS Strands + τ-Bench + PersonaGym)."
    role_in_outcome: "D — goldens-generated-from-simulation"
---

## Bitácora

- 2026-05-04 20:00 — `/pm` creó folder + `00-story.md`. Phase=PM_DRAFT, status=pending. Bloqueado hasta S1 + decisión tenants.
- 2026-05-06 — Migrado a paradigma v4: state=refining (legacy_exempt). Pendiente /po para spec ratification.
- 2026-05-06 16:00Z — `/po` redactó `01-spec.md` v1 (extracción de prod), 4 scenarios + 10 open questions. Commit `f7624c9f` push origin/development.
- 2026-05-06 17:11Z — **REFRAME synthetic-first** (Chris ratificó). v1 quedó archivado-en-repo. Story se reposiciona como rol D en sub-épica `eval-foundation-*`. Depende ahora de tenant-seed (A) + simulator-homologation (B) + personas-as-simulators (C). Spec v2 awaiting A/B/C refined.
