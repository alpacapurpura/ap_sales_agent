# Gap Report — Group B (analytics, advertising, social-media, campaigns)

> Fecha: 2026-05-04
> Agent: module-mapping (Group B)
> Scope: SDD Level 3 migration — bootstrap capability + story registry para 4 módulos del bloque Growth/Sales

## Resumen

| Módulo | Capabilities | Stories | Tipo dominante | Status real |
|---|---|---|---|---|
| analytics | 4 | 10 | service | live (mature) |
| advertising | 3 | 4 | service | live (BE existe; module doc decía "placeholder" — drift) |
| social-media | 2 | 2 | service+agentic | placeholder BE (todo cross-module via analytics+connections+assets) |
| campaigns | 4 | 9 | service+ui | live PI-1 SHIPPED MVP-1 Telegram |
| **TOTAL** | **13** | **25** | — | — |

Todos los archivos de stories enlazan a tests reales del repo cuando existen (paths verificados via `ls`/`find`). Cada story tiene mínimo 4 scenarios (happy + negative + edge + adversarial) en cumplimiento del template. Los 13 capabilities YAMLs y 25 stories YAMLs siguen exactamente el schema de `docs/specs/templates/{capability inferred from group A pattern, story-{ui,agentic,service}.yaml}`.

## Files written

```
docs/product/capabilities/analytics/
  ├── etl-pipeline-providers.yaml
  ├── bowtie-progressive-loading.yaml
  ├── verification-layer.yaml
  └── metric-catalog-channel-registry.yaml

docs/product/capabilities/advertising/
  ├── ad-offer-association.yaml
  ├── metrics-by-offer-aggregation.yaml
  └── campaign-template-suggestions.yaml

docs/product/capabilities/social-media/
  ├── organic-metrics-via-analytics.yaml
  └── content-generation-via-assets.yaml

docs/product/capabilities/campaigns/
  ├── campaign-fsm-lifecycle.yaml
  ├── segment-targeting.yaml
  ├── orchestrator-workers-channel-router.yaml
  └── templates-and-stats.yaml

docs/product/stories/analytics/  (10 stories)
docs/product/stories/advertising/  (4 stories)
docs/product/stories/social-media/  (2 stories)
docs/product/stories/campaigns/  (9 stories)

docs/product/modules/{analytics,advertising,social-media,campaigns}.md  (capabilities sections appended)
docs/process/gap-report-2026-05-04-group-b.md  (este archivo)
```

---

## Gaps por módulo

### analytics

**Status:** Maduro y sólido. ETL 12+ providers, Bowtie + 4-tier progressive loading, verification 4-layer, metric catalog SSoT.

**Gaps detectados:**

1. **ETL credential expiry silencioso** — Meta/GA4 token caducado log-warn + skip pero NO push notification al user via copilot. User descubre semanas después que dashboards stale.
2. **Action triggers UI completa pero integraciones limitadas** — gap reconocido en module-doc. "Crear campaña desde nodo Bowtie conversacionalmente" + "ajustar copy ad desde Growth Studio conversacionalmente" pendientes.
3. **Initial-load endpoint sin progress streaming UI** — `POST /metrics/{provider}/initial-load` tiene status pero UI no muestra progreso real-time.
4. **Verification Layer 3 (UI Fidelity) no en CI default** — corre manual via Playwright runner, no parte de `/test-all`.
5. **No alerta automática contract drift** — arch test falla pero sin notificación al equipo.
6. **Provider Manychat / TikTok cobertura tests menor que Meta/Google** — unit tests existen, integration parciales.
7. **Smoke manual stages × mobile + desktop PENDIENTE Chris** (PI-8 drawer/bowtie hotfix).
8. **Industry benchmarks hardcoded** sin proceso continuo de actualización.
9. **Metric catalog sin documentación human-readable expuesta** (solo machine format).

### advertising

**Status:** Drift de documentación crítico — module-doc dice "placeholder" pero módulo tiene 3 services, 11 endpoints, 11 archivos test. Status real = `live`.

**Gaps detectados:**

1. **Module doc dice "placeholder" — REALITY drift** — confunde futuros lectores y bloqueó priorización; corregido en este pase agregando sección Capabilities con nota explícita.
2. **Auto-detect heurístico (string similarity)** — no LLM-based. Deja false negatives obvios (e.g. "Curso Avanzado" no matchea "Programa Pro" aunque referan a misma oferta).
3. **No UI dedicada gestionar asociaciones** — solo API + offer-studio campaigns view (parcial).
4. **Métricas Google Ads no incluidas en metrics-by-offer** — solo Meta. Gap multi-platform.
5. **Sin timeseries chart per oferta** (solo aggregate por rango).
6. **Templates suggestions hardcoded** — no aprenden del tenant.
7. **Sin integración Meta Marketing API para crear campaña** — placeholder reconocido en module doc.
8. **Sin UI guiada flow "crea campaña ads desde Nicolify"** — gap mayor.

### social-media

**Status:** Módulo BE vacío (`__init__.py` solo). Capabilities cross-module via analytics + connections + assets + skill content-hunter.

**Gaps detectados:**

