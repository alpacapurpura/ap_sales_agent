# Billing Tiers + Cost Model — Plan Architecture

> Fecha: 2026-04-29 · Owner: /pm · Inputs: Chris (5 planes + reservación 50% sales_agent) + audit observability actual.

## Pedido Chris

5 planes con tope mensual de gasto LLM:

| Plan | Tope mensual LLM total |
|---|---|
| Free | $5 |
| Básico | $15 |
| Intermedio | $30 |
| Avanzado | $45 |
| Ultra | $95 |

**Invariante crítico:** mitad del tope (50%) **reservado para sales_agent**. Copilot u otros agentes NO pueden consumir el budget de sales_agent. Razón: "las ventas no deben parar".

Actualizable a nivel cuota de forma sencilla → tabla DB, no enum hardcoded.

## Cost model real Nicolify

Datos de `shared/agent_observability/cost/` + observación operacional:

| Agente | LLM | Costo input/M tokens | Costo output/M tokens | Costo típico/operación |
|---|---|---|---|---|
| sales_agent (specialist Kimi/DeepSeek) | Kimi K2.6 | $0.40 (cache: $0.10) | $2.00 | **~$0.001/mensaje** |
| sales_agent (closer Claude Sonnet) | Sonnet 4.6 | $3 (cache: $0.30) | $15 | ~$0.02/mensaje (raro) |
| copilot (orchestrator + cards) | Sonnet 4.6 | $3 | $15 | **~$0.05-0.20/turn** |
| copilot (subagent doc extraction) | Sonnet 4.6 | $3 | $15 | ~$0.30/extract |
| campaigns (orchestrator service) | n/a | n/a | n/a | $0 (no LLM, solo workers) |

**Variancia importante:** copilot turn con doc extraction = 60x más caro que un mensaje sales_agent base. Por eso reservación 50% sales_agent es defensiva.

## Quotas derivadas (estimado conservador)

50% reservado a sales_agent. 50% al pool restante (copilot + futuros agentes).

| Plan | Total | SA pool | Otros pool | SA mensajes/mes (~$0.001 c/u) | Copilot turns/mes (~$0.10 c/u promedio) |
|---|---|---|---|---|---|
| Free | $5 | $2.50 | $2.50 | ~2,500 | ~25 |
| Básico | $15 | $7.50 | $7.50 | ~7,500 | ~75 |
| Intermedio | $30 | $15 | $15 | ~15,000 | ~150 |
| Avanzado | $45 | $22.50 | $22.50 | ~22,500 | ~225 |
| Ultra | $95 | $47.50 | $47.50 | ~47,500 | ~475 |

**Notas:**
- SA mensajes son holgados (Kimi barato) — el cap real será probablemente `max_outbound_msg_per_day` (rate limit antispam), no budget.
- Copilot turns son el cuello — 25/mes en Free = ~1/día. Forzaría upgrade.
- Variancia copilot (extraction tools) puede consumir 5-10x más → soft alert 80% importante.

## Architecture proposal

### Tablas (todas en `backend/src/shared/billing/`)

```sql
-- Catálogo de planes (5 rows iniciales, editable sin migration)
CREATE TABLE plan_config (
  plan_id VARCHAR(32) PRIMARY KEY,           -- 'free' | 'basic' | 'intermediate' | 'advanced' | 'ultra'
  display_name VARCHAR(64) NOT NULL,
  llm_budget_total_usd NUMERIC(10,2) NOT NULL,        -- 5, 15, 30, 45, 95
  sales_agent_reserved_pct NUMERIC(4,3) DEFAULT 0.50, -- 50% default, overridable
  max_outbound_msg_per_day INT,                       -- NULL = unlimited (subject to budget)
  max_campaigns_active INT,
  max_segment_size INT,
  max_contacts_total INT,
  features JSONB DEFAULT '{}',                        -- {"event_campaigns": true, "retargeting": false}
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 1:1 tenant ↔ plan
CREATE TABLE tenant_subscription (
  tenant_id UUID PRIMARY KEY REFERENCES tenants(id),
  plan_id VARCHAR(32) NOT NULL REFERENCES plan_config(plan_id),
  cycle_anchor_day INT DEFAULT 1,         -- día del mes que inicia ciclo
  custom_overrides JSONB DEFAULT '{}',    -- {"llm_budget_total_usd": 50} para casos especiales
  trial_ends_at TIMESTAMPTZ,              -- NULL = no trial
  activated_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### `BudgetGuard` service (en `shared/billing/budget_guard.py`)

```python
class BudgetGuard:
    """
    Gate proactivo antes de invocar LLM.
    Reusa `mv_daily_llm_cost_per_tenant_v2` (ya existe en shared/agent_observability).
    """

    def check(self, tenant_id: UUID, agent_kind: str, estimated_cost_usd: Decimal) -> BudgetDecision:
        plan = self._get_effective_plan(tenant_id)  # plan_config + custom_overrides merged
        spent_by_agent = self._read_cycle_spend(tenant_id)  # MV query
        
        sa_budget = plan.llm_budget_total_usd * plan.sales_agent_reserved_pct
        other_budget = plan.llm_budget_total_usd - sa_budget
        
        if agent_kind == "sales_agent":
            spent = spent_by_agent.get("sales_agent", 0)
            allowed = sa_budget
        else:
            spent = sum(v for k, v in spent_by_agent.items() if k != "sales_agent")
            allowed = other_budget
        
        new_total = spent + estimated_cost_usd
        if new_total >= allowed:
            return BudgetDecision(allowed=False, reason="cycle_budget_exhausted",
                                   pool=agent_kind, spent=spent, cap=allowed)
        if new_total >= allowed * 0.80:
            return BudgetDecision(allowed=True, soft_warn=True, pool=agent_kind,
                                   spent=spent, cap=allowed)
        return BudgetDecision(allowed=True)
