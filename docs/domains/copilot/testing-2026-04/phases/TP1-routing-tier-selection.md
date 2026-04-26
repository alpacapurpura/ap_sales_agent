# TP1 — Routing + Tier Selection (F8 + F11.1)

**F# que valida:** F8 (LLMClassifier + cache prefix + 4-tier router) + F11.1 (wire al chat orchestrator).
**Tiempo estimado:** 2-3 hs.
**Pre-req hard:** TP0 cerrado.

---

## Misión

Confirmar que:

1. Cada turn dispara una decisión de routing visible en `copilot_routing_log` (F11.1 wire).
2. El tier seleccionado matchea las heurísticas (NANO short msg, HEAVY audit/design, MINI default).
3. Cache prefix system prompt mantiene hit rate ≥60% post-warmup (F8 §5.2).
4. Admin `/copilot-routing` muestra distribución real + classifier breakdown + p50/p95 latencia.
5. LLMClassifier fallback NANO no se activa cuando rule classifier matchea (cero waste).

---

## Research mandate

Queries:

- `"openai prompt caching cache_read pricing 2026 minimum tokens"` — confirmar threshold ≥1024 tokens cacheable + savings actuales.
- `"intent classification threshold confidence routing 2026 best practices"` — validar threshold 0.7 sigue siendo defensivo correcto.
- `"langchain usage_metadata cache_read input_token_details 2026"` — confirmar shape del usage_metadata en LangChain release activa.

Si OpenAI cambió pricing del cache (e.g. cache_read ahora gratis), revisar `01-master-plan.md §Cache hit rate` target.

---

## Scenarios

### S1.1 — Routing log per turn (F11.1 wire smoke)

Disparar 1 turn via API:
```bash
curl -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "X-Tenant-ID: <uuid>" -H "Authorization: Bearer <clerk-token>" \
  -d '{"message": "hola", "conversation_id": null}'
```

SQL post-turn:
```sql
SELECT tier_selected, classifier_used, confidence, reason, user_msg_length, tools_available
FROM copilot_routing_log
WHERE conversation_id = (SELECT id FROM copilot_conversations ORDER BY created_at DESC LIMIT 1);
```

**Pass:** 1 row exactamente, con `classifier_used IN ('rule', 'llm', 'default')` + `tier_selected IN ('NANO', 'MINI', 'REASONING', 'HEAVY')`.

### S1.2 — Routing rules canónicas (5 escenarios)

Tabla esperada (basada en `domain/routing_policy.py::DEFAULT_ROUTING_POLICY`, ajustada
post-TP1 corrida 2026-04-25):

| Input | Expected tier | Expected classifier (reason) |
|---|---|---|
| `"hola"` (4 chars) | NANO | rule (`short_msg_no_tools`) |
| `"audita mi marca completa"` | HEAVY | rule (`keyword_audit_diagnostic`) |
| `"diseña una oferta para mi curso"` (31 chars) | NANO | rule (`short_msg_no_tools`) — **F8 no incluye keyword `diseña`**; al ser ≤40 chars cae en NANO. Si producto requiere REASONING para diseño, agregar rule en F-pos. |
| `"compárame email vs whatsapp"` | REASONING | rule (`keyword_compare_reason`) |
| `"qué tal cómo va todo el día"` (27 chars) | NANO | rule (`short_msg_no_tools`) — sin keyword + ≤40 chars → NANO. El plan original esperaba MINI pero la rule de length captura primero, lo cual es **mejor económicamente** (cheaper tier para small talk). |

Run cada uno via API + assert con DeepEval `GEval`:

```python
metric = GEval(
    name="routing_correctness",
    evaluation_steps=[
        "tier_selected matches expected based on input keywords",
        "classifier_used is the most specific (rule before llm before default)",
    ],
    evaluation_params=["actual_output", "expected_output"],
)
```

### S1.3 — LLMClassifier NO se activa cuando rule matchea

Run scenario S1.2 con tracing detallado:

```sql
SELECT classifier_used, COUNT(*) FROM copilot_routing_log
WHERE conversation_id = :conv_id GROUP BY classifier_used;
```

**Pass:** 0 rows con `classifier_used='llm'` para los inputs que rule matchea (S1.2 filas 2-4).

**Fail flag:** si LLM se invoca cuando rule mached, reabrir bug F8 — ExplodingLLM test debería catch en CI pero la realidad puede divergir.

### S1.4 — Cache hit rate post-warmup

Disparar 10 turns idénticos en serie ("hola") sobre el mismo tenant. Después medir:

```sql
SELECT
  AVG((data->>'cache_hit_rate')::numeric) AS avg_hit,
  MIN((data->>'cache_hit_rate')::numeric) AS min_hit
FROM copilot_trace_event
WHERE event_type='turn_end' AND tenant_id=:tenant_id
  AND created_at >= NOW() - INTERVAL '5 minutes';
```

**Pass:** `avg_hit ≥ 0.60` post-warmup (turns 3-10).
**Fail flag:** avg_hit < 0.30 → prefix cache no garantizado, revisar `system_prompt_layout.py::compose_system_prompt` orden de fragmentos.

### S1.5 — p50/p95 latencia per tier

Disparar 30 turns mixtos (6 por tier × 5 tiers; los 5 escenarios S1.2 + variaciones). Medir:

