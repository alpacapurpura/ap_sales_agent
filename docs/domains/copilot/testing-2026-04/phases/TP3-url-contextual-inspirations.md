# TP3 — URL Contextual + Inspirations Persistence (F4)

**F# que valida:** F4 (`fetch_url` tool + `pin_to_memory` + scratchpad `/inspirations/*` + system prompt enriquecido).
**Tiempo estimado:** 2 hs.
**Pre-req hard:** TP0 + TP2 (brand summary aporta contexto al url_analyzer subagent).

---

## Misión

Confirmar que:

1. Pegar URL → `fetch_url` tool extrae + persiste como inspiración.
2. Inspiración aparece en sucesivos turns sin re-pegar la URL ("rescata el bloque de testimonios de mujerescoraje" funciona en turn 7).
3. `inspiration_saved` card aparece en UI cuando se persiste.
4. Múltiples inspiraciones acumulan correctamente sin pisarse.
5. URL inválida o paywalled fail gracefully (sin exception bubbleada).
6. `brand_relevance_score` populated en `copilot_inspiration` post-fetch (F4 hook).

---

## Research mandate

Queries:

- `"trafilatura web scraping LLM context 2026 best practices"` — confirmar lib sigue siendo state-of-the-art para extract.
- `"persistent context window agent memory 2026 patterns"` — validar que el patrón scratchpad sigue siendo el approach.
- `"web scraping ethics rate limit user-agent 2026"` — confirmar que `fetch_url` respeta robots.txt + UA.

---

## Scenarios

### S3.1 — Fetch URL básica

Turn:
```
"mirá esto: https://www.mujerescoraje.com — ¿qué te parece su sección de testimonios?"
```

Expected trace:
- `tool_call` con `name='fetch_url'`, `args={'url': 'https://www.mujerescoraje.com'}`.
- `card_emitted` con `card_kind='inspiration_saved'`.
- `assistant_text` referencia el contenido scrapeado.

```sql
SELECT name, status, data->'output_preview' FROM copilot_trace_event
WHERE turn_id=:tid AND event_type='tool_call';
SELECT * FROM copilot_inspiration WHERE conversation_id=:cid;
```

**Pass:** 1 fetch_url tool_call OK + 1 inspiration row con `url` y `extracted_content_preview` no vacíos.

### S3.2 — Persistencia cross-turn

Turn 2 (mismo conv): `"genial. ahora dame una idea de copy para mi landing"`.
Turn 3: `"para mi sección de testimonios, basate en lo que viste en mujerescoraje"`.

**Pass:** Turn 3 referencia testimonios de mujerescoraje SIN re-fetch (no aparece tool_call fetch_url en turn 3). System prompt de turn 3 incluye sección "Inspiraciones cargadas" con ≥1 entry.

```sql
SELECT data->'input_messages'->0->>'content' AS sys_prompt
FROM copilot_trace_event
WHERE turn_id=:turn3_id AND event_type='llm_call' LIMIT 1;
```

### S3.3 — Inspiration card UI (Chrome DevTools)

Browser flow:
1. Abrir conversación nueva en `dev-app.nicolify.com`.
2. Pegar URL en composer.
3. Submit.
4. Esperar `inspiration_saved` card aparecer.
5. Screenshot.

**Pass:** card visible en ≤5s, sin parpadeo, click en card no rompe.

### S3.4 — Múltiples inspiraciones

3 URLs en turns separados:
- Turn 1: URL competidor 1.
- Turn 2: URL competidor 2.
- Turn 3: URL artículo blog.

```sql
SELECT COUNT(*) FROM copilot_inspiration WHERE conversation_id=:cid;
```

Turn 4: `"resumime las 3 inspiraciones que tenemos cargadas"`.

**Pass:** 3 rows en DB + assistant_text menciona las 3.

### S3.5 — URL inválida graceful

Turn: `"mirá: https://does-not-exist-xyz.invalid"`.

**Pass:** trace muestra `tool_call status='error'` + assistant responde algo como "no pude acceder a esa URL" sin throwing 500.

### S3.6 — URL paywalled (Trafilatura empty)

Turn: `"mirá https://www.nytimes.com/<algun-articulo-pagado>"`.

**Pass:** copilot reporta "no pude extraer contenido — puede ser paywall" sin alucinar contenido.

### S3.7 — `pin_to_memory` tool funciona

Turn: `"recordá que mi marca usa el color #FF5733"`.

```sql
SELECT * FROM copilot_pinned_memory WHERE conversation_id=:cid;
```

**Pass:** 1 row con `content='#FF5733' o similar`. En turn siguiente, system prompt incluye memory.

### S3.8 — `brand_relevance_score` populated (F4 hook futuro)

```sql
SELECT brand_relevance_score FROM copilot_inspiration
WHERE conversation_id=:cid AND brand_relevance_score IS NOT NULL;
```

**Pass:** scores entre 0.0-1.0 cuando brand_summary está populated.
**Soft fail:** todos null → hook no implementado todavía (heredado de F4 backlog), documentar en results.

---

## Tools / queries

- DeepEval: `tests/quality/deepeval/test_tp3_url_inspirations.py`.
- Chrome DevTools MCP para S3.3.
- SQL: `copilot_inspiration`, `copilot_pinned_memory`, `copilot_trace_event`.

---

## Targets

| Métrica | Target | Hard fail |
|---|---|---|
| fetch_url latencia | ≤3s p50 | >10s |
| Inspiration row creada | 1:1 per URL | 0 |
| Persistence cross-turn | OK turn 7 | falla en turn 3 |
| Card UI render sin flash | 0 flashes | 1+ |
| URL inválida graceful | 0 exceptions | 1+ |
| Multiple inspirations independent | N rows | merge silente |
| pin_to_memory works | OK | row missing |

---

## Failure playbook

| Síntoma | Investigar | Root cause | Fix |
|---|---|---|---|
| fetch_url falla siempre | trafilatura version | `pip show trafilatura` + changelog | bump dep o downgrade |
| Inspiration NO aparece en system prompt turn N | inspirations_layer.py | `system_prompt_layout` orden | ver `inspirations_layer::_HEADER` se inyecta |
| Card flash | dual emit (block_append + ui_action) | `chat.py::_handle_tool_end_v2` | dedupe por card_id |
| pin_to_memory inactivo | tool registered? | `registry.py::PIN_TO_MEMORY` group | ver navigation map |
| brand_relevance_score null | ARQ task no implementado | F4 backlog | documentar como riesgo abierto |

---

## Lo que necesito de Chris

- [ ] URL real de competidor para S3.1 (la skill scrape lo que vos quieras testear).
- [ ] Confirmar que dev-app está en CF tunnel (TP3 usa Chrome DevTools).