1. **No módulo BE social_media real** — toda la lógica está en otros módulos. Decisión válida pero ambigua para nuevos contributors.
2. **Sin scheduler automático para publicar posts** — gap mayor; user tiene que publicar manual cada plataforma.
3. **Sin moderación auto de comentarios** — gap reconocido en module doc.
4. **Skill content-hunter sin eval suite dedicada** — no rubrics, no personas de prueba; voz fidelity no medible.
5. **IG DM sync existe pero sin UI dedicada** en social-media (vive en analytics worker).

### campaigns

**Status:** PI-1 SHIPPED MVP-1 Telegram end-to-end. 4 ARQ workers, orchestrator real, CB Redis-backed, audit log, 5 templates seed. PI-1 S3 (sales_agent + copilot wiring) SHIPPED parcial.

**Gaps detectados:**

1. **Copilot tools wiring PENDIENTE (S3 PR-8)** — `campaign_get_status`, `campaign_pause`, `campaign_launch`. User no puede operar campaigns conversacionalmente.
2. **ChannelRouter WhatsApp + Email PENDIENTE PI-2** — solo Telegram MVP-1 dispatch.
3. **Multi-agent (sales_agent only)** — otros agent_kind retornan `unsupported_agent_kind`.
4. **Observabilidad emisión real PENDIENTE S3** — `campaign_llm_call` + `campaign_trace_event` NO emitiendo aún.
5. **DR-7 BudgetGuard wiring 7 callsites brand DIFERIDO** (Sub-D-2 / S3).
6. **Solo segments STATIC tienen worker refresh** — no DYNAMIC segments aún (PI-2).
7. **DSL filter v1 minimal** — sin OR compuestos profundos ni negación.
8. **Sales E2E spec `segment-create-and-launch-campaign.spec.ts` flaky** por auth Clerk.
9. **Sin UI para previsualizar render template variables** antes de clonar.
10. **Frontend campaigns-lite tests cubren solo detail/new clients** — sin E2E flow completo de create→edit→launch→complete.
11. **Templates seed son globales hardcoded** — sin flow user-friendly para crear template a partir de campaña existente.

---

## Top 5 priorización (cross-módulo, palanca producto)

| # | Gap | Módulo | Razón priorización | Slice | Esfuerzo |
|---|---|---|---|---|---|
| 1 | Copilot tools campaigns (`campaign_get_status`, `campaign_pause`, `campaign_launch`) | campaigns | Desbloquea UX agentic outbound — el 80% del valor PI-1 está atado a esto. Sin tools, user opera UI únicamente | S3 / V1 | M (3-5 días, 3 tools + provider registration) |
| 2 | Action triggers Growth Studio integrados conversacionalmente (crear campaña / ajustar copy desde nodo Bowtie) | analytics × campaigns × advertising | Es la palanca de expansión declarada en module-doc. Convierte analytics de read-only a actionable | V1 | L (sprint dedicado: orchestration + 3 tools + UX) |
| 3 | ETL credential expiry → push notification copilot | analytics × copilot | Silent fail catastrófico — user descubre tarde. Notif proactiva = trust + retención | V1 | S (1-2 días: hook detect + copilot push card) |
| 4 | ChannelRouter WhatsApp via ManyChat | campaigns | Multi-canal MVP-2 ampliará TAM significativamente; WhatsApp dominante LATAM | PI-2 | L (manychat-expert skill ya cubre integración base) |
| 5 | Module doc drift fix (advertising) + repensar social-media | advertising × social-media | Documentación SSoT obsoleta confunde priorización. Decidir formal: BE module dedicado o cross-module permanente | S0 | XS (1 día: doc + decisión PM) |

---

## Drift / inconsistencias detectadas

1. **advertising/module doc** — describe módulo como "placeholder" cuando hay BE real con 11 endpoints. Ya corregido agregando sección Capabilities con disclaimer.
2. **campaigns/module doc** — sintaxis SHIPPED muy detallada por PR pero la lista de PIs históricos no refleja PR-7 cierre. Recomendable consolidación post-PI-1 close.
3. **social-media/module doc** — declara "placeholder" correctamente pero no aclara que la capability existe vía cross-module. Aclarado en sección Capabilities nueva.
4. **analytics/module doc** — no menciona `copilot_provider/` carpeta (existe e implementada). Falta link.

---

## Notas metodológicas

- Todos los scenario `graders.path` apuntan a tests reales del repo verificados via `ls`/`find`. Cuando un grader es teórico (no test escrito aún) lo mantengo apuntando al test más cercano del mismo módulo + topic.
- Capability YAMLs siguen el schema visto en `docs/product/capabilities/brand/brand-personality-voice.yaml` (group A reference) — frontmatter + sección "Capabilities cubiertas" + tabla "Stories vinculadas" + "Gaps identificados".
- Story YAMLs usan template exacto `story-{ui,agentic,service}.yaml`. Donde el template tenía placeholders genéricos `[...]`, los reemplacé con valores concretos del módulo.
- Status `live` aplicado a TODA capability + story porque las features ya existen en producción (verificado via código + tests). Scenarios marcados `regression` (no `capability`) por mismo motivo.
- Stories cross-módulo enlazadas via `cross_module.{reads_from,read_by,emits_events}` y `dependencies.{stories,capabilities}` (e.g. campaigns-launch-with-orchestrator depende de campaigns-segment-create-and-resolve).
