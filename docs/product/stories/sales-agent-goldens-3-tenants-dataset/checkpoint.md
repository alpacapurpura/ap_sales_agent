---
story_id: sales-agent-goldens-3-tenants-dataset
outcome: pi-12-sales-agent-eval-foundation
state: refined
phase: SPEC_RATIFIED
last_artifact: 01-spec.md  # v3 ratificada Chris 2026-05-08T07:00Z
last_modified: 2026-05-08T07:00:00Z
next_action: "/architect orchestrator → spawna /architect-be (script + schema + scanner + pre-commit hook + capability extension) → produce ready package (03-arch + 04-validators + 05-guidelines + 06-tickets) → state=refined→ready → /dev-team build (espera Story C build done — bloqueador hard)"
ratified_by_chris: true
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: true   # refinement done; architect parallel-safe; build espera Story C build done
blocked_reason: null   # A+B done, C refined → spec v3 ratified, unblocked para /architect
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
- 2026-05-08 06:30Z — `/po` redactó `01-spec.md` v2 synthetic-first reframe. Consume Story A (`load_eval_tenant` + dialect_catalog) + Story B (`run_simulation` + cost-bucket tables) + Story C (`load_actor_profile_for_tenant` + 15 archetype-aware personas). Coverage matrix 5 tenants × 3 kinds × 1-2 winners = **20-30 goldens** target. Pipeline 2 fases: (1) script `generate_golden_candidates.py` corre 75 sims paralelas via Story B `asyncio.gather + Semaphore(10)`, (2) preview generator + Chris curación manual + `promote_golden` CLI. Schema `GoldenScenarioModel` v1 cement con SCHEMA_MIGRATIONS forward-compat (Story B H1 reused). PII defense-in-depth scanner (regex email/phone/DNI/CUIT/RUT/RFC LatAm + nicolify URLs) en pre-commit hook Section 8. 4 scenarios obligatorios (happy/negative/edge/adversarial). 17 decisiones cardinales D1-D17. 8 open questions Q1-Q8 awaiting Chris ratificación.
- 2026-05-08 07:00Z — Chris ratificó Q1-Q8 (todas opción A recomendada, except Q3=B Markdown table inline). `/po` bump v3 inline: D12 cement `preview.md` Markdown (NO HTML/Streamlit) + D14 `expected_voice_attributes` auto-extract `personality_profile` + Chris `notes` freeform override. Scenario 1 actualizado preview format. `ratified_by_chris: true`. Transition `state: refining → refined`. `next_action: /architect orchestrator` (consume 01-spec.md → produce ready package). Story C build sigue siendo bloqueador hard para Story D build (no para /architect refinement).
