# S1 Learnings — Domain Campaigns

> Owner: PM. Sesión 2026-04-29. Multi-spawn autónomo.

## Lo que funcionó

1. **Architect autónomo + framing 1000 clientes:** ZERO open questions en PR-3 + PR-4. Decisiones production-grade (DAG, lazy segment, worker queue partial idx, dual UNIQUE PARTIAL, AsyncSession, SQL-side filtering) tomadas sin chris-in-loop. Cada decisión justificada con razón escalabilidad.

2. **TDD por capa Inside-Out (DDD strict):** PR-3 domain → infrastructure → repo impls → arch tests. Cada capa RED ANTES GREEN. Tests counts altos: 160 domain + 27 arch + 309 PR-4 = ~500 tests verde sprint.

3. **PR-folder pattern + prompts pre-cocidos:** architect / builder / auditor recibieron prompts auto-contenidos. Spawn agente sin explicar contexto cada vez.

4. **Cero deuda técnica respect:** F-1 (PR-3 mypy) + F-2/3/4/5/7 (PR-4 REVIEW) todos resueltos antes ship. Auditor caught F-2 CRITICAL real (signature mismatch enmascarado por mocks) — sin auditor el bug llega producción.

5. **Sesiones paralelas convivieron limpio:** PI-2 voice-media-hardening + suggestions-engine + backfill-content-blocks + S1-copilot-maintenance-batch corrieron en paralelo sin colisión files. Boundaries M1 respetados todo el sprint.

## Lo que falló

1. **Multi-spawn diminishing returns en builder PR-4 Sub-C:** ~6 spawns para fix fixture pattern (`AsyncMock` vs `_patch_session` inconsistencia). Costó tokens. Lección: si builder pause >2 spawns en mismo issue → diagnostic exacto desde main session + spawn quirúrgico.

2. **Mocks excesivos enmascararon F-2:** 17 tests Sub-C pasaron por `AsyncMock` pero signature service real era distinta. Auditor caught en prod-like check. Lección: política "1 integration test sin mocks per critical feature" añadida (F-7 PR-4 implementa).

3. **Fixture path resolution `_CANDIDATE_PATHS` (PR-3 Sub-D)** — builder paused investigando, terminó siendo no-bug (path correcto). Lección: confirmar test approach antes spawn re-investiga.

4. **Sub-deliverables grandes en un solo spawn:** Sub-B PR-4 = 6 services + DTOs + ports + cache + bridge. Builder se quedó sin tiempo commitear. Lección: si Sub > 5 archivos productivos, splitear en commits incrementales explícitos.

## Decisiones que evitar repetir (si)

- ~~Mocks AsyncMock en API tests sin integration backstop~~ → política dual: unit tests con mocks + 1 integration sin mocks per surface crítica.
- ~~Schema assumption sin verify (lifecycle_stage en LeadModel)~~ → architect verifica schema vivo ANTES escribir CONTRACT.
- ~~PR.md tentative no concretado en sprint.md~~ → architect fills PR.md spec atomic con CONTRACT.md (S1 lo hizo OK, mantener en S2).

## Patrones nuevos cristalizados (replicar S2+)

1. **Bootstrap PR autónomo:** main session crea folder + templates + spawn architect "atomic PR.md + CONTRACT.md autónomo, framing 1000 clientes". Architect output ZERO open questions ideal.

2. **Architect decisión-tree justificada:** cada decisión arquitectónica documenta razón "1000 clientes" + alternative considered + why rejected. Patrón visible PR-3/PR-4 §17.

3. **Worker queue partial idx temprano:** any task table futuro debe incluir partial idx `WHERE status IN ('pending','scheduled')` desde día 1. Costo trivial migration, performance crítica scale.

4. **Cache TTL + Redis pub/sub invalidation:** mirror billing pattern PR-2. Multi-pod ready desde día 1 (no es post-MVP problem).

5. **uuid5 reproducible para seeds globales:** templates / categorías / refData. ON CONFLICT DO NOTHING. Idempotente cross-env.

6. **Auditor F-N findings + Resolution section append:** REVIEW.md NO se reescribe — append "## Resolution" con commits hashes resolviendo. Audit trail completo.

7. **Schema audit vivo en architect:** antes escribir CONTRACT, architect lee modelo SQLA real (no solo migration spec). Atrapa drift schema/spec early.

## Métricas sprint

| Métrica | Valor |
|---|---|
| PRs shipped | 2 (PR-3 + PR-4) |
| Commits totales | 21 |
| Tests verde scope | ~520 (PR-3 ~190 + PR-4 ~330) |
| Arch tests nuevos | 8 (4 PR-3 + 4 PR-4) |
| Migrations | 2 (campaigns domain + templates seed) |
| Endpoints REST | 23 |
| Templates globales | 5 |
| Domain entities | 6 + 1 port |
| Domain events | 11 |
| Repositories | 6 |
| Application services | 4 (Campaign + Segment + Template + FilterEvaluator) |
| DTOs Pydantic v2 | 15+ |
| Bloqueadores resueltos | 9 (F-1 PR-3 + F-2/3/4/5/7 PR-4 + 3 fixture/schema) |
| Open questions PM | 0 |
| Verdict final | PR-3 PASS, PR-4 PASS post-fix |
| Sesiones paralelas convivientes | 4 (PI-2 voice/suggestions/backfill + S1-copilot-batch) |

## Hand-off siguiente sprint

Ver `handoff.md`. S2 inicio post-handoff con surface domain consumible.
