---
story_id: sales-agent-dialect-configuration
type: TBD  # likely ui-story (tenant config UI) + service-story (BE schema + runtime injection)
subtype: feature
module: sales_agent
capability: sales-conversational-engine
estimate: TBD
priority: TBD
links:
  outcome: "../../outcomes/pi-12-sales-agent-eval-foundation.md"
  related_stories:
    - "../eval-foundation-tenant-seed-data/"            # introduce dialect_code field as data
    - "../sales-agent-personas-instrumented-runtime/"   # consumer of dialect_code
    - "../sales-agent-voice-fidelity-grader-runtime/"   # gradea fidelity vs dialect_code
  related_rules:
    - "../../../../.claude/rules/spanish-text.md"
    - "../../../../.claude/rules/sales-agent-brand-voice.md"
---

# Story (PLACEHOLDER) — Sales Agent: Configuración de dialecto BCP-47 per tenant

> **Status: idea (placeholder).** Creada 2026-05-06 durante refinement de
> `eval-foundation-tenant-seed-data` para no perderla. Refinement
> propio se hará cuando Chris dispare "/pm — refinemos sales-agent-dialect-configuration"
> o equivalente.

## Job-To-Be-Done (boceto inicial)

**Como** tenant que está configurando su sales_agent en Brand Studio
**Quiero** seleccionar el dialecto/variante regional del español que usará el agente al hablar (e.g., rioplatense AR, mexicano MX, peruano PE, colombiano CO, neutro LatAm 419)
**Para** que el agente suene auténtico a la audiencia local del tenant, sin requerir que el equipo Nicolify hardcodee voseo/lexicón en cada tenant manualmente

## Por qué importa

Hoy `personality_profile.system_instruction` codifica voz pero NO dialecto explícito. Si un tenant es argentino, el voseo emerge implícitamente (o no) según cómo redactó el system_instruction. Esto es:
- Frágil — depende del prompt artesanal
- No-discoverable — el tenant no sabe que puede ajustar dialecto
- No-evaluable — el grader voice fidelity no tiene ground truth de qué dialecto debería usar

La configuración explícita de dialecto via BCP-47 (`es-AR`, `es-MX`, etc.) hace el atributo:
- Discoverable (UI dropdown en Brand Studio sección Estilo Comunicacional)
- Evaluable (grader compara output vs dialecto declarado)
- Reusable (el catálogo BCP-47 es estándar W3C, ya soportado por libs i18n)
- Default seguro (`es-419` neutro pan-LatAm hasta que tenant elija)

## Outcome esperado (boceto)

- Schema: `personality_profiles` agrega columna `dialect_code: str` (default `'es-419'`)
- Catálogo: nuevo archivo `backend/src/modules/sales_agent/domain/dialect_catalog.py` con la lista BCP-47 (≥13 entradas: es-419, es-AR, es-UY, es-CL, es-MX, es-PE, es-CO, es-VE, es-EC, es-PY, es-CR, es-DO, es-CU, es-PR, es-ES) + per entry: `code`, `display_name`, `voseo: bool | "parcial"`, `description`, `country_code`
- UI: dropdown en Brand Studio `/brand-studio/estilo` permite escoger dialecto. Default `es-419`. Tooltip explica qué cambia.
- Runtime: el compilador de personality_profile inyecta el `dialect_code` en el system_instruction (probablemente como nuevo bloque o como prefix de bloque 1 REGLAS DE PERSONALIDAD). Cache prefix slot 5 BRAND_VOICE refresca cuando dialect_code cambia.
- Migration:
  - Todos los tenants existentes → `dialect_code = 'es-419'` (neutro LatAm) como default
  - Backward compatible (column nullable + default; recompila personality on read si dirty)
- Grader: voice fidelity grader (story `sales-agent-voice-fidelity-grader-runtime`) recibe `expected_dialect: str` desde el tenant config y gradúa fidelity vs catálogo (e.g., output AR sin voseo → fidelity drop)

## Catálogo dialectos propuesto (BCP-47, base ratificada Chris 2026-05-06)

| Code | Nombre UI | Voseo | País/Región |
|---|---|---|---|
| `es-419` | Español neutro (LatAm) | No | Pan-regional (default) |
| `es-AR` | Rioplatense (Argentina) | Sí | AR |
| `es-UY` | Rioplatense (Uruguay) | Sí | UY |
| `es-CL` | Chileno | Parcial | CL |
| `es-MX` | Mexicano | No | MX |
| `es-PE` | Peruano (limeño/andino) | No | PE |
| `es-CO` | Colombiano | Parcial | CO (paisa voseo, bogotano tuteo) |
| `es-VE` | Venezolano | No | VE |
| `es-EC` | Ecuatoriano | No | EC |
| `es-PY` | Paraguayo | Sí | PY |
| `es-CR` | Costarricense | Parcial | CR |
| `es-DO` | Dominicano | No | RD |
| `es-CU` | Cubano | No | CU |
| `es-PR` | Puertorriqueño | No | PR |
| `es-ES` | Castellano (España) | No (vosotros) | ES (opcional) |

## Antecedentes / Contexto

- **Origen:** discovery 2026-05-06 durante refinement de `eval-foundation-tenant-seed-data` Q7. Chris explicitó: "para el sales_agent deberíamos hacer que el tenant escoja el lenguaje específico (chileno, argentino, peruano, etc.) como parte de la experiencia de usuario; voseo en cada parte hardcodeado es para development con Claude Code/copilot, no para producción agente"
- **Investigación realizada:** búsqueda 2026-05-06 reveló que NO hay códigos ISO específicos por dialecto del español; el estándar industria es BCP-47 `es-{COUNTRY}` + `es-419` (LatAm neutro)
- **Rule existente:** `.claude/rules/spanish-text.md` ya documenta excepción sales_agent ("output sales_agent respeta voz tenant"); esta story formaliza la SELECCIÓN explícita por tenant
- **Stack:** BE schema migration + UI Shadcn dropdown + runtime prompt injection + grader update

## Out of scope (boceto)

- NO migrar tenants existentes a dialect distinto de `es-419` automáticamente — cada tenant decide manualmente
- NO crear nuevos rule files en `.claude/rules/` (skill `sales-agent-expert` documenta la feature)
- NO escribir personality_profile compiler v3 (esta story extiende compiler v2 con nuevo input — no rewrite)
- NO refactor del slot 5 BRAND_VOICE cache (preservado, solo se invalida al cambio dialect_code)

## Riesgos / Asunciones (boceto)

- **Riesgo:** dialect_code conflictúa con voseo implícito en el system_instruction artesanal del tenant (e.g., tenant escribió voseo y eligió `es-MX`). **Mitigación:** validador en compiler que detecte conflicto + warning Brand Studio UI.
- **Riesgo:** catálogo BCP-47 se vuelve discusión política regional ("¿es-CO paisa o bogotano?"). **Mitigación:** MVP con país nivel; sub-dialectos diferidos a futura story.
- **Asunción:** los 1000+ tenants Nicolify objetivo son LatAm-mayoritario; `es-419` neutro como default cubre el 80% de casos sin configuración.

## Próximo paso

`→ Esperar trigger Chris ("/pm — refinemos sales-agent-dialect-configuration") para que /po o /po-ux redacte 01-spec.md. Pre-requisito: ninguno hard. Recomendación priorización: post sales-agent-voice-fidelity-grader-runtime (story E del PI-12) — el grader necesita expected_dialect ground truth, y esta feature lo provee. Si E se construye antes que esta, E asume todos los tenants en es-419 hasta que dialect_code esté disponible.`
