# Learnings · S12 · final hardening — plan close-out, zero floating debt

> Cierre formal del plan sales-agent-redesign-2026-04. No hay S13. Esta
> nota documenta qué cerró y qué quedó como backlog general producto
> para que futuras sesiones eviten reabrir DEFERRED ya resueltos.

---

## Resumen (3 líneas)

- **Entregado**: 4 entregables FIXED + 5 entregables WONT-FIX. Tier
  pricing arch ratchet (`test_pricing_tier_resolution_completeness.py`)
  + calculator splitting en `TIER_THRESHOLD = 200_000` con resolución
  opt-in (typed attribute o `raw_payload` JSONB). `OutputManager._calculate_typing_time(text, channel_type=None)`
  consume `get_channel_format(channel_type).typing_simulation_cpm` con
  fallback `CPM_SPEED` global (§3 calibration preservada). DeepSeek alias
  retire arch ratchet (`test_deepseek_alias_not_retired.py`) bloquea
  `deepseek-chat` / `deepseek-reasoner` post 2026-07-24. Streamlit
  `/sales-routing` admin page (`src/admin/modules/sales_routing.py`)
  surface tier + specialist + cost+latency per (provider, model_responded)
  para Kimi conversion monitor. Skill `.claude/skills/sales-agent-expert/SKILL.md`
  reescrito post-redesign-aware (7655 chars, ≤8000 cap). 18 tests nuevos
  (10 calculator tier + 7 typing_cpm + 1 deepseek arch). 645 arch verde
  + 3113 modules + 95 quality/snapshot. Snapshot diff = 0 byte-equal
  preservado. Goldens diff = 0.
- **Decisión no obvia**: el watchpoint S4 "Closer temp 0.4 / Kimi 0.6
  conversion monitor" se cierra con un `/sales-routing` admin page
  **mínimo viable** (tier dist + specialist breakdown + per-model
  cost/latency) + S10 quality eval drift detection en bucket
  `closing_payment` como proxy. La especificación pedía "conversion
  rate per (tenant, model_responded) con alerta -5%", lo que requiere
  CRM joins + baseline data que no existe pre-deploy. Trade-off: cierre
  el watchpoint con building blocks suficientes; el alert vs baseline
  específico vive en backlog general producto post-volumen.
- **Listo para producción**: el plan declara DoD §1 (cero entries
  DEFERRED-* flotantes al cierre S12). Cada entry FIXED tiene commit
  hash; cada WONT-FIX tiene razón explícita + condición de reapertura.
  Las 8 entries operacionales (S+1 / S8 cleanups / S10 watchpoints
  post-volumen) viven re-clasificadas a backlog general producto, NO
  bloquean el plan. S6.5 sigue reloj-gated 2026-05-26 — independiente.

---

## Decisiones clave

- **Tier pricing resolution opt-in via `getattr` defensivo**:
  - Tomada: el calculator usa `_resolve_tier_rate(pricing, key)` que
    intenta `getattr(pricing, key, None)` + `Decimal` coercion + fallback
    a `pricing.raw_payload[key]`. Tests existentes con `MagicMock` (que
    auto-generan attrs) NO regresionan porque `MagicMock()` no es
    `Decimal | int | float | str` — `_coerce_decimal` retorna `None` y
    el path tier no se activa.
  - Razón: el plan pedía arch ratchet sin tocar el schema del
    `ModelPricingSnapshotModel`. Los tier rates viven en LiteLLM JSON
    `raw_payload` JSONB que el sync ya guarda verbatim. No hay urgencia
    de columnas tipadas: el resolver lee del raw cuando aparece, sin
    columna nueva. Cuando reconciliation muestre tier hits frecuentes,
    promover a columnas tipadas con migration.
  - Alternativa descartada: extender el `_PricingLike` Protocol con
    campos opcionales tier. Rechazada — Protocol attributes opcionales
    no son back-compat con MagicMock test fixtures (los old tests pasan
    `MagicMock()` y los attrs auto-existen como MagicMock children).

- **typing_simulation_cpm wireado con fallback explícito a `CPM_SPEED`**:
  - Tomada: `_calculate_typing_time(text, channel_type=None)` resuelve
    `cpm = get_channel_format(channel_type).typing_simulation_cpm or
    cls.CPM_SPEED` con guard `override is not None and override > 0`.
    Channel sin override (los 7 baseline) cae al global; channel con
    override > 0 lo usa; channel con override 0 / negativo cae al global
    (defensive vs registries malformados).
  - Razón: §3 protected dice "CPM_SPEED + caracter cap calibrados, no
    tocar". El wiring per-canal NO toca `CPM_SPEED`; lo extiende. Goldens
    diff = 0 verificado post-wiring (todos los baseline declaran None).
  - Alternativa descartada: hardcodear `cpm = override or CPM_SPEED`
    (pythonic short-circuit). Rechazada — `0 or CPM_SPEED = CPM_SPEED`
    funciona pero pierde la intención semántica del defensive guard
    (registry con cpm=0 NO es bug, es config inválido del operador
    que mejor cae al fallback).

