# Architect kickoff — PR-2 shared-agent-observability

## BLOQUE FIJO (cacheable)

Sos `nicolify-architect` Opus. Producís `CONTRACT.md` para PR-2 shared-agent-observability.

PR-folder absoluto: `/home/chris/AISALESHT/docs/pm-nico/pis/active/PI-1.1-pi1-post-mortem/sprints/S2-shared-observability/prs/PR-2-shared-agent-observability/`

**Skills mandatory cargar Step 0:**
- `copilot-expert`
- `sales-agent-expert`
- `tessl__langgraph`
- `tessl__graceful-degradation`

**Rules vinculantes:**
- `.claude/rules/anti-duplication.md` (universal #12 CLAUDE.md)
- `.claude/rules/backend-ddd.md`
- `.claude/rules/parallel-safety.md` (PI-5 PR-2 active session — coordinate)
- `.claude/rules/copilot-observability.md`
- `.claude/rules/sales-agent-brand-voice.md`

## Step 0 GATE — Existing Systems Audit MANDATORY (anti-duplication enforcement primer test)

PR.md sección "Existing systems audit" tiene template MANDATORY. Vos producís grep output completo. NO claims sin evidence.

Para CADA subsystem (turn envelope, FX resolver factory, cost calculator, callback handler):

### Step 0.1 — Inventario shared abstractions consultar

```bash
cat /home/chris/AISALESHT/.claude/rules/anti-duplication.md | sed -n '/Inventario canónico/,/Regla shrink-only/p'
```

Identificar para cada subsystem si:
- Está LISTED en inventario (canonical shared) → EXTEND/USE-AS-IS
- NO listado pero similar pattern existe en `shared/` → posible LIFT-TO-SHARED
- NO listado y solo en 1 módulo → posible LIFT primer commit

### Step 0.2 — Grep cross-codebase obligatorio (output embedido en CONTRACT)

```bash
# Turn envelope
find /home/chris/AISALESHT/backend/src -name "turn_envelope.py" 2>/dev/null
grep -rn "class.*ObservabilityContext\|class.*Envelope" /home/chris/AISALESHT/backend/src/shared/ /home/chris/AISALESHT/backend/src/modules/ 2>/dev/null
grep -rn "async def observe_turn\|@asynccontextmanager" /home/chris/AISALESHT/backend/src/shared/agent_observability/ /home/chris/AISALESHT/backend/src/modules/copilot/observability/ 2>/dev/null

# FX resolver factory
grep -rn "FXResolver(" /home/chris/AISALESHT/backend/src/ 2>/dev/null | grep -v "class FXResolver"
grep -rn "http_client_factory" /home/chris/AISALESHT/backend/src/ 2>/dev/null | grep -v "class FXResolver"

# Callback handler
find /home/chris/AISALESHT/backend/src -name "callback_handler.py" 2>/dev/null
grep -rn "class.*CallbackHandler" /home/chris/AISALESHT/backend/src/shared/ /home/chris/AISALESHT/backend/src/modules/ 2>/dev/null

# Cost calculator + pricing
find /home/chris/AISALESHT/backend/src/shared/agent_observability -type f -name "*.py"
grep -rn "PricingResolver\|PricingSnapshotRepository" /home/chris/AISALESHT/backend/src/shared/ /home/chris/AISALESHT/backend/src/modules/ 2>/dev/null | head -10

# Tenant currency resolution
grep -rn "_resolve_tenant_currency\|TenantBillingConfigRepository" /home/chris/AISALESHT/backend/src/ 2>/dev/null | head -10
```

PEGAR salida REAL completa en CONTRACT.md sección "Existing systems audit". NO summary, NO paraphrase. Auditor Cat 13 verifica vs claims.

### Step 0.3 — Decisión EXTEND/LIFT/NEW por subsystem

| Subsystem | Existing canonical? | Decisión | Justificación path:line |
|---|---|---|---|
| Turn envelope | partial (copilot/observability/recording/turn_envelope.py + shared/agent_observability/recording/{base_callback_handler.py,sanitization.py} pero NO base envelope) | **LIFT-TO-SHARED + EXTEND** | Single source needed cross-agent. Copilot existing logic se promueve a shared base, copilot inherits + sales_agent inherits |
| FX resolver factory | shared/agent_observability/cost/fx_resolver.py existe FXResolver class CON `http_client_factory` arg requerido. Solo 1 caller (copilot/chat.py:647) lo construye correctamente. 2 callers (sales_agent/factory.py:116, 168) usan `FXResolver()` no-arg → runtime AttributeError | **EXTEND existing class** add `default()` classmethod | Encapsula `lambda: httpx.Client(timeout=10)` boilerplate. Tests override via `FXResolver(http_client_factory=mock)` directo |
| Concrete observability context per agent | NO existing pattern shared. Copilot's `turn_envelope.py::ObservabilityContext` es concrete monolithic | (después de LIFT) **NEW concrete subclass** Copilot + NEW concrete subclass SalesAgent | Justificación: cada agente tiene fields/repos específicos. Subclass solo overrides + heredan lifecycle base |

### Step 0.4 — Validar contra PI-5 PR-2 active session

PI-5 PR-2 (`docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/sprints/S2-telegram-orchestrator-memory-cache/prs/PR-2-telegram-orchestrator-hookup/`) está activa modificando `modules/copilot/`. Verificar si modifica `modules/copilot/observability/`:

```bash
git status --short backend/src/modules/copilot/observability/ 2>/dev/null
git diff HEAD~3 backend/src/modules/copilot/observability/ --stat 2>/dev/null
```

Si overlap → CONTRACT debe explicitar coordination plan: PI-5 PR-2 mergea primero, después PR-2 shared-observability lifts. Sino → architect proceeds.

## Workflow

### Phase 0 — Skills + GATE

1. Invoke skills (4 mandatory above)
2. Execute Step 0.1 + 0.2 + 0.3 + 0.4 grep output completo

### Phase 1 — CONTRACT.md production

CONTRACT.md secciones:

#### § 0 — Surface mapping
| Surface | Path | Owner builder |
|---|---|---|
| Shared base envelope | `backend/src/shared/agent_observability/recording/turn_envelope.py` | nicolify-agentic |
| Shared FX factory | `backend/src/shared/agent_observability/cost/fx_resolver.py` | nicolify-agentic |
| Copilot concrete context | `backend/src/modules/copilot/observability/recording/context.py` (NEW) + RENAME/DELETE turn_envelope.py | nicolify-agentic |
| Sales agent concrete context | `backend/src/modules/sales_agent/observability/recording/context.py` (NEW) | nicolify-agentic |
| Copilot orchestrator migration | `backend/src/modules/copilot/application/orchestrator/chat.py` | nicolify-agentic |
| Sales agent orchestrator migration | `backend/src/modules/sales_agent/application/orchestrator/{chat,outbound_orchestrator}.py` | nicolify-agentic |
| Sales agent factory migration | `backend/src/modules/sales_agent/observability/recording/factory.py` line 116, 168 | nicolify-agentic |

#### § 1 — Existing systems audit (real grep output embedded)
Pegar Step 0.2 output completo + table de decisiones EXTEND/LIFT/NEW per subsystem.

#### § 2 — BaseObservabilityContext interface (abstract base)
- Lifecycle methods: `__aenter__` → `turn_start` row commit; `__aexit__` → `turn_end` row commit; exception → `set_turn_error` row commit
- Abstract methods overridable by subclass: `_build_repos()`, `_build_callback_handler()`, `_persist_turn_end_data()`
- Shared composition: `pricing_resolver`, `fx_resolver`, `tenant_currency` instantiated by base
- Concrete fields per subclass: `tenant_id`, `lead_id` (sales) o `user_id`+`conversation_id` (copilot), `channel_type`, `turn_id`

#### § 3 — FXResolver.default() factory
```python
@classmethod
def default(cls) -> FXResolver:
    """Production default: httpx client with 10s timeout."""
    return cls(http_client_factory=lambda: httpx.Client(timeout=10))
```

#### § 4 — Migration plan (sequenced)
1. Lift turn_envelope copilot logic to shared base abstract
2. Add FXResolver.default() classmethod
3. Create copilot concrete subclass (preserve lifecycle parity — regression test)
4. Migrate copilot chat.py call sites
5. Create sales_agent concrete subclass
6. Migrate sales_agent factory.py:116, 168 (Bug #8 fix included)
7. Migrate sales_agent chat.py + outbound_orchestrator.py call sites
8. Real persistence smoke test sales_agent
9. Manual Telegram trigger Chris-mediated → verify trace count > 0

#### § 5 — Tests strategy
- Real DB persistence (no mocks): `tests/modules/sales_agent/observability/test_real_trace_persistence.py`
- Copilot regression: `tests/modules/copilot/observability/test_envelope_inheritance.py`
- Base contract: `tests/shared/agent_observability/test_turn_envelope_base.py`
- FX factory: `tests/shared/agent_observability/cost/test_fx_resolver_default.py`
- Anti-regression grep: `tests/architecture/test_no_fxresolver_no_arg.py` ensures `FXResolver()` (no-arg) banned cross-codebase

#### § 6 — Coordination con PI-5 PR-2
[Output Step 0.4 dictates] → Si overlap copilot/observability → blocker note "PI-5 PR-2 mergea primero". Si no → architect proceeds.

#### § 7 — Out of scope
- Bug #7 brand_data_adapter (separate PR backend negocio)
- Bug #9 LiteLLM container (separate PR infra)
- Bug #6 tenant switch (separate PR FE Clerk)
- Bug #5 max update depth (post-reproduce ticket)
- Backfill traces históricos (defer post-PR-2 + Chris discussion)

#### § 8 — Aceptación criteria

Lista checklist para builder verificar pre-commit + auditor verificar pre-PASS.

#### § 9 — Risks

Tabla riesgos + mitigations.

### Phase 2 — Output

1. `CONTRACT.md` en PR-folder con grep evidence + 9 secciones above
2. Reportar PM:
   - Coordination status PI-5 PR-2 (overlap detected o clean)
   - Estimated builder turns (≤150 cap agentic Opus)
   - Risk highlight si arch decision needs Chris confirmation

Última línea respuesta exacta cuando termines:
```
<!-- @pm: architect done. CONTRACT.md ready. Próximo paso: ejecutar /pm "PR-2 architect done — spawn builder" o pegar prompts/02-builder-agentic.md -->
```

## Restricciones absolutas

- NO escribís código fuera CONTRACT.md doc
- NO commit (PM commitea CONTRACT.md)
- NO --no-verify, NO git pull, NO force push
- NO claims sin grep evidence path:line
- Cap maxTurns 80 — eficiente: skills + 4 grep batches + 1 doc write

---

## BLOQUE VARIABLE (per-invocation)

PR-folder absoluto: `/home/chris/AISALESHT/docs/pm-nico/pis/active/PI-1.1-pi1-post-mortem/sprints/S2-shared-observability/prs/PR-2-shared-agent-observability/`

PR.md detalle completo: `{PR-folder}/PR.md`

Iteración: 1.

Tenant test (post-CONTRACT smoke): `6347e21e-8112-4aa1-80d3-6adaa73bf6f9` (visionarias).
Lead test reference: `cb711aea-e0a5-42c0-b276-7a63570207bd` (Christian Revilla).

Cross-session activa: PI-5 PR-2 (`docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/sprints/S2-telegram-orchestrator-memory-cache/prs/PR-2-telegram-orchestrator-hookup/`).
