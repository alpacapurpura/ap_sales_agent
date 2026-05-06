# Learnings — S1-copilot-maintenance-batch

> Append durante sprint, congela al cerrar. Lecciones técnicas + de proceso para próximo sprint y `process/process-learnings.md`.

## Cierre 2026-04-29

### Técnicas

1. **Reuse `core/rate_limit.py` antes de crear `shared/rate_limit/` nuevo** — el helper Redis sliding-window ya existía + in-use por `copilot/api/chat.py`. Architect detectó duplicación propuesta y decidió extender. Lección: arquitectos siempre `Explore` antes proponer módulo nuevo (preserva DRY + ratchets).
2. **Forward-compat ship subscriber sin producer es patrón válido** — `SuggestionAccepted` event class + subscriber listos en PR-2 sin producer (FE futuro). Patrón ya validado con `EVENT_CARD_EMITTED`. Habilita métricas desde día 1 cuando FE land.
3. **Patrón Nicolify data migrations**: marker migration + script externo (NO Python-in-alembic). 3 ejemplos confirmados:
   - `backfill_brand_summaries.py`
   - `backfill_offer_preset_id.py`
   - `backfill_copilot_content_to_blocks.py` (PR-3)
   - Beneficios: deploy <30s, re-run flexible per-tenant, audit table separada, sin Python invocation en alembic upgrade.
4. **Optimistic lock + idempotencia** para data migrations a escala: `WHERE messages = :original` rowcount=0 → re-run picks up. Sin `FOR UPDATE SKIP LOCKED` (no worker pool). Idempotencia estricta = re-run = 0 cambios.
5. **Triple safety CLI** para scripts de migración prod: dry-run default + `--apply` explícito + `--confirm-prod` regex `prod\.` interceptor + `--max-failure-rate 0.05`. A escala miles tenants, "oops apply" = catastrófico.
6. **Codec v1 warning sampled 1/100** evita log flood en read hot-path. Counter per-process, ops grep total. Threshold ops día 30+ con 0 warnings → safe drop legacy reader.
7. **Architect-empowered (no open questions)** acelera flujo cuando PM pre-empodera con criterio claro ("build-right-once para 1000+ tenants"). 8 decisiones técnicas resueltas en 1 spawn architect (PR-3).

### De proceso

8. **Auto-loop builder→auditor truncó 3/3 PRs S1** (token cap consistente). PM main thread completó manualmente cada vez. **Lección crítica**: para PRs L+ con muchos archivos, considerar:
   - Split builder en 2 sub-agents (implement + verify-and-commit)
   - Pre-cocido más compacto (menos lectura obligatoria, más delegación a Read on-demand)
   - Aceptar que main thread completa quality gates (más eficiente que re-spawn parcial)
9. **Regla M8 (extend no destroy ajenos)** probada con sesión paralela PI-1. Mejor que regla M7 estricta (paths-only): permite tocar archivos ajenos si entendés + extend, sin parar work. Probabilidad colisión real baja porque módulos distintos.
10. **Filosofía Chris paralelas relajada** funciona mejor que estricta — `campaigns/domain/repositories.py` arch fail (sesión PI-1 sub-G) NO bloqueó PR-3 (deselect + reportar). Sesión PI-1 lo arregla en su tiempo, PR-3 sigue.
11. **Doble PR-1 en PIs distintos confunde paths a builder agents** — early en S1 builder PR-1 PI-2 commiteó accidentalmente sobre PR-1 PI-1 (5 commits ajenos). Mitigación: prompts builder con prefijo PI completo + restricción path-explicit.
12. **Q1 drift expansion vs additive trade-off** — PM Chris dijo "expansion delete static", builder hizo híbrido pragmático (engine + brand_hints fallback). Aceptado como deuda S2+. Lección: decisiones architect "build-right-once" no siempre traducen a "delete legacy ahora" si tests goldens dependientes.

### De producto

13. **Tres áreas estables post-S1**: tenant rate limiting infrastructure + suggestions engine motor + data migration patterns. Base para PI-2 S2+ (FE swap) o cierre PI-2 si discovery Bloque C no priorizado.
14. **Cap upper 100 MiB media** = industry standard microempresarios. Editable post planes per-tenant. Cuando llegue PI tier-pricing, otro PR sube cap sin refactor.
15. **Default voice 6 RPM** cost-based ($0.036/min cap Whisper) = balance económico vs UX. Per-tenant override admin Streamlit ya disponible si tenant Pro paga más.

## Para process/process-learnings.md (escalable a global)

- **L-PROC-1**: Auto-loop builder→auditor truncate token cap en PRs L+. Considerar split sub-agents.
- **L-PROC-2**: Architect-empowered (no open questions) acelera con criterio PM claro.
- **L-PROC-3**: Regla M8 (extend no destroy) > M7 (paths-only restricción).
- **L-PROC-4**: Patrón data migrations Nicolify codificar en `references/data-migrations.md`.
- **L-PROC-5**: Doble PR-{n} cross-PI requiere prefijo PI explícito en builder prompts.