- **`/sales-routing` admin page minimal viable + sin CRM join**:
  - Tomada: dashboard renderiza tier distribution + specialist breakdown
    + cost+latency per (provider, model_responded) + recent decisions.
    NO incluye conversion rate baseline alert. El plan pedía "conversion
    rate per (tenant, model_responded) si rate < baseline -5% → alerta".
  - Razón: full conversion rate requiere `crm.LeadModel.lead_score_history`
    join + baseline temporal por tenant (pre vs post Kimi adoption). Sin
    volumen real (≥5 tenants × ≥4 sem post-Kimi) el baseline es noise.
    El dashboard entrega los building blocks (per-model latency / cost /
    calls) suficientes para detectar drift visual cuando un modelo nuevo
    absorbe el tráfico. La S10 quality eval ya cubre regression
    detection vía `closing_payment` bucket drift (proxy directo al
    closer specialist con Kimi K2.6).
  - Alternativa descartada: full CRM join + baseline alert structlog.
    Rechazada — scope creep para una página sin volumen real. Documentado
    en backlog general producto: "Sample real conversations cuando
    haya volumen multi-tenant" + "Per-bucket drift threshold post-volume".

- **Skill `sales-agent-expert` replace in-place vs convive**:
  - Tomada: replace contenido de `.claude/skills/sales-agent-expert/SKILL.md`
    con versión post-redesign-aware. Mantener el nombre con guión (ya
    catalogado), mantener `references/` directorio existente
    (conversation craft pre-redesign — útil para evolución de copy).
  - Razón: el plan dejó decidir merge vs replace. El contenido viejo
    hablaba de "current → target migration" — migration cumplida en
    S0..S11, así que el viejo era obsoleto en su narrativa. Mantener
    nombre con guión evita desincronizar el catálogo del repo y los
    triggers existentes ("modifica sales_agent" / "agente no cierra"
    etc.). Mantener `references/` evita perder swipe-files útiles.
  - Alternativa descartada: crear `salesagent-expert/` (sin guión) y
    convivir 2 skills. Rechazada — duplica catálogo + risk de invocar
    el viejo.

- **Skill ≤8000 chars cap forzó trim del 20%**:
  - Tomada: primera draft = 11817 chars. Trimm a 7655 chars cortando
    Glossary (table → bullets densos), Decisiones cross-fase (chunks
    largos → bullets de 1 línea), Pointers (paths concatenados con
    coma).
  - Razón: el plan dice "≤ 8000 chars (Anthropic skill recommended size)".
    Skill que excede el cap puede no cargarse en context window de
    sesiones sin token budget extra. Trim sistemático preserve substance:
    ningún anti-pattern, ningún SSoT, ningún checklist se eliminó.

---

## Sorpresas / gotchas críticos

- **`MagicMock` test fixtures break Protocol-based attribute checks**:
  los tests legacy del calculator (`test_cost_calculator.py`) usan
  `MagicMock()` como pricing snapshot. Cuando agregás `getattr(pricing,
  "input_cost_per_token_above_200k_tokens", None)`, MagicMock NO retorna
  None — retorna un nuevo MagicMock child. La defensa correcta es
  `isinstance(value, Decimal | int | float | str)` para descartar
  MagicMock children. **Lección S+**: cualquier nueva opt-in attribute
  resolution en una función pure que existing tests llaman con
  MagicMock necesita coerción defensiva, no solo None check.

- **Ruff RUF003 flagea `×` (multiplication sign) en docstrings/comments**:
  ascii `x` o `*` solamente. Mismo para `÷` → `/`. **Lección**: cualquier
  comentario o docstring con math symbols Unicode dispara RUF003. Stick
  to ASCII en código.

- **Tests modules dir = ~3000 tests, run en ~90s nativos**: con todos
  los tests sales/copilot/admin/shared/brand juntos. CI Docker corre
  más lento (~180-220s). Para iteración local, native pytest module-
  scoped es suficiente. Solo correr full suite native antes de push.

- **Anchor registry ratchet falla mostrando exactamente cuál anchor
  nuevo**: agregar `# [SALES-AGENT-COST-TIER-S12]` en
  `calculator.py` sin agregar entry a ANCHOR_REGISTRY → arch test rojo
  con mensaje claro. Workflow: agregar el anchor + entry registry en el
  mismo commit, NO uno y después el otro.