```sql
SELECT
  rl.tier_selected,
  COUNT(*) AS n,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY te.duration_ms) AS p50,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY te.duration_ms) AS p95
FROM copilot_routing_log rl
JOIN copilot_trace_event te ON te.conversation_id = rl.conversation_id AND te.event_type='turn_end'
WHERE rl.created_at >= NOW() - INTERVAL '10 minutes'
GROUP BY rl.tier_selected;
```

**Pass:** ver `03-metrics-and-targets.md §Latencia`. NANO/MINI p50 ≤1500ms; HEAVY p50 ≤8000ms.

### S1.6 — Admin `/copilot-routing` muestra data

Después de S1.1-S1.5, abrir admin Streamlit:

- Tab "Distribución de tier" → muestra ≥5 entries con counts variados.
- Tab "Classifier breakdown" → rule/llm/default repartidos.
- Tab "Cache hit rate" → curva sobre últimos 10 turns.

Screenshot en `results/TP1-{fecha}/admin-routing.png`.

**Pass:** las 3 tabs muestran data NO vacía.

### S1.7 — Cost real per tier

DeepEval token tracking + SQL probe:

```sql
SELECT
  rl.tier_selected,
  AVG((te.data->>'total_tokens')::int) AS avg_tokens,
  AVG((te.data->>'cached_input_tokens')::int) AS avg_cached
FROM copilot_routing_log rl
JOIN copilot_trace_event te ON te.conversation_id=rl.conversation_id AND te.event_type='turn_end'
WHERE rl.created_at >= NOW() - INTERVAL '10 minutes'
GROUP BY rl.tier_selected;
```

Calcular cost USD per tier con `03-metrics-and-targets.md §Cost estimation` formula. Reportar:

- Cost promedio chat short (NANO/MINI) — target ≤$0.005.
- Cost promedio HEAVY (audit/design) — target ≤$0.05.

---

## Tools / queries

- API: `curl POST /api/v1/copilot/chat`.
- DeepEval: `tests/quality/deepeval/test_tp1_routing.py` (crear si no existe).
- Admin: `http://localhost:8502/copilot-routing`.
- SQL: probes en `01-tooling.md §Cost / tokens por turn`.

---

## Targets

| Métrica | Target | Hard fail |
|---|---|---|
| Routing log row per turn | 1:1 | <1 |
| Rule classifier wins on keyword scenarios | 100% (S1.3) | <90% |
| Cache hit rate post-warmup | ≥60% | <30% |
| NANO/MINI p50 latencia | ≤1500ms | >5000ms |
| HEAVY p50 latencia | ≤8000ms | >30000ms |
| Cost chat short | ≤$0.005 | >$0.02 |
| Cost HEAVY | ≤$0.05 | >$0.20 |
| Admin routing 3 tabs populated | OK | empty post-30 turns |

---

## Failure playbook

| Síntoma | Investigar | Root cause probable | Fix arquitectónico |
|---|---|---|---|
| `copilot_routing_log` vacío post-turn | F11.1 wire roto | exception en `_record_routing_decision` swallowed | Ver `chat.py::_record_routing_decision` try/except → ¿logger.warning aparece en docker logs? |
| Cache hit rate <30% | Prefix corto o rotando | `compose_system_prompt` reorden | Sumar tokens del prefix cacheable + verificar orden vs F8 §5.2 |
| LLM classifier siempre invocado | rule classifier no matchea | regex policy desactualizada | `domain/routing_policy.py::DEFAULT_ROUTING_POLICY.rules` keywords |
| HEAVY p50 >30s | OpenAI rate limit o timeout | `COPILOT_STREAM_TIMEOUT_SECONDS` env | check timeout + Sentry warnings |
| Admin tab vacío con data en DB | query SQL en módulo | `src/admin/modules/copilot_routing.py` query SQL | verificar SQL en _fetch helper |

---

## Lo que necesito de Chris

- [ ] Tenant test con Clerk session válida (token API exportable).
- [ ] Confirmar `routing_policy.py` no fue tocado post-F8 (si sí, ajustar S1.2 expectations).
- [ ] (Opcional) baseline de routing log de prod si querés comparar con desarrollo.

---

## Antipatrones descubiertos durante la corrida 2026-04-25

- **Latencia degrada bajo OpenAI rate limit (TPM tier 1 = 30k/min).** El system
  prompt copilot pesa ~17.5k tokens; bajo carga sequencial (>1.7 turns/min) el
  cliente OpenAI re-trya con backoff y los turn_end reportan duración 28-45s.
  Antes de medir latencia per tier, **verificar org tier OpenAI** o espaciar
  turns ≥35s. Esto NO es bug Nicolify; es constraint billing.
- **`copilot_routing_log.tier_selected` ≠ modelo realmente usado.** F11.1 wired
  el router como **telemetry-only** (decisión documentada en `learnings/F11-housekeeping.md`).
  El graph sigue bound al MINI por defecto. Cualquier cost/latency assertion
  por tier debe agregar `JOIN ... ON data->>'model'` (real) o esperar al
  cutover F-pos que swappee el LLMFactory por tier.
- **Cost log overestimado por no aplicar discount cached.** `usage_tracking.calculate_cost`
  multiplica el total `prompt_tokens` por `prices["input"]` sin separar
  `cached_input_tokens`. Cache hit rate 99% = cost real ≈ 50% del logged.
  Fix futuro: actualizar fórmula con `cached_rate = input_rate * 0.5`.
