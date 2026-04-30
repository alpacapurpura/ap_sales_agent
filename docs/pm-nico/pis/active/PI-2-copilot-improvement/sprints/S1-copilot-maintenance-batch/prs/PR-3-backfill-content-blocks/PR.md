# PR-3-backfill-content-blocks

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-3-backfill-content-blocks |
| Sprint padre | S1-copilot-maintenance-batch |
| PI padre | PI-2-copilot-improvement |
| Estado | in-progress |
| Tipo | infra + migration |
| Esfuerzo | S |
| Owner PM | /pm |
| Claimed by session | sesión 2026-04-29 main thread (Opus 4.7) |
| Inicio | 2026-04-29 (architect spawn) |

## Problema (user-facing)

Migración `20260422_1200_copilot_multimodal.py` introdujo `blocks` (lista estructurada) coexistiendo con `content` legacy. Codec convierte v1→v2 on-fly al leer, pero filas legacy nunca se backfill. Resultado:
- Reporting que asuma todas filas tienen `blocks` falla
- Cualquier feature futura que dependa solo de `blocks` requiere check legacy
- Forward-compat dead code crece (codec v1 reader debe vivir indefinidamente)

JTBD invisible: "como mantener Nicolify, quiero el modelo limpio sin formato dual permanente".

## Outcome esperado

- Script Python idempotente que escanea filas con `content != null AND blocks IS NULL`, convierte content→blocks usando codec actual, persiste blocks
- Alembic data migration que invoca el script en upgrade (idempotent)
- Cleanup: codec v1 reader mantiene compat para safety, pero log warning si encuentra v1 post-migration
- Reporte: `legacy_content_rows = 0` al cierre del sprint

## Walking skeleton (mínimo viable cohesivo)

1. `scripts/backfill_copilot_content_to_blocks.py` — CLI con `--dry-run` (default) + `--apply` + `--batch-size N` + `--tenant-id` opcional
2. Script: `select where content IS NOT NULL AND (blocks IS NULL OR blocks = '[]')` → batch convert via codec → update
3. Logging: por batch reporta count + sample IDs
4. Alembic data migration `2026XXXX_backfill_copilot_blocks.py` — invoca script (`op.execute(...)` o python in-migration)
5. Tests: fixture seed legacy rows → run script dry-run → run apply → assert blocks populated + content preserved (no DELETE de content para safety)

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A: Script Python standalone + alembic invoca | Reusable manual + automático en deploy. Dry-run safety | LOC mayor (script + migration + tests) | ELEGIDA |
| B: SQL-only en alembic raw | Trivial | Codec v1→v2 tiene lógica Python (no trivial en SQL) | descartada |
| C: Background worker ARQ por tenant | Async + retry | Overkill para data one-time | descartada |

## Validación técnica preliminar (Technical Sanity Check)

- Modules afectados: `backend/scripts/`, `backend/alembic/versions/`, codec en `modules/copilot/infrastructure/codec/` (verificar nombre exacto)
- Blockers conocidos: ¿cuántas filas legacy hay en prod? — antes de apply en prod, query count. Dev DB tiene seed minimal
- Tiempo estimado: 1 sesión architect + 1 sesión builder + 1 sesión auditor
- Alternativas técnicas: usar `tqdm` para progress (descartado, structlog progress por batch enough)

## Decisiones diferidas (explícitas)

- ¿Eliminar `content` field post-backfill? → NO en este PR (safety: mantener content readable como fallback). Eventual `DROP COLUMN` en PR futuro tras validar 0 lecturas v1 por N días
- ¿Backfill corre auto en deploy o requiere comando manual? → Auto via alembic (idempotente, dry-run en CI antes de prod)

## Out of scope

- DROP `content` column (safety wait, PR futuro)
- Backfill de `copilot_trace_event` u otras tablas (solo `copilot_message`/equivalente)
- UI cambio (transparente para user)
- Eliminación codec v1 reader (mantener safety)

## Copilot-first checklist

- [ ] ¿Operable conversacional desde copilot? **NO** — script de mantenimiento interno, no flujo user
- [ ] ¿Qué tools nuevos requiere? Ninguno
- [ ] ¿Cards/UI nueva? No
- [x] Si NO copilot → razón documentada: data migration backend, transparente para user

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` + `copilot-expert` | `prompts/01-architect-start.md` | `CONTRACT.md` |
| Implementation | `nicolify-backend` + `copilot-expert` | `prompts/02-builder-start.md` | code + tests + IMPL-LOG.md |
| Audit | `nicolify-backend-auditor` + `copilot-expert` | `prompts/03-auditor-start.md` | `REVIEW.md` |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/copilot.md` update |

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| Script | `backend/scripts/backfill_copilot_content_to_blocks.py` | nuevo |
| Migration | `backend/alembic/versions/2026XXXX_backfill_copilot_blocks.py` | nueva (data migration idempotente) |
| Tests | `backend/tests/scripts/test_backfill_copilot_content_to_blocks.py` | nuevos |
| current-state/ | `current-state/copilot.md` | append capability "Backfill content→blocks completed" + lineage |

## Tests requeridos (TDD)

- `test_dry_run_does_not_mutate.py` — dry-run sobre seed legacy → assert no UPDATE
- `test_apply_converts_legacy_rows.py` — seed 5 legacy → run apply → assert 5 rows tienen blocks shape correcto + content preserved
- `test_idempotent_rerun.py` — apply 2x → segunda run = 0 rows updated
- `test_batch_size.py` — seed 100 + batch 10 → 10 batches procesados
- `test_per_tenant_filter.py` — seed mix tenants + `--tenant-id X` → solo X procesado

## Aceptación

- [ ] Tests verdes (5 nuevos)
- [ ] Lint/type check verdes
- [ ] Migración idempotente (`IF EXISTS` checks + safe re-run)
- [ ] Dry-run reporta count antes apply
- [ ] `IMPL-LOG.md` completo
- [ ] `REVIEW.md` PASS
- [ ] `RESULT.md` escrito por PM
- [ ] `current-state/copilot.md` actualizado
- [ ] Decisiones registradas en `decisions.md` PI-2
- [ ] Verificar dev DB post-apply: `legacy_content_rows = 0`

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Codec v1→v2 falla en fila corrupta | Script: try/except per row + reporta IDs problemáticos sin abortar batch |
| Migración corre en prod sin backup | Confirmar backup automatizado activo. Dry-run antes apply |
| Performance: tabla con millones de rows + batch chico = horas | Batch size configurable. Apply en off-hours si row count grande |
| Lock contention con writes activos | Update por batch + small batch size (default 100) |
| Forward-compat reader codec v1 sigue ejecutándose post-migration sin warning | Codec v1 path agrega `structlog.warning` "legacy v1 read post-migration" para detectar regresiones |
