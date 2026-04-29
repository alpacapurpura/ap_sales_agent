# Copilot-First Checklist (Nicolify-specific)

> Toda funcionalidad Nicolify operable conversacionalmente. UI = complemento. Esta checklist gate de cada PR.

## Por qué

Visión Nicolify (`vision-compressed.md`): copilot es **interfaz primaria**. Si nuevo feature solo accesible por UI directa, fallamos visión.

## Checklist obligatorio (PR.md sección)

```markdown
## Operable desde copilot? **(obligatorio)**

- [ ] **Sí** — descripción flujo conversacional:
  ```
  User: "{frase ejemplo}"
  Copilot: {respuesta + tool ejecución}
  ```
- [ ] **No** — justificación robusta:
  - {por qué la UI directa es necesaria}
  - {por qué el flujo conversacional no aporta}
```

## Default = Sí

Si dudás, es Sí. Carga de la prueba está en el "No". No requiere justificación robusta sobre por qué la conversación no es suficiente.

## Tipos de operación + cómo se mapea a copilot

| Operación | Pattern copilot |
|---|---|
| Crear entidad | Tool `create_X` con args extraídos del mensaje |
| Modificar entidad | Tool `update_X` + `propose_field_updates` para mutaciones complejas |
| Buscar / listar | Tool `list_X` + filtros en arg |
| Configurar setting | Tool `update_setting` |
| Subir doc / extraer | Tool `extract_document_to_fields` |
| Procedimiento multi-step | Tool guiado step-by-step (Procedure) |
| Diagnóstico (¿por qué bajó X?) | Tool query analytics + interpretación LLM |
| Visualización embedida | Card emitida por tool con datos formateados |

## Excepciones legítimas

Casos donde "No" es justificable. Documentar EN el PR.md.

| Excepción | Razón |
|---|---|
| Drag-drop visual complejo (Bowtie funnel) | Manipulación espacial > conversación |
| Edición assets visuales (flyer, logo) | Output visual > texto |
| Comparación side-by-side | Tabla densa más rápida ver |
| Setup OAuth multi-paso (callbacks redirect) | Flow técnico requiere UI |

Aún en excepciones: copilot debería poder **iniciar** el flujo + **resumir** post.

## Nicolify copilot capacidades existentes a aprovechar

| Capacidad | Doc |
|---|---|
| Auto-fill desde docs | `current-state/copilot.md` |
| Schema introspection | `.claude/rules/copilot-resilience.md` |
| Module Registry | tool registry route-based |
| Cards emitidas por tools | UI rich responses |
| Subagents (deepagents) | delegaciones complejas |
| Trazas observabilidad | debug + cost tracking |

## Anti-patterns

- ❌ Marcar "Sí" sin descripción flujo conversacional → vacío.
- ❌ "No" con razón débil ("es más visual") → reto: probá con una frase ejemplo.
- ❌ Diseñar UI primero, después pensar cómo "agregar" copilot → backwards.
- ❌ Tool genérico "do_anything" → cero precisión, mal UX.

## Anchor

Antes pasar PR a `ready` → revisá esta checklist. Sin checklist marcada = no ready.
