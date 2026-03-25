# Copilot v2 — Phase 3 Done: Rich Intelligence

**Completado:** 2026-03-25
**Verificación:** ruff clean, tsc clean, serialize/deserialize roundtrip OK, registry integration OK

---

## Arquitectura Post-Phase 3

### Archivos Nuevos

| Archivo | Sub-fase | Propósito |
|---------|----------|-----------|
| `frontend/.../messages/MetricSummaryCard.tsx` | 3.1 | Grid 2-col de mini-cards con trend arrows |
| `frontend/.../messages/ComparisonTable.tsx` | 3.1 | Tabla responsive con fila recomendada purple |
| `frontend/.../messages/ProgressChecklist.tsx` | 3.1 | Checklist clickeable con navegación |
| `frontend/.../messages/MultiOptionSelector.tsx` | 3.1 | Cards seleccionables + copilot:field-update |
| `backend/.../infrastructure/knowledge/__init__.py` | 3.2 | Package init |
| `backend/.../infrastructure/knowledge/vector_store.py` | 3.2 | CopilotKnowledgeStore (Qdrant hybrid) |
| `backend/.../application/services/knowledge_ingestion.py` | 3.2 | Chunking + embed + upsert + auto-summary |
| `backend/.../application/tools/knowledge_tools.py` | 3.2 | `search_knowledge_base` LangChain tool |
| `backend/.../api/knowledge.py` | 3.2 | REST: /ingest, /search, /{doc_id} |
| `backend/src/admin/modules/knowledge.py` | 3.4 | Streamlit 5-tab knowledge dashboard |

### Archivos Modificados

| Archivo | Sub-fase | Cambio |
|---------|----------|--------|
| `copilot-store.ts` | 3.1 | 4 nuevos UIAction types + 6 campos opcionales |
| `AssistantMessage.tsx` | 3.1 | Switch-based rendering por tipo de UIAction |
| `analytics_tools.py` | 3.1 | Emite `metric_summary` ui_action con 5 métricas |
| `awareness.py` | 3.1 | Emite `checklist` ui_action con módulos + routes |
| `registry.py` | 3.2 | `knowledge` tool group en TODAS las rutas |
| `main.py` | 3.2 | Router `/api/v1/copilot/knowledge` |
| `copilot_system.j2` | 3.2 | Sección "Herramientas de Conocimiento" |
| `chat.py` | 3.3 | Serialize/deserialize tool_calls + fix JSON parse |
| `app.py` (admin) | 3.4 | Nav entry "Knowledge Base" |

---

## Contratos API

### Knowledge Endpoints

```
POST /api/v1/copilot/knowledge/ingest
  Body: multipart/form-data (file, scope, source_label)
  Response: { document_id: str, chunks_indexed: int }

GET  /api/v1/copilot/knowledge/search?query=...&scope=...&limit=...
  Response: { results: [{ content, score, metadata }] }

DELETE /api/v1/copilot/knowledge/{document_id}
  Response: { deleted: true }
```

### UIAction Types (Phase 3 additions)

```typescript
// metric_summary
{ type: "metric_summary", metrics: [{ label, value, trend?, delta? }] }

// comparison
{ type: "comparison", columns: string[], rows: Record<string,string>[], recommended? }

// checklist
{ type: "checklist", items: [{ label, done, route? }] }

// multi_option
{ type: "multi_option", options: [{ id, title, content }], field_id }
```

---

## Estrategia Qdrant

- **Colección:** `copilot_knowledge` (SEPARADA de `visionarias_knowledge` y `visionarias_hybrid`)
- **Scopes:** `help` (docs sistema, auto-resúmenes) | `business` (docs usuario)
- **Hybrid search:** dense (OpenAI text-embedding-3-large 3072d) + sparse (BM25) + FlashRank reranking
- **Tenant isolation:** filtro `tenant_id` en todas las queries

---

## Persistencia de Mensajes

### Formato nuevo (con tool_calls)
```json
[
  {"role": "user", "content": "..."},
  {"role": "assistant", "content": "", "tool_calls": [{"id": "call_abc", "name": "...", "args": {...}}]},
  {"role": "tool", "content": "...", "tool_call_id": "call_abc", "name": "..."},
  {"role": "assistant", "content": "Respuesta final"}
]
```

### Backward compatible
Mensajes antiguos (sin `tool_calls`, sin role `tool`) se deserializan correctamente.

### Fix aplicado
Eliminado `tool_output.replace("'", '"')` — ahora se usa `json.loads(tool_output)` directo, confiando en que todos los tools usan `json.dumps()`.

---

## Auto-Resúmenes

`KnowledgeIngestionService.ingest_product_summary(tenant_id)`:
1. Lee Brand, Offer, Connections vía `MODULE_REGISTRY`
2. Genera markdown estructurado (sin LLM, puro format)
3. Ingesta como scope=`help`, source=`auto_summary`

---

## Streamlit Admin — Knowledge Base

5 tabs:
1. **Dashboard:** stats de colección (vectores, puntos, status)
2. **Explorar:** listar documentos con filtros tenant/scope
3. **Buscar:** búsqueda semántica con scores y metadata
4. **Ingestar:** upload archivo + auto-resumen por tenant
5. **Eliminar:** borrar por document_id con confirmación

---

## Dependencias para Phase 4

- Nuevos componentes (MetricSummaryCard, ComparisonTable, ProgressChecklist, MultiOptionSelector) listos para events tracking
- Knowledge base operativa para contextualizar respuestas del copilot
- Tool_calls persistidos permiten replay y debugging de conversaciones
- Streamlit admin permite monitoreo de knowledge sin acceso a producción
