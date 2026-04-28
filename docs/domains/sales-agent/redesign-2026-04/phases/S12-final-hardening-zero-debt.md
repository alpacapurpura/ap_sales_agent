# S12 · Final hardening — zero debt

## Objetivo

Cierre formal del plan. Auditar `05-tech-debt-log.md` con criterio
binario: cada entry **FIXED** (con commit hash) o **WONT-FIX** (con razón
documentada). Cero entries `DEFERRED-*` flotantes al cierre. Resolver los
watchpoints técnicos pendientes que no cabían en S11.

## Dependencias

S11 cerrado (orchestrator decomposition completa, callback handler lift
landed, goldens estables).

## Criterios de éxito

1. ✅ Tier pricing >200k arch ratchet activo:
   `tests/architecture/test_pricing_tier_resolution_completeness.py`. Si
   un tenant supera 200k tokens y el calculator no resuelve tier, el
   test falla. Cierra watchpoint S2.
2. ✅ `typing_simulation_cpm` wireado en `OutputManager._calculate_typing_time`
   con preferencia `fmt.typing_simulation_cpm or cls.CPM_SPEED`.
   §3 fragment validado por eval loop S10 — los goldens diff post-wiring
   = 0 (si > 0, validar que el cambio empíricamente mejora UX, no
   regresión). Cierra deuda S5 FLAGGED.
3. ✅ Presidio classification documentada como WONT-FIX en
   `05-tech-debt-log.md` con razón explícita: "regex sync cubre 80%
   PII LATAM, Presidio overhead 50-200ms incompatible con hot-path
   <10ms p99 target. Reabrir si emerge tenant enterprise con
   requirement explícito en contrato firmado".
4. ✅ DeepSeek alias retire validator activo en S10 goldens (cierra S4
   watchpoint). Test que falla si los aliases retired Jul 24 son
   referenciados.
5. ✅ Kimi temp 0.6 conversion monitor activo: dashboard Streamlit
   `/sales-routing` muestra conversion rate per-tenant pre/post Kimi
   adoption. Si rate < baseline -5% → alerta.
6. ✅ Scan voseo final ejecutado en sales_agent + brand_voice
   integration paths. Cero hits inesperados (excepción: tenants con
   override per Brand Studio).
7. ✅ `05-tech-debt-log.md` audit:
   - 0 entries `DEFERRED-*` flotantes.
   - Cada entry FIXED tiene commit hash.
   - Cada entry WONT-FIX tiene razón explícita y condición de reapertura.
   - FLAGGED entries archivadas (movidas a "Resolved watchpoints" section).
8. ✅ `make arch-test` global verde. Tests sales/copilot/admin/shared/brand
   verdes.
9. ✅ Cronograma completo: README estado fase ✅ S00 → S12.
10. ✅ §3 protected surfaces verificados intactos en smoke final.
11. ✅ Skill `/salesagent-expert` creado (o actualizado si existe variante
    previa) — guía permanente de contextualización rápida para futuras
    sesiones. Detalle abajo en sección "Entregable: skill /salesagent-expert".

## Research mandate

### Queries WebSearch

1. `LiteLLM model_prices_and_context_window tier pricing input_cost_per_token_above 2026`.
2. `Postgres long-running connection conversion rate aggregate query optimization 2026`.
3. `Python regex PII LATAM compliance LGPD LFPDPPP PDPA scope limit research 2026`.

### Lectura obligatoria

- `05-tech-debt-log.md` ENTERO — leer todas las entries DEFERRED + FLAGGED.
- `learnings/S2-cost-guardrails.md` — sección tier pricing >200k watchpoint.
- `learnings/S4-chatmodelspec-tier.md` — sección Kimi clamp + DeepSeek retire.
- `learnings/S5-channel-registry.md` — sección typing_simulation_cpm.
- `src/shared/agent_observability/cost/calculator.py` — current calculator
  state (sin tier resolution).

### Hallazgos research

> COMPLETAR.

---

## Diseño

### Tier pricing arch ratchet

```python
# tests/architecture/test_pricing_tier_resolution_completeness.py

def test_calculator_resolves_tier_when_tokens_exceed_threshold() -> None:
    """Si LiteLLM JSON declara `input_cost_per_token_above_200k_tokens`
    para algún provider, el calculator debe resolverlo. Si NO resuelve →
    fallar CI."""
    from src.shared.agent_observability.cost.calculator import calculate_cost
    from src.shared.agent_observability.pricing.litellm_sync import _read_pricing_json

    snapshots_with_tier = [
        s for s in _read_pricing_json()
        if s.get("input_cost_per_token_above_200k_tokens") is not None
    ]
    if not snapshots_with_tier:
        return  # nothing to test (LiteLLM no declared tier yet)

    # Use first snapshot as fixture
    snap = snapshots_with_tier[0]
    cost_under = calculate_cost(snap, input_tokens=100_000, output_tokens=0)
    cost_over = calculate_cost(snap, input_tokens=300_000, output_tokens=0)

    expected_unit_under = Decimal(snap["input_cost_per_token"])
    expected_unit_over = Decimal(snap["input_cost_per_token_above_200k_tokens"])

    assert cost_under == expected_unit_under * 100_000
    assert cost_over == (
        expected_unit_under * 200_000
        + expected_unit_over * 100_000
    )
```