- **Tech debt log es append-only auditable**: las DEFERRED-X labels en
  el body del log SON HISTÓRICAS. Reflejan la decisión AT THE TIME de
  detección. La SSoT del cierre es la sección "Cierre S12" + tabla de
  Reclasificación CTO. Future Claude que vea `DEFERRED-S00` en línea
  73 NO debe pánico — el contexto histórico es válido, el cierre vive
  en la sección final.

---

## Recomendaciones accionables para futuro

- [ ] **Cuando reconciliation worker detecte tier hits frecuentes**:
  promover los tier rates de `raw_payload` JSONB a columnas tipadas en
  `model_pricing_snapshot` (`input_cost_per_token_above_200k_tokens`
  + output sibling). Migration idempotente. Calculator detección
  automática (typed attribute precedence > raw_payload).

- [ ] **Cuando emerja volumen multi-tenant ≥10 tenants × ≥50 conversations/sem**:
  agregar segundo path al cron `weekly_sales_agent_quality_eval` que
  samplee conversaciones reales (con `sanitize_payload`) + bucket
  discriminator distinto en `extra_metadata` para que `/sales-agent-quality`
  distinga golden vs real. Reabre tech-debt entry "Sample real
  conversations" del log.

- [ ] **Si goldens del bucket `closing_payment` muestran drift > 5%
  post-Kimi K2.6 deploy real**: investigar si la temp clamp 0.4 → 0.6
  es la causa root o si el routing per-tenant aleja el closer del
  modelo correcto. `/sales-routing` permite ver la mezcla; la solución
  puede ser routing condicional (Kimi para descovery, OpenAI temp 0.4
  para closer en tier alto de oferta).

- [ ] **NO agregar nuevos `[SALES-AGENT-*-S12+]` anchors** al SKILL.md.
  Solo cuando una nueva fase introduzca un invariante nuevo (anti-pattern
  / §3 surface / SSoT permanente). Cambios en code (paths, LOC, tests)
  no requieren update del skill.

- [ ] **Audit semestral del skill**: cada 6 meses re-leer
  `SKILL.md` y cazar entries obsoletos (deudas que ya cerraron, anti-
  patterns superados por nueva arquitectura). Eliminar — el skill solo
  crece si la arquitectura crece. Si el skill excede 8000 chars,
  trimm igual.

---

## Hooks listos

- `src/shared/agent_observability/cost/calculator.py::TIER_THRESHOLD`
  — constant `200_000` exportado en `__all__`. Cualquier consumer puede
  consultar el threshold sin hardcodear.

- `src/shared/agent_observability/cost/calculator.py::_resolve_tier_rate`
  — pure function con coerción defensiva. Reusable si emerge tier
  pricing para cache reads/writes (`cache_read_input_token_cost_above_200k_tokens`
  ya declarado por LiteLLM en algunos modelos pero no consumido aún).

- `src/modules/sales_agent/infrastructure/external/output_manager.py::_calculate_typing_time`
  — signature `(text, channel_type=None)`. Cualquier nuevo canal con
  `typing_simulation_cpm` declared en `register_channel(...)` se aplica
  automático sin tocar OutputManager.

- `tests/architecture/test_pricing_tier_resolution_completeness.py` —
  5 arch tests sin allowlist. Si alguien strip-out tier handling,
  CI rojo claro.

- `tests/architecture/test_deepseek_alias_not_retired.py` — AST scan +
  allowlist mínimo (`pricing/aliases.py`). Para agregar excepción nueva,
  documentar razón en commit + agregar a `ALLOWLIST_RELATIVE_PATHS`.

- `src/admin/modules/sales_routing.py::render_sales_routing` — page
  reusable. Patrón para futuros agent-routing dashboards (nuevo agente
  → mirror este module + `PageSpec(slug=..., ...)`).

- `.claude/skills/sales-agent-expert/SKILL.md` — 7655 chars. Actualizar
  solo cuando una fase nueva agregue invariante permanente.

---

## Riesgos abiertos

- **Tier pricing resolution sin column typed**: hoy el resolver lee de
  `raw_payload` JSONB. Si LiteLLM cambia el shape del JSON (ej. rename
  `input_cost_per_token_above_200k_tokens` → otro key), el resolver
  silenciosamente cae a None y tier no aplica. Mitigación: el sync
  diario LiteLLM JSON → DB sigue corriendo; cualquier cambio de schema
  surge en cuestión de horas. Watchpoint: si reconciliation muestra
  drift constante >5% en alto-volumen tenant, validar que LiteLLM
  upstream sigue emitiendo el key esperado.

- **`/sales-routing` page sin volumen no muestra data**: con `sales_agent_routing_log`
  + `sales_agent_llm_call` casi vacíos pre-deploy real, el page renderiza
  los `st.info("Sin decisiones...")` placeholders. NO es bug — es
  comportamiento defensivo. Cuando el primer tenant productivo arranque,
  data se popula automatic.