```

### Reservación invariant (crítico)

| Escenario | sales_agent llamada | copilot llamada |
|---|---|---|
| sales_agent pool 50%, otros pool 0% restante | ✅ allowed | ❌ blocked |
| sales_agent pool 0% restante, otros pool 50% restante | ❌ blocked | ✅ allowed |

**Copilot exhausto NO consume budget de sales_agent.** Test arch enforcement.

### Rate limiter (separado de BudgetGuard, complementario)

```python
class OutboundRateLimiter:
    """
    Sliding window Redis. Antispam.
    """
    def check(self, tenant_id: UUID) -> bool:
        plan = self._get_effective_plan(tenant_id)
        if plan.max_outbound_msg_per_day is None:
            return True  # unlimited subject to budget
        sent_today = self._redis_count(tenant_id, "outbound_msg", window=24*3600)
        return sent_today < plan.max_outbound_msg_per_day
```

Hoy y mañana el cap operacional será el rate limiter (no el budget — Kimi barato). Cuando user use Sonnet en campaigns el budget patea primero.

## Updates UX/admin

- Streamlit admin `/planes-billing` page: tabla `plan_config` editable + lista tenants por plan + spend actual del ciclo.
- Cambiar cuota Ultra de $95 → $120: 1 UPDATE row, 0 migrations.
- Override per-tenant: edit `tenant_subscription.custom_overrides`.

## Anti-patterns prohibidos

- ❌ Hardcodear precios en código (existing `copilot-observability.md` rule lo prohíbe — extender a campaigns/sales_agent)
- ❌ Compartir budget cross-tenant (cada tenant tiene su pool)
- ❌ Cargar spend agregado en cada call sin caché (MV ya pre-agrega; refresh hourly)
- ❌ Permitir copilot consumir SA pool aunque "esté disponible" (rompe invariante)

## Decisiones derivadas

- **D13 (decisions.md):** 5 planes con tope LLM total $5/$15/$30/$45/$95. Tabla `plan_config` editable.
- **D14:** Reservación 50% para sales_agent. `BudgetGuard` enforce. Copilot exhausto NO consume SA pool.
- **D15:** Rate limiter complementario a BudgetGuard. `max_outbound_msg_per_day` per plan_config.

## Próximos pasos

1. PR-1 (Sprint 0.3): tablas + BudgetGuard + RateLimiter + Streamlit admin page (paralelo a S0.1 outbox + S0.2 idempotency).
2. Wire copilot orchestrator para llamar `BudgetGuard.check` antes de LLM call (refactor leve).
3. Wire sales_agent specialists igual.
4. Cards en copilot: "85% del budget consumido este ciclo" (ya hay alert en observability).

## Cost model — supuestos a validar

- Costo/mensaje sales_agent ($0.001) basado en Kimi tier 200k input. Si cambia provider → recompute.
- Costo/turn copilot ($0.10 promedio) basado en Sonnet 4.6 con prompt cache hit ratio ~70%. Si cae cache → 2x cost.
- Variancia extraction tools → 0.30 por extract. Si user hace 10/día → consume Free pool en 1 día.

Validar con queries reales contra `copilot_llm_call` post-rebuild para refinar números antes de hardcodear en `plan_config` rows.
