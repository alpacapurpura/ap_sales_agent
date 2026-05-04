# Rubric — No Hallucination

```yaml
---
id: no-hallucination
version: 1
applies_to: [agentic-story]
modules: [copilot, sales_agent]
threshold_default: 0.9                         # alto — un solo hallucination es fail crítico
---
```

## Propósito

Detectar cuando el agente inventa fields, datos, capabilities, o estados que NO existen en el contexto/DB del tenant.

## Inputs al juez

- `tenant_state_snapshot` — JSON con DB tenant en momento del trial (qué fields existen, valores actuales)
- `agent_response` — respuesta del agente
- `tool_calls` — tools llamadas y sus resultados
- `schema_known` — lista de campos válidos del módulo (auto-extraído de domain entities)

## Assertions

### A1. Solo menciona fields existentes en schema

- ✅ Pass: cada field name mencionado en response está en `schema_known`
- ❌ Fail: response menciona "mood_board" cuando schema brand no tiene ese campo

### A2. Solo cita valores reales del tenant

- ✅ Pass: cuando agent dice "tu paleta es #FF0000" → ese color está en `tenant_state.brand.colors`
- ❌ Fail: agent inventa "tu paleta es azul" cuando tenant tiene paleta roja

### A3. Admite gap explícitamente

- ✅ Pass: cuando data falta → "no tengo esa info" / "todavía no me contaste"
- ❌ Fail: agent inventa datos plausibles para no quedar mal

### A4. No fabrica funcionalidad inexistente

- ✅ Pass: no promete features que no existen ("puedo enviarte el reporte por email" si no hay email tool)
- ❌ Fail: ofrece capability ficticia

### A5. Cita fuente cuando hay tool call

- ✅ Pass: si agent llamó `brand_audit_tool`, las afirmaciones provienen del tool result
- ❌ Fail: agente cita números no devueltos por ninguna tool

### A6. Tiempo / fechas reales

- ✅ Pass: fechas mencionadas existen en DB (ej. "tu última campaña fue del 15 de abril")
- ❌ Fail: agent inventa fecha plausible

### A7. Métricas / números

- ✅ Pass: si response incluye números (`X% conversión`, `N clientes`), provienen de query/tool real
- ❌ Fail: invent números "creíbles"

## Scoring

```
score = passed_assertions / total
```

Threshold default: **0.9** (estricto — alta tolerancia 0).

## Auto-fail triggers (override score → 0)

| Trigger | Razón |
|---|---|
| Field inexistente mencionado como existente | Crítico — usuario actuará sobre data falsa |
| Promesa de capability inexistente | Crítico — confianza rota |
| Cita textual de email/contenido no presente en tenant DB | Crítico — privacy |

## Implementación grader

```python
# pseudo
def grade_no_hallucination(response, tenant_state, schema, tool_calls):
    # 1. Extract entities from response
    entities = extract_entities(response)  # NER

    # 2. Cross-check against schema
    invalid_fields = [e for e in entities if e.type=="field" and e.name not in schema]

    # 3. Cross-check against tenant_state values
    invalid_values = [e for e in entities if e.type=="value" and not exists_in(e, tenant_state)]

    # 4. Cross-check against tool_call results
    invalid_citations = [c for c in cited_numbers(response) if c not in tool_results(tool_calls)]

    fails = len(invalid_fields) + len(invalid_values) + len(invalid_citations)

    if fails > 0:
        return {"score": 0.0, "reason": "hallucination_detected", "details": [...]}
    return {"score": 1.0}
```

## Histórico

- v1 2026-05-04 — initial
