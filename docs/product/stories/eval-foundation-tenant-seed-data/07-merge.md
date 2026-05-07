# 07-merge.md — eval-foundation-tenant-seed-data

**Owner:** `/pm`
**Date:** 2026-05-07
**Auditor verdict:** APPROVED (`CHECKPOINTS.md` C1-C5 GREEN, 0 WARN/FAIL)
**State transition:** reviewing → done

## Tickets merged

| Ticket | Commit SHA | State | Audit |
|---|---|---|---|
| T-1 | 121fe7ba | audit-passed | APPROVED |
| T-2 | fcd99459 | audit-passed | APPROVED |
| T-3 | d4654e5e | audit-passed | APPROVED |
| T-4 | 46b558b3 | audit-passed | APPROVED |

Plus follow-up SHA backfills: 5d75b4ff, 359cbcda, 59731468.

## Capability promotion (Step 5 / Conv 3)

### sales-conversational-engine.yaml — UPDATE

- `last_audit`: 2026-05-04 → 2026-05-07
- `stories_live`: 3 → 4
- `stories_total`: 4 → 5
- `story_ids`: + `eval-foundation-tenant-seed-data`
- Stories table: + row con status `live (merged 2026-05-07)` y path archived
- `eval` block expanded with:
  - `seed_story_introduced: eval-foundation-tenant-seed-data`
  - `seed_merged_at: 2026-05-07`
  - `seed_test_coverage`: 5 paths a test files (loader/realism/schema_alignment/dialect_catalog/pii_scanner)

### Modules affected

- `docs/product/modules/sales-agent.md`: auto-list marker regenera con la capability actualizada (R32 reconcile + R33 BACKLOG regen)

## Outcome update

`docs/product/outcomes/pi-12-sales-agent-eval-foundation.md`:
- `last_modified`: 2026-05-06 → 2026-05-07
- `story_ids`: comentado `eval-foundation-tenant-seed-data` como DONE 2026-05-07 (archived)
- `eval-foundation-simulator-homologation` marked UNBLOCKED (era pre-requisito)

7 stories downstream del PI-12 ahora pueden arrancar refining → refined → ready con confianza en data ground truth concreta:
- eval-foundation-simulator-homologation (story B — wire client_simulator/)
- sales-agent-personas-instrumented-runtime (story C — personas-as-simulators)
- sales-agent-goldens-3-tenants-dataset (story D — goldens-generated-from-simulation)
- sales-agent-voice-fidelity-grader-runtime (story E — MAJ-EVAL voice fidelity grader)
- sales-agent-eval-pass-k-tracking (story F — Bloom-style pass^k)
- sales-agent-voice-fidelity-ci-gate (story G — CI gate w/ dynamic threshold)
- sales-agent-eval-cost-budget-cap (story H — cost cap)
- sales-agent-adversarial-jailbreak-suite (story I — PersonaGym Toxicity Control axis)

## Archive

Story folder migrado:
```
docs/product/stories/eval-foundation-tenant-seed-data/
  → docs/archive/2026/stories/eval-foundation-tenant-seed-data/
```

Snapshot inmutable. NO modificar post-archive.

## Learnings (suggested entries)

Decisiones cardinales para `docs/process/learnings.md`:

1. **Curación densa T-4 con loop iterativo Chris**: paradigma efectivo para data fixtures de alta densidad. Round 1 (single tenant + research específico) + Round 2 (replicar densidad a N restantes con benchmarks por sector) ahorra tokens y mejora coherencia vs intentar todo en single shot.

2. **Anti-sobreventa policies por tenant**: 3 de 5 tenants (A2 médica, A3 dental, A5 IA) implementan política documentada anti-sobreventa que sirve como diferencial competitivo + filtro decline para sales_agent. Útil para personas adversariales tests.

3. **Decline policies anti-mal-fit**: 2 de 5 tenants (A4 wantrepreneurs, A5 vibe-coders) implementan decline policies explícitas — sales_agent debe DECLINE professionally, NO upsell forzado. CRITICAL test value en personas adversariales suite.

4. **Variants offer-expert L10 application**: PERIOD para cohorts fechadas, TIER para niveles escalonados (basic/pro/elite), PACK para cantidades. 11 variants cross-tenants demuestran cobertura tipos de oferta LatAm.

5. **Discovery call cierre alta-ticket**: Nicolify scheduling (clon-Calendly built-in) integrado en 4 de 5 tenants para ofertas alta-ticket (>PEN 1k single-shot o >PEN 4k retainer). Anti-DM-impulse-buy.

## Verification post-merge

- [ ] Capability YAML válida (parseable + fields esperados)
- [ ] Outcome story_ids list reflects archive
- [ ] BACKLOG.{yaml,md} regenerated (auto via R33 hook)
- [ ] Reconcile_capabilities.py run sin errores (R32)
- [ ] Story folder archived a docs/archive/2026/stories/
- [ ] checkpoint.md state=done (final transition)
- [ ] modules/sales-agent.md auto-list refresh
- [ ] WIP cap reviewing 1→0 (libera capacidad para próxima story)

## Próximo paso

Outcome PI-12 desbloqueado para próxima story foundation:
**`eval-foundation-simulator-homologation`** (story B — wire client_simulator/, 2-3d).