Si el calculator no implementa tier resolution, el test falla. Forzar
implementation.

### Kimi conversion monitor

Streamlit page `/sales-routing` (planned S4 deferred a S12 si no se hizo
antes) lee `sales_agent_routing_log` + `crm.LeadModel.lead_score_history`
para computar conversion rate per (tenant, model_responded). Si Kimi
K2.6 muestra drop > 5% vs baseline OpenAI gpt-4o → alerta visible en UI.

### Voseo scan final

```bash
cd backend && grep -rEn '\b(vos|sos|tenés|querés|podés|sabés|hacés|venís|decís|mirá|dejá|poné|configurá|elegí|seleccioná|arrancá|empezá|agregá|escribí|guardá|subí|bajá|abrí|volvé|andá|cambiá|ofrecés|cobrás|integrás|listá|probá|mostrá|compartí|contá|explicá|fijate|acordate|dale)\b' \
  src/modules/sales_agent/ \
  src/shared/agent_observability/ \
  --include="*.py" --include="*.j2" --include="*.md"
```

Hits inesperados (no tenant override) → fix.

### Tech debt log audit

Procedimiento al cierre:

```bash
grep -E "^- Acción: DEFERRED-" docs/domains/sales-agent/redesign-2026-04/05-tech-debt-log.md
```

Si retorna líneas → S12 NO cerrada. Cada DEFERRED debe migrar a FIXED o
WONT-FIX antes del commit final.

## Plan TDD

1. RED: arch test tier pricing (sin implementation tier resolution).
2. Implementar tier resolution en `calculate_cost`.
3. RED: test typing_cpm wiring contra `OutputManager._calculate_typing_time`.
4. Wire `typing_simulation_cpm`. Goldens eval loop diff = 0.
5. Re-classify Presidio en tech-debt-log como WONT-FIX.
6. Cierre S10 watchpoints (DeepSeek alias + Kimi conv monitor) — si no
   se hicieron en S10, hacer ahora.
7. Voseo scan + fix hits.
8. Audit final tech-debt-log.

## Implementación step-by-step

1. Audit `05-tech-debt-log.md` lista entries `DEFERRED-*`. Para cada:
   - clasificar como S6.5/S7/S8/S9/S10/S11/S12 — verificar que la fase
     ya cerró y la entry tiene FIXED;
   - si la fase no la cerró → identificar gap y resolver acá;
   - si externa/operacional → WONT-FIX con razón.
2. Implementar tier pricing arch ratchet + tier resolution en calculator.
3. Wire typing_simulation_cpm.
4. Cerrar DeepSeek alias validator si no fue en S10.
5. Cerrar Kimi conv monitor si no fue en S10.
6. Voseo scan + fix.
7. Audit final.
8. Quality gates verdes.
9. Update README estado: `S12 ✅ DONE — plan cerrado, cero deuda`.
10. Commit final: `feat(sales-agent-redesign-s12): final hardening — plan close-out, zero floating debt`.

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Tier pricing implementation rompe calculator existing | Tests baseline pre-refactor + diff = 0 en cost computations sin tier hits. |
| typing_cpm wiring genera UX regression (canales con typing simulation diferente del esperado) | Goldens eval loop S10 + smoke manual per canal antes de merge. |
| Audit final detecta entry DEFERRED no cerrable acá | Re-clasificar la entry — el plan NO cierra hasta que cero DEFERRED. Si emerge bloqueante real, reabrir fase específica. |
| WONT-FIX mal documentado (futuro reader no entiende por qué) | Cada WONT-FIX debe incluir: razón técnica, qué condición re-abriría el ítem, link a learnings/research que fundamentan. |

## Tech debt closure

S12 cierra TODOS los entries que el plan dejó abiertos:

- `[MEDIUM] LiteLLM tier pricing > 200k tokens` (S2) — FIXED via arch ratchet + calculator.
- `[LOW] typing_simulation_cpm declarado pero no consumido` (S5) — FIXED via wiring.
- `[MEDIUM] PII async post-write worker (Presidio + spaCy NER)` (S2) — WONT-FIX.
- `[MEDIUM] DeepSeek alias retire deadline 2026-07-24` (S4) — FIXED via S10 validator.
- `[LOW] Closer temperature 0.4 clamped a 0.6 por Kimi K2.6` (S4) — FIXED via S10 monitor.

