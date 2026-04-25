# F4 — URL contextual + Scratchpad inspirations

**Pre-req:** F2 cerrada (subagents + scratchpad). F3 cerrada (brand lighthouse para evaluar relevancia).
**Sprints estimados:** 1.
**Valor entregado:** usuario pega URL → queda como inspiración persistente en la conversación → puede referenciarse en cualquier turn posterior. "Rescata el bloque de testimonios de mujerescoraje" funciona en turn 7 igual que en turn 2.

---

## §1 Objetivo

Tool transversal `fetch_url(url, why?)` que:

1. Detecta intención: ¿quiere extraer a campos (existing pipeline) o usar como contexto (este flow nuevo)?
2. Si contexto → spawn `url_analyzer` subagent (no contamina main):
   - httpx + trafilatura → markdown limpio.
   - LLM NANO summarize + extrae sub-elementos (testimonios, CTAs, propuesta valor, paleta visual mencionada).
   - Si tiene dudas relevantes a la marca del tenant (vs brand_lighthouse), genera **clarify** (1 a 1, adaptive).
3. Persiste en scratchpad `/inspirations/{slug}.md` con frontmatter (url, captured_at, intent del usuario, brand_relevance_score).
4. System prompt enriquecido con tabla resumen de inspiraciones activas.

---

## §2 Pre-lectura específica

- `02-architecture-target.md §1` (estructura final), §5 (scratchpad híbrido).
- `learnings/F2-deep-agents.md` (API subagent) y `learnings/F3-brand-summary.md` (context_injector pattern).
- Tools existentes:
  - `backend/src/modules/copilot/application/tools/extraction_tools.py` (extract_from_url legacy — NO eliminar).
  - `backend/src/modules/copilot/application/tools/shared_tools/web_research.py` (Tavily — NO duplicar).

---

## §3 Research mandate (abril 2026)

Queries WebSearch:

- `trafilatura python web extraction 2026 best practices markdown`
- `readability vs trafilatura vs newspaper3k 2026 benchmarks`
- `httpx async timeout retry web scraping 2026`
- `LLM url summarization brand alignment scoring 2026`

Productos:

- Versión `trafilatura` fijada.
- Estrategia anti-bloqueo (UA realistic, retry, fallback Playwright si HTML JS-heavy — opcional aplazable).
- Patrón scoring "brand_relevance" (LLM judge mini comparando summary vs brand_lighthouse).

---

## §4 Lo que NO se toca

- `extract_from_url` legacy (sigue siendo el path para extracción a fields). El nuevo flow es **alternativo**, no reemplazo.
- `web_research` Tavily (queries de mercado, no fetch URL específica).
- AssetsService.

---

## §5 Deliverables

### 5.1 Tool `fetch_url`

`backend/src/modules/copilot/application/tools/fetch_url.py`:

```python
@tool
async def fetch_url(url: str, why: str = "") -> dict:
    """Fetch and analyze a URL as context/inspiration. Persists summary to scratchpad."""
```

Comportamiento:

- Validación URL (https only, blocklist dominios privados/local).
- Spawn subagent `url_analyzer` con args (url, why, brand_lighthouse).
- Subagent escribe en scratchpad. Tool retorna preview + path scratchpad.
- UI Action: nueva card `inspiration_saved` (extends bloques existentes — coordinar con UI-SPEC).

### 5.2 Subagent `url_analyzer`

`backend/src/modules/copilot/application/subagents/url_analyzer.py`:

Pipeline interno:

1. httpx async fetch (timeout 15s, 1 retry).
2. trafilatura `extract(html)` → markdown.
3. LLM NANO: summarize + extract sub-elements + brand_relevance_score (0-1).
4. Si score < 0.4 + ≥2 dudas de aplicabilidad → emit clarify (1 question at a time).
5. Write `/inspirations/{slug}.md` con frontmatter completo.

### 5.3 Scratchpad enrichment

System prompt incluye tabla:

```
## Inspiraciones cargadas
- mujerescoraje.com → "competencia voz/imagen" (hace 5min, relevance 0.8)
- hotmart.com/curso-x → "estructura página venta" (hace 12min, relevance 0.6)
```

Cap: max 5 inspiraciones activas. Si supera, FIFO. Usuario puede `pin_to_memory(path)` para promover a persistente.

### 5.4 Tool `pin_to_memory` (de F2 ahora con uso real)

`backend/src/modules/copilot/application/tools/pin_to_memory.py`:

- Lee scratchpad path.
- Inserta en `copilot_pinned_memory` table (creada en F2).
- Path final: `/memories/{tenant_id}/{user_id}/{slug}.md`.

### 5.5 Tests

- Unit subagent con HTML fixture.
- Golden tests:
  - Pegar URL → inspiración guardada → 2do turn referencia.
  - Pegar URL irrelevante → clarify card pidiendo intención.
  - Pin to memory → persiste.
- E2E mock: `fetch_url` → scratchpad escrito → system prompt incluye tabla.

### 5.6 Frontend

- Renderer `inspiration_saved` card (preview + thumbnail si hay og:image).
- Acción "Pin a memoria" botón → invoca tool `pin_to_memory`.

---

## §6 Quality gates

- `/test-backend` + `/test-frontend` verdes.
- Manual: pegar URL real (`https://example.com`), verificar scratchpad escribe + UI muestra card + 2do turn LLM lo cita.
- Smoke: URL que falla fetch → user-friendly error, no crash.

---

## §7 Riesgos

| Riesgo | Mitigación |
|---|---|
| Trafilatura rompe en sitios JS-heavy | Fallback "no se pudo extraer" + sugerir copy-paste manual. Playwright fallback aplazable. |
| Abuse: usuario pega 50 URLs | Rate limit por conversación (max 10) + cap scratchpad. |
| Clarify loop infinito | Cap max 3 questions/url. |
| Privacy: URL contiene query string sensible | Strip query before persist. Log audit. |

---

## §8 Definición de hecho

- [ ] Tool `fetch_url` operativo.
- [ ] Subagent `url_analyzer` con context isolation.
- [ ] Scratchpad enrichment en system prompt.
- [ ] Tool `pin_to_memory` funcional.
- [ ] Frontend renderiza `inspiration_saved`.
- [ ] Tests + golden verdes.
- [ ] Privacy review: URLs con query strings strip.
- [ ] `learnings/F4-url-contextual.md` + `prompts/F5-start.md`.
