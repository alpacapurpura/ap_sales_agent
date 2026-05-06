# PRD Template — Multi-variant

> Producto del PM al final del discovery. Para Nicolify post-redesign 2026-05 usamos `docs/product/stories/{story-id}/01-spec.md` (autocontenido) — variantes según scope siguen siendo útiles para framing al redactar el spec.

## Cuándo usar cuál

| Variante | Cuándo | Tiempo dev estimado |
|---|---|---|
| **Feature Brief** | Solo exploración, antes de comprometerse | 1 sem o menos |
| **One-Page PR** | Feature simple, alcance claro | 2-4 sem |
| **Standard PR** | Feature compleja, multi-módulo | 6-8 sem |
| **PI Container** | Tema multi-PR coherente | Variable |

## Estructura común (toda variante)

1. **Job-to-be-done** (`Cuando X, quiero Y, para Z`) — 1 frase
2. **Outcome esperado** — métrica cuant + cualitativa
3. **Walking skeleton** — bullets MVP end-to-end
4. **Out of scope** — explícito, antes que pregunten
5. **Operable desde copilot** — sí + flujo, o no + razón
6. **User stories** + criterios aceptación
7. **Restricciones negocio** — multitenant, LATAM, PII, currency
8. **Decisiones tomadas / diferidas** — append-only

## Splitting técnicas (Patton + Lawrence)

Si user story muy grande, split por:

| Técnica | Ejemplo |
|---|---|
| **Datos** | "Acepta CSV" → "Acepta sólo nombres + email primero" |
| **Operación** | CRUD → "Solo create primero" |
| **Business rule** | Reglas multi-condicionales → versión más simple primero |
| **Esfuerzo entrada** | Form completo → form mínimo |
| **Caracteristicas extras** | Filtros + búsqueda → solo búsqueda |
| **Calidad técnica** | Optimizado → funcional simple primero |
| **Plataforma** | Mobile + desktop → desktop primero |

## Buen PR vs malo

| Bueno | Malo |
|---|---|
| Job-to-be-done preciso | Feature description |
| Outcome medible | "Mejorar X" |
| Walking skeleton priorizado | Lista plana sin orden |
| Out of scope explícito | Implícito |
| Operable copilot definido | Asumido o ignorado |
| Decisiones diferidas listadas | Decisiones ocultas |
| Acceptance criteria Gherkin | Vibes |

## Reference

- Patton, J. *User Story Mapping*
- Pocock, M. — write-a-prd skill (multi-stage interview pattern)