Y el meta-objetivo: `[CRITICAL] Plan deja deuda flotante` — FIXED.

---

## Entregable: skill `/salesagent-expert`

Skill **permanente** que sirve como contextualización rápida para
cualquier sesión Claude futura cuando se pida un cambio, feature o bug
fix sobre `sales_agent`. Equivale a "llamar al senior dev + arquitecto +
CTO que crearon el módulo".

### Por qué

Sin el skill, futuras sesiones recaen en:
- Parches que contaminan código (band-aids para síntomas, no root cause).
- Duplicación porque el dev ignora SSoT establecidas (LLM_ROLE_BY_SITE,
  channel registry shared, BaseAgentCallbackHandler, prompt fragments,
  pricing snapshot).
- Patterns no actualizados (e.g., introducir hardcoded model strings tras
  S4, hardcoded channels tras S5, `@trace_node` legacy tras S6.5).
- Romper §3 protected surfaces sin advertir.

El skill cierra ese gap. Permanente porque las decisiones de diseño no
cambian; el código sí.

### Principio rector — qué carga, qué NO carga

**SÍ carga** (decisiones permanentes, filosofía, anti-patterns):

- §3 protected list textual + razón por cada surface ("por qué no se
  toca").
- Principios senior del plan: TDD obligatorio, anti-parche, alta
  cohesión, bajo acoplamiento, ratchet pattern (lock-not-goal),
  Stranger Fig, Template Method, best-effort observability,
  tenant isolation, PII safety, response_model mandatory.
- Anti-patterns específicos sales_agent (lista cerrada):
  - NO migrar StateGraph a deepagents.
  - NO eliminar Closer Studio + WS + buffer + OutputManager + follow_up.
  - NO subagents deepagents.
  - NO hardcodear model wire names en specialists.
  - NO hardcodear canales literal en OutputManager.
  - NO importar copilot/ desde sales_agent ni viceversa.
  - NO tocar PromptVersionModel (DB-backed override per tenant).
  - NO `from __future__ import annotations` en LangGraph-introspected files.
  - NO bypass sanitize_payload en writes a `*_trace_event` o `*_llm_call`.
  - NO duplicar `BaseAgentCallbackHandler` plumbing — overrides solo.
  - NO bypass `LLM_ROLE_BY_SITE` SSoT (specialists + summary + nudge + safety).
  - NO bypass channel registry shared — siempre `get_channel_format`.
  - NO crear feature branches/worktrees salvo instrucción explícita.
- Decisiones cross-fase no obvias + razón:
  - Por qué `BaseAgentCallbackHandler` es Template Method (no mixin, no
    composición pura).
  - Por qué `compose_system_prompt` con CACHE_BOUNDARY_MARKER en lugar de
    Jinja monolítico (cache hit rate ≥60%).
  - Por qué `model_pricing_snapshot` cross-agent en shared (reference data
    global, no PII).
  - Por qué dual-write 4 semanas pre-cutover legacy.
  - Por qué `LLM_ROLE_BY_SITE` superset + `SPECIALIST_TO_ROLE` sub-view
    back-compat.
  - Por qué tenant isolation en CADA query (incluido `get_by_id`).
  - Por qué redirect_slashes=False en FastAPI app (Next.js proxy strips
    body en 307).
  - Por qué `from __future__ import annotations` rompe LangGraph runtime
    introspection.
- Cómo investigar antes de codear (orden estricto):
  1. Leer trazas (`copilot_trace_event` / `sales_agent_trace_event`).
  2. Leer plan + audit + tech-debt-log + learnings.
  3. Leer code de surface afectada con `grep` AST, no inventar.
  4. Si ambiguo → preguntar al usuario antes de tocar.
- Glossary cerrado: turn, span, parent_span_id, callback handler,
  pricing snapshot, LLM_ROLE_BY_SITE, ChatModelSpec, channel registry,
  specialist, lighthouse, dual-write, ratchet, Stranger Fig, §3.
- Pointers permanentes (paths estables a docs):
  - `CLAUDE.md` raíz.
  - `docs/domains/sales-agent/redesign-2026-04/README.md`.
  - `docs/domains/sales-agent/redesign-2026-04/00-vision-and-objectives.md` §3.
  - `docs/domains/sales-agent/redesign-2026-04/02-architecture-target.md`.
  - `docs/domains/sales-agent/redesign-2026-04/04-principles.md`.
  - `docs/domains/sales-agent/redesign-2026-04/05-tech-debt-log.md`.
  - `.claude/rules/copilot-resilience.md` (debug via trazas — patrón base).
  - `.claude/rules/copilot-observability.md` (cost/pricing/PII).
  - `.claude/rules/parallel-safety.md` (commits paralelos).
- Checklist pre-commit estilo "senior dev pass":
  1. ¿Toca §3? Si sí → escalé al usuario.
  2. ¿Hay test reproductor antes del fix? RED → GREEN.
  3. ¿Pasa por SSoT (channels / models / pricing / LLM_ROLE)?
  4. ¿Sanitize_payload en cada write a observability tables?
  5. ¿tenant_id filter en cada query?
  6. ¿response_model= en endpoint nuevo?
  7. ¿Spanish neutro LATAM en user-facing copy?
  8. ¿Stage por nombre en commit (no `git add -A`)?
  9. ¿Arch tests pasan native?
  10. ¿Tech-debt-log actualizado si emerge deuda?

**NO carga** (información volátil del código):

- Lista de archivos / paths específicos que pueden cambiar (`chat.py`
  podría reorganizarse).
- Counts / LOC actuales (cambian con cada commit).
- Lista de tests específicos por nombre.
- Allowlists de los ratchets (viven en los arch tests, mutan).
- Schemas Pydantic exactos (mutan por feature).
- Listado de tools específicos (S8/S9 agregan más).
- Modelos LLM concretos en uso (env var resuelve runtime).

Si el dev necesita esa info → la lee del código vivo (grep, AST, README
del módulo). El skill apunta DÓNDE buscar, no QUÉ encontrará.

### Estructura del skill

Ubicación: `.claude/skills/salesagent-expert/SKILL.md` (formato estándar
del repo — ver skills existentes como `copilot-expert`, `offer-expert`,
`brand-expert`).

Frontmatter mínimo:

```yaml
---
name: salesagent-expert
description: Senior dev + arquitecto + CTO del módulo sales_agent.
  Carga principios permanentes, §3 protected surfaces, anti-patterns,
  decisiones cross-fase no obvias y checklist pre-commit. NO carga code
  vivo (paths/LOC/tests específicos cambian). Use cuando user pida
  cambio/feature/bug en sales_agent y necesites contextualización
  rápida. Trigger: "modifica sales_agent", "bug en sales_agent",
  "agregar tool al agente", "nueva integración sales", "cómo cierra el
  agente", "debug del closer", "agregar canal sales", "modificar
  prompt del specialist", etc.
---
```

Secciones del cuerpo (en este orden):

1. **§3 — Lo que NO se toca** (lista textual + razón por surface).
2. **Antes de codear** (orden estricto investigación).
3. **Anti-patterns** (lista cerrada con razón cada uno).
4. **Decisiones cross-fase no obvias** (con razón).
5. **SSoT vivos del módulo** (qué + dónde mirar, sin paths exactos).
6. **Checklist pre-commit "senior dev pass"** (10 puntos).
7. **Glossary** (términos clave del redesign).
8. **Pointers permanentes** (docs estables, no source files).

### Procedimiento de creación en S12

1. Verificar si `.claude/skills/sales-agent-expert/` existe (con guión
   intermedio — el catálogo del repo lo lista). Si existe → leer
   contenido + decidir merge vs replace. El nuevo skill `salesagent-expert`
   (sin guión) puede convivir o reemplazar.
2. Si convive: nombrar el nuevo `salesagent-expert` (sin guión) como
   "redesign-aware" — agrega principios del plan 2026-04 + §3 + tech
   debt history sin modificar el viejo. Decidir según conversación con
   user si el viejo se elimina.
3. Si reemplaza: backup del viejo + sustituir.
4. Test del skill: invocar `/salesagent-expert` en una sesión nueva +
   pedir un fix ficticio. El skill debe responder con razón antes que
   código, citar §3, listar SSoT relevantes, NO inventar paths.
5. Commit con scope `chore(sales-agent-redesign-s12): skill /salesagent-expert`.

### Criterios de aceptación

- Skill SKILL.md ≤ 8000 chars (Anthropic skill recommended size).
- 0 paths absolutos a archivos que cambian (chat.py, etc).
- 0 listas de tests por nombre.
- 100% de §3 surfaces listadas.
- 100% de anti-patterns identificados en learnings/S0..S11 incluidos.
- Test manual: invocar el skill + pedir cambio ficticio que rompería
  §3 o duplicaría SSoT — el skill responde con escalation o redirección
  al SSoT existente, no con code.

### Mantenimiento futuro del skill

- **Cuándo updatear**: solo cuando una nueva fase/decision agrega un
  anti-pattern o §3 surface o SSoT permanente. Cambios en code (paths,
  LOC, tests) NO requieren update del skill.
- **Quién updatea**: cualquier fase que cierre con un nuevo invariante
  agrega 1 línea al skill durante su Paso 11 code review.
- **Audit semestral**: re-leer el skill cada 6 meses + cazar entries
  obsoletos (deudas que ya cerraron, anti-patterns superados por nueva
  arquitectura). Eliminar — el skill sólo crece si la arquitectura crece.