- **Skill ≤8000 chars cap puede ser estricto**: si el redesign futuro
  agrega 5-10 anti-patterns nuevos o §3 surfaces nuevas, el skill puede
  exceder cap. Audit semestral cubre esto. Worst case: split en
  `SKILL.md` core + `references/` extended.

- **Anchor registry CAP=25, hoy en 18**: 7 slots libres. Si futuros
  fases agregan ≥3 anchors c/u, el cap aprieta. Bumpear con
  justificación inline cuando se llegue.

---

## Tech debt detectado (NO arreglado)

Solo lo que dejé en backlog general producto (operacional, fuera scope
del plan). Todas las entries del plan FIXED o WONT-FIX en
`05-tech-debt-log.md::Cierre S12 (2026-04-28) — auditoría final`.

- [LOW] Goldens viven en `tests/` consumidas por cron prod (S10) →
  backlog. Reabrir si `tests/` se reorganiza o cron rompe.
- [LOW] Sample real conversations cuando haya volumen multi-tenant
  (S10) → backlog. Reabrir cuando ≥10 tenants × ≥50 conversations/sem.
- [LOW] Drift threshold 5% global, no per-bucket (S10) → backlog.
- [LOW] Judge LLM sin `prompt_cache_key` (S10) → backlog.
- [LOW] Closer Studio FE meetings tab (S8) → backlog FE post-deploy.
- [MEDIUM] BookingLink model sin tenant_id column (S8) → backlog DDD.
- [LOW] AppointmentModel.summary FK suave a event_slug (S8) → backlog DDD.
- [LOW] LLM call temp hardcoded 0.5 reminder engine (S8) → backlog.

---

## Fuentes research útiles

Solo las que **cambiaron una decisión**.

- [BerriAI/litellm `model_prices_and_context_window.json` GitHub](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json)
  — confirmó `input_cost_per_token_above_200k_tokens` + output sibling
  + cache variants vigentes 2026. Cambió: tier resolution lee de
  `raw_payload` JSONB primero, columnas tipadas later.
- [LiteLLM Custom Pricing docs](https://docs.litellm.ai/docs/proxy/custom_pricing)
  — confirmó schema completo de tier pricing fields. No cambió decisión
  pero validó que el approach getattr-from-raw_payload es correcto.
- [Microsoft Presidio + spaCy Universe](https://spacy.io/universe/project/presidio)
  + [oneuptime LLMOps PII Detection 2026-01-30](https://oneuptime.com/blog/post/2026-01-30-llmops-pii-detection/view)
  — confirmaron que Presidio overhead 50-200ms es real. Cambió: WONT-FIX
  classification con razón documentada + condición de reapertura
  (enterprise contract requirement explícito).

---

## Métricas medidas

- BE quality gates nativos: `ruff check src/ tests/ --no-cache` 0 errors,
  `ruff format --check` clean.
- `pytest tests/architecture/`: **645 passed, 1 warning** (Pydantic
  deprecation, no impacto). Pre-S12: 638. Net +7 tests.
- `pytest tests/modules/sales_agent/ tests/modules/copilot/ tests/admin/
  tests/shared/ tests/modules/brand/`: **3113 passed, 3 warnings**.
- `pytest tests/quality/ tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py
  tests/shared/agent_observability/test_callback_handler_snapshot.py`:
  **95 passed**. Snapshot diff = 0 byte-equal post-S12.
- Tests nuevos S12: **18** (10 calculator tier + 7 typing_cpm + 1
  deepseek alias arch test). Plus 5 arch tests para tier ratchet (ya
  contados en architecture global).
- Files nuevos: 6 (calculator tests + tier arch test + typing_cpm tests
  + deepseek arch test + sales_routing module + sales_routing page).
- Files modificados: 7 (calculator.py + output_manager.py + format_for_channel.py
  voseo fix + sales_agent_anchors.py + admin/app.py PageSpec +
  tech-debt-log.md cierre + sales-agent-expert SKILL.md).
- LOC añadidas: ~1500 (incluye learnings + tech debt log cierre + tests
  + admin module + skill rewrite).
- Spanish neutro: 0 hits actionables post-fix de `format_for_channel.py`
  (`querés` → `quieres` en 2 docstrings). Meta-statements en
  `compose.py` mantienen `vos`/`tenés` como prohibición explícita al LLM
  (no es voseo del UI).
- Skill chars: 7655 (cap 8000). Trimm 35% del primer draft.
- §3 protected surfaces: intactos. `git diff S11B→S12` sobre
  BufferService / OutputManager.process_response / enrollment / agent_state_checkpoint
  / webhooks / follow_up_engine = 0 cambios. `OutputManager._calculate_typing_time`
  toca su signature pero el `process_response` chunking sigue idéntico
  (CPM_SPEED fallback identical para los 7 baseline channels).
