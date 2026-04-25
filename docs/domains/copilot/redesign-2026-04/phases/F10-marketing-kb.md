# F10 — Marketing KB curado (`nicolify_marketing_kb`)

**Pre-req:** F9 cerrada (calidad + observabilidad listas para medir impacto).
**Sprints estimados:** 1-2 + curación contenido.
**Valor entregado:** copilot responde con autoridad técnica, cita método aplicado ("aplicando Hormozi value equation:...", "según metodología Nicolify..."). Cierre del puzzle.

---

## §1 Objetivo

1. Renombrar collection `copilot_knowledge` → `nicolify_marketing_kb` (tenant-agnostic).
2. Cerrar tenant ingest endpoint (`POST /api/v1/copilot/ingest`) → 410 Gone.
3. Schema metadata nuevo (category, methodology, domain, tags).
4. Tool `knowledge_search(query, domain?, methodology?)` simplificado (sin scope confuso).
5. System prompt: "Si tienes duda framework → usa knowledge_search, cita método".
6. Curación inicial corpus: ~30-50 docs base (yo armo: metodología propia Nicolify + frameworks complementarios).
7. Seed script + admin Streamlit refactor (solo Nicolify staff carga).

---

## §2 Pre-lectura específica

- Code actual: `copilot/infrastructure/knowledge/vector_store.py`, `application/services/knowledge_ingestion.py`.
- Admin Streamlit: `src/admin/pages/knowledge.py` + `src/admin/modules/knowledge.py`.
- `learnings/F8-routing.md` y `learnings/F9-quality.md`.
- Memory file: `feedback_strict_quality.md`.

---

## §3 Research mandate (abril 2026)

Queries WebSearch:

- `Qdrant collection migration rename data 2026`
- `RAG corpus curation chunking strategy 2026 marketing knowledge`
- `LLM citation pattern source attribution 2026 best practices`
- `hybrid search dense sparse rerank 2026 fastest`

Productos:

- Estrategia migration sin downtime.
- Chunking optimal para frameworks (chunk size, overlap, semantic boundaries).
- Pattern citation: `CitationBlock` ya existe — reusar.

---

## §4 Lo que NO se toca

- `CitationBlock` schema (multi-modal contract).
- Sales agent — su RAG queda fuera scope (vive en otro plan).

---

## §5 Deliverables

### 5.1 Migration collection

- Crear `nicolify_marketing_kb` Qdrant collection.
- Migrate puntos del scope `"help"` actual al nuevo (drop `tenant_id` field, rebrand metadata).
- Drop scope `"business"` (prohibido en este corpus).
- Rename completo + retire `copilot_knowledge` collection.

### 5.2 Schema metadata

```python
{
  "category": "framework" | "playbook" | "script" | "checklist" | "case_study",
  "methodology": "nicolify_owned" | "storybrand" | "hormozi" | "cialdini" | "aida" | "pas" | "jtbd",
  "domain": "brand" | "offer" | "copy" | "objections" | "pricing" | "funnel" | "audience",
  "tags": [...],
  "source_doc": str,
  "chunk_index": int,
  "language": "es",
  "version": int
}
```

### 5.3 Tool `knowledge_search`

Refactor `copilot/application/tools/knowledge_search.py`:

```python
@tool
async def knowledge_search(
    query: str,
    domain: str | None = None,
    methodology: str | None = None,
    limit: int = 5,
) -> list[dict]:
```

- Sin scope param. Solo filtros opcionales.
- Output incluye `methodology` para que el LLM cite.

### 5.4 System prompt

Addendum cacheable:

```
## Conocimiento técnico
Si dudas en framework de marketing/ventas, usa knowledge_search ANTES de responder.
Cita método aplicado (ej. "aplicando Hormozi value equation: …").
Frameworks disponibles: nicolify_owned, storybrand, hormozi, cialdini, aida, pas, jtbd.
```

### 5.5 Cierre tenant ingest endpoint

`POST /api/v1/copilot/ingest` → return 410 Gone con mensaje explicativo. Frontend del tenant: ocultar UI de upload (si existía).

### 5.6 Admin Streamlit refactor

Solo Nicolify staff. Página `/admin/copilot/knowledge`:

- Upload PDF/MD/DOCX con metadata categorizada.
- Lista corpus con filtros.
- Re-index button.
- Versión/diff entre uploads.

### 5.7 Curación corpus inicial (~30-50 docs)

Yo armo (claude que ejecuta F10):

- **Metodología Nicolify propia** (Chris provee contenido raw → estructuramos chunks).
- **Frameworks complementarios** (~20-25 docs):
  - StoryBrand: 7 elementos, hero/guide pattern.
  - Hormozi: grand slam offer, value equation, dream outcome, perceived likelihood.
  - Cialdini: 7 principios influencia.
  - AIDA / PAS / FAB / 4U.
  - JTBD framework.
  - Archetype playbooks por business_type (coach 1-on-1, infoproductor, productized service, agency, e-commerce, course, membership).
  - Headlines, hooks, CTAs cookbooks.
  - Manejo objeciones (precio/tiempo/confianza/aplicabilidad).

### 5.8 Seed script

`backend/scripts/seed_nicolify_marketing_kb.py`:

- Lee `data/marketing_kb/*.md`.
- Chunkea + embedea.
- UPSERT vectors a Qdrant.

### 5.9 Tests

- Arch test: copilot tools NO leen otra collection.
- Integration: `knowledge_search("cómo construyo un grand slam offer")` retorna chunks Hormozi con `methodology="hormozi"`.
- Citation flow: respuesta LLM cita método y emite `CitationBlock`.

---

## §6 Quality gates

- `/test-backend` verde.
- Migration sin downtime verificada (clone DB).
- ≥30 docs cargados.
- LLM-judge sample 50 queries: respuestas citan método cuando aplica (≥80% rate).

---

## §7 Riesgos

| Riesgo | Mitigación |
|---|---|
| Chunks mal curados degradan respuestas | Eval-set fijo corre semanal en F9 framework. |
| Migration Qdrant pierde data | Backup snapshot antes. Dual collection running 1 semana. |
| Tenants confundidos por ingest cerrado | Mensaje explicativo + comm en release notes. |

---

## §8 Definición de hecho

- [ ] `nicolify_marketing_kb` collection live.
- [ ] Tenant ingest cerrado.
- [ ] Schema metadata aplicado.
- [ ] Tool refactorizado.
- [ ] System prompt addendum.
- [ ] Admin refactor.
- [ ] ≥30 docs curados cargados.
- [ ] Citation flow verificado.
- [ ] `learnings/F10-marketing-kb.md` (cierre del plan).

---

## §9 Cierre del plan

Al cerrar F10, el copilot estará en estado "Claude Code de Marketing":

- Plug-in friendly (provider pattern).
- Memoria viva (brand lighthouse + scratchpad + pinned).
- Q&A natural sobre datos propios.
- URL contextual persistente.
- Workflows unificados.
- Channel-aware output.
- Routing/cost optimizado.
- Quality observability.
- RAG curado autoritario.

Documento `learnings/F10-marketing-kb.md` cierra con retrospectiva del plan completo + recomendaciones para futuras evoluciones (multi-modal generative, MCP servers, etc.).
